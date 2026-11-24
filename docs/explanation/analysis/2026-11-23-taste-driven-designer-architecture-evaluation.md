# `taste-driven-designer` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-TASTE-DESIGNER-EVAL-2026
> - **当前版本**: V1.0.1
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于 `skills/taste-driven-designer/` 全部 13 个源文件（1,407 行 / 74.9 KB）、设计书、原教旨原文 [how-to-turn-your-ai-into-a-world-class-designer.md](../../reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md)、两份历史实施计划、实跑 `pytest` 与脚本测试，并对照配套调研报告 [2026-11-23-taste-driven-designer-peer-research.md](./2026-11-23-taste-driven-designer-peer-research.md)。
> - **证据分级**: 【A】一手（本仓库全量源码/行号/实跑命令与脚本反例、外部标杆一手源码）｜【B】二手转引（工程文与论文摘要）｜【C】架构师诊断与重构设计

> [!NOTE]
> **执行注记 (2026-11-24)**：**Wave 3（[taste-driven-designer-design.md](../architecture/taste-driven-designer-design.md) V2.0.0）已按本报告推荐的方案 A 完成 V2.0 瘦身提纯升级**（与 `frontend-qa-gate` 双轨真实磁盘证据化升级同步落地）——D1 新增 `Persuade`/`Operate` 表面模式分流并合并种子流程至 `references/discover-phase.md`，D3 扩展 2026 10 大 AI Tells，D2 收敛为 5 列评审记录表并并入无截图降级与多模态能力门控，移除冗余状态矩阵并将五域运行时断言 SSOT 归位 `frontend-qa-gate`，重铸纯标准库无偏 `scripts/generate-seed.py`（配 `test_taste_generate_seed.py` 与 `test_taste_designer_v2_surface.py`），并退役 `multimodal-enrichment.md`、`seed-string-procedure.md`、`generate-seed.sh`、`test_gate_contract.py` 与 `test_generate_seed.py`。下文所有体量与路径均为 **Wave 3 重构前审计时刻的历史快照**（已退役或迁移的文件引用已转为纯反引号代码片段防止 404 断链）。

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.1** | 2026-11-24 | AI Agent | 核心架构组 | 补充 Wave 3（V2.0.0）已按方案 A 完成 V2.0 瘦身提纯升级的执行注记，并将下文指向已退役 V1 文件的相对链接转为纯反引号代码片段防止 404 断链 |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `taste-driven-designer` 13 文件全量审计、`generate-seed.py` 零状态数学 Bug 实测、7 处内部漂移与设计书覆写事故还原、与 `frontend-design` 70%+ 重叠解剖及三档重构去向方案 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`taste-driven-designer` 是否过度设计？是否需要重构优化？**

**结论：它拥有本仓库最具科学精神的一次演进资产——基于真实外部实跑反证（E1–E7）果断证伪了「9/10 绝对评分门禁」并创立「三信号相对盲比/排序门禁」；但它在防护补丁叠加中把轻量创意探索重塑成了 12 步官僚文书流水线（正文 47.7 KB，为 Anthropic 官方 `frontend-design` 的 5.1 倍），同时面临 0 次仓内实战验证、与已安装 `frontend-design` 重叠 >70%、198 行种子脚本含零状态数学 Bug、以及 7 处已落盘内部漂移（含设计书被事故覆写并断言「无自动化测试」）。急需大幅瘦身提纯，剥离官僚文书与重复 QA 职责。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **体量与流程摩擦** | **13 文件 / 1,407 行 / 74.9 KB**；纯指令与模板面 **47.7 KB（761 行）**；单轮设计迭代需穿越 12 道文书与门禁环节 | 是 Anthropic `frontend-design`（9.4 KB）的 **5.1 倍**；创意探索被 nonce、鉴别力自检、9 列评审账本等重文书严重拖慢 |
| **实战使用率** | 28 份计划与 18 项审查中，除自身建设/加固/迁移外，真实业务 UI 设计调用 **0 次**；V1.1/V1.2 三信号协议**未经一次真实闭环实跑** | 防护机制全部基于单次 V1.0 外部反证（E1–E7）纸面推演叠建，缺少实战减法校验 |
| **脚本与测试质量** | `generate-seed.py`（198 L）有 61 行复刻退役 Bash `getopts`，且含 **Park-Miller LCG 零状态吸收 Bug**（`-s A` 全输出 `A`）；`test_gate_contract.py`（213 L）**0 行为测试**，全为静态文案锁死却漏检 `ai-tells-audit.md:83` 旧口径 | 脚本与文案测试性价比极低，真实 Bug 照样逃逸 |
| **内部漂移与事故** | 实证揪出 **7 处缺陷/漂移**：设计书被 `ef7e325` 误覆写断言「无自动化测试」、个人真名 `王辉` 进 MIT 模板、`Critic 终分` 残留、状态矩阵 4 处打架、`goal-loop` 挂点 3 处冲突等 | 维护失同步已非常明显 |
| **跨技能定位夹心化** | 与本机已装 Anthropic `frontend-design`（199k★，9.4 KB，已更新 2026 新一代 AI Slop）**重叠 >70%**；又与本仓 `frontend-qa-gate` 在 Gate A 存在 SSOT 宣称倒挂 | 轻设计打不过 `frontend-design`，重工程打不过 `pbakaus/impeccable`；必须收缩聚焦到真正独有的增量护城河 |

---

## 1. 全量资产盘点与脚本/测试深度体检【A】

### 1.1 13 文件体量拆解

| 分层 | 文件 | 行数 | 字节数 | 健康度与发现 |
| :--- | :--- | :---: | :---: | :--- |
| 路由层 | [SKILL.md](../../../skills/taste-driven-designer/SKILL.md) | 118 | 9.6 KB | L11 裸引仓内路径 `docs/reference/articles/...`（单技能安装不可达） |
| 核心细则 (4) | [critic-loop-protocol.md](../../../skills/taste-driven-designer/references/critic-loop-protocol.md)（183 L）、[discover-phase.md](../../../skills/taste-driven-designer/references/discover-phase.md)（91 L）、[ai-tells-audit.md](../../../skills/taste-driven-designer/references/ai-tells-audit.md)（83 L）、`multimodal-enrichment.md`（原 `skills/taste-driven-designer/references/multimodal-enrichment.md`，已退役，73 L） | 430 | 27.7 KB | D2 协议过重；`ai-tells-audit.md:83` 残留已废止的「Critic 终分」；7 反模式滞后停留在 2025 上一代特征 |
| 模板套件 (3) | [critic-prompt-template.md](../../../skills/taste-driven-designer/templates/critic-prompt-template.md)（113 L）、[design-brief-template.md](../../../skills/taste-driven-designer/templates/design-brief-template.md)（57 L）、`seed-string-procedure.md`（原 `skills/taste-driven-designer/templates/seed-string-procedure.md`，已退役，43 L） | 213 | 11.5 KB | `design-brief-template.md:30-31` 在 MIT 开源模板中硬编码个人真名 `王辉` |
| 脚本 (2) | [generate-seed.py](../../../skills/taste-driven-designer/scripts/generate-seed.py)（198 L）+ `.sh`（5 L） | 203 | 7.4 KB | **实测数学 Bug** + 61 行 Bash `getopts` 仿写包袱 + `USAGE` 残留 `bash generate-seed.sh` |
| 测试与夹具 (3) | `test_gate_contract.py`（原 `skills/taste-driven-designer/tests/test_gate_contract.py`，已退役，213 L）、`test_generate_seed.py`（原 `skills/taste-driven-designer/tests/test_generate_seed.py`，已退役，185 L）、[critic-gate-counter-evidence.md](../../../skills/taste-driven-designer/tests/fixtures/critic-gate-counter-evidence.md)（45 L） | 443 | 20.4 KB | 实跑 `28 passed (1.45s)`；但 `test_gate_contract.py` 13 用例中 **0 行为测试**，全为静态子串锁死且漏扫 `ai-tells-audit.md` |

### 1.2 `generate-seed.py` 实测数学 Bug 与过度封装

1. **Park-Miller LCG 零状态吸收陷阱**（`generate-seed.py:128-138`）：初始 `state = 0` 且 `CHARSET[0] == 'A'`，循环未按 Park-Miller 数学前提做非零钳位（`1 ≤ state ≤ M-1`）。实测运行 `python3 skills/taste-driven-designer/scripts/generate-seed.py -s A -l 32` 与 `-s AAAA -l 32`，均输出 `AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`（**零熵死锁**）【A】。
2. **过度封装的 388 行随机串包袱**：该脚本不含任何美学词库，仅仅输出 `[A-Za-z0-9]` 随机串；却为了复刻已退役 Bash `getopts` 报错文本写了 61 行手写 `Getopts` 类（已被历史审查定性为「验收口径驱动的过度封装」），连带 `.sh` 壳与单测共消耗 **388 行**维护面——而标准库 `secrets.choice` + `hashlib.sha256` + `random.Random` 仅需 ≤25 行即可同时解决零状态 Bug 与跨平台一致性。

---

## 2. 六大过度设计与结构性漂移诊断【A】

### 病灶 1：D2 创意迭代环官僚化（单轮 12 步文书流水线）

对比 Anshu Chimala 原文「3 条轻量 Prompt 极速发散 + 独立 Critic 迭代」的精神，`taste-driven-designer` 在针对 E1–E7 反证加固时走到了另一极端：单次 UI 修改需穿越九态自检 → 生成 round-nonce → 截双图去标识并随机化左右 → 填 52 行 Critic 模板 + 粘贴原则台账 → 校验 Receipt 回执（连 2 轮作废熔断）→ 鉴别力自检 → 冲突仲裁与维度冻结 → 填 9 列评审账本 → 汇总三信号 → D3 删除清单 → 移交 `frontend-qa-gate` 31 条断言 → 移交 `dual-round-review`。在视觉探索最需要快速试错的阶段，维护账本与合规表格的认知成本远超设计本身【A/C】。

### 病灶 2：设计书误覆写事故与 7 处已落盘内部漂移

1. **设计书严重失实事故**（[taste-driven-designer-design.md](../architecture/taste-driven-designer-design.md) L161）：2026-11-22 `ef7e325` 因 G-08 脚本用 `replace("-design", "")` 将 `taste-driven-designer-design` 误裁为 `taste-drivener` 误报缺设计书，顺手把原 V1.1.0 设计书整篇覆写为 V1.0.0，导致丢失原有演进历史并赫然写下失实断言「**本技能没有自动化测试**」（实际存在 28 个 pytest 用例）；
2. **旧门禁口径逃逸残留**：`references/ai-tells-audit.md:83` 仍写着「**Critic 终分**」，与 V1.1 废分原则直接矛盾，且 `test_gate_contract.py:30-34` 漏扫该文件；
3. **个人真名泄露进 MIT 模板**：`templates/design-brief-template.md:30-31` 硬编码 `王辉`；
4. **状态矩阵四处打架 + 与 `frontend-qa-gate` SSOT 倒挂**：`ai-tells-audit.md:80`（5 态）vs `critic-loop-protocol.md:29`（8 态）vs `:154`（9 态）vs `frontend-qa-gate/references/acceptance-matrix.md:19-29`（9 态含派生状态、无独立重试格）；同时双方宣称 `taste` Gate A 是验收基线 SSOT，实际 `taste` Gate A 仅 4 行概括，真正在执行层定义 31 条断言的是 `frontend-qa-gate`；
5. **跨仓安装不可达与挂点三处冲突**：`SKILL.md:11` 裸引仓内路径 `docs/reference/articles/...`；`test_gate_contract.py:168` 硬编码 6 技能正则漏掉 `clarification-protocol`；在 `goal-loop` 中的挂点出现三处冲突（`goal-loop/SKILL.md:58` P3.5 vs `stage-progression-protocol.md:214` P4 步骤 5 vs 设计书 L157 P3）；且 `2026-09-20-critic-gate-hardening.md:18,70` 至今仍标「进行中」。

### 病灶 3：缺少表面模式分流且 AI Tells 停留在 2025 上一代

对照 [调研报告 §2.1 & §2.2](./2026-11-23-taste-driven-designer-peer-research.md)：
- 对落地页（Persuade）与工具后台/仪表盘（Operate）一刀切套用「随机种子 + 跨界雄心」，缺乏 `pbakaus/impeccable` 式的表面模式约束；
- `ai-tells-audit.md:10-18` 仍停留在 2025 赛博紫/药丸卡片清单，尚未覆盖 2026 新一代模式坍缩（如 Anthropic `frontend-design` 点名的暖米 `#F4F1EA` + 陶土红 `#D97757` + 广版报纸栏 + ALL-CAPS eyebrow）。

### 病灶 4：与本机已装 Anthropic `frontend-design` 重叠 >70%

本机 `.agents/skills/frontend-design/SKILL.md`（9.4 KB / 71 行，与 `anthropics/skills` 199k★ 逐字节一致）已低摩擦覆盖题材锚定、2026 新 AI Slop 校准、两遍规划与 UX 文案，使 `taste-driven-designer` 在常规 UI 编写场景中陷入「比轻不如 `frontend-design`、比全不如 `impeccable`」的夹心位置。

---

## 3. 真正值得保留的 3 项独特护城河

剥离全部文书官僚与重叠面后，本技能有 3 项连 Anthropic `frontend-design` 都不具备的稀缺真资产：

1. **反证驱动的「三信号相对盲比/4+1 排序 Critic 协议」**（连同 [critic-gate-counter-evidence.md](../../../skills/taste-driven-designer/tests/fixtures/critic-gate-counter-evidence.md) E1–E7 实跑证词）：彻底证伪了裸绝对分门禁，并用「已决原则防乒乓 + 盲比 A/B 强制选边 + 能力门控禁止假装看过截图」给出高含金量的视觉评审范式；
2. **外部随机熵发散（SSoT）**：在 0→1 品牌/营销探索期打破模型统计均值的低成本杠杆；
3. **D3 残酷减法与可见文案占位符化**：强迫在交付前做一轮“删无可删”的精炼和 AI 营销黑话清洗。

---

## 4. 三档重构去向方案对比【C】

| 方案 | 核心动作 | 预计体量变化 | 优点 | 代价与风险 |
| :--- | :--- | :---: | :--- | :--- |
| **方案 A（推荐）：瘦身提纯为「轻量品味发散 + 视觉 Critic 协议」** | ① **聚焦增量边界**：明确常规编码可叠加 `frontend-design`，本技能精简为两块真资产——「表面模式分流 + 2026 AI Tells + 残酷减法」与「极简版独立视觉盲比/4+1 Critic 协议（保留盲比/原则防乒乓/降级诚实声明，砍掉 9 列账本、nonce 官僚和重复状态矩阵）」；<br>② **职责彻底归位**：把响应式/九态/无障碍校验单归 `frontend-qa-gate`，消除 SSOT 倒挂；<br>③ **重铸脚本与清漂移**：`generate-seed.py` 缩为 ≤25 行纯标准库并修复 Park-Miller 零状态 Bug（或直接改为 1 行内置 Python 提示词命令），修复全部 7 处漂移（恢复正确设计书、清 `王辉`、删 `Critic 终分`、裁掉文案锁死测试） | **74.9 KB → ~18–25 KB（-70%）** | 保留全部核心护城河与反证智慧，体量回落至与 `impeccable` 路由层同量级，摩擦大降且零内部缺陷 | 仍需在未来真实前端项目中做至少 1 次端到端实跑校验 |
| **方案 B（退位专精插件）：仅保留「独立视觉 Critic 盲比协议」** | 彻底放弃 D1/D3 常规设计指导（全部路由给外部 `frontend-design` / `impeccable`），本技能缩水为 ~10 KB 的纯「多候选视觉盲比与 4+1 排序 Critic」子协议 | **74.9 KB → ~10 KB（-87%）** | 与 `frontend-design` 零重叠，定位锋利如手术刀 | 若目标环境未安装 `frontend-design`，失去独立端到端设计引导能力 |
| **方案 C（退役归档）：沉淀反证原则并下线独立技能** | 鉴于本仓长期偏向工具/后端/工程技能（UI 实战 0 次），将 E1–E7 反证与相对盲比原则归档为方法论说明或并入评审资产，正式退役 `taste-driven-designer` | **74.9 KB → 0** | 彻底卸下零业务使用率的维护包袱 | 若您后续在其他前端项目频繁使用本仓库技能集，会损失现成的反 Slop + 盲比 Critic 能力 |

> **关键拍板前提**：取决于您未来是否计划把本技能集安装到**外部前端/Web 产品仓库**日常使用——若会高频用于外部前端项目，推荐**方案 A**（瘦身提纯至 ~20 KB 并补齐 2026 AI Slop 与表面模式）；若本仓只聚焦工程编排与后端/工具研发，可评估**方案 B 或 C**。
