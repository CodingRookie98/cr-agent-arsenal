---
id: BK-0010
title: archive-root 空值与非法形态防御校验
type: Security
status: completed
priority: P3
trigger: null
created_at: 2026-10-04
closed_at: 2026-10-20
resolution: delivered
destination: docs/project/plans/2026-10-20-p3-six-backlog-batch.md
source: 
acceptance_criteria: 
updated_at: 2026-10-20
---

## 1. 背景与问题描述

实测错误信息 `无法创建归档目录: /2026-10-04-demo2`，仅因沙箱根只读才未建树；低优先级。

- **来源追溯**: Delta R2 R1-11
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

防止脚本参数为空时发生意外的系统根目录写入。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [x] --archive-root= 空值/非法形态校验，拒绝路径退化为文件系统根

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*

### 结项记录 (2026-10-20)
- **结论**: delivered
- **去向/凭据**: docs/project/plans/2026-10-20-p3-six-backlog-batch.md
- **归档目录**: archive/2026-Q4/

### 范围备注 (R2 终审登记, 2026-10-20)
- 守卫范围**仅限**：空值 + 文件系统根目录（先 `realpath` 解析符号链接再判定）。**不做**路径归属校验（不判断是否位于仓库内），依据 `docs/explanation/decisions/0002-subagent-direct-write-channel.md`「归档根由授权方命令行自持」；R1-3 / R2 均未要求收紧。
- 其余形态（相对 `../..`、指向非根目录的符号链接、仓库外绝对路径）由调用方自行负责；`skills/dual-round-review/SKILL.md` 的声明已同步收窄为「空值或文件系统根会被拒绝」，不再宣称「不得散落到仓库外任意位置」。
