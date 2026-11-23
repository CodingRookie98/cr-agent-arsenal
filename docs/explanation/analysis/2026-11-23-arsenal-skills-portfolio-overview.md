# `cr-agent-arsenal` 全仓 7 技能组合横向全景评估与架构治理总路线图

> **文档控制信息**
> - **文档标识**: ANA-ARSENAL-PORTFOLIO-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **报告定位**: 本报告为 2026-11-23 全仓技能系统性调研与评估工程的**顶层总纲**，横向综合 7 个现役技能（及已退役对照组 `spec-evolution` [ADR-0003](../decisions/0003-retire-spec-evolution.md)）全部 14 篇独立同类调研与架构评估报告的一手实证，回答三个组合级战略问题：**全仓技能为何普遍出现结构性过度设计、7 个技能各自应如何定位与去留、未来应按什么波次重构并以何种铁律防腐**。
> - **证据分级**: 【A】一手（基于全仓 113 个源码文件 / 24,821 行、390 次 Git 提交、28 份计划、18 项审查归档、8 份 RFC 与 40+ 个外部高星开源仓库的同日实测汇总）｜【B】二手转引（2024–2026 顶会论文与前沿实验室工程文摘要）｜【C】组合级架构战略研判与路线图设计

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：汇总全仓 7 技能 14 篇成对调研/评估一手数据，揭示跨技能五大系统性共病，确立去留瘦身四象限、Wave 0–3 执行总路线图与五条公共技能防腐宪法 |

---

## 0. 组合级核心结论（Executive Summary）

**一句话战略诊断**：`cr-agent-arsenal` 已经沉淀出一批**明显领先社区平均水准的核心工程思想**（三轨通道与 `Maintenance-Patch`、L0–L3 测试定级与 Mock 防逃逸、独立隔离红队审查、术语先行与低影响默认假设、反证驱动废除绝对分门禁、四类前端缺陷回流路由），但过去两个月在「只做加法不做消融 + 静态治理指标反向异化 + 手写 Markdown 正则验表执念」的叠加驱动下，全仓公共技能体量已膨胀至 **113 文件 / 24,821 行 / 1.22 MB**——其中 **超过 70% 的体量属于零实战消费外壳、低可移植单仓私有 CI、不可度量提示词伪运行时或文案锁死测试**。

通过有纪律的四波次（Wave 0–3）瘦身升级，**全仓公共技能总维护面可从 ~1.22 MB 安全削减约 70%–75%（收敛至 ~250–320 KB）**，清零 15+ 处已实证的源码级真 Bug 与跨技能 Split-Brain 冲突，同时让核心护城河追平 2026 头部开源标杆。

---

## 1. 全仓 7 技能实证全景对比表（2026-11-23 一手汇总【A】）

| 技能 | 追踪体量【A】 | 实战消费实证【A】 | 实证真 Bug / 致命漂移【A】 | 核心不可替代护城河 | 组合战略评级与目标体量【C】 | 对应双报告索引 |
| :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **`goal-loop`** | 17 文件<br>2,128 L<br>125.1 KB | 三轨 **28/28**、检查点 **89%**；但 tracker / `HALF-OPEN` / 2 模板均为 **0/28** | `25%` 预算与 `host-adapters:67` 自相矛盾；Diátaxis 旧目录；React 硬编码；个人路径 | 三轨分流（`Maintenance-Patch`）、L0–L3 与防 Mock 逃逸、`Active Checkpoint` | **核心支柱 · V3.0 瘦身升级**<br>（~125 KB → **~60 KB, -52%**） | [调研](./2026-11-23-goal-loop-peer-research.md) · [评估](./2026-11-23-goal-loop-architecture-evaluation.md) |
| **`dual-round-review`** | 24 文件<br>4,274 L<br>236.8 KB | 17 归档 / 70 报告（1.76 MB）；但 Artifact **0%**、R2 仅拦 **3 条**误报 P0/P1 | `_UNIT_RX` **17/17 全失效**；`[f](./f)` 链接 Bug 打红 CI；6 处模板漂移；24 条文案锁死测试 | 严格隔离红队、第一性原理攻击推演、Diff 边界锁、风险分级 | **核心支柱 · V3.0 降噪瘦身**<br>（~237 KB → **~85 KB, -64%**） | [调研](./2026-11-23-dual-round-review-peer-research.md) · [评估](./2026-11-23-dual-round-review-architecture-evaluation.md) |
| **`doc-governance`** | **32 文件**<br>**12,889 L**<br>**598.6 KB**（占全仓 **48.9%**） | 高频绑定 pre-commit，但致 **49.7%** 历史提交纯改文档（近 80 次达 **77.5%**）；drift 仅覆盖 **4% 自引用** | **7 处源码 Bug**（2 死参数、行号锚点退化、`articles` 豁免未落地、单文档读盘 6–8 次）；3 文件破千行；9 子系统混装 | Diátaxis 写作纯度、RFC 结晶流、MADR 3.0、通用 `check-doc-links.py` | **核心支柱 · 三刀公私分离**<br>（公共核 599 KB → **~55 KB, -91%**） | [LLM-WIKI](./llm-wiki-implementation-research.md) · [增量调研](./2026-11-23-doc-governance-peer-research.md) · [评估](./2026-11-23-doc-governance-architecture-evaluation.md) |
| **`clarification-protocol`** | 8 文件<br>949 L<br>48.0 KB | 业务激活 **0/28**；校验脚本实跑 8 篇真实 RFC **0/8 通过**；新 RFC 全压平为 4 列单表 | 脚本 **8 类硬伤**（CRLF 崩、自然表全红、空列+待定反而 `rc=0`）；`SKILL.md:72` 空指针预算；双模板 Split-Brain | 术语先行、影响×依赖排序、低影响显式默认假设、三问收敛判据 | **精品微技能 · 去壳提纯**<br>（48 KB → **~8 KB, -83%**） | [调研](./2026-11-23-clarification-protocol-peer-research.md) · [评估](./2026-11-23-clarification-protocol-architecture-evaluation.md) |
| **`agy-delegation-workflow`** | 8 文件<br>1,174 L<br>58.7 KB | 28 份计划业务派发 **0/28（0%）**；6/8 提交为被动应付治理指标 | 14 处过时模型 `Gemini 3.8`；6/7 审计项写死 Next.js 私有 props；2 处漏 `--add-dir`；强制跳过权限 | Silent Landing SOP、Direct-Write 四止损准则（极轻量） | **建议退役 · 抽资产合并**<br>（59 KB → **0 KB**，真资产并入 `goal-loop`） | [调研](./2026-11-23-agy-delegation-workflow-peer-research.md) · [评估](./2026-11-23-agy-delegation-workflow-architecture-evaluation.md) |
| **`taste-driven-designer`** | 13 文件<br>1,407 L<br>74.9 KB | 仓内业务 UI 调用 **0 次**；与本机已装 `frontend-design`（9.4 KB）重叠 >70% | `generate-seed.py` **Park-Miller 零状态 Bug**；设计书误覆写断言「无测试」；模板硬编码个人真名；7 处漂移 | E1–E7 反证驱动的三信号盲比/4+1 Critic、外部熵发散、残酷减法 | **垂直选配 · 大幅提纯或退位**<br>（75 KB → **~20 KB, -73%**，视前端路线定） | [调研](./2026-11-23-taste-driven-designer-peer-research.md) · [评估](./2026-11-23-taste-driven-designer-architecture-evaluation.md) |
| **`frontend-qa-gate`** | 8 文件<br>1,567 L<br>76.6 KB | 全仓真实 QA 报告 **0 份**；73.3% 代码用于验表格式，浏览器采集 **0 行** | **5 组对抗探针全击穿 Exit 0**（失败 99 条/`~~~` 围栏全放行）；无头环境 **100% BLOCKED 死锁**；跨技能调用缺参 | 拒绝打分的三态诚实、四类缺陷精确回流路由、五域覆盖视角 | **垂直选配 · 探针实采化或吸收**<br>（77 KB → **~22 KB, -71%** 或合并） | [调研](./2026-11-23-frontend-qa-gate-peer-research.md) · [评估](./2026-11-23-frontend-qa-gate-architecture-evaluation.md) |

*(注：另含 `skills/_shared/` 3 文件 / 433 行 / 20.0 KB，承担跨技能链接与基础交付面共享哨兵。)*

---

## 2. 贯穿全仓的「五大系统性共病」（跨技能根因解剖）【A/B/C】

把 7 个技能的病灶并列，会发现它们并非 7 个孤立偶然事件，而是由 **5 个共同的系统级工程根因**反复复制产生：

### 共病 1：治理指标反向异化（Goodhart's Law 与已退役 `spec-evolution` 的深远余波）

过去一轮全仓「交付面齐备化 + Bash→Python 逐字节差分迁移」运动产生了意料之外的副产品【A】：
- `clarification-protocol`（原 88 行清爽文档）1 天内被硬灌 741 行外壳与坏脚本（占 90.7% 源码）；
- `agy-delegation-workflow` 8 次提交中有 6 次纯为被动补测、补设计书与迁 Python，实战使用率仍为 0%；
- 4 个脚本（`dispatch-agy.py`、`scaffold-doc.py`、`generate-seed.py`、`check-decision-ledger.py`）因苛求与已退役 Bash/awk「逐字节报错一致」，在 Python 代码里硬写了伪造旧 Bash 行号报错、61 行手写 `Getopts` 类，甚至**为了复刻 awk 不剥 `\r` 而给跨平台 Python 硬生生造出了 Windows CRLF 全败 Bug**！

### 共病 2：「正则表达式校验 Markdown」的集体工程幻觉

全仓有 **5 个技能**同时投入超过 **3,000 行脚本与测试**去用正则解析或回写自由格式 Markdown，结果全线遭遇滑铁卢【A】：
- `goal-state-tracker.py`（667 行含测）：实战 **0/28** 调用；
- `check-decision-ledger.py`（560 行含测）：8 篇真实 RFC **0/8** 通过，空列+待定作弊反而 `rc=0`；
- `check-qa-report.py`（1,149 行含测）：11 次提交陷入中文否定句猫鼠战，5 组对抗探针 **100% 击穿 Exit 0**；
- `check-review-report.py` + `prepare-review-context.py`（2,978 行含测）：`_UNIT_RX` 17/17 失效、链接剥离拼出 `f.f` 打红 CI；
- `check-doc-drift.py`（2,516 行含测）：行区间锚点退化为文件级，覆盖率仅 **4.0%**（3 篇自引用），却贡献近 50 次提交里 **22%** 的纯重钉 SHA 噪音。

**行业破局之道【A/B】**：机器需要确定性校验的状态与裁决，必须用 **结构化 JSON / YAML Frontmatter** 或 **真实运行时物证（文件存在非空、编译器/测试/axe/LHCI/lychee 退出码、Git 拓扑祖先）**，绝不再用正则去解析自由散文与中文否定句！

### 共病 3：跨技能 Split-Brain（多真相源撕裂）与连带负外部性

随着技能数增长，各技能彼此「重复定义同一件事却各执一词」的现象已遍布全仓【A】：
1. **双委派 SSOT 冲突**：`agy-delegation-workflow/SKILL.md:22` vs `goal-loop/references/host-adapters.md`；
2. **双台账模板 Split-Brain**：`clarification-protocol`（5 表）vs `doc-governance` RFC 模板（三分节）vs 实战 RFC-0005~0008（4 列单表）；
3. **前端状态矩阵四处打架 + SSOT 倒挂**：`taste-driven-designer`（5/8/9 态三套版本）vs `frontend-qa-gate`（31 条真断言）；
4. **P0 阶段四重技能叠加**：`goal-loop` P-1/P0 同时压着 `brainstorming` + `grilling` + `clarification-protocol` + `doc-governance`；
5. **归档机制连带污染**：`dual-round-review` 的 Write-Once 全文入库迫使 `doc-governance` 6 个脚本硬编码双轨豁免并锁死已实现 RFC 不可归档移动。

### 共病 4：高指令密度引发 IFScale 静默脱落与「提示词伪运行时」

- 实证研究（ICLR 2025 *Curse of Instructions*、IFScale 150–200 条阈值、ETH Zurich 2026 `AGENTS.md` >20% 推理成本税【B】）在本仓库得到惊人复现：`dual-round-review` `SKILL.md` 达 36.8 KB / 96 条强禁令词后，2026-11-22 当日全部 4 个实战归档集体出现遗漏格式 + 篡改第 7 列 + 产生「Light 模式本就不该过门禁」的事后合理化幻觉【A】；
- 同时 `goal-loop` 的 `min(25%, 剩余÷3)`（被 `clarification-protocol` 再次复制）与 `2-Action Rule`、`frontend-qa-gate` 无头环境必测 VoiceOver 读屏，均属在纯 L1 提示词内强加物理不可度量或物理不可达的硬约束。

### 共病 5：「单仓私有治理」与「可跨仓分发公共技能」边界未切开

`cr-agent-arsenal` 定位为**对外可复用的公共技能库**，但全仓普遍存在「本仓私货混入公共技能」现象【A】：
- `doc-governance` 裹挟了 0% 可移植的 `check-golden-tasks.py`、`check-all.py` 与 1,537 行 Mini-Jira Backlog；
- 多个技能残留私有 React/Next.js 私有组件 props（`agy` 6/7 条、`goal-loop:204`、`dual-round-review` 32 行）、个人绝对路径（`goal-loop-design:10`、`doc-governance-design:317`）、个人真名（`taste` 模板 `王辉`）与外部用户完全看不懂的本仓私有回归编号（`RFC-0001`、`R1-x 回归`）。

---

## 3. 分波次全仓重构总路线图（Wave 0 → Wave 3）【C】

本路线图严格遵循「**先止血修红灯 → 再拆零用外壳与冲突 → 再升级三大核心支柱 → 最后定调前端垂直技能**」的渐进稳定切片原则，每波次独立可验收、可逆、无断崖风险：

| 波次 | 目标主题 | 具体动作清单 | 预期量化收益 |
| :---: | :--- | :--- | :--- |
| **Wave 0**<br>*(紧急止血)* | **清零现红 CI 与已证实的源码级真 Bug** | ① 修 `dual-round-review` 的 `_UNIT_RX`（17/17 失效）与 `[f](./f)` 链接剥离 Bug，处理 2026-11-22 4 归档恢复全仓 `pytest` 全绿；<br>② 修 `doc-governance` 7 处 Bug（`--max-doc-bytes`/`--lang`/`articles` 豁免/`check-all` 重复读盘与错误建议）；<br>③ 修 `taste` LCG 零状态 Bug、设计书失实断言「无测试」、清个人路径/真名与 `dual-round-review:123` 缺参错误 | **0 现红测试、0 静默死参数、0 个人敏感路径泄露**；为后续重构建立可信基线 |
| **Wave 1**<br>*(清场与去壳)* | **退役零用硬编码技能 + 提纯微技能** | ① **退役 `agy-delegation-workflow`**（写 `ADR-0004`）：将 Silent Landing SOP 与 Direct-Write 四准则（~35 行）并入 `goal-loop/references/host-adapters.md`，抽象虚假合规检查并入 `dual-round-review`；<br>② **提纯 `clarification-protocol`**：废除 0/8 损坏脚本与两份冲突模板，剥离 §5/§6 杂项并修 L72 空指针，收敛为 60–80 行微技能 + 统一 RFC-0005~0008 的 4 列单表 | 立刻净减 **~100 KB / ~2,000 行** 零实战消费维护债；消除「双委派」与「双台账」两大 Split-Brain |
| **Wave 2**<br>*(三大基座 V3.0)* | **核心工程三强现代化瘦身升级** | ① **`goal-loop` V3.0**：退役零用 tracker / `HALF-OPEN` 伪运行时 / 2 僵尸模板 / 机械 2-Action；收敛为 5 阶段（Align→Plan→Execute→Verify→Close）；引入 ~60 行文件指针交接脚本 + Rulings not stalls + 模型档位分层 + 合批/垂直切片；<br>② **`dual-round-review` V3.0**：精简 `SKILL.md` 至 ≤12 KB；引入空结果优先 + 防 Prompt Injection + Delta 免 R2 + Per-Issue 轻证伪；退役 0 用 Artifact；用 Frontmatter 轻门禁替代 620 行正则刮表并轻量化归档策略；<br>③ **`doc-governance` 三刀切割**：本仓私有门禁（`check-golden-tasks`/`check-all`）迁出至仓库根 `scripts/doc-gates/`；拆出 1,537 行 Backlog；退役手写修订表、2,516 行重型 drift（改 Git 拓扑或异步巡检）与强制 `llms.txt` pre-commit，回归 Convention-First 公共核 + 通用 `check-doc-links.py` | 全仓核心基座瘦身 **~75%**（960 KB → **~200 KB**）；彻底消灭 22% 重钉 SHA 与 20.5% `llms.txt` 治理税；审查与编排能力全面对齐 2026 标杆 |
| **Wave 3**<br>*(垂直定调)* | **前端双技能按实际业务诉求精准收口** | 若未来继续服务外部前端仓：① **`taste-driven-designer`** 提纯至 ~20 KB（表面模式 + 2026 新 AI Slop + 精简盲比 Critic + 25 行标准库种子，把状态矩阵单归 QA Gate）；② **`frontend-qa-gate`** 废弃 433 行验表正则，升级为直连 `chrome-devtools-mcp` / `agent-browser` / Playwright+axe+LHCI 的探针编排协议 + 拆分「自动化门禁 vs 真机人工签收」破除 BLOCKED 死锁。<br>*(若确定本仓不再承载前端业务，则可走「沉淀原则 + 退役/委派成熟外部技能」路线)* | 消除「只验表不验真」与永久死锁，彻底解决与 `frontend-design` / `agent-browser` 的叠床架屋 |

---

## 4. 面向未来的五条「公共技能防腐宪法」【C】

为避免瘦身半年后再次膨胀回 1.2 MB 巨石，建议将以下五条准则写入本仓库技能准入与评审红线：

1. **实证先于建壳（Usage Before Harness）**：任何新技能起步必须以**单文件纯 `SKILL.md`（≤150 行）**先经至少 3 次真实业务任务实战打磨；在未出现明确跨任务重复机械痛点前，严禁提前搭建脚本、多模板与数百行契约测试。
2. **机器只验结构化头与真物证，绝不用正则验中文散文**：脚本校验仅限 JSON / YAML Frontmatter、磁盘文件存在非空、或工具/测试真实退出码；凡试图靠正则拦截大模型中文自然语言措辞的脚本，一律视为反模式直接否决。
3. **公私物理分离（Portable Skill ≠ Repo-Local CI）**：`skills/<name>/` 内一切代码与模板必须满足「**零修改拷贝到任意英文/中文外部业务仓库即可运行**」；凡绑定本仓库目录结构、私有验收断言、个人路径/插件/真名的资产，必须放在仓库根 `scripts/` 或本地文档中。
4. **测试守行为，不锁文案（Behavior Over String-Pinning）**：禁止编写 `assert "精确中文句子" in skill_md` 或 `assert "len(fields) >= 9" in py_source` 类文案/变量名锁死测试；技能测试只允许覆盖真实脚本行为边界与防断链/frontmatter 合法性共享哨兵。
5. **模型代际消融日（Periodic Harness Simplification）**：遵循 Anthropic Harness 简化律【B】，每逢主力前沿模型大版本跃迁或季度复盘，按真实使用率对全部脚本、模板与阶段做一次「零使用清零消融」，把曾为旧模型短板打上的补丁及时拆除。

---

## 5. 全套 15 篇调研与评估工程资料总索引

本仓库 2026-11-23 技能全景调研与评估资产包已完整落盘于 `docs/explanation/analysis/`（均通过 `check-all.py` 全量门禁与 `G-10` 证据分级校验）：

- **组合总纲（本篇）**：[2026-11-23-arsenal-skills-portfolio-overview.md](./2026-11-23-arsenal-skills-portfolio-overview.md)
- **`goal-loop`**：[同类调研](./2026-11-23-goal-loop-peer-research.md) ｜ [架构评估](./2026-11-23-goal-loop-architecture-evaluation.md)
- **`dual-round-review`**：[同类调研](./2026-11-23-dual-round-review-peer-research.md) ｜ [架构评估](./2026-11-23-dual-round-review-architecture-evaluation.md)
- **`doc-governance`**：[LLM-WIKI 调研](./llm-wiki-implementation-research.md) ｜ [Docs-as-Code 增量调研](./2026-11-23-doc-governance-peer-research.md) ｜ [架构评估](./2026-11-23-doc-governance-architecture-evaluation.md)
- **`agy-delegation-workflow`**：[同类调研](./2026-11-23-agy-delegation-workflow-peer-research.md) ｜ [架构评估](./2026-11-23-agy-delegation-workflow-architecture-evaluation.md)
- **`clarification-protocol`**：[同类调研](./2026-11-23-clarification-protocol-peer-research.md) ｜ [架构评估](./2026-11-23-clarification-protocol-architecture-evaluation.md)
- **`taste-driven-designer`**：[同类调研](./2026-11-23-taste-driven-designer-peer-research.md) ｜ [架构评估](./2026-11-23-taste-driven-designer-architecture-evaluation.md)
- **`frontend-qa-gate`**：[同类调研](./2026-11-23-frontend-qa-gate-peer-research.md) ｜ [架构评估](./2026-11-23-frontend-qa-gate-architecture-evaluation.md)
