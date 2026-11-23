# spec-evolution 机械化演进回路技能实现计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-SPEC-EVOLUTION-2026
> - **当前版本**: V1.8.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-12

> **目标元数据**
> - **所属项目**: cr-agent-arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 新建 `spec-evolution` 技能——把技能与根提示词演进回路的「选择端」从**模型的意见**换成**脚本的退出码**。纯标准库事实采集器（`collect-facts.py`）→ 确定性判定器（`judge.py`，零 LLM / 零网络）→ Exit 0/1/2；判据表 C-01~C-10 覆盖交付面完整性、frontmatter 上限、文件规模、注册面漂移与根提示词净增长；v1 结构性地不做无客观信号的设计质量评价
> - **创建日期**: 2026-10-12
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-12（「准予 Accepted，进入 P1」）
> - **批准基线**: `master` @ `0306f37`（RFC-0004 受理流转提交）
> - **状态**: 已交付（Task 1~7 全部完成，P3.5 双轮对抗取得 ✅ 准予交付；已快进合入 `master` 并推送 `origin/master`）
> - **隔离分支**: `feature/spec-evolution`（P3 起用，基点 `0306f37`）
> - **需求确认文档**: [RFC-0004 spec-evolution 演进回路](../../proposals/RFC-0004-spec-evolution.md)（状态 **Accepted** · V0.3.0 · 已定案）
> - **技术调研备忘录**: 豁免（P0.5 未触发——`N-4` 明令零第三方依赖、纯 `python3` 标准库 + 既有 `pytest` 约定，无选型空间；宿主能力边界已在 RFC-0004 §3 随方案拷问完成）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`（已被 `.gitignore` 忽略）

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语（或经 `goal-state-tracker.sh` 写入本文件检查点），不另建并行状态文件；本文件的复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: **DONE / P5 已交付**（P3.5 裁决 ✅ 准予交付，Blockers = 0；`feature/spec-evolution` 已快进合入 `master`：`63de31b..5992a7a`，并推送 `origin/master`：`206d14b..5992a7a`。D-9 的分支/合入口径冲突已由用户裁定解决）
- **当前活跃子任务**: **交付完成**（P4 归档收口 + P5 交付收口均已落盘；非阻断残余 `BK-0040` 按用户裁定留待下一轮）
- **当前子任务重试计数**: 0/3（全流程收敛，无未决重入）
- **外层循环迭代**: 3/5（末轮，已收敛）
- **最后一次验证状态**: P5 交付终局实测（`5992a7a`）——`pytest skills/ -q` → **380 passed**；`check-doc-links.py --root docs` → **断链 0**；`audit-doc-health.py` → **PASS**；归档门禁 `check-review-report.sh` → **索引齐备 · 报告 5 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐**；§5 十二条验收判据全部实测通过（见 §5 表「实测」列）
- **最新有效提交**: `2100973`（本轮**最后一次行为变更**提交）。其后的提交均为**审查归档与文档收口**：`7bb09c5` / `186f648` / `037eca3` / `2100136` / `74ca674` / `5992a7a`。交付合并点 = `5992a7a`，`master` 与 `origin/master` 均已同步至此
- **阻断原因**: 无

---

## 1. 目标与文件结构 (Goal & File Structure)

### 1.1 本计划要构建什么

把 RFC-0004 已受理的契约落成可运行的技能：一条**只读、可回归、零谄媚面**的审计回路，用退出码回答「仓库的技能与根提示词是否存在机械可证的交付面缺陷」。

**不构建**（RFC §2.2 非目标红线）：不做设计质量评价、不自动修改任何文件、不往 `contexts/AGENTS.md` 加条款、不引入第三方依赖、不新增 CI、不改动既有三门禁的判定语义。

### 1.2 文件结构（分解决策，先于任务拆定）

```
skills/spec-evolution/
├── SKILL.md                              ← 路由层：触发条件、不变式、CLI 契约、挂载点
├── references/
│   ├── checks-spec.md                    ← 判据表 C-01~C-10 与严重度语义（单一真相源）
│   ├── anchor-contract.md                ← 锚点三种形式与存在性校验规则
│   └── baseline.json                     ← 根提示词基线常量（DA-3）
├── templates/
│   └── evolution-report.md               ← 报告模板（含空的「人类裁决」区）
├── scripts/
│   ├── collect-facts.py                  ← 采集器（只读）→ facts.json
│   └── judge.py                          ← 判定器（确定性）→ findings.json + report.md
└── tests/
    ├── conftest.py                       ← 合成仓库夹具与运行辅助（非测试文件）
    ├── test_collect_facts.py             ← 采集器契约测试
    ├── test_judge_contract.py            ← 判据 C-01~C-10 与 CLI 契约测试
    └── test_gate_invariants.py           ← 门禁不变式 GI-1~GI-6

docs/explanation/architecture/spec-evolution-design.md   ← 架构设计书（C-02 要求）
```

**改动的存量文件**（各自一处编辑，互不重叠）：

| 文件 | 改动 |
| :--- | :--- |
| `skills/_shared/tests/test_cross_skill_links.py` | `SKILL_NAMES` 追加 `spec-evolution` |
| `tools/skills-manager/collections/cr-agent-arsenal.json` | `names` 追加 `spec-evolution` **与** `clarification-protocol`（**F-9**） |
| `docs/index.md` | §3 技能表追加一行；§2 架构表追加一行；§4 计划表追加一行 |
| `README.md` | 技能清单表追加一行；目录树追加一行；设计书索引追加一行 |
| `docs/llms.txt` | **重跑生成器**（派生文件，不手改） |
| `skills/goal-loop/SKILL.md` | P5 节追加增量挂载点（不触碰 `contexts/AGENTS.md`） |

> **`docs/llms.txt` 的定位澄清**：`DK-13` 把 `docs/llms.txt` 从 **C-07 判据的注册面**中剔除（`generate-llms-txt.py` 的扫描根是 `docs/`，结构上不可能收录 `skills/`）。但这不等同于「本次交付不需要重跑它」——新增架构设计书落在 `docs/explanation/architecture/`，**会被生成器收录**，所以交付时仍须重跑生成器并提交其产物。二者不矛盾：**C-07 管「技能是否登记」，重跑生成器管「派生文件是否最新」。**

### 1.3 数据流

```
collect-facts.py --out facts.json          judge.py --facts facts.json --report report.md
        │                                          │
        ├─ S1 门禁事实 (4 条既有命令退出码)          ├─ C-09 先判 BLOCKER
        ├─ S2 结构事实 (文件系统遍历 + 正则)         ├─ C-01~C-08 / C-10 逐条映射
        └─ S3 注册事实 (4 个注册面)                 ├─ 锚点存在性校验（失败 → exit 2）
                                                    └─ findings.json + report.md；exit 0/1
```

---

## 2. 全局约束 (Global Constraints)

以下约束隐含存在于**每一个**任务中，不再逐任务重述：

1. **零第三方依赖**：仅 `python3` 标准库（`argparse` / `json` / `re` / `subprocess` / `pathlib` / `datetime` / `sys`）。**禁止** `pip install`、禁止 `pyproject.toml` / `requirements.txt` / `pytest.ini` / `package.json`。
2. **零 LLM、零网络**：`collect-facts.py` 与 `judge.py` **不得** import 任何网络或模型 SDK（`urllib` / `requests` / `httpx` / `socket` / `http` / `openai` / `anthropic` 一律禁止）。GI-1 由测试断言。
3. **只读**：两个脚本除 `--out` / `--json` / `--report` 显式指定的路径外，**不得**创建、修改或删除仓库内任何文件；不得创建目录。GI-6 由测试断言。
4. **确定性**：`judge.py` 对同一份 `facts.json` 必须产出**逐字节相同**的 `findings.json`（不得含时间戳、`set` 迭代序、随机值）。GI-2 由测试断言。
5. **退出码语义**：`0` = 无 **BLOCKER/HIGH**（可含 MID advisory）；`1` = 存在 **BLOCKER/HIGH**；`2` = 用法或输入错误。**无第四种取值。**（依据：Python `argparse` 的 `parser.error()` 即 `sys.exit(2)` 的既有惯例，叠加本仓库 `manage-doc-index.py` 文档化的 0/1 二值语义。**说明**：RFC-0004 `DK-4` 称此语义「与 `taste-driven-designer` 既有脚本一致」，但该技能 `scripts/` 下**仅有一个 `generate-seed.sh`**，无 `.py` 脚本可援引——本计划改以 `argparse` 惯例与仓库 0/1 语义为据，DK-4 的引用出处属误记，P4 回写修正。**2026-10-12 P3.5 修正**：原文写「无 finding」，与 `judge.py` 的 `MID→0` 实现不一致，经交付审查 R1-2 指出后按实现口径收敛。）
6. **文件规模**：任一文件 ≤ **1000** 行（`contexts/AGENTS.md` §3 硬约束，C-06 判据）。
7. **`SKILL.md` frontmatter**：必须是**合法 YAML** 且**不得**出现 `": "`（冒号+空格）序列；`description` ≤ **500** 字符（C-04 建议值，本技能须自身达标）。
8. **跨技能相对链接禁令**：技能文档中**禁止**出现指向其它技能的相对路径（独立分发会断链，C-08）。技能内部相对链接必须可达。
9. **围栏成对闭合**：技能文档中 ```` ``` ```` 必须成对，否则其后内容被静默跳过。
10. **技能内部不得出现仓库绝对路径**：路径一律相对技能根或仓库根。
11. **代码注释与标识符用英文，文档用中文**（沿用仓库既有风格）。
12. **原子提交**：每个 Task 结束即提交；Conventional Commits 格式。
13. **文件末尾保留一个空行**，UTF-8 无 BOM，LF 换行。

---

## 3. 《测试策略裁定书》

- **改动风险定级**: **HIGH**（新增技能，触及公共契约面：注册面 schema、`SKILL_NAMES`、`goal-loop` 挂载点、判定器退出码语义）
- **强制执行级别**: **L0 静态门禁 + L1 单元/契约测试 + L2 模块集成测试 + L3 端到端 dogfooding + L-Doc 文档门禁**
- **豁免测试级别**: 无豁免
- **豁免充分理由**: 不适用——本交付自身新增的技能必须**用自己产出的判据审计自己**（dogfooding），若豁免 L3，则「判定器是否真的能发现缺陷」这一核心命题无外部取证
- **精确验证命令清单**:
  1. **L0**: `python3 -m py_compile skills/spec-evolution/scripts/collect-facts.py skills/spec-evolution/scripts/judge.py`（Exit 0）
  2. **L1**: `python3 -m pytest skills/spec-evolution/tests/ -v`（本技能全部契约测试）
  3. **L2**: `python3 -m pytest skills/ -q`（全量，含 `_shared` 跨技能断链自检；基线 **324 passed**，本交付后应 ≥ 324 + 新增用例数）
  4. **L3**: 对本仓库真实运行 `python3 skills/spec-evolution/scripts/collect-facts.py --out /tmp/facts.json` → `python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json --json /tmp/findings.json --report /tmp/report.md`；须满足 §5 验收判据 A-1~A-4
  5. **L-Doc**: `python3 skills/doc-governance/scripts/check-doc-links.py --root docs`（断链 0）；`python3 skills/doc-governance/scripts/audit-doc-health.py`（PASS）；`python3 skills/doc-governance/scripts/check-doc-control-sync.py`（Exit 0）；`python3 skills/doc-governance/scripts/generate-llms-txt.py`（幂等，二次运行无 diff）

---

## 4. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P3 准备: 隔离分支与环境前置检查

- [ ] 从 `0306f37` 创建隔离分支：`git switch -c feature/spec-evolution 0306f37`
- [ ] 基线验证：`python3 -m pytest skills/ -q` → 期望 **324 passed**
- [ ] 基线记录：`python3 skills/doc-governance/scripts/check-doc-links.py --root docs` → 期望断链 **0**

---

### P3: 核心功能原子实现 (TDD 循环)

#### Task 1: 技能骨架——`SKILL.md`、判据表、锚点契约与基线常量

**Files:**
- Create: `skills/spec-evolution/SKILL.md`
- Create: `skills/spec-evolution/references/checks-spec.md`
- Create: `skills/spec-evolution/references/anchor-contract.md`
- Create: `skills/spec-evolution/references/baseline.json`

**Interfaces:**
- Consumes: 无（本任务是起点）
- Produces:
  - `references/baseline.json` 的顶层键 `root_prompt.{path,lines,bytes}` —— Task 2 的 `collect-facts.py` 读取它填入 `facts.json.root_prompt.baseline`
  - `references/checks-spec.md` 的判据 ID 集合 `C-01`..`C-10` 与严重度取值 `BLOCKER|HIGH|MID` —— Task 3 的 `judge.py` 与 Task 4 的测试按此实现
  - `references/anchor-contract.md` 的锚点三形式 `[SKILL:...]` / `[REPO:...]` / `[RULE:...]` —— Task 3 的 `judge.py` 按此校验

---

- [ ] **Step 1: 创建技能目录与 `SKILL.md`**

```bash
mkdir -p skills/spec-evolution/references skills/spec-evolution/templates \
         skills/spec-evolution/scripts skills/spec-evolution/tests
```

写入 `skills/spec-evolution/SKILL.md`（**注意**：`description` 中不得出现冒号+空格；字符数须 ≤ 500）：

````markdown
---
name: spec-evolution
description: Use when auditing delivery-surface completeness of this repository's skills and root prompt, or when a goal-loop P5 delivery re-checks the skills it touched. Runs a read-only fact collector and a deterministic exit-code judge (zero LLM, zero network) mapping facts to findings C-01 through C-10, emitting a report whose human-verdict section stays empty. Triggers on missing tests or design docs, incomplete skill surfaces, registration gaps, frontmatter length limits, oversized files, and root-prompt net growth.
license: MIT
---

# 机械化演进回路 (Spec Evolution)

## 概述 (Overview)

演进回路有两个端：**变异端**产出新规则候选，**选择端**判断哪条候选更好。本仓库的头号失败模式是「出问题就加一条」——那正是**只有变异、没有选择**的产物（ball of mud）。

本技能只做**选择端**，且只做其中**机械可证**的那部分：把「哪条规则需要修」从模型的**意见**换成脚本的**退出码**。

**立论**：凡不能被一条命令复现的「改进建议」，一律不产生 finding。

## 触发条件 (When to Use)

| 触发 | 说明 |
| :--- | :--- |
| **独立调用**（主路径） | 用户或智能体显式执行全量审计（7 技能 + 根提示词）；`--skills` 可缩窄范围 |
| **`goal-loop` P5 增量挂载** | 交付归档阶段复查**本次交付触及**的 `skills/<n>/`；不做全量扫描 |

**不适用**（结构性排除，详见 [references/checks-spec.md](references/checks-spec.md) §5）：
- 评价「这个技能该不该存在」「职责是否重叠」「设计是否过重」——无客观信号，是谄媚高发区；
- 评价判据阈值本身是否合理（如「1000 行是否应为 800 行」）。

## 硬不变式 (Hard Invariants)

1. **零 LLM、零网络**：判定器不得调用任何模型，不得访问网络。同一份输入永远得到同一份输出。
2. **只读**：采集与判定**不修改任何文件**。修改由人类裁决后另行发起。
3. **事实与发现分离**：采集器只回答「是什么」，判定器才回答「哪里不对」。二者分属不同进程，禁止合并。
4. **人类裁决不外判**：报告由判定器写到「人类裁决」标题即停止。任何由模型代填的裁决内容均视为**门禁违规**（GI-4 断言防护）。

## 快速开始 (Quick Start)

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --out /tmp/facts.json
python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json \
        --json /tmp/findings.json --report /tmp/report.md
echo "exit=$?"        # 0 = 无 BLOCKER/HIGH；1 = 存在 BLOCKER/HIGH；2 = 用法或输入错误
```

缩窄范围（推荐用于 P5 增量复查）：

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills goal-loop,doc-governance --out /tmp/facts.json
```

## 判据表 (Criteria)

十条判据的完整定义、严重度语义与已知表达上限见 [references/checks-spec.md](references/checks-spec.md)。

| ID | 判据 | 严重度 |
| :--- | :--- | :--- |
| **C-01** | 技能无 `tests/` 或其中无 `test_*.py` | HIGH |
| **C-02** | 技能无架构设计书 `docs/explanation/architecture/<n>-design.md` | MID |
| **C-03** | 技能交付面缺 `references/` / `scripts/` / `templates/`，或存在但为空 | MID |
| **C-04** | `description` 字符数 > 500（**软性建议值**，非硬限） | MID |
| **C-05** | `description` 字符数 ≥ 1024（Agent Skills 规范**硬限**） | HIGH |
| **C-06** | 单文件行数 > 1000 | MID |
| **C-07** | 技能在 4 个注册面中存在缺登记 | HIGH |
| **C-08** | 技能内存在跨技能相对链接 | HIGH |
| **C-09** | 既有门禁任一非零退出 | **BLOCKER** |
| **C-10** | 根提示词相对基线净增长 | MID |

## 锚点契约 (Anchors)

每条 finding 携带可被人直接核验的锚点。**锚点路径不存在时判定器自身报错退出 2**（防锚点幻觉）。三种形式与校验规则见 [references/anchor-contract.md](references/anchor-contract.md)。

## 退出码 (Exit Codes)

| 码 | 含义 |
| :--- | :--- |
| `0` | 无 **BLOCKER/HIGH**（可含 MID advisory） |
| `1` | 存在 **BLOCKER/HIGH** |
| `2` | 用法或输入错误（含锚点路径不存在 = 锚点幻觉） |

## 红线 (Red Lines)

- **不得**自动修复 finding——那会让本技能沦为「自动改自己规则的规则」，即 ball of mud 的机器化版本。
- **不得**往 `contexts/AGENTS.md` 增加条款——该文件准入判据禁止净增长。
- **不得**把本技能接入 CI 或引入第三方依赖。
````

- [ ] **Step 2: 校验 `SKILL.md` frontmatter 合规（C-04 / 冒号+空格禁令）**

```bash
python3 - <<'PY'
import re, pathlib
t = pathlib.Path('skills/spec-evolution/SKILL.md').read_text(encoding='utf-8')
fm = re.match(r'\A---[ \t]*\n(.*?)\n---[ \t]*\n', t, re.DOTALL).group(1)
desc = re.search(r'^description:[ \t]*(.*)$', fm, re.MULTILINE).group(1)
print('description_chars =', len(desc))
assert len(desc) <= 500, 'C-04：description 超 500 建议值'
assert '": "' not in fm, '冒号+空格会使 npx skills 静默跳过该技能'
print('OK')
PY
```

期望输出：`description_chars = <≤500 的整数>` 与 `OK`。**若超出 500，直接精简该行文案后重跑本步**，不得跳过。

- [ ] **Step 3: 写入判据表 `references/checks-spec.md`**

````markdown
# 判据表与严重度语义 (Checks Spec)

> **单一真相源**：本文件定义 C-01~C-10 与严重度语义。`judge.py` 与测试断言以本文件为准；
> 修改判据必须同时修改 `judge.py`、`tests/` 与本文件的修订记录。
> **来源**：本表结晶自 [RFC-0004](../../../docs/proposals/RFC-0004-spec-evolution.md) §3.2。

## 1. 判据定义

| ID | 判据 | 事实源 | 严重度 | 触发条件（精确） |
| :--- | :--- | :--- | :--- | :--- |
| **C-01** | 技能无测试 | S2 | HIGH | `has_tests == false`（`tests/` 不存在，或存在但无 `test_*.py`） |
| **C-02** | 技能无架构设计书 | S2 | MID | `design_doc == null` |
| **C-03** | 交付面不完整 | S2 | MID | `references`/`scripts`/`templates` 任一缺失，或存在但为空 |
| **C-04** | description 超建议值 | S2 | MID | `description_chars > 500` |
| **C-05** | description 超硬限 | S2 | HIGH | `description_chars >= 1024` |
| **C-06** | 单文件超 1000 行 | S2 | MID | `oversized_files` 非空 |
| **C-07** | 注册面缺登记 | S3 | HIGH | 4 个注册面任一处为 `false` |
| **C-08** | 跨技能相对链接 | S2 | HIGH | `cross_skill_links` 非空 |
| **C-09** | 既有门禁失败 | S1 | **BLOCKER** | 4 条门禁任一 `exit_code != 0` |
| **C-10** | 根提示词净增长 | S2 | MID | 行数 > 基线行数，或字节数 > 基线字节数 |

## 2. 严重度语义

| 严重度 | 含义 | 处置 |
| :--- | :--- | :--- |
| `BLOCKER` | 仓库既有门禁已失败 | 置顶并阻断交付；本技能不重复判定其根因 |
| `HIGH` | 违反**成文规范或外部硬限**（有权威出处，超限可致技能失效） | 应修复 |
| `MID` | 交付面完整性缺口，或**对软性建议值的偏离**（advisory，无权威硬约束） | 登记为待办，不阻断交付 |

## 3. 阈值权威性裁定

| 阈值 | 出处 | 性质 | 超限后果 |
| :--- | :--- | :--- | :--- |
| **1024** | [Agent Skills 规范](https://agentskills.io/specification)：`description` Max 1024 characters | **规范硬限** | 技能在 Claude API / CLI 侧被**静默丢弃** |
| **500** | `writing-skills` 技能：Keep under 500 characters **if possible** | **软性建议** | 无——仅增加每会话元数据开销 |
| **1000 行** | `contexts/AGENTS.md` §3「精准修改与代码卫生」下的「禁止占位符与规模控制」条目 | 仓库成文规范 | 违反工程规范 |

**「500 字符」不构成违规**：V0.1.0 曾以「仓库既有规范」为依据，该链经查为**循环引用**
（frontend-qa-gate 计划称「与仓库既有规范一致」，其唯一先例 taste-driven-designer 计划自己写的是
「超出 `writing-skills` **建议** 500 上限」）。故 C-04 恒为 MID，不得升格为 HIGH。

## 4. 已知表达上限（显式登记，不在 v1 掩饰）

1. **C-10 无法判定「理由是否成立」**：`contexts/AGENTS.md:3` 的准入判据允许净增长，前提是同一提交内给出等量删减或不可压缩的理由。判定器只能机械观测「是否净增长」，**无法**判定理由成立与否。故 C-10 的报告文案固定为**中性提示**，而非指控。
2. **C-03 存在误报面**：`scripts/` 与 `templates/` 对纯规程型技能可豁免（RFC-0004 `DA-2`）。C-03 采「有则须完整、无则记 MID 提示」而非 HIGH 指控；命中项**须人工确认是否属豁免场景**。
3. **C-08 的正则与 `test_cross_skill_links.py` 同源但不同文件**：两处正则可能漂移。缓解：C-09 会运行该测试本身，一旦二者语义背离，C-09 先失败。
4. **本技能不做设计质量评价**：职责重叠、技能该不该存在、是否过重，一律不在判定域内。此类问题无退出码可复现，纳入即等于给谄媚开门。

## 5. 修订记录

| 版本 | 日期 | 变更 |
| :--- | :--- | :--- |
| V1.0.0 | 2026-10-12 | 初次结晶自 RFC-0004 §3.2（已受理 V0.3.0） |
````

- [ ] **Step 4: 写入锚点契约 `references/anchor-contract.md`**

````markdown
# 锚点契约 (Anchor Contract)

> **来源**：[RFC-0004](../../../docs/proposals/RFC-0004-spec-evolution.md) §3.4。
> **目的**：让每条 finding 都能被人类用一条命令直接核验，且**抗行号漂移**。

## 1. 三种锚点形式

| 形式 | 语法 | 解析域 | 例 |
| :--- | :--- | :--- | :--- |
| 技能内文件 | `[SKILL:<skill-name>/<relative-path>]` | `skills/<skill-name>/` | `[SKILL:clarification-protocol/SKILL.md]` |
| 技能内文件 + 行 | `[SKILL:<skill-name>/<path>:<line>]` | 同上 | `[SKILL:doc-governance/tests/test_doc_governance_scripts.py:1]` |
| 仓库内其它文件 | `[REPO:<repo-relative-path>[:<line>]]` | 仓库根 | `[REPO:tools/skills-manager/collections/cr-agent-arsenal.json]` |
| 根提示词条款 | `[RULE:§<N>-<title>]` | `contexts/AGENTS.md` 标题树 | `[RULE:§3-精准修改与代码卫生]` |

> **`[REPO:...]` 是本计划对 RFC-0004 §3.4 的**扩展**。RFC 原列 `[SKILL:*]` 与 `[RULE:*]` 两种形式，
> 但 C-07（注册面）与 C-09（门禁）两类 finding 的核验位置落在技能目录之外，用 `[SKILL:*]` 表达会误导。
> 扩展理由与 RFC 回写动作登记于本计划 §5 与 P4。

## 2. 存在性校验（硬门禁）

**判定器在输出任何 finding 之前，必须校验全部锚点。任一锚点解析失败，判定器以退出码 2 终止并打印失效锚点。**

| 形式 | 校验规则 |
| :--- | :--- |
| `[SKILL:<n>/<p>]` | `skills/<n>/<p>` 必须为已存在路径 |
| `[SKILL:<n>/<p>:<l>]` | 路径存在，且 `<l>` 为 `1 <= l <= 该文件行数` 的整数 |
| `[REPO:<p>]` / `[REPO:<p>:<l>]` | 同上去掉 `skills/` 前缀，以仓库根为基准 |
| `[RULE:§<N>-<title>]` | `contexts/AGENTS.md` 的 `## <N>.` 标题下，存在 `###` 标题其规范化文本以 `<title>` 开头 |

**理由**：这是「防锚点幻觉」的机械保证——模型无法伪造一个不存在的核验位置。

## 3. `[RULE:*]` 的解析规则

1. 解析域为 `contexts/AGENTS.md` 的标题树，**不记行号**，故天然抗行号漂移。
2. `§<N>` 指向 `## <N>. ...` 形式的二级标题（`N` 为阿拉伯数字）。
3. `<title>` 为该二级标题下某个 `###` 标题的文本，**规范化**后比较：
   - 去除首尾空白；
   - 连续空白折叠为单个空格；
   - 比较方式为「规范化后的 `###` 标题**以** `<title>` 开头」。
4. 例：`### 工具链与环境防御 (Read-Modify-Verify)` 可被 `[RULE:§3-工具链与环境防御]` 或
   `[RULE:§3-工具链与环境防御 (Read-Modify-Verify)]` 命中。

## 4. 采集侧契约

`collect-facts.py` 必须把标题树导出到 `facts.json`：

```json
"root_prompt": {
  "path": "contexts/AGENTS.md",
  "lines": 97,
  "bytes": 10746,
  "baseline": {"lines": 97, "bytes": 10746},
  "headings": ["# SYSTEM RULES", "## 0. ⛔ 安全红线 (Safety Red Lines)", "### Git 操作红线", "..."]
}
```

`headings` 为按文件顺序排列的 `#`~`###` 标题原文（含前缀 `#` 与空格）。
````

- [ ] **Step 5: 写入基线常量 `references/baseline.json`**

```json
{
  "_comment": "根提示词基线常量。基线随合法增删而变；变更本文件须在提交信息中给出等量删减或不可压缩的理由（contexts/AGENTS.md:3 准入判据）。",
  "root_prompt": {
    "path": "contexts/AGENTS.md",
    "lines": 97,
    "bytes": 10746,
    "recorded_at": "2026-10-12",
    "recorded_head": "10359c2"
  }
}
```

- [ ] **Step 6: 校验基线常量与真实文件一致**

```bash
python3 - <<'PY'
import json, pathlib
b = json.loads(pathlib.Path('skills/spec-evolution/references/baseline.json').read_text(encoding='utf-8'))['root_prompt']
p = pathlib.Path(b['path'])
lines = len(p.read_text(encoding='utf-8').splitlines())
nbytes = p.stat().st_size
print('baseline', b['lines'], b['bytes'], '| actual', lines, nbytes)
assert lines == b['lines'], f'行数不符: {lines} != {b["lines"]}'
assert nbytes == b['bytes'], f'字节数不符: {nbytes} != {b["bytes"]}'
print('OK')
PY
```

期望：`baseline 97 10746 | actual 97 10746` 与 `OK`。**不符时以真实值为准修正 `baseline.json`**（不得改 `contexts/AGENTS.md` 迎合基线——那违反 `N-3`）。

- [ ] **Step 7: 提交**

```bash
git add skills/spec-evolution/SKILL.md skills/spec-evolution/references/
git commit -m "feat(spec-evolution): 技能骨架与判据/锚点/基线契约

Task 1/7：SKILL.md 路由层 + references（判据表 C-01~C-10、锚点三形式、根提示词基线）。
契约结晶自 RFC-0004 §3.2/§3.4（已受理 V0.3.0）。"
```

---

#### Task 2: 事实采集器 `collect-facts.py` 与契约测试

> 原文迁移至子册：[2026-10-12-spec-evolution-task2.md](./2026-10-12-spec-evolution-task2.md)（全部 Step、代码清单与验收判据逐字保留）。

#### Task 3: 判定器 `judge.py`、报告模板与判定契约测试

> 原文迁移至子册：[2026-10-12-spec-evolution-task3.md](./2026-10-12-spec-evolution-task3.md)。

#### Task 4: 门禁不变式测试 `test_gate_invariants.py`

> 原文迁移至子册：[2026-10-12-spec-evolution-task4-6.md](./2026-10-12-spec-evolution-task4-6.md)（含 Task 4 / Task 5 / Task 6）。

#### Task 5: 架构设计书

> 原文同见子册：[2026-10-12-spec-evolution-task4-6.md](./2026-10-12-spec-evolution-task4-6.md)。

#### Task 6: 全套注册面接入

> 原文同见子册：[2026-10-12-spec-evolution-task4-6.md](./2026-10-12-spec-evolution-task4-6.md)。

#### Task 7: P5 交付收口

**Files**
- Modify: `docs/proposals/RFC-0004-spec-evolution.md`（状态 → `Implemented`）
- Modify: `docs/project/plans/2026-10-12-spec-evolution.md`（Active Checkpoint 流转）

- [ ] **Step 1: RFC-0004 状态流转**

将提案元数据的「当前状态」改为 `Implemented`，并在修订历史追加一行（版本号 +1，描述「交付完成，判据器/采集器/门禁不变式落地」）。

> **默认假设（显式登记）**：`docs/GOVERNANCE.md` 规定 Implemented 后移入 `proposals/archive/`，但仓库现无该目录、且 RFC-0001~0003 均未归档，故**本次不移位**，仅在原位标注状态。理由：移位会打断 `skills/spec-evolution/references/*.md` 中指向 `../../../docs/proposals/RFC-0004-spec-evolution.md` 的相对链接，而归档目录约定尚未在实践中确立。此假设在交付报告中显式告知用户。

- [ ] **Step 2: 计划文件 Active Checkpoint 流转**

把头部 Active Checkpoint 的「当前活跃阶段」推进到 `P5 交付`，「最后一次验证状态」填写 Task 6 Step 8 的实际门禁结果，「最新有效提交」填 Task 6 的提交哈希。

- [ ] **Step 3: 终局全门禁**

```bash
python3 -m pytest skills/ -q
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py
git status --porcelain
```

期望：全绿；`git status` 除预期改动外干净。

- [ ] **Step 4: 提交并推送**

```bash
git add docs/proposals/RFC-0004-spec-evolution.md docs/project/plans/2026-10-12-spec-evolution.md
git commit -m "docs(spec-evolution): P5 交付收口

Task 7/7：RFC-0004 流转 Implemented（原位保留，归档目录约定未确立）；
计划文件 Active Checkpoint 推进至 P5。"
git push origin master
```

**Acceptance（Task 7）**：㉒ `git status --porcelain` 干净；㉓ 远端 `master` 含本次全部提交。

> **D-9（2026-10-12 P3 执行期修正）**：Step 4 的 `git push origin master` 与铁律⑦（分支隔离：严禁在 `master` 直接写代码）及铁律⑧（交付前必须有独立子智能体 Zero Blockers 裁决）**冲突** —— 本次全部提交位于 `feature/spec-evolution`，且 P3.5 独立终审尚未派发。故本次**只推送功能分支** `feature/spec-evolution`；合入 `master` 待 P3.5 取得 Zero Blockers 裁决后再由用户裁定。㉓ 的口径相应改为「远端 `feature/spec-evolution` 含本次全部提交」。

> **执行偏差记录 (Deviation Log) —— 2026-10-12 P3.5 双轮对抗审查修正 (D-10~D-14)**
>
> 触发：`dual-round-review` Full 模式，基线 `0306f37..fe8da78`。R1 红队裁决 3×P1 / 5×P2 / 7×P3；R2 元审判裁决**阻断交付**（3×🔴 / 12×🟡），并对 R1 的三处误报与本轮修法范围作出裁定。下表为落实后的实际改动。
>
> | # | 缺陷（R1/R2 编号） | 修法 | 变异对照 / 取证 |
> | :--- | :--- | :--- | :--- |
> | D-10 | **GI-6 只读不变式实质失效**（R1-1）：`GATES` 中 `check_doc_links`/`audit_doc_health` **无 `-B`**，且真实 `audit-doc-health.py` 级联调用兄弟脚本（`importlib` + `subprocess`）——命令行 `-B` **不进入子进程环境**，`__pycache__` 仍会落盘；**夹具还是「三无桩」**（`import sys; sys.exit(0)`），结构上不可能写字节码，使该断言恒真 | ① 采集器**每一处** `subprocess.run` 注入 `env=subprocess_env()`（`PYTHONDONTWRITEBYTECODE=1`）——唯一覆盖整棵进程树的机制；② 两条命令补 `-B` 作纵深防御；③ 夹具桩改为「门禁进程 → 子进程 → `import` 兄弟模块」三级链；④ 新增 `test_gi6_bytecode_suppression_is_structural`，以 `ast` 钉住「所有 `subprocess.run` 均带 `env`」 | 移除 `env=subprocess_env()` 后**两条测试同时失败**（功能 + 结构）；恢复后 52 passed |
> | D-11 | **退出码口径与实现漂移**（R1-2）：RFC §3.3、`SKILL.md`、本计划均写「0 = 无 finding」，但 `judge.py` 实测 **MID → 0** | 以**实现为准**收敛措辞为「`0` = 无 BLOCKER/HIGH（可含 MID advisory）；`1` = 存在 BLOCKER/HIGH」，四份文档同步（RFC-0004 / 本计划 / `SKILL.md` / 架构设计书）。**未**改 `judge.py` —— MID 不阻断是 RFC §3.2 严重度语义的既定设计，且被 23 条契约测试锁定 | 全仓 `grep` 复核无残留旧口径 |
> | D-12 | **`--no-gates` 时对既有门禁作肯定陈述**（R1-3）：`gates = null` ⇒ C-09 静默不执行，报告却输出「（无既有门禁失败）」——**未取证而宣称取证** | `render_report` 区分三态：有失败 / 已采集且无失败 / **未采集**，后者输出「未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论」。`SKILL.md` 加警示「放行前最终复查必须不带 `--no-gates`」 | 新增 `test_report_says_clean_only_when_gates_were_collected` 锁死「空表 ≠ null」 |
> | D-13 | **锚点 containment 收紧误伤目录锚点**（本轮自查）：按 R1 建议把解析改为「必须是普通文件」后，`GATE_ANCHORS["pytest"] = "skills/"` 这一**目录锚点**被判失效，含未失败门禁的报告恒以退出码 2 拒绝产出（5 条测试转红） | 区分语义：**路径存在性**允许文件或目录（`[REPO:skills/]` 指向套件根是合法证据）；**行号校验**只对文件有意义，目录带行号判失败。绝对路径逃逸的 containment 校验保留 | 52 passed |
> | D-14 | **R2 对 R1 的元裁定**：R1 三处不成立 —— ① R1-7「`grep -c "CI\|pytest"` 恒真」无法复现（该串在 1787 行中命中 0 次，R1 所报数字仅覆盖单段）；② R1-13「两处 `description` 计数不同源」属**过度表述**，实为同一 `len()` 计数的两处调用；③ R1-6 由 P2 **下调** P3 | 三项均**不成立即不修**，如实登记以保持「宣称与取证同宽」。R2 另**否决**三项扩大化改法（YAGNI）：不把夹具桩替换为真实门禁、不为 C-09 增设 `INCOMPLETE` 第四态、不把 MID 升格为阻断 | R2 报告 `r2-0306f37..fe8da78.md` |

> | D-15 | **RFC-0004 §3.4 锚点契约漏登 `[REPO:*]`**（R1-7，R2 认定「比 R1 所述更严重」）：实现已使用 `[REPO:*]` 表达 C-07 的四个注册面与 C-09 的门禁证据，但 RFC 原文只登记 `[SKILL:*]` / `[RULE:*]` —— 契约缺口 | 补登 `[REPO:<repo-relative-path>[:<line>]]` 形式与行号语义（`:line` 只对文件有意义、目录锚点不得带行号、裸路径允许文件或目录），并明确 `[RULE:*]` 解析域是**标题树**而非加粗条目；GI-3、术语表、DK-5 同步扩至三类锚点 | RFC-0004 V0.5.0 |
> | D-16 | **R1/R2 的非阻断项须登记为可追踪待办**，否则「登记待办」的裁决无落点 | 按 R2「待办登记（不阻断）」裁定，把 R1-4 / R1-5 / R1-8 / R1-10 / R1-11 / R1-13 / R1-15 七项落为 Backlog 卡片 `BK-0033`~`BK-0039`（`manage-backlog.py create` + `sync-index`），含来源追溯、触发条件与验收准则 | `docs/project/backlog/active/BK-0033..0039` |

> **执行偏差记录 (Deviation Log) —— 2026-10-12 P3.5 Delta 轮修正 (D-17~D-21)**
>
> 触发：`dual-round-review` Delta 模式，基线 `fe8da78..9e66a5d`。Delta R1 裁决 **1×P1 阻断 / 5×P2~P3**，其中 P1 直指 D-10 的修法**未根治**（Lead 已独立复现）。下表为落实后的实际改动。
>
> | # | 缺陷（DR1 编号） | 修法 | 变异对照 / 取证 |
> | :--- | :--- | :--- | :--- |
> | D-17 | **GI-6 仍未根治**（DR1-1，P1）：上一轮认定 `-B` 不足的**根因叙述有误** —— 真实泄漏路径是显式 `py_compile.compile()`，它**同时无视** `-B` 与 `PYTHONDONTWRITEBYTECODE`（出处：`skills/doc-governance/tests/test_doc_index_convention.py:415-421` 在 `-W error::SyntaxWarning` 下编译脚本） | `subprocess_env()` 增 `PYTHONPYCACHEPREFIX`（把字节码写入整体改道仓库外）+ 修正常量注释；夹具桩由「三级 import 链」升级为**真实触发该路径**（`py_compile.compile(...)`）；`test_gi6_bytecode_suppression_is_structural` 改为 `ast` 钉住 `subprocess_env()` 内两个环境键的赋值 | 变异实测：移除 `PYTHONPYCACHEPREFIX` → **2 条转红**（结构 + 功能）；单独移除 `PYTHONDONTWRITEBYTECODE` → 仅结构测试转红（其为冗余纵深）。端到端干净副本差分：修复前残留 `skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc`，修复后 **0 残留** |
> | D-18 | **根因叙述失实**（DR1-2）：四处把「`-B` 覆盖不足」归因于 `importlib` 动态加载，实为显式 `py_compile` | `collect-facts.py`、`conftest.py` 桩、`test_gate_invariants.py`、`docs/explanation/architecture/spec-evolution-design.md:87` 全部改写为「三条路径各需不同机制」（直接子进程靠 `-B`；经 `subprocess` 派生的孙进程靠 `PYTHONDONTWRITEBYTECODE`；显式 `py_compile` 只有 `PYTHONPYCACHEPREFIX` 能拦） | 与 D-17 的变异结果一致 |
> | D-19 | **权威断链**（DR1-3）：`SKILL.md:81` 把 `references/checks-spec.md` 指为退出码权威出处，但该文件**无退出码章节** | `checks-spec.md` 新增 §4「退出码语义」（三态表 + 「MID 不阻断」理由 + 「`2` 不写产物」理由），原 §4/§5 顺延为 §5/§6，修订记录加 V1.1.0 | 章节编号全文件复核 |
> | D-20 | **三态判据的 falsy 漏洞**（DR1-5）：`judge.py` 以 `raw_gates is None` 判「未采集」，而 `--facts` 接受外部输入，`[]`/`{}`/`0`/`""`/畸形结构均可达并被当作「已采集且无失败」 | 抽出 `collected_gates()`，要求**≥1 条 well-formed 的 `{cmd, exit_code, summary}`** 才构成「已采集」证据；`build_findings` 与 `render_report` 共用 | 原测试以 `gates = {}` 断言「已采集且无失败」，该期望**本身即 fail-open**；已改写为对 `(None, [], {}, 0, "", "junk", {"pytest": "junk"})` 逐项断言「未采集」，另加一条 well-formed 清洁表断言「已采集」。此为**收紧**语义，非弱化断言。**本轮 R1-1 进一步收紧**：顶层**类型**畸形（`skills=5` / `root_prompt="junk"`）改判退出码 2，见 D-24 |
> | D-21 | **未登记的行为变更**（DR1-6）：README 登记判据由裸子串 `skills/<name>` 收紧为精确串 `skills/<name>/SKILL.md`（前缀兄弟技能可致 C-07 **HIGH 假阴性**），但既未写入判据表、也无测试 | `checks-spec.md` §1 的 C-07 行注明精确形式；新增 `test_readme_registration_requires_exact_skill_path`（构造只含 `skills/demo-suffix` 的 README，断言仍判未登记） | 该测试在收紧前的实现上会转红 |

> | D-22 | **BK-0033 状态陈旧**（DR1-4）：卡片文案仍写「两处 `subprocess.run` 加 encoding」未做，实际已在 `d8aa611` 落地 | 卡片标题与 DoD 收窄为「print 硬化 + 异常退出码收敛」两项，§4 补记「部分落地（`d8aa611`）」 | `docs/project/backlog/active/BK-0033-*.md` |
> | D-23 | **Delta R1 报告区块标题不符门禁 schema**（本轮自查）：该报告五区块写作 `## §1 第一性原理与本质溯源` 等简写，而 `round-1-red-team.md` 模板与 `check-review-report.sh` 要求 `## 1. 第一性原理与本质溯源分析` 等**逐字标题**，归档后门禁报 5 条「缺少必需区块」。**根因是 Lead 派发提示词的简写，非子智能体偏离**（首轮 r1 逐字沿用模板即通过） | 报告是 SHA256 已登记的 Write-Once 审计凭据，**零改动**；台账该行由 `delta-r1` 降级为 `retired`（声明为非 R1 凭据，仍受文件存在 / 指纹 / 写入形态三项校验），全部事实写入台账、待办与修订历史。后续 delta 轮次的派发提示词改为**逐字粘贴模板标题** | 降级后 `check-review-report.sh` → **通过**（索引齐备 · 报告 3 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐） |
> | D-24 | **退出码伪装**（delta-r1 R1-1，P2）：`load_facts` 只校验顶层键**在场**，不校验**类型**。`skills=5` / `root_prompt="junk"` / `repo_root=123` 会让 `build_findings` 抛 `TypeError`，解释器以状态码 **1** 退出 —— 恰与「存在 BLOCKER/HIGH」同码，诊断也从 `❌` 降级为裸 traceback。编排方若只读退出码，会把「输入坏了」采信为「存在高危结论」 | `load_facts` 增键类型校验（`repo_root:str` / `skills:list` / `gates:dict|list|None` / `root_prompt:dict`，且 `skills[]` 每项须为含 `name` 的对象），不符即 `FactsError` → 退出码 2；原「falsy 值归未采集」用例拆分：结构性缺失（`None`/`[]`/`{}`/畸形成员）仍归「未采集」，**类型**畸形归退出码 2 | 新增 `test_malformed_top_level_types_exit_2`（6 组 patch 逐项断言 rc == 2）；`test_report_says_clean_only_when_gates_were_collected` 的负例收窄为结构性缺失 |
> | D-25 | **共享缓存投毒 → 门禁进程内任意代码执行**（delta-r1 R1-2，P2）：重定向根固定为 `/tmp/spec-evolution-pycache`（可预测、共享、跨运行持久）且不校验属主/独占性。`/tmp` 为 `drwxrwxrwt`，本地用户可抢先创建该目录并植入与门禁模块同尺寸同 mtime 的畸形成员字节码，被门禁进程当作真实模块读取执行（审查方**实测已执行注入代码**） | 弃用固定名，改 `tempfile.mkdtemp(prefix="spec-evolution-pycache-", dir=base)` 独占创建随机名目录（`mkdtemp` 保证不存在才创建、权限 0700），并 `atexit` 注册 `shutil.rmtree` 清理以免 /tmp 累积。代价是放弃「固定名复用」的既有取舍 —— 该取舍本身即漏洞来源 | 新增 `test_gi6_pycache_prefix_is_per_run_and_private`（两次独立进程取前缀，断言路径不同 + 权限 0700 + 不在仓库内）。**变异 A**（退回固定名 + `makedirs`）→ 该测试转红、其余 14 条不动 |
> | D-26 | **重定向根可被环境/回落重新指回仓库**（delta-r1 R1-3，P3）：重定向根在模块级由 `tempfile.gettempdir()` 推导，采集器不校验它位于 `repo_root` 之外。`TMPDIR` 指向仓库内、或候选临时目录全不可写导致 `gettempdir()` 回落 `os.getcwd()` 时，镜像整体落入仓库，GI-6 静默失守（审查方实测新增 3 个镜像文件） | 求值从模块级移入 `pycache_prefix(repo)`：**先**校验临时根在仓库之外（**在创建任何目录之前**，避免校验失败却已落盘），不成立即 `CollectError` → 退出码 2，绝不退化成「悄悄写进仓库」 | 新增 `test_gi6_rejects_pycache_prefix_inside_repo`（`TMPDIR=<repo>` 运行采集器，断言 rc == 2 + stderr 含「仓库内」+ 仓库零写入）。**变异 B**（删去 `if base == repo or repo in base.parents` 判定）→ 该测试转红、其余 14 条不动 |
> | D-27 | **章节重编号引入的引用断裂**（delta-r1 R1-4，P2）：D-19 为补登退出码权威新增 `checks-spec.md` §4 并把原 §4/§5 顺延为 §5/§6，但三处 `§4` 指针未同步（`SKILL.md:24`、`spec-evolution-design.md:161`、计划 `:2115` 及其代码副本 `:194`），改动后指向「退出码语义」而实际内容已顺延为 §5「已知表达上限」；D-19 自述的验证方法「章节编号全文件复核」**未落实**（宣称宽于取证） | 四处指针改为 `§5`（`SKILL.md` / 设计书 / 计划正文两处），并全仓复核确认剩余 `§4` 引用均正确指向「退出码语义」 | `grep -rn "checks-spec.md.*§4"` 只剩计划 `:31`（D-19 记述）与 `:2300`（D-19 行本身），二者语义正确 |

> | D-28 | **嵌套类型逃逸**（delta-r2 R2 残余发现，主智能体独立复现）：D-24 只给 `load_facts` 加了**顶层**键类型校验，未下探 `skills[]` 成员字段。`description_chars="abc"` / `registrations="x"` / `oversized_files=[123]` / `cross_skill_links=5` 会令 `build_findings` 抛 `TypeError`/`AttributeError`，解释器以状态码 **1** 退出 —— 与「存在 BLOCKER/HIGH」同码。**两处复核澄清**：R2 举例的 `skills[].path=123` 与 `skills[].files="x"` 实测 **rc=0**（判定器不消费这两个键）；且上述崩溃路径**均不写出报告**，故不存在「写出伪造报告」。R2 的 🟡 非阻断定级**维持不变**（退出码仍非 0，编排方不会误采信为 CLEAN）。另：`atexit` 在信号终止（SIGTERM/SIGKILL）下不执行，`mkdtemp` 目录会在 `/tmp` 残留 —— 属资源整洁度问题，非正确性问题 | **不在本次交付内修复**（R2 已裁定非阻断；且任何修复都必须重跑完整双轮闭环，不得在 Zero Blockers 后单方面改码）。登记 `BK-0040`（Bug / P2），修法建议：在 `main()` 中包一层兜底，把 `FactsError` 以外的异常转译为 `FactsError`（→ 退出码 2 + `❌` 诊断）—— 一次关闭**整类**逃逸，优于逐键白名单的「打地鼠」 | 独立复现（干净基线夹具：仅 `spec-evolution` 自身，正常 rc=0 / findings=0）：上表五例 rc 均为 **1** 且**不写报告**；对照 `path=123` / `files="x"` / `name=123` 三例 rc 均为 **0** |
---

### §5 验收判据总表（Definition of Done）

| # | 判据 | 命令 | 期望 | 实测（2026-10-13，交付点 `5992a7a`） |
| :--- | :--- | :--- | :--- | :--- |
| ① | 技能可被宿主发现 | `ls .agents/skills/spec-evolution/SKILL.md` | 存在 | ✅ 软链已建（`contexts/install.py` 输出确认） |
| ② | description ≤ 500 字符 | `python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills spec-evolution` | `description_chars` ≤ 500 | ✅ **427** |
| ③ | 采集器契约 | `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -q` | 全绿 | ✅ **16 passed** |
| ④ | 判定器契约 | `python3 -m pytest skills/spec-evolution/tests/test_judge_contract.py -q` | 全绿 | ✅ **25 passed** |
| ⑤ | 门禁不变式 | `python3 -m pytest skills/spec-evolution/tests/test_gate_invariants.py -q` | 全绿 | ✅ **15 passed** |
| ⑥ | 全仓回归 | `python3 -m pytest skills/ -q` | 全绿（≥ 324 + 新增） | ✅ **380 passed** |
| ⑦ | 文档断链 | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` | 0 断链 | ✅ **75 文件 0 断链** |
| ⑧ | 文档健康 | `python3 skills/doc-governance/scripts/audit-doc-health.py` | PASS | ✅ **PASS** |
| ⑨ | 自我判定 | 判定器扫描全仓 | `spec-evolution` 零 finding | ✅ **零 finding**（全仓 11 findings 中无一条指向本技能） |
| ⑩ | 只读不变式 | `git status --porcelain` 在采集后 | 除显式产物外无变化 | ✅ `git archive` 干净副本采集前后 **diff 为空** |
| ⑪ | 人类裁决留白 | 报告 `## 人类裁决` 之后 | 无 `[x]`、无判定器内容 | ✅ 裁决区 11 行**全留白** |
| ⑫ | 独立终审 | `dual-round-review` R1+R2 | Zero Blockers | ✅ delta-r2 **🔴 0 / 🟡 19 / ⚪ 0** → 准予交付 |

---

### §6 风险、回滚与显式默认假设

| 风险 | 触发信号 | 处置 |
| :--- | :--- | :--- |
| 判定器成为新的 ball of mud 源头 | 判据数持续增长、`C-11+` 频繁新增 | 判据表新增须同时给出「哪条判据被合并或删除」；否则拒绝 |
| 报告沦为无人读的仪式 | `docs/project/reviews/*selfcheck*` 长期裁决区空白 | 本技能定位为**按需/周期性**审计，不随每次交付触发；空白报告即证据，说明尚未需要 |
| 采集器误报（正则与真实文档风格漂移） | C-08 出现假阳性 | `test_cross_skill_links.py` 是 SSOT；采集器正则必须与其同源，漂移时改采集器而非改判据 |
| 门禁耗时拖慢日常 | 采集器被误挂进 pre-commit | 采集器**不得**挂 pre-commit；仅在显式调用时运行 |
| 锚点因文档搬迁失效 | 退出码 2 且 stderr 指向不存在路径 | 这是**设计行为**（fail-closed），修锚点或修文档，不得放宽校验 |
| 回滚 | 需要撤销本交付 | `git revert` 本次全部提交；本技能为纯新增 + 四处登记行，无数据迁移、无契约破坏 |

**显式默认假设（未获用户逐条确认，登记备查）**
1. RFC-0004 状态流转 `Implemented` 但**不移入 `proposals/archive/`**（理由见 Task 7 Step 1）。
2. `docs/project/reviews/spec-evolution-selfcheck.md` 作为裁决载体落 `reviews/`（每一交付单元一个目录的既有惯例下，本次以单文件形式落盘）。
3. F-1~F-8 不在本次修复，仅修 F-9；其余转为独立 backlog 条目（若用户需要，另起任务）。
4. 判据表固定在 C-01~C-10，v1 不扩表。

---

### 修订历史

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| V1.4.0 | 2026-10-12 | DSH AI Agent | 待用户裁定 | P3.5 Delta 轮修正收口（`7449aae`）：Delta R1 的 1×P1 + 5×P2~P3 全部落地，新增《执行偏差记录》D-17~D-22 —— D-17 指出上一轮 GI-6 修法**未根治**且根因叙述有误（真实泄漏路径是显式 `py_compile.compile()`，同时无视 `-B` 与 `PYTHONDONTWRITEBYTECODE`），改以 `PYTHONPYCACHEPREFIX` 改道仓库外；端到端干净副本差分由「残留 1 个 `.pyc`」转为 **0 残留**。验收 `pytest skills/` → 377 passed、断链 0、健康 PASS |
| V1.5.0 | 2026-10-12 | DSH AI Agent | 待用户裁定 | P3.5 **重派 Delta R1** 收口（`2100973` 修复批次 / `7bb09c5` 报告归档）：重派轮次裁决 **Zero Blockers**（P0 = 0 / P1 = 0），前轮 DR1-1~DR1-3 复核**全部根治**；落地其 4 条 P2~P3 建议，新增《执行偏差记录》D-24~D-27（退出码类型伪装 / 共享缓存投毒 / 重定向根越界回落 / 章节重编号指针断裂）—— 其中 D-25 是审查方实测确认「**具备代码执行后果**」的缓存投毒通道，改以 `mkdtemp` 独占随机名 + `atexit` 清理关闭；D-27 同时修正 D-19 自述「章节编号全文件复核」的过宽宣称。验收 `pytest skills/` → 380 passed、断链 0、健康 PASS、归档门禁通过 |
| V1.6.0 | 2026-10-12 | DSH AI Agent | 待用户裁定 | P3.5 双轮对抗收口并取得 **✅ 准予交付** 终审裁决：delta-r2 裁决 Blockers = 0（🔴 0 / 🟡 19 / ⚪ 0），首轮 3 个 P1 与 Delta 轮 4 条逐条实测根治，变异 A/B 独立复现判别力，`baseline.json` 与 `contexts/AGENTS.md` 逐值一致，判定器真实仓库自证 `spec-evolution` 自身 0 finding；报告归档并登记台账（V1.3.0）。R2 独立发现的嵌套类型逃逸经主智能体复现后登记 **D-28** + `BK-0040`（非阻断，`atexit` 信号下不执行一并记录），按「检测与修复分离」不随本次交付；Active Checkpoint 推进至 P4，待用户裁定合入 `master`（D-9） |
| V1.7.0 | 2026-10-13 | DSH AI Agent | 王辉 | **交付收口**：用户裁定「快进合并并推送」（D-9）与「R2 非阻断残余留作 `BK-0040`」。`feature/spec-evolution` 以 `--ff-only` 合入 `master`（`63de31b..5992a7a`，35 文件 / +4077−40）并推送 `origin/master`（`206d14b..5992a7a`）；Active Checkpoint 推进至 **DONE / P5 已交付**；§5 验收判据总表新增「实测」列，十二条判据逐条取证（`380 passed` / 断链 0 / 健康 PASS / 归档门禁通过 / `spec-evolution` 自身零 finding / 裁决区留白 / 🔴 0 终审） |
| V1.8.0 | 2026-11-23 | DSH AI Agent | 王辉 | **文档拆分（BK-0050）**：Task 2 / Task 3 / Task 4-6 原文迁移至子册（task2 / task3 / task4-6），主册保留目标、约束、Task 1、Task 7、验收与风险；两篇存量文档降至 64 KB 内并移除体量基线 |
