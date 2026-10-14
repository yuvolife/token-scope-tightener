# 轻量配对 A/B 评测

目标：在正确性和必要测试不下降的前提下，测量 Skill 是否减少资源消耗。
本工具没有预填真实业务结果。离线测试中的模拟事件仅验证工具逻辑。

## 实验设计

沿用 `first-run-eval.md` 的五类任务：精确修 Bug、小功能、只补测试、代码审查、大仓库精确修改。
每个任务共同使用一个任务正文、模型 ID、推理强度、CLI 版本、代码提交、初始化命令、测试命令和独立正确性验证器。
正文保留业务范围、禁止修改项和输出格式，移除原模板中的 `使用 $token-scope-tightener`。

- A/off：安装同一份 Skill，但用 `skills.config` 按名称禁用，不添加调用语句。
- B/on：启用同一份 Skill，仅在共同正文前增加 `Use $token-scope-tightener.`。
- 每次调用都是新线程、单轮、`--ephemeral`，不 resume；每次都从相同提交创建独立 clone。
- 首个顺序由 seed 决定，此后 AB/BA 交替。建议每任务至少 4 次配对（40 次模型调用）；1 次只用于兼容性冒烟。
- 每个配对检查初始化后的全文件哈希一致。依赖、工具链和测试数据也应固定；禁止带时间戳的初始化产物。
- 不清除服务端缓存，也不承诺冷缓存。新线程不代表没有缓存；顺序平衡及记录缓存命中减轻混杂。
- 不允许子代理：关闭 `features.multi_agent`，出现 collab 调用会使该次无效，防止漏计子线程用量。

这是原生显式调用 Skill 的实验，不是“只复制几条精简提示词”的实验。工具安装 SKILL.md 和全部 Markdown references，
两个实验臂内容相同，CLI 用量包含 Skill 加载的开销。是否遵循 Skill、实际查看范围和输出合同仍需复核轨迹或由 oracle 判定。
它不覆盖日常长线程、Desktop UI、隐式触发和同时运行其他 Skill 的效果。

## 运行

要求 Python >=3.10、Git、已认证的 Codex CLI、可访问的同一模型。评测工具无需 Python SDK 或第三方 Python 依赖。
先在独立测试账号/容器中固定 CLI 版本。执行 `codex --version` 和 `codex exec --help`，确认支持
`--json`、`--ephemeral`、`--model`、`--sandbox`，且此版本支持按名称配置 Skill 启用状态。
版本字符串必须与 manifest 的 `expected_cli_version` 完全一致。源码支持不等于安装版本支持，先做单任务冒烟。

```bash
python -m unittest discover -s tests -v
cp evals/tasks.example.json /tmp/business-ab.json
# 编辑 /tmp/business-ab.json，替换模型、提交、任务、允许修改路径和命令
# 把 oracle.example.py 复制到业务仓库之外，为五个任务分别编写真实验收断言
python tools/ab_eval.py /tmp/business-ab.json --output /tmp/business-ab-results
```

路径相对于 manifest 所在目录解析；建议使用绝对路径。`--output` 必须不存在且位于业务仓库之外。
可用 `--codex /absolute/path/to/codex` 指定可执行文件。
默认从现有 CODEX_HOME（否则 ~/.codex）只复制 `auth.json` 到每次临时 CODEX_HOME；也支持 `--auth-home`。
API key 可由 CLI 支持的环境变量提供。原有 config、插件、记忆和用户 Skill 不复制，bundled Skills 关闭。
认证文件不进入结果，临时目录结束后清除。使用 keyring 的账号可能需要独立 `auth.json` 登录或环境变量认证。

推荐专用 OS 用户/容器，没有 ~/.agents/skills、系统级 Skill/managed instructions、自定义 provider 或全局 always-on 提示词。
工具拒绝常见污染：~/.agents/skills、业务仓库中的 SKILL.md、.codex/config.toml，以及提到 tightener 的 AGENTS.md。
其它 AGENTS.md 对 A/B 相同；请人工确认没有复制的 tightener/always-on 规则。不要在 Skill 本身的仓库上测这套 Skill。
系统/组织强制配置无法由工具完全隔离，必须记录并检查。容器也是限制外部文件写入的边界；CLI workspace-write 不是完整容器。

`setup`/`checks` 是 argv 数组，不隐式执行 shell。初始化每次运行；依赖下载应使用固定版本的缓存，避免纳入 agent 时间。
不支持 submodule fixture；先准备内容完整的独立测试仓库。只评测指定提交，不复制未提交改动。
测试命令和 verifier 本身是执行代码，使用自己审核的命令。不要在不可信任务描述中接受动态生成的 verifier。

## 正确性和质量门槛

每任务都必须配置：

1. `checks`：必要回归/构建/类型检查的确定命令，由 runner 在模型结束后独立运行。
2. `oracle`：业务仓库之外的 Python 文件；runner 在开始时固定其字节，复制到工作区外运行，模型不能通过改写测试仓库中的 verifier 伪造通过。
3. `allowed_changes`：允许修改的文件或目录前缀；测试任务只允许测试路径，review 使用空列表。

Oracle 的 cwd 是修改后的工作区；可读 `AB_RESPONSE_FILE` 和 `AB_RESULT_DIR`。
必须写真实行为断言或运行独立的隐藏回归测试，不能只匹配“测试通过”等模型自述。
报告字段、顺序、禁止行为、已知缺陷必须发现、review 误报、test-only 的变异测试敏感性，都应作为 oracle 的任务特定验收。
`oracle.example.py` 默认失败，防止把尚未配置的验收当成通过。CLI 完成或普通测试绿不等于需求正确。
必要测试不能在 B 中少跑；外部检查耗时和 agent 耗时分别记录，另报两者总耗时。

通过条件同时要求：CLI 成功且未超时、恰好一次有效 completion 用量、存在最终响应、没有错误事件/子代理、
全部 checks 和 oracle 通过、修改均在允许范围。初始化失败直接终止实验，已经完成的记录保留。
同一 pair 的初始文件哈希不一致时，pair 无效。任意 B 质量下降都会标记，不允许整体宣称质量保持的节省。
始终保留失败案例；有效 pair 的聚合只作诊断，不能用它掩盖失败或选择性丢弃不利结果。

## 采集口径

| 字段 | 口径 |
|---|---|
| input_tokens | 新单轮 CLI completion 的 input_tokens，包含缓存输入 |
| output_tokens | CLI completion 的 output_tokens；不再加 reasoning_output_tokens |
| cached_input_tokens | 输入的子集，绝不能再次加进总 Token |
| total_tokens | input_tokens + output_tokens |
| uncached_input_tokens | input_tokens - cached_input_tokens |
| cache_hit_ratio | cached_input_tokens / input_tokens；零分母为 null |
| agent_seconds | CLI 进程开始到结束，包含其启动/握手/模型/工具时间 |
| validation_seconds | runner 的必要 checks + oracle 时间 |
| elapsed_seconds | agent_seconds + validation_seconds，不含 setup |
| repeated_commands | 相同 command 字符串的后续执行次数；按 item ID 去重 |
| failed_commands | 可观测非零退出命令数，不能直接当作任务失败或重试数 |
| hypothesis_retries / network_retries | null；exec 事件没有可靠的该层计数 |
| modified_files | agent 前后内容哈希不同的文件；包含未跟踪、被忽略文件、删除和符号链接 |

`repeated_commands` 是自动可观测重试代理指标。相同测试的必要复跑也会计入，换措辞命令的重试则可能漏计。
原有“同一假设下最多两次”仍需人工标注，不能拿这个代理直接替代。同样，命令轨迹无法可靠穷尽查看文件范围、追问次数。
源码中的 CLI fallback 可能在缺少 usage 通知时生成全零字段，本工具也拒绝全零用量，不把缺失当成免费执行。
单轮失败的部分用量可能没有公开 completion，保留日志并排除，不填 0，不估算。

## 报告与判定

产物：manifest.json（提交、Skill/CLI/verifier 哈希、参数）、runs.json、summary.json、summary.md；
每次的原始 JSONL/stderr、响应、命令轨迹、测试/验证日志、修改前后哈希、tracked diff 和修改文件副本。
修改文件副本包含未跟踪文件；changes.patch 只含 tracked diff。测试生成文件在 agent 快照之后产生，不计入 agent 修改范围。
结果可能包含业务代码、路径、测试输出与敏感信息，不自动上传。人工审核后再共享。

每指标相对节省 = `(off - on) / off`；负值是增加，off=0 或数据缺失为 null。
summary.json 提供所有有效配对的指标和加总后节省率（按总资源加权），同时提供两臂聚合缓存命中率。
缓存 Token 数降低本身不是收益，结合总输入/未缓存输入和命中率解读。Token 不直接等于价格或订阅额度，不自动推导人民币成本。
`quality_regression` 标记 A 通过而 B 不通过。失败、超时、无用量、初始化不一致都不能报告该 pair 的有效节省。
退出码 0 表示所有 pair 通过质量门槛，不表示一定省 Token；退出码 1 表示存在无效/失败 pair。

四次配对只是早期证据；检查每任务离散程度，追加不同真实任务与重复次数，避免把模型随机波动当 Skill 的因果效果。
只有质量门槛全通过且资源下降才是候选收益；没有预设“至少节省 X%”或统计显著性结论。
