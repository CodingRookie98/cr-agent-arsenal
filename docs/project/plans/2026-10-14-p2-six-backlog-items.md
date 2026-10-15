# P2 批次六项 backlog 卡片闭环实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-P2-SIX-2026
> - **当前版本**: V1.3.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-14

> **目标元数据**
> - **所属项目**: cr-agent-arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 闭环 `docs/project/backlog/active/` 中全部 6 张 P2 卡片（BK-0003 / BK-0004 / BK-0020 / BK-0033 / BK-0034 / BK-0040）——按各卡既有 DoD 完成 TDD 修复与契约测试，通过 L0/L1/L-Doc 门禁，取得独立 Zero Blockers 终审裁决后逐卡结项归档
> - **创建日期**: 2026-10-14
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-14（「那就做P2」）
> - **批准基线**: `master` @ `1b17965`（backlog 理牌提交）
> - **状态**: 已完成（P5 结项归档 + 已合入 `master` @ `892fc14`，交付分支已删除）
> - **隔离分支**: `fix/p2-six-backlog-items`（基点 `1b17965`）
> - **需求确认文档**: 豁免（需求源为 6 张卡片的既有 DoD 字段，已由历次双轮审查裁定；本轮不新增公共契约，仅收紧既有脚本的失败语义）
> - **技术调研备忘录**: 豁免（零第三方依赖；纯标准库 + 既有 pytest/shell 约定，无选型空间）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`（已被 `.gitignore` 忽略）

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语，不另建并行状态文件；本文件的复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: 交付完成（P0~P5 全阶段闭环，分支已合入并删除）
- **当前活跃子任务**: Task P4.3 完成——经用户裁决合入 `master`（`892fc14`），交付分支 `fix/p2-six-backlog-items` 已用 `git branch -d` 删除
- **当前子任务重试计数**: 1/3（R1 阻断项一轮修复闭环）
- **外层循环迭代**: 1/5（Delta Re-Loop 1 次：R1 阻断 → `deb691e` 修复 → R2 复核 Zero Blockers）
- **最后一次验证状态**: P5 结项实测——`python3 -m pytest skills/ -q` = **472 passed**；`check-review-report.sh <本归档> --require-verdict=PASS` rc=0（r1/r2 双轮按基线 `1b17965` 配对、稳定 ID 双向对齐）；全部 10 个审查归档回放 rc=0；L-Doc 断链 0（85 份文档）+ 健康体检 PASS（100/100）；backlog 活跃 33→20、归档 24
- **最新有效提交**: `892fc14`（merge: P2 批次六项卡片 TDD 闭环；被合并基线 `a79eabc`，合并后树与 `a79eabc` 逐字节一致）
- **阻断原因**: 无（R2 终审 ✅ 准予交付，Blockers = 0）

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收口径 (Acceptance Criteria — 由需求方定义)
- **验收人 (Acceptor)**: 王辉
- **验收场景 (Acceptance Scenarios)**: 6 张卡片各自的 `acceptance_criteria` 字段逐条被新增/既有回归用例覆盖，且每个用例在收紧前的实现上转红；全库 `pytest skills/ -q` Exit 0；文档门禁（断链 0 / 健康体检 PASS / 控制头同步 PASS）；6 张卡片由 `manage-backlog.py close` 结项归档。
- **明确不验收项 (Non-Acceptance)**: 不新增公共 API/契约能力；不引入第三方依赖；不做 `check-review-report.sh` 的裁决语义解析器或 `.docignore` 机制（BK-0003 卡片明文禁止）；不改动 `spec-evolution` 判据表 C-01~C-10 的语义。
- **口径冲突裁决人**: 王辉

### 1.1 核心交付物清单
- [x] `skills/dual-round-review/scripts/check-review-report.sh`（BK-0003 / BK-0004）
- [x] `skills/dual-round-review/tests/test_check_review_report.py`（BK-0003 / BK-0004 回归）
- [x] `skills/doc-governance/scripts/manage-doc-index.py`（BK-0020）
- [x] `skills/doc-governance/tests/test_doc_index_convention.py`（BK-0020 回归）
- [x] `skills/spec-evolution/scripts/collect-facts.py`（BK-0033 / BK-0034）
- [x] `skills/spec-evolution/scripts/judge.py`（BK-0033 / BK-0034 / BK-0040）
- [x] `skills/spec-evolution/tests/{test_collect_facts.py,test_judge_contract.py}`（BK-0033/0034/0040 回归）
- [x] 6 张卡片结项归档：`docs/project/backlog/archive/2026-Q4/` + `docs/project/backlog/index.md`（脚本生成）

### 1.2 依赖选型与开源调研结论 (Research & Feasibility Spike)
- **P0.5 备忘录**: 豁免
- **开源复用/自研裁决**: 仅复用既有标准库与既有测试夹具（`tests/conftest.py` 的 `build_repo` / `_build` 归档夹具），零新增依赖
- **API 权威契约与版本验证**: 仅用 `pathlib` / `json` / `sys.stdout.reconfigure`（Python 3.7+ 标准 API）与 `bash` 内建 参数展开/关联数组

### 1.3 严禁事项与反模式 (Strict Exclusions)
- 严禁修改未在目标范围内的公共核心契约（退出码 0/1/2 语义**保持不变**，仅把逃逸路径归位到既有契约）；
- 严禁未跑测试直接提交代码；
- 严禁为了让测试转绿而弱化既有断言；
- 严禁用 `rm` 物理删除卡片（BK 编号契约要求走 `close → archive`）。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: MEDIUM（三个技能的机械门禁脚本；不改变对外 CLI 契约，但改变失败语义）
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `bash -n`（shell）、`python3 -m py_compile`、`git diff --check`
  - [x] **L1 单元测试**: `python3 -m pytest skills/ -q`（新增契约用例须先在旧实现上转红）
  - [x] **L2 模块集成测试**: 对 `docs/project/reviews/` 全部 9 个真实归档实跑 `check-review-report.sh`（回归不得出现新 FAIL）；真实仓库实跑 `collect-facts.py` + `judge.py`
  - [ ] **L3 端到端测试**: 豁免（无用户主干交互链路；L2 的真实归档与新仓库回放已覆盖端到端路径）
- **豁免测试级别与充分依据**: 豁免 L3。理由：改动集中在三个纯本地脚本的判定/失败语义，L2 已在真实数据（9 个归档 + 真实仓库）上贯通全链路。
- **精确验证命令清单**:
  ```bash
  # L0
  bash -n skills/dual-round-review/scripts/check-review-report.sh
  python3 -m py_compile skills/spec-evolution/scripts/*.py skills/doc-governance/scripts/*.py
  git diff --check
  # L1
  python3 -m pytest skills/ -q
  # L2
  for d in docs/project/reviews/*/; do bash skills/dual-round-review/scripts/check-review-report.sh "$d"; done
  python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --out /tmp/facts.json && \
    python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json
  # L-Doc
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P3 准备: 隔离分支与环境前置检查
- [x] **Task P3.0**: 创建 `fix/p2-six-backlog-items`（基点 `1b17965`）；基线 `pytest skills/ -q` = 450 passed；锁定 Diff 范围为上列 7 个文件 + 结项产物
  - **验收方式**: 基线测试 Exit Code 0（已实测）

### P3: 核心功能原子实现 (TDD 循环)
- [x] **Task P3.1（BK-0003）**: 稳定 ID 方向二改为**按文件名基线配对**后施加，并加「R1 清单非空 ⇒ 配对 R2 明细表非空」断言
  - **涉及文件**: `skills/dual-round-review/scripts/check-review-report.sh`, `skills/dual-round-review/tests/test_check_review_report.py`
  - **TDD 步骤**: 🔴 共享归档「旧轮 R2 占位 + 新轮空明细表」用例转红 ➔ 🟢 按基线配对 ➔ 🔵 复用 `section_ids` ➔ ✅ 9 个真实归档回归 ➔ 💾 原子提交
  - **计划偏差（已落地）**: 🔵 步骤中「复用 `section_ids`」被证伪——只改配对而保留旧的全文 `grep -oE 'R1-[0-9]+'` 抽取，会把跨轮污染从「全局并集」原样搬进「同基线配对」，令两个真实归档（`2026-10-08-subagent-direct-write`、`2026-10-09-quadrant-index-convention`）报出并不存在的「未定性缺陷」（`DR1-7` 内含 `R1-7`；`delta-r1-458b4d2..e7cd191.md:47` 明文依赖旧抽取器的污染行为）。故同批把 `section_ids` 收紧为**该区块「稳定 ID」契约表格的首列**抽取，并逐归档验证 4 个含 R2 的归档按基线逐条 ID 对称。
  - **验收命令**: `python3 -m pytest skills/dual-round-review/tests/test_check_review_report.py -q`
- [x] **Task P3.2（BK-0004）**: 新增「`**终审裁决**` 在索引中唯一」校验（命中数 ≠ 1 → rc=1，≤3 行）
  - **涉及文件**: 同上
  - **TDD 步骤**: 🔴 索引含两处命中（围栏示例抢答）用例转红 ➔ 🟢 `grep -cF` 计数校验 ➔ ✅ 全部归档（各 1 处命中）不回归 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/dual-round-review/tests/test_check_review_report.py -q`
  - **收口**: BK-0003 与 BK-0004 改动同一脚本同一文件的两个区块、且共享同一份门禁契约，故合并为一个原子提交 `eb6e9a2`（拆成两个提交需手工构造分部补丁，无审查收益）。
- [x] **Task P3.3（BK-0020）**: `insert_revision_row` 表头定位限定在『修订历史记录』章节作用域内
  - **涉及文件**: `skills/doc-governance/scripts/manage-doc-index.py`, `skills/doc-governance/tests/test_doc_index_convention.py`
  - **TDD 步骤**: 🔴 无关同名表头（位于修订历史之前）用例转红 ➔ 🟢 章节作用域定位 + 章节边界 ➔ ✅ 既有 R1-5/DR1-8 用例不回归 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/doc-governance/tests/ -q`
- [x] **Task P3.4（BK-0034）**: `baseline.json` 损坏显式失败；judge 对 baseline 缺失/为 0 给出显式提示
  - **涉及文件**: `skills/spec-evolution/scripts/collect-facts.py`, `skills/spec-evolution/scripts/judge.py`, `skills/spec-evolution/tests/test_collect_facts.py`, `skills/spec-evolution/tests/test_judge_contract.py`
  - **TDD 步骤**: 🔴 假阳性（损坏基线静默降级为 0 基线）与假阴性（baseline 键缺失静默跳过 C-10）两用例转红 ➔ 🟢 采集侧 fail-closed（rc=2）+ 判定侧显式提示 ➔ ✅ 既有 C-10 用例不回归 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/spec-evolution/tests/ -q`
- [x] **Task P3.5（BK-0033）**: 两脚本 print 在非 UTF-8 环境下硬化；编码异常路径退出码收敛为 2
  - **涉及文件**: `skills/spec-evolution/scripts/collect-facts.py`, `skills/spec-evolution/scripts/judge.py`, `skills/spec-evolution/tests/test_gate_invariants.py`
  - **TDD 步骤**: 🔴 `LC_ALL=C PYTHONUTF8=0 PYTHONIOENCODING=ascii` 下 `UnicodeEncodeError` 裸 traceback（rc=1）用例转红 ➔ 🟢 流降级 `errors="replace"` + 入口兜底 rc=2 ➔ ✅ 正常环境输出不回归 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/spec-evolution/tests/ -q`
- [x] **Task P3.6（BK-0040）**: `build_findings` 嵌套类型逃逸兜底转译为退出码 2 且不写出产物
  - **涉及文件**: `skills/spec-evolution/scripts/judge.py`, `skills/spec-evolution/tests/test_judge_contract.py`
  - **TDD 步骤**: 🔴 5 类嵌套畸形（`description_chars` / `registrations`×2 / `oversized_files` / `cross_skill_links`）rc=1 用例转红 ➔ 🟢 `main()` 兜底 ➔ ✅ 5 例全 rc=2 且零产物 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/spec-evolution/tests/ -q`

### P3.5: 集成验证与端到端贯通
- [x] **Task P3.5.1**: 全库 L1 + 真实数据 L2 回放（9 个归档 + 真实仓库 collect/judge）
- [x] **Task P3.5.2**: L-Doc 门禁（断链 0 / 健康体检 PASS / 控制头同步 PASS / 机器地图一致）

### P4: 双轮对抗终审与再循环闭环硬门禁 (Dual-Round Review & Re-Loop Gate)
- [x] **Task P4.1**: R1 红队（agy · Gemini 3.8 Flash High）审查 `1b17965..92f749c` → **不准予交付（2×P1 / 2×P2 / 1×P3）**；R2 元架构师复核 `1b17965..deb691e` → **✅ 准予交付（Blockers = 0；0 驳回）**
  - **报告**: `docs/project/reviews/2026-10-14-p2-six-backlog-items/{r1-1b17965..92f749c.md,r2-1b17965..deb691e.md}`（SHA256 前 12 位 `86b8ad52e118` / `21d5d6f93888`，台账登记 `direct`）
- [x] **Task P4.2**: Delta Re-Loop 1 次——R1-1（R2 模板表头契约冲突）/ R1-2（消费期兜底浅层）2 个 P1 与 R1-3/R1-4/R1-5 全部修于 `deb691e`，新增 5 条回归用例（旧实现转红→修后转绿）
  - **备注**: 新增用例覆盖 R1 未发现的同类面，其中 `test_consumption_phase_malformation_exits_2_without_artifacts` 是 R1-2 的直接反证
- [x] **Task P4.3**: 用户裁决「合并然后删除分支」→ `git checkout master` + `git merge --no-ff fix/p2-six-backlog-items` = `892fc14`（merge 提交，沿用仓库既有 `merge:` 前缀惯例）；`git diff a79eabc HEAD` 为空（树逐字节一致）；`git branch -d fix/p2-six-backlog-items` 完成删除
  - **备注**: `origin/master` 尚未推送（推送需用户单独确认，仓库红线）
- **备注**: BK-0040 卡片 DoD 明示「修复后必须作为新基线重跑完整双轮闭环（单测全绿不替代外部审查）」，故本轮以整批提交为基线派发一次全量双轮。

### P5: 文档全向归档与联动升级
- [x] **Task P5.1**: 6 张卡片 `manage-backlog.py close --resolution delivered` 结项迁入 `archive/2026-Q4/`，`sync-index` 刷新仪表盘（活跃 33→20，归档 24）；DoD 复选框与 §4 占位语由作者按实况收敛（工具缺口 BK-0042）
- [x] **Task P5.2**: 本计划置 `已完成`（V1.2.0）并记录结项实测
- [x] **Task P5.3**: 审查凭据归档——R1/R2 报告全文逐字落盘 + SHA256 独立复算 + 轮次台账登记 + `--require-verdict=PASS` rc=0

---

## 4. 研究发现与环境状态记录 (Context Log)

- **[2026-10-14] 探查记录 1（BK-0003 配对键选择）**: 归档内轮次文件名形如 `r1-<base7>..<head7>.md` / `delta-r2-<base7>..<head7>.md`。实测 9 个真实归档中，`<base7>` 恰为**被审查基线**：R2 的 base 等于其裁决的 R1 轮的 base（例：`2026-10-12-spec-evolution-v1` 的两个 delta-r1 与 delta-r2 共享 base `fe8da78`，而 delta-r2 的 head 为 `2100136`，与 R1 的 head **不同**）。故配对键取 `<base7>` 而非整段 `<base7>..<head7>`；后者会误判该真实归档未闭环。
- **[2026-10-14] 探查记录 2（BK-0020 作用域前提）**: 仓库内 21 份文档含 `| 版本号` 表，其中 10 份无『修订历史记录』标题；但 `insert_revision_row` 仅由 `register` 在**托管象限索引**（`build_skeleton` 产物，必含该标题）上调用，故把标题设为定位前提不会误伤既有文档，且失败语义 fail-closed 与 R1-5 一致。
- **[2026-10-14] 探查记录 3（BK-0034 现实态）**: `skills/spec-evolution/references/baseline.json` 现存且与 `contexts/AGENTS.md` 实测一致（98 行 / 11015 字节），故 C-10 当前不触发；损坏场景纯属污染可达，修复按 fail-closed 处理。

---

## 5. 修订历史 (Revision History)

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-14 | AI Agent | 架构师 | 计划创建：P2 批次六项卡片 TDD 闭环 |
| **V1.1.0** | 2026-10-14 | AI Agent | 架构师 | P3 六项卡片实现与集成验证收口（467 passed / L-Doc PASS），进入 P4 双轮终审 |
| **V1.2.0** | 2026-10-14 | AI Agent | 架构师 | P4 双轮闭环（R1 阻断 2×P1 → `deb691e` 修复 → R2 准予交付，Blockers = 0）与 P5 结项归档（6 卡 delivered、472 passed、归档门禁 PASS）；`master` 合入待用户裁决 |
| **V1.3.0** | 2026-10-15 | AI Agent | 架构师 | 交付闭环：经用户裁决以 `--no-ff` 合并入 `master`（`892fc14`，合并后树与 `a79eabc` 一致）并删除交付分支；`origin/master` 推送待用户确认 |
