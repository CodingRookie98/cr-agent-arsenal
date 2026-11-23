---
id: BK-0055
title: check-doc-drift --staged 残余风险：新增文档复核点判据与纯日期复核（BD-9）
type: TechDebt
status: active
priority: P2
trigger: 下次修改 check-doc-drift.py 的 staged 分支时
created_at: '2026-11-23'
updated_at: '2026-11-23'
closed_at: null
resolution: null
destination: null
source:
- docs/project/reviews/2026-11-22-batch-gates/round-1-bd1r-confirm.md §4 P2/P3 残余
- docs/project/reviews/2026-11-22-batch-gates/round-2-bd1r-reconfirm.md §4 残余风险
acceptance_criteria:
- _verified_line_changed_staged 对新增/改名文档不得无条件返回 True：按「锚点是否也在本提交新增」判定并补回归
- BD-9：纯日期型「复核于」不能单独作为同提交豁免证据，或显式登记为接受偏离
- P3：补「中文文档名 + 合法刷新 → fresh」的 --staged 正例回归；`--name-only -z` 与 `git mv` 墓碑按需处理
---

## 1. 背景与问题陈述
BD-1-R2 修复后仍存的两条 P2 残余：① _verified_line_changed_staged 在 git show HEAD:path 失败（新增文档/改名）时 return True，新文档一律被视为已刷新复核点；与 drifted 子句叠加后仍是洗白通道。② 单锚点只改「复核于」日期即可 fresh（BD-9），未校验其指向提交是否覆盖本次锚点变更。二者均不构成当前阻断，登记为后续收口。

## 2. 影响面与技术考量
- 涉及模块: `skills/doc-governance/scripts/check-doc-drift.py`（`_verified_line_changed_staged` / `_verified_ts`）、`skills/doc-governance/tests/test_doc_drift.py`
- 风险点: 收紧新增文档判据可能误伤「新文档 + 新锚点同提交」的合法场景；日期型「复核于」是控制头模板的常规写法，若禁止单独作为同提交豁免证据会波及存量文档，需先评估改为「接受偏离」或引入独立字段。

## 3. 验收准则与验证设计 (DoD)
- [ ] _verified_line_changed_staged 对新增/改名文档不得无条件返回 True：按「锚点是否也在本提交新增」判定并补回归
- [ ] BD-9：纯日期型「复核于」不能单独作为同提交豁免证据，或显式登记为接受偏离
- [ ] P3：补「中文文档名 + 合法刷新 → fresh」的 --staged 正例回归；`--name-only -z` 与 `git mv` 墓碑按需处理

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
