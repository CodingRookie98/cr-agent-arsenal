---
id: BK-0048
title: 门禁自动化：pre-commit hook + 一键聚合脚本
type: Governance
status: completed
priority: P0
trigger: 每次 commit 前 / 交付前
created_at: '2026-11-22'
updated_at: '2026-11-22'
closed_at: '2026-11-22'
resolution: delivered
destination: check-all.py + .githooks/pre-commit + README 安装登记（提交 a0d5a4c 起）
source:
- RFC-0008 落地后评估（2026-11-22）
acceptance_criteria:
- 提供 scripts/check-all.sh 聚合五道门禁并以非零退出码阻断
- 提供 .githooks/pre-commit 并在 README 登记安装方式（git config core.hooksPath）
- hook 在故意引入断链时可复现阻断
---

## 1. 背景与问题陈述
9 条 GOVERNANCE 红线与 6 个门禁脚本目前全靠人手动运行，无 CI（仓库无 .github/）。忘记跑 = 门禁形同虚设，这是结构性风险而非功能缺失。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 提供 scripts/check-all.sh 聚合五道门禁并以非零退出码阻断
- [ ] 提供 .githooks/pre-commit 并在 README 登记安装方式（git config core.hooksPath）
- [ ] hook 在故意引入断链时可复现阻断

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录

### 结项记录 (2026-11-22)
- **结论**: delivered
- **去向/凭据**: check-all.py + .githooks/pre-commit + README 安装登记（提交 a0d5a4c 起）
- **归档目录**: archive/2026-Q4/
- **提示**: §3 DoD 仍有 3 项未勾选 —— `close` 不代勾验收准则，请作者核验后更新卡片（本项为机械统计）。
