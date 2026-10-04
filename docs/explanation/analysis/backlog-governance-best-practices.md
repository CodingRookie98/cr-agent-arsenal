# AI Coding 时代的待办清单（Backlog）治理最佳实践调研

> **文档控制信息**
> - **文档标识**: ANA-BACKLOG-GOV-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-10-04
> - **文档所有者**: 核心架构组
> - **理论与实践源流**:
>   - **精益与看板**: Toyota TPS 七大浪费 / Kanban University 官方指南 / Little's Law / Atlassian Agile Coach
>   - **产品方法论**: Basecamp *Shape Up* (Ryan Singer) / Scrum Guide 2020 / Scrum.org 反模式库 / INVEST (Bill Wake)
>   - **技术债治理**: Ward Cunningham (OOPSLA '92) / Martin Fowler 技术债与债务象限
>   - **上下文工程**: Anthropic《Effective context engineering for AI agents》(2025-09-29) / Chroma *Context Rot* / Claude Code 官方最佳实践
>   - **变更与决策治理**: Keep a Changelog v1.1.0 / MADR 3.0 Supersede 机制 / Bugzilla 拒绝状态
>   - **实证与反面意见**: ETH Zurich《Evaluating AGENTS.md》(arXiv:2602.11988) / GitHub「永恒九月」/ Fowler 对 SDD 的批评 / Zep《Markdown is not agent memory》
> - **调研动机**: 现有 [backlog-specification.md](../../../skills/doc-governance/references/backlog-specification.md)（V1.0.0）只解决了条目引用键（BK 编号），未解决容量治理与生命周期出口；实测样本已膨胀至 117,325 字符并出现双写漂移

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-04 | DSH AI Agent | 王辉 | 初始化调研报告：收敛软件工程史、AI 上下文工程与社区归档三条证据线（含一手原文核实与两处「无权威来源」诚实标注），产出十四条可落地实践并映射现有规范差距 |

---

## 0. 摘要（TL;DR）

**核心结论**：backlog 臃肿不是"条目太多"，而是**职责混淆 + 缺乏出口**的必然结果。历史上（精益/看板/Shape Up）与 AI 时代（上下文工程）给出的诊断高度一致——**任何只进不出的队列，最终都会同时摧毁决策效率与阅读效率**。AI 时代新增了一条约束，但它是致命的：**backlog 的每一行都在消耗一个有限且不可再生的注意力预算**。

六条一级结论：

1. **backlog 的定义边界必须钉死为「未完成工作」**。已完成条目滞留其中，是把 changelog 的职责塞进待办列表，属职责越界而非"沉淀"。
2. **容量治理必须按「承诺边界」分层**：承诺点之后的执行区严格限长；承诺点之前的选项区不设硬上限，但必须有**丢弃规则与补货节奏**（看板官方立场，区别于"一刀切限长"的粗暴做法）。
3. **淘汰与拒绝是一等公民**。Shape Up 的"let it go"、Bugzilla 的 `WONTFIX/INVALID`、Scrum 的"完成或放弃"三者同构：**没有否决出口的清单，最终必然被否决项填满**。
4. **AI 时代 backlog 的第三重身份：智能体的外部持久化状态层**。Anthropic 明确把"创建 to-do list"与维护 `NOTES.md` 列为长程任务的核心技术，适用场景正是"有清晰里程碑的迭代开发"。
5. **AI 让"创造"变便宜，但没有让"审阅"变便宜**。GitHub 官方对"开源界永恒九月"的判断与 curl 终止漏洞赏金，共同说明积压正以**审阅队列**而非实现队列的形式膨胀。
6. **过度文档化与文档不足同样有害**。ETH Zurich 实测显示 LLM 自动生成的上下文文件**降低**任务成功率并推高推理成本；Fowler 对规格驱动开发的批评（"用大锤砸核桃"、"false sense of control"）是本次调研必须正视的反面证据。

---

## 1. 调研范围与方法

### 1.1 调研问题

| # | 问题 | 收敛口径 |
| :--- | :--- | :--- |
| Q1 | backlog 为什么会随项目推进而臃肿？ | 机制归因，而非现象描述 |
| Q2 | 历史上有哪些被验证过的容量治理机制？ | 只取有原件依据或长期社区共识者 |
| Q3 | AI Coding 引入了哪些新约束与反向证据？ | 区分"新约束""新证据"与"旧问题新表现" |
| Q4 | 现有 `doc-governance` 规范缺什么？ | 可逐条对照、可验证 |

### 1.2 三条证据线与代表性来源

| 证据线 | 覆盖内容 | 代表性一手来源 |
| :--- | :--- | :--- |
| **A. 软件工程史** | 精益浪费观、看板承诺边界、Scrum 承诺机制、Shape Up 反 backlog 立场、技术债、INVEST 粒度 | Shape Up Ch.7/Ch.14 原文、Scrum Guide 2020、Kanban University 术语表、Cunningham OOPSLA '92 |
| **B. AI 上下文工程** | 注意力预算、context rot、按需检索、结构化笔记、规格驱动 | Anthropic 官方工程博客、Chroma Context Rot、Claude Code 官方最佳实践、ETH Zurich 论文 |
| **C. 社区与工具** | 变更日志边界、拒绝状态、归档与取代、自动关闭争议 | Keep a Changelog v1.1.0、MADR 3.0、Bugzilla 字段定义、GitHub 官方维护者公告 |

### 1.3 证据分级与诚实标注

- **【原文】**：直接引自一手文献原文，可靠性最高；
- **【共识】**：多个独立来源一致、社区长期稳定实践；
- **【争议】**：存在明确反方证据或权威分歧；
- **【推断】**：由前两者推导出的本项目适用性判断，需在落地时验证。

**三处必须诚实标注的取证边界**（防止本报告被后续引用时放大）：

1. **"backlog is a form of waste" 并非 Shape Up 原文措辞**——原文是 "Backlogs are a big weight we don't need to carry" 与 "Backlogs are big time wasters too"，前者是社区转述；
2. **"icebox" 与 Shape Up 的关联未找到一手来源**——它实际来自 Basecamp 旧版工单应用，社区二手转述常误挂其名下；
3. **"AI 导致 issue backlog 加速膨胀"未找到权威一手量化数据**——可验证的一手证据集中于 PR 与漏洞报告（审阅队列）。

### 1.4 本地实证样本

调研以 `DeepResearcher/docs/project/后续优化方向汇总.md` 为真实样本做反向验证，四项实测结果构成问题定义的经验基础（详见 §6）。

---

## 2. 历史经验：六个被反复验证的机制

### 2.1 库存与等待：积压是被计入成本的在制品【共识】

TPS 七大浪费把"库存"定义为**超过最低必要量的在制品**并列为最严重形式，"等待"则指人或工作被迫排队（[Lean Enterprise Institute](https://www.lean.org/lexicon-terms/seven-wastes/)）。Little's Law 给出量化桥梁：在吞吐稳定时，**队列长度上升必然拉长等待时间**，与团队是否加班无关（[Little's law](https://en.wikipedia.org/wiki/Little%27s_law)）。

**推论**：待办积压不是"看起来乱"的美学问题，而是可计算的流动问题——它把 WIP 从观感变成需要主动治理的系统参数。

### 2.2 承诺边界：看板真正的立场是分层治理【争议】

这一点常被简化误读。Kanban University 官方术语表把**承诺点之前**的想法称为"选项（options）"，只要求它们在**补货点**按产能被筛选、从而"大量被丢弃"，**并未规定池子上限**（[Kanban University Glossary](https://kanban.university/glossary/)）。因为这正是**延迟承诺（deferred commitment）**的机制本身：若 backlog 已被整体承诺，补货就退化为排序，拉动并未真正生效（[DJAA: Proto-Replenishment](https://djaa.com/proto-replenishment/)）。

同时存在更硬的实践派主张：James Shore 描述的队列"严格限制长度"（2–7 项），理由是**短队列才能让条目不变质**（[James Shore](https://www.jamesshore.com/v2/blog/2008/kanban-systems)）。

**收敛结论（本报告采纳）**：**按承诺边界分层**——选项区设"过期规则 + 补货节奏"（软约束），承诺区设"WIP 硬上限"（硬约束）。对选项区一刀切限长会破坏延迟承诺；对承诺区不加限制则必然过载。

### 2.3 Shape Up：为什么可以没有 backlog【原文】

其论证值得逐字引用（[Shape Up Ch.7: Bets, Not Backlogs](https://basecamp.com/shapeup/2.1-chapter-07)）：

> "Backlogs are a big weight we don't need to carry. Dozens and eventually hundreds of tasks pile up that we all know we'll never have time for. The growing pile gives us a feeling like we're always behind even though we're not."

> "Backlogs are big time wasters too. The time spent constantly reviewing, grooming and organizing old ideas prevents everyone from moving forward on the timely projects that really matter right now."

四条可迁移机制：

| 机制 | 原文要点 | 出处 |
| :--- | :--- | :--- |
| **下注桌（Betting Table）** | 每周期只看向上复现的 pitch，别无其他清单要审 | [Ch.7](https://basecamp.com/shapeup/2.1-chapter-07) |
| **放掉它（let it go）** | "If we don't, we let it go. There's nothing we need to track or hold on to." | [Ch.7](https://basecamp.com/shapeup/2.1-chapter-07) |
| **appetite（时间盒）** | "Fixed time, variable scope"——先给时间数字再出设计，方向与估算相反 | [Ch.3](https://basecamp.com/shapeup/1.2-chapter-03) |
| **熔断 + 砍范围** | 到期未完成即不延期，团队必须反复锤击 scope 使其塞进时间盒 | [Ch.14](https://basecamp.com/shapeup/3.5-chapter-14) |

另有一条直接影响条目写法的粒度要求：**先垂直打通一片（integrate one slice）**，反对先铺水平分层，否则"任务全打了勾却 nothing works"（[Ch.11](https://basecamp.com/shapeup/3.2-chapter-11)）。

> **边界提醒**：Shape Up 的"零 backlog"适用于产品探索型、周期制、小团队、无外部合规约束的场景。本项目为多租户平台 + 长周期 + 审计留痕需求，**不可照搬"取消 backlog"**，但可照搬"淘汰即常态""下注前只看向上复现项""条目带成本量级"三条机制（详见 §7）。

### 2.4 Scrum：承诺机制与官方点名的反模式【共识】

Scrum Guide 2020 的 backlog 定义极其精炼，并绑定一个常被忽视的承诺：

> "The Product Backlog is an emergent, **ordered** list of what is needed to improve the product. It is the single source of work undertaken by the Scrum Team."
> "For the Product Backlog it is the **Product Goal**. […] They must **fulfill (or abandon)** one objective before taking on the next."

两条硬约束：**未排序 = 未被决策**，不应占据条目位置；**（完成 或 放弃）是二选一，"挂着"不是选项**。

Scrum.org 官方反模式库进一步点名三类腐烂形态（[Product Backlog Refinement Anti-Patterns](https://www.scrum.org/resources/blog/product-backlog-refinement-anti-patterns)）：

- **囤积 / 超大 backlog（hoard/oversized backlogs）** 本身即浪费，官方建议**只维护未来 3–6 个迭代的近期待办**；
- 把 refinement 当作"写作任务"或"过度依赖 AI"，跳过了关于 why/what 的协作对话；
- **在前期定义并估算每一条**，与"按需精化（refined as needed）"背道而驰。

同时，官方明确指出一个易被误用的概念："Sprint Review 上拒绝某条目"是谬误——未完成不是被拒绝，而是**未达 Definition of Done，会立即转化为技术债并侵入下个 Sprint**（[The Fallacy of the Rejected Backlog Item](https://www.scrum.org/resources/blog/fallacy-rejected-backlog-item)）。

### 2.5 技术债：本金、利息与"不该混池"【原文 + 推断】

Cunningham 在 OOPSLA '92 的原始隐喻（[c2.com](https://c2.com/doc/oopsla92.html)）：

> "Shipping first time code is like going into debt. A little debt speeds development so long as it is paid back promptly with a rewrite… **Every minute spent on not-quite-right code counts as interest on that debt.**"

Fowler 把利息具体化为"本该 4 天的改动因结构混乱变成 6 天"（[TechnicalDebt](https://martinfowler.com/bliki/TechnicalDebt.html)），并以"故意/无意 × 鲁莽/审慎"四象限区分战略权衡与事故（[TechnicalDebtQuadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html)）。

**【推断】债务项不应与功能项混池排序**：利息按"后续改动次数"累积，功能价值按"用户收益"累积，两者量纲不同，混排的结果是债永远排在后面（这正是本仓库 backlog 中大量 `P3 · 历史债` 条目的处境）。

### 2.6 拒绝与淘汰：一等公民机制【共识】

三条独立先例指向同一结论——**拒绝必须显式留痕，而非静默消失**：

| 先例 | 机制 | 出处 |
| :--- | :--- | :--- |
| Bugzilla | `WONTFIX`（确属缺陷但永不修复）/ `INVALID`（所报问题不成立），拒绝必须留下可审计理由 | [GNU Bugzilla Docs](https://www.gnu.org/software/bugzilla/docs/html/bug_fields.html) |
| Shape Up | 不中标的 pitch 不进任何中心列表，由主张者自费重新游说 | [Ch.7](https://basecamp.com/shapeup/2.1-chapter-07) |
| Scrum | "完成或放弃"；未完成即技术债，不能靠"拒绝条目"掩盖 | [Scrum.org](https://www.scrum.org/resources/blog/fallacy-rejected-backlog-item) |

**【推断】**"deferred until trigger（触发型挂账）"作为具名实践**未找到一手来源**；可用等价替代：把触发条件直接写进条目的**重新激活规则**（"当 X 指标超过 Y 或 Z 客户再次报障时复活"）。

### 2.7 条目粒度：INVEST 与垂直切片【共识】

Bill Wake 的 INVEST 标准要求好故事 Independent / Negotiable / Valuable / Estimable / Small / **Testable**，且拆分应**垂直切过各层**——因为水平层对客户没有价值（[xp123](https://xp123.com/invest-in-good-stories-and-smart-tasks/)）。这与 Shape Up 的"integrate one slice"完全同构，也与 Claude Code 官方"给 agent 一个能自己跑的验证信号"的建议同向（详见 §3.4）。

---

## 3. AI 时代的新约束与反向证据

### 3.1 注意力预算：context rot 的机制解释【原文】

Anthropic《[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)》(2025-09-29) 给出本议题最重要的一段论证：

> "Context, therefore, must be treated as **a finite resource with diminishing marginal returns**. Like humans, who have limited working memory capacity, LLMs have an **'attention budget'** that they draw on when parsing large volumes of context. Every new token introduced depletes this budget by some amount, increasing the need to carefully curate the tokens available to the LLM."

机制原因（同源）：Transformer 的注意力是 n² 成对关系，上下文越长，成对关系越被稀释；且训练分布中短序列占优。该文引用 Chroma 的 [Context Rot](https://www.trychroma.com/research/context-rot) 研究：**随上下文 token 数增加，模型准确召回信息的能力下降，且所有模型都表现出这一特性**。长上下文还存在"中间位置召回最差"的位置偏差（[Lost in the Middle, arXiv:2307.03172](https://arxiv.org/abs/2307.03172)）。

**推论（本项目最关键的一条）**：一份 117K 字符的 backlog，成本不是"读起来慢"，而是**智能体在其中的定位精度实质性下降**——文档从"参考"退化为"噪音源"。

### 3.2 创造变便宜，审阅没变便宜：AI 时代积压的加速器【原文】

GitHub 官方对"开源界永恒九月"的判断给出了本议题在 AI 时代的最强一手证据：

> "一个 PR 几秒就能生成……**创造的成本降了，但审阅的成本没有降**（the cost of creation has dropped, but the cost of review has not）"——到达速度超过审阅能力时，即使善意的提交也会压垮维护者。（[GitHub Blog](https://github.blog/open-source/maintainers/welcome-to-the-eternal-september-of-open-source-heres-what-we-plan-to-do-for-maintainers/)）

可验证的后果链：curl 于 2026-01-31 终止漏洞赏金，确认率从 >15% 跌至 <5%（[Stenberg](https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/)）；GitHub 上线"关闭 PR / 仅协作者可开 PR"设置（[Changelog](https://github.blog/changelog/2026-02-13-new-repository-settings-for-configuring-pull-request-access/)）。

**重要限定**：上述一手证据全部作用于**审阅队列**。**"AI 导致 issue backlog 加速膨胀"未找到权威一手量化来源**——这是本报告明确的取证边界。

### 3.3 状态外置：结构化笔记与"可验证的完成信号"【原文】

Anthropic 列出长程任务的三种上下文技术（compaction / structured note-taking / sub-agent），其中与本议题最相关的是第二种：

> "**Structured note-taking, or agentic memory**, is a technique where the agent regularly writes notes persisted to memory outside of the context window. […] Like Claude Code creating a to-do list, or your custom agent maintaining a `NOTES.md` file, this simple pattern allows the agent to track progress across complex tasks, maintaining critical context and dependencies that would otherwise be lost across dozens of tool calls."

适用判据：*"Note-taking excels for iterative development with clear milestones."*

Claude Code 官方最佳实践把"**给 agent 一个能自己跑的验证信号**（测试 / 构建 / 退出码 / 截图）"列为首要原则（[Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)）。

**推论**：AI 时代 backlog 的定位升级为**人机共用的外部状态层**。这提高了两项要求——**可恢复（状态显式）与可信（不得与代码现实漂移）**；并附一条禁令：**不得成为重放历史的地方**。条目的验收标准应写成"命令 + 期望输出"，而非描述性文字。

### 3.4 反向证据：过度文档化的代价【争议】

本报告必须纳入三条相反方向的证据，否则改进方案会滑向另一个极端：

| 反证 | 关键发现 | 出处 |
| :--- | :--- | :--- |
| **ETH Zurich 实证** | **LLM 自动生成**的仓库级上下文文件（AGENTS.md 类）**降低**任务成功率并推高推理成本 20%+，内容多为 README 重复；**人手写**的版本平均 +4% 收益。建议"只描述最小必要需求" | [arXiv:2602.11988](https://arxiv.org/abs/2602.11988) |
| **Claude Code 官方** | 逐行判定法："删掉它 Claude 会犯错吗？不会就砍"；并警告**臃肿的上下文文件会让 Claude 忽略你真正的指令**——"某条规则反复不被遵守，多半是文件太长、规则被淹没了" | [Best Practices](https://code.claude.com/docs/en/best-practices) |
| **Fowler 对规格驱动开发的批评** | 实测批评很重：Kiro 把一个小 bug 变成 4 个 user story、16 条验收标准（"用大锤砸核桃"）；spec-kit 产出大量重复冗长的 markdown（"我更愿意审代码而不是审这些 markdown"）；agent 最终并未遵守全部指令，给出"**false sense of control**" | [Fowler: SDD 3 tools](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) |

**推论**：**臃肿的待办清单与臃肿的上下文文件遵循同一条失败定律——规则被淹没，真正重要的条目失去注意力。**任何"结构化"改造都必须以"减少常驻体积"为验收标准，而不是以"字段更齐全"为荣。

### 3.5 反面意见：Markdown 不是 agent memory【原文】

[Zep](https://blog.getzep.com/markdown-is-not-agent-memory/) 在承认"markdown 目录在范围狭窄时是正确工具"（并点名 `CLAUDE.md` / `AGENTS.md` 场景）之后，指出三项结构性缺陷：

1. **只记录"写了什么"，不记录"替代了什么、为什么"**：事实变化时，覆盖摧毁历史，追加留下矛盾；
2. **Git 不能闭合语义缺口**：*"It tracks who changed which line and when, not what a fact was derived from or when it was true. It reconciles text, not meaning."*；
3. **文件选择本身就是检索，且随文件数增长而失效**：*"A model choosing from a list of file descriptions has less to go on as the list lengthens."*

**采纳方式**（划边界而非否定）：缺陷 1、2 ⇒ **取代关系必须显式写入**；缺陷 3 ⇒ **当条目数或分片数超过智能体可靠选择的上限时，必须引入检索层**（索引、标签过滤、脚本查询），而不是继续往同一个文件追加。

---

## 4. 最佳实践十四条

**依据**列标注来源等级；**反模式**列给出该条要消灭的具体现象。

### A. 定义与边界

| # | 实践 | 依据 | 反模式 |
| :--- | :--- | :--- | :--- |
| **A1** | **关闭即迁出（Close-as-Move）**：backlog 中不存在"已完成"状态。完成 = 移出活跃区 + 追加 changelog + 归档留痕 | Shape Up / Scrum「fulfill or abandon」/ Keep a Changelog 职责边界【共识】 | "已关闭区"常驻 backlog，越积越厚，最终占全文 38% |
| **A2** | **单一事实源分工**：backlog 记"未完成 + 验收口径"，changelog 记"已发生的值得注意的变化"（面向使用者），ADR 记"决策与取代关系"；三者互不双写 | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) "Changelogs are for humans… Don't let your friends dump git logs into changelogs"【原文】 | 同一条目在 backlog 与 changelog 各写一遍；SHA 出现在 backlog |
| **A3** | **承诺边界显式化**：文件头部声明"哪些是被承诺的、哪些只是选项"；选项区不设硬上限但设过期规则，承诺区设硬上限 | [Kanban University 术语表](https://kanban.university/glossary/) 的 options / 补货点 / 延迟承诺【共识】 | 全部条目等权混排，"承诺"与"想法"无法区分 |
| **A4** | **拒绝与淘汰是一等公民**：`Rejected / Dropped / WONTFIX / 熔断关闭` 必须落档并给出理由与取代关系，不得静默消失 | [Bugzilla](https://www.gnu.org/software/bugzilla/docs/html/bug_fields.html)【共识】 | 同一问题被反复"复活—再挂起"，三次登记同一件事 |

### B. 容量与流动

| # | 实践 | 依据 | 反模式 |
| :--- | :--- | :--- | :--- |
| **B1** | **承诺区 WIP 硬上限**：进行中区 ≤3；达上限时禁止新开工，转向清理瓶颈 | [Atlassian：WIP 限制四目标](https://www.atlassian.com/agile/kanban/wip-limits) / [Kanban Guide](https://kanban.university/kanban-guide/)【共识】 | 十余条"进行中"并列，实际无人推进 |
| **B2** | **视界上限**：只维护未来 3–6 个迭代的近期待办；更远的方向只留一行索引，不细化、不估算 | [Scrum.org 反模式库](https://www.scrum.org/resources/blog/product-backlog-refinement-anti-patterns)【原文】 | 对几年后才会做的条目做详细估算（refinement 沦为流水线） |
| **B3** | **触发型挂账独立分区**：条件不成立前不占优先级队列，只登记触发条件与重新激活规则 | 精益 pull 思想 + Shape Up「重要的事会自己回来」【推断】 | 触发型与可立即执行项混排，稀释优先级排序 |
| **B4** | **技术债独立排序**：债务不与功能项混池竞争，且标注"利息"（它拖慢多少后续改动） | [Cunningham OOPSLA '92](https://c2.com/doc/oopsla92.html) / [Fowler](https://martinfowler.com/bliki/TechnicalDebt.html)【推断】 | 债永远排在末尾，慢慢无人问津 |

### C. 表达与粒度

| # | 实践 | 依据 | 反模式 |
| :--- | :--- | :--- | :--- |
| **C1** | **条目即契约（字段化）**：ID / 状态 / 优先级 / 类型 / 触发条件 / 来源引用键 / **可验证的完成信号（命令 + 期望输出）** / 详情链接 | [Anthropic「lightweight identifiers」](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) / [Claude Code「验证信号」](https://code.claude.com/docs/en/best-practices)【原文】 | 自由文本段落，验收口径缺失，无法判定"是否真的完成" |
| **C2** | **垂直切片**：每条必须能独立交付价值，禁止"某层完成"式条目 | [INVEST](https://xp123.com/invest-in-good-stories-and-smart-tasks/) / [Shape Up Ch.11](https://basecamp.com/shapeup/3.2-chapter-11)【共识】 | "数据层完成""接口层完成"——任务全勾完却跑不起来 |
| **C3** | **摘要—详情分离（just-in-time）**：主文件只留 ≤200 字符摘要 + 详情链接，长说明外置为按需加载的子文档 | [Anthropic just-in-time 检索](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)【原文】 | 单行 4,258 字符，检索与 diff 双双失效 |

### D. 机制与门禁

| # | 实践 | 依据 | 反模式 |
| :--- | :--- | :--- | :--- |
| **D1** | **取代关系显式化（Supersede）**：条目被拆分、降级、取代、否决时，显式写明 `Superseded by / Supersedes` 指向 | [MADR 3.0](https://adr.github.io/madr/) / [Zep 缺陷 1](https://blog.getzep.com/markdown-is-not-agent-memory/)【原文】 | 关闭 = 直接删除或改词，后人无法判断"这事还作数吗" |
| **D2** | **度量换挡**：用「条目数 + 字符/字节数 + 单行长度」度量膨胀，行数退居次要 | Context Rot + 本地实测【推断】 | 用 800 行红线判定 117K 字符文档"合规" |
| **D3** | **机器可校验 + 周期清收**：门禁做格式自适应、编号全域唯一、容量上限、残留已完成检测、字段完整性；每交付批次执行一次待办清收 | Docs-as-Code + Shape Up 下注前清理【共识】 | 正则只认一种格式，另一种永远绿灯（门禁空转） |

---

## 5. 与现有 `doc-governance` 规范的差距映射

现有 [backlog-specification.md](../../../skills/doc-governance/references/backlog-specification.md)（V1.0.0，2026-09-30 落地）共六节，逐条对照十四条实践：

| 现有规范章节 | 已覆盖 | 缺口 | 对应实践 |
| :--- | :--- | :--- | :--- |
| §1 文件分区结构（进行中/计划中/已关闭） | 分区意识 | **无容量上限**；「已关闭」留在文件内 ⇒ 必然膨胀；未区分承诺区与选项区 | A1 / A3 / B1 |
| §2 条目编号规则（BK-0001，只增不复用） | 稳定引用键 | 无字段契约；无摘要长度约束；无完成信号要求 | C1 / C3 |
| §3 生命周期与关闭闭环 | 关闭动作 | 关闭 = 原地留档，**无迁出机制**；无否决分支；无视界上限 | A1 / A4 / B2 |
| §4 跨文档引用约定 | 引用键纪律 | 未定义 supersede 表达 | D1 |
| §5 门禁校验 | 有门禁意识 | 正则只匹配复选框行，**实测对表格型 backlog 命中 0 次**；不校验容量/字段 | D3 |
| §6 存量迁移指引 | 一次性补号 | 无迁移后的**首次清收**与容量基线 | D3 / B2 |

**结论**：现有规范解决的是「**可追溯性**」（条目能被稳定引用），未解决「**可持续性**」（文档规模不随项目推进而失控）。二者缺一不可，且后者是当前实际痛点。

---

## 6. 本地实证：`DeepResearcher` 样本的四项实测

样本：`DeepResearcher/docs/project/后续优化方向汇总.md`（2026-10-04 快照）

| # | 实测结果 | 对应机制 | 对应实践 |
| :--- | :--- | :--- | :--- |
| 1 | 399 行（< 800 行红线 ⇒ 判定合规），但 **117,325 字符 / 201KB**；最长单行 **4,258 字符** | 行数度量失效 | D2 / C3 |
| 2 | §2 可继续方向（41.8%）+ §5 已完成关闭（38.0%）= **近八成体积** | 无出口 + 无上限 | A1 / B1 |
| 3 | `#215/#216/#217/#222` **同时存在于 §2 活跃表与 §5 关闭表**，其中三条已标"✅已闭环"却未移出 | 关闭 = 原地改词，非迁出 | A1 / A2 / D1 |
| 4 | 修订历史 **11 条**（红线要求 ≤5），单条描述均值 **440 字符** | 交付叙事无处可去 | A2 / D3 |

**根因判定**：该文档同时承担四种职责——待办队列、已完成档案、交付叙事、修订历史。膨胀不是"写得太多"，而是**职责没有物理分离**。

**处方（四步）**：

1. §5 的 123 条已关闭条目 → `docs/project/backlog/archive/2026.md`（保留编号，追加 `Superseded by` 关系列）；
2. §2 中标注已闭环的条目 → 同上迁出，并按 A2 在 changelog 建立对应记录；
3. 触发型条目（"触发：xx 时"）→ 独立挂账区，标记触发条件与重新激活规则；
4. §2 主表长说明（均值 393 字符 / 最长 2,692 字符）→ 抽取为条目详情文档，主表只留 ≤200 字符摘要 + 链接。

---

## 7. 边界条件与反模式

本节记录**本调研明确不建议做的事**，防止最佳实践被滥用为教条。

| 反模式 | 为何被劝退 | 适用边界 |
| :--- | :--- | :--- |
| **照搬 Shape Up 的"取消 backlog"** | 本项目为多租户平台、长周期交付、含合规审计与熔断留痕需求；零 backlog 将丢失跨版本技术债与触发型挂账的可追溯性 | 仅采纳"淘汰即常态""下注前只看复现项""条目带成本量级"三条机制 |
| **对选项区一刀切限长** | 会破坏延迟承诺机制（选项的意义就在于"尚未承诺"），补货退化为排序 | 选项区用过期规则 + 补货节奏；只有承诺区用硬上限 |
| **引入数据库/图存储替代 markdown backlog**（Zep 路线） | 当前规模（单文件、条目数十级、单仓单团队）下属过度工程；Zep 自身也承认"范围狭窄时 markdown 是正确工具" | 触发条件：多仓库 / 跨团队 / 条目数千级 / 需要时效性查询 |
| **用 stale bot 式超时自动关闭** | 存在显著社区争议（GitHub 社区讨论明确要求禁止自动关闭 stale issue）：超时 ≠ 失效，误关会摧毁信任并丢失触发型条目 | 仅对"已无触发条件且长期无复现"的条目**人工**清收 |
| **由 agent 自动批量生成/复述条目** | ETH Zurich 实测：LLM 自动生成的上下文文件降低成功率并推高成本 20%+ | 条目由人或有明确证据来源的流程写入；agent 只做校验与清收辅助 |
| **为结构化而引入 YAML/JSON 生成链** | 引入构建依赖与人工编辑摩擦；实践趋势是"Markdown 人读 + 结构化子集机器读" | 触发条件：需要跨文档自动统计（待办 SLA、优先级分布报表）时再评估 |
| **把 backlog 拆成大量小文件以求"单文件不臃肿"** | 文件数增长后，"从文件列表中选择"本身成为新的失败模式（Zep 缺陷 3） | 归档分片按**时间**切（年/季）而非按主题切，并维护单一索引 |

---

## 8. 参考文献

### 8.1 一手原文（已逐条核实）

1. Ryan Singer, *Shape Up* — [Ch.7 Bets, Not Backlogs](https://basecamp.com/shapeup/2.1-chapter-07) / [Ch.11 Integrate One Slice](https://basecamp.com/shapeup/3.2-chapter-11) / [Ch.14 Circuit Breaker](https://basecamp.com/shapeup/3.5-chapter-14)（Basecamp）
2. Ken Schwaber & Jeff Sutherland, *The Scrum Guide 2020* — [scrumguides.org](https://scrumguides.org/scrum-guide.html)
3. Anthropic Applied AI, *Effective context engineering for AI agents*（2025-09-29）— [anthropic.com](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
4. Anthropic, *Claude Code Best Practices* — [code.claude.com](https://code.claude.com/docs/en/best-practices)
5. *Keep a Changelog* v1.1.0 — [keepachangelog.com](https://keepachangelog.com/en/1.1.0/)
6. Ward Cunningham, *The WyCash Portfolio Management System*（OOPSLA '92）— [c2.com](https://c2.com/doc/oopsla92.html)
7. Martin Fowler, *TechnicalDebt* / *TechnicalDebtQuadrant* — [martinfowler.com](https://martinfowler.com/bliki/TechnicalDebt.html)
8. Bill Wake, *INVEST in Good Stories, and SMART Tasks* — [xp123.com](https://xp123.com/invest-in-good-stories-and-smart-tasks/)
9. Zep, *Markdown is not agent memory* — [blog.getzep.com](https://blog.getzep.com/markdown-is-not-agent-memory/)

### 8.2 权威二手与社区实践

10. Kanban University, *Kanban Guide* / *Glossary*（options、补货点、延迟承诺）— [kanban.university](https://kanban.university/kanban-guide/)
11. Atlassian, *Working with WIP limits for kanban* — [atlassian.com](https://www.atlassian.com/agile/kanban/wip-limits)
12. Lean Enterprise Institute, *Seven Wastes*（Ohno 的库存与等待定义）— [lean.org](https://www.lean.org/lexicon-terms/seven-wastes/)
13. Scrum.org, *Product Backlog Refinement Anti-Patterns*（3–6 迭代视界）— [scrum.org](https://www.scrum.org/resources/blog/product-backlog-refinement-anti-patterns)
14. Scrum.org, *The Fallacy of the Rejected Backlog Item* — [scrum.org](https://www.scrum.org/resources/blog/fallacy-rejected-backlog-item)
15. Chroma Research, *Context Rot* — [trychroma.com](https://www.trychroma.com/research/context-rot)
16. Liu et al., *Lost in the Middle*（arXiv:2307.03172）— [arxiv.org](https://arxiv.org/abs/2307.03172)
17. Gloaguen et al. (ETH Zurich), *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?*（arXiv:2602.11988, v3）— [arxiv.org](https://arxiv.org/abs/2602.11988)
18. GitHub, *Welcome to the Eternal September of Open Source* — [github.blog](https://github.blog/open-source/maintainers/welcome-to-the-eternal-september-of-open-source-heres-what-we-plan-to-do-for-maintainers/)
19. Daniel Stenberg, *The End of the curl Bug Bounty*（2026-01-26）— [haxx.se](https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/)
20. Martin Fowler, *Exploring Gen AI: SDD 3 tools*（对规格驱动开发的批评）— [martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
21. MADR 3.0 决策记录规范 — [adr.github.io/madr](https://adr.github.io/madr/)
22. GNU Bugzilla, *Bug Fields*（WONTFIX / INVALID 定义）— [gnu.org](https://www.gnu.org/software/bugzilla/docs/html/bug_fields.html)

### 8.3 仓库内相关文档

23. [doc-governance 技能架构设计书](../architecture/doc-governance-design.md)（§2.4 双受众公理与总纲-子册拓扑）
24. [backlog-specification.md](../../../skills/doc-governance/references/backlog-specification.md)（V1.0.0，待按本报告升级）
25. [GOVERNANCE.md](../../GOVERNANCE.md)（本仓库知识库治理规程 V1.4.0）
