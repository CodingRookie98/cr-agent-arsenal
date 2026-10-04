---
id: BK-0001
title: trim-revision.py 复用 project-reviews 归档豁免常量
type: TechDebt
status: active
priority: P2
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-1
acceptance_criteria:
- trim-revision.py 复用同一 project/reviews 归档豁免常量（≤3 行），或令 --fix 拒写归档路径
- 补 1 条回归测试用例
---

## 1. 背景与问题描述

该脚本是唯一具备写能力的治理消费者，实测 `--fix` 就地改写归档报告致 SHA256 变化（G1 逐字归档红线破损）。

- **来源追溯**: Delta R2 R1-1
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/doc-governance/scripts/trim-revision.py` 与交付凭据不可变性门禁。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] trim-revision.py 复用同一 project/reviews 归档豁免常量（≤3 行），或令 --fix 拒写归档路径
- [ ] 补 1 条回归测试用例

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
