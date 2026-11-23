---
id: BK-0050
title: 存量超限文档拆分（spec-evolution / skill-scripts）
type: TechDebt
status: completed
priority: P2
trigger: 下次修改这两篇文档时
created_at: '2026-11-22'
updated_at: '2026-11-23'
closed_at: '2026-11-23'
resolution: delivered
destination: 主册 52,355 B + task2/task3/task4-6 三子册；skill-scripts 40,438 B / 最长 854；体量基线清空
source:
- RFC-0008 基线 docs/.doc-size-baseline.json
acceptance_criteria:
- 两篇均降至 64 KB / 1000 字符以内并从基线移除
---

## 1. 背景与问题陈述
两篇文档已入体量基线：spec-evolution.md 127,747 字节 / 2,360 行；skill-scripts-python-unification.md 最长单行 1,269 字符。基线只降不升，需拆分或改写长行。

## 2. 影响面与技术考量
- 涉及模块: `docs/project/plans/2026-10-12-spec-evolution.md`（拆为主册 + Task 2/3/4-6 三个子册）、`docs/project/plans/2026-10-19-skill-scripts-python-unification.md`（长行按标点换行）、`docs/.doc-size-baseline.json`、`docs/llms.txt` / `docs/_llms/`
- 风险点: 历史审查报告中的旧行号引用不可改写（Write-Once 凭据），仅保证语义原文逐字迁移；拆分后新子册须纳入机器地图与链接校验。

## 3. 验收准则与验证设计 (DoD)
- [x] 两篇均降至 64 KB / 1000 字符以内并从基线移除（主册 52,355 B / 最长 879；skill-scripts 40,438 B / 最长 854；基线 `{"docs": {}}`）

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录

### 交付 (2026-11-23)

- **spec-evolution 拆分**：主册保留目标/约束/Task 1/Task 7/验收与风险（**52,355 字节 / 584 行 / 最长 879**）；Task 2 → `2026-10-12-spec-evolution-task2.md`（27,951 B）、Task 3 → `...-task3.md`（31,950 B）、Task 4-6 → `...-task4-6.md`（17,987 B），原文逐字迁移并反向链接母计划
- **skill-scripts 长行改写**：唯一 1,269 字符长行按 `；`/`。` 语义边界换行，全文 **40,438 字节 / 最长 854**
- **基线**：`docs/.doc-size-baseline.json` 刷新为 `{"docs": {}, "version": 1}`（两篇均已达标）
- **验证**：`check-all.py --full` **7/7 全绿**；`audit-doc-health.py` PASS；断链 0；机器地图已重生成
- **已知边界**：历史审查报告按 Write-Once 保留旧行号引用，不随拆分改写（语义由子册逐字承接）

- **结项结论**: delivered
- **去向/凭据**: 主册 + 3 子册 + skill-scripts 长行改写 + 空体量基线

### 结项记录 (2026-11-23)
- **结论**: delivered
- **去向/凭据**: 主册 52,355 B + task2/task3/task4-6 三子册；skill-scripts 40,438 B / 最长 854；体量基线清空
- **归档目录**: archive/2026-Q4/
