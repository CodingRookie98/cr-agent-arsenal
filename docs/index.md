# CR 公共技能库与文档总索引 (CR Public Skills Knowledge Base)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-INDEX-2026
> - **当前版本**: V1.36.5 (独立复核 V11 收口：提交信息中 `skills/doc-governance` 的 passed 数 132 与实测 134 不同宽，已在 BK-0042 归档卡追加更正记录 E-4/E-5；功能面与门禁结论不变)
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-10-04

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.36.5** | 2026-10-13 | DSH AI Agent | 王辉 | **独立复核（V11）更正记录**：提交 `8390df8` 的取证行称 `pytest skills/doc-governance -q = 132 passed`，该提交树实测 134（132 为父提交 `ecf5d24` 数值，技能总数 448→450 互证），属凭据数字与实测不同宽，已在 BK-0042 §5 追加 E-4；另登记 E-5 两处口径澄清（「trim 5 行」为修订表滑窗上限、`llms.txt` 重生成为幂等无 diff）。功能面与门禁经 V12 独立复跑通过（V11 报告未入库，其结论未由本轮核验） |
| **V1.36.4** | 2026-10-13 | DSH AI Agent | 王辉 | **独立复核（V10）收口（提交 8390df8）**：V10 阻断项 B1 —— `scaffold-doc.sh:390` 未加引号的 heredoc 使新增 `:420` 行反引号被命令替换，骨架卡丢失 `close` 词元（rc 仍为 0），已转义并补「与 create 模板逐字一致」回归用例；非阻断 N1 —— 未勾选项数由全正文统计收敛为 §3 小节统计（`count_unchecked_dod()`）并在 spec 注明范围；非阻断 N3 —— 七张历史归档卡占位语残余登记为不追溯项（BK-0042 §5 E-1~E-3） |
| **V1.36.3** | 2026-10-13 | DSH AI Agent | 王辉 | **BK-0042 结项（提交 afdb4e5）**：`manage-backlog.py` 的 `close` 归档时机械收敛 §4 `*(未开工)*` 占位语（兼容历史措辞）并按项数提示未勾选 DoD（不代勾复选框），`create` 写明 DoD 由作者人工勾选，`reopen` 写明历史结项记录仅作留痕；`scaffold-doc.sh` 与 `references/backlog-specification.md` 同步；新增 8 用例契约测试（变异 4 项逐项被捕获） |
| **V1.36.2** | 2026-10-13 | DSH AI Agent | 王辉 | **独立复核（V9）收口**：BK-0039 §5 追加 E-5（`0600→0644` 属工作区副作用，git 不追踪、不可由提交复核，今后不进入提交信息宣称）并把 E-1 由动因归因改写为末态实测对照；E-1~E-5 经 V9 逐项复现（8facf12 = 7/0 含 C-02；3abacf7 = 10/2；6eacc31 = 11/3；历史未改写）。新增 BK-0043：Write-Once 审查归档 `2026-10-12-spec-evolution-v1` 的终审裁决字段不满足 `--require-verdict=PASS` 精确匹配契约（9 个归档中唯一失败者，不可就地修复） |
| **V1.36.1** | 2026-10-13 | DSH AI Agent | 王辉 | **独立复核（V8）更正记录**：BK-0039 归档卡追加「更正记录 (Errata)」——提交 `8facf12` 的 judge 宣称限定为同批末态测量（该提交自身树实测 7 findings / 0 HIGH）、交付面基线数字补测量时点（`3abacf7` = 10 / 2，末态 = 4 / 0）、destination 的 C-02 限定为 `clarification-protocol` 设计书；`manage-backlog.py close` 未收敛卡片 §3/§4 占位的工具缺陷登记为 BK-0042 |

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
| **`clarification-protocol`** | 以「依赖强度 × 实现影响」排序提问、以三类决策台账（已决项 / 已排除边界 / 默认假设）承载裁决、以三项收敛自检（目标 / 边界 / 矛盾）作终止判据；把「是否收敛」从感觉变成可判定句，台账结构由离线校验器机械把关 | [clarification-protocol-design.md](./explanation/architecture/clarification-protocol-design.md) |
| **`spec-evolution`** | 机械化演进回路：把演进回路的「选择端」从模型意见换成脚本退出码（只读采集器 → 确定性判定器 → Exit 0/1/2）+ 锚点硬门禁（不可解析即 fail-closed）+ 人类裁决区永久留白；只判「产物存在性」，不做设计质量评价 | [spec-evolution-design.md](./explanation/architecture/spec-evolution-design.md) |
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
| **`clarification-protocol`** | [clarification-protocol 规程](../skills/clarification-protocol/SKILL.md) | 需求澄清与收敛规程（术语先行前置项、提问分级排序、决策台账去重、三项收敛自检、熔断预算与人类升级）；由全局提示词 §4 的一行指针按需唤起 |
| **`spec-evolution`** | [spec-evolution 规程](../skills/spec-evolution/SKILL.md) | 机械化演进回路（技能交付面完整性、`description` 上限、文件规模、四注册面漂移、根提示词净增长）；判定只采信脚本退出码与可核验锚点，人类裁决区永久留白 |

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
| **RFC-0004 spec-evolution 演进回路** | 新建 `spec-evolution` 技能：把演进回路的「选择端」从**模型意见**换成**脚本退出码**——事实采集器（`collect-facts.py`）→ 确定性判定器（`judge.py`，零 LLM/零网络/纯标准库）→ Exit 0/1；判据表 C-01~C-10 覆盖技能交付面完整性、frontmatter 上限、文件规模、注册面漂移与根提示词净增长；v1 结构性地不做无客观信号的设计质量评价（**已实现**，状态 Implemented · V0.4.0：7 个 Task 全部交付，判定器实测复现 §1.1 的 F-1~F-9 全部九项缺陷并修 F-9；`spec-evolution` 自身零 finding，待独立终审） | [RFC-0004-spec-evolution.md](./proposals/RFC-0004-spec-evolution.md) |
| **`dual-round-review` V2.1.0** | 审查报告持久化归档：三层职责分离（运行时状态/交付凭据/机械门禁）、`check-review-report.sh`、R2 双通道输入、模板↔门禁标题漂移防护（**已终审放行 ✅**，审查归档见 `docs/project/reviews/2026-10-04-review-report-archive/`） | [2026-10-04-review-report-archive.md](./project/plans/2026-10-04-review-report-archive.md) |
| **`dual-round-review` V2.2.0** | 子智能体直写通道：Write-Scope 单路径例外 + 路径预授权六条 + 主智能体独立复算指纹 + 转录降级显式登记（台账第 7 列）+ `--round` 预授权路径 + 门禁第 8 项 + 旧归档补列迁移 | [2026-10-08-subagent-direct-write.md](./project/plans/2026-10-08-subagent-direct-write.md) |
| **批次 D 机器地图身份写保护契约** | BK-0030/BK-0031 交付（**已完成**，Maintenance-Patch 通道：五轮审查全部无 P0/P1 准予交付） | [2026-10-09-backlog-batch-d-identity-contract.md](./project/plans/2026-10-09-backlog-batch-d-identity-contract.md) |
| **批次 C 机器地图提示文案净化与零覆盖口径登记** | BK-0026/BK-0027 交付（Light 单轮红队审查）：项目名可打印字符校验 + 64 字符上限 + `--name=` 形式（修复建议恒可执行）；GOVERNANCE 显式登记零覆盖态豁免口径（**已完成**，Maintenance-Patch 通道：四轮审查末轮 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-c-llms-hardening.md](./project/plans/2026-10-09-backlog-batch-c-llms-hardening.md) |
| **批次 B 机器地图写入侧安全与一致性门禁** | 闭环 BK-0023/BK-0025：缺省落点统一 `resolve()`、零覆盖拒绝落盘；`audit-doc-health.py` 将「机器地图 == 注册命令生成物」固化为硬阻断（**已完成**，Maintenance-Patch 通道：Light 单轮 + 两轮 Delta 复核 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-b-llms-integrity.md](./project/plans/2026-10-09-backlog-batch-b-llms-integrity.md) |
| **批次 A 归档豁免与 llms 落点修复** | 闭环 BK-0001/BK-0002/BK-0021：两个治理消费者补齐交付凭据归档豁免（写入侧 root 无关兜底）、机器地图落点随 `--root` 派生（**已完成**，Maintenance-Patch 通道：Light 单轮 + 两轮 Delta 复核 Zero Blockers 准予交付） | [2026-10-09-backlog-batch-a-archive-exemption.md](./project/plans/2026-10-09-backlog-batch-a-archive-exemption.md) |
| **`doc-governance` 目录级索引约定** | 象限索引托管化与 scaffold 索引自愈：`manage-doc-index.py`（ensure/register/入参校验）+ 六分支自愈接入 + tutorial 条件渲染（**已完成**，三轮双轮对抗审查 Zero Blockers 准予交付） | [2026-10-09-quadrant-index-convention.md](./project/plans/2026-10-09-quadrant-index-convention.md) |
| **项目待办清单 (Backlog)** | 形态 B 目录分片架构（active/ 与 archive/，由 `manage-backlog.py` 自动化治理；活跃 **32** 项 / 历史归档 **11** 项，编号至 `BK-0043`；BK-0039「存量技能交付面债务」已按验收准则结项归档，残余 MID 债务登记于 BK-0041「存量技能交付面残余债务」（agy 设计书 / 两条 description 超建议值 / 测试文件超行限），`close` 未收敛卡片占位与 DoD 勾选的工具缺陷 BK-0042 已修复结项（提交 afdb4e5，V10 复核收口 8390df8；V11 更正记录见归档卡 §5 E-4/E-5），Write-Once 审查归档终审裁决契约失配登记于 BK-0043） | [index.md](./project/backlog/index.md) |
| **ADR-0001 交付凭据归档层** | 审查凭据按「可否重建」分层：运行时状态留隐藏目录、交付凭据进版本库独立目录并对齐治理豁免语义（MADR 3.0；含四轮对抗审查证据） | [0001-review-evidence-archive-layer.md](./explanation/decisions/0001-review-evidence-archive-layer.md) |
| **ADR-0002 子智能体直写通道** | 写盘权归还内容作者：消除转录失真、写盘与核验分离；显式登记三项代价（授权面由零扩大为单文件、路径预授权是提示词契约而非沙箱强制、写入形态声明不可机械验证）（MADR 3.0） | [0002-subagent-direct-write-channel.md](./explanation/decisions/0002-subagent-direct-write-channel.md) |
| **全局提示词渐进披露重构** | `contexts/AGENTS.md` 129 → 97 行：压缩条件性条款、把澄清规程下沉为 `clarification-protocol` 技能、合并 §4 标题层级，并按用户裁决新增 root 防回流准入判据；依据社区/官方「root 只放每任务适用内容 + 指令预算」最佳实践（**已完成**：三批 + 收口交付，129 → 97 行 / 13316 → 10746 字节；Fast Path 文档重构，未挂对抗审查） | [2026-10-10-agents-md-progressive-disclosure.md](./project/plans/2026-10-10-agents-md-progressive-disclosure.md) |

---

## 5. 📖 外部前沿文献与理论基准 (External References & Theory)

| 文档标识 | 主题与核心突破 | 参考链接 |
| :--- | :--- | :--- |
| **`ai-world-class-designer`** | Anshu Chimala (前 Apple AI 原型负责人): AI 设计双钻模型、独立 Critic 审稿闭环与 8 大反平庸工程技术 | [how-to-turn-your-ai-into-a-world-class-designer.md](./reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md) |
| **`ai-coding-frontend-common-problems`** | kejun: AI Coding 前端常见问题全景 —— 研究证据、风险分层与十条可执行防御清单（本文献为本技能需求源） | [ai-coding-frontend-common-problems.md](./reference/articles/ai-coding-frontend-common-problems.md) |
| **`backlog-capacity-governance`** | 真实实践调研：Linear/Jira/GitHub/actions-stale 的入口收口、自动出清、Close-as-Move 与 index+shard 拓扑 | [2026-10-04-backlog-capacity-governance.md](./research/2026-10-04-backlog-capacity-governance.md) |

---

## 6. 📖 平台规则与不可变约束 (Rules & Invariants)

| 规则标识 | 约束对象与核心内容 | 规则文档 |
| :--- | :--- | :--- |
| **`source-group-inclusion`** | 预设来源组收录判据：缺省预设 `common` 的四条准入（即装即用 / 增量能力 / 厂商中立命名 / 粒度克制）、唯一例外边界、厂商／产品专用套件走独立预设、登记同步口径 | [source-group-inclusion.md](./reference/rules/source-group-inclusion.md) |

> 象限索引：[reference/rules/index.md](./reference/rules/index.md)
