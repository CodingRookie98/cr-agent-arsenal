# LLM-WIKI 社区实现全景与工程难点深度调研（兼 doc-governance 对照审计）

> **文档控制信息**
> - **文档标识**: ANA-LLM-WIKI-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-21
> - **文档所有者**: 核心架构组
> - **调研动机**: 本仓库 `doc-governance` 被定位为 LLM-WIKI 的一种实现，但「LLM-WIKI」在社区中至少有四种互不相同的所指（模式 / 接口 / 产品 / 记忆层），本仓库此前未做过该谱系的横向对标；本次调研回答三个问题：别人怎么实现、撞到哪些墙、我们缺哪一块
> - **证据分级**: 【A】一手（规范原文 / 论文摘要或正文 / 官方文档 / 源码或 API 实测）｜【B】二手转引（报道、搜索引擎摘要、他人综述，未读原文）｜【C】观点与厂商自测（博客、白皮书、产品页，存在利益相关性）

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-21 | DSH AI Agent | 王辉 | 初版：基于 4 路并行检索（标准接口 / 仓库生成 / 智能体记忆 / 中文落地）与 12 篇一手论文，收敛六条实现路线、十类工程难点与十二维对照审计；含 6 项「无权威来源」诚实标注 |

---

## 0. 摘要（TL;DR）

**一句话结论**：LLM-WIKI 不是一个产品形态，而是一条**把知识从「查询时重算」搬到「写入时编译」**的工程路线。它换来的是一次编译、多次复用的复利，代价是**陈旧、错误与成本都会同时被固化**——社区所有技术难点，都可以还原为「编译期质量」与「查询期新鲜度」之间的这条张力线。

九条一级结论：

1. **模式的正典是 Karpathy 的两份文本，不是某个项目。** 2026-04-02 的推文给出规模锚点（约 100 篇源、约 40 万字仍可用索引文件替代向量库）【A】，2026-04-04 的 gist 把它抽象成三层（不可变 `raw/`、LLM 独占写入的 `wiki/`、约束行为的 schema）与三操作（Ingest / Query / Lint）【A】。此后 48 小时内涌现的十余个仓库，全部是对这份「想法文件」的具体化【A】。
2. **社区实现分成六条路线，彼此不是替代关系而是不同层。** 规范驱动纯文件、文件+索引/搜索、生成式仓库 wiki、知识图谱、检索即答案、确定性编译器。**选错层的典型症状是：用 RAG 的工程量去解决维护问题，或用 LLM 的算力去解决本可用正则解决的排字问题。**
3. **「编译一次」的经济学没有被算清，且现有唯一的前注册对照实验给出的是坏消息**：在同一 13 问 / 24 篇论文的语料上，wiki 的跨文献综合更好，但**每查询 token 消耗约为向量 RAG 的 21 倍，且不存在盈亏平衡点**【A】。
4. **最大的技术难点不是构建，而是「保持最新」与「知道何时可信」。** 生产级实测：模型对「文档被改坏」的检出率 67–94%、对「文档与实现明确矛盾」50–91%，但当**只有代码变了而文档未动**时，检出率骤降 21–43 个百分点【A】——这恰好是仓库文档最常见的腐化形态。
5. **自动 lint 的召回率天花板约五成。** 六周、118 条 agent 失败记录的实证中，陈旧文档是最大失败类（48/118）；一次月度 LLM 文档审计只找到约 50% 的已知漂移，但**至少 93% 的产出是对的**【A】。这意味着 lint 只能当「高精度抽样器」，不能当「完备性门禁」。
6. **结构门禁与语义真值必须分开两层。** 断链、控制头、修订窗口这类检查可以用确定性脚本做到零误报（本仓库已达成的部分）；而「内容是否仍然为真」目前没有可靠自动化——最好的自动文档 agent 在 DoGBench 上也只有 47.3/100【A】。
7. **面向智能体的「标准接口层」已经赢在 MCP，而不是 llms.txt。** llms.txt 的采用率被各家测成 5%–28% 的不同数字，且 97% 的文件在整月内零请求【A/B】；Google Search 官方明确表示忽略它【A】。真正常被消费的是**按页 `.md` 与文档 MCP server**（Context7 65k★、GitMCP 8.5k★、Stripe/Vercel/Cloudflare 官方 MCP）【A】。
8. **本仓库的 `doc-governance` 是「模式层 + 接口层」的半个实现**：它把机器地图做成了逐字节门禁（强于社区绝大多数实践），把生命周期与归档做成了强制流程；但它**没有编译管线**（无源摄取、无增量编译、无矛盾综合），也**没有语义体检、漂移检测与检索层**。
9. **可落地的演进方向不是「上一个向量库」，而是三件事**：控制头加「来源指纹 + 代码锚点」、健康分中拆出「新鲜度/可回答性」两个真值维度、把 `llms.txt` 从「全集清单」改成「受限预算的分层入口」并配消费端烟测。

### 六条路线速查

| 路线 | 一句话骨架 | 代表实现 | 适合 | 主要代价 |
| :--- | :--- | :--- | :--- | :--- |
| R1 规范驱动纯文件 | schema 约束 + 纯 md + 索引/日志 | Karpathy gist、hermes llm-wiki 技能、**本仓库 doc-governance** | 单写者、可审计、规模 ≤ 数百页 | 无检索、无漂移检测 |
| R2 文件 + 索引/搜索 | 文件仍为真相源，外挂 BM25/向量/重排 | nashsu/llm_wiki（21.8k★）、qmd（31k★） | 个人知识库、需低延迟检索 | 索引与文件双写一致性 |
| R3 生成式仓库 wiki | 代码 → 分块 → 生成页面树 + 问答 | DeepWiki、Google Code Wiki、deepwiki-open（18.5k★） | 陌生代码库理解 | 幻觉、不可 opt-out、整仓重建成本 |
| R4 知识图谱 | 实体/关系/时效 + 社区发现 | GraphRAG、LightRAG、Zep Graphiti、4-signal 模型 | 跨源、冲突多、要溯源 | 建图成本、抽取误差累积 |
| R5 检索即答案 | 不做编译，按页 md / MCP 现取 | Context7、GitMCP、llms.txt 托管 | 对外文档、频繁变更 | 不解决维护，只加快错误 |
| R6 确定性编译器 | 能脚本化的绝不交给 LLM | 纯 Python 编译器实践、Vale/lychee/Swimm | 结构、链接、风格、耦合 | 无法产生综合与解释 |

### 成熟度阶梯（用于自评与路线图）

| 级别 | 判据 | 本仓库现状 |
| :--- | :--- | :--- |
| L0 静态文档 | 有人写、有人读 | — |
| L1 结构门禁 | 断链/锚点/命名/元数据可机械校验 | ✅ 已达成（含 `.txt` 扫描域） |
| L2 机器入口 | 生成式机器地图 + 目录索引 + 生命周期 | ✅ 已达成（`llms.txt` 逐字节门禁） |
| L3 真值体检 | 漂移检测、矛盾登记、新鲜度评分 | ❌ 未建 |
| L4 闭环写入 | 变更→影响面→起草→owner 放行→评测 | ❌ 未建 |

---


## 1. 研究范围与方法

### 1.1 四个能指，一个能指链

「LLM-WIKI / LLM wiki」在英文社区指 Karpathy 2026 年 4 月提出的**编译式个人知识库模式**；但在工程语境里，同一个词被用来指四件不同的事。不先拆开，后面的争论几乎全部是错位对话：

| 层 | 指的是什么 | 典型载体 | 谁写 | 失败形态 |
| :--- | :--- | :--- | :--- | :--- |
| **模式层** | 写入时编译、多页互链、可 lint 的知识工件 | `raw/` + `wiki/` + schema | LLM 写，人只选题 | 陈旧、错误固化、成本 |
| **接口层** | 站点/仓库向智能体暴露的入口约定 | `/llms.txt`、`AGENTS.md`、页级 `.md`、MCP | 平台/仓库作者 | 无人消费、体积截断 |
| **产品层** | 代码库 → 结构化 wiki + 问答 | DeepWiki、Code Wiki、deepwiki-open | 系统自动 | 幻觉、无法更新/撤下 |
| **记忆层** | 智能体跨会话的持久记忆 | memory bank、Basic Memory、Graphiti/Zep | 智能体自动 | 规模、并发、权限 |

**本报告判定**：`doc-governance` 是「模式层」的治理骨架 + 「接口层」的机器入口，**不是**产品层的生成器，也**不是**记忆层的运行时。这个定位很重要——它的对标对象应当是 R1 与 R2，而不是 DeepWiki。

### 1.2 检索与取证方法

- **四路并行检索**（标准接口 / 仓库生成 / 智能体记忆 / 中文落地），各自独立取证后由主智能体交叉核验；
- **一手优先**：规范原文（llmstxt.org、agents.md）、arXiv 摘要或正文、官方文档（Cognition、Google、Cline、Cloudflare）、GitHub API 实测星数与创建时间；
- **数字复核**：所有关键数字保留样本量与统计口径（例：97% 零请求来自 Ahrefs 137,210 域名的 2026-05 日志）；
- **诚实标注**：检索工具（firecrawl）本周期额度耗尽（`402`，0/1000 credits），部分站点正文无法取得，凡仅有摘要者标【B】，凡厂商自测标【C】，凡互相矛盾者单列。

### 1.3 本次调研的边界

- **不做**：具体产品选型推荐、采购建议、对任何厂商的评测结论；
- **不做**：中文知识库产品的功能横评（只取其对「分块 / 权限 / 版本」的处理方式作为证据）；
- **已知偏差**：英文一手材料远多于中文；Reddit/HN 讨论因反爬只能读到桥接正文，无法量化「社区共识」，只能引用具体句子。

---

## 2. 概念解剖：正典说了什么，社区又加上了什么

### 2.1 正典的四个断言

Karpathy 的 gist 只有约 12 KB，但它把整条路线的因果关系写死了【A】：

1. **对手是 RAG 的「无累积」**：`"the LLM is rediscovering knowledge from scratch on every question"`——RAG 每次查询都重新拼接片段，五次文献的综合永远不被保存；
2. **解法是「编译一次并保持最新」**：`"compiled once and then kept current, not re-derived on every query"`；每摄入一个源，可能牵动 10–15 个 wiki 页；
3. **写入权归 LLM**：`"You never (or rarely) write the wiki yourself"`；人的职责是选源、提问、判断意义；
4. **人机分工的隐喻**：`"Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase"`——这句隐喻解释了为什么它的治理问题与代码库同构（版本、评审、ownership、CI）。

推文里还有两个容易被忽略的**工程锚点**：索引文件在「约 100 篇源、约 40 万字」的规模上仍然够用，因此不必上向量库；以及作者自认 `"I rarely touch it directly"`——即**人类审计在实践中是缺位的**，这正是后面 Zep 攻击的靶心【A】。

### 2.2 社区在正典之上补的四层

| 补充 | 代表 | 解决的正典缺口 |
| :--- | :--- | :--- |
| **Schema 工程化**：把 schema 写成可执行技能（含标签税则、页面阈值、frontmatter 字段、置信度/争议标记） | hermes-agent `llm-wiki` 技能【A】 | gist 只说「写个 schema」，没说 schema 要约束到什么粒度 |
| **增量与幂等**：源文件 SHA256 摘要，内容未变则跳过摄入；两段式（先分析、后生成）提升质量 | nashsu/llm_wiki【A】 | 全量重编译的 token 与时间成本 |
| **检索层**：索引之外再加 tokenized 检索、CJK bigram、可选向量、图扩展、预算控制 | nashsu/llm_wiki、qmd【A】 | 「索引够用」只在个人规模成立 |
| **人类闸门**：把「LLM 起草 + owner 秒级 accept/reject」写进流程；或反向规定「仅人类可验证」 | falconer（企业实践）【C】、nvk/llm-wiki【A】 | 人类审计缺位导致错误静默固化 |

### 2.3 两个被混淆的概念

- **「second brain」不是 Karpathy 的词**：原文引用的是 Vannevar Bush 1945 年的 Memex，中文二手报道普遍改写成「第二大脑」，导致讨论滑向笔记方法论【A】；
- **「LLM-WIKI ≠ 知识库问答」**：前者产出的是**可被人阅读、可被 git 管理的工件**，后者产出的是**一次性的回答**。把两者混同，会得出「wiki 就是 RAG 的前端」这一错误结论——而这恰是第 5 节要反驳的观点之一。

---


## 3. 六条实现路线图谱

### R1 规范驱动纯文件（schema as code）

**骨架**：`raw/`（不可变）→ `wiki/`（LLM 独占写）→ `SCHEMA.md`/`CLAUDE.md`（约束）；配 `index.md`（内容目录，回答前先读它）与 `log.md`（append-only，`grep "^## \[" log.md | tail -5` 即可解析）。

**代表**：Karpathy gist 本身；hermes-agent 把模式固化成技能（三层目录、`sha256` 漂移检测、段落级 provenance 标记 `^[raw/articles/x.md]`、`confidence`/`contested` 字段、页面阈值「同一实体出现 ≥2 源才建页」「>200 行必拆」「全量 >200 页建 topic-map」）【A】；**本仓库 `doc-governance` 是这一路线的治理侧变体**：schema 变成 `GOVERNANCE.md` + 技能 SKILL，`index.md` 变成象限索引，`log.md` 的职能被 changelog + backlog 卡片 + 审查归档分走。

**关键设计**：所有约束都是**可读的文本**，因此可被 diff、可被评审、可被脚本校验——这是它能进入企业版本库的唯一原因。

**边界**：没有检索层时，规模天花板由索引长度决定（社区经验约 100 源 / 数百页）；没有漂移检测时，正确性依赖写者自觉。

### R2 文件 + 索引/搜索（file-as-source, index-as-accelerator）

**骨架**：文件仍是唯一真相源，另建可重建的派生索引（BM25 / 向量 / 图），检索结果**回填为上下文**而不是答案。

**代表**：nashsu/llm_wiki（21,800★ / 2,467 fork / 2026-04-08 创建，GitHub API 实测）【A】。其查询管线分四段：tokenized 检索（英文分词去停用词、**中文 CJK bigram**、标题命中 +10）→ 可选向量（任意 OpenAI 兼容 embedding，LanceDB 存储）→ 图扩展（4 信号：直链 ×3.0、同源 ×4.0、Adamic-Adar ×1.5、类型亲和 ×1.0，2 跳衰减）→ 预算装配（4K–1M token，**60% wiki / 20% 对话 / 5% 索引 / 15% 系统**）。官方 README 给出的消融是**召回 58.2% → 71.4%**（开启向量后）【A】。

另一代表是 qmd（31k★）：本地 markdown 搜索引擎，智能分块 ~900 token、SQLite FTS5 BM25 + 本地 GGUF 向量 + LLM 查询扩展 + RRF 融合 + 重排，同时提供 CLI 与 MCP【A】。Karpathy 的 gist 亲自点名了它——**这等于承认「索引够用」有一个规模上限**。

**关键设计**：**任何派生索引都必须可丢弃重建**。nashsu 的 README 里有一条「从既有页面重建 wiki 索引」，是这条原则的直接体现。

**边界**：索引与文件的双写一致性；CJK 场景下分词质量直接决定召回（bigram 是低成本解法，但不是最优解）。

---

### R3 生成式仓库 wiki（code → generated wiki）

**骨架**：整仓扫描 → 分层/聚类规划页面 → 逐页生成（含架构图）→ 超链接回源码符号 → 聊天问答复用同一份 wiki。

**代表与硬数据**：

| 系统 | 性质 | 关键事实 |
| :--- | :--- | :--- |
| **DeepWiki**（Cognition） | 托管闭源 | 自述已索引 **5 万+** 顶级公开仓库；把 `github.com` 换成 `deepwiki.com` 即用；配套免费 MCP（`ask_question`/`read_wiki_contents`/`read_wiki_structure`）【A】 |
| **Devin 内置 wiki** | 托管闭源 | **页面预算**：最多 30 页（企业 80 页）、总注释 ≤100 条、单条 ≤10,000 字符；用 `.devin/wiki.json` 做 steering，可指定页面层级/标题/目的；三档 effort（企业版强制 low）【A】 |
| **Google Code Wiki** | 托管闭源 | 2025-11-13 public preview；**每次代码变更后整仓重生成**；每段超链接回符号；架构/类/时序图；以整份 wiki 为上下文的 Gemini chat【A】 |
| **deepwiki-open** | 开源 MIT | 18,469★ / 2025-04-30；FastAPI + Next.js + AdalFlow RAG 管线，默认 gemini-2.5-flash + text-embedding-3-small，可切 Ollama；含 Ask 与最多 5 轮 DeepResearch【A】 |
| **CodeWiki**（论文） | 学术 | 分层分解 + 递归多 agent 动态委派 + 多模态综合；**CodeWikiBench** 上 68.79 vs DeepWiki 基线 64.06（OpenHands 229,909 LOC 上 82.45 vs 73.04）【A】 |
| **RepoAgent** | 学术开源 | 1,059★，**pre-commit 触发刷新并暂存**；最后一次 push 2024-12（已停更）【A】 |

**关键设计（值得本仓库借鉴的三条）**：

1. **页面预算**：DeepWiki 把「wiki 多大」变成显式配额（30/80 页），而不是让模型自由发挥。这是对「生成越多越贵、越难审」的工程回答；
2. **steering 文件**：`.devin/wiki.json` 让人类声明页面结构，模型只填内容——把**结构性决策留给确定性输入**；
3. **符号级回链**：每个断言可点回源码行，把「核验成本」从「读整篇」降到「点一下」。Code Wiki 与 DeepWiki 都这么做，OpenWrt 维护者的批评帖也承认这是唯一可行的减损手段【B】。

**边界与事故现场**：OpenWrt 论坛 2026-04-26 的维护者贴指出 DeepWiki 的页面「经常产生幻觉与事实错误」，且「仓库更新后不会重新生成、也无法被撤下」【B】。这暴露 R3 的结构性缺陷：**托管型 wiki 缺乏版本化与 opt-out 机制**，一旦模型改动基线，错误会长期驻留在搜索结果里。

### R4 知识图谱与时效记忆

**骨架**：把「文本」升级为「实体 + 关系 + 时间」，用图遍历替代相似度排序，用社区发现发现知识缺口。

**代表**：

- **nashsu 的 4 信号图 + Louvain 社区发现**：自动聚类后按簇内边密度算 cohesion，低于 0.15 标为「稀疏知识区」；并检出孤立页（度 ≤1）、桥节点（连接 ≥3 簇）、跨社区「意外连接」【A】。这是把「wiki 健康检查」从文字 lint 升级成了**拓扑诊断**；
- **GraphRAG / LightRAG**：社区摘要支撑全局问题、dual-level 检索与增量更新；**Graphiti（Zep）**：双时态（事件时间 + 摄入时间），按事实有效期做排序；
- **Zep 的反驳**：`"similarity is not relevance… makes the store bigger without making it memory"`；并列出 markdown 记忆的五个断裂点——规模与检索、历史与溯源、并发写、访问控制与留存、无本地上游可回查的业务事实【C，厂商立场】。

**权衡**：图路线的**建图成本与抽取误差会复利**（错一条边污染多跳检索），且图本身也需要 lint。它适合「跨源、冲突多、需溯源」的场景，不适合作为仓库文档的默认形态。

---

### R5 检索即答案（retrieval-as-answer）

**骨架**：不编译、不落盘，只把「正确的入口」暴露给智能体：页级 `.md`、文档 MCP、`llms.txt` 索引。

**代表**：Context7（65,226★，`resolve-library-id` + `query-docs` 两段式，先解析库 ID 再取版本化文档）【A】；GitMCP（8,529★，`gitmcp.io/{owner}/{repo}` 把任意仓库变文档 MCP）【A】；厂商官方 MCP：Stripe（`mcp.stripe.com`，含文档与支持文章搜索）、Vercel、Cloudflare（"2,500 endpoints in 1k tokens"）【A】。

**关键设计**：**入口即契约**。两段式（先解析 ID、再取内容）解决了「库名歧义」，版本化解决了「模型读到旧 API」。

**边界**：这一层**不解决维护**。Falconer 的判断是对的（尽管其立场相关）：`"Better retrieval over bad context delivers wrong answers more quickly"`【C】。

### R6 确定性编译器（能脚本化的绝不交给 LLM）

**骨架**：正则抽取元数据 → 图构建（词索引短语匹配）→ 分段感知重写（只改生成区块，保留手写区块）→ 固定规则 linter。

**代表**：一位工程师把 Karpathy 模式整体替换成纯 Python 编译器，理由三条——token 成本、延迟、**非确定性**（同一输入两次运行给出不同的关联判断，作为事实源不可接受）【C】；性能：100 / 1,000 / 5,000 文件的全管线耗时 171 ms / 1.8 s / 12.4 s【C】。

工业侧的同类：Vale（prose lint，6.4k★，被 Mintlify 内置进 CI）、lychee（Rust 断链检查）、Swimm（文档与代码 coupling，`swimm verify` 进 CI，商业）【A/B】。

**边界**：编译器只能保证「结构、链接、风格、耦合」，产生不了综合与解释。**它的正确用法是当 LLM 的地基，而不是替代品**——这也正是本仓库「脚本管结构、LLM 管语义」的现有分工。

### 路线选择决策树

```text
读者是外部开发者？
├─ 是 → R5（页级 .md + MCP）+ R6（链接/风格门禁）；不要自建 wiki 生成器
└─ 否 → 规模？
   ├─ ≤ 数百页、单写者 → R1（schema + 索引 + 日志），必要时加 R2
   ├─ 数千页、多写者 → R2（可重建索引）+ R6（结构门禁）+ 漂移检测
   └─ 跨工具、跨源、冲突多 → R4（图谱）+ owner 路由
需要「陌生代码库速读」→ R3（预算 + steering + 符号回链），并把产出标注为「探索辅助，非 API 真相」
```

### 六条反模式（社区反复踩过）

1. **把 `llms.txt` 当 RAG 用**：它是**入口清单**，不是知识库；堆成全集后会被截断且无人读；
2. **让 LLM 重写整个文档树**：非确定性 + 不可评审，第二次运行与第一次不一致【C】；
3. **用 lint 冒充真值**：链接全绿不等于内容还对（第 4.2 节有量化证据）；
4. **索引无限膨胀**：从 40 行涨到 600 行的 `AGENTS.md`，实测「该漏的请求照样漏，废弃写法被当成现行规范」【B】；
5. **多 agent 同写同一批文件**：文件锁在跨平台/网络盘上不可靠，git 只能合并文本不能调和语义【C】；
6. **只生成、不撤下**：托管型 wiki 缺少 opt-out 与版本化，错误会长期驻留（OpenWrt 事件）【B】。

---

## 4. 十类技术难点：现象、证据、解法与未解

### 4.1 D1 写入放大的成本经济学

**现象**：每次摄入不是「读一遍」，而是「读一遍 + 改十几页 + 更新索引与日志」。gist 自己写明单个源可牵动 10–15 页【A】。

**证据**：唯一的前注册对照实验（13 问 / 24 篇论文 / 同答案模型 / 双盲 LLM 评委）给出——wiki 每次查询约 **21 倍** token（1.65M vs 78K），且**不存在盈亏平衡点**；wiki 建库更便宜，但查询更贵【A】。社区侧的二手数据：单源摄入约 4.4 万 token、单个播客转写约 8 分钟【B】。

**社区解法**：源级 SHA256 增量跳过（nashsu）【A】；两段式摄入（先分析后生成）【A】；把确定性部分交给编译器（R6）【C】；KV-cache 优先的上下文布局（Manus：输入输出比约 100:1，缓存 token $0.30/MTok vs 未缓存 $3/MTok）【B】；预算装配（60/20/5/15）【A】。

**未解**：**没有公开的「摄入成本 → 查询收益」模型**。21 倍这个数字只在「单轮问答」口径下成立；如果把「一次编译供 N 个读者复用」计入，结论可能反转——但至今没有人做多读者、多轮的对照实验。

### 4.2 D2 漂移与时间：最大的失败类，也是最难测的

**现象**：文档腐化的主因不是「写错」，而是「代码变了，文档没动」。

**证据（最强的三条）**：

1. **TRACE 实验**（22,339 条有效响应 / 7 个模型 / 456 个 Java 方法包）：模型对「文档被注入故障」的检出率 67–94%，对「文档与实现明确矛盾」50–91%；但**当只有实现被改动、文档保持原样时，检出率下降 21–43 个百分点**【A】。换言之，**最需要检测的形态恰是检测盲区**；
2. **六周实证**（118 条失败记录）：陈旧文档是最大失败类（48/118）；一次月度 LLM 审计只找到约 **50%** 的已知漂移，但 **≥93%** 的产出是对的【A】——高精度、低召回；
3. **EMSE 大样本**：3,000+ GitHub 项目中，多数历史上至少出现过一处指向已不存在代码元素的引用【B】。

**社区解法**：DeepWiki 用 `.devin/wiki.json` 重新生成；Code Wiki 每次变更整仓重生成；RepoAgent 用 pre-commit 钩子刷新；RepoDoc 用 RepoKG + 语义影响传播做**选择性局部重生成**【A/B】；产品侧只有 Swimm 把「文档-代码耦合 + CI 校验」做成了商业能力【B】。

**未解**：**「变更 → 文档影响面」的通用工具是真空**。Vale/lychee 只覆盖风格与链接，不覆盖语义；企业普遍靠人工 matrix。

### 4.3 D3 事实固化、矛盾与「静默腐化」

**现象**：编译式 wiki 把 LLM 的判断写进了工件；一旦判断有误，错误会被后续所有引用继承。Zep 的原话：`"Git tracks line edits, not a fact's validity or source"`，且 `"Errors compound"`【C】。

**证据**：同一篇对照实验里，**claim 级引用支持度**的自动评分与两位人工标注者的一致率，首轮仅 50–54%，修正截断错误后 65–69%，仍未达到预先设定的门槛【A】。也就是说，**「这句话有没有出处」这件事本身都难以自动判定**。另一侧的上限：DoGBench（292 个真实任务，Helm/PostHog/Mautic）上最强 agent 仅 **47.3/100**，失败模式前三为任务完成缺口 45.5%、技术不准确 36.6%、概念/参考覆盖不全 32.5%【A】。

**社区解法**：`confidence`/`contested` 字段 + 争议页互链（hermes 技能）【A】；段落级 provenance 标记【A】；「冲突登记 → 路由给 owner」【C】；写作闸门（human-only verification）【A】。

**未解**：**矛盾检测没有基准**。现有做法都是「让 LLM 找矛盾」，而找矛盾的模型与写页面的模型往往是同一个——同源偏差无法排除。

### 4.4 D4 并发写与多写者语义

**现象**：一旦有两个以上 agent 或人写同一批文件，「最后写入者获胜」会静默覆盖。

**证据**：Zep 的五点里，并发与权限是最硬的两条：`"File locking is inconsistent across platforms and breaks on network filesystems"`；即使 git 化，也只是合并文本，不是调和语义【C】。另一侧，**中文落地实践**里最常被提到的正是「多人同时维护同一份制度文档，版本互相覆盖」【B】。

**社区解法**：单写者原则（Karpathy：LLM 独占写）；写者队列串行化（nashsu：持久化摄入队列，串行执行、崩溃恢复、失败重试 3 次）【A】；起草 + owner 放行（企业实践）【C】；PR 式评审 + 版本库。

**未解**：**章节级 ownership 没有通用标准**；CODEOWNERS 只到文件粒度，而 wiki 页面的冲突常发生在段落级。

### 4.5 D5 规模拐点与渐进披露的意外结论

**现象**：索引先行的设计（「回答前先读 index.md」）在规模上会被自己的索引压垮。

**证据**：一项前注册消融在**真实 709 页**的 LLM 维护 wiki 上改造渐进披露（先读目录与一行摘要，再开需要页），四个版本页面完全相同、只改访问结构；结果**质量持平**（在预设裕度内）。更关键的是预实验发现：**能力足够的 agent 根本不读大索引**——它从问题直接推断页面位置并去读那一页，因此「渐进披露省 token」的前提不成立【A】。另一侧，nashsu 的向量检索把召回从 58.2% 提到 71.4%，说明规模上来后**检索确实有用，但省的不是索引，是召回**【A】。

**社区解法**：分层 `llms.txt`（根 → `_llms/<section>.md`，Mintlify 模式，厂商自测任务快 52.1%、token 省 44.8%）【C】；索引分节/按字母分片（>50 条拆分、>200 条建 topic-map）【A】；预算装配与页数上限【A】。

**未解**：**「索引该多大」没有可移植的判据**；社区经验值（100 源 / 200 页）与模型能力、任务类型强相关。

---

### 4.6 D6 双读者冲突：给人看，还是给模型看

**现象**：同一份文档要同时满足两个读者，而两者的最优形态相反——人要好读（叙事、背景、渐进），模型要好取（短段、显式术语、稳定锚点、可预算）。

**证据**：`llms.txt` 规范 v2 明确它是「curated overview」而非全量清单，并引入 `rel="alternate" type="text/markdown"` 与 `rel="describedby"` 让页面级 md 与索引解耦【A】；实践中 `llms-full.txt` 普遍超过模型内置抓取的截断阈值（社区实测被截在 25–30k token 且不报错）【C】。本仓库 `docs/llms.txt` 在本次登记前为 **21,333 字节 / 89 条**，登记本文后为 **21,810 字节 / 90 条**（约 5–6k token），每新增一篇文档都在推高「精炼入口」的边界——这正是本节要指出的问题。

**社区解法**：**同一知识、两种渲染**（页级 `.md` + 人读 HTML）；索引与正文分离；预算装配；`## Optional` 区段标注可跳过（v2 已弱化其机械语义，仅剩约定）【A】。

**未解**：**没有「文档可读性 vs 可取性」的联合度量**；两边各自优化，容易互相破坏（给模型加锚点会让人读起来像规格书）。

### 4.7 D7 评测：连评委都不可靠

**现象**：所有人都能说「我的 wiki 更好」，没人能证明。

**证据**：

- 上述对照实验中，两位模型评委在**整体可信度**上的排序一致性 `rho = 0.04`，而在定义最具体的标准上 `rho = 0.81`【A】——**越抽象的标准越不可测**；另一项消融里「人工评分者与模型评委的一致度远低于计划要求」，最终只能以模型评委为准并做敏感性检查【A】；
- 仓库级上下文文件的对照实验（SWE-bench + 开发者自写 issue 集）得出**负结果**：提供 context file **不普遍提升**任务成功率，反而平均增加 **20%+** 推理成本；其中「指令类」内容被良好遵循，而「仓库概览类」内容（恰恰是厂商最推荐的）**没有帮助**【A】；
- 正面证据也存在：生产环境 43 天 shadow mode 的多 agent 文档维护系统处理 499 张工单、发现 92 处缺口，独立模型家族评委判定其可核验断言 **81.1%** 正确，长度可比时 **70.5%** 优于人类工程师回答（人类 23.2%）【A】。

**社区解法**：任务级 benchmark（DoGBench 含「**该不该更新**」的弃权判定，防止为改而改）；多模型家族评委 + 人工抽样；把「拒答/弃权」纳入计分。

**未解**：**wiki 作为「治理工件」的质量没有基准**。现有 benchmark 全是「生成质量」，没有「这个知识库让 agent 少走多少弯路」的度量。

### 4.8 D8 安全：入口层成了新的注入面

**现象**：任何「被 agent 自动读取的文档」都是提示注入载体。`llms.txt` 位于站点根、被约定为「给 agent 的说明」，天然是高价值靶子。

**证据**：社区与厂商安全文章记录了「在 `llms.txt` 中嵌入恶意系统提示」的供应链攻击路径【B】；更系统的研究把 llms.txt 的风险拆成 publication / fetch / model use / action 四段与五条威胁路径，并指出当前**连「是否被消费」都无法隔离测量**，遑论评估攻击面【A】。仓库侧同理：`AGENTS.md`/`SKILL.md` 可被注入「忽略既有规则」一类指令。

**社区解法**：把外部文档当**不可信数据**而非指令（本仓库 `AGENTS.md` 已写入该口径）；对入口文件做来源与变更审计；MCP 侧做权限最小化。

**未解**：**没有「文档可信度」的密码学或流程学标准**；签名、来源证明、审查戳都还停留在个别厂商实践。

### 4.9 D9 组织与治理：谁维护、谁放行、谁负责撤下

**现象**：个人模式靠一个热心的所有者运转；组织里没有这个人。

**证据**：企业化分析把模式拆成四属性——capture / link / compound / stay current——并指出四条在组织内**全部失效**：没有 `raw/` 目录（知识散在 GitHub、Slack、工单、会议）、链接要跨工具做实体消解、新内容常与旧内容**冲突**而非叠加、健康检查必须从「按需」变「常态」【C】。Zep 补充了另外两条组织级缺口：文件权限无法表达「代表某用户的 agent 只能看该用户的事实」，以及**删除没有留存策略与审计轨迹**【C】。

**社区解法**：SSOT 指定 + ownership 元数据；起草 → owner 秒级 accept/reject；漂移检测进后台循环（周级复核）【C】。

**未解**：**「知识 owner」在多数组织里不是一个真实岗位**；没有 ownership 的自动路由，四属性无法闭合。

### 4.10 D10 标准碎片：接口层还在打仗

**现象**：三种互不兼容的「给 agent 的入口」并存——`llms.txt`（约定文件）、`Accept: text/markdown`（内容协商，Cloudflare "Markdown for Agents" 已在边缘实时转换）【A】、MCP（工具调用）。`AGENTS.md` 则在仓库侧与 `CLAUDE.md`/`.cursor/rules`/`GEMINI.md` 收敛（Claude Code 可直接读 AGENTS.md；Cursor 明说「想要纯 markdown 就用 AGENTS.md」）【A】。

**证据**：采用率被各家测成互相矛盾的数字——同一时期，Top-1M 域名 14.3%、Tranco 9.0%、SE Ranking 300k 域名 10.13%、Ahrefs 客户域名 28%、Installmap 汇总区间 5–13%【A/B】；且**大量采用是插件驱动的**（Shopify 站点 78.1%，Inc 5000 中 48.3% 的文件带生成器签名）【B】。消费侧的证据更冷：**97% 的文件整月零请求**，其中 AI 检索 bot 仅占 1.1%【A】；Google Search 官方写明「忽略它们」【A】，同时 Chrome Lighthouse 又上线了 `llms.txt` 审计【A】。效果研究亦为负：SISTRIX 96,418 个 URL、43 个特征，`llms.txt` **无可测优势**，而「目录（TOC）」带来 1.7×【A】。

**社区解法**：把 `llms.txt` 降级为「锦上添花」，主投入放到**页级 md + MCP + 真文档站**；采用分层索引控制体积。

**未解**：**没有强制消费方**。这决定了它在本仓库里的定位：**它是给自家 agent 的地图，不是给搜索引擎的接口**——这一点必须写清楚，否则会被误当成 SEO 手段。

---

## 5. 争议与反面证据：必须正视的六条

本节刻意把最强反对意见集中呈现——如果一份调研只收集支持材料，它就不是调研，而是宣传。

**① 「这不过是把 RAG 换了个说法」——部分成立。** 21 倍 token、无盈亏平衡，说明在**单轮问答**口径下编译式 wiki 是净亏损【A】。反驳只在「多读者复用 + 需要跨文献综合」时才成立，而这类场景尚未被量化。**结论：不要把 wiki 当检索的替代品；它是「综合产物」的缓存。**

**② 「LLM 维护 wiki 是过度工程」——有实测支撑。** 一位工程师把整套流程换成纯 Python 编译器后，5,000 文件的处理时间是 12.4 秒，且结果确定【C】。这条批评的杀伤力不在成本，而在**非确定性**：同一输入两次运行给出不同关联判断的知识库，不能作为事实源。

**③ 「AGENTS.md 类上下文文件无效」——有对照实验。** 提供 context file 不普遍提升成功率、反而增加 20%+ 成本，且被厂商最推荐的「仓库概览」类内容无效【A】。注意边界：它评的是**仓库级上下文文件**，不能直接外推到 `llms.txt` 或知识库（后者的读者与任务不同）。

**④ 「llms.txt 是 feel-good task」——数据支持。** 97% 零请求、Google 明确忽略、SISTRIX 无可测优势、采用率的分母口径混乱且大量由插件自动生成【A/B】。**但它对「自家 agent 读自家仓库」仍然有效**——因为那里有强制消费方，这是我们与公开互联网的关键区别。

**⑤ 「错误会复利，markdown 救不了」——立场相关但论点成立。** Zep 卖图记忆，动机不纯【C】；然而它指出的五点（规模、溯源、并发、权限、无本地上游可回查的业务事实）逐条可验，且与本仓库的实际痛点高度重合。**采信论点，不采信结论（「所以要用图数据库」）。**

**⑥ 「模型自噬 / model collapse」——争议未决。** Hacker News 上「这难道不会导致模型崩溃」是最热评论之一，反方引用 2024 年以来的经验证据反驳【B】；本报告不采信任何一方，只记录该风险的存在：**当 LLM 写的内容又成为 LLM 的输入时，需要外部真值锚（代码、测试、原始来源）来阻断闭环**。

---

## 6. 对照审计：`doc-governance` 站在哪里

### 6.1 判定口径

本节不评价「做得好不好」，只回答「社区已经形成基线的那件事，我们做了没有」。判定三档：**✅ 达标/领先**、**◐ 部分**、**❌ 缺位**。审计对象为当前 `master` 上的 `docs/`（154 篇 md）与 `skills/doc-governance/`（8 个 Python 脚本 + 1 个 POSIX 兼容壳 + 7 个 references + 2 个模板 + 4 套契约测试）。

### 6.2 十二维对照表

| # | 维度 | 社区主流基线 | `doc-governance` 现状 | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 源不可变与溯源 | `raw/` 只读 + `sources[]` + 内容指纹 | 无来源字段、无指纹；仅审查归档按 SHA256 逐字冻结 | ❌ |
| 2 | 编译产物可重建 | 索引/日志由脚本生成，禁手改 | `llms.txt` 必须是生成器逐字节产物，漂移即 REJECT | ✅ 领先 |
| 3 | 结构门禁 | 断链 + 锚点 + 风格 lint | 断链/锚点/后缀，**扫描域含 `.txt`**；另有控制头版本一致性断言 | ✅ 领先 |
| 4 | 语义体检 | 矛盾标记、置信度、争议页 | 无 `contested`/`confidence`；无冲突登记 | ❌ |
| 5 | 新鲜度 / 漂移 | 变更→影响面；代码锚点；定期审计 | 仅有《变更联动触发矩阵》人工对照表，无脚本、无代码锚点 | ❌ **最大缺口** |
| 6 | 检索层 | 可重建 BM25/向量索引 + MCP | 只有机器地图，无检索；`llms.txt` 已 21 KB | ❌ |
| 7 | 写入权与并发 | 单写者 / 写者队列 / owner 路由 | 多 agent 可直写；有路径预授权，无 ownership 与串行化 | ❌ |
| 8 | 预算与渐进披露 | 索引预算、页数上限、分层 `_llms/` | 有 800 行/篇、5 条修订窗口；无读取预算与分层地图 | ◐ |
| 9 | 评测 | 任务级 benchmark + 评委一致性 | 只有结构健康分（链接 35 / 元数据 25 / 修订 20 / 孤儿 10 / 架构 10），**无真值维度** | ❌ |
| 10 | 机器入口 | `llms.txt` + 页级 md + MCP + `AGENTS.md` | `llms.txt` 有；仓库根无 `AGENTS.md`/`CLAUDE.md`；无 MCP | ◐ |
| 11 | 生命周期与归档 | RFC→结晶、backlog 冷热分区 | RFC 结晶 + backlog 卡片化 + 审查凭据归档，且**显式登记豁免的已知代价** | ✅ 领先 |
| 12 | 安全 | 外部文档视为不可信数据 | 全局 `AGENTS.md` 已写入该口径；文档侧无注入建模 | ◐ |

**一句话**：我们**领先在「结构」与「生命周期」，落后在「语义真值」与「检索」**；而后者恰好是社区过去 18 个月投入最多、也是失败案例最集中的地方。

---

## 7. 建议：把「结构领先」升级为「真值可测」

原则：**能用确定性脚本回答的问题，绝不交给 LLM；LLM 只做三件脚本做不了的事——摘要、影响面推断、矛盾发现。** 以下八项按 ROI 排序，P0 三项可在单批次内交付。

### P0-1 控制头扩三字段：来源、锚点、复核点

在现有控制信息中追加（不新增文档类型，只加字段）：

```yaml
> - **来源**: raw/…（可为空，提案/决策类必填）
> - **代码锚点**: src/api/routes.ts:120-168, src/models/user.ts
> - **复核于**: 2026-11-20 / commit a1b2c3d
```

**为什么**：这是社区唯一被反复验证有效的漂移防线——把「文档断言」钉在可变的代码位置上（DeepWiki/Code Wiki 的符号回链、Swimm 的 coupling、RepoDoc 的语义影响传播，本质都是这一件事）。
**验收**：控制头解析器能提取 `代码锚点`；`check-doc-control-sync.py` 增加「锚点路径必须存在」断言（`--strict-anchors`，默认 warn）。

### P0-2 新增 `check-doc-drift.py`：把变更矩阵脚本化

**做法**：读每个文档的 `代码锚点` → 取各文件最近一次提交时间 → 与 `复核于` 的 commit 比较 → 输出「已漂移但未复核」清单；CI 默认 `--warn`，P1 后可 `--fail`。
**为什么**：现有《变更联动触发矩阵》是**人工对照表**，而社区证明「人的自觉」不足以对抗漂移（48/118 失败类）。
**验收**：在 `docs/` 上跑出非空清单（应当命中一批真实陈旧文档）；配 3 条契约测试（锚点缺失、提交不可解析、跨象限豁免）。

### P0-3 健康分拆出两个真值维度

现权重（链接 35 / 元数据 25 / 修订 20 / 孤儿 10 / 架构 10）**全是结构指标**，满分不代表内容还对。建议改为：

| 维度 | 现权重 | 建议权重 | 新指标定义 |
| :--- | ---: | ---: | :--- |
| 链接与锚点 | 35 | 25 | 不变 |
| 元数据 | 25 | 20 | 增加「代码锚点/复核于」字段覆盖率 |
| 修订窗口 | 20 | 15 | 不变 |
| 孤儿 | 10 | 5 | 不变 |
| 架构规范 | 10 | 10 | 不变 |
| **新鲜度** | — | **15** | `check-doc-drift.py` 的未复核比例取反 |
| **可回答性** | — | **10** | 20 条 golden question 的检索命中率（人工标注） |

**为什么**：社区最贵的教训是「断链全绿 + 内容全错」；健康分若与真值无关，就会变成另一种「feel-good metric」。
**验收**：总分 100 不变；`--json` 输出新增两键；旧报告可复算（不允许拿结构分冒充真值分）。

### P1-4 把「矛盾」升为一等公民

frontmatter/控制头增加 `状态: Active | Contested | Superseded`（现有取值扩展，不新建体系）；`audit-doc-health.py` 输出**未决冲突清单**；RFC 结晶时强制标注 `Superseded-by`。
**为什么**：LLM 写的东西会静默腐化；把「有争议」写进元数据，是把审计从「读全文」降级为「看状态」。

### P1-5 分层 `llms.txt` + 消费端烟测

根 `llms.txt` 只保留**象限级入口**（目标 ≤8 KB），细则下沉 `_llms/<quadrant>.md`；并新增 `docs/AGENTS.md`（≤30 行）只做一件事：**告诉 agent「先读 llms.txt → 再读象限索引 → 再读正文」的顺序**。
**为什么**：21 KB 的地图已经等于「把目录当正文」；分层索引是社区唯一有量化收益的做法（任务快 52.1%、token 省 44.8%，厂商自测【C】）。而 `AGENTS.md` 是当前仓库侧的收敛事实标准（60k+ 项目、Linux 基金会托管【A】）。
**验收**：`generate-llms-txt.py` 增加 `--split` 模式且保持逐字节可复现；文档大小纳入门禁；用 5 条真实任务跑「无 AGENTS.md / 有 AGENTS.md」对照并留档。

### P2-6 检索层：先 BM25，后向量

SQLite FTS5 + CJK bigram（nashsu 同款最低成本方案）→ 若召回不足再引入向量；对外暴露 MCP（`docs_search` / `docs_get`）。
**为什么**：不要用向量库解决「索引太长」的问题；先证明检索缺口真实存在。

### P2-7 并发写者：软锁 + 写域声明

`docs/.owners`（象限级 owner）+ 提交模板声明写域；跨 agent 并发时以「文件级软锁 + 冲突清单」兜底。
**为什么**：Zep 的第 3、4 条断裂点（并发、权限）在这里同样成立。

### P2-8 评测闭环：20 条 golden task

固定 20 条「新 agent 入职任务」（如「实现一个新的象限索引托管命令」），度量：成功率、步数、token、以及**是否引用了过期文档**；人工与模型评委各评一次，记录一致性。
**为什么**：这是唯一能回答「我们的知识库到底有没有让人少走弯路」的办法；否则所有改进都是主观感受。

---

## 8. 中文社区与企业侧的差异化观察

中文一手材料整体弱于英文（多为二手教程与自报指标），但其关注点与英文社区**明显不同**：英文在争论「模式是否成立」，中文在解决「检索为什么不准」。这些工程细节恰好补上了模式层最缺的一段——**入库质量**。

| 观察 | 具体做法 | 对我们的意义 |
| :--- | :--- | :--- |
| **分块决定召回上限** | Dify 提供「通用/父子」双模；把固定字数切分改为「标题层级 + 500–800 字」后，某案例命中率自报 60%→80%【B】 | 文档的**标题层级本身就是检索友好度**，这是 `doc-governance` 可以直接施加影响的地方 |
| **表格与表头是重灾区** | WeKnora 默认 512 字符 / 80 重叠，并用「表头追踪」把表头前置到后续块，防止大表被切后列名丢失【A】 | 我们的 `reference/` 大量使用表格；若未来上检索，需要「表格不被腰斩」的约束 |
| **版本污染** | 中文实践里最典型的失败是「旧版本制度仍被召回」；解法是「停用旧版 + 名称带版本号 + 墓碑（tombstone）+ 索引水位」【B】 | 与 §4.2 的漂移问题同源：**召回层不解决版本，问题只是被推迟** |
| **权限必须在召回阶段过滤** | chunk 上挂 `department/project_id/classification/status/version/effective_to`，检索时动态拼 ACL；飞书官方口径「接入知识库不代表获得更高权限」【A/B】 | 我们的文档目前是「全库可读」，尚无分级需求；但审查归档的豁免机制说明**分级迟早会来** |
| **配置文件膨胀失效** | `AGENTS.md` 从 40 行涨到 600 行后「该漏的照样漏，废弃写法被当现行规范」；对策是把它降级为**路由器**，硬禁则下沉到 CI/ESLint/MCP【B】；`CLAUDE.md` 建议 ≤200 行【B】 | 直接支持 P1-5「入口文件 ≤30 行 + 只做路由」的建议 |
| **中文 token 成本** | cl100k 下 219 汉字 = 291 token（≈1.33 token/字），o200k 下降约 35%【B】 | 中文文档的「800 行上限」对应的 token 预算比英文更紧 |
| **排序被同域近邻抢位** | 问「出差住宿报销上限」首条返回「差旅餐补」，加「查询词覆盖率」加权才稳定【C】 | 若做检索，**标题与正文的术语一致性**比同义词扩展更值钱 |

**必须标注的三点**：① 「准确率 85%」「效率提升 80%」一类数字均为**自报且无评测集**，本报告不作为结论；② 小红书技术号未检索到可核实的技术长文，故不作为来源；③ `firecrawl` 额度耗尽（`402`）导致 Dify/RAGFlow 部分官方文档只能读摘要，相关参数取自第三方源码解读【B】。

---

## 9. 结论与研究空白

### 9.1 五条结论

1. **模式成立，但适用面比宣传窄。** 编译式 wiki 的真实优势是「跨源综合」与「多读者复用」；在单轮问答上它是 21 倍的净亏损【A】。判定一个场景是否值得上 LLM-WIKI，只需问：**这里是否存在「同一堆材料被反复综合」的需求**？没有，就不要编译。
2. **工程价值集中在「治理」而非「生成」。** 生成器可以一周做出来，能长期不腐化的治理体系做不出来。社区失败案例（幻觉驻留、无法撤下、索引膨胀、并发覆盖）全部发生在治理侧。
3. **确定性是稀缺资源。** 凡是能用脚本判定的（链接、锚点、控制头、修订窗口、索引生成、分类归属），交给脚本；LLM 只做摘要、影响面推断、矛盾发现。这不是保守，而是把不确定性压缩到最小可评审面积。
4. **「保持最新」是当前唯一没有通用解的问题。** 漂移检测的模型盲区（实现变了、文档没动时检出率下降 21–43 个百分点）与 lint 召回天花板（约 50%）共同说明：**只能靠「代码锚点 + 定期抽检 + owner 路由」三重冗余**，不能指望单点自动化。
5. **接口层的赢家是 MCP，不是 `llms.txt`。** `llms.txt` 该做，但定位必须是「自家 agent 的地图」；对外的知识分发应走页级 md + MCP + 真正的文档站。

### 9.2 我们最该补的三块（按缺口严重度）

| 缺口 | 严重度 | 最小可行动作 |
| :--- | :--- | :--- |
| 语义真值（无漂移/矛盾/新鲜度维度） | 🔴 高 | P0-1 + P0-2 + P0-3 |
| 检索层缺失（21 KB 地图 + 无索引） | 🟠 中 | P1-5 + P2-6 |
| 评测缺位（结构分冒充质量） | 🟠 中 | P2-8（20 条 golden task） |

### 9.3 五个公开研究空白（谁做谁有价值）

1. **多读者成本模型**：把「一次编译、N 读者、M 轮查询」纳入成本核算——现有唯一对照实验只算了单轮；
2. **矛盾检测的独立评审**：用与写作者不同模型家族的检测器，量化同源偏差；
3. **「治理工件」质量基准**：现有 benchmark 测生成质量，没有测「知识库让 agent 少走多少弯路」；
4. **章节级 ownership 与语义合并**：git 只能合并文本；段落级冲突的自动调和无人做；
5. **入口层的消费遥测**：`llms.txt`/`AGENTS.md` 被读了多少、读了哪一段，目前没有任何标准化的可观测手段。

---

## 10. 参考文献

> 分级：**[A]** 一手（规范/论文/官方文档/源码或 API 实测）｜**[B]** 二手（报道、摘要、他人综述）｜**[C]** 观点/厂商自测。

### 10.1 模式正典与社区实现

- **[A] [R1]** Karpathy, *LLM Wiki*（gist，2026-04-04）— <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- **[A] [R2]** Karpathy, *LLM Knowledge Bases*（X，2026-04-02，规模锚点 ~100 篇 / ~400K 词）— <https://x.com/karpathy/status/2039805659525644595>
- **[B] [R3]** VentureBeat 报道 — <https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an>
- **[A] [R4]** nashsu/llm_wiki（21,800★，Tauri + LanceDB + 4 信号图，召回 58.2%→71.4%）— <https://github.com/nashsu/llm_wiki>
- **[A] [R5]** hermes-agent `llm-wiki` 技能（三层 + sha256 + provenance + confidence/contested + 页面阈值）— <https://raw.githubusercontent.com/NousResearch/hermes-agent/v0.23.3/optional-skills/research/llm-wiki/SKILL.md>
- **[A] [R6]** nvk/llm-wiki（human-only verification 契约）— <https://github.com/nvk/llm-wiki>
- **[C] [R7]** Falconer, *The enterprise LLM wiki*（2026-04-28，厂商指南）— <https://falconer.com/guides/enterprise-llm-wiki-karpathy/>
- **[C] [R8]** Zep, *Markdown is not agent memory*（2026-06-23，厂商博客）— <https://www.getzep.com/blog/markdown-is-not-agent-memory>
- **[B] [R9]** Reddit r/learnmachinelearning, *The hardest part in building Karpathy's LLM wiki* — <https://www.reddit.com/r/learnmachinelearning/comments/1sq5bxl/>
- **[C] [R10]** *LLM Wikis Are Over-Engineered — I Replaced Mine With a Pure Python Compiler*（TDS）— <https://towardsdatascience.com/llm-wikis-are-over-engineered-i-replaced-mine-with-a-pure-python-compiler>

### 10.2 前注册实验与论文（本报告最强证据）

- **[A] [R11]** *Single-Round Vector RAG vs an LLM-Compiled Wiki*（arXiv:2605.18490，21× token、评委 rho=0.04/0.81、claim 支持度 50–54%→65–69%）— <https://arxiv.org/abs/2605.18490>
- **[A] [R12]** *Progressive Disclosure for LLM-Maintained Wiki Knowledge Bases*（arXiv:2607.04576，709 页真实 wiki；有能 agent 不读大索引）— <https://arxiv.org/abs/2607.04576>
- **[A] [R13]** *Evaluating AGENTS.md*（arXiv:2602.11988，SWE-bench；无提升、成本 +20%）— <https://arxiv.org/abs/2602.11988>
- **[A] [R14]** *TRACE: Measuring LLM Trust Allocation Across Conflicting Software Artifacts*（arXiv:2604.03447，实现变而文档不变时检出率降 21–43 pp）— <https://arxiv.org/abs/2604.03447>
- **[A] [R15]** *Lessons Outlive Their Failures*（arXiv:2610.32578，118 条失败记录；审计召回 ~50%、精度 ≥93%）— <https://arxiv.org/abs/2610.32578>
- **[A] [R16]** *DoGBench*（arXiv:2609.39909，292 任务；最强 agent 47.3/100；含弃权判定）— <https://arxiv.org/abs/2609.39909>
- **[A] [R17]** *CodeWiki*（arXiv:2510.24428，CodeWikiBench 68.79 vs DeepWiki 64.06）— <https://arxiv.org/abs/2510.24428>
- **[A] [R18]** *RepoAgent*（arXiv:2402.16667，pre-commit 刷新）— <https://arxiv.org/abs/2402.16667>
- **[A] [R19]** *Mind the Gap: A Deployed Multi-Agent System for Documentation Maintenance*（arXiv:2611.23142，43 天 / 499 工单 / 81.1% 断言正确）— <https://arxiv.org/abs/2611.23142>
- **[B] [R20]** Tan, Wagner, Treude, EMSE（3,000+ 项目文档-代码元素过期）— <https://doi.org/10.1007/s10664-023-10397-6>

### 10.3 生成式仓库 wiki

- **[A] [R21]** Cognition DeepWiki 博客（5 万+ 仓库）— <https://cognition.com/blog/deepwiki>
- **[A] [R22]** Devin 文档：DeepWiki 页面预算与 `.devin/wiki.json` steering — <https://docs.devin.ai/work-with-devin/deepwiki>
- **[A] [R23]** Google, *Introducing Code Wiki*（2025-11-13）— <https://developers.googleblog.com/en/introducing-code-wiki-accelerating-your-code-understanding>
- **[A] [R24]** deepwiki-open（18,469★，MIT）— <https://github.com/AsyncFuncAI/deepwiki-open>
- **[B] [R25]** OpenWrt 论坛：DeepWiki 幻觉与不可撤下 — <https://forum.openwrt.org/t/249471>

### 10.4 接口层与标准

- **[A] [R26]** llms.txt v2 规范 — <https://llmstxt.org/>
- **[A] [R27]** agents.md（60k+ 项目，Linux Foundation / Agentic AI Foundation）— <https://agents.md/>
- **[A] [R28]** Google Search, *AI optimization guide*（明确忽略 llms.txt）— <https://developers.google.com/search/docs/fundamentals/ai-optimization-guide>
- **[A] [R29]** Ahrefs, *We Analyzed 137K Sites: 97% of llms.txt Files Never Get Read* — <https://ahrefs.com/blog/llmstxt-study>
- **[A] [R30]** SISTRIX citation-worthiness 研究（96,418 URL；llms.txt 无可测优势，TOC 1.7×）— <https://www.sistrix.com/blog/citation-worthiness-study/>
- **[B] [R31]** Installmap, *llms.txt 2026 Statistics*（采用率 5–13% 的汇总口径）— <https://installmap.com/research/llms-txt-statistics>
- **[C] [R32]** Mintlify, *Scaling llms.txt*（分层索引，厂商自测快 52.1%/省 44.8%）— <https://www.mintlify.com/blog/scaling-llms-txt>
- **[A] [R33]** Cloudflare, *Markdown for Agents*（`Accept: text/markdown` 内容协商）— <https://blog.cloudflare.com/markdown-for-agents>
- **[A] [R34]** Context7（65,226★）— <https://github.com/upstash/context7>；GitMCP（8,529★）— <https://gitmcp.io>
- **[A] [R35]** Anthropic, *Effective context engineering for AI agents*（JIT 检索 / 文件系统 / 渐进披露）— <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>

### 10.5 检索与记忆相邻系统

- **[A] [R36]** qmd（31k★，BM25 + 向量 + RRF + 重排，CLI/MCP）— <https://github.com/tobi/qmd>
- **[A] [R37]** Cline Memory Bank（固定 6 文件、全量读）— <https://docs.cline.bot/prompting/cline-memory-bank>
- **[A] [R38]** Diátaxis — <https://diataxis.fr/>

### 10.6 中文来源

- **[A] [C1]** WeKnora 分块文档（512/80、表头追踪）— <https://weknora.weixin.qq.com/docs/03-features/04-chunking>
- **[A] [C2]** FastGPT OpenAPI（`pushData` ≤200 条/次、混合检索 + 重排）— <https://doc.fastgpt.io/zh-CN/openapi/dataset>
- **[A] [C3]** 飞书：知识库权限不提升原则与版本标注 — <https://feishu.cn/content/article/7667878406574328795>
- **[B] [C4]** 掘金《别再堆 AGENTS.md 了》（40→600 行失效与分层路由）— <https://juejin.cn/post/7685944661652602914>
- **[B] [C5]** 腾讯云社区案例（60 万字知识库、分块改标题层级 60%→80%）— <https://developer.cloud.tencent.com/article/2775502>
- **[B] [C6]** 阿里云：chunk 级 ACL 与版本水位/墓碑 — <https://developer.aliyun.com/article/1752786>

---

## 11. 附录：取证边界与未核实项

### 11.1 工具与可达性限制

| 限制 | 影响 | 处理 |
| :--- | :--- | :--- |
| `firecrawl` 额度 0/1000，`search`/`scrape` 返回 `402` | 无法做站点级批量抓取 | 改用 `web_search` / `web_fetch` / `read_page` / arXiv API / GitHub API |
| Reddit 直连 403 | 无法取得投票数与评论排序 | 只引用桥接正文中的原句，不宣称「社区共识」 |
| Ahrefs / SE Ranking 正文 JS 渲染 | 无法逐字核验百分比 | 标注【B】，并交叉比对多个二手来源 |
| RAGFlow 官方文档站两次超时 | 分块参数取自第三方源码解读 | 标注【B】 |
| 小红书技术号无可核实长文 | 该渠道不适合作引用源 | 以掘金/知乎/V2EX/腾讯云/阿里云替代 |

### 11.2 明确未核实（不得当作结论使用）

1. **OpenAI / Anthropic 是否在推理时消费第三方 `llms.txt`**——两家均无官方声明；本报告只证伪了 Google Search；
2. **`llms.txt` 采用率的「真实」数字**——各口径分母不同（Top-1M / Tranco / 客户域名 / Inc 5000），且插件自动生成造成虚高；
3. **Mintlify 的 52.1% / 44.8%**——厂商自测，10 站点 200 任务，无第三方复现；
4. **nashsu/llm_wiki 的 21.8k★ 增长曲线**——API 数值为真，未做时序核验，无法排除异常增长；
5. **DeepWiki 是否已修复「不重新生成 / 无法撤下」**——官方文档页为 JS 渲染，未取得现行条款；
6. **中文案例的 85% / 80% 类指标**——自报，无评测集与判定口径。

### 11.3 可复现线索

```bash
# 仓库星数与创建时间（2026-11-21 实测）
curl -sS https://api.github.com/repos/nashsu/llm_wiki | jq '.stargazers_count, .created_at'
# 论文摘要（避免网页 JS 渲染）
curl -sS "https://export.arxiv.org/api/query?id_list=2605.18490,2607.04576,2602.11988"
# 本仓库机器地图体量（用于 §4.6 的预算论证）
wc -c docs/llms.txt && grep -c '^- \[' docs/llms.txt
```

### 11.4 本文的自我限定

本文是**证据汇编 + 工程判断**，不是系统性综述（未做 PRISMA 式筛选），也不是产品评测。所有「建议」均为面向本仓库的可执行假设，落地前应按 `goal-loop` 的 P0 流程产出需求确认文档并做对照验证。若后续出现与本报告冲突的一手证据，以证据为准，并按 `doc-governance` 的修订流程升版。
