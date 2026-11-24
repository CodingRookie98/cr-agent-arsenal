# CR 公共技能库与文档总索引 (CR Public Skills Knowledge Base)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-INDEX-2026
> - **当前版本**: V1.53.0 (执行 Wave 3：`taste-driven-designer` 与 `frontend-qa-gate` V2.0 瘦身、去正则与真实磁盘证据化升级)
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-10-04

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.53.0** | 2026-11-24 | AI Agent | 王辉 | **Wave 3 前端双技能 V2.0 重构**：更新 §2/§3 `taste-driven-designer` V2.0 与 `frontend-qa-gate` V2.0 描述，并在 §4 补登 Wave 3 实施计划 |
| **V1.52.0** | 2026-11-24 | AI Agent | 王辉 | **Wave 2C `doc-governance` V3.0 三刀切割（ADR-0005）**：移除 `llms.txt` 与 `_llms/` 机器地图入口，更新 §2/§3 `doc-governance` V3.0 与 §2.5 操作手册描述，流转 RFC-0003/0005/0006 为 `Superseded` 并在 §4 补登 ADR-0005 与 Wave 2C 实施计划 |
| **V1.51.0** | 2026-11-24 | AI Agent | 王辉 | **Wave 2B `dual-round-review` V3.0 瘦身与现代化升级**：更新 §2/§3 `dual-round-review` 描述（退役 Artifact 支线、Scoped Delta 零缺陷免 R2、Untrusted Data 防注入与空结果优先），并在 §4 补登 Wave 2B 实施计划 |
| **V1.50.0** | 2026-11-23 | AI Agent | 王辉 | **Wave 2A `goal-loop` V3.0 瘦身与现代化升级**：更新 §2/§3 `goal-loop` 描述（五主阶段、三轨分流、事件驱动上下文工程与文件指针交接），并在 §4 补登 Wave 2A 实施计划 |
| **V1.49.0** | 2026-11-23 | AI Agent | 王辉 | **Wave 1 架构瘦身（ADR-0004 + `clarification-protocol` V2.0.0）**：从现役技能/设计书表移除 `agy-delegation-workflow`，同步 `clarification-protocol` V2.0.0 描述，并在 §4 补登 `ADR-0004` 与 Wave 1 实施计划 |
| **V1.48.0** | 2026-11-23 | AI Agent | 王辉 | **Wave 0 止血修复计划登记**：在 §4 补登 `2026-11-23-wave0-skill-bugs-stabilization.md`（修复全仓现红测试与 12 处实证技能源码缺陷） |

---

## 1. 概述 (Overview)

本项目为现代 AI 智能体（Claude Code / Antigravity / Cursor 等）研发与多智能体协作平台提供工业级可复用公共技能（Public Agent Skills）与工程规范体系。

* 📋 **知识库治理标准**: [docs/GOVERNANCE.md](./GOVERNANCE.md)（V2.0.0）
* 📦 **变更日志**: [docs/project/changelog.md](./project/changelog.md)（按交付单元聚合的可交付成果）
* 🧭 **智能体路由规则**: [docs/AGENTS.md](./AGENTS.md)（读取顺序与硬约束，≤30 行）
* 🔧 **本仓私有门禁与待办工具**: `scripts/doc-gates/`（三道文档门禁）· [scripts/backlog/README.md](../scripts/backlog/README.md)

---

## 2. 📚 核心技能架构设计 (Explanation: Architecture Specifications)

以下设计书记录了各核心技能的理论来源、第一性原理、架构拓扑与实现细节：

| 技能标识 | 核心定位与理论支柱 | 架构规格文档 |
| :--- | :--- | :--- |
| **`doc-governance`** | V3.0 Convention-First 轻内核与公私分离架构（ADR-0005）：公共技能仅保留 Diátaxis / RFC 结晶 / MADR / 变更联动规程与通用 `--exclude` 断链扫描器；私有门禁与待办管理分别下沉 `scripts/doc-gates/` 与 `scripts/backlog/` | [doc-governance-design.md](./explanation/architecture/doc-governance-design.md) |
| **`goal-loop`** | V3.0 五主阶段（`Align → Plan → Execute → Verify → Close`）与三轨分流、事件驱动上下文工程、极薄文件指针交接、自适应测试分级裁定与双轮终审的工业级目标收敛循环 | [goal-loop-design.md](./explanation/architecture/goal-loop-design.md) |
| **`dual-round-review`** | V3.0 红队第一性原理穿透 + 元架构师审判校准；支持 Full / Light / Scoped Delta（`delta-r1` 零缺陷免 R2）与能力档位分层、Untrusted Data 防注入、空结果优先、退役 0 用 Artifact 支线（吸收为通用非代码提示），保留 Write-Once 交付凭据归档与机械门禁 | [dual-round-review-design.md](./explanation/architecture/dual-round-review-design.md) |
| **`taste-driven-designer`** | V2.0 源于 Anshu Chimala AI 双钻模型：D1 `Persuade`/`Operate` 表面模式分流 + 纯标准库外部种子 + 5 列极简盲比/4+1 Critic 闭环（内置无截图降级与多模态门控）+ 2026 10 大 AI Tells 与残酷减法，五域运行时验收 SSOT 归位 `frontend-qa-gate` | [taste-driven-designer-design.md](./explanation/architecture/taste-driven-designer-design.md) |
| **`frontend-qa-gate`** | V2.0 双轨前端产物验收硬门禁：Tier 1 23 项自动化阻断（`D-R` 5 / `D-S` 8 / `D-A` 7 / `D-P` 3）+ Tier 2 4 项 `pending_human` 人工/真机签收 + 现代探针编排 + Fail-Closed 真实磁盘证据 JSON 门禁（`check-qa-report.py` Schema v2）+ 四类回流路由 | [frontend-qa-gate-design.md](./explanation/architecture/frontend-qa-gate-design.md) |
| **`clarification-protocol`** | V2.0.0 精简微技能：先读代码自查事实、术语先行、按「依赖强度 × 实现影响」筛问与 ≤5 题软预算、原地维护 4 列单表决策台账（已决项 / 已排除边界 / 默认假设）与出口三问内联自核（目标 / 边界 / 矛盾） | [clarification-protocol-design.md](./explanation/architecture/clarification-protocol-design.md) |
| **Backlog 治理最佳实践** | 结合软件工程史（精益/看板/Shape Up）与 AI 上下文工程的 14 项待办治理法则 | [backlog-governance-best-practices.md](./explanation/analysis/backlog-governance-best-practices.md) |
| **LLM-WIKI 社区实现调研** | 六条实现路线（规范纯文件 / 索引检索 / 仓库生成 / 知识图谱 / 检索即答案 / 确定性编译器）+ 十类工程难点（含 21× token、漂移检出盲区、lint 召回 ~50%）+ 十二维对照审计与 P0–P2 改造建议 | [llm-wiki-implementation-research.md](./explanation/analysis/llm-wiki-implementation-research.md) |
| **长程 Agent 研发闭环同类调研** | 2026-11-23 六大流派（`superpowers` / `mattpocock/skills` / `planning-with-files` / `spec-kit` & `OpenSpec` & `BMAD` / `gsd-core` / `ralph` & Anthropic Harness / `beads` & 原生原语）源码级解剖、五条实证规律与六类行业反模式 | [2026-11-23-goal-loop-peer-research.md](./explanation/analysis/2026-11-23-goal-loop-peer-research.md) |
| **`goal-loop` 过度设计与重构评估** | 17 文件 / 125 KB 全量体量与 28 份真实计划活跃度实证审计、十二维横向对标、六大过度设计与腐化病灶诊断、五项护城河甄别及 P0–P2 分阶段瘦身升级路线图 | [2026-11-23-goal-loop-architecture-evaluation.md](./explanation/analysis/2026-11-23-goal-loop-architecture-evaluation.md) |
| **AI 代码审查与对抗验证同类调研** | Anthropic `/code-review`（112 行 Per-Issue 并行证伪）、OpenAI Codex（95 行空结果优先 + JSON Schema）、`superpowers`、`mattpocock`、`PR-Agent` 与 6 项前沿实证研究 | [2026-11-23-dual-round-review-peer-research.md](./explanation/analysis/2026-11-23-dual-round-review-peer-research.md) |
| **`dual-round-review` 过度设计与重构评估** | 24 文件 / 236.8 KB 体检、17 归档 / 70 报告实证 ROI、`_UNIT_RX` 17/17 失效与链接剥离双 Bug、0 用 Artifact 模式与 V3.0 瘦身升级方案 | [2026-11-23-dual-round-review-architecture-evaluation.md](./explanation/analysis/2026-11-23-dual-round-review-architecture-evaluation.md) |
| **Docs-as-Code 与 Agent-First 文档增量调研** | 衔接既有 LLM-WIKI 调研，增量覆盖 `lychee`/`vale`/`markdownlint`/`madr`、Diátaxis 中小仓反噬、OpenAI/Anthropic/ETH Zurich 实证与 `addyosmani`/`anthropics` 公共技能边界法则 | [2026-11-23-doc-governance-peer-research.md](./explanation/analysis/2026-11-23-doc-governance-peer-research.md) |
| **`doc-governance` 过度设计与重构评估** | 598.6 KB 巨无霸体量与 9 子系统解构、12 脚本可移植性审计、390 commits 治理税实证、7 处真实源码 Bug 与三刀切割瘦身蓝图 | [2026-11-23-doc-governance-architecture-evaluation.md](./explanation/analysis/2026-11-23-doc-governance-architecture-evaluation.md) |
| **无头 Coding Agent 委派与多 CLI 编排调研** | 10 个高星多 CLI/无头编排标杆（`superpowers`/`claude -p`/`codex exec`/`gastown`/`agent-orchestrator`/`vibe-kanban` 停运信号、`agy 1.5.14` 实测）与原生时代剩余生态位裁定 | [2026-11-23-agy-delegation-workflow-peer-research.md](./explanation/analysis/2026-11-23-agy-delegation-workflow-peer-research.md) |
| **`agy-delegation-workflow` 过度设计与重构评估** | 28 份计划 0% 实战使用率审计、四重硬绑定与 70%+ 重叠解剖、脚本安全隐患、仅存 3 项真资产与「抽资产退役 vs 止血」去向方案 | [2026-11-23-agy-delegation-workflow-architecture-evaluation.md](./explanation/analysis/2026-11-23-agy-delegation-workflow-architecture-evaluation.md) |
| **AI 需求澄清与交互收敛同类调研** | `spec-kit` `/speckit.clarify`（≤5 题原地回写）、`superpowers` `brainstorming`、`mattpocock` `grilling`（28 行）、`OpenSpec` 及 *HumanEvalComm*/*ClarEval*/*ClarifyCodeBench* 学术实证 | [2026-11-23-clarification-protocol-peer-research.md](./explanation/analysis/2026-11-23-clarification-protocol-peer-research.md) |
| **`clarification-protocol` 过度设计与重构评估** | 8 篇真实 RFC 实跑 0/8 通过、脚本 8 类硬伤（含空列放行 `rc=0`）、L72 空指针预算、双模板 Split-Brain 与 60–80 行微技能去壳提纯方案 | [2026-11-23-clarification-protocol-architecture-evaluation.md](./explanation/analysis/2026-11-23-clarification-protocol-architecture-evaluation.md) |
| **AI 前端审美设计、反 Slop 与 Critic 同类调研** | Anthropic `frontend-design`（9.4 KB，2026 新一代 AI Slop）、`ui-ux-pro-max`（153k★ 策展库）、`pbakaus/impeccable`（115k★ 表面模式 + 44 微剧本 + 双隔离评审）与 `vercel/web-design-guidelines` | [2026-11-23-taste-driven-designer-peer-research.md](./explanation/analysis/2026-11-23-taste-driven-designer-peer-research.md) |
| **`taste-driven-designer` 过度设计与重构评估** | 13 文件 / 74.9 KB 体检、`generate-seed.py` Park-Miller 零状态数学 Bug、设计书误覆写断言「无测试」、与 `frontend-design` >70% 重叠及三档提纯方案 | [2026-11-23-taste-driven-designer-architecture-evaluation.md](./explanation/analysis/2026-11-23-taste-driven-designer-architecture-evaluation.md) |
| **AI 前端运行时验收与浏览器 QA 同类调研** | `gstack`（142k★）、`chrome-devtools-mcp`（58.9k★）、`agent-browser`（53.5k★ `dogfood`）、`playwright-mcp`（40k★）、`axe-core` / `lhci` 与三层黄金验收架构 | [2026-11-23-frontend-qa-gate-peer-research.md](./explanation/analysis/2026-11-23-frontend-qa-gate-peer-research.md) |
| **`frontend-qa-gate` 过度设计与重构评估** | 73.3% 代码验表 / 0 行采集、5 组对抗探针全击穿 Exit 0、无头环境永久 BLOCKED 死锁机理与「探针编排实采化 vs 吸收合并」方案 | [2026-11-23-frontend-qa-gate-architecture-evaluation.md](./explanation/analysis/2026-11-23-frontend-qa-gate-architecture-evaluation.md) |
| **全仓 7 技能组合横向全景评估与治理总路线图** | 汇总全仓 15 篇调研/评估一手数据：7 技能去留评级表、五大跨技能系统性共病（Goodhart 异化/正则验 MD/Split-Brain/IFScale/公私混淆）、Wave 0–3 总路线图（预计瘦身 70%–75%）与五条防腐宪法 | [2026-11-23-arsenal-skills-portfolio-overview.md](./explanation/analysis/2026-11-23-arsenal-skills-portfolio-overview.md) |

---

---

## 2.5 🎓 上手与操作指南 (Tutorials & How-To)

面向**第一次使用**与**遇到具体问题**的两类读者。教程按学习路径组织（跟着做即可），How-To 按任务组织（直奔步骤）。

| 文档 | 类型 | 解决什么问题 |
| :--- | :--- | :--- |
| [5 分钟上手：装技能 / 跑门禁 / 定位文档](./tutorials/quick-start.md) | Tutorial | 完全没接触过本仓库，想最短路径跑通一次 |
| [把技能安装到宿主 Agent](./how-to/install-skills.md) | How-To | 本仓库开发 vs 外部项目安装的选型、命令、验证与卸载 |
| [执行文档门禁并解读失败](./how-to/run-doc-gates.md) | How-To | 三道本仓门禁各查什么、红了怎么改、pre-commit 与 CI 怎么接 |
| [文档治理故障排查](./how-to/troubleshoot-doc-governance.md) | How-To | 按症状索引的常见故障排查：目录断链、`--exclude` exit 2、体量超限、文档三态、路由守卫等 |

> 象限索引：[tutorials/index.md](./tutorials/index.md) · [how-to/index.md](./how-to/index.md)

---
## 3. 📖 技能工程落地规程 (Skill Specifications & References)

各技能的独立安装规范与执行规程如下：

| 技能名称 | 规程入口 | 核心能力描述 |
| :--- | :--- | :--- |
| **`doc-governance`** | [doc-governance 规程](../skills/doc-governance/SKILL.md) | Convention-First 文档工程与知识库治理 V3.0（Diátaxis 四象限、RFC 结晶、MADR 决策、变更联动矩阵与通用 `--exclude` 断链扫描器） |
| **`goal-loop`** | [goal-loop 规程](../skills/goal-loop/SKILL.md) | 工业级端到端长任务目标实现循环 V3.0（五主阶段、三轨分流、事件驱动检查点、文件指针交接、自适应测试与 3-Tries 非阻塞熔断） |
| **`dual-round-review`** | [dual-round-review 规程](../skills/dual-round-review/SKILL.md) | 对抗性双轮代码终审硬门禁 V3.0（红队穿透 + 元架构师审判）；支持 Full / Light / Scoped Delta 三模式、能力档位分层、Untrusted Data 防注入与空结果优先，保留 Write-Once 归档与机械门禁 |
| **`taste-driven-designer`** | [taste-driven-designer 规程](../skills/taste-driven-designer/SKILL.md) | 品味驱动设计三阶段流程 V2.0（`Persuade`/`Operate` 表面模式、纯标准库 SSoT 种子、5 列极简盲比/4+1 Critic 闭环、2026 10 大 AI Tells 与残酷减法）；能力门控、宿主无关、可降级 |
| **`frontend-qa-gate`** | [frontend-qa-gate 规程](../skills/frontend-qa-gate/SKILL.md) | 前端产物验收双轨硬门禁 V2.0（Tier 1 23 项自动化阻断 + Tier 2 4 项 `pending_human` 人工/真机签收、现代探针编排、Schema v2 真实磁盘证据 JSON 门禁与四类回流路由） |
| **`clarification-protocol`** | [clarification-protocol 规程](../skills/clarification-protocol/SKILL.md) | 需求澄清与收敛规程 V2.0.0（先自查事实、术语先行、按影响筛问与 ≤5 题软预算、4 列单表决策台账去重、出口三问内联自核）；由全局提示词 §4 一行指针按需唤起 |

---

## 4. 🚀 工程演进与管理 (Project Governance: Plans & Decisions)

| 计划标识 | 目标 | 计划文档 |
| :--- | :--- | :--- |
| **`goal-loop` V2.0** | 宿主无关执行适配器、计划文件唯一真相源、tracker 派生化与单测 | [2026-09-14-goal-loop-v2-refactor.md](./project/plans/2026-09-14-goal-loop-v2-refactor.md) |
| **`dual-round-review` V2.0** | 宿主无关派发、审查记录锚点、Light 模式与条件维度 | [2026-09-14-dual-round-review-v2.md](./project/plans/2026-09-14-dual-round-review-v2.md) |
| **派发预算与人机契约** | 派发超时收口、并行预算制编排、需求方/批准人/验收口径字段 | [2026-09-16-dispatch-budget-and-human-contract.md](./project/plans/2026-09-16-dispatch-budget-and-human-contract.md) |
| **术语先行与维护通道** | 术语对齐前置与影响分级豁免、Maintenance-Patch 通道、术语 SSOT 落地 | [2026-09-16-terminology-first-and-maintenance-track.md](./project/plans/2026-09-16-terminology-first-and-maintenance-track.md) |
| **`taste-driven-designer` V1.0** | 新建品味驱动设计技能：SKILL.md + references + templates + seed 脚本 + pytest + 设计书与全套注册 | [2026-09-20-taste-driven-designer.md](./project/plans/2026-09-20-taste-driven-designer.md) |
| **`frontend-qa-gate` V1.0** | 新建前端产物验收技能：SKILL.md + references + templates + 报告校验脚本 + 契约测试 + 设计书与全套注册；同步补强 taste Gate A 与 goal-loop P3.5 挂载点 | [2026-09-21-frontend-qa-gate.md](./project/plans/2026-09-21-frontend-qa-gate.md) |
| **`frontend-qa-gate` 后续待办闭环** | 闭环交付遗留三项待办：「：无」声明变体误拒、跨技能相对链接断链自检、结论列 `N/A` 白名单（Maintenance-Patch 通道，已闭环） | [2026-09-21-qa-gate-followups.md](./project/plans/2026-09-21-qa-gate-followups.md) |
| **Critic 门禁加固 V1.1** | 实跑反证驱动：绝对评分门禁换代三信号门禁，补版本回执/鉴别力自检/冲突仲裁/评审账本 | [2026-09-20-critic-gate-hardening.md](./project/plans/2026-09-20-critic-gate-hardening.md) |
| **RFC-0001 审查报告归档契约** | 为 `dual-round-review` 引入交付凭据归档：报告全文逐字落盘至版本库归档根 + SHA256 指纹 + 机械门禁（**已实现**，状态 Implemented；审查归档见 `docs/project/reviews/2026-10-04-review-report-archive/`） | [RFC-0001-review-report-archive.md](./proposals/RFC-0001-review-report-archive.md) |
| **RFC-0003 目录级索引约定（已取代）** | 曾落地象限索引托管化与 `manage-doc-index.py` 自愈（已于 2026-11-24 依据 `ADR-0005` 流转为 `Superseded`，托管与脚手架脚本退役，象限索引回归按需人工维护，本文件原位保留） | [RFC-0003-quadrant-index-convention.md](./proposals/RFC-0003-quadrant-index-convention.md) |
| **RFC-0002 子智能体直写契约** | 执行 RFC-0001 §7.3 A1 预留路径：子智能体直写报告至预授权路径（Write-Scope 单路径例外）+ 主智能体独立复算指纹 + 写入形态登记；含诚实边界（预授权是提示词契约而非沙箱强制）（**已实现**，状态 Implemented；审查归档见 `docs/project/reviews/2026-10-08-subagent-direct-write/`） | [RFC-0002-subagent-direct-write.md](./proposals/RFC-0002-subagent-direct-write.md) |
| **RFC-0004 spec-evolution 演进回路（已退役）** | 曾新建 `spec-evolution` 技能并落地 C-01~C-10 采集/判定器（已于 2026-11-23 依据 ADR-0003 流转为 `Superseded`，技能下线，核心哨兵 C-01/C-05/C-07 下沉 `skills/_shared/tests/test_skill_surface_sentinels.py`） | [RFC-0004-spec-evolution.md](./proposals/RFC-0004-spec-evolution.md) |
| **RFC-0005 文档真值轴（已取代）** | 曾落地控制头三字段与 `check-doc-drift.py` 漂移检测（已于 2026-11-24 依据 `ADR-0005` 流转为 `Superseded`，脚本与 `.doc-truth-baseline.json` 退役，原位保留；六轮审查归档 `2026-11-22-doc-truth-axis/`） | [RFC-0005-doc-truth-axis.md](./proposals/RFC-0005-doc-truth-axis.md) |
| **RFC-0006 分层机器地图（已取代）** | 曾落地根 `llms.txt` 与 `_llms/` 生成器（已于 2026-11-24 依据 `ADR-0005` 流转为 `Superseded`，生成物与脚本退役，原位保留；审查归档 `2026-11-22-split-llms-map/`） | [RFC-0006-split-llms-map.md](./proposals/RFC-0006-split-llms-map.md) |
| **RFC-0007 文档状态机** | `文档状态` 三态（Active / Contested / Superseded）+ `取代于` / `争议点`（**已实现**，状态 Implemented；Wave 2C 本仓实现迁至 `scripts/doc-gates/check-doc-health.py`，归档 `2026-11-22-doc-status-machine/`） | [RFC-0007-doc-status-contested.md](./proposals/RFC-0007-doc-status-contested.md) |
| **RFC-0008 文档体量度量** | 字节 ≤64 KB、最长单行 ≤1,000 字符为阻断判据，行数 >800 仅警告（**已实现**，状态 Implemented；Wave 2C 本仓实现迁至 `scripts/doc-gates/check-doc-health.py`，`.doc-size-baseline.json` 退役，审查归档 `2026-11-22-batch-gates/`） | [RFC-0008-doc-size-metric.md](./proposals/RFC-0008-doc-size-metric.md) |
| **`dual-round-review` V2.1.0** | 审查报告持久化归档：三层职责分离（运行时状态/交付凭据/机械门禁）、`check-review-report.sh`、R2 双通道输入、模板↔门禁标题漂移防护（**已终审放行 ✅**，审查归档见 `docs/project/reviews/2026-10-04-review-report-archive/`） | [2026-10-04-review-report-archive.md](./project/plans/2026-10-04-review-report-archive.md) |
| **`dual-round-review` V2.2.0** | 子智能体直写通道：Write-Scope 单路径例外 + 路径预授权六条 + 主智能体独立复算指纹 + 转录降级显式登记（台账第 7 列）+ `--round` 预授权路径 + 门禁第 8 项 + 旧归档补列迁移 | [2026-10-08-subagent-direct-write.md](./project/plans/2026-10-08-subagent-direct-write.md) |
| **批次 D 机器地图身份写保护契约** | BK-0030/BK-0031 交付（**已完成**，Maintenance-Patch 通道：五轮审查全部无 P0/P1 准予交付） | [2026-10-09-backlog-batch-d-identity-contract.md](./project/plans/2026-10-09-backlog-batch-d-identity-contract.md) |
| **批次 C 机器地图提示文案净化与零覆盖口径登记** | BK-0026/BK-0027 交付（Light 单轮红队审查）：项目名可打印字符校验 + 64 字符上限 + `--name=` 形式（修复建议恒可执行）；GOVERNANCE 显式登记零覆盖态豁免口径（**已完成**，Maintenance-Patch 通道：四轮审查末轮 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-c-llms-hardening.md](./project/plans/2026-10-09-backlog-batch-c-llms-hardening.md) |
| **批次 B 机器地图写入侧安全与一致性门禁** | 闭环 BK-0023/BK-0025：缺省落点统一 `resolve()`、零覆盖拒绝落盘；`audit-doc-health.py` 将「机器地图 == 注册命令生成物」固化为硬阻断（**已完成**，Maintenance-Patch 通道：Light 单轮 + 两轮 Delta 复核 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-b-llms-integrity.md](./project/plans/2026-10-09-backlog-batch-b-llms-integrity.md) |
| **批次 A 归档豁免与 llms 落点修复** | 闭环 BK-0001/BK-0002/BK-0021：两个治理消费者补齐交付凭据归档豁免（写入侧 root 无关兜底）、机器地图落点随 `--root` 派生（**已完成**，Maintenance-Patch 通道：Light 单轮 + 两轮 Delta 复核 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-a-archive-exemption.md](./project/plans/2026-10-09-backlog-batch-a-archive-exemption.md) |
| **`doc-governance` 目录级索引约定** | 象限索引托管化与 scaffold 索引自愈：`manage-doc-index.py`（ensure/register/入参校验）+ 六分支自愈接入 + tutorial 条件渲染（**已完成**，三轮双轮对抗审查 Zero Blockers 准予交付） | [2026-10-09-quadrant-index-convention.md](./project/plans/2026-10-09-quadrant-index-convention.md) |
| **`spec-evolution` 实施计划（主册）** | 机械化演进回路技能实现：目标 / 约束 / Task 1 / Task 7 / 验收与风险（Task 2/3/4-6 见子册） | [2026-10-12-spec-evolution.md](./project/plans/2026-10-12-spec-evolution.md) |
| **`spec-evolution` 实施子册** | Task 2 / Task 3 / Task 4-6 原文迁移（历史实施细节，不再增量维护） | [task2](./project/plans/2026-10-12-spec-evolution-task2.md) · [task3](./project/plans/2026-10-12-spec-evolution-task3.md) · [task4-6](./project/plans/2026-10-12-spec-evolution-task4-6.md) |
| **文档体量度量换挡（RFC-0008）** | 字节 + 最长单行阻断、棘轮基线消化存量（**已完成**，审查并入 `2026-11-22-batch-gates/`） | [2026-11-22-doc-size-metric.md](./project/plans/2026-11-22-doc-size-metric.md) |
| **文档状态机（RFC-0007）** | 三态状态机 + 未决冲突清单（**已完成**，归档 `2026-11-22-doc-status-machine/`） | [2026-11-22-doc-status-machine.md](./project/plans/2026-11-22-doc-status-machine.md) |
| **项目待办清单 (Backlog)** | 形态 B 目录分片架构（active/ 与 archive/，由 `scripts/backlog/manage-backlog.py` 自动化治理；活跃/归档数量与编号以 `backlog/index.md` 动态仪表盘为准（禁止在本索引手写对账）；BK-0039「存量技能交付面债务」已按验收准则结项归档，残余 MID 债务登记于 BK-0041「存量技能交付面残余债务」（agy 设计书 / 两条 description 超建议值 / 测试文件超行限），`close` 未收敛卡片占位与 DoD 勾选的工具缺陷 BK-0042 已修复结项（提交 afdb4e5，V10 复核收口 8390df8；V11 更正记录见归档卡 §5 E-4/E-5），Write-Once 审查归档终审裁决契约失配登记于 BK-0043，提交信息取证据口径的反复更正登记于 BK-0044） | [index.md](./project/backlog/index.md) |
| **ADR-0001 交付凭据归档层** | 审查凭据按「可否重建」分层：运行时状态留隐藏目录、交付凭据进版本库独立目录并对齐治理豁免语义（MADR 3.0；含四轮对抗审查证据） | [0001-review-evidence-archive-layer.md](./explanation/decisions/0001-review-evidence-archive-layer.md) |
| **ADR-0002 子智能体直写通道** | 写盘权归还内容作者：消除转录失真、写盘与核验分离；显式登记三项代价（授权面由零扩大为单文件、路径预授权是提示词契约而非沙箱强制、写入形态声明不可机械验证）（MADR 3.0） | [0002-subagent-direct-write-channel.md](./explanation/decisions/0002-subagent-direct-write-channel.md) |
| **ADR-0003 退役 `spec-evolution` 技能** | 停用不可跨仓复用、零真实触发且高维护成本的 `spec-evolution` 技能，将不可替代的 C-01 / C-05+YAML / C-07 硬护栏下沉为 `skills/_shared/tests/test_skill_surface_sentinels.py`（MADR 3.0） | [0003-retire-spec-evolution.md](./explanation/decisions/0003-retire-spec-evolution.md) |
| **退役 `spec-evolution` 实施计划** | 方案 A（退技能、留哨兵）的落地计划、TDD 哨兵、注册面同步与文档状态流转记录 | [2026-11-23-retire-spec-evolution.md](./project/plans/2026-11-23-retire-spec-evolution.md) |
| **Wave 0 止血修复计划** | Maintenance-Patch 通道：并行委派 W0-A/B/C 修复全仓现红测试、`_UNIT_RX` 17/17 失效、Markdown 链接解析、`--max-doc-bytes` 死参数、`reference/articles` 豁免、Park-Miller LCG 零状态及失实设计书 | [2026-11-23-wave0-skill-bugs-stabilization.md](./project/plans/2026-11-23-wave0-skill-bugs-stabilization.md) |
| **ADR-0004 退役 `agy-delegation-workflow` 技能** | 停用实战使用率 0%、存在四重硬绑定且与原生编排高度重叠的 `agy-delegation-workflow` 技能，将 Silent Landing / Direct-Write / 虚假合规检查三项核心资产沉淀至 `goal-loop` 与 `dual-round-review`（MADR 3.0） | [0004-retire-agy-delegation-workflow.md](./explanation/decisions/0004-retire-agy-delegation-workflow.md) |
| **Wave 1 架构瘦身实施计划** | Heavy Track：并行执行 W1-A（按 ADR-0004 抽离三项资产并物理退役 `agy-delegation-workflow`）与 W1-B（去壳提纯 `clarification-protocol` 至 V2.0.0 微技能并清理失效脚本与冲突模板）（**已完成**：四轮独立双轮对抗审查 R1 → R2 → Delta-R1 → Delta-R2 达成 Zero Blockers 准予交付，归档见 [2026-11-23-wave1-retire-agy-and-slim-clarification](./project/reviews/2026-11-23-wave1-retire-agy-and-slim-clarification/README.md)） | [2026-11-23-wave1-retire-agy-and-slim-clarification.md](./project/plans/2026-11-23-wave1-retire-agy-and-slim-clarification.md) |
| **Wave 2A `goal-loop` V3.0 重构计划** | Heavy Track：并行执行 W2A-1（收敛为 `Align → Plan → Execute → Verify → Close` 五主阶段、清理死重模板与伪运行时、对齐 Diátaxis 路径并同步架构设计书 V3.0.0）与 W2A-2（移除 `goal-state-tracker` 与文案锁死测试、引入极薄 `pack-handoff.py` 交接脚本与行为契约单测、同步跨技能与全局索引）（**已完成**：四轮独立双轮对抗审查 R1 → R2 → Delta-R1 → Delta-R2 达成 Zero Blockers 准予交付，归档见 [2026-11-23-wave2a-goal-loop-v3](./project/reviews/2026-11-23-wave2a-goal-loop-v3/README.md)） | [2026-11-23-wave2a-goal-loop-v3.md](./project/plans/2026-11-23-wave2a-goal-loop-v3.md) |
| **Wave 2B `dual-round-review` V3.0 重构计划** | Heavy Track：并行执行 W2B-1（压缩 `SKILL.md` 至 ≤12 KB 与 `description` 310 字符、退役 0 用 Artifact 支线、去技术栈硬编码并注入 Untrusted Data/空结果优先/Scoped Delta/能力档位分层、对齐模板与设计书 V3.0.0）与 W2B-2（清理脚本 Artifact 分支、迁移并重建行为与表面契约测试、同步全局入口与日志）（**已完成**：三轮独立对抗审查 R1 → R2 → Scoped Delta R1 零缺陷达成 Zero Blockers 准予交付，归档见 [2026-11-24-wave2b-dual-round-review-v3](./project/reviews/2026-11-24-wave2b-dual-round-review-v3/README.md)） | [2026-11-24-wave2b-dual-round-review-v3.md](./project/plans/2026-11-24-wave2b-dual-round-review-v3.md) |
| **ADR-0005 物理切割 `doc-governance` 公共技能与本仓私有文档门禁体系** | 执行「三刀切割」：公共技能回归 Convention-First 轻内核 + 通用 `--exclude` 断链扫描器；本仓私有门禁与待办管理分别下沉 `scripts/doc-gates/` 与 `scripts/backlog/`；退役低 ROI 仪式税（`trim-revision`/`check-doc-drift`/`llms.txt` 等），取代 RFC-0003/0005/0006（MADR 3.0，Accepted） | [0005-split-doc-governance-public-vs-repo-local.md](./explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md) |
| **Wave 2C `doc-governance` V3.0 重构计划** | Heavy Track：三路并行委派 W2C-1（公共技能瘦身与通用 `--exclude` 断链扫描器）、W2C-2（本仓私有 `scripts/doc-gates/`、`scripts/backlog/` 与 `.githooks/pre-commit`）、W2C-3（退役旧生成物、流转 RFC 状态并同步全仓治理与引导文档）（**已完成**：三轮独立对抗审查 R1 → R2 → Scoped Delta R1 零缺陷达成 Zero Blockers 准予交付，归档见 [wave2c-doc-governance-v3](./project/reviews/2026-11-24-wave2c-doc-governance-v3/README.md)） | [2026-11-24-wave2c-doc-governance-v3.md](./project/plans/2026-11-24-wave2c-doc-governance-v3.md) |
| **Wave 3 前端双技能 V2.0 重构计划** | Heavy Track：三路并行委派 W3-1（`taste-driven-designer` V2.0：表面模式分流、2026 10 大 AI Tells、5 列盲比记录表与纯标准库无偏种子）、W3-2（`frontend-qa-gate` V2.0：双轨 23+4 门禁、现代探针编排与 Schema v2 真实磁盘证据 JSON 门禁）与 W3-3（跨技能 `goal-loop` 同步与仓级文档/设计书升级）（**已完成**：三轮独立对抗审查 R1 → R2 → Scoped Delta R1 零缺陷达成 Zero Blockers 准予交付，归档见 [wave3-frontend-skills-v2](./project/reviews/2026-11-24-wave3-frontend-skills-v2/README.md)） | [2026-11-24-wave3-frontend-skills-v2.md](./project/plans/2026-11-24-wave3-frontend-skills-v2.md) |
| **全局提示词渐进披露重构** | `contexts/AGENTS.md` 129 → 97 行：压缩条件性条款、把澄清规程下沉为 `clarification-protocol` 技能、合并 §4 标题层级，并按用户裁决新增 root 防回流准入判据；依据社区/官方「root 只放每任务适用内容 + 指令预算」最佳实践（**已完成**：三批 + 收口交付，129 → 97 行 / 13316 → 10746 字节；Fast Path 文档重构，未挂对抗审查） | [2026-10-10-agents-md-progressive-disclosure.md](./project/plans/2026-10-10-agents-md-progressive-disclosure.md) |
| **P2 批次六项 backlog 卡片闭环** | 闭环 BK-0003/BK-0004/BK-0020/BK-0033/BK-0034/BK-0040：稳定 ID 按基线逐轮配对与终审裁决唯一性、修订表头章节作用域、非 UTF-8 输出硬化、baseline 损坏显式失败、嵌套类型逃逸收口（**进行中**，Heavy Track；实施计划与验收口径见计划文档） | [2026-10-14-p2-six-backlog-items.md](./project/plans/2026-10-14-p2-six-backlog-items.md) |
| **技能脚本 Python 统一化** | 8 个自建技能脚本改为**单一 Python 实现** + 同目录 `.sh` POSIX 兼容壳（形态 B，旧调用面零破坏）；9 套契约测试改为运行时无关（Windows 默认 `sys.executable`，POSIX 另验壳转发）；四注册面与技能内文档口径同步为 Python 主路径；Windows 侧以 uv 隔离环境取证（**进行中**，Heavy Track；实施计划与验收口径见计划文档） | [2026-10-19-skill-scripts-python-unification.md](./project/plans/2026-10-19-skill-scripts-python-unification.md) |
| **分层机器地图（RFC-0006）** | 根 `llms.txt` 降为象限入口（≤8 KB，实测 883 B），全量条目下沉 `_llms/<象限>.md`；新增路由文件 `docs/AGENTS.md`（≤30 行，只写读取顺序与硬约束）；生成器增 `--split` / `--check` / `--max-root-bytes`；audit 改多文件集合比对 | [2026-11-22-split-llms-map.md](./project/plans/2026-11-22-split-llms-map.md) |
| **文档真值轴（RFC-0005）** | 控制头三字段（来源/代码锚点/复核于）+ `check-doc-drift.py` 五态漂移检测（退出码 0/1/2）+ `audit-doc-health.py --truth=warn|require` 双轴报告；结构分语义不变，零声明不颁发满分；红线 7「严禁删锚点清零」 | [2026-11-22-doc-truth-axis.md](./project/plans/2026-11-22-doc-truth-axis.md) |
| **P3 批次六项 backlog 卡片闭环** | 闭环 BK-0045/BK-0010/BK-0008/BK-0016/BK-0007/BK-0014：未跟踪文件清单平台无关化（GNU BRE `\?` 缺陷 + `-z` 原样路径）、`--archive-root` 空值/根路径防御、围栏未闭合告警补嵌套演示提示、象限索引幂等判据剥离锚点与查询串（非法文件名 fail-closed）、GOVERNANCE §4.1 豁免口径精确化与可读性约定守卫边界、作废轮次版本库留痕口径（**已完成**：四轮审查（R1 → R2 → delta-r1 → delta-r2）闭环、终审准予交付、门禁 PASS；Heavy Track；六卡已迁入 `archive/2026-Q4/`，审查归档见 [2026-10-20-p3-six-backlog-batch](./project/reviews/2026-10-20-p3-six-backlog-batch/README.md)） | [2026-10-20-p3-six-backlog-batch.md](./project/plans/2026-10-20-p3-six-backlog-batch.md) |

---

## 5. 📖 外部前沿文献与理论基准 (External References & Theory)

| 文档标识 | 主题与核心突破 | 参考链接 |
| :--- | :--- | :--- |
| **`ai-world-class-designer`** | Anshu Chimala (前 Apple AI 原型负责人): AI 设计双钻模型、独立 Critic 审稿闭环与 8 大反平庸工程技术 | [how-to-turn-your-ai-into-a-world-class-designer.md](./reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md) |
| **`ai-coding-frontend-common-problems`** | kejun: AI Coding 前端常见问题全景 —— 研究证据、风险分层与十条可执行防御清单（本文献为本技能需求源） | [ai-coding-frontend-common-problems.md](./reference/articles/ai-coding-frontend-common-problems.md) |
| **`backlog-capacity-governance`** | 真实实践调研：Linear/Jira/GitHub/actions-stale 的入口收口、自动出清、Close-as-Move 与 index+shard 拓扑 | [2026-10-04-backlog-capacity-governance.md](./explanation/analysis/2026-10-04-backlog-capacity-governance.md) |

---

## 6. 📖 平台规则与不可变约束 (Rules & Invariants)

| 规则标识 | 约束对象与核心内容 | 规则文档 |
| :--- | :--- | :--- |
| **`source-group-inclusion`** | 预设来源组收录判据：缺省预设 `common` 的四条准入（即装即用 / 增量能力 / 厂商中立命名 / 粒度克制）、唯一例外边界、厂商／产品专用套件走独立预设、登记同步口径 | [source-group-inclusion.md](./reference/rules/source-group-inclusion.md) |
| **`commit-evidence`** | 提交信息取证口径：区分可复核的门禁结论与一次测量值；数字须附可复现命令并落盘；不可复核属性不得作为完成度宣称；历史更正不回改 | [commit-evidence.md](./reference/rules/commit-evidence.md) |

> 象限索引：[reference/rules/index.md](./reference/rules/index.md)
