# 文档-代码全向联动维护矩阵 (Change Impact Matrix Protocol)

> **控制信息**
> - **规范版本**: V2.0.0
> - **核心原则**: 严禁孤立修改，代码与契约必须双向闭环同步；路径按宿仓既有约定映射（以下以 Diátaxis 拓扑为例）
> - **适用范围**: 所有涉及功能演进、接口调整与重构任务的代码交付门禁

---

## 1. 核心铁律：代码与文档全向闭环

在 AI 辅助研发与团队协作中，“代码改了但文档没改”或“文档改了但代码没跟进”是造成架构腐蚀与幻觉的根源。
实行**双向联动触发机制**：
* **正向演进**：代码落地 ➔ 自动触发关联文档的契约同步、变更日志记录与 Issue 状态闭环；
* **反向驱动**：需求/契约修改 ➔ 必须先行更新文档并作为测试/编码基准，严禁代码已变而契约脱节。

---

## 2. 变更联动触发矩阵表 (Change Impact Matrix)

| 代码或资产变更特征 | 涉及物理路径示例 | 必须同步更新的文档集合 | 验收与门禁标准 (Exit Criteria) |
|:---|:---|:---|:---|
| **新增/调整业务功能与规则** | `src/lib/services/*`<br>`src/rules/*` | 1. `docs/reference/rules/`（或宿仓规则文档）<br>2. 宿仓 `CHANGELOG.md` / 变更日志与关联 Issue | 业务规则/状态机描述更新，变更日志与关联 Issue 状态同步闭环。 |
| **调整 API 接口契约** | `src/controllers/*`<br>`src/api/*`<br>`src/routes/*` | 1. `docs/reference/api/`<br>2. `docs/reference/models/` | Endpoint、方法签名、请求/响应 Payload 字段、错误信封 100% 一致。 |
| **调整数据模型与数据库实体** | `src/models/*`<br>`src/entities/*`<br>`prisma/schema.prisma` | 1. `docs/reference/models/`<br>2. `docs/reference/api/` (若影响响应结构) | 字段命名、类型定义（nullable/optional）、枚举值严格对齐，零遗漏。 |
| **前端页面、组件与设计 Token** | `src/components/*`<br>`src/styles/tokens.css`<br>`src/app/*` | 1. `docs/reference/ui/`<br>2. `docs/how-to/` (若涉及新页面操作流) | 设计 Token 变量名一致，组件 Props 与事件契约更新，无虚构组件。 |
| **核心架构、框架与基础设施** | `src/core/*`<br>`package.json`<br>`docker-compose.yml` | 1. `docs/explanation/architecture/`<br>2. `docs/explanation/decisions/` (新建 MADR)<br>3. `docs/explanation/analysis/` | 记录架构分层演进、选型评估对比与 Append-Only MADR 决策记录。 |
| **部署配置、环境与调试脚本** | `.env.example`<br>`Dockerfile`<br>`scripts/deploy.sh` | 1. `docs/how-to/deployment.md`<br>2. `docs/how-to/local-setup.md` | 环境变量清单 100% 完整，部署与启动命令在干净环境中可复现。 |
| **文档拓扑变动 (增/删/重命名)** | `docs/**/*.md` | 1. 宿仓根级总索引（如 `docs/index.md` 或导航配置）<br>2. 受影响目录的入口（按需维护的 `index.md` / `README.md`）<br>3. 所有上游引用文件相对路径 | 运行宿仓断链/文档门禁（或兜底 `check-doc-links.py`）严格 Exit Code 0，全局零 404 断链。 |

---

## 3. 伴随式联动操作标准作业程序 (Sync SOP)

在完成代码编写并通过本地测试后、准备提交 Git 前，执行以下四步：

### 步骤 1：检视 Git Diff 推导影响面
```bash
git diff --name-only HEAD~1
# 或检视当前工作区/暂存区改动
git status -s
```
根据输出的文件路径，在上方矩阵中定位对应的文档类别（若宿仓采用非 Diátaxis 目录，按职责映射到宿仓既有对应目录）。

### 步骤 2：同步对应契约、架构与 MADR
- 若修改了接口字段或数据模型，同步更新对应的 `reference/api/` 或 `reference/models/`；
- 若改变了业务规则或操作流程，同步更新 `reference/rules/` 或 `how-to/`；
- 若涉及不可逆技术选型或架构分层演进，在 `explanation/decisions/` 追加新的 MADR 3.0 记录。

### 步骤 3：更新宿仓 Changelog 与关联 Issue
- 在宿仓 `CHANGELOG.md`（或 `docs/project/changelog.md`）当前未发布版本段落追加变更摘要；
- 更新关联 Issue / PR 的验收状态与文档链接（历史版本与修改时间由 Git 原生提交记录承载，无需手写文档修订历史表）。

### 步骤 4：运行文档规范与断链检查器（Exit 0）
- 优先运行宿仓已配置的文档校验命令（如 `lychee`、`markdownlint-cli2`、`vale`、`mkdocs build --strict` 等）；
- 若宿仓未配备专用工具，运行零依赖兜底扫描器：
```bash
python3 scripts/check-doc-links.py --root <docs_root> [--exclude <rel_dir>]
```
必须返回 `Exit Code 0` 后方可进行 `git commit`；若因故跳过某项同步，须按 [change-registration.md](../templates/change-registration.md) 显式登记理由。
