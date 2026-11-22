---
id: BK-0049
title: 知识库可用性评测：20 条 golden task
type: Feature
status: completed
priority: P1
trigger: 文档体系稳定后 / 需要向他人证明价值时
created_at: '2026-11-22'
updated_at: '2026-11-22'
closed_at: '2026-11-22'
resolution: delivered
destination: check-golden-tasks.py（20 条断言）+ check-all 第 6 道门禁；GAP 5 项已转 BK-0052/0053/0054
source:
- LLM-WIKI 调研报告 §7 P2-8
acceptance_criteria:
- 20 条任务覆盖 6 个象限，每条含期望产物与判据
- 记录成功率、步数、token 三项，并可复跑对比
---

## 1. 背景与问题陈述
所有文档改进都没有「知识库是否让 agent 少走弯路」的度量；调研报告 P0-3 的「可回答性」维度至今为空。需要固定任务集 + 成功率/步数/token 记录，才能证明投入有回报。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 20 条任务覆盖 6 个象限，每条含期望产物与判据
- [ ] 记录成功率、步数、token 三项，并可复跑对比

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录

### 结项记录 (2026-11-22)
- **结论**: delivered
- **去向/凭据**: check-golden-tasks.py（20 条断言）+ check-all 第 6 道门禁；GAP 5 项已转 BK-0052/0053/0054
- **归档目录**: archive/2026-Q4/
- **提示**: §3 DoD 仍有 2 项未勾选 —— `close` 不代勾验收准则，请作者核验后更新卡片（本项为机械统计）。
