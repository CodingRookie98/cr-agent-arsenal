# 多模态增强层 (Multimodal Enrichment) — 能力门控细则

> 定位：本层是**可选增强**，不是必经之路。它在宿主能力允许时显著拉高视觉上限；缺能力时直接跳过，不得卡死流程。
> 纪律：**按宿主实际能力启用**；API Key 只允许本地使用，严禁写入代码与产品。

---

## 1. 为什么需要多模态资产

编码智能体天然爱写代码、不爱放图：它们默认用渐变、形状、基础图案这些"代码就能实现"的替代品——而这恰恰是 AI 生成设计的**最强泄漏信号**。一张真正的图像资产（玻璃折射、3D 渲染、摄影贴图）能立刻把界面从"模板感"拉升到"定制感"。

---

## 2. 增强项 1：图像生成 (Image Generation)

**使用时机**：D2 中 Critic 点名"视觉太平 / 缺少质感 / 太代码化"时；Hero 背景、产品视觉、装饰纹理缺真实资产时。

**接入方式**（按宿主能力递进）：
1. 宿主内建图像工具（如 Antigravity / Codex / Grok Build 的 build-in generator）→ 显式指示 agent 使用它；
2. 无内建工具 → 通过 OpenAI / Gemini API 以 API Key 调用（**只用于本地，不存进代码或产品**；Claude Code / Cursor 可用 `.env.agents` 配置 CLI 图像工具）；
3. 都无 → 跳过，启用代码级质感替代（§4）。

**实用示例**（Prompt 骨架）：

```text
The design is pretty plain. Add more personality using image generation.
Consider shaders or 3D effects in combination with images to create more interesting visuals.
Verify that your work looks right frame-by-frame in the browser.
```

**落地建议**：
- 玻璃折射/3D 资产：让图像模型渲染**纯背景色底 + 物件**，便于前端直接合成与去底；
- 产物必须回浏览器逐帧目检，确认与版式、缩放、间距真实融合，而不是"贴了张图"。

---

## 3. 增强项 2：视频生成与动效 (Video Generation & Motion)

模型：Runway / Luma / Kling / Seedance（聚合器如 fal.ai 可一站接入）。

**两个高价值用例**：

1. **带背景抠除的循环动画资产**：
   - 对纯背景色渲染一段循环 3D/玻璃折射片段；
   - 用视频抠像（matting）去掉背景，得到自带真实光学折射/焦散/阴影的干净 Web 资产；
2. **关键帧插值转场**：
   - 不用手写复杂 CSS/GSAP 过渡；生成**起始关键帧**与**结束关键帧**，让视频模型插值补间；
   - 把生成片段绑到用户交互上（滚动逐帧 scrub / 页面转场触发）。

**工程注意**：视频资产要管控体积与加载策略（循环片段 ≤ 数秒、提供降级静态帧），避免拖垮首屏。

---

## 4. 能力门控矩阵 (Capability Gating Matrix)

| 宿主能力 | 处置 |
|---|---|
| 有截图能力 | D2 走真截图 Critic 评审（最优）；D3 交付前补终审截图 |
| 无截图能力 | 降级为结构化摘要评审（见 [critic-loop-protocol.md](critic-loop-protocol.md) §8） |
| 有图像生成 | 启用增强项 1；API Key 仅本地、不入库 |
| 无图像生成 | 用 CSS 渐变/噪点纹理/着色器（如 WebGL shader）做"代码级质感"替代，避免干瘪纯色 |
| 有视频生成 | 启用增强项 2（循环资产 + 关键帧插值）；注意体积与降级帧 |
| 无视频生成 | 跳过动效增强；用 CSS transitions / 滚动驱动动画保持交互品质 |

**门控总原则**：能力有 → 用；能力无 → 降级或跳过，**永远不假装**有截图、有图像、有视频。

---

## 5. 安全与合规红线

- API Key：仅本地环境变量/CLI 配置；严禁写入源代码、配置文件、产品与环境提交；
- 参考图/moodboard：只做质量锚点，禁止照抄（与 Critic 基准确认共用同一批参考时明确"锚点非拷贝"语义）；
- 生成资产：检查许可与品牌合规；视频/图像产出记录来源，便于最终交付说明。
