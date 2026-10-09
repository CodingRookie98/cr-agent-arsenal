# doc-governance 目录级索引约定与 scaffold 索引自愈实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-DOCGOV-QUADRANT-INDEX-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-09

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 把"目录即入口"的既有门禁事实提升为成文规范，并让 `scaffold-doc.sh` 在生成文档时自动 ensure 象限索引 + 幂等登记，根治 tutorial 模板硬编码断链
> - **创建日期**: 2026-10-09
> - **计划负责人**: DSH AI Agent（主调度）
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-09 11:00
> - **批准基线**: `master @ 95863c9`（分支切出点 `feature/quadrant-index-convention`）
> - **状态**: 进行中
> - **隔离分支**: `feature/quadrant-index-convention`
> - **技术调研备忘录**: [豁免: Heavy Track 内部一致性修复，无第三方选型；依据为仓库内脚本源码实测]
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md` (已被 `.gitignore` 忽略)

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语（`goal-90920f8b-46ed-44e6-9067-c25efa8f054d`），本文件的复选框与检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P4 双轮对抗终审
- **当前活跃子任务**: Task P4.2（第 2 次 Delta 循环：Delta R2 维持 DR1-1 阻断 → 已二次修复（DR1-1/DR1-2/DR1-4/DR1-9）并提交 `45b61ad`；待第三轮 Delta 复验）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: ✅ 全绿（pytest **57 passed**；`python3 -W error::SyntaxWarning` 编译 rc=0；生成物字节检查 **0 反斜杠残留、stderr 0 SyntaxWarning**；L3 端到端 6 托管索引 rc=0；本仓库 docs 三件套 rc=0，**health 100.0/100 且孤儿 0/46**，满足 G5「不下降」相对不变式）
- **最新有效提交**: `45b61ad`（共 5 个原子提交：`bc8c1c5` RFC+计划 / `2583210` 实现+规范 / `7124561` 首轮 Delta 修复 / `458b4d2` P5.1+归档 / `45b61ad` 二次 Delta 修复）
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收口径 (Acceptance Criteria — 由需求方定义)

- **验收人 (Acceptor)**: 王辉
- **验收场景 (Acceptance Scenarios)**：
  - **AS-1 断链根治**：在隔离空目录执行 `scaffold-doc.sh tutorial demo --root <tmp>`，随后 `check-doc-links.py --root <tmp>` 返回 **Exit Code 0**（当前实测为 1，即本交付的核心可观察行为）；
  - **AS-2 索引自愈**：执行 `scaffold-doc.sh how-to demo --root <tmp>` 后，`<tmp>/how-to/index.md` 存在、含标准控制头与 `## 文档清单` 段、且清单内含 `demo.md` 链接；`check-doc-control-sync.py --root <tmp>` 返回 **Exit Code 0**；
  - **AS-3 幂等**：重复执行同一 scaffold / register，清单无重复行、托管索引版本不重复升级；
  - **AS-4 人工索引零改写**：当象限索引不含托管标记时，执行 scaffold 后该文件**逐字节不变**，且脚本给出跳过提示；
  - **AS-5 零回归**：本仓库 `docs/` 三件套门禁保持 rc=0 / 健康度 PASS，且**未新增**任何追溯补齐的索引文件。
- **明确不验收项 (Non-Acceptance)**：
  - 不为现存目录追溯补齐 `index.md`（N1）；
  - 不要求 `llms.txt` 收录托管索引（由 `generate-llms-txt.py` 既有拓扑决定）；
  - 不要求 `scaffold-doc.sh` 自动登记到根索引 `docs/index.md`（N3）。
- **口径冲突裁决人**: 王辉

### 1.1 核心交付物清单
- [ ] 新增脚本: `skills/doc-governance/scripts/manage-doc-index.py`（`ensure` / `register`，镜像硬链接至 `.agents/skills/`）
- [ ] 脚手架改造: `skills/doc-governance/scripts/scaffold-doc.sh`（六分支 register + tutorial 链接降级）
- [ ] 规范补登记: `skills/doc-governance/SKILL.md`（拓扑 + 目录级索引约定节）、`skills/doc-governance/references/change-impact-matrix.md`
- [ ] 治理与设计同步: `docs/GOVERNANCE.md`、`docs/explanation/architecture/doc-governance-design.md`
- [x] 自动化测试: `skills/doc-governance/tests/test_doc_index_convention.py`（AS-1~AS-5 验收用例 + Delta 回归 8 例；R1-13 勘误：本交付新增独立测试文件，非 `test_doc_governance_scripts.py`）
- [ ] 索引与机器地图: `docs/index.md` 版本联动、`docs/llms.txt` 重生成
- [ ] 需求确认与审查: `docs/proposals/RFC-0003-quadrant-index-convention.md`、`docs/project/reviews/2026-10-09-quadrant-index-convention/`

### 1.2 依赖选型与开源调研结论 (Research & Feasibility Spike)
- **P0.5 备忘录**: 豁免（无第三方选型；结论全部来自仓库内脚本源码实测，见 `.goal-loop/scratchpad.md`）
- **开源复用/自研裁决**: 复用既有封装——与 `manage-backlog.py sync-index` 同构，零新增依赖（纯标准库 `argparse` / `pathlib` / `re`）
- **API 权威契约与版本验证**: `check-doc-links.py:173-177`（目录入口判定）、`check-doc-control-sync.py:152-162`（控制头/修订表一致性）、`audit-doc-health.py:471`（元数据基线率计分）

### 1.3 严禁事项与反模式 (Strict Exclusions)
- 严禁修改 `check-doc-links.py` / `audit-doc-health.py` / `check-doc-control-sync.py` 的判定语义与阈值；
- 严禁改写任何不含 `<!-- doc-index:managed -->` 标记的既有索引（含 `docs/index.md`、`docs/project/backlog/index.md`）；
- 严禁为通过测试而弱化断言（断言必须覆盖 AS-1~AS-4 的可观察行为）；
- 严禁在 `master` 直接提交（隔离分支 `feature/quadrant-index-convention`）；
- 严禁引入新依赖或新 CLI 开关（N4）。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

### 第 1 步：改动影响面分析 (Blast Radius Analysis)
- `manage-doc-index.py` 为新增叶子脚本，仅被 `scaffold-doc.sh` 与测试引用 → 影响面 LOW；
- `scaffold-doc.sh` 是技能公开 CLI（SKILL.md 模式 3 明文引用），被使用者与智能体直接调用 → **骨干节点，影响面 HIGH**；
- `SKILL.md` / 设计书 / GOVERNANCE.md 为规范层公共契约，被全库引用 → 影响面 HIGH。

### 第 2 步：I/O 边界穿透判定 (Boundary Inquiry)
- **是**：脚本真实读写文件系统、拉起 python 子进程。按矩阵"构建脚本/配置变更"行 → **强制 L2**，且必须保留真实装配（真实调用既有门禁脚本验证产物），不得以"内部函数已单测"豁免。

### 第 3 步：用户链路感知性检查 (User-Facing Check)
- **是**：CLI 操作者（工程师/智能体）直接观测 scaffold 输出与生成物结构变化 → 纳入 **L3** 端到端链路（全类型批量生成 + 全门禁复核）。

### 第 4 步：《测试策略裁定书》

- **改动风险定级**: **MEDIUM**（脚本公共契约 + 文件系统 I/O；无网络、无并发、无数据迁移）
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `bash -n` 语法校验、`python3 -m py_compile` 字节码校验
  - [x] **L1 单元测试**: `manage-doc-index.py` ensure/register 的函数级与 CLI 级断言（含幂等、人工索引只读、降级分支）
  - [x] **L2 模块集成测试**: scaffold 产物 → 既有门禁脚本真实装配复核（`check-doc-links.py` / `check-doc-control-sync.py`）
  - [x] **L3 端到端测试**: 隔离根目录全类型批量生成 → 三件套门禁 + 幂等重跑 + 人工索引零改写复算
  - [x] **L-Doc 文档一致性**: 本仓库 `docs/` 与技能目录链接审计、`audit-doc-health.py` 得分不下降
- **豁免测试级别与充分依据**:
  - 豁免"全局构建"（本项目为文档与脚本资产，无编译产物；等价物为 L0 语法门禁 + 全量 pytest）；
  - 豁免 L4 级并发/压力测试。理由：单进程 CLI 顺序调用（DA-2），无并发契约。
- **精确验证命令清单**:
  ```bash
  # L0 静态语法门禁
  bash -n skills/doc-governance/scripts/scaffold-doc.sh
  python3 -m py_compile skills/doc-governance/scripts/manage-doc-index.py

  # L1 + L2 + L3 单元与集成（技能全量测试套件，含新增闭环断言）
  python3 -m pytest skills/doc-governance/tests/ -q

  # L3 端到端：隔离根目录全类型链路（集成验证阶段执行）
  #   见 Task P3.5.1 的一次性脚本（临时目录内完成后清理）

  # L-Doc 文档三件套（本仓库真实 docs/）
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
  python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

> 阶段代码与状态机一致（P1 → P2 → P3 → P3.5 → P4 → P5），不使用第二套编号。

### P3 准备: 隔离分支与环境前置检查
- [x] **Task P3.0**: 创建功能分支、校验测试框架与构建脚本就绪，锁定 Diff 范围与基线
  - **涉及文件**: 无（分支 `feature/quadrant-index-convention` @ `95863c9`）
  - **验收方式**: `python3 -m pytest skills/doc-governance/tests/ -q` Exit Code 0（已取证：26 passed）

### P3: 核心功能原子实现 (TDD 循环)
- [x] **Task P3.1**: 新增 `manage-doc-index.py`（`ensure` / `register` + 托管标记 + 版本联动）
  - **涉及文件**: `skills/doc-governance/scripts/manage-doc-index.py`, `skills/doc-governance/tests/test_doc_index_convention.py`
  - **TDD 步骤**: 🔴 失败单测（ensure 创建骨架 / register 幂等 / 人工索引只读）➔ 🟢 最简实现 ➔ 🔵 重构 ➔ ✅ 单元测试通过 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/doc-governance/tests/ -q -k ManageDocIndex`
- [x] **Task P3.2**: `scaffold-doc.sh` 集成自愈（六分支 register + tutorial 条件渲染）
  - **涉及文件**: `skills/doc-governance/scripts/scaffold-doc.sh`, `skills/doc-governance/tests/test_doc_index_convention.py`
  - **TDD 步骤**: 🔴 失败集成测试（AS-1 断链闭环 / AS-2 索引自愈 / AS-4 降级双分支）➔ 🟢 集成调用与条件渲染 ➔ 🔵 重构 ➔ ✅ 测试通过 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/doc-governance/tests/ -q -k ScaffoldDocSh`
- [x] **Task P3.3**: 补规范——SKILL.md 拓扑与"目录级索引约定"节 + 变更联动矩阵
  - **涉及文件**: `skills/doc-governance/SKILL.md`, `skills/doc-governance/references/change-impact-matrix.md`
  - **TDD 步骤**: 🔴 规范断言测试（SKILL.md 含托管标记契约与象限索引约定关键字）➔ 🟢 补写规范 ➔ 🔵 校对术语一致性 ➔ ✅ 测试通过 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/doc-governance/tests/ -q -k SkillSpec`
- [x] **Task P3.4**: 设计书与治理规程同步（版本联动 + 拓扑一致）
  - **涉及文件**: `docs/explanation/architecture/doc-governance-design.md`, `docs/GOVERNANCE.md`
  - **TDD 步骤**: 🔴 一致性测试（三处拓扑对象限索引的表述同构）➔ 🟢 同步补写 + 升版本 + 修订行 ➔ ✅ 三件套门禁通过 ➔ 💾 原子提交
  - **验收命令**: `python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs`

### P3.5: 集成验证与端到端贯通
- [x] **Task P3.5.1**: 隔离根目录全类型端到端链路（生成 ➔ 门禁 ➔ 幂等重跑 ➔ 人工索引零改写复算）
  - **验收命令**: 一次性脚本（`mktemp -d` 隔离 + `cmp` 校验人工索引逐字节不变 + 三件套 rc=0）
- [x] **Task P3.5.2**: 本仓库真实 `docs/` 与技能目录 L-Doc 复核
  - **验收命令**: `check-doc-links.py --root docs`、`check-doc-control-sync.py --root docs`、`audit-doc-health.py --root docs` 全部 rc=0 且健康分不下降

### P4: 双轮对抗终审与再循环闭环硬门禁 (Dual-Round Review & Re-Loop Gate)
- [ ] **Task P4.0 (条件 · 仅前端产物交付)**: 不适用（无前端产物）
- [ ] **Task P4.1**: 派发 R1 红队穿透 + R2 元架构师审判（Heavy Track 全量双轮）
  - **审查输入**: `95863c9..HEAD` + Diff 边界锁 + 技能公共契约变更面
  - **验收标准**: 独立子智能体终审裁决明细表（Zero Blockers 方可放行）
- [ ] **Task P4.2**: 阻断项修复与 Delta Re-Loop（迭代上限 5 次）
- [ ] **Task P4.3**: 阻断项清零终审放行与合并

### P5: 文档全向归档与联动升级
- [ ] **Task P5.1**: 索引联动——`docs/index.md` 版本升级与收录、`docs/llms.txt` 重生成、`skills-lock.json` 哈希自洽
- [ ] **Task P5.2**: RFC-0003 流转 `Implemented` + 防腐声明 + 本计划状态置 `[已完成]`
- [ ] **Task P5.3**: 按 `documentation-sync-matrix.md` 复核技能契约与 backlog 登记（如需）

---

## 4. 研究发现与环境状态记录 (Context Log)

- **[2026-10-09 11:02] 探查记录 1（基线）**：本仓库 `docs/` 三件套门禁全绿（41 md / 0 断链；26 md / 0 版本漂移；health PASS），pytest 26 passed。缺陷复现：仅含 tutorial 模板产物的临时根目录执行 `check-doc-links.py` 得 rc=1（404 → `how-to/index.md`）。
- **[2026-10-09 11:03] 探查记录 2（契约）**：`check-doc-links.py:173-177` 与 `audit-doc-health.py:447-451` 已支持多层级 `index.md`/`README.md`；`check-doc-control-sync.py:152-162` 对"无控制头且无修订表"文档跳过，对"有修订表无控制头"报错 → 托管索引必须携带控制头并保持版本联动。
- **[2026-10-09 11:18] 探查记录 5（R1 等待期只读自我加固）**：新增脚本存在两处**输入契约缺口**（仅直接调用 CLI 时可触发，scaffold 内部路径不受影响）——SH-1 `--file` 未校验 basename（传 `sub/x.md` 会登记出指向不存在路径的清单行）；SH-2 `--dir` 未拒绝 `..`（`../escape` 会在 root 之外创建目录并写索引）。另有 SH-3 标题未转义（含 `]`/`|` 时破坏链接语法，scaffold 传 kebab 文件名故正常路径不触发）。正向结论：空文件/非 UTF-8 索引安全 no-op、前缀相似名幂等无误判、`--root` 绝对路径与尾斜杠均正常。**处置待 R1/R2 裁决**（若坐实为本次引入的契约缺陷则并入同一轮精准修复）。另核查：`skills-lock.json` 的 `computedHash` 与基线提交 `95863c9` 的 SKILL.md 字节 sha256 不一致（且仓库内无校验实现）→ 拟不擅自改写，登记为已知边界交 R2 裁决。
- **[2026-10-09 11:12] 探查记录 4（实现与验证）**：新增 `manage-doc-index.py`（196 行）与验收测试 `test_doc_index_convention.py`（R1-13 勘误：实测 18 个用例，非 17）；`scaffold-doc.sh` 六分支接入自愈、tutorial 条件渲染。L3 端到端：6 个托管索引自动生成、幂等复跑零重复登记、人工索引 sha256 逐字节不变。**发现既有脆弱点**：设计书 §4.1 的「修订历史格式示例」被 `check-doc-control-sync.py` 当作真实修订记录解析，控制头升版必须同步该示例行（本次按既有惯例同步为 V1.3.0）→ 候选 Suggestion，待 P4 裁决。
- **[2026-10-09 11:04] 探查记录 3（环境）**：`skills/doc-governance/*` 与 `.agents/skills/doc-governance/*` 为**硬链接同 inode**（抽样 4 例一致），写入需复核两份视图一致；`skills-lock.json` 记录 `computedHash`，但仓库内 `tools/skills-manager/skills_manager.py` 无校验实现。

---

## 5. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 计划创建：P-1/P0 裁定采用方案 A（补规范 + 脚本自愈 + 链接降级），锁定验收场景 AS-1~AS-5 与测试裁定 L0+L1+L2+L3 |
