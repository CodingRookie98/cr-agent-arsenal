# 变更日志 (Changelog)

> **文档控制信息**
> - **文档标识**: CHANGELOG-CR-ARSENAL
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：按「交付单元」记录可交付成果（此前交付叙事散落在各计划的执行偏差表与提交信息里） |

---

本文件记录**已交付**的成果。进行中的工作在 [backlog](./backlog/index.md)，逐日过程在 git log。

格式参照 Keep a Changelog，按交付单元聚合（不按提交逐条罗列）。

## [2026-11-22] 文档治理基础设施

合并提交 `6d63582`（分支 feat/doc-truth-axis，59 个提交，64 文件 +11,245/−192）。

### 新增

- **真值轴**（RFC-0005）：控制头三字段（来源 / 代码锚点 / 复核于）+ check-doc-drift.py 五态漂移检测 + 棘轮基线防「删锚点洗绿」；pre-commit 下 --staged 拦截本次提交引入的漂移，同一次提交视为同步
- **分层机器地图**（RFC-0006）：根 docs/llms.txt 从 21,810 字节降为 **883 字节**（象限入口），全量条目下沉 docs/_llms/&lt;象限&gt;.md；新增路由文件 docs/AGENTS.md（≤30 行）
- **文档状态机**（RFC-0007）：Active / Contested / Superseded 三态 + 取代于 + 争议点；审计输出「未决冲突清单」
- **体量度量换挡**（RFC-0008）：以字节（≤64 KB）与最长单行（≤1000 字符）替代已证失效的行数指标；棘轮基线消化 2 篇存量
- **门禁自动化**（BK-0048）：check-all.py 聚合六道门禁（实测 1.5 s）+ .githooks/pre-commit
- **可回答性评测**（BK-0049）：check-golden-tasks.py 20 条机械断言（PASS/GAP/FAIL 三态）

### 变更

- audit-doc-health.py 新增 doc_status / doc_size / truth 三个报告块；evaluate_verdict 统一收口新增判据
- generate-llms-txt.py 新增 --split / --check / --max-root-bytes；默认模式产物与旧版逐字节一致

### 修复

- 七轮独立审查累计收口 **9 个 P1**：同日复核必红、删锚点洗绿、浅克隆假漂移、空账本绕过、行区间锚点漏检、--output 基名丢弃、审计重复定义、hook 结构性失明、同提交豁免被注释蒙混
- 八条 P2/P3：.MD/.markdown 改名逃逸、U+2028 绕过单行上限、非数值基线崩溃、chmod 000 fail-open、PYTHON_BIN=true 旁路、基线投毒、G-02 断言恒真、G-14 删目录即 PASS

## [2026-11-22] 上手与操作象限

提交 `cd19017`。

### 新增

- docs/tutorials/quick-start.md：5 分钟最短路径（装技能 → 跑门禁 → 定位文档）
- docs/how-to/install-skills.md：本地软连接 vs 外部安装的选型与命令
- docs/how-to/run-doc-gates.md：六道门禁用途、失败处置、pre-commit/CI 接入
- docs/how-to/troubleshoot-doc-governance.md：按症状索引的 12 类真实故障

### 影响

- 可回答性评测：G-12 / G-13 由 GAP 转 PASS；总分 PASS 15/GAP 5 → **PASS 17/GAP 3**

## [2026-11-21] LLM-WIKI 社区实现调研

提交 `2360b32`。

### 新增

- docs/explanation/analysis/llm-wiki-implementation-research.md：六条实现路线、十类工程难点、十二维 doc-governance 对照审计与 P0–P2 改造建议

## 更早的交付

2026-09 至 2026-10 的交付记录散落在各计划的「执行偏差记录」与 docs/project/reviews/ 的审查归档中，尚未回溯整理（登记为后续工作）。
