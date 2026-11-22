---
id: BK-0050
title: 存量超限文档拆分（spec-evolution / skill-scripts）
type: TechDebt
status: active
priority: P2
trigger: 下次修改这两篇文档时
created_at: '2026-11-22'
updated_at: '2026-11-22'
closed_at: null
resolution: null
destination: null
source:
- RFC-0008 基线 docs/.doc-size-baseline.json
acceptance_criteria:
- 两篇均降至 64 KB / 1000 字符以内并从基线移除
---

## 1. 背景与问题陈述
两篇文档已入体量基线：spec-evolution.md 127,747 字节 / 2,360 行；skill-scripts-python-unification.md 最长单行 1,269 字符。基线只降不升，需拆分或改写长行。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 两篇均降至 64 KB / 1000 字符以内并从基线移除

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
