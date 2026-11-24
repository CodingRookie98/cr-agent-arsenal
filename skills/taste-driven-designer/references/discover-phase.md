# D1 Discover — 表面模式与发散探索

> 目标：打破 LLM 平庸默认（紫渐变 + 对称 Hero + 卡片堆砌 + 空话）。先定表面模式，再用外部熵打散方向。

## 1. 表面模式分流 (Surface Mode)

开局必选其一写入简报，**严禁混用**：

| 模式 | 适用产物 | 视觉与节奏 | 禁忌 |
|---|---|---|---|
| **`Persuade`** | 落地页、品牌展示、发布页 | 视觉冲击、不对称节奏、大留白与叙事张力 | 堆砌密集工具控件或长表格 |
| **`Operate`** | 工具、工作台、仪表盘、编辑器 | 高信息密度、极速扫描、克制装饰、稳定反馈 | 巨幅 Hero、浮夸动效或低对比毛玻璃 |

## 2. String Seed of Thought（外部随机熵）

口头“随机一点”无效——必须用外部脚本生成密码学随机串作灵感源。

```text
Build/redesign <目标，如 editorial landing page 或 telemetry workspace>.
1. Generate seeds: python3 "$SKILL_DIR/scripts/generate-seed.py" -l 128 -c 3
   (团队复现改用 -s <种子词>)
2. Inspect subpatterns: digit frequencies, letter ascender/descender shapes,
   contiguous blocks, segment rhythms, case flips.
3. Map hints to color, layout, typography, and texture in the brief.
Never leak the seed string into visible UI or copy.
```

- **提取维度**：数字（频率定分割比/栏数）、字母形状（高低定节奏）、块状分布（卡片 vs 通栏）、分段节奏（区段长短）、奇偶大小写（强调色与字重）。
- **多方向并行**：用 `-c 3` 产 **2–4 份简报**（[design-brief-template.md](../templates/design-brief-template.md)），并排对齐选 1（兼修至多 2）进 D2；种子串**禁泄露**到可见产物。

## 3. 雄心跨界 Prompt 三步入炉法

1. **宽列不深挖**：让 AI 一句话列出大量高概念方向（`"List bold design languages, one line each. Go broad, not deep."`）。
2. **直觉反应精修**：挑出有共鸣的隐喻（工业控制台、地质层、档案室等），写明好恶交 AI 锐化。
3. **压缩可执行指令**：收敛为 3–5 句具体约束入简报；听起来“会翻车”的破格点子最值得试跑。

## 4. D1 出口检查清单

- [ ] 已定 `Persuade`/`Operate` 且未混用；2–4 份简报落盘并由用户选定方向
- [ ] 已用 `generate-seed.py` 注入外部种子且可见产物零泄露
