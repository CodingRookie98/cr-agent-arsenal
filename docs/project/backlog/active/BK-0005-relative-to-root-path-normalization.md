---
id: BK-0005
title: 豁免判定前执行路径根相对语义归一化
type: Governance
status: active
priority: P3
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-7
acceptance_criteria:
- 豁免判定前执行 path.resolve().relative_to(root_dir.resolve())（2 行/脚本；保持元组全等比较，禁止改前缀语义）
- 在 docs/GOVERNANCE.md 补「根相对语义，收窄根即不豁免」提示
---

## 1. 背景与问题描述

`--dir project/reviews/../../plans` 实测扫描 0 文件 rc=0，根外文档被静默豁免。

- **来源追溯**: Delta R2 R1-7
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/doc-governance/scripts/` 下全部审计脚本的路径归一化。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [ ] 豁免判定前执行 path.resolve().relative_to(root_dir.resolve())（2 行/脚本；保持元组全等比较，禁止改前缀语义）
- [ ] 在 docs/GOVERNANCE.md 补「根相对语义，收窄根即不豁免」提示

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*
