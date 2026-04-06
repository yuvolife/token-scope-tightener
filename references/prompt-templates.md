# Prompt Templates

Use this file only when the user wants a reusable prompt template or when a request needs to be rewritten into a tighter execution brief.

## Language Policy

- Chinese-first is intentional for this skill because the target workflow, trigger phrases, and prompt examples are mainly Chinese.
- Keeping this file in Chinese reduces duplication and keeps the reference cheaper to load.
- If the current request is mainly English, translate the template structure without changing the control logic: scope, task, no-touch constraints, preferred strategy, and output contract.
- Preserve the tightening intent even after translation. The wording can change; the structure should not.

## One-Line Universal Template

```text
请在仅限 [范围] 内完成 [任务]，不要改 [禁止项]，优先最小改动、复用现有实现、避免无关扫描和重构，最后输出：[固定格式]。
```

## Fix a Bug

```text
请在仅限 [相关文件/目录] 内修复 [具体 bug/报错/异常现象]，不要改动 [禁止修改项]，优先定位根因并做最小修复，避免无关重构，最后输出：根因、修改文件、修复点、测试结果、风险点。
```

## Implement a Feature

```text
请在仅限 [相关文件/目录] 内实现 [具体功能]，不要改动 [禁止修改项]，优先复用现有逻辑和组件，采用最小范围改动完成需求，最后输出：修改文件、实现摘要、验收情况、风险点。
```

## Small Refactor

```text
请在仅限 [相关文件/目录] 内对 [重复逻辑/可读性问题/结构问题] 做小规模重构，保证行为不变，不要扩大范围或顺带处理无关问题，优先减少重复并控制 diff，最后输出：重构前问题、具体改动、行为不变依据、验证结果。
```

## Performance Optimization

```text
请在仅限 [相关文件/目录] 内优化 [慢查询/渲染卡顿/重复计算]，不要改变对外行为和接口，优先找出主要瓶颈并做最小必要优化，最后输出：瓶颈位置、优化方式、涉及文件、验证结果、潜在副作用。
```

## Add Tests

```text
请在仅限 [测试文件/相关模块] 内为 [函数/模块/缺陷场景] 补充测试，不要改动业务逻辑，优先覆盖关键路径和边界条件，最后输出：新增测试点、涉及文件、覆盖范围、未覆盖风险。
```

## Review Code

```text
请在仅限 [相关文件/目录] 内审查 [功能/模块]，重点检查 [正确性/边界条件/并发/安全/可维护性]，不要直接大改代码，先给出问题清单并按严重程度排序，最后输出：问题、位置、影响、建议修复方式。
```

## Explain Code

```text
请在仅限 [相关文件/目录] 内解释 [模块/流程] 的实现方式，不要泛泛而谈，重点说明入口、主流程、关键状态和依赖关系，最后输出：入口文件、执行流程、关键函数、注意事项。
```

## Precise Large-Repo Edit

```text
请只从 [入口文件/目录] 开始，在必要时再扩展到直接相关文件，完成 [具体任务]；不要扫描整个仓库，不要修改 [禁止修改项]，优先基于现有实现做最小改动，最后输出：实际查看范围、修改文件、改动摘要、测试结果、风险点。
```

## Continue Without Frequent Questions

```text
信息不足时，请先基于现有代码做最合理判断并继续推进，不要为小问题频繁追问；只有当缺失信息会明显改变实现方向时，再在结果里指出。
```

## Shortest Combo

```text
请在仅限 [范围] 内完成 [任务]，不要改 [禁止项]，优先最小改动和复用现有实现，不要扫描无关代码，不要无关重构，最后输出：[固定格式]。
```
