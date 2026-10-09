# 批次 D 机器地图身份写保护契约实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-BATCH-D-IDENTITY-CONTRACT-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-09

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: Maintenance-Patch (存量维护通道)
> - **目标简述**: 闭环 BK-0030（身份写保护闸门完备性）与 BK-0031（身份写保护契约登记与历史防护面口径）
> - **创建日期**: 2026-10-09
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-09 16:30
> - **批准基线**: `master @ e14347e`（分支切出点 `fix/backlog-batch-d-identity-contract`）
> - **状态**: 已完成
> - **隔离分支**: `fix/backlog-batch-d-identity-contract`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P5 文档归档（已结项）
- **当前活跃子任务**: 无（Light 单轮 + 四轮 Delta，迭代 5/5 收敛：五轮均 **无 P0/P1**，终审 ✅ 准予交付）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: ✅ 全绿（pytest **105 passed**；实仓健康度 **100.0/100**、0 断链、0 漂移；归档门禁 `--require-verdict=PASS`；产物权限 644 取证）
- **最新有效提交**: 见分支 `fix/backlog-batch-d-identity-contract` HEAD
- **阻断原因**: 无

---

## 1. 现象与复现 (Phenomenon & Reproduction)

| 待办 | 现象 | 破坏机理 |
|:---|:---|:---|
| **BK-0030 / R1-14** | 闸门**放行路径**零覆盖：任取「无条件拒绝」变异（MUT-D8）全量仍全绿 | 测试只覆盖拒绝侧，放行语义无回归保护 |
| **BK-0030 / R1-15/16** | fail-closed 文案「以显式 --name 重新生成」对行分隔符名永不成立；拒绝文案与「用户已显式传 --name」自相矛盾；无合法改名通道 | 工具自铸它修不好的状态，唯一出路是删除 SSOT |
| **BK-0030 / R1-17** | 闸门对不可读可写（chmod 0200）地图 **fail-open**：rc=0、stderr 空、H1 被静默改写 | `except OSError: return` 把「读不到」当成「无既有地图」 |
| **BK-0031 / R1-13** | `errors="replace"` 使非法 UTF-8 身份被归一化为 U+FFFD 后仍判可信 | 身份比较建立在有损解码之上 |
| **BK-0031 / R1-20** | 身份写保护契约未登记进治理文档；登记的注册命令（无 `--name`）对自定义身份地图 rc=1 被拒 | 契约只在代码里，文档与现实不一致 |

## 2. 根因 (Root Cause)
- `--name` 缺省写死为 `System`，使「未显式指定」与「显式要求 System」不可区分 → 闸门只能拒绝，无法沿用既有身份；
- 闸门读取失败路径 `return` 而非拒绝（fail-open）；解码使用 `errors="replace"`（有损）；
- 契约语义（身份=H1 项目名、改名须显式移除）从未落入 SSOT。

## 3. 锁定修复范围 (Locked Diff Scope)
- `skills/doc-governance/scripts/generate-llms-txt.py`：`--name` 缺省改 `None`；新增 `_resolve_outgoing_name()` —— 无既有地图用显式名/缺省 `DEFAULT_PROJECT_NAME`，有既有地图时**未显式则沿用既有身份**、显式同名放行、异名拒绝（文案给出「先移除文件」通道）、不可读/非 UTF-8/不可反解一律 fail-closed 拒绝；
- `skills/doc-governance/scripts/audit-doc-health.py`：`_resolve_project_name()` 改**严格解码**（`UnicodeDecodeError` 归入不可信）；docstring 修正 NBSP 事实错误；空名诊断文案补充「为空」；
- `docs/GOVERNANCE.md` §4.1：新增**身份写保护契约**登记（注册命令语义、显式改名通道、fail-closed 边界、地图缺失边界）；
- `skills/doc-governance/tests/test_doc_governance_scripts.py`：新增 3 条批次 D 用例；批次 C 的「缺省必须拒绝」断言升级为**身份保真**（H1 永不被改写，要么拒绝要么沿用）；
- **严禁**：新增独立脚本层、裁决语义解析器、`.docignore` 机制或共享模块重构。

## 4. 回归测试 (Regression Tests)
- `TestBatchDIdentityContract::test_regeneration_keeps_identity_and_passes`（BK-0030 ①④：放行路径 —— 缺省/显式同名重生成均 rc=0 且 H1 与内容逐字节不变，audit 不报缺陷）；
- `TestBatchDIdentityContract::test_custom_identity_survives_bare_regeneration`（BK-0030 ①：自定义身份在缺省重生成下保持不变）；
- `TestBatchDIdentityContract::test_gate_fails_closed_on_unreadable_or_non_utf8_map`（BK-0030 ③ / BK-0031：不可读与非 UTF-8 均拒绝且字节不变）；
- `TestBatchCLlmsHintHardening::test_bare_regeneration_never_rewrites_identity`（升级为身份保真断言）。

## 5. 审查与放行 (Review & Release)
- 通道：Maintenance-Patch → `dual-round-review` **Light 单轮定向红队**；
- 注意：本次改变 `--name` 缺省语义与放行条件，已要求 R1 重点审计「沿用既有身份」是否被滥用为改写通道、放行侧用例是否真正承重；命中 Blocker 时按 Light-Delta 仅重跑 R1。


### 5.1 五轮审查记录（迭代 5/5）

| 轮次 | 基线 | 结论 | 关键发现与处置 |
|:---|:---|:---|:---|
| Light R1 | `e14347e..d39f041` | 🟡 无 P0/P1（4×P2+6×P3） | **BK-0030 ② 验收准则零实现**；三条零保护侧（异名拒绝 / audit 严格解码 / skipTest 位置） |
| Delta 2 | `d39f041..1a4e0c2` | 🟡 无 P0/P1 | DR1-1 只建模读出半程（写出半程可编码性缺失）；DR1-2 审计 strip 与生成器不一致 |
| Delta 3 | `1a4e0c2..3e55cad` | 🟡 无 P0/P1 | DR1-1 **真根治**（全码点等价证明）；DR1-2 仅机器侧闭合；R1-3 用例空转被我误判为已闭合 |
| Delta 4 | `3e55cad..8f3d1e4` | 🟡 无 P0/P1 | **原子替换引入 `.tmp` 影子写入面**（可劫持覆盖归档凭据）；分支 2 处方劝离注册命令 |
| Delta 5（收敛） | `8f3d1e4..fc97021` | ✅ **放行（Zero P0/P1）** | R1-21 四形态免疫、R1-20 闭合、并发与残 file 闭合；新增 **R1-27 产物权限 0600 回归** |

**本轮最有价值的教训**：我的连续修复多次在**错误的层次**上打补丁 —— ① 把「身份保真」做成提示文案的正确性（应为生成器侧写保护）；② 把「原子落盘」直接拼固定 `.tmp` 名（绕过了既有的归档写保护闸门）；③ 用「统一处方」收口两个语义不同的分支（把用户从唯一无损通道上劝离）。三次都是独立审查者指出**根因层次**后才真正闭合。

**残余（已登记 BK-0032，不阻断）**：R1-25/R1-27 的权限与硬链接语义细节、R1-26 审计打印非法 UTF-8 样例名崩溃、R1-6 行尾分隔符静默归一化、R1-7 自指软链 RuntimeError、R1-8 FIFO 用例目录半边不承重。

**迭代上限说明**：末轮（Delta 5）后已达审查层上限 5/5；R1-27 / R1-28 按 R1 最小修法修复并以实仓权限取证（600→644），但**未经独立复核轮**，已在审查归档 README 的裁决边界中如实标注。
---

## 6. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：批次 D 两项待办的现象、根因、锁定范围与回归测试 |
