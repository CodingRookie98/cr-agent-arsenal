---
name: goal-loop
description: Industrial-grade goal realization loop with context engineering, tiered testing decision, and multi-skill synergy. Orchestrates end-to-end delivery from requirements brainstorming, grilling, planning, and TDD execution, to dual-round review and document synchronization.
---

# `goal-loop` 目标实现循环技能规程 (Goal Realization Loop)

## 概述 (Overview)

`goal-loop` 是专为大语言模型（LLM）长程、跨模块研发任务设计的**自愈闭环状态机工作流**。
它融合了 **Ralph Loop 磁盘记忆持久化思维**、**Manus AI 上下文工程** 与 **faceFusionCpp 工业级 TDD 规程**，通过“主调度智能体长上下文统筹 + 执行子智能体短上下文物理隔离”的现代架构，深度串联全生命周期技能：
* **阶段 -1 (意图对齐)** ➔ `brainstorming`
* **阶段 0 (方案拷问)** ➔ `grilling` (`/grill-me`)
* **阶段 1 (架构规划与测试定级)** ➔ `writing-plans`
* **阶段 3 (执行委派)** ➔ `agy-delegation-workflow`
* **阶段 4 (终审门禁)** ➔ `dual-round-review`

---

## 适用场景 (When to Use)

### 必须使用
* **长程复合研发任务**：跨越多个文件或模块、耗时预期超过 10 分钟的新特性开发、系统重构或重大 Bug 修复；
* **需要高保真交付与严格测试保护**：杜绝浅层修补（Palliative Patching）或未跑测试就草率交付的任务；
* **易受上下文腐化（Context Rot）困扰的复杂任务**：步骤繁琐、容易遗忘初始目标或需要跨会话断点恢复的场景。

### 豁免场景
* 纯文案微调、单行常量修改、直接的只读问答检索。

---

## 总体架构与状态机拓扑 (State Machine Architecture)

```mermaid
graph TD
    Start(["🎯 目标输入 (Goal Input)"]) --> P_Minus1{"阶段 -1: 是否涉及方案创新或意图不明确?"}
    
    P_Minus1 -->|"是 - 需澄清意图"| Brainstorm["阶段 -1: 头脑风暴与意图对齐<br/>激活 brainstorming 技能探明真实需求"]
    P_Minus1 -->|"否 - 目标已完全明确"| P0_Check
    Brainstorm --> P0_Check{"阶段 0: 是否需要方案压力测试或代码评估?"}
    
    P0_Check -->|"是 - 需压力测试或评估"| Grill["阶段 0: 方案拷问与现状评估<br/>激活 grilling 压力拷问 + 产出 evaluation 报告"]
    P0_Check -->|"否 - 方案已知且边界受控"| P1
    Grill --> P1["阶段 1: 计划制定与测试策略裁定<br/>激活 writing-plans 编写 IMPLEMENTATION_PLAN.md<br/>输出 测试级别判定矩阵"]
    
    P1 --> P2["阶段 2: 原子子任务拆解<br/>落地通用 7 维任务提示词或独立 task_*.md"]
    P2 --> Branch["阶段 3 准备: 隔离分支与环境检测"]
    
    Branch --> LoopHeader["阶段 3: TDD 原子执行循环 (Task Iteration)"]
    
    subgraph TDDCycle["阶段 3: TDD 原子自愈闭环 (结合 agy 宿主自适应委派)"]
        T1["红灯: 编写失败测试 (L1 单测)"] --> T2["绿灯: 编写最简实现使测试通过"]
        T2 --> T3["重构: 优化代码结构消除异味"]
        T3 --> T4["验证: 本地执行单测 (必须 Exit Code 0)"]
        T4 --> PassCheck{"单元测试全绿?"}
        PassCheck -->|"否 - 重试不超过3次"| T2
        PassCheck -->|"连续3次失败"| Escalate["触发 3-Tries 熔断: 记录原因并上报人类"]
        PassCheck -->|"是"| Commit["原子提交当前子任务 Git Commit"]
        Commit --> Persist["持久化更新任务状态与进度文件"]
    end
    
    LoopHeader --> TDDCycle
    TDDCycle --> AllDone{"所有子任务均已完成?"}
    AllDone -->|"否 - 加载下一未完成任务"| LoopHeader
    
    AllDone -->|"是"| NeedInteg{"计划判定: 是否需要 L2 集成测试?"}
    NeedInteg -->|"是 - 涉及跨模块联动"| P35["阶段 3.5: 集成验证与跨模块回归测试"]
    NeedInteg -->|"否 - 单一内联模块豁免"| NeedE2E
    
    P35 --> IntegCheck{"集成测试与构建全绿?"}
    IntegCheck -->|"否"| FixInteg["定向修复回归缺陷"] --> P35
    IntegCheck -->|"是"| NeedE2E{"计划判定: 是否需要 L3 E2E 测试?"}
    
    NeedE2E -->|"是 - 涉及端到端主链路"| E2ERun["阶段 4 前置: 运行 E2E 系统测试"]
    NeedE2E -->|"否 - 无外部界面/链路豁免"| DualRevGate
    E2ERun --> DualRevGate["阶段 4: 双轮对抗终审硬门禁<br/>激活 dual-round-review (红队第一性原理 + 架构师元审判)"]
    
    DualRevGate --> RevPass{"双轮审查阻断项清零?"}
    RevPass -->|"存在阻断项"| FixBlocker["根据终审意见定向修复"] --> LoopHeader
    RevPass -->|"Zero Blockers 通过"| Merged["合并功能分支并清理临时分支"]
    
    Merged --> P5["阶段 5: 文档全向归档与联动升级<br/>同步架构/API/配置/ADR"]
    P5 --> Finish(["🏁 目标圆满达成 (Goal Achieved) ✅"])
```

---

## 核心阶段 SOP 与生态技能协同契约

详见 [stage-progression-protocol.md](references/stage-progression-protocol.md)。

### 1. 阶段 -1：头脑风暴与意图对齐 ➔ `brainstorming`
* **适用条件**：目标需求不明确、涉及交互创意、或有多种架构选型可能。
* **协同契约**：调用 `brainstorming` 梳理意图，向用户呈现 2~3 个备选方案。
* **硬门禁 (<HARD-GATE>)**：**未获得用户明确点头认可（User Nod）前，严禁动手写代码或编写实施方案！**

### 2. 阶段 0：方案压力测试与技术债评估 ➔ `grilling`
* **适用条件**：重大架构重构、安全核心链路、并发竞态或面对复杂遗留系统。
* **协同契约**：调用 `grilling` 针对设计假设进行无情拷问，清空设计决策树未决分支；对既有代码库按需产出质量评估报告（参考 [evaluation-report-template.md](templates/evaluation-report-template.md)）。

### 3. 阶段 1：计划制定与测试策略裁定 ➔ `writing-plans`
* **协同契约**：激活 `writing-plans` 技能，在磁盘编写 `docs/.../IMPLEMENTATION_PLAN.md`（参考 [goal-plan-template.md](templates/goal-plan-template.md)）；
* **自适应测试定级**：依据 [testing-decision-matrix.md](references/testing-decision-matrix.md) 输出《测试策略裁定书》，明确当前任务必须执行的测试级别（L0~L3）与命令。

### 4. 阶段 2：原子任务拆解与规约生成
* **拆解原则**：切分为 2~5 分钟的微型子任务（Bite-Sized），每个子任务具备独立测试断言；
* **通用标准**：遵循 [atomic-task-template.md](templates/atomic-task-template.md) 规定的 7 维黄金标准，严禁让执行端推测数据契约与接口。

### 5. 阶段 3：TDD 循环实现 ➔ `agy-delegation-workflow`
* **宿主自适应**：
  - **Antigravity 原生环境**：前台直接调用原生 `invoke_subagent` 派发子任务，**严禁在终端套娃调用 `agy` 命令行**；
  - **非 agy 终端环境**：使用 `dispatch-agy.sh` 清除代理并注入 `Gemini 3.8 Flash (High)` 无头后台进程。
* **TDD 铁律**：🔴 编写失败单测（L1）➔ 🟢 最简代码使测试通过 ➔ 🔵 保持测试全绿重构 ➔ ✅ 单元测试 Exit Code 0 ➔ 💾 原子提交 Git Commit。

### 6. 阶段 3.5：集成验证与回归测试
* **触发条件**：测试策略裁定书中包含 **L2 集成测试** 时必须执行；
* **验证标准**：全量集成测试与全局编译构建（如 `pnpm build` / `cargo build`）全绿通过。

### 7. 阶段 4：E2E 验收与双轮对抗终审 ➔ `dual-round-review`
* **E2E 执行**：若涉及用户主干链路，运行 L3 端到端测试；
* **终审硬门禁 (<HARD-GATE>)**：必须调用 `dual-round-review` 技能派发第一轮红队审计（R1）与第二轮资深架构师（R2），**取得 Zero Blockers（阻断项清零）终审裁决报告方可合并入库！**

### 8. 阶段 5：文档全向归档与联动同步
* **同步规范**：对照 [documentation-sync-matrix.md](references/documentation-sync-matrix.md) 逐项核验并更新架构、API、用户手册、配置与 ADR 记录，将计划更新为 `[已完成]`。

---

## 上下文工程核心守则 (Context Engineering)

详见 [context-engineering.md](references/context-engineering.md)。

1. **持久化优先**：内存易失有限，磁盘无限持久。任何关键发现与进度必须物理写入磁盘。
2. **核心事实即刻沉淀**：探查捕获到重大架构契约、决策或致命报错时即刻落盘；临时碎片记录在临时 Scratchpad，防止主计划文档膨胀反噬上下文。
3. **防御性调用规范 (Read-Modify-Verify)**：文件写入或局部编辑后，必须通过 `git diff`、精准查看关键变更行或执行编译/测试状态码检查确认变更生效，严禁盲目假设写入成功。进入新阶段主动读取计划，中断恢复读取状态机。

---

## 异常恢复与 3-Tries 熔断协议

详见 [failure-recovery-protocol.md](references/failure-recovery-protocol.md)。

* **3-Tries Rule**：针对任何单一错误连续尝试上限为 **3 次**。
* **熔断动作**：第 3 次失败时立即停止代码修改，生成结构化仲裁报告（`STOP -> RECORD -> RESEARCH -> ESCALATE`），向人类工程师请求决策。

---

## 辅助工具与状态机脚本

工作区可通过轻量脚本跟踪断点状态（维护 `.goal-loop/state.json`）：
```bash
# 初始化目标状态机
bash skills/goal-loop/scripts/goal-state-tracker.sh init "目标名称" "计划文件路径"

# 查看当前看板
bash skills/goal-loop/scripts/goal-state-tracker.sh status

# 切换阶段
bash skills/goal-loop/scripts/goal-state-tracker.sh set-phase P3

# 标记子任务完成
bash skills/goal-loop/scripts/goal-state-tracker.sh complete-task "task-2.1"
```

---

## 支持资源与参考导航

### 规程与矩阵参考
* [testing-decision-matrix.md](references/testing-decision-matrix.md) - 改动特征与测试级别判定规则 (L0~L3 详细对照表)
* [context-engineering.md](references/context-engineering.md) - 2-Action Rule、读写决策矩阵与持久化工程规范
* [stage-progression-protocol.md](references/stage-progression-protocol.md) - P-1 到 P5 各阶段详细执行细则与门禁
* [failure-recovery-protocol.md](references/failure-recovery-protocol.md) - TDD/集成失败矩阵与 3-Tries 熔断报告模板
* [documentation-sync-matrix.md](references/documentation-sync-matrix.md) - 全向文档联动复核清单 (架构/API/配置/ADR)

### 模板套件与辅助脚本
* [goal-plan-template.md](templates/goal-plan-template.md) - 通用实施方案计划模板 (内嵌测试策略裁定书)
* [atomic-task-template.md](templates/atomic-task-template.md) - 通用 7 维独立子任务规约模板
* [evaluation-report-template.md](templates/evaluation-report-template.md) - 阶段零现状评估报告模板
* [goal-state-tracker.sh](scripts/goal-state-tracker.sh) - 状态追踪与断点恢复辅助 CLI
