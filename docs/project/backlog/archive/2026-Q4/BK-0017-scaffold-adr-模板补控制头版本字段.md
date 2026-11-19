---
id: BK-0017
title: scaffold ADR 模板补控制头版本字段
type: TechDebt
status: completed
priority: P3
trigger: null
created_at: 2026-10-09
updated_at: 2026-11-19
closed_at: 2026-11-19
resolution: delivered
destination: e6fa6e6（ADR 控制头版本 + 修订历史；八类批量 14/14 合规）
source:
  - RFC-0003 首轮审查 r1-95863c9..2583210 的 R1-14（历史既有；Delta R2 封顶 P3 正确；DR1-7 修正溯源标注）
acceptance_criteria:
  - ADR 模板补『当前版本: V1.0.0』并同步修订历史；全类型批量生成元数据合规率 12/12
---

## 1. 背景与问题陈述
scaffold-doc.sh ADR 分支模板控制头仅含决策编号/当前状态/决策所有者/决议日期，缺『当前版本』字段，拉低 audit-doc-health.py 元数据基线率（全类型批量生成实测 11/12 合规）。历史既有，非本次变更引入。

## 2. 影响面与技术考量
- 涉及模块: skills/doc-governance/scripts/scaffold-doc.py 的 `ADR_TEMPLATE`
- 风险点: 只补字段不改结构；修订历史表须与其它模板同形（版本号/修订日期/修订人/审核人/修订描述），否则 `audit-doc-health.py` 的控制头↔修订表一致性校验会反向报漂移

## 3. 验收准则与验证设计 (DoD)
- [x] ADR 模板补『当前版本: V1.0.0』并同步修订历史；全类型批量生成元数据合规率 **14/14**（八类文档 + 六个象限索引，实测 100%）

## 4. 实施去向与结项记录
### 实施记录（2026-11-19）

`ADR_TEMPLATE` 控制头补 `> - **当前版本**: V1.0.0`（紧跟决策编号，与其它四类模板同位置），并补 `### 修订历史记录` 表（V1.0.0 首行）。

**为何必须同时补修订历史**：`audit-doc-health.py` 除「有 version 字段」外还跑控制头↔修订表一致性校验；只加版本号而无修订表，等于把元数据合规换成版本漂移告警——修一个告警换另一个。

**实测（八类批量生成 + 审计）**：tutorial / how-to / reference / explanation / adr / rfc / backlog / proposal 各生成一份，共 14 篇（含 6 个象限索引），`控制信息元数据基线: 25.0 / 25（合规文档 14/14）`，诊断 PASS。卡片原定「12/12」在八类口径下为 14/14，合规率 100%。

**回归**：`test_scaffolded_adr_is_metadata_compliant` —— 生成 ADR 后断言文件含 `**当前版本**` 与 `修订历史记录`，并断言审计的元数据行出现 `(合规文档: 2/2)`（ADR + 象限索引）。

### 结项记录 (2026-11-19)
- **结论**: delivered
- **去向/凭据**: e6fa6e6（ADR 控制头版本 + 修订历史；八类批量 14/14 合规）
- **归档目录**: archive/2026-Q4/
