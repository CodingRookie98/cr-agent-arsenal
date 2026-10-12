# `spec-evolution` 规格演进技能架构设计书 (Architecture & Design Specification)

> **文档控制信息**
> - **文档标识**: SKILL-DES-SPEC-EVOLUTION-2026
> - **当前版本**: V1.0.0 (事实层 / 判定层 / 门禁层三层分离 + 锚点硬门禁 + 零 LLM judge)
> - **设计所有者**: 王辉
> - **设计架构师**: DSH AI Agent
> - **创建日期**: 2026-10-12
> - **参考基准**:
>   - [RFC-0004 spec-evolution 演进回路](../../proposals/RFC-0004-spec-evolution.md)（已受理 · V0.3.0）
>   - Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet* ([arXiv:2310.01798](https://arxiv.org/abs/2310.01798))
>   - [Agent Skills 规范](https://agentskills.io/specification)（`description` 硬限 1024 字符）
>   - 内部技能生态：`goal-loop`（P5 文档归档挂载点）、`doc-governance`（Diátaxis 与文档门禁）、`dual-round-review`（交付终审）、`writing-skills`（技能形态与失败类型）

---

## 1. 背景与核心痛点 (Problem Statement)

1. **既有三门禁的判定域都是「产物正确性」，不是「产物存在性」**：
   `check-doc-links.py` 判链接有效（链接**存在**才可能断）、`audit-doc-health.py` 判文档结构健康（文档**存在**才可能不健康）、`pytest` 判已写代码的行为合规（测试**存在**才可能失败）。**没有任何一道门禁规定「什么东西必须存在」**。于是「技能缺 `tests/`」「缺架构设计书」「交付面目录不全」「`description` 超建议值」「注册面漏登记」「单文件超 1000 行」这类**存在性缺陷**落入盲区长期存续 —— 实测一次扫描即得 9 项真实缺口。

2. **演进回路的瓶颈在选择端，不在变异端**：
   本仓库的头号失败模式是「出问题就加一条」。那是**只有变异、没有选择**的进化产物（ball of mud）。变异很便宜（模型随时能提议一条新规则），选择很贵（判断该删哪条需要对照证据）。给变异端加闸门只会加速 ball of mud。

3. **指令预算的均匀削弱**：
   增加条款会**均匀削弱**所有条款的遵循度，而不是只影响新增那条。因此「改进提示词」不能等同于「往提示词里加内容」。

4. **把「评价」交给模型，必然产出机械谄媚**：
   开放式评价请求（「看看哪里可以优化」）隐含了期望答案的存在性；回答「没有」在训练分布中被判为没帮上忙。实证后果是「N 次熔断产出 N 条摩擦记录」——记录量与触发次数同阶，信号为零。更根本的是，让正在执行规则的模型去评判约束它自己的规则，直接违反 `contexts/AGENTS.md` §2 的**审查独立性 (Reviewer ≠ Author)**。

5. **行号引用不可核验**：
   条款的文本引用（`AGENTS.md:64`）会随文档演进漂移。实测：审查报告里引用的 `contexts/AGENTS.md:64` 出现 51 次，而当前该行**是空行**。基于行号的摩擦统计会持续制造幻觉热点。

---

## 2. 第一性原理与理论源流 (Theoretical Foundations)

### 2.1 变异—选择—遗传三要素

任何演进系统都需要三个要素。缺任何一个，进化都不发生（或退化为漂变）：

| 要素 | 含义 | 本仓库现状 |
| :--- | :--- | :--- |
| **变异** | 产出新规则候选 | 昂贵但频繁（人为提议） |
| **选择** | 判断哪条候选更好 | **缺失** —— 这正是本技能要补的 |
| **遗传** | 候选进入下一代会话 | 已具备（`contexts/install.py` 软链到各宿主） |

本技能的定位是**只补选择端**，且把选择端的判据从「模型意见」换成「脚本退出码」。

### 2.2 无外部反馈的自我纠错有害

Huang et al. (2023) 的结论是：没有外部反馈时，模型的自我批评会让性能**下降**。推论到本场景：**任务内的模型不得评判约束自己的规则**。因此本技能不在执行期提问，只做周期性的、有退出码的离线判定。

### 2.3 审查独立性（Reviewer ≠ Author）

`contexts/AGENTS.md` §2 要求审查者与作者分离。本技能把这条在工程上落实为**结构性约束**：判定结果由脚本产出，模型不参与打分；人类裁决区永久留白，模型代填即视为门禁违规。

---

## 3. 架构分层 (Architecture)

### 3.1 数据流

```
[仓库现状]
   │  collect-facts.py        ← 只回答「是什么」，不做判断
   ▼
facts.json (事实层)
   │  judge.py                ← 确定性映射，零 LLM / 零网络 / 纯标准库
   ▼
findings.json + evolution-report.md (判定层)
   │  pytest                  ← 对判定器自身回归
   ▼
GI-1~GI-6 门禁不变式 (门禁层)
```

三层职责严格分离：**采集不判定、判定不采集、门禁不判定业务语义只测自身不变式**。

### 3.2 事实层：`scripts/collect-facts.py`

只读、零第三方依赖。产出 `facts.json`，三个事实域：

- **S1 门禁事实**：跑四道既有门禁（`pytest` / `check-doc-links` / `audit-doc-health` / `cross_skill_links`）并记录 `{cmd, exit_code, summary}`；`--no-gates` 时 `gates = null`，此时 **C-09 不执行**，报告对该项输出「未采集门禁事实」而非「无失败」。
- **S2 结构事实**：逐技能记录目录存在性、`SKILL.md` frontmatter / `description` 字符数、最大文件行数、超限文件、跨技能相对链接、架构设计书。
- **S3 注册事实**：四个注册面（`SKILL_NAMES` / `docs/index.md` / `README.md` / collections）是否登记该技能；根提示词行数、字节数与基线对比、标题树。

**只读不变式 (GI-6)**：采集器与它跑的门禁除显式 `--out` 外不得在仓库内创建、修改或删除任何文件，也不得创建目录。**落实方式**：门禁子进程一律注入 `PYTHONDONTWRITEBYTECODE=1`（`subprocess_env()`）——仅靠命令行 `-B` 不足以覆盖全部路径，`audit-doc-health.py` 内部的 `importlib` 动态加载不受 `-B` 约束、会写出 `__pycache__`；`pytest` 两条命令另带 `-B -p no:cacheprovider`。

### 3.3 判定层：`scripts/judge.py`

把事实映射为 finding。退出码语义：

| 退出码 | 含义 |
| :--- | :--- |
| `0` | 无 BLOCKER/HIGH（可含 MID 级 advisory finding） |
| `1` | 存在 BLOCKER 或 HIGH 级 finding |
| `2` | 用法/输入错误，或**锚点校验失败**（fail-closed，拒绝写出任何产物） |

排序 `(严重度, 技能名, 判据 ID, 锚点, 证据命令, 观测值)` —— 与输入字典顺序无关，保证 `findings.json` 双跑逐字节相同。

### 3.4 门禁层：`tests/test_gate_invariants.py`

GI-1~GI-6 的对象是**本技能自身**，不是被测技能：

| 不变式 | 断言 |
| :--- | :--- |
| **GI-1** | 模板占位符集合 == 渲染器变量集合；无未替换占位符；同一输入双跑逐字节相同 |
| **GI-2** | findings 排列不依赖输入字典顺序 |
| **GI-3** | 报告锚点是 `findings.json` 锚点的子集；幻影/畸形锚点必被拒 |
| **GI-4** | 人类裁决区永久留白（模板副本满足，不是靠渲染时抹除） |
| **GI-5** | 退出码严格 0 / 1 / 2 三态 |
| **GI-6** | 采集与门禁运行零仓内副作用 |

### 3.5 报告模板：`templates/evolution-report.md`

报告以 `## 人类裁决 (Human Verdict)` 结尾，其下一律为空白表格行。判定器输出到该标题即停止写入。

---

## 4. 关键决策与理由 (Key Decisions)

### 4.1 为什么不做 LLM judge

自评对上下文敏感、有讨好倾向、无对照基线 —— 产出的是**假设**而非**结论**。本技能把「哪个条款该改」这个判断压缩成「哪条机械判据被触发、证据命令的退出码是多少」。为此付出的代价是**判定力上限**（见 §6），换来的是**可复现、可回归、可反驳**。

替代方案「让子智能体评审技能」被否决：它没有解决谄媚，只是把谄媚换了个执行体，且引入非确定性使回归测试不可能。

### 4.2 为什么默认 fail-closed

锚点不可解析（目标路径不存在、行号越界、章节标题不在标题树中）时，`judge.py` **退出 2 并拒绝写出任何产物**，而不是降级为「锚点可疑」的 finding。

理由：锚点是本技能唯一的抗幻觉手段。若允许带幻影锚点的报告流出，报告本身就变成了不可核验的文本——回到 §1.5 的起点。宁可本次不出报告，也不出一份无法核验的报告。

### 4.3 为什么人类裁决区永久留白

Reviewer ≠ Author。判定器负责**列出**候选，人类负责**裁决**采纳或驳回。模板与渲染器都不写裁决内容，GI-4 把这条变成断言。这也是与 `dual-round-review` 的「Zero Blockers 由独立子智能体签署」同构的防自证设计。

### 4.4 为什么用章节路径锚点而不是行号

`[RULE:§3-质量门槛]` 指向标题树（`## 3. …` / `### 质量门槛 …`），判定器解析标题树校验存在性。章节标题比行号稳定得多，且当文档重构后锚点会**显式失败**而不是静默指向错误位置。第三种锚点形式 `[REPO:<repo-relative-path>[:<line>]]` 用于技能目录之外的核验位置（注册面、门禁脚本）。

### 4.5 为什么零第三方依赖、不引入 CI

与仓库既有的「零依赖 + pytest 直跑」生态一致（`contexts/AGENTS.md` §3：严格沿用项目既有生态）。判定器只用标准库，任何人都能 `python3 judge.py` 复现同一结论。CI 属于宿主侧决策，不在本技能职责内。

---

## 5. 与既有技能的职责边界 (Boundaries)

| 技能 | 管什么 | 与本技能的区别 |
| :--- | :--- | :--- |
| [`doc-governance`](./doc-governance-design.md) | `docs/` 文档的链接、健康度、索引 | 本技能管**技能与根提示词**，不管文档制品 |
| [`dual-round-review`](./dual-round-review-design.md) | 单次**交付物**的对抗审查 | 本技能管**跨时间的演进**，不做单次终审 |
| [`goal-loop`](./goal-loop-design.md) | **执行**长程任务 | 本技能评估**技能自身**，不执行任务；仅作为 P5 文档归档的挂载点 |
| **`spec-evolution`** | 采集摩擦 → 复现证据 → 确定性判定 → 生成带锚点的改进候选（人类二元裁决） | — |

---

## 6. 已知表达上限 (Known Limits)

与 [`references/checks-spec.md`](../../../skills/spec-evolution/references/checks-spec.md) §4 保持一致，显式登记、不在 v1 掩饰：

1. **C-10 无法判定「理由是否成立」**：准入判据允许根提示词净增长（前提是同一提交给出等量删减或不可压缩的理由）。判定器只能观测「是否净增长」，**无法**判定理由是否成立。故 C-10 报告文案固定为中性提示，而非指控。
2. **C-03 存在误报面**：`scripts/` 与 `templates/` 对纯规程型技能可豁免。C-03 采「有则须完整、无则记 MID 提示」，命中项须人工确认是否属豁免场景。
3. **C-08 与 `test_cross_skill_links.py` 的正则同源但不同文件**：两处可能漂移。缓解：C-09 会运行该测试本身，一旦语义背离，C-09 先失败。
4. **不做设计质量评价**：职责重叠、技能该不该存在、是否过重，一律不在判定域内。此类问题无退出码可复现，纳入即等于给谄媚开门。
5. **检测与修复分离**：本技能只产出候选，不自动修改任何文件。修复是独立的、由人类裁决后另行立项的动作。

---

## 7. 演进方向 (Roadmap)

- **v1（当前）**：覆盖 `skills/` 交付面完整性 + 四个注册面 + 根提示词净增长观测。判据表 C-01~C-10。
- **v2（未启动）**：是否把 `docs/` 制品与 `docs/project/plans/` 的方案完整性纳入判定域。启动前提是先把 v1 跑出若干轮真实结论，验证判定器的信噪比。

v2 的启动与否记录在 [RFC-0004](../../proposals/RFC-0004-spec-evolution.md) §6 未决项，由人类裁决。

---

## 8. 相关文档 (See Also)

- 技能规程：[`skills/spec-evolution/SKILL.md`](../../../skills/spec-evolution/SKILL.md)
- 判据表：[`references/checks-spec.md`](../../../skills/spec-evolution/references/checks-spec.md)
- 锚点契约：[`references/anchor-contract.md`](../../../skills/spec-evolution/references/anchor-contract.md)
- 需求确认文档：[RFC-0004 spec-evolution 演进回路](../../proposals/RFC-0004-spec-evolution.md)
- 落地计划：[2026-10-12-spec-evolution.md](../../project/plans/2026-10-12-spec-evolution.md)
