---
id: BK-0042
title: manage-backlog.py close 未收敛卡片 §3 DoD 勾选与 §4「(未开工)」占位
type: TechDebt
status: active
priority: P3
trigger: doc-governance 脚本维护窗口；无前置依赖，随时可做
created_at: '2026-10-13'
updated_at: '2026-10-13'
closed_at: null
resolution: null
destination: null
source:
- 独立复核 V8 非阻断建议③（2026-10-13，reviewer subagentId 019e463d-cb16-41b0-8316-dd5eb367fb37）
- BK-0039 归档卡为直接证据：结项记录与 *(未开工)* 占位共存于同一归档卡
acceptance_criteria:
- close 归档时替换或移除 §4 的「*(未开工)*」建卡占位语，归档卡不再同时出现占位与结项记录
- §3 DoD 复选框提供结项收敛路径（自动勾选，或显式声明为作者手工职责并在建卡模板中写明）
- 在 skills/doc-governance/tests/ 增加回归测试覆盖上述行为，pytest skills/doc-governance -q 全绿
---

## 1. 背景与问题陈述
`manage-backlog.py create` 在 skills/doc-governance/scripts/manage-backlog.py:329 写入 `*(未开工)*` 占位语，:323-327 写入未勾选的 §3 DoD 复选框（含 :327 else 缺省分支）；`cmd_close`（:340-394）只追加「### 结项记录」，既不替换占位语也不收敛复选框。实测证据：BK-0039 归档卡同一 §4 内同时存在 `*(未开工)*` 与结项记录，§3 DoD 在验收准则全部达成后仍为未勾选。属工具缺陷而非作者疏漏：结项动作缺少对卡片自身状态的收口一致性保证。

## 2. 影响面与技术考量
- 涉及模块: skills/doc-governance/scripts/manage-backlog.py（cmd_create 占位写入、cmd_close 归档收口），skills/doc-governance/tests/
- 风险点: 若 close 自动勾选 DoD，等于把「验收准则是否达成」这一人工判断写成机器结论（与「检测与修复分离」冲突）。收敛策略须二选一并显式登记：(a) 仅收敛占位语，DoD 勾选声明为作者手工职责；(b) close 增加显式参数（如 `--dod-done`）后才勾选。

## 3. 验收准则与验证设计 (DoD)
- [ ] close 归档时替换或移除 §4 的「*(未开工)*」建卡占位语，归档卡不再同时出现占位与结项记录
- [ ] §3 DoD 复选框提供结项收敛路径（自动勾选，或显式声明为作者手工职责并在建卡模板中写明）
- [ ] 在 skills/doc-governance/tests/ 增加回归测试覆盖上述行为，pytest skills/doc-governance -q 全绿

## 4. 实施去向与结项记录
*(未开工)*
