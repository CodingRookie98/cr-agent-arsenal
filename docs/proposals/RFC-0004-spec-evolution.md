# RFC-0004: spec-evolution 技能 —— 面向提示词与技能的机械化演进回路

> **提案元数据**
> - **标识**: RFC-2026-SPEC-EVOLUTION
> - **当前状态**: Accepted
> - **发起人**: 工程师 / AI Agent
> - **当前版本**: V0.3.0
> - **初次发起日期**: 2026-10-12
> - **目标里程碑**: spec-evolution V1.0.0（新增技能，不涉及仓库版本号变更）
> - **定案日期**: 2026-10-12
> - **关联前置**: [RFC-0001](./RFC-0001-review-report-archive.md)（交付凭据归档契约）、[goal-loop 架构设计书](../explanation/architecture/goal-loop-design.md)、[docs/GOVERNANCE.md](../GOVERNANCE.md)

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V0.1.0** | 2026-10-12 | DSH AI Agent | 王辉 | 初次发起：确立「只做机械可复现信号、v1 明确排除无客观信号的设计质量评价」的范围红线；判据表 C-01~C-10 由真实试跑数据支撑 |
| **V0.2.0** | 2026-10-12 | DSH AI Agent | 王辉 | 四项未决项收口：C-04 降为建议值（MID）、C-05 改按 `description` 口径、C-07 注册面 5→4、F-1~F-9 不进本次交付。依据 Agent Skills 规范原文与生成器源码实证，修正 V0.1.0 中两处契约误设 |
| **V0.3.0** | 2026-10-12 | DSH AI Agent | 王辉 | **状态流转 In Review → Accepted**（用户裁决准予受理）；批准进入 P1 编写落地计划。契约内容未变更，仅登记受理决定 |

---

## 1. 背景与业务痛点 (Why)

### 1.1 现象：三门禁全绿，技能层缺陷长期存在

2026-10-12 在 `master`（HEAD `10359c2`）实测既有三道机械门禁，**全部 PASS**：

| 门禁 | 命令 | 实测结果 |
| :--- | :--- | :--- |
| 契约测试 | `python3 -m pytest skills/ -q` | **324 passed**（30.40s） |
| 断链扫描 | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` | 扫描 65 个 md，**断链 0** |
| 知识库健康 | `python3 skills/doc-governance/scripts/audit-doc-health.py` | **PASS**，零缺陷，100.0/100 |

但同一时刻，技能层存在下列**可被单条命令复现**的缺陷，无一被上述门禁捕获：

| # | 技能 | 缺陷 | 复现命令 | 实测值 |
| :--- | :--- | :--- | :--- | :--- |
| F-1 | `dual-round-review` | `description` 超 500 字符**建议值**（非规范硬限） | 见 §3.2 C-04 | **738** 字符（超建议值 +238，距硬限 1024 尚余 286） |
| F-2 | `clarification-protocol` | 同上 | 同上 | **623** 字符（超建议值 +123，距硬限 1024 尚余 401） |
| F-3 | `clarification-protocol` | 交付面仅 `SKILL.md`（无 `references/` `scripts/` `templates/` `tests/`） | `ls skills/clarification-protocol` | 仅 1 项 |
| F-4 | `agy-delegation-workflow` | 无 `tests/` | `ls skills/agy-delegation-workflow` | 无 |
| F-5 | `agy-delegation-workflow` | 无架构设计书 | C-02 | 缺 |
| F-6 | `clarification-protocol` | 无架构设计书 | C-02 | 缺 |
| F-7 | `doc-governance` | 无 `templates/` | C-03 | 缺 |
| F-8 | `doc-governance` | 单文件超 1000 行硬约束 | C-06 | `tests/test_doc_governance_scripts.py` **1583** 行 |
| F-9 | `clarification-protocol` | 集合登记面缺登记 | C-07 | `tools/skills-manager/collections/cr-agent-arsenal.json` 的 `names` 为 6 项，实际 7 项 |

**「500 字符」与「1024 字符」的权威性裁定**（2026-10-12，V0.2.0）：两者层级不同，不可混用——

| 阈值 | 出处 | 性质 | 超限后果 |
| :--- | :--- | :--- | :--- |
| **1024** | [Agent Skills 规范](https://agentskills.io/specification)：「`description`：Max 1024 characters」（Claude Platform Docs 与 Microsoft Learn 表述一致） | **规范硬限** | 技能在 Claude API / CLI 侧被**静默丢弃**（[copilot-cli#3494](https://github.com/github/copilot-cli/issues/3494) 实证） |
| **500** | `writing-skills` 技能：「Keep under 500 characters **if possible**」 | **软性建议** | 无——仅增加每会话元数据开销 |

规范原文另有 progressive disclosure 条款，正是「500 建议」的真实依据：**`name` 与 `description` 在所有技能上启动期全量加载**（约 100 tokens/技能），正文才按需载入。故 description 长度是**真实的每会话成本**，但它不构成**违规**。

V0.1.0 曾以「仓库既有规范」作为 500 的依据，该链是**循环引用**，V0.2.0 撤回：
- [2026-09-21-frontend-qa-gate.md:209](../project/plans/2026-09-21-frontend-qa-gate.md) 称「与仓库既有规范一致」，但其唯一先例即下条；
- [2026-09-20-taste-driven-designer.md:137](../project/plans/2026-09-20-taste-driven-designer.md) 自己写的是「超出 `writing-skills` **建议** 500 上限」——来源本就是软性建议，而非成文规范。

### 1.2 根因：门禁只覆盖「产物正确性」，不覆盖「交付面完整性」

既有三门禁的判定域是：**文档之间的链接是否有效**、**文档库的结构是否健康**、**已写代码的行为是否符合契约**。
它们共同的前提是「东西已经存在」——测试存在才可能失败，链接存在才可能断。

**没有任何一道门禁规定「什么东西必须存在」。** 于是「技能缺测试」「技能缺设计书」「技能交付面不全」「description 超限」这类**存在性缺陷**落入盲区，长期存续（F-3/F-5/F-6 自 2026-10-11 下沉 `clarification-protocol` 起即存在）。

### 1.3 更深一层：演进回路缺的不是「变异」，是「选择」

本仓库 2026-10-12 曾否决一条提案（往根提示词写入「发现可优化处就提 Issue」），理由记录在案：**该提议只补了「变异」端，「选择」端完全没补；而 ball of mud 本身就是「只有变异、没有选择」的进化产物，故只补变异会加速 ball of mud。**

「选择」无法交给会话内模型，原因是硬的：
1. 判断一条规则该删该改需要**消融证据（ablation）**，而会话内模型无实验能力；
2. 对同一段文本，模型的自评随上下文漂移，且存在**机械谄媚**倾向——被问「有没有可优化之处」时，回答「没有」在训练分布中被判为「没帮上忙」，输出必然收敛到「有」；
3. 模型既是被测规则的**执行者**又是**评判者**，违反仓库自身的「审查独立性 (Reviewer ≠ Author)」。
4. 本仓库 `skills/goal-loop/tests/test_failure_recovery_contract.py:14` 已引用 **Huang et al. 2310.01798**：无外部反馈的自我批评会导致性能下降。

**本提案的立论**：把「选择」从模型的**意见**换成脚本的**退出码**。凡不能被一条命令复现的「改进建议」，一律不产生 finding。

### 1.4 为什么现在做

`clarification-protocol` 是 2026-10-11 从根提示词下沉出来的新技能，其 SKILL.md 明确承担了原本写在 `contexts/AGENTS.md` §4 的澄清规程。**下沉动作本身正确（root 因此从 106 行降到 97 行），但下沉动作同时制造了新的交付面债务**（F-2/F-3/F-6/F-9 四条同源）。若没有「交付面完整性」的选择端，每一次正确的下沉都会**等量制造**一批无人检查的债务。这正是本提案要堵的结构性缺口。

---

## 2. 目标与非目标 (Goals & Non-Goals)

### 2.1 核心目标 (Goals)

- **G1 事实层**：产出**纯事实**采集器——不判断、不评价，只把「技能与提示词的客观状态」导出为结构化 `facts.json`。
- **G2 判定层**：以纯 Python 标准库实现**确定性判定器** `judge.py`，输入 `facts.json`，输出 `findings.json` 与人类可读报告；以 **Exit Code 0/1** 表达「有无 finding」。
- **G3 零谄媚**：判定器**不得调用任何 LLM**、不得访问网络、不得读取会话上下文。同一份输入必须永远得到同一份输出。
- **G4 全量覆盖**：v1 对 `skills/` 下全部 7 个技能执行 §3.2 判据表，并对根提示词 `contexts/AGENTS.md` 执行 C-10。
- **G5 可回归**：判定器自身由 `pytest` 门禁覆盖——喂人造 `facts.json` 断言判定结果，使「判定器退化」可被捕获。
- **G6 零改动落地**：判定过程**只读**，任何文件修改均不得由本技能自动执行。

### 2.2 明确非目标 (Non-Goals / 防蔓延红线)

| 编号 | 非目标 | 依据 |
| :--- | :--- | :--- |
| N-1 | **不做无客观信号的设计质量评价**（职责重叠、技能该不该存在、是否过重） | 此类问题无法用退出码复现，是谄媚高发区；v1 结构性排除，见 §4 争议焦点 |
| N-2 | **不自动修改任何文件** | 本技能只产出 finding 与报告；修改由人类裁决后另行发起（G6） |
| N-3 | **不往 `contexts/AGENTS.md` 增加任何条款** | 该文件准入判据禁止净增长；「出问题就加一条」是本仓库头号失败模式 |
| N-4 | **不引入任何第三方依赖、不新增 CI** | 仓库无 `package.json`/`pytest.ini`/`.github/`，纯 `python3` + `pytest` 既有约定 |
| N-5 | **不改动既有三门禁的判定语义** | 避免扩大公共契约面；本技能是**叠加**层，不替换 |
| N-6 | **不对 `docs/project/reviews/**` 做入链扫描** | 该目录被 GOVERNANCE.md 显式豁免（交付凭据必须逐字原文） |
| N-7 | **不评价阈值本身的合理性**（如「1000 行是否应为 800 行」） | 阈值来自 `contexts/AGENTS.md` §3 与既有计划文件，本技能只执行不讨论 |

---

## 3. 核心设计与契约草案 (How - Technical Draft)

### 3.1 三类事实源（采集层）

采集器只回答「是什么」，不回答「好不好」。

| 事实源 | 内容 | 采集方式 |
| :--- | :--- | :--- |
| **S1 门禁事实** | 四条既有命令的退出码与 stdout 摘要 | `subprocess` 调用 §1.1 表中的命令 |
| **S2 结构事实** | 技能目录树、`SKILL.md` frontmatter 字符数、单文件行数、`docs/explanation/architecture/` 存在性 | 文件系统遍历 + 正则 |
| **S3 注册事实** | 技能在 4 个注册面的登记状态 | 解析 `SKILL_NAMES`（`test_cross_skill_links.py`）、`docs/index.md`、`README.md`、`tools/skills-manager/collections/cr-agent-arsenal.json` |

`facts.json` 顶层结构（草案）：

```json
{
  "schema_version": "1.0",
  "generated_at": "<ISO8601>",
  "repo_head": "<git rev-parse --short HEAD>",
  "gates": {
    "pytest":            {"cmd": "...", "exit_code": 0, "summary": "324 passed"},
    "check_doc_links":   {"cmd": "...", "exit_code": 0, "summary": "断链 0"},
    "audit_doc_health":  {"cmd": "...", "exit_code": 0, "summary": "PASS"},
    "cross_skill_links": {"cmd": "...", "exit_code": 0, "summary": "0 violations"}
  },
  "skills": [
    {
      "name": "clarification-protocol",
      "dirs": ["SKILL.md"],
      "has_tests": false,
      "test_files": [],
      "design_doc": null,
      "frontmatter_chars": 678,
      "description_chars": 623,
      "max_file_lines": 0,
      "oversized_files": [],
      "registrations": {
        "cross_skill_names": true,
        "docs_index": true,
        "readme": true,
        "collection": false
      }
    }
  ],
  "root_prompt": {"path": "contexts/AGENTS.md", "lines": 97, "bytes": 10746}
}
```

### 3.2 判据表（判定层核心）

| ID | 判据 | 事实源 | 严重度 | 复现命令范式 |
| :--- | :--- | :--- | :--- | :--- |
| **C-01** | 技能无 `tests/` 或其中无 `test_*.py` | S2 | HIGH | `ls skills/<n>/tests` |
| **C-02** | 技能无架构设计书 `docs/explanation/architecture/<n>-design.md` | S2 | MID | `test -f` |
| **C-03** | 技能交付面缺 `references/` 或 `scripts/` 或 `templates/`（有则须完整） | S2 | MID | `ls skills/<n>` |
| **C-04** | `description` 字符数 > 500（**软性建议值**，非硬限） | S2 | MID | frontmatter 计数脚本 |
| **C-05** | `description` 字符数 ≥ 1024（Agent Skills 规范**硬限**） | S2 | HIGH | 同上 |
| **C-06** | 单文件行数 > 1000（`contexts/AGENTS.md` §3 硬约束） | S2 | MID | `wc -l` |
| **C-07** | 技能在 4 个注册面中存在缺登记 | S3 | HIGH | 解析各注册面 |
| **C-08** | 技能内存在跨技能相对链接 | S2 | HIGH | `test_cross_skill_links.py` 同源正则 |
| **C-09** | 既有门禁任一非零退出 | S1 | **BLOCKER** | 四条命令 |
| **C-10** | 根提示词 `contexts/AGENTS.md` 相对基线（97 行 / 10746 字节）净增长 | S2 | MID | `wc -l` / `wc -c` |

**严重度语义**：
- `BLOCKER`：仓库既有门禁已失败，本技能不重复判定，直接置顶并阻断交付。
- `HIGH`：违反**成文规范或外部硬限**（有权威出处，超限可致技能失效），应修复。
- `MID`：交付面完整性缺口，或**对软性建议值的偏离**（advisory，无权威硬约束），登记为待办，不阻断交付。

**C-10 的口径说明**：`contexts/AGENTS.md:3` 的准入判据允许净增长，**前提是同一提交内给出等量删减或不可压缩的理由**。判定器只能机械观测「是否净增长」，无法判定「理由是否成立」——故 C-10 的报告文案固定为**中性提示**（「⚠️ 根提示词相对基线净增长 N 行，须确认已在同提交内给出等量删减或不可压缩理由」），而非指控。这是本判据的**已知表达上限**，显式登记，不在 v1 掩饰。

### 3.3 判定器接口契约

```
skills/spec-evolution/scripts/collect-facts.py [--repo-root <path>] [--out facts.json]
skills/spec-evolution/scripts/judge.py --facts facts.json [--json findings.json] [--report report.md]
```

| 契约项 | 约束 |
| :--- | :--- |
| 退出码 | `judge.py`：**0 = 无 finding**；**1 = 有 finding**；**2 = 用法/输入错误**（与 `taste-driven-designer` 既有脚本一致） |
| 依赖 | 仅 Python 3 标准库（`json`/`pathlib`/`re`/`subprocess`/`argparse`） |
| 网络/LLM | **禁止**。判定器不得 import 任何网络库或 SDK |
| 确定性 | 同一 `facts.json` 输入必须产出逐字节相同的 `findings.json`（不含时间戳等易变字段） |
| 排序 | findings 按 `严重度 desc, 技能名 asc, 判据 ID asc` 稳定排序 |

### 3.4 锚点契约

每条 finding 携带**章节路径锚点**，指向可被人直接核验的位置：

```
[SKILL:<skill-name>/<relative-path>]       例: [SKILL:clarification-protocol/SKILL.md]
[SKILL:<skill-name>/<path>:<line>]         例: [SKILL:doc-governance/tests/test_doc_governance_scripts.py:1]
[RULE:<§-heading-path>]                    例: [RULE:§3-精准修改与代码卫生]
```

- `[SKILL:*]` 锚点由判定器在**运行时**校验路径存在性；路径不存在则**判定器自身报错退出 2**（防锚点幻觉）。
- `[RULE:*]` 锚点以 `contexts/AGENTS.md` 的 `## / ###` 标题树为解析域，天然抗行号漂移。

### 3.5 报告模板契约

```
# spec-evolution 演进报告 · <ISO8601 日期>
- 仓库基线: <HEAD> | 扫描技能数: 7 | 判据数: 10
- 结论: <CLEAN | 发现 N 项>   ← 由 judge.py 生成，不得人工改写

## BLOCKER
（C-09 命中时的既有门禁失败明细）

## HIGH / MID
| 判据 | 锚点 | 证据命令 | 实测值 | 期望 |

## 人类裁决 (Human Verdict)   ← 以下区域由人类填写，智能体不得代填
| finding | 裁决 | 裁决人 | 日期 | 理由 |
| F-1     | [ ] 采纳 / [ ] 驳回 | | | |
```

**红线**：「人类裁决」区的存在是**结构性的**——判定器输出到该标题为止即停止写入。任何为模型生成的裁决内容都视为门禁违规（由 §3.7 GI-4 断言防护）。

### 3.6 触发路由契约

| 触发方式 | 范围 | 说明 |
| :--- | :--- | :--- |
| **独立调用**（v1 主路径） | 全量 7 技能 + 根提示词 | 用户或智能体显式执行；`--skills <a,b>` 可缩窄 |
| **goal-loop P5 增量挂载**（v1 随附） | 仅本次交付触及的 `skills/<n>/` | 交付归档阶段复查被改动技能的交付面完整性 |

挂载仅追加对**被改动技能**的定向检查，不做全量扫描，避免把周期性治理成本摊进每个 Heavy Path 任务。挂载点在 `skills/goal-loop/SKILL.md` 内，**不触碰 `contexts/AGENTS.md`**（N-3）。

### 3.7 门禁不变式 (Gate Invariants)

| 编号 | 不变式 | 断言方式 |
| :--- | :--- | :--- |
| **GI-1** | 判定器源码不含任何 LLM SDK / 网络库 import | pytest 源码扫描 |
| **GI-2** | 同一 `facts.json` 两次执行产出逐字节相同的 `findings.json` | pytest 双跑比对 |
| **GI-3** | 每条 finding 的 `[SKILL:*]` 锚点路径必然存在 | pytest 人造锚点用例 |
| **GI-4** | 报告生成器输出的「人类裁决」区**为空模板**，不含任何裁决结论 | pytest 字符串断言 |
| **GI-5** | 判定器退出码语义严格为 0/1/2，无其他取值 | pytest 边界用例 |
| **GI-6** | 采集器与判定器均不改写任何文件（只读） | pytest 目录快照比对 |

---

## 4. 备选方案权衡与争议焦点 (Alternatives & Trade-offs)

### 方案 A（本提案选定）：纯机械判定器 + 全量结构扫描

只采信退出码与文件系统事实，v1 结构性地不做设计质量评价。

- **优点**：零谄媚面（无 LLM 调用即无「意见」）；可回归；成本近似为零；立即可产出 §1.1 的 F-1~F-9 真实 finding。
- **缺点**：覆盖面窄——最需要判断力的「这技能该不该存在」不在其中。
- **接受理由**：窄而真 > 宽而假。§1.3 已论证无客观信号的评价必然谄媚。

### 方案 B（未采纳）：任务内摩擦记录（原「A5 方案」）

在 `goal-loop` 熔断复盘时追加「记录提示词可优化之处」，落 `.agents/prompt-friction.jsonl`。

- **成本数据**：该方案约 **35 tok/任务**，优于独立技能的 **340 tok/任务**，因此曾在 2026-10-12 的成本对比中胜出。
- **否决理由**：开放式评价请求隐含「期望答案存在性」，模型必然找出「可优化之处」——**熔断 N 次就出 N 条记录**，违反「审查独立性 (Reviewer ≠ Author)」。成本论证成立但设计不成立。
- **补充**：其修正版「准入判据 F1~F4」（强制具体条款 + 判别预测 + 外部证据 + 默认不记录）在 agy 独立评估中被判 **C · 不可行**——现存产物中无「被引用条款行号」字段，缺乏可提取数据源。

### 方案 C（未采纳）：完整对抗基准套件（含 LLM 采样层）

三层架构：`cases/*.json` 固定用例集 → workflow fan-out 采样 N 个 fresh 子智能体产出结构化 JSON → `judge.py` 确定性判定 → pytest 门禁。

- **优点**：能覆盖「设计质量」这类需判断力的维度，且用「人造用例 + 判定器」方法控制谄媚。
- **否决理由（v1 范围）**：采样层不可 import、不可回归（派发是会话内动作），一旦纳入 pytest 就会造出「跑一次就烂掉」的假门禁；且其首要被测对象（§4 熔断报告模板）**当前无落盘数据源**——该模板是向用户输出的 markdown，不保证落盘，模板中也不含任何「被引用条款」字段。**建立在不存在的数据源上的判定器是空中楼阁。**
- **去向**：登记为 v2 候选，前置条件是先让被测对象产生可机械读取的落盘产物。

### 方案 D（未采纳）：往 `contexts/AGENTS.md` 加一条「定期检查技能交付面」

- **否决理由**：① 直接违反 `contexts/AGENTS.md:3` 准入判据（触发条件偶发 = 条件性条款，应下沉）；② 指令预算均匀削弱论——每加一条都会稀释全部既有条款的遵循度；③ 与 §1.3 记录的「ball of mud 头号失败模式」同构。

### 争议焦点与裁决

| 争议点 | 分歧 | 裁决 |
| :--- | :--- | :--- |
| 「设计质量」是否应纳入 v1 | 纳入则覆盖完整，但无客观信号、谄媚高发 | **不纳入**。无退出码可复现的评价不产生 finding（G3 / N-1） |
| 成本 vs 形态：曾在成本对比中落败的「独立技能」形态为何重启 | 2026-10-12 的 A1（独立技能，340 tok/任务）输给 A5（35 tok/任务） | **成本模型不同**：A1 是**每任务付费**的高频记录；本提案是**按需触发的低频审计**。同一形态在两个成本模型下结论相反，并不矛盾 |
| C-10 能否判定「理由是否成立」 | 准入判据允许带理由的净增长 | **不能**。判定器只报「净增长」这一事实并提示核验，不自称判定理由成立与否（§3.2 口径说明） |
| 是否 v1 就挂载到 goal-loop P5 | 早挂载可得强制路由，但误报会污染所有 Heavy Path 交付 | **挂载但限增量**：只扫本次触及的技能，全量保持按需（§3.6） |
| 500 字符上限是否升格为**成文规范** | 两个计划文件曾据此整改，看似构成先例 | **不升格**。出处原文是「Keep under 500 characters **if possible**」，属软性建议；C-04 降为 MID，硬限按规范原文归 C-05（`description` ≥1024）。依据见 §1.1 权威性裁定表 |
| `docs/llms.txt` 是否为技能注册面 | 曾列为 C-07 第 5 面，但该面判定当前恒为「不适用」 | **剔除**。`generate-llms-txt.py` 的扫描根为 `docs/`（`root_dir.rglob("*.md")`），**结构上不可能收录 `skills/`**；且它是**派生文件**——对生成物查「忘登记」是范畴错误，正确操作是重跑生成器。它与 C-02 亦冗余（技能无设计书时同样进不了 llms.txt） |
| F-1~F-9 是否随本次交付修复 | 「吃自己的狗粮」使仓库自洽的诱惑很强 | **不随本次交付**。检测与修复分离：混合二者使 diff 不可审、耦合两个独立决策；F-5/F-6（两份架构设计书）与 F-8（1583 行拆分）各自是独立的重型任务。**唯一例外 F-9**：本次交付本就要编辑 `collections/cr-agent-arsenal.json` 登记新技能，同数组内补 `clarification-protocol` 属同一处、同一动作 |

---

## 5. 术语表与易歧义对齐 (Glossary & Terminology Alignment)

### 5.1 核心术语定义 (Core Term Definitions)

| 术语 | 定义 |
| :--- | :--- |
| **规范资产 (Spec Asset)** | 对智能体行为施加约束的可分发文本，本提案域内指 `skills/<n>/` 全部内容与根提示词 `contexts/AGENTS.md` |
| **事实 (Fact)** | 由采集器观测、不含任何评价的文件系统或进程退出状态。例：「`clarification-protocol` 的 description 为 623 字符」 |
| **发现 (Finding)** | 事实经判据表映射后得到的**缺陷断言**。例：「命中 C-04，超限 123 字符」 |
| **判定器 (Judge)** | 把 `facts.json` 映射为 `findings.json` 的确定性程序，不调用任何模型 |
| **选择端 (Selection End)** | 演进回路中判定「哪条候选更好」的环节。本提案的全部设计目的在于把它从**模型的意见**换成**脚本的退出码** |
| **变异端 (Mutation End)** | 演进回路中产出新规则候选的环节。本提案**不涉及**（见 N-3） |
| **锚点 (Anchor)** | finding 中指向可核验位置的稳定引用，形如 `[SKILL:...]` / `[RULE:...]`，由判定器运行时校验存在性 |
| **谄媚污染 (Sycophancy Contamination)** | 在无客观依据时，评价者仍收敛到「有问题/可优化」的输出偏差 |
| **既有三门禁** | `pytest skills/`、`check-doc-links.py`、`audit-doc-health.py`（狭义）；广义含 `test_cross_skill_links.py` |

### 5.2 易歧义与同义词裁决 (Ambiguity & Synonym Resolution)

| 易混对 | 裁决 |
| :--- | :--- |
| 「事实」vs「发现」 | **严格区分**：事实是观测，发现是断言。采集器只产事实，判定器才产发现。二者分属不同进程，禁止合并 |
| 「技能改进」vs「技能修复」 | 本技能产出的是**修复线索**（finding），不是修复动作（N-2） |
| 「提示词」vs「根提示词」 | 本提案中「提示词」统称规范资产；「根提示词」特指 `contexts/AGENTS.md` |
| 「门禁」 | 不加限定时指**既有三门禁**；本技能自身称「判定器」或「spec-evolution 门禁」，避免混淆 |

### 5.3 禁用称谓与历史别名

| 禁用称谓 | 原因 | 应称 |
| :--- | :--- | :--- |
| 「自进化 / self-evolution」 | 暗示系统自动修改自身，与 N-2/N-3 直接冲突，且是本仓库已否决提案的历史用语 | 「**演进回路**」或「spec-evolution 审计」 |
| 「摩擦日志 / prompt-friction」 | 方案 B 的历史产物，本提案不使用该机制 | 「finding」 |
| 「LLM judge / 模型评审」 | 本提案结构性排除（G3） | 「判定器」 |

---

## 6. 未决问题与对齐清单 (Open Questions & Grilling Checklist)

- [x] 技能名 → `spec-evolution`（用户 2026-10-12 裁定）
- [x] v1 被测对象范围 → 全量 7 个技能（用户 2026-10-12 裁定）
- [x] 执行后端（P3 前置） → `workflow` 批量 fan-out（用户 2026-10-12 授权；仅用于实现阶段的并行编码，判定器运行时无 LLM 调用）
- [x] v1 是否纳入「设计质量」评价 → 否（N-1，§4 裁决）
- [x] 是否往 `contexts/AGENTS.md` 加条款 → 否（N-3）
- [x] **C-04 的 500 字符上限是否升格为成文规范？** → **否**（2026-10-12 裁定）。出处措辞为「if possible」，属软性建议；C-04 降为 MID，硬限归 C-05。依据见 §1.1 权威性裁定表
- [x] **`docs/llms.txt` 是否应作为技能注册面？** → **否，已剔除**（2026-10-12 裁定）。`generate-llms-txt.py` 扫描根为 `docs/`，结构上不可能收录 `skills/`；C-07 注册面 5→4。依据见 §4 裁决
- [x] **F-1~F-9 的修复是否纳入本次交付？** → **否，唯一例外 F-9**（2026-10-12 裁定）。检测与修复分离；F-9 因与「登记新技能」属同一处编辑而随附。依据见 §4 裁决
- [ ] **v2 是否启动？** 前置条件：让 §4 熔断报告模板产生可机械读取的落盘产物。→ 登记为 backlog，不在本次范围

---

## 7. 决策台账与默认假设 (Decision Ledger & Default Assumptions)

### 7.1 已决项 (Settled Decisions)

| 编号 | 决策 | 依据 |
| :--- | :--- | :--- |
| DK-1 | 采用方案 A：纯机械判定器，v1 不做设计质量评价 | §4 裁决 / 用户 N-1 红线 |
| DK-2 | 判定器零 LLM、零网络、纯标准库 | G3 / N-4；谄媚面消除的**结构性**保证 |
| DK-3 | 事实与发现分属两个进程（`collect-facts.py` / `judge.py`） | §5.2 术语裁决；便于独立测试与门禁断言 |
| DK-4 | 退出码语义 0/1/2 | 与 `taste-driven-designer` 既有脚本一致，沿用仓库惯例 |
| DK-5 | 锚点采用章节路径式 `[SKILL:...]` / `[RULE:...]` | 抗行号漂移；`[RULE:*]` 复用根提示词标题树 |
| DK-6 | 技能名 `spec-evolution` | 用户 m00219 裁定；符合 `<对象>-<名词>` 命名式 |
| DK-7 | v1 被测对象 = 全量 7 技能 + 根提示词 | 用户 m00219 裁定 |
| DK-8 | 触发路由 = 独立调用（主）+ goal-loop P5 增量挂载 | §3.6；避免把周期治理成本摊进每个任务，且不触碰根提示词 |
| DK-9 | 不自动修改任何文件 | N-2 / G6；人类二元裁决是唯一出口 |
| DK-10 | 交付通道 = Heavy Track（新增技能，触及公共契约与注册面） | goal-loop 铁律 8 |
| DK-11 | C-04 保留 500 阈值但降为 MID（advisory），**不升格为成文规范** | §1.1 权威性裁定；出处为 `writing-skills` 软性建议（措辞 if possible） |
| DK-12 | C-05 口径由「frontmatter 总长 ≥1024」改为「`description` ≥1024」 | Agent Skills 规范原文：1024 仅约束 `description`，规范中不存在 frontmatter 总长限制 |
| DK-13 | C-07 注册面 = 4 个（剔除 `docs/llms.txt`） | `generate-llms-txt.py` 扫描根为 `docs/`；派生文件不承载「存在性缺陷」，且与 C-02 冗余 |
| DK-14 | F-1~F-9 不随本次交付；仅 **F-9** 随「登记新技能」同处修正，其余 8 项登记 backlog | §4 裁决 |

### 7.2 已排除边界 (Explicitly Excluded Boundaries)

| 编号 | 排除项 | 排除依据 |
| :--- | :--- | :--- |
| EX-1 | 任务内摩擦记录机制（方案 B） | 机械谄媚；且经 agy 独立评估判 C·不可行（无数据源） |
| EX-2 | LLM 采样层与对抗用例集（方案 C，v1 范围） | 不可回归、假门禁风险；被测对象无落盘数据源 |
| EX-3 | 往根提示词加条款（方案 D） | 违反准入判据 + 指令预算稀释 |
| EX-4 | 自动修复 finding | N-2；会使本技能沦为「自动改自己规则的规则」，即 ball of mud 的机器化版本 |
| EX-5 | 对 `docs/project/reviews/**` 入链扫描 | GOVERNANCE.md 显式豁免 |
| EX-6 | 评价判据阈值本身的合理性 | N-7 |
| EX-7 | v1 交付 F-1~F-9 的修复 | 2026-10-12 裁定：检测与修复分离（§4）；**唯一例外 F-9** 随注册动作同处修正 |

### 7.3 默认假设 (Default Assumptions)

| 编号 | 假设 | 若假设不成立的影响 |
| :--- | :--- | :--- |
| DA-1 | 判定器在仓库根执行，`skills/` 与 `docs/` 为标准布局 | 若布局变更需显式传 `--repo-root`；不影响判定逻辑 |
| DA-2 | 「技能交付面四要素」（`references`/`scripts`/`templates`/`tests`）中，`scripts` 与 `templates` 对纯规程型技能可豁免 | **会导致 C-03 误报**。缓解：C-03 采「有则须完整、无则记 MID 提示」而非 HIGH 指控；v1 实测的 F-3 仍需人工确认是否属豁免场景 |
| DA-3 | `contexts/AGENTS.md` 基线为 97 行 / 10746 字节 | 基线随合法增删而变；缓解：基线写入 `references/` 常量文件，变更需显式提交，C-10 因此可审计 |
| DA-4 | 既有三门禁命令路径与参数稳定 | C-09 依赖其调用方式；若命令改名需同步采集器 |
| DA-5 | pytest 全量执行耗时约 30s，可接受在审计中同步执行 | 若技能规模增长致耗时显著上升，C-09 改为读取缓存结果或设为可选项 |

### 7.4 矛盾扫描记录 (Contradiction Scan)

| 检查项 | 结论 |
| :--- | :--- |
| 核心业务目标是否仍有未明确？ | 否——G1~G6 逐条对应 §3 的具体契约 |
| 关键边界与异常是否未确认？ | 否——已覆盖「技能目录不存在」「frontmatter 缺失」「注册面文件缺失」「既有门禁超时」「锚点路径不存在」五类边界（GI-3/GI-5） |
| 已决项之间是否互相矛盾？ | 否——N-2（不自动改）与 DK-9 一致；N-3（不加根条款）与 DK-8（挂载进技能内）方向一致；G4（全量扫描）与 DK-8（增量挂载）不矛盾，因二者是不同触发路径 |
| 与既有规范是否冲突？ | 否——C-04/C-06 的阈值均取自既有成文来源；N-4 与仓库无 CI 现状一致；G5 沿用既有 pytest 约定 |

---

## 8. 结晶去向预告 (Crystallization Preview)

| 结晶物 | 去向 |
| :--- | :--- |
| 判据表 C-01~C-10 与严重度语义（§3.2） | `skills/spec-evolution/references/checks-spec.md` |
| 锚点契约（§3.4） | `skills/spec-evolution/references/anchor-contract.md` |
| 采集器/判定器接口契约（§3.3） | `skills/spec-evolution/scripts/` + `SKILL.md` |
| 报告模板契约（§3.5） | `skills/spec-evolution/templates/evolution-report.md` |
| 门禁不变式 GI-1~GI-6（§3.7） | `skills/spec-evolution/tests/`（pytest 断言） |
| 触发路由（§3.6） | `skills/goal-loop/SKILL.md` P5 节（增量挂载点） |
| 架构设计书 | `docs/explanation/architecture/spec-evolution-design.md` |
| 全套注册 | `test_cross_skill_links.py::SKILL_NAMES`、`docs/index.md`、`docs/llms.txt`、`README.md`、`tools/skills-manager/collections/cr-agent-arsenal.json`，并重跑 `python3 contexts/install.py` |
| RFC 本体 | 交付后流转 `Implemented` 并置防腐声明（`proposals/archive/`） |
