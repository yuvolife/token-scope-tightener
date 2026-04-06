# Escalation Gates

Use this file when the task may need clarification or a switch from direct execution into `plan/spec`.

## Clarification Gate

Ask a follow-up question only if the missing information would materially change one of these:

- implementation direction
- scope boundary
- no-touch constraints
- acceptance criteria
- risk level

Do not ask when the detail can be inferred safely from local context or when it only affects a minor implementation choice.

## Plan/Spec Gate

Switch to `plan/spec` when one or more are true:

- the task spans multiple modules or subsystems
- the order of work is non-obvious
- the change has meaningful regression risk
- the acceptance path is unclear
- multiple reasonable implementations have non-trivial tradeoffs
- the user explicitly asks for a plan, spec, or staged execution

Stay in direct execution mode when the task is local, bounded, and the next action is obvious.

## Direct Execution Gate

Stay in direct execution mode when:

- scope is named and small
- the user wants a concrete fix or answer now
- the likely solution is one local change or one short reading pass
- validation is straightforward

## Example Judgments

- local bug fix in one folder -> direct execution
- app-wide auth refactor -> `plan/spec`
- unclear feature request with several UX options -> clarify first, then likely `plan/spec`
- review of a small named module -> direct execution
- large-repo issue with uncertain ownership -> brief first, then decide whether to clarify or move to `plan/spec`

## Minimal Rule

Default to direct execution after scope-tightening. Escalate only when doing so clearly improves correctness or risk handling.
