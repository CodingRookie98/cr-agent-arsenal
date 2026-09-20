# D3 Deliver — AI Tells 审计、减法与文案重写细则

> 阶段目标：把"惊艳但粗糙"的产出收敛成"细节经得起放大镜"的成品。
> 阶段纪律：**AI 的爱是加法，极品设计是减法**。AI 生成的界面最大的廉价信号是"解释过度、元素过剩"；本阶段的大部分工作在**删除**而非增补。

---

## 1. AI 设计 7 大反模式 (The 7 AI Design Anti-Patterns)

| # | 反模式 | 典型表现 | 纠治与重构方案 |
|:---:|:---|:---|:---|
| 1 | **赛博紫霓虹眩光** (Purple/Cyan Glow Slop) | 暗黑背景 + 紫色/青色弥散径向渐变、高亮发光边框 | 替换为扎实的大面积中性色底、真实阴影或自然光照纹理 |
| 2 | **容器卡片疲劳** (Card & Bento Fatigue) | 每个指标、每句话都装进独立圆角卡片，层级破碎 | 消除 70% 的卡片边框与背景色，用排版层级与负空间组织信息 |
| 3 | **全面药丸化** (Universal Pill Syndrome) | 按钮/标签/输入框一律 `rounded-full` 或超大圆角 | 采用克制的系统级圆角（4px~8px）或直角几何风 |
| 4 | **模板化 Hero 布局** (Cookie-Cutter Hero) | 居中大字，或左文案+CTA + 右侧漂浮无意义 3D 浮雕 | 采用不对称画幅、沉浸式全宽视觉、编辑杂志式排版或动态交互卡片 |
| 5 | **装饰性标签泛滥** (Unmotivated Badges) | 标题上方堆砌 `⚡ AI Powered` / `✨ Seamless` 彩色药丸 Tag | 全部删除无语义 Tag，让主标题与交互功能自证价值 |
| 6 | **蹩脚自造控件** (Clunky Custom Widgets) | 手写丑陋的自定义开关/滑块/下拉，缺状态与物理反馈 | 引入平台级成熟设计系统（Apple HIG / Radix / Tailwind / shadcn）原生状态 |
| 7 | **假大空废话文案** (Slop Marketing Copy) | "Empower your workflow"、"Supercharge your productivity" | 全部视作排版占位符，人工重写为具体、克制、口语化的人类语言（§3） |

**执行时机**：这些反模式**不在首轮 Prompt 里禁止**（一次性禁令清单会让模型瘫痪、产出更僵），而是在打磨阶段通过**显式 AI Tells 审计**逐项清除——审计时点由 D2 Critic 评分与人类判断共同决定。

---

## 2. 减法规则 (Ruthless Subtraction)

> **The Rule**: Look over your design and ask yourself what really needs to be there. Often, putting less on the screen communicates more.

按"它为什么必须存在"拷问每一处装饰，给出不了答案的就删：

- 粉/紫光晕背景与进度条特效；
- 随机出现的强调高亮与多色文本；
- 多余的标签、徽章、空占位容器；
- 比原生 OS 组件更笨拙的自定义按钮/输入框（如 iOS 场景直接用 Apple HIG 原生件）。

**执行方式**：逐项删除并记录删除清单（删了什么、为什么），防止"删了又悄悄加回来"；删除后跑一轮 Critic 复核（或至少一次人工快速目检）确认没有误伤信息层级。

---

## 3. 文案重写规则 (Rewrite Copy by Hand)

文案不直接改变视觉代码，但对"用户觉得这设计是品味还是廉价"影响最大。

**问题**：AI 营销文案满是可预测的黑话（"Unleash / Seamlessly / Revolutionize / Supercharge"）、被动语态与疲惫的三段式排比，读着就累，一眼假。

**规程**：
1. **地位定义**：AI 文案 = 排版 Lorem ipsum，只用于撑起版面空间，不具备留存价值；
2. **重写主体**：由人类或专门的编辑化提示词逐条重写——headline、subhead、按钮 CTA；
3. **重写标准**：更短、更劲、更口语化、零营销词、说具体的事情（数字/事实/用户真实收益），放弃陈词滥调；
4. **审计**：对照黑名单过一遍全部可见文本。

### 3.1 文案黑名单（出现即处理）

```text
Unleash / Seamlessly / Revolutionize / Supercharge / Empower / Transform /
Elevate / Unlock / Level up / Game-changer / Cutting-edge / Next-gen /
"Your one-stop shop" / "The future of" / "Effortlessly" / "Experience the power of" /
"Streamline your workflow" / "Take your X to the next level"
（以及任何三连排比式营销腔："Faster. Smarter. Better." ）
```

### 3.2 文案重写示例（风格基准）

| AI 默认（占位） | 重写后（可交付） |
|---|---|
| "Unleash your productivity potential" | "Done by 2pm. Every day." |
| "Seamlessly sync across all your devices" | "Open it on your phone. It's where you left it." |
| "Revolutionize the way your team collaborates" | "One doc. Zero status meetings." |
| "Supercharge your workflow with AI" | "30 seconds from idea to first draft." |

---

## 4. D3 出口检查清单

- [ ] 7 大反模式逐项过审（记录每项结论：无 / 已修复 / 已删除）
- [ ] 减法删除清单已记录，且无价值元素全部移除
- [ ] 全部可见文案通过黑名单审计并重写（AI 文案不再残留）
- [ ] 自定义控件替换为平台原生/成熟设计系统组件（能力允许时）
- [ ] 方向一致性复核：Critic 审美方向未被减法误伤
- [ ] 交付说明：方向来源（种子 + 用户口味）、Critic 终分、删除清单
