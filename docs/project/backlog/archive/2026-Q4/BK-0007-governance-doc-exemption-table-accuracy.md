---
id: BK-0007
title: GOVERNANCE.md 豁免表文本精确化
type: Governance
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

现登记仅 2 项（元数据/孤儿），实现实为全部计分维度。

- **来源追溯**: Delta R2 R1-6
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

消除文档与门禁实现之间的漂移。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [x] GOVERNANCE.md 豁免表文本精确化（1 行）：改为「该目录不参与任何计分维度扫描」
- [x] 显式声明索引控制头与报告清单互链为无守卫的可读性约定

## 4. 结项与闭环记录

*(当前处于活跃计划中，结项后由 `manage-backlog.py close` 自动迁入 archive/)*

### 结项记录 (2026-10-20)
- **结论**: delivered
- **去向/凭据**: docs/project/plans/2026-10-20-p3-six-backlog-batch.md
- **归档目录**: archive/2026-Q4/
