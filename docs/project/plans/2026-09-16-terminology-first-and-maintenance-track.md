# 术语先行与维护通道机制升级 实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: [PLAN-GOVERNANCE-TERMINOLOGY-2026]
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-16

> **目标元数据**
> - **所属项目**: CR Agent Arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 补三处机制缺口 —— ① 术语对齐缺失"先行性"且与收敛律的影响分级规则冲突；② 判定矩阵缺"任务生命周期阶段"维度，维护类任务无轻量通道；③ RFC 契约缺术语表段落与术语 SSOT 落位。
> - **创建日期**: 2026-09-16
> - **计划负责人**: DSH AI Agent
> - **状态**: 已完成（P4 取得 Zero Blockers）
> - **隔离分支**: `feature/goal-terminology-and-maintenance-track`
> - **技术调研备忘录**: [豁免: P0.5 无新增第三方依赖或技术选型，改动为自研文档契约]
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。进度、复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: 已完成（P4 取得 Zero Blockers，全部阶段闭合）
- **当前活跃子任务**: 无（P3~P5 全部闭合）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: L0 exit 0；L-Doc 断链 0，健康度 35/35 · 25/25 · 20/20 · 10/10 · 10/10 → PASS
- **最新有效提交**: `bb0b2c0`（R1 复验基线）
- **阻断原因**: 无
- **执行后端**: 当前会话内联（用户本轮显式点名"1 2 3 都做"并要求执行，视为已完成 P3 后端确认；如需隔离后端请随时打断）

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.1 核心交付物清单
- [x] 修正术语对齐逻辑冲突：`contexts/AGENTS.md`、`skills/goal-loop/references/stage-progression-protocol.md`
- [x] 新增维护通道与任务生命周期维度：`skills/goal-loop/references/stage-progression-protocol.md`
- [x] 术语表契约与 SSOT 落位：`skills/doc-governance/references/rfc-crystallization-lifecycle.md`
- [x] 术语漂移校验与维护通道声明：`skills/goal-loop/references/documentation-sync-matrix.md`、`skills/goal-loop/SKILL.md`
- [x] 治理修订历史回填：`docs/GOVERNANCE.md`、`docs/index.md`

### 1.2 依赖选型与开源调研结论
- **P0.5 备忘录**: 豁免。无第三方依赖引入，全部改动为本仓库自研文档契约。
- **复用裁决**: 复用 RFC 孵化机制与 `docs/reference/rules/` 象限，不新建文档类型、不新建目录。

### 1.3 严禁事项与反模式
- 严禁创建 `docs/requirements/` 等瀑布旧目录；
- 严禁改动第三方锁定技能（`mattpocock/*` 系列）本体；
- 严禁把"术语表"膨胀为全量词表（只登记核心术语 + 易歧义术语）；
- 严禁在维护通道中裁掉熔断（3-Tries）与定向红队审查。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

> 依据 `testing-decision-matrix.md` 第 2 节：「纯文档 / 注释变更 → **L-Doc**，豁免 L1/L2/L3」。

- **改动风险定级**: MEDIUM（改动 owner 未被审计过的 skill 源文件，非 `AGENTS.md` 本体）
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `git diff --check`（空白/冲突残留）+ 一致性断言（grep 关键锚点）
  - [x] **L-Doc 文档/元数据检查**: `check-doc-links.py`（断链 + 锚点）、`audit-doc-health.py`（健康度 PASS）
  - [ ] **L1 单元测试**: 豁免（无可执行代码单元）
  - [ ] **L2 模块集成测试**: 豁免（无运行时模块）
  - [ ] **L3 端到端测试**: 豁免（无 CLI/UI 链路变更）
- **豁免依据**: testing-decision-matrix 第 2 节"纯文档/注释变更"行；但本次触及公共契约，**额外加载补偿控制**：L1 级一致性断言（下列命令），用于防止"矩阵维度加了一处、漏了另一处"的跨文件漂移。
- **精确验证命令清单**:
  ```bash
  # L0 静态门禁
  git diff --check

  # L1 补偿控制：跨文件一致性断言（三处必须同时出现"任务生命周期阶段"）
  grep -c "任务生命周期阶段" skills/goal-loop/references/stage-progression-protocol.md contexts/AGENTS.md

  # L-Doc 文档门禁
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P3: 原子子任务实现
- [x] **Task P3.1**: 修正术语对齐的逻辑冲突（术语先行 + 豁免影响分级 + 歧义定界）
  - **涉及文件**: `contexts/AGENTS.md`, `skills/goal-loop/references/stage-progression-protocol.md`
  - **验收命令**: `grep -n "全局前置项" contexts/AGENTS.md`
- [x] **Task P3.2**: 新增"任务生命周期阶段"判定维度与 Maintenance-Patch 轻量通道
  - **涉及文件**: `skills/goal-loop/references/stage-progression-protocol.md`, `contexts/AGENTS.md`
  - **验收命令**: 一致性断言（三处维度命名一致）
- [x] **Task P3.3**: RFC 契约新增术语表段落 + 术语 SSOT 落位（`docs/reference/rules/`）
  - **涉及文件**: `skills/doc-governance/references/rfc-crystallization-lifecycle.md`
  - **验收命令**: `grep -n "术语表" <上述文件>`
- [x] **Task P3.4**: 同步矩阵补术语漂移校验行 + 维护通道行；SKILL 路由表补维护通道
  - **涉及文件**: `skills/goal-loop/references/documentation-sync-matrix.md`, `skills/goal-loop/SKILL.md`
  - **验收命令**: `git diff --stat` 范围受控

### P3.5: 集成验证与全局门禁
- [x] **Task P3.5.1**: 运行全部 L0 + L1(补偿) + L-Doc 门禁，确认 Exit Code 0
- [x] **Task P3.5.2**: 全库术语/编号引用一致性复核（禁止伪引用，如"第 3.5 节"）

### P4: 对抗式终审
- [x] **Task P4.1**: R1 红队穿透 → 复验子智能体 `bc024b83` 对基线 `bb0b2c0` 出具 `R1B_VERDICT: BLOCKERS=0 | PASS_ZERO_BLOCKERS`（含 B3 四条逃逸路径逐条排空）
- [x] **Task P4.2**: R2 元架构师审判 → `R2_VERDICT: BLOCKERS=4 | REJECT_WITH_BLOCKERS`（独立核查版，4 项与主会话独立核证一致）
- [x] **Task P4.3**: Delta Re-Loop 第 1 轮（迭代 1/5）→ 修复 B1~B5 并提交 `bb0b2c0`，经 R1 复验裁决 Zero Blockers 清零

### P5: 文档全向归档与联动升级
- [x] **Task P5.1**: 回填 `docs/GOVERNANCE.md` 与 `docs/index.md` 修订历史
- [x] **Task P5.2**: 计划状态置为 `[已完成]`（Zero Blockers 已取得），输出最终执行总结

---

## 4. 未覆盖项登记 (Explicitly Uncovered — 不默认通过)

> 按提问收敛律「提前收敛必须登记被判定为低影响而转为默认假设的分支」的同一纪律，P4 审查中**未被任何审查方回答**的问题在此显式登记，不得视为已通过：

| # | 未覆盖问题 | 状态 | 风险定性 | 建议处置 |
|---|---|---|---|---|
| U1 | 通道 C 要求「修复前先复现」，但存量维护常遇**非确定性缺陷**（flaky / 环境相关）；规程未给出不可稳定复现时的处理路径 | 已向 R1 派发问询，**因该子智能体长时间无产出被中断，未获回答**；R1 复验与 R2 均未覆盖 | LOW-MEDIUM：可能导致 flaky 缺陷被强行套用「必须 Red 先行」而卡住，或反向导致跳过复现即修复 | 下一轮增量补充「最小复现脚本 + 可观测证据 + 复现失败 3 次即熔断升级」的合格性判据 |
| U2 | 存量维护 vs 契约扩展的分类仍由 Agent 自行裁定（无自动强制） | R1 复验判定为「任何分类机制的固有属性，非本次引入缺口」 | LOW | 接受，不追加机制；若后续观测到误判再补判据 |

---

## 5. 研究发现与环境状态记录 (Context Log)

- **[2026-09-16] 探查 1**: 全库 `grep 术语|Glossary` 命中 3 处均非术语表 —— RFC 模板 §1~§6 无术语表段落，术语无 SSOT。
- **[2026-09-16] 探查 2**: 判定矩阵 4 维度全部度量"改动复杂度"，无一度量"任务生命周期阶段"；维护类任务在路由层无判定依据。
- **[2026-09-16] 探查 3**: 收敛律"LOW 影响项不提问"与术语对齐存在逻辑冲突 —— 术语歧义为全局乘法级影响，不可用局部影响分级过滤。
- **[2026-09-16] 自行发现**: 上一轮提交在结晶 SOP 写入"第 3.5 节已收束"属伪造引用（RFC 模板无该节），已修正为"第 5 节/第 6 节"。

---

## 6. 修订历史 (Revision History)
- **[2026-09-16] P4 裁决记录**: R2 出具 4 项阻断（B1~B4）；Delta Re-Loop 第 1 轮修复后由 R1 复验子智能体对基线 `bb0b2c0` 裁决 **Zero Blockers**。
- **[2026-09-16]**: 计划创建（Heavy Track）。
