# ADR-0005: 物理切割 `doc-governance` 公共技能与本仓私有文档门禁体系

> **ADR 控制元数据**
> - **决策编号**: 0005
> - **当前版本**: V1.0.0
> - **当前状态**: Accepted
> - **决策所有者**: 核心架构组
> - **决议日期**: 2026-11-24
> - **取代历史提案**: [RFC-0003 目录级索引约定](../../proposals/RFC-0003-quadrant-index-convention.md) · [RFC-0005 文档真值轴](../../proposals/RFC-0005-doc-truth-axis.md) · [RFC-0006 分层机器地图](../../proposals/RFC-0006-split-llms-map.md)
> - **评估依据**: [LLM-WIKI 调研](../analysis/llm-wiki-implementation-research.md) · [Docs-as-Code 增量调研](../analysis/2026-11-23-doc-governance-peer-research.md) · [doc-governance 过度设计评估](../analysis/2026-11-23-doc-governance-architecture-evaluation.md)
> - **关联实施计划**: [2026-11-24-wave2c-doc-governance-v3.md](../../project/plans/2026-11-24-wave2c-doc-governance-v3.md)

---

## 1. 背景与上下文 (Context and Problem Statement)

`doc-governance` 经两个月增量演进后，已从轻量文档工作流技能膨胀为 **32 个追踪文件 / 12,889 行（含缓存 13,106 行）/ 598.6 KB** 的单体「God Skill」，独占本仓全部 7 技能总字节的 **48.9%**、总行数的 **51.9%**，并暴露四项结构性危机：

1. **公私混装导致零可移植性**：`skills/doc-governance/` 内部塞入了 9 个异构子系统。`check-golden-tasks.py`（硬编码 `docs/AGENTS.md` 中文键、`reference/rules/commit-evidence.md`、`【A】/一手` 等本仓专有断言）、`check-all.py`（`parents[2]` 写死仓根路径）、`audit-doc-health.py`（1,482 行强绑 Diátaxis 中文目录与 `BK-XXXX`）在外部常规项目实测跨仓可移植度仅 **0%–15%**，违背本仓库「公共可复用技能」定位；同时将 1,537 行 / ~73 KB 的 Mini-Jira 系统（`manage-backlog.py` + `backlog-specification.md`）寄宿于文档技能中，被迫在 4 处门禁硬编码豁免补丁。
2. **高昂「文档治理税」与自激振荡**：Git 全史 390 次提交中 **49.7%**（近 80 次达 **77.5%**）纯改文档或治理脚本自身；`check-doc-drift.py` + 测试共 **2,516 行**却仅覆盖 **3 篇自引用文档（4.0%）**，仍导致近 50 次提交中 **22%** 纯为重钉 `复核于 SHA`；`llms.txt` + `_llms/*.md` 同步门禁导致 **20.5%** 的提交被迫顺手刷写生成物。
3. **规则复杂度反噬自身**：源码实证存在 7 处真实缺陷与契约漂移（含 `--max-doc-bytes`、`--lang` 两个静默死参数、行区间锚点退化为文件级、`reference/articles` 体量豁免声明与实现不一致、同文档控制头版本与修订表漂移、`pre-commit` 重复读盘 6–8 次），且 3 个文件长期突破单文件 1,000 行上限。
4. **少数高价值核心护城河需要提纯保留**：Diátaxis 四象限边界、RFC → Diátaxis 结晶流转、纯正 MADR 3.0 决策记录、变更影响面核查意识、RFC-0007 三态状态机与 RFC-0008 体量上限（≤64 KB / ≤1,000 字符），以及零依赖物理断链扫描器 `check-doc-links.py` 具有真实工程价值。

---

## 2. 考虑的备选方案 (Considered Options)

* **方案 A（选定）：物理「三刀切割」完整重构**
  - **第一刀（公私分离）**：公共技能 `skills/doc-governance/` 仅保留 Convention-First 通用写作与联动规程、通用登记模板、及去硬编码后的 `check-doc-links.py`（新增 `--exclude`）；本仓私有门禁（`check-all.py`、`check-golden-tasks.py`、精简重建的 `check-doc-health.py`）下沉至仓库私有目录 `scripts/doc-gates/`。
  - **第二刀（拆出 Mini-Jira）**：将 `manage-backlog.py` 与 `backlog-specification.md` 物理移出公共技能至本仓 `scripts/backlog/`（通用仓库应由各自 Issue 平台承载，不再捆绑分发）。
  - **第三刀（去仪式税与自激振荡）**：废除每篇文档强制手写版本号 + 5 行修订历史表裁剪仪式（退役 `trim-revision.py` 与 `check-doc-control-sync.py`）；退役 2,516 行自激重钉型 `check-doc-drift.py` 与 `.doc-truth-baseline.json`（取代 `RFC-0005`）；退役同步刷盘型 `generate-llms-txt.py` 与 `docs/llms.txt` / `docs/_llms/`（取代 `RFC-0006`）；退役 `manage-doc-index.py` 托管脚本与空 `.doc-size-baseline.json`（取代 `RFC-0003`）；退役 682 行硬编码中文模板的 `scaffold-doc.py/.sh`；仅将高 ROI 的 `RFC-0007` 三态状态机 + `RFC-0008` 体量上限 + `docs/AGENTS.md` 路由守卫保留于 `scripts/doc-gates/check-doc-health.py`。
* **方案 B（未采纳）：仅做第一、二刀 + 修复 7 处 Bug** —— 仍保留 `check-doc-drift.py`（4% 覆盖率）与 `llms.txt` pre-commit 强同步税，无法根治 22% 重钉 SHA 与 20.5% 刷盘摩擦。
* **方案 C（未采纳）：原位修 Bug 与拆超千行文件** —— 不改动契约，但完全无法解决跨仓 0% 可移植性与 God Skill 体量膨胀。

---

## 3. 最终决策与裁决 (Decision Outcome)

选定 **方案 A**：

1. **公共技能契约（`skills/doc-governance/`，Convention-First）**：
   - 遵循「先适配宿仓既有规范、工具（如 `lychee` / `markdownlint-cli2` / `vale`）与 Git 原生历史」原则，精简至 ~11 个追踪文件 / ~65 KB；
   - `check-doc-links.py` 移除硬编码 `project/reviews` 路径段，提供通用可重复 `--exclude <rel_prefix>`（非法或越界 `..` 路径直接 `exit 2` fail-closed）与严格多反引号/波浪线围栏闭合，可零修改拷贝至任意外部项目开箱运行。
2. **本仓私有门禁与待办工具（`scripts/doc-gates/` 与 `scripts/backlog/`）**：
   - `.githooks/pre-commit` 与 `AGENTS.md` 改为调用 `python3 scripts/doc-gates/check-all.py`；
   - `check-all.py` 顺序执行 **3 道低摩擦硬门禁**（零重复读盘）：① 通用断链 `skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews`；② 精简健康检查 `scripts/doc-gates/check-doc-health.py`（`RFC-0007` 三态状态机 + `RFC-0008` ≤64 KB / ≤1,000 字符体量，真实透传参数与 `reference/articles` 豁免 + `docs/AGENTS.md` ≤30 行）；③ 可回答性评测 `scripts/doc-gates/check-golden-tasks.py`（`G-18` 更新为校验人类总入口 `docs/index.md` 象限导航）。`--full` 追加 `pytest skills/ scripts/ -q`；
   - 待办管理由 `scripts/backlog/manage-backlog.py` 与 `scripts/backlog/README.md` 独立承载，彻底解除与文档治理门禁的交织耦合。
3. **历史 RFC 与凭据归档处置**：
   - [RFC-0003](../../proposals/RFC-0003-quadrant-index-convention.md)、[RFC-0005](../../proposals/RFC-0005-doc-truth-axis.md)、[RFC-0006](../../proposals/RFC-0006-split-llms-map.md) 原位保留不删除不移动（保证 Write-Once 审查归档链接有效），文档状态流转为 `Superseded`（`取代于: ../explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md`）；
   - [RFC-0007](../../proposals/RFC-0007-doc-status-contested.md) 与 [RFC-0008](../../proposals/RFC-0008-doc-size-metric.md) 保持 `Implemented`，注明其本仓运行承载脚本迁至 `scripts/doc-gates/check-doc-health.py`。

### 3.1 积极后果 (Positive Consequences)

* 公共 `doc-governance` 技能体量削减 **~89%**（598.6 KB → ~65 KB），彻底消除 3 个超千行巨石文件与 7 处实证源码 Bug；
* 全仓 6 个现役公共技能 **100%** 实现跨仓无依赖独立分发，无本仓私有门禁与 Mini-Jira 寄生；
* 每次提交仅跑 3 道不重读的高价值检查，永久根除 22% `复核于` 重钉提交与 20.5% `llms.txt` 刷盘振荡。

### 3.2 消极后果与已知代价 (Negative Consequences / Trade-offs)

* 放弃代码锚点 `check-doc-drift.py` 的自动时间差报警后，文档与代码的语义一致性回归由 `doc-governance` 的「变更影响面触发清单」配合人工 / Review 阶段检视 `git diff` 承担；
* 新建文档与象限索引维护回归按需人工创建或 Agent 遵循通用规程完成，不再提供 7 套硬编码中文模板脚本。

---

## 4. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 修订描述 |
| :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-24 | AI Agent | 正式裁决执行「三刀切割」公私分离重构，将公共核与本仓私有门禁/待办工具解耦并取代 RFC-0003/0005/0006 |
