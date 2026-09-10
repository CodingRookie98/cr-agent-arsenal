# 项目语言习惯与文件命名规范 (Language Habit & File Naming Conventions)

> **控制信息**
> - **规范版本**: V1.0.0
> - **核心原则**: 尊重既有工程语言习惯，初期命名规范统一，消除歧义与割裂
> - **适用范围**: 通用软件工程文档库与 AI 智能体跨系统协作

---

## 1. 语言习惯继承铁律 (Language Continuity Rule)

在人机协作和多智能体交互中，**语言的随意切换是导致上下文理解阻抗与术语割裂的核心元凶**。必须严格遵循以下原则：

### 1.1 尊重并继承既有工程语言基线
* **中文主导工程（如本工程及多数国内开源协作项目）**：
  - 若项目中既有文档、需求设计、架构说明和注释以**中文**为主，后续所有新增、修改、重构的文档**必须统一使用中文**进行正文阐述；
  - 严禁在中文主导的工程中无故输出大段纯英文设计文档，破坏团队阅读与评审体验。
* **英文主导工程（如国际化开源社区）**：
  - 若项目既有文档为纯英文，则后续新增文档严格保持纯英文。
* **反割裂要求**：
  - 同一模块或同类文档中，严禁出现一份中文、一份英文的无序混杂；保持整个知识库的语言一致性。

### 1.2 概念与术语正交分离 (Orthogonal Separation)
* **业务与架构叙述（主语言）**：背景痛点、场景分析、设计哲学、操作步骤、权衡对比等使用项目主语言（如中文）；
* **机械实体与技术标识符（标准英文）**：
  - 代码类名、函数名、数据模型字段名（如 `userId`, `templateStatus`）；
  - HTTP 动词与 API 路径（如 `POST /api/v1/workspaces`）；
  - JSON Schema 键名与 HTTP 状态码；
  - Git Commit Conventional 规范前缀（`feat:`, `fix:`, `docs:` 等）。
* **严禁硬译**：严禁对技术业界公认的标识符进行生硬音译或字面直译（例如严禁将 `Reducer` 直译为“规约器”，代码实体中保持其原汁原味的英文命名）。

---

## 2. 文件命名规范 (File Naming Conventions)

### 2.1 项目初期 (0-to-1 Inception Phase)
在全新项目立项或无既有历史包袱的阶段，**文件命名优先推荐使用全小写中划线 (kebab-case) 英文风格**：
* **为什么初期优先英文 kebab-case？**
  1. **跨平台与文件系统兼容性**：Linux（大小写敏感）、macOS（默认大小写保留但不敏感）、Windows（大小写不敏感）在处理非 ASCII 字符或大小写混合时存在隐蔽冲突；kebab-case 是跨平台移植的最稳健方案；
  2. **URL 与 Web 路由友好**：当文档被 VitePress、Docusaurus、Nextra 等 Docs-as-Code 工具渲染为静态站点时，纯英文 kebab-case 无需 URL 转码，生成的链接清晰自然（如 `/docs/how-to/quick-start`）；
  3. **终端与自动化脚本兼容**：在 Bash、Python 自动化脚本扫描与 Git 命令中，无需复杂的特殊字符转义。

* **初期典型命名范式**：
  - 教程类：`quick-start.md`, `onboarding.md`
  - 操作类：`deployment.md`, `local-setup.md`, `troubleshooting.md`
  - 契约类：`api-contracts.md`, `task-tree-schema.md`
  - 提案类：`rfc-0001-canvas-collab.md`
  - 决策类：`0001-use-zustand.md`

### 2.2 既有项目与用户倾向确认 (Respect Existing & Inquire on Ambiguity)
* **尊重既有中文命名体系**：
  - 如果目标工程已经建立了成体系的中文文件命名习惯（如 `前端功能设计文档.md`、`视觉设计规范.md`、`系统业务规则文档.md`），智能体**必须优先遵循项目既有风格**，切忌盲目发起大规模重命名；
  - 既有项目的文件重命名可能引发大面积的断链与 Git 历史断裂，如经深入分析确有重构必要，必须与用户对齐；
* **模糊与争议场景的询问机制 (Inquire on Ambiguity)**：
  - 当项目处于初期过渡阶段、既有命名风格模糊、或存在中英文混合分歧时，智能体**严禁擅自做主**，应主动向用户呈现选项并征求意见：
    > “检测到当前项目存在部分中文命名与英文命名文件。针对即将新建的文档，您更倾向于使用英文 kebab-case（如 `quick-start.md`）还是语义化中文（如 `快速上手指南.md`）？”

---

## 3. 中英文文件命名映射与建议对照表

| Diátaxis 象限 | 英文 kebab-case 规范 (初期推荐) | 既有中文体系对照 (既有项目兼容) |
|:---|:---|:---|
| **`tutorials/`** | `quick-start.md`<br>`onboarding.md` | `快速上手指南.md`<br>`新手接入向导.md` |
| **`how-to/`** | `deployment.md`<br>`local-setup.md`<br>`troubleshooting.md` | `部署运维手册.md`<br>`本地联调环境搭建.md`<br>`故障排查手册.md` |
| **`reference/`** | `api-specification.md`<br>`data-models.md`<br>`business-rules.md` | `后端API接口规格.md`<br>`领域数据模型.md`<br>`系统业务规则文档.md` |
| **`explanation/`** | `architecture-overview.md`<br>`framework-evaluation.md` | `系统总体架构设计.md`<br>`智能体框架选型评估.md` |
| **`proposals/`** | `rfc-0001-agent-canvas.md` | `RFC-0001-画布协作提案.md` |
