# Acceptance Baseline

Use this file when you want to verify that `token-scope-tightener` is functioning as a real bottom-layer capability instead of only sounding good in prompts.

## Goal

Judge whether the skill measurably improves execution on real repository tasks by reducing:

- viewed scope
- unnecessary follow-up questions
- unrelated edits
- repeated retries
- output drift from the requested format

## Core Metrics

Track these five metrics for each task:

1. `viewed_scope`
   Count the number of files or directories inspected before the first meaningful change or answer.
2. `follow_up_questions`
   Count how many user questions were asked before work meaningfully progressed.
3. `unrelated_changes`
   Count files modified outside the justified task scope.
4. `retry_loops`
   Count repeated attempts under the same hypothesis.
5. `output_contract_match`
   Mark `yes` only when the final answer follows the requested report fields and order.

## Acceptance Targets

For a representative batch, the skill passes if most tasks meet all of these:

- `viewed_scope` stays within the named scope plus at most one justified hop
- `follow_up_questions` is `0` for straightforward tasks
- `unrelated_changes` is `0`
- `retry_loops` does not exceed `2` under the same hypothesis
- `output_contract_match` is `yes`

If a task fails one metric for a good reason, record the reason explicitly instead of forcing a pass.

## Representative Task Set

Use at least one task from each relevant category:

- precise bug fix in a named directory
- small feature in a named component or page
- small refactor with behavior unchanged
- targeted performance issue
- test-only task with business logic frozen
- code review with severity ordering
- code explanation limited to a local module
- large-repo precise edit starting from named entry files

For the first real evaluation pass, use `references/first-run-eval.md` to keep the sample set and scoring flow consistent.

## Suggested Chinese Evaluation Prompts

Use prompts similar to these so the evaluation matches the intended workflow:

```text
请在仅限 src/auth/ 和 tests/auth/ 内修复登录时偶发空指针报错，不要改 API 返回结构和其他业务模块，优先定位根因并做最小修复，避免无关重构，最后输出：根因、修改文件、修复点、测试结果、风险点。
```

```text
请在仅限 src/components/cart/ 和 src/pages/checkout.tsx 内实现购物车商品数量上限提示，不要修改支付流程和后端接口，优先复用现有提示组件，采用最小范围改动完成需求，最后输出：修改文件、实现摘要、验收情况、风险点。
```

```text
请只从 src/billing/invoice.ts 和 src/billing/formatter.ts 开始，在必要时再扩展到直接相关文件，完成发票金额格式错误的修复；不要扫描整个仓库，不要修改税务计算逻辑，优先基于现有实现做最小改动，最后输出：实际查看范围、修改文件、改动摘要、测试结果、风险点。
```

## Recording Sheet

Copy this sheet for each task:

```text
task_name:
task_type:
named_scope:
actual_viewed_scope:
follow_up_questions:
unrelated_changes:
retry_loops:
output_contract_match:
validation_ran:
pass_or_fail:
notes:
```

## Batch Review Rule

After 5 to 8 representative tasks:

- pass if at least 80% of tasks pass all core metrics
- review if failures cluster around one pattern such as broad scans or output drift
- revise the skill if the same failure pattern appears in 2 or more tasks

## Common Failure Patterns

- broad scan before reading the named files
- asking clarifying questions for minor details that could have been inferred
- expanding to unrelated modules without direct evidence
- modifying helper files that were not required
- answering in a generic summary instead of the requested fixed format
- retrying the same approach with only small wording or parameter changes

## What To Change If It Fails

- broad scan failures -> tighten `Expansion Gate` and `Scope Expansion Ladder`
- too many follow-up questions -> strengthen `Input Repair Rules`
- unrelated diffs -> strengthen `No-touch` extraction and final self-check
- retry loops -> strengthen `Retry Budget`
- output drift -> strengthen `Output Control Rules`

## Minimal Success Claim

Do not claim this skill is a true bottom-layer capability until it has passed a representative batch on real tasks, not just synthetic examples.
