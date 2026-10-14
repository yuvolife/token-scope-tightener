# Codex 用量与客户端兼容性核实

核实日期：2026-10-14 UTC / 2026-10-15 上海。

## 固定源码证据

- 本 Skill 基线：`2f37498087bb74bb072d80c850ad7996f3952d41`。
- OpenAI Codex main 核实提交：`76ed3b484d62ccceb9fa512ff4dd139f421814c3`。
- 下列链接使用固定提交，避免把之后的 main 变化当作本次证据。

| 源码 | 能证明的事实 |
|---|---|
| [thread_usage.rs](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/codex-rs/app-server-protocol/src/protocol/v2/thread_usage.rs) | `ThreadUsage` 是线程估算费用/credits 和分组用量结构；group 的输入、缓存、输出等为可选字段；不是 streaming notification 本体 |
| [Python mini CLI](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/sdk/python/examples/11_cli_mini_app/sync.py) | 接收 `ThreadTokenUsageUpdatedNotification`，保存最新的 `payload.token_usage`，区分 `last` 和 `total`，并验证 completion 与 usage 存在 |
| [exec_events.rs](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/codex-rs/exec/src/exec_events.rs) | JSONL `turn.completed.usage` 提供 input_tokens、cached_input_tokens、output_tokens，以及 cache_write/reasoning 字段；命令事件包含 command/exit_code |
| [JSONL processor](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/codex-rs/exec/src/event_processor_with_jsonl_output.rs) | 从最新通知的 `usage.total` 生成 exec completion；缺失时使用默认 Usage。因此新线程单轮只取一次，不累加累计快照，不使用 resume |
| [skills_config.rs](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/codex-rs/config/src/skills_config.rs) | 支持 `skills.config` 按 name 或 path 设置 enabled，以及 `skills.bundled.enabled`；名称与路径不能在一条规则同时指定 |
| [Python pyproject](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/sdk/python/pyproject.toml) | Python >=3.10；pydantic >=2.12、packaging >=26.2；此源码包的匹配 CLI binary 依赖为 0.153.4，源码项目版本是 0.0.0-dev，不能当 PyPI 发布版本号 |
| [runtime requirements](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/sdk/python/src/openai_codex/_runtime_requirements.py) | SDK 对 toolOutput、turnTrigger、serviceTierForTurn、excludeTurns 等较新参数要求 CLI >=0.151.0；这是特定选项检查而非全部 SDK 调用的统一最低版本，无版本 checkout 需检查 experimental schema |
| [Getting started](https://github.com/openai/codex/blob/76ed3b484d62ccceb9fa512ff4dd139f421814c3/sdk/python/docs/getting-started.md) | 安装 openai-codex 会带匹配 CLI runtime，复用既有认证或通过 ChatGPT/API-key 登录；可创建线程和流式 turn |

官方 [非交互模式文档](https://developers.openai.com/codex/noninteractive) 说明了 `codex exec --json` 的使用。
源码的存在不能证明本机安装包已有这些字段/配置，manifest 要求固定实际 CLI 版本并先做冒烟。

## 选用的轻量实现

当前工具用 Python 标准库调用 Codex CLI JSONL，不要求安装 Python SDK。
与 SDK 一样底层需要实际模型访问和认证，但不会连接或抓取正在运行的 Desktop 会话。
这个选择减少依赖，同时保留原始事件可复核；不是声称 SDK 不支持采集。

若后来添加 SDK adapter，遵守同一规范：新线程/单轮、等待 completed、读取最后的累计 total、不能相加多次通知；
SDK 中线程多轮累计值的使用要取差，失败或缺失用量保留 unknown。reasoning 输出为输出子项，缓存输入为输入子项。
协议升级时必须重新确认字段关系，不能把费用估算 group 和 streaming tokenUsage 混为一谈。

## 本次验证边界

| 能力 | 状态 |
|---|---|
| CLI JSONL 用量结构、SDK streaming 示例与运行要求 | 已核实固定源码 |
| 工具解析、配对、计时、文件快照、质量门槛、报告 | 已实现，离线模拟 CLI 和回归测试验证 |
| 真实 CLI 版本对 flags、Skill 按名称开关、认证方式和用量事件的支持 | 需在实际运行机器单任务冒烟；本执行环境没有 codex 可执行文件 |
| 实际模型能否使用指定 model/effort | 需真实认证账号验证，CLI 接受参数并不证明服务端解析到不可变模型快照 |
| 当前 Python SDK 发布包的安装与真实模型通信 | 本次未安装/运行，源码要求已核实；不能宣称已跑通 |
| 当前用户 Codex Desktop 版本和已有线程的数据访问 | 未访问客户端，未验证；SDK/CLI 证据不推出 Desktop 暴露相同接口 |
| 真实业务节省比例和质量保持 | 未实测，不提供虚构百分比 |

## 实机冒烟清单

1. 专用评测用户固定 CLI 版本，记录 `codex --version`，填入 expected_cli_version。
2. 配置一个真实任务和外部 verifier，repeats=1；先确认所用 sandbox 能跑必要工具/测试。
3. 检查两臂原始 stdout 有一条有效 completion、正 Token 用量、最终响应；stderr 没有未知配置/认证/模型错误。
4. 验证 B 实际加载了 Skill、A 未加载：检查轨迹/响应，并在需要时结合该 CLI 版本的调试日志或 app-server skills/list 验证开关。仅看到 B 读 SKILL.md 不能证明遵循全部规则。
5. 核对每次初始化哈希一致、所有独立 checks/verifier 正常执行、代码变更内容正确，再增加到每任务 4 次。
6. 要验证 Desktop，另行记录 Desktop 版本及其公开支持的数据导出/接口，比较一段已知任务的实际用量。不要把 CLI benchmark 写成 Desktop 实测。
