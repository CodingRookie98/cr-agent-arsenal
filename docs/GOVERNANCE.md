# CR 公共技能库文档工程与知识库治理规程 (Knowledge Base Governance)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-GOV-2026
> - **当前版本**: V1.5.0
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-09-10

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.5.0** | 2026-10-09 | DSH AI Agent | 王辉 | 补「目录级索引约定」：根级人类入口唯一、象限索引按需托管（`<!-- doc-index:managed -->` 标记 + 幂等登记 + 人工索引零改写），新增工具 `manage-doc-index.py` 与 `scaffold-doc.sh` 索引自愈 |
| **V1.4.0** | 2026-10-04 | DSH AI Agent | 王辉 | 目录拓扑补 `docs/project/reviews/`（交付凭据归档：审查报告全文进版本库）与 `docs/project/plans/`；归档根遵循「推荐默认 + 宿主优先」 |
| **V1.3.0** | 2026-09-16 | DSH AI Agent | 王辉 | 需求确认文档补「验收口径」（验收人/验收场景/不验收项/口径裁决人）；人机契约字段（需求方/批准人/批准基线）进入计划与 RFC 模板 |
| **V1.2.0** | 2026-09-16 | DSH AI Agent | 王辉 | RFC 标准模板新增「术语表与易歧义对齐」段（术语先行前置条件）与 `docs/reference/rules/glossary.md` SSOT 落位；决策台账顺延为 §7 |
| **V1.1.0** | 2026-09-16 | DSH AI Agent | 王辉 | RFC 标准模板新增「决策台账与默认假设」段（提案收敛证据链）；明确需求确认文档落位 `docs/proposals/`，继续禁止 `docs/requirements/` 瀑布旧目录 |

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

**目录级索引约定**：根级 `docs/index.md` 为**唯一**的人类总索引入口；象限/子目录 `index.md`（或 `README.md`）为**按需存在**的分流入口，由 `scaffold-doc.sh` 经 `manage-doc-index.py` 自动创建与幂等登记（托管标记 `<!-- doc-index:managed -->`）。不含托管标记的索引视为人工维护，脚本只读不改；严禁为凑齐拓扑批量创建空索引。

---

## 3. 自动化门禁与工具链 (CI Toolchain)

项目内置 `doc-governance` 自动化工具箱（位于 `skills/doc-governance/scripts/`）：

| 工具脚本 | 核心功能 | 触发时机 | 执行命令 |
| :--- | :--- | :--- | :--- |
| **`check-doc-links.py`** | 静态扫描物理文件超链接与 `#anchor` 锚点 | 提交前 / CI 门禁 | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` |
| **`trim-revision.py`** | 自动裁剪历史记录至最近 5 条滑动窗口 | 提交前 / 维护 | `python3 skills/doc-governance/scripts/trim-revision.py --root docs --fix --keep 5` |
| **`audit-doc-health.py`** | 综合健康体检（打分 0-100 分，断链/元数据/孤儿/架构/**机器地图一致性**） | 交付验收 / 定期体检 | `python3 skills/doc-governance/scripts/audit-doc-health.py --root docs` |
| **`generate-llms-txt.py`** | 自动提取 Frontmatter 并刷新机器地图 `llms.txt` | 文档拓扑变动后 | `python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt` |
| **`manage-doc-index.py`** | 象限索引托管维护（ensure 骨架 / register 幂等登记 / 人工索引零改写） | 新建文档后 / 拓扑变动 | `python3 skills/doc-governance/scripts/manage-doc-index.py register --root docs --dir how-to --file deployment.md --title "部署 SOP" --kind HowTo` |
| **`scaffold-doc.sh`** | 快速生成符合 Diátaxis 规范的文档脚手架，并自动 ensure 象限索引与登记（跨象限链接按需降级） | 新建文档时 | `skills/doc-governance/scripts/scaffold-doc.sh <type> <name>` |

---

## 4. ⛔ 核心红线与负向规范 (Negative Invariants)

1. **⛔ 严禁 404 断链**：所有相对链接必须显式保留 `.md` 物理后缀，严禁裸路由或失效相对路径；
2. **⛔ 严禁跨象限职责混淆**：技术参考（Reference）只记录冷峻事实，严禁加入教程或背景说理；操作指南（How-To）直奔步骤，理论分析外链至 Explanation；
3. **⛔ 严禁机器地图与生成物不一致**：`docs/llms.txt` 必须是注册命令 `generate-llms-txt.py --root docs --output docs/llms.txt` 在该树上的**逐字节产物**（先定稿全部文档、最后重生成）；`audit-doc-health.py` 已将其固化为硬阻断项，漂移即 REJECT；
4. **⛔ 严禁修订历史无限膨胀**：每个文档修订历史表格最多保留 5 条最新记录，超过部分必须裁剪；
5. **⛔ 严禁瀑布生命周期旧目录**：严禁创建 `docs/requirements/`、`docs/design/`、`docs/planning/` 等旧时代目录，必须归入对应 Diátaxis 象限；
6. **⛔ 严禁文件命名随意混乱**：一律采用纯小写 `kebab-case` 命名风格（如 `goal-loop-design.md`），禁止驼峰与无规则空格。

---

## 4.1 交付凭据归档豁免 (Evidence Archive Exemption)

`docs/project/reviews/**` 为**交付凭据归档**（`dual-round-review` 审查报告全文，需求源 RFC-0001）：报告必须以**逐字原文**落盘（G1 红线——添加文档控制头会改变内容并污染其 SHA256 指纹），且报告之间不存在 markdown 入链。因此该目录**豁免**以下扫描：

| 工具 | 豁免项 | 理由 |
| :--- | :--- | :--- |
| `check-doc-links.py` | 全量跳过（不计入扫描文件数） | 报告正文可能引用归档目录外的相对路径，逐字归档不得改写 |
| `check-doc-control-sync.py` | 控制头与修订表版本一致性校验 | 报告无标准控制头，不参与版本联动扫描 |
| `audit-doc-health.py` | 元数据控制头合规率、孤儿文档计分 | 报告不得添加控制头；报告无 markdown 入链 |
| `trim-revision.py` | 修订历史裁剪（含 `--fix` 就地写入） | 报告逐字归档，任何写入都会破坏 SHA256 指纹（BK-0001） |
| `generate-llms-txt.py` | 机器地图收录 | 逐字凭据不进入智能体引导地图，保持机器地图纯净（BK-0002） |

**判定实现**：只读消费者采用 root 锚定判定（`in_evidence_archive(path, root_dir)`）；**具备写能力的 `trim-revision.py` 与 `generate-llms-txt.py` 额外采用路径段扫描（`is_archive_path`）** —— 该判定**不依赖 `--root`**，凡路径中出现相邻的 `project/reviews` 段即视为交付凭据。它是有意为之的**保守超集**（比上方 `<docs 根>/project/reviews/**` 边界更宽：即使该段不位于 docs 根之下亦受保护），以换取「任何 `--root` 形态下都不写入交付凭据」的写入安全（BK-0001 / R1-2）；机器地图落点若解析落入归档则直接拒绝写入（`--output` 显式分支已解析后判定；**缺省落点分支的 `resolve()` 加固与零覆盖守卫见 BK-0023**）。

**边界**：豁免仅覆盖 `<docs 根>/project/reviews/**`。归档**索引** `README.md` 仍应携带标准控制头（`prepare-review-context.sh` 的 scaffold 模板已内置），以保持人类可读性。
