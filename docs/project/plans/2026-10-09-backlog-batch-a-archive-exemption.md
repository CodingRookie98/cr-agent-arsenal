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
- **当前活跃阶段**: P4 定向单轮红队审查（Light-Delta 复核）
- **当前活跃子任务**: Task P4.2（Light R1 已返回：1×P1 + 3×P2 + 3×P3；全部修复完成，待 Light-Delta 复核）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: ✅ 全绿（pytest **64 passed**；三件套 rc=0；health **100.0/100**、孤儿 0/51；llms.txt 以注册命令重生成可复现：**49 条**、H1 `System`、归档条目 0）
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
- `docs/llms.txt`：以 **GOVERNANCE §3 登记的注册命令**重生成一次（归档条目 **17 → 0**；总条目 65 → 48；该树 md 总数 67 → 新增计划后 68 → 68 − 17 归档 − 2 根文件 = 49）；
- **严禁**：引入裁决语义解析器、`.docignore` 配置机制、共享模块重构或其它过度工程（遵循 BK-0001/0002 卡片所载 R2 YAGNI 指令）。

## 4. 回归测试 (Regression Tests)
- `TestArchiveExemptionBatchA::test_trim_revision_exempts_archive_reports`（BK-0001：归档逐字节不变 + 不进超额清单 + 非归档仍被裁剪）；
- `TestArchiveExemptionBatchA::test_generate_llms_txt_excludes_archive_reports`（BK-0002：归档条目排除 + 非归档保留）；
- `TestArchiveExemptionBatchA::test_generate_llms_txt_output_defaults_to_root`（BK-0021：隔离 CWD 下默认落点随 `--root` 派生且不写回 CWD）。

## 5. 审查与放行 (Review & Release)
- 通道：Maintenance-Patch → `dual-round-review` **Light 单轮定向红队**（未触及公共契约与核心链路）；
- 命中 Blocker 时按 Light-Delta 仅重跑 R1 再裁决。

### 5.1 首轮 Light 审查结论与修复（R1：`docs/project/reviews/2026-10-09-batch-a-archive-exemption/r1-8ea3f65..6e7b92d.md`）

R1 判定：三项待办**技术内核均为本质根因修复**（经 git archive 隔离三树 A/B 反证：归档实扫 17 篇全跳过 / llms 归档条目 17→0 / `--output` 落点随 `--root` 派生），但**交付物层面 1 项 P1 阻断**。逐项处置：

| 稳定 ID | 终审前定级 | 缺陷 | 处置 |
|:---|:---:|:---|:---|
| R1-1 | **P1** | 交付的 `docs/llms.txt` 非其生成器在该树上的输出：同提交新增的计划文档未收录（应 49 条、实 48），且 H1 由**未注册的 `--name`** 决定 | ✅ 以 GOVERNANCE §3 **注册命令**（不传 `--name`）重生成：H1 恢复 `System`、条目 **49**、归档条目 0，可复现 |
| R1-2 | P2 | 归档豁免为 root 锚定，写入侧未闭合：`--root .` / `--root docs/project` 下 `--fix` 仍改写归档 | ✅ 新增 `is_archive_path()` **不依赖 root 的路径段扫描兜底**，两个消费者统一使用；任意 root 下均不写/不收录 |
| R1-3 | P2 | 单文件模式与目录模式判定非同构 → 同一文件两种入口结论相反，且输出「共检查 0 个文件/✅ 完美」假绿；该分支零覆盖 | ✅ 单文件模式改用同一 `is_archive_path()`，并**显式打印跳过原因**；补 3 条覆盖用例 |
| R1-4 | P2 | 新增计划文档零入链、未登记 `index.md`/`llms.txt` → 孤儿（head 健康度 99.8） | ✅ 登记 `docs/index.md`（V1.20.0 + 修订行）并随重生成入机器地图 → 孤儿 0/51、health **100.0** |
| R1-5 | P3 | GOVERNANCE §4.1 豁免登记表未补登 2 个新消费者 | ✅ 补登至**全部 5 个消费者**，并新增「判定实现」段说明写入侧 root 无关兜底 |
| R1-6 | P3 | 计划书「18→0」与「65→48」算术互斥（实为 17） | ✅ 勘误为 **17 → 0**，并补全口径（该树 md 67→68，68 − 17 − 2 = 49） |
| R1-7 | P3（封顶） | 三个只读消费者的 root 锚定债（历史既有，未在本 Diff 改动） | 保留为后续迭代统一排期；本批次已在写入侧与两个新消费者上闭合 |

---

## 6. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：批次 A 三项待办（BK-0001/BK-0002/BK-0021）的现象取证、根因、锁定修复范围与回归测试 |
