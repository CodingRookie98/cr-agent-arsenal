# dual-round-review 审查报告子智能体直写实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-DUAL-ROUND-REVIEW-DIRECT-WRITE-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-08

> **目标元数据**
> - **所属项目**: cr-agent-arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 执行 RFC-0001 §7.3 A1 预留的替代路径——为 R1/R2 子智能体的 Write-Scope 约束开唯一例外，授权其将报告原文**直写**至主智能体预授权的归档路径，消除主智能体转录环节与自证式指纹残差；无写能力宿主保留转录降级通道并在台账显式登记
> - **创建日期**: 2026-10-08
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-08 10:20（「直接做A」）
> - **批准基线**: 分支 `feature/review-subagent-direct-write`，基点 `771ad29`
> - **状态**: 进行中
> - **隔离分支**: `feature/review-subagent-direct-write`
> - **需求确认文档**: [RFC-0002 子智能体直写契约](../../proposals/RFC-0002-subagent-direct-write.md)
> - **技术调研备忘录**: 豁免（P0.5 未触发——复用既有两个脚本与既有 pytest 契约测试范式，无新第三方依赖；预授权语义的宿主能力边界已在 RFC-0002 §3.7 随方案拷问完成）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`（已被 `.gitignore` 忽略）

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语，不另建并行状态文件；本文件的复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P4 双轮对抗终审（R1 已派发）
- **当前活跃子任务**: 无
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 1/5
- **执行后端**: 宿主原生子智能体（当前会话 DSH `subagent`；P3 编码由主会话内联执行，P4 审查由独立子智能体隔离）
- **最后一次验证状态**: L0 `bash -n` OK；L1 `pytest skills/dual-round-review/tests/` **78 passed**；L2 `pytest skills/` **215 passed**（基线 190）；契约测试变异反证通过（2 处变异各自触发对应用例失败）；V2.1.0 归档迁移后门禁 rc=0 且**四个报告指纹未变**
- **最新有效提交**: `455eccc`
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收口径 (Acceptance Criteria)

- **验收人 (Acceptor)**: 王辉
- **验收场景 (Acceptance Scenarios)**：
  1. 对**本交付自身**跑一次真实双轮审查（dogfooding），R1 与 R2 报告均由**子智能体直写**落盘，文件中**不含**任何主智能体转录痕迹；
  2. 归档索引轮次台账的「写入形态」列登记为 `direct`，且该列在报告由子智能体直写 / 主智能体降级两种情况下取值不同、可区分；
  3. `bash skills/dual-round-review/scripts/check-review-report.sh <归档目录> --require-verdict=PASS` 退出码为 0；
  4. 人为删除台账「写入形态」列（或写入非法取值）后重跑该校验器，退出码非 0（第 8 项校验生效）；
  5. 派发前运行 `prepare-review-context.sh --slug=<slug> --round=r1` 能**直接打印**本轮报告目标路径，且目标文件已存在时给出 Write-Once 告警。
- **明确不验收项 (Non-Acceptance)**: 宿主沙箱级路径强制的实现；外部签名/时间戳工具链；「报告确由子智能体所写」的机械校验（不可验证，RFC-0002 §3.5/X5）；历史交付报告的原文回填；报告体量保留策略（RFC-0002 §2.2）。
- **口径冲突裁决人**: 王辉

### 1.1 核心交付物清单

- [ ] **技能规程**: `skills/dual-round-review/SKILL.md`（铁律 5、步骤 1.6 写入通道与路径预授权、步骤 2/3 派发前预授权与回报后核验、异常降级、反模式表）
- [ ] **提示词模板**: `skills/dual-round-review/references/round-1-red-team.md`、`round-2-meta-architect.md`（Write-Scope 例外条款、`[REPORT_PATH]` 槽位、写盘动作与回报契约）
- [ ] **上下文脚本**: `skills/dual-round-review/scripts/prepare-review-context.sh`（新增 `--round`，输出目标路径与 Write-Once 告警）
- [ ] **机械门禁**: `skills/dual-round-review/scripts/check-review-report.sh`（追加第 8 项「写入形态合法性」）
- [ ] **契约测试**: `skills/dual-round-review/tests/test_prepare_review_context.py`（扩展）、`test_check_review_report.py`（扩展）、`test_write_channel_contract.py`（新增）
- [ ] **核心架构决策**: `docs/explanation/decisions/0002-subagent-direct-write-channel.md`（MADR 3.0）
- [ ] **设计说明**: `docs/explanation/architecture/dual-round-review-design.md`（升至 V2.2.0）
- [ ] **索引联动**: `docs/index.md`、`docs/llms.txt`、`docs/GOVERNANCE.md`（如需）
- [ ] **交付凭据**: 本交付自身的四轮审查报告归档于 `docs/project/reviews/2026-10-08-subagent-direct-write/`

### 1.2 依赖选型与开源调研结论 (Research & Feasibility Spike)

**零新增依赖**（显式裁定）：

| 需求 | 选型 | 理由 |
| :--- | :--- | :--- |
| 文件路径确定 | 复用既有 `prepare-review-context.sh` | 已有 `--slug` scaffold 能力，仅追加 `--round` 输出 |
| 摘要计算 | 系统 `sha256sum`（既有 `sha_of()` 封装） | 门禁已封装跨平台降级（shasum 兜底），零新依赖 |
| 台账解析 | 复用既有 awk 固定列解析 | 追加第 7 列不破坏 `$5`/`$6` 取值 |
| 测试框架 | 既有 pytest + subprocess 范式 | 与两个既有测试文件完全一致 |

### 1.3 严禁事项与反模式 (Strict Exclusions)

1. **严禁**在报告文件中添加任何头部、尾部、来源标注或元数据（RFC-0002 N3 逐字红线）。
2. **严禁**让子智能体自选、推断或改写报告路径（RFC-0002 §3.2）。
3. **严禁**默认转录放行——子智能体未写盘时必须先确认是否能力缺失，确认后方可降级并登记。
4. **严禁**改动 `check-review-report.sh` 既有 7 项校验的判定语义（RFC-0002 N5）。
5. **严禁**在文档中把路径预授权表述为「已隔离」（RFC-0002 §3.7 诚实边界）。
6. **严禁**子智能体覆盖既有报告文件（Write-Once）。
7. **严禁**修改任何无关代码、顺手重构或批量重排格式。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

### 第 1 步：改动影响面分析 (Blast Radius Analysis)

| 待改动文件 | 依赖消费者 | 影响面 |
| :--- | :--- | :--- |
| `SKILL.md` | 所有使用 `dual-round-review` 的交付流程；`goal-loop` 阶段 4 | **HIGH**（公共契约） |
| `references/round-1/2-*.md` | 每次审查派发的提示词构建 | **HIGH**（公共契约） |
| `scripts/check-review-report.sh` | 交付放行门禁；`docs/GOVERNANCE.md` 引用 | **HIGH** |
| `scripts/prepare-review-context.sh` | 审查启动流程 | **MEDIUM** |
| `tests/*` | 仅测试自身 | LOW |

**结论**：判定为**修改公共接口 / 核心领域契约**，对应矩阵强制级 **L0 + L1 + L2 + 全局构建**。

### 第 2 步：I/O 边界穿透判定 (Boundary Inquiry)

本模块**执行真实文件系统写入与子进程调用**（bash 脚本创建目录/写文件、`sha256sum` 子进程）→ **必须 L2 模块集成测试**。防逃逸红线不适用（无 Mock 隔离）。

### 第 3 步：用户链路感知性检查 (User-Facing Check)

**是**。技能使用者（人类 + 编排智能体）直接观测：① 台账新增列；② 提示词模板新增必填槽位；③ 脚本新增参数与输出 → **纳入 L3 验收清单**。

### 第 4 步：《测试策略裁定书》

- **改动风险定级**: **HIGH**
- **强制执行级别**: **L0 静态门禁 + L1 单元/契约测试 + L2 模块集成测试 + L3 端到端 dogfooding + L-Doc 文档门禁**
- **豁免测试级别**: 无豁免
- **豁免充分理由**: 不适用——本次改动触及公共契约（技能提示词契约 + 台账 schema + 放行门禁），矩阵明令「严禁豁免 L2」；L3 由本交付自身的真实双轮审查承担（dogfooding），不可豁免
- **精确验证命令清单**:
  1. **L0**: `bash -n skills/dual-round-review/scripts/*.sh`
  2. **L1**: `python3 -m pytest skills/dual-round-review/tests/ -v`
  3. **L2**: `python3 -m pytest skills/ -v`（全量含 `_shared` 跨技能断链自检）
  4. **L3**: 以 V2.2.0 契约对本交付自身执行真实双轮审查（R1→R2→Delta 闭环），R1/R2 报告由子智能体直写；随后 `bash skills/dual-round-review/scripts/check-review-report.sh docs/project/reviews/2026-10-08-subagent-direct-write/ --require-verdict=PASS` 必须 rc=0
  5. **L-Doc**: `python3 skills/doc-governance/scripts/check-doc-links.py` 断链 0；`python3 skills/doc-governance/scripts/audit-doc-health.py` 健康度不低于交付前基线

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P3 准备: 隔离分支与环境前置检查

- [x] 分支 `feature/review-subagent-direct-write` 已从 `771ad29` 创建
- [x] 基线验证：`python3 -m pytest skills/ -q` → **190 passed**
- [x] 基线记录：`audit-doc-health.py` → PASS（交付前存在 1 篇孤儿文档告警，为新建计划自身，P5 收录）

---

### P3: 核心功能原子实现 (TDD 循环)

#### Task 1: `prepare-review-context.sh` 新增 `--round`，机械化输出本轮报告目标路径

**Files:**
- Modify: `skills/dual-round-review/scripts/prepare-review-context.sh`
- Test: `skills/dual-round-review/tests/test_prepare_review_context.py`

**Interfaces:**
- Consumes: 既有 `resolve_archive_dir()`、`RECORD_BASE`/`RECORD_HEAD` 变量
- Produces: 新参数 `--round=<r1|r2|delta-r1|delta-r2>`；stdout 打印 `📄 本轮报告目标路径 (预授权写入面): <ARCHIVE_DIR>/<round>-<base7>..<head7>.md`；目标已存在时追加 `⚠️ 目标文件已存在（Write-Once 保护）` 告警

- [ ] **Step 1: 写失败测试**（`test_prepare_review_context.py` 追加）

```python
def test_round_prints_report_path(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert r.returncode == 0, r.stderr
    assert '本轮报告目标路径' in r.stdout
    assert 'r1-working..' in r.stdout

def test_round_requires_slug(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo, '--round=r1', '--working')
    assert r.returncode != 0
    assert '--slug' in r.stderr

def test_invalid_round_rejected(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo, '--slug=demo', '--round=r9', '--working')
    assert r.returncode != 0
    assert 'r1' in r.stderr

def test_round_warns_when_target_exists(tmp_path):
    repo = _repo(tmp_path)
    _run(repo, '--slug=demo', '--round=r1', '--working')
    archive_dir = next((repo / 'docs' / 'project' / 'reviews').iterdir())
    (archive_dir / 'r1-working..HEAD.md').write_text('existing\n', encoding='utf-8')
    r = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert r.returncode == 0, r.stderr
    assert 'Write-Once' in r.stdout
```

- [ ] **Step 2: 运行确认失败** — `python3 -m pytest skills/dual-round-review/tests/test_prepare_review_context.py -k round -v` → FAIL（未知选项）
- [ ] **Step 3: 实现** — 参数解析追加 `--round=*) ROUND="${arg#--round=}" ;;`；在 §2.1 后追加校验块（`--round` 必须与 `--slug` 同用；取值白名单 `r1|r2|delta-r1|delta-r2`）；在 scaffold 块内追加目标路径打印与存在性告警；`usage()` 补文档
- [ ] **Step 4: 运行确认通过** — 同 Step 2 命令 → PASS
- [ ] **Step 5: 提交** — `git add` 两文件，`git commit -m "feat(dual-round-review): prepare-review-context 新增 --round 输出预授权报告路径"`

#### Task 2: `check-review-report.sh` 追加第 8 项「写入形态合法性」校验

**Files:**
- Modify: `skills/dual-round-review/scripts/check-review-report.sh`
- Test: `skills/dual-round-review/tests/test_check_review_report.py`

**Interfaces:**
- Consumes: 台账第 7 列（写入形态）
- Produces: 校验项 8——每行「写入形态」必须存在且 ∈ `{direct, transcribed}`；否则 `FAIL=1` 并被 rc=1 反映

- [ ] **Step 1: 写失败测试**：`test_missing_write_mode_fails`（台账 6 列 → rc!=0，stderr 含「写入形态」）、`test_invalid_write_mode_fails`（值写 `auto` → rc!=0）、`test_direct_write_mode_passes`（7 列 `direct` → rc==0）、`test_transcribed_write_mode_passes`（`transcribed` → rc==0）。**同步改造既有 fixture**：`INDEX_TMPL` 台账表头追加 `| 写入形态 |`，`_write_index` 行默认补 `direct`
- [ ] **Step 2: 运行确认失败** — `pytest ... -k write_mode -v` → FAIL
- [ ] **Step 3: 实现** — 台账 awk 追加 `m=$7` 提取与 trim，输出第 4 字段；行循环内追加取值校验（空 → 缺登记；非白名单 → 非法）；usage 补第 8 项说明
- [ ] **Step 4: 运行确认通过** — 全量 `pytest skills/dual-round-review/tests/ -v` → PASS（含既有 24 项不回归）
- [ ] **Step 5: 提交**

#### Task 3: `SKILL.md` 契约更新（铁律 5 / 步骤 1.6 / 步骤 2 / 步骤 3 / 反模式表）

**Files:**
- Modify: `skills/dual-round-review/SKILL.md`
- Test: `skills/dual-round-review/tests/test_write_channel_contract.py`（Task 6 建）

**Interfaces:**
- Consumes: Task 1 的 `--round` 输出格式；Task 2 的写入形态取值
- Produces: 主智能体的派发前预授权与回报后核验动作规程

- [ ] **Step 1: 改铁律 5** — 「双层落盘」扩为三通道描述（状态锚点 + 直写凭据 + 转录降级）
- [ ] **Step 2: 重写步骤 1.6「写入责任边界」** → 「写入通道与路径预授权」：直写为默认通道、转录降级为显式通道、路径预授权五条、诚实边界声明（非隔离）
- [ ] **Step 3: 改异常降级表** — 追加第 4/5 条（子智能体不可写 → 转录降级 + 登记；指纹不一致 → 收口，不得登记）
- [ ] **Step 4: 重写步骤 2/3 的「落盘审查记录与报告归档」** → 「派发前预授权 + 收到回报后核验与登记」（含 `--round` 调用与独立复算）
- [ ] **Step 5: 反模式表追加两行** — 「子智能体说写成功了，我直接登记」（未复算即登记）、「报告没落盘，我替他写一份登记 direct」（虚假登记）
- [ ] **Step 6: 参考导航补门禁第 8 项说明**
- [ ] **Step 7: 提交**

#### Task 4: R1 模板改造（Write-Scope 例外 + 路径槽位 + 写盘动作）

**Files:**
- Modify: `skills/dual-round-review/references/round-1-red-team.md`

- [ ] **Step 1: 替换 Read-Only 行** → `Write-scope constraint` 单路径例外条款（英文，含 `<REPORT_PATH>` 占位）
- [ ] **Step 2: Context & Inputs 追加** `**报告目标路径 (Pre-authorized Report Path)`: [REPORT_PATH]` 槽位及三条从属约束（不建目录 / 不覆盖 / 不自选路径）
- [ ] **Step 3: Output Format 之后追加**「写盘动作 (Mandatory Write-Back)」章节：逐字写入 + `REPORT_PATH/REPORT_BYTES/REPORT_SHA256` 回报契约 + 失败时附全文回退
- [ ] **Step 4: 自检** — 五区块标题**逐字未变**（`test_template_headings_match_checker_constants` 必须继续通过）
- [ ] **Step 5: 提交**

#### Task 5: R2 模板改造（同构 + 归档保真核验增强）

**Files:**
- Modify: `skills/dual-round-review/references/round-2-meta-architect.md`

- [ ] **Step 1: 同 Task 4 步骤 1–3**（R2 版本措辞）
- [ ] **Step 2: §6「归档与转录保真核验」维度** 追加：核验 R1 报告的产出通道（`direct` / `transcribed`），`transcribed` 时降低采信度并在裁决书标注
- [ ] **Step 3: 自检** — 三区块标题逐字未变
- [ ] **Step 4: 提交**

#### Task 6: 新增 `test_write_channel_contract.py` 契约测试

**Files:**
- Create: `skills/dual-round-review/tests/test_write_channel_contract.py`

- [ ] **Step 1: 写断言**
  - 两模板均含 `Write-scope constraint`、`[REPORT_PATH]`、`REPORT_SHA256`
  - 两模板均**不再**含旧串 `Read-Only constraint: You must not modify the working tree, branch, or index.`
  - `SKILL.md` 含「直写通道」「转录降级」「写入形态」「路径预授权」「--round」
  - `SKILL.md` 含诚实边界表述（「提示词契约」且不含「已隔离」断言句）
  - `check-review-report.sh` 常量含 `direct` 与 `transcribed`
- [ ] **Step 2: 先跑确认**（实现未到位时红，到位后绿）— `pytest .../test_write_channel_contract.py -v`
- [ ] **Step 3: 提交**

---

### P3.5: 集成验证与端到端贯通

- [ ] **L0**: `bash -n skills/dual-round-review/scripts/*.sh` → 全部 exit 0
- [ ] **L1**: `python3 -m pytest skills/dual-round-review/tests/ -v` → 全绿
- [ ] **L2**: `python3 -m pytest skills/ -q` → 全绿（含 `_shared` 跨技能断链自检）
- [ ] **负向验证**：手工构造缺列/非法列台账 → `check-review-report.sh` rc!=0
- [ ] **Write-Once 验证**：目标文件已存在时 `--round` 输出告警且脚本 rc=0
- [ ] **落盘检查点**：更新本文件 Active Checkpoint

### P4: 双轮对抗终审与再循环闭环硬门禁 (Dual-Round Review & Re-Loop Gate)

- [ ] 以 `771ad29..<HEAD>` 为基线，按 `dual-round-review` **V2.2.0 新契约**执行 Full 模式：
  - R1 红队（独立子智能体，**直写**报告至预授权路径，台账登记 `direct`）
  - R2 元审判（独立子智能体，**直写**报告，通道 A 读归档文件 + 指纹核验）
  - 阻断项 > 0 → Delta 再循环直至 Zero Blockers
- [ ] 归档门禁：`check-review-report.sh docs/project/reviews/2026-10-08-subagent-direct-write/ --require-verdict=PASS` rc=0
- [ ] **dogfooding 双重要求**：① 本交付的审查结论为零阻断项；② 审查过程本身**跑通**了 V2.2.0 直写契约（否则本次改造未被真实验证）

### P5: 文档全向归档与联动升级

- [ ] `docs/explanation/decisions/0002-subagent-direct-write-channel.md`（MADR 3.0）
- [ ] `docs/explanation/architecture/dual-round-review-design.md` → V2.2.0
- [ ] RFC-0002 状态流转 In Review → Implemented + Archival Notice
- [ ] `docs/index.md` 版本升级 + 修订历史行
- [ ] `docs/llms.txt` 重生成或同步
- [ ] `docs/GOVERNANCE.md` 评估（豁免语义是否需改）
- [ ] L-Doc：断链 0、健康度不低于基线
- [ ] 合并至 master

---

## 4. 研究发现与环境状态记录 (Context Log)

| 时间 | 发现 | 影响 |
| :--- | :--- | :--- |
| 2026-10-08 10:20 | 侦察确认 RFC-0001 §3.7 自认指纹为自证式校验；§7.3 A1 已预留本次替代路径与成本估算 | 本提案为「执行既有预留路径」而非新立项 |
| 2026-10-08 10:20 | `check-review-report.sh` 台账解析固定取 `$5`/`$6` | 追加第 7 列对既有 7 项校验零影响 |
| 2026-10-08 10:20 | DSH `subagent` 工具无权限参数；子智能体继承父会话沙箱快照、approval 固定 `'never'` | 路径预授权在 DSH 上是提示词约束；RFC-0002 §3.7 据此写入诚实边界，禁止表述为「已隔离」 |
| 2026-10-08 10:20 | `.agents/skills/dual-round-review` 与源码 `skills/dual-round-review` 内容一致（符号链接安装） | 改源码即改生效副本，无需同步两份 |

---

## 5. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 修订描述 |
| :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-08 | DSH AI Agent | 初始计划：6 个原子任务 + 测试策略裁定书（L0–L3 + L-Doc 全量强制）+ dogfooding 双重要求 |
