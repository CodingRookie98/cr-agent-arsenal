---
id: BK-0039
title: 存量技能交付面债务：agy/clarification 缺测试与 README 登记
type: TechDebt
status: active
priority: P3
trigger: 下一轮 spec-evolution 扫描或专门的存量修复任务
created_at: '2026-10-12'
updated_at: '2026-10-13'
closed_at: null
resolution: null
destination: null
source:
- dual-round-review Delta R1 R1-15（spec-evolution-v1，历史既有技术债）
- RFC-0004 §1.1 F-1~F-9（本次交付明确不含修复，仅例外 F-9）
- spec-evolution judge 2026-10-13 复跑：F-01（agy 无 tests/）、F-02（clarification-protocol 无 tests/）实测仍在；同批 F-03 见 README §1 技能表
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
- [ ] agy-delegation-workflow 与 clarification-protocol 具备 tests/；clarification-protocol 补入 README 技能表；dual-round-review 补 templates/；doc-governance 补 templates/；judge.py 对全仓复跑后 HIGH+BLOCKER 归零（对应 judge F-01/F-02/F-03/F-05/F-06）

## 4. 实施去向与结项记录
*(未开工)*

2026-10-13 复核：judge 复跑仍报 11 findings / 3 HIGH，其中 **F-01**（`agy-delegation-workflow` 无 `tests/`）与 **F-02**（`clarification-protocol` 无 `tests/`）为本卡首批交付项；同日已修复同批 F-03（根 README §1 技能表补 `clarification-protocol`）。
