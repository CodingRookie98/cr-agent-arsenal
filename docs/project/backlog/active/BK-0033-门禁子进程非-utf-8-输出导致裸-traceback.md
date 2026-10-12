---
id: BK-0033
title: 门禁输出非 UTF-8 环境下的 print 硬化与异常退出码收敛
type: TechDebt
status: active
priority: P2
trigger: 采集器或判定器在 LC_ALL=C / PYTHONUTF8=0 等非 UTF-8 环境下运行
created_at: '2026-10-12'
updated_at: '2026-10-12'
closed_at: null
resolution: null
destination: null
source:
- dual-round-review Delta R1 R1-4（spec-evolution-v1，R2 复现成立 P2）
acceptance_criteria:
- judge.py 与 collect-facts.py 的 print 输出在 LC_ALL=C / PYTHONUTF8=0 下不再抛 UnicodeEncodeError（ASCII 前缀或对 stdout 设 errors=replace）
- 上述编码异常路径的退出码为 2（用法/输入错误）而非 1
---

## 1. 背景与问题陈述
门禁子进程输出非 UTF-8 时 `subprocess.run(text=True)` 抛未捕获 `UnicodeDecodeError`，退出码 1（契约应为 2）；`LC_ALL=C PYTHONUTF8=0` 下 `print` 富符号抛 `UnicodeEncodeError`。与 G1 零依赖 fail-closed 取向不符（Delta R1 R1-4）。

## 2. 影响面与技术考量
- 涉及模块: `skills/spec-evolution/scripts/collect-facts.py`（print 边界）、`skills/spec-evolution/scripts/judge.py`（print 边界）
- 风险点: 真实风险有限（本仓文档全 UTF-8、技能不接 CI），但裸 traceback 与 fail-closed 取向不符

## 3. 验收准则与验证设计 (DoD)
- [ ] judge.py 与 collect-facts.py 的 print 输出在 LC_ALL=C / PYTHONUTF8=0 下不再抛 UnicodeEncodeError
- [ ] 上述编码异常路径的退出码为 2，而非 1

## 4. 实施去向与结项记录
**部分落地（2026-10-12，`d8aa611`）**：第一项验收准则的前半已实现 —— `collect-facts.py:268` 与 `:288` 两处 `subprocess.run` 已加 `encoding="utf-8", errors="replace"`，非 UTF-8 门禁输出不再触发裸 `UnicodeDecodeError`。**剩余**：两处 `print` 的 `UnicodeEncodeError` 硬化与异常退出码收敛仍未做，故卡片保持 `active`（Delta R1 DR1-4 指出原卡片文案未反映这一部分完成状态，本行为修正）。
