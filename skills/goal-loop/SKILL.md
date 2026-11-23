---
name: goal-loop
description: Use for long-horizon, multi-file engineering goals (~10+ min) needing durable checkpoints, tiered testing (L0–L3), 3-Tries circuit breaking, and an independent Zero-Blockers review. Runs a 5-stage loop (Align, Plan, Execute, Verify, Close) with 3 tracks (Heavy Track, Fast-Track, Maintenance-Patch) for new features, cross-module refactors, and brownfield defect fixes.
license: MIT
---

# `goal-loop` 目标实现循环

## 概述

面向长程、跨模块研发与存量维护任务的自愈闭环状态机：以**计划文件为唯一可读真相源**，通过 **`Align → Plan → Execute → Verify → Close`** 五主阶段与三轨分流，按需联动外部技能，以分级测试（L0–L3）与独立对抗终审守住交付质量。

本文件是**路由层**：只声明触发条件、铁律、阶段指针与通道裁剪。阶段细则见 [stage-progression-protocol.md](references/stage-progression-protocol.md)。

---

## 何时使用 / 何时不用

**使用**（满足任一）：
- 涉及 2 个以上文件或模块，或改动公共契约/数据模型；
- 预期耗时超过约 10 分钟，或需要跨会话断点恢复；
- 存量系统缺陷修复，需要「先复现 + 最小修复 + 回归测试 + Diff 边界审查」；
- 需要分级测试（L0–L3）与独立 Zero-Blockers 终审门禁。

**不用**：纯文案微调、单行常量修改、直接的只读问答检索。

---

## 铁律 (Invariants)

1. **计划文件是唯一人类可读真相源**：进度、复选框与头部 `Active Checkpoint` 由智能体直接精准编辑维护，**不建并行状态文件**；会话内进度视图对接宿主原生步骤清单/工作流原语。
2. **先读检查点再动**：进入新阶段或恢复会话时，首选动作是读计划头部的 `Active Checkpoint`。
3. **未获用户明确认可（User Nod），不写代码、不写落地计划**（`Align` 门禁）。
4. **选型裁决未完成，不进 `Plan`**：优先复用既有模块与成熟开源方案，自研必须书面辩护。
5. **`Execute` 开工前向用户确认执行后端**：宿主原生子智能体 / 外部无头 CLI / 当前会话内联（见 [host-adapters.md](references/host-adapters.md)）。
6. **按裁定级别测试，先红后绿**：以计划《测试策略裁定书》的 L0–L3 级别为准，Exit Code 0 才允许原子提交。
7. **分支隔离**：在独立功能/修复分支工作，严禁直接在 `main`/`master` 写代码。
8. **交付前必须取得独立子智能体的 Zero Blockers 裁决**：Heavy Track 走全量双轮对抗审查；Fast-Track / Maintenance-Patch 走定向单轮红队审查，触及公共契约或核心链路时升级为全量双轮。
9. **重试有上限**：单错误 3-Tries 熔断（第 2 次触发微观调研，第 3 次冻结并升级）；场景级更小上限（编译/重构 2 次、循环摆动 1 次）优先触发；`Verify` 的 Delta Re-Loop 上限 5 次。
10. **事件驱动落盘**：在阶段切换、关键根因/契约确立、大块探索收敛及上下文压缩前（PreCompact）强制落盘检查点；超长原始日志按需卸载至 `.goal-loop/scratchpad.md`。
11. **Read-Modify-Verify 与 Git 安全红线**：写入后用 `git diff`、关键行回读或退出码验真；严禁破坏性 Git 命令（`reset`/`rebase`/`revert`/`restore`/`clean -fd`/`push -f`/`branch -D`）。

> 细则下沉在 `references/` 下对应文件，按需读取，勿抄回本文件。

---

## 五主阶段路由 (5-Stage Routing)

| 阶段 | 历史对照 | 目标 | 联动技能 | 产物 / 指针 |
|:---:|:---:|---|---|---|
| **Align** | P-1 / P0 / P0.5 | 意图对齐、压力澄清与开源选型 | `brainstorming` / `grilling` / `clarification-protocol` / `research` / `find-docs` | User Nod；RFC `docs/proposals/RFC-*.md`；调研落盘 `docs/explanation/analysis/` |
| **Plan** | P1 / P2 | 实施方案、L0–L3 测试定级与垂直切片拆解 | `writing-plans` | [goal-plan-template.md](templates/goal-plan-template.md) + [testing-decision-matrix.md](references/testing-decision-matrix.md) + [atomic-task-template.md](templates/atomic-task-template.md) |
| **Execute** | P3 | 隔离分支 TDD 原子实现与后端派发 | 宿主执行后端（开工前确认） | [host-adapters.md](references/host-adapters.md) |
| **Verify** | P3.5 / P4 | L2 集成构建、前端条件验收与独立对抗终审 | `frontend-qa-gate`（前端条件）+ `dual-round-review` | [stage-progression-protocol.md](references/stage-progression-protocol.md) |
| **Close** | P5 | 文档联动同步与计划归档 | `doc-governance`（可选） | [documentation-sync-matrix.md](references/documentation-sync-matrix.md) |

**三轨通道裁剪**：
- **Heavy Track（重型主航道）**：全量执行 `Align → Plan → Execute → Verify → Close` 与全量双轮对抗终审；
- **Fast-Track（敏捷轻量）**：豁免 `Align`，直入 `Plan`（轻量计划）→ `Execute` → `Verify`（定向单轮红队，触及契约升级双轮）→ `Close`；
- **Maintenance-Patch（存量维护）**：豁免 `Align` 与子任务重型拆解；保留 `Plan` 极简计划、`Execute`（定位 + 最小修复 + 回归测试）、`Verify`（L2 局部回归 + 定向单轮红队）、`Close`。**强制保留 3-Tries 熔断、修复前先复现、修复必带回归测试、Diff 边界锁**；一旦需改公共契约即升级 Heavy Track。

> **可选依赖**：`Align` / `Plan` 的外部技能是增强件而非前提。进入首个相关阶段前按 [optional-skill-dependencies.md](references/optional-skill-dependencies.md) 探测一次，按三分支处置——**缺什么问什么，但不得阻塞，也不得伪称已激活**。

---

## 异常恢复与交接脚本

- **异常熔断**：同一错误连续 3 次未收敛即触发 `STOP → RECORD → RESEARCH → ESCALATE`；升级为非阻塞（报告落盘、受阻点 `parked`、下游 `blocked-by`、独立项继续推进）。细则见 [failure-recovery-protocol.md](references/failure-recovery-protocol.md)。
- **文件指针交接（可选）**：派发子任务或终审前，可用 `scripts/pack-handoff.py` 打包独立交接文件，仅传路径指针以防主上下文膨胀：

```bash
SKILL_DIR="<goal-loop 技能实际所在目录>"
python3 "$SKILL_DIR/scripts/pack-handoff.py" brief <plan_file> --task <task_id> [--out <path>]
python3 "$SKILL_DIR/scripts/pack-handoff.py" review-pkg <base_ref> [head_ref] [--out <path>]
```

---

## 参考导航

- [stage-progression-protocol.md](references/stage-progression-protocol.md) — 五主阶段执行细则、三轨判定矩阵与门禁
- [testing-decision-matrix.md](references/testing-decision-matrix.md) — 改动特征到 L0–L3 的测试定级与防逃逸规则
- [host-adapters.md](references/host-adapters.md) — `Execute` 后端适配、派发预算与 2026 自治编排纪律
- [failure-recovery-protocol.md](references/failure-recovery-protocol.md) — 3-Tries 熔断、场景子上限与非阻塞升级
- [context-engineering.md](references/context-engineering.md) — 事件驱动落盘、读写矩阵与断点恢复
- [documentation-sync-matrix.md](references/documentation-sync-matrix.md) — `Close` 阶段 Diátaxis 文档联动复核清单
- [optional-skill-dependencies.md](references/optional-skill-dependencies.md) — 可选技能探测与三分支降级
- 模板套件：[goal-plan-template.md](templates/goal-plan-template.md)（实施计划）、[atomic-task-template.md](templates/atomic-task-template.md)（原子子任务规约）
