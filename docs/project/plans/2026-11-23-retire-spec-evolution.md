# 退役 `spec-evolution` 技能并下沉核心哨兵测试实施计划

> **文档控制信息**
> - **文档标识**: PLAN-RETIRE-SPEC-EVOLUTION-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-11-23

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: **Heavy Track**（删除公开技能 + 修改共享测试与发布清单 + 文档生命周期流转）
> - **关联决策**: [ADR-0003 退役 spec-evolution 技能并下沉哨兵测试](../../explanation/decisions/0003-retire-spec-evolution.md)
> - **分支基线**: `refactor/retire-spec-evolution` @ `a11ba82`
> - **执行后端**: 当前会话内联（P4 交付终审派发独立子智能体执行双轮对抗审查）
> - **状态**: 进行中

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 待审核 | 初版：确立「退技能、留哨兵（方案 A）」实施计划、测试分级与清理清单 |

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)

- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P4（独立双轮对抗审查：`dual-round-review` Full 模式）
- **当前活跃子任务**: T-5（派发 R1 红队与 R2 元架构师独立审查至 Zero Blockers）
- **当前子任务重试计数**: 0/3
- **门禁基线（改动前实测）**: `check-all.py` 6/6 通过（rc=0）；`audit-doc-health.py` PASS 100.0/100（118/118 合规）；`skills/` 共收集 692 条用例（其中 `spec-evolution` 占 84 条 / 16.73s）
- **最新实测（T-1~T-4 落地后）**: `check-all.py --full` **7/7 全绿**（含 `doc-governance` 测试套件）；`check-golden-tasks.py` **PASS 20 / GAP 0 / FAIL 0**；`pytest skills/_shared/tests/` **8 passed**（0.14s）；`pytest skills/ -q` **611 passed / 1 pre-existing failed**（`master` 既有 `test_existing_archives_all_pass_gate`，与本次变更无关）

---

## 1. 目标与范围

**目标**：按用户裁定的「方案 A（退技能、留哨兵）」退役 `spec-evolution`：
1. 将不可替代的三道硬护栏（`C-01` 测试存在性、`C-05` `description < 1024` 与 YAML frontmatter 合法性、`C-07` 四注册面一致性）浓缩为轻量化仓库级哨兵测试，落入 `skills/_shared/tests/test_skill_surface_sentinels.py`；
2. 删除 `skills/spec-evolution/` 与本地悬空软链接 `.agents/skills/spec-evolution`；
3. 同步更新发布清单（`cr-agent-arsenal.json`）、共享测试与策略（`skills/_shared/`、`clarification-protocol` 合同测试）、用户指南（`README.md`、`install-skills.md`、`quick-start.md`）、文档生命周期状态（`ADR-0003`、`RFC-0004`、`spec-evolution-design.md`、`clarification-protocol-design.md`、`docs/index.md`、`changelog.md`）及分层机器地图（`docs/llms.txt`、`docs/_llms/*.md`）。

**非目标**：
- 不迁移已被 `doc-governance` / `_shared` 替代或已裁定 `wontfix` 的判据（`C-02`、`C-03`、`C-04`、`C-06`、`C-08`、`C-09`、`C-10`）；
- 不触碰 Write-Once 审查凭据归档（`docs/project/reviews/**`）与已结项 backlog 历史档案（`docs/project/backlog/archive/**`）。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: **HIGH**（删除公开技能 + 变更共享测试门禁 + 改写分发清单与治理索引）
- **强制执行级别**: **L0 + L1 + L2 + L-Doc**
- **豁免测试级别**: L3（无独立长流程 CLI 产物需真仓多步演进报告；迁移后哨兵直接运行在真实仓库树上）
- **精确验证命令清单**:
  1. L0: `python3 -m py_compile skills/_shared/tests/test_skill_surface_sentinels.py skills/_shared/tests/test_cross_skill_links.py`
  2. L1/L2: `python3 -m pytest skills/_shared/tests/ -v`（含真实仓哨兵断言 + 合成隔离仓负向变异断言）
  3. 全量测试: `python3 -m pytest skills/ -q`
  4. L-Doc 全量门禁: `python3 skills/doc-governance/scripts/check-all.py --full`

---

## 3. 原子任务清单

- [x] **T-1**：编写 `skills/_shared/tests/test_skill_surface_sentinels.py`（覆盖 `C-01`、`C-05` + YAML 合法性、`C-07` 四注册面一致性 + 合成仓库负向反证测试），先红后绿
- [x] **T-2**：删除 `skills/spec-evolution/`（`git rm -r`）与 `.agents/skills/spec-evolution` 悬空软链接，确认 T-1 哨兵按预期爆红（捕获残留登记）
- [x] **T-3**：同步 `tools/skills-manager/collections/cr-agent-arsenal.json`、`skills/_shared/tests/test_cross_skill_links.py`、`skills/_shared/cross-skill-link-policy.json`、`skills/clarification-protocol/tests/test_clarification_protocol_contract.py` 与 `README.md`、`docs/index.md`，使 T-1 转绿
- [x] **T-4**：完成文档生命周期同步——新建 [ADR-0003](../../explanation/decisions/0003-retire-spec-evolution.md)、流转 `RFC-0004` 与 `spec-evolution-design.md` 为 `Superseded` 并消除死相对链接、清理 `clarification-protocol-design.md` 失效外链、更新 `install-skills.md` / `quick-start.md` / `changelog.md`，重生成 `docs/llms.txt` 与 `docs/_llms/*.md`
- [ ] **T-5**：运行全量验证（`pytest skills/` + `check-all.py --full` + `audit-doc-health.py`）并派发独立双轮对抗审查（`dual-round-review` Full 模式）至 Zero Blockers 放行

---

## 4. 回滚方案

所有变更限定在隔离分支 `refactor/retire-spec-evolution`。若需恢复 `spec-evolution`，可通过合并前放弃分支或对删除提交执行反向恢复重建目录与注册面；`skills/_shared/tests/test_skill_surface_sentinels.py` 为独立测试文件，可直接移除而不影响其余测试。
