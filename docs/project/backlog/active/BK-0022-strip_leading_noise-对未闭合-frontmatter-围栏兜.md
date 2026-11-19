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
- 涉及模块: skills/doc-governance/scripts/manage-doc-index.py（strip_leading_noise）+ 其纯逻辑用例
- 风险点: 修法必须「保守」——未闭合围栏一律按普通正文处理，不猜测意图、不写盘；若日后引入容错解析器即为过度设计

## 3. 验收准则与验证设计 (DoD)
- [x] 最小形态 fallback（未找到闭合围栏时 return 原文，共 7 行含注释）+ 3 条回归用例；未引入 frontmatter 解析器或新判据框架

## 4. 实施去向与结项记录
### 实施记录（2026-11-19）

在闭合围栏搜索循环之后加 EOF 判定：`idx >= len(lines)` 即视为围栏未闭合，**返回去 BOM 的原文**，而不是把 `idx` 推过末行后切片成空串。

取舍说明：另两种写法都被否掉——(a) 抛错会让一次磁盘损坏阻断整个 register 流程，而该流程本可只降级；(b) 「把未闭合围栏当围栏内容继续剥离」等于猜测作者意图，且剥多剥少都能自圆其说。返回原文是唯一零损失、可解释的出口：托管标记若真在文中，判据依旧能命中。

回归 3 条（`test_doc_index_convention.py::TestUnclosedFrontmatterFence`）：未闭合围栏下正文与托管标记不得丢失、闭合围栏剥离行为逐字不变（防回归到旧语义）、BOM + 闭合围栏组合仍能定位 H1。doc-governance 全量 144 passed / 7 skipped。
