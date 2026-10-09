---
id: BK-0019
title: README 入口象限的索引自愈与健康评分语义对齐
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
- RFC-0003 Delta 审查 DR1-3（Delta R2 由 P2 降 P3：DA-4 已明令，缺披露非缺陷）
acceptance_criteria:
- 二选一并落地：(a) audit-doc-health 对 README 入口象限内文档豁免孤儿判定；或 (b) RFC/规范显式披露该评分代价与人工登记义务
---

## 1. 背景与问题陈述
DA-4 明令 README 入口象限不生成托管索引，但该象限内 scaffold 生成的文档因此永不登记，被 audit-doc-health.py 判为孤儿并扣分（隔离根实测 88.3/100、孤儿 1/3）。DA-4 原文只披露『链接需人工处理』，未披露评分后果，需在设计上决定：或补齐健康门禁语义（README 入口象限的文档视作已索引），或在规范中显式披露该代价。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 二选一并落地：(a) audit-doc-health 对 README 入口象限内文档豁免孤儿判定；或 (b) RFC/规范显式披露该评分代价与人工登记义务

## 4. 实施去向与结项记录
*(未开工)*
