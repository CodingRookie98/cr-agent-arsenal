---
id: BK-0011
title: 审查归档契约测试的弱断言改为行为断言
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
- dual-round-review V2.2.0 Delta R2 DR-2
acceptance_criteria:
- test_write_channel_contract.py 对 check-review-report.sh 末列定位的断言由纯文本存在性改为行为断言：合法含裸竖线行过闸
  rc=0、无尾随竖线行 rc=1
- 变异反转末列三元后测试必须变红（现为 89/89 全绿）
---

## 1. 背景与问题陈述
Delta R2 实测：把 check-review-report.sh:144 的三元 m=(NF>=9)?$(NF-1):$8 反转为 m=(NF>=9)?$8:$(NF-1) 后 L1 89 passed 零失败，而该变异使门禁对合法行实测 rc=1。弱断言系 V2.2.0 新增，使 R1-12 的语义契约无行为保真度。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] test_write_channel_contract.py 对 check-review-report.sh 末列定位的断言由纯文本存在性改为行为断言：合法含裸竖线行过闸 rc=0、无尾随竖线行 rc=1
- [ ] 变异反转末列三元后测试必须变红（现为 89/89 全绿）

## 4. 实施去向与结项记录
*(未开工)*
