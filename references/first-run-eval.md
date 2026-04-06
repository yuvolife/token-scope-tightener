# First Run Evaluation Pack

Use this file for the first real validation round after enabling `token-scope-tightener` as an always-on preflight rule.

## Purpose

Run a small but representative batch so you can quickly tell whether the skill is behaving like a real bottom-layer capability.

This pack is intentionally lightweight:

- 5 tasks
- 1 pass/fail sheet per task
- 1 short summary at the end

## Before You Start

- Open a new session if you recently changed global rules.
- Use the same model and similar environment for all 5 tasks.
- Do not manually remind the agent about every metric during the run unless the template explicitly includes it.
- Prefer real tasks from your current repo over synthetic toy tasks.

## Suggested Run Order

1. precise bug fix
2. small feature
3. test-only task
4. code review
5. large-repo precise edit

This order gives a fast read on scope control, implementation restraint, output discipline, and large-repo behavior.

## Task 1: Precise Bug Fix

Replace bracket content with a real local task:

```text
使用 $token-scope-tightener，请在仅限 [相关文件/目录] 内修复 [具体 bug/报错/异常现象]，不要改动 [禁止修改项]，优先定位根因并做最小修复，避免无关重构，最后输出：根因、修改文件、修复点、测试结果、风险点。
```

Primary things to observe:

- 是否先看命名文件
- 是否很快形成根因假设
- 是否避免顺手大改

## Task 2: Small Feature

```text
使用 $token-scope-tightener，请在仅限 [相关文件/目录] 内实现 [具体功能]，不要改动 [禁止修改项]，优先复用现有逻辑和组件，采用最小范围改动完成需求，最后输出：修改文件、实现摘要、验收情况、风险点。
```

Primary things to observe:

- 是否优先复用现有实现
- 是否控制变更范围
- 是否按验收格式汇报

## Task 3: Test-Only Task

```text
使用 $token-scope-tightener，请在仅限 [测试文件/相关模块] 内为 [函数/模块/缺陷场景] 补充测试，不要改动业务逻辑，优先覆盖关键路径和边界条件，最后输出：新增测试点、涉及文件、覆盖范围、未覆盖风险。
```

Primary things to observe:

- 是否避免越界改业务代码
- 是否先补关键路径
- 是否输出覆盖范围而不是泛泛总结

## Task 4: Code Review

```text
使用 $token-scope-tightener，请在仅限 [相关文件/目录] 内审查 [功能/模块]，重点检查 [正确性/边界条件/并发/安全/可维护性]，不要直接大改代码，先给出问题清单并按严重程度排序，最后输出：问题、位置、影响、建议修复方式。
```

Primary things to observe:

- 是否 findings first
- 是否按严重程度排序
- 是否避免直接改代码

## Task 5: Large-Repo Precise Edit

```text
使用 $token-scope-tightener，请只从 [入口文件/目录] 开始，在必要时再扩展到直接相关文件，完成 [具体任务]；不要扫描整个仓库，不要修改 [禁止修改项]，优先基于现有实现做最小改动，最后输出：实际查看范围、修改文件、改动摘要、测试结果、风险点。
```

Primary things to observe:

- 是否从入口文件开始
- 是否只扩展到一跳相关文件
- 是否避免广撒网式搜索

## Recording Sheet

Copy one block per task:

```text
task_name:
task_type:
named_scope:
actual_viewed_scope:
first_files_opened:
follow_up_questions:
unrelated_changes:
retry_loops:
output_contract_match:
validation_ran:
pass_or_fail:
notes:
```

## Lightweight Scoring

For each task, mark `pass` only if all of these are true:

- actual scope stayed within named scope plus justified local expansion
- no unnecessary follow-up question was asked
- no unrelated file was modified
- no repeated loop exceeded the retry budget
- final output matched the requested format

## End-of-Batch Summary

After all 5 tasks, write one short summary:

```text
first_run_date:
tasks_run:
passed:
failed:
main_failure_pattern:
recommended_skill_adjustment:
is_ready_for_daily_use:
```

## Decision Rule

- `5/5 pass`: ready for daily use
- `4/5 pass`: usable, but revise the dominant failure pattern soon
- `3/5 or below`: do not treat it as a true bottom-layer capability yet

## Assumption Note

This pack assumes you will substitute real tasks from your own repository. If you test on artificial toy tasks only, the result is weaker and should not be treated as final validation.
