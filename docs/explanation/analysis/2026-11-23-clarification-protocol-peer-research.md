# AI 编码代理需求澄清与交互收敛同类工程及学术前沿深度调研报告

> **文档控制信息**
> - **文档标识**: ANA-CLARIFICATION-PEERS-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **调研动机**: 本仓库 `clarification-protocol` 试图把需求澄清规训为包含术语先行、提问排序、决策台账、三项收敛自检、三层熔断预算与离线脚本的完整流程。随着 2025–2026 年 `github/spec-kit`、Matt Pocock `grilling`、`obra/superpowers` `brainstorming`、`OpenSpec` 以及宿主原生 `Plan Mode` / `AskUserQuestion` 成熟，本次调研一手梳理业界标杆与最新顶会实证研究，为配套评估报告 [2026-11-23-clarification-protocol-architecture-evaluation.md](./2026-11-23-clarification-protocol-architecture-evaluation.md) 建立参照基准。
> - **证据分级**: 【A】一手（2026-11-23 `gh api` 实拉上游源码、本机已安装 `brainstorming` / `grilling` 一手源码）｜【B】二手转引（学术论文与官方平台特性综合摘要）｜【C】基于一手证据的工程规律提炼

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 4 大高星澄清/探索标杆（`spec-kit` 151k★、`superpowers`、`mattpocock/skills` 331k★、`OpenSpec` 75.5k★）一手源码剖析、宿主原生原语替代效应分析与 4 项 2024–2026 顶会学术实证综述 |

---

## 0. 摘要（TL;DR）

**一句话结论**：2025–2026 年学术界与工程界共同证实了需求澄清的「双重铁律」——**不问必翻车（>60% 场景 LLM 面对歧义仍盲目写码），但问得太碎或表太重同样翻车（触发人类审查疲劳倒 U 曲线与低影响细节淹没主干）**。头部工程实践的收敛形态是：**先读代码自查事实不问人 + 术语与高影响决策优先 + 单题/分层推荐选项 + 决策直接原地回写主 Spec（零独立重型台账校验脚本）**。

六条一级结论：

1. **学术实证强力背书「术语先行 + 按影响筛问 + 显式默认假设」的认知纪律**。*HumanEvalComm*（ACM TOSEM 2025）证实 >60% 场景代码模型面对有缺陷规格仍盲目编码【B】；*ClarEval*（2026）将**术语歧义**单列为与目标缺失、前提缺失并列的三大独立歧义源【B】；*ClarifyCodeBench*（2026）揭示了**能力解耦**（写码强 ≠ 澄清强）与**多歧义天花板**（歧义一多，模型就把提问轮次浪费在无关紧要的微末细节上）【B】。
2. **过度形式化的门禁与多轮盘问触发「人类监督疲劳倒 U 曲线」**。*Oversight Has a Capacity*（2025–2026）实证表明：将人类审阅者视为有限且会疲劳的资源时，高频低价值打断与繁复表格核对会直接诱发审阅疲劳，反而令真正关键的架构误判被草率放行【B】。
3. **`github/spec-kit`（151.1k★）用「≤5 题硬上限 + 原地回写主 Spec」解决收敛失控**。一手读取其 `templates/commands/clarify.md`（291 行）：内部扫描 10 类歧义并按 `(Impact × Uncertainty)` 选 Top 5，单题串行给出 `**Recommended:**` 与短答选项，**用户每答一题立即原地替换主 Spec 模糊句并追加 `## Clarifications` 记录**，无需额外建独立台账或跑正则脚本【A】。
4. **`mattpocock/skills`（330.8k★）把澄清压到极致 28 行，但也暴露了「不落盘会稀释」的盲区**。其 `grilling`（28 行）以「设计树 + Frontier 依赖批问 + **凡代码库可自查的事实绝不问人**」闻名；它刻意拒绝硬题数上限与宿主特定 UI 绑定，但配套 `grill-with-docs` 坦承：除了实时进 `GLOSSARY.md` 和 `docs/adr/` 的条目外，**精确负面约束与默认数值若只留在对话中，在下游实现极易被稀释**【A】。
5. **`obra/superpowers` `brainstorming` 与 `OpenSpec` 均坚持「按复杂度缩放仪式感」**。`brainstorming`（250 行）先将任务分为 `Spike / Bounded / Architectural` 三档（Spike 仅需 2–3 句共识，绝不套重模板）【A】；`Fission-AI/OpenSpec`（75.5k★）更把探索阶段降维为零落盘只读的 `/opsx:explore`，仅在用户点头后再一次性 `/opsx:propose` 建档【A】。
6. **宿主原生原语已接管交互排版，技能层只应聚焦「认知决策」**。Claude Code 的 `Plan Mode` + `AskUserQuestion` 与 Antigravity 的 `ask_question` 已在协议层内建结构化单/多选 UI、推荐前缀与超时机制【A/B】；公共技能不再需要大篇幅教模型怎么画选项表，真正不可替代的是 **Ask vs Lookup vs Default-Assumption 的三向判据、术语前置拦截与极简留痕**。

---

## 1. 四大高星工程体系一手源码横评（2026-11-23 实测【A】）

| 对比维度 | `github/spec-kit`<br>`/speckit.clarify` (151.1k★) | `obra/superpowers`<br>`brainstorming` (324.4k★) | `mattpocock/skills`<br>`grilling` (330.8k★) | `Fission-AI/OpenSpec`<br>`/opsx:explore` (75.5k★) |
| :--- | :--- | :--- | :--- | :--- |
| **体量与载体** | 1 份命令提示词 `clarify.md`（291 行）+ 1 个防偷懒测试 | 1 份 `SKILL.md`（250 行） | **`SKILL.md` 仅 28 行**（`grill-with-docs` 组合领域建模） | 内置只读探索命令，无笨重表单 |
| **排序与提问边界** | 内部 10 维扫描（含 Terminology），按 `Impact × Uncertainty` 挑 Top 5；禁把 NFR 推给 Plan | 按 `Spike / Bounded / Architectural` 分级缩放；聚焦 purpose / constraints / success | 设计树 + **Frontier 依赖层批问**；**「查代码能得到的事实绝不问人」** | 先读代码库定位根因，再呈 2–3 方案对比权衡 |
| **题数预算策略** | **硬上限：全会话 ≤ 5 题**，超限高影响项标 Deferred | 少而精、一次一题，无硬数 | **显式拒绝硬上限**（防机械截断真正模糊的需求，也警示“问 200 题”反例） | 零强制轮次，收敛即转 `propose` |
| **交互方式** | 单题串行 + 1 句 Why it matters + `**Recommended:**` + 允许回 `yes` | 单题串行，多选优先 | 按 Frontier 批问 + `➡️` 推荐项；拒绝绑死单一宿主 UI 工具 | 自然对话 + 架构图；点头后建档 |
| **决策落盘方式** | **原地增量回写主 Spec**：写 `- Q → A` 并**立即替换正文模糊处** | Architectural 写 `specs/...-design.md` + 4 项内联自查 | 术语→`GLOSSARY.md`；硬决策→`ADR`；其余留对话（已知易被下游稀释） | 探索期零强制落盘，点头后一次性生成 `proposal.md` + delta specs |
| **离线校验脚本** | 无独立台账正则校验脚本 | 无 | 无 | 不校验对话台账 |

---

## 2. 2024–2026 学术前沿实证证据汇总【B】

| 论文 / 研究 | 规模与核心实测发现 | 对澄清技能设计的直接指导【C】 |
| :--- | :--- | :--- |
| **HumanEvalComm**<br>（Wu & Fard, *ACM TOSEM* 2025, arXiv:2406.00215） | 在 762 道含不一致、歧义或不完整信息的编码任务中，前沿 Code LLM **超过 60% 的响应仍盲目直接写代码而非主动提问** | 证明「默认不澄清直接开工」是 LLM 固有顽疾，必须设立显式澄清触发门禁 |
| **ClarEval**<br>（Li, Wu & Chang, 2026, arXiv:2603.00187） | 评测 11 个前沿代码智能体，把交互歧义拆分为 **missing goals / missing premises / ambiguous terminology（术语歧义）** 三类独立维度，指出写码强模型普遍缺乏策略性沟通能力 | 直接为「**术语先行**」提供一等学术背书——术语歧义不会随需求问答自动消失，必须前置拦截 |
| **ClarifyCodeBench**<br>（Fang et al., 2026, arXiv:2607.00711） | 419 道歧义任务，提出轮次折扣关键提问率 **TKQR** 与最优轮次遵从度 **ORA**；揭示三大现象：① **能力解耦**（静态写码强 ≠ 澄清强）；② **推理悖论**（单靠拉长 CoT 对主动发现歧义收益微弱）；③ **多歧义天花板**（歧义一多，模型频繁把轮次浪费在低影响微末细节上） | 强力验证「**按影响度排序 + 低影响直转显式默认假设**」的必要性；同时表明仅靠“显式化思考块”无法替代结构化澄清纪律 |
| **SAGE-Agent / CIGAsk / *Oversight Has a Capacity***（2025–2026） | 前两者倡导按期望信息价值（EVPI）动态抉择「自查工具 vs 问用户 vs 弃权」；后者建模人类审阅疲劳，证明系统真实安全性随打断/门禁频率呈**倒 U 型曲线** | 警示任何强制填满多张重型表格、要求每轮单开自检回合的设计，都会把人类推向倒 U 曲线右侧的疲劳区，适得其反 |

---

## 3. 宿主原生原语演进与澄清技能的真边界【A/B/C】

在 Claude Code `Plan Mode` + `AskUserQuestion` 与 Antigravity `ask_question` 普及之后，交互式提问的「UI 与协议层」已被宿主接管。澄清类公共技能唯一不可替代的真正边界收敛为四条极薄认知律：
1. **Lookup Before Asking（先自查事实，只问人类决策）**：凡读代码、查文档、看配置能确定的事实，严禁打扰用户；
2. **Terminology First（易歧义术语前置对齐）**：只对真正容易产生理解分叉的核心词对齐，禁扩为大词典；
3. **Impact-Gated Asking + Explicit Defaults（高影响提问、低影响转默认假设、软题数控制）**：把有限人类注意力留给不可逆与高杠杆分叉；
4. **Lightweight In-Place Persistence（轻量原地留痕，拒绝重型多表与正则门禁）**：用极简 1 张单表或直接回写主文档的方式留存决策与默认假设，既解决 `grill-with-docs` 的“下游稀释”痛点，又不触发审阅疲劳。

---

## 4. 下篇衔接与参考来源

基于以上标杆与学术实证，配套评估报告 **[2026-11-23-clarification-protocol-architecture-evaluation.md](./2026-11-23-clarification-protocol-architecture-evaluation.md)** 将全面体检 `skills/clarification-protocol/`（8 文件 / 48.0 KB），揭示其 8 篇真实 RFC **0/8** 校验通过、8 类脚本缺陷、L72 空指针预算与 Split-Brain 双模板冲突，并给出精准瘦身方案。

### 主要参考来源

- **一手开源与本机源码实测（2026-11-23）【A】**：`github/spec-kit`（https://github.com/github/spec-kit ，`templates/commands/clarify.md`）、`obra/superpowers`（本地 `.agents/skills/brainstorming/SKILL.md`）、`mattpocock/skills`（https://github.com/mattpocock/skills ，本地 `.agents/skills/grilling/SKILL.md`）、`Fission-AI/OpenSpec`（https://github.com/Fission-AI/OpenSpec ）。
- **学术实证与平台特性摘要【B】**：Wu & Fard *HumanEvalComm*（arXiv:2406.00215 / *ACM TOSEM* 2025）；Li, Wu & Chang *ClarEval*（arXiv:2603.00187, 2026）；Fang et al. *ClarifyCodeBench*（arXiv:2607.00711, 2026）；*Oversight Has a Capacity* / SAGE-Agent / CIGAsk（2025–2026）；Claude Code `Plan Mode` & `AskUserQuestion` 官方文档摘要。
