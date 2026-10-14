---
id: BK-0034
title: baseline.json 损坏静默降级导致 C-10 假阳性与假阴性
type: Bug
status: completed
priority: P2
trigger: skills/spec-evolution/references/baseline.json 被人工写坏或键被删除
created_at: '2026-10-12'
updated_at: '2026-10-14'
closed_at: '2026-10-14'
resolution: delivered
destination: fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/）
source:
- dual-round-review Delta R1 R1-5（spec-evolution-v1，R2 复现成立 P2）
acceptance_criteria:
- baseline 解析失败时显式失败（exit 2 或输出 baseline_valid=false）；judge 对 baseline 缺失或为 0 给出显式提示而非静默跳过；两条新增断言覆盖假阳性与假阴性
---

## 1. 背景与问题陈述
collect-facts.py 的 except (JSONDecodeError, KeyError, TypeError): pass 使基线退化为 lines=0/bytes=0，未改动的根提示词被判 C-10 假阳性；删除 root_prompt.baseline 键则 C-10 静默消失（假阴性）。两种污染均静默发生。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [x] baseline 解析失败时显式失败（exit 2 或输出 baseline_valid=false）；judge 对 baseline 缺失或为 0 给出显式提示而非静默跳过；两条新增断言覆盖假阳性与假阴性

## 4. 实施去向与结项记录

### 结项记录 (2026-10-14)
- **结论**: delivered
- **去向/凭据**: fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/）
- **归档目录**: archive/2026-Q4/
- **验收核验 (作者)**: §3 DoD 全部项已核验落地（回归用例转红→转绿 + L0/L1/L-Doc 全绿 + R2 终审 Zero Blockers）；上方 `close` 的机械未勾选提示按实况收敛（工具侧缺口见 BK-0042）。
