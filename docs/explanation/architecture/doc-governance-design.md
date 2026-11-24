# `doc-governance` 文档工程与知识库治理技能架构设计书 (Architecture & Design Specification)

> **文档控制信息**
> - **文档标识**: SKILL-DES-DOC-GOVERNANCE-2026
> - **当前版本**: V3.0.0 (Wave 2C 三刀切割：公共技能回归 Convention-First 轻内核，私有门禁与待办工具迁至仓库根 `scripts/`)
> - **文档状态**: Active
> - **设计所有者**: 王辉
> - **设计架构师**: Antigravity AI Agent
> - **创建日期**: 2026-09-10
> - **生效日期**: 2026-11-24
> - **参考基准**:
>   - [skills/doc-governance/SKILL.md](../../../skills/doc-governance/SKILL.md) —— 公共技能规程唯一入口（Convention-First 写作与联动规程 + `--exclude` 断链扫描）
>   - [ADR-0005 物理切割公共技能与本仓私有门禁](../decisions/0005-split-doc-governance-public-vs-repo-local.md) —— V3.0 三刀公私分离架构裁决
>   - [架构重构评估报告](../analysis/2026-11-23-doc-governance-architecture-evaluation.md) —— V2.x 598.6 KB 巨石体检与治理税实证
>   - [Wave 2C 实施计划](../../project/plans/2026-11-24-wave2c-doc-governance-v3.md) —— V3.0 物理切割重构实施基线

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V3.0.0** | 2026-11-24 | AI Agent | 王辉 | **Wave 2C 三刀切割（ADR-0005）**：移除 `代码锚点`/`复核于` 字段；公共技能瘦身为 Convention-First 轻内核 + 通用 `--exclude` 断链扫描；本仓私有门禁下沉 `scripts/doc-gates/`，Backlog 拆至 `scripts/backlog/`；退役 9 个高税/私有脚本与 `llms.txt`/`_llms/` |
| **V1.5.0** | 2026-11-23 | DSH AI Agent | 王辉 | 治理轴扩展成文：补 `_llms/`、`AGENTS.md`、`plans/`、`reviews/`、形态 B backlog 与五条治理轴（已由 V3.0.0 重构分离） |
| **V1.4.0** | 2026-11-22 | DSH AI Agent | 王辉 | 新增真值轴（RFC-0005）：控制头三字段与 `check-doc-drift.py` 五态判定（已于 V3.0.0 退役） |
| **V1.3.0** | 2026-10-09 | AI Agent | 王辉 | 增补目录级索引约定（RFC-0003）与 `manage-doc-index.py`（已于 V3.0.0 退役） |

---

## 1. 背景与核心痛点 (Problem Statement)

在 AI 智能体工程实践中，文档既是人类工程师的知识沉淀，也是智能体规划、契约对齐与编码的上下文真相源。围绕文档治理，系统需要同时解决两类正交问题：

1. **通用的文档工程方法论问题**：消除「需求/设计/规划」瀑布目录混杂，贯彻 Diátaxis 四象限内容纯度、RFC 孵化到 Diátaxis 结晶、MADR 3.0 不可逆决策记录、代码变更联动触发，以及零 404 物理断链保障；
2. **公共技能与单仓私有治理的边界失控问题（Wave 2C 根治）**：V1.x–V2.x 将本仓私有 CI 断言（20 条黄金可回答性测试）、强绑定中文控制头的千行审计巨石、1,500+ 行 Mini-Jira 待办系统与高摩擦同步生成物（`llms.txt` / `_llms/`、`复核于 SHA` 真值轴、5 行修订表裁剪）全部塞入公共技能 `skills/doc-governance/`，导致其膨胀至 **598.6 KB / 32 文件 / 3 个超千行巨石**，跨仓可移植度塌方并制造高昂的文档治理税。

---

## 2. 理论源流与核心原则 (Theoretical Foundations)

1. **Convention-First（先适配宿仓）**：公共技能进入新仓库时，先识别宿仓既有文档目录规范、静态检查工具（如 `lychee`、`markdownlint-cli2`、`vale`）与 Git 原生变更历史，拒绝强行覆盖或引入冗余仪式；
2. **Diátaxis 四象限正交分类**：严格按读者即时心智划分 `tutorials/`（学习）、`how-to/`（任务步骤）、`reference/`（权威事实）、`explanation/`（原理解析），严禁单文档跨象限混写；
3. **RFC → Diátaxis 两阶段演进**：高变动的探索期特性先在 `proposals/RFC-XXXX-*.md` 单文件自洽对齐（`Draft → In Review → Accepted`），定案后解构下沉至稳态 Diátaxis 目录，原 RFC 标注 `Implemented` 或 `Superseded` 防腐保留；
4. **MADR 3.0 Append-Only 决策流**：重大架构权衡沉淀于 `explanation/decisions/NNNN-*.md`，不可原地篡改，演进采用新 ADR 显式 `Supersedes`；
5. **变更影响面联动与零断链底线**：API/模型/规则/架构变更时同步评估关联文档，相对链接必须显式保留 `.md` 后缀，杜绝裸路由与失效绝对路径。

---

## 3. V3.0 公私分离架构（三刀切割，ADR-0005）

依据 [ADR-0005](../decisions/0005-split-doc-governance-public-vs-repo-local.md)，V3.0 将原单体「God Skill」按可复用边界物理切分为互不寄生、职责单一的三层：

```text
cr-agent-arsenal/
├── skills/doc-governance/       # 【第一层：公共可复用技能（Convention-First）】
│   ├── SKILL.md                 # 精简核心规程（≤120 行）：工作流、Diátaxis/RFC/MADR 准则与影响矩阵
│   ├── references/              # 可按需加载的方法论参考库（四象限 / RFC 结晶 / MADR / 命名 / 联动 / 迁移）
│   ├── templates/               # 通用变更联动登记模板（change-registration.md）
│   └── scripts/check-doc-links.py  # 零依赖通用断链扫描器（支持可重复 --exclude <rel_prefix>）
│
├── scripts/doc-gates/           # 【第二层：本仓私有文档门禁（仅服务 cr-agent-arsenal）】
│   ├── check-all.py             # pre-commit 与 CI 聚合入口：顺序执行 3 道门禁（--full 追加 pytest）
│   ├── check-doc-health.py      # 本仓健康体检：RFC-0007 三态、RFC-0008 体量上限、docs/AGENTS.md 30 行守卫
│   └── check-golden-tasks.py    # 本仓 20 条可回答性机械断言（G-18 校验 docs/index.md 象限导航）
│
└── scripts/backlog/             # 【第三层：本仓私有 Mini-Jira 待办管理】
    ├── manage-backlog.py        # 形态 B 待办目录（index.md + active/ + archive/）自动化管理
    └── README.md                # 本仓待办契约与生命周期说明
```

### 3.1 第一刀：公共技能纯化（`skills/doc-governance/`）

* **方法论轻内核**：`SKILL.md` 聚焦可跨任何语言/仓库复用的原则——优先适配宿仓工具链与 Git 历史，仅在缺乏成熟工具时提供零依赖兜底；
* **通用断链与锚点扫描器 `check-doc-links.py`**：
  * 剥离硬编码的 `project/reviews` 路径特判，改为可重复 `--exclude <rel_prefix>` 参数（越界 `..` 或非法前缀直接 `exit 2` fail-closed）；
  * 严格按开围栏字符与长度配对闭合多反引号/波浪线代码块，忽略行内代码示例；
  * 校验相对链接目标存在性、`.md` 物理后缀、目录入口（`index.md` / `README.md`）与 `#anchor` 标题 Slug。

### 3.2 第二刀：待办管理拆出（`scripts/backlog/`）

* 将与通用文档工程正交的形态 B 文件型待办管理系统（`manage-backlog.py` 与 `README.md`）彻底移出 `skills/doc-governance/`；
* 外部业务仓默认沿用各自的 GitHub Issues / Linear 等平台，不再被迫继承跨界补丁与额外文件。

### 3.3 第三刀：本仓私有门禁瘦身与去仪式税（`scripts/doc-gates/`）

本仓通过 `check-all.py`（`.githooks/pre-commit` 默认入口）顺序执行 **3 道低摩擦、无重复读盘的硬门禁**：

1. **通用断链扫描**：调用公共 `skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews`；
2. **精简健康检查 `check-doc-health.py`**：
   * **RFC-0007 三态状态机**：校验 `Active` / `Contested` / `Superseded` 取值与 `取代于` 仓库内 `.md` 相对路径有效性；
   * **RFC-0008 体量硬限**：单文档字节 `≤ 65,536`（64 KB）与最长单行 `≤ 1,000` 字符（行数 `> 800` 仅警告），严格落实 `reference/articles/**` 豁免；
   * **路由文件守卫**：校验 `docs/AGENTS.md` `≤ 30` 行且包含「读取顺序」与「硬约束」两节；
3. **可回答性评测 `check-golden-tasks.py`**：校验 20 条知识库结构与检索可达性断言（`G-18` 校验人类总入口 `docs/index.md` 象限导航；`FAIL` 阻断，`GAP` 登记 backlog）；`--full` 模式追加运行 `pytest skills/ scripts/ -q`。

**同步退役的低 ROI 机制**：废除强制手写 5 行修订表一致性校验、2,516 行自激重钉型代码锚点漂移检测（`check-doc-drift.py` 与 `.doc-truth-baseline.json`）、同步刷盘型分层机器地图（`generate-llms-txt.py`、`docs/llms.txt`、`docs/_llms/`）、托管索引脚本与中文模板生成器（`manage-doc-index.py`、`scaffold-doc.py/.sh`）及空体量基线（`.doc-size-baseline.json`）。知识库导航统一收敛为「`docs/AGENTS.md`（≤30 行路由）→ `docs/index.md`（全局总索引）→ 按需人工/Agent 维护的象限 `index.md` → 正文」。

---

## 4. 知识库目录职责矩阵 (Repository Topology Reference)

| 目录层级 | Diátaxis 定位 | 核心职责与唯一真相源 | 常见豁免（见 [GOVERNANCE.md](../../GOVERNANCE.md) §4.1） |
| :--- | :--- | :--- | :--- |
| `proposals/` | Inception | 初期高变动需求/方案单文件对齐；有历史审查引用的已定案/被取代 RFC 原位保留 | — |
| `tutorials/` | Tutorials | 新人上手成功路径，按需人工维护 `index.md` | — |
| `how-to/` | How-To Guides | 面向具体任务的操作 SOP 与排障手册 | — |
| `reference/` | Reference | 对外规则、模型、API 契约与外部文献（`articles/`） | `reference/articles/**` 豁免体量与控制头 |
| `explanation/` | Explanation | 系统设计书（`architecture/`）、MADR 决策（`decisions/`）、调研评估（`analysis/`） | `decisions/` 采用 MADR 元数据头 |
| `project/` | Project Mgmt | 发布日志（`changelog.md`）、计划（`plans/`）、审查凭据（`reviews/`）、待办（`backlog/`） | `reviews/**` 全豁免；`backlog/**` 豁免文档状态机 |

---

## 5. 演进与兼容性保障 (Evolution & Compatibility)

* **公共技能零私有泄漏**：`skills/doc-governance/` 不含任何本仓相对路径（如 `docs/reference/rules/`）或私有文件型待办假设，可零修改分发至任意外部仓库；
* **历史审查凭据零破坏**：`RFC-0003`、`RFC-0005`、`RFC-0006` 原位保留并流转状态为 `Superseded`（指向 [ADR-0005](../decisions/0005-split-doc-governance-public-vs-repo-local.md)），保障 `docs/project/reviews/` 历史归档中所有相对链接永久有效且逐字不改。
