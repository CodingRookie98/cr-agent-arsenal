# `clarification-protocol` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-CLARIFICATION-EVAL-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于 `skills/clarification-protocol/` 全部 8 个源文件（949 行 / 48.0 KB）、设计书、7 次 Git 提交历史、对本仓全部 8 份 `docs/proposals/RFC-*.md` 实跑 `check-decision-ledger.py` 与 28 份计划实证审计，并对照配套调研报告 [2026-11-23-clarification-protocol-peer-research.md](./2026-11-23-clarification-protocol-peer-research.md)。
> - **证据分级**: 【A】一手（本仓库源码/行号/实跑 8 份 RFC 与 8 组边界探针、外部标杆一手源码）｜【B】二手转引（学术论文摘要）｜【C】架构师诊断与重构设计

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `clarification-protocol` 8 文件体检、8 份真实 RFC 实跑 0/8 假阳性审计、`check-decision-ledger.py` 8 类实测缺陷、Split-Brain 双模板剖析与轻量重塑方案 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`clarification-protocol` 是否过度设计？是否需要重构？**

**结论：这是一个「核心认知理念领先业界半步，但工程载体彻底沦为治理债务」的典型标本。它提炼的四条核心心法（术语先行、依赖×影响排序、低影响显式默认假设、非空口收敛判据）获得 2026 最新顶会实证强力背书；但为了应付现已退役的 `spec-evolution` 交付面指标，它在 1 天内被硬灌进了 741 行重型外壳——产出了一套本仓 8/8 真实 RFC 100% 拒绝、却对空单元格+「待定」作弊放行 `rc=0` 的损坏校验脚本，以及两份与 `doc-governance` 全面冲突的零用模板。只需果断剥壳去债，它就能还原为一个极高信噪比的 60–80 行精品微技能。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **演化失真与体量倒挂** | 8 文件 **949 行 / 48.0 KB**（`tests/` 428 L + `scripts/` 137 L 占 **59.5%**）；7 次提交中后续 5 次（贡献 **90.7% 代码**）100% 属被动应付已退役 `spec-evolution` 体检与 Python 迁移，**0 次来自真实业务澄清迭代** | 原本是 `AGENTS.md` 瘦身下沉的 88 行清爽文档，被治理指标反向异化成了 8 文件重壳 |
| **实战消费率与 RFC 实跑** | 对全仓 8 份 `docs/proposals/RFC-*.md` 实跑 `check-decision-ledger.py`：**0 / 8 通过（100% 假阳性 rc=1）**；28 份计划真实业务激活 **0 / 28**；最新 4 份 RFC（RFC-0005~0008）全部用脚投票，自发压平为极简 4 列单表 | 脚本与双模板已被真实研发彻底弃用，形成纯粹死重 |
| **脚本 8 类实测硬伤** | 实测确认：① Windows CRLF 全败（测试刻意 `newline="\n"` 掩盖）；② 强制数据行重复写列名导致自然表格全红；③ **空列 + 错前缀 + 违禁「待定」反而 `rc=0` 放行**；④ 行内 ```` ``` ```` 永久吞噬后文且漏判 `~~~`；⑤ 拒双语标题、反引号 ID 与合法「零默认假设」 | 既防不住作弊又挡住全部真实合规文档，真实工程价值为负 |
| **Split-Brain 与源码硬伤** | 与 `doc-governance/references/rfc-crystallization-lifecycle.md` 存在两套全面冲突的台账模板；`goal-loop` P0 叠了四重技能并直接绕过本模板；`SKILL.md:72` 提问层预算写着「本节」却全文无任何预算定义（循环空指针）；§5 越界杂糅错误/审查熔断、§6 杂糅显式思考 | 职责不纯、接口断裂且存在内部空指针缺陷 |

---

## 1. 全量资产盘点与 8 篇真实 RFC 实跑审计【A】

### 1.1 8 源文件拆解（949 行 / 48.0 KB）

| 文件路径 | 行数 | 字节数 | 真实状态与发现 |
| :--- | :---: | :---: | :--- |
| [SKILL.md](../../../skills/clarification-protocol/SKILL.md) | 102 | 6.4 KB | `description` = **623 字符**（超 500 软限）；§1–§4 凝练优秀，但 §5 越界含错误/审查熔断且 L72 提问层预算为空指针，§6 含非澄清杂项 |
| [decision-ledger.md](../../../skills/clarification-protocol/references/decision-ledger.md) & [convergence-checklist.md](../../../skills/clarification-protocol/references/convergence-checklist.md) | 156 | 10.8 KB | 过度展开为 5 张表 / 9 项候选边界全填「不适用+理由」；连 `decision-ledger.md:14` 自身标题都通不过本技能脚本 |
| [decision-ledger-template.md](../../../skills/clarification-protocol/templates/decision-ledger-template.md) & [requirement-confirmation-template.md](../../../skills/clarification-protocol/templates/requirement-confirmation-template.md) | 126 | 7.5 KB | **0% 实战采用**；为迁就脚本在单元格里硬写反人类的 `出处: ...` / `影响级别: ...`；与 `doc-governance` RFC 模板 Split-Brain 冲突 |
| [check-decision-ledger.py](../../../skills/clarification-protocol/scripts/check-decision-ledger.py) + `.sh` | 137 | 5.8 KB | **实测 8 类严重缺陷**，本仓 8 份真实 RFC **0/8** 通过，`USAGE` 仍硬编码 `bash check-decision-ledger.sh` |
| [test_clarification_protocol_contract.py](../../../skills/clarification-protocol/tests/test_clarification_protocol_contract.py) | 428 | 17.5 KB | 实跑 `27 passed (0.52s)`，占总行数 **45.1%**；10 项静态文案锁死 + 5 项正则元自检 + 12 项脚本行为测试（L313–315 以 `newline="\n"` 掩盖 CRLF Bug，0 用例测真实 RFC） |

> 另核实：[clarification-protocol-design.md](../architecture/clarification-protocol-design.md)（169 行）L13/L67/L137/L166 仍漂移指向已退居兼容壳的 `check-decision-ledger.sh`。

### 1.2 全仓 8 份真实 RFC 实跑结果（本仓工程师用脚投票实证【A】）

对 `docs/proposals/RFC-0001` 至 `RFC-0008` 逐一实跑 `python3 skills/clarification-protocol/scripts/check-decision-ledger.py <rfc>`：
- **RFC-0001 ~ RFC-0004（2026-10 月）**：均采用 `doc-governance` 第 5/7 节双语三分节模板（`### 7.1 已决项 (Settled Decisions)`、`D1`/`X1`），实跑校验器 **4/4 全部 `rc=1` 失败**；
- **RFC-0005 ~ RFC-0008（2026-11-22，晚于本技能建成一个多月）**：作者全部主动抛弃三小节分表 + 矛盾扫描表 + 三项收敛自检表，**自发收敛为极简 4 列单表 `## 6. 决策台账（编号 | 类型 | 条目 | 依据）` + `## 2. 术语表（术语先行）`**，实跑校验器同样 **4/4 全部 `rc=1` 失败**。
- **综合实证**：真实 RFC 通过率 **0 / 8（0%）**，28 份历史实施计划业务激活率 **0 / 28（0%）**。唯一能通过该脚本的只有它自己目录里的 2 份示例模板。

---

## 2. 四大核心病灶深度剖析【A】

### 病灶 1：`check-decision-ledger.py` 8 类实测缺陷（假阳性 100% + 假阴性逃逸）

主智能体逐行复核 `check-decision-ledger.py`（132 行）并验证 8 类硬伤：
1. **Windows CRLF 全线崩溃**（`:39-55`）：为复刻已退役 awk 保留 `\r` 且 `trim()` 不剥 `\r`，导致 Windows 换行文件 `"已决项\r" not in REQUIRED_FIELD` 全报错，测试却靠 `newline="\n"` 掩耳盗铃；
2. **自然 Markdown 表格全红**（`:89`）：要求每行数据文本字面包含 `"出处"` / `"排除依据"` / `"影响级别"`，逼迫单元格违背 Markdown 常识重复书写列名；
3. **空列 + 错前缀 + 违禁「待定」反而绿灯逃逸**（`:35, 85-93`）：输入 `| Z-99 | 出处待定 |  |  |` 三类拼凑行实测返回 **`rc=0`**（不校列位、不校空格、不校前缀与类别匹配、不校禁词）；
4. **脆弱围栏解析**（`:67-69`）：`if "```" in line: in_fence = not in_fence`，正文出现行内 ```` ```markdown``` ```` 即永久翻转状态吞噬后续全文，且完全忽略 CommonMark `~~~` 围栏；
5. **标题/ID/空分类过度僵化**（`:35, 72-76, 94-100`）：拒绝双语后缀标题（`已决项 (Settled Decisions)`）、拒绝反引号 ID（`` `D-01` ``）、拒绝合法的「零默认假设」场景，倒逼作者硬编假条目。

### 病灶 2：Split-Brain 双模板与 `goal-loop` P0 四重技能叠床架屋

- `clarification-protocol` 与 `doc-governance/references/rfc-crystallization-lifecycle.md:117-164` 各管一套互不兼容的台账编号与标题格式；
- `goal-loop/references/stage-progression-protocol.md:78-108` 在 P-1/P0 阶段不仅同时叠加 `brainstorming` + `grilling` + `clarification-protocol` + `doc-governance` **四重技能**，而且原地内联复述了收敛律后，明确要求落盘遵循 `doc-governance` RFC 模板，直接架空了本技能的两份模板与脚本。

### 病灶 3：职责拼盘残留与 `SKILL.md:72` 循环空指针

- **§5 越界杂糅 + 空指针**：[SKILL.md](../../../skills/clarification-protocol/SKILL.md) §5（L66–76）仍携带着 `AGENTS.md` 瘦身时一并倒进来的「错误层 3-Tries + 25% 预算」与「审查层 Delta ≤ 5 轮」（二者分属 `goal-loop` 与 `dual-round-review`）；而唯一归属本技能的 `| 提问层 | 本节 |`（L72）竟在整篇技能里**从未定义过具体预算上限**，构成货真价实的空指针循环引用！
- **§6 非澄清杂项**：`显式化思考`（L80–82）属于通用推理要求，与需求澄清无专属耦合，且现代推理模型已原生具备思考流。

### 病灶 4：重型 5 表 + 独立无问回合撞上「人类疲劳倒 U 曲线」

对照 [调研报告 §2](./2026-11-23-clarification-protocol-peer-research.md) 的 *Oversight Has a Capacity* 研究【B】与 `spec-kit`/`OpenSpec` 实践【A】：要求每轮问答后单开一次“不带新问题”的自检回合、填满 5 张表 16 个字段、对 9 类候选边界逐条写「不适用+理由」，仪式感成本极高，因此本仓真实作者在 RFC-0005~0008 中全部果断将其压平为 1 张 4 列单表。

---

## 3. 真正值得保留的 4 项精华内核

剥离全部坏脚本、冲突模板与拼盘杂项后，本技能有 4 条极高密度的认知纪律——经 2026 顶会研究（*HumanEvalComm* / *ClarEval* / *ClarifyCodeBench*）与本仓 8/8 RFC 实践共同验证，甚至补上了 Matt Pocock `grill-with-docs`「非 ADR 约束在下游被稀释」的短板：

1. **术语先行前置门禁**（只针对易歧义核心词，禁扩全量词典）；
2. **依赖强度 × 实现影响排序 + 低影响直转显式默认假设**（抑制多歧义天花板下的细节漂移）；
3. **三类决策的极简持久化留痕（已决项 / 已排除边界 / 默认假设，统一压平为 1 张 4 列单表）与禁止重开已排除项**；
4. **目标 / 边界 / 矛盾三问收敛判据**（改为出口前轻量内联自核，拒用空口「没问题了」）。

---

## 4. 三档重构方案对比【C】

| 方案 | 核心动作 | 预计体量变化 | 优点 | 代价与风险 |
| :--- | :--- | :---: | :--- | :--- |
| **方案 A（强烈推荐）：去壳提纯为 60–80 行精品微技能** | ① **彻底废弃** `check-decision-ledger.py/.sh`、两份冲突模板与 428 行重型测试（仅保留极简交付面/外链哨兵）；<br>② **剥离杂项并修空指针**：删除 §5 错误/审查熔断与 §6 显式思考；补齐借鉴 `spec-kit` 的**软题数锚点（如单次核心澄清 ≤5 关键题）**与 `grilling` 的**「先读代码自查事实，只问人类决策」**铁律；<br>③ **消除 Split-Brain**：台账形式统一对齐 RFC-0005~0008 已实战跑通的**极简 4 列单表 `编号 | 类型 | 条目 | 依据`**（或直接原地回写主 Spec/计划）；<br>④ 压缩 `description` 至 ≤400 字符，修复设计书旧 `.sh` 漂移 | **48.0 KB (8 文件) → ~6–10 KB (1–2 文件，-82%)** | 保留全部领先理念、彻底消灭 0/8 损坏脚本与双模板冲突，体量与 `mattpocock` 精品微技能同级，独立与组合调用两相宜 | 失去所谓「机械脚本验台账」——但实证已明该脚本从未通过任何真实 RFC |
| **方案 B（吸收合并退役）：并入 `goal-loop` P0 与 `doc-governance` RFC 规范** | 将上述 4 条精华浓缩（~25 行）并入 `goal-loop` Align 阶段，台账 4 列单表单归 `doc-governance` RFC 规范，正式退役 `clarification-protocol` 独立技能 | **48.0 KB → 0** | 彻底消除 P0 叠加四重技能的路由重叠与维护面 | 若用户仅想做一次独立需求澄清（不启动 `goal-loop` 重型循环），缺少可单独按需触发的轻技能入口 |
| **方案 C（重写脚本维持重型门禁）** | 彻底重写 Markdown 表格解析器（修齐 8 类 Bug、兼容单表与双语标题）并合并双模板 | ~35–40 KB | 保留离线机械台账门禁 | 违背行业共识（`spec-kit`/`superpowers`/`grilling`/`OpenSpec` 无一用正则脚本校验对话台账），高维护税且低 ROI（不推荐） |
