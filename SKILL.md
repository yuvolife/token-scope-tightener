---
name: "token-scope-tightener"
description: "Reduce wasted token usage by acting as a preflight scope-tightening and routing layer before execution. Use when the user asks for limited file or directory scope, minimal edits, fewer scans or retries, fixed output sections, concise answers, or phrases such as '仅限', '最小改动', '少扫描', '不要无关重构', '固定输出格式', '信息不足先合理判断并继续', or '收口'. Also use when the request is broad, noisy, or underspecified and the input or expected output should be tightened before execution, especially before invoking domain-specific skills."
---

# Token Scope Tightener

Treat token budget as a hard constraint. Use this skill as a thin preflight and routing layer for repository work: tighten scope first, then decide whether deeper planning, clarification, or another skill is actually needed.

## Core Loop

Extract these fields first:

- Scope: files, directories, entry points, or explicit boundaries
- Task: bug fix, feature, refactor, optimization, test, review, or explanation
- No-touch zone: files, modules, APIs, behaviors, or workflows that must not change
- Preferred strategy: minimal diff, reuse existing logic, avoid broad scans, avoid unrelated refactors
- Output contract: required report fields, ordering, and answer length

Compress the request into one execution brief:

`Only in [scope], do [task], do not change [no-touch], prefer [strategy], report [output contract].`

Then follow this order:

- Build the execution brief before broad exploration or long explanation.
- Start from the narrowest named file or directory.
- Expand only by direct evidence and only one hop at a time.
- Prefer minimal changes and reuse before inventing new structure.
- Match the user's requested output shape; if none is given, use the shortest useful structure.

## Decision Gates

- Clarification gate: ask only if the missing information would materially change implementation direction.
- Plan/spec gate: switch to `plan/spec` when the task spans multiple modules, has non-obvious sequencing, carries meaningful risk, or lacks a clear acceptance path.
- Session-window gate: suggest a fresh session when the current thread has become bloated, drifted across topics, or requires repeated recap before useful work can continue.
- Routing gate: load another skill only if it materially improves execution after the brief is stable.
- Retry gate: under the same hypothesis, try at most 2 times before changing the hypothesis.
- Bypass gate: skip the full protocol for casual chat, pure translation, rewriting user-provided text, or explicitly broad brainstorming.

## Always-On Use

When this skill is used from a global or persistent instruction, run the preflight silently before the first tool call or long explanation. Do not announce the full brief unless it helps the user.

## Reference Map

Read only what is needed:

- `references/brief-schema.md`: standard execution brief schema, field definitions, and compact examples
- `references/escalation-gates.md`: when to ask clarifying questions, when to escalate to `plan/spec`, and when to stay in direct execution mode
- `references/session-window-gate.md`: when to recommend a fresh session, how to hand off context, and how to include a current thread link when available
- `references/execution-guardrails.md`: retry budget, scope expansion ladder, validation floor, routing rules, and bypass cases
- `references/acceptance-baseline.md`: acceptance metrics, representative task set, scoring sheet, and pass thresholds for validating real-world impact
- `references/first-run-eval.md`: a ready-to-run first evaluation pack with 5 task slots, run order, and a lightweight scoring routine
- `references/personal-use-templates.md`: three copy-paste Chinese prompts for your daily default, explicit, and large-repo workflows
- `references/prompt-templates.md`: compact templates for bug fixes, features, small refactors, performance work, tests, reviews, explanations, precise large-repo edits, and shortest-form prompts
- `references/always-on-snippet.md`: short persistent-prompt snippet for forcing a scope-tightening pass before execution
