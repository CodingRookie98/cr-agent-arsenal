# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

> **审查模式**: DELTA_RE_LOOP（定向再循环核验）｜**审查基线**: 455eccc...d0a8fe1（该区间实际含 3 个提交：d7a524d 文档收录、437baed R1 报告归档、d0a8fe1 修复本体）｜**Previous Blockers**: R1-1、R1-2
> **边界锁**: 仅审查 455eccc...d0a8fe1 的变更行及其紧邻 5~10 行；未被本次触及的历史行为一律标注「历史既有」且级别限 P2/P3；R1-5（--archive-root 包含性校验）按 R2 驳回裁定**不计入阻断**。
> **方法**: 全部实测在 /tmp 隔离副本内完成（cp -a 后操作）；本审查对工作树、分支、索引零改动。审查期间观测到 docs/project/plans/2026-10-08-subagent-direct-write.md 于 11:22:02 被外部（编排者）修改，非本审查所为，亦不构成本轮结论依据。

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **本质根因修复（但根治面不完整）**。R1-1 的根因是「预授权路径是**工作区脏净状态**的函数，而非基线的函数」——修复以 fail-closed 守卫（--round 时无显式基线即拒绝产出路径，prepare-review-context.sh:139-147）切断了漂移的**发生器**，这是根因层处置，不是措辞补丁；R1-2 的根因是「schema 由 6 列扩为 7 列而生成器字面量未同步」——修复即字面量补列（:328-329），属精确最小修复。**但**「孤儿报告」问题只被解决了一半：修复堵住了发生器，未补**检测器**——门禁仍只遍历台账行（check-review-report.sh:155-197），不枚举归档目录中未登记的报告文件。该缺口 R2 未列为处置要求，故不据此定阻断，仅登记为残余 DR-3。
- **物理与业务一致性**: 修复前，路径 = f(基线, 自适应模式(树脏净), 轮次, 归档根, slug, 日期)，其中「自适应模式」是树状态的函数，导致同一条命令两次调用可产出两个文件名；修复后 --round 场景下模式不再由树状态决定，路径成为 (BASE_SHA, HEAD_SHA 解析值, 轮次, 归档根, slug, 日期) 的确定函数。实测 A2/A3 证明：显式基线下，工作区被 scaffold 自身产物弄脏（新增 .review-context/ 与 docs/ 未跟踪项）**不改变**路径；A4 证明目标文件存在时 Write-Once 告警真实触发。业务语义自洽：Write-Once 的前提「同轮次 + 同基线 ⟹ 同路径」被恢复。--working/--staged 被显式放行，其 base7 位取 working/staged 字面量，属 RFC-0001 既有命名，本次未改动（历史既有，不在本轮范围）。
- **过度设计审计**: 无新增抽象，净代码增量约 20 行（+536 中绝大多数为报告归档与文档）。R1-5 被 R2 驳回后**未**强加 --archive-root 包含性校验（prepare-review-context.sh:95 仍为裸赋值），未把「授权方自持参数」伪装成安全边界，此项自律应予确认。末列定位用字段数三元而非重构解析器、以独立布尔 ROUND_SET 而非改写既有分支，均为最小实现。唯一可议之处：修复把「路径必须是基线的确定函数」写成 SKILL.md:123 的「预授权六条」，却未同步 RFC-0002:107 的「预授权五条」（→ DR-1）。

## 1.5 定向再循环核验（Proof of Fix · 本轮核心）

### R1-1 路径确定性（隔离仓库实测，2 提交 + 期间 HEAD 漂移）

| 用例 | 命令要点 | 实测结果 | 判定 |
|:---|:---|:---|:---|
| A1 | --slug=demo --round=r1（不传基线） | rc=1，报「--round 要求确定性基线——请显式指定 BASE_SHA [HEAD_SHA]，或显式给出 --working / --staged」 | **守卫生效** |
| A2/A3 | --slug=demo --round=r1 HEAD~1 HEAD 连跑两次（第 2 次工作区已被 scaffold 弄脏：?? .review-context/、?? docs/） | 两次同路径 r1-d652fcb..c091765.md | **路径稳定（核心不变量成立）** |
| A4 | 目标文件存在后再跑同命令 | 输出「⚠️ 目标文件已存在（Write-Once 保护）」 | Write-Once 可触发，不再静默 |
| A5 | 仅 1 个位置参数（SKILL.md:153 明文形式 BASE_SHA [HEAD_SHA]）+ 两次调用间 HEAD 前进 | 路径由 r1-2606378..255127e.md 变为 r1-2606378..e9ad591.md | **残余 DR-3** |
| A5b | 两个位置参数均为字面 SHA + 期间 HEAD 前进 | 两次均 r2-2606378..255127e.md | 双 SHA 形式完全确定 |
| A6 | --round=delta-r1 --working / --staged | rc=0，路径固定为 delta-r1-working.. / delta-r1-staged.. | 显式模式放行且确定 |
| A7 | --round=r1 --no-record --working | rc=1「--round 与 --no-record 互斥」 | 显式拒绝 |
| A8/A9 | --round=（空值），分别带/不带 --slug | 均 rc=1「--round 值不能为空」 | 静默失联已堵死 |
| A10 | --round=r9 | rc=1，白名单报错 | 未回归 |
| A11/A16 | 不传 --round 的自适应模式（净树/脏树） | rc=0，仍按树状态选择 range/working | 既有能力未被破坏 |
| A12/A13 | --round + -w + 位置参数（位置参数优先）/ -w 与 -s 同用（后者胜出） | rc=0，路径确定 | 组合无歧义 |
| A14 | 未知选项 --bogus | rc=1 | 未回归 |

**结论**：R1-1 的原始逃逸路径（净树→range、脏树→working 的自动切换）在 --round 下**已不可达**；R2 处置要求 (a) 显式基线、(b) 异常表补重派分支、(c) 补回归断言三项均已落地且经变异反证。

### R1-2 scaffold 表头与门禁直通（实测）

| 检查 | 实测结果 |
|:---|:---|
| scaffold 表头 | 「\| 轮次 \| 基线 \| 派发句柄 \| 报告文件 \| SHA256(前 12 位) \| 结论 \| 写入形态 \|」，separator 行同为 7 列；header_cols=7、sep_cols=7（prepare-review-context.sh:328-329） |
| 新 scaffold 归档 + 两行合法 7 值台账（放入真实 R1/R2 报告并登记真实指纹） | check-review-report.sh **rc=0**「结构校验通过: 索引齐备 · 报告 2 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐」——**无需任何手工补列** |
| 对照组：同一 scaffold 写入 6 值行 | rc=1「台账缺少「写入形态」登记」 |

**结论**：R1-2 已根治；「合法形态无自动生成途径」的镜像残余**不存在**——行由编排者登记属既有设计（脚本仅生成表头与分隔行，grep 确认 scripts/ 内无行生成器），非本缺陷的残余。

### 次生回归的变异反证（M1–M8，全部在隔离副本执行）

| 变异 | 预期捕获者 | 实测 |
|:---|:---|:---|
| M1 删除确定性守卫（exit 1→true） | test_round_requires_explicit_baseline | **捕获**（该用例唯一失败）；变异后无基线 --round 实测 rc=0，证明变异有效 |
| M2 表头退回 6 列 | test_scaffold_index_header_has_write_mode_column | **捕获**（唯一失败） |
| M3 ROUND_SET 退回 -n ROUND | test_empty_round_rejected | **捕获**（唯一失败）；变异后 --round= 实测 rc=0 |
| M4 删除 --no-record 互斥 | test_round_with_no_record_rejected | **捕获**（唯一失败） |
| M5 反转末列三元为 (NF>=9) ? $8 : $(NF-1) | 应有行为用例 | **未捕获：89/89 全绿**；而反转实现使「结论含裸竖线」的合法行实测 rc=1（正确实现 rc=0）→ DR-2 |
| M6 SKILL.md 回退为 12 位截断复算 | test_skill_fingerprint_comparison_is_full_value | **捕获**（唯一失败） |
| M7 删除 R1 模板占位符兜底 | test_templates_guard_unreplaced_placeholder | **捕获**（唯一失败） |
| M8 删除异常分支 7（重派） | test_skill_documents_replay_branch | **捕获**（唯一失败） |

### 整体复跑与文档措辞核验

- **L1**（skills/dual-round-review/tests）= **89 passed**；**L2**（pytest skills 全量）= **226 collected**，与计划登记口径一致；**全仓** pytest = **493 passed / 0 failed**（.agents 267 + skills 226）。
- 两处真实归档门禁均 **rc=0**（2026-10-08-subagent-direct-write、2026-10-04-review-report-archive）。
- **R1-3 措辞核验（实测）**：删除表头「写入形态」单元格后门禁仍 rc=0（证明确实**不解析表头**）；再删除数据行取值后 rc=1（取值校验严格）。SKILL.md:127 的「机制如实说明」**属实**，R2 的改文档而非补实现裁定正确。
- **R1-5 未采纳核验**：prepare-review-context.sh:95 仍为裸赋值，未新增包含性校验 → 符合驳回裁定，本轮不计入任何缺陷项。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

未激活（非客户端/SSR 改动）

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

- **攻击路径 1: 按 SSOT 与验收契约执行必然失败（契约漂移）**:
  - **触发条件**: 验收人/下一轮编排者按 docs/project/plans/2026-10-08-subagent-direct-write.md:54 的验收场景 5 执行 prepare-review-context.sh --slug=<slug> --round=r1。
  - **复现推演**: 实测 A1 该命令 rc=1（修复前 rc=0 并打印路径）。同一无基线形式还出现在 SKILL.md:118 与 docs/explanation/architecture/dual-round-review-design.md:78；RFC-0002:107 仍写「预授权五条」，而实现载体 SKILL.md:123 已写「六条」，且 RFC 全文无「路径必须是基线的确定函数」条款。
  - **影响结果**: 交付无法按自身声明的验收场景验收（rc=1 与「能直接打印」相反）；RFC 作为契约 SSOT 缺失本次修复所依赖的核心不变式，后续实现者可能重新引入自适应漂移。
  - **涉及代码**: docs/project/plans/2026-10-08-subagent-direct-write.md:54；skills/dual-round-review/SKILL.md:118；docs/explanation/architecture/dual-round-review-design.md:78；docs/proposals/RFC-0002-subagent-direct-write.md:107

- **攻击路径 2: 单参数形式的 HEAD 漂移 → 孤儿报告仍不可枚举**:
  - **触发条件**: 以 --round=<轮次> <BASE_SHA>（HEAD 省略）调用，且在两次调用之间存在提交（例如编排者在派发间隙提交 scaffold 出的归档索引）。
  - **复现推演**: 实测 call1 = r1-2606378..255127e.md，HEAD 前进后 call2 = r1-2606378..e9ad591.md；因新路径不存在，**Write-Once 告警不触发**；门禁仅遍历台账行（check-review-report.sh:155-197，代码核验），未登记报告文件不可见。
  - **影响结果**: 同轮同基线可并存两份报告，门禁只看得见已登记那份；孤儿文件长期残留且零信号。
  - **涉及代码**: skills/dual-round-review/scripts/prepare-review-context.sh:134-137、347-354；skills/dual-round-review/scripts/check-review-report.sh:155-197

- **攻击路径 3: 反转末列定位可全绿通过全部 89 项测试**:
  - **触发条件**: 任何后续改动把 check-review-report.sh:144 的 (NF>=9) ? $(NF-1) : $8 写错（反转、或写成 $8 但保留 NF>=9 字样）。
  - **复现推演**: 变异 M5 反转后 89/89 全绿；同一变异下门禁对「结论含裸竖线 + 尾随竖线」的合法行实测 rc=1，正确实现 rc=0。根因：test_write_channel_contract.py:184 断言的是子串 'NF>=9' 是否存在，属纯文本存在性断言。
  - **影响结果**: R1-12 修复的语义契约无任何行为保真度，契约漂移不被测试发现（与 R1-11 对门禁第 8 项的批评同型，且该弱断言由本次 diff 新增）。
  - **涉及代码**: skills/dual-round-review/tests/test_write_channel_contract.py:184；skills/dual-round-review/scripts/check-review-report.sh:144

- **攻击路径 4: 无尾随竖线 + 结论含裸竖线 → 合法台账被误拦**:
  - **触发条件**: 台账行不以竖线结尾，且结论单元格含未转义竖线（如 🔴 2 | 🟡 10），行内第 7 值仍为 direct。
  - **复现推演**: 实测该行 rc=1「写入形态取值非法: 登记 🟡 10」；同内容补一个尾随竖线即 rc=0。因 NF>=9 判定为真时取的是 $(NF-1)，而在无尾随竖线的行上该字段落回结论碎片。
  - **影响结果**: fail-closed 误拒（不致命，可改行），且该输入本身已是非法 Markdown 表格（裸竖线破坏整表渲染）。
  - **涉及代码**: skills/dual-round-review/scripts/check-review-report.sh:144

- **攻击路径 5: 作废轮次在版本库中零留痕**:
  - **触发条件**: 按 SKILL.md:135 异常分支 7 处置不合格报告（移出归档目录至 .review-context/、不登记台账、同基线重派）。
  - **复现推演**: .review-context/ 被 .gitignore:8 忽略且 git ls-files 计数为 0；本交付真实存在 .review-context/r1-superseded-format-error-771ad29..455eccc.md（即被作废的首版 R1 报告），clone 后不可见。
  - **影响结果**: 「作废该轮」这一治理事件零留痕，与 SKILL.md:122 新增的「降级原因须写入版本库载体」取向相反；审计者只能看到最终登记的那份报告。
  - **涉及代码**: skills/dual-round-review/SKILL.md:135；skills/dual-round-review/SKILL.md:122；.gitignore:8

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | **原 P1 → 本轮核验：已根治** | 是（本次修复） | skills/dual-round-review/scripts/prepare-review-context.sh:139-147、:94、:84 | 原缺陷「--round 路径随工作区脏净漂移」已由确定性守卫消除；显式基线下两次调用同路径，Write-Once 告警可触发 | 残余 DR-3 仅剩单参数形式的 HEAD 漂移，需真实提交发生 |
| R1-2 | **原 P1 → 本轮核验：已根治** | 是（本次修复） | skills/dual-round-review/scripts/prepare-review-context.sh:328-329 | 原缺陷「scaffold 表头 6 列与 7 列 schema 自相矛盾」已修复；新 scaffold + 合法 7 值行可直接过门禁 rc=0 | 无（变异 M2 可被测试捕获） |
| DR-1 | **P2**（不构成阻断，但建议放行前修正） | 是（修复引入的契约漂移） | docs/project/plans/2026-10-08-subagent-direct-write.md:54；skills/dual-round-review/SKILL.md:118；docs/explanation/architecture/dual-round-review-design.md:78；docs/proposals/RFC-0002-subagent-direct-write.md:107 | 四处载体仍记载「无基线的 --round 调用」或「预授权五条」：验收场景 5 已被本次补丁证伪（rc=1），SKILL.md 已扩为六条而 RFC 未同步 | 编排者按验收契约执行必失败（rc=1，报错自解释故破坏有限）；RFC 缺失确定性不变式，后续实现者可能重新引入漂移 |
| DR-2 | P3 | 是（本次新增测试的保真度） | skills/dual-round-review/tests/test_write_channel_contract.py:184；skills/dual-round-review/scripts/check-review-report.sh:144 | R1-12 的「回归断言」是纯文本存在性断言；反转末列三元后 89/89 全绿，而门禁对合法行实际误判 rc=1 | 契约漂移、死代码与语义反转都不会被测试发现（与 R1-11 批评同型，且该弱断言由本次新增） |
| DR-3 | P3 | 否（R1-1 残余，未被本次修复消除） | skills/dual-round-review/scripts/prepare-review-context.sh:134-137、:347-354；skills/dual-round-review/scripts/check-review-report.sh:155-197 | 单参数形式以符号 HEAD 参与命名，HEAD 漂移即路径漂移且 Write-Once 静默；门禁不枚举未登记报告文件 | 同轮可并存两份报告，孤儿文件门禁不可见、无任何信号 |
| DR-4 | P3 | **历史既有**（修复未消除，非本次引入） | skills/dual-round-review/scripts/check-review-report.sh:144 | 无尾随竖线且结论含裸竖线时，NF>=9 判定取 $(NF-1) 落在结论碎片上，合法行被 fail-closed 误拒 | 误判「写入形态非法」（不致命、可改行；修复前 m=$8 行为完全相同，故非本次引入） |
| DR-5 | P3 | 是（本次新增分支 7 的取向） | skills/dual-round-review/SKILL.md:135；.gitignore:8 | 作废轮次仅移入已 gitignore 的 .review-context/ 留痕，版本库零记录 | 治理事件对 clone 者不可见，与 SKILL.md:122 新增的「原因须进版本库载体」取向相反 |
| DR-6 | P3（如实登记，非本轮缺陷） | 否（历史既有） | skills/dual-round-review/scripts/prepare-review-context.sh:171、:203 | --working/--staged 模式下路径 base7 位为 working/staged 字面量，与 SKILL.md:118 的 <base7>..<head7> 命名模板字面不符 | 仅命名口径差异，不影响 Write-Once 与门禁；RFC-0001 既有行为，本轮不改判 |
| R1-5 | ⚪ 未采纳（R2 驳回） | 否（历史既有） | skills/dual-round-review/scripts/prepare-review-context.sh:95 | --archive-root 无包含性校验 | 按 R2 裁定驳回，本轮**不计入**阻断或缺陷统计 |

## 5. 第一轮结论概要

- **Previous Blockers 核验结果：R1-1 与 R1-2 均已根治，阻断项清零。** R1-1：确定性守卫使无基线调用 rc=1，显式基线下脏树不再改变路径（A2/A3），Write-Once 告警真实触发（A4），重派分支与回归断言均落地，变异 M1 被唯一用例捕获并反证变异有效。R1-2：表头与分隔行列数自洽（7/7），新 scaffold 归档配合法 7 值台账可直接过门禁 rc=0 且无需手工补列，变异 M2 被捕获。两条阻断项**未呈现镜像残余**（合法形态的行登记由编排者手工完成属既有设计，非本缺陷残余）。
- **本轮未发现新增 P0/P1 阻断项。** 新增 1 项 P2（DR-1：契约漂移——验收场景 5 被自身补丁证伪、RFC 五条未同步为六条）与 4 项 P3（DR-2 弱断言、DR-3 R1-1 残余、DR-5 作废留痕、DR-6 命名口径）；DR-4 为**历史既有**（限 P3）。DR-1 我已定为 P2 而非阻断：机制层无功能失效、报错自解释，但它是**唯一会导致「按文档验收必然失败」**的项，若 R2 采「验收契约不得被自身补丁证伪」的严格口径，可升级为阻断——请 R2 明确裁定，我不回避该判断。
- **对抗性审查应逐项承认的事实**（不构成放行依据）：L1=89 passed / L2=226 collected / 全仓 493 passed，两处真实归档门禁 rc=0；R1-3 的「门禁不解析表头」经实测证伪性检验为**属实**（删表头单元格仍 rc=0，删取值即 rc=1）；R1-4/R1-7/R1-8/R1-9/R1-10/R1-11 的修复均已在代码或文档中落地并经变异或直读核验，未见「声称已修而未落地」；R1-5 未采纳属正确自律。
- **明确移交第二轮**：① 裁定 DR-1 是否升级为阻断（我建议 P2 + 放行前同轮修正四处载体，其中 plan:54 为验收契约、RFC-0002:107 为 SSOT）；② 裁定 DR-3 的残余是否需要在门禁侧补「未登记报告文件枚举」（约 3 行即可让整类孤儿问题机械可见，属可选强化，非 R2 原处置要求）；③ DR-2 应记入待办并在下一轮改为行为断言；④ 沿用 R2 结论——**不得**把门禁第 8 项读作「写入形态已可机械验证」，本报告未获得任何该方向的机械证据，也不主张存在；⑤ DR-4/DR-6 按边界锁限 P3 且标注历史既有，不得重新升级为阻断项。
