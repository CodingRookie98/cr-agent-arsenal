---
id: BK-0039
title: 存量技能交付面债务：agy/clarification 缺测试与 README 登记
type: TechDebt
status: completed
priority: P3
trigger: 下一轮 spec-evolution 扫描或专门的存量修复任务
created_at: '2026-10-12'
updated_at: '2026-10-13'
closed_at: '2026-10-13'
resolution: delivered
destination: 技能交付面补齐：agy 与 clarification-protocol 补 tests/、clarification 交付面与设计书入册、doc-governance
  与 dual-round-review 补 templates/，C-01/C-02/C-03 转绿；提交 8facf12/cdedd38
source:
- dual-round-review Delta R1 R1-15（spec-evolution-v1，历史既有技术债）
- RFC-0004 §1.1 F-1~F-9（本次交付明确不含修复，仅例外 F-9）
- spec-evolution judge 2026-10-13 复跑：F-01（agy 无 tests/）、F-02（clarification-protocol
  无 tests/）实测仍在；同批 F-03 见 README §1 技能表
acceptance_criteria:
- agy-delegation-workflow 与 clarification-protocol 具备 tests/；clarification-protocol
  补入 README 技能表；dual-round-review 补 templates/；doc-governance 补 templates/；judge.py
  对全仓复跑后 HIGH+BLOCKER 归零（对应 judge F-01/F-02/F-03/F-05/F-06）
---

## 1. 背景与问题陈述
真仓实跑 11 findings / 3 HIGH：agy-delegation-workflow 与 clarification-protocol 的 C-01 无 tests、clarification-protocol 的 C-07 README 缺登记（改动前即存在）。另有 MID：clarification-protocol 缺架构设计书与交付面目录（C-02/C-03）、dual-round-review 缺 templates/（C-03，本次新发现）、doc-governance 缺 templates/（F-7）、dual-round-review 的 description 738 字符与 clarification-protocol 623 字符（C-04）。按『检测与修复分离』裁定不随本次交付。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [x] agy-delegation-workflow 与 clarification-protocol 具备 tests/；clarification-protocol 补入 README 技能表；dual-round-review 补 templates/；doc-governance 补 templates/；judge.py 对全仓复跑后 HIGH+BLOCKER 归零（对应 judge F-01/F-02/F-03/F-05/F-06）

## 4. 实施去向与结项记录
*（建卡模板占位语；任务已于 2026-10-13 实施并结项，见下。占位未被 `close` 收敛属工具缺陷，已登记 BK-0042。）*

2026-10-13 复核：judge 复跑仍报 11 findings / 3 HIGH，其中 **F-01**（`agy-delegation-workflow` 无 `tests/`）与 **F-02**（`clarification-protocol` 无 `tests/`）为本卡首批交付项；同日已修复同批 F-03（根 README §1 技能表补 `clarification-protocol`）。

### 结项记录 (2026-10-13)
- **结论**: delivered
- **去向/凭据**: 技能交付面补齐：agy 与 clarification-protocol 补 tests/、clarification 交付面与设计书入册、doc-governance 与 dual-round-review 补 templates/，C-01/C-02/C-03 转绿；提交 8facf12/cdedd38
- **归档目录**: archive/2026-Q4/

## 5. 更正记录 (Errata)（2026-10-13，结项后追加）

本卡及其关联提交的对外宣称经独立红队复核（reviewer V8，subagentId `019e463d-cb16-41b0-8316-dd5eb367fb37`）后，按「宣称与取证同宽」原则显式更正。已推送的提交信息不可改写（仓库红线：禁止重写已推送历史），更正以本条记录为准。

- **E-1 提交信息测量时点错位**：提交 `8facf12` 信息中的「judge 复跑：两技能 C-01 消失，clarification-protocol 仅余 C-04 MID 建议项」与同批末态 `cdedd38` / `f037116` 的实测（4 MID / 0 HIGH）一致，但在 `8facf12` 自身树上不成立——clarification-protocol 的设计书由紧随的 `cdedd38` 才新增。复现：`git archive 8facf12 | tar -x -C /tmp/c8` 后运行 `collect-facts.py --no-gates` + `judge.py` → **findings=7 / 0 HIGH**，其中含 clarification-protocol 的 C-02「设计书文件不存在」；末态 `cdedd38` / `f037116` 实测 4 条 MID。
- **E-2 交付面基线数字的测量时点**：本卡 §1 与 §4 所载「11 findings / 3 HIGH」（含 §4 复核段）为 **`c13b1e2` 修复 C-07 之前**的测量值。复核实测：`3abacf7` = **10 findings / 2 HIGH**（C-07 已消除），末态 `f037116` = **4 findings / 0 HIGH / 0 BLOCKER**。
- **E-3 destination 范围限定**：frontmatter `destination` 与本卡 §4 结项记录中的「C-01/C-02/C-03 转绿」，其 **C-02 仅指 `clarification-protocol` 设计书入册**；`agy-delegation-workflow` 的 C-02（设计书缺失）当时未修复，已按「检测与修复分离」移交 BK-0041。
- **E-4 模板占位残留**：§3 DoD 复选框与 §4「*(未开工)*」占位语在结项时未被 `manage-backlog.py close` 收敛（见 `skills/doc-governance/scripts/manage-backlog.py:329` 与 `:340-394`）。本次按实况补勾并替换占位；工具缺陷登记为 BK-0042。
- **E-5 工作区副作用不可由提交复核**：提交 `3b12d1e` 信息中的「设计书权限 0600→0644」属工作区操作——git index mode 仅表达 `100644` / `100755`，该差异既不在该提交 diff 内，也无法由任何提交取证（当前磁盘态为 644，可直接验证）。此类工作区副作用今后不进入提交信息的完成度宣称。

以上 E-1~E-5 经独立复核 V9（subagentId `e0210a3d-178d-4b72-ada2-c8035d6b0569`）逐项复现：`8facf12` = 7 findings / 0 HIGH（含 clarification-protocol C-02）、`cdedd38` 与 `f037116` = 4 MID、`3abacf7` = 10 / 2 HIGH、`6eacc31` = 11 / 3 HIGH；全部列名 SHA 均为 `3b12d1e` 祖先，已推送历史未被改写。

