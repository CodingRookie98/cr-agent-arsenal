---
id: BK-0006
title: 四条审查护栏各补 1 条反证测试用例
type: TechDebt
status: active
priority: P3
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-8
acceptance_criteria:
- 四条护栏各补 1 条反证用例（行首锚定 / 方向二 / 豁免边界 / 索引控制头与互链）
- 否决任何测试框架重构
---

## 1. 背景与问题描述

变异实跑证明四处关键行为零覆盖（删方向二仍 31 passed、豁免常量改前缀仍 13 passed）。

- **来源追溯**: Delta R2 R1-8
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

提高 `skills/dual-round-review/` 门禁契约测试防御力。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] 四条护栏各补 1 条反证用例（行首锚定 / 方向二 / 豁免边界 / 索引控制头与互链）
- [ ] 否决任何测试框架重构

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
