# 变更日志 (Changelog)

> **文档控制信息**
> - **文档标识**: CHANGELOG-CR-ARSENAL
> - **当前版本**: V1.8.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.8.0** | 2026-11-24 | AI Agent | 王辉 | 新增 2026-11-24「Wave 3：`taste-driven-designer` 与 `frontend-qa-gate` V2.0 瘦身与真实证据化升级」记录 |
| **V1.7.0** | 2026-11-24 | AI Agent | 王辉 | 新增 2026-11-24「Wave 2C：`doc-governance` V3.0 三刀切割与公私物理分离」记录（ADR-0005） |
| **V1.6.0** | 2026-11-24 | AI Agent | 王辉 | 新增 2026-11-24「Wave 2B：`dual-round-review` V3.0 瘦身与现代化升级」记录 |
| **V1.5.0** | 2026-11-23 | AI Agent | 王辉 | 新增 2026-11-23「Wave 2A：`goal-loop` V3.0 瘦身与现代化升级」记录 |
| **V1.4.0** | 2026-11-23 | AI Agent | 王辉 | 新增 2026-11-23「Wave 1 架构瘦身：退役 `agy-delegation-workflow` 与精简 `clarification-protocol` V2.0.0」记录 |
| **V1.3.0** | 2026-11-23 | AI Agent | 王辉 | 新增 2026-11-23「退役 `spec-evolution` 技能并下沉核心哨兵」（ADR-0003）：移除技能目录与对外发行条目，C-01/C-05+YAML/C-07 迁移至 `skills/_shared/tests/` |

---

本文件记录**已交付**的成果。进行中的工作在 [backlog](./backlog/index.md)，逐日过程在 git log。

格式参照 Keep a Changelog，按交付单元聚合（不按提交逐条罗列）。

## [2026-11-24] Wave 3：taste-driven-designer 与 frontend-qa-gate V2.0 瘦身与真实证据化升级

### 移除

- **`taste-driven-designer` 冗余外壳清理**：退役并移除独立的 `references/multimodal-enrichment.md`（并入 `critic-loop-protocol.md`）、`templates/seed-string-procedure.md`（并入 `discover-phase.md`）、`scripts/generate-seed.sh` POSIX 兼容壳，以及旧版 `tests/test_generate_seed.py` 与文案锁死测试 `tests/test_gate_contract.py`；移除冗余状态矩阵与「Critic 终分」/个人真名残留。
- **`frontend-qa-gate` 假正则门禁退役**：物理废弃 433 行中文 Markdown 正则解析器与旧文书契约件（`references/browser-verification-protocol.md`、`templates/qa-report-template.md`、`scripts/check-qa-report.sh` 与 `tests/test_qa_gate_contract.py`）；从 `D-S` 交互状态域移除越界的代码级推导项 `S9`（归位 `dual-round-review`）。

### 重构与升级

- **`taste-driven-designer` V2.0**：D1 新增 `Persuade` vs `Operate` 表面模式分流与一体化 SSoT 种子流程；D3 将反模式扩展为 **2026 10 大 AI Tells**；D2 拆除 9 列账本与 `round-nonce` 回执官僚负担，收敛为 **5 列评审记录表**（保留盲比匿名去标识、空白截图作废、鉴别力自检、原则优先与防乒乓、5 轮上限）并内置无截图降级与多模态门控；将 `scripts/generate-seed.py` 升级为纯标准库 `argparse` + `secrets` + `hashlib.sha256` 拒绝采样无偏流（消除 Park-Miller 零状态死锁）；五域运行时断言 SSOT 归位 `frontend-qa-gate`；新建 `tests/test_taste_generate_seed.py` 与 `tests/test_taste_designer_v2_surface.py`。
- **`frontend-qa-gate` V2.0**：实施**双轨门禁架构**破解无头永久 `BLOCKED` 死锁——Tier 1 自动化阻断门禁（23 项：`D-R` 5 + `D-S` 8 + `D-A` 7 + `D-P` 3）与 Tier 2 人工/真机签收清单（4 项：`H-A5`/`H-V4/V5`/`H-V6`/`H-B1/B2`，标 `pending_human` 不阻断自动化放行）；新增现代探针编排协议 `references/probe-orchestration.md`（路由至 `chrome-devtools-mcp` / `agent-browser` / Playwright + axe + LHCI / `webapp-testing`）；将 `scripts/check-qa-report.py` 重构为 Schema v2 **Fail-Closed 真实磁盘证据 JSON 门禁**（校验磁盘文件存在、非空、symlink 防逃逸、`.png`/`.jpg`/`.webp`/`.json` 魔数格式、占位符拦截、`runtime_signals` 计数清零与 `verdict` 推导一致性），配 `templates/qa-evidence-template.json`、`templates/qa-summary-template.md` 及测试 `tests/test_frontend_qa_evidence_gate.py`、`tests/test_frontend_qa_v2_surface.py`。

### 接口与文档同步

- 同步 `skills/goal-loop/`（`references/stage-progression-protocol.md` 与 `templates/goal-plan-template.md`）前端机械校验命令为 `python3 <frontend-qa-gate 技能目录>/scripts/check-qa-report.py <qa-evidence.json> --require-verdict=PASS`，并清晰标注 V2.0 双轨放行口径（Tier 1 `PASS` 放行，Tier 2 `pending_human` 交人类签收）。
- 同步更新 `README.md`、[docs/index.md](../index.md)（V1.53.0）、[taste-driven-designer-design.md](../explanation/architecture/taste-driven-designer-design.md)（V2.0.0）、[frontend-qa-gate-design.md](../explanation/architecture/frontend-qa-gate-design.md)（V2.0.0），并创建 [Wave 3 实施计划](./plans/2026-11-24-wave3-frontend-skills-v2.md)。

## [2026-11-24] Wave 2C：doc-governance V3.0 三刀切割与公私物理分离

### 决策与移除

- **[ADR-0005](../explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md)**：物理执行「三刀切割」公私分离重构，终结公共技能混装私有门禁、Mini-Jira 与高摩擦生成物的历史耦合。
- 物理退役 `docs/llms.txt`、`docs/_llms/*.md`、`docs/.doc-truth-baseline.json`、`docs/.doc-size-baseline.json`，以及公共技能中的私有/高仪式脚本与对应旧测试集（`audit-doc-health.py`、`check-doc-drift.py`、`check-doc-control-sync.py`、`generate-llms-txt.py`、`manage-doc-index.py`、`scaffold-doc.py/.sh`、`trim-revision.py`）。

### 公私分离与重构

- **第一刀（公共核纯化）**：`skills/doc-governance/` 瘦身为 Convention-First 轻内核（保留 Diátaxis、RFC 结晶、MADR 3.0 与变更联动触发矩阵），`check-doc-links.py` 剥离硬编码路径改为可重复 `--exclude <rel_prefix>` 参数并修复围栏闭合。
- **第二刀（待办拆出）**：将形态 B 待办管理器与规范从公共技能迁至本仓私有目录 `scripts/backlog/`（`manage-backlog.py` 与 `README.md`）。
- **第三刀（私有门禁精简）**：`scripts/doc-gates/` 承接本仓三道低摩擦门禁（`check-all.py`、精简重建的 `check-doc-health.py` 与更新 `G-18` 校验 `docs/index.md` 的 `check-golden-tasks.py`）；`.githooks/pre-commit` 与仓库根 `AGENTS.md` 同步切换至此入口。

### 状态流转与文档同步

- 原位将 `RFC-0003`、`RFC-0005`、`RFC-0006` 流转为 `Superseded`（取代于 `ADR-0005`），保持 `project/reviews/` 历史归档链接有效；`RFC-0007` 与 `RFC-0008` 标注实现迁移至 `scripts/doc-gates/check-doc-health.py`。
- 同步更新 `AGENTS.md`、`README.md`、`docs/AGENTS.md`、`docs/GOVERNANCE.md`（V2.0.0）、[doc-governance-design.md](../explanation/architecture/doc-governance-design.md)（V3.0.0）、[2026-11-23-doc-governance-architecture-evaluation.md](../explanation/analysis/2026-11-23-doc-governance-architecture-evaluation.md)（V1.0.1）、[backlog-governance-best-practices.md](../explanation/analysis/backlog-governance-best-practices.md)、How-To/Tutorial、象限索引与 [docs/index.md](../index.md)（登记 [Wave 2C 实施计划](./plans/2026-11-24-wave2c-doc-governance-v3.md)）。

## [2026-11-24] Wave 2B：dual-round-review V3.0 瘦身与现代化升级

### 移除

- 物理退役 0% 使用率的 `Artifact Review` 平行分支：`skills/dual-round-review/references/artifact-contract.md`、`round-1-artifact-red-team.md`、`verdict-rubric-artifact.md`、`templates/r1-report-artifact.md` 与 `tests/test_artifact_schema_contract.py`；同步清除 `check-review-report.py` 中的 `Artifact Schema` 双分支逻辑。
- 物理移除 20/20 静态文案与源码变量名锁死测试 `skills/dual-round-review/tests/test_write_channel_contract.py`。

### 重构与升级

- **`dual-round-review` V3.0 瘦身**：压缩 `SKILL.md` 并清偿全仓最后一条超限 `description`（738 → 310 字符，现役 6/6 技能全部收敛至 ≤ 500 字符建议值）；清除私有历史术语与单栈硬编码；将非代码规范审查吸收为通用 R1 规程中的 3 条核心提示。
- **注入四项高杠杆审查升级**：R1/R2 提示词引入 **Untrusted Data 防注入** 与 **空结果优先（Zero-Noise）** 准则，建立 **能力档位分层** 与 **Scoped Delta 零缺陷免 `delta-r2` 收口**（`check-review-report.py` 对无 `delta-r2` 的零缺陷 `delta-r1` 正常放行，同时保持历史 Write-Once 归档兼容）。

### 测试迁移与文档同步

- 将 `test_existing_archives_all_pass_gate`（含 4 项 `2026-11-22-*` 冻结集合及防漂移断言）与轮次列容错回归迁移至 `skills/dual-round-review/tests/test_check_review_report.py`（补齐 `(stage, base)` 阶段隔离、Scoped Delta 零缺陷 `--require-verdict=PASS` 与 `## 4.` fail-closed 守卫），并将模板/参考/脚本零漂移、R2 三源 7 列表头对齐、frontmatter 与体积预算、围栏配对及全目录防回流哨兵独立至 `skills/dual-round-review/tests/test_v3_surface_contract.py`。
- 同步更新架构设计书 [dual-round-review-design.md](../explanation/architecture/dual-round-review-design.md)、评估报告执行注记 [2026-11-23-dual-round-review-architecture-evaluation.md](../explanation/analysis/2026-11-23-dual-round-review-architecture-evaluation.md)、全局入口 `README.md`、`docs/index.md` 与 [Wave 2B 实施计划](./plans/2026-11-24-wave2b-dual-round-review-v3.md)。

## [2026-11-23] Wave 2A：goal-loop V3.0 瘦身与现代化升级

### 移除

- 物理移除 0% 实战使用率的状态跟踪脚本与文案锁死测试：`skills/goal-loop/scripts/goal-state-tracker.py`、`skills/goal-loop/scripts/goal-state-tracker.sh`、`skills/goal-loop/tests/test_goal_state_tracker.py`、`skills/goal-loop/tests/test_failure_recovery_contract.py`、`skills/goal-loop/tests/test_optional_skill_contract.py`。
- 物理移除两份零使用模板：`skills/goal-loop/templates/evaluation-report-template.md`、`skills/goal-loop/templates/research-spike-template.md`（调研与评估落盘统一对齐 Diátaxis `docs/explanation/analysis/`）。

### 新增

- `skills/goal-loop/scripts/pack-handoff.py`：≤145 行纯 Python 3 标准库跨平台文件指针交接脚本，提供 `brief`（按任务 ID 从计划精准抽取单任务简报落盘）与 `review-pkg`（采集 `base..head` 提交清单、三点式 Diff 统计与变更文件清单，防止审查漏前序提交）。
- `skills/goal-loop/tests/test_goal_loop_contract.py`：覆盖 `pack-handoff.py` 真实文件与 Git 行为单测，以及抗脆弱的 frontmatter / 围栏 / 五主阶段 / 防回流表面哨兵。

### 重构与变更

- **`goal-loop` V3.0 规程收敛**：将历史 9–10 编号收敛为 `Align → Plan → Execute → Verify → Close` 五主阶段（保留三轨裁剪矩阵中的历史编号映射）；拆除不可度量的 `HALF-OPEN` 伪运行时与机械 `2-Action Rule`，升级为事件驱动上下文工程与 3-Tries 非阻塞熔断；修复 `documentation-sync-matrix.md` 与 `stage-progression-protocol.md` 内部路径腐化，并在 `host-adapters.md` / `atomic-task-template.md` 引入四项现代执行纪律。
- 同步更新架构设计书 [goal-loop-design.md](../explanation/architecture/goal-loop-design.md)、评估报告 [2026-11-23-goal-loop-architecture-evaluation.md](../explanation/analysis/2026-11-23-goal-loop-architecture-evaluation.md)、跨技能与全局入口（`skills/frontend-qa-gate/SKILL.md`、`contexts/AGENTS.md`、`README.md`、`docs/index.md`），并登记 [Wave 2A 实施计划](./plans/2026-11-23-wave2a-goal-loop-v3.md)。

## [2026-11-23] Wave 1 架构瘦身：退役 agy-delegation-workflow 与精简 clarification-protocol V2.0.0

### 决策与移除

- **[ADR-0004](../explanation/decisions/0004-retire-agy-delegation-workflow.md)**：经实证审计确认 `agy-delegation-workflow` 实战使用率 0%、存在硬编码过时模型与私有前端约定且与原生委派高度重叠，物理移除 `skills/agy-delegation-workflow/` 全部 8 个源文件与本地软链；现役公开技能由 7 个收敛为 6 个。
- [agy-delegation-workflow-design.md](../explanation/architecture/agy-delegation-workflow-design.md) 按文档状态机流转为 `Superseded`（取代于 `ADR-0004`），清除 `docs/` 下指向已删技能目录的失效相对链接。
- 移除 `clarification-protocol` 已失效的离线校验脚本、双份模板与冗余参考文件（`scripts/check-decision-ledger.py`、`.sh`、`references/decision-ledger.md`、`references/convergence-checklist.md`、`templates/decision-ledger-template.md`、`templates/requirement-confirmation-template.md`）。

### 资产沉淀与精简

- **资产无损沉淀**：将 `agy-delegation-workflow` 中仅存的三项通用资产——Silent Landing（假失败 / 延迟落盘）判别 SOP 与 Direct-Write 四条止损准则并入 `skills/goal-loop/references/host-adapters.md`（同步去除 `stage-progression-protocol.md` 旧依赖）；将抽象后的虚假合规检查要点并入 `skills/dual-round-review/references/failure-modes-catalog.md`。
- **`clarification-protocol` V2.0.0 去壳提纯**：重构 `skills/clarification-protocol/SKILL.md` 为 67 行轻量微技能（`description` 由 623 压降至 362 字符），新增「先自查事实（Lookup Before Asking）」与「≤5 题软预算」，统一 4 列单表决策台账与出口三问内联自核，并将契约测试重构为轻量表面哨兵，同步升级 [clarification-protocol-design.md](../explanation/architecture/clarification-protocol-design.md) 至 V2.0.0。

### 变更

- 同步更新全仓注册面、引导文档与指针：`contexts/AGENTS.md`、`README.md`、`docs/index.md`、`docs/how-to/install-skills.md`、`docs/tutorials/quick-start.md`、`tools/skills-manager/collections/cr-agent-arsenal.json`、`skills/_shared/tests/test_cross_skill_links.py`、`skills/_shared/cross-skill-link-policy.json` 及受影响测试白名单；登记 [Wave 1 架构清场计划](./plans/2026-11-23-wave1-retire-agy-and-slim-clarification.md) 并重生成分层机器地图。

## [2026-11-23] 退役 `spec-evolution` 技能并下沉核心哨兵

### 决策与移除

- **ADR-0003**：经实证评估（硬编码绑定本仓无法外部复用、30 天真实执行 0 次、现行输出全为 BK-0041 已裁定 `wontfix` 噪声、2,851 行代码与 84 条用例维护成本倒挂），物理移除 `skills/spec-evolution/` 与 `.agents/skills/spec-evolution` 悬空软链接；现役公开技能由 8 个收敛为 7 个。
- `RFC-0004` 与 `spec-evolution-design.md` 按文档状态机流转为 `Superseded`（取代于 `ADR-0003`），清除 `docs/` 下指向已删技能目录的失效相对链接，保留历史计划与 Write-Once 审查凭据原貌。

### 新增

- `skills/_shared/tests/test_skill_surface_sentinels.py`：承接不可替代的三道硬护栏（`C-01` 测试存在性、`C-05` `description < 1024` 与 YAML frontmatter 合法性、`C-07` 五处注册面双向严格一致）及合成仓库负向自检用例。

### 变更

- `cr-agent-arsenal.json`、`README.md`、`docs/index.md`、`docs/how-to/install-skills.md`、`docs/tutorials/quick-start.md`、`skills/_shared/tests/test_cross_skill_links.py`、`skills/_shared/cross-skill-link-policy.json`、`skills/clarification-protocol/tests/test_clarification_protocol_contract.py`、`clarification-protocol-design.md` 同步更新并重生成分层机器地图。

## [2026-11-23] 真值轴残余收口与存量文档拆分

### 修复

- **BK-0055**：`check-doc-drift.py` 的 `--staged` 口径再加固——① `staged_paths()` 改用 `git diff --cached --name-only -z`（NUL 切分，覆盖引号/反斜杠/换行文件名）；② 新文档仅当**所有锚点也在本提交新增**时才视为已刷新，否则 fail-closed；③ 新增 `_verified_commit_points_to_head()`，「复核于」的 commit 必须指向本次提交父提交（HEAD），只改日期不再构成豁免（BD-9）
- 新增 4 条回归（合法刷新 L、中文文档名正例、新文档+既有锚点 fail-closed、新文档+新锚点通过）；`change-impact-matrix` V1.3.1 与 SKILL 模式 1 同步判定细则

### 变更

- **BK-0050**：`2026-10-12-spec-evolution.md` 由 127,747 字节拆为主册 **52,355 字节**（保留目标/约束/Task 1/Task 7/验收与风险）+ 三个原文子册（Task 2 27,951 B / Task 3 31,950 B / Task 4-6 17,987 B）
- `2026-10-19-skill-scripts-python-unification.md` 唯一 1,269 字符长行按语义边界换行，全文 **40,438 字节 / 最长 854**
- `docs/.doc-size-baseline.json` 刷新为 `{"docs": {}, "version": 1}`（体量基线清空）

### 验证

- `check-all.py --full` **7/7 全绿**；`pytest skills/doc-governance/tests` **302 passed**；断链 0；机器地图重生成

## [2026-11-23] doc-governance 交付尾巴收口

### 变更

- **RFC 生命周期补完**：RFC-0008 状态 In Review → Implemented（V1.0.0），补 `[!IMPORTANT]` 防腐块（结晶去向：GOVERNANCE §3/§4、SKILL 负向规范 6、体量基线、batch-gates 归档、BK-0050）；RFC-0004~0007 补登防腐块（此前只改状态、未加防腐声明）
- **归档口径明确**：SKILL 模式 3 与 `rfc-crystallization-lifecycle` 统一为「移至 `proposals/archive/` 或原位保留」——存在 Write-Once 审查引用时必须原位保留（历史报告不得改写，移动即断链）
- **计划 checkpoint 校准**：`2026-11-22-doc-size-metric` 状态改「已完成」、A-4/A-5 勾选；`2026-11-22-doc-truth-axis` A-7 ⏳ → ✅
- **设计书 V1.5.0**：§3 拓扑对齐现状（`_llms/`、`AGENTS.md`、`plans/`、`reviews/`、形态 B backlog）；§4.1 控制头补三态状态与真值三字段；§6 工具表补全 11 个脚本 + §6.1 五条治理轴；§8 登记阶段 5
- **文档总索引 V1.42.0**：RFC-0001/0002/0004 状态更正为 Implemented，补登 RFC-0005~0008；backlog 指标改为指向动态仪表盘（禁止手写对账）

### 修复

- **BD-1-R2**（P1）：`check-doc-drift.py` 的 `--staged` 分支只保护 `missing_anchor`、漏 `drifted`，多锚点部分漂移可被「暂存另一锚点 + 刷新复核于」洗白；已补 `drifted` 守卫，新增 3 条回归（空行 / 多锚点 / 非 ASCII 路径）
- **非 ASCII 路径**（P2）：`staged_paths()` 关闭 `core.quotePath`，中文锚点不再失明、中文文档名合法刷新不再误判漂移

### 审查

- `2026-11-22-batch-gates` 追加 BD-1-R 独立确认两轮：第 1 轮 **FAIL（Blockers=1，BD-1-R2）** → 修复 → 第 2 轮 **PASS（Blockers=0）**；报告全文见 `round-1-bd1r-confirm.md` / `round-2-bd1r-reconfirm.md`
- 残余 P2/P3（新增文档复核判据、纯日期复核 BD-9、Unicode 正例缺回归）登记 `BK-0055`

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
