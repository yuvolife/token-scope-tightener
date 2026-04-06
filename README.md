# token-scope-tightener

Preflight scope-tightening skill for Codex-style repository work.

This skill reduces wasted token usage by forcing a narrow execution brief before broad exploration. It is designed for requests such as limited-file edits, minimal diffs, concise output, fewer retries, and "do not refactor unrelated code".

## What It Does

Before deeper execution, the skill extracts:

- Scope
- Task
- No-touch zone
- Preferred strategy
- Output contract

It then compresses the request into a brief like:

`Only in [scope], do [task], do not change [no-touch], prefer [strategy], report [output contract].`

## When To Use

Use this skill when you want the assistant to:

- start from the narrowest named file or directory
- avoid scanning the whole repository up front
- prefer minimal changes and reuse existing logic
- avoid unrelated refactors
- keep answers short and structured
- ask clarifying questions only when they would materially change the implementation direction

It is especially useful for bug fixes, small refactors, targeted reviews, precise feature work, and large repositories where context discipline matters.

## Repository Layout

```text
.
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- acceptance-baseline.md
|   |-- always-on-snippet.md
|   |-- brief-schema.md
|   |-- escalation-gates.md
|   |-- execution-guardrails.md
|   |-- first-run-eval.md
|   |-- personal-use-templates.md
|   |-- prompt-templates.md
|   `-- session-window-gate.md
|-- LICENSE
`-- README.md
```

## Files

- `SKILL.md`: main skill definition and routing rules
- `agents/openai.yaml`: lightweight metadata for agent-facing invocation
- `references/`: supporting guidance, templates, evaluation pack, and guardrails

## Installation

Clone or copy this repository into your Codex skills directory so the final path becomes:

```text
~/.codex/skills/token-scope-tightener/
```

Example:

```bash
git clone https://github.com/yuvolife/token-scope-tightener.git ~/.codex/skills/token-scope-tightener
```

## Usage

Invoke it explicitly:

```text
Use $token-scope-tightener before touching the repo. Keep the diff minimal and avoid unrelated refactors.
```

Or make it part of your persistent workflow by referencing the included always-on snippet in `references/always-on-snippet.md`.

## Notes

- The skill is intentionally lightweight: tighten scope first, then decide whether another domain-specific skill is actually needed.
- The repository includes evaluation and prompt-template references so the skill can be validated and adapted without changing the core `SKILL.md`.

## Maintainer

- GitHub: [yuvolife](https://github.com/yuvolife)
- Email: [yuvolife@qq.com](mailto:yuvolife@qq.com)
- Bio: 在局里看见生活的真实，在局外寻找自己的答案。

## License

Released under the MIT License. See `LICENSE`.
