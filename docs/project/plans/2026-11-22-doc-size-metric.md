# 文档体量度量换挡（RFC-0008）实施计划

> **文档控制信息**
> - **文档标识**: PLAN-DOC-SIZE-METRIC-2026
> - **当前版本**: V1.0.1
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-11-22

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: **Heavy Track**（新增门禁 + 基线机制 + 规程同步）
> - **需求源**: [RFC-0008](../../proposals/RFC-0008-doc-size-metric.md) + Backlog 调研 D2/C3
> - **执行后端**: 当前会话内联
> - **批准基线**: `feat/doc-truth-axis` @ `14166b1`
> - **状态**: 已完成（2026-11-23 收口登记：实现 `a5686f2`；审查并入 batch-gates 归档；存量消化转 BK-0050）

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)

- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P5 完成（交付 + 审查归档 + 收口登记）
- **当前活跃子任务**: 无（交付完成）
- **当前子任务重试计数**: 0/3
- **门禁基线（改动前）**: pytest 270 passed｜audit PASS｜links rc=0｜drift rc=0
- **批次进度**: A-1 ✅ / A-2 ✅ / A-3 ✅ / A-4 ✅ / A-5 ✅
- **实测（2026-11-23 收口复跑）**: `check-all.py` 6 项全通过；`pytest skills/doc-governance/tests` → **295 passed**

---

## 1. 目标与非目标

**目标**：把已证失效的「800 行」度量换成「字节 + 最长单行」，并用棘轮基线消化存量，使体量治理第一次有机械实现。

**非目标**：自动拆分文档（编辑决策）、修改存量文档内容。

## 2. 测试策略与级别裁定

- **改动风险定级**: **MEDIUM**（新增审计维度；不改既有输出键）
- **强制执行级别**: **L0 + L1 + L2 + L-Doc**
- **豁免测试级别**: L3（无用户交互链路）
- **精确验证命令**:
  1. L0: `python3 -m py_compile skills/doc-governance/scripts/*.py`
  2. L1: `python3 -m pytest skills/doc-governance/tests/test_doc_size.py -q`
  3. L2: `python3 -m pytest skills/doc-governance/tests -q`
  4. L-Doc: links / control-sync / drift / audit / `--split --check`

## 3. 原子任务清单

- [x] **A-1** `check_doc_size` + `write_size_baseline` + `load_size_baseline`（字节/最长单行/行数三指标）
- [x] **A-2** 接入 `audit_health` 的 `doc_size` 块与 `evaluate_verdict`；CLI 增 `--write-size-baseline` / `--max-doc-bytes` / `--max-doc-line`
- [x] **A-3** 存量基线生成（2 篇）并验证降级为警告
- [x] **A-4** 文档同步（GOVERNANCE §3/§4、SKILL 负向规范 6、控制头模板无需变更）+ 提交（`a5686f2`、`a38cc85`）
- [x] **A-5** 审查 + 归档（并入 `2026-11-22-batch-gates` 归档：Light 红队 → Delta 复核 → 最终确认，5×P1 全收口）

## 4. 实测（交付时）

| 文档 | 指标 | 处置 |
| :--- | :--- | :--- |
| `project/plans/2026-10-12-spec-evolution.md` | 127,747 字节 / 2,360 行 | 基线内，警告 |
| `project/plans/2026-10-19-skill-scripts-python-unification.md` | 最长单行 1,269 | 基线内，警告 |

## 5. 回滚方案

删除 `docs/.doc-size-baseline.json` 并移除 `check_doc_size` 调用即可；不涉及数据迁移。
