---
id: BK-0012
title: 门禁枚举未登记报告文件或收紧 --round 命名输入
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
- dual-round-review V2.2.0 Delta R2 DR-3
acceptance_criteria:
- 在「门禁枚举未登记报告文件」与「约束 --round 命名输入使 head 分量确定」之间择一实现，不做双份
- 补回归用例（归档目录含 README.md，天真枚举会假红，须文件名模式 + 台账交叉校验）
---

## 1. 背景与问题陈述
R1-1 残余：单参数形式 --round <BASE_SHA> 下 HEAD 为符号引用，HEAD 漂移即路径漂移且 Write-Once 静默；实测未登记报告放入归档目录后门禁仍 rc=0（孤儿不可枚举）。触发需三步编排者失误叠加，故记待办而非阻断。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 在「门禁枚举未登记报告文件」与「约束 --round 命名输入使 head 分量确定」之间择一实现，不做双份
- [ ] 补回归用例（归档目录含 README.md，天真枚举会假红，须文件名模式 + 台账交叉校验）

## 4. 实施去向与结项记录
*(未开工)*
