# Brief Schema

Use this file when the task is complex enough that the scope-tightening pass should produce a stable internal brief before execution.

## Standard Fields

Required:

- `scope`: named files, directories, entry points, or explicit bounds
- `task_type`: bugfix, feature, refactor, optimization, test, review, explanation
- `goal`: the concrete user outcome inside the chosen scope
- `no_touch`: modules, APIs, workflows, or behaviors that must not change
- `strategy`: minimal diff, reuse existing logic, avoid broad scans, avoid unrelated refactors
- `output_contract`: final report headings, ordering, and desired verbosity

Optional when needed:

- `validation`: smallest relevant check needed before claiming success
- `expansion_rule`: when it is acceptable to inspect one-hop related files
- `assumptions`: minor inferred details that do not justify a blocking question
- `routing_hint`: whether another skill or workflow should be loaded after the brief is stable

## Compact Template

```text
scope:
task_type:
goal:
no_touch:
strategy:
output_contract:
validation:
expansion_rule:
assumptions:
routing_hint:
```

## Short Internal Form

When the task is simple, compress the same structure into one line:

```text
Only in [scope], do [goal], do not change [no_touch], prefer [strategy], validate with [validation], report [output_contract].
```

## Example: Bug Fix

```text
scope: src/auth/, tests/auth/
task_type: bugfix
goal: fix intermittent null-pointer during login
no_touch: API response shape, unrelated business modules
strategy: root-cause first, minimal fix, no broad refactor
output_contract: 根因、修改文件、修复点、测试结果、风险点
validation: run the auth tests most directly related to login
expansion_rule: inspect one-hop imported helper only if the root cause is not local
assumptions: the failure is in local login flow, not remote API contract
routing_hint: none unless framework-specific tooling is clearly needed
```

## Example: Large-Repo Precise Edit

```text
scope: start from src/billing/invoice.ts and src/billing/formatter.ts
task_type: bugfix
goal: fix invoice amount formatting error
no_touch: tax calculation logic
strategy: inspect the entry files first, expand only to direct dependencies
output_contract: 实际查看范围、修改文件、改动摘要、测试结果、风险点
validation: run the smallest billing formatter test or equivalent check
expansion_rule: one-hop dependency only, based on direct evidence
assumptions: the formatting fault is presentation-side, not calculation-side
routing_hint: none
```
