---
name: taste-driven-designer
description: Use when the user wants to design or redesign any UI/UX artifact — landing pages, web apps, mobile interfaces, game UIs, or dashboards — and expects distinctive, tasteful results instead of generic AI slop. Also use when asked to give a design a personality or art direction, make it look premium/unique/not AI-generated, critique an existing interface, or give a frontend build direction. Triggers on landing page, hero section, design language, moodboard, art direction, UI polish, taste.
---

# taste-driven-designer 品味驱动设计

## 概述

将 AI 从"统计平庸的默认设计器"升级为"世界级设计师"的三阶段流程技能。理论基准：[《How to Turn Your AI into a World-Class Designer》](../../docs/reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md)（Anshu Chimala 的 AI 双钻模型，前 Apple AI 原型团队 12 年负责人）。

**黄金公式**：

$$\text{World-Class AI Design} = \text{外部随机种子} + \text{独立 Critic 闭环} + \text{多模态增强} + \text{残酷减法}$$

本文件是**路由层**：只声明触发条件、铁律与阶段指针，阶段细则见 `references/`。

---

## 何时使用 / 何时不用

**使用**（满足任一）：
- 用户要求设计/重设计落地页、Web 应用、移动界面、游戏 UI、仪表盘等界面产物；
- 用户明确要求"有设计感 / 有品味 / 不像 AI 生成的 / 独特一点 / 高级感 / 给出艺术方向"；
- 既有界面需要"设计批评 / 视觉 vibe-check / 打磨"；
- 前端构建需要超出纯功能布局的创意方向。

**不用**：纯功能改动且无视觉诉求、后端/数据逻辑任务、用户明确要求"就按默认模板来"。

---

## 铁律 (Invariants)

1. **随机性必须来自模型外部**：任何设计开工前先跑种子字符串规程（`scripts/generate-seed.sh`）；"随机一点 / 独特一点"等口头指令不算数——模型只会预测"听起来随机"的 Token。
2. **Critic 分离纪律**：Critic 每次以**全新上下文** + **固定提示词** + **只收当前产物**（截图，无则降级）介入；不得携带实现代码、历史迭代与前次批评。
3. **收敛门禁**：仅当 Critic 独立评分 **≥ 9/10** 才算完成；达标线只存在于主智能体侧，**严禁写入 Critic 提示词**（保持评分客观）。
4. **预算有上限**：先跑 1~2 轮验证可收敛性；全流程迭代上限 5 轮，超限熔断向用户汇报。
5. **减法优先**：Deliver 阶段先删除后增补——删不掉价值说明的元素（装饰渐变/多余卡片/装饰标签）一律移除；AI Tells 审计必须逐项过清单（`references/ai-tells-audit.md`）。
6. **文案是占位符**：AI 生成的文案一律视为排版 Lorem ipsum，交付前必须重写为具体、克制、口语化的人类语言（黑名单词表见 `references/ai-tells-audit.md`）。
7. **能力门控**：截图/图像/视频能力按宿主实际可用性启用；缺截图则走降级评审，禁止假装看见了截图。
8. **人类是创意总监**：方向选择、品味标杆与取舍裁决归用户；智能体负责提供速度、广度与执行。
9. **参考是锚点不是拷贝**：moodboard/参考图只用于校准质量基线，禁止照抄。
10. **事实即刻落盘**：方向决策与删除清单写入设计简报，避免上下文腐化。

---

## 阶段路由 (Phase Routing)

| 阶段 | 目标 | 核心技法 | 产物 / 指针 |
|:---:|---|---|---|
| **D1 Discover** | 打散统计平庸，发散探索 | 种子字符串注入随机性 + 雄心跨界 Prompt | 设计简报（`templates/design-brief-template.md`）；细则见 [discover-phase.md](references/discover-phase.md) |
| **D2 Define** | 注入品味与个性，逼近世界级执行水准 | 独立 Critic 闭环 + （可选）图像/视频增强 | Critic 往返记录 + 评分轨迹；细则见 [critic-loop-protocol.md](references/critic-loop-protocol.md)、[multimodal-enrichment.md](references/multimodal-enrichment.md) |
| **D3 Deliver** | 收敛与减法，剔除 AI 痕迹 | 残酷减法 + AI Tells 审计 + 文案重写 | AI Tells 审计清单 + 删除记录；细则见 [ai-tells-audit.md](references/ai-tells-audit.md) |

**阶段纪律**：D1 未产出多方向简报不得进入 D2；D2 未取得 ≥9/10 不得进入 D3；D3 审计未逐项过清单不得宣称交付。

---

## 快速流程清单 (Quick Checklist)

```text
D1  ┌ generate-seed.sh 生成种子 → 提取子模式 → 定义创意方向（配色/布局/字体/质感）
    ├ 多方向并行：产出 2~4 个 Brief（必要时派发子智能体分别执行）
    └ 与用户对齐方向，选定 1 个（兼修时取 2 个）
D2  ┌ 实现初版 → 捕获产物（截图 / 降级文本）
    ├ 派发 Critic（全新上下文 + 固定提示词 + 只看产物）→ 记分
    ├ 评分 ≥9/10？→ 是则放行；否则按批评精准修复 → 再派发（上限 5 轮）
    └ 可选增强：图像资产 / 视频动效（能力门控，见 multimodal-enrichment.md）
D3  ┌ 逐项过 AI Tells 审计清单（7 反模式 + 减法 + 文案黑名单）
    ├ 删除无价值元素 → 重写全部文案 → 人工复核方向一致
    └ 交付并说明：方向来源、Critic 终分、删除了什么
```

---

## 降级与预算 (Fallbacks & Budgets)

| 场景 | 处置 |
|---|---|
| 宿主无截图能力 | 走降级评审：向 Critic 提供结构化产物摘要（语义树 + 视觉参数 + 关键区段），见 [critic-loop-protocol.md](references/critic-loop-protocol.md) §4 |
| 宿主无图像/视频生成 | 跳过增强层，用代码级质感（着色器/CSS 纹理）替代，见 [multimodal-enrichment.md](references/multimodal-enrichment.md) §4 门控矩阵 |
| Critic 连续 ≥3 轮评分不涨 | 熔断：停止空转，向用户展示评分轨迹与已尝试修复，请求方向裁决 |
| 总迭代超 5 轮 | 熔断：汇报当前最佳状态与差距清单，请用户决定是否继续 |

---

## 辅助脚本（可选）

`scripts/generate-seed.sh` 为 Discover 阶段注入外部随机性（String Seed of Thought）：

```bash
SKILL_DIR="<taste-driven-designer 技能实际所在目录>"
bash "$SKILL_DIR/scripts/generate-seed.sh"            # 64 位真随机种子
bash "$SKILL_DIR/scripts/generate-seed.sh" -l 128 -c 3  # 3 条种子并行探索
bash "$SKILL_DIR/scripts/generate-seed.sh" -s team-2026 -l 48  # 团队可复现
```

完整施工步骤与灵感提取 Prompt 见 [seed-string-procedure.md](templates/seed-string-procedure.md)。

---

## 参考导航

- [discover-phase.md](references/discover-phase.md) — D1 种子字符串规程与雄心 Prompt 三步入炉法
- [critic-loop-protocol.md](references/critic-loop-protocol.md) — D2 闭环结构、降级评审、评分量规与收敛控制
- [ai-tells-audit.md](references/ai-tells-audit.md) — D3 7 大反模式清单、减法规则与文案黑名单
- [multimodal-enrichment.md](references/multimodal-enrichment.md) — 可选增强层与能力门控矩阵
- 模板套件：`templates/` 下设计简报、Critic 固定提示词、种子施工三步模板
