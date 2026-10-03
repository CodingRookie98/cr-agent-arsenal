# dual-round-review 审查报告持久化归档实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-DUAL-ROUND-REVIEW-ARCHIVE-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-04

> **目标元数据**
> - **所属项目**: cr-agent-arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 为 `dual-round-review` 增加交付凭据归档契约——报告全文逐字落盘至版本库跟踪的归档根，并新增机械门禁，使审查凭据对人类与子智能体持久可读、可寻址、可校验
> - **创建日期**: 2026-10-04
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-04 00:44
> - **批准基线**: 分支 `feature/goal-review-report-archive`，基点 `940e0f3`
> - **状态**: 进行中
> - **隔离分支**: `feature/goal-review-report-archive`
> - **需求确认文档**: [RFC-0001 审查报告持久化归档契约](../../proposals/RFC-0001-review-report-archive.md)
> - **技术调研备忘录**: 豁免（P0.5 未触发——复用 `frontend-qa-gate` 既有的报告校验器范式与 `prepare-review-context.sh` 既有脚本，无新第三方依赖；社区惯例调研已在 P0 阶段随方案拷问完成，见 RFC §4）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`（已被 `.gitignore` 忽略）

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语，不另建并行状态文件；本文件的复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P3 TDD 循环
- **当前活跃子任务**: Task P3.1
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: P0 出口已验证 —— 断链 0、健康度 99.4/100（RFC 落盘）
- **最新有效提交**: 无（本次提交）
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收口径 (Acceptance Criteria — 由需求方定义)

- **验收人 (Acceptor)**: 王辉
- **验收场景 (Acceptance Scenarios)**:
  1. 对一次真实双轮审查，归档目录以**被版本库跟踪**的新增文件出现在 `docs/project/reviews/` 下；
  2. 打开归档目录可直接阅读 R1 与 R2 的**报告全文**（含攻击路径推演与裁决明细表全部行），而非摘要；
  3. `bash skills/dual-round-review/scripts/check-review-report.sh <归档目录>` 退出码为 0；
  4. 人为篡改报告一行后重跑该校验器，退出码非 0（指纹校验生效）。
- **明确不验收项 (Non-Acceptance)**: 历史交付（`frontend-qa-gate` 等）审查报告的原文回填；报告体量自动裁剪/保留期策略；`frontend-qa-gate` 或其他技能的落位改造（RFC §2.2 Non-Goals）。
- **口径冲突裁决人**: 王辉

### 1.1 核心交付物清单

- [ ] **技能规程**: `skills/dual-round-review/SKILL.md`（铁律 5 扩展、新增步骤 1.6 交付凭据归档、步骤 2/3 归档动作、恢复规则、参考导航）
- [ ] **机械门禁**: `skills/dual-round-review/scripts/check-review-report.sh`（新增）
- [ ] **上下文脚本**: `skills/dual-round-review/scripts/prepare-review-context.sh`（新增 `--slug` / `--archive-root` 归档 scaffold，默认关闭以保持向后兼容）
- [ ] **提示词模板**: `skills/dual-round-review/references/round-1-red-team.md`、`references/round-2-meta-architect.md`（归档说明 + R2 文件引用输入契约）
- [ ] **契约测试**: `skills/dual-round-review/tests/test_check_review_report.py`（新增）、`tests/test_prepare_review_context.py`（扩展）
- [ ] **架构设计书**: `docs/explanation/architecture/dual-round-review-design.md`（新增交付凭据归档章节 + V2.1.0 变更摘要）
- [ ] **治理规程**: `docs/GOVERNANCE.md`（目录拓扑补 `docs/project/reviews/`）
- [ ] **索引与机器地图**: `docs/index.md`（收录 RFC 与本计划）、`docs/llms.txt`（脚本重新生成）

### 1.2 依赖选型与开源调研结论 (Research & Feasibility Spike)

- **P0.5 备忘录**: 豁免（见目标元数据说明）
- **开源复用/自研裁决**: **复用既有封装，零新增依赖** ——
  - 门禁脚本形态（参数解析、退出码 0/1/2、围栏剥离 `strip_fences`、双层区块校验）**逐项对齐** `skills/frontend-qa-gate/scripts/check-qa-report.sh` 的已验证实现；
  - 归档 scaffold 的 heredoc 骨架生成**对齐** `prepare-review-context.sh` 既有锚点生成手法；
  - SHA256 计算使用系统自带 `sha256sum`（回退 `shasum -a 256`），不引入新依赖。
- **API 权威契约与版本验证**: 仅使用 Bash 内建与 `grep`/`awk`/`awk` 状态机，无外部库版本约束。

### 1.3 严禁事项与反模式 (Strict Exclusions)

- 严禁修改未在范围内的公共契约：审查模式语义（Full/Light/Delta）、裁决分级标准、派发预算与 `verdict-rubric.md` 均**不得改动**；
- 严禁改动 `.review-context/` 的 `.gitignore` 忽略状态（RFC §7.2 X4）；
- 严禁在报告落盘失败时宣布审查通过（RFC §3.8）；
- 严禁删除或重写 `prepare-review-context.sh` 的既有锚点行为（必须保持向后兼容，现有 7 项测试须继续全绿）；
- 严禁未跑测试直接提交代码；
- 严禁擅自引入未在技术栈清单中的异构第三方库。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

> 依据 `testing-decision-matrix.md` 规则进行 4 步推理裁定：

### 第 1 步：改动影响面分析 (Blast Radius Analysis)

| 改动对象 | 被引用面 | 影响评定 |
| :--- | :--- | :--- |
| `check-review-report.sh`（新增） | 被 `SKILL.md` 步骤、`goal-loop` 阶段 4 门禁引用 | 骨干节点（交付准入链路）→ **HIGH** |
| `prepare-review-context.sh`（扩展） | 被 `SKILL.md` 步骤 1 引用；已有 7 项契约测试 | 骨干节点 → **HIGH** |
| `SKILL.md`（契约扩展） | 全技能流程的编排入口 | 骨干节点 → **HIGH** |
| `references/*.md`（模板） | 派发提示词的构造依据 | 叶子节点 → LOW |

### 第 2 步：I/O 边界穿透判定 (Boundary Inquiry)

- 门禁脚本执行**真实文件系统读写**（读取归档目录、计算文件哈希、创建归档目录）→ **跨边界** → 必须升级为 **L2 模块集成测试**；
- Python 契约测试以 `subprocess` 拉起真实 Bash 脚本并操作真实临时 Git 仓库（沿用现有 `test_prepare_review_context.py` 的 `tmp_path` 手法）→ 真实进程装配，不可伪称纯内存逻辑。

### 第 3 步：用户链路感知性检查 (User-Facing Check)

- 编排者（`goal-loop` P4）与人类验收者**可直接观测**归档目录的产生与门禁退出码 → 纳入 **L3 端到端验收清单**（真实归档目录冒烟）。

### 第 4 步：《测试策略裁定书》

- **改动风险定级**: **MEDIUM**
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `bash -n` 语法检查全部改动脚本；`shellcheck` 若可用则零告警
  - [x] **L1 单元测试**: `pytest skills/dual-round-review/tests/` —— 门禁脚本的每一项校验规则各配失败/通过用例；归档 scaffold 的新增行为配用例
  - [x] **L2 模块集成测试**: `pytest skills/` 全量套件（验证跨技能无回归）+ 既有 `frontend-qa-gate` 校验器不受影响
  - [x] **L3 端到端测试**: 真实归档目录冒烟 —— 手工 scaffold 一个归档目录、写入最小合规 R1/R2 报告、跑门禁得 0、篡改一份得非 0
  - [x] **L-Doc 文档检查**: `check-doc-links.py`（断链 0）+ `audit-doc-health.py`（健康度 ≥ 80 且无新增孤儿）
- **豁免测试级别与充分依据**: **无豁免**。
- **精确验证命令清单**:
  ```bash
  # L0 静态语法检查
  bash -n skills/dual-round-review/scripts/check-review-report.sh
  bash -n skills/dual-round-review/scripts/prepare-review-context.sh

  # L1 单元测试（技能内）
  python3 -m pytest skills/dual-round-review/tests/ -q

  # L2 集成测试（全技能套件，含跨技能回归）
  python3 -m pytest skills/ -q

  # L3 端到端冒烟（见 Task P3.5.2 的具体脚本）
  #   构造归档目录 -> 跑门禁（期望 0）-> 篡改报告 -> 跑门禁（期望非 0）

  # L-Doc 文档门禁
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
  python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

> 阶段代码与状态机一致（P1 → P2 → P3 → P3.5 → P4 → P5）。复选框由编排者更新，执行子智能体不得代改。

### P3 准备: 隔离分支与环境前置检查
- [x] **Task P3.0**: 创建功能分支并锁定基线
  - **涉及文件**: 无（Git 操作）
  - **执行**: `git switch -c feature/goal-review-report-archive`（基点 `940e0f3`）
  - **验收方式**: `git branch --show-current` 输出 `feature/goal-review-report-archive`；`python3 -m pytest skills/ -q` 基线全绿

### P3: 核心功能原子实现 (TDD 循环)

- [ ] **Task P3.1**: 新增《审查归档》机械门禁 `check-review-report.sh`
  - **涉及文件**: `skills/dual-round-review/scripts/check-review-report.sh`（新增）、`skills/dual-round-review/tests/test_check_review_report.py`（新增）
  - **接口契约**:
    - 用法: `bash check-review-report.sh <归档目录> [--require-verdict=PASS]`
    - 退出码: `0` = 通过；`1` = 结构/证据缺陷；`2` = 用法错误
    - 必需区块常量（**必须与 R1/R2 模板的输出格式逐字一致**）:
      - `R1_SECTIONS`: `## 1. 第一性原理与本质溯源分析` / `## 2. 运行时与 SSR/沙盒安全推演` / `## 3. 红队攻击路径推演` / `## 4. 潜在缺陷清单` / `## 5. 第一轮结论概要`
      - `R2_SECTIONS`: `## 1. 元审查辩证质询` / `## 2. 最终裁决明细表` / `## 3. 终审放行结论`
    - 索引必需字段: `**交付单元**` / `**归档根**` / `**终审裁决**`
  - **校验规则**（对应 RFC §3.5 的 7 项）:
    1. `README.md` 存在且含三个必需字段；
    2. 轮次台账登记的每个报告文件存在且非空；
    3. 台账登记的 SHA256 前 12 位与文件实际值一致（失败时打印期望值与实际值，便于直接修正）；
    4. R1 报告 5 区块齐备且**围栏剥离后仍齐备**（防围栏伪造）；
    5. R2 报告 3 区块齐备（**仅当**台账含 `R2` / `delta-r2` 行）；
    6. 稳定 ID 对齐：R2 §2 表中出现的 `R1-<n>` 必须全部存在于 R1 §4 表；
    7. `--require-verdict=PASS` 时「终审裁决」必须为「准予交付」。
  - **TDD 步骤**: 🔴 先写失败用例（缺索引字段 / 报告缺失 / 指纹不符 / R1 缺区块 / R2 缺区块 / ID 不对齐 / 围栏内伪造 / verdict 不匹配 / 合法归档通过 / 用法错误退出 2）➔ 🟢 最简实现 ➔ 🔵 对齐 `check-qa-report.sh` 的围栏奇偶 fail-closed 与双层校验结构 ➔ ✅ 测试通过 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/dual-round-review/tests/test_check_review_report.py -q`

- [ ] **Task P3.2**: 扩展 `prepare-review-context.sh` 支持归档 scaffold
  - **涉及文件**: `skills/dual-round-review/scripts/prepare-review-context.sh`、`skills/dual-round-review/tests/test_prepare_review_context.py`
  - **新增接口**:
    - `--slug=<交付单元slug>`: 启用归档 scaffold（**不传则行为完全不变**，保持向后兼容）
    - `--archive-root=<路径>`: 归档根，默认 `docs/project/reviews`
  - **行为契约**:
    1. 若 `<archive-root>/*-<slug>` 已存在则**复用**该目录（Delta 再循环跨天不分裂）；否则以**当天日期**创建 `<archive-root>/<YYYY-MM-DD>-<slug>/`；
    2. 目录不存在时生成 `README.md` 骨架（含三个必需字段 + 空的轮次台账表头）；已存在时**不覆盖**；
    3. 锚点文件追加「归档索引」段：`- **归档根**: <相对路径>`；已存在该段时**更新而非重复追加**；
    4. `--help` 增补两个新选项说明；
    5. 归档 scaffold 失败（权限/磁盘）时以非零退出并提示，**不得**静默继续。
  - **TDD 步骤**: 🔴 先写失败用例（传 slug 生成目录与索引 / 复用既有目录而不重复创建 / 缺 slug 时不生成归档目录（向后兼容）/ 锚点归档索引段不重复追加 / --help 含新选项）➔ 🟢 实现 ➔ 🔵 复用既有 `RECORD_BASE` 与 heredoc 手法 ➔ ✅ 全绿（含既有 7 项）➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/dual-round-review/tests/test_prepare_review_context.py -q`

- [ ] **Task P3.3**: `SKILL.md` 落地归档契约
  - **涉及文件**: `skills/dual-round-review/SKILL.md`
  - **改动点**:
    1. **铁律 5** 由「状态落盘」扩展为「状态落盘 + 凭据归档」，明确**报告全文必须逐字落盘**，禁止以摘要替代；
    2. **新增步骤 1.6「交付凭据归档 (Review Evidence Archive)」**：定义三层拓扑（运行时状态 / 交付凭据 / 机械门禁）、归档根推荐默认与宿主优先原则、命名规范、索引 schema、写入责任边界（主智能体逐字转录 + SHA256 指纹）、异常降级表；
    3. **步骤 2 / 步骤 3** 的「落盘审查记录」条目增补「归档报告全文 + 登记指纹 + 跑门禁」动作，并明确**归档完成后方可进入下一步骤**；
    4. **恢复规则** 增补：Delta 再循环除读锚点外，还应从归档 `README.md` 的轮次台账读取上一轮报告路径；
    5. **参考文档导航** 增补门禁脚本条目；
    6. **Rationalizations 表** 增补反模式：「报告摘要已落盘，无需归档全文」。
  - **验收方式**: `grep -n '步骤 1.6\|交付凭据归档\|check-review-report' skills/dual-round-review/SKILL.md` 三项均命中；文档门禁通过

- [ ] **Task P3.4**: 提示词模板适配归档契约
  - **涉及文件**: `skills/dual-round-review/references/round-1-red-team.md`、`skills/dual-round-review/references/round-2-meta-architect.md`
  - **改动点**:
    1. R1 模板：在 `Context & Inputs` 增补「报告将被逐字归档至 `<归档路径>`，请严格按 Output Format 输出，区块标题逐字保留」；
    2. R2 模板：`- **Round 1 Red-Team Review Report**:` 输入项由纯内联槽位改为**双通道**——优先「归档文件路径 + SHA256」要求 R2 读取原文并核验；宿主无读文件能力时降级内联全文并在报告中标注「内联降级」；
    3. R2 模板新增一条元审查维度：「归档完整性核验——R1 报告是否与归档文件一致（指纹校验）」；
    4. 两个模板的 Output Format **区块标题一律不改**（门禁校验项依赖其逐字一致性）。
  - **验收方式**: `grep -n '归档' skills/dual-round-review/references/round-2-meta-architect.md` 命中；R1/R2 的 Output Format 区块标题与门禁脚本常量逐字比对一致

- [ ] **Task P3.5**: 文档与治理联动同步
  - **涉及文件**: `docs/explanation/architecture/dual-round-review-design.md`、`docs/GOVERNANCE.md`、`docs/index.md`、`docs/llms.txt`
  - **改动点**:
    1. 设计书：版本升至 V2.1.0，新增「交付凭据归档」章节（三层拓扑 + 命名规范 + 门禁校验项 + V2.1.0 变更摘要行 + 修订历史行）；
    2. 治理规程：目录拓扑中补 `docs/project/reviews/` 与说明；
    3. 索引：收录 RFC-0001 与本计划（消除孤儿文档）；
    4. `llms.txt`：由 `generate-llms-txt.py` 重新生成。
  - **验收命令**: `check-doc-links.py` 退出 0；`audit-doc-health.py` 孤儿文档数归零且得分 ≥ 99

### P3.5: 集成验证与端到端贯通
- [ ] **Task P3.5.1**: 运行跨技能集成测试与静态门禁
  - **验收命令**: `python3 -m pytest skills/ -q`（全绿） + `bash -n` 全部改动脚本（退出 0）
- [ ] **Task P3.5.2**: L3 端到端冒烟 —— 真实归档目录闭环
  - **执行**: 在临时目录构造合规归档（README 索引 + R1 报告 + R2 报告）➔ 跑门禁期望退出 0 ➔ 篡改 R1 报告一行 ➔ 重跑门禁期望退出非 0 ➔ 恢复后跑 `--require-verdict=PASS` 期望退出 0
  - **验收方式**: 四个退出码符合预期，且门禁失败信息明确指出缺陷位置

### P4: 双轮对抗终审与再循环闭环硬门禁 (Dual-Round Review & Re-Loop Gate)
- [ ] **Task P4.1**: 派发 `dual-round-review` **Full** 模式（R1 红队 ➔ R2 元架构师）
  - **审查输入**: 本功能提交范围 `940e0f3..HEAD` + Diff 边界锁 + 需求源 RFC-0001
  - **验收标准**: 取得独立子智能体给出的终审裁决明细表
- [ ] **Task P4.2**: 阻断项修复与 Delta Re-Loop 再循环闭环（迭代上限 5 次）
  - **触发条件**: Task P4.1 裁定 `Blockers > 0`
  - **执行动作**: 精准根因修复 + 原子提交 ➔ 以修复提交为新基线重派 R1 ➔ 直至阻断项清零或触发上限熔断
- [ ] **Task P4.3**: 阻断项清零终审放行与分支合并
  - **准入标准**: 持有 Zero Blockers 终审凭据

### P5: 文档全向归档与联动升级
- [ ] **Task P5.1**: 对照 `documentation-sync-matrix.md` 复核文档联动残余
- [ ] **Task P5.2**: RFC-0001 状态流转（In Review ➔ Accepted ➔ Implemented），按 RFC §8 结晶去向执行并置防腐声明
- [ ] **Task P5.3**: 本计划状态置 `[已完成]`，登记结项总结与修订历史

---

## 4. 研究发现与环境状态记录 (Context Log)

- **[2026-10-04 00:40] 探查 1（缺口实证）**: `SKILL.md:36` 铁律 5 只要求落盘「每轮结论」；`SKILL.md:91-92` 的锚点 schema 为 8 字段且目录被 `.gitignore:8` 忽略；`.review-context/r1-report-c1252a4.md:3` 自述「全文见会话记录」——坐实报告全文零落盘。
- **[2026-10-04 00:42] 探查 2（社区惯例核实）**: 未检索到「审查报告应放隐藏目录」的社区标准。dotagents 提案 FAQ 原文为 `Agent-specific skills, personas, and reviewed configuration may be committed`（指**配置**且用 `may`）；本仓库 `README.md:44` 定义 `.agents/skills/` 为 `install.py` 生成的安装态视图且被 `.gitignore:14` 忽略——放审计凭据存在语义冲突且不解决持久化。真正有共识的是 ADR 类决策记录进版本库。
- **[2026-10-04 00:50] 探查 3（范式对齐）**: `check-qa-report.sh` 确立的已验证范式——退出码 0/1/2、`FAIL` 累积、围栏奇偶 fail-closed、`strip_fences` awk 状态机双层校验、`--require-verdict=PASS` 锚定章节。本计划的门禁脚本逐项对齐，零新增依赖。
- **[2026-10-04 00:52] 探查 4（门禁基线）**: RFC 落盘后 `check-doc-links.py` 断链 0（18 文件 100% 有效）；`audit-doc-health.py` 得分 99.4/100，唯一扣分项为 RFC-0001 孤儿文档（扣 0.6），由 Task P3.5 的索引收录闭环。

---

## 5. 修订历史 (Revision History)
- **[2026-10-04]**: 计划创建（P0 出口 RFC-0001 已落盘，P0.5 判为豁免）。
