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
- **当前活跃阶段**: P3（集成验证与文档同步）
- **当前活跃子任务**: W5 卡片结项/注册面/门禁 → W6 双轮独立审查
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 1/5
- **最后一次验证状态**: WSL 定向 154 passed（dual-round-review 全量 + doc-index 文件）；新增用例单测 11 passed（WSL）/10 passed + 1 skipped（Windows）；Windows 定向 21 failed 全部为 doc-governance 存量 cp936 债务（⊆ 基线）
- **最新有效提交**: `7a2a3a0`（批次基线；本批次改动未提交）
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收准则
1. **六张卡片 DoD 逐项达成**：BK-0045 / BK-0010 / BK-0008 / BK-0016 / BK-0007 / BK-0014 卡片 §3 所列验收条件全部满足。
2. **WSL 全量回归**：`python3 -B -m pytest skills/ -q` **0 failed** 且通过数 ≥ 490（基线 490）。
3. **Windows umbrella**：`.venv\Scripts\python.exe -B -m pytest skills/ -q` 失败集 ⊆ 改造前基线失败集（新增失败 0；存量 cp936/POSIX-only 债务按口径 B 豁免披露），且本次触碰的 4 个测试文件在 Windows 原生全绿——例外：`test_doc_index_convention.py` 的存量 20 条 cp936 失败属基线债务（`manage-doc-index.py` / `scaffold-doc.py` 调用的兄弟脚本 emoji 输出），按口径 B 豁免披露；本批次在该文件新增的端到端用例以 `unittest.skipIf(os.name == "nt")` 隔离并给出原因，新增纯逻辑用例 `TestDocLinkDetection` 在 Windows 全绿（见 §1.4 第 4 项）。
4. **差分矩阵**：`prepare-review-context`、`check-review-report` 的 bash↔python 差分在「有意分歧白名单」之外逐字节一致（见 §1.4）。
5. **契约与文档门禁**：`verify-contract.py` 0 失败；`check-doc-links` / `check-doc-control-sync` / `audit-doc-health` / `trim-revision --keep 5` 全绿；`judge.py` 无新增 BLOCKER/HIGH 发现。
6. **交付流程**：独立子智能体 R1（红队）→ R2（架构师元审判）Zero Blockers 裁决；审查报告逐字归档并登记台账与 SHA256 指纹。
7. **backlog 结项**：6 张卡片 `manage-backlog.py close --resolution delivered` 迁入 archive，`sync-index` 后 index 仪表盘更新。

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
- **L3**：Windows 目标四文件 + Windows 全量失败集 ⊆ 基线。
- **L4**：文档四件套门禁 + `verify-contract.py` + `judge.py`。

### 1.4 已知有意分歧白名单（R1 不得据此定级阻断项）
1. **BK-0045**：未跟踪清单由「全部 status 条目」收窄为「仅 `??` 条目」——修复目标本身，与 bash 原实现差分必然不同。
2. **BK-0008**：围栏未闭合告警追加「嵌套围栏演示请避免行首标记」，文案差分必然不同。
3. **BK-0010**：`--archive-root` 空值/根路径新增拒绝分支——原实现无此错误分支，属新增防御而非回归。
4. **BK-0016 的 Windows 用例隔离**：新增端到端用例 `test_register_is_idempotent_with_anchor_variant` 在 Windows 上 `skip`，原因是被调用脚本 `manage-doc-index.py` 打印 emoji 触发存量 cp936 `UnicodeEncodeError`（口径 B 豁免的平台债务，非本批次引入）；同一修复的跨平台覆盖由新增纯逻辑用例 `TestDocLinkDetection`（直接加载模块调用 `has_doc_link`）承担，该用例在 Windows 全绿。

---

## 2. 分阶段任务 (WBS)

- **W1（BK-0045 + BK-0010）**：`_status_second_fields` → 平台无关未跟踪过滤（仅 `??` 行）；`--archive-root=` 非空 + 非文件系统根校验；各补 1 条行为用例。
- **W2（BK-0008）**：围栏奇偶告警文案补充嵌套演示规避提示（≤1 行）；补 1 条断言该文案的用例。
- **W3（BK-0016）**：`register_doc` 幂等判据改为「剥离 `#锚点` / `?查询串` 后与文件名精确比对」；补锚点变体用例。
- **W4（BK-0007 + BK-0014）**：GOVERNANCE.md §4.1 豁免表文本精确化为「该目录不参与任何计分维度扫描」+ 显式声明归档索引控制头与报告清单互链为无守卫可读性约定（控制头升版 V1.6.2 + 修订行）；`dual-round-review/SKILL.md` 异常分支 7 补一句作废留痕要求。
- **W5**：6 张卡片 close + `sync-index`；`docs/index.md` 登记本计划行与升版；`docs/llms.txt` 重生成；四件套门禁。
- **W6**：`prepare-review-context.py --slug=p3-six-backlog-batch --round=r1 <BASE> <HEAD>` → R1 独立子智能体 → R2 → Zero Blockers → 归档门禁 `--require-verdict=PASS`。

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
| 2026-10-20 | W1（BK-0045）：`_status_second_fields` → `_untracked_paths`（仅 `??` 行、去引号、join），docstring 记录 GNU BRE `\?` 缺陷；调用点同步 | `skills/dual-round-review/scripts/prepare-review-context.py`；新增用例 2 条（三态混排 / 无未跟踪） |
| 2026-10-20 | W1（BK-0010）：`_validate()` 新增 `--archive-root` 空值与文件系统根拦截（rc=1 + 可操作修复提示） | 同上；新增用例 2 条（空值 / `abspath(os.sep)`） |
| 2026-10-20 | W2（BK-0008）：围栏未闭合告警追加「嵌套围栏演示请避免行首标记」；新增诊断可定位性用例 | `skills/dual-round-review/scripts/check-review-report.py`；`test_check_review_report.py::test_unclosed_fence_message_identifies_report_and_parity` |
| 2026-10-20 | W3（BK-0016）：`manage-doc-index.py` 新增 `has_doc_link()`（剥离 `#锚点`/`?查询串` 后比对文件名），替换裸子串判据；新增锚点变体幂等用例 + 跨平台纯逻辑用例 3 条 | `skills/doc-governance/scripts/manage-doc-index.py`；`test_doc_index_convention.py`（`test_register_is_idempotent_with_anchor_variant`、`TestDocLinkDetection`） |
| 2026-10-20 | W4（BK-0007）：GOVERNANCE.md §4.1 主句改「不参与任何计分维度扫描」+ 索引可读性约定守卫边界声明；控制头升 V1.6.2、修订历史滑窗 | `docs/GOVERNANCE.md` |
| 2026-10-20 | W4（BK-0014）：SKILL.md 异常分支 7 补「作废事实与原因须登记归档索引留痕区」 | `skills/dual-round-review/SKILL.md` |
| 2026-10-20 | 定向回归：WSL `154 passed`（dual-round-review 全量 + doc-index 文件）；新用例 WSL `11 passed` / Windows `10 passed, 1 skipped`（BK-0016 端到端按 §1.4 第 4 项隔离） | `.goal-loop` 本地运行输出 |
| 2026-10-20 | 文档面：`docs/index.md` 登记本计划行（V1.36.8 + 修订行）；`docs/llms.txt` 重生成（85 篇） | `docs/index.md`、`docs/llms.txt` |
| 2026-10-20 | 文档门禁四件套：`check-doc-links`（88 md，0 断链）、`check-doc-control-sync`（42 md，0 漂移）、`trim-revision --keep 5`（87 文件，0 超限）、`audit-doc-health` PASS | `.goal-loop/gates.sh` 输出 |

