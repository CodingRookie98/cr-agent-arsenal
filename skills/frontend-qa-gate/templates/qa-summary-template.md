# 前端产物验收摘要 · `<artifact-name>`

> **门禁声明**：自动化门禁仅校验 `qa-evidence.json`（`python3 "$SKILL_DIR/scripts/check-qa-report.py" <qa-evidence.json> --require-verdict=PASS`），**不解析本 Markdown**。顺序：`taste-driven-designer` D1-D3 → `frontend-qa-gate` → `dual-round-review`。

## 1. 结论与信号

- 清单：`<qa-evidence.json>` · 结论：`<PASS | FAIL | BLOCKED>` · Commit：`<commit>` · 探针：`<probe_tool>`
- 信号：`console_errors=<n>` · `page_errors=<n>` · `axe_critical_serious=<n>`
- 断言：总计 `<n>` · `passed=<n>` · `failed=<n>` · `unverified=<n>` · `na=<n>`

## 2. Tier 2 人类与真机签收

| ID | 核验项 | 状态 | 人类签收 |
|---|---|---|---|
| H-A5 | 真实屏幕阅读器（VoiceOver/NVDA）主干流程 | `pending_human` | `<签收人 / 日期>` |
| H-V4/V5 | 真机软键盘不遮挡与刘海屏安全区 | `pending_human` | `<签收人 / 日期>` |
| H-V6 | 真机横竖屏切换可用性 | `pending_human` | `<签收人 / 日期>` |
| H-B1/B2 | 最低支持版本 Safari/Firefox/WebView 真机覆盖 | `pending_human` | `<签收人 / 日期>` |

## 3. 缺陷回流路由

| 断言 ID | 摘要 | 类型（行为/结构/根因/方向/超范围） | 回流目标 | 状态 |
|---|---|---|---|---|
| `<无>` | `<无>` | `<->` | `<->` | `<->` |

- 人类签收：`<姓名>` · `<YYYY-MM-DD>` · **放行权：人类（用户）**
