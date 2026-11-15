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

### 全量取证（先采集，后动手）

| 运行条件 | 结果 | 结论 |
| :--- | :--- | :--- |
| cp936 终端（无 UTF-8 环境变量） | 94 failed / 426 passed | 基线现场 |
| 强制 UTF-8 环境（PYTHONIOENCODING / PYTHONUTF8） | 12 failed / 490 passed | 差值 82 条即编码类 |
| 批次 A 修复后（仍无 UTF-8 环境变量） | **12 failed / 490 passed** | 与 UTF-8 环境完全一致，A 类清零 |

可识别的 A 类用例 64 条，按文件分布：test_doc_governance_scripts 24 / test_doc_index_convention 20 / test_llms_txt_hardening 11 / test_manage_backlog_close_contract 9；剩余差值来自子测试与未逐条枚举的多行用例，两种条件下通过数完全相等，据此判定编码类已无残留。

### 归因分三类

**批次 A · 控制台编码（已闭环）**

- 写侧：门禁脚本入口未固化输出编码。Windows 控制台与管道缺省 cp936，脚本把 emoji 与富符号直接 print，抛 UnicodeEncodeError，被测试读成「create 失败」。
- 读侧：测试侧 subprocess.run(text=True) 未指定 encoding，按 locale 解码 UTF-8 输出，解码异常吞掉结果（res.stderr 变 None，报成 NoneType 不可迭代）。
- 结论：根因不是「某一处 print 的 bug」，而是**输出契约缺失**。修法取仓库既有 5 个脚本的同源写法——脚本入口 sys.stdout / sys.stderr.reconfigure(encoding="utf-8", newline="\\n")，消费者按 UTF-8 解码；写侧与读侧必须同批改。
- 已改脚本（7 个 CLI 入口）：manage-backlog / audit-doc-health / check-doc-links / check-doc-control-sync / generate-llms-txt / trim-revision / manage-doc-index。
- 已改测试侧解码（4 个文件）：test_doc_governance_scripts / test_doc_index_convention / test_llms_txt_hardening / test_manage_backlog_close_contract 的 subprocess 调用一律 encoding="utf-8"。

**批次 B · 平台差异（POSIX 专属用例缺跳过守卫）**

- TestBatchDIdentityContract 的 4 条（test_audit_refuses_non_regular_map / test_generation_failure_leaves_no_partial_map / test_non_regular_file_output_is_refused / test_unencodable_byte_name_is_refused）依赖 os.mkfifo（test_doc_governance_scripts.py:1451、:1545）与非法字节文件名；Windows 无此原语且无 skipif 守卫。

**批次 C · 夹具与断言漂移**
- test_judge_contract.py::test_clean_repo_yields_no_findings：合成仓库上产出 C-10 MID，baseline.json 口径与夹具不一致；另有 INCOMPLETE / CLEAN / finding 顺序三处渲染断言与实现不符。
- test_gate_invariants.py::test_gi4_rendered_verdict_rows_are_empty（实测 3 行 vs 期望 2 行）、test_gi6_pycache_prefix_is_per_run_and_private（实测 0o777 vs 期望 0o700，Windows 无 POSIX 权限位）。
- test_doc_governance_scripts.py::test_create_and_sync_index：创建的卡片 source 解析为空串而非列表，需查 dump / parse 往返。

取证口径：每一批的用例清单须先全量采集并写回本卡，不以抽样代替全量；批次 A 的收敛判据是「无 UTF-8 环境变量下的通过数等于有 UTF-8 环境变量时的通过数」。

## 2. 影响面与技术考量
- 涉及模块: skills/doc-governance/scripts/（7 个 CLI 入口）+ skills/doc-governance/tests/（4 个测试文件的 subprocess 调用面）+ skills/spec-evolution/tests/（批次 C）
- 风险点: 输出改 UTF-8 后，仍按 locale 解码的消费者会从「解码异常」变成「乱码断言失败」——写侧与读侧必须同批改；POSIX 专属用例加跳过守卫须写明理由，不得笼统 skip

## 3. 验收准则与验证设计 (DoD)
- [x] 批次 A：skills/ 下无脚本把裸 emoji 直接 print 到 stdout（或统一改为 UTF-8 输出重配置），相关用例在 cp936 终端下转绿
- [ ] 批次 B：test_judge_contract 的 C-10 基线与 INCOMPLETE 渲染断言与实现对齐，且不依赖同尺寸同 mtime 之类的脆弱性质
- [ ] Windows .venv 下全量 pytest 为 0 failed，且采集器带门禁跑出 blocker/high = 0（C-09 不再红）
- [ ] WSL 主线保持 0 failed，不回退既有通过数基线

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
