# How to Turn Your AI into a World-Class Designer

> **文档控制信息 (Document Control Info)**
> - **文档标识**: REF-ART-AI-DESIGNER-2026
> - **当前版本**: V1.0.0
> - **作者**: Anshu Chimala (前 Apple 软件工程与 AI 产品设计原型团队负责人，负责未来 AI 产品研发与原型设计 12 年)
> - **来源**: [Lenny's Newsletter](https://www.lennysnewsletter.com/p/how-to-turn-your-ai-into-a-world)
> - **发布日期**: 2026-09-01
> - **生效日期**: 2026-09-01
> - **归档分类**: Reference / External Articles (外部前沿方法论引用)
> - **目的**: 本文作为后续研发高质量 AI UI/UX 设计技能（如 `taste-driven-designer` / `ai-world-class-designer`）的理论与工程实操基准。

---

## 目录 (Table of Contents)

1. [核心架构与技能转化提炼 (Executive Summary & Skill Blueprint)](#1-核心架构与技能转化提炼-executive-summary-skill-blueprint)
2. [文章完整内容 (Complete Article)](#2-文章完整内容-complete-article)
   - [Introduction & Background](#introduction-background)
   - [Why AI Struggles with Design by Default](#why-ai-struggles-with-design-by-default)
   - [The Reimagined Double Diamond for AI](#the-reimagined-double-diamond-for-ai)
   - [Phase 1: Discover (打破统计平庸，发散探索)](#phase-1-discover)
     - [Technique 1: Use seed strings to inject variety](#technique-1-use-seed-strings-to-inject-variety)
     - [Technique 2: Be much more ambitious with your prompts](#technique-2-be-much-more-ambitious-with-your-prompts)
   - [Phase 2: Define (注入品味与个性，多智能体链式生成)](#phase-2-define)
     - [Technique 3: Create positive feedback loops with subagents](#technique-3-create-positive-feedback-loops-with-subagents)
     - [Technique 4: Use image generation to enrich designs](#technique-4-use-image-generation-to-enrich-designs)
     - [Technique 5: For more advanced motion, use video generation](#technique-5-for-more-advanced-motion-use-video-generation)
   - [Phase 3: Deliver (收敛与减法，剔除 AI 痕迹)](#phase-3-deliver)
     - [Technique 6: Cut out elements that don’t add value](#technique-6-cut-out-elements-that-dont-add-value)
     - [Technique 7: Remove AI tells](#technique-7-remove-ai-tells)
     - [Technique 8: Rewrite copy by hand](#technique-8-rewrite-copy-by-hand)
   - [Summary & Takeaways](#summary-takeaways)
3. [AI 设计反模式与审查提示词速查表 (Anti-Patterns & Prompts Cheatsheet)](#3-ai-设计反模式与审查提示词速查表-anti-patterns-prompts-cheatsheet)

---

## 1. 核心架构与技能转化提炼 (Executive Summary & Skill Blueprint)

### 为什么 AI 默认生成的全是「设计垃圾（AI Slop）」？
- **第一性原理**: LLM 是基于海量数据训练的「Next-Token Predictor」，配合 RLHF（人类反馈强化学习），导致模型在做设计决策（颜色搭配、组件布局、文案撰写）时，默认倾向于选择**最符合大众平均审美的安全 Token**。
- **结果**: 导致千篇一律的「紫色渐变、左文右图 Hero、圆角卡片 Bento Grid、空洞营销空话」。
- **突破口**: 顶级设计源于情感、品味与出人意料的克制选择。AI 不缺创造力，但需要人类在工作流中为其注入**外部随机性/灵感源（Entropy）**、**分离式评审（Critic Subagent）**与**极度严苛的减法剪裁（Ruthless Pruning）**。

### AI 设计双钻模型（Double Diamond for AI Agents）

```mermaid
flowchart LR
    subgraph Phase1["1. Discover (发散探索)"]
        direction TB
        T1["Technique 1: 种子字符串注入随机性 (Seed Strings)"]
        T2["Technique 2: 极致雄心与特定跨界提示 (Ambitious Prompts)"]
    end

    subgraph Phase2["2. Define (个性塑形)"]
        direction TB
        T3["Technique 3: 独立审稿智能体反馈闭环 (Critic Subagent Loop)"]
        T4["Technique 4: 注入图像与着色器特效 (Multimodal Images/Shaders)"]
        T5["Technique 5: 视频模型实现物理动效与转场 (Keyframe Video Transitions)"]
    end

    subgraph Phase3["3. Deliver (收敛落地)"]
        direction TB
        T6["Technique 6: 极简减法，剔除无价值装饰 (Ruthless Subtraction)"]
        T7["Technique 7: 抹除 AI 典型陈词滥调 (Strip AI Tells)"]
        T8["Technique 8: 人工重写真实文案 (Human Copywriting)"]
    end

    Phase1 --> Phase2 --> Phase3
```

---

## 2. 文章完整内容 (Complete Article)

### Introduction & Background

> **By Lenny Rachitsky & Anshu Chimala**

I’d always thought AI was bad at design. But after reading this mind-blowing post by [Anshu Chimala](https://www.linkedin.com/in/achimala/), I realize I was just doing it wrong. Anshu led software engineering and design teams at Apple for 12 years, focusing on research and prototyping for future AI products. He regularly shares design tutorials and demos on [X](https://x.com/anshuc) (he’s one of my favorite follows).

Let’s get into it.

- A conversational calorie tracker, built in three prompts with Claude Fable 5
- A space exploration game, built in two prompts with Claude Opus 5
- A dynamic landing page, built in three prompts with Claude Opus 5 + GPT-5.6 Sol

I often post AI design demos like these on X. Every time I do, someone inevitably asks:
> *"Why does the model create all this incredible stuff for you, but when I try, I only get generic slop? It’s like you’re using a completely different model."*

I’m not using a different model, but I am getting more out of the models I work with. Most people only see 1% of AI’s creative potential. I want to show you how to tap into the other 99%.

---

### Why AI Struggles with Design by Default

AI models are capable of amazing creativity, but that creativity gets stifled by how they’re trained. Large language models are next-token predictors: at each step, they look at a sequence of text and predict what comes next based on millions of examples. The results may be rated by humans, and those ratings fed back into the model. This teaches the model to make consistent, safe choices that fit everyone’s preferences.

This makes typical LLMs great at most tasks but poor designers. To create a design, an LLM has to build it out token by token. Whenever it needs to make a design decision—what colors to use, or how to arrange elements—the model fills in the tokens it thinks are most likely to please everyone. As a result, the design usually ends up being repetitive and bland. It’s like the ultimate case of design-by-committee.

Great design, on the other hand, starts with feeling and aims to create an emotional response. It bends the rules and delights users with memorable, unexpected choices. Great design is exactly the opposite of what an LLM does naturally, which is to make the most predictable choice at every step.

However, if we can get the model to reach beyond the most predictable choices, we can access a vast landscape of creative ideas that most people miss out on.

This is a lesson I learned from managing human designers, before I was managing AI ones. For most of my career at Apple, I led an R&D team designing exploratory future AI products. Early on, our preconceived notions about how user interfaces should work limited our creativity and kept us returning to the same old ideas. Through rigor and new processes, we learned to stop re-creating what’s comfortable and instead look to the fringes of what’s possible, to generate something new. We became experts at polishing the little details to an Apple level of quality.

Since my time at Apple, I’ve been working on applying that same process to my work with AI. In the past couple years, AI agents have become extremely capable. They can do in hours what used to take my team weeks. And with the right guidance, they can create designs that look completely unlike anything else.

---

### The Reimagined Double Diamond for AI

Loosely inspired by the [Double Diamond design process](https://en.wikipedia.org/wiki/Double_Diamond_(design_process_model)), I’ve reimagined the design process for a team of AI agents instead of human designers:

1. **Discover** new ideas beyond the average slop by exploring a variety of directions and creating bold, ambitious design briefs.
2. **Define** an individual design identity by pushing AI beyond its familiar patterns and chaining models together to fully realize the design’s potential.
3. **Deliver** a stunning final result by polishing away the sloppy rough edges and focusing on the key elements.

By following these stages and applying the techniques within each one, you can create an incredible design remarkably quickly—and make people ask, *“Why does AI create magic for you (and not me)?”*

---

### Phase 1: Discover

The hardest part of the design process is looking at a blank screen with infinite possibilities. The best way to tackle that moment is to start by going broad before going deep. AI is an excellent tool to explore a wide variety of potential directions.

As we know, though, models tend to overrely on familiar patterns and make conservative choices. To explore the full potential design space, we want to coax a model to do the opposite: be bold, be varied, and take risks. Below are two ways to push it out of its comfort zone.

#### Technique 1: Use seed strings to inject variety

The idea here is to get the model to find a new source of inspiration for designs, rather than relying on the defaults it learned from training. If you’ve tried to prompt a model to design a website or app, you’ve probably already seen what that default looks like.

As a simple example, I gave four instances of Claude Code the same prompt:
```text
Prompt:
Build me a landing page for my productivity app.
```
Almost every time, we get a purplish gradient, text on the left, graphic on the right, and the exact same structure. It looks like every AI-designed website ever.

We didn’t ask the model to do anything unique or varied, so it makes sense that it keeps falling back on the same patterns it knows well. But just asking for variety doesn’t work:
```text
Prompt:
Build me a landing page for my productivity app. Give me something totally unique. Make every design decision completely at random.
```
The results are different from before, but they’re still not varied. The model always uses the same color scheme, structure, and even the same awkward pottery metaphors. It’s predicting tokens that sound random but aren’t actually random.

The problem is that the model can’t inherently act randomly. It can only predict the most likely token. If we want variety, we have to bring it from outside the model. One technique for this is **String Seed of Thought**, published by Sakana AI (https://pub.sakana.ai/ssot/). We make the AI generate a random string and use it as design inspiration. That way, the model is truly making different decisions each time.

```text
Prompt:
I want you to build me a landing page for my productivity app.
Follow this procedure:
1. Generate a long, random alphanumeric string using a shell script.
2. Define the creative direction (color scheme, layout, typography, etc.) based on the string. Look beyond the surface for subpatterns, special numbers, anything that inspires you.
3. Use your judgment to bring this direction to life and make it look great.
Don’t reveal the string in the design. It’s only for your inspiration.
```

Suddenly the outputs are much more varied! Now we’re seeing different color schemes, fonts, and new ideas. The previous designs were ones that any Claude user could get. These designs are one-of-a-kind; no two runs ever produce the same result.

#### Technique 2: Be much more ambitious with your prompts

Another approach to giving a model a strong push is to get more specific and wild with your prompts. This gives the model a clear vision to base its decisions on, rather than letting it make them up on the fly. The best way to find a unique idea is by bringing your own taste into the equation. You first imagine the inspiration—a video game, an interior design trend, an art installation—and describe how you’d like that inspiration to influence the AI’s outputs. Here are some examples:

- *“Build me a landing page for my productivity app, with a bold pixel art theme and stunning graphics. Each section should feel like a still from a video game, yet somehow it should all function as a landing page.”*
- *“Build me a landing page for my productivity app, set in an isometric living 3D city, where different features are somehow represented by neighborhoods or buildings.”*
- *“Build me a landing page for my productivity app, with a radically asymmetric layout, dissonant colors and typography, and uncomfortable negative space. Break all the rules but still make it look good.”*

Of course, the hard part is coming up with original ideas to ask for. AI can help with this too, but if you simply ask it for ideas, you’ll get the same average ones everyone else gets. Here’s a system I use to find unique prompt ideas with AI:

##### 1. Ask AI to list a bunch of ideas, intentionally lacking detail
The goal is just to inspire your imagination:
```text
I want to come up with a bold, unique design language for my product. Can you list as many ideas as you can, with short, high-level descriptions? Go broad, not deep.
```

##### 2. Visualize your favorites and note how you react to different directions. Then ask AI to refine them
```text
Industrial Control Panel:
- I’m imagining something tactile. Clicky, satisfying buttons, nice sounds.
- Initially I pictured something cartoony or skeuomorphic, but this feels tacky to me. Avoid that.
- Instead, want consistent components and little touches that land this look without going overboard.
- Gray gradients would look boring. Need more texture. Maybe we can incorporate some color, while retaining the control panel feel?
Can you sharpen this one based on my tastes?
```

##### 3. Iterate until you’re satisfied, then ask AI to write the prompt to build it
```text
Can you write a concise prompt that an AI agent could use to build an initial POC page with this?
```

If you just paste AI-generated ideas back into AI, it’s hard to get something unique. After all, anyone else could have done the same thing. However, when you actively steer the design direction, you end up with something only you could have created.

Don’t be afraid to try ideas that sound terrible. If you find yourself thinking, “There’s no way this will work,” you’re on the right track. Often, your agent will surprise you, and you’ll realize you were underestimating it.

---

### Phase 2: Define

So far, we’ve looked at how to explore a broad set of ideas and hopefully land on a promising initial design. No matter how we prompt, though, our initial AI-generated designs will usually still feel generic.

For example, look at the designs we came up with using seed strings: these have promise, but they’re still relying heavily on the same stale patterns: text on the left with a CTA button below, nav bar up top, graphic on the right.

Our next goal is to give each design an individual personality through distinct design choices. Below are my favorite techniques to do that.

#### Technique 3: Create positive feedback loops with subagents

We need to iterate on our designs to improve them. But simply asking our agent to look at the design and improve it won’t work, because the agent isn’t objective: it reviews its own code, past decisions, and previous rationale. AI can’t easily zoom out, look at the big picture, and “think different.”

To solve this, instead of letting the coding agent decide when the design is good enough, have it ask another agent—a **“design critic.”** The critic’s job is to look at screenshots of the current design and provide feedback. It doesn’t care how the current design is implemented or how much effort went into it, only if it actually hits the quality bar.

This approach has an extra benefit: we can use a big, expensive model for the critic without breaking the bank, because we’ll only use it for executive decisions. A cheap, fast model can do the grunt work, while the strong critic model provides taste.

```text
Prompt:
I want you to improve this design. To figure out what to focus on, use a Claude Fable 5 subagent as a design critic.
Follow this procedure at each iteration:
- Capture a screenshot of the current design.
- Invoke the critic in a fresh context, with just the screenshot, not the code, implementation details, or earlier iterations/critiques.
- Ask it to evaluate the aesthetic that the design is going for, imagine how a top design studio would execute this aesthetic, then outline the biggest gaps.
- Lastly, it should provide a score out of 10 indicating how close the current design is to that studio-level quality bar.

Provide this guidance to the critic in its prompt:
- It should think high-level about the overall structure and composition as well as look at the fine details.
- It should watch out for patterns that feel overdone, excessive, or otherwise obviously AI-generated, and penalize them.
- It should provide tight, specific feedback, not vague prose.
- It should be bold and opinionated, not rely on what’s safe or easy.

Your work is only complete when the critic independently deems it 9/10 or higher. Do not put that criterion in the critic prompt; keep it objective in its scoring. Use the same critic prompt each time.
```

The way you set these loops up matters a lot. Here are key tips:
- **Make criteria concrete and objective:**
  - *Bad*: “Judge if our design looks beautiful, not AI-generated.” (Too subjective, high variance)
  - *OK*: “Review the aesthetic we’re going for, visualize how a top design studio would execute it, then judge our design’s quality against that bar.” (Consistent framework, but still slightly mushy)
  - *Great*: “Here are 5 designs: 4 professional examples and 1 screenshot of our product. Rank them by polish and taste level.” (Concrete, comparative baseline)
- **Provide moodboards / baselines:** Feed reference screenshots or AI concept art as quality anchors (as reference/moodboard, never to copy outright).
- **Control stopping criteria:** Start with 1-2 iterations to check convergence, avoiding endless token-burning loops.
- **Role separation:** Strong reasoning/vision model as Critic; fast/cheap model as Code Implementer.

#### Technique 4: Use image generation to enrich designs

Coding agents love to write code, but they usually don’t incorporate images. Instead, they tend to use the easy code-based alternatives: gradients, shapes, and basic patterns. Those are all strong giveaways of an AI-generated design.

Some agents have image tools built in, but they underutilize them. Others don’t have image tools out of the box but can easily use the OpenAI or Gemini APIs to generate images with an API key.

```text
Prompt:
The design is pretty plain. Add more personality using image generation. Consider shaders or 3D effects in combination with images to create more interesting visuals.
For image generation, use this API key (only use it locally, do not store it in the code or product): sk-...
Verify that your work looks right frame-by-frame in the browser.
```

- If using Antigravity, Codex, or Grok Build: Explicitly instruct the agent to use its built-in image generator tool.
- If using Claude Code / Cursor: Pass an API key or configure CLI image tools locally via `.env.agents`.

#### Technique 5: For more advanced motion, use video generation

Video generation models (Runway, Luma, Kling, Seedance) can do wonders for everyday design when used via aggregators like fal.ai.

Two killer use-cases:
1. **Stunning animated graphics with background matting:**
   - Render a looping 3D/glass refraction clip against the background color.
   - Use video matting to remove the background, leaving real optical refraction, caustics, and shadows baked into a clean web-ready asset.
2. **Fluid state transitions via keyframe interpolation:**
   - Instead of writing complex CSS/GSAP transitions, generate the start keyframe and end keyframe, then let a video model interpolate between them.
   - Bind the generated clip to user interaction (e.g. scrub frames on scroll or trigger on screen transitions).

---

### Phase 3: Deliver

Once we’ve gotten to a unique, standout design, the final step is to clean up the details and get it ready for production use. AI can build striking visuals, but human judgment is key to making sure the design makes sense, flows well, and serves its practical purpose.

#### Technique 6: Cut out elements that don’t add value

AI loves to add more, but it rarely takes away. One of the biggest signs that a design is AI-generated is that it overexplains everything or contains elements that don’t serve any practical purpose. By contrast, a design that exercises restraint immediately looks premium and tasteful.

When polishing AI designs, most effort goes into removing things:
- Pink/purple glowy effects in backgrounds and progress bars
- Random accent highlights and multi-colored text
- Extra labels, badges, and empty spacer containers
- Custom buttons and inputs that look clumsy compared to native OS components (e.g., Apple HIG iOS components)

**The Rule:** Look over your design and ask yourself what really needs to be there. Often, putting less on the screen communicates more.

#### Technique 7: Remove AI tells

Every AI model defaults to predictable, overused design tropes. In isolation they aren’t errors, but when combined, they scream "AI slop":
- **Ambient purple/cyan glows and gradient borders**
- **Excessive containerization (Card fatigue / Bento overload):** Wrapping every stat, list item, and paragraph in its own rounded rectangle
- **Uniform heavy border-radius:** Making every single button, container, tag, and modal into a pill or super-round shape
- **Floating decorative tags and badges:** Unmotivated mini-labels like "Fast", "AI-Powered", "Automated" scattered without functional reason
- **Standardized left-column / right-graphic Hero section**

**Action:** Do not ban everything in the first prompt (which paralyzes the model). Instead, run an explicit **AI Tells Audit** during the polishing phase. Direct the agent to strip out arbitrary containers, replace custom widgets with platform-native components, and let whitespace and typographic scale establish hierarchy.

#### Technique 8: Rewrite copy by hand

The copy a model puts in your design doesn’t affect the visual code directly, but it may have the biggest impact on whether users perceive your design as tasteful or cheap slop.

- **The Problem:** AI-generated marketing copy is full of predictable buzzwords ("Unleash", "Seamlessly", "Revolutionize", "Supercharge"), passive voice, and tired triads. It is fatiguing to read and instantly signals low-effort automation.
- **The Remedy:** Treat AI copy strictly as **visual Lorem ipsum**—a temporary placeholder for spatial layout.
- **Human Rewrite:** Have a human or a specialized editorial prompt replace each headline, subhead, and button CTA with concise, conversational, authentic phrasing. Shorter, punchier, and zero marketing fluff.

---

### Summary & Takeaways

- **The model is rarely the bottleneck—the workflow is:** Most builders tap into only ~1% of what frontier models can design because they expect a single one-shot prompt to deliver Apple-grade aesthetics.
- **The Golden Formula:**
  $$\text{World-Class AI Design} = \text{External Randomness/Seed} + \text{Separated Critic Loop} + \text{Multimodal Assets} + \text{Ruthless Subtraction}$$
- **Human as Creative Director:** The agent provides unprecedented speed and execution breadth; the human sets the taste bar, curates the direction, and enforces restraint.

---

## 3. AI 设计反模式与审查提示词速查表 (Anti-Patterns & Prompts Cheatsheet)

### 3.1 AI 设计 7 大反模式 (The 7 AI Design Anti-Patterns)

| 反模式名称 (Anti-Pattern) | 典型表现 (Telltale Sign) | 纠治与重构方案 (Remediation) |
| :--- | :--- | :--- |
| **1. 赛博紫霓虹眩光 (Purple/Cyan Glow Slop)** | 页面大面积使用暗黑背景 + 紫色/青色弥散径向渐变、高亮发光边框 | 替换为扎实的大面积中性色底、真实阴影或自然的自然光照纹理 |
| **2. 容器卡片疲劳 (Card & Bento Fatigue)** | 每一个指标、每句话都要装进独立圆角卡片，导致层级破碎 | 消除 70% 的卡片边框与背景色，用排版层级与负空间（Whitespace）组织信息 |
| **3. 全面药丸化 (Universal Pill Syndrome)** | 按钮、标签、输入框一律使用 `rounded-full` 或过度大圆角 | 采用克制的系统级圆角（如 4px-8px）或直角几何风，增强专业质感 |
| **4. 模板化 Hero 布局 (Cookie-Cutter Hero)** | 居中大字或左侧文案+CTA，右侧漂浮一个毫无意义的 3D 浮雕插画 | 采用不对称画幅、沉浸式全宽视觉、编辑杂志式排版或动态交互卡片 |
| **5. 装饰性标签泛滥 (Unmotivated Badges)** | 在每个标题上方堆砌彩色药丸 Tag（如 `⚡ AI Powered` / `✨ Seamless`） | 全部删除无语义 Tag，直接通过主标题与交互功能自证价值 |
| **6. 蹩脚自造控件 (Clunky Custom Widgets)** | 手写丑陋的自定义开关、滑块、下拉菜单，缺少状态与物理反馈 | 引入平台级成熟设计系统（Apple HIG / Radix / Tailwind / shadcn）原生状态 |
| **7. 假大空废话文案 (Slop Marketing Copy)** | "Empower your workflow", "Supercharge your productivity" | 全部视作排版占位符，人工重写为具体、克制、口语化的人类真实语言 |

---

### 3.2 独立评审（Critic Subagent）标准提示词模板

```markdown
Role: Elite Design Director & Visual Critic (Top-Tier Studio Level)
Task: Evaluate the attached visual screenshot of the current UI.

Rules:
1. Ignore all code and technical implementation details. Critique purely on aesthetic taste, composition, rhythm, and polish.
2. Identify the intended aesthetic direction. Contrast this design against how Pentagram, Apple, or Teenage Engineering would execute this exact same concept.
3. Call out every single "AI tell" (unmotivated purple gradients, card-within-card fatigue, pill tags, generic hero layouts).
4. Point out the top 3 highest-leverage things to DELETE or SIMPLIFY.
5. Provide a brutal, objective polish score out of 10. (Be extremely strict: 7 is average agency work, 9 is award-winning bespoke craftsmanship).
```
