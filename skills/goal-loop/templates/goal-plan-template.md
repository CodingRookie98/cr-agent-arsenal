# [目标名称] 实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: [PLAN-<模块>-YYYY]
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: YYYY-MM-DD
> - **所属项目**: [项目名称]
> - **执行通道**: [Heavy Track | Fast-Track | Maintenance-Patch]
> - **目标简述**: [一句话描述最终交付物与业务价值]
> - **需求方 / 批准人 (User Nod)**: [姓名或角色] | **批准基线**: [commit SHA 或版本号]
> - **状态**: [未开始 | 进行中 | 已完成 | 熔断受阻]
> - **隔离分支**: `feature/goal-[name]`（或按项目分支规范）
> - **调研分析文档**: `docs/explanation/analysis/YYYY-MM-DD-<topic>.md`（或 `[豁免: Fast-Track / 复用既有模块]`）
> - **临时运行目录**: `.goal-loop/`（已被 `.gitignore` 忽略，按需存放 scratchpad、派发账本与交接包）

> **唯一真相源声明**：本文件是当前目标的唯一跨会话真相源，由主调度智能体直接精准编辑维护（会话内实时视图同步至宿主原生步骤清单，不另建并行状态文件）。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)

- **当前执行通道**: [Heavy Track | Fast-Track | Maintenance-Patch]
- **当前活跃阶段**: [Align | Plan | Execute | Verify | Close | DONE]
- **当前活跃子任务**: [无 | Task E-1]
- **当前子任务重试计数**: [0/3；第 2 次触发微观调研，第 3 次熔断]
- **外层 Delta Re-Loop**: [0/5]
- **最后一次验证状态**: [无 | Exit Code 0, X passed]
- **最新有效提交**: [无 | Commit SHA]
- **在途派发摘要**: [无 | 句柄/基线，明细见 `.goal-loop/dispatch-ledger.md`]
- **阻断原因**: [无 | 具体原因与 `parked` 项]

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.1 验收口径 (Acceptance Criteria — 由需求方定义)
> AI 侧定义「怎么测」，需求方定义「算不算达成」；以下字段空缺即视为需求未收敛，不得进入 `Execute`。

- **验收人 (Acceptor)**: [需求方本人 / 指定验收角色]
- **验收场景 (Acceptance Scenarios)**: [需求方视角的可观察行为，而非内部实现]
- **明确不验收项 (Non-Acceptance)**: [本轮明确排除的范围，防止范围蔓延]
- **口径冲突裁决人**: [需求口径与既有契约冲突时的最终裁决人]

### 1.2 核心交付物与选型结论
- [ ] 核心模块新增/修改: `[文件相对路径]`
- [ ] 自动化测试用例: `[单元测试与集成测试路径]`
- [ ] 关联文档同步: `[文档相对路径]`
- **调研分析链接**: `docs/explanation/analysis/YYYY-MM-DD-<topic>.md`（或豁免说明）
- **选型裁决与契约核准**: [采用开源库 `pkg` / 复用既有封装 / 自研（已书面辩护）| 官方文档核准的关键版本与签名]

### 1.3 严禁事项 (Strict Exclusions)
- 严禁修改目标范围之外的公共契约；严禁未跑裁定测试直接提交；严禁引入未核准的异构依赖；
- [项目特定的运行时安全或架构红线]。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

> 依据 `testing-decision-matrix.md` 四步推理裁定：

- **改动风险定级**: [LOW / MEDIUM / HIGH]
- **强制执行级别**:
  - [x] **L0 静态门禁**: 语法、类型检查与 Lint 零警告
  - [x] **L1 单元测试**: 核心逻辑、边界与异常分支覆盖
  - [ ] **L2 集成测试**: [跨模块接口 / 存储交互 / 全局构建；纯独立单元可豁免]
  - [ ] **L3 端到端测试**: [主干用户链路或 CLI 全流程；局部改动可豁免]
- **豁免级别与依据**: [例如：豁免 L3，理由：纯内部模块重构，无外部可感知交互变更]
- **精确验证命令清单**:
  ```bash
  # L0 静态检查: [如 type-check / lint 命令]
  # L1 单元测试: [如 pytest / vitest 单测命令]
  # L2 集成构建: [如集成测试与全局构建命令（若适用）]
  # L3 端到端:   [如 e2e 命令（若适用）]
  ```

---

## 3. 分阶段垂直切片与子任务清单 (Phased Tasks & DAG)

> 复选框由主调度验真后更新，执行子智能体严禁代改。优先按**垂直曳光弹切片**拆解并显式标注 DAG 依赖；无冲突同形微改可合批派发。

### Execute：隔离分支与 TDD 垂直切片实现（原 P3）
- [ ] **Task E-0**: 切出隔离分支、核验基线测试与工具链就绪 | **依赖**: 无
  - **涉及文件**: `[环境/配置文件]` | **验收命令**: `[基线验证命令]`
- [ ] **Task E-1**: [垂直切片 A：端到端最小可运行闭环] | **依赖**: Task E-0
  - **涉及文件**: `src/...`, `tests/...`
  - **TDD 节拍**: 🔴 失败单测 ➔ 🟢 最简实现 ➔ 🔵 重构 ➔ ✅ L0/L1 Exit 0 ➔ 💾 原子提交
  - **验收命令**: `[针对 E-1 的验证命令]`
- [ ] **Task E-2**: [垂直切片 B 或无冲突同形合批任务] | **依赖**: Task E-0（可与 E-1 并行，若文件零交集）
  - **涉及文件**: `src/...`, `tests/...`
  - **验收命令**: `[针对 E-2 的验证命令]`

### Verify：集成验证、前端条件验收与独立终审（原 P3.5 / P4）
- [ ] **Task V-1**: 运行 L2 跨模块集成测试、全局构建与 L3 E2E（若裁定适用）
  - **验收命令**: `[L2/L3 与全局构建命令]`
- [ ] **Task V-2（条件 · 仅前端产物交付）**: 取得 `frontend-qa-gate`《前端验收报告》且结论为 `PASS`
  - **机械校验**: ``python3 <frontend-qa-gate 技能目录>/scripts/check-qa-report.py <报告文件> --require-verdict=PASS --min-assertions=15``（`FAIL`/`BLOCKED` 严禁进入 V-3）
- [ ] **Task V-3**: 按通道执行独立对抗终审（Heavy 全量双轮 `dual-round-review`；Fast-Track / Maintenance-Patch 定向单轮红队）与 Delta Re-Loop 闭环（上限 5 次），取得最新提交的 **Zero Blockers** 裁决后合并分支
  - **审查输入**: 可由 `scripts/pack-handoff.py review-pkg <base_ref> HEAD --out .goal-loop/review-pkg.md` 生成交接包

### Close：文档联动同步与归档（原 P5）
- [ ] **Task C-1**: 对照 `documentation-sync-matrix.md` 同步 Diátaxis 架构/契约/指南/ADR/CHANGELOG，并运行 `doc-governance` 门禁（若已配置）
- [ ] **Task C-2**: 将本计划状态标记为 `[已完成]` 并沉淀最终执行摘要

---

## 4. 关键事实与自主裁决日志 (Context & Rulings Log)

> 按**事件驱动落盘**原则，仅在阶段切换、关键根因/契约确立、大块探索收敛或上下文压缩前沉淀高信息密度结论；临时长日志卸载至 `.goal-loop/scratchpad.md`。

- **[YYYY-MM-DD] 事实/根因**: [记录核实后的接口契约、环境边界或故障根因]
- **[YYYY-MM-DD] Ruling**: [执行期非致命歧义的最小可逆自主裁决及依据，避免无谓卡死；触及四类硬停边界必须请示人类]

---

## 5. 修订历史 (Revision History)

- **[YYYY-MM-DD]**: 计划创建。
