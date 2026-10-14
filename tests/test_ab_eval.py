"""Offline tests. Synthetic telemetry is test input, never an efficiency benchmark."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('ab_eval', Path(__file__).resolve().parents[1] / 'tools/ab_eval.py')
ab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ab)


class EvaluationTests(unittest.TestCase):
    def parse(self, events):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'events'
            p.write_text('\n'.join(json.dumps(e) if not isinstance(e, str) else e for e in events))
            return ab.parse_events(p)

    def test_cache_is_subset_and_duplicate_items_are_not_retries(self):
        item = {'type': 'item.completed', 'item': {'id': '1', 'type': 'command_execution', 'command': 'pytest', 'exit_code': 0}}
        result = self.parse([item, item, {'type': 'item.completed', 'item': {**item['item'], 'id': '2'}},
                             {'type': 'turn.completed', 'usage': {'input_tokens': 100, 'cached_input_tokens': 70, 'output_tokens': 20}}])
        self.assertEqual(result['metrics']['total_tokens'], 120)
        self.assertEqual(result['metrics']['uncached_input_tokens'], 30)
        self.assertEqual(result['metrics']['repeated_commands'], 1)

    def test_unknown_usage_is_not_zero(self):
        for events in ([], ['bad-json'], [{'type': 'turn.completed', 'usage': {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0}}], [{'type': 'turn.completed', 'usage': {'input_tokens': 20}}],
                       [{'type': 'turn.completed', 'usage': {'input_tokens': 1, 'cached_input_tokens': 2, 'output_tokens': 1}}]):
            result = self.parse(events)
            self.assertFalse(result['usage_valid'])
            self.assertIsNone(result['metrics']['total_tokens'])

    def test_multiple_turns_are_rejected_in_single_turn_adapter(self):
        event = {'type': 'turn.completed', 'usage': {'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 1}}
        self.assertFalse(self.parse([event, event])['usage_valid'])

    def test_subagent_usage_rejected(self):
        self.assertTrue(self.parse([{'type': 'item.completed', 'item': {'type': 'collab_tool_call'}}])['errors'])

    def test_quality_regression_blocks_savings(self):
        rows = [{'task': 'a', 'repeat': 0, 'arm': arm, 'fixture_sha256': 'same',
                 'quality_pass': arm == 'off', 'metrics': {k: 10 for k in ab.METRICS}} for arm in ('on', 'off')]
        result = ab.report(rows)
        self.assertTrue(result['pairs'][0]['quality_regression'])
        self.assertIsNone(result['pairs'][0]['savings']['total_tokens'])
        self.assertEqual(result['eligible_pairs'], 0)

    def test_fixture_mismatch_blocks_savings(self):
        rows = [{'task': 'a', 'repeat': 0, 'arm': arm, 'fixture_sha256': arm,
                 'quality_pass': True, 'metrics': {k: 10 for k in ab.METRICS}} for arm in ('on', 'off')]
        self.assertEqual(ab.report(rows)['eligible_pairs'], 0)

    def test_zero_baseline_and_negative_savings(self):
        self.assertIsNone(ab.savings(0, 10))
        self.assertEqual(ab.savings(10, 20), -1)

    def test_scope_directory_boundary(self):
        self.assertTrue(ab.in_scope('src/a.py', ['src/']))
        self.assertFalse(ab.in_scope('src-other/a.py', ['src/']))

    @unittest.skipUnless(os.name == 'posix', 'fixture executable uses POSIX shebang')
    def test_end_to_end_five_categories_alternating_and_quality_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / 'repo'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / 'value.txt').write_text('old')
            (repo / '.gitignore').write_text('ignored.txt\n')
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture'], check=True)
            binary = root / 'fake-codex'
            binary.write_text('''#!/usr/bin/env python3
import json, sys
from pathlib import Path
if '--version' in sys.argv:
    print('TEST-ONLY fake-codex'); raise SystemExit
prompt = sys.stdin.read()
on = 'enabled=true' in ' '.join(sys.argv)
if 'review' not in prompt:
    Path('value.txt').write_text('fixed')
if 'fail-oracle' in prompt and on:
    Path('value.txt').write_text('wrong')
if 'out-of-scope' in prompt and on:
    Path('ignored.txt').write_text('new')
print(json.dumps({'type':'item.completed', 'item':{'id':'response','type':'agent_message','text':'fixed'}}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':30,'output_tokens':10}}))
''')
            binary.chmod(0o755)
            verifier = root / 'oracle.py'
            verifier.write_text("from pathlib import Path\nassert Path('value.txt').read_text() in ('old', 'fixed')\n")
            config = {'repo': str(repo), 'revision': 'HEAD', 'model': 'TEST-ONLY', 'reasoning_effort': 'high',
                      'expected_cli_version': 'TEST-ONLY fake-codex', 'repeats': 2, 'tasks': [{'id': category, 'category': category,
                       'prompt': 'review' if category == 'code_review' else 'fix value',
                       'allowed_changes': [] if category == 'code_review' else ['value.txt'],
                       'checks': [[os.sys.executable, '-c', 'pass']], 'oracle': str(verifier)}
                       for category in sorted(ab.CATEGORIES)]}
            with patch.object(ab.Path, 'home', return_value=root):
                result = ab.run(config, root / 'out', str(binary), root / 'auth', Path(__file__).resolve().parents[1])
                self.assertEqual(result['eligible_pairs'], 10)
                self.assertTrue(result['all_quality_pass'])
                rows = json.loads((root / 'out/runs.json').read_text())
                for category in ab.CATEGORIES:
                    orders = [[r['arm'] for r in rows if r['task'] == category and r['repeat'] == i] for i in (0, 1)]
                    self.assertEqual(orders[0], orders[1][::-1])
                config['repeats'] = 1
                config['tasks'] = [config['tasks'][0]]
                config['tasks'][0]['prompt'] = 'fail-oracle'
                failed = ab.run(config, root / 'failed', str(binary), root / 'auth', Path(__file__).resolve().parents[1])
                self.assertTrue(failed['pairs'][0]['quality_regression'])
                config['tasks'][0]['prompt'] = 'out-of-scope'
                self.assertFalse(ab.run(config, root / 'scope', str(binary), root / 'auth', Path(__file__).resolve().parents[1])['all_quality_pass'])
                config['tasks'][0]['checks'] = [[os.sys.executable, '-c', 'raise SystemExit(1)']]
                config['tasks'][0]['prompt'] = 'fix'
                self.assertFalse(ab.run(config, root / 'check', str(binary), root / 'auth', Path(__file__).resolve().parents[1])['all_quality_pass'])

    def test_timeout_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = ab.execute([os.sys.executable, '-c', 'import time; time.sleep(5)'], tmp, os.environ.copy(), .05, Path(tmp) / 'timeout')
            self.assertTrue(r['timed_out'])
            self.assertNotEqual(r['exit_code'], 0)

    def test_snapshot_includes_ignored_files_and_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', '-q', tmp], check=True)
            (root / '.gitignore').write_text('ignored\n')
            (root / 'ignored').write_text('yes')
            before = ab.snapshot(root)
            self.assertIn('ignored', before)
            (root / 'ignored').unlink()
            self.assertIn('ignored', ab.changed(before, ab.snapshot(root)))


if __name__ == '__main__':
    unittest.main()
