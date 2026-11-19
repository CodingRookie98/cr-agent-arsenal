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

- [x] 四条护栏各补 1 条反证用例（行首锚定 / 方向二 / 豁免边界 / 索引控制头与互链）——复核后：三条此前已有，本次补「豁免边界」
- [x] 否决任何测试框架重构（本次只加用例，零基建改动）

## 4. 结项与闭环记录

### 实施记录（2026-11-19）

**复核结论：四条里三条此前已被后续批次补上，本次只补第四条。** 逐条取证：

| 护栏 | 现有反证用例 |
| :--- | :--- |
| 行首锚定 | `test_check_review_report.py:339 / :347`（区块标题必须行首，散文提及不构成齐备） |
| 方向二（按基线逐轮配对） | `test_check_review_report.py:478+`（删该护栏即红） |
| 索引控制头与互链 | `test_prepare_review_context.py:214 / :233`（`## 归档索引` 唯一性） |
| **豁免边界** | **本次新增** `test_exemption_matches_exact_segment_not_prefix` |

**豁免边界的反证设计**（针对 R1-8 里「豁免常量改前缀仍 13 passed」的零覆盖）：

1. 单元层直接断言 `in_evidence_archive()`：`project/reviews/…` 为 True，`project/reviews-extra/…` 为 **False**——前缀语义（`startswith("project/review")`）在这一步即失守；
2. 端到端两阶段：树里只有归档内断链 → 豁免、rc=0；再加入形似越界的 `reviews-extra/` 断链 → 同一断链形态 rc=1 且报错指名 `gone.md`。两阶段互为对照，避免「整体恒红」式的伪覆盖。

**未做**：任何测试框架重构（卡片明确否决）。doc-governance 全量 146 passed / 7 skipped；全仓库 517 passed / 20 skipped / 0 failed。
