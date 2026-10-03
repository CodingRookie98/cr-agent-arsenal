# `dual-round-review` 双轮对抗审查技能架构设计书 (Architecture & Design Specification)

> **文档控制信息**
> - **文档标识**: SKILL-DES-DUAL-ROUND-REVIEW-2026
> - **当前版本**: V2.1.0 (宿主无关派发 + 审查记录锚点 + 三模式 + 交付凭据归档)
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

由 `scripts/prepare-review-context.sh` 在提取上下文时 scaffold（`--no-record` 可关闭；传 `--slug=<slug>` 时同时 scaffold 交付凭据归档目录与索引骨架）。

### 4.1 交付凭据归档 (Review Evidence Archive · V2.1.0)

审查报告全文是**不可重建**的交付凭据——会话结束后，子智能体的推理链、攻击路径推演与 `文件:行` 反证据即永久消失。V2.0 只落盘 8 字段摘要锚点，且该目录被 gitignore，导致报告全文从未落盘。V2.1.0 引入**三层职责分离**：

| 层 | 位置 | 生命周期 | 进版本库 |
|:---|:---|:---|:---:|
| ① 运行时状态 | `.review-context/review-<baseline-sha>.md` | 一次审查循环 | ❌（gitignore，正确设计） |
| ② 交付凭据 | `<归档根>/<YYYY-MM-DD>-<slug>/` | 交付审计期 | ✅ |
| ③ 机械门禁 | `scripts/check-review-report.sh` | — | ✅ |

* **归档根**：推荐默认 `docs/project/reviews/`；宿主项目若已有既定审查记录规范则**以宿主为准**，实际归档根登记至锚点「归档索引」段。
* **命名**：一个交付单元一个目录（Delta 再循环共享，日期取首次审查日）；轮次文件 `<轮次标记>-<base7>..<head7>.md`（`r1` / `r2` / `delta-r1` / `delta-r2`）。
* **写入责任**：子智能体 Read-Only 约束不变；主智能体逐字写盘并登记 SHA256 前 12 位——指纹使「转录失真」可被机械检出。
* **R2 输入双通道**：优先「归档文件路径 + SHA256」（要求 R2 读取原文并核验），宿主无读文件能力时降级内联并标注「内联降级」。
* **门禁校验项**：索引字段齐备 / 报告在位非空 / 指纹一致 / R1 五区块 / R2 三区块 / 稳定 ID 两轮对齐 / 围栏剥离后仍齐备。
* **异常降级**：落盘失败按 `goal-loop` 的 `host-adapters.md` §5 收口，且**不得宣布审查通过**；Delta 同名冲突视为基线漂移缺陷，不得覆盖。

完整契约与决策台账见 RFC-0001（`docs/proposals/RFC-0001-review-report-archive.md`）。

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

### 9.1 V2.1.0 变更摘要 (V2.1.0 Refactor Summary)

| 关注点 | V2.0 | V2.1.0 |
|---|---|---|
| 报告产物 | 仅 8 字段摘要锚点；报告全文只存在于会话 | 全文逐字归档至版本库跟踪的归档根 + SHA256 指纹 |
| 受众 | R2 依赖主智能体内联转录；人类不可见 | R2 优先读归档原文并核验指纹；人类 `git clone` 即可读 |
| 可移植性 | — | 归档根「推荐默认 + 宿主优先」，实际根登记至运行时锚点 |
| 机械门禁 | 无 | `check-review-report.sh`（索引 / 指纹 / 两轮区块 / 稳定 ID 对齐，`--require-verdict=PASS`） |
| 脚本 | 锚点 scaffold | 追加 `--slug` / `--archive-root` 归档 scaffold（默认关闭，向后兼容） |
| 验证 | 7 项脚本单测 | 新增 23 项契约测试 + 模板↔门禁标题漂移防护（含实跑反证） |

实施计划与需求确认：`docs/project/plans/2026-10-04-review-report-archive.md`（RFC-0001）。

---

## 10. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 修订描述 |
| :--- | :--- | :--- | :--- |
| **V2.1.0** | 2026-10-04 | DSH AI Agent | 交付凭据归档（三层职责分离）+ `check-review-report.sh` 机械门禁 + R2 双通道输入；需求源 RFC-0001 |
| **V2.0.0** | 2026-09-14 | Antigravity AI Agent | 宿主无关派发、审查记录锚点、Light 模式、条件维度、R2 证据契约 |
