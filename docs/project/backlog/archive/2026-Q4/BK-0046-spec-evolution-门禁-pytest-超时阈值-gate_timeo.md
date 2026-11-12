---
id: BK-0046
title: spec-evolution 门禁 pytest 超时阈值（GATE_TIMEOUT=300s）与实际套件时长临界导致 C-09 假 BLOCKER
type: Bug
status: completed
priority: P2
trigger: 执行 spec-evolution 的 collect-facts.py 采集全量门禁时（尤其在 /mnt/d 9p 文件系统、PYTHONPYCACHEPREFIX
  冷导入或机器负载较高时），pytest 门禁超时记为 exit 124，judge.py 的 C-09 随即判 F-01 BLOCKER
created_at: '2026-10-20'
updated_at: '2026-11-12'
closed_at: '2026-11-12'
resolution: delivered
destination: docs/project/backlog/archive/2026-Q4/BK-0046-spec-evolution-门禁-pytest-超时阈值-gate_timeo.md
source:
- 2026-10-20 P3 批次六项卡片交付（R1/R2/delta-r2 审查与交付取证期间实测）
- skills/spec-evolution/scripts/collect-facts.py:42 GATE_TIMEOUT
acceptance_criteria:
- spec-evolution 门禁不再因套件时长抖动误报 C-09 BLOCKER：TIMEOUT 与真实门禁失败可区分（或以可配置/自适应阈值消除临界）；collect-facts.py
  门禁与 judge.py 对超时语义的判定同步更新，并有回归测试覆盖（模拟超时场景不误判为交付基线不成立）
- WSL 直跑全量 pytest（503 用例、约 204~300s）时 collect-facts.py 全量门禁 exit 0、judge.py findings
  无 BLOCKER/HIGH
- SKILL.md / checks-spec.md（C-09 语义）/ 架构设计书 三处超时与退出码说明同步更新，文档门禁全绿
---

## 1. 背景与问题陈述
skills/spec-evolution/scripts/collect-facts.py:42 硬编码 GATE_TIMEOUT = 300（秒），collect_gates() 对每条门禁命令执行 subprocess.run(..., timeout=GATE_TIMEOUT)，超时统一记 exit_code=124、summary=TIMEOUT after 300s；judge.py 的 C-09 判据「既有门禁非零退出」据此产出 F-01 BLOCKER（消息：既有门禁非零退出，交付基线不成立）。实测：WSL 直跑全量 python3 -B -m pytest skills/ -q -p no:cacheprovider = 503 passed / 204.09s（暖缓存）；但 collect-facts 在 PYTHONPYCACHEPREFIX 重定向导致冷导入的条件下同一命令 >300s，2026-10-20 连续多次 TIMEOUT，使 judge 输出 F-01 BLOCKER，而套件本身 0 failed。历史对照：2026-10-13/14 套件 450~472 用例时同一门禁可通过（findings=4 / blocker·high=0）。危害：(1) 交付的 judge 门禁在套件规模增长后不可用，产生假 BLOCKER 污染交付证据；(2) TIMEOUT(124) 与真实失败同属非零，判定器无法区分，掩盖真实门禁问题或反向误伤。

## 2. 影响面与技术考量
- 涉及模块: `skills/spec-evolution/scripts/collect-facts.py`（`:42` `GATE_TIMEOUT`、`collect_gates()` 与 `subprocess_env()` 的冷导入口径）、`skills/spec-evolution/scripts/judge.py`（C-09 判据与 F-01 BLOCKER 渲染）、`checks-spec.md`（C-09 语义）、`SKILL.md`、`docs/explanation/architecture/spec-evolution-design.md`；间接影响所有把 judge 退出码当交付门禁的批次计划与审查归档。
- 风险点: 单纯调大阈值只是把临界点后移（套件继续增长仍会复发）且拉长门禁反馈时间；把 TIMEOUT 直接降级为非阻断会削弱 RFC-0004 的 fail-closed 硬条件（结论必须锚定真实退出码、真实非零退出即阻断），需保留该语义；`PYTHONPYCACHEPREFIX` 冷导入成本需实测，避免用「放宽超时」掩盖真实性能退化；Windows 与 WSL 的耗时差异（cp936/9p I/O）需一并纳入口径。
- 候选方向（择一或组合）: (a) 阈值可配置（CLI/环境变量）并对 124 输出可诊断的「门禁超时」finding（保留阻断但不与「真实失败」同码）；(b) 门禁改用稳定子集/预热缓存的等价命令（不得破坏 GI-6 只读不变式）；(c) 按套件规模或机器基准自适应阈值，并在报告中记录实测耗时以便趋势监控。

## 3. 验收准则与验证设计 (DoD)
- [x] spec-evolution 门禁不再因套件时长抖动误报 C-09 BLOCKER：TIMEOUT 与真实门禁失败可区分（或以可配置/自适应阈值消除临界）；collect-facts.py 门禁与 judge.py 对超时语义的判定同步更新，并有回归测试覆盖（模拟超时场景不误判为交付基线不成立）
- [x] WSL 直跑全量 pytest（503 用例、约 204~300s）时 collect-facts.py 全量门禁 exit 0、judge.py findings 无 BLOCKER/HIGH
- [x] SKILL.md / checks-spec.md（C-09 语义）/ 架构设计书 三处超时与退出码说明同步更新，文档门禁全绿

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
**2026-11-12 结项（resolution=delivered）。**

修法（三处代码 + 三处文档）：

1. `skills/spec-evolution/scripts/collect-facts.py`：`GATE_TIMEOUT` 300 → 600，并给门禁结果追加显式语义位 —— 产出字段扩展为 `{"cmd","exit_code","summary","timed_out","error","duration_s"}`。超时置 `timed_out=True`；`OSError`（如 9p `[Errno 19] No such device`）置 `error`。阈值只决定跑不跑得完，超时语义交给 `timed_out`，不靠调大数字掩盖问题。
2. `skills/spec-evolution/scripts/judge.py`：新增 `_gate_state(info)` 三态 —— `timed_out` 或 `error` → `incomplete`（不产 finding）、`exit_code != 0` → `failed`、否则 `ok`。C-09 只对 `failed` 产 BLOCKER。标记缺失仍按 `failed` 处理（宁可真红不可漏放，保留 fail-closed 语义）。
3. `render_report` 拆出 `_gate_rows` / `_incomplete_note`，BLOCKER 段四态：有 failed → 表格（若同时有未得出结论的门禁追加附注）；仅 incomplete → 「（N 道门禁**未得出结论**：… —— 既非失败亦非通过，本报告不据此对交付基线表态）」；未采集 → 原文案；全绿 → 「（已采集门禁事实，无失败）」。
4. 回归测试三条（`skills/spec-evolution/tests/test_judge_contract.py`）：`test_c09_gate_timeout_is_not_a_blocker`、`test_c09_real_failure_still_blocker_next_to_timeout`、`test_c09_gate_execution_error_is_not_a_blocker`。
5. 文档三处同步：`SKILL.md`（C-09 行标注「超时不计」+ 退出码 0 语义）、`references/checks-spec.md`（C-09 判定列、BLOCKER 语义、追加 V1.2.0 修订记录）、`docs/explanation/architecture/spec-evolution-design.md`（§3.2 字段、§3.3 新增「C-09 的三态」）。

验收取证（2026-11-12，WSL）：

- `python3 -m pytest skills/spec-evolution/tests -q -p no:cacheprovider` → **71 passed**。
- `collect-facts.py --out …` → `COLLECT_RC=0`；`judge.py` → `findings=3, blocker/high=0`，`JUDGE_RC=0`；报告 BLOCKER 段渲染为「（已采集门禁事实，无失败）」。pytest 全量门禁在 600s 阈值内正常跑完（9p 上约 6~7 分钟），未触发 `timed_out`。
- 文档门禁：`check-doc-links.py` 0 断链、`audit-doc-health.py` PASS 99.8/100、`test_cross_skill_links.py` 4 passed。

剩余 3 条 findings 全为 MID（F-01 clarification-protocol description 623 字符 / F-02 `test_doc_governance_scripts.py` 超 1000 行 / F-03 dual-round-review description 738 字符），即 BK-0041 §4 已裁定「接受偏离」的三项，不再作为本卡验收对象。

一句话结论：**超时不再伪装成「交付基线不成立」，而是显式表达为「本轮未取证」；真实非零退出仍然阻断。**

### 红队复审 (R1, 2026-11-12)

独立子智能体只读审查 + 变异实验，首轮裁定 `BLOCKED: 1`，逐条修复后复验：

- **[BLOCKER] B1 规范与实现不一致**：`references/checks-spec.md` 的 C-09 判定式只写「`timed_out` 非真」、漏 `error` 为空——按字面会把本卡要修的第二类假阻断（9p 断连的 `OSError`）原样写回规范。已补「**且** `error` 为空」，§2 严重度语义与 V1.2.0 修订记录同步补 `error`。
- **[HIGH] H1 报告头条自相矛盾**：超时-only 时 `render_report` 的 verdict 仍只由 findings 决定，输出 `CLEAN`，与 BLOCKER 段「本报告不据此对交付基线表态」反向表述。已加第四态：无 finding 但存在 `incomplete` 门禁时判 `INCOMPLETE`；`test_c09_gate_timeout_is_not_a_blocker` 补 `判定结论: **INCOMPLETE**` 断言。
- **[HIGH] H2 测试杀不死「按退出码猜 124/125」**：把 `_gate_state` 变异为 `exit_code in (124, 125)` 时原有 C-09 用例全绿（都自带语义位）。已补两条 fail-closed 用例：`test_c09_timeout_code_without_marker_still_blocker`（124 无 `timed_out`）、`test_c09_execution_error_code_without_marker_still_blocker`（125 无 `error`），断言仍产 BLOCKER。**变异复验：改回猜码后这 2 条立即转红（2 failed），还原后 6 passed。**
- **[MID] M1/M2 文档漏 `error`**：设计书 §3.2 字段表补 `error`、§3.3 三态定义改为「超时 **或** 采集器未能执行」、结论态补 `INCOMPLETE`；`SKILL.md` 删悬空的「见下」，补「**未得出结论**」整段（超时/采集失败不产 finding、结论记 `INCOMPLETE`、语义位缺失一律按失败处理）。
- **[MID] M3 超时丢弃已捕获输出**：`TimeoutExpired.stdout` 实测非空却被替换成一句 `TIMEOUT`，导致「跑到一半才挂死」与「一行没跑」无法区分。已保留 `exc.stdout`（bytes 时先解码）再追加 `TIMEOUT after 600s`。
- **[MID] M4 余量基数算错**：注释原按「503 用例 204s（暖缓存）」得 3 倍余量，而同一门禁在 9p 冷导入实测 360~420s，600s 实为 **1.4 倍**。注释已按最坏实测改正。
- **[MID] M5 未提交 diff 混入 P5 撤回**：事实正确但与 C-09 语义修复无因果关系；本次**未提交**，提交时拆成两次（P5 撤回 / C-09 语义）。
- **[OK] 复核通过项**：`timed_out` 缺失一律按失败（fail-closed）、`gates` 为 `null`/`{}`/`[]` 不误伤、failed 与 incomplete 并存不丢信息、原三条测试确由语义变更驱动（变异回二态时 3 failed），均由探针/变异实测确认。

复审后复验：`pytest skills/spec-evolution/tests` **73 passed**；`check-doc-links.py` 90 文件 0 断链；`audit-doc-health.py` PASS；`test_cross_skill_links.py` 4 passed。

### 结项记录 (2026-11-12)
- **结论**: delivered
- **去向/凭据**: docs/project/backlog/archive/2026-Q4/BK-0046-spec-evolution-门禁-pytest-超时阈值-gate_timeo.md
- **归档目录**: archive/2026-Q4/
### 红队复审 (R2, 2026-11-12)

同一独立子智能体在隔离副本（`D:/_se_reverify`）重跑，裁定 **ZERO BLOCKERS**；首轮修复项逐条自跑变异复核（不采信作者自报）：`_gate_state` 改按码猜 → 2 failed（恰为两条 fail-closed 用例）；verdict 的 `INCOMPLETE` 改回 `CLEAN` → `test_c09_gate_timeout_is_not_a_blocker` 转红；删 `or info.get("error")` → `test_c09_gate_execution_error_is_not_a_blocker` 转红。渲染四态与 INCOMPLETE 和模板/既有用例的兼容性均实跑核对通过。

R2 提出并已修复的残余问题：

- **[HIGH] H-1 部分输出永远进不了 `facts.json`**：超时分支虽保留 `exc.stdout`，却把 `partial` 拼在 `TIMEOUT` **之前**，而事实层落盘的是 `"summary": lines[-1]`（stdout 最后一行）—— 落盘的永远只是那句 `TIMEOUT after 600s`，「跑到一半才挂死（teardown 卡住）」与「一行没跑」仍不可区分，注释宣称的证据保留并未生效。已改为 `stdout = (tail + "\n" + partial.rstrip()) if partial.strip() else tail`，并在注释写明「`summary` 取最后一行，tail 放前、部分输出放后」。
- **[MID] M-1 采集层新字段零覆盖**：`test_collect_facts.py` 原本全部走 `--no-gates`，超时 / `OSError` / 部分输出三处新逻辑没有测试覆盖。已补两条：`test_gate_timeout_keeps_partial_output`（注入 `GATE_TIMEOUT=1` + 先 `print` 后 `sleep` 的假门禁，断言 `timed_out=True`、`exit_code=124`、`summary` 含 `FAILED test_x`）、`test_gate_execution_error_records_reason`（门禁命令指向不存在路径，断言 `exit_code=125`、`error` 非空、`timed_out=False`）。**变异复验：把拼接顺序改回 `partial + tail` 后该用例立即转红（`assert FAILED test_x in TIMEOUT after 1s`），还原后 21 passed。**
- **[MID] M-2 RFC-0004 与实现不一致**：`:179` 的 C-09 行与 `:183` 的严重度语义仍写「任一非零退出 → BLOCKER」，`:26` 的 V0.6.0 行漏 `error`。已同步为三条件（`exit_code != 0` **且** `timed_out` 非真 **且** `error` 为空），并把 V0.6.0 行标注为「本行含两项独立变更，提交时应拆分」。
- **[MID] M-3 退出码 `0` 的消费口径未写死**：`0` 只表示「无 BLOCKER/HIGH」，存在未得出结论的门禁时判定结论行是 `INCOMPLETE`。已在 `SKILL.md` 写明「消费方不得只读退出码，必须读判定结论行」。
- **[MID] M-4 提交拆分**：本次仍未提交（AGENTS.md 未获授权不 commit）；拆分点已写进 RFC-0004 V0.6.0 行内标注（P5 撤回 / C-09 语义修复）。
复审后最终全量取证（2026-11-12 18:14~18:22，WSL）：

- `collect-facts.py` 四道门禁全 `exit=0` / `timed_out=False`：`pytest` **510 passed in 339.53s**（600s 阈值，约 1.8 倍余量）、`check_doc_links` 30.1s / 90 文件 0 断链、`audit_doc_health` 22.1s / **PASS**、`cross_skill_links` 8.1s / 4 passed。
- `judge.py` → `findings=3, blocker/high=0`、`JUDGE_RC=0`、判定结论 `MID`、BLOCKER 段渲染「（已采集门禁事实，无失败）」；3 条 MID 即 BK-0041 §4 已裁定「接受偏离」项。
- `pytest skills/spec-evolution/tests` **75 passed in 56.16s**（含 R2 新增两条采集层用例）。
- 归档后 `docs/llms.txt` 重新生成（87 篇），文档门禁复跑仍全绿。
