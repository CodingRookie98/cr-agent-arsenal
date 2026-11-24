# 现代探针编排与 Schema v2 契约 (Probe Orchestration)

> 定位：规定「探针工具路由、证据落盘目录、`qa-evidence.json` Schema v2 与结论推导」。断言全集见 [acceptance-matrix.md](acceptance-matrix.md)。

---

## 1. 现代探针优先路由矩阵

| 场景 | 优先探针工具链 | 采集重点 |
|---|---|---|
| 交互排查、DOM/视口/LCP/a11y 诊断 | `chrome-devtools-mcp` / `chrome-devtools-plugin`（含 `a11y-debugging`、`debug-optimize-lcp`） | 实机快照、console/network、LCP 与无障碍树 |
| 多步 UI 操作、表单流与截图取证 | `agent-browser` | 导航、点击、键盘路径、视口调整与截图 |
| CI 自动化回归与基线扫描 | `Playwright + @axe-core/playwright + Lighthouse CI` / `webapp-testing` | 可复现断言、axe 违规计数、体积与时序 JSON |

**能力门控**：Tier 1 缺浏览器或测量能力时必须记 `unverified`（推导 `BLOCKED`），禁假装通过；Tier 2 无物理设备/读屏时记 `pending_human` 交人类签收，不阻断 Tier 1 `PASS`。

---

## 2. 证据落盘目录规范

```text
.qa-evidence/                    # 证据根目录（--evidence-root 默认为清单所在目录）
├── qa-evidence.json             # Schema v2 主清单（机械门禁唯一校验对象）
├── shots/                       # 真实截图（.png/.jpg/.webp，非空且过魔数校验）
└── logs/                        # 探针输出（.json 须可解析；.txt/.log 须非空）
```

- `passed` 断言 `evidence` 须为相对 `--evidence-root` 的相对路径（字符串或非空列表），禁绝对路径、禁 `..` 与符号链接逃逸；`--evidence-root` 默认为清单文件所在目录；若把清单置于 `reports/` 等子目录且证据在外层 `shots/`/`logs/` 时，须显式传 `--evidence-root=<dir>`。

---

## 3. `qa-evidence.json` Schema v2 契约

| 字段 | 约束 | 说明 |
|---|---|---|
| `schema_version` | 严格整数 `2`（排除 `bool`） | 版本标识 |
| `artifact` | 对象：`name` / `url` / `commit` / `captured_at` / `probe_tool` | 非空且无 `<...>` 占位符 |
| `runtime_signals` | `console_errors`、`page_errors`（必选）；`axe_critical_serious`（可选） | 严格非负整数（排除 `bool`），`>0` 触发 `FAIL` |
| `automated_assertions` | 非空数组（≥ `--min-assertions`，默认 `4`） | 默认须覆盖 `D-R`/`D-S`/`D-A`/`D-P` 四个核心域 |
| `human_signoff` | 可选数组（存在时必为 `list`） | Tier 2 人工真机清单 |
| `verdict` | `"PASS"` / `"FAIL"` / `"BLOCKED"`（大小写精确） | 必须等于推导结论 |

- **`automated_assertions` 行字段**：唯一 `id`、`domain`（`D-R`/`D-S`/`D-A`/`D-P`/`D-B`）、`status`（`passed`/`failed`/`unverified`/`na`）、`steps`；`passed` 必含合法磁盘 `evidence`；`na` 必含 `na_reason`（均禁 `<...>` 占位符）。
- **`human_signoff` 行字段**：唯一 `id`、`item`、`status`（`pending_human`/`signed_off`/`failed`/`na`）；`signed_off` 必含 `signer` 与 `signed_at`；`na` 必含 `na_reason`。

---

## 4. 结论推导与非死锁规则

| 结论 | 判定条件（按优先级） | 门禁语义 |
|---|---|---|
| **FAIL** | 任一自动化断言 `failed`，或 `human_signoff` `failed`，或任一 `runtime_signals` > 0 | Exit 0（`--require-verdict=PASS` 时 Exit 1）；按 [regression-routing.md](regression-routing.md) 分流 |
| **BLOCKED** | 非 `FAIL`，且有 `unverified` 断言或无 `passed` 断言 | Exit 0（`--require-verdict=PASS` 时 Exit 1）；补探针或升级人类 |
| **PASS** | ≥1 条 `passed`，无 `failed`/`unverified`，`runtime_signals` 全 0 | Exit 0；**含 `pending_human` 仍为 `PASS`**，交人类签收 Tier 2 |

> 禁止输出绝对评分/通过率替代结论；禁止正则解析 Markdown 替代 `qa-evidence.json` 校验。
