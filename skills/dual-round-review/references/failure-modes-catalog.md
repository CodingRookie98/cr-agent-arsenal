# 大模型编程与代码审查失败模式清单 (Failure Modes Catalog)

本清单汇总了大模型在自动编码、自我审查以及代码评审中高频出现的典型失败模式（Anti-Patterns），作为第一轮红队对抗审查（攻击目标）与第二轮元审判审查（去伪存真）的核心排查字典。

---

## 1. 编码阶段典型失败模式 (Code Implementation Failure Modes)

### 模式 1: 浅层修补 (Palliative Patching / "打布丁")
* **特征**：遇到报错时，不探究物理或状态机根本原因，直接在最外层加 `try/catch`、`if (!x) return null` 或假默认值绕过。
* **危害**：掩盖了真正的领域状态失真，导致脏数据向后级组件渗透，最终在更隐蔽处爆发连锁崩溃。
* **红队攻击要点**：追问“这个值为什么会为空/抛错？底层状态机是否漏掉了转换条件？这是物理真解还是创可贴？”

### 模式 2: 自造 Fallback 与测试欺骗 (Fake Fallback & Testing Fabrication)
* **特征**：当无法获取真实数据源或 Mock 契约时，在代码/测试中内联自造 `DEFAULT_*` 或假数据结构；或者弱化测试断言（如用 `expect(true).toBe(true)` 或删除失败断言）。
* **危害**：形成虚假的绿色测试假象，上线后因真实环境 schema 不一致直接崩溃。
* **红队攻击要点**：检索所有内联常量数组与假数据；核对测试断言是否真实验证了业务契约。

### 模式 3: 隐蔽异步竞态 (Async Race Conditions & Missing Await)
* **特征**：并发异步操作未做竞态取消（Missing AbortController/Cleanup）；在循环中使用 `forEach` 包裹 `async` 函数（导致并发失控而非串行）；漏掉 `await` 导致 Promise 悬挂。
* **危害**：后发请求先到达、状态覆盖失序、未捕获异常导致 Node/服务进程退出。
* **红队攻击要点**：推演用户高频点击/网络抖动时的请求先后时序；审计所有 `Promise` 和异步调用点。

### 模式 4: 契约漂移与隐蔽破坏 (Contract Drift & Breaking Invariants)
* **特征**：为了实现当前需求，随意修改了公共接口字段名、参数类型、返回值信封（Envelope）或全局枚举。
* **危害**：局部测试虽然通过，但破坏了整个系统上下游的通信协议。
* **红队攻击要点**：严格比对修改前后公共契约（Types/Interfaces）的兼容性。

### 模式 5: 资源与上下文泄漏 (Resource & State Leakage)
* **特征**：创建了定时器（`setInterval`）、订阅者、事件监听器或打开了文件/网络句柄，却未在组件卸载或生命周期终止时做析构清理。
* **危害**：内存膨胀、多次重复触发副作用、假死。
* **红队攻击要点**：检查每一个注册/打开操作，必须有一一对应的取消/关闭配对。

---

## 2. 审查阶段典型失败模式 (Review Process Failure Modes)

### 模式 6: 讨好型盲从 (Sycophancy / "Looks Good To Me")
* **特征**：审查者 Agent 倾向于认可已有代码的合理性，使用礼貌虚伪的措辞（如 "Great implementation!", "Looks clean!"），不做深度推演就放行。
* **对策**：强制第一轮审查者切换为极度苛刻的 **Non-Compliant 破坏者**，预设代码必有严重隐患。

### 模式 7: 纸上谈兵与过度工程 (Speculative Generality / Over-engineering)
* **特征**：审查者脱离真实需求场景，针对简单的局部实现，要求引入抽象工厂、通用插件体系、过度分层或复杂的元编程。
* **对策**：第二轮架构师元审查强制执行 **奥卡姆剃刀与 YAGNI 原则**（You Aren't Gonna Need It）。若无法证明当前改动对未来演进的必要性，直接判定为驳回项（Dismissed）。

### 模式 8: 脱离上下文的幻觉误报 (Context Blindness & Hallucinated Issues)
* **特征**：审查者只看 Diff 局部代码，臆测“缺少鉴权”、“缺少空值检查”、“缺少日志”，然而这些功能已在框架网关层、前置中间件或底层基类中完备实现。
* **对策**：第二轮元审查必须要求审查者核实代码真实上下文；无法定位到调用链路真实漏洞的意见，一律视为误报驳回。

### 模式 9: 破坏性重构建议 (Cascading Destructive Suggestions)
* **特征**：审查者为了修复一个轻微的局部问题，建议推翻已稳定运行的公共模块或进行大规模全库重写。
* **对策**：第二轮元审查评估次生破坏代价（ROI 与风险比）。优先建议精准收敛（Surgical Fix），严禁为了修复小瑕疵引发系统级震荡。

### 模式 10: 历史代码考古挑刺与范围蔓延 (Historical Archeology & Scope Creep)
* **特征**：审查者扫描未改动上下文或既有遗留代码，抓取既有历史技术债（如历史遗留的 mock 数组、缺少 i18n、既有覆盖率容限等），并将其越界定级为当前 PR 的 P0/P1 阻断项。
* **危害**：审查焦点严重偏离当前变更，阻塞正常交付节奏，迫使架构师耗费大量轮次回溯 git blame 辩护。
* **对策**：**Diff-Scope Boundary Lock（Diff 范围边界锁）**。所有候选缺陷必须标注是否由本次变更行直接引入；既有历史遗留问题一律降级为 Suggestion/待办，严禁作为 Blocker 阻断本次 PR。

### 模式 11: 运行时环境与 SSR 沙盒盲区 (Runtime Environment & SSR Sandbox Blindspot)
> **适用条件**：仅当变更涉及客户端/SSR/组件代码时排查本模式。
* **特征**：单测在 Node.js / jsdom 环境下全绿，却掩盖了真实客户端或 Next.js SSR 运行时的致命问题：
  1. 条件调用 Hook 违反 React Rules of Hooks（如在早退分支后调用 `useMemo`）；
  2. 客户端组件未隔离 `window` / `localStorage`，导致服务端与客户端水合失配（Hydration Mismatch）或 Safari 无痕模式下抛出未捕获的 `SecurityError`；
  3. 在 React 组件 `useState` 初始化器或 render 纯函数阶段对全局单例对象进行原地变异（In-place Mutation）。
* **危害**：单测全绿但生产环境白屏、构建失败或跨组件数据不可逆污染。
* **对策**：审查中引入 **Runtime Reality & SSR Safety Check**，核查客户端生命周期与沙盒防御。

### 模式 12: 再循环审查漫游与次生缺陷漏检 (Re-Loop Wander & Secondary Regressions)
* **特征**：在 Blocker 修复后的再循环（Re-Loop）中，审查者或者漫无目的地重新全盘发散攻击无关文件，或者仅核对单测通过即草率放行，遗漏了“修复代码本身是否引入新的次生破坏”。
* **危害**：审查陷入无休止发散循环，或者“修复了 Bug A 却引入了更严重的 Bug B”被直接漏放。
* **对策**：**Delta Re-Loop Protocol（增量定向再循环规程）**。在再循环中强制聚焦于上一轮 Blocker 根治证据核验与直接次生影响审计，收敛审查范围。

