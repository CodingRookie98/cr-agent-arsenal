---
id: BK-0004
title: 新增终审裁决在索引中唯一校验
type: Security
status: completed
priority: P2
trigger: null
created_at: '2026-10-04'
closed_at: '2026-10-14'
resolution: delivered
destination: fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/）
source:
- Delta R2 R1-5
acceptance_criteria:
- 新增「`**终审裁决**` 在索引中唯一」校验（命中数 ≠ 1 即 rc=1，≤3 行；禁止 YAML/语义解析）
updated_at: '2026-10-14'
---

## 1. 背景与问题描述

首匹配制下索引围栏示例行可抢答产生假 PASS。

- **来源追溯**: Delta R2 R1-5
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/dual-round-review/scripts/check-review-report.sh` 审查归档门禁。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [x] 新增「`**终审裁决**` 在索引中唯一」校验（命中数 ≠ 1 即 rc=1，≤3 行；禁止 YAML/语义解析）

## 4. 结项与闭环记录

### 结项记录 (2026-10-14)
- **结论**: delivered
- **去向/凭据**: fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/）
- **归档目录**: archive/2026-Q4/
- **验收核验 (作者)**: §3 DoD 全部项已核验落地（回归用例转红→转绿 + L0/L1/L-Doc 全绿 + R2 终审 Zero Blockers）；上方 `close` 的机械未勾选提示按实况收敛（工具侧缺口见 BK-0042）。
