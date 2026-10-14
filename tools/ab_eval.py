#!/usr/bin/env python3
"""Paired Codex CLI evaluation; Python 3.10+, standard library only."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time

CATEGORIES = {'bug_fix', 'small_feature', 'test_only', 'code_review', 'large_repo_edit'}
METRICS = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'total_tokens',
           'uncached_input_tokens', 'agent_seconds', 'validation_seconds', 'elapsed_seconds',
           'repeated_commands', 'modified_file_count')


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def execute(argv, cwd, env, timeout, prefix, stdin=None):
    """Save streams to disk; kill process group on POSIX timeout, never retry silently."""
    start = time.monotonic()
    with prefix.with_suffix('.stdout').open('wb') as out, prefix.with_suffix('.stderr').open('wb') as err:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                             stdout=out, stderr=err, start_new_session=os.name == 'posix')
        timed_out = False
        try:
            p.communicate(stdin.encode() if stdin else None, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'posix':
                os.killpg(p.pid, signal.SIGKILL)
            else:
                subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
                p.kill()
            p.wait()
    return {'exit_code': p.returncode, 'timed_out': timed_out, 'seconds': time.monotonic() - start}


def parse_events(path):
    usage = None
    commands = []
    messages = []
    errors = []
    ids = set()
    completed = 0
    for n, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError('event is not an object')
        except (ValueError, TypeError):
            errors.append(f'invalid JSONL at line {n}')
            continue
        typ = event.get('type')
        if typ == 'turn.completed':
            completed += 1
            usage = event.get('usage')
        if typ in ('turn.failed', 'error'):
            errors.append(event)
        if typ != 'item.completed':
            continue
        item = event.get('item', {})
        if not isinstance(item, dict):
            errors.append(f'invalid item at line {n}')
            continue
        key = item.get('id')
        if key and key in ids:
            continue
        if key:
            ids.add(key)
        if item.get('type') == 'command_execution':
            commands.append({'command': item.get('command', ''), 'exit_code': item.get('exit_code')})
        if item.get('type') == 'collab_tool_call':
            errors.append('subagent usage is not accounted for; run invalid')
        if item.get('type') == 'agent_message':
            messages.append(item.get('text', ''))
    required = ('input_tokens', 'output_tokens', 'cached_input_tokens')
    valid = (completed == 1 and isinstance(usage, dict) and all(
        isinstance(usage.get(k), int) and not isinstance(usage[k], bool) and usage[k] >= 0 for k in required))
    valid = valid and usage['cached_input_tokens'] <= usage['input_tokens']
    # CLI may synthesize an all-zero Usage when no notification was received.
    valid = valid and usage['input_tokens'] + usage['output_tokens'] > 0
    metrics = {k: usage[k] if valid else None for k in required}
    metrics['total_tokens'] = metrics['input_tokens'] + metrics['output_tokens'] if valid else None
    metrics['uncached_input_tokens'] = metrics['input_tokens'] - metrics['cached_input_tokens'] if valid else None
    metrics['cache_hit_ratio'] = metrics['cached_input_tokens'] / metrics['input_tokens'] if valid and metrics['input_tokens'] else None
    counts = collections.Counter(c['command'] for c in commands)
    metrics['repeated_commands'] = sum(count - 1 for count in counts.values())
    return {'usage_valid': bool(valid), 'metrics': metrics, 'commands': commands,
            'hypothesis_retries': None, 'network_retries': None,
            'failed_commands': sum(c['exit_code'] not in (0, None) for c in commands),
            'final_response': messages[-1] if messages else '', 'errors': errors,
            'raw_usage': usage, 'completed_turns': completed}


def snapshot(repo):
    """Hash tracked AND untracked/ignored files, including deletions and symlinks."""
    data = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--cached', '--others'])
    result = {}
    for name in set(data.decode().split('\0')) - {''}:
        p = repo / name
        if p.is_symlink():
            result[name] = digest(('symlink:' + os.readlink(p)).encode())
        elif p.is_file():
            result[name] = digest(str(p.stat().st_mode & 0o777).encode() + b'\0' + p.read_bytes())
    return result


def changed(before, after):
    return sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))


def in_scope(path, scopes):
    return any(path == s.rstrip('/') or path.startswith(s.rstrip('/') + '/') for s in scopes)


def savings(a, b):
    return (a - b) / a if a is not None and b is not None and a > 0 else None


def report(rows):
    pairs = []
    grouped = collections.defaultdict(dict)
    for row in rows:
        grouped[(row['task'], row['repeat'])][row['arm']] = row
    for (task, repeat), arms in sorted(grouped.items()):
        a, b = arms.get('off'), arms.get('on')
        fixture_match = bool(a and b and a['fixture_sha256'] == b['fixture_sha256'])
        eligible = bool(fixture_match and a['quality_pass'] and b['quality_pass'])
        pairs.append({'task': task, 'repeat': repeat, 'eligible': eligible, 'fixture_match': fixture_match,
                      'quality_regression': bool(a and b and a['quality_pass'] and not b['quality_pass']),
                      'failure': not eligible,
                      'savings': {k: savings(a['metrics'].get(k), b['metrics'].get(k))
                                  if eligible else None for k in METRICS}})
    eligible_rows = [r for r in rows if any(p['eligible'] and p['task'] == r['task'] and
                     p['repeat'] == r['repeat'] for p in pairs)]
    totals = {arm: {k: sum(r['metrics'][k] for r in eligible_rows if r['arm'] == arm)
                    for k in METRICS} for arm in ('off', 'on')}
    aggregate = {k: savings(totals['off'][k], totals['on'][k]) for k in METRICS}
    return {'pairs': pairs, 'eligible_pairs': sum(p['eligible'] for p in pairs),
            'total_pairs': len(pairs), 'all_quality_pass': bool(pairs) and all(p['eligible'] for p in pairs),
            'eligible_totals': totals, 'eligible_savings': aggregate,
            'eligible_cache_hit_ratio': {arm: totals[arm]['cached_input_tokens'] / totals[arm]['input_tokens']
                                        if totals[arm]['input_tokens'] else None for arm in totals},
            'claim': 'candidate efficiency improvement; review task oracles and paired variance'
                     if pairs and all(p['eligible'] for p in pairs) and (aggregate['total_tokens'] or 0) > 0
                     else 'no quality-preserving efficiency claim'}


def validate_manifest(config):
    if not config.get('model') or not config.get('reasoning_effort'):
        raise ValueError('model and reasoning_effort must be explicit')
    if type(config.get('repeats')) is not int or config['repeats'] < 1:
        raise ValueError('repeats must be a positive integer')
    if not config.get('tasks'):
        raise ValueError('tasks required')
    ids = set()
    for task in config['tasks']:
        if not task.get('id') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in task['id']) or task['id'] in ids:
            raise ValueError('unique filesystem-safe task ids required')
        ids.add(task['id'])
        if task.get('category') not in CATEGORIES:
            raise ValueError('unknown category')
        if not task.get('prompt') or '$token-scope-tightener' in task['prompt']:
            raise ValueError('common prompt required, without Skill invocation')
        if not task.get('checks') or not task.get('oracle'):
            raise ValueError('every task requires independent checks and a correctness oracle')
        if not isinstance(task['oracle'], str):
            raise ValueError('oracle must name an external Python verifier file')
        for argv in [*task['checks'], *task.get('setup', [])]:
            if not isinstance(argv, list) or not argv or not all(isinstance(v, str) for v in argv):
                raise ValueError('commands must be nonempty argv arrays, not shell strings')
        for scope in task.get('allowed_changes', []):
            if not scope or scope.startswith('/') or '..' in Path(scope).parts:
                raise ValueError('allowed_changes must be repository-relative paths')
        if task['category'] == 'code_review' and task.get('allowed_changes'):
            raise ValueError('code_review must have empty allowed_changes')


def run(config, output, codex, auth_home, skill_root):
    validate_manifest(config)
    repo = Path(config['repo']).resolve()
    ref = git(repo, 'rev-parse', config['revision'] + '^{commit}')
    # Dedicated evaluation user recommended; fail closed on common external contamination.
    if (Path.home() / '.agents' / 'skills').exists():
        raise ValueError('use a dedicated OS evaluation user without ~/.agents/skills')
    if output == repo or repo in output.parents:
        raise ValueError('output must be outside the business repository')
    output.mkdir(parents=True, exist_ok=False)
    binary = shutil.which(codex)
    if not binary:
        raise ValueError('Codex CLI not found')
    version = subprocess.check_output([binary, '--version']).decode().strip()
    if version != config.get('expected_cli_version'):
        raise ValueError('expected_cli_version must exactly match codex --version; pin the tested CLI')
    skill_files = [skill_root / 'SKILL.md', *sorted((skill_root / 'references').glob('*.md'))]
    skill_hash = digest(b''.join(str(p.relative_to(skill_root)).encode() + p.read_bytes() for p in skill_files))
    oracle_sources = {}
    for task in config['tasks']:
        verifier = Path(task['oracle']).resolve()
        if verifier == repo or repo in verifier.parents:
            raise ValueError('oracle must live outside the agent repository')
        oracle_sources[task['id']] = verifier.read_bytes()
    manifest = {**config, 'resolved_revision': ref, 'cli_version': version,
                'cli_sha256': digest(Path(binary).read_bytes()), 'skill_sha256': skill_hash,
                'adapter': 'codex-exec-json',
                'oracle_hashes': {k: digest(v) for k, v in oracle_sources.items()}, 'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    write_json(output / 'manifest.json', manifest)
    rng = random.Random(config.get('seed', 0))
    rows = []
    for task in config['tasks']:
        first = rng.choice(['off', 'on'])
        for repeat in range(config['repeats']):
            order = [first, 'on' if first == 'off' else 'off']
            if repeat % 2:
                order.reverse()
            for arm in order:
                dest = output / f"{task['id']}-{repeat}-{arm}"
                dest.mkdir()
                with tempfile.TemporaryDirectory(prefix='scope-ab-') as tmp:
                    root = Path(tmp)
                    work, home = root / 'workspace', root / 'codex-home'
                    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', '--no-local', str(repo), str(work)], check=True)
                    git(work, 'checkout', '--quiet', '--detach', ref)
                    if git(work, 'ls-files', '.gitmodules'):
                        raise ValueError('submodules require a separately materialized fixture')
                    for p in work.rglob('*'):
                        if p.name == 'SKILL.md' or (p.name == 'config.toml' and p.parent.name == '.codex'):
                            raise ValueError(f'remove repo Skill/config contamination from fixture: {p.relative_to(work)}')
                        if p.name == 'AGENTS.md' and 'token-scope-tightener' in p.read_text(errors='replace'):
                            raise ValueError('always-on tightener in AGENTS.md contaminates control')
                    home.mkdir(mode=0o700)
                    # Never copy user config/plugins/memories, or persist auth in results.
                    auth = auth_home / 'auth.json'
                    if auth.is_file():
                        shutil.copyfile(auth, home / 'auth.json')
                        (home / 'auth.json').chmod(0o600)
                    installed = home / 'skills' / 'token-scope-tightener'
                    installed.mkdir(parents=True)
                    for p in skill_files:
                        target = installed / p.relative_to(skill_root)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(p, target)
                    env = os.environ.copy()
                    env['CODEX_HOME'] = str(home)
                    setup = [execute(argv, work, env, config.get('timeout_seconds', 600), dest / f'setup-{i}')
                             for i, argv in enumerate(task.get('setup', []))]
                    if any(x['exit_code'] or x['timed_out'] for x in setup):
                        raise ValueError('fixture setup failed; inspect setup logs')
                    verifier = root / 'verifier.py'
                    verifier.write_bytes(oracle_sources[task['id']])
                    before = snapshot(work)
                    prompt = task['prompt']
                    if arm == 'on':
                        prompt = 'Use $token-scope-tightener.\n\n' + prompt
                    (dest / 'prompt.txt').write_text(prompt)
                    argv = [binary, '-a', 'never', '-c', 'skills.bundled.enabled=false',
                            '-c', 'features.memories=false', '-c', 'features.multi_agent=false',
                            '-c', 'skills.config=[{name="token-scope-tightener",enabled=' + str(arm == 'on').lower() + '}]',
                            '-c', 'model_reasoning_effort=' + json.dumps(config['reasoning_effort']),
                            'exec', '--json', '--ephemeral', '--model', config['model'],
                            '--sandbox', 'workspace-write', '-']
                    execution = execute(argv, work, env, config.get('timeout_seconds', 600), dest / 'agent', prompt)
                    parsed = parse_events(dest / 'agent.stdout')
                    response = dest / 'response.txt'
                    response.write_text(parsed['final_response'])
                    # Capture agent state BEFORE validator writes build/coverage artifacts.
                    after = snapshot(work)
                    modifications = changed(before, after)
                    for name in modifications:
                        source = work / name
                        if source.is_file() and not source.is_symlink():
                            target = dest / 'modified-files' / name
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(source.read_bytes())
                    (dest / 'changes.patch').write_bytes(subprocess.check_output(['git', '-C', str(work), 'diff', '--binary', ref]))
                    write_json(dest / 'file-hashes.json', {'before': before, 'after': after})
                    env['AB_RESPONSE_FILE'] = str(response.resolve())
                    env['AB_RESULT_DIR'] = str(dest.resolve())
                    checks = [execute(argv, work, env, config.get('check_timeout_seconds', 300), dest / f'check-{i}')
                              for i, argv in enumerate(task['checks'])]
                    oracle = execute([sys.executable, str(verifier)], work, env, config.get('check_timeout_seconds', 300), dest / 'oracle')
                    outside = [p for p in modifications if not in_scope(p, task.get('allowed_changes', []))]
                    seconds = sum(c['seconds'] for c in checks) + oracle['seconds']
                    metrics = {**parsed['metrics'], 'agent_seconds': execution['seconds'],
                               'validation_seconds': seconds, 'elapsed_seconds': execution['seconds'] + seconds,
                               'modified_file_count': len(modifications)}
                    quality = (execution['exit_code'] == 0 and not execution['timed_out'] and parsed['usage_valid']
                               and not parsed['errors'] and bool(parsed['final_response']) and not outside
                               and all(c['exit_code'] == 0 and not c['timed_out'] for c in [*checks, oracle]))
                    row = {'task': task['id'], 'category': task['category'], 'repeat': repeat, 'arm': arm,
                           'quality_pass': bool(quality), 'fixture_sha256': digest(json.dumps(before, sort_keys=True).encode()), 'metrics': metrics, 'execution': execution,
                           'checks': checks, 'oracle': oracle, 'modified_files': modifications,
                           'out_of_scope': outside, 'telemetry': parsed, 'setup': setup}
                    rows.append(row)
                    write_json(dest / 'result.json', row)
                    write_json(output / 'runs.json', rows)
                    summary = report(rows)
                    write_json(output / 'summary.json', summary)
    lines = ['# Paired A/B results', '', summary['claim'], '',
             f"Eligible pairs: {summary['eligible_pairs']}/{summary['total_pairs']}", '',
             '| Task | Repeat | Eligible | Quality regression | Total token saving |',
             '|---|---:|---|---|---:|']
    for p in summary['pairs']:
        value = p['savings']['total_tokens']
        lines.append(f"| {p['task']} | {p['repeat']} | {p['eligible']} | {p['quality_regression']} | " +
                     (f'{value:.1%}' if value is not None else 'N/A') + ' |')
    lines += ['', 'All resource metrics and eligible-only totals are in summary.json.',
              'Cache tokens are a subset of input. Retry metric = repeated exact commands, not hypothesis retries.',
              'No Desktop compatibility or monetary-cost claim is established by this report.']
    (output / 'summary.md').write_text('\n'.join(lines) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--auth-home', type=Path, default=Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
    args = parser.parse_args()
    config = json.loads(args.manifest.read_text())
    # Resolve repository relative to manifest, never implicitly against caller cwd.
    config['repo'] = str((args.manifest.resolve().parent / config['repo']).resolve())
    for task in config['tasks']:
        task['oracle'] = str((args.manifest.resolve().parent / task['oracle']).resolve())
    summary = run(config, args.output.resolve(), args.codex, args.auth_home.resolve(), Path(__file__).resolve().parents[1])
    print(json.dumps({'output': str(args.output.resolve()), 'claim': summary['claim']}))
    return 0 if summary['all_quality_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
