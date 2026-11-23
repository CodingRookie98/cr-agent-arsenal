# Docs-as-Code 与 Agent-First 仓库文档治理同类工程增量调研报告

> **文档控制信息**
> - **文档标识**: ANA-DOC-GOVERNANCE-PEERS-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **调研动机与衔接声明**: 本仓库已有 58 KB 的 [llm-wiki-implementation-research.md](./llm-wiki-implementation-research.md)（深度剖析 Karpathy LLM-WIKI 正典、六条编译式知识库路线与 `llms.txt` 接口层）。为避免重复，本报告作为**增量专题调研**，聚焦其未展开的三大工程谱系：**① 成熟开源 Docs-as-Code 确定性工具链；② Code-to-Doc 防腐与 Agent-First 仓库文档范式；③ 头部 Agent Skills 仓库如何划分「通用文档技能」与「单仓 CI 治理套件」的职责边界**，为配套评估报告 [2026-11-23-doc-governance-architecture-evaluation.md](./2026-11-23-doc-governance-architecture-evaluation.md) 提供外部参照系。
> - **证据分级**: 【A】一手（2026-11-23 `gh api` 实测星数/活跃度与源码精读）｜【B】二手转引（官方文档、技术评论与学术论文综合摘要）｜【C】基于一手证据的行业提炼与架构研判

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：衔接既有 LLM-WIKI 调研，增量完成 10 个 Docs-as-Code/Agent Skills 一手标杆调研（`lychee`/`vale`/`markdownlint`/`madr`/`adr-tools`/`addyosmani`/`anthropics` 等）、Diátaxis 中小仓反噬评述、OpenAI/Anthropic/ETH Zurich Agent-First 文档实证与公共技能边界法则 |

---

## 0. 摘要（TL;DR）

**一句话结论**：2025–2026 年的工业界在仓库文档治理上形成了极清晰的「两分法」——**通用 Agent 文档技能极度克制（10–20 KB，Convention-First 优先适配目标仓既有约定），确定性校验交给成熟开源 CLI（`lychee` / `markdownlint` / `vale`），文档防腐转向异步园丁（Doc-Gardening）与 Git 拓扑比较，而非把上万行私有 CI 门禁和项目管理工具硬塞进公共 Skill**。

六条一级结论：

1. **头部 Agent Skills 对文档技能的定位都是「薄规范 + 零寄生」**。`addyosmani/agent-skills`（119.9k★）的 `documentation-and-adrs` 仅 **1 文件 12.3 KB（零脚本）**，第一条原则即是 *Match the existing convention first*，并把待办拆分严格独立为 `planning-and-task-breakdown`【A】；`anthropics/skills`（199.2k★）的 `doc-coauthoring` 仅 **1 文件 15.4 KB（零脚本）**【A】。
2. **Docs-as-Code 确定性检查早有零自维护成本的成熟开源工业基线**。`lycheeverse/lychee`（4.2k★ Rust 异步断链器，支持本地相对路径 + `#anchor` + 外部 URL + `--offline`）、`DavidAnson/markdownlint`（6.4k★，内建 `MD013` 行宽/层级检查）、`vale-cli/vale`（6.4k★，声明式 YAML 术语与风格检查）、`adr/madr`（2.7k★，明确不要求 ADR 写版本号与修订历史表）【A】。在通用技能里重复手写数千行正则解析器属于高成本重造轮子。
3. **Diátaxis 是极佳的「写作心智透镜」，但照搬为中小仓的「强制物理目录蓝图」会产生显著反噬**。技术写作社区反复指出：对中小型工程仓库强行按四象限拆物理目录并给缺失象限扣分，会造成人为碎片化（Click-Around Penalty）、空象限凑数与更新门槛激增；中小仓更适合「Flat + 清晰入口 + 轻量 `docs/`」，把 Diátaxis 作为单篇内容纯度边界【B/C】。
4. **Code-to-Doc 防腐正在告别「同步 pre-commit 手钉 Commit SHA」模式**。`addyosmani/agent-skills` 仅用 **6 行 `git merge-base --is-ancestor`** 通过 Git 拓扑祖先关系判定文档新鲜度，天然兼容同提交【A】；OpenAI 2026《Harness Engineering》与 Mintlify Autopilot 采用**异步 Doc-Gardening Agent** 定期提清理 PR，而不是在每次本地 `git commit` 时强迫开发者反复提交“重钉 SHA”噪音提交【B】。
5. **面向本地 Coding Agent 的多层导航索引存在严重「房间里画房间地图」税负**。Anthropic `CLAUDE.md` 指南提出 200 行红线（理想 60–100 行）并要求「凡 Agent 读代码/目录树即可发现的内容一律删除」【B】；ETH Zurich SRI Lab（2026）受控实验证实，冗余仓库上下文/导航文件使推理成本暴涨 **>20%** 且自动生成版反令成功率微降 ~3%【B】。`llms.txt` 的核心价值在**面向外部 Web 爬虫的公开文档站**（Agent 无法 `glob` HTML 站点），而非本地拥有 `glob`/`rg` 的 Git 源码仓【B/C】。
6. **「通用公共技能」与「单仓私有 CI 套件」必须物理分离**。任何硬编码特定仓库路径（如 `skills/*/SKILL.md`）、特定语言控制头、或特定项目验收断言的脚本，都属于该仓库自身的 `scripts/` / CI 工具，而不应伪装成可跨仓安装的公共 Agent Skill【A/C】。

---

## 1. Docs-as-Code 确定性治理工业标杆（2026-11-23 `gh api` 一手实测【A】）

| 开源项目 | Stars 【A】 | 实现语言 | 最近活跃 【A】 | 核心能力与工程启示 |
| :--- | :---: | :--- | :---: | :--- |
| **`meta/docusaurus`** | **66,786** | TypeScript | 2026-11-20 | 大型静态文档站标杆，内建构建期 `onBrokenLinks: 'throw'` / `onBrokenAnchors: 'throw'` 零配置断链拦截【A】 |
| **`DavidAnson/markdownlint`**<br>（+ `markdownlint-cli2`） | **6,449**<br>（+ 987） | JavaScript | 2026-11-23 | 事实标准 Markdown 结构、标题层级与行宽（`MD013`）Linter；直接替代自写行宽与 Markdown 语法解析器【A】 |
| **`vale-cli/vale`** | **6,419** | Go | 2026-11-21 | 可编程散文、术语一致性与禁用别名 Linter；全部规则以声明式 YAML 风格包外置，绝不把业务术语硬编码进源码【A/B】 |
| **`npryce/adr-tools`** | **5,785** | Shell | 2024-04-25 | 经典 ADR CLI（`adr new` / `adr link` / `adr generate toc`），极度克制：只负责顺序编号与 `Supersedes` 双向链接，不强加控制头或修订表【A】 |
| **`lycheeverse/lychee`** | **4,156** | Rust | 2026-11-16 | 工业级高性能异步断链扫描器，同时覆盖相对路径、`#anchor`、外部 HTTP URL、`.lycheeignore` 与离线模式 `--offline`，全面强于手写几百行正则脚本【A】 |
| **`adr/madr`** | **2,661** | Markdown | 2026-11-13 | MADR 3.0 官方标准：极简 YAML frontmatter（`status`, `date`, `decision-makers`），**明确将 ADR 视为 Append-Only 不可变记录，不要求维护版本号与手写修订历史表**【A】 |
| **`evildmp/diataxis-documentation-framework`** | **1,283** | Python | 2026-10-14 | Daniele Procida 的 Diátaxis 官方框架，面向 Django/Canonical 等大型多受众公开文档站【A】 |

### 关键专题：社区对 Diátaxis 在中小型工程仓过度应用的批评【B】

Diátaxis 将文档按「学习/行动 × 实践/理论」切分为 Tutorials、How-To Guides、Reference、Explanation 四象限，在大型开源项目文档站极受推崇。但技术写作界与工程社区（包括 HN 与 Hillel Wayne 等长期实践复盘）反复指出其在**中小型代码仓库**落地时的四个经典陷阱【B】：

1. **人为碎片化与跳转税（Click-Around Penalty）**：原本 1 份紧凑文档就能讲清的设计与用法，被强拆进 4 个目录，迫使人类读者与 AI Agent 反复跨目录跳转拼图；
2. **空象限与凑数文档**：小仓往往天然只有架构解释与参考手册，为通过「四象限完整度」机械扣分而硬造低密度 Tutorial / How-To 凑数；
3. **高同步门槛打击维护意愿**：开发者修改一项行为时，若被迫思考拆散到哪几个象限、分别刷版本号、补修订表与更新多层索引，最终只会绕开文档更新；
4. **公认折中范式**：在中小工程仓中，把 Diátaxis 用作**单篇文档的写作边界透镜**（如别把操作手册和长篇原理解释混成一团），而不是**一刀切的强制目录与扣分教条**【B/C】。

---

## 2. Code-to-Doc 防腐与 Agent-First 文档治理演进【B】

### 2.1 文档与代码同步的三种工程代际

| 同步范式 | 代表方案 | 工作机理 | 维护税与真实代价 |
| :--- | :--- | :--- | :--- |
| **G1 同步人工重钉型** | 手写控制头版本号 + 手写修订表 + 手写 `复核于 commit SHA` + pre-commit 硬阻断 | 每次改代码强制在同一 commit 手工翻新关联文档版本号与 SHA | 极易产生「纯重钉 SHA / 修格式」自激噪音提交，打断研发流【A/C】 |
| **G2 Git 拓扑 / 符号锚定型** | `addyosmani` 6 行 `git merge-base --is-ancestor`【A】；Swimm AST/Token 符号锚定【B】 | 用 Git 祖先关系或代码 AST 符号绑定判定文档是否落后于实现，不依赖脆弱行号或人工填 SHA | 零额外元数据税；符号级工具（Swimm）精度高但引入商业/专用工具链 |
| **G3 异步园丁代理型（2026 前沿）** | OpenAI **Doc-Gardening Agent**、Mintlify Autopilot【B】 | 监听主干 PR 合并或定期巡检，由后台 Agent 自动比对代码与文档差异并**提交清理 PR**，人类仅做轻量 Review | 把同步阻塞的机械税转化为异步可审查增量，开发体验与新鲜度兼得 |

### 2.2 Agent-First 仓库文档的三条实证铁律

1. **OpenAI 2026《Harness Engineering: Leveraging Codex in an Agent-First World》**【B】：
   - 根级 `AGENTS.md` 严控在**约百行以内**（仅作地图指针与硬边界），拒绝百科全书式文档，依托渐进披露按需下钻 `docs/`；
   - 把机械门禁收敛到**真正高 ROI 的架构不变量**（依赖边界、断链、关键契约），日常过期文档交给异步 **Doc-Gardening Agent** 定期发 PR 清理。
2. **Anthropic Claude Code `CLAUDE.md` 官方最佳实践**【B】：
   - 明确提出 **200 行红线（理想 60–100 行）**；
   - 确立残酷删减判据：**「如果 Agent 直接读代码或目录树就能自己发现这条信息，就立刻删掉它！」** 只保留代码本身看不出来的隐性陷阱、非标准命令与硬契约。
3. **ETH Zurich SRI Lab（2026）《Evaluating AGENTS.md》与「房间里画房间地图」陷阱**【B】：
   - 跨真实仓库评测表明：LLM 生成的仓库上下文/导航文件使任务成功率**微降 ~3%**，人工编写仅微增 **~4%**，但二者一律使**推理 Token 成本增加 >20%**；
   - **对本地仓库多级地图的警示**：`llms.txt` 诞生于 Web 文档站场景（外部 Agent 无法对 HTML 网站执行 `glob`/`rg`）。而在本地克隆的 Git 仓库里，Coding Agent 原本 1 步 `glob`/`grep` 就能直达目标文件；若人为规定必须经由 `AGENTS.md → llms.txt → _llms/<象限>.md → <目录>/index.md` **四层跳转**才能读正文，反而制造了典型的 **「站在房间里先画房间地图再按图找门（Map-to-a-Room-You're-Standing-In）」** 步数与 Token 税【B/C】。

---

## 3. 头部 Agent Skills 仓库如何划定「文档技能」的职责边界【A】

通过 `gh api` 一手精读当前 GitHub 最高星的三座 Agent Skills 仓库，其对文档类技能的克制与分工边界高度一致【A】：

| 标杆仓库 | Stars 【A】 | 文档 / ADR 类技能形态 | 核心架构边界法则 |
| :--- | :---: | :--- | :--- |
| **`addyosmani/agent-skills`** | **119,853** | `skills/documentation-and-adrs/SKILL.md`<br>（**单文件 12.3 KB，零脚本**） | ① **Convention-First（优先匹配目标仓既有约定）**，不强加专有控制头或目录税；<br>② 仅用 **6 行 `git merge-base --is-ancestor`** 判 `current / stale / can't tell`，零墓碑账本、零手钉 SHA；<br>③ **严格解耦**：待办管理独立拆为 `planning-and-task-breakdown`（10.4 KB），CI 门禁拆为 `ci-cd-and-automation`，互不寄生 |
| **`anthropics/skills`** | **199,150** | `skills/doc-coauthoring/SKILL.md`<br>（**单文件 15.4 KB，零脚本**） | 聚焦「文档协作方法论」（上下文采集 → 结构化共创 → 读者盲测验收），绝不将特定仓库的 CI 校验器塞进通用技能目录 |
| **`obra/superpowers`** | **324,422** | 15 个高内聚轻量流程微技能 | 单技能只解决单一认知/工作流切片，保持接近 100% 的跨仓库可移植性 |

### 行业黄金分界线：Portable Skill vs Repo-Local CI Tooling

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ 通用公共技能 (Portable Skill, 目标 10–50 KB)                                │
│  · Convention-First：先识别宿仓库既有目录/语言/模板，按需渐进引入            │
│  · 承载：Diátaxis 写作纯度、RFC 结晶流、MADR 3.0、代码-文档联动清查心法       │
│  · 确定性检查：优先调用成熟开源 CLI (lychee / markdownlint / vale) 或薄兜底  │
├────────────────────────────────────────────────────────────────────────────┤
│ 单仓私有 CI 治理套件 (Repo-Local Tooling, 置于宿仓库 scripts/ 或 tools/)    │
│  · 承载：本仓专属目录断言、黄金问答测试、pre-commit 聚合器、特定语言控制头    │
│  · 归属：只随该仓库自身演进，绝不伪装为跨仓公共 Skill 分发                   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 下篇衔接与参考来源

结合既有 [llm-wiki-implementation-research.md](./llm-wiki-implementation-research.md) 与本篇增量调研建立的行业标尺，配套评估报告 **[2026-11-23-doc-governance-architecture-evaluation.md](./2026-11-23-doc-governance-architecture-evaluation.md)** 将对本仓库 `skills/doc-governance/`（32 追踪文件 / 12,889 行 / 598.6 KB）进行全量职责拆解、可移植性审计、390 次提交「治理税」实测与三刀瘦身重构规划。

### 主要参考来源

- **一手开源与 `gh api` 实测（2026-11-23）【A】**：`obra/superpowers`（https://github.com/obra/superpowers ）、`anthropics/skills`（https://github.com/anthropics/skills ）、`addyosmani/agent-skills`（https://github.com/addyosmani/agent-skills ）、`meta/docusaurus`（https://github.com/meta/docusaurus ）、`DavidAnson/markdownlint`（https://github.com/DavidAnson/markdownlint ）、`vale-cli/vale`（https://github.com/vale-cli/vale ）、`npryce/adr-tools`（https://github.com/npryce/adr-tools ）、`lycheeverse/lychee`（https://github.com/lycheeverse/lychee ）、`adr/madr`（https://github.com/adr/madr ）、`evildmp/diataxis-documentation-framework`（https://github.com/evildmp/diataxis-documentation-framework ）。
- **工程文、社区评述与实证研究【B】**：OpenAI Engineering《Harness Engineering: Leveraging Codex in an Agent-First World》（2026）；Anthropic Claude Code `CLAUDE.md` 官方最佳实践；ETH Zurich SRI Lab（Gloaguen et al., 2026）《Evaluating AGENTS.md》；Swimm / Mintlify Autopilot 代码耦合文档范式评述；Diátaxis 中小工程仓实践批评综述。
- **本仓前序调研【A】**：[llm-wiki-implementation-research.md](./llm-wiki-implementation-research.md)。
