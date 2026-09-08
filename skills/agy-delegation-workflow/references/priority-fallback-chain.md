# 执行智能体优先级链与降级规程 (Priority & Fallback Chain)

在多智能体协作闭环中，前台智能体（负责规划与审查）与后台执行智能体之间必须维系明确的执行优先级与降级容灾机制。

---

## 1. 执行智能体三级优先级链 (Priority Chain)

```mermaid
graph TD
    Start["任务准备就绪"] --> EnvCheck{"当前宿主环境检查"}
    EnvCheck -->|Antigravity/agy 原生环境 (含 invoke_subagent)| P1Native["首选: 宿主环境原生派发<br/>(直接调用 invoke_subagent)"]
    EnvCheck -->|非 agy 宿主 (Claude Code/终端/CI)| P1CLI["首选: agy 无头命令行<br/>(Gemini 3.8 Flash 独立进程)"]
    P1CLI -->|基础设施连续 3 次硬故障 (OAuth EOF / 区域阻断)| Fallback1["触发 3-Tries Rule 降级为系统子智能体"]
    P1Native -->|连续 2+ 批次重写率 >50% 或配额超限| Fallback2["触发直接编写标准"]
    P1CLI -->|连续 2+ 批次重写率 >50%| Fallback2
    Fallback2 --> P3["最终兜底: 前台智能体直接编写 (Direct-Write)<br/>(调用 write_file / replace_file_content)"]
```

### 第一优先级 (A)：宿主环境原生派发（agy 宿主首选）
* **适用条件**：当前 Agent **本身即运行于 Antigravity (agy) / Antigravity IDE 宿主环境**且具备 `invoke_subagent` 原生工具时。
* **执行原则**：**直接且强制调用 `invoke_subagent` 派发子智能体**。严禁在当前终端内通过终端套娃调用 `agy` 命令行另起新进程，彻底杜绝无头权限拦截、代理污染与嵌套死锁。

### 第一优先级 (B)：`agy` 无头命令行执行（非 agy 宿主首选）
* **适用条件**：**当宿主环境不是 agy**（例如运行在 Claude Code、Cursor、外部无原生子智能体调度器的通用终端或纯命令行 CI/批处理环境中）时，**优先使用 `agy` 命令行派发后台无头进程**。
* **默认模型**：`Gemini 3.8 Flash (High)`。
* **标准命令**：
  ```bash
  unset HTTPS_PROXY HTTP_PROXY http_proxy https_proxy ALL_PROXY all_proxy; \
  agy -p "$(cat .agy-tasks/task.md)" \
    --model 'Gemini 3.8 Flash (High)' \
    --dangerously-skip-permissions \
    --print-timeout 20m
  ```

### 第二优先级：系统子智能体降级 (`invoke_subagent` / `delegate_task`)
* **触发条件**：仅在非 agy 宿主环境中，`agy` 出现**网络、认证、区域限制等基础设施连续 3 次失败**时触发（严格遵循 3-Tries Rule），而非因为代码质量不佳。
* **调用方式**：直接复用任务 Prompt 内容作为 `Prompt`。
* **注意事项**：若此时子智能体因模型提供商配额超限（如 HTTP 429），切勿原地盲目重试，应切换至前台直接编写。

### 第三优先级：前台智能体直接编写 (Direct-Write)
* **定位**：终止委派，由前台调度智能体使用原生写入工具直接编写落地。
* **触发标准**：必须同时满足下方《直接编写决策标准》的全部 4 项准则。

---

## 2. 直接编写决策标准 (Direct-Write Decision Criteria)

当以下 4 条准则 **全部满足** 时，前台智能体应果断停止委派，改由自身直接编写（实测通常比反复委派排错快 3 倍以上）：

1. **高失败率**：连续 2 个及以上批次中，>50% 的后台产出需要完整重写（非 1~3 行轻度 patch 可修复）；
2. **系统性错误**：同类结构性错误（如伪造 API、类型泛化）跨文件反复重复出现，证明后台执行模型缺乏对当前工程模式的拟合能力；
3. **已充分掌握上下文**：前台智能体已完整阅读全部目标组件 API、类型定义与 Mock 结构，掌握的工程事实远超后台无状态执行器；
4. **页面 / 模块高度同质化**：待开发页面遵循完全一致的布局或架构模式，完成首个页面后，其余模块基本属于机械化复刻。

---

## 3. 反触发条件 (Strict Anti-Triggers)

以下 5 类任务具有高度破坏性或决策敏感性，**严禁委派给后台执行智能体（agy 或外部子智能体）**，必须由前台智能体亲自处理：

1. **Git 写操作**：包括 `commit`、`push`、`reset`、`rebase`、`merge`、`checkout` 等。
2. **破坏性文件变更**：删除（`rm`）、批量移动版本管理文件或修改 `.gitignore`。
3. **交互式决策与需求澄清**：需要与用户协商业务权衡或确认设计规范的任务。
4. **安全与凭据敏感操作**：涉及密钥、API Token、环境变量及访问控制策略。
5. **编写架构设计与规划文档**：包括 `IMPLEMENTATION_PLAN.md`、`task.md`、需求规格与设计总纲。前台的核心立身之本是规划，后台只做纯代码执行。
