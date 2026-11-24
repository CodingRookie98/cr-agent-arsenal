# 五域双轨验收矩阵 (Acceptance Matrix · SSOT)

> **唯一真相源（SSOT）**：本文件是前端产物运行时断言的唯一权威基线。每条断言须二值可判定并附步骤与磁盘证据；`taste-driven-designer` D2 自检仅作过程抽查，不替代本矩阵。
> **边界**：仅测运行态浏览器产物；源码推理（hydration/竞态/派生状态）归 `dual-round-review`，视觉品味与 Gate C 创意放行归 `taste-driven-designer`。

---

## Tier 1 · Automated Block-Merge Assertions（共 23 项，无头探针取证）

### 1. D-R 响应式视口（5 项）

| ID | 断言 | 探针取证方法 | 证据产物 |
|---|---|---|---|
| V1 | 最小目标宽度（320/375px）无横向滚动 | 设 320/375px 滚到底，查 `scrollWidth <= innerWidth` | 截图 + 测量 JSON |
| V2 | 无元素溢出父容器或互相遮挡 | 多断点查 DOM 边界矩形与截断 | 截图 + 检测 JSON |
| V3 | 长文本、超长词与长标题不撑破布局 | 注入超长合成文本与连续无空格串 | 注入后截图 |
| V7 | 关键触控/点击目标尺寸达标（≥44×44px）且不误触 | 测核心按钮 bounding box 与间距 | 尺寸 JSON |
| V8 | 200% 缩放不丢失内容与核心功能 | 设 200% zoom 重走关键交互 | 缩放后截图 |

### 2. D-S 交互状态（8 项，已移除越界代码项 S9）

| ID | 断言 | 探针取证方法 | 证据产物 |
|---|---|---|---|
| S1 | 冷加载完整渲染，无控制台/页面错误与明显跳动 | 冷加载采集 console/pageerror 与 CLS | 首屏截图 + 日志 |
| S2 | 限速下加载态真实可见（≥300ms 指示可见） | 网络节流打开页面捕获加载中间帧 | 限速加载截图 |
| S3 | 空态有明确说明与下一步指引，而非空白/报错 | 注入空数据集打开列表或视图 | 空态截图 |
| S4 | 错误态提供原因与重试，且**保留用户输入** | 断网/500 后提交表单并核对输入保留 | 错误截图 + 日志 |
| S5 | 禁用态视觉与语义（`disabled`/`aria-disabled`）一致 | 条件未满足时核对外观与 DOM 属性 | 截图 + DOM JSON |
| S6 | 键盘焦点可见且顺序符合视觉顺序 | Tab 遍历核对 focus ring 与顺序 | 焦点日志 + 截图 |
| S7 | 重复提交被阻止或幂等（连击无重复副作用） | 短时连击提交并统计写请求数 | 网络计数 JSON |
| S8 | 浏览器后退/路由返回恢复不丢状态 | 填写或筛选后退再前进核对恢复 | 前后截图 + 记录 |

### 3. D-A 无障碍（7 项）

| ID | 断言 | 探针取证方法 | 证据产物 |
|---|---|---|---|
| A1 | 表单输入控件有关联标签或 `aria-label`/`aria-labelledby` | axe-core + 无障碍树扫描表单 | 扫描 JSON |
| A2 | 图标按钮均有可访问名称 | 无障碍树核对 icon-only 按钮名称 | 扫描 JSON |
| A3 | 仅键盘可走完关键流程（含弹窗与菜单） | 仅用 Tab/Enter/Space/Esc 跑通主流程 | 键盘日志 + 截图 |
| A4 | 焦点顺序合理且弹窗内焦点不逃逸 | 打开模态框连续 Tab 查闭环与回焦 | 焦点轨迹 JSON |
| A6 | 尊重 `prefers-reduced-motion` 动效降级 | 启用 `reduced-motion: reduce` 核查动效 | 降级截图/日志 |
| A7 | axe-core / 无障碍树语义结构零 critical/serious 违规 | 运行 `@axe-core/playwright` 或 DevTools a11y | axe 报告 JSON |
| A8 | `aria-live` 状态变化（提交结果/报错）可感知 | 触发校验提示并检查 live region | live region 日志 |

### 4. D-P 性能预算（3 项）

| ID | 断言 | 探针取证方法 | 证据产物 |
|---|---|---|---|
| P1 | 构建体积相对基线无未解释增长 | 对比改动前后构建产物体积 | 体积对比 JSON |
| P2 | 核心交互/首屏时序相对基线未回归 | 多次采样首屏与核心交互时序 | Lighthouse/时序 JSON |
| P3 | 非首屏图片懒加载或显式宽高尺寸声明 | 检查非首屏图片 `loading="lazy"` 或尺寸 | 资源属性 JSON |

---

## Tier 2 · Human & Device Sign-Off Checklist（4 项，交人类签收不阻断 Tier 1）

| ID | 域 | 人工真机核验项 | 记录形态 |
|---|---|---|---|
| H-A5 | `D-A` | 真实屏幕阅读器（VoiceOver / NVDA）主干流程 | `human_signoff` |
| H-V4/V5 | `D-R` | 物理真机软键盘不遮挡与刘海屏安全区 | `human_signoff` |
| H-V6 | `D-R` | 真机横竖屏切换后布局可用 | `human_signoff` |
| H-B1/B2 | `D-B` | 目标最低支持版本 Safari/Firefox/WebView 跨浏览器真机覆盖 | `human_signoff` |

---

## 跨技能分工表

| 问题归属 | 负责方 | 说明 |
|---|---|---|
| 浏览器运行时行为与机械门禁（Tier 1+2） | `frontend-qa-gate` | 本矩阵为 SSOT；未验 Tier 1 项阻断 |
| 视觉品味、创意方向、盲比与 Gate C 签收 | `taste-driven-designer` | 结构性布局崩溃回流其 D2 |
| 源码正确性、派生状态与竞态/泄漏根因 | `dual-round-review` | 不在本技能审源码 |
| XSS、凭据泄漏、依赖投毒与供应链安全 | 宿主 CI 与安全层 | 标「超出本技能范围」并升级 |
