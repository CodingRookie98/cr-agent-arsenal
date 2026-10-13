---
id: BK-0042
title: manage-backlog.py close 未收敛卡片 §3 DoD 勾选与 §4「(未开工)」占位
type: TechDebt
status: completed
priority: P3
trigger: doc-governance 脚本维护窗口；无前置依赖，随时可做
created_at: '2026-10-13'
updated_at: '2026-10-13'
closed_at: '2026-10-13'
resolution: delivered
destination: close/create/reopen 收口一致性：close 机械收敛 *(未开工)* 占位语并按项数提示未勾选 DoD、reopen
  写明历史留痕口径、create 声明人工勾选职责；新增 8 用例契约测试；提交 afdb4e5
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
- [x] close 归档时替换或移除 §4 的「*(未开工)*」建卡占位语，归档卡不再同时出现占位与结项记录
- [x] §3 DoD 复选框提供结项收敛路径（自动勾选，或显式声明为作者手工职责并在建卡模板中写明）
- [x] 在 skills/doc-governance/tests/ 增加回归测试覆盖上述行为，pytest skills/doc-governance -q 全绿

## 4. 实施去向与结项记录

### 结项记录 (2026-10-13)
- **结论**: delivered
- **去向/凭据**: close/create/reopen 收口一致性：close 机械收敛 *(未开工)* 占位语并按项数提示未勾选 DoD、reopen 写明历史留痕口径、create 声明人工勾选职责；新增 8 用例契约测试；提交 afdb4e5
- **归档目录**: archive/2026-Q4/
## 5. 更正记录 (Errata)

- **E-1 scaffold 同步宣称不成立（独立复核 V10 阻断项 B1）**：提交 `afdb4e5` 与 `docs/index.md` V1.36.3 修订行均称「`scaffold-doc.sh` 与 `references/backlog-specification.md` 同步写入 DoD 人工核验职责说明」。实测该脚本 `:390` 为未加引号的 heredoc，`:420` 行的反引号被 shell 当作命令替换执行：生成卡丢失 `close` 词元并输出 `scaffold-doc.sh: line 390: close: command not found`（退出码仍为 0，属静默失真）。修复：转义反引号（不可改为 `<<'EOF'`，该 heredoc 依赖 `${NAME}`/`${TODAY}`/`${SEQ_PADDED}` 变量插值），并补回归用例断言 scaffold 骨架与 create 模板的职责说明逐字一致（提交 `8390df8`）。
- **E-2 提示项数统计口径（独立复核 V10 非阻断项 N1）**：`afdb4e5` 的实现按全正文统计 `- [ ]`，而提示文案写「§3 DoD 仍有 N 项未勾选」，两者不符。现改为按 §3 小节统计（`DOD_SECTION_PATTERN` + `count_unchecked_dod()`，卡片无 §3 小节时返回 0），`references/backlog-specification.md` 注明统计范围，并补用例覆盖「§3 之外的复选框不计入」（提交 `8390df8`）。
- **E-3 历史归档卡占位语残余（独立复核 V10 非阻断项 N3）**：`BK-0021`/`BK-0023`/`BK-0025`/`BK-0026`/`BK-0027`/`BK-0030`/`BK-0031` 七张归档卡仍同时存在 `*(未开工)*` 与 `### 结项记录`（均为修复前 `close` 的产物；`BK-0001`/`BK-0002` 无占位语）。决定不追溯改写历史归档卡（保留既有记录原貌），本卡验收准则「归档卡不再同时出现占位与结项记录」按「对后续 `close` 生效」解读。
- **E-4 提交信息凭据数字失真（独立复核 V11 阻断项 B1）**：提交 `8390df8` 的「取证」行称 `pytest skills/doc-governance -q = 132 passed`，该提交自身树实测为 **134 passed / 134 collected**（`132` 系其父提交 `ecf5d24` 的数值，可由技能总数 `448 → 450` 相互印证：本批新增 2 个用例）。属凭据数字与实测不同宽（非功能缺陷）；提交已推送，遵循「禁止改写已推送历史」保留原文，以本条更正。复现：`python3 -m pytest skills/doc-governance -q` → `134 passed`（用时为本机一次测量：本会话 9.61 s、独立复核 9.99 s / 9.96 s，**非可复现常数**；代码面自 `8390df8` 起未变）。
- **E-5 两处口径澄清（独立复核 V11/V12 非阻断项）**：①「trim 5 行」指修订表滑窗上限 5 行（实测该次为 1 行置换、行数恒 5，非裁剪 5 行）；②「`docs/llms.txt` 重生成（80 篇）」的产物与库内文件逐字节相同（幂等、无 diff），「重生成」不等于「内容有变更」。两处表述均出自提交 `c24f27c` 的提交信息，**不在** `8390df8` 内（后者仅改 `skills/` 下 4 个文件；独立复核 V12 指出初稿归因错误，此为本条更正）。
