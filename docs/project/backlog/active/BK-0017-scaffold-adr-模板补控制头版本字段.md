---
id: BK-0017
title: scaffold ADR 模板补控制头版本字段
type: TechDebt
status: active
priority: P3
trigger: null
created_at: '2026-10-09'
updated_at: '2026-10-09'
closed_at: null
resolution: null
destination: null
source:
- RFC-0003 Delta 审查 R1-14（历史既有 · R2 封顶 P3）
acceptance_criteria:
- 'ADR 模板补『当前版本: V1.0.0』并同步修订历史；全类型批量生成元数据合规率 12/12'
---

## 1. 背景与问题陈述
scaffold-doc.sh ADR 分支模板控制头仅含决策编号/当前状态/决策所有者/决议日期，缺『当前版本』字段，拉低 audit-doc-health.py 元数据基线率（全类型批量生成实测 11/12 合规）。历史既有，非本次变更引入。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] ADR 模板补『当前版本: V1.0.0』并同步修订历史；全类型批量生成元数据合规率 12/12

## 4. 实施去向与结项记录
*(未开工)*
