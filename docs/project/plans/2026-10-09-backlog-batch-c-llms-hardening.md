# 批次 C 机器地图提示文案净化和零覆盖口径登记实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-BATCH-C-LLMS-HARDENING-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-09

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: Maintenance-Patch (存量维护通道)
> - **目标简述**: 闭环 BK-0026（提示文案终端注入面和畸形项目名）与 BK-0027（零覆盖态无门禁兜底的口径显式登记）
> - **创建日期**: 2026-10-09
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-09 15:05
> - **批准基线**: `master @ 2f3a338`（分支切出点 `fix/backlog-batch-c-llms-hardening`）
> - **状态**: 进行中
> - **隔离分支**: `fix/backlog-batch-c-llms-hardening`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P4 定向单轮红队审查
- **当前活跃子任务**: Task P4.1（Light 模式 R1 派发）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: ✅ 全绿（pytest **83 passed**；实仓健康度 100.0/100；Light R1 判 1×P1 → 已二次修复）
- **最新有效提交**: 见分支 `fix/backlog-batch-c-llms-hardening` HEAD
- **阻断原因**: 无

---

## 1. 现象与复现 (Phenomenon & Reproduction)

| 待办 | 现象 | 破坏机理 |
|:---|:---|:---|
| **BK-0026 / D2-3** | 项目名含裸 `ESC/OSC/BEL` 时，控制序列被原样写入门禁 stdout | `shlex.quote` 只做 shell 层转义，不剥离终端控制字符 → 可篡改窗口标题/剪贴板并污染 CI 日志 |
| **BK-0026 / D2-4** | 项目名以 `-` 开头（如 `--root`）时，提示的修复命令被 argparse 判为缺参（rc=2） | 提示用 `--name <value>` 空格形式，值被当作选项 → 修复建议成为死巷 |
| **BK-0026 / D2-5** | 含 NUL 的名字使提示命令在 execve 层不可执行；10 万字符名把缺陷行膨胀 10 万字节 | 反解结果缺少可打印性与长度校验 |
| **BK-0027 / D1-3 · D2-6** | 零覆盖态（无可收录文档）时一致性检查不适用，但 `llms.txt` 为 `.txt` 不在断链扫描域 → 含死链/过期条目的手写地图被 `PASS 100.0` 静默接受；且现有测试把该状态断言为绿色契约 | 豁免未登记时，下一轮会把漏检固化为正确性契约 |

## 2. 根因 (Root Cause)
- 反解得到的项目名直接进入「人读文案 + 可复制命令」两个语义域，而净化只覆盖了 shell 层（`shlex.quote`），未覆盖终端层（控制字符）与 execve 层（NUL/超长）；
- 提示命令采用 `--name <value>` 空格形式，值以 `-` 开头时被 argparse 当作选项；
- 零覆盖豁免（BK-0023 为避免死胡同而引入）的真实代价此前只存在于审查报告，未落入治理条文（SSOT）。

## 3. 锁定修复范围 (Locked Diff Scope)
- `skills/doc-governance/scripts/audit-doc-health.py`：新增 `_resolve_project_name()`（反解**未净化原名**供判定逐字同源，并回报 `resolved` 可信标志）与 `_is_safely_displayable()`（全可打印 + 非空 + ≤64 字符）；**反解不可信或名字不可安全回显时一律不下发 `--name` 命令**，改以 prose 指引；可安全回显时用 `--name=<value>` 赋值形式；
- `docs/GOVERNANCE.md` §4.1：新增「零覆盖态边界（BK-0027 显式登记）」，写明所选口径为**显式登记豁免**（不引入条目可解析性校验）及其代价；
- `skills/doc-governance/tests/test_doc_governance_scripts.py`：新增 3 条用例；修正零覆盖用例 docstring，指明其所锁定的是**登记豁免**而非正确性契约；
- **严禁**：新增独立脚本层、裁决语义解析器、`.docignore` 机制或共享模块重构。

## 4. 回归测试 (Regression Tests)
- `TestBatchCLlmsHintHardening::test_hint_strips_terminal_control_sequences`（D2-3：输出零裸 ESC/BEL）；
- `TestBatchCLlmsHintHardening::test_hint_rejects_nul_name` / `test_hint_rejects_overlong_name`（D2-5：零 NUL、输出不被膨胀）；
- `TestBatchCLlmsHintHardening::test_legit_edge_names_are_not_misjudged_as_drift`（R1-1：4 类合法边缘名不得被误判漂移）；
- `TestBatchCLlmsHintHardening::test_malformed_names_never_emit_a_name_option`（R1-1：畸形名不得下发改名命令）；
- `TestBatchCLlmsHintHardening::test_hint_name_matches_map_identity`（R1-3：提示 `--name` 值须逐字等于地图身份）；
- `TestBatchCLlmsHintHardening::test_hint_command_is_executable_for_dash_prefixed_name`（D2-4：`--name=--root` 被 argparse 接受，rc≠2）。

## 5. 审查与放行 (Review & Release)
- 通道：Maintenance-Patch → `dual-round-review` **Light 单轮定向红队**；
- 注意：本次触及门禁输出契约与治理条文，已要求 R1 重点审计净化是否破坏正常中文/空格项目名、是否仍存在绕过面；命中 Blocker 时按 Light-Delta 仅重跑 R1。

---

## 6. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：批次 C 两项待办的现象、根因、锁定范围与回归测试 |
