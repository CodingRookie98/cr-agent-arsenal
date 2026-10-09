---
id: BK-0018
title: 明确 skills-lock.json computedHash 权威定义并评估全量重算
type: Governance
status: active
priority: P3
trigger: null
created_at: '2026-10-09'
updated_at: '2026-10-09'
closed_at: null
resolution: null
destination: null
source:
- RFC-0003 Delta 审查 R1-15（历史既有 · R2 封顶 P3）
acceptance_criteria:
- 先明确该字段的权威定义（生成器/算法）再决定是否重算全量，避免按未证前提批量改写 86 条记录
---

## 1. 背景与问题陈述
实测 4 条本地存在 SKILL.md 的技能其 computedHash 与文件原始 sha256 0/4 匹配（另 82 条路径缺失），且全库无生成/校验实现——该字段等于 SKILL.md 字节 sha256 属未证前提。仓库级既有状态，非本次 diff 引入。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 先明确该字段的权威定义（生成器/算法）再决定是否重算全量，避免按未证前提批量改写 86 条记录

## 4. 实施去向与结项记录
*(未开工)*
