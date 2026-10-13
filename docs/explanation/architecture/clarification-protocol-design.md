# `clarification-protocol` 需求澄清与收敛协议技能架构设计书 (Architecture & Design Specification)

> **文档控制信息**
> - **文档标识**: SKILL-DES-CLARIFICATION-PROTOCOL-2026
> - **当前版本**: V1.0.0 (六节澄清协议 + 交付面四件套：展开 / 骨架 / 校验 / 回归)
> - **设计所有者**: 王辉
> - **设计架构师**: DSH AI Agent
> - **创建日期**: 2026-10-13
> - **参考基准**:
>   - [skills/clarification-protocol/SKILL.md](../../../skills/clarification-protocol/SKILL.md) —— 规程唯一真相源（六节正文）
>   - [references/decision-ledger.md](../../../skills/clarification-protocol/references/decision-ledger.md) —— §3 决策台账的展开（字段、去重、提前收敛）
>   - [references/convergence-checklist.md](../../../skills/clarification-protocol/references/convergence-checklist.md) —— §4 三项自检的展开（逐问判定与反例）
>   - [scripts/check-decision-ledger.sh](../../../skills/clarification-protocol/scripts/check-decision-ledger.sh) —— 台账结构机械校验器（离线只读）
>   - [templates/decision-ledger-template.md](../../../skills/clarification-protocol/templates/decision-ledger-template.md) / [templates/requirement-confirmation-template.md](../../../skills/clarification-protocol/templates/requirement-confirmation-template.md) —— 台账与需求确认文档骨架
>   - [tests/test_clarification_protocol_contract.py](../../../skills/clarification-protocol/tests/test_clarification_protocol_contract.py) —— 交付面与硬约束回归
>   - [skills/goal-loop/SKILL.md](../../../skills/goal-loop/SKILL.md) —— 熔断预算的重入门控与成本上限由其 failure-recovery-protocol 承载
>   - [skills/spec-evolution/references/checks-spec.md](../../../skills/spec-evolution/references/checks-spec.md) —— C-01 / C-02 / C-03 交付面判据的定义源

---

## 1. 背景与核心痛点 (Problem Statement)

多轮澄清是长程任务里最容易被"看起来在推进"掩盖的失控点。三种失败形态反复出现：

1. **术语未对齐就开问**：同一个词在提问者与裁决者眼中指向不同对象（"预设""技能""注册面"），答非所问被误读为需求变更，后续所有问题都建在流沙上。
2. **提问无排序**：高影响、强依赖的问题与低影响、可自决的问题混在同一轮抛出，决策者被细节淹没，关键分叉反而被跳过；低影响问题重复占用人类注意力。
3. **无台账导致的"换说法重开"**：已裁决的结论被换一种措辞重新提问，决策成本反复支付；被明确排除的边界漂回讨论，任务是"回合数"而非"收敛度"的函数。

与之对应的反面同样有害：把"问完所有边界"当出口，问题预算耗尽仍不收敛；把"没问题了"当收敛信号——它既不可判定也不可复核。

## 2. 设计目标与非目标 (Goals & Non-Goals)

**目标**

- 让澄清过程**可判定**：每一轮结束时能机械回答"是否收敛"，而不是凭感觉宣布。
- 让决策**可追溯**：任一已决结论都能指出出处（用户裁决轮次 / 证据文件:行 / 权威规范）；任一被排除边界都能指出排除依据与复开条件。
- 让提问**有性价比**：按依赖强度 × 实现影响排序，高影响进本轮清单，低影响直接转默认假设并登记。
- 让纪律**机械可查**：把台账的三类必填字段交给离线脚本校验，收敛自检前先跑一次。

**非目标**

- 不产出代码、不做技术选型裁决——本技能只负责"问什么、何时停、怎么记"。
- 不代替人类的裁决权：脚本只校验**类别与字段是否登记**，不判断结论对错与依据是否成立。
- 不建立全量术语表：术语先行的范围仅限"易产生歧义"的词，扩为全量词表即为过度设计。

## 3. 架构总览 (Architecture Overview)

```text
触发（宏观目标 / 多路径 / 多轮问答 / 已决项被重开）
        │
        ▼
§1 术语先行 ── 全局前置项；术语未对齐则不进入需求澄清
        │
        ▼
§2 提问排序 ── 依赖强度 × 实现影响 → 本轮清单 / 直接转默认假设
        │
        ├──► §3 决策台账 ── 已决项 D-NN / 已排除边界 E-NN / 默认假设 A-NN
        │            └── scripts/check-decision-ledger.sh（结构校验，0/1/2）
        │
        ▼
§4 三项收敛自检 ── 目标 / 边界 / 矛盾；三项皆否定即收敛
        │            └── references/convergence-checklist.md（逐问判定与反例）
        ▼
§5 熔断预算与升级 ── 提问预算耗尽 → 升级人类；重入门控与成本上限见 goal-loop
        │
        ▼
§6 显式化思考 ── 约束 → 候选 → 取舍 → 结论
        │
        ▼
templates/ ── 台账骨架（落进计划文件）/ 需求确认文档骨架（P0 出口产物）
```

**与相邻技能的接缝**

- **goal-loop**：本技能是其 P0 阶段的澄清与收敛规程（收敛判据、提问预算）；预算耗尽后的重入门控四条与成本上限 `min(任务总预算 × 25%, 剩余预算 ÷ 3)` 由 goal-loop 的 failure-recovery-protocol 承载，本技能只引用不复写。
- **writing-plans**：本技能产出的需求确认文档是计划文档的上游输入；计划文件里可直接内嵌台账模板。
- **dual-round-review**：审查者对照的是"已冻结的契约与台账"，不是重新澄清需求；台账就是 R1 判定"是否偏离意图"的基线。

## 4. 核心机制 (Core Mechanisms)

### 4.1 术语先行（§1，全局前置项）

进入需求澄清前，先把可能歧义的词对齐到同一指称。判据是"该词是否会在后续被两种以上理解"——因此范围为**易产生歧义**的词，不扩为全量词表。

### 4.2 提问排序（§2，依赖强度 × 实现影响）

| 象限 | 处置 |
| :--- | :--- |
| 高依赖 × 高影响 | 进本轮清单，且给出 2–3 个可选方案做选择题（附取舍与推荐） |
| 高影响 × 低依赖 | 进本轮清单，可与其它问题并行提出 |
| 低影响（任意依赖） | 直接转默认假设并登记（取值、影响级别、可否决性、反转成本） |

### 4.3 决策台账（§3，三类登记 + 去重纪律）

台账是"澄清产出"的唯一载体，三类登记各有必填字段（详见 references/decision-ledger.md）：

| 类别 | 编号 | 核心必填字段 | 违约形态 |
| :--- | :--- | :--- | :--- |
| 已决项 | `D-NN` | 结论本身、**出处**、影响面 | 写"常识/惯例/一般认为"当出处 |
| 已排除边界 | `E-NN` | 被排除的方案或范围、**排除依据**、复开条件 | 只写"不需要/不合适"，无复开条件 |
| 默认假设 | `A-NN` | 具体取值、**影响级别**、可否决性、反转成本 | 取值写"待定/按需" |

**去重纪律**：同一问题换措辞重开即违规；"已决项被换一种说法重开"是本技能的显式触发条件之一。

### 4.4 三项收敛自检（§4）

依次回答三问：**Q1** 核心业务目标与流程是否仍有未明确；**Q2** 关键边界与异常是否仍有未确认；**Q3** 已决项之间是否存在相互矛盾。**三项皆否定即收敛**——不以"穷尽问题"为出口。`没问题了` 不算收敛：它不可判定，也无法复核；自检必须落成可指认的判定句（references/convergence-checklist.md 给出逐问标准与反例对照）。

### 4.5 熔断预算与升级（§5）

- 错误层：同一错误连续 3 次未解决即 STOP → 记录 → 检索 → 升级，不得继续试错。
- 审查层：Delta Re-Loop 最多 5 轮。
- 提问层：预算耗尽即升级人类裁决；重入门控与成本上限引用 goal-loop，不在本技能内复写。

### 4.6 显式化思考（§6）

关键架构决策、复杂重构或多步骤任务前，用思考块写出"约束 → 候选 → 取舍 → 结论"，逻辑自洽后再落笔。

## 5. 交付面与机械契约 (Delivery Surface & Contracts)

| 交付物 | 形态 | 机械契约 |
| :--- | :--- | :--- |
| [SKILL.md](../../../skills/clarification-protocol/SKILL.md) | 规程正文（六节） | 唯一真相源；frontmatter `name` 与目录同名、`license: MIT`、description < 1024 字符（硬限） |
| [references/decision-ledger.md](../../../skills/clarification-protocol/references/decision-ledger.md) | 展开文档 | 不得引入新政策，只细化 §3 的字段与判定式 |
| [references/convergence-checklist.md](../../../skills/clarification-protocol/references/convergence-checklist.md) | 展开文档 | 只细化 §4 的逐问判定与反例 |
| [templates/decision-ledger-template.md](../../../skills/clarification-protocol/templates/decision-ledger-template.md) | 骨架 | 示例表格必须自洽于校验器（字段名写在单元格内） |
| [templates/requirement-confirmation-template.md](../../../skills/clarification-protocol/templates/requirement-confirmation-template.md) | 骨架 | 术语表 / 已决项 / 已排除边界 / 默认假设 / 收敛结论 / 待裁决分叉六段 |
| [scripts/check-decision-ledger.sh](../../../skills/clarification-protocol/scripts/check-decision-ledger.sh) | 校验器 | 离线、只读、无网络；退出码 **0 = 合规 / 1 = 不合规 / 2 = 用法错误**；围栏内示例不计入 |
| [tests/test_clarification_protocol_contract.py](../../../skills/clarification-protocol/tests/test_clarification_protocol_contract.py) | 回归 | 静态契约（frontmatter、六节、硬约束、链接、交付面非空）+ 校验器行为（合规/四类缺失/围栏豁免/三种用法错误/只读性） |

**校验器的判定边界**：它只回答"三类小节是否齐备、每类是否至少一条数据行、必填字段名是否出现在该行"。它**不判断**结论是否正确、依据是否成立、影响级别是否恰当——这些属于人的裁决，工具不得外判。

## 6. 判据与边界 (Criteria & Boundaries)

**使用**：目标宏观或含糊；存在多种技术路径；多轮问答中；已决项被换一种说法重开；需要在"问用户"与"登记默认假设"之间取舍；澄清轮次有失控迹象。

**不用**：单文件微调、指令明确的直接执行、只读检索类问答——直接干活即可。

**红线**

- 不把"问完所有边界"当终止条件；收敛判据是三项自检的结果，不是问题数量。
- 不重复提问已登记的已决项与已排除边界；重开必须走复开条件。
- 不把术语先行扩为全量词表。
- 不在本技能内复写 goal-loop 的重入门控与成本上限。

## 7. 演进方向 (Roadmap)

- **description 收敛**：当前 623 字符，超出 spec-evolution C-04 的建议值（≤ 500）；压缩会改变触发面，需与触发回归一起做，已登记为存量债务（BK-0041）。
- **台账校验器扩展**：当前为结构校验；后续可在不引入人类裁决的前提下，增加"编号连续性"与"复开条件非空"的机械检查。
- **与计划文件的耦合**：评估在 writing-plans 的计划模板中直接内嵌台账骨架，减少一次复制。

## 8. 相关文档 (See Also)

- [技能规程](../../../skills/clarification-protocol/SKILL.md)
- [决策台账展开](../../../skills/clarification-protocol/references/decision-ledger.md)
- [三项收敛自检展开](../../../skills/clarification-protocol/references/convergence-checklist.md)
- [台账结构校验器](../../../skills/clarification-protocol/scripts/check-decision-ledger.sh)
- [goal-loop 技能](../../../skills/goal-loop/SKILL.md)（熔断预算的重入门控与成本上限）
- [spec-evolution 交付面判据](../../../skills/spec-evolution/references/checks-spec.md)
- [技能注册与治理总入口](../../index.md)
