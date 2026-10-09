# 批次 B 机器地图写入侧安全与一致性门禁实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-BATCH-B-LLMS-INTEGRITY-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-09

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: Maintenance-Patch (存量维护通道)
> - **目标简述**: 闭环 BK-0023（机器地图写入侧安全加固）与 BK-0025（机器地图与生成物一致性门禁固化）—— 让地图漂移从不可检出变为**硬阻断**
> - **创建日期**: 2026-10-09
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-09 14:20
> - **批准基线**: `master @ 0d0eded`（分支切出点 `fix/backlog-batch-b-llms-integrity`）
> - **状态**: 进行中
> - **隔离分支**: `fix/backlog-batch-b-llms-integrity`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P4 定向单轮红队审查
- **当前活跃子任务**: Task P4.1（Light 模式 R1 派发）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: ✅ 全绿（pytest **71 passed**；实仓健康度 100.0/100 且机器地图一致；零覆盖守卫隔离根取证未落盘）
- **最新有效提交**: 见分支 `fix/backlog-batch-b-llms-integrity` HEAD
- **阻断原因**: 无

---

## 1. 现象与复现 (Phenomenon & Reproduction)

| 待办 | 现象 | 破坏机理 |
|:---|:---|:---|
| **BK-0023 / R1-16** | 缺省落点 `root_path / llms.txt` 未 `resolve()`；当 `docs/llms.txt` 是指向归档内文件的符号链接时，守卫放行、`write_text` 跟随链接改写归档 | 写入侧未做符号链接解析 → 击穿 G1 逐字归档红线与台账指纹；而「落点**解析**落入归档则拒绝」是 GOVERNANCE 已登记的承诺 |
| **BK-0023 / R1-17** | 生成器无零覆盖守卫：收录 0 篇仍落盘 rc=0 | `--root <归档根> --output docs/llms.txt` 可把 SSOT 地图静默覆盖为 261 字节空壳 |
| **BK-0025 / R1-22** | 机器地图与生成物的一致性仅靠人工 `diff` 口头验收 | 批次 A 期间该性质**连续两轮失效**（R1-1），全仓零门禁消费 → 漂移不可机械检出 |

## 2. 根因 (Root Cause)
- 显式 `--output` 分支做了 `resolve()` 而缺省分支没有 → 两条路径的归档判定强度不一致；
- `generate_llms_txt` 无返回值契约，调用方无从判断收录数，零覆盖自然无人拦截；
- `audit-doc-health.py` 的 PASS 条件只覆盖断链 / 版本漂移 / backlog 违规三类硬阻断，未覆盖「产物 == 生成物」这一内容级不变式。

## 3. 锁定修复范围 (Locked Diff Scope)
- `skills/doc-governance/scripts/generate-llms-txt.py`：缺省落点与 `--output` 分支统一 `resolve()`；`generate_llms_txt` 返回收录数，**收录 0 篇不落盘**且 CLI 以 rc≠0 报错；
- `skills/doc-governance/scripts/audit-doc-health.py`：新增 `check_llms_map_consistency()`（复用 `_load_sibling` 加载生成器，输出重定向到临时文件后逐字节比对），结果入 `llms_map_issue` 并**升级为 PASS 硬阻断条件**；
- `docs/GOVERNANCE.md`：§3 工具链表 audit 行补「机器地图一致性」；§4 新增红线「严禁机器地图与生成物不一致」（原编号顺延）；
- **严禁**：新增独立脚本层、引入裁决语义解析器、`.docignore` 机制或共享模块重构（沿用 BK-0023/0025 卡片的 YAGNI 约束）。

## 4. 回归测试 (Regression Tests)
- `TestBatchBLlmsIntegrity::test_llms_output_symlinked_into_archive_is_refused`（BK-0023：符号链接穿透拒绝且归档逐字节不变）；
- `TestBatchBLlmsIntegrity::test_llms_zero_coverage_is_refused`（BK-0023：零覆盖拒绝落盘）；
- `TestBatchBLlmsIntegrity::test_audit_detects_llms_map_drift`（BK-0025：漂移被机械检出且门禁失败）；
- `TestBatchBLlmsIntegrity::test_audit_accepts_consistent_llms_map`（BK-0025：一致地图不误报）。

## 5. 审查与放行 (Review & Release)
- 通道：Maintenance-Patch → `dual-round-review` **Light 单轮定向红队**；
- 注意：本次触及**放行门禁的判定面**（新增硬阻断项），已要求 R1 重点审计新增阻断是否过严或误报；命中 Blocker 时按 Light-Delta 仅重跑 R1。

---

## 6. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：批次 B 两项待办的现象、根因、锁定范围与回归测试 |
