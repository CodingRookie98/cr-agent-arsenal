# `goal-loop` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-GOAL-LOOP-EVAL-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于本仓库 `skills/goal-loop/` 全量 17 文件源码精读、28 份真实历史实施计划（`docs/project/plans/*.md`）实证使用率统计，以及配套外部调研报告 [2026-11-23-goal-loop-peer-research.md](./2026-11-23-goal-loop-peer-research.md) 收敛的六大流派与实证规律。
> - **证据分级**: 【A】一手（本仓库源码/行号实测、28 份计划脚本全量统计、外部开源项目一手源码）｜【B】二手转引（学术论文与工程博客综合摘要）｜【C】架构师专业裁决与推演建议

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `goal-loop` 全量资产与 28 份真实计划活跃度实证审计、十二维横向对标、六大过度设计与结构病灶诊断、五项核心护城河甄别及 P0–P2 分阶段重构路线图 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`goal-loop` 是否过度设计？是否还有重构优化空间？**

**结论：核心骨架立意正确且具备真正的差异化护城河，但外围已出现明确的结构性过度设计与「提示词伪运行时」膨胀；存在显著的高 ROI 瘦身与现代化升级空间（预计可安全削减 45%–55% 体积与死代码，同时补齐 2026 年代的关键编排能力）。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **总维护体量** | `skills/goal-loop/` 共 **17 文件 / 2,128 行 / 125,073 字节**（另含设计书 30,429 字节） | 路由层 `SKILL.md`（103 行）控制良好，但外围细则、脚本、模板与文案锁死测试过度堆叠 |
| **功能活跃度极化** | 28 份真实计划中：`Active Checkpoint` **89%**、三轨分流 **100%**、终审 **79%**、测试定级 **61%**；而 `goal-state-tracker.py`、`HALF-OPEN/G1–G4`、`evaluation-report`、`research-spike` 四大组件均为 **0%** | 呈现典型的「核小壳重」：真正承载交付价值的是核心 4 项，外围大片复杂机制长期空转 |
| **架构层位错配** | 在纯 Markdown 提示词中设计 4 态熔断器、`min(25%, 剩余÷3)` token/wall-clock 预算公式、以及每 2 次只读强制写盘规则 | 典型「提示词伪运行时」（对应调研报告 AP-1），且与同目录 `host-adapters.md:67` 自相矛盾 |
| **内部一致性与合规** | 发现 4 类已落盘的腐化：个人绝对路径泄露、违背 `GOVERNANCE.md` Diátaxis 红线的旧目录清单、前端 Hooks/SSR 污染通用阶段、以及 168 行字符串存在性测试锁死冗余文案 | 已产生明显维护税，需先止血清理 |
| **前沿能力缺口** | 缺文件指针交接（防主上下文滚雪球）、缺「先裁决不卡死」、缺模型档位分层与同形批处理、缺 DAG 垂直切片指导 | 相比 2026 年末 `superpowers` 与 `mattpocock/skills` 存在代差，可通过低成本重构追平 |

---

## 1. 全量资产盘点与 28 份真实计划的实证审计

### 1.1 `skills/goal-loop/` 文件体量全景（2026-11-23 实测【A】）

| 分组 | 文件路径 | 行数 | 字节数 | 当前角色与初步诊断 |
| :--- | :--- | :---: | :---: | :--- |
| **路由入口** | [SKILL.md](../../../skills/goal-loop/SKILL.md) | 103 | 8,229 | 路由层精炼合规（远低于 `agentskills.io` 500 行线），但包含零用脚本示例与机械 2-Action 铁律 |
| **核心细则** | [stage-progression-protocol.md](../../../skills/goal-loop/references/stage-progression-protocol.md) | 237 | 19,123 | 体量最大；含三轨矩阵（真资产），但阶段过密且遗留双轨旧图、旧目录与 React/SSR 污染 |
| **核心细则** | [failure-recovery-protocol.md](../../../skills/goal-loop/references/failure-recovery-protocol.md) | 148 | 11,765 | 3-Tries 与非阻塞升级有价值，但 `HALF-OPEN` / `G1–G4` / 25% 预算属不可度量伪运行时 |
| **核心细则** | [host-adapters.md](../../../skills/goal-loop/references/host-adapters.md) | 135 | 11,409 | 隔离红线与超期收口极有价值；但含虚构原语 `create_goal`，缺模型分层与 Rulings 纪律 |
| **核心细则** | [context-engineering.md](../../../skills/goal-loop/references/context-engineering.md) | 101 | 7,672 | 检查点与写入分层合理，但机械「2-Action Rule」未落地且滞后于 Manus 二次演化 |
| **核心细则** | [testing-decision-matrix.md](../../../skills/goal-loop/references/testing-decision-matrix.md) | 86 | 7,334 | **全场最高价值细则**（L0–L3 矩阵 + 影响面分析 + Mock 防逃逸红线），应重点保留 |
| **核心细则** | [optional-skill-dependencies.md](../../../skills/goal-loop/references/optional-skill-dependencies.md) | 65 | 3,767 | 三分支无头安全降级清晰实用，体量克制 |
| **核心细则** | [documentation-sync-matrix.md](../../../skills/goal-loop/references/documentation-sync-matrix.md) | 52 | 4,944 | **重度腐化**：通篇引用 `GOVERNANCE.md` 明令禁止的瀑布旧目录，与 `doc-governance` 重叠 |
| **脚本代码** | [goal-state-tracker.py](../../../skills/goal-loop/scripts/goal-state-tracker.py) + `.sh` | 370 | 13,068 | **高债僵尸代码**：365 行正则读写 Markdown，28 份真实业务计划 **0 次调用** |
| **模板套件** | [goal-plan-template.md](../../../skills/goal-loop/templates/goal-plan-template.md) | 152 | 9,208 | 常用主模板，但需清理旧调研路径与 tracker 备注 |
| **模板套件** | [atomic-task-template.md](../../../skills/goal-loop/templates/atomic-task-template.md) | 89 | 3,926 | 子任务 7 维契约 + 输出规约，实用但可与文件指针交接结合精简 |
| **模板套件** | [research-spike-template.md](../../../skills/goal-loop/templates/research-spike-template.md) | 82 | 4,442 | **零使用僵尸模板**，且约定目录与 Diátaxis 冲突 |
| **模板套件** | [evaluation-report-template.md](../../../skills/goal-loop/templates/evaluation-report-template.md) | 43 | 2,002 | **零使用僵尸模板**，且约定目录与 Diátaxis 冲突 |
| **测试套件** | [test_goal_state_tracker.py](../../../skills/goal-loop/tests/test_goal_state_tracker.py) | 297 | 10,043 | 仅服务零使用脚本，构成纯粹的连带维护债 |
| **测试套件** | [test_failure_recovery_contract.py](../../../skills/goal-loop/tests/test_failure_recovery_contract.py) | 92 | 4,474 | **文案锁死测试**：逐字断言 Markdown 子串（`"25%"`、`"3 + 2 + 2 = **7 次**"`），阻碍精简 |
| **测试套件** | [test_optional_skill_contract.py](../../../skills/goal-loop/tests/test_optional_skill_contract.py) | 76 | 3,667 | 同为 Markdown 子串断言测试，部分关键防挂死条款可留极简哨兵，其余过度绑定措辞 |
| **合计** | **17 个文件**（另含 [goal-loop-design.md](../architecture/goal-loop-design.md) 352 行 / 30.4 KB） | **2,128** | **125,073** | 其中明确可退役/大幅瘦身的死重与锁死代码超过 **1,000 行（~50 KB）** |

### 1.2 本仓 28 份真实实施计划的活跃度画像（实证统计【A】）

对 `docs/project/plans/*.md` 全部 **28 份**历史交付计划执行全量正则检索并人工核验命中语境，得出客观采用率分层：

| 机制 / 工件 | 真实采用率 | 命中明细与语境核验【A】 | 价值分层 |
| :--- | :---: | :--- | :---: |
| **三轨通道分流** | **28 / 28 (100%)** | Heavy Track 18 份、Maintenance-Patch 8 份、Fast-Track 2 份，全量生效 | 核心护城河 |
| **`Active Checkpoint` 检查点** | **25 / 28 (89%)** | 计划头部统一维护当前阶段、完成度与恢复锚点，跨会话恢复主力 | 核心护城河 |
| **独立对抗终审联动** | **22 / 28 (79%)** | 广泛挂载 `dual-round-review`（Full / Light / Delta），质量核心保障 | 核心护城河 |
| **测试策略 / L0–L3 定级** | **17 / 28 (61%)** | 明确区分风险定级、强制级别与豁免理由，杜绝盲测与漏测 | 核心护城河 |
| **`dispatch-ledger` 派发账本** | **4 / 28 (14%)** | 集中出现于并行多子任务批次，属按需低频工具 | 保留（精简） |
| **`.goal-loop/` 运行时临时目录** | **2 / 28 (7%)** | 14 份复制了模板元数据行，但仅 2 份（`python-unification` / `p3-six-backlog`）真正存放差分基线或运行日志；**0 份**记录过「每 2 次只读强制写 scratchpad」 | 降级为按需约定 |
| **`goal-state-tracker.py`** | **0 / 28 (0%)** | 仅 3 份计划出现该词：2 份是重构/迁移该脚本本身，1 份（`spec-evolution` L24）为复制模板样板句，**业务任务实际调用为 0** | **建议退役** |
| **`HALF-OPEN` / `Re-Entry Gate`（G1–G4）** | **0 / 28 (0%)** | 从未被任何真实故障触发或落盘（`0/3+R1-1/2` 记法全仓零实例） | **建议大幅拆除** |
| **`evaluation-report-template.md`** | **0 / 28 (0%)** | 全仓零实例，且 `docs/project/evaluation/` 目录根本不存在 | **建议退役** |
| **`research-spike-template.md`** | **0 / 28 (0%)** | 全仓零实例；实际深度调研全部按 Diátaxis 落盘至 `docs/explanation/analysis/` | **建议退役** |

> **关键洞察**：就像此前退役 `spec-evolution`（见 [ADR-0003](../decisions/0003-retire-spec-evolution.md)）所验证的规律一样，**实证采用率是最诚实的过滤器**。一个在 28 次真实重型与维护交付中零次被业务调用的 667 行脚本模块，不是「备而不用」，而是持续消耗迁移成本（如专门为它做过 Bash→Python 统一迁移与 30 用例差分测试）的纯负资产。

---

## 2. 十二维横向对标矩阵（`goal-loop` vs 同类标杆）

基于 [同类调研报告](./2026-11-23-goal-loop-peer-research.md) 的一手剖析，将 `goal-loop` 与五大代表标杆逐维对标：

| # | 对比维度 | 本仓库 `goal-loop`【A】 | `obra/superpowers`【A】 | `mattpocock/skills`【A】 | `planning-with-files`【A】 | `OpenSpec`【A】 | `ralph-claude-code`【A】 |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **定位抽象层** | L1 提示词 + 零用 Python 状态脚本 | L1 微技能群 + 3 个极薄交接脚本 | L1 超薄微技能群 | L1 + L2（6 个确定性宿主 Hook） | L1/L2 轻流式变更集 CLI/Skill | L3 外部 Bash 循环运行时 |
| **2** | **总指令/代码体量** | 17 文件 / 2,128 行 / 125 KB | SDD 7 文件 / 1,171 行 / 56.7 KB；其余微技能 2–9 KB | 单技能 **20–133 行**（0.6–12 KB） | `SKILL.md` 534 行 + Hook 101 行 | 精简三命令闭环 | 外置 Shell 引擎 + 784 项测试 |
| **3** | **阶段密度** | **9–10 编号阶段**（`P-1` 至 `P5` + `DONE`） | 拆为独立技能按需串联 | 2–3 步（Spec → Tickets → Implement） | 动态阶段列表（`task_plan.md`） | 3 命令（Propose → Apply → Archive） | 单循环（读 PRD → 编码 → 验证 → 提交） |
| **4** | **存量维护友好度** | **极强**（专属 `Maintenance-Patch` 轨） | 中（需自行选技能组合） | 强（天然轻流式） | 强 | **极强**（定位 Built for brownfield） | 中（偏向新需求清单批跑） |
| **5** | **状态存储策略** | Markdown 计划头部 + 冗余正则脚本 | 计划专属 `.superpowers/sdd/progress.md` + `git log` | 代码库 + 轻量 Ticket | 三 Markdown 文件 + Hook 同步 | `changes/` 增量目录 + `specs/` | `prd.json` + `progress.txt` + Git |
| **6** | **跨会话/压缩保活** | 纯提示词要求「先读检查点」 | 纯提示词 + 强调信任账本与 `git log` | 无专用保活机制 | **确定性 `SessionStart` + `PreCompact` Hook** | 变更目录自然持久 | **每轮硬重置上下文** |
| **7** | **熔断与重试治理** | 纯提示词 4 态机 + G1–G4 + 25% 预算（**不可度量**） | 5 轮修复上限（R4–5 换更强模型）+ 裁决收口 | 极简人工介入 | 无硬熔断 | 无硬熔断 | **确定性外置 Bash 三态熔断 + 双条件退出门禁** |
| **8** | **子任务上下文交接** | 粘贴 7 维任务规约（易主上下文膨胀） | **文件指针交接**（`task-brief` 41 行 + `review-package` 46 行） | 上下文指针引用 | 单会话工作记忆 | 变更集文件引用 | 磁盘文件自读取 |
| **9** | **人机自治节奏** | 多处前置人工确认（P-1 / P0 / P3 开工前） | **先裁决不卡死（Rulings, not stalls）**，仅停 4 类硬边界 | 高自治小步推进 | 低打断单会话 | Propose 确认后直接 Apply | 全无人值守 |
| **10** | **任务切片范式** | 偏向线性子任务（`P3.1`, `P3.2`） | 独立任务 + **同形小改动合批** + 禁套娃审查 | **垂直曳光弹切片（DAG）** + Expand-Contract | 阶段清单 | 增量变更集 | JSON Story 列表 |
| **11** | **测试分级策略** | **行业罕见的强项**：L0–L3 + 影响面 + Mock 防逃逸 | 任务级 TDD + 完成后验证 | 切片自带验收测试 | 无专用测试矩阵 | 依赖项目自身 | 依赖外部验收脚本 |
| **12** | **独立审查与模型分层** | **强独立终审**（`dual-round-review`）；**缺模型档位分层** | 每任务审查 + 整分支终审 + **模型分层律** | 独立 `code-review` 技能 | 无独立审查 | 无强制双轮审查 | 无内置对抗审查 |

---

## 3. 过度设计与结构性病灶深挖（六大诊断）

### 病灶 1：零实战调用的 667 行「Markdown 正则状态机」代码债

- **一手证据【A】**：`skills/goal-loop/scripts/goal-state-tracker.py`（365 行）+ `.sh`（5 行）+ `tests/test_goal_state_tracker.py`（297 行）合计 **667 行 / 23.1 KB**，占整个技能近五分之一代码量，但在 28 份真实交付计划中**业务调用次数为 0/28**。
- **架构根因**：
  1. **定位尴尬**：`SKILL.md:31` 一方面声明「计划文件是唯一人类可读真相源、不建并行状态文件、`goal-state-tracker.py` 只做派生读写」，另一方面却花了 365 行用正则去解析和原地改写自由格式 Markdown 表格与复选框；
  2. **被两头夹击**：在对话型 Agent 环境下，模型直接 `edit_file` 修改计划头部检查点远比拼装 `SKILL_DIR` 环境变量和四条 CLI 子命令更自然、更少出错；而宿主原生任务清单（`update_steps` / `TodoWrite`）又承担了会话内实时进度展示；
  3. **虚构原语残留**：`host-adapters.md:49` 与 `goal-loop-design.md:13` 反复提及「宿主原生 goal 原语（如 `create_goal` / `get_goal` / `update_goal`）」，但主流宿主（Claude Code / Antigravity / Cursor）实际暴露的是步骤/待办/工作流原语，并非这套早期假设的命名。
- **行业对照**：Anthropic 明确指出机器高频维护的状态应存为 JSON，而非脆弱地解析 Markdown【B】；`beads` 更直接拒绝以 Markdown 作为数据库【A】。既然 `goal-loop` 决定坚持「Markdown 计划文件为唯一真相源」，就应顺应其本质让 Agent 直接读写精简的检查点块，彻底卸掉正则解析脚本包袱。

### 病灶 2：「提示词伪运行时」——不可度量且内部自相矛盾的重入状态机

- **一手证据【A】**：[failure-recovery-protocol.md](../../../skills/goal-loop/references/failure-recovery-protocol.md) L20, L50–L53, L70, L141 构造了一套高度精密的 4 态熔断协议：
  - 状态机：`CLOSED → OPEN → HALF-OPEN → ESCALATED`；
  - 4 条重入闸门（`G1 新假设`、`G2 新证据`、`G3 非措辞改写`、`G4 预算未耗尽`）；
  - 特定无空格落盘记法：`0/3+R1-1/2`；
  - 成本数学公式：上限 = `min(任务总预算 × 25%, 任务剩余预算 ÷ 3)`，且「**token 与 wall-clock 取先触顶者**」。
- **双重硬伤**：
  1. **物理不可度量**：在纯提示词（L1）环境中，LLM **根本看不到自身当前已耗 token 数、任务总预算基准或真实墙钟占比**。写进 Markdown 的 `min(25%, 剩余÷3)` 只能导致模型要么完全无视（28/28 计划零触发即为明证），要么在被逼填写《熔断报告》L141 成本快照时编造虚假百分比！对比 `frankbria/ralph-claude-code` 的 `lib/circuit_breaker.sh`【A】，真正的 `HALF_OPEN` 状态机与额度熔断必须在外部代码层计量；
  2. **同目录规范自相矛盾**：同在 `skills/goal-loop/references/` 下的 [host-adapters.md](../../../skills/goal-loop/references/host-adapters.md) L67 斩钉截铁地写着：**「预算单位是『轮次 / 检查点周期』，不是人类日历时间……AI 的执行时长不可预测且不对承诺有意义，可收敛的只有轮次。」** 而 `failure-recovery-protocol.md` L53/L141 却引入了 wall-clock 与百分比预算做硬判据——两份相邻核心规程直接打架！

### 病灶 3：阶段与规程过密，触发指令预算衰减与「大锤砸核桃」税负

- **一手证据【A】**：尽管入口 [SKILL.md](../../../skills/goal-loop/SKILL.md) 控制在 103 行 / 8.2 KB（遵循了 `agentskills.io` 的入口红线），但一旦进入 Heavy Track 实战，路由指针把 Agent 依次引入 **9–10 个编号阶段**（`P-1`、`P0`、`P0.5`、`P1`、`P2`、`P3`、`P3.5`、`P4`、`P5`、`DONE`）、**12 条铁律**、**7 份共 69.6 KB 的 `references/`** 以及 **4 份共 19.6 KB 的模板**。
- **成本与认知代价**：
  - 按 [调研报告 §3.1](./2026-11-23-goal-loop-peer-research.md) 汇总的实证规律，当单次重型任务陆续装入 `stage-progression-protocol.md`（19.1 KB）+ `host-adapters.md`（11.4 KB）+ `failure-recovery-protocol.md`（11.8 KB）+ `testing-decision-matrix.md`（7.3 KB）+ `context-engineering.md`（7.7 KB）+ 模板（9.2 KB），**累计超过 66 KB 中文规范与上百条显式/隐式约束**，极易逼近 IFScale 150–200 条指令阈值【B】，并触发 ETH Zurich 论文观测到的「模型过度服从导致的 **>20% 推理成本税**」与多余遍历【B】；
  - 编号 `P-1`、`P0`、`P0.5`、`P3.5` 本身就是典型「不断往原骨架打补丁插队」的历史演化痕迹（先有 P0–P5，后塞入 P-1、P0.5、P3.5），不仅心智繁琐，连 `evaluation-report-template.md`（43 行）与 `research-spike-template.md`（82 行）两份配套模板也都在实战中被完全弃用（0/28）。

### 病灶 4：机械未落地的 `2-Action Rule` 与 Manus 二次演化脱节

- **一手证据【A】**：[SKILL.md](../../../skills/goal-loop/SKILL.md) L40 将「每 2 次只读探查后，把结论写入 `.goal-loop/scratchpad.md` 或检查点锚点」列为**铁律 10**；[context-engineering.md](../../../skills/goal-loop/references/context-engineering.md) L20, L31 进一步展开。
- **问题本质**：
  1. **零执行力**：28 份计划中无一留存「每 2 次只读强制写盘」行为，因为探索代码库时动辄并行发起 4–8 次只读检索，每读 2 次就打断思路写一次 `.goal-loop/scratchpad.md` 在交互体验与轮次消耗上极其反人性；
  2. **违背最新上下文工程实践**：如调研报告 §3.3 所述，Manus 后续演进与 `planning-with-files` 均已表明——高频机械重写草稿文件会推高工具轮次税，真正需要保护的关键时点是**阶段切换、关键根因确立、大块探索收敛以及上下文压缩前（`PreCompact`）**，而非死板的「每 2 次只读」。

### 病灶 5：内部规范腐化、领域越界与「文案锁死型」假契约测试

精读源码共查出四处确凿的内部腐化证据【A】：

1. **个人环境绝对路径泄露**：[goal-loop-design.md](../architecture/goal-loop-design.md) L10 至今写着参考基准 `/home/hui/workspace/projects/faceFusionCpp/docs/dev/zh/process/workflow.md`，直接违背公共开源技能库的脱敏与可移植原则；
2. **违背本仓库 `GOVERNANCE.md` Diátaxis 治理红线**：
   - [stage-progression-protocol.md](../../../skills/goal-loop/references/stage-progression-protocol.md) L104, L133 与 [goal-plan-template.md](../../../skills/goal-loop/templates/goal-plan-template.md) L20, L55 仍在指令 Agent 写入 `docs/project/evaluation/` 和 `docs/project/research/`，但本仓库早将调研分析统一归位 `docs/explanation/analysis/`（`docs/index.md` V1.43.0）；
   - [documentation-sync-matrix.md](../../../skills/goal-loop/references/documentation-sync-matrix.md) L15–L35 更是全盘列举 `docs/architecture/*.md`、`docs/design/*.md`、`docs/adr/*.md`、`docs/getting_started.md`、`docs/user_guide.md`、`docs/reference/rules/glossary.md` 等**非 Diátaxis 瀑布旧路径**，直接与本仓 [GOVERNANCE.md](../../GOVERNANCE.md) 红线冲突，且职责上与 `doc-governance` 严重重叠；
3. **特定前端技术栈硬编码 + 叙述前后漂移**：
   - [stage-progression-protocol.md](../../../skills/goal-loop/references/stage-progression-protocol.md) L204 在通用的 P4 阶段步骤中写死了「**核查 Rules of Hooks、SSR 沙盒**」（明显残留自早期某个 React/Next.js 项目的拷贝）；
   - 同文件 L4 仍称「本规程确立**双轨执行通道**」，L13–L19 的 ASCII 图也仅有 Heavy Track 与 Fast-Track，而 L28 矩阵和 L43 早已扩展为三轨（含 Maintenance-Patch），文档内部演进脱节；
4. **168 行「文案锁死型」假安全感测试**：
   - [test_failure_recovery_contract.py](../../../skills/goal-loop/tests/test_failure_recovery_contract.py)（92 行）与 [test_optional_skill_contract.py](../../../skills/goal-loop/tests/test_optional_skill_contract.py)（76 行）看似增加了 pytest 绿灯数量，实则核心断言形如 `assert "3 + 2 + 2 = **7 次**" in body`（L50）、`assert "25%" in body and "任务剩余预算 ÷ 3" in body`（L51）。这类测试**完全不能证明 LLM 会遵守规程**，唯一效果是在你试图简化冗余提示词时让 CI 变红——把「过度设计」焊死在了回归测试里。

### 病灶 6：缺失四项经 2026 社区验证的高杠杆编排模式

横向对比 `obra/superpowers`（Nov 2026）与 `mattpocock/skills`，`goal-loop` 在真正决定多智能体长任务成败的四个现代抓手上反而处于空白：

1. **缺「文件指针交接」防主上下文滚雪球**：[host-adapters.md](../../../skills/goal-loop/references/host-adapters.md) L36 要求按 `atomic-task-template.md` 传 7 维任务规约，却未提供类似 `superpowers` 的极薄打包脚本（`task-brief` 41 行、`review-package` 46 行），长任务多轮派发与审查时极易把完整计划段落、历史摘要和长 Diff 反复粘贴进主上下文；
2. **缺「先裁决，不卡死（Rulings, not stalls）」**：当前 `SKILL.md` 设有 P-1 User Nod、P0 澄清、P3 开工前选后端等多个停顿点，但对「执行过程中遇到非致命小歧义或计划微瑕疵时，应自主裁决、入账并继续，还是停下来问人」缺少明确的四类硬停边界定义；
3. **缺「垂直曳光弹切片（DAG）+ 同形小改动合批 + 禁套娃审查」**：现有 `atomic-task-template.md` 与 `host-adapters.md` 强调无文件冲突可并行，但未引入「跨文件同形微改合批单次派发（省审查与派发开销）」「子执行器严禁自派审查员（防重复烧席位）」「垂直切片优于水平分层」三项高收益工程纪律；
4. **缺「通用能力档位模型分层」**：`host-adapters.md:21` 仅规定「不得写死品牌模型名」（这是对的），但连带空白了「按任务复杂度分高/中/低能力档位 + 轮次成本优于单价（Turn count beats token price）」的平台无关路由指导，导致所有机械子任务默认继承主会话最贵模型。

---

## 4. 真正值得保留的差异化护城河

严格遵守「客观严苛但不盲目否定」原则，以下 **5 项真资产**在实证采用率与横向对标中均表现优异，**是 `goal-loop` 不可丢弃的核心护城河**：

| # | 核心护城河 | 内部实证【A】 | 为何优于多数社区竞品 |
| :---: | :--- | :---: | :--- |
| **1** | **三轨通道分流（尤以 `Maintenance-Patch` 为最）** | 28 / 28 (100%) | 精准破解了 `spec-kit` / `BMAD` 在存量缺陷修复中的「大锤砸核桃」顽疾；「生命周期阶段先于文件跨度判定 + 契约变动即升级」是极佳的架构判据 |
| **2** | **改动特征 → L0–L3 测试定级矩阵 + Mock 防逃逸红线** | 17 / 28 (61%) | `superpowers`、`OpenSpec`、`planning-with-files` 均缺乏同等严谨的「影响面分析 + I/O 边界判定 + 禁止借 Mock 逃逸 L2」规程 |
| **3** | **计划头部 `Active Checkpoint` 单一真相源** | 25 / 28 (89%) | 相比 `planning-with-files` 三文件同步或 `goal-state-tracker` 双写，单计划文件头部锚点天然符合人类审阅与 Git 版本化习惯 |
| **4** | **可插拔独立对抗终审 + 隔离不可内联红线** | 22 / 28 (79%) | `host-adapters.md:105-108` 明确禁止审查超期时退化为主会话内联自审，与 Anthropic 2026 Evaluator 独立原则完全同频，且比竞品更严密 |
| **5** | **可选外部技能三分支无头安全降级协议** | 工程防呆关键 | 实测防住了「无头子智能体调人类提问工具导致整条流水线挂死」（`host-adapters.md:88`）的真实生产故障，比硬绑定依赖的框架更具可移植性 |

---

## 5. 分阶段重构优化路线图

重构总原则：**「砍掉零使用与伪运行时死重，修平内部腐化，用极薄确定性脚本换回真正高价值的上下文经济性与自治纪律」**。

### 5.1 阶段划分与具体改造清单

#### P0：止血减重与一致性清零（高 ROI、低风险、立竿见影）

| 序号 | 改造项 | 目标文件 | 预期效果与验收口径 |
| :---: | :--- | :--- | :--- |
| **P0-1** | **退役零使用正则状态机脚本及配套测试** | 删除 `scripts/goal-state-tracker.py`、`.sh`、`tests/test_goal_state_tracker.py`；同步清理 `SKILL.md:78-90` 与模板备注 | 净减 **667 行 / 23.1 KB** 零用代码债；`SKILL.md` 聚焦纯路由；更新设计书并写明「直接编辑计划头部锚点」 |
| **P0-2** | **拆除不可度量的 `HALF-OPEN / G1–G4 / 25% 预算` 伪运行时** | 重写 [failure-recovery-protocol.md](../../../skills/goal-loop/references/failure-recovery-protocol.md) 与 [SKILL.md](../../../skills/goal-loop/SKILL.md) 铁律 9；清理 [test_failure_recovery_contract.py](../../../skills/goal-loop/tests/test_failure_recovery_contract.py) 文案锁死断言 | 回归清晰、可执行、无自相矛盾的「3-Tries 熔断 → STOP/RECORD/RESEARCH → 非阻塞升级（`parked` + 人类裁决）」；彻底消除与 `host-adapters.md:67` 的冲突，减少约 6–8 KB 提示词噪音 |
| **P0-3** | **退役两份零使用僵尸模板** | 删除 `templates/evaluation-report-template.md` 与 `templates/research-spike-template.md` | 净减 **125 行 / 6.4 KB**；P0.5 调研统一直指 `docs/explanation/analysis/`（与 `doc-governance` 对齐），存量评估收归计划背景段 |
| **P0-4** | **修复内部腐化、路径违例与领域泄露** | 修订 [documentation-sync-matrix.md](../../../skills/goal-loop/references/documentation-sync-matrix.md)（删全部瀑布旧目录，对齐 Diátaxis 与 `doc-governance`）、[stage-progression-protocol.md](../../../skills/goal-loop/references/stage-progression-protocol.md)（补全三轨图、删 L204 React/SSR 硬编码、修 L104/L133 旧路径）、[goal-plan-template.md](../../../skills/goal-loop/templates/goal-plan-template.md)（修旧路径）、[goal-loop-design.md](../architecture/goal-loop-design.md)（删 L10 个人绝对路径） | 全技能零 Diátaxis 违例、零个人路径、零特定前端栈污染、零双轨/三轨自相矛盾 |
| **P0-5** | **将机械 `2-Action Rule` 升级为事件驱动落盘** | 修订 `SKILL.md` 铁律 10 与 [context-engineering.md](../../../skills/goal-loop/references/context-engineering.md) | 废除「每 2 次只读强写盘」；改为「阶段切换 / 关键根因收敛 / 上下文压缩前落盘检查点，大型原始输出按需卸载至 `.goal-loop/`」 |

#### P1：现代化架构升级（补齐 2026 标杆高杠杆能力）

| 序号 | 改造项 | 目标文件 | 预期效果与验收口径 |
| :---: | :--- | :--- | :--- |
| **P1-1** | **收敛 9–10 个补丁编号为 5 个清晰逻辑阶段** | `SKILL.md`、`stage-progression-protocol.md`、`goal-plan-template.md` | 将 `P-1 / P0 / P0.5 / P1 / P2 / P3 / P3.5 / P4 / P5` 收敛为 **`Align`（对齐/选型）→ `Plan`（计划/定级）→ `Execute`（切片实现）→ `Verify`（集成/对抗终审）→ `Close`（归档）** 五主阶段，用三轨裁剪表声明子步骤启停，消除历史编号债 |
| **P1-2** | **引入极薄「文件指针交接」脚本替代重型 tracker** | 新增约 40–60 行 Python 极薄脚本 `scripts/pack-handoff.py`（提供 `brief` 抽单任务块与 `review-pkg` 打包 `BASE..HEAD` 提交与 Diff）+ 精简单测 | 精准解决主调度上下文滚雪球痛点（`superpowers` 42k 字符教训），主调度与子智能体只传文件路径指针，避免 `HEAD~1` 丢提交 |
| **P1-3** | **注入四项现代多智能体执行纪律** | [host-adapters.md](../../../skills/goal-loop/references/host-adapters.md) 与 [atomic-task-template.md](../../../skills/goal-loop/templates/atomic-task-template.md) | ①「先裁决不卡死（Rulings, not stalls）」+ 四类硬停边界 + 账本 `Ruling:` 记录；② 通用能力档位模型分层（低/中/高档，含「轮次成本优于单价」提示）；③ 同形小改动合批 + 严禁子执行器套娃自派审查；④ 垂直曳光弹切片（DAG）优先 |
| **P1-4** | **对齐真实宿主原语并压缩冗余参考文案** | [host-adapters.md](../../../skills/goal-loop/references/host-adapters.md) | 替换虚构的 `create_goal` 为真实宿主能力族（步骤清单、隔离工作区子智能体、工作流编排），合并重叠段落 |

#### P2：远期可选演进（待宿主 Hook 跨平台生态成熟后按需评估）

- **可选宿主 Hook 轻适配包**：参考 `OthmanAdi/planning-with-files` 的 `hooks/hooks.json`【A】，为支持确定性 Hook 的宿主（如 Claude Code）提供可选安装的轻量 Hook（仅挂载 `SessionStart` 提醒检查点、`PreCompact` 强制落盘、`Stop` 校验未勾选项），将真正需确定性兜底的动作从 L1 提示词升格到 L2，而不是继续往 Markdown 里写更严厉的警告词。

### 5.2 重构前后体量与结构预期对照

| 指标 | 重构前（现状实测【A】） | 仅执行 P0 预期【C】 | 执行 P0 + P1 预期（`goal-loop` V3.0）【C】 |
| :--- | :---: | :---: | :---: |
| **总文件数** | 17 | 11（-35%） | 11–12（含 1 个极薄交接脚本 + 行为单测） |
| **总行数** | 2,128 行 | ~1,100 行（**-48%**） | ~1,000–1,150 行（**-46%~-53%**） |
| **总字节数** | 125.1 KB | ~65 KB（**-48%**） | ~58–68 KB（**-46%~-54%**） |
| **脚本代码定位** | 365 行零用 Markdown 状态解析器 | 0 行脚本（纯路由 + 细则） | ~60 行高频文件指针交接打包器（真正被调用） |
| **测试类型** | 297 行死代码单测 + 168 行文案锁死测试 | 仅保留关键行为与防伪造哨兵（~40 行） | 打包脚本真实行为单测 + 极简防回归哨兵 |
| **内部违例与矛盾数** | 4 类确凿腐化（路径/Diátaxis/React/预算矛盾） | **0** | **0** |

---

## 6. 供决策的可选执行档位

为避免未经确认擅自大改核心技能，以下提供三个可行重构方案供决策拍板（按推荐顺序排列）：

| 方案 | 范围 | 优点 | 代价与风险 | 适用诉求 |
| :--- | :--- | :--- | :--- | :--- |
| **方案 A（推荐）：V3.0 完整升级（P0 + P1）** | 止血瘦身 + 收敛 5 阶段 + 文件指针交接 + Rulings/模型分层/合批/DAG 切片 | 一次清完所有历史债并追平 2026 标杆代差；总体积减半、执行效率与自治体验跃升 | 改动跨多文件与阶段命名，需同步更新 `goal-loop-design.md`、跨技能引用与跑 `dual-round-review` 终审 | 希望 `goal-loop` 成为长期高水准主力技能，愿意投入 1 次完整 Heavy Track 重构 |
| **方案 B（稳健快速）：仅执行 P0 止血瘦身** | 退役零用 tracker 与 2 份僵尸模板、拆除 `HALF-OPEN/25%` 伪运行时、清零全部腐化与路径违例、废除机械 2-Action Rule | **改动安全且向后兼容**（保留现有 P-1..P5 阶段号，零跨技能破坏），立刻砍掉 ~48% 死重 | 暂未补齐文件指针交接、Rulings 与模型分层等 2026 新模式 | 优先追求低风险快速瘦身，架构大升级留待下个迭代 |
| **方案 C（激进拆分）：微技能化解体** | 将测试定级、后端适配、异常恢复等拆分为多个独立微技能，`goal-loop` 退化为 ~80 行超薄路由（效仿 `superpowers`） | 单技能极致精简，可单独复用 `testing-decision-matrix` | 显著增加技能注册面、版本同步与用户激活心智负担，且可能破坏本仓现有路由契约 | 仅当计划将各子能力分别作为独立公共技能对外发布时考虑 |

> **下一步建议**：若确认采用**方案 A** 或**方案 B**，可先针对是否存在外部项目直接依赖 `goal-state-tracker.py` 或旧阶段编号（`P0.5`/`P3.5`）做一次全仓 `grep` 核查，随后按计划文档与独立对抗终审流程实施落地。
