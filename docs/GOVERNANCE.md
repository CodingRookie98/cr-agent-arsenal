# CR 公共技能库文档工程与知识库治理规程 (Knowledge Base Governance)

> **文档控制信息**
> - **文档标识**: CR-PUB-DOCS-GOV-2026
> - **当前版本**: V2.0.0
> - **文档状态**: Active
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-10-20

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V2.0.0** | 2026-11-24 | AI Agent | 王辉 | **Wave 2C 三刀切割公私分离（ADR-0005）**：§2 移除 `llms.txt`/`_llms/` 与托管索引脚本约定；§3 拆分为公共技能与本仓私有门禁/待办工具三层；§4 废除修订表、真值轴重钉与机器地图一致阻断，保留状态机、体量上限与凭据/文献/待办豁免 |
| **V1.11.2** | 2026-11-23 | DSH AI Agent | 王辉 | **目录拓扑与现状对齐**：补 `_llms/`、`AGENTS.md`、`plans/`、`reviews/`；`backlog.md` → 形态 B `backlog/`；how-to/reference 按实际文件与目录更新，删除未落地示例条目 |
| **V1.11.1** | 2026-11-22 | DSH AI Agent | 王辉 | **红队 B 项收口**：补充真值轴 `--staged`、体量门禁边界与 `reference/articles` 豁免、可回答性 GAP 口径细化 |
| **V1.11.0** | 2026-11-22 | DSH AI Agent | 王辉 | **门禁自动化与可回答性评测（BK-0048/BK-0049）**：新增 `check-all.py`（pre-commit 入口）与 `check-golden-tasks.py`（20 条可回答性断言） |
| **V1.10.0** | 2026-11-22 | DSH AI Agent | 王辉 | **体量度量换挡（RFC-0008）**：引入字节 ≤64 KB 与最长单行 ≤1,000 字符阻断阈值，废弃「800 行」阻断判据 |

---

## 1. 概述与核心哲学 (Philosophy & Principles)

在 AI 智能体软件研发时代，文档不仅是人类工程师的备忘录，更是**智能体执行任务规划、架构推演与代码生成的唯一真相源（Single Source of Truth）与黄金上下文**。

本项目遵循四大治理支柱：
1. **Diátaxis 四象限架构**：严格依据读者即时心智切分象限，严禁职责混淆；
2. **RFC 提案孵化与定案结晶流转**：初期单文件集中对齐，定案后解构下沉至稳态目录；
3. **Docs-as-Code 低摩擦自动化门禁**：物理链接显式 `.md` 后缀、三态文档状态机、体量硬上限与全域零 404 断链；
4. **语言习惯继承与命名标准**：工程主语言保持一致，文件名采用全小写 kebab-case。

---

## 2. 目录拓扑与职责划分 (Directory Topology)

知识库根目录为 `docs/`，严禁在不同象限间混杂内容：

```text
docs/
├── index.md                 # 【全局总入口】人类与智能体共用的全景知识库索引
├── AGENTS.md                # 【路由规则】读取顺序与硬约束（≤30 行，不承载领域知识）
├── GOVERNANCE.md            # 【知识库治理规程】本文档
│
├── proposals/               # 💡 0. 需求与设计孵化层 (Inception / RFC Proposals)
│   │                        # ⭐ 单文件对齐草案；存在历史审查引用时定案/取代后原位保留
│   └── RFC-XXXX-xxx.md      # 状态：Draft -> In Review -> Accepted -> Implemented / Superseded
│
├── tutorials/               # 🎓 1. 教程象限 (Learning-Oriented / Newcomer Success)
│   ├── index.md             # 象限分流入口（按需手工/Agent 维护）
│   └── quick-start.md       # 5 分钟上手开发与运行首个特性
│
├── how-to/                  # 🛠️ 2. 操作指南象限 (Problem-Oriented / Task Recipes)
│   ├── index.md             # 象限分流入口（按需手工/Agent 维护）
│   ├── install-skills.md    # 技能安装与软链接配置 SOP
│   ├── run-doc-gates.md     # 三道文档门禁的执行与失败处置 SOP
│   └── troubleshoot-doc-governance.md  # 按症状索引的故障排查
│
├── reference/               # 📖 3. 技术参考象限 (Information-Oriented / Machine Truth)
│   │                        # ⭐ 核心规范与规则真相源；rules/index.md 登记全部规则文档
│   ├── articles/            # 外部文献逐字转载（RFC-0008 §4.3 豁免体量与控制头）
│   └── rules/               # 行为协议、规则与不可变约束
│
├── explanation/             # 💡 4. 深度剖析象限 (Understanding-Oriented / The "Why")
│   ├── architecture/        # 系统与技能总体架构设计书 (Hub & Spokes)
│   ├── decisions/           # MADR 3.0 格式架构决策记录 (ADR, Append-Only)
│   └── analysis/            # 技术选型评估与调研报告
│
└── project/                 # 🚀 5. 工程演进与项目管理 (Project Management & Evolution)
    ├── changelog.md         # 版本发布日志与交付叙事单一事实源
    ├── plans/               # 实施计划与结项记录
    ├── reviews/             # Write-Once 交付凭据归档（审查报告全文，只增不改）
    └── backlog/             # 本仓待办形态 B（index.md + active/ + archive/<version>/）
```

**目录级索引约定**：根级 `docs/index.md` 为**唯一**的全局总索引入口；象限/子目录 `index.md`（或 `README.md`）为**按需存在**的分流入口，由人工或智能体按需创建与维护（原 `manage-doc-index.py` 与 `scaffold-doc.py` 已随 [ADR-0005](./explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md) 退役）。严禁为凑齐拓扑批量创建空目录与空索引；指向目录的链接，其目标目录必须含 `index.md` 或 `README.md`。

---

## 3. 自动化门禁与工具链 (CI Toolchain)

依据 [ADR-0005](./explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md)，工具链严格划分为**公共可复用技能**、**本仓私有门禁**与**本仓待办管理**三层：

### 3.1 公共可复用技能（`skills/doc-governance/`）

| 工具脚本 | 核心功能 | 适用范围 | 执行命令 |
| :--- | :--- | :--- | :--- |
| **`check-doc-links.py`** | 零依赖物理链接与 `#anchor` 静态扫描器（支持可重复 `--exclude <rel_prefix>`，越界参数 fail-closed Exit 2） | 任意项目（跨仓通用） | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews` |

> **`--dir` 与 `--exclude` 的作用域契约**：两者取值均按 `--root` 相对路径给出；越出根目录（如 `../../x`）或 `--dir` 指向不存在的路径一律 **exit 2**（fail-closed），杜绝静默扫描 0 文件报平安。

### 3.2 本仓私有门禁（`scripts/doc-gates/`）

| 工具脚本 | 核心功能 | 触发时机 | 执行命令 |
| :--- | :--- | :--- | :--- |
| **`check-all.py`** | 本仓门禁聚合器：顺序执行 **断链 / 健康体检 / 可回答性** 3 道门禁；`--full` 追加 `pytest skills/ scripts/ -q` | 每次 commit 前（pre-commit）/ CI | `python3 scripts/doc-gates/check-all.py [--full] [--quiet]` |
| **`check-doc-health.py`** | 本仓健康体检：RFC-0007 三态状态机、RFC-0008 体量上限（≤64 KB / 最长单行 ≤1,000 字符，行数 >800 仅警告）与 `docs/AGENTS.md` ≤30 行路由守卫 | 交付前 / 聚合门禁调用 | `python3 scripts/doc-gates/check-doc-health.py --root docs` |
| **`check-golden-tasks.py`** | 知识库可回答性评测：20 条机械断言，PASS/GAP/FAIL 三态（`G-18` 校验 `docs/index.md` 象限导航）；仅 FAIL 阻断 | 交付前 / 聚合门禁调用 | `python3 scripts/doc-gates/check-golden-tasks.py --root docs` |

### 3.3 本仓待办管理（`scripts/backlog/`）

| 工具脚本 | 核心功能 | 规范依据 | 执行命令 |
| :--- | :--- | :--- | :--- |
| **`manage-backlog.py`** | 形态 B 待办目录（`index.md` + `active/` + `archive/<version>/`）CRUD 与索引同步 | [scripts/backlog/README.md](../scripts/backlog/README.md) | `python3 scripts/backlog/manage-backlog.py list` |

> **已退役机制说明**：原 `trim-revision.py`、`check-doc-control-sync.py`、`check-doc-drift.py`、`generate-llms-txt.py`、`manage-doc-index.py`、`scaffold-doc.py/.sh` 及 `docs/llms.txt`、`docs/_llms/`、`.doc-truth-baseline.json`、`.doc-size-baseline.json` 已于 V2.0.0（ADR-0005 Wave 2C）全面退役，代码与文档的语义同步改由变更影响面核查与独立 Review 把关。

---

## 4. ⛔ 核心红线与负向规范 (Negative Invariants)

1. **⛔ 严禁 404 断链**：所有相对链接必须显式保留 `.md` 物理后缀，严禁裸路由、本地 `file:///` 绝对路径或失效相对路径；指向目录的链接要求目标目录含 `index.md` 或 `README.md`；
2. **⛔ 严禁跨象限职责混淆**：技术参考（Reference）只记录冷峻事实，严禁加入教程或背景说理；操作指南（How-To）直奔步骤，理论分析外链至 Explanation；
3. **⛔ 严禁瀑布生命周期旧目录**：严禁创建 `docs/requirements/`、`docs/design/`、`docs/planning/` 等旧时代目录，必须归入对应 Diátaxis 象限；
4. **⛔ 严禁文件命名随意混乱**：新项目与新增标准文档一律采用纯小写 `kebab-case` 命名风格（如 `goal-loop-design.md`），禁止驼峰与无规则空格（已有历史中文命名除外）；
5. **⛔ 严禁伪造文档状态（RFC-0007）**：控制头 `文档状态` 只允许 `Active` / `Contested` / `Superseded`（缺省视同 `Active`）；`Superseded` 必须填写仓库内真实有效的 `.md` 相对路径 `取代于`（非自身且不越出仓库根）；`Active`（含隐式 `Active`）不得携带 `取代于`；`Contested` 建议填写 `争议点`；
6. **⛔ 严禁文档体量失控（RFC-0008）**：单文档 `> 64 KB`（65,536 字节）或最长单行 `> 1,000` 字符即阻断；行数 `> 800` 仅警告。超限时必须采用总纲-子册拆分或语义换行，不得豁免。

---

## 4.1 豁免边界与执行口径 (Exemptions & Gate Protocol)

为避免结构性规则误伤特定性质文件，以下目录/文件享有明文登记的豁免边界：

| 范围 | 豁免项 | 理由与约束 |
| :--- | :--- | :--- |
| **`docs/project/reviews/**`** | 断链扫描（`--exclude project/reviews`）、体量三指标、状态机、控制头（G-20） | **Write-Once 交付凭据归档**（RFC-0001）：报告逐字原文落盘以保护 SHA256 指纹，不得改写；归档索引 `README.md` 的结构化字段由 `dual-round-review` 的 `check-review-report.py` 校验，其控制头与清单链接属可读性约定。 |
| **`docs/reference/articles/**`** | 体量三指标（RFC-0008）、控制头（G-20） | 外部权威文献逐字转载，原文结构与篇幅不可人为裁切或注入控制头。 |
| **`docs/project/backlog/**`** | 文档三态状态机（RFC-0007）、G-20 标准控制头 | 卡片使用 YAML frontmatter 的生命周期 `status`（`planned`/`in-progress`/`completed`），与文档三态正交。 |
| **`docs/AGENTS.md`** | G-20 标准控制头、RFC-0008 体量上限 | 路由规则文件受专属 `≤30 行` 与必需小节（`读取顺序`、`硬约束`）守卫；**断链扫描仍覆盖它**。 |

* **门禁执行口径（BK-0048）**：3 道本仓私有门禁由 `scripts/doc-gates/check-all.py` 聚合，推荐通过 `git config core.hooksPath .githooks` 安装 pre-commit hook；临时跳过使用 `git commit --no-verify` 时**必须在提交信息登记原因**。CI 直接调用 `python3 scripts/doc-gates/check-all.py --full`。
* **可回答性 GAP 口径（BK-0049）**：`check-golden-tasks.py` 输出 `GAP` 表示知识库确实缺该块内容，**不得**为消 GAP 临时堆砌空壳文档——应使用 `scripts/backlog/manage-backlog.py` 登记卡片排期；`FAIL` 为结构缺陷，必须立即修复。
* **历史 RFC 原位保留原则**：已被 `Superseded` 或 `Implemented` 的提案，若仍被 `docs/project/reviews/` 等 Write-Once 凭据以相对路径引用，必须原位保留不删除不移动，仅流转其控制头状态与 `[!IMPORTANT]` 防腐说明。
