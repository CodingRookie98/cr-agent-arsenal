# agy 代码生成高频失败模式与审计命令清单 (Failure Modes & Audit Checklist)

后台执行智能体（`agy`）虽然编码速度极快，但在特定场景下存在大模型特有的思维惯性与虚假合规问题。前台智能体在合并其代码前，**必须对以下典型失败模式执行针对性审计命令**。

---

## 1. 常见失败模式与审计对照表

| # | 失败模式 | 典型现象 | 根因与危害 | 必跑审计命令 |
|---|---|---|---|---|
| **1** | **自造 Fallback 数据** | 忽略指定的 `@/mock`，自造 `DEFAULT_*` / `FALLBACK_*` 内联数组 | 字段与后端模型不匹配，上线后因真实数据字段差异报错 | `grep -rn 'DEFAULT_\|FALLBACK_' src/app/<新路径>/*.tsx src/components/**/*.tsx \| grep -v 'import\|useState\|mock\|\.map\|\.filter'` |
| **2** | **编造组件 API** | `Badge variant="secondary"` (应为 `neutral`)<br>`Button variant="outline"` (应为 `secondary`)<br>`Tabs items=` (应为 `tabs=`)<br>`toast variant="destructive"` (应为 `"error"`) | 盲目猜测 UI 库组件属性，导致运行时样式错乱或控制台报错 | `grep -rn 'variant="secondary"\|variant="outline"\|variant="destructive"\|items=\[\|activeKey=' src/app/<新路径>/*.tsx` |
| **3** | **硬编码颜色 + `alert()`** | 使用 `text-white`/`bg-white` 替代设计 Token；使用 `alert()` 替代 `useToast()` | 破坏深色模式与全站主题设计规范；破坏无头测试环境（`alert` 挂起） | `grep -rn 'text-white\|bg-white\|border-white\|via-\[#\|to-\[#' src/app/<新路径>/*.tsx src/components/**/*.tsx`；<br>`grep -rn 'alert(' src/app/**/*.tsx src/components/**/*.tsx` |
| **4** | **`"use client"` 指令缺失** | 包含 `useState`、`useEffect`、`onClick` 的组件未在文件首行声明指令 | jsdom 单元测试通常无法捕获此问题，Next.js 生产环境构建或真机运行时交互完全失效 | `grep -rL '"use client"' src/app/<新路径>/*.tsx \| xargs grep -l 'useState\|useEffect\|useRef\|onClick\|onChange' 2>/dev/null` |
| **5** | **防级联渲染违规** | 在 `useEffect` 钩子中直接执行同步 `setState`（如 `setIsLoading(true)`） | 触发 React 级联重新渲染（Cascading Renders），引发性能损耗与 ESLint 警报 | `grep -rn 'useEffect(' -A 5 src/components/**/*.tsx \| grep 'set[A-Z]'` |
| **6** | **全局 Store 类型隐蔽泛化** | 为了当前任务编译通过，将共享 Store 字段从 `id: number` 扩大为 `number \| string` | 造成全工程范围内的下游组件类型级联破坏，单文件 `tsc` 无法捕获 | 审查阶段**必须强制执行全量构建验证**：<br>`pnpm build` 或 `npm run build` |
| **7** | **React 19 Fake Timers 死锁** | 在涉及 `setInterval` 轮询的状态机测试中使用 `vi.useFakeTimers()` | React 19 调度器导致 interval 回调的 setState 无法在虚假计时器推进中及时 flush，测试假死 | 检查测试代码，涉及多步轮询必须使用真实计时器配合 `waitFor({ timeout: 5000 })` |

---

## 2. 审查全流程 6 步验收 SOP (Review Checklist)

在将 `agy` 的产出合并入库前，前台智能体必须逐项执行以下 6 步核验：

1. **Diff 范围核验**：
   * 运行 `git diff --stat`，确认所有改动文件均在任务任务书指定范围内，**严禁无端重构无关文件**；
   * 检查是否混入了 `IMPLEMENTATION_PLAN.md` 或 `task.md`，若有立即执行 `rm` 删除。
2. **静态类型与 Lint 校验**：
   * `npx tsc --noEmit` 零错误；
   * `npx eslint <所修改文件>` 零警告零错误。
3. **失败模式硬命令审计**：
   * 执行上方表格中的全部 `grep` 审计命令，确保匹配项清零。
4. **全链路测试套件**：
   * 运行目标单元测试：`npx vitest run <目标测试>` 全部通过；
   * 确保测试真实覆盖了业务逻辑，杜绝删断言或伪造测试。
5. **全局构建验证 (Catch Cascades)**：
   * 运行 `pnpm build`。确保全项目拓扑类型一致，无全局类型泛化引发的隐蔽断裂。
6. **双轮对抗审查闭环**：
   * 调用 `dual-round-review` 技能，通过红队第一性原理与架构师元审判取得阻断项清零结论后方可准予提交。
