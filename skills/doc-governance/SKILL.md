---
name: doc-governance
description: Convention-first documentation governance skill using the Diátaxis framework, RFC-to-Crystallization lifecycle, Append-Only MADR 3.0 architecture decisions, and change-impact synchronization. Use when structuring docs, aligning RFC proposals, maintaining API/model contracts via git diff, migrating legacy docs, or verifying markdown links.
license: MIT
---

# 文档工程与知识库治理 (Documentation Governance)

面向软件工程与 AI 智能体协作的 **Convention-First** 轻量化文档治理体系，聚焦高信噪比结构与联动纪律，不强加冗余文档税。

## 1. Convention-First 优先原则（操作既有项目必读）

在新建、修改或重构任何文档前，**先侦察宿仓现状**，尊重既有约定：
1. **目录与导航约定**：若宿仓已有明确的文档目录（如 `docs/guides/`、`docs/api/`、`mkdocs.yml`）或根索引，沿用宿仓拓扑；仅在 **0-to-1 新建**或**结构混乱需重构**时引入标准 Diátaxis 四象限布局。
2. **语言与命名习惯**：继承宿仓既有的正文语言与文件命名风格（见 [language-naming-conventions.md](references/language-naming-conventions.md)）。
3. **工具链与 Git 原生历史**：版本演进与变更溯源优先依赖 Git 原生历史（`git log` / `git diff` / `CHANGELOG.md`）与宿仓 Issue 平台，不强加手写版本号或修订历史表。若宿仓已配置 `lychee`、`markdownlint-cli2`、`vale` 或 `mkdocs build --strict` 等检查器，优先运行既有工具。

---

## 2. 适用边界 (Scope)

- **应当触发**：新增/变更/废弃 API 契约、数据模型、业务规则或状态机；重大架构选型需留存 ADR；立项期提案（RFC）孵化与定案结晶；旧文档目录重构迁移；交付前断链核查。
- **无需触发**：不改变外部行为契约的纯内部实现重构、拼写修正或临时草稿。

---

## 3. 四大核心资产与 0-to-1 推荐拓扑

| 资产支柱 | 核心职责 | 权威规程 |
|:---|:---|:---|
| **Diátaxis 四象限** | 按读者心智隔离 `tutorials` / `how-to` / `reference` / `explanation` | [diataxis-standard.md](references/diataxis-standard.md) · [language-naming-conventions.md](references/language-naming-conventions.md) |
| **RFC 孵化-结晶流** | 草案期单文件高内聚对齐，定案后解构下沉至稳态象限并防腐封存 | [rfc-crystallization-lifecycle.md](references/rfc-crystallization-lifecycle.md) |
| **Append-Only MADR 3.0** | 重大技术决策只追加不篡改，推翻旧决策须新建 `Supersedes` ADR | [adr-specification.md](references/adr-specification.md) |
| **变更联动与平滑迁移** | 基于 `git diff --name-only` 同步契约/指引；用 `git mv` 渐进迁移旧目录 | [change-impact-matrix.md](references/change-impact-matrix.md) · [change-registration.md](templates/change-registration.md) · [legacy-migration-guide.md](references/legacy-migration-guide.md) |

```text
docs/                         # 0-to-1 绿色新建推荐拓扑（已有约定以宿仓为准）
├── index.md                  # 根级人类总入口（子目录按需放置 index.md 或 README.md）
├── proposals/                # 孵化期提案（Draft -> In Review -> Accepted -> Implemented）
├── tutorials/                # 新手上手教程（Learning-Oriented）
├── how-to/                   # 任务型操作手册（Problem-Oriented）
├── reference/                # 权威技术事实真相源：api/、models/、rules/、ui/
└── explanation/              # 深度剖析与架构演进：architecture/、decisions/ (MADR)
```

---

## 4. 核心工作流 (Workflows)

### 模式 A：伴随式变更联动 (Change-Impact Sync)
1. 运行 `git diff --name-only`（或 `git status -s`）识别代码变更路径；
2. 对照 [change-impact-matrix.md](references/change-impact-matrix.md) 同步受影响的 `reference/` 契约、`how-to/` 操作说明或 `explanation/decisions/` MADR 记录；
3. 按宿仓规范更新 `CHANGELOG.md`（或项目变更日志）与关联 Issue，重大变更可按 [change-registration.md](templates/change-registration.md) 留存影响面与门禁证据；
4. 运行宿仓文档门禁（或兜底断链扫描器）至 `Exit Code 0`。

### 模式 B：RFC 孵化、定案结晶与旧目录迁移
1. **立项孵化**：未定型设计集中于单篇 RFC 草案对齐边界、术语表与默认假设，严禁直接写入 `reference/`；
2. **结晶归档**：方案 `Accepted` 后将契约、规则、MADR 与操作指引下沉至对应象限，原 RFC 置为 `Implemented` 并附归档提示（若已有历史审查凭据以相对路径引用该提案，应原位保留以免断链）；
3. **旧目录迁移**：按 [legacy-migration-guide.md](references/legacy-migration-guide.md) 用 `git mv` 分模块小步迁移，同步更新引用路径与总索引。

### 模式 C：零依赖物理断链兜底校验
当宿仓未配置 `lychee` 等成熟链接校验器时，运行本技能自带的零依赖静态扫描器（校验相对路径、目录入口 `index.md`/`README.md`、`.md` 后缀与 `#anchor` 标题锚点，自动忽略行内代码及围栏代码块）：

```bash
python3 scripts/check-doc-links.py --root <docs_root> [--exclude <rel_dir>]
```

* `--dir <rel_path>`：收窄扫描至指定子目录或单文件（可重复；越界或不存在返回 Exit 2）；
* `--exclude <rel_prefix>`：跳过指定根内相对前缀，如只读历史审查归档（可重复；禁止绝对路径或 `..` 越界，fail-closed 返回 Exit 2）；
* `--no-strict-ext`：允许省略 `.md` 后缀（仅用于兼容特定静态站点）。

---

## 5. 不可妥协红线 (Invariants)

1. **⛔ 象限隔离与真相源纯洁**：严禁在 `reference/` 中夹带操作教学、原理辩论或未定案草案；
2. **⛔ 决策不可原地篡改**：已 `Accepted` 的 ADR 严禁改写历史结论，演进必须通过新 ADR 的 `Superseded` 链衔接；
3. **⛔ 零断链与显式相对引用**：文档内相对路径须保持物理可达并显式保留 `.md` 后缀（宿仓另有路由规则除外），目录链接目标须包含 `index.md` 或 `README.md`；
4. **⛔ 宣称与取证同宽**：未实际运行校验命令不得宣称断链清零或文档已同步。
