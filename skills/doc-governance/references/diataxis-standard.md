# Diátaxis 四象限架构标准与写作指南 (Diátaxis Documentation Standard)

> **控制信息**
> - **规范版本**: V1.0.0
> - **理论来源**: Daniele Procida 的 Diátaxis 体系 (https://diataxis.fr/)
> - **适用范围**: 通用软件工程文档库与 AI 智能体上下文构建

---

## 1. 核心理论：两维四象限心智矩阵

Diátaxis 认为，任何技术文档的分类不能基于“软件处于什么生命周期”，而必须严格基于**读者即时心智状态与工作意图 (Reader's Mental State and Intent)**。

这个空间由两个相互垂直的正交轴构成：
1. **水平轴 (Acquisition vs Application)**：
   - **理论学习 (Theoretical / Acquisition)**：读者正在思考、消化概念；
   - **实践应用 (Practical / Application)**：读者正在双手敲键盘、解决现实任务。
2. **垂直轴 (Work vs Study)**：
   - **服务于生产工作 (Serving Work)**：读者需要以最快速度完成目标，没有闲暇深究；
   - **服务于思考研究 (Serving Study)**：读者需要理解全局背景与设计哲学。

```text
               【实践应用 (Practical)】
                         ▲
                         │
        How-To Guides    │    Tutorials
        (操作指南)        │    (新手教程)
  服务于生产             │               服务于学习
  (Serving Work)         │               (Serving Study)
 ────────────────────────┼────────────────────────►
                         │
        Reference        │    Explanation
        (技术参考)        │    (深度剖析)
                         │
                         ▼
               【理论知识 (Theoretical)】
```

---

## 2. 四大象限详细规范与写作准则

### 2.1 教程象限：Tutorials (Learning-Oriented)

* **读者心智**：“我刚接触这个项目，请带领我完整走一遍，给我一个能够运行成功的首战体验。”
* **核心目标**：建立信心与基本认知。
* **写作铁律**：
  1. **手把手领航**：提供明确、不容出错的线性步骤（Step 1, Step 2, Step 3）；
  2. **最小可运行体验**：以最快路径让新手看到期望的输出（如“运行第一个 Agent 研究流”）；
  3. **严禁展开深层理论**：绝对不在教程里长篇大论为什么不用另一个算法；只教怎么跑起来，不展开架构争辩；
  4. **严禁提供过多分支选项**：不要出现“或者你也可以选择配置 Redis/Kafka/MySQL”——在教程里只给唯一的官方推荐默认值。

### 2.2 操作指南象限：How-To Guides (Problem-Oriented)

* **读者心智**：“我是一个有经验的开发者/运维，我当前面临一个具体问题（如部署、排错、测覆盖率），直接告诉我怎么做。”
* **核心目标**：高效解决特定的现实任务。
* **写作铁律**：
  1. **食谱式指令 (Recipe-style)**：明确的前置条件（Prerequisites）+ 执行命令 + 预期结果（Expected Output）；
  2. **行动导向 (Action-Driven)**：直奔主题，拒绝“在现代分布式系统中，高可用至关重要……”等无意义的宏观废话；
  3. **问题聚焦 (Single Goal)**：一份 How-To 只解决一个独立问题（如 `how-to/deployment.md`, `how-to/troubleshooting.md`）；
  4. **理论引用外链**：若某一步骤涉及深奥的网络拓扑或数据隔离机制，使用超链接指向 `explanation/`，不在操作手册中就地展开。

### 2.3 技术参考象限：Reference (Information-Oriented)

* **读者心智**：“我正在写代码或排查错误，我需要查验绝对权威的技术事实、参数类型、错误码或枚举约束。”
* **核心目标**：**充当全系统的机器事实真相源 (Single Source of Truth) 与 AI 智能体生成代码的核心基准！**
* **写作铁律**：
  1. **冷峻客观、毫无废话**：像机械图纸一样精确。只陈述“是什么”、“有哪些字段”、“约束是什么”，不教人怎么用，不解释为什么这样选；
  2. **全覆盖无遗漏**：API Endpoint、请求/响应 Payload 结构、HTTP 状态码、错误信封（Envelope）、数据库模型 Schema、状态机图谱、前端 Token；
  3. **严格格式化**：以结构化 Markdown 表格、TypeScript Interface、JSON Schema 形式呈现，极大提升机器可读性；
  4. **⛔ 绝对隔离禁令**：严禁在 Reference 中混合教程步骤或方案讨论。

### 2.4 深度剖析象限：Explanation (Understanding-Oriented)

* **读者心智**：“我想深入理解系统的灵魂。为什么这样分层？为什么否决了那个库？核心算法的推导逻辑是什么？”
* **核心目标**：传递系统设计思想、架构权衡与为什么（The "Why"）。
* **写作铁律**：
  1. **宏观与全景**：阐述架构拓扑、领域模型边界、组件交互时序图（Mermaid）；
  2. **决策证据链**：记录技术选型对比（如 Zustand vs Redux, SQLite vs PostgreSQL）以及为什么选择当前方案；
  3. **不可逆决策归档**：使用标准 MADR 格式沉淀为不可篡改的架构决策记录（`explanation/decisions/0001-xxx.md`）；
  4. **概念与设计哲学**：阐述项目所遵循的核心设计哲学（如不可变数据流、防御性扫描、两轮对抗）。

---

## 3. 分类决策树 (Classification Decision Tree)

当你准备创建或重构一份文档时，运行如下决策树判断其归属：

```text
Q1: 它是项目初期还在激烈讨论、反复对齐的提案草案吗？
    ├── 是 ──► 【docs/proposals/RFC-xxxx.md】 (定案结晶前在此闭环)
    └── 否 ──► 进入 Diátaxis 四象限判断：

Q2: 这份文档的主要目的是为了指导初学者学习，还是为了完成某项具体工作？
    ├── 指导学习 ──► Q3: 它是手把手的上手教程，还是解释原理与为什么？
    │                ├── 手把手 ──► 【docs/tutorials/】 (教程象限)
    │                └── 讲原理 ──► 【docs/explanation/】 (剖析象限)
    │
    └── 完成工作 ──► Q4: 它是操作步骤（动词/任务），还是查询规格与事实（名词/参数）？
                     ├── 怎么做步骤 ──► 【docs/how-to/】 (操作指南象限)
                     └── 查询规格事实 ──► 【docs/reference/】 (技术参考象限)
```

---

## 4. 经典反模式与整改对照 (Anti-Patterns & Corrections)

| 反模式名称 | 典型坏味道症状 | 致命危害 | 标准整改对策 |
|:---|:---|:---|:---|
| **大乱炖文档 (Omnibus Doc)** | 一份“后端开发文档”里写了架构思想、又写了怎么配环境变量、又写了 20 个 API 接口定义 | AI 上下文瞬间撑爆；找一个 API 字段需要翻 1000 行无关文本 | 按 Diátaxis 拆解：架构进 `explanation/`，环境配置进 `how-to/`，API 进 `reference/api/` |
| **参考中夹带私货 (Explanation in Reference)** | 在定义 API 请求体字段时，写了 3 段话解释为什么当初没有选 GraphQL | 严重稀释 AI 对类型契约的注意力，容易引发生成参数混淆 | 将 GraphQL 选型论证提取为一条 ADR，在 API 字段旁使用外链 `[详见ADR-002](../explanation/decisions/0002.md)` |
| **步骤里大讲原理 (Lecturing in How-To)** | 在“部署服务”指南第一步，花 500 字科普 Docker 的 cgroup 和 namespace 容器隔离底层 | 读者处于紧急发布状态，冗长铺垫增加操作失误率 | 删去原理科普，直接给出可执行的构建与发布命令 |
| **将草案当事实 (Draft Contaminating Reference)** | 将还在脑暴的 API 伪代码直接写入 `reference/api/` | 其它 Agent 以为接口已存在，生成假代码引发大面积单测红线 | 转移至 `proposals/RFC-xxx.md` 中孵化对齐，定案结晶后再写入 `reference/` |
