# `dual-round-review` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-DUAL-ROUND-REVIEW-EVAL-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于 `skills/dual-round-review/` 全部 24 个源码文件（4,274 行 / 236.8 KB）、设计书与 RFC-0001/0002 / ADR-0001/0002、`docs/project/reviews/` 全部 17 个归档目录（70 份报告 / 1.76 MB）与 28 份计划的实跑实证，并对照配套调研报告 [2026-11-23-dual-round-review-peer-research.md](./2026-11-23-dual-round-review-peer-research.md)。
> - **证据分级**: 【A】一手（本仓库全量源码/行号/实跑 pytest 与 17 归档门禁、外部标杆 `gh api` 一手源码）｜【B】二手转引（学术论文与官方博客摘要）｜【C】架构师诊断与重构设计

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `dual-round-review` 24 文件源码体检、17 归档 / 70 报告实证 ROI 统计、2 处高危脚本 Bug 与 6 处模板漂移定位、R2 边际收益量化及分阶段重构方案 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`dual-round-review` 是否过度设计？是否需要重构优化？**

**结论：核心理念正确且经受了实战检验（「隔离上下文 + 红队第一性原理质疑 + 独立取证」是本仓库最硬核的质量护栏之一），但 V2.1–V2.3 围绕「永久全文归档 + SHA256 Write-Once + 11 项脆弱正则门禁 + 零用 Artifact 模式」层层加码的外围官僚仪式已出现严重过度设计与系统反噬——既打红了仓库现有 `pytest` 基线（128 passed / 1 failed），又埋下了 17/17 全量失效的脚本 Bug，更把外部 100 行级精悍审查方案膨胀成了 4,274 行 / 236.8 KB 的沉重怪兽。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **体量与指令密度** | **24 文件 / 4,274 行 / 236.8 KB**（仅 MD 108.2 KB；单篇 `SKILL.md` 283 行 / 36.8 KB / **96 处强指令词**；门禁 11 项） | 比 Anthropic `/code-review`（112 行）、OpenAI Codex `rubric.md`（95 行）膨大 **1–2 个数量级**，已实证触发 IFScale 高密度指令静默脱落 |
| **合规门禁反噬现状** | 17 个真实归档中仅 **13/17（76.5%）** 通过门禁；**2026-11-22 同日全部 4 个实战归档 100% 失败**，直接导致 `pytest` 现红 | 叠加暴露「脚本正则把 `[f](./f)` 拆成 `f.f` 的真 Bug」+「代理在大负荷下遗漏格式细节并产生事后合理化幻觉」 |
| **隐藏脚本致命 Bug** | `prepare-review-context.py:358` 的 `_UNIT_RX` 强求行首 `>`，但自身 `:500` 生成无 `>`；实测对 **17/17 真实归档全部返回 `None`** | 测试靠手造带 `>` 假夹具漏检；跨天 Delta 会 100% 击穿「一交付单元一目录」不变量 |
| **模式使用率与 R2 ROI** | V2.3.0 `Artifact Review`（~550 行）实战使用率 **0%**；16 份 R2 报告（>173 条缺陷）仅拦截 **3 条** R1 误判 P0/P1（仅 1 次免除 Delta），Delta-R2 几乎全员 0 拦截 | 串行全量 R2 与零用 Artifact 模式维护/Token 成本高昂，边际收益极低 |
| **仓库与跨技能负外部性** | 17 次交付已往版本库永久写入 **70 份报告 / 1.76 MB**（均值 4.12 轮 / 103.5 KB，极端高达 9 份 / 280.8 KB）；迫使 `doc-governance` 6 个脚本全部加装双轨豁免并禁止已实现 RFC 移动 | 局部技能的刚性设计对全仓库治理体系产生了严重的连带架构污染 |

---

## 1. 全量资产盘点与 17 个真实归档实证审计【A】

### 1.1 `skills/dual-round-review/` 体量结构（24 源文件 / 4,274 行 / 236.8 KB）

| 分层 | 文件数 | 行数 | 字节数 | 核心健康度评估 |
| :--- | :---: | :---: | :---: | :--- |
| 核心路由 [SKILL.md](../../../skills/dual-round-review/SKILL.md) | 1 | 283 | 36.8 KB | 严重超重：含 96 处强禁令词、121 条列表项、15 条反模式、7 处本仓私有 RFC/回归历史与 9 处跨技能硬耦合 |
| 参考规程 `references/` | 7 | 708 | 55.4 KB | 含 3 份 **0% 使用率**的 `artifact` 规程（269 行）及散布 7 文件 32 行的 React/Next.js/Safari 硬编码 |
| 报告模板 `templates/` | 4 | 142 | 8.5 KB | **与 `references/` 及 `scripts/` 存在 6 处确凿漂移**（单测只测了 `references/` 漏测 `templates/`） |
| 教学案例 `examples/` | 4 | 163 | 7.5 KB | 4 份前端/TS 案例，体量尚可但偏重前端视角 |
| Python 脚本 + `.sh` 壳 `scripts/` | 4 | 1,213 | 53.1 KB | `check-review-report.py`（620 L，含链接剥离 Bug + Bash/awk 怪癖）与 `prepare-review-context.py`（583 L，含 17/17 失效 Bug） |
| 测试套件 `tests/`（129 用例） | 4 | 1,765 | 73.8 KB | 128 passed / **1 failed**；**24 条（18.6%）为静态文案/变量名锁死断言**（`test_write_channel_contract.py` 20/20 全为文案锁死） |

### 1.2 17 个真实审查归档（70 份报告 / 1.76 MB）实证画像

对 `docs/project/reviews/` 全部 18 个顶层项（17 归档目录 + 1 孤立散文文件 `spec-evolution-selfcheck.md`）与 `docs/project/plans/*.md`（28 份）实跑统计：

1. **吞吐与极端长尾**：
   - 17 次交付合计 **70 份报告 / 1,758,717 字节（1.76 MB）**，均值 **4.12 份 / 103.5 KB**；
   - **≥5 份报告的极端长尾占 6/17（35.3%）**：`2026-11-22-doc-truth-axis`（**9 份 / 280.8 KB**）、`2026-10-10-global-agent-delegation-redlines`（**9 行改动跑 6 轮 / 207.0 KB**，第 4–5 轮自造新 P1，用户判语「矫枉过正、过度形式化」）、`2026-10-12-spec-evolution-v1`（5 份 / 178.4 KB）、`2026-10-09-quadrant-index-convention`（6 份 / 124.7 KB）、`batch-d`（5 份 / 117.1 KB）、`batch-gates`（5 份 / 70.8 KB）。
2. **模式真实采用分布**：
   - 17 归档中：Full **9**、Light **8**、**Artifact 0**（70 份报告中 `> **Review Schema**: artifact` 命中 **0 / 70**）；
   - 28 份计划中：Full 9、Light 10、Delta 14、**Artifact 0**；提及 `prepare-review-context` 仅 5 份（其中 4 份是修改该脚本自身！），归档目录有 `prepare` 脚手架痕迹的仅 **7/17（41.2%）**。
3. **第 7 列写入形态实证（69 条台账行）**：
   - 合法 `direct` 47 条（68.1%）、非法装饰 `direct（<字节>；...）` 17 条（24.6%）、`transcribed` 5 条（7.2%——其中 4 条是 V2.1 历史补列，**V2.2 上线后 65 轮实战中仅 1 轮因 ID 前缀 `RD-01` 被门禁拒收而手改降级**）。实质上 V2.2 后直写占比达 **64/65（98.5%）**。
4. **R2 串行元审判的真实边际收益（9 个 Full 归档 / 16 份 R2 报告）**：
   - 剔除 Delta-R2 对已修项关单后，全量 16 份 R2 报告（>173 条候选缺陷）中，**R2 真正把 R1 误判的 P0/P1 阻断项拦截降级为 P2/Dismissed 的实证仅 3 条**（`quadrant-index` R1-2、`p3-six-backlog` R1-2、`retire-spec-evolution` R1-1，其中仅最后 1 次直接避免了一次 Delta 循环）；
   - **绝大多数 Delta-R2 报告（6+ 份）的误报拦截数为 0**，实质沦为对已清零 Delta-R1 的昂贵重复确认仪式。

---

## 2. 六大过度设计与结构性病灶深挖【A】

### 病灶 1：两处确凿的脚本级 Bug，一处已打红 CI、一处 17/17 全军覆没

1. **`prepare-review-context.py:358` `_UNIT_RX` 100% 失效隐藏 Bug**：
   - 源码 `:358` 写死 `_UNIT_RX = re.compile(r"^>\s*-\s*\*\*交付单元\*\*:[ \t]*(.+?)[ \t]*$", re.MULTILINE)`（强求行首 `>`）；
   - 但同文件 `:500` 自己生成的 `README.md` 写的是 `- **交付单元**: {slug}`（无 `>`），全部 17 个真实归档均无 `>`；
   - 实跑 `_read_unit()` 在 **17/17 归档上全返回 `None`**！之所以单测未发现，是因为 `test_prepare_review_context.py:407,426` 手造了带 `>` 的假夹具，且同日重跑因日期同名巧合掩盖了缺陷。跨天跑 Delta 会 100% 分裂出第二个归档目录。
2. **`check-review-report.py:216` Markdown 链接剥离 Bug + 2026-11-22 门禁塌方**：
   - `:216` 沿用旧版 awk 习惯 `fname = _NON_FILE_CHARS_RE.sub("", raw_file)`，把台账中合法的 Markdown 链接 `[round-1-light.md](./round-1-light.md)` 里的标点全抹除，拼出不存在的 `round-1-light.md.round-1-light.md`；
   - 叠加 2026-11-22 同日 4 个归档集体出现第 7 列带括号注释、自定义轮次名、缺五区块标题与孤儿报告（`round-4-r3dc-confirm.md` 漏登），导致全仓 `pytest` 唯一红灯至今未解；更发人深省的是，其中 3 份归档 `README.md` 竟写出**「Light 模式本就不该过门禁」的事后合理化幻觉**（被早期 5 个全绿 Light 归档直接证伪）——这正是 IFScale 所揭示的高指令密度下静默脱落 + 代理自圆其说的教科书样本【A/B】。
3. **基线配对盲区（`:286-294`）**：`_base_key()` 只取 `<base7>`，在 `2026-10-14-p2-six-backlog-items` 中 R1 审 `1b17965..92f749c` 后直接跳修代码并派 R2 审 `1b17965..deb691e`，违反级联铁律却以 `rc=0` 放行。

### 病灶 2：Write-Once + 11 项形式门禁的「官僚税」与跨技能负外部性

- **轻微排版差异引发整轮重派**：`2026-10-08`（改写 §2 标题）与 `2026-10-12`（一份 45 KB 高质量 Delta-R1 报告仅因标题写为 `## §1` 而非 `## 1.`）均因 Write-Once 严禁微调，被迫作废报告整轮重派子智能体；`2026-10-20` 仅因 ID 前缀 `RD-01` vs `DR-01` 被迫手改降级 `transcribed`；
- **拖累整个仓库治理体系**：为了把 1.76 MB 不可改写的审查长文永久放进 `docs/project/reviews/`，不仅持续膨胀 Git 仓库体积，还迫使 `doc-governance` **全部 6 个脚本**硬编码双轨豁免，并迫使 `rfc-crystallization-lifecycle.md:199` 放弃已实现 RFC 归档移动以防打断归档内相对链接。对比 `obra/superpowers`（git-ignored 临时工作区，交付后清理，只留精简结论）与 Anthropic `/code-review`（直接锚定行内评论），永久入库全文的 ROI 明显偏低【A/C】。

### 病灶 3：全量串行 R2 的边际收益递减 vs 缺少「空结果优先 + Per-Issue 证伪」

- 实证显示 R1 预设「代码必有缺陷」虽擅长深挖隐藏 Bug，但在小改动或干净代码上会诱发「硬凑 P2/P3 噪音」（如 9 行改动跑 6 轮 207 KB）；
- 现有架构用「**串行全量 R2 重读整份 Diff + 25 KB 散文报告**」去纠偏，不仅每轮多烧一整份主力模型上下文（且长文诱发 EMNLP 2025 警告的 Verbosity Bias），而且在 Delta 轮次几乎 0 拦截；
- 相比之下，OpenAI Codex 的 **「空结果优先（无确凿缺陷宁可零输出）」**、Anthropic `/code-review` 的 **「按候选缺陷 Per-Issue 并行轻验证 + Haiku/Sonnet/Opus 分级选模」**、以及 `superpowers` 的 **「Scoped Re-Review 限审修复 Diff + 接收端反驳规程」** 在误报控制与 Token 经济学上全面占优【A/B】。

### 病灶 4：零使用率的 `Artifact Review` 模式（~550 行死资产）

V2.3.0 引入的 `artifact-contract.md`（63 L）+ `round-1-artifact-red-team.md`（145 L）+ `verdict-rubric-artifact.md`（61 L）+ `templates/r1-report-artifact.md`（34 L）+ `test_artifact_schema_contract.py`（245 L）+ 门禁双分支逻辑，自上线以来在全部 9 个后续归档（含多篇纯文档规范交付）中**使用率为 0%**——实战中所有审查无一例外沿用默认代码流，独立维护一套 550 行的平行 schema 属典型投机性过度抽象。

### 病灶 5：`templates/` ↔ `references/` ↔ `scripts/` 6 处内部漂移 + 24 条文案锁死测试

- `templates/` 目录已与 `references/`、`scripts/` 全面脱节（6 处确凿漂移：R1 缺「是否由当前 Diff 引入」列、R1 §2 条件激活矛盾、R2 表头 4 列 vs 7 列、Artifact 模板缺 Top-3/⚖️、PASS 加粗校验说明过期、`prepare` 与模板索引段落不一致）；
- 同时 `test_write_channel_contract.py` **20/20 全是源码/文档子串断言**，甚至锁死 `assert 'R1-1 回归' in t`、`assert 'len(fields) >= 9' in t`（`:183, :210`），用 CI 红灯锁死了脚本内部变量名与历史补丁注释。

### 病灶 6：领域硬编码、私有历史泄露与缺少 Prompt Injection 防御

- 7 个文件共 32 行硬编码 React Rules of Hooks / Next.js SSR / Safari `localStorage` / `jsdom`；
- `SKILL.md` 充斥大量外部用户无法理解的本仓私有术语（`RFC-0001/0002`、`R1-x 回归`、`2026-10-10 216KB`）并 9 处强耦 `goal-loop` / `frontend-qa-gate`；
- 对照 `The-PR-Agent/pr-agent`【A】，缺少「**显式声明待审代码/注释/文档为 Untrusted Data**」的 Prompt Injection 免疫指令。

---

## 3. 真正值得保留的 4 项核心护城河

`dual-round-review` 绝不是应该退役的技能，它是本仓库最核心的质量守门员，以下 4 项真资产具有极高实战价值：

1. **严格上下文隔离的独立审查员 + 严禁主会话内联自审红线**（与 Anthropic 2026 Evaluator 理论完全契合）；
2. **第一性原理攻击路径推演 + 真实复现取证**（擅长揪出并发竞态、资源泄漏、契约破坏与浅层创可贴补丁）；
3. **Diff-Scope Boundary Lock（仅锁本次变更引入的缺陷，不越界批斗存量历史代码）**；
4. **结构化风险分级（P0/P1 阻断 vs P2/P3 非阻断）+ Scoped Delta 收口机制**（避免把微瑕升级为无限返工）。

---

## 4. 分阶段重构优化路线图与三档方案【C】

### 4.1 重构核心原则

**「保住隔离红队与 Meta-Judge 灵魂，砍掉 11 项脆弱正则官僚门禁与 0 用 Artifact 支线，吸收空结果优先 + Per-Issue 轻验证 + 文件化 Diff 交接 + 分级选模」**。

| 阶段 | 核心改造动作 | 预期直接收益 |
| :---: | :--- | :--- |
| **P0 止血修 Bug（低风险立即可做）** | ① 修复 `prepare-review-context.py:358` `_UNIT_RX`（去掉必选 `>` 前缀，补真实无 `>` 归档回归测试）；<br>② 修复 `check-review-report.py:216` Markdown 链接解析（提取 `](...)` 或 `basename`，不再把 `[f](./f)` 拼成 `f.f`）；<br>③ 清理/补正 2026-11-22 4 个红灯归档（或在单测明确历史兼容性策略），恢复 `pytest` 全绿；<br>④ 消除 `templates/` 与 `references/` 6 处漂移，剥离 32 行 React/Next.js 领域硬编码与私有 `RFC-0001/R1-x` 历史文案，删掉锁死内部变量名（`len(fields)`）的脆弱测试；<br>⑤ 在 R1/R2 提示词顶部加入 **Untrusted Data 防 Prompt Injection** 声明与 **「空结果优先（宁缺毋滥）」** 纪律 | 立刻修复仓库现红 `pytest` 与 17/17 隐藏失效 Bug，抑制 AI 硬凑 P2/P3 噪音 |
| **P1 架构瘦身与现代化升级（V3.0 核心）** | ① **大幅精简 `SKILL.md`（36.8 KB → ≤12 KB）**：剔除冗余借口表与本仓历史，消除 IFScale 指令坍缩；<br>② **重构 R2 触发策略**：常规小改动与 **Delta 复审轮默认跳过全量 R2**（改为单轮 Scoped Re-Review）；重型 Full 审查中，仅当 R1 报出 P0/P1 阻断项时，对候选阻断项触发 **轻量化 Per-Issue 证伪 / 元裁决**（不再对已清零或纯 P2/P3 报告烧一整轮全量 R2）；<br>③ **引入显式能力档位分层**：Scoped Re-Review / 轻查用中档，首次深水红队与争议终裁用最强档；<br>④ **轻量交接包替代重型 620 行正则门禁**：借鉴 `superpowers` 46 行 `review-package` 思路，用极薄脚本打包 `BASE..HEAD` `.diff` 文件给审查员，审查报告改用**精简 JSON/YAML Frontmatter 裁决头**供脚本 50 行确定性校验（彻底告别 620 行 Bash 风格正则刮 Markdown 表格与 Write-Once 排版返工）；<br>⑤ **退役 0% 使用率的 `Artifact Review` 独立 550 行支线**（保留 10 行通用非代码文档审查提示即可）；<br>⑥ **调整归档留存策略**：默认将详尽过程报告放 git-ignored 临时目录（或按需仅将精简终审摘要入库），逐步卸载 `docs/project/reviews/` 无限膨胀与 `doc-governance` 6 脚本豁免税 | 总代码与文档体量从 **236.8 KB → ~75–95 KB（-60%~-68%）**；单次交付审查 Token 消耗与轮次预计下降 **40%–55%**；彻底消除格式门禁导致的整轮返工 |

### 4.2 三档决策方案对比

| 方案 | 范围 | 预计体量变化 | 优点 | 代价与风险 |
| :--- | :--- | :---: | :--- | :--- |
| **方案 A（推荐）：V3.0 现代瘦身升级（P0 + P1）** | 修 2 处真 Bug + 降噪（空结果优先 / Per-Issue 证伪 / Delta 免 R2）+ 退役 0 用 Artifact + Frontmatter 轻门禁替代 620 行正则刮表 + 精简 `SKILL.md` 至 ≤12 KB + 评估归档轻量化 | **236.8 KB → ~85 KB（-64%）** | 根治 IFScale 坍缩、11 项形式门禁反噬、R2 低 ROI 空转与跨技能豁免污染；审查质量不降反升 | 涉及 RFC-0001/0002 归档门禁口径演进，需走 ADR 留痕与 `goal-loop` 专项计划 |
| **方案 B（稳健止血）：仅执行 P0** | 修 `_UNIT_RX` 与链接剥离 Bug、修绿 4 个红灯归档、对齐 6 处模板漂移、删 20 条源码变量锁死测试、加防注入与空结果优先、清 React/私有历史 | **236.8 KB → ~200 KB（-15%）** | 零架构破坏，极快恢复 `pytest` 全绿并堵住高危脚本 Bug | 未解决 `SKILL.md` 36.8 KB 指令过载、1.76 MB 归档持续膨胀、Delta-R2 空转与 0 用 Artifact 死重 |
| **方案 C（激进极简）：全面转向 `superpowers` + Codex 极简流** | 彻底放弃持久归档与 R2 机制，收缩为 200 行以内的单轮高精度 JSON Rubric + 46 行 `review-package` | **236.8 KB → ~15 KB（-94%）** | 极致轻盈零维护税 | 放弃了对高风险并发/安全改动的独立元审判把关与可追溯交付凭据，偏离本仓库严肃工程交付定位（不推荐） |
