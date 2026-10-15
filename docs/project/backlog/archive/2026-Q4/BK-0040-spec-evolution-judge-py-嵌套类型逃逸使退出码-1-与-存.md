---
id: BK-0040
title: spec-evolution judge.py 嵌套类型逃逸使退出码 1 与「存在 BLOCKER/HIGH」同码
type: Bug
status: completed
priority: P2
trigger: '`--facts` 输入被截断、被手工修改，或上游 `collect-facts.py` schema 漂移时可达（`--facts` 接受任意外部输入）。'
created_at: '2026-10-12'
updated_at: '2026-10-14'
closed_at: '2026-10-14'
resolution: delivered
destination: fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/）
source:
- Delta R2 终审裁决书残余发现（docs/project/reviews/2026-10-12-spec-evolution-v1/delta-r2-fe8da78..2100136.md）
- 主智能体逐条独立复现（2026-10-12，干净基线夹具对照）
acceptance_criteria:
- 嵌套类型畸形 `description_chars="abc"` / `registrations="x"` / `registrations=5` / `oversized_files=[123]`
  / `cross_skill_links=5` 一律退出码 2，且不写出任何产物
- 新增判定契约测试覆盖上述各例（在收紧前的实现上应转红）
- 修复后必须作为新基线重跑完整双轮闭环（单测全绿不替代外部审查）
---

## 1. 背景与问题陈述
**现象**：D-24（Delta 轮重派 R1-1）已为 `load_facts` 加**顶层**键类型校验，但校验未下探到 `skills[]` 的成员字段。畸形嵌套值会令 `build_findings` 抛异常，解释器以状态码 **1** 退出 —— 与「存在 BLOCKER/HIGH」的语义同码，把「输入坏了」伪装成「存在高危裁决」。

**复现（干净基线：仅 `spec-evolution` 自身，正常 rc=0 / findings=0）**：

| 注入 | 实际 rc | 报告 | 异常 |
| :--- | :--- | :--- | :--- |
| `description_chars="abc"` | **1** | 无 | `TypeError: '>=' not supported between instances of 'str' and 'int'` |
| `registrations="x"` | **1** | 无 | `AttributeError: 'str' object has no attribute 'items'` |
| `registrations=5` | **1** | 无 | `AttributeError: 'int' object has no attribute 'items'` |
| `oversized_files=[123]` | **1** | 无 | `AttributeError: 'int' object has no attribute 'count'` |
| `cross_skill_links=5` | **1** | 无 | `TypeError: 'int' object is not iterable` |

**澄清两处不成立的表述**（主智能体复核结论，避免按错误线索修复）：R2 报告举例的 `skills[].path=123` 与 `skills[].files="x"` 实测 **rc=0**（判定器不消费这两个键，不抛异常）；且上述崩溃路径**均不写出报告**，故不构成「写出伪造报告」。R2 原判 `🟡` 非阻断的结论与严重度**维持不变**（退出码仍非 0，编排方不会误采信为 CLEAN）。

**建议修法（而非逐键白名单）**：在 `main()` 中把 `build_findings(facts)` 包一层兜底 —— 捕获 `FactsError` 以外的异常并转译为 `FactsError`（→ 退出码 2 + `❌` 诊断）。逐键白名单只会把「打地鼠」搬到下一层；兜底一次关闭**整类**逃逸，且复杂度更低。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [x] 嵌套类型畸形 `description_chars="abc"` / `registrations="x"` / `registrations=5` / `oversized_files=[123]` / `cross_skill_links=5` 一律退出码 2，且不写出任何产物
- [x] 新增判定契约测试覆盖上述各例（在收紧前的实现上应转红）
- [x] 修复后必须作为新基线重跑完整双轮闭环（单测全绿不替代外部审查）

## 4. 实施去向与结项记录

### 结项记录 (2026-10-14)
- **结论**: delivered
- **去向/凭据**: fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/）
- **归档目录**: archive/2026-Q4/
- **验收核验 (作者)**: §3 DoD 全部项已核验落地（回归用例转红→转绿 + L0/L1/L-Doc 全绿 + R2 终审 Zero Blockers）；上方 `close` 的机械未勾选提示按实况收敛（工具侧缺口见 BK-0042）。
