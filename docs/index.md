# CR 公共技能库与文档总索引 (CR Public Skills Knowledge Base)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-INDEX-2026
> - **当前版本**: V1.27.0 (批次 D 交付完成：BK-0030/BK-0031 经五轮审查全部无 P0/P1，终审准予交付)
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-10-04

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.27.0** | 2026-10-09 | DSH AI Agent | 王辉 | **批次 D 交付完成**（五轮审查全部无 P0/P1，5 份归档报告）：BK-0030/BK-0031 关闭归档 2026-Q4；落地 `--name` 缺省沿用身份、round-trip 断言、全面 fail-closed（含审计读闸门与原子落盘）；GOVERNANCE §4.1 身份写保护契约；新增 BK-0032 |
| **V1.26.0** | 2026-10-09 | DSH AI Agent | 王辉 | 批次 D（BK-0030/BK-0031）：`--name` 缺省改 `None` 并**沿用既有地图身份**（正常重生成不再被拒或改名）、不可读/非 UTF-8/不可反解一律 fail-closed；GOVERNANCE §4.1 登记**身份写保护契约** |
| **V1.25.0** | 2026-10-09 | DSH AI Agent | 王辉 | **批次 C 交付完成**（四轮审查：前三轮各指 1×P1 且均为实质缺陷，第四轮后果级复核根治，4 份归档报告）：BK-0026/BK-0027 关闭归档 2026-Q4；落地**生成器侧身份写保护闸门**与 fail-closed 提示；新增 BK-0030/BK-0031 |
| **V1.24.0** | 2026-10-09 | DSH AI Agent | 王辉 | 批次 C（BK-0026/BK-0027）：提示文案项目名新增**可打印字符校验 + 长度上限**（消除终端控制序列注入与畸形名死巷）、改用 `--name=<value>` 赋值形式；GOVERNANCE §4.1 显式登记**零覆盖态无门禁兜底**的口径与代价 |
| **V1.23.0** | 2026-10-09 | DSH AI Agent | 王辉 | **批次 B 交付完成**（三轮审查均 Zero P0/P1，3 份归档报告）：BK-0023/BK-0025 关闭归档 2026-Q4；加固含命令注入闭合（`shlex.quote`）、判定与生成参数同源、合规树接线用例；新增 BK-0026~0029 |

---

## 1. 概述 (Overview)

本项目为现代 AI 智能体（Claude Code / Antigravity / Cursor 等）研发与多智能体协作平台提供工业级可复用公共技能（Public Agent Skills）与工程规范体系。

* 📋 **知识库治理标准**: [docs/GOVERNANCE.md](./GOVERNANCE.md)
* 🤖 **智能体机器地图**: [docs/llms.txt](./llms.txt)

---

## 2. 📚 核心技能架构设计 (Explanation: Architecture Specifications)

以下设计书记录了各核心技能的理论来源、第一性原理、架构拓扑与实现细节：

| 技能标识 | 核心定位与理论支柱 | 架构规格文档 |
| :--- | :--- | :--- |
| **`doc-governance`** | 基于 Diátaxis 四象限、RFC 提案结晶模型与 Docs-as-Code 自动化门禁的文档治理体系 | [doc-governance-design.md](./explanation/architecture/doc-governance-design.md) |
| **`goal-loop`** | 融合 Manus 上下文工程、自适应测试分级裁定与双轮终审的工业级目标收敛循环 | [goal-loop-design.md](./explanation/architecture/goal-loop-design.md) |
| **`dual-round-review`** | 红队第一性原理穿透 + 元架构师审判校准；支持 Full / Light / Delta 三模式、审查记录锚点与交付凭据归档（报告全文进版本库 + 结构机械门禁） | [dual-round-review-design.md](./explanation/architecture/dual-round-review-design.md) |
| **`taste-driven-designer`** | 源于 Anshu Chimala AI 双钻模型：外部随机种子 + 独立 Critic 闭环（三信号门禁：结构清单 + 盲比改进 + 人类签收，分数仅作遥测）+ 多模态增强 + 残酷减法 | [taste-driven-designer-design.md](./explanation/architecture/taste-driven-designer-design.md) |
| **`frontend-qa-gate`** | 源于 kejun《前端开发转向 AI Coding 的常见问题全景》：五域产物断言（响应式 / 状态矩阵 / 无障碍 / 浏览器 / 性能）+ 证据三态 + 回流路由；不做分数判据、不替代人工签收、不侵入代码级审查 | [frontend-qa-gate-design.md](./explanation/architecture/frontend-qa-gate-design.md) |
| **Backlog 治理最佳实践** | 结合软件工程史（精益/看板/Shape Up）与 AI 上下文工程的 14 项待办治理法则 | [backlog-governance-best-practices.md](./explanation/analysis/backlog-governance-best-practices.md) |

---

## 3. 📖 技能工程落地规程 (Skill Specifications & References)

各技能的独立安装规范与执行规程如下：

| 技能名称 | 规程入口 | 核心能力描述 |
| :--- | :--- | :--- |
| **`doc-governance`** | [doc-governance 规程](../skills/doc-governance/SKILL.md) | 文档工程与知识库治理（断链静态扫描、历史裁剪、健康体检、llms.txt 生成） |
| **`goal-loop`** | [goal-loop 规程](../skills/goal-loop/SKILL.md) | 工业级端到端长任务目标实现循环（2-Action Rule、自适应测试、外部技能协同） |
| **`dual-round-review`** | [dual-round-review 规程](../skills/dual-round-review/SKILL.md) | 对抗性双轮代码终审硬门禁（红队穿透 + 元架构师审判）；支持 Full / Light / Delta 三模式 |
| **`agy-delegation-workflow`** | [agy-delegation-workflow 规程](../skills/agy-delegation-workflow/SKILL.md) | Antigravity CLI 后台工人自适应委派规程（无头任务派发、环境隔离、边界管控） |
| **`taste-driven-designer`** | [taste-driven-designer 规程](../skills/taste-driven-designer/SKILL.md) | 品味驱动设计三阶段流程（D1 种子发散 / D2 三信号门禁 / D3 AI Tells 审计与减法）；能力门控、宿主无关、可降级 |
| **`frontend-qa-gate`** | [frontend-qa-gate 规程](../skills/frontend-qa-gate/SKILL.md) | 前端产物验收（五域断言 + 报告结构机械门禁 + 缺陷回流路由）；能力门控，缺能力记未验证不降级通过 |

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
| **RFC-0001 审查报告归档契约** | 为 `dual-round-review` 引入交付凭据归档：报告全文逐字落盘至版本库归档根 + SHA256 指纹 + 机械门禁（需求确认，状态 In Review） | [RFC-0001-review-report-archive.md](./proposals/RFC-0001-review-report-archive.md) |
| **RFC-0003 目录级索引约定** | 象限索引托管化与 scaffold 索引自愈：根级人类入口唯一、象限索引按需托管（`<!-- doc-index:managed -->` 位置契约）、登记防 404 与 README 入口跳过（**已实现**，状态 Implemented；三轮双轮对抗审查 Zero Blockers 准予交付） | [RFC-0003-quadrant-index-convention.md](./proposals/RFC-0003-quadrant-index-convention.md) |
| **RFC-0002 子智能体直写契约** | 执行 RFC-0001 §7.3 A1 预留路径：子智能体直写报告至预授权路径（Write-Scope 单路径例外）+ 主智能体独立复算指纹 + 写入形态登记；含诚实边界（预授权是提示词契约而非沙箱强制）（需求确认，状态 In Review） | [RFC-0002-subagent-direct-write.md](./proposals/RFC-0002-subagent-direct-write.md) |
| **`dual-round-review` V2.1.0** | 审查报告持久化归档：三层职责分离（运行时状态/交付凭据/机械门禁）、`check-review-report.sh`、R2 双通道输入、模板↔门禁标题漂移防护（**已终审放行 ✅**，审查归档见 `docs/project/reviews/2026-10-04-review-report-archive/`） | [2026-10-04-review-report-archive.md](./project/plans/2026-10-04-review-report-archive.md) |
| **`dual-round-review` V2.2.0** | 子智能体直写通道：Write-Scope 单路径例外 + 路径预授权六条 + 主智能体独立复算指纹 + 转录降级显式登记（台账第 7 列）+ `--round` 预授权路径 + 门禁第 8 项 + 旧归档补列迁移 | [2026-10-08-subagent-direct-write.md](./project/plans/2026-10-08-subagent-direct-write.md) |
| **批次 D 机器地图身份写保护契约** | BK-0030/BK-0031 交付（**已完成**，Maintenance-Patch 通道：五轮审查全部无 P0/P1 准予交付） | [2026-10-09-backlog-batch-d-identity-contract.md](./project/plans/2026-10-09-backlog-batch-d-identity-contract.md) |
| **批次 C 机器地图提示文案净化与零覆盖口径登记** | BK-0026/BK-0027 交付（Light 单轮红队审查）：项目名可打印字符校验 + 64 字符上限 + `--name=` 形式（修复建议恒可执行）；GOVERNANCE 显式登记零覆盖态豁免口径（**已完成**，Maintenance-Patch 通道：四轮审查末轮 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-c-llms-hardening.md](./project/plans/2026-10-09-backlog-batch-c-llms-hardening.md) |
| **批次 B 机器地图写入侧安全与一致性门禁** | 闭环 BK-0023/BK-0025：缺省落点统一 `resolve()`、零覆盖拒绝落盘；`audit-doc-health.py` 将「机器地图 == 注册命令生成物」固化为硬阻断（**已完成**，Maintenance-Patch 通道：Light 单轮 + 两轮 Delta 复核 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-b-llms-integrity.md](./project/plans/2026-10-09-backlog-batch-b-llms-integrity.md) |
| **批次 A 归档豁免与 llms 落点修复** | 闭环 BK-0001/BK-0002/BK-0021：两个治理消费者补齐交付凭据归档豁免（写入侧 root 无关兜底）、机器地图落点随 `--root` 派生（**已完成**，Maintenance-Patch 通道：Light 单轮 + 两轮 Delta 复核 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-a-archive-exemption.md](./project/plans/2026-10-09-backlog-batch-a-archive-exemption.md) |
| **`doc-governance` 目录级索引约定** | 象限索引托管化与 scaffold 索引自愈：`manage-doc-index.py`（ensure/register/入参校验）+ 六分支自愈接入 + tutorial 条件渲染（**已完成**，三轮双轮对抗审查 Zero Blockers 准予交付） | [2026-10-09-quadrant-index-convention.md](./project/plans/2026-10-09-quadrant-index-convention.md) |
| **项目待办清单 (Backlog)** | 形态 B 目录分片架构（active/ 与 archive/，由 `manage-backlog.py` 自动化治理；当前 21 项：BK-0001~0010 源自 V2.1.0 Delta R2 终审，BK-0011~0015 源自 V2.2.0 Delta R2 终审，BK-0016~0018 源自 RFC-0003 首轮审查 R1-11/R1-14/R1-15，BK-0019~0021 源自 RFC-0003 Delta 审查 DR1-3/DR1-8/DR1-10，BK-0022 源自 RFC-0003 第三轮 Delta R2 终审 DR1-13，BK-0023~0025 源自批次 A Light-Delta 审查；其中 BK-0001/BK-0002/BK-0021 已于 2026-Q4 交付归档） | [index.md](./project/backlog/index.md) |
| **ADR-0001 交付凭据归档层** | 审查凭据按「可否重建」分层：运行时状态留隐藏目录、交付凭据进版本库独立目录并对齐治理豁免语义（MADR 3.0；含四轮对抗审查证据） | [0001-review-evidence-archive-layer.md](./explanation/decisions/0001-review-evidence-archive-layer.md) |
| **ADR-0002 子智能体直写通道** | 写盘权归还内容作者：消除转录失真、写盘与核验分离；显式登记三项代价（授权面由零扩大为单文件、路径预授权是提示词契约而非沙箱强制、写入形态声明不可机械验证）（MADR 3.0） | [0002-subagent-direct-write-channel.md](./explanation/decisions/0002-subagent-direct-write-channel.md) |

---

## 5. 📖 外部前沿文献与理论基准 (External References & Theory)

| 文档标识 | 主题与核心突破 | 参考链接 |
| :--- | :--- | :--- |
| **`ai-world-class-designer`** | Anshu Chimala (前 Apple AI 原型负责人): AI 设计双钻模型、独立 Critic 审稿闭环与 8 大反平庸工程技术 | [how-to-turn-your-ai-into-a-world-class-designer.md](./reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md) |
| **`ai-coding-frontend-common-problems`** | kejun: AI Coding 前端常见问题全景 —— 研究证据、风险分层与十条可执行防御清单（本文献为本技能需求源） | [ai-coding-frontend-common-problems.md](./reference/articles/ai-coding-frontend-common-problems.md) |
| **`backlog-capacity-governance`** | 真实实践调研：Linear/Jira/GitHub/actions-stale 的入口收口、自动出清、Close-as-Move 与 index+shard 拓扑 | [2026-10-04-backlog-capacity-governance.md](./research/2026-10-04-backlog-capacity-governance.md) |
