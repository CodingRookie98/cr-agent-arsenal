# `frontend-qa-gate` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-FRONTEND-QA-EVAL-2026
> - **当前版本**: V1.0.1
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于 `skills/frontend-qa-gate/` 全部 8 个源文件（1,567 行 / 76.6 KB）、设计书、17 次 Git 提交历史、全仓 582 篇 `.md` 与 28 份计划的实战统计、5 组针对 `check-qa-report.py` 的对抗实测探针，以及配套外部调研报告 [2026-11-23-frontend-qa-gate-peer-research.md](./2026-11-23-frontend-qa-gate-peer-research.md)。
> - **证据分级**: 【A】一手（本仓库全量源码/行号/实跑 pytest 与 5 组实测对抗探针、外部标杆一手源码）｜【B】二手转引（工程文摘要）｜【C】架构师诊断与重构方案

> [!NOTE]
> **执行注记 (2026-11-24)**：**Wave 3（[frontend-qa-gate-design.md](../architecture/frontend-qa-gate-design.md) V2.0.0）已按本报告推荐的方案 A 完成双轨真实磁盘证据化升级**——拆分为 Tier 1（23 项自动化阻断）与 Tier 2（4 项人工/真机签收）破除无头死锁，新增 `references/probe-orchestration.md` 现代探针编排，重铸 Schema v2 Fail-Closed 真实磁盘证据 JSON 门禁 `scripts/check-qa-report.py`（配 `templates/qa-evidence-template.json` 与 `templates/qa-summary-template.md`），新建 `test_frontend_qa_evidence_gate.py` 与 `test_frontend_qa_v2_surface.py`，并退役原 433 行中文正则校验器、`.sh` 兼容壳、`browser-verification-protocol.md`、`qa-report-template.md` 与 `test_qa_gate_contract.py`。下文所有体量与路径均为 **Wave 3 重构前审计时刻的历史快照**（已退役或迁移的文件引用已转为纯反引号代码片段防止 404 断链）。

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.1** | 2026-11-24 | AI Agent | 核心架构组 | 补充 Wave 3（V2.0.0）已按方案 A 完成双轨真实磁盘证据化升级的执行注记，并将下文指向已退役 V1 文件的相对链接转为纯反引号代码片段防止 404 断链 |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `frontend-qa-gate` 8 文件体量倒挂审计、5 组实测击穿 `check-qa-report.py` 铁证、永久 BLOCKED 死锁机理分析、与本机可执行浏览器技能生态对比及两档重构方案 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`frontend-qa-gate` 是否过度设计？是否跑偏？**

**结论：思想内核非常正确（拒绝主观打分、诚实标出未验证项、按四类缺陷回流路由），但工程实现严重跑偏为典型的「零采集能力 + 只验表不验真（Paperwork Theater）」过度设计——全技能 73.3% 的行数（1,149 行）消耗在 433 行中文自然语言反走私正则器与 711 行单测的猫鼠战里，实际驱动浏览器采集的代码 = 0 行、全仓实战产出报告 = 0 份，且经 5 组对抗探针实测，该校验器连「失败 99 条 / 全域 FAIL / `~~~` 围栏 / 证据文件不存在」都全线放行 Exit 0！同时其「真机读屏无降级即 BLOCKED」设计在无头 Agent 环境下构成 100% 永久死锁。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **体量与演化倒挂** | 8 文件 **1,567 行 / 76.6 KB**：格式校验脚本（433 L）+ 单测（711 L）占 **73.3% 行数 / 66.6% 字节**；可执行浏览器/a11y/性能代码 **0 行**；17 次提交中 **11 次（65%）** 陷入中文否定词正则猫鼠战 | 把绝大部分工程预算花在“校验 Markdown 中文措辞”上，本末倒置 |
| **实战使用率** | 扫描全仓 582 个 `.md` 与 28 份计划：真实《前端验收报告》= **0 份**；业务实跑 **0 次**（全部 5 次计划提及均为建技能、打补丁、抄范式与迁 Python） | 上线以来零真实前端产品反馈闭环，属闭门纸上打磨 |
| **门禁脚本 5 连击穿** | 实跑 `--require-verdict=PASS --min-assertions=15`：① 结论表失败 99 条+第 3 章 0 断言+第 6 章塞 15 个 `[ ]`+第 4 章有序列表 → **Exit 0**；② `~~~` 围栏整篇包裹 → **Exit 0**；③ 无标题无表格纯散文子串 → **Exit 0**；④ 5 域全 FAIL 仅结论列写 PASS → **Exit 0**；⑤ 协议要求的「证据文件真实存在 / nonce / 空白图」全部 **0 行校验** | **假安全感门禁**：拦不住刻意敷衍与空壳造假，却徒增大量排版摩擦 |
| **架构死锁与漂移** | 必含 A5 读屏、V4/V5 真机软键盘刘海屏、B1/B2 Safari 最低版 + 无降级即 `BLOCKED` + `goal-loop` HARD-GATE 禁合并；`dual-round-review/SKILL.md:123` 调用命令甚至漏传 `<报告文件>` 必选参数 | 在无头宿主下 100% 永久死锁，反向逼迫伪造 PASS；跨技能接口已多处漂移 |
| **本机生态高度割裂** | 本机已安装 `chrome-devtools-plugin`（`a11y-debugging` + `debug-optimize-lcp`）、`agent-browser`（Rust CDP + `dogfood`）、`webapp-testing`（Playwright + `with_server.py`），全部自带真执行层 | 本技能既不调用上述真实探针，又与 `taste-driven-designer` Gate A 双向互指重复定义 |

---

## 1. 体量结构与 59 条单测的成分解剖【A】

| 文件路径 | 行数 | 字节数 | 占比 | 实质定位与缺陷 |
| :--- | :---: | :---: | :---: | :--- |
| [SKILL.md](../../../skills/frontend-qa-gate/SKILL.md) | 110 | 7.0 KB | 9.1% | 路由层、8 条铁律、五域索引、能力门控（无降级即 BLOCKED 死锁源头） |
| [acceptance-matrix.md](../../../skills/frontend-qa-gate/references/acceptance-matrix.md) | 103 | 7.5 KB | 9.8% | 五域 31 条静态断言（与 `taste` Gate A 双向互指且枚举漂移） |
| `browser-verification-protocol.md`（原 `skills/frontend-qa-gate/references/browser-verification-protocol.md`，已退役） | 68 | 4.4 KB | 5.7% | 强制要求证据文件存在、nonce、commit、时间戳、空白图作废——**脚本 0 行落实** |
| [regression-routing.md](../../../skills/frontend-qa-gate/references/regression-routing.md) | 54 | 3.2 KB | 4.2% | **高价值内核**：4 类缺陷回流路由（行为修复 / 回 `taste` / 转 `dual-round-review` / 人类裁决） |
| `qa-report-template.md`（原 `skills/frontend-qa-gate/templates/qa-report-template.md`，已退役） | 83 | 3.4 KB | 4.4% | 8 节重型手工填写报告模板 |
| [check-qa-report.py](../../../skills/frontend-qa-gate/scripts/check-qa-report.py) + `.sh` | 438 | 17.2 KB | **22.5%** | 433 行正则格式检查器（Bash 1:1 转译，不支持 `--help`，USAGE 仍写 `bash .sh`，5 组探针全击穿） |
| `test_qa_gate_contract.py`（原 `skills/frontend-qa-gate/tests/test_qa_gate_contract.py`，已退役） | 711 | 33.8 KB | **44.1%** | 实跑 `59 passed (3.24s)`：**33 个（55.9%）**是第 4 章中文 NLP 否定句猫鼠测试 + 12 个静态文案锁死 + 3 个正则自检，行为验证前端产物 = **0** |

> 另核实 3 处同步滞后【A】：[frontend-qa-gate-design.md](../architecture/frontend-qa-gate-design.md) L125 仍停留在「17 个用例」与 `bash -n`；[dual-round-review/SKILL.md](../../../skills/dual-round-review/SKILL.md) L123 硬编码的门禁命令漏掉了必选位置参数 `<报告文件>`（执行必报 `rc=2`）；`test_qa_gate_contract.py:44` 内联跨技能正则漏掉 `clarification-protocol`（与 `_shared/cross-skill-link-policy.json` 7 技能漂移）。

---

## 2. `check-qa-report.py` 五组实测击穿铁证【A】

在最严苛门禁参数 `--require-verdict=PASS --min-assertions=15`（或 `5`）下，内存直调 `check_report()` 实测全部放行（**Exit 0**）：

| 探针 | 构造载荷 | 实测结果 | 源码根因（精确行号） |
| :---: | :--- | :---: | :--- |
| **P1** | 结论表写失败 **99** 条、第 3 章 **0 条断言**、第 6 章塞 15 行未勾选 `- [ ] dummy`、第 4 章用有序列表 `1. A5 未验证` 与纯段落 | **PASS (Exit 0)** | `:321` `ASSERT_LINE_RE` 扫整篇 `body` 不限第 3 章且不区分 `[x]`/`[ ]`；`:206-215` 不校验「失败」列=0；`:72` `OTHER4_LINE_RE` 仅扫 `[-|>]` 行，放行有序列表/段落/同义词 |
| **P2** | 整份伪造报告包在 CommonMark `~~~markdown ... ~~~` 围栏代码块内 | **PASS (Exit 0)** | `:50` `FENCE_LINE_RE` 只认 `` ``` ``，未同步 `check-review-report.py:91` 对 `~~~` 的修复 |
| **P3** | 全文无任何 `## 1..7` 标题、无结论表，仅在散文行内顺口提及章节名与「断言 5」+ 5 行勾选项 | **PASS (Exit 0)** | `:112-121` 用子串 `needle in line` 匹配而非行首 `startswith`；无表格行时校验循环为空直接通过 |
| **P4** | 结论表 5 域全 FAIL（通过 0 / 失败 5）、明细全 `[ ] FAIL`，仅结论列填 `PASS` | **PASS (Exit 0)** | `:347-365` `check_verdict` 完全不核对「通过/失败」列数值与 `[x]` 勾选状态 |
| **P5** | 协议强制要求的「证据文件真实存在 / nonce / commit / 空白图作废 / 模板 `<...>` 清零」 | **全部 0 行校验** | `browser-verification-protocol.md:22-48` 与脚本实现存在彻底断层；连原模板本身在无 verdict 模式下也 `rc=0` 通过 |

---

## 3. 结构性硬伤：无头环境下的「永久 BLOCKED 死锁」【A/C】

[acceptance-matrix.md](../../../skills/frontend-qa-gate/references/acceptance-matrix.md) 强制纳入了无头 Coding Agent 宿主物理上几乎不可能具备的条目：
- **A5（L61）**：真实屏幕阅读器（VoiceOver / NVDA）全流程操作；
- **V4 / V5（L42–43）**：真机移动端软键盘弹出不遮挡、刘海屏安全区；
- **B1 / B2（L72–73）**：目标浏览器最低支持版本（含 Safari / WebView）；
- **S2 / S9 / P3（L22, 29, 84）**：人工判定项。

同时 `SKILL.md:46,62` 严令「**无降级通过路径**，缺能力唯一合法输出为未验证 + `BLOCKED`」，而 `goal-loop/references/stage-progression-protocol.md:220` 又设定 `HARD-GATE`「**FAIL / BLOCKED 严禁合并**」。两者相乘的结果是：**任何严格遵守诚实原则的 Agent 在 Linux 无头/CI 环境下都会 100% 永久卡死在 BLOCKED**，最终反过来逼迫代理把未测项胡乱标成 `N/A` 或伪造 `PASS`。

---

## 4. 真正值得保留的 3 项核心护城河

剥离空壳正则门禁与死锁条款后，本技能有三项极有价值的思想资产值得保全：
1. **反对绝对打分的诚实三态语义**：区分「已运行通过 / 失败 / 受限未验证」，杜绝用自动扫描得分冒充可用性完备；
2. **四类缺陷精确回流路由**（[regression-routing.md](../../../skills/frontend-qa-gate/references/regression-routing.md)）：将行为实现缺陷、结构品味缺陷（回 `taste`）、深层代码根因（转 `dual-round-review`）与方向裁决分流，避免胡乱返工；
3. **前端五域风险清单视角**（响应式 / 交互状态 / 无障碍 / 跨浏览器 / 性能）：作为探针编排的覆盖面蓝图（而非手填 31 行表格的官僚负担）。

---

## 5. 两档重构去向方案对比【C】

对照 [调研报告 §2](./2026-11-23-frontend-qa-gate-peer-research.md) 的三层黄金架构与本机已装的真实可执行浏览器技能（`chrome-devtools-plugin`、`agent-browser`、`webapp-testing`），给出两档清晰方案：

| 方案 | 核心动作 | 预计体量变化 | 优点 | 代价与风险 |
| :--- | :--- | :---: | :--- | :--- |
| **方案 A（推荐）：瘦身 + 实采化改造（升级为「前端探针编排协议」）** | ① **彻底废弃 433 行中文 Markdown 反走私正则器与 33 个猫鼠用例**；<br>② **直连真实执行探针**：将技能主干改为按宿主能力自动路由到 `chrome-devtools-mcp`（`a11y-debugging`/`debug-optimize-lcp`）、`agent-browser dogfood` 或 `playwright test` + `@axe-core/playwright` + `lhci`，门禁脚本瘦身为 ~60 行**真物证校验器**（校验截图/trace 文件磁盘真实存在且非空、Console/PageError=0、axe/LHCI JSON 退出码 = 0）；<br>③ **硬拆两层门禁破除死锁**：拆为「**自动化必过门禁（Block Merge）**」与「**真机/读屏人工签收清单（Human Sign-off）**」；<br>④ **消除双向重复**：由本技能单一承载前端可用性清单，从 `taste-driven-designer` 抽离重复状态矩阵，修复 `dual-round-review/SKILL.md:123` 缺参错误 | **76.6 KB → ~20–25 KB（-70%）** | 彻底终结「只验表不验真」与永久 BLOCKED 死锁，让门禁真正盯住运行态事实；维护面骤降 70% | 若后续仓库仍长期无前端项目，仍需在外部前端仓做一次端到端实跑校验 |
| **方案 B（吸收合并）：不再维护独立技能，并入上下游并委派成熟外部工具** | 若本仓定位聚焦后端/通用工程治理、不打算维护独立前端 QA 编排层：将 **四类缺陷回流路由 + 人工签收清单元件**精简（~30 行）并入 `goal-loop` P3.5 / `taste-driven-designer`，实际浏览器与性能验收直接调用外部成熟标杆（`agent-browser dogfood` + `chrome-devtools-plugin` + `webapp-testing`） | **76.6 KB → 0**（净省 1,567 行） | 零重复造轮子、零维护税、立即消除跨技能硬编码耦合 | 若目标宿主未安装 `chrome-devtools-plugin` 或 `agent-browser`，缺少独立的五域前端验收蓝图 |
