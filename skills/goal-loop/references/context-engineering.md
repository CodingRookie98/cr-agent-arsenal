# 上下文工程与持久化规范 (Context Engineering & Persistence Rules)

## 概述 (Overview)

长程研发任务中，**上下文腐化（Context Rot）** 是导致幻觉与过早宣告完成的物理根因。本规范确立以文件系统为唯一真相源的**事件驱动持久化**法则，确保跨会话与压缩后可秒级无损恢复。

---

## 1. 持久化优先公理 (Persistence-First Axiom)

```text
上下文窗口 (Context Window) = 易失内存（有限，随时因压缩或重启归零）
文件系统   (Filesystem)     = 持久磁盘（唯一跨会话真相源）
```

**核心律条**：任何未落盘的决策、契约、根因与完成态等于不存在。关键进度与裁决写入计划文件及其 `Active Checkpoint`；高频临时细节（超长日志、探查草稿、派发账本明细）卸载至 `.goal-loop/`（已被 `.gitignore` 忽略）。

---

## 2. 事件驱动落盘原则 (Event-Driven Persistence)

废除打断并行探索的机械计次写盘，改为在以下 **4 类关键事件** 强制落盘检查点或卸载摘要：

1. **阶段切换**：`Align / Plan / Execute / Verify / Close` 任一阶段流转或执行通道重判时，立即更新 `Active Checkpoint`；
2. **关键根因或契约确立**：定位故障根因、做出自主裁决（`Ruling:`）或核实关键接口签名后，立即写入计划 Context Log；
3. **大块探索收敛**：完成一组关联只读检索/代码阅读后，一次性将高信息密度结论沉淀到计划或 `.goal-loop/scratchpad.md`，不打断并行只读；
4. **上下文压缩前（PreCompact）与挂起前**：在上下文接近上限、准备切换后端或等待异步派发前，强制刷新检查点与在途句柄摘要。

> 超长原始输出（完整构建日志、测试堆栈、长网页/PDF 摘录）按需卸载至 `.goal-loop/scratchpad.md`，主上下文仅保留精炼结论与文件路径指针。

---

## 3. 读写决策矩阵 (Read-Write Decision Matrix)

| 触发场景 | 动作 | 操作要求 |
|---|:---:|---|
| **完成文件写入/编辑** | 🔍 验真读 | 严格 **Read-Modify-Verify**：用 `git diff`、回读关键行或退出码确认变更准确生效 |
| **测试/构建命令结束** | ✍️ 记结论 | 提炼退出码、通过数与核心报错行写入检查点或 Scratchpad，避免瞬时输出滑出窗口 |
| **大块探索/长日志** | ✍️ 收敛卸载 | 一组探查完成后精炼落盘，原始长日志卸载至 `.goal-loop/scratchpad.md` |
| **开始新子任务** | 📖 读计划 | 仅读取计划中对应任务小节或交接简报文件，重置目标基线 |
| **遇到编译/单测报错** | 🔍 定向读 | 仅读取报错指向的具体文件与行段，严禁全量扫描无关目录 |
| **中断/重启恢复** | 🔄 恢复读 | 首选读取计划头部 `Active Checkpoint` 与 `- [x]` 清单，配合 `git status -s` 重建状态机 |

---

## 4. 跨会话断点恢复 SOP (Disaster Recovery)

会话重启、压缩恢复或网络中断重连后，固定执行 4 步：
1. **读锚点**：定位 `docs/project/plans/*.md` 中活跃计划并读取头部 `Active Checkpoint`；
2. **找断点**：自顶向下扫描任务清单，定位首个未勾选 `- [ ]` 任务（跳过标记 `parked` 的阻塞项）；
3. **核磁盘**：运行 `git status -s` 与对应单测，排查是否已发生「代码落盘但状态未更新（Silent Landing）」；
4. **定续跑**：已落盘且测试全绿则补勾 `- [x]` 后推进下一项；部分落盘或测试失败则从该断点续跑，并向用户简明汇报恢复位置。

---

## 5. Active Checkpoint 标准模板

所有 `goal-loop` 计划头部必须保留统一检查点块，由主调度智能体直接精准编辑维护：

```markdown
## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: [Heavy Track | Fast-Track | Maintenance-Patch]
- **当前活跃阶段**: [Align | Plan | Execute | Verify | Close | DONE]
- **当前活跃子任务**: [无 | Task E-1 - 描述]
- **当前子任务重试计数**: [0/3；第 2 次触发微观调研，第 3 次熔断]
- **外层 Delta Re-Loop**: [0/5]
- **最后一次验证状态**: [无 | Exit Code 0, 简要结果]
- **最新有效提交**: [无 | Commit SHA]
- **在途派发摘要**: [无 | 句柄/基线，明细见 .goal-loop/dispatch-ledger.md]
- **阻断原因**: [无 | 具体原因与 parked 项]
```

---

## 6. 批次同步抗膨胀原则 (Batched Sync)

- **子任务级**：仅精准编辑对应复选框（`- [ ]` ➔ `- [x]`）与 `Active Checkpoint`；
- **阶段级**：阶段验收通过后，集中同步里程碑进度与计划 Context Log，杜绝逐行碎屑追加；
- **临时态隔离**：高频派发账本、草稿与交接简报全部落盘 `.goal-loop/`，结项后按需清理。
