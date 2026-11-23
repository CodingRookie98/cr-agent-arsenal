# `clarification-protocol` 需求澄清与收敛协议技能架构设计书 (Architecture & Design Specification)

> **文档控制信息**
> - **文档标识**: SKILL-DES-CLARIFICATION-PROTOCOL-2026
> - **当前版本**: V2.0.0 (去壳提纯：废除 0/8 假阳性脚本与冲突双模板，收敛为 4 列单表精品微技能)
> - **设计所有者**: 王辉
> - **设计架构师**: DSH AI Agent
> - **创建日期**: 2026-10-13
> - **参考基准**:
>   - [skills/clarification-protocol/SKILL.md](../../../skills/clarification-protocol/SKILL.md) —— 规程唯一真相源（§0–§4 精品微技能正文）
>   - [tests/test_clarification_protocol_contract.py](../../../skills/clarification-protocol/tests/test_clarification_protocol_contract.py) —— 交付面、链接与防回流契约哨兵
>   - [架构评估报告](../analysis/2026-11-23-clarification-protocol-architecture-evaluation.md) —— V1.x 过度设计诊断、8 份真实 RFC 实跑 0/8 假阳性实证与 V2.0.0 去壳方案
>   - [同类前沿调研报告](../analysis/2026-11-23-clarification-protocol-peer-research.md) —— 2025–2026 学术界与业界标杆对比基准
>   - [skills/goal-loop/SKILL.md](../../../skills/goal-loop/SKILL.md) —— P0 澄清阶段挂载点（错误层 / 审查层熔断仍归 `goal-loop` 与 `dual-round-review` 各自承载）
>   - [ADR-0003 退役 spec-evolution 技能并下沉哨兵测试](../decisions/0003-retire-spec-evolution.md) —— C-01 / C-05 / C-07 交付面硬护栏现由 `skills/_shared/tests/test_skill_surface_sentinels.py` 统一承载

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V2.0.0** | 2026-11-23 | AI Agent | 王辉 | 去壳提纯：废除 0/8 假阳性脚本 `check-decision-ledger.py/.sh`、冲突双模板与过度展开参考文档；统一对齐 RFC 4 列单表；补齐先自查事实（§0）与 ≤5 题软预算（修复旧 L72 空指针）；剥离越界熔断与显式思考，精简契约哨兵与 `description`（≤400 字符） |
| **V1.0.1** | 2026-11-23 | AI Agent | 王辉 | 随 `ADR-0003` 移除已退役的 `skills/spec-evolution/references/checks-spec.md` 外链，对齐现行哨兵来源 |
| **V1.0.0** | 2026-10-13 | DSH AI Agent | 王辉 | 初版（六节澄清协议 + 交付面四件套：展开 / 骨架 / 校验 / 回归） |

---

## 1. 背景、痛点与 V2.0.0 去壳演进 (Problem Statement & V2 Evolution)

多轮澄清是长程任务里最容易被「看起来在推进」掩盖的失控点，反复出现四类失效形态：

1. **能自查却打扰人类**：把读代码、查配置或翻文档即可确认的客观事实抛给用户，徒增上下文切换成本。
2. **术语未对齐就开问**：同一个词在提问者与裁决者眼中指向不同对象，答非所问被误读为需求变更，后续讨论建在流沙上。
3. **提问无排序且无软上限**：高影响架构分叉与低影响细节混在同一轮抛出，或试图「问完所有边界」替代收敛，迅速触及人类审查疲劳倒 U 曲线。
4. **无轻台账导致的「换说法重开」**：已裁决结论或被排除边界只留在对话流里，稍后被换一种措辞反复重问；而空口「没问题了」既不可判定也无法复核。

### V1.x → V2.0.0 去壳提纯动因

经 [架构评估报告](../analysis/2026-11-23-clarification-protocol-architecture-evaluation.md) 实证审计，V1.x 在保留 4 条高密度核心认知纪律的同时，因被动迎合现已退役的 `spec-evolution` 交付面指标，堆积了 6 个高维护税、零实战消费的外壳文件：

- **0/8 假阳性损坏脚本**：对本仓全部 8 份真实 `docs/proposals/RFC-*.md` 实跑 `scripts/check-decision-ledger.py`（及兼容壳 `scripts/check-decision-ledger.sh`）通过率为 **0/8**，却对空列+违禁「待定」放行 `rc=0`，且存在 Windows CRLF 崩溃与脆弱围栏解析等 8 类缺陷。
- **Split-Brain 双模板冲突**：`templates/decision-ledger-template.md`、`templates/requirement-confirmation-template.md` 以及 `references/decision-ledger.md`、`references/convergence-checklist.md` 强制 5 张表 16 字段与单元格内重复列名，既与 `doc-governance` RFC 规范冲突，也被本仓 RFC-0005~0008 作者用脚投票抛弃（实战全部自发压平为 1 张 4 列单表）。
- **职责拼盘与循环空指针**：原 `SKILL.md` §5 越界杂糅了分属 `goal-loop` / `dual-round-review` 的错误层与审查层熔断，而唯一归属本技能的「`提问层 | 本节`」（原 L72）竟无任何具体预算定义；原 §6「显式化思考」与澄清无专属耦合。

V2.0.0 遵循「**剥离全部坏脚本与冲突外壳，提纯为单文件精品微技能**」路线，彻底清偿上述债务。

## 2. 设计目标与非目标 (Goals & Non-Goals)

**目标**

- **先自查后提问**：把客观事实核查留在智能体内部，让人类注意力严格聚焦于业务取舍与不可逆决策。
- **轻台账可追溯**：用与实战 RFC 统一的 **4 列单表**原地落盘，消除平行冗余文档与模板分裂；每条已决项、已排除边界与默认假设皆可指认依据。
- **提问有分级与软上限**：按依赖强度 × 实现影响排序，低影响直转默认假设，单次核心澄清默认 ≤ 5 个关键问题，超限闭合主干或结构化升级。
- **出口内联可判定**：收敛前内联核对目标 / 边界 / 矛盾三问，不靠单开「无新问题回合」制造仪式感，也不容许空口「没问题了」。

**非目标**

- 不编写离线正则脚本校验自然语言台账——结构正确不等于决策正确，机械强校验已被实证为负价值维护税。
- 不另造独立台账模板或与 `doc-governance` 竞争 RFC 结构——台账直接原地嵌入当前 RFC / 计划 / Spec 正文。
- 不越界承载错误重试熔断、审查 Delta 轮次上限或通用显式思考规范。
- 不建立全量术语词典：术语先行严格限定于易歧义核心词。

## 3. 架构总览 (Architecture Overview)

```text
触发（宏观/含糊目标 · 不可逆多路径 · 多轮问答发散 · 已排除边界被重开）
        │
        ▼
§0 先自查事实 (Lookup Before Asking) ── 读代码/配置/文档自证客观事实，只问人类决策
        │
        ▼
§1 术语先行 (Terminology First) ── 对齐易歧义核心词并登记（禁扩全量词典）
        │
        ▼
§2 按影响筛问与软预算 (Impact-Gated Asking & Soft Cap)
        ├── HIGH（影响架构/契约/主干）──► 本轮提问（2–3 方案选择题，软上限 ≤ 5 关键题）
        ├── LOW （仅影响局部细节）     ──► 直转显式默认假设登记
        └── 触顶仍未收敛              ──► 闭合主干 + 次要分叉记默认假设 / 携四项要素升级裁决
        │
        ▼
§3 极简单表决策台账 (Lightweight Decision Ledger)
        └── 1 张 4 列单表（编号 | 类型 | 条目 | 依据 / 影响级别），原地落盘 RFC/计划/Spec；禁止换说法重开已排除边界
        │
        ▼
§4 出口三问内联自核 (Convergence Self-Check)
        └── 目标 / 边界 / 矛盾三问皆否即收敛输出；任一为是则定向补问
```

**与相邻技能的接缝**

- **`goal-loop`**：本技能是其 P0 需求澄清阶段的轻量化规程；错误层 3-Tries 与重入门控归属 `goal-loop`，不再在本技能复写。
- **`doc-governance`**：决策台账统一对齐 RFC-0005~0008 实战形态的 4 列单表，原地落入 RFC / 计划 / Spec，彻底消除 Split-Brain。
- **`dual-round-review`**：R1 审查以已落盘的台账与确认文档为意图基线；审查层 Delta 轮次上限归属 `dual-round-review`。

## 4. 核心机制 (Core Mechanisms)

### 4.1 先自查事实，只问人类决策（§0）

吸收业界标杆最佳实践：凡通过读取代码、配置、文档或目录树能够确认的事实，一律由智能体自主取证；人类裁决带宽只保留给业务目标权衡、范围约束与不可逆架构分叉。

### 4.2 术语先行（§1）

在进入需求与范围澄清前，对齐可能产生两种以上理解的核心术语，并直接写入 RFC / 计划 / Spec 术语段落。易歧义术语豁免「低影响转默认假设」，但严禁扩张为全量词典。

### 4.3 依赖 × 影响排序与 ≤ 5 题软预算（§2）

| 级别 | 处置方式 |
| :--- | :--- |
| **HIGH**（强依赖或影响主干/架构/公共契约） | 进本轮问题清单；涉及决策时给出 2–3 个可行方案（优缺点对比 + 推荐理由），引导做选择题 |
| **LOW**（仅影响局部实现细节） | 直接转为显式默认假设并登记，不占用人类注意力 |

单次核心澄清设置 **≤ 5 个关键问题**软预算（彻底替代旧 L72「提问层：本节」空指针）。预算触顶仍未收敛时，优先闭合主干并将次要分叉记为默认假设；若确存高风险不可代决分叉，则携「**现状 / 已验证事实 / 当前瓶颈 / 待裁具体分叉**」四项升级人类裁决。

### 4.4 极简 4 列单表决策台账与去重纪律（§3）

统一收敛为 1 张 4 列单表 `| 编号 | 类型 | 条目 | 依据 / 影响级别 |`，原地落盘在当前 RFC / 计划 / Spec 正文：

- **`已决项`（`D-NN`）**：一句话可执行结论 + 用户裁决轮次或证据出处。
- **`已排除边界`（`E-NN`）**：明确不做的方案或范围 + 排除依据（含复开前提，若有）。
- **`默认假设`（`A-NN`）**：未提问即采用的具体取值 + 低影响说明与反转成本。
- **去重铁律**：禁止换一种措辞重开已排除边界——重复提问即违规；提前收敛时，低影响分支必须登记为默认假设，未登记即未收敛。

### 4.5 出口三问内联自核（§4）

输出确认文档前内联核对三问：① 核心业务目标与主干流程是否仍有未明确？② 关键边界、契约与异常情况是否仍有未确认？③ 台账条目之间是否存在相互矛盾？**三问皆否即收敛**，不以穷尽所有细节为出口，也无需单开「无新问题回合」消耗交互轮次；任一为是，则下一轮只针对该项定向补问。

## 5. 交付面与机械契约 (Delivery Surface & Contracts)

### 5.1 现行交付面（极简 2 文件）

| 交付物 | 形态 | 机械契约 |
| :--- | :--- | :--- |
| [SKILL.md](../../../skills/clarification-protocol/SKILL.md) | 规程正文（§0–§4，65–85 行） | 唯一真相源；合法 YAML frontmatter、`name == clarification-protocol`、`license: MIT`、`description` ≤ 400 字符（哨兵软限 ≤ 500，硬限 < 1024） |
| [tests/test_clarification_protocol_contract.py](../../../skills/clarification-protocol/tests/test_clarification_protocol_contract.py) | 轻量表面与防回流哨兵 | 满足 C-01；守护 frontmatter 与 `description` 软限、围栏成对闭合、无跨技能相对外链、技能内相对链接物理可达且不越界、禁止已退役外壳关键词与旧空指针回流 |

### 5.2 V2.0.0 已退役的外壳文件（历史溯源）

以下 6 个 V1.x 外壳文件已于 V2.0.0 移除，不再作为交付面维护：

- `skills/clarification-protocol/scripts/check-decision-ledger.py` 与 `skills/clarification-protocol/scripts/check-decision-ledger.sh`（8 份真实 RFC 实跑 0/8 假阳性且存在 8 类缺陷）
- `skills/clarification-protocol/references/decision-ledger.md` 与 `skills/clarification-protocol/references/convergence-checklist.md`（过度展开为 5 表 16 字段，正文精华已收束进 `SKILL.md`）
- `skills/clarification-protocol/templates/decision-ledger-template.md` 与 `skills/clarification-protocol/templates/requirement-confirmation-template.md`（与 `doc-governance` RFC 规范 Split-Brain 冲突且 0% 实战采用）

## 6. 判据与边界 (Criteria & Boundaries)

- **使用**：目标宏观或含糊；存在多种不可逆路径；多轮问答出现发散或已排除项被换说法重开；需要在「问用户」与「记默认假设」之间取舍。
- **不用**：单文件微调、指令明确的直接执行、或查代码/文档即可回答的只读检索——直接干活即可。
- **红线**：
  - 能通过代码/配置/文档自查的事实，严禁向用户发问。
  - 不把「问完所有细节」当终止条件；收敛判据是台账留痕 + 出口三问自核。
  - 不换说法重开已登记的已排除边界；不将术语先行扩为全量词典。
  - 不复写 `goal-loop` 或 `dual-round-review` 的错误/审查层熔断细则。

## 7. 演进方向 (Roadmap)

- **与 `doc-governance` RFC 4 列单表持续对齐**：后续若在 `doc-governance` 中正式将 RFC-0005~0008 的 4 列单表结晶为推荐范式，双方共用同一表头语义，不再出现第二套模板。
- **按真实澄清案例持续微调**：仅基于真实多轮澄清暴露出的歧义或发散模式小步修订 `SKILL.md`，严禁为追求外部静态指标而重新堆砌无实战消费的校验脚本或冗余模板。

## 8. 相关文档 (See Also)

- [技能规程 (SKILL.md)](../../../skills/clarification-protocol/SKILL.md)
- [契约与防回流哨兵测试](../../../skills/clarification-protocol/tests/test_clarification_protocol_contract.py)
- [架构评估报告（V1.x 过度设计诊断）](../analysis/2026-11-23-clarification-protocol-architecture-evaluation.md)
- [同类工程及学术前沿调研报告](../analysis/2026-11-23-clarification-protocol-peer-research.md)
- [goal-loop 技能](../../../skills/goal-loop/SKILL.md)
- [ADR-0003 退役 spec-evolution 技能](../decisions/0003-retire-spec-evolution.md)
- [技能注册与治理总入口](../../index.md)
