# CR 公共技能库文档工程与知识库治理规程 (Knowledge Base Governance)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-GOV-2026
> - **当前版本**: V1.11.1
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-10-20
> - **代码锚点**: skills/doc-governance/scripts/audit-doc-health.py, skills/doc-governance/scripts/check-doc-drift.py
> - **复核于**: 2026-11-23 / commit ef7e325

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.11.1** | 2026-11-22 | DSH AI Agent | 王辉 | **红队 B 项收口**：真值轴新增 `--staged`（pre-commit 下「锚点已暂存而文档未同步」即判漂移）与「同一次提交视为同步」豁免；体量门禁后缀大小写不敏感、U+2028 不再绕过、不可读 fail-closed；§4.1 登记 `reference/articles` 豁免；可回答性 GAP 口径细化 |
| **V1.11.0** | 2026-11-22 | DSH AI Agent | 王辉 | **门禁自动化与可回答性评测（BK-0048/BK-0049）**：§3 新增 `check-all.py`（六道门禁聚合，1.5 s，pre-commit 入口）与 `check-golden-tasks.py`（20 条可回答性断言，三态 PASS/GAP/FAIL）；§5 登记 pre-commit 安装方式与 GAP 处置口径 |
| **V1.10.0** | 2026-11-22 | DSH AI Agent | 王辉 | **体量度量换挡（RFC-0008）**：新增 `check_doc_size`（字节 ≤64 KB、最长单行 ≤1000 阻断；行数仅警告），棘轮基线 `.doc-size-baseline.json` 消化 2 篇存量；§3 工具表与红线 10 同步；废弃「800 行」作为阻断判据 |
| **V1.9.1** | 2026-11-22 | DSH AI Agent | 王辉 | **状态机 TD 收口**：`取代于` 允许根内 `../` 跨目录链、只拦越界；表格形态只解析控制头连续块（字段说明表不再被误读）；C-4 覆盖引用式/带 title/大写扩展名；隐式 Active 携带指针亦阻断；§4.1 登记 backlog 豁免 |
| **V1.9.0** | 2026-11-22 | DSH AI Agent | 王辉 | **文档状态机（RFC-0007）**：控制头 `文档状态` 扩为 Active/Contested/Superseded 三态，新增 `取代于`（Superseded 必填）与 `争议点`；§3 工具表补 `check_doc_status`；§4 新增红线 9「禁 Active 带取代于」；审计输出新增「未决冲突清单」 |

---

## 1. 概述与核心哲学 (Philosophy & Principles)

在 AI 智能体软件研发时代，文档不仅是人类工程师的备忘录，更是**智能体执行任务规划、架构推演与代码生成的唯一真相源（Single Source of Truth）与黄金上下文**。

本项目遵循四大治理支柱：
1. **Diátaxis 四象限架构**：严格依据读者即时心智切分象限，严禁职责混淆；
2. **RFC 提案孵化与定案结晶流转**：初期单文件集中对齐，定案后解构下沉至稳态目录；
3. **Docs-as-Code 自动化门禁**：物理链接强制带 `.md` 后缀校验、修订历史 5 条滑动裁剪窗口、全域零 404 断链；
4. **语言习惯继承与命名标准**：工程主语言保持一致，文件名采用全小写 kebab-case。

---

## 2. 目录拓扑与职责划分 (Directory Topology)

知识库根目录为 `docs/`，严禁在不同象限间混杂内容：

```text
docs/
├── index.md                 # 【全局人类总入口】全景知识库拓扑与分类索引
├── llms.txt                 # 【AI 智能体机器地图】精炼的机器可读知识拓扑与关键参考入口
├── GOVERNANCE.md            # 【知识库治理规程】本文档
│
├── proposals/               # 💡 0. 需求与设计孵化层 (Inception / RFC Proposals)
│   ├── RFC-0001-xxx.md      # 初期对齐提案草案 (Draft -> In Review -> Accepted)
│   └── archive/             # 已结晶下沉的提案历史归档 (Implemented / Superseded)
│
├── tutorials/               # 🎓 1. 教程象限 (Learning-Oriented / Newcomer Success)
│   └── quick-start.md       # 5 分钟上手开发与运行首个特性
│
├── how-to/                  # 🛠️ 2. 操作指南象限 (Problem-Oriented / Task Recipes)
│   ├── installing-skills.md # 技能安装与软链接配置 SOP
│   └── testing-guide.md     # 技能自测与门禁校验 SOP
│
├── reference/               # 📖 3. 技术参考象限 (Information-Oriented / Machine Truth)
│   ├── api/                 # 接口契约规格与错误信封
│   ├── models/              # 数据模型与 Schema 定义
│   └── rules/               # 行为协议、规则与不可变约束
│
├── explanation/             # 💡 4. 深度剖析象限 (Understanding-Oriented / The "Why")
│   ├── architecture/        # 系统与技能总体架构设计书 (Hub & Spokes)
│   ├── decisions/           # MADR 3.0 格式架构决策记录 (ADR)
│   └── analysis/            # 技术选型评估与调研报告
│
└── project/                 # 🚀 5. 工程演进与项目管理 (Project Management & Evolution)
    ├── roadmap.md           # 路线图与规划
    ├── changelog.md         # 版本发布日志
    ├── backlog.md           # 待办与技术债清单
    ├── plans/               # 实施计划与结项记录
    └── reviews/             # 交付凭据归档（审查报告全文；推荐默认归档根，schema 见 RFC-0001）
```

**目录级索引约定**：根级 `docs/index.md` 为**唯一**的人类总索引入口；象限/子目录 `index.md`（或 `README.md`）为**按需存在**的分流入口，由 `scaffold-doc.py` 经 `manage-doc-index.py` 自动创建与幂等登记（托管标记 `<!-- doc-index:managed -->`）。不含托管标记的索引视为人工维护，脚本只读不改；严禁为凑齐拓扑批量创建空索引。

---

## 3. 自动化门禁与工具链 (CI Toolchain)

项目内置 `doc-governance` 自动化工具箱（位于 `skills/doc-governance/scripts/`）：

| 工具脚本 | 核心功能 | 触发时机 | 执行命令 |
| :--- | :--- | :--- | :--- |
| **`check-doc-links.py`** | 静态扫描物理文件超链接与 `#anchor` 锚点（根扫描含机器地图 `llms.txt`） | 提交前 / CI 门禁 | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` |
| **`trim-revision.py`** | 自动裁剪历史记录至最近 5 条滑动窗口 | 提交前 / 维护 | `python3 skills/doc-governance/scripts/trim-revision.py --root docs --fix --keep 5` |
| **`audit-doc-health.py`** | 综合健康体检（打分 0-100 分，断链/元数据/孤儿/架构/**机器地图一致性**） | 交付验收 / 定期体检 | `python3 skills/doc-governance/scripts/audit-doc-health.py --root docs` |
| **`check-all.py`** | 门禁聚合器：机器地图 / 断链 / 版本一致 / 真值轴 / 健康体检 / 可回答性，任一失败即非零退出并给修复命令 | 每次 commit 前（pre-commit）/ 交付前 | `python3 skills/doc-governance/scripts/check-all.py [--full] [--quiet]` |
| **`check-golden-tasks.py`** | 知识库可回答性评测：20 条机械断言，PASS/GAP/FAIL 三态；仅 FAIL 阻断，GAP 登记 backlog | 交付前 / 定期 | `python3 skills/doc-governance/scripts/check-golden-tasks.py --root docs` |
| **`check_doc_size`**（audit 内置） | 文档体量门禁：字节数 / 最长单行（阻断）、行数（警告）；棘轮基线 `--write-size-baseline` 登记存量 | 交付前 / 巡检 | `python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .` |
| **`check_doc_status`**（audit 内置） | 文档状态机门禁：取值合法性、`取代于` 必填与有效性、`Active` 携带指针；输出「未决冲突清单」 | 交付前 / 巡检 | `python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .` |
| **`check-doc-drift.py`** | 真值轴漂移检测（代码锚点存在性 + git 提交时间 vs `复核于`；五态输出；零声明不颁发满分） | 交付前 / 定期巡检 | `python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . [--fail-on-drift]` |
| **`generate-llms-txt.py`** | 自动提取 Frontmatter 并刷新机器地图；`--split` 分层（根=象限入口，全量下沉 `_llms/`），`--check` 只校验，`--max-root-bytes` 体量门禁 | 文档拓扑变动后 | `python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --split` |
| **`manage-doc-index.py`** | 象限索引托管维护（ensure 骨架 / register 幂等登记 / 人工索引零改写） | 新建文档后 / 拓扑变动 | `python3 skills/doc-governance/scripts/manage-doc-index.py register --root docs --dir how-to --file deployment.md --title "部署 SOP" --kind HowTo` |
| **`scaffold-doc.py`** | 快速生成符合 Diátaxis 规范的文档脚手架，并自动 ensure 象限索引与登记（跨象限链接按需降级；POSIX 下旧 `.sh` 兼容壳仍可用） | 新建文档时 | `python3 skills/doc-governance/scripts/scaffold-doc.py <type> <name>` |

> **`--dir` 的作用域契约**：`--dir` 只用于在 `--root` **之内**收窄扫描面，取值按根相对路径给出且必须真实存在。越出根目录（如 `--dir ../../x`）或指向不存在的路径一律 **exit 2**——此前这两种写法会被静默拼成「扫描 0 个文件 + rc=0」，用退出码报平安。收窄根会改变豁免基线：判据是 `resolve()` 后的根相对语义，不是字符串前缀（BK-0005）。

> **真值门口径（RFC-0005 / V1.7.4）**：门禁模式下账本 missing/corrupt 直接 rc=2（先跑 `check-doc-drift.py --write-baseline` 并提交账本）；墓碑判据是**全局锚点多重集不减少**——纯改名/拆分合法，删文档/删锚点/缩减锚点才违规，合法迁移须显式刷新账本并在提交信息登记。

> **旧口径（V1.7.2，已被上行取代）**：`--truth=warn` 只报告不改判；`--truth=require` 按序阻断——不可判定（浅克隆）→ 未启用 → **基线墓碑违规**（`check-doc-drift.py --write-baseline` 登记过的声明被删除/缩减）→ 覆盖率 < `--min-coverage`（默认 0.5）→ 真值分 < `--truth-threshold`（默认 12/15）。**删锚点不能替代修复漂移**：唯一机械拦截是基线墓碑，覆盖率下限只是辅助；浅克隆（`fetch-depth: 1`）下漂移检测直接 fail-closed（rc=2），CI 须使用 `fetch-depth: 0`。

> **孤儿文档计分的边界（BK-0019）**：**入口象限**（`<docs 根>` 根级文档）不参与孤儿判定——DA-4 明令该象限不生成托管索引，其文档在结构上不可能被机械登记；把规范强制的结构计入缺陷，是对同一决策的双重惩罚。**已知代价**：根级真孤儿不再由该指标发现；根级本应只放入口文档，其健康度由链接完整率与人工评审覆盖。宿主脚本：`audit-doc-health.py` 的 `orphan_docs` 判定。

---

## 4. ⛔ 核心红线与负向规范 (Negative Invariants)

1. **⛔ 严禁 404 断链**：所有相对链接必须显式保留 `.md` 物理后缀，严禁裸路由或失效相对路径；
2. **⛔ 严禁跨象限职责混淆**：技术参考（Reference）只记录冷峻事实，严禁加入教程或背景说理；操作指南（How-To）直奔步骤，理论分析外链至 Explanation；
3. **⛔ 严禁机器地图与生成物不一致**：`docs/llms.txt` 必须是注册命令 `generate-llms-txt.py --root docs --output docs/llms.txt` 在该树上的**逐字节产物**（先定稿全部文档、最后重生成）；`audit-doc-health.py` 已将其固化为硬阻断项，漂移即 REJECT；
4. **⛔ 严禁修订历史无限膨胀**：每个文档修订历史表格最多保留 5 条最新记录，超过部分必须裁剪；
5. **⛔ 严禁瀑布生命周期旧目录**：严禁创建 `docs/requirements/`、`docs/design/`、`docs/planning/` 等旧时代目录，必须归入对应 Diátaxis 象限；
6. **⛔ 严禁文件命名随意混乱**：一律采用纯小写 `kebab-case` 命名风格（如 `goal-loop-design.md`），禁止驼峰与无规则空格；
7. **⛔ 严禁手改生成物**：`docs/llms.txt` 与 `docs/_llms/*.md` 必须由 `generate-llms-txt.py --split` 逐字节生成；手改即触发「机器地图不一致」硬阻断（含子地图多余/缺失）；
8. **⛔ 严禁伪造文档状态**：`Superseded` 必须给出真实接替者（`取代于` 指向存在且非自身），`Active` 不得携带 `取代于`；状态取值只允许 `Active`/`Contested`/`Superseded`，其余一律阻断（RFC-0007）；
9. **⛔ 严禁文档体量失控**：单文档 >64 KB 或最长单行 >1000 字符即阻断；行数 >800 仅警告（行数指标已证失效）。存量超限登记于 `docs/.doc-size-baseline.json`（棘轮：只降不升，恶化即阻断）；
10. **⛔ 严禁「删锚点清零」自我豁免**：声明过 `代码锚点` 的文档，禁止为让 `check-doc-drift.py` 变绿而删除锚点声明或伪造 `复核于`——删除声明等于把文档移出真值统计（RFC-0005 §3 已点名此反模式）。正确动作是**复核断言**：内容仍成立则只刷新复核点，不成立则改文档。

---

## 4.1 交付凭据归档豁免 (Evidence Archive Exemption)

`docs/project/reviews/**` 为**交付凭据归档**（`dual-round-review` 审查报告全文，需求源 RFC-0001）：报告必须以**逐字原文**落盘（G1 红线——添加文档控制头会改变内容并污染其 SHA256 指纹），且报告之间不存在 markdown 入链。因此该目录**不参与任何计分维度扫描**（下列工具针对交付凭据的具体豁免项如下）：

| 工具 | 豁免项 | 理由 |
| :--- | :--- | :--- |
| `check-doc-links.py` | 全量跳过（不计入扫描文件数） | 报告正文可能引用归档目录外的相对路径，逐字归档不得改写 |
| `check-doc-control-sync.py` | 控制头与修订表版本一致性校验 | 报告无标准控制头，不参与版本联动扫描 |
| `audit-doc-health.py` | 元数据控制头合规率、孤儿文档计分 | 报告不得添加控制头；报告无 markdown 入链 |
| `trim-revision.py` | 修订历史裁剪（含 `--fix` 就地写入） | 报告逐字归档，任何写入都会破坏 SHA256 指纹（BK-0001） |
| `generate-llms-txt.py` | 机器地图收录 | 逐字凭据不进入智能体引导地图，保持机器地图纯净（BK-0002） |

**门禁执行口径（BK-0048）**：六道门禁由 `check-all.py` 聚合，推荐以 `git config core.hooksPath .githooks` 安装 pre-commit hook；临时跳过用 `git commit --no-verify`，**须在提交信息登记原因**。CI 环境直接调用同一入口即可（无需另写脚本）。

**可回答性评测的 GAP 口径（BK-0049）**：`check-golden-tasks.py` 的 GAP 表示「知识库确实缺这块内容」，**不得**为消除 GAP 而当场补写文档——应登记 backlog 卡片，按优先级排期。FAIL 才是结构缺陷，必须立即修复。

**外部文献豁免（RFC-0008）**：`docs/reference/articles/**` 为外部文章逐字转载，无控制头、原文不可改写，不参与体量三指标与可回答性 G-20 的控制头断言（其余文档照常受检）。

**待办卡片豁免（RFC-0007）**：`docs/project/backlog/**` 不参与文档状态机——卡片的 YAML `status` 是**生命周期字段**（planned/in-progress/completed），与文档状态（Active/Contested/Superseded）语义不同，混用会把 48 张卡片误判为非法状态。宿主：`check_doc_status` 的目录判定（按 `project/backlog` 相对路径，不按绝对路径分量）。

**生成物与路由文件豁免（RFC-0006）**：`docs/_llms/**`（分层子地图，生成物）与 `docs/AGENTS.md`（路由规则）不参与元数据控制头、孤儿文档、修订历史计分——它们无控制头、无 markdown 入链是**设计使然**，计入即双重惩罚。但**断链扫描仍覆盖它们**（链接必须有效），机器地图一致性门禁亦覆盖全部子地图。宿主：`audit-doc-health.py` 的 `in_generated_map` / `is_router_file`。

**判定实现**：只读消费者采用 root 锚定判定（`in_evidence_archive(path, root_dir)`）；**具备写能力的 `trim-revision.py` 与 `generate-llms-txt.py` 额外采用路径段扫描（`is_archive_path`）** —— 该判定**不依赖 `--root`**，凡路径中出现相邻的 `project/reviews` 段即视为交付凭据。它是有意为之的**保守超集**（比上方 `<docs 根>/project/reviews/**` 边界更宽：即使该段不位于 docs 根之下亦受保护），以换取「任何 `--root` 形态下都不写入交付凭据」的写入安全（BK-0001 / R1-2）；机器地图落点若解析落入归档则直接拒绝写入（`--output` 显式分支已解析后判定；**缺省落点分支的 `resolve()` 加固与零覆盖守卫见 BK-0023**）。

**零覆盖态边界（BK-0027 显式登记）**：当 `<docs 根>` 下**没有任何可收录文档**（生成器收录数为 0，例如仅剩根文件与交付凭据归档）时，机器地图一致性检查**不适用**（跳过判定）—— 这是为避免「提示的修复命令必然 rc=1」的不可修复死胡同（BK-0023 / R1-1）。

> **该豁免的已知代价（显式登记，不掩饰；V1.6.0 起收敛）**：此时若仓库仍保留 `llms.txt`，**一致性检查不判定其条目是否过期**（无生成基准可比对）；但**物理断链已不再是盲区** —— `check-doc-links.py` 的根扫描已显式纳入 `<docs 根>/llms.txt`（其相对链接按所在目录解析），死链会被检出并以 rc=1 阻断。**口径选择：仅保留「条目是否过期」的登记豁免，不引入条目与文档树的语义比对**（保持门禁简单性；该状态仅在项目删净全部可收录文档时出现）。此状态下作者须自行确认并**删除**不再成立的 `llms.txt`。

**身份写保护契约（BK-0031 登记）**：`docs/llms.txt` 首行 `# <项目名> Machine-Readable Knowledge Base Map` 中的**项目名即地图身份**，受写保护：

- **注册命令**（§3 登记，不带 `--name`）：既有地图存在时生成器**沿用既有身份**（正常重生成绝不改名）；仅当无既有地图时才使用缺省 `System`；
- **显式改名**：`--name=<新名>` 与既有身份不同时**拒绝落盘**（rc≠0）；确需改名须先人工移除既有地图文件（有意动作，无隐式通道）；
- **fail-closed 边界**：既有地图不可读、非合法 UTF-8、或首行不符合标准 H1 格式时，一律拒绝覆盖（不得归一化或回落占位名后静默改写）；
- **地图缺失边界**：无既有地图时不触发本契约；「有可收录文档但地图缺失」**不参与**一致性判定（与零覆盖态边界同源），该逃逸面由 `docs/index.md` 的入链断链门禁间接兜底，属**已登记豁免**。

**边界**：豁免仅覆盖 `<docs 根>/project/reviews/**`。归档**索引** `README.md` 仍应携带标准控制头（`prepare-review-context.py` 的 scaffold 模板已内置），以保持人类可读性。

**索引可读性约定的守卫边界（BK-0007 显式登记）**：归档索引的控制头与 `## 报告清单` 的相对链接属**无门禁守卫的可读性约定** —— `check-doc-control-sync.py`、`check-doc-links.py`、`audit-doc-health.py` 对该目录整体豁免，上述内容由人工维护、不参与版本一致性/断链/健康度校验；索引的**结构性字段**（索引字段齐备、轮次台账、SHA256 指纹、稳定 ID 对齐、终审裁决取值）由 `check-review-report.py` 机械校验，不属可读性约定范畴。
