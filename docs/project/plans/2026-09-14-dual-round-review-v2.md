# dual-round-review 技能 V2.0 重构实施方案 (A → B → C)

> **文档控制信息**
> - **文档标识**: PLAN-DUAL-ROUND-REVIEW-V2-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-14

> **目标元数据**
> - **所属项目**: cr-public-skills
> - **执行通道**: Heavy Track（跨 8 个技能文件 + 脚本 + 文档）
> - **目标简述**: 将 dual-round-review 从"宿主绑定 + 循环状态不落盘 + 与 goal-loop 口径冲突"重构为"宿主无关派发 + 审查记录锚点 + 双/单轮双模"。
> - **创建日期**: 2026-09-14
> - **隔离分支**: `feature/dual-round-review-v2`（基于 `master` 97dd04c）
> - **状态**: 已完成
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`（gitignored）

> **唯一可读真相源声明**：本文件是本目标的唯一人类可读真相源；审查循环运行期的短周期状态由 `.review-context/review-<sha>.md` 承载（见 D1）。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P5 / DONE（目标达成）
- **当前活跃子任务**: 无
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: 全绿 —— 残留宿主绑定 0；断链 0（docs 6 / 技能 9）；`bash -n` OK；`pytest` 12 passed；知识库健康度 100/100；独立红队复审 Blockers=0，Delta 复验 0/0/0
- **最新有效提交**: `a416a67`
- **阻断原因**: 无

---

## 1. 锁定决策 (Locked Decisions)

| # | 决策点 | 选定方案 |
|---|---|---|
| D1 | 审查状态锚点 | 启用 `.review-context/review-<baseline-sha>.md`：基线 SHA、模式（full/light/delta）、轮次、Previous Blockers、迭代计数、终审裁决；由 `prepare-review-context.sh` scaffold |
| D2 | 单轮模式 | 技能内新增显式 **Light Mode**（R1 模板 + 轻量裁决，输出契约与双轮一致）；`goal-loop` Fast-Track 调用它 |
| D3 | 环境专有维度 | React/SSR/Hooks/Storage 维度**按 diff 文件特征条件激活**，非前端仓库不被 N/A 字段逼供 |
| D4 | 分支基线 | 基于 `master` 新开 `feature/dual-round-review-v2`，与 goal-loop V2 解耦 |

---

## 2. 根因分析 (Root Cause)

1. **宿主绑定 + 异步假设**：`invoke_subagent`/`Agent`/`agy -p`/`view_file` 写死；"必须结束回合等待异步唤醒"在同步前台派发宿主上会丢结果。
2. **循环状态只在上下文里**：Previous Blockers 与"3 次循环"上限无落盘载体，断点不可恢复、上限不可验证。
3. **跨技能口径漂移**：goal-loop V2 裁定 Fast-Track 单轮，dual-round-review 定义上只有双轮，无人胜出。
4. **环境专有内容硬编码为强制维度**：React/SSR 检查项对非前端仓库是噪音与虚构压力。
5. **机制重复**：Diff 边界锁在 7 处复述，具备漂移条件。

---

## 3. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: MEDIUM
- **强制执行测试级别**:
  - [x] **L0 静态门禁**: 断链扫描（技能目录 + docs + README）+ Bash 语法 + 旧宿主工具名/旧路径残留断言
  - [x] **L1 单元测试**: `prepare-review-context.sh` 行为测试（新建 `skills/dual-round-review/tests/`）
  - [ ] **L2 / L3**: 豁免（纯技能规程与无外部 I/O 的辅助脚本）
- **精确验证命令清单**:
  ```bash
  # L0-a 断链
  python3 skills/doc-governance/scripts/check-doc-links.py --root skills/dual-round-review
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  # 注: README 的技能目录链接属既有历史债，已在 feature/goal-loop-v2 分支修复；本分支不重复改动

  # L0-b 脚本语法
  bash -n skills/dual-round-review/scripts/prepare-review-context.sh

  # L0-c 旧宿主绑定/旧路径残留（应为 0 命中）
  grep -rnE 'invoke_subagent|view_file|agy -p|skills/dual-round-review/scripts' skills/dual-round-review

  # L1 脚本单测
  python3 -m pytest skills/dual-round-review/tests -q
  ```

---

## 4. 分阶段实施与子任务清单 (Phased Implementation)

### 阶段 A：P0 止血
- [x] **A-1 派发契约宿主无关化 + 同步/异步分流**：SKILL.md 派发方式改为"宿主原生子智能体能力"，新增同步（前台派发，直接取报告）与异步（后台派发，结束回合等唤醒）两种模式的判定与选择规则；删除无条件 Stop & Await；round-1/round-2 模板的 `view_file` 改为宿主代码库读取能力
- [x] **A-2 审查状态锚点**：新增审查记录文件规范与 `.review-context/review-<sha>.md` scaffold；SKILL.md 规定每轮写入字段（基线 SHA/模式/轮次/Previous Blockers/迭代计数/裁决），并支持从锚点恢复
- [x] **A-3 单轮 Light Mode**：SKILL.md 新增 Light Mode 章节（R1-only + 轻量裁决），与 goal-loop Fast-Track 对接；明确 Light Mode 的阻断项处理与升级为双轮的条件
- [x] **A-4 提交 A**

### 阶段 B：结构对齐
- [x] **B-1 维度条件化**：将 React/SSR/Hooks/Storage 维度改为按 diff 文件特征激活；R1/R2 输出模板的对应字段改为条件存在
- [x] **B-2 Diff 边界锁单一真相源**：在 `verdict-rubric.md` 定义一次，SKILL.md/templates/catalog/脚本改为引用
- [x] **B-3 消费方路径 + R2 上下文对称**：脚本调用改技能目录相对写法；R2 获得与 R1 对等的仓库读取授权，驳回必须附 `文件:行` 证据，新增"批量降级需证据"红旗
- [x] **B-4 去否定化**：收敛为 6 条正向铁律清单（invariants）；rationalizations 表保留"借口→对策"结构，逐条正向化留待后续迭代
- [x] **B-5 提交 B**

### 阶段 C：平台化与可验证
- [x] **C-1 输出契约机器可解析化**：R1/R2 报告与 Previous Blockers 增加稳定 ID 与统一 schema
- [x] **C-2 脚本增强**：`--help`/usage + 审查记录 scaffold 已实现；`--prompt` 作为可选增强留待后续
- [x] **C-3 脚本单测 + 门禁**：新增 `tests/`，并把断链/残留断言纳入技能自检
- [x] **C-4 文档同步与验收**：README/index 同步，跑通第 3 节全部命令
- [x] **C-5 提交 C**

---

## 5. 严禁事项 (Strict Exclusions)
1. 严禁改动 `goal-loop` / `doc-governance` / `agy-delegation-workflow` 的技能内容（仅可引用其脚本作为门禁）；
2. 严禁执行破坏性 Git 命令（`reset`/`rebase`/`revert`/`restore`/`clean -fd`/强制推送）；
3. 严禁在 master 分支提交；
4. 严禁删除既有 examples/references 文件而不做内容迁移。

---

## 6. 修订历史 (Revision History)
- **2026-09-14**: 计划创建，锁定 D1–D4。
