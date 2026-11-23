# `agy-delegation-workflow` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-AGY-DELEGATION-EVAL-2026
> - **当前版本**: V1.0.1
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于本仓库 `skills/agy-delegation-workflow/` 全部 8 个源文件与设计书的源码精读、28 份历史实施计划及 18 份审查归档的实证统计、本机 `agy 1.5.14` CLI 实测，以及配套外部调研报告 [2026-11-23-agy-delegation-workflow-peer-research.md](./2026-11-23-agy-delegation-workflow-peer-research.md)。
> - **证据分级**: 【A】一手（本仓库源码/行号/Git 历史/实跑统计、本机 CLI 实测、外部仓库一手源码）｜【B】二手转引（官方文档与工程博客摘要）｜【C】架构裁决与重构建议

> [!NOTE]
> **执行注记 (2026-11-23)**：本评估报告选定的**方案 A** 已按 [ADR-0004](../decisions/0004-retire-agy-delegation-workflow.md) 正式执行退役，原 `skills/agy-delegation-workflow/` 技能文件已移除；下表与正文中指向已退役源文件的相对链接已改为反引号路径文本以保留历史溯源。

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.1** | 2026-11-23 | AI Agent | 王辉 | 补充已按 `ADR-0004` 执行退役的注记，并将已删除的 `skills/agy-delegation-workflow/` 相对链接转为行内路径文本消除断链 |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `agy-delegation-workflow` 全量源码与 28 份计划 0% 实战使用率审计、四重硬绑定与功能重叠解剖、脚本安全体检及三档去向方案对比 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`agy-delegation-workflow` 是否过度设计/过时？是否还有继续独立存在的价值？**

**结论：该技能已处于典型的「零实战消费、高被动维护税、四重硬绑定腐化、与上游规程双 SSOT 冲突」状态——属于继 `spec-evolution` 之后，本仓库最具备「抽离少量真资产后正式退役（降维合并）」充分依据的候选技能。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **仓库实证使用率** | 28 份历史计划中文本提及 10 次，但实际启用 `.agy-tasks/` 或 `dispatch-agy` 派发任务为 **0 / 28（0%）** | 导入仓库两个半月以来零实战消费，全部近期提交均为被动应付仓库治理指标（补测、Python 迁移、补设计书） |
| **跨技能与原生重叠度** | 约 **70%+** 内容与 `contexts/AGENTS.md`、`goal-loop/references/host-adapters.md`、`goal-loop/templates/atomic-task-template.md` 及 Antigravity 原生 `invoke_subagent`/`run_workflow`/`swarm` 重叠或被全面超越 | 与 `host-adapters.md` 形成双份委派真相源冲突，且曾因协调 9 行边界措辞触发 6 轮 216 KB 审查事故 |
| **硬绑定与腐化程度** | ① `Gemini 3.8 Flash (High)` 在 6 文件 **14 处**硬编码（已跨代过时）；② `failure-modes-audit.md` 7 条中 **6 条**硬编码历史 Next.js 项目私有组件库 props；③ 绑死 WSL2 代理与私人 Hindsight 插件变量；④ 两份 references 遗漏 `--add-dir` 自违 `SKILL.md` 红线 | 作为「公共可复用技能」已严重失格，无法直接安装到非本人、非特定前端仓库使用 |
| **脚本代差与安全风险** | `dispatch-agy.py` 强制 `--dangerously-skip-permissions`、大 Prompt 走 argv（存在 Windows 截断/注入与 Linux 128 KB 风险）、后台 fire-and-forget 且污染未配 `.gitignore` 的仓库；完全未用 `agy 1.5.14` 原生 `--sandbox`/`--mode`/`--output-format stream-json`/`acp` | 相比 2026 工业基线落后整整一代 |
| **真正剩余的独特资产** | 仅剩 **3 项**可数资产：① Silent Landing（假失败/延迟落盘）判别 SOP；② 连续 2 批重写率 >50% 切回 Direct-Write 四准则；③ 外部宿主调用 `agy -p` 时的代理清洗与 `--add-dir` 防串台技巧 | 价值真实但极度轻量，完全无需为此维持 1,174 行独立技能（含 490 行测试）+ 152 行设计书的沉重外壳 |

---

## 1. 全量资产盘点与 0% 实战活跃度实证【A】

### 1.1 文件体量与演化轨迹

| 文件路径 | 行数 | 字节数 | 真实定位与健康度 |
| :--- | :---: | :---: | :--- |
| `SKILL.md` | 126 | 9,260 | 入口路由（`description` = 334 字符，未超限）；6 处写死 `Gemini 3.8 Flash`、L22 宣称全仓委派 SSOT 与 `host-adapters.md` 冲突 |
| `references/failure-modes-audit.md` | 39 | 4,209 | **重度污染**：7 条失败模式中 6 条写死某历史 Next.js/React 19 私有组件库 props 与命令 |
| `references/infrastructure-troubleshooting.md` | 87 | 4,161 | 含高价值 **Silent Landing SOP**，但 L24–L28 标准命令漏 `--add-dir`，绑死 WSL 代理 |
| `references/priority-fallback-chain.md` | 66 | 4,708 | 含高价值 **Direct-Write 四准则**（L47–L55），但 L29–L33 漏 `--add-dir`、L26 写死过时模型 |
| `templates/task-prompt-template.md` | 91 | 5,384 | **100% 被超越**：1–7 节与 `goal-loop/templates/atomic-task-template.md` 几乎逐字重复，且缺少后者的第 8 节结构化输出契约 |
| `scripts/dispatch-agy.py` + `.sh` | 275 | 10,454 | 强制无沙箱全权限、硬编码过时模型、argv 传大 Prompt、含原 Bash 行号 `42/46/50/54` 历史包袱 |
| `tests/test_agy_delegation_contract.py` | 490 | 20,514 | 占总行数 **41.7%**；前 9 用例为脆弱中文排版/条数锁死测试，后 9 用例为离线 fake-shim 行为测试（但锁死过时默认模型） |
| **技能目录合计** | **1,174** | **58,690** | 另含 [agy-delegation-workflow-design.md](../architecture/agy-delegation-workflow-design.md)（152 行 / 11.5 KB） |

**Git 演化实证（全史 8 次提交）【A】**：
- `2026-09-08` 随仓库初始化导入后，3 份 references 与模板**至今零业务驱动演进**；
- 唯一一次真实运维修复是 `2026-09-24`（`1dd2caf`）补 `--add-dir` 修 Hindsight 记忆库落错 `coding-agent::config`；
- 其余 6 次提交全部为**被动响应仓库治理指标**：补 MIT license、补 SSOT 边界句（引发 6 轮审查）、为结清 `BK-0039` 补 490 行测试、全仓 Python 统一迁移、以及 `2026-11-12` 为结清 `BK-0041` 补 152 行设计书。

### 1.2 全部 28 份历史实施计划实证使用率【A】

全量扫描 `docs/project/plans/*.md`（28 份），命中 `agy` 相关关键词的共 10 份，逐一核验真实语境后确认**业务派发使用率为 0 / 28（0%）**：
- **作为解耦/反面教材（2 份）**：`2026-09-14-dual-round-review-v2.md`、`2026-09-14-goal-loop-v2-refactor.md`（均批评并拆除旧版对 `agy -p` 的硬绑定）；
- **作为仓库运维/清单枚举/体检受检对象（6 份）**：软链修复、技能枚举、`spec-evolution` 缺测试体检与 `BK-0041` 排除声明；
- **作为统一迁移被改造对象（1 份）**：`2026-10-19-skill-scripts-python-unification.md`（把 `.sh` 迁成 `.py`，自身未被用来派发任务）；
- **易误判项澄清（1 份）**：`2026-10-14-p2-six-backlog-items.md:138` 虽写有 `R1 红队（agy · Gemini 3.8 Flash High）`，但核对 [对应审查归档 README](../../project/reviews/2026-10-14-p2-six-backlog-items/README.md) L18–L19 可证实其派发句柄为**宿主原生子智能体**（写入形态 `direct`），全程未调用 `dispatch-agy` 或 `.agy-tasks/`。

---

## 2. 核心架构矛盾与五大病灶深挖【A】

### 病灶 1：四重硬绑定与内部滞后自相矛盾

1. **跨代过时模型硬编码（14 处）**：`Gemini 3.8 Flash (High)` 被写死在 `SKILL.md:3,16,64,79,85,126`、`infrastructure-troubleshooting.md:26`、`priority-fallback-chain.md:13,26,31`、`dispatch-agy.py:5,28`、`test_agy_delegation_contract.py:44` 与设计书 L77。实测本机 `agy 1.5.14` 已有 23 个模型（主力已迈向 `Gemini 4` 系列与 `Claude 5.5`），且这种写死**公然违背** [goal-loop/references/host-adapters.md](../../../skills/goal-loop/references/host-adapters.md)（L21）「不得在规程里写死品牌模型名」的本仓原则。
2. **单一历史前端项目私有约定污染**：`failure-modes-audit.md`（L11–L17）7 条失败模式中 **6 条**直接锁死某个 Next.js/React 19 项目的私有 UI 组件库 props（`Badge variant="secondary"` 应为 `neutral`、`Tabs items=` 应为 `tabs=`、`toast variant="destructive"` 应为 `"error"`、`@/mock`、`src/app/<新路径>/*.tsx`、`npx vitest run`、`pnpm build`）。尽管设计书 §8.2 早已承认此缺陷，但从未剥离。
3. **私人机器与私人插件耦合**：WSL2 TUN 死代理直接写入技能 `description`（`SKILL.md:3`）；`dispatch-agy.py:241-249` 在无 git 根时输出 Hindsight 插件专属警告 `coding-agent::{cwd_name}`，对未装 Hindsight 的外部用户毫无意义。
4. **内部规则自相矛盾**：`2026-09-24` 修复 Hindsight 串台时仅改了 `SKILL.md:82-87` 与脚本，**遗漏了** `infrastructure-troubleshooting.md`（L24–L28）和 `priority-fallback-chain.md`（L29–L33）中的「标准命令」——两处均缺少 `--add-dir "$PWD"`，直接违反 `SKILL.md:82` 硬红线。

### 病灶 2：70%+ 功能重叠与双 SSOT 摩擦事故

| 能力模块 | 本技能现状 | 仓库上位归属 / 原生能力 | 判定 |
| :--- | :--- | :--- | :---: |
| 认知不外包 / Zero-Trust | `SKILL.md:33-51, 106-113` | `contexts/AGENTS.md:60-64` | ~90% 重叠 |
| 后端选择与并行编排 | `SKILL.md:55-66, 96-99`、`priority-fallback-chain.md` | `goal-loop/references/host-adapters.md`（后端三选一 + 账本 + 在途上限） | **双 SSOT 冲突** |
| 7 维自包含任务模板 | `templates/task-prompt-template.md` | `goal-loop/templates/atomic-task-template.md`（多第 8 节结构化输出契约） | **100% 被超越** |
| 同宿主子任务隔离并发 | 仅知 `invoke_subagent` | Antigravity 原生 `invoke_subagent(Workspace="share"/"branch")`、`run_workflow`、`swarm` | **全面代差落后** |
| 3-Tries 降级与终审 | 一句话提 3-Tries + 调 `dual-round-review` | `goal-loop` + `dual-round-review` | 完全冗余 |

**历史高昂摩擦实证【A】**：`SKILL.md:22` 宣称全仓执行委派细则均以本技能为 SSOT，直接与宿主无关的 `host-adapters.md` 冲突；而 [2026-10-10-global-agent-delegation-redlines/README.md](../../project/reviews/2026-10-10-global-agent-delegation-redlines/README.md) 记录，当年为协调 `AGENTS.md`（+7 行）与 `SKILL.md`（+2 行）共 **9 行边界措辞**，竟耗费 **6 轮对抗审查、216 KB 报告、6 次提交**，暴露出该技能独立占山头的边际成本远超收益。

### 病灶 3：`dispatch-agy.py` 安全边界与跨平台隐患

对照 [调研报告 §2 & §3.1](./2026-11-23-agy-delegation-workflow-peer-research.md) 的 2026 工业基线，`dispatch-agy.py` 存在四处工程硬伤【A】：
1. **无条件裸奔权限**（`dispatch-agy.py:260`）：硬编码 `--dangerously-skip-permissions`，无参数可启用 `agy 1.5.14` 原生 `--sandbox` 或 `--mode accept-edits`；
2. **大 Prompt 走 `argv` 存在截断/注入隐患**（`:215-217, 256-257`）：Windows `CreateProcess` 32 KB（`.cmd` 约 8 KB 且特殊字符易被 `cmd.exe` 解析）与 Linux 128 KB 限制下，大自包含 Prompt 应走 stdin 管道或文件路径而非裸 `-p content`；
3. **后台模式 fire-and-forget 且可能污染目标仓库**（`:188-208`）：无 PID 锁/退出码落盘/僵死检测，且会在未配 `.gitignore` 的外部仓库根目录强建 `.agy-tasks/logs/` 产生未追踪垃圾文件；
4. **子进程 `$PATH` 不可达与过时包袱**（`:71-81, 218, 230`）：当前 Antigravity 子智能体默认 `$PATH` 不含 `~/.local/bin` 导致 `shutil.which("agy")` 直接失败；同时代码中残留复刻原 Bash 行号 `42/46/50/54` 的 `$2: unbound variable` 假报错，以及 `:218` `os.execvp("agy", ...)` 二次查找 PATH 的小瑕疵。

### 病灶 4：490 行测试占总行数 41.7%，半数为文案排版锁死

实测 `test_agy_delegation_contract.py` 18/18 通过（0.75s）【A】，但前 9 个用例（L53–259）锁死确切中文标题、`len(bullets) == 4`、固定词组（`终端套娃`、`IMPLEMENTATION_PLAN.md`、`以本技能为准`），导致任何精简或去硬绑定都会大面积误报红灯；后 9 个 fake-shim 行为用例虽扎实，却把已过时的 `DEFAULT_MODEL = "Gemini 3.8 Flash (High)"` 焊死在 `:44` 断言中。

---

## 3. 仅存的 3 项真资产（抽离后无损保留）

剥离全部重叠、硬编码与过时外壳后，本技能真正经得起时间检验的独特工程智慧高度收敛为三小块【A】：

| # | 真资产 | 原位置 | 建议落点（若退役本技能） |
| :---: | :--- | :--- | :--- |
| **1** | **Silent Landing（假失败 / 延迟落盘）判别 SOP** | `SKILL.md:101-104`、`infrastructure-troubleshooting.md:33-87` | 并入 `goal-loop/references/host-adapters.md` 无头后端异常处理节（或轻量故障排查段落），明确「退出码 ≠ 磁盘状态，先 `git status` + 跑单测再判失败」 |
| **2** | **Direct-Write 四条止损判据** | `priority-fallback-chain.md:47-55` | 并入 `goal-loop/references/host-adapters.md` 编排经济学节（与 `superpowers` 的「Turn count beats token price」形成完美互补：连续 2 批重写率 >50% + 系统错配 + 已掌握全上下文 + 同质化复刻 → 停委派改直写） |
| **3** | **通用大模型虚假合规 grep 审计思想**（剥离 Next.js 私有 props 后） | `failure-modes-audit.md:1-18`（仅保留「自造 Fallback / 编造 API / 硬编码绕过规范 / 隐蔽放宽共享类型」四类语言无关抽象模式） | 并入 `dual-round-review` 红队常见攻击面清单，彻底删掉私有组件库 props |

> 注：针对个人机器的「WSL 代理清洗 + `agy --add-dir` 防 Hindsight 串台」，属于极度依赖特定用户环境与单一 CLI 版本的运维笔记，适合浓缩为 `docs/how-to/` 下的一篇简短操作说明或归档到本机配置，而非撑起一个 58 KB 的公共技能。

---

## 4. 横向对标与三档去向方案对比【C】

结合配套调研报告中「同宿主已被原生原语彻底取代，跨宿主/CI 生态位极窄且正转向 SDK/ACP」的外部趋势，给出三档决策选项：

| 方案 | 核心动作 | 收益 | 代价与风险 | 推荐度 |
| :--- | :--- | :--- | :--- | :---: |
| **方案 A（强烈推荐）：抽离真资产 + 正式退役（效仿 ADR-0003）** | ① 将 **Silent Landing SOP** 与 **Direct-Write 四准则**浓缩（~35 行）并入 `goal-loop/references/host-adapters.md`；将抽象后的虚假合规检查并入 `dual-round-review`；② 写 `ADR-0004` 正式退役 `skills/agy-delegation-workflow/`（清理 1,174 行 + 152 行设计书与全部过时引用），同步更新 `host-adapters.md` 对外部无头 CLI 的引用口径 | 彻底消除 0% 实战使用率僵尸技能、14 处过时模型、Next.js 私有污染、双 SSOT 冲突与被动治理税；全仓结构更干净 | 若未来偶发在 Claude Code 里调 `agy -p`，需手敲带 `--add-dir --sandbox` 命令或直接用官方 `google-antigravity` SDK（可在 `docs/how-to/` 留 1 页备忘） | **首选** |
| **方案 B：最小止血瘦身（降格为纯 `agy` CLI 后端薄适配插件）** | 保留技能目录，但大幅瘦身：删掉 `task-prompt-template.md`、`failure-modes-audit.md` 与 `SKILL.md:22` 双 SSOT 声明；去除 `Gemini 3.8 Flash` 默认值与强制 `--dangerously-skip-permissions`（接入 `--sandbox`/stdin）；修齐两处漏 `--add-dir`；拆掉前 9 个文案锁死测试 | 保留 `dispatch-agy.py` 跨平台脚本兼容性，消除显性腐化与冲突 | 未解决在原生 Antigravity 宿主下 **0/28 实战使用率**的结构性闲置问题，仍需随 `agy` CLI 版本持续维护 | 次选（仅当您确实经常在 Claude Code / CI 中调用 `agy -p`） |
| **方案 C：大重构为厂商中立「跨 CLI 无头派发器」** | 更名去 `agy` 化（如 `headless-cli-dispatch`），同时封装 `agy 1.5+`、`claude -p`、`codex exec` + git worktree + NDJSON 解析 | 覆盖异构跨模型套利与 CI 批处理生态位 | 工程与维护投入极高，直接与 `OrchestratorInc/agent-orchestrator`（15k★）、`ccmanager`、`ACP` 重复造轮子，ROI 极低 | 不推荐 |

> **关键拍板前提**：若您在日常工作中**基本都在 Antigravity 或各自宿主内使用原生子智能体**、极少在 Claude Code 里外挂调 `agy -p`，建议直接选**方案 A（抽资产 + 退役）**；只有当您高频跨宿主调用 `agy -p` 执行批量无头任务时，方案 B 才值得投入维护。
