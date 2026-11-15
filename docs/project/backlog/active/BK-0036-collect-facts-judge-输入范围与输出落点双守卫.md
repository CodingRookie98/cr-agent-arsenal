---
id: BK-0036
title: collect-facts/judge 的输入范围与输出落点双守卫（未知技能名静默 CLEAN + 静默覆盖被跟踪文件）
type: Security
status: active
priority: P2
trigger: ① 调用 collect-facts.py --skills <拼错的技能名>；② 把 --out / --json / --report 指向仓库内已存在的被跟踪文件
created_at: '2026-10-12'
updated_at: '2026-11-15'
closed_at: null
resolution: null
destination: null
source:
- BK-0036 原卡（dual-round-review Delta R1 R1-10，spec-evolution-v1）
- BK-0037 原卡（dual-round-review Delta R1 R1-11，spec-evolution-v1）
acceptance_criteria:
- 输入范围守卫：collect-facts.py 的 --skills 含未知技能名时，stderr 列出未知名并 exit 2；合法名照旧
- 输出落点守卫：collect-facts.py / judge.py 拒绝写入被 git 跟踪的路径，显式 --force 才允许；拒绝时报错给出可复制的下一步
- 两条守卫各有反例用例与正例用例，断言以退出码为准，不依赖文本存在性
- 拒绝路径断言零副作用（不残留目录、不产生半成品文件），且 SKILL.md 用法段同步说明 --force
---

## 1. 背景与问题陈述

本卡由 BK-0036 与 BK-0037 合并而来（合并理由见 §2）。两条缺陷同属「采集器 / 判定器的入参与落点校验缺位」，共用同一个校验层，一次 diff 可审、一次回归可验。

**缺陷 A · 输入范围（原 BK-0036）**

`collect-facts.py --skills spec-evolutoin`（拼错）→ selected=[] → 「技能 0 个」、CLEAN、exit 0。2026-11-15 复验：`rc=0`，stdout 为「✅ 事实已导出（技能 0 个，门禁 已跳过）」。范围参数拼错即伪装成「零 findings」，与本技能「退出码即结论」的核心承诺直接冲突——这正是本技能存在的理由（RFC-0004：把判断换成退出码）。

**缺陷 B · 输出落点（原 BK-0037）**

judge.py 与 collect-facts.py 的输出路径仅校验 `parent.is_dir()`，随后 `mkdir(parents=True, exist_ok=True)` + `write_text`。2026-11-15 在 `git archive HEAD` 的干净副本中复验：`collect-facts.py --no-gates --out docs/index.md` → `rc=0`，且该被跟踪文件**确实被覆盖**。指向 `contexts/AGENTS.md`、`docs/index.md` 等任意被跟踪文件皆静默生效。触发需显式指定路径（SKILL.md 全部示例指向 /tmp），故不属自动落点风险，但一旦发生无可恢复，且与「项目自带门禁应 fail-closed」的取向相反。

## 2. 影响面与技术考量

- 涉及模块: skills/spec-evolution/scripts/collect-facts.py、skills/spec-evolution/scripts/judge.py、skills/spec-evolution/tests/、SKILL.md 用法段
- 风险点: 两道守卫都必须在写入前求值；若顺序错（先 mkdir 再校验）会残留空目录，故用例须断言「拒绝时零副作用」。`--force` 一旦引入即成为配置面，须在 SKILL.md 明示，且不得出现在任何默认路径或示例里
- 合并理由: 两卡同属入参 / 落点校验层。分开实现会出现「同一脚本两处各自校验、口径漂移」这一既有失败模式（同类事故见 BK-0044 §2 记录的双写入口漂移）

## 3. 验收准则与验证设计 (DoD)

- [x] 输入范围守卫：collect-facts.py 的 --skills 含未知技能名时，stderr 列出未知名并 exit 2；合法名照旧
- [x] 输出落点守卫：collect-facts.py / judge.py 拒绝写入被 git 跟踪的路径，显式 --force 才允许；拒绝时报错给出可复制的下一步
- [x] 两条守卫各有反例用例与正例用例，断言以退出码为准，不依赖文本存在性（tests/test_io_guards.py，8 条）
- [x] 拒绝路径断言零副作用（目标文件字节不变），且 SKILL.md 用法段同步说明 --force

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录

### 实施记录（2026-11-15）

**输入范围守卫**（`collect-facts.py`）：`--skills` 解析后立刻与 `discover_skills(repo)` 求差，未知名逐项列出并 exit 2，同时打印合法名单便于自查。实测：`--skills demo,no-such-skill` → rc=2；`--skills demo` → rc=0；省略 `--skills` → rc=0（不误伤全量）。

**输出落点守卫**（`collect-facts.py` + `judge.py`）：写入前查 `git ls-files --error-unmatch`，命中即拒绝并 exit 2，`--force` 放行。非 git 仓库 / git 不可用 / 目标在仓库外判为未跟踪（fail-open）——本守的职责是挡住「把产物写进源码树」。

**AC 的一处修订（须记录）**：原 AC 写「拒绝写入已存在文件**或** git 被跟踪路径」。实现改为**只拦被跟踪者**：`--out` 天然的用法就是反复覆盖同一路径（本仓库门禁、CI、调试均如此），拦「已存在但未跟踪」会让工具不可重跑，而那一类覆盖又完全可恢复。可恢复的覆盖不该与不可恢复的覆盖共用一条禁令。

**验收**：`tests/test_io_guards.py` 8 条（未知名 rc=2 并列出合法名 / 合法子集 rc=0 / 省略参数 rc=0 / collect 拒绝覆盖被跟踪文件且目标字节不变 / `--force` 放行且真写出 / 未被跟踪的既有文件可覆盖 / judge 的 `--report` 与 `--json` 双落点均拒绝 / `--force` 放行）。全部对**退出码**断言。
