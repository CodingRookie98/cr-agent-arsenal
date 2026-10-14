---
id: BK-0018
title: 明确 skills-lock.json computedHash 权威定义并评估全量重算
type: Governance
status: rejected
priority: P3
trigger: null
created_at: '2026-10-09'
updated_at: '2026-10-14'
closed_at: '2026-10-14'
resolution: wontfix
destination: 治理对象不在本仓所有权：skills-lock.json 已 gitignore 且未跟踪，由外部 npx skills 生成，82/86
  skillPath 本地不存在，全库无消费方
source:
- RFC-0003 首轮审查 r1-95863c9..2583210 的 R1-15（历史既有；Delta R2 封顶 P3 正确；DR1-7 修正溯源标注）
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

### 结项记录 (2026-10-14)
- **结论**: wontfix
- **去向/凭据**: 治理对象不在本仓所有权：skills-lock.json 已 gitignore 且未跟踪，由外部 npx skills 生成，82/86 skillPath 本地不存在，全库无消费方
- **归档目录**: archive/2026-Q4/
- **提示**: §3 DoD 仍有 1 项未勾选 —— `close` 不代勾验收准则，请作者核验后更新卡片（本项为机械统计）。
