# Wave 2C 实施计划：`doc-governance` V3.0 三刀切割与公私物理分离

> **文档控制信息**
> - **文档标识**: PLAN-WAVE2C-DOC-GOVERNANCE-V3-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **执行通道**: **Heavy Track（核心治理技能与全局门禁架构重构）** —— 独立分支 + Full Mode 双轮对抗审查（R1 → R2 → Delta-R1 零缺陷放行）
> - **分支**: `refactor/wave2c-doc-governance-v3`（基于 `master` `d63ee31`）
> - **决策与评估依据**: [ADR-0005](../../explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md) · [doc-governance 评估报告](../../explanation/analysis/2026-11-23-doc-governance-architecture-evaluation.md) · [Docs-as-Code 增量调研](../../explanation/analysis/2026-11-23-doc-governance-peer-research.md)

---

### Active Checkpoint

- **当前阶段**: `DONE`（已完成并终审放行）
- **状态**: 已完成
- **已完成**:
  - 调研全部 32 文件与下游引用并定稿 [ADR-0005](../../explanation/decisions/0005-split-doc-governance-public-vs-repo-local.md)；
  - 三路并行完成 W2C-1（公共核心瘦身至 11 文件 / 1,457 行 / 76,292 字节，移除 19 个冗余资产，`SKILL.md` 79 行 / 6,339 字节 / `description` 340 字符）、W2C-2（`check-doc-health.py` / `check-all.py` / `check-golden-tasks.py` / `.githooks/pre-commit` / `scripts/backlog/` 与 3 份单测）与 W2C-3（退役 `llms.txt`/`_llms`/旧基线、流转 RFC 与同步治理文档/索引/日志），并解决测试模块重名冲突，提交审查前基线 `3e0b501`；
  - 独立 R1（`eedff73b27fe`）与 R2（`34d78dacde6a`，裁定 `阻断交付`，坐实 `R1-1`–`R1-4`） → 独立 W2C-Delta 修复（`b7ce47a`，根治 `R1-1`–`R1-4` 并顺并 `R1-5`/`R1-6`/`R1-9`） → 独立 Scoped Delta R1（`17487bb4a768`）复核 **🔴 0 / 🟡 0 / ⚪ 0** 免派 `delta-r2` 直接收口准予交付，归档见 [wave2c-doc-governance-v3](../reviews/2026-11-24-wave2c-doc-governance-v3/README.md)；
  - 全量终验：`check-review-report.py --require-verdict=PASS` Exit 0、`scripts/doc-gates/check-all.py --full`（4/4 PASS）、`check-golden-tasks.py --root docs`（`PASS 20 | GAP 0 | FAIL 0`）、`pytest skills/ scripts/ -q`（`299 passed`）与 `.githooks/pre-commit` 全绿。
- **待办**: 无（准备 Fast-Forward 合入 `master` 并推送）

---

## 1. 三刀切割执行蓝图（零文件交集三任务包）

### 1.1 前置 `git mv` 隔离（主智能体执行）
- `skills/doc-governance/scripts/check-all.py` → `scripts/doc-gates/check-all.py`
- `skills/doc-governance/scripts/check-golden-tasks.py` → `scripts/doc-gates/check-golden-tasks.py`
- `skills/doc-governance/scripts/manage-backlog.py` → `scripts/backlog/manage-backlog.py`
- `skills/doc-governance/references/backlog-specification.md` → `scripts/backlog/README.md`

### 1.2 并行任务包划分

| 任务包 | 独占写边界 | 核心交付 |
| :--- | :--- | :--- |
| **W2C-1** | `skills/doc-governance/` | 退役 9 个私有/高税源码与 10 个旧测试；重构 Convention-First 轻量 `SKILL.md`（≤120 行 / ≤11 KB / desc ≤430 字符）、`references/` 与 `change-registration.md`；将 `check-doc-links.py` 升级为通用 `--exclude` + 严格围栏闭合；新建 `test_check_doc_links.py` 与 `test_doc_governance_v3_surface.py` |
| **W2C-2** | `scripts/doc-gates/`、`scripts/backlog/`、`scripts/tests/`、`.githooks/pre-commit` | 新建精简 `check-doc-health.py`（≤320 行：RFC-0007 三态 + RFC-0008 体量真正透传与 `articles` 豁免 + `AGENTS.md` 30 行守卫）；改造 `check-all.py`（3 道门禁 + `--full`）与 `check-golden-tasks.py`（`G-18` 校验 `docs/index.md`）；更新 `.githooks/pre-commit` 与 `scripts/backlog/`；补齐 3 份聚焦单元测试（均 ≤350 行） |
| **W2C-3** | `AGENTS.md`、`README.md`、`docs/`（排除 `ADR-0005`、本计划书及 `docs/project/reviews/`） | 退役 `docs/llms.txt`、`docs/_llms/`、`.doc-truth-baseline.json`、`.doc-size-baseline.json`；原位将 RFC-0003/0005/0006 标为 `Superseded`（指向 ADR-0005），RFC-0007/0008 标注实现迁移；同步升级 `AGENTS.md`、`docs/AGENTS.md`、`docs/GOVERNANCE.md`（V2.0.0）、`doc-governance-design.md`（V3.0.0）、评估注记、how-to/tutorial、索引与 `changelog.md` |

---

## 2. 验收硬门禁

1. `python3 scripts/doc-gates/check-all.py --full` → `Exit 0`（断链 / 健康体检 / 可回答性 / 测试套件 4/4 全绿）
2. `python3 scripts/doc-gates/check-golden-tasks.py --root docs` → `Exit 0`（`PASS 20 | GAP 0 | FAIL 0`）
3. `python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews` → `Exit 0`（0 断链）
4. `python3 skills/doc-governance/scripts/check-doc-links.py --root skills/doc-governance` → `Exit 0`（0 断链）
5. `python3 -m pytest skills/ scripts/ -q` → `Exit 0`（全仓测试通过）
6. 体量与红线：`skills/doc-governance/` ≤ 12 追踪文件 / ≤ 75 KB（`SKILL.md` ≤ 130 行 & ≤ 12 KB，`description` ≤ 500 字符）；全仓所有代码/测试单文件 ≤ 1,000 行；新增/修改函数 ≤ 50 行；`docs/project/reviews/` 历史归档 0 改动
7. Full Mode 独立双轮对抗审查（`docs/project/reviews/2026-11-24-wave2c-doc-governance-v3/`）达成 **Zero Blockers / 准予交付**
