---
id: BK-0013
title: 台账末列定位对无尾随竖线且结论含裸竖线的行误判
type: TechDebt
status: active
priority: P3
trigger: null
created_at: '2026-10-08'
updated_at: '2026-10-08'
closed_at: null
resolution: null
destination: null
source:
- dual-round-review V2.2.0 Delta R2 DR-4（历史既有）
acceptance_criteria:
- 与 DR-2 的行为用例一并覆盖，不单独排期
---

## 1. 背景与问题陈述
历史既有：无尾随竖线且结论单元格含半角竖线时，NF>=9 判定取 $(NF-1) 落在结论碎片上，合法行被 fail-closed 误拒。实测 455eccc 旧实现与当前实现在该输入下同为 rc=1（行为相同），且该输入本身已破坏 Markdown 表格渲染。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 与 DR-2 的行为用例一并覆盖，不单独排期

## 4. 实施去向与结项记录
*(未开工)*
