---
id: BK-0003
title: 稳定 ID 方向二改为按文件名配对 R1-R2 后施加
type: Governance
status: active
priority: P2
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-3
acceptance_criteria:
- 稳定 ID 方向二改为按文件名 <base7>..<head7> 配对 R1/R2 后施加
- 加「R1 清单非空 ⇒ R2 明细表非空」判定断言
---

## 1. 背景与问题描述

跨轮次 ID 并集碰撞——共享归档下旧轮 R2 行已占位，新一轮空明细表仍 rc=0 且打印「稳定 ID 对齐」。

- **来源追溯**: Delta R2 R1-3
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/dual-round-review/scripts/check-review-report.sh` 跨轮次审查报告归档判定。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] 稳定 ID 方向二改为按文件名 <base7>..<head7> 配对 R1/R2 后施加
- [ ] 加「R1 清单非空 ⇒ R2 明细表非空」判定断言

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
