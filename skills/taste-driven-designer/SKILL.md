---
name: taste-driven-designer
description: "Use when designing or redesigning landing pages, web apps, mobile/game UI, or dashboards requiring distinctive taste over generic AI slop. Also use for visual direction, design critique, or UI polish. Triggers on landing page, hero section, art direction, UI polish, taste, surface mode."
license: MIT
---

# taste-driven-designer 品味驱动设计

理论基准：Anshu Chimala，《How to Turn Your AI into a World-Class Designer》。

$$\text{World-Class AI Design} = \text{外部随机种子} + \text{独立 Critic 闭环} + \text{多模态增强} + \text{残酷减法}$$

**职责边界**：本技能管视觉品味、表面模式（`Persuade` / `Operate`）、AI Tells 与减法；五域运行时验收由 `` `frontend-qa-gate` `` 独立承担，不复制其矩阵。

## 何时使用 / 何时不用

- **使用**：设计/重设计落地页、Web/移动/游戏 UI 或仪表盘；要求有品味/破除 AI 感/定艺术方向；设计批评或打磨。
- **不用**：纯功能或后端逻辑；用户明确要求用默认模板。

## 核心铁律

1. **外部随机熵**：开工必跑 `scripts/generate-seed.py` 注入外部种子；口头“随机”无效。
2. **Critic 产物隔离**：每次全新上下文 + 固定模板 + 只看产物（盲比附去标识、随机左右的上一版）；禁传代码、历史与前次批评。
3. **三信号收敛门禁**：D2 须同时满足 **Gate A 视觉结构清单** + **Gate B 盲比改进 / 4+1 排序**（禁绝绝对分数作判据；遥测须锚点+双 Critic 中位数且永不入门禁）+ **Gate C 人类签收**。未达报 `blocked`。
4. **5 轮硬上限**：先跑 1–2 轮验信号；D2 上限 **5 轮**（记 5 列评审表），连续 2 轮无改进熔断。
5. **减法优先**：Deliver 先删后补，删掉无必要价值的元素，过 10 项 AI Tells 清单。
6. **文案占位符**：AI 文案视作 `Lorem ipsum`，交付前重写为具体口语人类语言并清零黑名单。
7. **能力门控**：截图/生图/视频按宿主能力启用或降级，绝不假装具备能力。
8. **人类创意总监**：模式取舍、品味锚点（禁照抄）、原则仲裁与签收归用户；决策即刻落盘。

## 三阶段路由

| 阶段 | 核心动作 | 细则与模板 |
|:---:|---|---|
| **D1 Discover** | 定 `Persuade`/`Operate`，外部种子产 2–4 份简报 + 雄心 Prompt 选 1 | [discover-phase.md](references/discover-phase.md)、[design-brief-template.md](templates/design-brief-template.md) |
| **D2 Define** | 独立 Critic 闭环（盲比 / 4+1 排序）+ 可选多模态 + 三信号门禁 | [critic-loop-protocol.md](references/critic-loop-protocol.md)、[critic-prompt-template.md](templates/critic-prompt-template.md) |
| **D3 Deliver** | 残酷减法 + 10 项 AI Tells 审计 + 文案重写，移交 `` `frontend-qa-gate` `` | [ai-tells-audit.md](references/ai-tells-audit.md) |

## 降级与熔断

| 场景 | 处置 |
|---|---|
| 无截图 / 生图 / 视频 | 降级结构化摘要评审，或以 CSS/shader/过渡替代（API Key 仅本地不入库） |
| 盲比连续 2 轮无改进 / 达 5 轮上限 | 熔断停转，展示 5 列评审表与差距交用户裁决 |
| 鉴别力失效 / 连续 2 轮空白作废 | 停转升级人工（输出逐字同或管线连续空白即故障） |
| 建议与已决原则冲突或反转 | 原则优先并冻结冲突维度，记台账交用户仲裁 |
| 门禁未达或 `` `frontend-qa-gate` `` 未过 | 报 `blocked` 或回流修复，**严禁宣称交付完成** |

## 辅助脚本

```bash
SKILL_DIR="<taste-driven-designer 技能目录>"
python3 "$SKILL_DIR/scripts/generate-seed.py"              # 64 位真随机 base62
python3 "$SKILL_DIR/scripts/generate-seed.py" -l 128 -c 3  # 3 条 128 位种子并行
python3 "$SKILL_DIR/scripts/generate-seed.py" -s team-2026 # 团队可复现模式
```
