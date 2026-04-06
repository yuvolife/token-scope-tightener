# Personal Use Templates

Use these as your default copy-paste prompts for daily work. They are optimized for a Chinese workflow and assume `$token-scope-tightener` is your preflight layer.

## 1. Default Daily Template

Use this when the task is local and the scope is already known.

```text
请在仅限 [范围] 内完成 [任务]，不要改 [禁止项]，优先最小改动、复用现有实现、避免无关扫描和重构，最后输出：修改文件、改动摘要、测试结果、风险点。
```

## 2. Explicit Forced Template

Use this when you want to force the preflight behavior and make the skill visible in the prompt.

```text
使用 $token-scope-tightener，请在仅限 [范围] 内完成 [任务]，不要改 [禁止项]，先收口范围和输出格式，再以最小改动推进，避免无关扫描、无关重构和重复重试，最后输出：修改文件、改动摘要、测试结果、风险点。
```

## 3. Large-Repo Precise Template

Use this when the repository is large and you want to avoid broad discovery.

```text
使用 $token-scope-tightener，请只从 [入口文件/目录] 开始，在必要时再扩展到直接相关文件，完成 [任务]；不要扫描整个仓库，不要修改 [禁止项]，优先基于现有实现做最小改动，最后输出：实际查看范围、修改文件、改动摘要、测试结果、风险点。
```

## Quick Fill Guide

- `[范围]`: specific file, directory, or a very small module set
- `[任务]`: bug fix, feature, refactor, optimization, test, review, explanation
- `[禁止项]`: API shape, payment flow, data model, unrelated business module, or any other no-touch area

## Suggested Habit

- Daily default -> use Template 1
- Need stronger enforcement -> use Template 2
- Large repo or expensive context -> use Template 3
