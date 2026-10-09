---
id: BK-0022
title: strip_leading_noise 对未闭合 frontmatter 围栏兜底
type: TechDebt
status: active
priority: P3
trigger: null
created_at: '2026-10-09'
updated_at: '2026-10-09'
closed_at: null
resolution: null
destination: null
source:
- RFC-0003 Delta 审核 DR1-13（第三轮 Delta R2 终审 P3，记入待办）
acceptance_criteria:
- 最小形态 2 行 fallback（未找到闭合围栏时 return 原文）+ 1 条回归用例；严禁引入 frontmatter 解析器或新判据框架
---

## 1. 背景与问题陈述
strip_leading_noise 对未闭合 frontmatter 围栏无兜底：闭合围栏搜索循环走到 EOF 后 idx 越界，lines[idx:] 变空串 → 整篇正文被丢弃 → 托管标记仍在却被判人工索引，register 返回 rc=0、文件不变、stdout 打印与事实相反的「检测到人工索引（无托管标记）」。外部截断/损坏的托管索引会使自愈链静默失联并误导排障。方向保守（零写盘、零数据破坏）。由 Delta R2 第三轮终审记入待办（不阻断交付）。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 最小形态 2 行 fallback（未找到闭合围栏时 return 原文）+ 1 条回归用例；严禁引入 frontmatter 解析器或新判据框架

## 4. 实施去向与结项记录
*(未开工)*
