---
id: BK-0033
title: 门禁子进程非 UTF-8 输出导致裸 traceback
type: TechDebt
status: active
priority: P2
trigger: 采集器在 LC_ALL=C / PYTHONUTF8=0 或非 UTF-8 门禁输出的环境下运行
created_at: '2026-10-12'
updated_at: '2026-10-12'
closed_at: null
resolution: null
destination: null
source:
- dual-round-review Delta R1 R1-4（spec-evolution-v1，R2 复现成立 P2）
acceptance_criteria:
- collect-facts.py 两处 subprocess.run 加 encoding=utf-8/errors=replace；judge.py 与 collect-facts.py
  的 print 输出对非 UTF-8 环境不再抛 UnicodeEncodeError；异常路径退出码仍为 2 而非 1
---

## 1. 背景与问题陈述
门禁子进程输出非 UTF-8 时 subprocess.run(text=True) 抛未捕获 UnicodeDecodeError，退出码 1（契约应为 2）；LC_ALL=C PYTHONUTF8=0 下 print 富符号抛 UnicodeEncodeError。与 G1 零依赖 fail-closed 取向不符。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] collect-facts.py 两处 subprocess.run 加 encoding=utf-8/errors=replace；judge.py 与 collect-facts.py 的 print 输出对非 UTF-8 环境不再抛 UnicodeEncodeError；异常路径退出码仍为 2 而非 1

## 4. 实施去向与结项记录
*(未开工)*
