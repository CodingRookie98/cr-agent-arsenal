# 种子字符串施工模板 (String Seed of Thought Procedure)

> 用途：D1 Discover 的第 1 项技法——把外部随机性注入创意方向的完整施工步骤。直接复制下面的提示词块使用（`<…>` 处按实替换）。

## 完整施工提示词（可直接发给实现智能体）

```text
I want you to build/redesign <目标：例如 a landing page for my productivity app>.
Follow this procedure:

1. Generate a long, random alphanumeric string using a shell script:
   bash <SKILL_DIR>/scripts/generate-seed.sh -l <64|更长越多样>
   (多方向并行时加 -c <2~4> 生成多条; 团队复现方向时用 -s <种子词>)
2. Define the creative direction (color scheme, layout, typography, texture, mood)
   based on the string. Look beyond the surface for subpatterns, special numbers,
   block rhythms, digit groupings — anything that inspires you.
3. Use your judgment to bring this direction to life and make it look great.

Don't reveal the string in the design. It's only for your inspiration.
```

## 子模式提取参考（第 2 步的观察维度）

- **数字暗示**：出现的数字及频率（如 3/7 → 三比七版面分割；质数 → 奇数节奏的专栏数）
- **字母形状**：高字母/低字母分布 → 版式的高度节奏
- **块状分布**：连续块与间隔 → 卡片化 vs 通栏的取舍
- **分段节奏**：串的天然分段 → 页面段落的数量与长度
- **奇偶与大小写**：交替模式 → 强调色或字重的出现位置

## 施工示例（真实效果对照）

| 种子串节选（示意） | 可提取的暗示 | 收敛出的方向（示意） |
|---|---|---|
| `…K7kk…333…aX…` | 数字 3 密集、大小写交替 | 三栏节奏 + 大小写交替的标题强调 |
| `…00…1…00…8…` | 中间孤 1、两边成对 | 中心焦点 + 双侧对称的仪表盘式布局 |
| `…LONG…short…` | 长块与短块交替 | 杂志式：长文区与短卡片交替排版 |

## 纪律提醒

1. 种子串由**脚本**生成——模型"生成一个随机串"仍会掉进统计平庸的随机；
2. 种子串永不进入设计成品与文案；
3. 每条种子产出独立简报，2~4 个方向并排对齐后再选 1；
4. 方向简报落盘（设计简报模板），Critic 往返记录从 D2 起追加。
