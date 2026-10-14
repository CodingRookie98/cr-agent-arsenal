---
id: BK-0013
title: 台账末列定位对无尾随竖线且结论含裸竖线的行误判
type: TechDebt
status: rejected
priority: P3
trigger: null
created_at: '2026-10-08'
updated_at: '2026-10-14'
closed_at: '2026-10-14'
resolution: wontfix
destination: 有意保留 fail-closed：目标输入无尾随竖线且结论含裸竖线，本身已破坏 Markdown 表格渲染；BK-0011 行为用例已把「无尾随竖线行
  rc=1」固化为预期契约
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

### 结项记录 (2026-10-14)
- **结论**: wontfix
- **去向/凭据**: 有意保留 fail-closed：目标输入无尾随竖线且结论含裸竖线，本身已破坏 Markdown 表格渲染；BK-0011 行为用例已把「无尾随竖线行 rc=1」固化为预期契约
- **归档目录**: archive/2026-Q4/
- **提示**: §3 DoD 仍有 1 项未勾选 —— `close` 不代勾验收准则，请作者核验后更新卡片（本项为机械统计）。
