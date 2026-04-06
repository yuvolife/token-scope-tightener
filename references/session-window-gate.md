# Session Window Gate

Use this file when you need to decide whether the current thread is too bloated to remain the best place for the next task.

## When To Recommend a Fresh Session

Recommend a new session when one or more are true:

- the thread has drifted across multiple unrelated tasks
- useful progress now requires repeated recap of old context
- the working set is much larger than the next task needs
- the user is asking for a clean restart, reframe, or re-planning pass
- the app or visible context suggests the thread is nearing compaction or feels crowded

Do not recommend a fresh session just because the thread is long. Recommend it only when the current thread is now making the next step less efficient or less accurate.

## What To Say

Keep the suggestion short and actionable:

- say that the current thread has become heavy or mixed
- recommend opening a fresh session for the next phase
- explain in one sentence what should be carried over

## Thread Link Rule

If the current thread link is available from the user, app context, or other reliable local context, include it as:

```text
codex://threads/<thread-id>
```

Do not invent a thread link.

If the exact link is not available, say briefly that the user can attach the current thread link as supplemental context in the new session.

## Suggested Handoff Format

```text
建议切到新会话继续下一阶段，因为当前会话已经偏重 / 混入了多段历史上下文。
新会话首条消息建议带上：下一阶段目标、明确范围、禁止改动项、验收格式。
补充上下文：codex://threads/<thread-id>
```

If no link is available:

```text
建议切到新会话继续下一阶段，因为当前会话已经偏重 / 混入了多段历史上下文。
新会话首条消息建议带上：下一阶段目标、明确范围、禁止改动项、验收格式。
如有需要，请把当前会话链接一并附上作为补充上下文。
```

## Minimal Rule

Prefer staying in the current thread when it is still helping. Recommend a new session only when the thread has become a cost instead of an asset.
