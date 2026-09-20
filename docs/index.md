# CR 公共技能库与文档总索引 (CR Public Skills Knowledge Base)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-INDEX-2026
> - **当前版本**: V1.8.0 (新增 taste-driven-designer 品味驱动设计技能)
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-09-20

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.8.0** | 2026-09-20 | DSH AI Agent | 王辉 | 新增 taste-driven-designer 品味驱动设计技能（双钻流程 + Critic 闭环 + AI Tells 审计）及架构设计书、实施计划索引 |
| **V1.7.0** | 2026-09-20 | Antigravity AI Agent | 王辉 | 新增外部前沿设计文献《How to Turn Your AI into a World-Class Designer》索引引用 |
| **V1.6.0** | 2026-09-16 | DSH AI Agent | 王辉 | 新增派发超时预算与多智能体并行编排契约、人机契约字段（需求方/批准人/验收口径） |
| **V1.5.0** | 2026-09-16 | DSH AI Agent | 王辉 | 新增术语先行前置条件与 Maintenance-Patch 存量维护通道；补齐术语漂移校验与术语 SSOT |
| **V1.4.0** | 2026-09-16 | DSH AI Agent | 王辉 | 新增提问收敛律：P0 方案拷问以「需求确认文档」为收敛出口；RFC 标准模板增补决策台账与默认假设段 |
| **V1.3.0** | 2026-09-14 | Antigravity AI Agent | 王辉 | 合并 dual-round-review V2.0 架构设计书与实施计划索引 |

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
| **`dual-round-review`** | 红队第一性原理穿透 + 元架构师审判校准；支持 Full / Light / Delta 三模式与审查记录锚点 | [dual-round-review-design.md](./explanation/architecture/dual-round-review-design.md) |
| **`taste-driven-designer`** | 源于 Anshu Chimala AI 双钻模型：外部随机种子 + 独立 Critic 闭环 + 多模态增强 + 残酷减法，将 AI 从统计平庸升级为世界级设计执行 | [taste-driven-designer-design.md](./explanation/architecture/taste-driven-designer-design.md) |

---

## 3. 📖 技能工程落地规程 (Skill Specifications & References)

各技能的独立安装规范与执行规程如下：

| 技能名称 | 规程入口 | 核心能力描述 |
| :--- | :--- | :--- |
| **`doc-governance`** | [doc-governance 规程](../skills/doc-governance/SKILL.md) | 文档工程与知识库治理（断链静态扫描、历史裁剪、健康体检、llms.txt 生成） |
| **`goal-loop`** | [goal-loop 规程](../skills/goal-loop/SKILL.md) | 工业级端到端长任务目标实现循环（2-Action Rule、自适应测试、外部技能协同） |
| **`dual-round-review`** | [dual-round-review 规程](../skills/dual-round-review/SKILL.md) | 对抗性双轮代码终审硬门禁（红队穿透 + 元架构师审判）；支持 Full / Light / Delta 三模式 |
| **`agy-delegation-workflow`** | [agy-delegation-workflow 规程](../skills/agy-delegation-workflow/SKILL.md) | Antigravity CLI 后台工人自适应委派规程（无头任务派发、环境隔离、边界管控） |
| **`taste-driven-designer`** | [taste-driven-designer 规程](../skills/taste-driven-designer/SKILL.md) | 品味驱动设计三阶段流程（D1 种子发散 / D2 Critic 闭环 / D3 AI Tells 审计与减法）；能力门控、宿主无关 |

---

## 4. 🚀 工程演进与管理 (Project Governance: Plans & Decisions)

| 计划标识 | 目标 | 计划文档 |
| :--- | :--- | :--- |
| **`goal-loop` V2.0** | 宿主无关执行适配器、计划文件唯一真相源、tracker 派生化与单测 | [2026-09-14-goal-loop-v2-refactor.md](./project/plans/2026-09-14-goal-loop-v2-refactor.md) |
| **`dual-round-review` V2.0** | 宿主无关派发、审查记录锚点、Light 模式与条件维度 | [2026-09-14-dual-round-review-v2.md](./project/plans/2026-09-14-dual-round-review-v2.md) |
| **派发预算与人机契约** | 派发超时收口、并行预算制编排、需求方/批准人/验收口径字段 | [2026-09-16-dispatch-budget-and-human-contract.md](./project/plans/2026-09-16-dispatch-budget-and-human-contract.md) |
| **术语先行与维护通道** | 术语对齐前置与影响分级豁免、Maintenance-Patch 通道、术语 SSOT 落地 | [2026-09-16-terminology-first-and-maintenance-track.md](./project/plans/2026-09-16-terminology-first-and-maintenance-track.md) |
| **`taste-driven-designer` V1.0** | 新建品味驱动设计技能：SKILL.md + references + templates + seed 脚本 + pytest + 设计书与全套注册 | [2026-09-20-taste-driven-designer.md](./project/plans/2026-09-20-taste-driven-designer.md) |

---

## 5. 📖 外部前沿文献与理论基准 (External References & Theory)

| 文档标识 | 主题与核心突破 | 参考链接 |
| :--- | :--- | :--- |
| **`ai-world-class-designer`** | Anshu Chimala (前 Apple AI 原型负责人): AI 设计双钻模型、独立 Critic 审稿闭环与 8 大反平庸工程技术 | [how-to-turn-your-ai-into-a-world-class-designer.md](./reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md) |
