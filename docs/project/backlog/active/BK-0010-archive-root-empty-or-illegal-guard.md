---
id: BK-0010
title: archive-root 空值与非法形态防御校验
type: Security
status: active
priority: P3
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-11
acceptance_criteria:
- --archive-root= 空值/非法形态校验，拒绝路径退化为文件系统根
---

## 1. 背景与问题描述

实测错误信息 `无法创建归档目录: /2026-10-04-demo2`，仅因沙箱根只读才未建树；低优先级。

- **来源追溯**: Delta R2 R1-11
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

防止脚本参数为空时发生意外的系统根目录写入。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] --archive-root= 空值/非法形态校验，拒绝路径退化为文件系统根

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
