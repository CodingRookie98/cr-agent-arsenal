# CR 公共技能库文档工程与知识库治理规程 (Knowledge Base Governance)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-GOV-2026
> - **当前版本**: V1.2.0
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-09-10

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-09-10 | Antigravity AI Agent | 王辉 | 初始化项目级文档治理规程与 CI 门禁标准 |
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
    └── backlog.md           # 待办与技术债清单
```

---

## 3. 自动化门禁与工具链 (CI Toolchain)

项目内置 `doc-governance` 自动化工具箱（位于 `skills/doc-governance/scripts/`）：

| 工具脚本 | 核心功能 | 触发时机 | 执行命令 |
| :--- | :--- | :--- | :--- |
| **`check-doc-links.py`** | 静态扫描物理文件超链接与 `#anchor` 锚点 | 提交前 / CI 门禁 | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` |
| **`trim-revision.py`** | 自动裁剪历史记录至最近 5 条滑动窗口 | 提交前 / 维护 | `python3 skills/doc-governance/scripts/trim-revision.py --root docs --fix --keep 5` |
| **`audit-doc-health.py`** | 综合健康体检（打分 0-100 分，断链/元数据/孤儿/架构） | 交付验收 / 定期体检 | `python3 skills/doc-governance/scripts/audit-doc-health.py --root docs` |
| **`generate-llms-txt.py`** | 自动提取 Frontmatter 并刷新机器地图 `llms.txt` | 文档拓扑变动后 | `python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt` |
| **`scaffold-doc.sh`** | 快速生成符合 Diátaxis 规范的文档脚手架 | 新建文档时 | `skills/doc-governance/scripts/scaffold-doc.sh <type> <name>` |

---

## 4. ⛔ 核心红线与负向规范 (Negative Invariants)

1. **⛔ 严禁 404 断链**：所有相对链接必须显式保留 `.md` 物理后缀，严禁裸路由或失效相对路径；
2. **⛔ 严禁跨象限职责混淆**：技术参考（Reference）只记录冷峻事实，严禁加入教程或背景说理；操作指南（How-To）直奔步骤，理论分析外链至 Explanation；
3. **⛔ 严禁修订历史无限膨胀**：每个文档修订历史表格最多保留 5 条最新记录，超过部分必须裁剪；
4. **⛔ 严禁瀑布生命周期旧目录**：严禁创建 `docs/requirements/`、`docs/design/`、`docs/planning/` 等旧时代目录，必须归入对应 Diátaxis 象限；
5. **⛔ 严禁文件命名随意混乱**：一律采用纯小写 `kebab-case` 命名风格（如 `goal-loop-design.md`），禁止驼峰与无规则空格。
