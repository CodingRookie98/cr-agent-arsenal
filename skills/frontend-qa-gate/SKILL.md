---
name: frontend-qa-gate
description: "Use when a frontend artifact needs runtime acceptance verification against real browser evidence: responsive viewports, interaction states, accessibility, performance budgets, and pre-release QA gates. Triggers on frontend acceptance, QA gate, a11y check, responsive breakage, keyboard trap, error-state missing, performance regression."
license: MIT
---

# frontend-qa-gate 前端产物验收

补齐「设计收敛」与「代码审查」间的空缺：**真实浏览器运行时产物验收**——回答产物在真实浏览器中是否真的可用。

```text
taste-driven-designer D1-D3  →  frontend-qa-gate  →  dual-round-review
       (品味与方向)            (运行时产物门禁)          (代码正确性)
```

本技能是前端产物五域运行时断言的**唯一真相源（SSOT）**，以 **双轨门禁（Tier 1 自动化阻断 + Tier 2 人工真机签收）** + **现代探针编排** + **磁盘证据 JSON 机械门禁**，破除无头环境 100% `BLOCKED` 死锁。

---

## 适用边界

- **使用**：页面/组件/流程（含 AI 生成产物）交付前验收；验证响应式、交互态（加载/空/错/禁用/焦点/幂等/返回）、无障碍键盘路径或性能预算；`taste-driven-designer` D3 后或 `goal-loop` Verify 阶段。
- **不用**：视觉品味裁决（归 `taste-driven-designer`）、源码静态推理与竞态分析（归 `dual-round-review`）、安全/供应链审计（XSS/密钥/投毒标「超出本技能范围」升级宿主 CI）、纯后端逻辑。

---

## 铁律 (Invariants)

1. **证据优先**：每条 `passed` 断言须对应非空物理文件（截图魔数/JSON 可解析校验），叙述不构成证据。
2. **三态诚实**：断言状态仅限 `passed` / `failed` / `unverified`（或带 `na_reason` 的 `na`）；未验不得标 `passed`。
3. **禁分数判据**：禁止以绝对分数、等级或通过率作为验收或放行判据，结论仅限 `PASS` / `FAIL` / `BLOCKED`。
4. **双轨不死锁**：**Tier 1**（`D-R`/`D-S`/`D-A`/`D-P` 共 23 项）由无头探针取证并阻断合并；**Tier 2**（4 项真机/读屏）标 `pending_human` 交人类签收，不阻断 Tier 1 `PASS`。**放行权归人类**。
5. **产物级边界**：仅据运行态行为判定，不审源码；代码级根因路由至 `dual-round-review`。
6. **独立可分发**：禁止跨技能相对链接，仅用反引号命名引用他技能。
7. **四向回流**：缺陷按 [regression-routing.md](references/regression-routing.md) 分流，禁止静默修补结构或代码根因。
8. **安全合规**：仅用合成数据，禁落盘凭据或 PII；安全问题标「超出本技能范围」升级宿主 CI。

---

## 双轨门禁与执行流程

| 轨道 | 覆盖域 | 门禁语义 |
|---|---|---|
| **Tier 1 · 自动化阻断** | `D-R`(5) · `D-S`(8) · `D-A`(7) · `D-P`(3) | 无头探针取证；任一 `failed`→`FAIL`，任一 `unverified`→`BLOCKED` |
| **Tier 2 · 人类与真机** | `H-A5` · `H-V4/V5` · `H-V6` · `H-B1/B2` | 记入 `human_signoff`（`pending_human`）交人类签收，不阻断 Tier 1 `PASS` |

```text
Q1  确认 URL/commit 与基线，按 probe-orchestration.md 选探针（chrome-devtools-mcp / agent-browser / Playwright）
Q2  执行 Tier 1 23 项断言，截图与日志落盘并生成 qa-evidence.json（Schema v2）；Tier 2 记入 human_signoff
Q3  运行机械门禁校验证据文件、魔数与结论一致性：
    SKILL_DIR="<frontend-qa-gate 技能实际所在目录>"
    python3 "$SKILL_DIR/scripts/check-qa-report.py" <qa-evidence.json> --require-verdict=PASS
Q4  生成人类摘要（qa-summary-template.md）；缺陷按 regression-routing.md 分流；人类完成 Tier 2 签收
```

---

## 参考导航

- [acceptance-matrix.md](references/acceptance-matrix.md) — 五域 23+4 项断言唯一真相源（SSOT）与分工表
- [probe-orchestration.md](references/probe-orchestration.md) — 探针路由、`qa-evidence.json` Schema v2 与落盘规范
- [regression-routing.md](references/regression-routing.md) — 四向缺陷回流路由与 `dual-round-review` 接口
- [qa-evidence-template.json](templates/qa-evidence-template.json) — Schema v2 机器校验模板
- [qa-summary-template.md](templates/qa-summary-template.md) — 人类审阅与 Tier 2 签收摘要模板
- [check-qa-report.py](scripts/check-qa-report.py) — Fail-Closed 物理证据与 JSON 机械门禁脚本
