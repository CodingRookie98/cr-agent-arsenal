# 文档-代码全向联动维护矩阵 (Change Impact Matrix Protocol)

> **控制信息**
> - **规范版本**: V1.0.0
> - **核心原则**: 严禁孤立修改，代码与契约必须双向闭环同步
> - **适用范围**: 所有涉及功能演进、接口调整与重构任务的代码交付门禁

---

## 1. 核心铁律：代码与文档全向闭环

在大模型编程与团队协作中，“代码改了但文档没改”或“文档改了但代码没跟进”是造成架构腐蚀与 AI 幻觉的根源。
本项目实行**双向联动触发机制**：
* **正向演进**：代码落地 ➔ 自动触发关联文档的契约同步、待办关闭与版本更新；
* **反向驱动**：需求/契约修改 ➔ 必须先行更新文档并作为测试/编码基准，严禁代码已变而契约脱节。

---

## 2. 变更联动触发矩阵表 (Change Impact Matrix)

| 代码或资产变更特征 | 涉及物理路径示例 | 必须同步更新的文档集合 | 验收与门禁标准 (Exit Criteria) |
|:---|:---|:---|:---|
| **新增/调整业务功能与规则** | `src/lib/services/*`<br>`src/rules/*` | 1. `docs/reference/rules/`<br>2. `docs/project/changelog.md`<br>3. `docs/project/backlog.md` | 业务规则/状态机图更新，发布日志记录 Commit SHA，对应待办状态置为已完成。 |
| **调整 API 接口契约** | `src/controllers/*`<br>`src/api/*`<br>`src/routes/*` | 1. `docs/reference/api/`<br>2. `docs/reference/models/` | Endpoint、HTTP Method、请求/响应 Payload 字段、错误信封 100% 镜像一致。 |
| **调整数据模型与数据库实体** | `src/models/*`<br>`src/entities/*`<br>`prisma/schema.prisma` | 1. `docs/reference/models/`<br>2. `docs/reference/api/` (若影响响应结构) | 字段命名、类型定义（nullable/optional）、枚举值严格对齐，零遗漏。 |
| **前端页面、组件与设计 Token** | `src/components/*`<br>`src/styles/tokens.css`<br>`src/app/*` | 1. `docs/reference/ui/`<br>2. `docs/how-to/` (若涉及新页面操作流) | 设计 Token 变量名一致，组件 Props 与事件契约更新，无虚构组件。 |
| **核心架构、框架与基础设施** | `src/core/*`<br>`package.json`<br>`docker-compose.yml` | 1. `docs/explanation/architecture/`<br>2. `docs/explanation/decisions/` (新建 MADR)<br>3. `docs/explanation/analysis/` | 记录架构分层演进、选型评估对比与 MADR 决策记录。 |
| **部署配置、环境与调试脚本** | `.env.example`<br>`Dockerfile`<br>`scripts/deploy.sh` | 1. `docs/how-to/deployment.md`<br>2. `docs/how-to/local-setup.md` | 环境变量清单 100% 完整，部署与启动命令在干净环境中可复现。 |
| **文档拓扑变动 (增/删/重命名)** | `docs/**/*.md` | 1. `docs/index.md` (全局人类索引)<br>2. `docs/llms.txt` (智能体机器地图)<br>3. 所有上游引用文件相对路径 | 运行 `check-doc-links.py` 严格 Exit Code 0，全局零 404 断链。 |

---

## 3. 伴随式联动操作标准作业程序 (Sync SOP)

在完成代码编写并通过本地测试后、准备提交 Git 前，执行以下三步：

### 步骤 1：扫描代码 Diff 推导影响面
```bash
git diff --name-only HEAD~1
# 或当前未提交的代码
git status -s
```
根据输出的文件路径，在上方矩阵中检索对应的文档类别。

### 步骤 2：精准同步受影响文档
1. **契约镜像同步**：如果是修改了字段名，打开对应的 `reference/api/` 或 `reference/models/`，将变更行更新；
2. **待办闭环**：打开 `docs/project/backlog.md`，将对应编号的条目从 `[ ] 进行中` 更新为 `[x] 已完成 (Commit SHA)`；
3. **日志追加**：打开 `docs/project/changelog.md`，在当前未发布的版本段落中追加一条变更陈述；
4. **版本号与滑动修订记录**：
   - 检查被修改文档的头部 Frontmatter，根据语义化版本升级（破坏性升 Major，新增功能升 Minor，补丁修正升 Patch）；
   - 在修订历史表格追加一行，并确保表格**总行数不超过 5 行**（超额需裁剪最早一行）。

### 步骤 3：断链与健康静态验证
```bash
# 验证全局链接合法性
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
```
必须返回 Exit Code 0 方可进行 `git commit`。
