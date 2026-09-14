# goal-loop 技能 V2.0 重构实施方案 (A → B → C)

> **文档控制信息**
> - **文档标识**: PLAN-GOAL-LOOP-V2-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-14

> **目标元数据**
> - **所属项目**: cr-public-skills
> - **执行通道**: Heavy Track（跨模块重构，涉及 4 个技能文档族 + 脚本 + 设计书 + README）
> - **目标简述**: 将 goal-loop 从"单一宿主绑定 + 三处状态真相源 + 自相矛盾门禁"重构为"宿主无关方法论层 + 薄适配器 + 单一可读真相源"。
> - **创建日期**: 2026-09-14
> - **隔离分支**: `feature/goal-loop-v2`
> - **状态**: 已完成

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P5 / DONE（目标达成）
- **当前活跃子任务**: 无
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: 全绿 —— 断链 0；`bash -n` OK；残留断言 0；`pytest` 24 passed；知识库健康度 100/100（已并入独立红队复审 2B/5M/7m 的整改）
- **最新有效提交**: `5bb2ae1`
- **阻断原因**: 无

---

## 1. 锁定决策 (Locked Decisions)

以下四项经用户确认，作为不可回退的实现约束：

| # | 决策点 | 选定方案 |
|---|---|---|
| D1 | 状态真相源 | **计划文件为唯一可读 SoT**；机器状态适配宿主原生 goal 原语（如本 harness 的 `create_goal`/`get_goal`/`update_goal`），脚本仅作派生视图，不再拥有状态 |
| D2 | P3 执行后端 | **宿主无关**：通用 subagent / agy / 内联三档适配；**后端选择在运行时询问用户**，无 agy 也能跑完 P3 |
| D3 | 兼容策略 | **允许破坏性重构**，升 V2.0，同步 README 与设计书 |
| D4 | 分支策略 | 在 `feature/goal-loop-v2` 交付，严禁在 master 写代码 |

---

## 2. 根因分析 (Root Cause)

当前 goal-loop 将三类关注点压在同一层：

1. **可移植方法论**：阶段流转、测试矩阵、熔断协议 —— 真正的长期资产；
2. **宿主运行时绑定**：`agy`、Antigravity 专有工具名（`invoke_subagent`/`grep_search`/`find_by_name`/`read_url_content`）、硬编码模型名 —— 不可移植，随环境腐烂；
3. **状态持久化实现**：`.goal-loop/state.json` 与计划复选框、检查点锚点三方并行 —— SSOT 撕裂的物理根源。

A/B/C 依次对应"止血 → 拆分 → 适配"，顺序不可颠倒（C 建在矛盾规格上会把矛盾固化为测试断言）。

---

## 3. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: MEDIUM
- **强制执行测试级别**:
  - [x] **L0 静态门禁**: Markdown 断链扫描 + Bash 语法检查 + 术语一致性断言
  - [x] **L1 单元测试**: `goal-state-tracker.sh` 子命令行为测试（沿用 doc-governance 的 pytest 模式，新增 `skills/goal-loop/tests/`）
  - [ ] **L2 模块集成测试**: 豁免
  - [ ] **L3 端到端测试**: 豁免
- **豁免充分理由**: 本目标产物为技能规程文档与一个无外部 I/O 的辅助 CLI，无应用运行时与用户主干链路；正确性由断链扫描、脚本单测与模板可执行性验证覆盖。
- **精确验证命令清单**:
  ```bash
  # L0-a 文档断链（docs 与 goal-loop 技能目录分别扫描）
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/check-doc-links.py --root skills/goal-loop
  python3 skills/doc-governance/scripts/check-doc-links.py --root . --dir README.md

  # L0-b Bash 语法
  bash -n skills/goal-loop/scripts/goal-state-tracker.sh

  # L0-c 旧路径/宿主专有工具名残留断言（应输出 0 行）
  # host-adapters.md 的"宿主能力映射"表按设计保留宿主工具名，故排除该文件
  grep -rnE --exclude=host-adapters.md 'docs/(planning|superpowers)/|docs/dev/(research|evaluation|process)|grep_search|find_by_name|read_url_content|invoke_subagent|regress-check|task-prompt-template|IMPLEMENTATION_PLAN' skills/goal-loop docs/explanation/architecture/goal-loop-design.md

  # L1 状态机脚本单测
  python3 -m pytest skills/goal-loop/tests -q
  ```

---

## 4. 分阶段实施与子任务清单 (Phased Implementation)

### 阶段 A：可执行性止血（无结构改动，可独立回滚）
- [x] **A-1 路径与命令统一**：把 `bash skills/goal-loop/...` 改为"以技能实际所在目录为准"的写法；将计划/调研/评估路径统一为 `docs/project/{plans,research,evaluation}/`
  - **涉及文件**: `SKILL.md`, `references/*.md`, `templates/*.md`, `scripts/goal-state-tracker.sh`
- [x] **A-2 工具名能力化**：`grep_search`/`find_by_name`/`read_url_content`/`invoke_subagent` 改为宿主能力描述，并附通用对应物
  - **涉及文件**: `SKILL.md`, `references/stage-progression-protocol.md`
- [x] **A-3 修正设计书坏引用与过期状态**：`regress-check`、`task-prompt-template.md`、roadmap "未开始"、L1 耗时不一致
  - **涉及文件**: `docs/explanation/architecture/goal-loop-design.md`
- [x] **A-4 提交并建立 L0 基线**

### 阶段 B：结构重构（消除矛盾，SKILL.md 降为路由层）
- [x] **B-1 SKILL.md 压缩为路由层**：只保留触发条件 + invariants 清单 + 指针，删除与 references 重复的状态机图与 SOP 目录
- [x] **B-2 消除矛盾**：统一阶段编号（废弃计划模板里的第二套编号）、裁定 Fast-Track 审查门禁、3-Tries 计数落盘为字段、外层循环与 Delta Re-Loop 加迭代上限、区分 Heavy/Fast 判定阈值
- [x] **B-3 补齐 atomic-task 输出契约**：worker → orchestrator 的必填回传字段、受阻回传格式、`git status --porcelain` 证据要求、明确"checkbox 由编排者更新"
- [x] **B-4 提交 B**

### 阶段 C：平台化（宿主无关 + 单一真相源 + 可验证）
- [x] **C-1 新增 `references/host-adapters.md`**：三档后端（通用 subagent / agy / 内联）的能力矩阵与降级规则；P3 开工前**询问用户选择后端**
- [x] **C-2 状态层改造**：计划文件为唯一可读 SoT；tracker 重写为派生视图（读写计划复选框与检查点，`state.json` 仅清理遗留）
- [x] **C-3 为 tracker 补单测**（24 passed），断链扫描纳入技能自检
- [x] **C-4 提交 C**

### 阶段 D：文档同步与终审
- [x] **D-1** 同步 `README.md` 与设计书至 V2.0，记录 A→B→C 的实际落地
- [x] **D-2** 跑通第 3 节全部验证命令（Exit Code 0）
- [x] **D-3** 终审并将计划标记为 `[已完成]`

---

## 5. 严禁事项 (Strict Exclusions)
1. 严禁改动 `dual-round-review` / `agy-delegation-workflow` / `doc-governance` 的技能内容（仅可引用其脚本作为门禁）；
2. 严禁执行任何破坏性 Git 命令（`reset`/`rebase`/`revert`/`restore`/`clean -fd`/强制推送）；
3. 严禁在 master 分支提交；
4. 严禁删除既有 references/templates 文件而不做内容迁移。

---

## 6. 修订历史 (Revision History)
- **2026-09-14**: 计划创建，锁定 D1–D4。
