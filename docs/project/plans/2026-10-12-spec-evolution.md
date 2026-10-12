# spec-evolution 机械化演进回路技能实现计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-SPEC-EVOLUTION-2026
> - **当前版本**: V1.1.0
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
> - **状态**: 已交付（Task 1~7 全部完成，待 P3.5 独立终审）
> - **隔离分支**: `feature/spec-evolution`（P3 起用，基点 `0306f37`）
> - **需求确认文档**: [RFC-0004 spec-evolution 演进回路](../../proposals/RFC-0004-spec-evolution.md)（状态 **Accepted** · V0.3.0 · 已定案）
> - **技术调研备忘录**: 豁免（P0.5 未触发——`N-4` 明令零第三方依赖、纯 `python3` 标准库 + 既有 `pytest` 约定，无选型空间；宿主能力边界已在 RFC-0004 §3 随方案拷问完成）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`（已被 `.gitignore` 忽略）

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语（或经 `goal-state-tracker.sh` 写入本文件检查点），不另建并行状态文件；本文件的复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P3.5（7 个 Task 全部交付完毕，待派发 `dual-round-review` 独立终审；通过后进入 P5 交付）
- **当前活跃子任务**: 无（Task 1~7 已全部完成并提交，含执行期 8 处设计稿缺陷修正 D-1~D-8）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 1/5
- **最后一次验证状态**: Task 6 终局门禁实测——`python3 -m pytest skills/ -q` → **374 passed**；`check-doc-links.py --root docs` → 68 文件断链 **0**；`audit-doc-health.py` → **PASS**；判定器自证 `spec-evolution` **零 finding**（全仓 findings 11 条 / HIGH+BLOCKER 3 条，均属既有技能的历史缺口）
- **最新有效提交**: `95af3f1`
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
5. **退出码语义**：`0` = 无 finding（CLEAN）；`1` = 有 finding；`2` = 用法或输入错误。**无第四种取值。**（依据：Python `argparse` 的 `parser.error()` 即 `sys.exit(2)` 的既有惯例，叠加本仓库 `manage-doc-index.py` 文档化的 0/1 二值语义。**说明**：RFC-0004 `DK-4` 称此语义「与 `taste-driven-designer` 既有脚本一致」，但该技能 `scripts/` 下**仅有一个 `generate-seed.sh`**，无 `.py` 脚本可援引——本计划改以 `argparse` 惯例与仓库 0/1 语义为据，DK-4 的引用出处属误记，P4 回写修正。）
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

**不适用**（结构性排除，详见 [references/checks-spec.md](references/checks-spec.md) §4）：
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
echo "exit=$?"        # 0 = 无 finding (CLEAN)；1 = 有 finding；2 = 用法/输入错误
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
| `0` | 无 finding（CLEAN） |
| `1` | 有 finding |
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

**Files:**
- Create: `skills/spec-evolution/scripts/collect-facts.py`
- Create: `skills/spec-evolution/tests/conftest.py`
- Create: `skills/spec-evolution/tests/test_collect_facts.py`

**Interfaces:**
- Consumes: `skills/spec-evolution/references/baseline.json` 的 `root_prompt.{lines,bytes}`（Task 1 产出）
- Produces:
  - CLI `python3 collect-facts.py [--repo-root PATH] [--out FILE] [--no-gates] [--skills a,b]`，退出码 `0`/`2`
  - `facts.json` 完整 schema（**Task 3 的 `judge.py` 按此消费，键名不得改动**）：

```
schema_version   str   固定 "1.0"
generated_at     str   ISO8601 带时区
repo_root        str   绝对路径
repo_head        str   git rev-parse --short HEAD，非 git 仓库时为 null
gates            obj|null   null 当且仅当 --no-gates；否则 4 个键
                          pytest/check_doc_links/audit_doc_health/cross_skill_links
                          每键 {cmd: str, exit_code: int, summary: str}
skills           array  按 name 升序
  name                str
  dirs                [str]  技能目录下顶层条目名，升序
  has_skill_md        bool
  has_tests           bool   tests/ 存在且含 test_*.py
  test_files          [str]  相对技能根的测试文件名，升序
  has_references      bool
  has_scripts         bool
  has_templates       bool
  empty_surface_dirs  [str]  references/scripts/templates 中「存在但为空」者，升序
  design_doc          str|null  仓库相对路径
  frontmatter_chars   int    frontmatter 正文（不含 --- 行）字符数；无 frontmatter 为 0
  description_chars   int    description 值字符数（去引号）；缺失为 0
  max_file_lines      int    技能内被扫描文件的最大行数
  oversized_files     [str]  行数 > 1000 的仓库相对路径，升序
  cross_skill_links   [str]  "skills/<n>/<file>:<line>"，升序
  registrations       obj    cross_skill_names/docs_index/readme/collection → bool
root_prompt      obj   {path, lines, bytes, baseline:{lines,bytes}, headings:[str]}
```

- [ ] **Step 1: 写失败测试——`tests/conftest.py`（合成仓库夹具）**

```python
"""spec-evolution 测试夹具：在 tmp_path 中合成一个最小可审计仓库。

不使用任何第三方依赖；所有夹具均为纯 `pathlib` 文件写入。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
COLLECT = REPO_ROOT / "skills" / "spec-evolution" / "scripts" / "collect-facts.py"
JUDGE = REPO_ROOT / "skills" / "spec-evolution" / "scripts" / "judge.py"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


DEFAULT_AGENTS_MD = (
    "# SYSTEM RULES\n"
    "\n"
    "## 3. 基础工程规范与防御底线 (Engineering Invariants)\n"
    "\n"
    "### 精准修改与代码卫生\n"
    "\n"
    "### 工具链与环境防御 (Read-Modify-Verify)\n"
    "\n"
    "### 质量门槛 (Definition of Done)\n"
    "\n"
    "正文。\n"
)


def make_skill_md(name: str, description: str, extra: str = "license: MIT") -> str:
    return f"---\nname: {name}\ndescription: {description}\n{extra}\n---\n\n# {name}\n\n正文。\n"


def build_repo(root: Path, *, skill_description: str = "Use when testing.",
               agents_md: str = DEFAULT_AGENTS_MD) -> Path:
    """合成一个含 1 个技能（demo）的最小仓库，且 demo 满足全部判据。

    `agents_md` 默认镜像真实 `contexts/AGENTS.md` §3 的 `###` 标题层级
    （精准修改与代码卫生 / 工具链与环境防御 / 质量门槛），以便 C-01/C-02 的
    `[RULE:§3-质量门槛]` 与 C-06 的 `[RULE:§3-精准修改与代码卫生]` 锚点可解析；
    传入精简版本可用于断言锚点校验失败路径。
    """
    write(root / "contexts" / "AGENTS.md", agents_md)
    write(root / "skills" / "demo" / "SKILL.md", make_skill_md("demo", skill_description))
    write(root / "skills" / "demo" / "references" / "notes.md", "# notes\n")
    write(root / "skills" / "demo" / "scripts" / "run.sh", "#!/bin/sh\nexit 0\n")
    write(root / "skills" / "demo" / "templates" / "tpl.md", "# tpl\n")
    write(root / "skills" / "demo" / "tests" / "test_demo.py", "def test_ok():\n    assert True\n")
    write(root / "docs" / "explanation" / "architecture" / "demo-design.md", "# demo design\n")
    write(root / "docs" / "index.md", "| demo | [demo 规程](../skills/demo/SKILL.md) |\n")
    write(root / "README.md", "| **`demo`** | [`skills/demo`](./skills/demo/SKILL.md) |\n")
    write(root / "tools" / "skills-manager" / "collections" / "cr-agent-arsenal.json",
          json.dumps({"skills": [{"source": "x", "mode": "all", "names": ["demo"]}]}, indent=2) + "\n")
    write(root / "skills" / "_shared" / "tests" / "test_cross_skill_links.py",
          'SKILL_NAMES = [\n    "demo",\n]\n\n\ndef test_ok():\n    assert True\n')
    # 门禁桩：让合成仓库能真的跑通四道门禁（GI-6 需要门禁真实执行后才可断言无残留产物）。
    # 这两个桩不放在 skills/<skill>/ 下带 SKILL.md 的目录中，故不会被 discover_skills 识别为技能。
    write(root / "skills" / "doc-governance" / "scripts" / "check-doc-links.py",
          "#!/usr/bin/env python3\nimport sys\n\nsys.exit(0)\n")
    write(root / "skills" / "doc-governance" / "scripts" / "audit-doc-health.py",
          "#!/usr/bin/env python3\nimport sys\n\nsys.exit(0)\n")
    write(root / "skills" / "spec-evolution" / "references" / "baseline.json",
          json.dumps({"root_prompt": {"path": "contexts/AGENTS.md",
                                      "lines": len(agents_md.splitlines()),
                                      "bytes": len(agents_md.encode("utf-8"))}}) + "\n")
    return root


def snapshot(root: Path, skip: set[str] | None = None) -> dict[str, tuple[int, int]]:
    """目录清单：{仓库相对路径: (字节数, mtime_ns)}，用于只读断言。"""
    skip = skip or set()
    out: dict[str, tuple[int, int]] = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if any(rel == s or rel.startswith(s + "/") for s in skip):
            continue
        if "__pycache__" in p.parts or ".git" in p.parts:
            continue
        st = p.stat()
        out[rel] = (st.st_size, st.st_mtime_ns)
    return out


def run_collect(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(COLLECT), "--repo-root", str(root), *args],
        capture_output=True, text=True, timeout=120,
    )


def run_judge(facts: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(JUDGE), "--facts", str(facts), *args],
        capture_output=True, text=True, timeout=120,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    return build_repo(tmp_path / "repo")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -v`
Expected: FAIL —— 采集器脚本尚不存在（`can't open file ... collect-facts.py`）

- [ ] **Step 3: 写 `tests/test_collect_facts.py`**

```python
"""采集器契约测试：只回答「是什么」，只读，schema 稳定。"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import build_repo, run_collect, snapshot, write


def collect_json(root: Path, *args: str) -> dict:
    out = root / "_facts.json"
    r = run_collect(root, "--no-gates", "--out", str(out), *args)
    assert r.returncode == 0, r.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def test_schema_top_level_keys(repo: Path):
    facts = collect_json(repo)
    assert set(facts) == {
        "schema_version", "generated_at", "repo_root", "repo_head",
        "gates", "skills", "root_prompt",
    }
    assert facts["schema_version"] == "1.0"
    assert facts["gates"] is None, "--no-gates 时 gates 必须为 null"


def test_skill_structure_facts(repo: Path):
    skill = collect_json(repo)["skills"][0]
    assert skill["name"] == "demo"
    assert skill["has_skill_md"] is True
    assert skill["has_tests"] is True
    assert skill["test_files"] == ["test_demo.py"]
    assert skill["has_references"] and skill["has_scripts"] and skill["has_templates"]
    assert skill["empty_surface_dirs"] == []
    assert skill["design_doc"] == "docs/explanation/architecture/demo-design.md"
    assert skill["max_file_lines"] >= 1
    assert skill["oversized_files"] == []
    assert skill["cross_skill_links"] == []


def test_description_chars_counts_value_only(repo: Path):
    desc = "Use when testing."
    skill = collect_json(repo)["skills"][0]
    assert skill["description_chars"] == len(desc), "description_chars 只计值，不含 'description: ' 前缀"
    assert skill["frontmatter_chars"] > len(desc), "frontmatter_chars 计整个 frontmatter 正文"


def test_quoted_description_value_is_unwrapped(tmp_path: Path):
    root = build_repo(tmp_path / "repo2", skill_description='"Use when quoted."')
    skill = collect_json(root)["skills"][0]
    assert skill["description_chars"] == len("Use when quoted.")


def test_missing_surfaces_and_tests(tmp_path: Path):
    root = build_repo(tmp_path / "repo3")
    for rel in ("references", "scripts", "templates", "tests"):
        target = root / "skills" / "demo" / rel
        for f in sorted(target.rglob("*"), reverse=True):
            f.unlink() if f.is_file() else f.rmdir()
        target.rmdir()
    skill = collect_json(root)["skills"][0]
    assert skill["has_tests"] is False
    assert [skill["has_references"], skill["has_scripts"], skill["has_templates"]] == [False, False, False]


def test_empty_surface_dir_is_reported(tmp_path: Path):
    root = build_repo(tmp_path / "repo4")
    (root / "skills" / "demo" / "references" / "notes.md").unlink()
    skill = collect_json(root)["skills"][0]
    assert skill["empty_surface_dirs"] == ["references"]


def test_oversized_file_is_reported(tmp_path: Path):
    root = build_repo(tmp_path / "repo5")
    write(root / "skills" / "demo" / "references" / "big.md", "x\n" * 1001)
    skill = collect_json(root)["skills"][0]
    assert skill["oversized_files"] == ["skills/demo/references/big.md"]
    assert skill["max_file_lines"] == 1001


def test_cross_skill_link_is_detected(tmp_path: Path):
    root = build_repo(tmp_path / "repo6")
    write(root / "skills" / "demo" / "references" / "link.md",
          "见 [demo](../demo/SKILL.md) 与 [other](../../other/SKILL.md)\n")
    skill = collect_json(root)["skills"][0]
    assert any("link.md" in hit for hit in skill["cross_skill_links"])


def test_inline_code_link_is_not_flagged(tmp_path: Path):
    root = build_repo(tmp_path / "repo7")
    write(root / "skills" / "demo" / "references" / "ok.md", "示例 `[x](../demo/SKILL.md)` 不算链接\n")
    skill = collect_json(root)["skills"][0]
    assert skill["cross_skill_links"] == []


def test_registration_surfaces(repo: Path):
    reg = collect_json(repo)["skills"][0]["registrations"]
    assert reg == {"cross_skill_names": True, "docs_index": True, "readme": True, "collection": True}


def test_registration_gap_detected(tmp_path: Path):
    root = build_repo(tmp_path / "repo8")
    write(root / "tools" / "skills-manager" / "collections" / "cr-agent-arsenal.json",
          json.dumps({"skills": [{"source": "x", "mode": "all", "names": []}]}) + "\n")
    assert collect_json(root)["skills"][0]["registrations"]["collection"] is False


def test_root_prompt_facts_and_headings(repo: Path):
    rp = collect_json(repo)["root_prompt"]
    assert rp["path"] == "contexts/AGENTS.md"
    assert rp["lines"] == 11
    assert rp["baseline"]["lines"] == 11
    assert rp["headings"][0] == "# SYSTEM RULES"
    assert "## 3. 基础工程规范与防御底线 (Engineering Invariants)" in rp["headings"]
    assert "### 精准修改与代码卫生" in rp["headings"]
    assert "### 工具链与环境防御 (Read-Modify-Verify)" in rp["headings"]
    assert "### 质量门槛 (Definition of Done)" in rp["headings"]


def test_skill_filter_narrows_scope(tmp_path: Path):
    root = build_repo(tmp_path / "repo9")
    write(root / "skills" / "other" / "SKILL.md", "---\nname: other\ndescription: x\n---\n\n# other\n")
    names = [s["name"] for s in collect_json(root, "--skills", "demo")["skills"]]
    assert names == ["demo"]


def test_collector_is_read_only(repo: Path):
    before = snapshot(repo)
    out = repo / "_facts.json"
    r = run_collect(repo, "--no-gates", "--out", str(out))
    assert r.returncode == 0, r.stderr
    after = snapshot(repo, skip={"_facts.json"})
    assert after == before, "采集器在 --no-gates 下不得改动仓库内任何文件"


def test_missing_repo_root_exits_2(tmp_path: Path):
    r = run_collect(tmp_path / "nope", "--no-gates")
    assert r.returncode == 2, "用法/输入错误须以退出码 2 终止"
```

- [ ] **Step 4: 运行测试确认失败**

Run: `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -v`
Expected: FAIL —— `collect-facts.py` 不存在

- [ ] **Step 5: 写 `scripts/collect-facts.py`**

```python
#!/usr/bin/env python3
"""spec-evolution 事实采集器（只读）。

只回答「是什么」，不回答「好不好」：把技能与根提示词的客观状态导出为结构化
`facts.json`，供 `judge.py` 做确定性判定。本脚本不含任何判据逻辑，也不修改
仓库内任何文件（`--out` 指定的输出路径除外）。

用法:
    python3 collect-facts.py [--repo-root PATH] [--out FILE] [--no-gates] [--skills a,b]

退出码:
    0 = 成功；2 = 用法或输入错误
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"

SKILLS_DIRNAME = "skills"
NON_SKILL_DIRS = {"_shared"}
SURFACE_DIRS = ("references", "scripts", "templates")
ARCH_RELDIR = Path("docs/explanation/architecture")
ROOT_PROMPT_REL = Path("contexts/AGENTS.md")
COLLECTION_REL = Path("tools/skills-manager/collections/cr-agent-arsenal.json")
CROSS_TEST_REL = Path("skills/_shared/tests/test_cross_skill_links.py")
INDEX_REL = Path("docs/index.md")
README_REL = Path("README.md")
BASELINE_REL = Path("skills/spec-evolution/references/baseline.json")

LINE_LIMIT = 1000
GATE_TIMEOUT = 300
SCANNED_SUFFIXES = {".py", ".sh", ".md", ".json", ".yaml", ".yml", ".txt", ".cfg", ".toml"}

FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
DESC_RX = re.compile(r"^description:[ \t]*(.*)$", re.MULTILINE)
NAME_RX = re.compile(r"^name:[ \t]*(.*)$", re.MULTILINE)
SKILL_NAMES_RX = re.compile(r"SKILL_NAMES\s*=\s*\[(.*?)\]", re.DOTALL)
STRING_RX = re.compile(r"[\"']([^\"']+)[\"']")
HEADING_RX = re.compile(r"^(#{1,3})[ \t]+(.*?)[ \t]*$", re.MULTILINE)

LINK_RX = re.compile(r"\]\(([^)]+)\)")
INLINE_CODE_RX = re.compile(r"`[^`]*`")
COMMAND_EXAMPLE_RX = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")

# 与 skills/_shared/tests/test_cross_skill_links.py 同源的跨技能链接正则
CROSS_RX_TEMPLATE = r"(?:^|[\s(=/\"'>、，（])(?:[^)\s\"'<>]*?[\\/])*(?<![.])(?:{names})[\\/]"

GATES = (
    ("pytest", ["python3", "-B", "-m", "pytest", "skills/", "-q", "-p", "no:cacheprovider"]),
    ("check_doc_links",
     ["python3", "skills/doc-governance/scripts/check-doc-links.py", "--root", "docs"]),
    ("audit_doc_health",
     ["python3", "skills/doc-governance/scripts/audit-doc-health.py"]),
    ("cross_skill_links",
     ["python3", "-B", "-m", "pytest", "skills/_shared/tests/test_cross_skill_links.py",
      "-q", "-p", "no:cacheprovider"]),
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def line_count(path: Path) -> int:
    return len(read_text(path).splitlines())


def strip_fences(text: str) -> str:
    """剥离围栏代码块（与 test_cross_skill_links.py 同源语义）。"""
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def strip_inline_code(line: str) -> str:
    return INLINE_CODE_RX.sub("", line)


def unquote(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_frontmatter(text: str) -> tuple[int, int, str | None]:
    """返回 (frontmatter_chars, description_chars, name)。"""
    m = FRONTMATTER_RX.match(text)
    if not m:
        return 0, 0, None
    body = m.group(1)
    name_m = NAME_RX.search(body)
    desc_m = DESC_RX.search(body)
    desc = unquote(desc_m.group(1)) if desc_m else ""
    name = unquote(name_m.group(1)) if name_m else None
    return len(body), len(desc), name


def discover_skills(repo: Path) -> list[str]:
    """技能 = `skills/` 下含 `SKILL.md` 的目录。

    要求 `SKILL.md` 存在是刻意的：`skills/spec-evolution/references/baseline.json`
    等旁挂资产所在的目录不应被误认为一个技能。
    """
    root = repo / SKILLS_DIRNAME
    if not root.is_dir():
        return []
    return sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and p.name not in NON_SKILL_DIRS and not p.name.startswith(".")
        and (p / "SKILL.md").is_file()
    )


def scan_cross_skill_links(skill_dir: Path, repo: Path, names: list[str]) -> list[str]:
    if not names:
        return []
    pattern = re.compile(
        CROSS_RX_TEMPLATE.format(names="|".join(re.escape(n) for n in names)), re.IGNORECASE
    )
    hits: list[str] = []
    for md in sorted(skill_dir.rglob("*.md")):
        if "__pycache__" in md.parts:
            continue
        for i, line in enumerate(strip_fences(read_text(md)).splitlines(), 1):
            if COMMAND_EXAMPLE_RX.match(line) and "](" not in line:
                continue
            if pattern.search(strip_inline_code(line)):
                hits.append(f"{md.relative_to(repo).as_posix()}:{i}")
    return hits


def scan_files(skill_dir: Path, repo: Path) -> tuple[int, list[str]]:
    max_lines, oversized = 0, []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        if p.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        n = line_count(p)
        max_lines = max(max_lines, n)
        if n > LINE_LIMIT:
            oversized.append(p.relative_to(repo).as_posix())
    return max_lines, oversized


def parse_skill_names_from_test(path: Path) -> list[str]:
    m = SKILL_NAMES_RX.search(read_text(path))
    return STRING_RX.findall(m.group(1)) if m else []


def parse_collection_names(path: Path) -> list[str]:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return []
    names: list[str] = []
    for entry in data.get("skills", []):
        names.extend(entry.get("names", []))
    return names


def collect_skill(repo: Path, name: str, all_names: list[str],
                  registered: dict[str, list[str]]) -> dict:
    skill_dir = repo / SKILLS_DIRNAME / name
    entries = sorted(p.name for p in skill_dir.iterdir()) if skill_dir.is_dir() else []
    tests_dir = skill_dir / "tests"
    test_files = sorted(
        p.name for p in tests_dir.glob("test_*.py")
    ) if tests_dir.is_dir() else []

    empty_dirs = [d for d in SURFACE_DIRS
                  if (skill_dir / d).is_dir() and not any((skill_dir / d).iterdir())]

    design_doc = None
    candidate = repo / ARCH_RELDIR / f"{name}-design.md"
    if candidate.is_file():
        design_doc = candidate.relative_to(repo).as_posix()

    fm_chars, desc_chars = 0, 0
    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        fm_chars, desc_chars, _ = parse_frontmatter(read_text(skill_md))

    max_lines, oversized = scan_files(skill_dir, repo)
    idx_text = read_text(repo / INDEX_REL)
    readme_text = read_text(repo / README_REL)

    return {
        "name": name,
        "dirs": entries,
        "has_skill_md": skill_md.is_file(),
        "has_tests": bool(test_files),
        "test_files": test_files,
        "has_references": (skill_dir / "references").is_dir(),
        "has_scripts": (skill_dir / "scripts").is_dir(),
        "has_templates": (skill_dir / "templates").is_dir(),
        "empty_surface_dirs": empty_dirs,
        "design_doc": design_doc,
        "frontmatter_chars": fm_chars,
        "description_chars": desc_chars,
        "max_file_lines": max_lines,
        "oversized_files": oversized,
        "cross_skill_links": scan_cross_skill_links(skill_dir, repo, all_names),
        "registrations": {
            "cross_skill_names": name in registered["cross_skill_names"],
            "docs_index": f"skills/{name}/SKILL.md" in idx_text,
            "readme": f"skills/{name}" in readme_text,
            "collection": name in registered["collection"],
        },
    }


def collect_root_prompt(repo: Path) -> dict:
    path = repo / ROOT_PROMPT_REL
    text = read_text(path)
    baseline = {"lines": 0, "bytes": 0}
    baseline_path = repo / BASELINE_REL
    if baseline_path.is_file():
        try:
            baseline = json.loads(read_text(baseline_path))["root_prompt"]
            baseline = {"lines": baseline["lines"], "bytes": baseline["bytes"]}
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return {
        "path": ROOT_PROMPT_REL.as_posix(),
        "lines": len(text.splitlines()),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "baseline": baseline,
        "headings": [f"{m.group(1)} {m.group(2)}" for m in HEADING_RX.finditer(text)],
    }


def collect_gates(repo: Path) -> dict:
    gates = {}
    for key, cmd in GATES:
        try:
            proc = subprocess.run(cmd, cwd=str(repo), capture_output=True,
                                  text=True, timeout=GATE_TIMEOUT)
            exit_code, stdout = proc.returncode, proc.stdout
        except subprocess.TimeoutExpired:
            exit_code, stdout = 124, f"TIMEOUT after {GATE_TIMEOUT}s"
        except OSError as exc:
            exit_code, stdout = 125, f"OSError: {exc}"
        lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
        gates[key] = {
            "cmd": " ".join(cmd),
            "exit_code": exit_code,
            "summary": lines[-1] if lines else "",
        }
    return gates


def git_head(repo: Path) -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=str(repo), capture_output=True, text=True, timeout=30)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def build_facts(repo: Path, *, with_gates: bool, only: list[str] | None) -> dict:
    all_names = discover_skills(repo)
    selected = [n for n in all_names if only is None or n in only]
    registered = {
        "cross_skill_names": parse_skill_names_from_test(repo / CROSS_TEST_REL),
        "collection": parse_collection_names(repo / COLLECTION_REL),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo_root": str(repo),
        "repo_head": git_head(repo),
        "gates": collect_gates(repo) if with_gates else None,
        "skills": [collect_skill(repo, n, all_names, registered) for n in selected],
        "root_prompt": collect_root_prompt(repo),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="collect-facts.py",
        description="spec-evolution 事实采集器（只读）：导出技能与根提示词的客观状态。",
    )
    ap.add_argument("--repo-root", default=".", help="仓库根目录（默认当前目录）")
    ap.add_argument("--out", default=None, help="facts.json 输出路径；省略则打印到 stdout")
    ap.add_argument("--no-gates", action="store_true", help="跳过 S1 门禁事实采集（纯文件系统扫描）")
    ap.add_argument("--skills", default=None, help="逗号分隔的技能名子集；省略为全部")
    args = ap.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    if not repo.is_dir():
        print(f"❌ repo-root 不存在或不是目录: {repo}", file=sys.stderr)
        return 2
    if not (repo / SKILLS_DIRNAME).is_dir():
        print(f"❌ 仓库根下缺少 {SKILLS_DIRNAME}/ 目录: {repo}", file=sys.stderr)
        return 2

    only = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else None
    facts = build_facts(repo, with_gates=not args.no_gates, only=only)
    payload = json.dumps(facts, ensure_ascii=False, indent=2, sort_keys=False)

    if args.out:
        out = Path(args.out)
        if not out.parent.is_dir():
            print(f"❌ 输出目录不存在: {out.parent}", file=sys.stderr)
            return 2
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"✅ 事实已导出: {out}（技能 {len(facts['skills'])} 个，门禁 {'已采集' if facts['gates'] else '已跳过'}）")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: 运行测试确认通过**

Run: `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -v`
Expected: PASS（全部用例绿）

- [ ] **Step 7: 对真实仓库冒烟，核对 F-1~F-9 事实**

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --out /tmp/facts.json
python3 - <<'PY'
import json
f = json.load(open('/tmp/facts.json'))
assert len(f['skills']) == 7, f"技能数应为 7，实际 {len(f['skills'])}"
by = {s['name']: s for s in f['skills']}
print('dual-round-review desc =', by['dual-round-review']['description_chars'], '(期望 738)')
print('clarification-protocol desc =', by['clarification-protocol']['description_chars'], '(期望 623)')
print('agy has_tests =', by['agy-delegation-workflow']['has_tests'], '(期望 False)')
print('doc-governance oversized =', by['doc-governance']['oversized_files'])
print('clarification registrations =', by['clarification-protocol']['registrations'])
print('root_prompt =', f['root_prompt']['lines'], f['root_prompt']['bytes'])
PY
```

期望：技能数 7；`dual-round-review` = 738；`clarification-protocol` = 623；`agy-delegation-workflow` `has_tests` = False；`doc-governance` `oversized_files` 含 `skills/doc-governance/tests/test_doc_governance_scripts.py`；`clarification-protocol` 的 `collection` 为 `False`（**F-9**）；`root_prompt` = 97 / 10746。

- [ ] **Step 8: 提交**

```bash
git add skills/spec-evolution/scripts/collect-facts.py skills/spec-evolution/tests/
git commit -m "feat(spec-evolution): 事实采集器 collect-facts.py 与契约测试

Task 2/7：只读采集 S1 门禁事实 / S2 结构事实 / S3 注册事实 → facts.json。
门禁调用统一加 -B 与 -p no:cacheprovider，保证只读不变式（GI-6）。
真实仓库冒烟核对 F-1/F-2/F-4/F-8/F-9 事实值。"
```

---

#### Task 3: 判定器 `judge.py`、报告模板与判定契约测试

**Files**
- Create: `skills/spec-evolution/scripts/judge.py`
- Create: `skills/spec-evolution/templates/evolution-report.md`
- Create: `skills/spec-evolution/tests/test_judge_contract.py`
- Modify: `skills/spec-evolution/tests/conftest.py`（仅**追加** `base_facts()` 便利函数，不改既有签名）

**Goal**：把 `facts.json` 确定性映射为 finding 列表与演进报告；实现三锚点存在性硬门禁（GI-3）与人类裁决区留白（GI-4）。

> **执行偏差记录 (Deviation Log) —— 2026-10-12 P3 执行期实测修正**
>
> 本任务块下方内嵌的代码为设计稿；实际实现以 `skills/spec-evolution/scripts/judge.py` 为准。执行期实测发现 5 处设计稿缺陷，已按下表修正（修正同时回写本计划与 `references/checks-spec.md`）：
>
> | # | 缺陷 | 修正 | 依据 |
> | :--- | :--- | :--- | :--- |
> | D-1 | 夹具 `DEFAULT_AGENTS_MD` 使用了 `### 禁止占位符与规模控制 (No Placeholders / Size Limits)` 标题，该标题在真实 `contexts/AGENTS.md` 中**不存在**（真实 §3 的 H3 只有 精准修改与代码卫生 / 工具链与环境防御 / 质量门槛；「禁止占位符与规模控制」是前者下的**加粗条目**） | 夹具标题改为 `### 工具链与环境防御 (Read-Modify-Verify)`，镜像真实层级（行数仍为 11，故 `test_root_prompt_facts_and_headings` 的 `lines == 11` 断言不变） | 实测 `grep -n '^###' contexts/AGENTS.md` |
> | D-2 | `RULE_SIZE = "[RULE:§3-禁止占位符与规模控制]"` 在真实仓库**无法解析**，导致 `judge.py` 恒以退出码 2 拒绝产出（工具不可用） | 改为 `"[RULE:§3-精准修改与代码卫生]"` | `references/anchor-contract.md:13` 早已声明该锚点示例；RFC-0004 §3.4 的锚点契约是**标题树**，不含加粗条目 |
> | D-3 | 设计稿按**嵌套** schema 消费 facts（`sk["paths"]["has_tests"]`、`sk["missing_surfaces"]`、`sk["registration"][s]["registered"]`），与 Task 2 已冻结的**扁平** schema 不一致 | `judge.py` 改按扁平 schema 消费（`sk["has_tests"]`；缺失面由 `has_references/has_scripts/has_templates` 推导；`sk["registrations"][s]` 为布尔），并新增 `REGISTRATION_SURFACES` 常量把 4 个注册面映射到 `[REPO:*]` 锚点路径 | Task 2 Interfaces 明示「`facts.json` schema 键名不得改动」 |
> | D-4 | `--no-gates` 时 `facts["gates"] is None`，设计稿的 `sorted(facts["gates"].items())` 抛 `AttributeError` | `build_findings` 与 `render_report` 均改用 `facts.get("gates") or {}` | 实测 `test_clean_repo_yields_no_findings` 路径 |
> | D-5 | `load_facts` 用 `raise SystemExit("❌ …")` 表达输入错误，但 `SystemExit` 携带非空字符串时退出码为 **1**，与契约「2 = 用法或输入错误」冲突 | 新增 `FactsError` 异常，`main()` 捕获后 `return 2` | RFC-0004 §3.3 退出码契约 |
>
> 另：`test_report_and_json_written_to_requested_paths` 的旧注记已过时（`_run` 恒传 `--json`，该断言实际检查的是**未被请求**的路径不存在），实现时按新注记执行。

- [ ] **Step 1: 写入 `skills/spec-evolution/scripts/judge.py`**

```python
#!/usr/bin/env python3
"""spec-evolution 判定器 judge.py —— 把 facts.json 转成结构化 finding 与演进报告。

确定性、零 LLM、零网络。判定语义与退出码见 skills/spec-evolution/references/checks-spec.md。

退出码：
  0 = 无 BLOCKER / HIGH
  1 = 存在 HIGH 或 BLOCKER
  2 = 输入无效、facts 结构不合法、或 finding 锚点不可解析
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
SEVERITY_ORDER = {"BLOCKER": 0, "HIGH": 1, "MID": 2}
DESC_SOFT_LIMIT = 500
DESC_HARD_LIMIT = 1024
REQUIRED_TOP_KEYS = ("repo_root", "skills", "gates", "root_prompt")

RULE_DOD = "[RULE:§3-质量门槛]"
RULE_SIZE = "[RULE:§3-精准修改与代码卫生]"

GATE_ANCHORS = {
    "pytest": "skills/",
    "check_doc_links": "skills/doc-governance/scripts/check-doc-links.py",
    "audit_doc_health": "skills/doc-governance/scripts/audit-doc-health.py",
    "cross_skill_links": "skills/_shared/tests/test_cross_skill_links.py",
}

SKILL_ANCHOR_RX = re.compile(r"^\[SKILL:([^/\]]+)/([^\]:]+)(?::(\d+))?\]$")
REPO_ANCHOR_RX = re.compile(r"^\[REPO:([^\]:]+)(?::(\d+))?\]$")
RULE_ANCHOR_RX = re.compile(r"^\[RULE:§(\d+)-(.+)\]$")
H2_RX = re.compile(r"^##\s+(\d+)\.\s*(.*)$")
H3_RX = re.compile(r"^###\s+(.*)$")

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "evolution-report.md"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def validate_anchor(anchor: str, repo_root: Path, headings: list) -> str | None:
    """锚点可解析返回 None，否则返回人可读的失败原因。"""
    m = SKILL_ANCHOR_RX.match(anchor)
    if m:
        name, rel, line = m.group(1), m.group(2), m.group(3)
        target = repo_root / "skills" / name / rel
        if not target.exists():
            return f"技能锚点文件不存在: skills/{name}/{rel}"
        if line is not None and int(line) > _count_lines(target):
            return f"技能锚点行号越界: skills/{name}/{rel}:{line}（共 {_count_lines(target)} 行）"
        return None
    m = REPO_ANCHOR_RX.match(anchor)
    if m:
        rel, line = m.group(1), m.group(2)
        target = repo_root / rel
        if not target.exists():
            return f"仓库锚点路径不存在: {rel}"
        if line is not None and int(line) > _count_lines(target):
            return f"仓库锚点行号越界: {rel}:{line}（共 {_count_lines(target)} 行）"
        return None
    m = RULE_ANCHOR_RX.match(anchor)
    if m:
        section, title = m.group(1), _norm(m.group(2))
        current = None
        for heading in headings:
            h2 = H2_RX.match(heading)
            if h2:
                current = h2.group(1)
                continue
            h3 = H3_RX.match(heading)
            if h3 and current == section and _norm(h3.group(1)).startswith(title):
                return None
        return f"根提示词锚点无对应标题: {anchor}"
    return f"锚点格式非法: {anchor}"


def _mk(criterion, severity, skill, anchor, rule, evidence_cmd, observed, expected, message):
    return {
        "id": None,
        "criterion": criterion,
        "severity": severity,
        "skill": skill,
        "anchor": anchor,
        "rule": rule,
        "evidence_cmd": evidence_cmd,
        "observed": observed,
        "expected": expected,
        "message": message,
    }


def build_findings(facts: dict) -> list:
    out: list = []

    for key, info in sorted(facts["gates"].items()):
        if info.get("exit_code") != 0:
            out.append(_mk(
                "C-09", "BLOCKER", "<repo>",
                f"[REPO:{GATE_ANCHORS.get(key, 'skills/')}]", None, info.get("cmd", ""),
                f"exit_code={info.get('exit_code')}", "exit_code == 0",
                "既有门禁非零退出，交付基线不成立。"))

    for sk in facts["skills"]:
        name = sk["name"]
        skill_anchor = f"[SKILL:{name}/SKILL.md]"

        if not sk["paths"]["has_tests"]:
            out.append(_mk(
                "C-01", "HIGH", name, skill_anchor, RULE_DOD,
                f"ls skills/{name}/tests", "目录不存在", "存在 tests/ 且至少 1 个 test_*.py",
                "技能缺少契约测试，其判据不可机械回归。"))

        if not sk["design_doc"]:
            out.append(_mk(
                "C-02", "MID", name, skill_anchor, RULE_DOD,
                f"test -f docs/explanation/architecture/{name}-design.md", "文件不存在",
                "存在架构设计书", "技能无架构设计书，架构决策不可追溯。"))

        if sk["missing_surfaces"] or sk["empty_surface_dirs"]:
            parts = []
            if sk["missing_surfaces"]:
                parts.append("缺失: " + ", ".join(sk["missing_surfaces"]))
            if sk["empty_surface_dirs"]:
                parts.append("为空: " + ", ".join(sk["empty_surface_dirs"]))
            out.append(_mk(
                "C-03", "MID", name, skill_anchor, None, f"ls skills/{name}",
                "；".join(parts), "references/scripts/templates 存在且非空",
                "技能交付面不完整。"))

        chars = sk["description_chars"]
        if chars >= DESC_HARD_LIMIT:
            out.append(_mk(
                "C-05", "HIGH", name, skill_anchor, None,
                f"python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills {name}",
                f"{chars} 字符", f"< {DESC_HARD_LIMIT} 字符（规范硬限）",
                "description 超过规范硬限，技能会被宿主静默丢弃。"))
        elif chars > DESC_SOFT_LIMIT:
            out.append(_mk(
                "C-04", "MID", name, skill_anchor, None,
                f"python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills {name}",
                f"{chars} 字符", f"≤ {DESC_SOFT_LIMIT} 字符（建议值）",
                "description 超出仓库建议上限，常驻注入成本偏高。"))

        for rel in sk["oversized_files"]:
            short = rel.split("/", 2)[2] if rel.count("/") >= 2 else rel
            out.append(_mk(
                "C-06", "MID", name, f"[SKILL:{name}/{short}]", RULE_SIZE,
                f"wc -l {rel}", "超过 1000 行", "单文件 ≤ 1000 行",
                "单文件越过规模红线，拆分前不得新增内容。"))

        for surface, info in sorted(sk["registration"].items()):
            if not info["registered"]:
                out.append(_mk(
                    "C-07", "HIGH", name, f"[REPO:{info['path']}]", None,
                    f"grep -nF '{name}' {info['path']}", info["detail"],
                    "注册面已登记", f"注册面 {surface} 缺登记，技能无法被发现。"))

        for link in sk["cross_skill_links"]:
            short = link.split("/", 2)[2] if link.count("/") >= 2 else link
            out.append(_mk(
                "C-08", "HIGH", name, f"[SKILL:{name}/{short}]", None,
                "python3 -m pytest skills/_shared/tests/test_cross_skill_links.py -q",
                link, "无跨技能相对链接", "跨技能相对链接在单技能安装后断链。"))

    rp = facts["root_prompt"]
    baseline = rp.get("baseline") or {}
    grew = [
        f"{key}: {baseline[key]} -> {rp[key]}"
        for key in ("lines", "bytes")
        if key in baseline and rp[key] > baseline[key]
    ]
    if grew:
        out.append(_mk(
            "C-10", "MID", "<repo>", f"[REPO:{rp['path']}]", None,
            f"wc -l {rp['path']}", "；".join(grew), "不超过 baseline",
            "根提示词净增长，须同提交给出等量删减或不可压缩理由。"))

    out.sort(key=lambda f: (
        SEVERITY_ORDER[f["severity"]], f["skill"], f["criterion"],
        f["anchor"], f["evidence_cmd"], f["observed"]))
    for i, f in enumerate(out, 1):
        f["id"] = f"F-{i:02d}"
    return out


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(facts: dict, findings: list) -> str:
    gates = facts["gates"]
    failed = [(k, v) for k, v in sorted(gates.items()) if v.get("exit_code") != 0]
    if failed:
        lines = ["| 门禁 | 证据命令 | 退出码 | 摘要 |", "| :--- | :--- | :--- | :--- |"]
        for key, info in failed:
            lines.append("| {} | `{}` | {} | {} |".format(
                key, _cell(info.get("cmd", "")), info.get("exit_code"),
                _cell(info.get("summary", ""))))
        blocker_section = "## BLOCKER\n\n" + "\n".join(lines)
    else:
        blocker_section = "## BLOCKER\n\n（无既有门禁失败）"

    rest = [f for f in findings if f["severity"] != "BLOCKER"]
    if rest:
        rows = ["| ID | 判据 | 严重度 | 技能 | 锚点 | 实测 | 期望 | 证据命令 |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
        for f in rest:
            rows.append("| {} | {} | {} | {} | {} | {} | {} | `{}` |".format(
                f["id"], f["criterion"], f["severity"], _cell(f["skill"]),
                _cell(f["anchor"]), _cell(f["observed"]), _cell(f["expected"]),
                _cell(f["evidence_cmd"])))
        findings_table = "\n".join(rows)
    else:
        findings_table = "（无）"

    verdict_rows = ["| ID | 裁决 | 裁决人 | 裁决日期 | 驳回理由 |",
                    "| :--- | :--- | :--- | :--- | :--- |"]
    for f in findings:
        verdict_rows.append(f"| {f['id']} | [ ] 采纳 / [ ] 驳回 | | | |")
    if not findings:
        verdict_rows.append("| — | （无 finding，无需裁决） | | | |")
    verdict_table = "\n".join(verdict_rows)

    if any(f["severity"] == "BLOCKER" for f in findings):
        verdict = "BLOCKER"
    elif any(f["severity"] == "HIGH" for f in findings):
        verdict = "HIGH"
    elif findings:
        verdict = "MID"
    else:
        verdict = "CLEAN"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (template
            .replace("{{DATE}}", (facts.get("generated_at") or "")[:10])
            .replace("{{REPO_HEAD}}", str(facts.get("repo_head") or "unknown"))
            .replace("{{SKILL_COUNT}}", str(len(facts["skills"])))
            .replace("{{CRITERIA_COUNT}}", "10")
            .replace("{{VERDICT}}", verdict)
            .replace("{{BLOCKER_SECTION}}", blocker_section)
            .replace("{{FINDINGS_TABLE}}", findings_table)
            .replace("{{VERDICT_TABLE}}", verdict_table))


def load_facts(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"❌ 找不到 facts 文件: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ facts 不是合法 JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("❌ facts 顶层必须是对象")
    missing = [k for k in REQUIRED_TOP_KEYS if k not in data]
    if missing:
        raise SystemExit("❌ facts 缺少必需键: " + ", ".join(missing))
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="spec-evolution 判定器（确定性、零 LLM）")
    ap.add_argument("--facts", required=True)
    ap.add_argument("--repo-root", default=None,
                    help="锚点解析根；缺省取 facts.repo_root")
    ap.add_argument("--report", default=None, help="演进报告输出路径")
    ap.add_argument("--json", dest="json_out", default=None, help="finding JSON 输出路径")
    args = ap.parse_args(argv)

    facts = load_facts(Path(args.facts))
    findings = build_findings(facts)

    repo_root = Path(args.repo_root or facts["repo_root"])
    headings = facts["root_prompt"].get("headings") or []
    problems = []
    for f in findings:
        for key in ("anchor", "rule"):
            anchor = f.get(key)
            if anchor is None:
                continue
            reason = validate_anchor(anchor, repo_root, headings)
            if reason:
                problems.append(f"{f['id']} {f['criterion']} {key}: {reason}")
    if problems:
        sys.stderr.write("❌ 锚点存在性校验失败（GI-3），拒绝写出任何产物：\n")
        for p in problems:
            sys.stderr.write(f"  - {p}\n")
        return 2

    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_report(facts, findings), encoding="utf-8")
        print(f"✅ 演进报告已写出: {path}")
    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"✅ finding JSON 已写出: {path}")

    blocking = [f for f in findings if f["severity"] in ("BLOCKER", "HIGH")]
    print(f"📊 findings={len(findings)} blocker/high={len(blocking)}")
    for f in blocking:
        print(f"  ⛔ {f['id']} {f['severity']} {f['criterion']} {f['skill']} {f['anchor']}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
```

> **注意**：C-04 / C-05 互斥（`elif`），同一技能不会同时产出两条 description 判据。

- [ ] **Step 2: 写入 `skills/spec-evolution/templates/evolution-report.md`**

````markdown
# spec-evolution 演进报告 · {{DATE}}

- 仓库基线: `{{REPO_HEAD}}`
- 扫描技能数: {{SKILL_COUNT}} | 判据数: {{CRITERIA_COUNT}}
- 判定结论: **{{VERDICT}}**

{{BLOCKER_SECTION}}

## 判据发现 (Findings)

{{FINDINGS_TABLE}}

## 人类裁决 (Human Verdict)

> 本节由人类填写。判定器在此标题处停止写入；任何由模型生成、或预先勾选的裁决内容均视为门禁违规（RFC-0004 §3.7 / GI-4）。

{{VERDICT_TABLE}}
````

- [ ] **Step 3: 向 `skills/spec-evolution/tests/conftest.py` 追加 `base_facts()`**

在文件末尾追加（不改动既有函数签名）：

```python
def base_facts(root: Path) -> dict:
    """在合成仓库上跑一次 `--no-gates` 采集，返回可被测试点状修改的 facts 字典。"""
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))
```

- [ ] **Step 4: 写入 `skills/spec-evolution/tests/test_judge_contract.py`（第一部分：十条判据）**

```python
"""test_judge_contract.py — judge.py 判定契约、锚点硬门禁与报告不变式。"""

import json
from pathlib import Path

from conftest import build_repo, run_collect, run_judge


def _rm(path: Path) -> None:
    for p in sorted(path.rglob("*"), reverse=True):
        p.unlink() if p.is_file() else p.rmdir()
    path.rmdir()


def _facts(root: Path) -> dict:
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def _run(root: Path, facts: dict, tmp_path: Path, *extra):
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    js = tmp_path / "f.json"
    proc = run_judge(src, "--repo-root", str(root), "--json", str(js), *extra)
    data = json.loads(js.read_text(encoding="utf-8")) if js.exists() else None
    return proc, data


def _only(data, criterion):
    hits = [f for f in data if f["criterion"] == criterion]
    assert len(hits) == 1, f"{criterion} 命中 {len(hits)} 条: {data}"
    return hits[0]


def test_clean_repo_yields_no_findings(tmp_path):
    root = build_repo(tmp_path / "repo")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert data == []


def test_c01_missing_tests_is_high(tmp_path):
    root = build_repo(tmp_path / "repo")
    _rm(root / "skills" / "demo" / "tests")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-01")
    assert f["severity"] == "HIGH" and f["skill"] == "demo"
    assert f["anchor"] == "[SKILL:demo/SKILL.md]"
    assert f["rule"] == "[RULE:§3-质量门槛]"


def test_c02_missing_design_doc_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    (root / "docs" / "explanation" / "architecture" / "demo-design.md").unlink()
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-02")
    assert f["severity"] == "MID" and f["rule"] == "[RULE:§3-质量门槛]"


def test_c03_missing_surface_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    _rm(root / "skills" / "demo" / "templates")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-03")
    assert f["severity"] == "MID" and f["observed"] == "缺失: templates"


def test_c04_description_over_soft_limit_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo", skill_description="Use when " + "x" * 500 + ".")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-04")
    assert f["severity"] == "MID" and f["observed"] == "510 字符"


def test_c05_description_over_hard_limit_is_high(tmp_path):
    root = build_repo(tmp_path / "repo", skill_description="Use when " + "x" * 1100 + ".")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-05")
    assert f["severity"] == "HIGH" and f["observed"] == "1110 字符"
    assert not [x for x in data if x["criterion"] == "C-04"], "C-04/C-05 必须互斥"


def test_c06_oversized_file_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    (root / "skills" / "demo" / "references" / "big.md").write_text(
        "行\n" * 1010, encoding="utf-8")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-06")
    assert f["severity"] == "MID"
    assert f["anchor"] == "[SKILL:demo/references/big.md]"
    assert f["rule"] == "[RULE:§3-精准修改与代码卫生]"


def test_c07_registration_gap_is_high(tmp_path):
    root = build_repo(tmp_path / "repo")
    idx = root / "docs" / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8").replace("skills/demo/SKILL.md", ""),
                   encoding="utf-8")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-07")
    assert f["severity"] == "HIGH" and f["anchor"] == "[REPO:docs/index.md]"


def test_c08_cross_skill_link_is_high(tmp_path):
    root = build_repo(tmp_path / "repo")
    (root / "skills" / "demo" / "references" / "link.md").write_text(
        "见 [demo](../demo/SKILL.md) 不算。\n", encoding="utf-8")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-08")
    assert f["severity"] == "HIGH"
    assert f["anchor"].startswith("[SKILL:demo/references/link.md:")


def test_c09_gate_failure_is_blocker(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    proc, data = _run(root, facts, tmp_path)
    assert proc.returncode == 1
    assert data[0]["criterion"] == "C-09" and data[0]["severity"] == "BLOCKER"
    assert data[0]["anchor"] == "[REPO:skills/]"


def test_c10_root_prompt_growth_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["root_prompt"]["lines"] += 1
    facts["root_prompt"]["bytes"] += 30
    proc, data = _run(root, facts, tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-10")
    assert f["severity"] == "MID"
    assert f["anchor"] == "[REPO:contexts/AGENTS.md]"
    assert "lines:" in f["observed"] and "bytes:" in f["observed"]


def test_finding_order_is_severity_then_skill_then_criterion(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "c", "exit_code": 1, "summary": "s"}}
    facts["skills"][0]["paths"]["has_tests"] = False
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    proc, data = _run(root, facts, tmp_path)
    assert [(f["severity"], f["criterion"]) for f in data] == [
        ("BLOCKER", "C-09"), ("HIGH", "C-01"), ("MID", "C-03")]
```

- [ ] **Step 5: 追加 `test_judge_contract.py` 第二部分（锚点硬门禁与退出码 2）**

```python
def test_phantom_skill_anchor_exits_2_without_writing(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["oversized_files"] = ["skills/demo/references/ghost.md"]
    report = tmp_path / "report.md"
    js = tmp_path / "f.json"
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    proc = run_judge(src, "--repo-root", str(root), "--report", str(report), "--json", str(js))
    assert proc.returncode == 2
    assert "ghost.md" in proc.stderr
    assert not report.exists() and not js.exists(), "GI-3：锚点失败时不得写出任何产物"


def test_invalid_rule_anchor_exits_2(tmp_path):
    root = build_repo(tmp_path / "repo", agents_md="# SYSTEM RULES\n")
    (root / "skills" / "demo" / "references" / "big.md").write_text(
        "行\n" * 1010, encoding="utf-8")
    facts = _facts(root)
    facts["skills"][0]["oversized_files"] = ["skills/demo/references/big.md"]
    proc, data = _run(root, facts, tmp_path)
    assert proc.returncode == 2
    assert "根提示词锚点无对应标题" in proc.stderr


def test_missing_facts_file_exits_2(tmp_path):
    proc = run_judge(tmp_path / "nope.json")
    assert proc.returncode == 2
    assert "找不到 facts 文件" in proc.stderr


def test_invalid_json_exits_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    proc = run_judge(bad)
    assert proc.returncode == 2
    assert "不是合法 JSON" in proc.stderr


def test_missing_required_key_exits_2(tmp_path):
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"repo_root": str(tmp_path)}), encoding="utf-8")
    proc = run_judge(partial)
    assert proc.returncode == 2
    assert "缺少必需键" in proc.stderr
```

- [ ] **Step 6: 追加 `test_judge_contract.py` 第三部分（报告不变式）**

```python
def test_report_written_to_requested_path(tmp_path):
    root = build_repo(tmp_path / "repo")
    report = tmp_path / "out" / "report.md"
    js = tmp_path / "out" / "findings.json"
    src = root / "_in.json"
    src.write_text(json.dumps(_facts(root), ensure_ascii=False), encoding="utf-8")
    proc = run_judge(src, "--repo-root", str(root), "--report", str(report), "--json", str(js))
    assert proc.returncode == 0, proc.stderr
    assert report.exists() and js.exists()
    assert json.loads(js.read_text(encoding="utf-8")) == []


def test_report_is_written_with_requested_name(tmp_path):
    root = build_repo(tmp_path / "repo")
    report = tmp_path / "sub" / "report.md"
    js = tmp_path / "f.json"
    src = root / "_in.json"
    src.write_text(json.dumps(_facts(root), ensure_ascii=False), encoding="utf-8")
    proc = run_judge(src, "--repo-root", str(root), "--report", str(report), "--json", str(js))
    assert proc.returncode == 0
    assert report.exists()


def test_report_head_contains_verdict_and_metadata(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 0
    text = report.read_text(encoding="utf-8")
    assert "spec-evolution 演进报告" in text
    assert "判定结论: **MID**" in text
    assert "扫描技能数: 1" in text
    assert "C-04" in text
    assert "（无既有门禁失败）" in text


def test_report_blocker_section_lists_failed_gate(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 1
    text = report.read_text(encoding="utf-8")
    assert "判定结论: **BLOCKER**" in text
    assert "| pytest |" in text and "1 failed" in text


def test_report_human_verdict_section_is_never_prefilled(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    _run(root, facts, tmp_path, "--report", str(report))
    text = report.read_text(encoding="utf-8")
    head, sep, tail = text.partition("## 人类裁决 (Human Verdict)")
    assert head and sep, "报告必须含人类裁决区"
    assert "[x]" not in tail, "GI-4：裁决区不得被预勾选"
    for token in ("BLOCKER", "HIGH", "MID", "建议", "推荐"):
        assert token not in tail, f"GI-4：裁决区混入判定器内容 {token!r}"
    assert "[ ] 采纳 / [ ] 驳回" in tail


def test_no_findings_still_renders_verdict_header(tmp_path):
    root = build_repo(tmp_path / "repo")
    report = tmp_path / "report.md"
    proc, _ = _run(root, _facts(root), tmp_path, "--report", str(report))
    assert proc.returncode == 0
    text = report.read_text(encoding="utf-8")
    assert "判定结论: **CLEAN**" in text
    assert "| ID | 裁决 | 裁决人 | 裁决日期 | 驳回理由 |" in text
    assert "[x]" not in text
```

> **注意**：`test_report_and_json_written_to_requested_paths` 中 `_run` 总是传 `--json`，因此该断言检查的是**未被请求的路径**（`out/report.md`）不存在，而不是 `--json` 被禁用。

- [ ] **Step 7: 跑判定契约测试**

```bash
python3 -m pytest skills/spec-evolution/tests/test_judge_contract.py -q
```

期望：全绿。若 `test_c04` 的期望字符数不符，用 Step 8 的采集命令核对实际值后修正断言（**禁止弱化断言迎合实现**）。

- [ ] **Step 8: 在真实仓库跑一遍判定器（冒烟）**

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --out /tmp/facts.json
python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json --report /tmp/evolution-report.md --json /tmp/findings.json
echo "exit=$?"
```

期望：`exit=1`（存在 F-1/F-2/F-4/F-8/F-9 等 HIGH）；报告含 `判定结论: **HIGH**`；`/tmp/findings.json` 中 `C-04` 的 `observed` = `738 字符`（dual-round-review）、`C-05` 为空（738 < 1024）、`C-01` 命中 `agy-delegation-workflow`。

- [ ] **Step 9: 提交**

```bash
git add skills/spec-evolution/scripts/judge.py skills/spec-evolution/templates/ skills/spec-evolution/tests/
git commit -m "feat(spec-evolution): 判定器 judge.py、报告模板与判定契约测试

Task 3/7：facts.json → finding 列表 + 演进报告；三锚点存在性硬门禁（GI-3，
锚点不可解析即退出 2 且不写产物）与人类裁决区留白（GI-4）。"
```

**Acceptance（Task 3）**：⑪ `python3 -m pytest skills/spec-evolution/tests/test_judge_contract.py -q` 全绿；⑫ `python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json --json /tmp/findings.json; echo $?` 输出 `1`；⑬ 真实仓库 findings 中 `dual-round-review` 的 C-04 `observed` 为 `738 字符`。

---

#### Task 4: 门禁不变式测试 `test_gate_invariants.py`

**Files**
- Create: `skills/spec-evolution/tests/test_gate_invariants.py`

**Goal**：把 RFC-0004 §3.7 的 GI-1~GI-6 变成可回归断言。**这些断言的对象是 spec-evolution 自身**（判定器确定性、模板留白、锚点一致、退出码语义、采集只读），不是被测技能 —— 这是本技能「有真实选择端」的落点。

> **D-6（2026-10-12 P3 执行期修正）**：`test_gi5_exit_code_semantics` 原以 `description_chars = 600` 构造「存在 HIGH」用例，但 600 落在 `DESC_SOFT_LIMIT < n < DESC_HARD_LIMIT` 区间，判定为 **C-04 MID**，`main()` 按 MID 不计阻断 → 退出码为 `0`，断言必失败。已改为 `description_chars = 1100`（触发 **C-05 HIGH**，`>= DESC_HARD_LIMIT`），断言本身保持不变。

- [ ] **Step 1: 写 `test_gate_invariants.py`（第一部分：GI-1 确定性 / GI-2 排列稳定）**

```python
"""test_gate_invariants.py — RFC-0004 §3.7 的 GI-1~GI-6 回归门禁。

对象是 spec-evolution 自身：确定性、留白、锚点一致、退出码语义、只读。
"""

import hashlib
import importlib.util
import json
import re
from pathlib import Path

from conftest import build_repo, run_collect, run_judge

SPEC_DIR = Path(__file__).resolve().parents[1]
ANCHOR_RX = re.compile(r"\[(?:SKILL|REPO|RULE):[^\]]+\]")
PLACEHOLDER_RX = re.compile(r"\{\{(\w+)\}\}")
EXPECTED_PLACEHOLDERS = {
    "DATE", "REPO_HEAD", "SKILL_COUNT", "CRITERIA_COUNT",
    "VERDICT", "BLOCKER_SECTION", "FINDINGS_TABLE", "VERDICT_TABLE",
}


def _judge_module():
    spec = importlib.util.spec_from_file_location(
        "spec_evo_judge", SPEC_DIR / "scripts" / "judge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _facts(root: Path, *extra: str) -> dict:
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out), *extra)
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def _run(root: Path, facts: dict, tmp_path: Path, *extra: str):
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    js = tmp_path / "f.json"
    proc = run_judge(src, "--repo-root", str(root), "--json", str(js), *extra)
    data = json.loads(js.read_text(encoding="utf-8")) if js.exists() else None
    return proc, data


def _files(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_gi1_template_placeholders_are_exactly_the_rendered_set():
    tpl = (SPEC_DIR / "templates" / "evolution-report.md").read_text(encoding="utf-8")
    assert set(PLACEHOLDER_RX.findall(tpl)) == EXPECTED_PLACEHOLDERS


def test_gi1_no_unreplaced_placeholders_in_report(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 0, proc.stderr
    assert "{{" not in report.read_text(encoding="utf-8")


def test_gi1_report_and_json_are_byte_identical_across_runs(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    outs = []
    for i in (1, 2):
        rep, js = tmp_path / f"r{i}.md", tmp_path / f"j{i}.json"
        proc = run_judge(src, "--repo-root", str(root),
                         "--report", str(rep), "--json", str(js))
        assert proc.returncode == 0, proc.stderr
        outs.append((rep.read_bytes(), js.read_bytes()))
    assert outs[0] == outs[1], "GI-1：同一 facts 必须产出逐字节相同的报告与 JSON"


def test_gi2_findings_are_stable_under_gate_input_permutation(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    facts["skills"][0]["paths"]["has_tests"] = False
    facts["gates"] = {
        "pytest": {"cmd": "c", "exit_code": 1, "summary": "s"},
        "audit_doc_health": {"cmd": "d", "exit_code": 1, "summary": "t"},
    }
    _, first = _run(root, facts, tmp_path)

    shuffled = json.loads(json.dumps(facts))
    shuffled["gates"] = dict(reversed(list(shuffled["gates"].items())))
    _, second = _run(root, shuffled, tmp_path)
    assert first == second, "GI-2：findings 排列不得依赖输入字典顺序"
```

- [ ] **Step 2: 追加第二部分（GI-3 锚点一致 / GI-4 留白）**

```python
def test_gi3_report_anchors_are_a_subset_of_findings_json(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    report = tmp_path / "report.md"
    proc, data = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 1
    anchors = set(ANCHOR_RX.findall(report.read_text(encoding="utf-8")))
    assert anchors, "报告必须携带可核验锚点"
    assert anchors <= {f["anchor"] for f in data}, "GI-3：报告出现 finding 之外的锚点"


def test_gi3_anchor_validator_rejects_phantom_and_malformed(tmp_path):
    mod = _judge_module()
    root = build_repo(tmp_path / "repo")
    headings = ["# SYSTEM RULES", "## 3. 基础工程规范与防御底线",
                "### 质量门槛 (Definition of Done)"]
    accepted = ["[SKILL:demo/SKILL.md]", "[REPO:docs/index.md]", "[RULE:§3-质量门槛]"]
    rejected = ["[SKILL:nope/SKILL.md]", "[SKILL:demo/ghost.md]",
                "[SKILL:demo/SKILL.md:9999]", "[REPO:docs/ghost.md]",
                "[RULE:§3-不存在的条款]", "[RULE:§9-质量门槛]",
                "SKILL:demo/SKILL.md", "[SKILL:demo/]", ""]
    for anchor in accepted:
        assert mod.validate_anchor(anchor, root, headings) is None, anchor
    for anchor in rejected:
        assert mod.validate_anchor(anchor, root, headings) is not None, anchor


def test_gi4_template_verdict_section_is_blank():
    tpl = (SPEC_DIR / "templates" / "evolution-report.md").read_text(encoding="utf-8")
    _, sep, tail = tpl.partition("## 人类裁决 (Human Verdict)")
    assert sep, "模板必须含人类裁决区"
    assert "[x]" not in tail
    for token in ("BLOCKER", "HIGH", "MID"):
        assert token not in tail, f"GI-4：模板裁决区混入 {token}"


def test_gi4_rendered_verdict_rows_are_empty(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    facts["gates"] = {"pytest": {"cmd": "c", "exit_code": 1, "summary": "s"}}
    report = tmp_path / "report.md"
    _run(root, facts, tmp_path, "--report", str(report))
    _, sep, tail = report.read_text(encoding="utf-8").partition("## 人类裁决 (Human Verdict)")
    assert sep
    rows = [ln for ln in tail.splitlines() if ln.startswith("| F-")]
    assert len(rows) == 2, rows
    for ln in rows:
        assert ln.count("[ ] 采纳 / [ ] 驳回") == 1
        assert ln.endswith("| | | |"), ln
```

- [ ] **Step 3: 追加第三部分（GI-5 退出码 / GI-6 只读）**

```python
def test_gi5_exit_code_semantics(tmp_path):
    root = build_repo(tmp_path / "repo")
    clean, _ = _run(root, _facts(root), tmp_path)
    assert clean.returncode == 0, "无 HIGH/BLOCKER 必须退出 0"

    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 1100  # C-05 HIGH
    blocking, _ = _run(root, facts, tmp_path)
    assert blocking.returncode == 1, "存在 HIGH 必须退出 1"

    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert run_judge(bad).returncode == 2, "输入非法必须退出 2"


def test_gi6_collector_is_read_only_without_gates(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = run_collect(root, "--no-gates", "--out", str(tmp_path / "facts.json"))
    assert proc.returncode == 0, proc.stderr
    assert _files(root) == before, "GI-6：采集改动了仓库"


def test_gi6_gates_run_without_leaving_artifacts(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = run_collect(root, "--out", str(tmp_path / "facts.json"))
    assert proc.returncode == 0, proc.stderr
    after = _files(root)
    assert after == before, f"GI-6：门禁留下产物 {sorted(set(after) - set(before))}"
    assert not (root / ".pytest_cache").exists(), "GI-6：-p no:cacheprovider 未生效"


def test_gates_recorded_when_enabled(tmp_path):
    root = build_repo(tmp_path / "repo")
    out = tmp_path / "facts.json"
    proc = run_collect(root, "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    gates = json.loads(out.read_text(encoding="utf-8"))["gates"]
    assert set(gates) == {"pytest", "check_doc_links", "audit_doc_health", "cross_skill_links"}
    assert all(g["exit_code"] == 0 for g in gates.values()), gates
```

- [ ] **Step 4: 运行不变式测试**

```bash
python3 -m pytest skills/spec-evolution/tests/test_gate_invariants.py -q
```

期望：全绿。若 `test_gi6_gates_run_without_leaving_artifacts` 失败，**修正采集器的门禁调用**（补 `-B` / `-p no:cacheprovider`）而不是放宽断言。

- [ ] **Step 5: 运行技能全套测试**

```bash
python3 -m pytest skills/spec-evolution/ -q
```

期望：三个测试文件全绿（`test_demo.py` 为技能自证夹具，Task 1 已建）。

- [ ] **Step 6: 提交**

```bash
git add skills/spec-evolution/tests/test_gate_invariants.py
git commit -m "test(spec-evolution): GI-1~GI-6 门禁不变式回归

Task 4/7：确定性（逐字节可复现）、排列与输入顺序无关、报告锚点必为
findings 子集、裁决区永久留白、退出码三态语义、采集只读（含 pytest 无残留）。"
```

**Acceptance（Task 4）**：⑭ `python3 -m pytest skills/spec-evolution/ -q` 全绿；⑮ `test_gi6_gates_run_without_leaving_artifacts` 在真实执行四道门禁后仍断言无新文件。

---

#### Task 5: 架构设计书

**Files**
- Create: `docs/explanation/architecture/spec-evolution-design.md`

**Goal**：补上 C-02 要求的架构设计书，并对外解释「为什么是判定器而不是 LLM 评审」。

> **D-7（2026-10-12 P3 执行期修正）**：本 Task 的 Step 3「门禁复验」在**本 Task 内无法通过** —— 新增的设计书会成为索引孤儿，且 `docs/llms.txt` 与生成物不一致，`audit-doc-health.py` 必然 `REJECTED`。二者都要等 Task 6 完成注册与重生成才转 PASS。故 Step 3 的 ⑱ 实际验收点**顺延到 Task 6 之后**（Task 5 只保证 ⑯ 文件存在 与 ⑰ 断链 0）。

- [ ] **Step 1: 侦察既有设计书结构**

```bash
ls docs/explanation/architecture/
head -40 docs/explanation/architecture/goal-loop-design.md
```

- [ ] **Step 2: 写 `spec-evolution-design.md`**

**必须**模仿 `docs/explanation/architecture/goal-loop-design.md` 的章节骨架（标题层级、元信息块、后续阅读链接风格）。内容至少覆盖：

1. **问题域**：为什么「提示词/技能自身的演进」需要独立机制 —— 三门禁只判「产物正确性」，「存在性缺陷」是盲区。
2. **架构分层**：采集器（只回答是什么）/ 判据表（十条）/ 判定器（确定性映射）/ 报告模板（人类裁决留白）。
3. **关键决策与理由**：
   - 为什么**不做 LLM judge** —— 自评对上下文敏感、有讨好倾向、无对照基线，产出的是假设而非结论；锚点硬门禁把「幻觉」变成进程退出码。
   - 为什么**默认 fail-closed**（锚点不可解析即退出 2、拒绝写产物）。
   - 为什么**人类裁决区永久留白**（Reviewer ≠ Author）。
4. **与 `doc-governance` / `dual-round-review` / `goal-loop` 的边界**（RFC-0004 §3.8 职责边界表）。
5. **已知表达上限**（与 `references/checks-spec.md` §4 一致，不得夸大）。
6. **演进方向**：v1 覆盖 `skills/`；v2 才考虑根提示词与 `docs/` 制品。

- [ ] **Step 3: 门禁复验**

```bash
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py
```

期望：0 断链；PASS。

- [ ] **Step 4: 提交**

```bash
git add docs/explanation/architecture/spec-evolution-design.md
git commit -m "docs(spec-evolution): 架构设计书

Task 5/7：补 C-02 要求的架构设计书，说明分层、锚点硬门禁与
「不做 LLM judge」的决策理由。"
```

**Acceptance（Task 5）**：⑯ `test -f docs/explanation/architecture/spec-evolution-design.md` 成立；⑰ 断链扫描 0；⑱ `audit-doc-health.py` PASS。

---

#### Task 6: 全套注册面接入

**Files**
- Modify: `skills/_shared/tests/test_cross_skill_links.py`（`SKILL_NAMES` 追加 `"spec-evolution"`）
- Modify: `docs/index.md`（技能表新增行 + 版本号 + 修订历史）
- Modify: `README.md`（技能表新增行）
- Modify: `tools/skills-manager/collections/cr-agent-arsenal.json`（**补 F-9**：`clarification-protocol` 缺登记）
- Regenerate: `docs/llms.txt`

**Goal**：让 C-01~C-10 全部对本技能自身返回「已合格」——即用判定器给 spec-evolution 自己打分，结果必须是 CLEAN。

> **D-8（2026-10-12 P3 执行期修正）**：Step 4 写的版本号迁移 `V1.28.0` → `V1.29.0` 已过期 —— RFC-0004 受理流转时 `docs/index.md` 已升至 **V1.29.0**，故本次须 `V1.29.0` → **`V1.30.0`**（`trim-revision.py` 维持修订历史 ≤5 行）。同 Step 2 中「覆盖全部 8 个技能」按实际追加后的 `names` 长度为准。

- [ ] **Step 1: 追加 `SKILL_NAMES`**

在 `skills/_shared/tests/test_cross_skill_links.py:20-28` 的列表中追加 `"spec-evolution"`（保持既有排序风格）。

- [ ] **Step 2: 修 F-9 —— `clarification-protocol` 补登记**

读取 `tools/skills-manager/collections/cr-agent-arsenal.json`，在 `skills[].names` 中补入 `"clarification-protocol"`，使 `names` 覆盖全部 8 个技能（原 7 个 + `spec-evolution`）。**保持既有 JSON 缩进风格**，不改其它字段。

- [ ] **Step 3: `README.md` 技能表新增行**

在技能表中按既有格式新增 `spec-evolution` 行（沿用相邻行的列结构与链接风格）。

- [ ] **Step 4: `docs/index.md` 登记**

1. 技能表新增 `spec-evolution` 行；
2. 版本号 `V1.28.0` → `V1.29.0`；
3. 修订历史新增 V1.29.0 行；
4. 若 RFC-0004 行需反映状态变化，一并更新为 `Implemented`。

- [ ] **Step 5: 裁剪修订历史并重生成机器地图**

```bash
python3 skills/doc-governance/scripts/trim-revision.py --root docs/index.md --fix
python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --name=System
```

> **陷阱（身份写保护）**：`generate-llms-txt.py` 必须沿用既有身份 `--name=System`。以其它名字调用会被拒绝（`❌ 拒绝改写机器地图身份`），**不得**为绕过而删除 `docs/llms.txt`。

- [ ] **Step 6: 让本技能暴露给宿主**

```bash
python3 contexts/install.py
```

期望：`skills/spec-evolution` 经相对软链出现在 `.agents/skills/` 下。

- [ ] **Step 7: 用判定器自证 —— 这是本任务的核心验收**

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --out /tmp/facts-self.json
python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts-self.json \
    --report docs/project/reviews/spec-evolution-selfcheck.md --json /tmp/findings-self.json
echo "exit=$?"
python3 - <<'PY'
import json
f = [x for x in json.load(open('/tmp/findings-self.json')) if x['skill'] in ('spec-evolution', 'clarification-protocol')]
print('spec-evolution 自身 + F-9 相关 findings =', len(f), f)
PY
```

期望：`spec-evolution` **零 finding**；`clarification-protocol` 仅剩既有已知项（本计划不修 F-3/F-6 等），且不再含 `C-07`（F-9 已修）。

> 报告落 `docs/project/reviews/` 供人类裁决 —— 该目录已存在且被文档门禁纳管。**裁决区必须留空**，由人类填写。

- [ ] **Step 8: 全门禁复验**

```bash
python3 -m pytest skills/ -q
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py
```

期望：`pytest` 全绿（基线 324 + 新增）；断链 0；健康度 PASS。

- [ ] **Step 9: 提交**

```bash
git add skills/_shared/tests/test_cross_skill_links.py docs/index.md README.md \
        tools/skills-manager/collections/cr-agent-arsenal.json docs/llms.txt \
        docs/project/reviews/spec-evolution-selfcheck.md skills/spec-evolution/tests/test_demo.py
git commit -m "feat(spec-evolution): 全套注册面接入 + F-9 收口

Task 6/7：SKILL_NAMES / README / docs/index.md / collections 四处登记，
重生成 llms.txt；修 F-9（clarification-protocol 集合缺登记）。
判定器自证 spec-evolution 零 finding。"
```

**Acceptance（Task 6）**：⑲ `python3 -m pytest skills/_shared/tests/test_cross_skill_links.py -q` 4 passed；⑳ `audit-doc-health.py` PASS 且断链 0；㉑ 判定器对 `spec-evolution` 返回零 finding。

---

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

---

### §5 验收判据总表（Definition of Done）

| # | 判据 | 命令 | 期望 |
| :--- | :--- | :--- | :--- |
| ① | 技能可被宿主发现 | `ls .agents/skills/spec-evolution/SKILL.md` | 存在 |
| ② | description ≤ 500 字符 | `python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills spec-evolution` | `description_chars ≤ 500` |
| ③ | 采集器契约 | `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -q` | 全绿 |
| ④ | 判定器契约 | `python3 -m pytest skills/spec-evolution/tests/test_judge_contract.py -q` | 全绿 |
| ⑤ | 门禁不变式 | `python3 -m pytest skills/spec-evolution/tests/test_gate_invariants.py -q` | 全绿 |
| ⑥ | 全仓回归 | `python3 -m pytest skills/ -q` | 全绿（≥ 324 + 新增） |
| ⑦ | 文档断链 | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` | 0 断链 |
| ⑧ | 文档健康 | `python3 skills/doc-governance/scripts/audit-doc-health.py` | PASS |
| ⑨ | 自我判定 | 判定器扫描全仓 | `spec-evolution` 零 finding |
| ⑩ | 只读不变式 | `git status --porcelain` 在采集后 | 除显式产物外无变化 |
| ⑪ | 人类裁决留白 | 报告 `## 人类裁决` 之后 | 无 `[x]`、无判定器内容 |
| ⑫ | 独立终审 | `dual-round-review` R1+R2 | Zero Blockers |

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
| V1.0.0 | 2026-10-12 | 主智能体 | 待用户裁定 | P1 落地计划首发：7 个原子任务、12 条验收判据、6 类风险与 4 条显式默认假设 |
| V1.1.0 | 2026-10-12 | DSH AI Agent | 王辉 | P3 执行收口：Task 1~7 全部交付（`1418e2b` / `629c6b1` / `dfc301b` / `3f58d00` / `5775c6c` / `95af3f1`）；新增《执行偏差记录》D-1~D-8（设计稿缺陷与 Task 3 段 5 处 + Task 4 段 1 处 + Task 5/6 各 1 处顺序/版本问题）；Active Checkpoint 推进至 P3.5 |
