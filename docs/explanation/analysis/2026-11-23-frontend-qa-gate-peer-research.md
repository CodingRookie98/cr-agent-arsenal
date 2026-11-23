# AI 前端运行时验收、浏览器 QA 代理与 Web 质量门禁同类工程深度调研报告

> **文档控制信息**
> - **文档标识**: ANA-FRONTEND-QA-PEERS-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **调研动机**: 本仓库 `frontend-qa-gate` 试图以「五域 31 条静态断言 + 8 节 Markdown 报告模板 + 433 行格式校验脚本」把守前端交付质量。2025–2026 年浏览器自动化 MCP（Chrome DevTools MCP、Playwright MCP）、无依赖 CDP CLI（`agent-browser`）与 CI 确定性门禁（`axe-core` / Lighthouse CI）已成为 AI 前端 QA 的主流基础设施。本次调研一手拉取 11 个头部开源标杆与本机已装同类技能，为配套评估报告 [2026-11-23-frontend-qa-gate-architecture-evaluation.md](./2026-11-23-frontend-qa-gate-architecture-evaluation.md) 建立行业标尺。
> - **证据分级**: 【A】一手（2026-11-23 `gh api` 实测元数据与上游源码精读、本机已装 `chrome-devtools-plugin` / `agent-browser` / `webapp-testing` 原文）｜【B】二手转引（官方工程文与最佳实践综合摘要）｜【C】基于实证的架构提炼与研判

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：基于 2026-11-23 `gh api` 11 个开源前端验收标杆一手实测、本机 4 类可执行浏览器/QA 技能源码剖析及 Anthropic 2026 Playwright Evaluator 前沿范式，收敛现代 AI 前端 QA 三层架构规律 |

---

## 0. 摘要（TL;DR）

**一句话结论**：2025–2026 年所有高星 AI 前端验收方案的核心共同点只有一条——**「State over Intent（只信浏览器运行态事实，不信 Agent 手写叙述）」**。从 `gstack`（142k★）到 `chrome-devtools-mcp`（58.9k★）、`agent-browser`（53.5k★）、`playwright-mcp`（40k★）再到 `axe-core`/`lhci`，**业界没有任何头部标杆采用「零采集代码 + 让 Agent 手填长篇 Markdown 表格 + 用正则验中文报告格式」的门禁路线**；主流范式是 **「MCP/CDP 探针实时探索取证 → 固化确定性 Playwright + axe + LHCI 退出码门禁 → 真机/读屏等不可自动化项明确划归人工签收」**。

五条一级结论：

1. **头部 AI 前端 QA 技能全部自带真实浏览器执行抓手，而非空壳填表规程**。`garrytan/gstack`（142.4k★）的 `qa` + `browse` 自带无头浏览器执行层，强制 diff-aware 范围收缩、before/after 截图对比、`CONSOLE_ERRORS=` 检查与 Test→Fix→Verify 闭环【A】；`vercel-labs/agent-browser`（53.5k★）以 Rust 原生 CDP CLI 驱动 `dogfood` 技能，走 Repro-First（发现即停、步步标注截图+录屏+`errors`/`console`）【A】；`anthropics/skills`（199.2k★）的 `webapp-testing`（96 行）配 `with_server.py` 托管多服务并直接跑 Playwright 脚本【A】。
2. **Google 与 Microsoft 已将底层浏览器采集能力彻底 MCP 化**。`ChromeDevTools/chrome-devtools-mcp`（58.9k★）不仅开放完整 CDP MCP，更附带 8 个开箱即用的原子技能（如本机已装的 `a11y-debugging` 内置 Lighthouse + A11y Tree + 4 段 JS 探针、`debug-optimize-lcp` 内置 Trace + Fast 3G 限速仿真）【A】；`microsoft/playwright-mcp`（40.0k★）原生支持 Chromium / Firefox / WebKit 跨引擎无障碍树交互【A】。
3. **规则速查类前端技能极度克制，绝不强造复杂报告门禁**。`vercel-labs/agent-skills`（34.8k★）的 `web-design-guidelines` 主文件仅 **51 行（2.1 KB）**，以 SHA-256 锁定上游规则快照，输出极简 `file:line` 缺陷列表【A】。
4. **Anthropic 2026 Harness 实证确立了「Playwright Evaluator」范式**。Anthropic 在《Harness design for long-running application development》中明确指出：让编码 Agent 自己填自检表必然落入自评乐观陷阱；解法是由独立 Evaluator 驱动 Playwright MCP 访问真实 live app，真实点击、填表、核查 API 与 Console 错误，以运行态客观证据而非文字声明作为判据【B】。
5. **自动化硬门禁与人类体验签收必须硬拆两层**。行业 CI 黄金组合（`playwright test` + `@axe-core/playwright` + `lhci autorun`）校验的是**确定性退出码、JSON 审计阈值与非空截图工件**；而屏幕阅读器（VoiceOver/NVDA）、真机软键盘/刘海屏与真实浏览器手感等无头环境物理不可达项，只能列入「人工签收清单」，绝不能塞进无降级路径的 CI 阻断门禁，否则必然制造死锁或倒逼造假【A/B/C】。

---

## 1. 头部开源浏览器/前端验收标杆一手全景（2026-11-23 `gh api` 实测【A】）

| 仓库 | Stars 【A】 | 最近推送 【A】 | 核心验收范式与一手源码观察【A】 |
| :--- | :---: | :---: | :--- |
| **`anthropics/skills`** (`webapp-testing`) | **199,160** | 2026-11-16 | 96 行精简规程 + `with_server.py` 托管 dev server 生命周期 + 原生 Playwright 侦察-执行（`networkidle` + `console_logging.py`），无繁复报告格式门禁 |
| **`garrytan/gstack`** (`qa` + `browse`) | **142,412** | 2026-11-23 | 自带无头浏览器执行层；支持 diff-aware 范围收缩与 Quick/Standard/Exhaustive 三档；`browser-verify.md` 强制 before/after 截图对比 + `CONSOLE_ERRORS=` + 快照树 diff + Test→Fix→Verify 闭环；**零 Markdown 正则报告校验器** |
| **`browser-use/browser-use`** | **121,800** | 2026-11-22 | Python AI 浏览器代理通用执行框架 |
| **`ChromeDevTools/chrome-devtools-mcp`** | **58,910** | 2026-11-23 | Google 官方 CDP MCP + 8 个原子诊断技能（`a11y-debugging` 含 Lighthouse/A11y Tree/4 段 JS 探针、`debug-optimize-lcp` 含 Trace/Fast 3G 限速仿真、`cookie-debugging`、`memory-leak-debugging`） |
| **`vercel-labs/agent-browser`** (`dogfood`) | **53,484** | 2026-11-23 | 零 Playwright 依赖的 Rust 原生 CDP CLI（`@eN` 无障碍树引用），内置 `dogfood` 协议：**Repro-First**（步步标注截图+录屏+`errors`/`console`），限定 5–10 个高证据真缺陷，拒绝硬凑长表 |
| **`microsoft/playwright-mcp`** | **40,035** | 2026-11-18 | 微软官方跨引擎（Chromium / Firefox / WebKit）Playwright MCP，基于无障碍树做确定性交互 |
| **`vercel-labs/agent-skills`** (`web-design-guidelines`) | **34,770** | 2026-11-20 | 仅 **51 行 / 2.1 KB**，SHA-256 锁定上游规则快照，极简 `file:line` 输出 |
| **`GoogleChrome/lighthouse`** / **`lighthouse-ci`** | **31,193** / **7,163** | 2026-11-20 / 11-17 | 行业标准 Web 性能/无障碍/CWV 确定性审计与 Commit 级预算回归门禁（`lhci autorun`） |
| **`microsoft/playwright-cli`** | **15,397** | 2026-11-18 | Playwright 轻量录制、选择器探测与截图 CLI |
| **`dequelabs/axe-core`** | **7,871** | 2026-11-19 | 行业标准 WCAG/ARIA 确定性规则引擎（配合 `@axe-core/playwright` 进入 CI 零违例硬门禁） |

---

## 2. 2026 前端 AI QA 的三层黄金架构【A/B/C】

综合 Anthropic Playwright Evaluator 实践【B】与上述 11 个开源工具链【A】，成熟的前端 AI 验收并非“手写表格门禁”，而是清晰的三层协同：

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Layer 1: 探索与诊断层（实时运行时探针）                                     │
│  · Chrome DevTools MCP (a11y-debugging / debug-optimize-lcp / Trace / 3G)  │
│  · vercel-labs/agent-browser dogfood (Repro-First 步步标注截图+录屏+errors) │
├────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: 跨引擎交互验证与回归固化层（确定性退出码门禁，Block Merge）        │
│  · Playwright MCP / playwright test (Chromium + Firefox + WebKit)          │
│  · @axe-core/playwright (WCAG 自动化零违例) + lhci (性能/CWV 预算)          │
│  · Console / PageError / UnhandledRejection 计数 == 0 + 截图文件真实存在     │
├────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: 人工体验签收清单（Human Sign-off，不制造无头 CI 死锁）             │
│  · 真实读屏体验 (VoiceOver/NVDA)、真机软键盘/刘海屏、真实网络体感与视觉签收  │
└────────────────────────────────────────────────────────────────────────────┘
```

### 两条必须牢记的反面教训【B/C】

1. **Goodhart 定律与「只验表不验真（Paperwork Theater）」**：一旦机械门禁只检查 Markdown 表格格式、章节标题和自然语言禁用词，而不核对真实浏览器退出码、Console 错误数与磁盘截图文件存在性，Agent 就会把算力消耗在排版绕过上，而非真正测出页面 Bug；
2. **「自动化必过项」与「真机/人工项」混为一谈必然引发死锁**：在 Linux 无头容器/CI 中强制要求 VoiceOver、iOS 刘海屏与 Safari 最低版通过且禁止降级，等于构造 100% 不可满足条件，最终反向诱导伪造 PASS 或滥用 N/A。

---

## 3. 下篇衔接与参考来源

配套评估报告 **[2026-11-23-frontend-qa-gate-architecture-evaluation.md](./2026-11-23-frontend-qa-gate-architecture-evaluation.md)** 将基于本篇标尺，对本仓库 `skills/frontend-qa-gate/`（8 文件 / 76.6 KB）进行全量源码解剖、展示 5 组实测击穿 `check-qa-report.py` 的对抗载荷，并给出从「Markdown 验表警察」重构为「真实探针编排协议」的落地路线图。

### 主要参考来源

- **一手开源与本机源码实测（2026-11-23）【A】**：`anthropics/skills`（https://github.com/anthropics/skills ，及本地 `.agents/skills/webapp-testing/`）、`garrytan/gstack`（https://github.com/garrytan/gstack ）、`browser-use/browser-use`（https://github.com/browser-use/browser-use ）、`ChromeDevTools/chrome-devtools-mcp`（https://github.com/ChromeDevTools/chrome-devtools-mcp ，及本地 `a11y-debugging`/`debug-optimize-lcp`/`chrome-devtools`）、`vercel-labs/agent-browser`（https://github.com/vercel-labs/agent-browser ，及本地 `agent-browser`）、`microsoft/playwright-mcp`（https://github.com/microsoft/playwright-mcp ）、`vercel-labs/agent-skills`（https://github.com/vercel-labs/agent-skills ）、`GoogleChrome/lighthouse`（https://github.com/GoogleChrome/lighthouse ）、`GoogleChrome/lighthouse-ci`（https://github.com/GoogleChrome/lighthouse-ci ）、`dequelabs/axe-core`（https://github.com/dequelabs/axe-core ）。
- **前沿实验室工程文摘要【B】**：Anthropic Engineering（2026-03）《Harness design for long-running application development》（Playwright MCP Evaluator / State over Intent）。
