---
id: BK-0046
title: spec-evolution 门禁 pytest 超时阈值（GATE_TIMEOUT=300s）与实际套件时长临界导致 C-09 假 BLOCKER
type: Bug
status: active
priority: P2
trigger: 执行 spec-evolution 的 collect-facts.py 采集全量门禁时（尤其在 /mnt/d 9p 文件系统、PYTHONPYCACHEPREFIX
  冷导入或机器负载较高时），pytest 门禁超时记为 exit 124，judge.py 的 C-09 随即判 F-01 BLOCKER
created_at: '2026-10-20'
updated_at: '2026-10-20'
closed_at: null
resolution: null
destination: null
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
- [ ] spec-evolution 门禁不再因套件时长抖动误报 C-09 BLOCKER：TIMEOUT 与真实门禁失败可区分（或以可配置/自适应阈值消除临界）；collect-facts.py 门禁与 judge.py 对超时语义的判定同步更新，并有回归测试覆盖（模拟超时场景不误判为交付基线不成立）
- [ ] WSL 直跑全量 pytest（503 用例、约 204~300s）时 collect-facts.py 全量门禁 exit 0、judge.py findings 无 BLOCKER/HIGH
- [ ] SKILL.md / checks-spec.md（C-09 语义）/ 架构设计书 三处超时与退出码说明同步更新，文档门禁全绿

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
