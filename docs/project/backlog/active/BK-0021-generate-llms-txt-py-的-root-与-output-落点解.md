---
id: BK-0021
title: generate-llms-txt.py 的 --root 与 --output 落点解耦缺陷
type: Bug
status: active
priority: P3
trigger: null
created_at: '2026-10-09'
updated_at: '2026-10-09'
closed_at: null
resolution: null
destination: null
source:
- RFC-0003 Delta 审查 DR1-10（历史既有；Delta R2 封顶正确）
acceptance_criteria:
- --output 默认值随 --root 派生，或强制显式给出 --output；补 1 条隔离根回归用例
---

## 1. 背景与问题陈述
generate-llms-txt.py 的 --output 默认值为相对 CWD 的 docs/llms.txt，不随 --root 派生；以隔离根 --root <tmp> 调用时仍会写回真实仓库的 docs/llms.txt，使『隔离复算』不成立（Delta 审查实测触发，内容与 HEAD 逐字节一致未污染工作树）。历史既有，未在本次区间改动。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] --output 默认值随 --root 派生，或强制显式给出 --output；补 1 条隔离根回归用例

## 4. 实施去向与结项记录
*(未开工)*
