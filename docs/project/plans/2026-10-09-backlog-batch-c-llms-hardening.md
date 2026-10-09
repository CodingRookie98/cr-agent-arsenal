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
> - **状态**: 已完成
> - **隔离分支**: `fix/backlog-batch-c-llms-hardening`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P5 文档归档（已结项）
- **当前活跃子任务**: 无（Light 单轮 + 三轮 Delta，迭代 4/5 收敛：末轮 **Zero P0/P1**，终审 ✅ 准予交付）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: ✅ 全绿（pytest **86 passed**；实仓健康度 **100.0/100**、0 断链、0 漂移；归档门禁 `--require-verdict=PASS`；变异自验 MUT-D1/D2 均打红）
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


### 5.1 四轮审查与三轮加固记录（迭代 4/5）

| 轮次 | 基线 | 结论 | 关键发现与处置 |
|:---|:---|:---|:---|
| Light R1 | `2f3a338..d9f2514` | 🔴 1×P1 + 3×P2 + 4×P3 | **净化被挂在判定路径**：4 类合法边缘名（65 字符 / 前后空格 / NBSP）被误判漂移 → 判定/显示路径分离 |
| Delta R1 ·2 | `d9f2514..88fc92f` | 🔴 维持 1×P1 | 守卫谓词结构性失效：反解失败回落 `System` 恒等自身 → 仍下发 `--name=System` → 身份静默改写 |
| Delta R1 ·3 | `88fc92f..ee1258b` | 🔴 维持 1×P1 | **换形保留**：fail-closed 分支虽无 `--name=` 字面量，却内嵌可执行命令，而其**缺省参数**即 `--name=System` |
| Delta R1 ·4 | `ee1258b..4dfc3ad` | ✅ **放行（Zero P0/P1）** | **生成器侧根因闸门** `_reject_identity_rewrite()`：19 类名 × 2 条操作**后果级**复核，既有 H1 逐字节不变、上轮 6/6 转 PASS 零复现 |

**决定性转向**：前三轮修复都在「提示文案层」打补丁，第三轮 R1 指出根因后改为**双侧闸门**——① 生成器 CLI 落盘咽喉处的身份写保护（与提示内容无关，覆盖全部提示路径）；② fail-closed 分支删除可执行命令。测试判据同步从「字面量缺席」升级为「**照做后既有地图必须逐字节不变**」的后果级断言。

**未闭合项（已登记待办，不阻断交付）**：BK-0030（闸门完备性残余：放行路径零覆盖、行分隔符名无出路、改名通道缺失、`chmod 0200` fail-open、空名文案事实错误）、BK-0031（身份写保护契约登记、非法 UTF-8 归一化、`isprintable` 放行 Mn/`U+3164`、地图缺失逃逸面、except 兜底）。
---

## 6. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：批次 C 两项待办的现象、根因、锁定范围与回归测试 |
