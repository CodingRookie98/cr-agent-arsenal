# 批次 A 归档豁免与 llms 落点修复实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-BATCH-A-ARCHIVE-EXEMPTION-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-09

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: Maintenance-Patch (存量维护通道)
> - **目标简述**: 闭环 BK-0001 / BK-0002 / BK-0021 —— 让 `trim-revision.py` 与 `generate-llms-txt.py` 复用既有的 `project/reviews` 归档豁免语义，并使 `--output` 缺省落点随 `--root` 派生
> - **创建日期**: 2026-10-09
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-09 13:35
> - **批准基线**: `master @ 8ea3f65`（分支切出点 `fix/backlog-batch-a-archive-exemption`）
> - **状态**: 进行中
> - **隔离分支**: `fix/backlog-batch-a-archive-exemption`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P4 定向单轮红队审查
- **当前活跃子任务**: Task P4.1（Light 模式 R1 派发）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: ✅ 全绿（pytest **60 passed**；三件套 rc=0；health 100.0/100；归档树指纹 `--fix` 前后一致；llms.txt 归档条目 17→0，条目数 65→48）
- **最新有效提交**: 见分支 `fix/backlog-batch-a-archive-exemption` HEAD
- **阻断原因**: 无

---

## 1. 现象与复现 (Phenomenon & Reproduction)

| 待办 | 现象（已实测取证） | 破坏机理 |
|:---|:---|:---|
| **BK-0001** | `trim-revision.py --root <tmp> --fix` 对 `project/reviews/r.md` 打印 `[FIXED] r.md: 修订历史从 7 行成功裁剪至 5 行`，文件 SHA256 变化 | 该脚本是唯一具备写能力的治理消费者，扫描时无归档豁免 → 就地改写**不可重建**的交付凭据，破坏 G1 逐字归档红线 |
| **BK-0002** | `generate-llms-txt.py --root docs` 生成的机器地图含 **18** 条 `project/reviews` 条目（已固化进 `docs/llms.txt`，共 65 条） | 机器地图无归档豁免 → 逐字凭据混入智能体引导地图，且与 links/audit 三消费者语义不一致 |
| **BK-0021** | `--output` 缺省值为相对 CWD 的 `docs/llms.txt`，不随 `--root` 派生；以隔离根调用会写回真实仓库文件 | 隔离复算不成立（Delta 审查实测触发），复算证据可信度受损 |

## 2. 根因 (Root Cause)
- `check-doc-links.py` / `check-doc-control-sync.py` / `audit-doc-health.py` 三消费者各自持有同构的 5 行豁免（`EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")` + `in_evidence_archive()`），而 `trim-revision.py` 与 `generate-llms-txt.py` **缺该判断**；
- `generate-llms-txt.py` 的 `--output` 默认值写死为 `docs/llms.txt`（相对 CWD），与 `--root` 无耦合。

## 3. 修复范围 (Locked Diff Scope)
- `skills/doc-governance/scripts/trim-revision.py`：新增同构豁免常量与判断；目录遍历与单文件模式均拒绝归档路径；
- `skills/doc-governance/scripts/generate-llms-txt.py`：新增同构豁免判断（生成循环跳过归档）；`--output` 缺省改为 `<root>/llms.txt`；
- `docs/llms.txt`：重生成一次（归档条目 18 → 0，总条目 65 → 48）；
- **严禁**：引入裁决语义解析器、`.docignore` 配置机制、共享模块重构或其它过度工程（遵循 BK-0001/0002 卡片所载 R2 YAGNI 指令）。

## 4. 回归测试 (Regression Tests)
- `TestArchiveExemptionBatchA::test_trim_revision_exempts_archive_reports`（BK-0001：归档逐字节不变 + 不进超额清单 + 非归档仍被裁剪）；
- `TestArchiveExemptionBatchA::test_generate_llms_txt_excludes_archive_reports`（BK-0002：归档条目排除 + 非归档保留）；
- `TestArchiveExemptionBatchA::test_generate_llms_txt_output_defaults_to_root`（BK-0021：隔离 CWD 下默认落点随 `--root` 派生且不写回 CWD）。

## 5. 审查与放行 (Review & Release)
- 通道：Maintenance-Patch → `dual-round-review` **Light 单轮定向红队**（未触及公共契约与核心链路）；
- 命中 Blocker 时按 Light-Delta 仅重跑 R1 再裁决。

---

## 6. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：批次 A 三项待办（BK-0001/BK-0002/BK-0021）的现象取证、根因、锁定修复范围与回归测试 |
