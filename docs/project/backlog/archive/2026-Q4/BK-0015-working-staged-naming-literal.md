---
id: BK-0015
title: working/staged 模式的报告命名与 base7..head7 模板字面不符
type: TechDebt
status: rejected
priority: P3
trigger: null
created_at: '2026-10-08'
updated_at: '2026-10-14'
closed_at: '2026-10-14'
resolution: wontfix
destination: 不接受：纯命名措辞澄清，零运行时与门禁影响；卡片维护成本高于一句文案收益，可在后续文档润色时顺带修正
source:
- dual-round-review V2.2.0 Delta R2 DR-6（历史既有）
acceptance_criteria:
- 在 SKILL.md 命名规范处注明 --working/--staged 模式使用字面标记（working/staged）而非短 SHA
---

## 1. 背景与问题陈述
历史既有（RFC-0001 行为）：--working/--staged 下路径为 <轮次>-working..<head7>.md，base7 位是字面标记而非短 SHA，与 SKILL.md 的 <轮次标记>-<base7>..<head7>.md 命名模板字面不符。仅命名口径差异，不影响 Write-Once 与门禁（不校验文件名形态）。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 在 SKILL.md 命名规范处注明 --working/--staged 模式使用字面标记（working/staged）而非短 SHA

## 4. 实施去向与结项记录

### 结项记录 (2026-10-14)
- **结论**: wontfix
- **去向/凭据**: 不接受：纯命名措辞澄清，零运行时与门禁影响；卡片维护成本高于一句文案收益，可在后续文档润色时顺带修正
- **归档目录**: archive/2026-Q4/
- **提示**: §3 DoD 仍有 1 项未勾选 —— `close` 不代勾验收准则，请作者核验后更新卡片（本项为机械统计）。
