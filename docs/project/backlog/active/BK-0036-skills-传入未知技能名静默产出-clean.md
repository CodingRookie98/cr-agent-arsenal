---
id: BK-0036
title: --skills 传入未知技能名静默产出 CLEAN
type: Bug
status: active
priority: P3
trigger: 调用 collect-facts.py --skills <拼错的技能名>
created_at: '2026-10-12'
updated_at: '2026-10-12'
closed_at: null
resolution: null
destination: null
source:
- dual-round-review Delta R1 R1-10（spec-evolution-v1，R2 复现成立 P3）
acceptance_criteria:
- main 中校验 only 内未知技能名 → stderr 警告或 exit 2；新增断言覆盖该路径
---

## 1. 背景与问题陈述
--skills spec-evolutoin（拼错）→ selected=[] → 0 技能、CLEAN、exit 0，范围参数拼错伪装成『零 findings』，与本技能『退出码即结论』的核心承诺冲突。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] main 中校验 only 内未知技能名 → stderr 警告或 exit 2；新增断言覆盖该路径

## 4. 实施去向与结项记录
*(未开工)*
