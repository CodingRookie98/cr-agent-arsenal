# 派发超时预算与人机契约字段 实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: [PLAN-DISPATCH-BUDGET-2026]
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-16

> **目标元数据**
> - **所属项目**: CR Agent Arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 修复"派发的子智能体挂死即无人收口"这一已发生缺陷（A 档：超时预算 + 人机契约字段），并补齐多 agent 并行作业的**预算制编排**（不涉对外交期承诺）。
> - **创建日期**: 2026-09-16
> - **计划负责人**: DSH AI Agent
> - **状态**: 进行中
> - **隔离分支**: `feature/dispatch-budget-and-human-contract`（基于 master）
> - **需求方 / 批准人**: 王辉（本轮指令："A，另外也做多 agent 并行作业的部分，承诺交期的部分先不做"）
> - **技术调研备忘录**: 豁免（无第三方依赖引入；根因与取证见 §5）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。进度、复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P4 对抗式终审（串行派发）
- **当前活跃子任务**: Task P4.1（R1 红队，串行）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: L0 exit 0；4 条一致性断言通过；L-Doc 断链 0 / 体检 PASS
- **最新有效提交**: `0fa29f7`（Delta Re-Loop 第 2 轮修复）
- **P4 裁决记录**: R1 `blocker=1 major=3 minor=2 nit=2` → R2 `BLOCKERS=5 | REJECT_WITH_BLOCKERS`（B5 为 R2 独立实测发现的真实断链）→ Delta Re-Loop 第 1 轮 `aa3f094`（迭代 1/5）→ R1 复验 `BLOCKERS=2`（B6 引用处矛盾 / B7 出口空白）→ Delta Re-Loop 第 2 轮 `0fa29f7`（迭代 2/5）
- **派发账本摘要**: 当前在途 1 笔（R1 复验 Delta 2）；最近基线 `0fa29f7`；**恢复锚点** = `.goal-loop/dispatch-ledger.md`（高频易变明细，已被 gitignore）
- **阻断原因**: 无
- **执行后端**: 当前会话内联（用户已在上一轮明确选择 A 档并要求执行）
- **P4 纪律（防重演）**: **严禁并发派发 R1/R2**；R1 真实报告返回后方可派发 R2；派发预算 1 个检查点周期

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.1 核心交付物清单
- [ ] **A-1 派发超时预算与替代路径**：`skills/goal-loop/references/host-adapters.md`
- [ ] **A-2 计划模板人机契约字段**：`skills/goal-loop/templates/goal-plan-template.md`
- [ ] **A-3 需求确认文档验收标准段**：`skills/doc-governance/references/rfc-crystallization-lifecycle.md`
- [ ] **并行-1 预算制编排规则**（派发即登记 / 无用户交互 / 预算计量）：同上 host-adapters.md
- [ ] **并行-2 反模式诊断入口**（违规记录与恢复）：`skills/dual-round-review/SKILL.md`
- [ ] 治理回填：`docs/GOVERNANCE.md`、`docs/index.md`

### 1.2 依赖选型与开源调研结论
- **复用裁决**: 复用既有反模式表（`dual-round-review/SKILL.md:166-176`）与后端能力矩阵（`host-adapters.md:25-34`），不新建技能、不新建目录。

### 1.3 严禁事项与反模式
- 严禁并发派发 R1/R2（`dual-round-review/SKILL.md:176` 既有铁律）；
- 严禁把"预算"重新定义为人类日历/工期估计（用户已明确本期不做对外交期承诺）；
- 严禁在派发提示词中要求子智能体调用人类交互（并发下必然被环境拒绝，见 §5 证据 E3）。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: MEDIUM（改动 skill 源文件与公共模板契约）
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `git diff --check` + 一致性断言
  - [x] **L-Doc 文档/元数据检查**: `check-doc-links.py`、`audit-doc-health.py`
  - [ ] **L1/L2/L3**: 豁免（无可执行代码单元 / 无运行时模块 / 无 CLI-UI 链路）
- **豁免依据**: testing-decision-matrix 第 2 节"纯文档/注释变更"行；因触及公共模板契约，**额外加载补偿控制**：
  ```bash
  git diff --check
  # 断言 1：派发预算在 host-adapters 与 SKILL.md 均出现（跨文件一致）
  grep -c "派发预算\|超时预算" skills/goal-loop/references/host-adapters.md skills/dual-round-review/SKILL.md
  # 断言 2：模板具备"需求方/批准人"字段
  grep -c "需求方\|批准人" skills/goal-loop/templates/goal-plan-template.md
  # 断言 3：RFC 具备验收标准段
  grep -c "验收口径\|验收标准" skills/doc-governance/references/rfc-crystallization-lifecycle.md
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P3: 原子子任务实现
- [x] **Task P3.1**: host-adapters 新增派发超时预算与并行编排契约（A-1 + 并行-1）
- [x] **Task P3.2**: 计划模板补需求方/批准人/验收字段（A-2）
- [x] **Task P3.3**: RFC 模板补验收标准段（A-3）
- [x] **Task P3.4**: dual-round-review 补派发预算纪律与违规诊断入口（并行-2）

### P3.5: 集成验证与全局门禁
- [x] **Task P3.5.1**: 运行全部门禁与三条一致性断言，确认 Exit Code 0
- [x] **Task P3.5.2**: 复核无"工期/人日/交期"类表述被误引入（命中项均为禁止性说明）

### P4: 对抗式终审
- [ ] **Task P4.1**: **串行**派发 R1 红队穿透（派发即登记，超预算即中断并记录）
- [ ] **Task P4.2**: 取得 R1 真实报告**后**派发 R2 元审判（严禁并发）
- [ ] **Task P4.3**: Delta Re-Loop 修复（上限 5 次）

### P5: 文档全向归档与联动升级
- [ ] **Task P5.1**: 回填 `docs/GOVERNANCE.md` 与 `docs/index.md`
- [ ] **Task P5.2**: 计划结项与最终总结

---

## 4. 未覆盖项登记 (Explicitly Uncovered — 不默认通过)

| # | 未覆盖问题 | 状态 | 风险定性 | 建议处置 |
|---|---|---|---|---|
| U1 | 通道 C「修复前先复现」对 flaky / 环境相关缺陷无处理路径（承上轮） | 本轮不处理 | LOW-MEDIUM | 下一轮增量补充"最小复现脚本 + 可观测证据 + 复现失败 3 次即熔断升级"判据 |
| U2 | 对外交期承诺机制 | **用户明确本期不做** | — | 待未来需要对外承诺时另立目标 |

---

## 5. 研究发现与环境状态记录 (Context Log)

- **[2026-09-16] 证据 E1（根因）**: `dual-round-review/SKILL.md:176` 既有反模式已禁止并发派发 R1/R2；上一轮主会话**违反了既有规范**（并发派发），导致 R2 零输入、仅出具"独立核查版"。**本项目为规范执行缺陷，非规范缺失**。
- **[2026-09-16] 证据 E2（机制空洞）**: `host-adapters.md` 全文无"派发后等待预算"概念；`failure-recovery-protocol.md:61` 的 10 分钟超时仅管**被测进程**，不管**已派发的子智能体** → 挂死无人收口，需人类手动中断。
- **[2026-09-16] 证据 E3（并行与人类接口冲突）**: R2 子智能体在存活代理下调用 `ask_user_question` 被拒（`human interaction is unavailable while the calling agent is owned by another live agent`）→ 派发提示词**必须自包含所需决策**，禁止把人类交互留给子智能体运行时索取。
- **[2026-09-16] 证据 E4（时间量词）**: 全库 `工期/排期/人日/交期` 零命中；AI 侧真实约束全为**计次**（3-Tries、Delta Re-Loop ≤ 5、2-Action Rule），故本期以"预算"表达编排约束，不引入日历。

---

## 6. 修订历史 (Revision History)
- **[2026-09-16]**: 计划创建（Heavy Track）。
