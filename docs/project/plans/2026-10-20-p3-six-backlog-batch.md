# P3 六项 Backlog 批次实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-P3-SIX-BACKLOG-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-20

> **目标元数据**
> - **所属项目**: cr-agent-arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 一次性闭环 6 张 backlog 卡片——BK-0045（P2 Bug：`prepare-review-context` 未跟踪文件过滤失效）、BK-0010（Security：`--archive-root` 空值/非法形态防御）、BK-0008（Governance：围栏奇偶告警补充嵌套演示提示）、BK-0016（TechDebt：象限索引幂等判据剥离锚点与查询串）、BK-0007（Governance：GOVERNANCE.md 豁免表文本精确化）、BK-0014（Governance：作废轮次版本库留痕口径补一句）
> - **创建日期**: 2026-10-20
> - **计划负责人**: DSH AI Agent (lead)
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-20（原话「接受你的建议」，即采纳 Lead 提出的第一批 6 项方案）
> - **批准基线**: `master` @ `7a2a3a0`
> - **状态**: 进行中
> - **隔离分支**: `fix/p3-six-backlog-batch`（基点 `7a2a3a0`）
> - **需求确认文档**: 豁免（需求源为用户对 6 张既有卡片的显式采纳，卡片本身含 DoD）
> - **技术调研备忘录**: 豁免（6 项均为既有代码小改，无选型空间）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语；本文件检查点与机器状态必须一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P4（双轮独立审查与阻断修复闭环）
- **当前活跃子任务**: delta-r2 终审已完成（✅ 准予交付，Blockers=0）→ 归档闭包（配对键改名/README 定稿/门禁 PASS/本检查点收口）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 3/5
- **最后一次验证状态**: 闭包态 WSL 全量 `503 passed / 0 failed`；闭包态 Windows UTF-8 模式 `12 failed / 475 passed / 16 skipped`（BASE `7a2a3a0` 为 12 failed / 464 passed / 14 skipped，失败集逐条相同、新增失败 0）；文档四件套全绿
- **最新有效提交**: `4d4eed8`（闭包提交：delta-r2 归档 + 门禁 `--require-verdict=PASS` 通过 + 计划/docs 收口；其后的书签提交仅回填本行提交号）
- **阻断原因**: 无（R2 唯一阻断 R1-1 已由 `f1f2189` 结项，Delta 复核中）

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收准则
1. **六张卡片 DoD 逐项达成**：BK-0045 / BK-0010 / BK-0008 / BK-0016 / BK-0007 / BK-0014 卡片 §3 所列验收条件全部满足。说明（R2 §1.2.5 反向发现）：BK-0045 的 frontmatter `priority` 为 **P2**，与本批次名「P3 六项」不一致——批次名沿用「六张 P2/P3 混合卡」的既有命名习惯（前例为「P2 批次六项」），非缺陷；BK-0045 以 P2 优先级随批次交付，其 `acceptance_criteria` 3 项与 §3 DoD 4 项不一致处，以 §3 为准（R1-1 已处置）。
2. **WSL 全量回归**：`python3 -B -m pytest skills/ -q` **0 failed** 且通过数 ≥ 490（基线 490）。
3. **Windows umbrella（同一 UTF-8 模式对照）**：在 Windows 上以 UTF-8 模式运行（`$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'`，随后执行 `.venv\Scripts\python.exe -B -m pytest skills/ -q`）。本批次新增测试显式以 `encoding="utf-8"` 解码子进程输出，必须让子进程同处 UTF-8 模式；plain cp936 控制台下会出现 18 条 `UnicodeDecodeError` 环境假差异，不作判定依据（§5 已记录）。同口径实测：BASE `7a2a3a0` = **12 failed / 464 passed / 14 skipped**；HEAD（修复后）= **12 failed / 475 passed / 16 skipped**，失败集逐条相同（**新增失败 0**）；残留 12 条均为 doc-governance（5）与 spec-evolution（7）的 POSIX-only / 存量债务（口径 B 豁免披露）。本次触碰的 **3 个**测试文件在该模式下全绿（dual-round-review 两文件 0 failed、`test_doc_index_convention.py` 0 failed）；该文件的端到端用例在 Windows 上按 §1.4 第 4 项 `skip`，跨平台覆盖由纯逻辑用例承担。
4. **差分矩阵**：`prepare-review-context`、`check-review-report` 的 bash↔python 差分在「有意分歧白名单」之外逐字节一致（见 §1.4）。
5. **契约与文档门禁**：文档四件套（`check-doc-links` / `check-doc-control-sync` / `audit-doc-health` / `trim-revision --keep 5`）全绿；`judge.py` 无新增 BLOCKER/HIGH 发现。本批次不涉及 8 个既有技能脚本的 Python 契约壳，故 `.goal-loop/verify-contract.py`（Lead 临时工具，`.gitignore` 忽略，证据边界见 §1.5）不适用于本批次（R1-10 更正）。
6. **交付流程**：独立子智能体 R1（红队）→ R2（架构师元审判）Zero Blockers 裁决；审查报告逐字归档并登记台账与 SHA256 指纹。说明（R1-1 处置口径）：提交 `7f35a33` 的「闭环六项」指**代码与文档闭环**，卡片状态由 W5 结项提交收口；结项事实以 `docs/project/backlog/index.md` 与本计划 §5 为准，不改写历史提交信息。
7. **backlog 结项**：6 张卡片 `manage-backlog.py close --resolution delivered` 迁入 archive，`sync-index` 后 index 仪表盘更新（活跃 21 → 15、归档 24 → 30）。

### 1.1 变更范围（写作用域）
- `skills/dual-round-review/scripts/prepare-review-context.py`（BK-0045、BK-0010）
- `skills/dual-round-review/scripts/check-review-report.py`（BK-0008）
- `skills/doc-governance/scripts/manage-doc-index.py`（BK-0016）
- `docs/GOVERNANCE.md`（BK-0007）
- `skills/dual-round-review/SKILL.md`（BK-0014）
- 对应测试：`skills/dual-round-review/tests/test_prepare_review_context.py`、`test_check_review_report.py`、`skills/doc-governance/tests/test_doc_index_convention.py`
- 注册/收尾：`docs/index.md`、`docs/project/backlog/**`、`docs/llms.txt`、本计划

### 1.2 不做（Out of Scope）
- 不修 BK-0041（agy 设计书 / description 压缩 / 测试文件拆分）、BK-0043（三方案待裁决）、BK-0044（政策口径待裁决）。
- 不重构 6 项之外的任何逻辑；不引入配置机制或新依赖（沿用既有 YAGNI 约束）。
- 不改历史 plan/review/proposal 文本。

### 1.3 测试级别
- **L0**：六项各自的行为用例（新增 6 条）+ 既有契约测试全绿。
- **L1**：两脚本 bash↔python 差分矩阵（含新增白名单）。
- **L2**：WSL 全量 `pytest skills/`。
- **L3**：Windows 目标三文件 + Windows 全量失败集 ⊆ 基线（以同一 UTF-8 模式对照，见 §1.0 第 3 条）。
- **L4**：文档四件套门禁 + `judge.py`（`.goal-loop/verify-contract.py` 仅覆盖 8 个既有技能脚本契约壳，本批次不适用，见 §1.0 第 5 条）。

### 1.4 已知有意分歧白名单（R1 不得据此定级阻断项）
1. **BK-0045**：未跟踪清单由「全部 status 条目」收窄为「仅 `??` 条目」——修复目标本身，与 bash 原实现差分必然不同；解析改用 `git status --porcelain -z` 后中文/空格路径不再被 git 引号或八进制转义（R1-7），展示面与旧实现必然不同。
2. **BK-0008**：围栏未闭合告警追加「嵌套围栏演示请避免行首标记」，文案差分必然不同。
3. **BK-0010**：`--archive-root` 空值/根路径新增拒绝分支——原实现无此错误分支，属新增防御而非回归。
4. **BK-0016 的 Windows 用例隔离**：新增端到端用例 `test_register_is_idempotent_with_anchor_variant` 在 Windows 上 `skip`，原因是被调用脚本 `manage-doc-index.py` 打印 emoji 触发存量 cp936 `UnicodeEncodeError`（口径 B 豁免的平台债务，非本批次引入）；同一修复的跨平台覆盖由新增纯逻辑用例 `TestDocLinkDetection`（直接加载模块调用 `has_doc_link`）与 `test_register_rejects_non_compliant_filename`（拒绝分支在写盘前，输出纯 ASCII，Windows 亦运行）承担。
5. **BK-0010 归档根守卫的判定面收窄（R1-3 处置）**：守卫只拦截两类形态——空值、以及经 `os.path.realpath` 解析后仍为文件系统根的路径（含「符号链接指向根」）；`../` 相对外跳、仓库外绝对路径等其余形态由调用方自行保证落在仓库内。`SKILL.md`、代码注释与错误文案同步收窄了「报告不得散落到仓库外任意位置」的宽泛宣称，避免宣称与实现不同宽。
6. **BK-0016 的 fail-closed 收紧（R2 §3.3 裁决，替代最初「放宽正则」方案）**：`validate_file_arg` 新增拒绝含空白 / `#` / `?` / `(` / `)` 的文件名（rc=1 + kebab-case 建议），识别的正则**不放宽**（`[^)\s?#]+`）。BASE 接受这类文件名并导致幂等断裂，故新增拒绝分支属有意分歧；`docs/GOVERNANCE.md` 本已禁止空格命名，全库受跟踪路径中此类名称为 0。

---

## 2. 分阶段任务 (WBS)

- **W1（BK-0045 + BK-0010）**：`_status_second_fields` → 平台无关未跟踪过滤（解析 `git status --porcelain -z`，仅 `??` 条目，路径原样呈现）；`--archive-root=` 非空 + 非文件系统根（`realpath`）校验；各补行为用例（含中文/空格路径原样呈现，R1-7）。
- **W2（BK-0008）**：围栏奇偶告警文案补充嵌套演示规避提示（≤1 行）；补 1 条断言该文案的用例，并以 BASE 脚本做变异验证（R1-4）。
- **W3（BK-0016）**：`register_doc` 幂等判据改为「剥离 `#锚点` / `?查询串` 后与文件名精确比对」，识别正则保持严格（`[^)\s?#]+`）；`validate_file_arg` 对非法文件名 fail-closed（R2 §3.3 裁决）；补锚点变体幂等用例 + 非法名拒绝用例（BASE 变异须杀死）。
- **W4（BK-0007 + BK-0014）**：GOVERNANCE.md §4.1 豁免表文本精确化为「该目录不参与任何计分维度扫描」+ 显式声明归档索引控制头与报告清单互链为无守卫可读性约定（控制头升版 V1.6.2 + 修订行）；`dual-round-review/SKILL.md` 异常分支 7 补一句作废留痕要求。
- **W5**：6 张卡片 close + `sync-index`；`docs/index.md` 登记本计划行与升版；`docs/llms.txt` 重生成；四件套门禁。
- **W6**：`prepare-review-context.py --slug=p3-six-backlog-batch --round=r1 <BASE> <HEAD>` → R1 独立子智能体 → R2 → Zero Blockers → 归档门禁 `--require-verdict=PASS`。本轮 R1 判「不放行」（2 P1 + 9 建议），故按 Full-Delta 从 R1 重走闭环：阻断修复提交后派发 delta-r1（聚焦 R1-1/R1-2 修复证据与直接次生退化）→ delta-r2 终审 → PASS。

---

## 3. 风险与对策
- **差分噪声**：BK-0045/0008/0010 会改变输出，差分矩阵必然出现「预期差异」→ 已在 §1.4 预登记；R1 依据白名单判断。
- **测试夹具跨平台**：`git status -s` 输出在 Windows/WSL 一致；新增用例统一用 `newline="\n"` 写文件、断言 utf-8。
- **卡片文本漂移**：BK-0043/0045 等卡片正文仍写 `.sh`（迁移后已退役）→ 本批次仅在需要时同步所改卡片的引用；其余卡片的 `.sh` 口径作为独立 housekeeping 后续处理。
- **Windows 编码**：新增脚本代码沿用既有 `sys.stdout.reconfigure(encoding="utf-8", newline="\n")`，不新增 print emoji 风险点。

---

## 4. 交付门禁与审查 (Delivery Gate)
- Full 模式双轮独立审查（R1 红队 → R2 元审判），基线 `<BASE>..<HEAD>`，Zero Blockers 后 `--require-verdict=PASS`。
- 审查归档：`docs/project/reviews/<YYYY-MM-DD>-p3-six-backlog-batch/`。
- 只提交本地分支，不 merge、不 push（用户指令）。

---

## 5. 执行日志 (Execution Log)

| 日期 | 事项 | 证据/文件 |
| :--- | :--- | :--- |
| 2026-10-20 | W1（BK-0045）：`_status_second_fields` → `_untracked_paths`（解析 `git status --porcelain -z`，仅 `??` 条目、路径原样呈现），docstring 记录 GNU BRE `\?` 缺陷；调用点同步 | `skills/dual-round-review/scripts/prepare-review-context.py`；新增用例 3 条（三态混排 / 无未跟踪 / 中文+空格路径原样） |
| 2026-10-20 | W1（BK-0010）：`_validate()` 新增 `--archive-root` 空值与文件系统根拦截（rc=1 + 可操作修复提示） | 同上；新增用例 2 条（空值 / `abspath(os.sep)`） |
| 2026-10-20 | W2（BK-0008）：围栏未闭合告警追加「嵌套围栏演示请避免行首标记」；新增诊断可定位性用例 | `skills/dual-round-review/scripts/check-review-report.py`；`test_check_review_report.py::test_unclosed_fence_message_identifies_report_and_parity` |
| 2026-10-20 | W3（BK-0016）：`manage-doc-index.py` 新增 `has_doc_link()`（剥离 `#锚点`/`?查询串` 后比对文件名），替换裸子串判据；新增锚点变体幂等用例 + 跨平台纯逻辑用例 3 条 | `skills/doc-governance/scripts/manage-doc-index.py`；`test_doc_index_convention.py`（`test_register_is_idempotent_with_anchor_variant`、`TestDocLinkDetection`） |
| 2026-10-20 | W4（BK-0007）：GOVERNANCE.md §4.1 主句改「不参与任何计分维度扫描」+ 索引可读性约定守卫边界声明；控制头升 V1.6.2、修订历史滑窗 | `docs/GOVERNANCE.md` |
| 2026-10-20 | W4（BK-0014）：SKILL.md 异常分支 7 补「作废事实与原因须登记归档索引留痕区」 | `skills/dual-round-review/SKILL.md` |
| 2026-10-20 | 定向回归（`7f35a33` 树）：WSL `154 passed`（dual-round-review 全量 + doc-index 文件）；新增用例 WSL `160 passed` / Windows `157 passed, 3 skipped`（改前口径见下一行更正） | `.goal-loop` 本地运行输出 |
| 2026-10-20 | 文档面：`docs/index.md` 登记本计划行（V1.36.8 + 修订行）；`docs/llms.txt` 重生成（85 篇） | `docs/index.md`、`docs/llms.txt` |
| 2026-10-20 | 文档门禁四件套：`check-doc-links`（88 md，0 断链）、`check-doc-control-sync`（42 md，0 漂移）、`trim-revision --keep 5`（87 文件，0 超限）、`audit-doc-health` PASS | `.goal-loop/gates.sh` 输出 |
| 2026-10-20 | **证据口径更正（R1-5 / R2 §1.2.5 采纳）**：`7f35a33` 时点本批次新增用例 **9 条**（WSL collect `499−490`、Windows collect `126−117` 双向互证；「11」为选择器含既有用例的误读）。「消除 154」数学不成立（R1 结论维持、其「248 日志混用」归因被 R2 驳回）：提交 `7f35a33` 的 Windows 结果与 BASE `7a2a3a0` 同为 **94 failed**，故正确表述为「新增失败 0、新增通过 8」。「WSL 499 passed」仅在干净树成立（未跟踪空台账归档会让归档门禁既有用例 1 failed）。附带更正：计划原称「4 个测试文件」实际 3 个（`test_prepare_review_context.py` / `test_check_review_report.py` / `test_doc_index_convention.py`），已改；BK-0045 为 P2 例外已在 §1.0 第 1 条注明。 | 本计划 §1.0/§1.3/§5；`.goal-loop/win-batch.txt`、`win-baseline.txt` |
| 2026-10-20 | 提交 `7f35a33`（W1–W5 代码与文档落盘；11 files / +306 / −21）。提交信息中的「消除 154」「11 passed」数字口径以本节更正行为准。 | `git show --stat 7f35a33` |
| 2026-10-20 | R1 派发与归档：句柄 `8d6c5172`，报告 17780 B / SHA256 `3ea790f6960b…`；裁决**不放行**（🔴 2 + 🟡 3 + ⚪ 6），并主动驳回 §1.4 白名单四项（驳回理由经复核成立：白名单仅提供定级豁免，不豁免卡片结项与证据口径）。 | `docs/project/reviews/2026-10-20-p3-six-backlog-batch/` |
| 2026-10-20 | R2 派发（同基线 `7a2a3a0..7f35a33`，句柄 `bd273adc`），要求逐条裁决 R1 的 11 项并复核 R1-1/R1-2/R1-5。 | `.goal-loop/dispatch-ledger.md` |
| 2026-10-20 | **R1-1 修复**：六卡 §3 DoD 全部勾选 + `manage-backlog.py close --resolution delivered` 迁入 `archive/2026-Q4/` + `sync-index`；instrument 活跃 21→15、归档 24→30。计划 §1.0 第 6 条补「代码闭环 vs 卡片结项」处置口径。 | `docs/project/backlog/index.md`、`archive/2026-Q4/` |
| 2026-10-20 | **R1-2 修复（R2 §3.3 口径：fail-closed，不放宽正则）**：`validate_file_arg` 拒绝含空白 / `#` / `?` / `(` / `)` 的文件名（rc=1 + kebab-case 建议）；`has_doc_link` 识别正则保持严格 `[^)\s?#]+`；用例改为 `test_register_rejects_non_compliant_filename`（拒绝分支零写入，Windows 亦运行）与 `test_link_target_grammar_stops_at_unsafe_characters`。取证：HEAD 单次 rc=1、连续 3 次 rc=1 且 `index_exists=no`；BASE 脚本变异下拒绝用例 **1 failed**（可杀死）。 | `skills/doc-governance/scripts/manage-doc-index.py`、`test_doc_index_convention.py`；`.goal-loop/bk16-evidence.sh` |
| 2026-10-20 | **R1-3 修复**：归档根根判定改用 `os.path.realpath`（覆盖符号链接指向根）；`SKILL.md` 与错误文案把宣称收窄为「空值 + 解析后为根」两类形态（§1.4 第 5 项）。 | `skills/dual-round-review/scripts/prepare-review-context.py`、`SKILL.md` |
| 2026-10-20 | **R1-4 修复**：围栏诊断用例补断言「嵌套围栏演示请避免行首标记」——对 BASE 脚本变异可杀死（此前该用例对 BASE 同样通过＝空转）。 | `skills/dual-round-review/tests/test_check_review_report.py` |
| 2026-10-20 | **R1-10/R1-11 修复**：计划删除 `verify-contract.py` 的本批次适用性引用（§1.0 第 5 条、§1.3 L4）；`SKILL.md` 异常分支 7 留痕要求补「与 §1.6 转录降级留痕要求同构」。 | 本计划、`skills/dual-round-review/SKILL.md` |
| 2026-10-20 | 结项工具的平台依赖观察（非本批次引入，未修）：`manage-backlog.py` 在 Windows 生成索引链接用 `\`，在 WSL/Linux 用 `/`；本次在 Windows 上 `close`/`sync-index` 后 WSL 的 `check-doc-links` 报 35 处 404，改用 WSL 重跑 `sync-index` 后恢复（88 md 0 断链）。该跨平台差异登记为后续独立事项（对应 BK-0037 输出路径族），不纳入本批次写作用域。 | `docs/project/backlog/index.md`；WSL 门禁输出 |
| 2026-10-20 | **R1-4 变异取证**：`test_unclosed_fence_message_identifies_report_and_parity` 对 BASE 脚本（`7a2a3a0` 的 `check-review-report.py`）运行 → **1 failed**（空转已消除；脚本恢复后零差异）。 | `.goal-loop` 本地运行输出 |
| 2026-10-20 | **R1-7 修复**：`_untracked_paths` 改解析 `git status --porcelain -z`（NUL 分隔，无引号/八进制转义）；新增用例 `test_untracked_block_preserves_unicode_and_space_paths`（`文档 名.md` 原样、无 `\346`、无引号）。 | `skills/dual-round-review/scripts/prepare-review-context.py`、`test_prepare_review_context.py` |
| 2026-10-20 | **R2 归档**：句柄 `bd273adc`，报告 37922 B / SHA256 `efdaf03adcd3…`；裁决 **🔴 不予交付（Blockers=1，R1-1）**，R1-2 由 P1 降 P2（真实回归、本轮必修），🟡 10（P2×4 + P3×6）、⚪ 0；README 升 V1.0.2、台账 r2 行 `direct`、门禁 rc=0（报告 2 份）。 | `docs/project/reviews/2026-10-20-p3-six-backlog-batch/` |
| 2026-10-20 | **Windows umbrella 取证环境更正**：plain Windows（cp936 控制台）下 HEAD 因测试端 `encoding="utf-8"` 解码子进程 cp936 输出而出现 18 条新增 `UnicodeDecodeError` 失败，不能作为判定环境；改以 **UTF-8 模式**（`PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8`）同口径对照两棵树：BASE `7a2a3a0` = 12 failed / 464 passed / 14 skipped；HEAD（修复后）= 12 failed / 475 passed / 16 skipped，**失败集逐条相同（新增失败 0）**。DRR 两测试文件 0 failed、doc-index 文件 0 failed（≤20 门槛）。 | `.goal-loop/win-base7a-utf8.txt`、`win-head-utf8-final.txt` |
| 2026-10-20 | **R1-1 收口**：`docs/index.md` V1.36.8 → V1.36.9（修订历史滑窗），§4 本计划行由「进行中」改「已完成」并链接审查归档；六卡状态 `delivered`/迁入 `archive/2026-Q4/`、index 活跃 21→15、归档 24→30。 | `docs/index.md`、`docs/project/backlog/index.md` |
| 2026-10-20 | **R2 §3.3 前置条件逐条落实**：R1-1（六卡结项 + DoD 勾选 + index + docs/index.md + 计划检查点/§5）、R1-4（补断言 + 变异）、R1-11（同构声明，前提交）、R1-2（fail-closed）、R1-5/R1-10（口径更正与计划行）、R1-3（SKILL:118 收窄，前提交）、R1-7（`-z`）。 | 本计划 §5 |
| 2026-10-20 | 修复提交落盘后派发 **delta-r1**（基线 `7f35a33..<修复提交>`，聚焦阻断修复证据与次生退化）→ delta-r2 终审 → `--require-verdict=PASS`。 | `git log`；`.goal-loop/dispatch-ledger.md` |
| 2026-10-20 | **Delta-r1 归档与裁决**：句柄 `eeb36673`，报告 30332 B / SHA256 `13db2d6d5baba…`；判 **不放行**（1 阻断 DR-1：`docs/index.md` 提前宣称「已完成 / Delta 闭环 Zero Blockers」，与计划「进行中」、README 终审「未定」、门禁 rc=1 冲突 → 宣称宽于取证）。独立复核确认 **R1-2/R1-4/R1-7 已根治**，新增 🟡 2（DR-7 非 UTF-8 文件名崩溃、DR-8 计划数字取自 `f1f2189` 树）。 | `docs/project/reviews/2026-10-20-p3-six-backlog-batch/README.md` |
| 2026-10-20 | **Delta-r1 阻断与建议处置**：DR-1 → `docs/index.md` 恢复「进行中（Delta 复核中）」口径、修订历史去掉未兑现的「已完成 / Zero Blockers」；DR-7 → `prepare-review-context.py` 输出侧 `errors="surrogateescape"` 与 git 解码口径对齐 + POSIX 专用非 UTF-8 文件名用例；DR-8 → 计划 Windows 数字更正为 475 passed / 16 skipped（`:34` / `:45` / `:134` 三处同步）；DR-5 → `has_doc_link` 要求「可选锚点/查询串 + 右括号」收尾并补 4 条负例断言；DR-6（原始状态块 C-quote，历史既有 P3）登记为后续项不修。 | 修复提交 diff |
| 2026-10-20 | **Delta-r2 归档与裁决**：句柄 `c8f54bab`，报告 35774 B / SHA256 `9d4ff312e9aa…`；终审 **✅ 准予交付（Blockers=0）**：DR-1/DR-5/DR-7 关闭、DR-6 维持后续项、DR-8 要求闭包口径统一；同时指出 🔴 闭包结构阻断（delta-r1 已归档而 delta-r2 默认命名 `8de971e..1f6a826` 与配对键不兼容，门禁 rc=1）→ 本提交处置。 | `docs/project/reviews/2026-10-20-p3-six-backlog-batch/README.md` |
| 2026-10-20 | **闭包处置（delta-r2 §3.3 逐条）**：① delta-r2 报告改名为 `delta-r2-7f35a33..1f6a826.md`（与 delta-r1 同基线键；字节与 SHA256 不变，README 加 `[!NOTE]` 留痕）；② README 台账/链接/指纹补登，终审裁决置为 `✅ 准予交付`（V1.0.4）；③ 计划 `:34/:45/:134` 数字与 `:35/:36` 口径统一为闭包态；④ `docs/index.md` 恢复「已完成」并注明四轮审查闭环（仅在门禁 PASS 后书写）；⑤ llms.txt 重生成与文档四件套复跑。 | `docs/index.md`、本计划、归档 README |
| 2026-10-20 | **闭包提交号回填（书签提交）**：闭包提交 `4d4eed8`（4 files, +304/−11：归档 README V1.0.4、delta-r2 报告改名入库、计划闭包态、docs/index.md 完成态）；本行由随后书签提交写入，避免计划文档自指。 | 本计划 :35、§5 |
