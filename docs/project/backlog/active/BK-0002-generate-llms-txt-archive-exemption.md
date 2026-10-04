---
id: BK-0002
title: generate-llms-txt.py 复用归档豁免常量
type: TechDebt
status: active
priority: P2
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-2
acceptance_criteria:
- generate-llms-txt.py 复用同一豁免常量（与 audit/links 三消费者保持一致），或明确排除归档条目后重生成并提交一次
---

## 1. 背景与问题描述

实测重生成 21 条 vs 已提交 17 条，差集精确等于 4 条归档条目，机器地图静默漂移。

- **来源追溯**: Delta R2 R1-2
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/doc-governance/scripts/generate-llms-txt.py` 与 `docs/llms.txt` 的纯净度。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] generate-llms-txt.py 复用同一豁免常量（与 audit/links 三消费者保持一致），或明确排除归档条目后重生成并提交一次

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
