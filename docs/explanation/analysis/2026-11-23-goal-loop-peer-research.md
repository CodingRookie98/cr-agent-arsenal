# 长程 Agent 研发闭环同类技能与工程实践深度调研报告

> **文档控制信息**
> - **文档标识**: ANA-GOAL-LOOP-PEERS-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **调研动机**: 本仓库 `goal-loop` 经多轮演进已成长为 17 文件 / 125 KB 的完整状态机技能。为了在「继续加厚护栏」与「主动架构瘦身」之间做出基于证据的决策，本次调研系统梳理 2025–2026 年社区主流长程 Agent 研发闭环方案、官方 Harness 工程实践与上下文/指令实证研究，回答三个问题：社区有哪些代表流派、真正奏效的底层工程规律是什么、行业踩过哪些典型坑。本报告与配套评估报告 [2026-11-23-goal-loop-architecture-evaluation.md](./2026-11-23-goal-loop-architecture-evaluation.md) 成对交付。
> - **证据分级**: 【A】一手（GitHub API 实测数据、仓库 README/源码原文、本地技能源码、官方技术文档与论文核心数据）｜【B】二手转引（搜索引擎综合摘要、行业综述文章，未抓取原始全文）｜【C】观点与厂商自测（个人博客、方法论倡议、单方经验总结）

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：基于 2026-11-23 GitHub API 一手实测（15 个开源项目）、7 个代表实现源码精读、3 家一线实验室（Anthropic / OpenAI / Manus）工程文与 4 项实证研究，收敛六大同类流派、五条底层规律与六类行业反模式 |

---

## 0. 摘要（TL;DR）

**一句话结论**：2025–2026 年长程编码 Agent 编排的核心演进主轴，是从**「靠大段提示词祈祷模型自律」**转向**「提示词做薄地图 + 确定性机制外置（Hook / 外部循环 / 门禁脚本）+ 隔离上下文的指针化交接」**。随着前沿模型能力与宿主原生原语（Plan Mode、Subagents、Hooks、Dynamic Workflows）成熟，重量级手写状态机正在被两头挤压：轻端让位给超薄可组合技能，重端让位给外置确定性 Harness。

八条一级结论：

1. **生态已分化为六大流派，彼此处于不同抽象层，不是简单替代关系**。分别是：模块化可组合技能（`superpowers`、`mattpocock/skills`）、Hook 强约束文件记忆（`planning-with-files`）、规约驱动开发 SDD（`spec-kit`、`OpenSpec`、`BMAD`）、新鲜上下文波次编排（`gsd-core`）、外部自主循环 Harness（`ralph`、`ralph-claude-code`、Anthropic Harness）与结构化任务图/原生原语（`beads`、`task-master`、Claude Code / Antigravity 原生能力）【A】。
2. **最高星数的通用编程技能都在做「激进减法」与「按需组合」**。`mattpocock/skills`（330.8k★）单技能多在 20–133 行之间【A】；`obra/superpowers`（324.4k★）把规划、执行、验证、收尾拆成独立微技能，核心路由与主指令严格控体量【A】。反观重型多角色/全流程 SDD 框架，在存量代码库（Brownfield）普遍遭遇「大锤砸核桃（sledgehammer to crack a nut）」与「Markdown 溺毙（death by markdown files）」批评【B/C】。
3. **「指令越多越可靠」已被多篇实证研究证伪**。ICLR 2025 *Curse of Instructions* 指出多约束同时满足概率随数量近似指数衰减（`P = p^N`）【B】；IFScale 基准测得约 150–200 条指令即出现明显首位偏置与尾部丢弃【B】；ETH Zurich SRI Lab（2026）对 `AGENTS.md` 的受控评测表明：**LLM 生成的上下文文件使任务成功率反降约 3%，人工编写仅提升约 4%，但二者一律令推理成本暴涨 >20%**【B】。
4. **真正的熔断、完成门禁与压缩前保活，行业标杆全部外置到代码而非写在提示词里**。`OthmanAdi/planning-with-files`（28.2k★）通过 6 个宿主生命周期 Hook（`SessionStart` / `PreToolUse` / `PostToolUse` / `PreCompact` / `Stop` 等）实现确定性提醒与拦截【A】；`frankbria/ralph-claude-code`（9.7k★）把三态熔断器（`CLOSED`/`HALF_OPEN`/`OPEN`）与双条件退出门禁实现为外部 Bash 状态机（配 784 项测试）【A】。在纯提示词内要求 LLM 自行核算 token 百分比或严格遵守高频落盘频率，本质上不可度量、不可强制。
5. **多智能体编排的隐形杀手是「主调度上下文雪球」，现代解法是文件指针交接 + 模型分层 + 批处理**。`superpowers` 2026 年末新版 `subagent-driven-development` 记录了真实教训：把历史摘要贴进派发提示词曾导致单次派发膨胀至 42,000 字符（99% 为历史噪音）【A】；其解法是用极薄脚本（`task-brief` 41 行、`review-package` 46 行）把需求与 Diff 落盘，主调度只传文件路径，并提出「**轮次成本高于单价（Turn count beats token price）**」的模型分层律与同形小改动合批规则【A】。
6. **自治体验的分水岭在于「先裁决不卡死（Rulings, not stalls）」**。最新 `superpowers` 明确反对在任务间向人类反复请示，要求编排者在非不可逆/非安全/非外部副作用的范围内依据 Spec 自主裁决、将裁决记入账本并继续推进，仅停在四类真正高危边界【A】；传统步步确认式状态机在长任务中反而把人变成瓶颈。
7. **状态存储出现明显分层：人类可读计划用精简 Markdown，机器高频解析状态用 JSON 或数据库**。Anthropic 工程文指出 JSON 比 Markdown 更抗模型误改结构【B】；`beads`（28.9k★）明确宣称「不要用 Markdown TODO 列表做任务追踪」，改用 Dolt 支撑的哈希 ID 依赖图【A】；`ralph` 系列用 `prd.json` 存任务完成位、用纯文本 `progress.txt` 做追加日志【A】。用复杂正则反向解析/回写自由格式 Markdown 是最脆弱的中间地带。
8. **Anthropic 的 Harness 简化律值得全行业铭记**：「Harness 里的每一个组件，都编码了一条关于『当前模型做不到什么』的假设」【B】。前沿模型每代跃迁后，必须反过来压力测试并拆除不再必要的脚手架，否则昔日护栏会演变成拖慢推理、增加成本的死重（Dead Weight）。

### 六大流派全景速查（数据采集于 2026-11-23）

| 流派 | 代表项目（实测星数 / 状态） | 核心骨架 | 上下文与状态机制 | 适用边界 | 主要代价 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S1 模块化可组合技能** | `mattpocock/skills`（330.8k★ 活跃）【A】<br>`obra/superpowers`（324.4k★ 活跃）【A】 | 独立微技能按需触发；先规约/切片，后子智能体隔离实现与双维审查 | 极薄脚本抽 `task-brief` / `review-package` 文件指针；plan 专属 `.superpowers/sdd/` 账本 | 日常功能开发、重构、多任务迭代 | 缺少跨仓强制治理与统一测试分级矩阵 |
| **S2 Hook 强约束文件记忆** | `OthmanAdi/planning-with-files`（28.2k★ 活跃）【A】 | Manus 风格三文件（`task_plan.md` / `findings.md` / `progress.md`）+ 宿主插件 | 6 类确定性 Hook（启动恢复、工具前复读、压缩前保全、停机前完成校验） | 单会话长程探索、复杂调试、研究与实施 | 强绑定支持 Hook 生命周期的宿主（如 Claude Code） |
| **S3 规约驱动 SDD 框架** | `github/spec-kit`（151.1k★ 活跃）【A】<br>`Fission-AI/OpenSpec`（75.5k★ 活跃）【A】<br>`BMAD-METHOD`（55.6k★ 活跃）【A】 | 宪章/规约 → 计划 → 任务 → 实现；OpenSpec 走向轻量流式变更集 | 文档目录树（`specs/`、`changes/`）或分角色 Persona 文档流转 | 团队协作、绿地 0→1（BMAD/spec-kit）或存量渐进变更（OpenSpec） | 文档膨胀风险高、部分范式在存量小改下仪式感过重 |
| **S4 新鲜上下文波次编排** | `gsd-build/get-shit-done`（64.1k★ 已归档）【A】<br>`open-gsd/gsd-core`（11.8k★ 活跃）【A】 | 5 步闭环（Discuss → Plan → Execute → Verify → Ship）+ 并行波次 | 薄编排器 + 每子任务独立新鲜 200k 上下文窗口，状态落盘于 `.planning/` | 独立可并行的大型需求、全栈从零构建 | 社区曾因治理争议分裂归档；多波次 token 消耗大 |
| **S5 外部自主循环 Harness** | `snarktank/ralph`（22.3k★ 停更）【A】<br>`frankbria/ralph-claude-code`（9.7k★ 活跃）【A】<br>Anthropic Harness（官方工程文）【B】 | 宿主外部 `while` 循环逐轮拉起全新 Agent 进程，直到退出门禁满足 | `prd.json` / `feature_list.json` + `progress.txt` + Git 提交 + 外置 JSON 熔断状态 | 夜间无人值守批量交付、长周期应用构建 | 需外部运行器与明确验收脚本，人机中途协同成本高 |
| **S6 结构化任务图与原生原语** | `gastownhall/beads`（28.9k★ 活跃）【A】<br>`claude-task-master`（28.5k★ 低频）【A】<br>Claude Code / Antigravity 原生原语【A/B】 | 机器一等公民的依赖图（Dolt/JSON）或宿主内置 Plan/Subagent/Swarm/Workflow | 数据库/哈希 ID 依赖图（防多分支合并冲突）或平台托管任务状态 | 多智能体并发协作、跨周跨仓长线工程 | 引入外部 CLI/DB 依赖或绑定特定宿主平台 |

### 生态分层定位图

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ L4 宿主原生编排原语     Claude Code (Plan Mode / Subagents / Agent Teams)    │
│                        Antigravity (update_steps / run_workflow / swarm)     │
├──────────────────────────────────────────────────────────────────────────────┤
│ L3 外部自主运行时       ralph / ralph-claude-code / Anthropic Harness        │
│                        (外部进程循环 + 确定性熔断器 + JSON 状态 + 限流)       │
├──────────────────────────────────────────────────────────────────────────────┤
│ L2 确定性增强与状态层   planning-with-files (6-Hook) / beads (Dolt DAG)      │
│                        superpowers scripts (task-brief / review-package)     │
├──────────────────────────────────────────────────────────────────────────────┤
│ L1 提示词与规程技能层   mattpocock/skills / superpowers / OpenSpec /         │
│                        spec-kit / BMAD / ★ 本仓库 goal-loop (当前所在层)     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. 调研范围、方法与证据分级

### 1.1 先分层，再对标

社区讨论「长程 Agent 研发工作流」时，常把四类完全不同运行层的工具混为一谈。不先区分抽象层，就容易拿纯提示词技能去硬扛本该由外部运行时承担的职责：

| 层级 | 核心承载物 | 能力边界 | 不可逾越的物理限制 |
| :--- | :--- | :--- | :--- |
| **L1 提示词规程层** | `SKILL.md`、`AGENTS.md`、模板与检查清单 | 塑造推理路径、定义门禁语义、组织多技能路由 | **无法机械强制**；受上下文衰减与指令数量天花板约束；无法自测真实 token/时间消耗 |
| **L2 确定性增强层** | 宿主 Hooks、小型 CLI 辅助脚本、结构化任务数据库 | 在固定事件点注入提醒/阻断退出、剥离大文本交接、维护并发安全依赖图 | 依赖宿主开放 Hook 接口或本地工具链可用性 |
| **L3 外部循环 Harness 层** | Shell/Python 外层调度器 + 无头 Agent CLI | 硬重置上下文（每轮全新实例）、硬控重试/限流/熔断/超时、自动化验收循环 | 失去高带宽实时对话交互，依赖高质量前置规约与可机检测试 |
| **L4 宿主原生原语层** | IDE/CLI 内建 Plan Mode、子智能体、Workflow/Swarm | 零安装成本、深度集成 UI/沙箱/权限/账单计量 | 跨宿主不可移植，厂商演进会快速吞噬 L1/L2 的重复造轮子 |

### 1.2 检索样本与一手取证方法

本次调研于 **2026-11-23** 执行，采用多路交叉取证：

1. **GitHub API 一手元数据采集【A】**：使用已认证 `gh api` 实时拉取 15 个目标开源仓库的星数、最近推送时间（`pushed_at`）、是否归档（`archived`）及许可证，杜绝依赖过期记忆或二手文章的旧星数。
2. **源码与 README 精读【A】**：通过 `gh api` 直接读取 `github/spec-kit`、`Fission-AI/OpenSpec`、`open-gsd/gsd-core`、`bmad-code-org/BMAD-METHOD`、`gastownhall/beads`、`OthmanAdi/planning-with-files`（含 `SKILL.md` 534 行与 `hooks/hooks.json` 101 行）、`snarktank/ralph`、`frankbria/ralph-claude-code`（含 `lib/circuit_breaker.sh`）等一手源码；直接读取本机 `.agents/skills/` 下已安装的 `obra/superpowers`（含 `subagent-driven-development` 7 文件及 `scripts/`）与 `mattpocock/skills`（`implement`、`implement-spec`、`loop-me`、`to-spec`、`to-tickets`、`wayfinder`）。
3. **前沿工程文与学术基准核验【B/C】**：检索 Anthropic（2025/2026 Harness 系列）、OpenAI（2026 Harness Engineering）、Manus AI（2025 Context Engineering）、MartinFowler.com（SDD 评述）、`agentskills.io` 官方规范，以及 *Curse of Instructions*、*IFScale*、*Context Rot*、ETH Zurich *Evaluating AGENTS.md* 等实证结论。

### 1.3 诚实边界与已知偏差

- **正文抓取边界**：当前环境未安装 `firecrawl` CLI，对站外博客文章与学术论文仅通过搜索引擎综合摘要交叉确认，未逐字抓取原始 PDF/HTML 全文，故在文中**一律保守标注为【B】或【C】**，不冒充【A】一手全文核验。凡标注【A】者，均为本次通过 `gh api` 或本地文件读取直接核验过原文的事实。
- **星数不等于架构最优**：开源仓库星数受 KOL 传播（如 Matt Pocock、Jesse Vincent）、GitHub 官方背书（`spec-kit`）及入场时机影响极大；本报告将其视为「社区真实采用热度信号」，而非架构优劣的唯一裁决。
- **时间截面**：所有星数、推送时间与项目存续状态均反映 `2026-11-23` 快照（例如 `gsd-build/get-shit-done` 与 `RooCodeInc/Roo-Code` 均已于 2026 年中归档）。

---

## 2. 六大同类流派源码级深度解剖

### 2.1 流派一：模块化可组合技能（`obra/superpowers` 与 `mattpocock/skills`）

这是当前社区采用最广、且与 `goal-loop` 处于同一抽象层（L1 + 轻量 L2 脚本）的直接参照系。

#### （1）`obra/superpowers`（324,408★，活跃至 2026-11-03）【A】

`superpowers` 不把整条研发生命周期塞进一个巨型技能，而是拆成十余个边界锋利的独立微技能：`brainstorming` → `using-git-worktrees` → `writing-plans`（220 行 / 8.8 KB）→ `executing-plans`（64 行 / 2.3 KB）或 `subagent-driven-development`（7 文件 / 1,171 行 / 56.7 KB）→ `verification-before-completion`（120 行 / 3.6 KB）→ `finishing-a-development-branch`（225 行 / 7.8 KB）【A】。

精读其 2026 年末迭代后的 `subagent-driven-development/SKILL.md`（568 行）与 3 个极薄脚本（`sdd-workspace` 40 行、`task-brief` 41 行、`review-package` 46 行），可提炼出四项极具实战含金量的现代设计【A】：

1. **「先裁决，不卡死（Rulings, not stalls）」**（`SKILL.md` L17–L31）：明确禁止编排器在子任务之间向人类询问「是否继续」或刷进度总结。遇到计划歧义、小冲突或需要微调时，以 Spec 为最高权威自主裁决，在账本中按 `Ruling: <决定> — <原因> — <错判代价>` 登记并继续推进；**仅在四类硬边界才停下来问人**：不可逆/破坏性操作、安全敏感操作、越出当前工作树的外部副作用（合并/推送共享分支/发布）、以及计划崩坏到每条路都只能瞎猜【A】。
2. **文件指针交接治「上下文雪球」**（`SKILL.md` L231–L271，`scripts/task-brief`、`scripts/review-package`）：文中披露了一条血泪实证——真实会话中因主调度不断把前序任务总结贴进后续派发提示词，**单次派发膨胀到 42,000 字符，其中 99% 是粘贴的历史**【A】。新架构用 41 行 `task-brief` 将单任务需求抽出为独立文件，用 46 行 `review-package` 把 `BASE..HEAD` 的 commit 列表、`diff --stat` 与 `git diff -U10` 打包落盘，主调度只传递路径指针；实现者也把详尽报告写盘，只回传状态、提交哈希与一行摘要，彻底阻断主上下文污染【A】。
3. **模型分层律：「轮次成本击败单价（Turn count beats token price）」**（`SKILL.md` L184–L219）：显式要求派发子智能体时**必须指定模型档位**（否则静默继承主会话最贵模型）。并指出反直觉规律：最便宜模型在多步任务上往往多耗 2–3× 轮次，总成本与耗时反升；因此只把最便宜模型用于「计划已给出完整代码的转录 + 测试」或单文件机械修补，中档模型作为审查与散文需求实现的地板，修复循环第 4–5 轮与整分支终审才升级最强模型【A】。
4. **同形小改动批处理 + 禁止子智能体二次套娃**（`SKILL.md` L223–L229, L272–L277）：对跨文件的相同小修（如统一改常量、补字段）合并为单次派发与单次审查；同时硬性规定实现者**绝不自行派生审查子智能体**（防止每个任务白烧一套重复审查席位）【A】。

#### （2）`mattpocock/skills`（330,765★，活跃至 2026-11-19）【A】

Matt Pocock 路线走向了「极简主义 + 现代软件工程切片」的另一端，单个技能短小精悍到令人警醒【A】：

| 技能 | 行数 / 字节 | 核心做法 |
| :--- | :---: | :--- |
| `implement` | 20 行 / 572 B | 只约束三件事：读规范、小步验证、不擅自扩范围 |
| `loop-me` | 37 行 / 2.7 KB | 极简自我迭代回路，无重型状态机 |
| `implement-spec` | 40 行 / 2.2 KB | 读 Spec → 识别下一步垂直切片 → 实现并校验 |
| `to-spec` | 80 行 / 3.2 KB | 对话收敛为精简规约，拒绝填表仪式 |
| `to-tickets` | 110 行 / 5.8 KB | 拆解为**垂直曳光弹切片（Vertical Tracer-Bullet Slices）**与 DAG 依赖图；大范围重构用 Expand-Contract；用上下文指针替代复制粘贴 |
| `wayfinder` | 133 行 / 12.1 KB | 上下文导航路由 |

**核心启示**：两座 30 万星标杆共同验证了一个事实——**真正高频复用的技能，核心指令层极度克制**；哪怕复杂如 `superpowers/subagent-driven-development`，其复杂度也集中在「经真实失败倒逼出的反膨胀工程细节」（防 42k 历史粘贴、防失忆重跑已完成任务、防子智能体套娃），而不是宏大抽象的理论体系。

---

### 2.2 流派二：宿主 Hook 强约束文件记忆（`OthmanAdi/planning-with-files`）

`OthmanAdi/planning-with-files`（28,197★，活跃至 2026-11-21）是最直接落地 Manus 上下文工程思想的社区项目【A】。

其表面上是极简的三文件持久化模式（`task_plan.md` 存阶段与决策、`findings.md` 存调研发现、`progress.md` 存会话日志，辅以 `SKILL.md` 534 行）【A】，但**真正让它超越同类纯提示词技能的，是 `hooks/hooks.json`（101 行）把关键不变式全部挂到了宿主确定性生命周期事件上**【A】：

| 宿主 Hook 事件 | 匹配器 | 确定性动作（由 `claude-hook.sh` 执行） | 替代了哪类脆弱提示词 |
| :--- | :--- | :--- | :--- |
| `SessionStart` | `startup\|resume\|clear\|compact` | 自动检测并注入既有计划状态，恢复上下文 | 「启动/恢复时请先读计划头部」 |
| `UserPromptSubmit` | 全量 | 随用户输入轻量刷新计划关联状态 | 「不要忘记原始目标」 |
| `PreToolUse` | `Write\|Edit\|Bash\|Read\|Glob\|Grep` | 在关键工具调用前自动重申当前计划锚点（Recitation） | 「每 2 次只读后请自觉落盘与复读」 |
| `PostToolUse` | `Write\|Edit` | 写操作后触发状态同步提醒 | 「改完代码记得更新计划复选框」 |
| `PreCompact` | `*` | 在上下文压缩发生前强制保全未落盘关键事实 | 「感觉上下文快满时主动写检查点」 |
| `Stop` | 全量 | 拦截模型提前停机，校验 `task_plan.md` 是否仍有未完成阶段 | 「所有任务未绿前禁止宣告完成」 |

**核心启示**：同样是 Manus 的「文件系统作外部工作记忆 + 复读防失焦」，写在 `SKILL.md` 里靠模型自觉执行，遵守率会随上下文增长断崖下跌；而挂到 `PreCompact` / `Stop` / `SessionStart` 这类确定性 Hook 上，才真正把「希望模型记住」变成了「系统保证触发」。

---

### 2.3 流派三：规约驱动开发 SDD 框架光谱（`spec-kit`、`OpenSpec`、`BMAD-METHOD`）

2025–2026 年 SDD（Spec-Driven Development）迅速分化为两条截然不同的演化方向：

1. **重量级流程/多角色派：`bmad-code-org/BMAD-METHOD`（55,637★，活跃至 2026-11-23）与早期 `github/spec-kit`（151,066★，活跃至 2026-11-22）**【A】：
   - `BMAD-METHOD` 将敏捷团队全套角色（PM / 架构师 / Scrum Master / 开发者 / QA）虚拟化为不同 Persona 提示词与多阶段交接工件，强于 0→1 绿地产品完整文档化，但单次小改动链路极长【A】。
   - `github/spec-kit` 早期以固定流水线（Constitution → Specify → Plan → Tasks → Implement）著称，但在承受广泛存量场景摩擦后，2026 年版本明显走向**模块化多入口**（将 SDD、Bug 修复、创意评估拆为独立入口，并引入 Extensions / Presets / Hooks 扩展机制）【A】。
2. **轻量流式存量派：`Fission-AI/OpenSpec`（75,500★，活跃至 2026-11-23）**【A】：
   - `OpenSpec` 的 README 直接把竞品痛点写成了定位宣言：**「Fluid not rigid（流式而非僵化）、Iterative not waterfall（迭代而非瀑布）、Built for brownfield（为存量代码库而生）」**【A】。
   - 它把全流程压缩为极简三命令闭环：`/openspec-propose`（在独立变更文件夹集中草拟提案与变更集）→ `/openspec-apply-change`（实施）→ `/openspec-archive-change`（将增量变更合并回长期 `specs/` 真相源并归档），显著降低了存量仓库改动的文档摩擦【A】。

**行业权威批评（Birgitta Boeckeler / MartinFowler.com）**：Thoughtworks 资深架构师 Birgitta Boeckeler 在实测 AWS Kiro 与 `github/spec-kit` 后指出，过度形式化的 SDD 存在三大顽疾【B/C】：
- **大锤砸核桃**：修复一个小 Bug 或做局部调整时，强迫走完多层规约-计划-任务模板，耗时远超直接编码；
- **Markdown 溺毙（Death by Markdown files）**：生成成百上千行规约与模板文档后，**人类审阅者根本读不完也审不严**，反而造成「虚假控制感」——审批流走完了，真正的实现偏差却藏在无人细读的冗长文档里；
- **存量演进失配**：代码一旦变更，静态规约文档极速腐化，维护多层同步文档的税负常超过收益。

---

### 2.4 流派四：新鲜上下文波次编排器（`get-shit-done` → `open-gsd/gsd-core`）

`gsd-build/get-shit-done` 曾凭借「解决上下文腐化（Context Rot）」理念飙升至 **64,114★**，但在 2026 年中因维护者争议已标记为 **`archived: true`**，社区分叉并延续为 **`open-gsd/gsd-core`（11,778★，活跃至 2026-11-23）**【A】。

其核心架构非常鲜明（精读 `open-gsd/gsd-core` README）【A】：
- **五步主干**：`Discuss`（对齐偏好）→ `Plan`（研究 + 制定可验证任务）→ `Execute`（按依赖分层为多个 **Wave 波次**，每波并行派发独立子智能体，每个子智能体拥有**全新满血 200k 上下文**）→ `Verify`（自动验证 + UAT）→ `Ship`【A】。
- **薄编排器原则**：主调度自身尽量只保持极低上下文占用，把重活全部卸载到一次性新鲜执行器，通过 `.planning/` 目录里的阶段文件传递最小必要上下文【A】。
- **反面警示**：`gsd-build/get-shit-done`（64k★）与 `RooCodeInc/Roo-Code`（24.2k★，2026-05-15 归档）双双归档提醒工程团队——**重度耦合某一社区单一维护者工具链存在治理断档风险**，而基于开放标准（`SKILL.md` + 宿主原生原语）的低耦合架构具有更长生命力【A】。

---

### 2.5 流派五：外部自主循环 Harness（Ralph 谱系与 Anthropic 官方演进）

当任务真正走向数小时级、跨多窗口的无人值守执行，社区与前沿实验室不约而同走出提示词层，进入 **L3 外部循环 Harness**：

#### （1）Ralph 谱系：`snarktank/ralph`（22,324★）与 `frankbria/ralph-claude-code`（9,739★）【A】

- **极简原教旨 `snarktank/ralph`**（最后更新 2026-02-02）：核心就是一个外部 `ralph.sh` 循环脚本——每轮启动**全新的** AI CLI 实例，读取磁盘上的三件套（`prd.json` 结构化需求清单、`progress.txt` 仅追加进度日志、`git log` 真实代码史），完成一个故事后提交并退出；上下文彻底清零，从根源消灭单会话 Context Rot【A】。
- **工业加固版 `frankbria/ralph-claude-code`**（活跃至 2026-11-14，含 784 项测试）：精读其 `lib/circuit_breaker.sh` 与 README 可见，它把长程自治最关键的安全机制全部做成了**确定性外部代码**【A】：
  1. **外置三态熔断器**：`CLOSED` → `HALF_OPEN` → `OPEN` 的状态与连续无进展计数、同错误重复计数持久化在 `.ralph/.circuit_breaker_state` JSON 中，由 Bash 脚本在每轮结束后客观比对 `git diff` 变化量与错误指纹自动流转，**不依赖 LLM 自我申报**【A】；
  2. **双条件退出门禁**：必须同时满足「启发式完成信号」与「显式 `EXIT_SIGNAL` 校验」才结束循环，防止模型过早停工或陷入死循环【A】；
  3. **真实限流与超时**：由外部进程控制每小时 API 调用上限、单轮执行超时与五小时额度退避【A】。

#### （2）Anthropic 2025→2026 官方 Harness 演进与「简化律」【B】

Anthropic 工程博客先后发布两篇里程碑式文章，清晰勾勒出长程 Agent 架构的两段演进【B】：
- **第一阶段（2025-11，《Effective harnesses for long-running agents》）**：解决「跨上下文窗口轮班交接（Shift-Work）」问题，拆出 **Initializer Agent**（首轮初始化环境 `init.sh` 并把需求拆成细粒度 `feature_list.json`）与 **Coding Agent**（逐项推进、写 `claude-progress.txt` + Git 提交）。明确指出**用 JSON 而非 Markdown 存机器需维护的完成状态**，因为模型更不容易意外破坏或篡改 JSON 结构，且默认全项 `FAIL`（Default-FAIL 契约）【B】。
- **第二阶段（2026-03，《Harness design for long-running application development》）**：针对单智能体自审过于宽容的顽疾（讨好与敷衍验收），引入 **Planner → Generator ↔ Evaluator** 三角闭环，让独立 Evaluator 借助真实工具（如 Playwright MCP）客观判分与打回【B】。
- **最关键的反身性洞见（Harness Simplification）**：Anthropic 明确提出——**Harness 中的每一个脚手架组件，本质上都在编码一条「模型自身做不到」的假设**；随着新一代模型能力提升（如上下文焦虑减弱、自主分解增强），必须定期做消融实验并**拆掉冗余脚手架**，避免历史补丁固化为性能与成本负资产【B】。

---

### 2.6 流派六：结构化任务图与平台原生原语

1. **`gastownhall/beads`（28,939★，活跃至 2026-11-22）**【A】：Steve Yegge 推出的 Agent 专属分布式 Issue/任务图工具，底层基于 Dolt（带 Git 版本语义的 SQL 数据库）提供基于哈希的 ID（避免多 Agent/多分支并发建任务时整数 ID 合并冲突）与一等依赖图。其 README 直言：**「Do not use markdown TODO lists for task tracking」**，认为自由格式 Markdown 在多智能体长程协作下难以精准查询就绪前沿（Ready Frontier）与并发安全更新【A】。
2. **`eyaltoledano/claude-task-master`（28,526★，最近推送 2026-04-28）**【A】：以 PRD 自动解析为 JSON 任务树并通过 MCP/CLI 暴露给 Agent 闻名，2026 年下半年活跃度已明显放缓，侧面反映原生任务原语与轻量化方案对其空间形成了挤压【A】。
3. **宿主原生原语的快速扩张**【A/B】：
   - **Claude Code**：原生提供 Plan Mode、独立上下文 Subagents、可编程 Hooks、以及实验性多代理协作 **Agent Teams**（实测/官方披露约带来 **~7× token 成本**，仅适合高度并行且解耦的探索/审查，不适合常规串行编码）【B】；
   - **OpenAI Codex Harness Engineering（2026）**：提出面向 Agent-First 代码库的三大支柱——**极短 `AGENTS.md`（约 100 行，仅作地图/TOC 而非百科全书）+ 渐进式文档披露 + 机械化 Linter 与定期 Doc-Gardening Agent**【B】；
   - **Antigravity**：原生内置任务清单（`update_steps`）、隔离工作区子智能体（`invoke_subagent` `share`/`branch`）、Python 编排工作流（`run_workflow`）与多代理协同（`swarm`）【A】。

---

## 3. 跨流派关键工程共性与底层实证规律

把六大流派与前沿实证研究并置，五条跨框架收敛的底层规律浮出水面：

### 3.1 指令膨胀反噬律（Instruction Budget & Context Tax）

多组独立实证研究从不同维度证明了同一件事——**给 Agent 塞进过多规程、模板与冗余约束，不是「免费的多重保险」，而是会实打实降低成功率并推高账单**：

| 研究 / 规范 | 来源与时间 | 核心量化发现 | 证据等级 |
| :--- | :--- | :--- | :---: |
| **Curse of Instructions** | ICLR 2025 | 模型同时满足 `N` 条独立约束的概率近似呈指数衰减（`P = p^N`）；条数越多，联合合规率迅速塌方 | 【B】 |
| **IFScale** | Distyl AI（2025） | 指令规模越过约 **150–200 条**阈值后，即使前沿推理模型也会出现明显首位偏置（Primacy Bias），系统性忽略靠后的约束 | 【B】 |
| **Context Rot** | Chroma Research（2025-07） | 性能并非在触碰窗口上限时才骤降，而是在远未满窗前便随无关噪音累积持续软腐化 | 【B】 |
| **Evaluating AGENTS.md** | ETH Zurich SRI Lab（Gloaguen et al., 2026） | LLM 自动生成的仓库上下文文件使任务成功率**下降约 3%**；人类手写文件仅带来**约 +4% 微弱提升**；两类文件一律导致**推理成本增加 >20%**（因模型过度服从，触发多余遍历与防御性动作）。作者结论：删掉模型自行读代码即可发现的常规说明，仅保留「不可自行发现的踩坑雷区」 | 【B】 |
| **Agent Skills Specification** | `agentskills.io` 官方规范 | 确立三层渐进披露：启动元数据 ~100 tokens → 激活 `SKILL.md` **严格建议 < 500 行 / < 5,000 tokens** → `references/` 与 `scripts/` 仅在明确触发时按需读取 | 【B】 |

### 3.2 确定性外置定律（Externalize Determinism）

跨 `planning-with-files`、`ralph-claude-code`、OpenAI Harness Engineering 与本仓库 `doc-governance` 的共同结论是：

- **适合留在提示词（L1）的**：判断标准、权衡原则、审查视角、非显然的领域雷区、以及何时触发何种工具的路由表；
- **必须外置到代码/Hook/测试（L2/L3）的**：熔断计数器、预算/时间上限、文件格式/断链门禁、上下文压缩前落盘触发、任务完成前的停机拦截、大文本（任务规约与 Diff）打包传递。
- **最危险的错位（「提示词伪运行时」）**：把本需外部运行时状态机才能度量的数学公式（如精确 token 占比上限、墙钟时间比例、每 N 次工具调用强写盘）写成纯 Markdown 提示词，再写单元测试去断言这些中文句子出现在 Markdown 里——这既无法被 LLM 可靠执行，又锁死了后续重构空间。

### 3.3 上下文经济性与 Manus 经验的二次演化

2025 年 7 月 Manus AI 联合创始人季逸超（Peak Ji）发表《Context Engineering for AI Agents》【B/C】，提出 KV-Cache 命中率优先（前缀稳定、仅追加不修改历史）、文件系统卸载与 `todo.md` 末尾复读三大原则，深刻影响了包括 `goal-loop` 与 `planning-with-files` 在内的整代技能。

但需要高度注意的是 **2025 年底至 2026 年的二次演化**：
- 社区复盘与后续实践显示，**过高频率地重写 `todo.md` / scratchpad 反而造成大量额外工具轮次与上下文 token 浪费**，且容易破坏前缀缓存效率；Manus 后续也逐步向专用 Planner / Agent-as-a-Tool 与结构化工具隔离演进【B/C】；
- 同期 `superpowers` 用 `task-brief` / `review-package` 文件指针替代主上下文粘贴【A】，OpenAI 用约 100 行极简 `AGENTS.md` 做渐进地图【B】，三者殊途同归：**上下文是按字节计费且会衰减的稀缺注意力预算，不是免费的草稿纸**。

### 3.4 自治节奏升级：从「步步审批」到「边界内自主裁决」

长程任务的人机协同正从两种极端向中间最优解收敛：
- 左极端（早期瀑布 SDD）：每小步都输出长篇文档等人类签字，制造「审阅疲劳 + 会话长时间空转」；
- 右极端（盲目全自动）：无护栏一路狂奔，改坏核心契约或推送危险提交；
- **2026 收敛态（`superpowers` + `OpenSpec`）**：**事前对准关键契约与不可逆边界** → **事中在安全边界内自主裁决并记录账本（Rulings, not stalls）** → **事后用独立验证/审查门禁 + 精简决策摘要接受人类抽检**【A】。

### 3.5 DAG 垂直切片优于线性瀑布拆解

`mattpocock/skills`（`to-tickets`）、`gsd-core`（Wave 执行）与 `beads`（依赖图）共同强调：把长任务按「数据库层 → 后端层 → 前端层 → 测试层」水平切片或严格线性编号，会造成前期无法验证、后期集成爆炸；按**可独立测试的垂直曳光弹切片（Vertical Tracer-Bullet Slices）**与显式依赖前沿（DAG）组织任务，既能尽早暴露集成风险，又能天然识别哪些切片可安全并行、哪些同形微改应合并批处理【A】。

---

## 4. 行业典型反模式与踩坑地图

| 编号 | 反模式名称 | 典型表现 | 行业真实案例 / 依据 | 后果 |
| :---: | :--- | :--- | :--- | :--- |
| **AP-1** | **提示词伪运行时** | 在纯 Markdown 提示词中设计复杂数学预算公式、多态熔断状态机或精确频次规则，却无外部运行器计量 | 对比 `ralph-claude-code`（外置 Bash 状态机）【A】与纯提示词约束的失效率【B】 | 规则形同虚设，徒增数百行指令噪音与 >20% 推理成本 |
| **AP-2** | **Markdown 溺毙 / 大锤砸核桃** | 小任务也被迫填充多份模板与冗长规约；多层文档互相镜像 | Birgitta Boeckeler 对 Kiro / 早期 `spec-kit` 的批评【B/C】；`OpenSpec` 的反向定位【A】 | 人类审阅形同虚设，文档滞后代码，开发摩擦激增 |
| **AP-3** | **主调度历史滚雪球** | 把已完成任务总结、全量计划或大段 Diff 直接粘贴进后续子智能体提示词 | `superpowers` 披露单次派发膨胀至 42k 字符（99% 为历史）【A】 | 注意力被稀释、重复派发已完成任务、成本非线性暴涨 |
| **AP-4** | **盲目多代理与套娃审查** | 对强耦合任务开多代理并行写同一模块，或允许子执行器自行派生审查员 | Claude Code Agent Teams ~7× token 税【B】；`superpowers` 禁子智能体套娃审查【A】 | 合并冲突频发、审查席位双倍浪费、收益远低于成本 |
| **AP-5** | **脆弱的 Markdown 正则状态机** | 编写数百行脚本用正则解析和回写自由格式 Markdown 充当数据库，既没人调又难维护 | `beads` 明确反对 Markdown TODO 追踪【A】；Anthropic 改用 JSON 存机器状态【B】 | 代码债高、一旦人类微调标题或缩进即失配、被原生原语绕过 |
| **AP-6** | **只做加法不做消融** | 每次踩坑就往提示词里补一段铁律与模板，从未随模型升级或零使用率清理存量 | Anthropic Harness Simplification 原则【B】；ETH Zurich 上下文成本研究【B】 | 技能体积持续膨胀，新老规则自相矛盾、跨技能越界 |

---

## 5. 对 `goal-loop` 的启示与下篇衔接

综合本次六大流派调研与五条底层规律，审视本仓库 `goal-loop` 时应抓住四把标尺：

1. **实证活跃度标尺**：哪些机制在真实交付中被反复用到（核心护城河），哪些脚本、模板与子协议在实战中长期零使用（死重候选）？
2. **层位匹配标尺**：`goal-loop` 哪些条款属于「提示词伪运行时」（在 L1 假装做 L2/L3 的事），哪些本应交给宿主原生原语或极薄脚本？
3. **指令预算标尺**：参考 `agentskills.io`（`< 500 行` / `< 5,000 tokens`）与 ETH Zurich（`>20%` 成本税），`goal-loop` 当前的 17 文件 / 125 KB 架构在按需加载与总维护面上是否过度膨胀？
4. **前沿能力吸收标尺**：`superpowers` 的文件指针交接（`task-brief`/`review-package`）、模型分层、同形批处理、`Rulings not stalls`，`mattpocock/skills` 的垂直切片，以及 `planning-with-files` 的可选轻量 Hook，哪些值得低成本引入？

上述全部问题将在配套评估报告 **[2026-11-23-goal-loop-architecture-evaluation.md](./2026-11-23-goal-loop-architecture-evaluation.md)** 中，结合 `goal-loop` 全量源码与本仓 28 份真实交付计划的实证审计逐一作答，并给出可执行的分阶段重构方案。

---

## 6. 一手参考来源清单

### 6.1 开源项目与本地源码（均为 2026-11-23 实测【A】）

- `mattpocock/skills`（330,765★，pushed `2026-11-19`）：https://github.com/mattpocock/skills （并精读本地 `implement` / `implement-spec` / `loop-me` / `to-spec` / `to-tickets` / `wayfinder`）
- `obra/superpowers`（324,408★，pushed `2026-11-03`）：https://github.com/obra/superpowers （并精读本地 `.agents/skills/subagent-driven-development/` 全部 7 文件与 `writing-plans` / `executing-plans` / `verification-before-completion` / `finishing-a-development-branch`）
- `anthropics/claude-code`（156,746★，pushed `2026-11-22`）：https://github.com/anthropics/claude-code
- `github/spec-kit`（151,066★，pushed `2026-11-22`）：https://github.com/github/spec-kit
- `Fission-AI/OpenSpec`（75,500★，pushed `2026-11-23`）：https://github.com/Fission-AI/OpenSpec
- `cline/cline`（71,837★，pushed `2026-11-22`）：https://github.com/cline/cline
- `gsd-build/get-shit-done`（64,114★，已归档）：https://github.com/gsd-build/get-shit-done
- `open-gsd/gsd-core`（11,778★，pushed `2026-11-23`）：https://github.com/open-gsd/gsd-core
- `bmad-code-org/BMAD-METHOD`（55,637★，pushed `2026-11-23`）：https://github.com/bmad-code-org/BMAD-METHOD
- `gastownhall/beads`（28,939★，pushed `2026-11-22`）：https://github.com/gastownhall/beads
- `eyaltoledano/claude-task-master`（28,526★，pushed `2026-04-28`）：https://github.com/eyaltoledano/claude-task-master
- `OthmanAdi/planning-with-files`（28,197★，pushed `2026-11-21`）：https://github.com/OthmanAdi/planning-with-files （精读 `SKILL.md` 与 `hooks/hooks.json`）
- `RooCodeInc/Roo-Code`（24,239★，已归档 `2026-05-15`）：https://github.com/RooCodeInc/Roo-Code
- `snarktank/ralph`（22,324★，pushed `2026-02-02`）：https://github.com/snarktank/ralph
- `frankbria/ralph-claude-code`（9,739★，pushed `2026-11-14`）：https://github.com/frankbria/ralph-claude-code （精读 README 与 `lib/circuit_breaker.sh`）

### 6.2 实验室工程文、规范与行业评述（【B】/【C】）

- Anthropic Engineering, *Effective harnesses for long-running agents* (Nov 2025) & *Harness design for long-running application development* (Mar 2026), https://www.anthropic.com/engineering 【B】
- OpenAI Engineering, *Harness Engineering: Leveraging Codex in an Agent-First World* (2026) 【B】
- Manus AI (Yichao "Peak" Ji), *Context Engineering for AI Agents* (Jul 2025) 【B/C】
- Agent Skills Specification (*Progressive Disclosure & Sizing Guidance*): https://agentskills.io/specification 【B】
- Birgitta Boeckeler, *Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl*, MartinFowler.com 【B/C】

### 6.3 学术与实证基准研究（【B】）

- Gloaguen, Mündler, Mueller, Raychev, Vechev (ETH Zurich SRI Lab & LogicStar.ai, 2026), *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?* 【B】
- *Curse of Instructions: Large Language Models Cannot Follow Multiple Instructions at Once* (ICLR 2025) 【B】
- Distyl AI (2025), *IFScale: Benchmarking Instruction Following at Scale* 【B】
- Chroma Research (Jul 2025), *Context Rot: How Increasing Input Tokens Impacts LLM Performance* 【B】
