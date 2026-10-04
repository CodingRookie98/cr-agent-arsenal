---
id: BK-0009
title: resolve_archive_dir 增加交付单元与请求 slug 一致性校验
type: Bug
status: active
priority: P3
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-10
acceptance_criteria:
- resolve_archive_dir 复用分支增加「既有索引「交付单元」字段 == 请求 slug」一致性校验
---

## 1. 背景与问题描述

后缀 glob 使 `--slug=archive` 命中 `2026-10-04-review-report-archive`，违反 RFC §3.3 一单元一目录。

- **来源追溯**: Delta R2 R1-10
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

保护 `skills/dual-round-review/` 归档目录查找准确性。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] resolve_archive_dir 复用分支增加「既有索引「交付单元」字段 == 请求 slug」一致性校验

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
