# 无头 Coding Agent 委派与多 CLI 编排同类工程深度调研报告

> **文档控制信息**
> - **文档标识**: ANA-AGY-DELEGATION-PEERS-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **调研动机**: 本仓库 `agy-delegation-workflow` 定位于「前台规划审查 + 后台 `agy -p` 无头进程执行」。随着 2026 年主流宿主（Antigravity / Claude Code / Codex）原生补齐 Subagent、Worktree 隔离、Swarm 与官方 SDK，外挂无头 CLI 派发模式的真实边界已发生剧变。本次调研系统梳理 2025–2026 年主流无头委派与多 CLI 编排工程实践，为配套评估报告 [2026-11-23-agy-delegation-workflow-architecture-evaluation.md](./2026-11-23-agy-delegation-workflow-architecture-evaluation.md) 提供外部参照系。
> - **证据分级**: 【A】一手（2026-11-23 `gh api` 实测星数与活跃度、开源仓库 README/源码原文、本机 `agy 1.5.14` CLI 实测、本地已安装 `superpowers` 源码）｜【B】二手转引（官方文档与工程博客搜索综合摘要）｜【C】行业经验判断与架构研判

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：基于 2026-11-23 `gh api` 10 个标杆仓库一手实测、主流 CLI（`claude -p` / `codex exec` / `agy 1.5.14`）能力对标及三大工程专题（worktree 隔离、编排经济学、幂等验收），明确外挂无头派发器的剩余生态位 |

---

## 0. 摘要（TL;DR）

**一句话结论**：2026 年「前台编排 + 后台 Coding Agent 执行」已经彻底分化为两极——**同宿主内由原生 Subagent / Worktree / Swarm / Workflow 原语全面接管**，**跨宿主与离线 CI 由标准协议（ACP / 官方 SDK）与带沙箱/JSON 流的原生无头 CLI 接管**；单一厂商 CLI 的薄 Shell 包装脚本和独立外挂看板正在快速失去生存空间。

六条一级结论：

1. **宿主原生原语已基本吞噬「同宿主外挂派发」**。Claude Code 原生提供 Subagents（含 `isolation: "worktree"`）与 Agent Teams【B】；Antigravity 原生提供 `invoke_subagent`（含 `share`/`branch` worktree 与 `flash_lite`/`flash`/`pro` 分档）、`run_workflow`（Python 编排 + JSON Schema 强制回传）与 `swarm`【A】。连拥有 **28,794★** 的独立多 CLI 编排看板 `BloopAI/vibe-kanban` 也在 README 顶栏挂出了 **`Vibe Kanban is sunsetting`** 停运公告，印证外部薄壳编排器正被宿主原生能力剧烈挤压【A】。
2. **2026 无头 CLI 安全与可观测基线已全面升级，裸文本 + 跳过权限已被淘汰**。`openai/codex`（136.2k★）的 `codex exec` 默认只读沙箱，须显式声明 `--sandbox workspace-write` 并输出 `--json`（JSONL 流）【B】；`claude -p`（156.7k★）标配 `--output-format stream-json`、`--allowedTools`、`--max-budget-usd` 与 `--worktree`【B】；本机实测 `agy 1.5.14` 也已原生具备 `--sandbox`、`--mode (accept-edits|auto|plan)`、`--effort`、`--output-format stream-json`、`--json-schema`、`acp` 及官方 Python SDK `google-antigravity`（4,166★）【A】。
3. **Git worktree 物理隔离已成为并行编码的绝对标配，靠提示词约定「不改同一文件」已过时**。`obra/superpowers`（324.4k★）、`gastownhall/gastown`（18.9k★）、`OrchestratorInc/agent-orchestrator`（15.0k★）与 `kbwo/ccmanager`（1.3k★）均以「一任务一 worktree + 外部账本」隔离并发写入【A】。
4. **编排经济学揭示「盲目委派更贵更慢」**。Anthropic 实测多智能体系统消耗的 token 约为单轮聊天的 **15×**（单智能体循环约 4×）【B】；小任务盲目委派会带来 **40%–60% 协调税**【B】；`obra/superpowers` 一手源码提出 **「Turn count beats token price」**——最便宜模型在散文规格任务上常多花 2–3× 轮次，总成本与耗时反而更高，因此应按任务可验证性与复杂度路由，而非无脑全下发给最廉价小模型【A】。
5. **无头进程的退出码与磁盘副作用天然解耦，验收必须转向「产物 + 确定性门禁」**。网络抖动、OAuth 刷新超时常发生在代码落盘之后；行业共识是以 `git status`/commit SHA 与确定性测试作为完成真相，避免 at-least-once 重试覆写已落地改动【B】。
6. **外挂无头 CLI 仅剩两个真实但极窄的剩余生态位**：① **异构跨宿主/跨模型套利**（如在 Claude Code 中调用 `agy -p` / `codex exec` 跑异构模型或跨源盲审）；② **无交互 CI / Cron / 离线批处理**（但更现代的工程入口是官方 SDK、ACP 或直接带 `--sandbox --output-format stream-json` 的原生命令，而非硬编码模型的薄包装脚本）【A/C】。

---

## 1. 调研范围与生态分层

为避免将不同运行形态混为一谈，2025–2026 年的 Coding Agent 后台委派生态可按四个清晰层级划分：

| 层级 | 形态与代表 | 核心优势 | 典型短板 |
| :--- | :--- | :--- | :--- |
| **L1 宿主原生编排原语** | Antigravity（`invoke_subagent` / `run_workflow` / `swarm`）、Claude Code（Subagents / Agent Teams） | 零安装、自动继承权限与工作区、原生 worktree 隔离、结构化回传、零记忆库串台 | 绑定单一宿主平台，难以跨厂商混排模型 |
| **L2 宿主无关技能规程** | `obra/superpowers`（`dispatching-parallel-agents` / `subagent-driven-development`） | 跨宿主复用、不写死模型名/CLI 名、以文件指针与账本管控质量与成本 | 依赖宿主底层提供派发能力 |
| **L3 专业多 CLI 编排器 / SDK / 协议** | `gastownhall/gastown`、`OrchestratorInc/agent-orchestrator`、`kbwo/ccmanager`、`google-antigravity` SDK、`ACP` | 跨 10–35+ 异构 CLI 混排、统一 worktree 管理、CI 评论回流、强类型事件流 | 独立运维工具链重；纯薄壳 UI 易被原生替代（如 `vibe-kanban` 停运） |
| **L4 单一 CLI 薄包装脚本** | 早期 `agy-delegation-workflow` / 各类自写 bash wrapper | 针对特定本机痛点（如 WSL 代理、特定插件 env）响应快 | 极易随 CLI 升级与模型换代快速过时，安全与可观测能力滞后 |

---

## 2. 2025–2026 主流标杆项目一手横评（2026-11-23 `gh api` 实测【A】）

| 仓库 | Stars 【A】 | 最近推送 【A】 | 形态与核心工程机制 |
| :--- | :---: | :---: | :--- |
| **`obra/superpowers`** | **324,421** | 2026-11-03 | **技能级标杆**：完全宿主无关、不写死品牌模型名；按任务复杂度分 3 档抽象模型（cheap / standard / most capable）并提出「Turn count beats token price」；强制 git worktree；用 `task-brief` + `review-package` 文件指针与 `progress.md` ledger 防主上下文膨胀与压缩失忆；5 轮熔断且 R4–5 换新 subagent 并升档模型【A】 |
| **`anthropics/claude-code`** | **156,749** | 2026-11-23 | **三层并发典范**：无头 `claude -p --output-format stream-json --allowedTools ... --max-budget-usd ... --worktree`；内置 Subagents（frontmatter `isolation: "worktree"` + 最小权限工具集）；实验性 Agent Teams（共享任务板 + 独立上下文协作）【B】 |
| **`openai/codex`** | **136,180** | 2026-11-23 | **默认安全无头 CLI**：`codex exec` 默认只读沙箱，写盘需显式 `--sandbox workspace-write`（废弃宽泛 `--full-auto`），严禁非容器裸用全权限；原生支持 `--json`（JSONL）、`-o summary.md` 落盘与 `--ephemeral` 零历史污染【B】 |
| **`BloopAI/vibe-kanban`** | **28,794** | 2026-11-15 | 支持 10+ CLI 的看板 + 独立 worktree 编排器；**重大行业拐点信号**：README 顶栏已正式公告 **`Vibe Kanban is sunsetting`**，证明薄壳外挂多终端 UI 难以抵御原生宿主多代理能力挤压【A】 |
| **`gastownhall/gastown`** | **18,869** | 2026-11-14 | Steve Yegge 的大规模多 Agent 工作区管理器（支持 20–30 并发）：Coordinator（Mayor）+ Project Container（Rig）+ 短命 Worker（Polecats）+ worktree 持久化 Hooks + Beads 外部账本，彻底把任务状态抽离出 LLM 上下文【A】 |
| **`OrchestratorInc/agent-orchestrator`** | **15,032** | 2026-11-23 | 原 `ComposioHQ/agent-orchestrator`，支持 Claude Code / Codex 等 **35+ Coding Agents** 跨平台编排：每任务独立 worktree + 按任务任选异构 CLI/模型 + 失败 CI 与 PR Review 评论自动路由回对应分支 Worker + 独立 Reviewer Agent【A】 |
| **`amantus-ai/vibetunnel`** | **4,709** | 2026-08-05 | 浏览器远程终端代理，专注解决无头/后台 CLI 进程的实时远程可观测与人工接管【A】 |
| **`google-antigravity/antigravity-sdk-python`** | **4,166** | 2026-11-19 | Antigravity 官方 Python SDK：通过 `async with Agent(LocalAgentConfig(...))` 自动管理二进制、默认只读安全策略、提供强类型 `response.thoughts` / `response.tool_calls` 异步流，全面取代脆弱的 shell stdout 文本抓取【A】 |
| **`stravu/crystal`** | **3,128** | 2026-02-26 | 早期多 worktree 并行 Codex/Claude 桌面管理器，2026 年初已停更并转型【A】 |
| **`kbwo/ccmanager`** | **1,280** | 2026-10-27 | 轻量级无 tmux 多 CLI 会话管理器：突出工程细节包括 **Busy / Waiting / Idle 实时状态探测**、`.worktreeinclude` 自动拷贝 `.env`/本地凭据到新 worktree、以及崩溃会话恢复【A】 |

### 关键补充：本机 `agy 1.5.14` 原生无头能力实测【A】

实测本机 `/home/hui/.local/bin/agy`（版本 `1.5.14`，2026-11-21 更新）的 `--help` 与 `models` 输出可见，Antigravity CLI 自身已完成向 2026 工业基线的跃迁【A】：
- **安全与权限细粒度**：原生提供 `--sandbox`、`--mode (accept-edits|auto|plan)`、`--disable-slash-commands`，无需再被迫裸跑 `--dangerously-skip-permissions`；
- **结构化输入输出**：原生提供 `--output-format (text|json|stream-json)`、`--input-format stream-json`、`--json-schema`、`--log-file` 以及标准协议子命令 **`acp`（Agent Client Protocol）**；
- **能力档位与模型演进**：原生提供 `--effort (low|medium|high|xhigh|max)`，且可用模型已演进至 23 个（含 `Gemini 4 Neon/Argon/Hydrogen`、`Orchestrator`、`Claude Opus/Sonnet 5.5` 等），旧一代 `Gemini 3.8 Flash (High)` 已处于列表末端的跨代遗留位置【A】。

---

## 3. 四大核心工程专题深度洞察

### 3.1 无头子进程隔离：从「提示词约定」到「Worktree + 沙箱 + 管道」

2026 年生产级无头派发的四条铁律已高度收敛【A/B】：

1. **物理隔离优于口头约束**：并行写任务必须落在独立 git worktree（而非共享工作区靠 Prompt 约束「别碰同一文件」）；同时须防范 worktree 的隐蔽共享陷阱——所有 worktree 共用主 `.git/config`（如 Husky `core.hooksPath`），且需借助 `.worktreeinclude` 同步被 `.gitignore` 排除的 `.env`/证书，并设置 `GIT_EDITOR=true`、`CI=true` 杜绝非交互进程等待 TTY 挂死【A/B】。
2. **最小权限沙箱优于全权限裸奔**：`codex exec` 与 `google-antigravity` SDK 均坚持「默认只读、按需放权写工作区」；`claude -p` 通过 `--allowedTools` 精准限定工具白名单【A/B】。无条件写死 `--dangerously-skip-permissions` 在非容器环境下存在高危越权风险。
3. **大 Prompt 必须走 Stdin 或文件路径，严禁裸走 `argv`**：将数万字符的 7 维自包含 Markdown Prompt 直接拼进命令行参数 `-p "<content>"`，在 Windows `CreateProcess`（32 KB 上限，经 `.cmd` 包装时更窄至 ~8 KB 且存在 `&`/`|`/`%VAR%` 注入风险）和 Linux（单参数 `MAX_ARG_STRLEN` 128 KB）上均存在截断或崩溃风险【A/B】。
4. **结构化流与真实状态机取代 `tail -f`**：现代编排器通过 NDJSON 流（`stream-json`）、ACP JSON-RPC 或 `Busy / Waiting / Idle` 状态探测取代 fire-and-forget 后台重定向，并在超时或额度触顶（`--max-budget-usd` / `--max-turns`）时做确定性收口【A/B】。

### 3.2 Orchestrator-Worker 编排经济学：何时委派、何时直写

| 规律 | 实证依据 | 工程指导 |
| :--- | :--- | :--- |
| **多代理天然带高倍 Token 税** | Anthropic 披露多智能体编排消耗约单轮对话 **15×** token（单智能体循环约 4×）【B】 | 严禁为了「架构洁癖」把所有任务机械外包；仅在任务足够独立且上下文规模大时启用隔离委派 |
| **小任务的协调税倒挂** | 行业评测显示小任务委派带来 **40%–60% 协调税**（写 7 维 Prompt + 派发 + 全量复查）【B】 | 小于数分钟或前台已读全上下文的同质化改动，直接前台编写更快更准 |
| **轮次成本高于 Token 单价** | `obra/superpowers` 实战总结（`subagent-driven-development/SKILL.md:208-214`）【A】 | 最廉价小模型面对自然语言需求常多耗 2–3× 轮次；便宜模型仅适合「计划已含精确代码的转录或单文件机械改」，散文规格与审查应以中档模型为地板 |
| **按可验证性路由（Routing by Verifiability）** | 社区工程共识【B/C】 | 拥有确定性机器验收（编译器 / 单测 / Linter）的任务才适合下放低成本 Worker；模糊架构权衡必须留给高阶 Orchestrator |

### 3.3 退出码与磁盘副作用解耦：Silent Landing 与幂等验收

在无头进程调用远端模型 API 的场景中，**「代码已流式写盘，但进程在尾段 OAuth 刷新/流关闭/超时处返回非零退出码」**是一类真实且高频的分布式系统式故障【A/B】。行业最佳实践与 `agy-delegation-workflow` 总结的 **Silent Landing（假失败/延迟落盘）判别**高度一致：
- **绝不把子进程退出码当作唯一状态真相**；
- 故障或超时后，先以**持久化磁盘产物（`git status --porcelain` / `git diff`）+ 确定性验证门禁（单测/构建）**判定真实进度；
- 外部账本记录幂等键或基线 Commit SHA，防止无脑重试造成重复写入或覆盖已完工代码【A/B】。

### 3.4 终极生态位裁定：原生能力成熟后的边界重划

将 2026 年的原生宿主能力与外挂无头 CLI 并置可见清晰的生态位迁徙：

```text
2025 痛点：前台单窗口易腐化、缺子代理 ──► 外挂 CLI 派发脚本（dispatch-agy / ralph 包装）大放异彩
                                                    │
                                                    ▼ 2026 宿主原生能力爆发
同宿主内并行编码 / 单测 / 审查  ────────► 已被 Antigravity (invoke_subagent / run_workflow / swarm)
                                         与 Claude Code (Subagents worktree / Agent Teams) 彻底取代
                                                    │
外挂无头 CLI / SDK 仅剩极窄生态位 ──────► ① 异构跨宿主/跨模型套利（Claude 调 agy/codex 或跨源盲审）
                                         ② 无交互 CI / Cron / 离线流水线（优先官方 SDK / ACP / 原生 --sandbox --json）
```

---

## 4. 行业典型反模式与踩坑警示

1. **在规程与脚本中硬编码具体厂商与代际模型名**：模型每 3–6 个月换代一次，把具体版本号写进 `SKILL.md`、`description`、脚本默认常量与单元测试，会让技能在半年内迅速沦为「跨代化石」【A】。
2. **用单项目的组件库约定污染公共通用技能**：将具体前端项目私有组件的 prop 名称、目录结构写进通用委派技能的审计清单，使技能完全失去跨仓库复用能力【A】。
3. **单一宿主环境下强行「套娃」或维持双份委派真相源**：当宿主已有原生隔离原语，或总控工作流技能（如 `goal-loop`）已有后端无关适配器时，继续维护一个以单一厂商 CLI 为中心的并行委派规程，必然制造 SSOT 撕裂与高昂的文案对齐摩擦【A】。
4. **把个人本机故障（WSL 代理 / 私有插件变量）提升为公共技能核心卖点**：个人机器的网络与插件环境应下沉为本机 shell profile 或独立故障笔记，不应绑死在公共技能的路由描述与强制报错路径里【A/C】。

---

## 5. 下篇衔接与参考来源

基于以上 2026 年行业基线与生态位裁定，配套评估报告 **[2026-11-23-agy-delegation-workflow-architecture-evaluation.md](./2026-11-23-agy-delegation-workflow-architecture-evaluation.md)** 将对本仓库 `skills/agy-delegation-workflow/` 进行逐行源码体检、28 份计划实证审计，并给出「降维合并退役 vs 厂商中立重构 vs 最小止血」的量化决策对比。

### 主要参考来源

- **一手开源与实测【A】**：`obra/superpowers`（https://github.com/obra/superpowers ，含本地 `.agents/skills/subagent-driven-development/` 与 `dispatching-parallel-agents/`）、`anthropics/claude-code`（https://github.com/anthropics/claude-code ）、`openai/codex`（https://github.com/openai/codex ）、`BloopAI/vibe-kanban`（https://github.com/BloopAI/vibe-kanban ）、`gastownhall/gastown`（https://github.com/gastownhall/gastown ）、`OrchestratorInc/agent-orchestrator`（https://github.com/OrchestratorInc/agent-orchestrator ）、`google-antigravity/antigravity-sdk-python`（https://github.com/google-antigravity/antigravity-sdk-python ）、`amantus-ai/vibetunnel`（https://github.com/amantus-ai/vibetunnel ）、`kbwo/ccmanager`（https://github.com/kbwo/ccmanager ）、`stravu/crystal`（https://github.com/stravu/crystal ）；本机 `/home/hui/.local/bin/agy`（`1.5.14`）实测。
- **官方文档与工程实践摘要【B】**：Claude Code Headless / Subagents / Agent Teams 官方文档、OpenAI Codex CLI `codex exec` 沙箱与非交互指南、Anthropic 多智能体 Token 成本实证摘要。
