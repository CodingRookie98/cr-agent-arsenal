# D1 Discover — 发散探索细则

> 阶段目标：打散 LLM 的"统计平庸"默认（紫渐变 + 左文右图 Hero + Bento 卡片 + 营销空话），把创意空间从"平均值附近"扩展到"可能性边缘"。
>
> 阶段纪律：**随机性必须来自模型外部**。模型只能预测"听起来随机"的 Token——所有"随机一点 / 独特一点"类口头指令都无效。本阶段的两把钥匙：**种子字符串（外部熵）** 与 **雄心跨界 Prompt（品味注入）**。

---

## 1. 种子字符串注入随机性 (String Seed of Thought)

理论出处：Sakana AI 公开论文 *String Seed of Thought*（<https://pub.sakana.ai/ssot/>）。核心：用一段**模型无法预测**的随机字符串充当创意方向的唯一灵感源，使每次运行都产生不同的、一次性的设计决策。

### 1.1 施工步骤（完整规程）

1. **生成种子**：`bash ${SKILL_DIR}/scripts/generate-seed.sh`（默认 64 位 base62 真随机；多方向并行用 `-l 128 -c 3`；团队复现用 `-s <种子词>`）。完整 Prompt 模板见 [seed-string-procedure.md](../templates/seed-string-procedure.md)。
2. **提取子模式**：要求模型在种子串里"看"出可用的灵感——子模式、特殊数字、字母形状、奇偶分布、分段节奏等，越过表面寻找暗示。
3. **定义创意方向**：基于提取的暗示定义完整方向：配色 / 布局 / 字体 / 质感 / 交互氛围。
4. **落地执行**：把方向写进设计简报（[design-brief-template.md](../templates/design-brief-template.md)）并实现。
5. **不泄露种子**：种子只做灵感源，禁止出现在设计成品与任何可见文案中。

### 1.2 反模式：为什么"随机指令"无效

| 指令 | 结果 |
|---|---|
| "Give me something totally unique. Make every design decision completely at random." | 输出不同了，但**不多样**——同一配色、同一结构、甚至同一个别扭的陶器比喻。模型在预测"听起来随机"的 Token |
| "换个风格试试" | 换汤不换药，回到另一个训练高频范式 |

只有把熵源放到**模型外部**，多样性才是真的。

### 1.3 多方向并行探索

默认单方向直接落地宿敌是"第一版即终版"。本技能要求：

- 单次生成 **2~4 条种子**（`-c 3`），分别产出 2~4 个方向简报；
- 有余力时**派发子智能体并行执行**每个方向的初版，产物并排比较；
- 与用户（创意总监）对齐后选定 1 个方向深化；最多保留 2 个方向并行打磨。

---

## 2. 雄心 Prompt：跨界注入品味 (Ambitious Prompts)

LLM 默认的设计决策是"最可能取悦所有人"的安全选择；突破它的方式是**由人类先给出独特愿景**，再让模型执行。这要求人类（或人机协作打磨）先有一个"离谱"的灵感。

### 2.1 三步入炉法（用于生成雄心 Prompt 本身）

AI 可以帮你找灵感，但**直接问它要创意，得到的仍是平均创意**。正确流程：

**第 1 步：宽列不深挖**——让 AI 列出大量高概念方向，只要一句话描述：

```text
I want to come up with a bold, unique design language for my product.
Can you list as many ideas as you can, with short, high-level descriptions?
Go broad, not deep.
```

**第 2 步：视觉化 + 表达直觉反应**——挑出让你"起反应"的方向，明确写下喜欢什么、嫌弃什么（"太卡通 = tacky，避开"、"灰渐变无聊，要质感"），再让 AI 按你的口味精修：

```text
Industrial Control Panel:
- I'm imagining something tactile. Clicky, satisfying buttons, nice sounds.
- Initially I pictured something cartoony or skeuomorphic, but this feels tacky to me. Avoid that.
- Instead, want consistent components and little touches that land this look without going overboard.
- Gray gradients would look boring. Need more texture. Maybe we can incorporate some color,
  while retaining the control panel feel?
Can you sharpen this one based on my tastes?
```

**第 3 步：收敛成可执行 Prompt**——满意后让 AI 把方向压缩成"智能体可直接开工"的简短指令。

### 2.2 雄心 Prompt 示例库（可直接改写复用）

- 像素游戏风："Build me a landing page for my productivity app, with a bold pixel art theme and stunning graphics. Each section should feel like a still from a video game, yet somehow it should all function as a landing page."
- 等距 3D 都市："Build me a landing page … set in an isometric living 3D city, where different features are somehow represented by neighborhoods or buildings."
- 激进破格："Build me a landing page … with a radically asymmetric layout, dissonant colors and typography, and uncomfortable negative space. Break all the rules but still make it look good."
- 电控台 / 仪器面板 / 地质层 / 星图 / 档案室 / 打字机年代……（从第 2.1 节流程生成你自己的）

### 2.3 大胆试错心态

> "Don't be afraid to try ideas that sound terrible. If you find yourself thinking, 'There's no way this will work,' you're on the right track."

当方向"听起来一定完蛋"时，反而值得跑一次——agent 经常会给你惊喜。

---

## 3. D1 出口检查清单

- [ ] 种子串已生成且**未被模型自选**（外部熵，`generate-seed.sh` 产出）
- [ ] 至少 2 个方向简报（多方向并行；每份含配色/布局/字体/质感四个决策域）
- [ ] 用户（创意总监）已选定方向或明确兼修策略
- [ ] 未在任何可见位置泄露种子串
- [ ] 设计简报已落盘（暂存或 `templates/design-brief-template.md`）
