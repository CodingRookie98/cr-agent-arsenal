---
id: BK-0041
title: 存量技能交付面残余债务：agy 设计书缺失 / 两条 description 超建议值 / doc-governance 测试文件超行限
type: TechDebt
status: active
priority: P3
trigger: spec-evolution judge 全量复跑出现 C-02 / C-04 / C-06 类 MID 发现且不阻断交付时登记；无前置条件，随时可做
created_at: '2026-10-13'
updated_at: '2026-10-13'
closed_at: null
resolution: null
destination: null
source:
- BK-0039 §4 残余项移交（2026-10-13 该卡 AC 结清时按「检测与修复分离」裁定不随本次交付）
- spec-evolution judge 2026-10-13 全量复跑：agy 无设计书 / clarification description 623 /
  doc-governance 测试文件超 1000 行 / dual-round-review description 738
acceptance_criteria:
- skills/agy-delegation-workflow 具备设计书 docs/explanation/architecture/agy-delegation-workflow-design.md（C-02
  转绿）
- clarification-protocol 与 dual-round-review 的 description 收敛至 ≤ 500 字符，触发回归逐条复验通过（C-04
  转绿）
- skills/doc-governance/tests/test_doc_governance_scripts.py 拆分至单文件 ≤ 1000 行，断言强度不下降（C-06
  转绿）
- 作为新基线重跑 judge 全量：MID 数量下降且无新增发现
---

## 1. 背景与问题陈述
BK-0039 结清后剩余的存量交付面债务，均为 MID 级、不阻断交付：(1) agy-delegation-workflow 缺架构设计书（C-02）；(2) clarification-protocol description 623 字符、dual-round-review 738 字符，均超 spec-evolution C-04 的 500 字符建议值（软性建议值，恒为 MID；压缩会改变技能触发面，需与触发回归同做）；(3) skills/doc-governance/tests/test_doc_governance_scripts.py 76761 字节 / 1583 行，超 C-06 单文件 1000 行阈值，拆分属纯 churn 需谨慎。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] skills/agy-delegation-workflow 具备设计书 docs/explanation/architecture/agy-delegation-workflow-design.md（C-02 转绿）
- [ ] clarification-protocol 与 dual-round-review 的 description 收敛至 ≤ 500 字符，触发回归逐条复验通过（C-04 转绿）
- [ ] skills/doc-governance/tests/test_doc_governance_scripts.py 拆分至单文件 ≤ 1000 行，断言强度不下降（C-06 转绿）
- [ ] 作为新基线重跑 judge 全量：MID 数量下降且无新增发现

## 4. 实施去向与结项记录
*(未开工)*
