---
id: BK-0051
title: 检索层决策：当前不引入 MCP（已评估）
type: Governance
status: active
priority: P3
trigger: 文档 >300 篇，或出现跨仓库检索需求，或出现非文件系统消费者
created_at: '2026-11-22'
updated_at: '2026-11-22'
closed_at: null
resolution: null
destination: null
source:
- LLM-WIKI 调研报告 §7 P2-6；2026-11-22 评估
acceptance_criteria:
- 重新评估时须先给出「grep 失败」的实测场景
---

## 1. 背景与问题陈述
实测 99 篇 / 1.4 MB / 子地图 24 KB / grep 全库 0.00s，且消费者就在仓库文件系统内（Read/Grep/Glob 已够用）。MCP 的价值在跨进程/跨仓库/远程，本仓库一个都不占。结论：不引入。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 重新评估时须先给出「grep 失败」的实测场景

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
