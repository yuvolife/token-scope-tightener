# Execution Guardrails

Use this file when the task is likely to sprawl, loop, or accidentally expand beyond the requested scope.

## Retry Budget

- Same hypothesis: at most 2 tries
- Third attempt must change the hypothesis, not just the parameter or wording
- After 2 failed hypotheses, stop expanding blindly and state the current boundary
- Prefer one targeted search or one direct file read over several vague retries

## Scope Expansion Ladder

Expand in this order and stop as soon as the evidence is sufficient:

1. named file or directory from the user
2. paired test, fixture, or helper in the same local area
3. directly imported or directly called dependency
4. one-hop related file discovered through concrete evidence

Do not skip straight to repo-wide scans unless the user explicitly asked for broad investigation.

## Validation Floor

Before claiming completion, do the smallest relevant validation:

- bugfix -> targeted test or smallest reproducer
- feature -> focused functional check
- refactor -> behavior-equivalent check
- review -> findings with exact locations
- explanation -> concrete entry point and flow references

If validation cannot run, say so briefly and state why.

## Routing Rules

Run this skill first for repository work, then load only the minimum extra skill set that materially improves execution.

Examples:

- Vue task -> scope-tighten first, then Vue skill
- test-writing task -> scope-tighten first, then testing skill
- simple local fix -> often no extra skill is needed

## Bypass Cases

Do not force the full protocol for:

- casual chat
- pure translation
- rewriting user-provided text
- broad brainstorming explicitly requested by the user

Keep the concise-output intent, but skip the heavier preflight behavior.

## Success Signals

The skill is working as intended when:

- the viewed file range stays narrow
- follow-up questions decrease
- unrelated edits decrease
- repeated retries decrease
