# `dual-round-review` 双轮对抗审查技能架构设计书 (Architecture & Design Specification)

> **文档控制信息**
> - **文档标识**: SKILL-DES-DUAL-ROUND-REVIEW-2026
> - **当前版本**: V2.0.0 (宿主无关派发 + 审查记录锚点 + 三模式)
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-14

---

## 1. 背景与目标 (Problem & Goals)

大模型编程面临三大核心陷阱：**讨好型盲从（Sycophancy）**、**浅层打补丁（Palliative Patching）** 与 **审查幻觉与过度工程（Over-engineering）**。双轮对抗审查以"红队穿透 + 元架构师审判"级联机制应对。

V2.0 的三项结构目标：

1. **可移植**：派发不绑定任何厂商工具名与平台；
2. **可恢复**：审查循环状态落盘，跨会话/中断可续；
3. **可解析**：报告与裁决使用稳定 ID，便于编排者机械消费。

---

## 2. 审查模式 (Review Modes)

| 模式 | 轮次 | 适用场景 | 产出 |
|---|---|---|---|
| **Full（默认）** | R1 红队 → R2 元审判 | Heavy Track / 核心架构 / 关键业务链路 / Pre-Merge | 终审裁决明细表 |
| **Light（单轮）** | 仅 R1 红队 + 轻量裁决 | Fast-Track / 局部定向改动 | R1 报告 + 轻量裁决表 |
| **Delta（再循环）** | Full 或 Light 的再循环 | 阻断项修复后，以修复提交为新基线 | 更新后的审查记录与终审 |

**升级为 Full 的触发条件**：改动触及公共契约、核心业务链路、鉴权/并发/数据一致性，或即将合并 PR/发布。

---

## 3. 宿主无关派发模型 (Host-Agnostic Dispatch)

* **能力优先**：按"宿主实际的子智能体派发能力"选择，不绑定工具名。
* **同步/异步分流**：
  * 同步派发（调用即返回结果）——当前回合直接取回报告；
  * 异步派发（返回句柄、稍后唤醒）——结束回合等待唤醒。
  * 判定依据是工具的返回语义，而非平台名称。
* **上下文隔离**：R1、R2 各在独立子智能体中运行，只接收 Spec、Diff 与（R2 额外）R1 报告，不传入主会话历史。
* **真实产出纪律**：子智能体真实返回前，主智能体不输出任何审查结论。

---

## 4. 审查记录锚点 (Review Record Anchor)

审查循环的短周期状态必须落盘，避免上下文截断后丢失 `Previous Blockers` 与迭代计数。记录文件固定为 `.review-context/review-<baseline-sha>.md`（该目录已 gitignore），schema：

```markdown
# 审查记录 · <baseline-sha>
- **模式**: [full | light | delta]
- **基线**: <BASE_SHA>..<HEAD_SHA>
- **轮次**: [1 | 2 | ...]
- **迭代计数**: [n/3]
- **Previous Blockers**: [稳定 ID 列表，或 无]
- **Round 1 结论**: [摘要或报告路径]
- **终审裁决**: [🔴 阻断交付 | ✅ 准予交付 | 未定]
- **阻断项统计**: [🔴 X / 🟡 Y / ⚪ Z]
```

由 `scripts/prepare-review-context.sh` 在提取上下文时 scaffold（`--no-record` 可关闭）。

---

## 5. Diff 范围边界锁 (Diff-Scope Boundary Lock)

完整规则定义在 `references/verdict-rubric.md` §3，作为**单一真相源**。由于审查子智能体上下文隔离、无法自行读取该文件，`round-1-red-team.md` 与 `round-2-meta-architect.md` 模板中**内联**该规则；编排者侧的 `SKILL.md` 只引用不复制。

---

## 6. 输出契约 (Output Contract)

* **稳定 ID**：R1 候选缺陷使用 `R1-<n>`；R2 裁决表沿用同一 ID，实现两轮机械对齐。
* **Previous Blockers**：上一轮 R2 裁定的阻断项稳定 ID 列表（如 `[R1-3, R1-7]`），从审查记录读取。
* **证据要求**：驳回或降级 R1 评级必须附 `文件:行` 级反证据；无证据的降级不生效。
* **批量降级红旗**：R2 一次性降级/驳回多个 P0/P1 时，主智能体抽检证据充分性。

---

## 7. 环境专有维度 (Conditional Dimensions)

React Rules of Hooks、SSR 水合、Storage 沙盒等维度**按 diff 文件特征条件激活**（`*.tsx`/`*.jsx`/`*.vue`/`*.svelte`/`next.config.*`，或含 `"use client"`/`"use server"`/`react`/`next/*` 导入）。非前端改动跳过该维度，并在输出中标注 `本节未激活（非客户端/SSR 改动）`（不填 N/A 占位）。

---

## 8. 有界收敛 (Bounded Convergence)

同一模块连续 **3 次**双轮循环未清零阻断项，或两轮陷入无法调和的哲学争议时：停止自动循环，产出《双轮审查争议焦点报告》，升级人类裁决。修复收敛在最小改动范围，避免基线漂移。

---

## 9. V2.0 变更摘要 (V2.0 Refactor Summary)

| 关注点 | V1.x | V2.0 |
|---|---|---|
| 派发 | 绑定 `invoke_subagent`/`Agent`/`agy -p`，无条件"结束回合等待" | 宿主无关能力 + 同步/异步分流 |
| 循环状态 | 只在上下文中 | `.review-context/review-<sha>.md` 锚点 + 恢复规则 |
| 模式 | 只有双轮 | Full / Light / Delta 三模式 |
| 环境维度 | React/SSR 强制项 | 按 diff 特征条件激活 |
| 边界锁 | 7 处复述 | `verdict-rubric.md` §3 单一真相源（模板内联因隔离需要） |
| R2 上下文 | 只给 diff，却要求核验上游 | 对等读仓库授权 + 驳回需 file:line 反证据 |
| 输出 | 编号为 `1,2,3` | 稳定 ID `R1-<n>`，两轮对齐 |
| 脚本 | 只打印指引 | `--help` + 审查记录 scaffold |
| 验证 | 无测试 | `tests/` 7 项脚本单测 + 断链门禁 |

重构实施计划：`docs/project/plans/2026-09-14-dual-round-review-v2.md`。

---

## 10. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 修订描述 |
| :--- | :--- | :--- | :--- |
| **V2.0.0** | 2026-09-14 | Antigravity AI Agent | 宿主无关派发、审查记录锚点、Light 模式、条件维度、R2 证据契约 |
