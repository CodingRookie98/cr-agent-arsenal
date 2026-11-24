# 五主阶段推进与三轨分流规程 (Stage Progression & Track Triage Protocol)

## 概述 (Overview)

本规程定义了 `goal-loop` 从 **`Align`** 到 **`Close`** 的五主阶段全生命周期推进法则（括号内保留 V2.x 历史编号对照以兼容存量计划）。为兼顾复杂系统的质量确定性与局部/存量任务的敏捷性，确立**三轨执行通道 (Tiered Execution Tracks)**：

```text
                             ┌─────────────────────────┐
                             │ 🎯 目标输入 (Goal Input) │
                             └────────────┬────────────┘
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
 【Heavy Track (重型主航道)】    【Fast-Track (敏捷轻量)】    【Maintenance-Patch (存量维护)】
  跨模块重构 / 核心契约 / 新特性   单文件微调 / 局部已知修复      既有契约不变的故障定位与修复
  Align (P-1/P0/P0.5)            豁免 Align                     豁免 Align 与重型子任务拆解
   ➔ Plan (P1/P2)                 ➔ Plan (轻量计划)              ➔ Plan (极简复现/根因计划)
   ➔ Execute (P3)                 ➔ Execute (Surgical TDD)       ➔ Execute (复现+最小修复+回归)
   ➔ Verify (P3.5/P4 全量双轮)    ➔ Verify (定向单轮红队)         ➔ Verify (L2回归+定向单轮红队)
   ➔ Close (P5)                   ➔ Close (文档归档)              ➔ Close (CHANGELOG/案例归档)
```

---

## 1. 执行通道分级判定矩阵 (Track Triage Matrix)

启动任务前，主调度智能体必须首先判定所属通道：

| 判定维度 | Heavy Track (重型主航道) | Fast-Track (敏捷轻量通道) | Maintenance-Patch (存量维护通道) |
|:---|:---|:---|:---|
| **任务生命周期阶段** | 新项目 0→1、架构演进或契约扩展期 | 任意阶段的任务级局部改动 | **存量维护**：契约不变，仅纠正既有接口语义内的缺陷 |
| **改动文件跨度** | 涉及 2 个以上文件/模块，或改动公共契约/数据模型，或预期 >10 分钟 | 单文件、局部改动、预期 <10 分钟且不改公共契约 | 单文件或局部链路，不新增对外能力 |
| **契约稳定性** | 涉及底层数据模型、公共 API 签名、全局状态机 | 不改变公共外部契约与数据模型 | **契约不变**：不新增/修改接口签名与数据模型 |
| **未知风险度** | 涉及陌生第三方依赖、并发竞态或技术选型未决 | 模式成熟已知，无未知第三方依赖 | 故障现象明确，但根因待定位收敛 |
| **阶段裁剪策略** | **全量五主阶段 (`Align` → `Close`)** | **豁免 `Align`**，直入 `Plan` 轻量计划、`Execute`、`Verify`（定向单轮）、`Close` | **豁免 `Align` 与重型任务拆解**；保留 `Plan` 极简计划、`Execute` 定位+回归、`Verify`（L2+定向单轮）、`Close` |

> **通道判据优先级**：「任务生命周期阶段（维护 vs 开发）」先于「改动文件跨度」判定。维护期任务优先走 Maintenance-Patch，仅当必须扩展公共契约时升级为 Heavy Track。
> **误判降级**：若 Fast-Track 执行中暴露跨模块契约影响或未知风险，立即重判为 Heavy Track 并补做被豁免阶段，切换记录写入计划检查点，严禁静默升级。

---

## 2. 通道 C：存量维护通道 (Maintenance-Patch Track)

* **触发条件（须同时满足）**：① **契约不变**（不改接口签名/数据模型/状态机节点）；② **目标是"改对"而非"改设计"**；③ **改动局部**（可被单文件或局部链路测试覆盖）。
* **强制保留项（严禁裁剪）**：
  - **3-Tries 熔断**：同一故障 3 次未收敛即中断升级；根因未明时严禁盲改试错；
  - **修复前先复现**：无失败测试或可复现命令不得开始修改；
  - **修复必带回归测试**：新增测试须在修复前确认失败（Red），与修复同一原子提交（Green）；
  - **禁止顺手重构**：Diff 严格限定于故障根因路径；
  - **定向红队审查**：仅锁 `BASE..HEAD` Diff 边界，不越界审计历史代码；
  - **契约扩展熔断**：一旦发现必须改动公共契约，立即中止并升级为 Heavy Track。
* **执行步骤**：复现与定位（根因即刻落盘检查点）→ 回归测试前置（Red）→ 最小化修复（Green）→ 裁定级别验证 Exit Code 0 并原子提交 → 定向单轮红队审查 → 沉淀根因至 CHANGELOG 或排障文档。
* **准出底线**：根因书面落盘、回归测试全绿、Diff 范围受控、定向红队无阻断项。

---

## 3. 五主阶段执行细则 (5-Stage Protocol)

### 阶段 1：`Align` — 意图对齐、压力澄清与开源选型（原 P-1 / P0 / P0.5）

* **适用通道**：仅限 **Heavy Track**（Fast-Track / Maintenance-Patch 豁免）。
* **子步骤 1.1 意图对齐（原 P-1 · 联动 `brainstorming`）**：
  1. 界定路径类型（探索 Spike / 局部 Bounded / 架构 Architectural）并探明核心痛点；
  2. 提供 2~3 个可操作备选方案（对比权衡、成本与回滚）；
  3. **<HARD-GATE>**：未获用户明确认可（User Nod），严禁写代码、严禁进入 `Plan`！
* **子步骤 1.2 方案压力澄清（原 P0 · 联动 `grilling` / `clarification-protocol`）**：
  1. **术语先行**：先对齐核心术语与歧义定义，再进入需求与边界澄清；
  2. **收敛出口**：以红队视角拷问隐式假设、并发、安全与回滚；按「依赖强度 × 实现影响」排序并收敛，需求确认文档落盘为 `docs/proposals/RFC-{NNNN}-{slug}.md`（状态 `In Review`，采用 `clarification-protocol` 4 列决策台账），严禁写入 `docs/requirements/` 等瀑布旧目录；存量工程现状评估摘要直接并入 RFC 或计划背景段。
* **子步骤 1.3 技术调研与开源选型（原 P0.5 · 联动 `research` / `find-docs`）**：
  - 触发：引入新依赖、复杂通用能力（认证/队列/调度/协议解析/并发）或面临开源复用 vs 自研抉择；纯既有模块复用可豁免；
  - **三级调研工具链**：① 本地代码库检索可复用封装 → ② GitHub 生态检索（`gh search repos/code/issues`）→ ③ 官方规范检索（`find-docs` / `context7-cli` / `web_search`）；
  - **隔离与落盘**：委派只读子智能体在独立上下文中执行，调研结论统一按 Diátaxis 落盘至 `docs/explanation/analysis/YYYY-MM-DD-<topic>.md`；
  - **<HARD-GATE>**：优先复用成熟方案；决定自研必须在调研文档中书面辩护；选型未决严禁进入 `Plan`！

### 阶段 2：`Plan` — 实施方案、测试定级与垂直切片拆解（原 P1 / P2）

* **适用通道**：三轨均执行（Heavy 完整计划 / Fast-Track 轻量计划 / Maintenance-Patch 极简计划）。
* **外部联动**：`writing-plans`（可选）、[goal-plan-template.md](../templates/goal-plan-template.md)、[testing-decision-matrix.md](testing-decision-matrix.md)、[atomic-task-template.md](../templates/atomic-task-template.md)。
* **核心步骤**：
  1. 在 `docs/project/plans/YYYY-MM-DD-<feature>.md` 创建计划并初始化头部 `Active Checkpoint` 与需求方验收口径；
  2. 依据 [testing-decision-matrix.md](testing-decision-matrix.md) 输出《测试策略裁定书》（风险定级、L0–L3 必跑命令与豁免依据）；
  3. **垂直曳光弹切片（Vertical Tracer-Bullet Slices）与任务 DAG 拆解**：按 2~5 分钟/步切分自包含子任务，优先切为端到端可编译可验证的垂直切片并标注依赖边（DAG），避免按技术层水平切碎导致后期集成爆炸；
  4. 固化 7 维任务规约（技术栈中立，严禁让执行端推测字段名；Maintenance-Patch 豁免重型拆解）。
* **准出底线**：验收口径明确、测试裁定书与 `- [ ]` 任务清单齐备、每个待派发子任务 100% 自包含。

### 阶段 3：`Execute` — 隔离分支 TDD 实现与原子提交（原 P3）

* **后端确认与执行纪律**：开工前按 [host-adapters.md](host-adapters.md) 向用户确认执行后端（宿主原生子智能体 / 外部无头 CLI / 当前会话内联），遵循文件指针交接与 §7 四项现代自治纪律。
* **分支隔离**：基于开发主干创建独立功能/修复分支，**严禁直接在 `main` 或 `master` 写代码**。
* **Surgical TDD 循环**：
  1. 🔴 **Red**：编写反映期望行为的失败单测（L1）并确认必然失败；
  2. 🟢 **Green**：编写最简代码使测试通过（严禁投机性抽象）；
  3. 🔵 **Refactor**：在测试保护下消除坏味道；
  4. ✅ **Verify**：运行裁定书要求的 L0 静态检查与 L1 单测至 Exit Code 0（裁定豁免 L1 的纯配置改动按其裁定级别验证）；
  5. 💾 **Atomic Commit**：使用 Conventional Commits 原子提交，主调度验真后更新计划复选框（`- [ ]` ➔ `- [x]`）与检查点。
* **准出底线**：每笔提交覆盖裁定测试级别，所有执行子任务均标记 `- [x]`。

### 阶段 4：`Verify` — 集成验证、前端条件验收与独立对抗终审（原 P3.5 / P4）

* **子步骤 4.1 集成与构建验证（原 P3.5）**：对裁定书含 L2 的任务，运行跨模块集成测试与项目全局编译构建至 Exit Code 0（纯独立单元可按裁定书豁免）。
* **子步骤 4.2 前端产物验收（条件步骤 · 仅前端产物交付，位于 R1 之前）**：
  - **设计任务链路**：`taste-driven-designer` D1-D3 → `frontend-qa-gate`（Tier 1 自动化门禁结论须为 `PASS`，Tier 2 人工/真机签收项按 `pending_human` 交付人类签收）→ `dual-round-review` R1/R2；
  - **非设计任务链路**：`frontend-qa-gate` → `dual-round-review`；
  - **双轨与无效证据纪律**：V2.0 采用「Tier 1 自动化阻断门禁 + Tier 2 人工/真机签收清单」双轨制——Tier 1 真实磁盘证据校验 `PASS` 即可放行进入 `dual-round-review`（`FAIL` 或 `BLOCKED` 不得声称通过，须按回流路由修复后重验）；Tier 2 人工/真机签收项（如读屏实测、软键盘安全区、低版浏览器矩阵）按 `pending_human` 交付人类签收，不构成无头死锁。产物断言、代码终审与品味裁决三者不得互相替代；
  - **机械校验命令**：`python3 <frontend-qa-gate 技能目录>/scripts/check-qa-report.py <qa-evidence.json> --require-verdict=PASS`（退出码 0 方视为 Tier 1 `PASS` 可证）。
* **子步骤 4.3 独立对抗终审与 Delta Re-Loop（原 P4 · 联动 `dual-round-review`）**：
  1. 运行 L3 端到端测试（若裁定书适用）；
  2. **通道裁量**：Heavy Track 执行全量双轮对抗审查；Fast-Track / Maintenance-Patch 执行定向单轮红队审查（Diff 边界锁），触及公共契约、核心链路或鉴权/并发/数据一致性时升级为全量双轮；
  3. **独立双轮执行**：R1 独立红队锁定 `BASE..HEAD` Diff 边界，穿透核查**逻辑漏洞、竞态/资源泄漏与领域运行时安全风险**；R2 元架构师独立审判，剔除历史未改代码越界挑刺并输出最终裁决明细表；
  4. **Delta Re-Loop 硬门禁**：若 `Blockers > 0`，根因修复并原子提交后，**必须以修复提交为新基线重派 Delta Re-Loop 复核**，严禁自宣通过；同一目标迭代上限 **5 次**，触顶按 [failure-recovery-protocol.md](failure-recovery-protocol.md) 升级人类裁决；
  5. 阻断项清零后安全合并功能分支并清理临时分支。
* **准出底线 (<HARD-GATE>)**：持有独立子智能体针对最新提交的 **Zero Blockers** 终审凭据（前端交付另需 `frontend-qa-gate` Tier 1 真实磁盘证据校验 `PASS` 且退出码 0，Tier 2 人工/真机签收项按 `pending_human` 交人类签收）方可合并入库。

### 阶段 5：`Close` — 文档联动同步与计划归档（原 P5）

* **外部联动**：对照 [documentation-sync-matrix.md](documentation-sync-matrix.md) 逐项同步受影响文档；若项目已配置 `doc-governance`，在本阶段末尾派发断链、版本一致与机器地图门禁审计。
* **核心步骤**：同步架构/契约/指南/ADR/CHANGELOG → 将实施计划状态更新为 `[已完成]` 并沉淀最终执行总结。
* **准出底线**：代码变更与文档脱节清零，所有交付门禁全绿，目标闭环结项。
