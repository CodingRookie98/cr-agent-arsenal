---
id: BK-0055
title: check-doc-drift --staged 残余风险：新增文档复核点判据与纯日期复核（BD-9）
type: TechDebt
status: completed
priority: P2
trigger: 下次修改 check-doc-drift.py 的 staged 分支时
created_at: '2026-11-23'
updated_at: '2026-11-23'
closed_at: '2026-11-23'
resolution: delivered
destination: check-doc-drift.py 三处加固 + 4 条回归 + change-impact-matrix V1.3.1
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
- [x] `_verified_line_changed_staged` 对新增/改名文档不再无条件返回 True：新增文档仅当**所有锚点也在本提交新增**时才视为已刷新，否则 fail-closed 判 drifted（`check-doc-drift.py` `_head_path_missing`）
- [x] BD-9：`--staged` 同提交豁免新增 `_verified_commit_points_to_head`——「复核于」的 `commit` 必须指向本次提交父提交（HEAD），只改日期不算刷新
- [x] P3：补「中文文档名 + 合法刷新 → fresh」正例回归；`--name-only -z` 已落地（替代 quotePath，覆盖引号/反斜杠/换行文件名）；`git mv` 墓碑保留为操作约束（改名时同步 `--write-baseline`，已在卡内登记）

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录

### 交付 (2026-11-23)

- **代码**：`skills/doc-governance/scripts/check-doc-drift.py`
  - `staged_paths()` 改用 `git diff --cached --name-only -z` 按 NUL 切分（彻底替代 `core.quotePath=false`，覆盖引号/反斜杠/换行文件名）
  - `_verified_line_changed_staged()` 新增 `anchor_paths` 参数与 `_head_path_missing()`：新文档仅当所有锚点同为本提交新增时才判「已刷新」
  - 新增 `_verified_commit_points_to_head()`：`--staged` 下「复核于」的 commit 必须指向 HEAD，日期单独变化不再构成豁免
- **测试**：`skills/doc-governance/tests/test_doc_drift.py` 新增 4 条（合法刷新 L、中文文档名正例、新文档+既有锚点 fail-closed、新文档+新锚点通过）；全量 **302 passed**
- **文档**：`references/change-impact-matrix.md` V1.3.1 增补同提交豁免判定细则；`SKILL.md` 模式 1 第 5 步同步
- **验证**：`check-all.py --full` 7/7；BD-1-R 两轮独立确认报告中的 L/E3/E10 场景均由新增正例覆盖
- **保留约束**：锚点文件 `git mv` 改名会触发基线墓碑 rc=1，属操作约束（改名时同步 `--write-baseline`），不在本卡修复范围

- **结项结论**: delivered
- **去向/凭据**: check-doc-drift.py 三处加固 + 4 条回归 + change-impact-matrix V1.3.1

### 结项记录 (2026-11-23)
- **结论**: delivered
- **去向/凭据**: check-doc-drift.py 三处加固 + 4 条回归 + change-impact-matrix V1.3.1
- **归档目录**: archive/2026-Q4/
