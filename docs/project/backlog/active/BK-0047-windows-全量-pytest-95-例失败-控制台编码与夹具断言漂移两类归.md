---
id: BK-0047
title: Windows 全量 pytest 95 例失败：控制台编码与夹具断言漂移两类归因
type: Bug
status: active
priority: P2
trigger: 在 Windows 原生环境（cp936 终端）运行 spec-evolution 采集器带门禁模式，或全量 pytest 时
created_at: 2026-11-15
updated_at: 2026-11-15
closed_at: null
resolution: null
destination: null
source:
  - 2026-11-15 会话：C-09 假 BLOCKER 排查与解释器修复（提交 6b99b30）
  - docs/project/reviews/2026-10-19-skill-scripts-python-unification.md：既有 Windows 失败集为基线的记录
acceptance_criteria:
  - 批次 A：skills/ 下无脚本把裸 emoji 直接 print 到 stdout（或统一改为 UTF-8 输出重配置），相关用例在 cp936 终端下转绿
  - 批次 B：test_judge_contract 的 C-10 基线与 INCOMPLETE 渲染断言与实现对齐，且不依赖同尺寸同 mtime 之类的脆弱性质
  - Windows .venv 下全量 pytest 为 0 failed，且采集器带门禁跑出 blocker/high = 0（C-09 不再红）
  - WSL 主线保持 0 failed，不回退既有通过数基线
---

## 1. 背景与问题陈述
2026-11-15 实测（Windows 11 / Python 3.14 / .venv）：pytest skills/ 结果为 95 failed / 424 passed / 16 skipped。该失败集在 C-09 解释器修复（6b99b30）之前即存在，已用 git archive HEAD~1 在纯净副本复现，非该次改动引入。

同日已修复其中一条假 BLOCKER：门禁解释器写死 python3，而宿主 python3 无 pytest，导致 cross_skill_links 与 pytest 两道门禁误红；现改为继承 sys.executable（SPEC_EVOLUTION_PYTHON 可覆盖）。本卡登记修复后仍然存在的真实门禁红。

抽样归因分两类。两者根因不同、修法不同，混在一个提交里会让 diff 不可审，且重犯 BK-0046「同一张卡永不可结项」的毛病，故按批次推进：

批次 A · 控制台编码类
- skills/doc-governance/scripts/manage-backlog.py:353 把 U+2705（对勾符号）直接 print 到 cp936 终端，抛 UnicodeEncodeError，被测试读成「create 失败」（test_manage_backlog_close_contract.py 多条命中）
- 同族问题：其它脚本与测试里的 emoji、富符号直接 print

批次 B · 夹具与断言漂移类
- test_judge_contract.py::test_clean_repo_yields_no_findings：合成仓库上产出 C-10 MID，baseline.json 口径与夹具不一致
- test_judge_contract.py::test_no_findings_still_renders_verdict_header：期望「判定结论 INCOMPLETE」，实际渲染 MID 且附带 BLOCKER 小节

取证口径：两批的用例清单须在动手前用 pytest --tb=no 全量采集并写回本卡，不以抽样代替全量。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 批次 A：skills/ 下无脚本把裸 emoji 直接 print 到 stdout（或统一改为 UTF-8 输出重配置），相关用例在 cp936 终端下转绿
- [ ] 批次 B：test_judge_contract 的 C-10 基线与 INCOMPLETE 渲染断言与实现对齐，且不依赖同尺寸同 mtime 之类的脆弱性质
- [ ] Windows .venv 下全量 pytest 为 0 failed，且采集器带门禁跑出 blocker/high = 0（C-09 不再红）
- [ ] WSL 主线保持 0 failed，不回退既有通过数基线

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
