---
id: BK-0004
title: 新增终审裁决在索引中唯一校验
type: Security
status: active
priority: P2
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-5
acceptance_criteria:
- 新增「`**终审裁决**` 在索引中唯一」校验（命中数 ≠ 1 即 rc=1，≤3 行；禁止 YAML/语义解析）
---

## 1. 背景与问题描述

首匹配制下索引围栏示例行可抢答产生假 PASS。

- **来源追溯**: Delta R2 R1-5
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/dual-round-review/scripts/check-review-report.sh` 审查归档门禁。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] 新增「`**终审裁决**` 在索引中唯一」校验（命中数 ≠ 1 即 rc=1，≤3 行；禁止 YAML/语义解析）

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
