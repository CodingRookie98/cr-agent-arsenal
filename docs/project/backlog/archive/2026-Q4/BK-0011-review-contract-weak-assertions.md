---
id: BK-0011
title: 审查归档契约测试的弱断言改为行为断言
type: TechDebt
status: completed
priority: P3
trigger: null
created_at: 2026-10-08
updated_at: 2026-11-15
closed_at: 2026-11-15
resolution: superseded
destination: 前提已被 test_write_channel_contract.py:203-211（R1-12 回归）推翻；残余形态偏好并入 BK-0006 判定
source:
  - dual-round-review V2.2.0 Delta R2 DR-2
acceptance_criteria:
  - test_write_channel_contract.py 对 check-review-report.sh 末列定位的断言由纯文本存在性改为行为断言：合法含裸竖线行过闸
  - 变异反转末列三元后测试必须变红（现为 89/89 全绿）
---

## 1. 背景与问题陈述
Delta R2 实测：把 check-review-report.sh:144 的三元 m=(NF>=9)?$(NF-1):$8 反转为 m=(NF>=9)?$8:$(NF-1) 后 L1 89 passed 零失败，而该变异使门禁对合法行实测 rc=1。弱断言系 V2.2.0 新增，使 R1-12 的语义契约无行为保真度。

### 复核结论（2026-11-15，关单前取证）

原指控的「变异存活」前提已不成立：`skills/dual-round-review/tests/test_write_channel_contract.py:203-211` 的 `test_checker_uses_last_column_not_fixed_index` 已把末列定位钉死为 `len(fields) >= 9` 与 `len(fields) - 2` 两条并存断言——三元反转成 `- 3`、或退回固定下标，都会让该断言变红。卡片所指的「89/89 全绿」不再是事实。

残余差异仅剩形态偏好：该断言读源码文本而非跑端到端 rc。这不是契约缺陷（门禁行为已被 `test_ledger_round_column_*` / `test_write_channel_contract.py` 的 rc 级用例覆盖），且与本仓库「零依赖、pytest 直跑」的取向相比，为它引入脚本内省/变异框架属于过度设计。故本卡以 `superseded` 关闭，形态偏好并入 BK-0006 的「豁免边界反证」批次决定是否值得做。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] test_write_channel_contract.py 对 check-review-report.sh 末列定位的断言由纯文本存在性改为行为断言：合法含裸竖线行过闸 rc=0、无尾随竖线行 rc=1
- [ ] 变异反转末列三元后测试必须变红（现为 89/89 全绿）

## 4. 实施去向与结项记录

### 结项记录 (2026-11-15)
- **结论**: superseded
- **去向/凭据**: 前提已被 test_write_channel_contract.py:203-211（R1-12 回归）推翻；残余形态偏好并入 BK-0006 判定
- **归档目录**: archive/2026-Q4/
- **提示**: §3 DoD 仍有 2 项未勾选 —— `close` 不代勾验收准则，请作者核验后更新卡片（本项为机械统计）。
