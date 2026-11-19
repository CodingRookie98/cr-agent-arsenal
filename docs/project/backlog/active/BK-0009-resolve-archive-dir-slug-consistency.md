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

- [x] resolve_archive_dir 复用分支增加「既有索引「交付单元」字段 == 请求 slug」一致性校验

## 4. 结项与闭环记录

### 实施记录（2026-11-19）

判据从「目录名后缀命中」换成「索引登记的 `**交付单元**` 等于请求 slug」：新增 `_read_unit()` 读归档 README 的该字段；`_resolve_archive_dir()` 逆序遍历后缀候选，命中相等即复用；不等或索引缺该字段则**跳过并 stderr 告警**，全部落空时才按当天日期新建。

**为何不硬阻断**：同后缀的多个交付单元并存是合法形态（`review-report-archive` 与 `archive`），硬阻断会让历史归档把新单元挡在门外；静默复用又会让报告写进别人的归档。告警 + 新建是同时满足「不串单元」与「不阻塞」的出口。

**回归**：`tests/test_prepare_review_context.py` 新增 2 条——后缀命中但单元不同必须跳过且新建（并断言既有目录不被移动/改名）、单元一致必须复用（不新建重复目录）。dual-round-review 全量 120 passed / 3 skipped。

**过程中撞到并修掉的真回归**：首次实现在模块级新增 `_UNIT_RX = re.compile(...)`，但该脚本并未 `import re`——模块导入即 NameError，连 `--help` 都跑不起来，测试 36 条齐红。补 `import re` 后恢复。教训：模块级常量的依赖须就地核对，不能默认脚本已导入。
