# ADR-0004: 退役 `agy-delegation-workflow` 技能并将三项核心资产沉淀至通用规程

> **ADR 控制元数据**
> - **决策编号**: 0004
> - **当前版本**: V1.0.0
> - **当前状态**: Accepted
> - **决策所有者**: 核心架构组
> - **决议日期**: 2026-11-23
> - **取代历史文档**: [agy-delegation-workflow 架构设计书](../architecture/agy-delegation-workflow-design.md)
> - **评估依据**: [无头 Coding Agent 委派调研](../analysis/2026-11-23-agy-delegation-workflow-peer-research.md) · [agy-delegation-workflow 过度设计评估](../analysis/2026-11-23-agy-delegation-workflow-architecture-evaluation.md)
> - **关联实施计划**: [2026-11-23-wave1-retire-agy-and-slim-clarification.md](../../project/plans/2026-11-23-wave1-retire-agy-and-slim-clarification.md)

---

## 1. 背景与上下文 (Context and Problem Statement)

`agy-delegation-workflow` 于 2026-09-08 随仓库初始化导入，原定位是「前台规划审查 + 后台 `agy -p` 无头进程执行」。结合 2026-11-23 全仓深度调研与源码实证审计，该技能暴露出四项结构性失配：

1. **仓库实战使用率为 0%**：全量扫描 28 份历史实施计划，实际调用 `.agy-tasks/` 或 `dispatch-agy.py/.sh` 派发编码任务的次数为 **0 / 28**；近两个月 8 次提交中有 6 次纯属被动应付仓库治理指标（补测、Python 迁移、补设计书），零业务驱动演进。
2. **四重硬绑定丧失公共复用性**：① 在 6 文件 14 处硬编码已跨代过时模型 `Gemini 3.8 Flash (High)`（直接违背 `goal-loop/references/host-adapters.md`「禁止写死品牌模型名」）；② `failure-modes-audit.md` 7 条审计项中 6 条写死某历史 Next.js/React 19 项目的私有组件库 props；③ 绑死个人机器 WSL2 代理与 Hindsight 插件环境变量；④ `dispatch-agy.py` 无条件 `--dangerously-skip-permissions` 且以 `argv` 传递大 Prompt，相比 `agy 1.5.14` 原生 `--sandbox` / `--mode` / `--output-format stream-json` / `acp` 与官方 SDK 落后整代。
3. **70%+ 功能重叠与双 SSOT 冲突**：认知不外包、Zero-Trust 验收、7 维自包含任务模板（已被 `goal-loop/templates/atomic-task-template.md` 含第 8 节输出契约全面超越）、并行编排与宿主原生 `invoke_subagent` / `run_workflow` / `swarm` 高度重叠；`SKILL.md:22` 宣称全仓委派 SSOT 与 `host-adapters.md` 冲突，历史上曾为协调 9 行边界措辞触发 6 轮 216 KB 审查事故。
4. **仅存 3 项极轻量独特资产**：① **Silent Landing（假失败 / 延迟落盘）判别 SOP**；② **Direct-Write（连续 2 批重写率 >50% 切回前台直写）四条止损准则**；③ 剥离私有前端约定后的**通用大模型虚假合规检查要点**（编造 API 属性、硬编码绕过规范、隐蔽放宽共享类型）。

---

## 2. 考虑的备选方案 (Considered Options)

* **方案 A（选定）：抽离真资产 + 正式退役** —— 将上述 3 项真资产浓缩并入 `goal-loop/references/host-adapters.md` 与 `dual-round-review/references/failure-modes-catalog.md`，物理移除 `skills/agy-delegation-workflow/` 与全部公开注册面，将现役公共技能集由 7 个收敛为 6 个。
* **方案 B（未采纳）：最小止血保留为 `agy` 后端插件** —— 清理硬编码模型与前端私有 props、升级脚本加 `--sandbox`，但未解决原生子智能体时代 **0/28 实战使用率** 的闲置维护税。
* **方案 C（未采纳）：重构为厂商中立多 CLI 派发器** —— 同时封装 `agy` / `claude -p` / `codex exec` + worktree，投入巨大且直接与 `agent-orchestrator` / `ccmanager` / `ACP` / 官方 SDK 重复造轮子。

---

## 3. 最终决策与裁决 (Decision Outcome)

选定 **方案 A**：

1. **真资产无损沉淀**：
   - 将 **Silent Landing 判别 SOP** 与 **Direct-Write 四条止损准则**并入 `skills/goal-loop/references/host-adapters.md`（使任何外部无头 CLI 后端都能直接复用，不再绑死单一厂商）；更新 `host-adapters.md` 与 `stage-progression-protocol.md` 消除对 `agy-delegation-workflow` 的依赖；
   - 将抽象后的**虚假合规检查要点**（编造组件/库 API 属性、硬编码绕过规范、隐蔽放宽共享类型）并入 `skills/dual-round-review/references/failure-modes-catalog.md` 模式 2 与模式 4。
2. **物理退役与全注册面同步**：
   - 通过 `git rm` 移除 `skills/agy-delegation-workflow/` 全部 8 个源文件并移除本地软链 `.agents/skills/agy-delegation-workflow`；
   - 同步更新全部 5 处哨兵注册面（`test_cross_skill_links.py`、`cross-skill-link-policy.json`、`cr-agent-arsenal.json`、`README.md`、`docs/index.md`）及 `install-skills.md` / `quick-start.md` / 各技能内联白名单，确保 `test_skill_surface_sentinels.py`（C-01/C-05/C-07）全绿。
3. **历史文档状态流转**：
   - `docs/explanation/architecture/agy-delegation-workflow-design.md` 流转为 `Superseded`（`取代于: ../decisions/0004-retire-agy-delegation-workflow.md`），保留历史溯源。

### 3.1 积极后果 (Positive Consequences)

* 净减 1,174 行 / 58.7 KB 零实战消费维护债（含 490 行脆弱测试）与 14 处过时模型硬编码；
* 彻底消除全仓「双委派 SSOT」冲突，收敛到 `goal-loop/references/host-adapters.md` 单一宿主无关后端规程；
* 3 项经实战检验的底层经验得以在现役核心技能中继续发挥作用。

### 3.2 消极后果与已知代价 (Negative Consequences / Trade-offs)

* 极少数在非 Antigravity 宿主或离线 CI 中需要直接调 `agy -p` 的场景，改由用户直接使用 `agy` 1.5+ 原生 CLI（`--add-dir` / `--sandbox` / `--output-format stream-json`）或官方 Python SDK `google-antigravity`，不再提供仓库封装脚本。

---

## 4. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 修订描述 |
| :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 正式裁决退役 `agy-delegation-workflow` 技能，将 Silent Landing / Direct-Write / 虚假合规检查三项核心资产沉淀至 `goal-loop` 与 `dual-round-review` |
