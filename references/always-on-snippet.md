# Always-On Snippet

Use this file when you want `token-scope-tightener` to behave like a persistent preflight rule instead of an occasional task skill.

## 推荐中文常驻版

```text
在开始任何工作前，始终先应用 $token-scope-tightener：先把请求收口为范围、任务、禁止改动项、优先策略和输出格式；从最小命名文件或目录开始；避免全仓扫描、无关重构和重复重试；只有当缺失信息会明显改变实现方向时才追问；最终按用户要求的简洁格式输出。
```

## 中文极短版

```text
始终先应用 $token-scope-tightener：先收口范围，少扫描，少重试，最小改动，避免无关工作，并按要求的简洁格式输出。
```

## 中文强约束版

```text
把 token 预算视为硬约束。任何探索、搜索或修改前，先应用 $token-scope-tightener；除非有直接证据表明必须扩展到一跳相关文件，否则不要超出用户指定范围。
```

## Recommended Global Snippet

```text
Before doing any work, always apply $token-scope-tightener: first compress the request into scope, task, no-touch constraints, preferred strategy, and output contract; start from the narrowest named files or directories; avoid repo-wide scanning, unrelated refactors, and repeated retries; ask follow-up questions only if the missing information would materially change the implementation direction; answer in the user's requested concise format.
```

## Ultra-Short Variant

```text
Always apply $token-scope-tightener first: narrow the scope, minimize scanning, keep changes small, avoid unrelated work, and answer in the requested concise format.
```

## Stronger Variant

```text
Treat token budget as a hard constraint. Before any exploration or edits, apply $token-scope-tightener and do not expand beyond the named scope unless direct evidence shows a one-hop dependency is required.
```

## Placement Note

对于中文工作流，优先使用上面的中文版本并放进你的 persistent system prompt、memory 或 always-on instruction。推荐中文常驻版最均衡；极短版更省 token；强约束版更适合大仓库和高频编码场景。
