# 项目待办与后续演进清单 (Backlog Index)

> **文档控制信息**
> - **文档标识**: BK-INDEX-GOV
> - **当前版本**: V2.0.0 (动态索引)
> - **维护模式**: 机器脚本自动化生成 (请勿手写对账日记，运行 `manage-backlog.py sync-index` 自动刷新)
> - **更新日期**: 2026-11-23

---

## 1. 待办健康度仪表盘 (Metrics Dashboard)

- **现役活跃待办**: **2** 项 (进行中: 0, 计划中: 2)
- **历史已归档项**: **54** 项 (物理归档于 `archive/` 目录)

| 优先级 | P0 (阻断级) | P1 (高优) | P2 (中优) | P3 (低优) |
| :--- | :--- | :--- | :--- | :--- |
| **活跃数量** | 0 | 0 | 1 | 1 |

---

## 2. 🔄 进行中待办 (In Progress)

*(当前暂无进行中的待办)*

---

## 3. 📋 计划中待办 (Planned Backlog)

| 编号 | 优先级 | 类型 | 标题 | 触发条件 | 卡片入口 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0056** | `P2` | `TechDebt` | 技能哨兵轻量加固与口径对齐（R1-1/R1-2/R1-3/R1-5） | 下次修改 skills/_shared/tests/test_skill_surface_sentinels.py 或新增第 8 个技能时 | [BK-0056](./active/BK-0056-技能哨兵轻量加固与口径对齐-r1-1-r1-2-r1-3-r1-5.md) |
| **BK-0051** | `P3` | `Governance` | 检索层决策：当前不引入 MCP（已评估） | 文档 >300 篇，或出现跨仓库检索需求，或出现非文件系统消费者 | [BK-0051](./active/BK-0051-检索层决策-当前不引入-mcp-已评估.md) |

---

## 4. 🗄️ 历史已结项归档 (Archive Summary)

> 共收录 54 条已关闭历史条目，详情参见 `archive/` 各版本目录。

| 编号 | 类型 | 标题 | 结项日期 | 结论 | 交付去向 | 归档卡片 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0050** | `TechDebt` | 存量超限文档拆分（spec-evolution / skill-scripts） | 2026-11-23 | delivered | 主册 52,355 B + task2/task3/task4-6 三子册；skill-scripts 40,438 B / 最长 854；体量基线清空 | [BK-0050](./archive/2026-Q4/BK-0050-存量超限文档拆分-spec-evolution-skill-scripts.md) |
| **BK-0055** | `TechDebt` | check-doc-drift --staged 残余风险：新增文档复核点判据与纯日期复核（BD-9） | 2026-11-23 | delivered | check-doc-drift.py 三处加固 + 4 条回归 + change-impact-matrix V1.3.1 | [BK-0055](./archive/2026-Q4/BK-0055-check-doc-drift-staged-残余风险-新增文档复核点判据与纯日.md) |
| **BK-0048** | `Governance` | 门禁自动化：pre-commit hook + 一键聚合脚本 | 2026-11-22 | delivered | check-all.py + .githooks/pre-commit + README 安装登记（提交 a0d5a4c 起） | [BK-0048](./archive/2026-Q4/BK-0048-门禁自动化-pre-commit-hook-一键聚合脚本.md) |
| **BK-0049** | `Feature` | 知识库可用性评测：20 条 golden task | 2026-11-22 | delivered | check-golden-tasks.py（20 条断言）+ check-all 第 6 道门禁；GAP 5 项已转 BK-0052/0053/0054 | [BK-0049](./archive/2026-Q4/BK-0049-知识库可用性评测-20-条-golden-task.md) |
| **BK-0052** | `Feature` | 知识库缺口：how-to 与 tutorials 象限为空 | 2026-11-22 | delivered | tutorials/quick-start.md + how-to/install-skills.md + how-to/run-doc-gates.md + how-to/troubleshoot-doc-governance.md | [BK-0052](./archive/2026-Q4/BK-0052-知识库缺口-how-to-与-tutorials-象限为空.md) |
| **BK-0053** | `Governance` | 知识库缺口：changelog 缺失与 3 篇 RFC 无落地计划链接 | 2026-11-22 | delivered | docs/project/changelog.md + RFC-0001/0002/0003 落地计划链接 | [BK-0053](./archive/2026-Q4/BK-0053-知识库缺口-changelog-缺失与-3-篇-rfc-无落地计划链接.md) |
| **BK-0054** | `TechDebt` | 知识库缺口：taste-driven-designer 缺架构设计书 | 2026-11-22 | delivered | docs/explanation/architecture/taste-driven-designer-design.md（185 行，含与文献原意的显式偏离） | [BK-0054](./archive/2026-Q4/BK-0054-知识库缺口-taste-driven-designer-缺架构设计书.md) |
| **BK-0005** | `Governance` | 豁免判定前执行路径根相对语义归一化 | 2026-11-19 | delivered | 78c73dc（--dir 作用域守卫 + 4 条回归 + GOVERNANCE 提示） | [BK-0005](./archive/2026-Q4/BK-0005-relative-to-root-path-normalization.md) |
| **BK-0006** | `TechDebt` | 四条审查护栏各补 1 条反证测试用例 | 2026-11-19 | delivered | e6fa6e6（豁免边界反证；其余三条复核已覆盖） | [BK-0006](./archive/2026-Q4/BK-0006-review-gates-negative-test-cases.md) |
| **BK-0009** | `Bug` | resolve_archive_dir 增加交付单元与请求 slug 一致性校验 | 2026-11-19 | delivered | e238a1f（交付单元一致性校验 + 2 条回归） | [BK-0009](./archive/2026-Q4/BK-0009-resolve-archive-dir-slug-consistency.md) |
| **BK-0012** | `TechDebt` | 门禁枚举未登记报告文件或收紧 --round 命名输入 | 2026-11-19 | delivered | 4b30642（校验项 11：未登记报告可枚举；12/12 归档无假红） | [BK-0012](./archive/2026-Q4/BK-0012-enumerate-unregistered-reports.md) |
| **BK-0017** | `TechDebt` | scaffold ADR 模板补控制头版本字段 | 2026-11-19 | delivered | e6fa6e6（ADR 控制头版本 + 修订历史；八类批量 14/14 合规） | [BK-0017](./archive/2026-Q4/BK-0017-scaffold-adr-模板补控制头版本字段.md) |
| **BK-0019** | `Governance` | README 入口象限的索引自愈与健康评分语义对齐 | 2026-11-19 | delivered | 1fb984f（入口象限豁免孤儿判定 + GOVERNANCE 登记代价） | [BK-0019](./archive/2026-Q4/BK-0019-readme-入口象限的索引自愈与健康评分语义对齐.md) |
| **BK-0022** | `TechDebt` | strip_leading_noise 对未闭合 frontmatter 围栏兜底 | 2026-11-19 | delivered | 263a4a4（EOF 兜底 + 3 条回归） | [BK-0022](./archive/2026-Q4/BK-0022-strip_leading_noise-对未闭合-frontmatter-围栏兜.md) |
| **BK-0024** | `TechDebt` | 治理脚本契约细节四项（空范围返回契约/判定越界/归因顺序/表格渲染） | 2026-11-19 | superseded | 逐项复核：R1-18 已消除假绿、R1-19 为 GOVERNANCE §4.1 已披露的保守超集（DR1-1 已闭合）、R1-20 已修、R1-21 不成立；仅剩返回元组形状一项，主动不做 | [BK-0024](./archive/2026-Q4/BK-0024-治理脚本契约细节四项-空范围返回契约-判定越界-归因顺序-表格渲染.md) |
| **BK-0028** | `TechDebt` | 机器地图判定侧剩余缺口（用例承重与反解契约） | 2026-11-19 | delivered | d4d8e8a（单一真源 + 4 条承重/契约用例；D1-5/D1-6 留待另立卡） | [BK-0028](./archive/2026-Q4/BK-0028-机器地图判定侧剩余缺口-用例承重与反解契约.md) |
| **BK-0043** | `Governance` | Write-Once 审查归档 2026-10-12-spec-evolution-v1 的终审裁决字段不满足 check-review-report.sh 精确匹配契约 | 2026-11-19 | delivered | 2677b9b（方案 a：正则结构化放宽 + 3 条回归；12/12 归档 rc=0） | [BK-0043](./archive/2026-Q4/BK-0043-write-once-审查归档终审裁决字段不满足精确匹配契约.md) |
| **BK-0044** | `Governance` | 提交信息取证据口径：易失数字与工作区属性反复触发独立复核阻断 | 2026-11-19 | delivered | 00489b7（commit-evidence.md V1.0.0 成文；R1–R5） | [BK-0044](./archive/2026-Q4/BK-0044-提交信息取证据口径-易失数字与工作区属性反复触发独立复核阻断.md) |
| **BK-0011** | `TechDebt` | 审查归档契约测试的弱断言改为行为断言 | 2026-11-15 | superseded | 前提已被 test_write_channel_contract.py:203-211（R1-12 回归）推翻；残余形态偏好并入 BK-0006 判定 | [BK-0011](./archive/2026-Q4/BK-0011-review-contract-weak-assertions.md) |
| **BK-0036** | `Security` | collect-facts/judge 的输入范围与输出落点双守卫（未知技能名静默 CLEAN + 静默覆盖被跟踪文件） | 2026-11-15 | delivered | 0954ca8（双守卫实现 + tests/test_io_guards.py 8 条退出码断言） | [BK-0036](./archive/2026-Q4/BK-0036-collect-facts-judge-输入范围与输出落点双守卫.md) |

*(其余 34 条历史记录已隐藏，可查看 archive/ 目录)*
