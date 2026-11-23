# `doc-governance` 技能过度设计诊断与架构重构评估报告

> **文档控制信息**
> - **文档标识**: ANA-DOC-GOVERNANCE-EVAL-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **文档所有者**: 核心架构组
> - **评估依据**: 基于 `skills/doc-governance/` 全部 32 个 Git 追踪源码文件（12,889 行 / 598.6 KB）、`docs/GOVERNANCE.md`、`docs/explanation/architecture/doc-governance-design.md`、全仓 218 篇文档与 Git 全史 390 commits 实证统计，并综合衔接 [llm-wiki-implementation-research.md](./llm-wiki-implementation-research.md) 与增量调研 [2026-11-23-doc-governance-peer-research.md](./2026-11-23-doc-governance-peer-research.md)。
> - **证据分级**: 【A】一手（本仓库全量源码/行号/Git 统计/脚本实跑、外部标杆 `gh api` 源码）｜【B】二手转引（工程文与学术基准摘要）｜【C】架构师诊断与重构方案设计

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 王辉 | 初版：完成 `doc-governance` 598.6 KB 巨无霸体量与 9 大异构子系统解构、12 脚本跨仓可移植性审计、390 commits 治理税实证、7 处真实源码 Bug 定位及三刀切割瘦身路线图 |

---

## 0. 评估总结论（Executive Verdict）

**直接回答核心问题——`doc-governance` 是否过度设计？是否需要深度重构？**

**结论：它是本仓库「过度设计最严重、职责边界最失控、隐性维护税最高」的技能。`doc-governance` 实质上已经不再是一个可跨仓复用的 Agent Skill，而是一个伪装成 Skill 的 1.17 万行单仓私有 CI 门禁 + Mini-Jira 混合软件产品（独占全仓 7 技能总字节的 48.9%、总行数的 51.9%）。通过「物理三刀切割」剥离本仓私有 CI、寄宿 Backlog 与低 ROI 仪式税，预计可将公共技能核瘦身 ~80%–90%（降至 <60–100 KB），同时显著降低日常提交摩擦。**

| 评估维度 | 当前实测状态【A】 | 诊断结论 |
| :--- | :--- | :--- |
| **体量畸形与结构倒挂** | Git 追踪 **32 文件 / 12,889 行 / 598.6 KB**（占全仓技能总字节 **48.9%**、总行数 **51.9%**）；其中脚本+测试占 **86.5%（518 KB）**；**3 文件突破千行红线**（1,457 / 1,938 / 1,709 行） | 对比同类标杆 `addyosmani/documentation-and-adrs`（12.3 KB）与 `anthropics/doc-coauthoring`（15.4 KB），体量膨胀近 **40–50 倍** |
| **God Skill 职责爆炸** | 单一技能同时塞入 **9 个异构子系统**，甚至寄宿了一套 1,537 行的独立项目管理 Mini-Jira（`manage-backlog.py` 785 行 + 140 行手写 YAML 解析器 + 245 行审计） | 严重违背单一职责，引发跨子系统互相打补丁（四处硬编码 `backlog` 与 `reviews` 豁免） |
| **跨仓可移植性塌方** | 12 个脚本中：`check-golden-tasks.py` / `check-all.py` **0% 可移植**；`audit-doc-health.py` 仅 **15%**；`check-doc-drift.py` 仅 **35%**；**仅 `check-doc-links.py`（85%）真正具备跨仓普适价值** | 无法兑现本仓库「工业级可复用公共技能」的定位 |
| **实测高昂「文档治理税」** | 全史 390 commits 中 **49.7%（194 次）**纯改文档/治理本身（近 80 commits 高达 **77.5%**）；**20.5%（80 次）**被迫连带刷 `llms.txt`；近 50 commits 中 **22%（11 次）**纯为给 `check-doc-drift.py` 重钉 `复核于 SHA` | 治理体系已从「低摩擦护栏」异化为消耗大量提交与审查精力的自激振荡源 |
| **真值轴 ROI 极端失衡** | `check-doc-drift.py` + 测试共 **2,516 行 / 114.5 KB**，全仓 75 篇受检文档实际覆盖仅 **3 篇（4.0%）且 100% 是 `doc-governance` 自引用**（三字段齐全 0 篇，却因默认 `--truth=warn` 颁发 15.0/15 满分） | 典型的「为 4% 自引用文档养了 2,516 行复杂状态机并制造 22% 重钉噪音提交」 |
| **源码级真实 Bug 与漂移** | 实证揪出 **7 处真实代码 Bug / 契约漂移**（含 2 个静默死参数、行区间锚点空承诺、`reference/articles` 豁免未落地、自身版本漂移、pre-commit 重复读盘 6–8 次） | 复杂度过高已反噬自身正确性 |

---

## 1. 体量倒挂与「God Skill」九大子系统解构【A】

### 1.1 全仓体量占比与三文件突破千行红线

根据 `git ls-files skills/` 全量统计，`doc-governance` 仅 1 个技能就吃掉了全仓近半江山（注：含本地未追踪 `.pytest_cache` 4 文件则为 36 非 `.pyc` 文件 / 12,904 行 / 613.5 KB）：

| 分层 | 文件数 | 行数 | 字节数 | 占比 | 核心体量异常 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| 规范与模板（`SKILL.md` + 7 ref + 2 tpl） | 10 | 1,193 | 82.5 KB | 13.5% | `SKILL.md` 186 行尚克制，但 `backlog-specification.md` 占 281 行 |
| Python 脚本工具箱（11 `.py` + 1 `.sh`） | 12 | 5,896 | 255.5 KB | 41.7% | **[audit-doc-health.py](../../../skills/doc-governance/scripts/audit-doc-health.py) 达 1,457 行**（超千行红线 +45.7%） |
| 自动化测试套件（10 文件 / 302 用例） | 10 | 5,800 | 274.9 KB | 44.8% | **[test_doc_governance_scripts.py](../../../skills/doc-governance/tests/test_doc_governance_scripts.py) 1,938 行**、**[test_doc_drift.py](../../../skills/doc-governance/tests/test_doc_drift.py) 1,709 行**（双双大幅破千行红线） |
| **Git 追踪合计** | **32** | **12,889** | **598.6 KB** | **100%** | **另含设计书 [doc-governance-design.md](../architecture/doc-governance-design.md) 38.1 KB** |

### 1.2 单壳塞入 9 个异构子系统全景

| # | 子系统 | 核心承载物 | 约占体量 | 职责归属判断 |
| :-: | :--- | :--- | :---: | :--- |
| **①** | Diátaxis / RFC / MADR 写作规程与脚手架 | `SKILL.md` + 5 references + `scaffold-doc.py/.sh` (664 L) | ~42 KB | **规程属公共核心**；但 664 行 bash 仿写脚手架过重 |
| **②** | Markdown 物理断链与 `#anchor` 扫描器 | [check-doc-links.py](../../../skills/doc-governance/scripts/check-doc-links.py) (330 L) | ~14 KB | **唯一被全仓其他技能测试调用过的高普适脚本**（成熟开源替代：`lychee`） |
| **③** | 手写修订历史 5 行滑动窗口裁剪 | [trim-revision.py](../../../skills/doc-governance/scripts/trim-revision.py) (230 L) | ~10 KB | **自造需求闭环**：Git 已原生记录全史，却强迫手写修订表再写脚本裁剪 |
| **④** | 分层 `llms.txt` + `_llms/` 生成与身份保护 | [generate-llms-txt.py](../../../skills/doc-governance/scripts/generate-llms-txt.py) (532 L) + 2 测试 | ~65 KB | 错位把 Web 公开站分发标准做成 Git 本地仓每次提交的逐字节硬阻断 |
| **⑤** | 目录级托管索引（`<dir>/index.md`）维护 | [manage-doc-index.py](../../../skills/doc-governance/scripts/manage-doc-index.py) (372 L) + 704 L 测试 | ~53 KB | 1,076 行代码仅服务全仓 4 个索引文件，配合自造「孤儿扣分」门禁 |
| **⑥** | 真值轴代码锚点漂移检测 + 墓碑账本 | [check-doc-drift.py](../../../skills/doc-governance/scripts/check-doc-drift.py) (807 L) + 1,709 L 测试 | **114.5 KB** | **2,516 行代码仅覆盖 3 篇自引用文档（4.0%）**，却催生 22% 重钉提交税 |
| **⑦** | 控制头同步 + 文档三态 + 体量棘轮 + 百分体检 | [check-doc-control-sync.py](../../../skills/doc-governance/scripts/check-doc-control-sync.py) + `audit-doc-health.py` + 3 测试 | ~103 KB | 把 5 套正交规则揉成 1,457 行巨石；`.doc-size-baseline.json` 当前为 `{}` 空对象 |
| **⑧** | 20 条可回答性黄金断言 + pre-commit 聚合器 | [check-golden-tasks.py](../../../skills/doc-governance/scripts/check-golden-tasks.py) (297 L) + [check-all.py](../../../skills/doc-governance/scripts/check-all.py) (111 L) | ~22 KB | **100% 是本仓 `cr-agent-arsenal` 私有 CI 套件**，完全不该放在公共技能内 |
| **⑨** | **项目管理待办系统（Mini-Jira / Issue-as-File）** | [manage-backlog.py](../../../skills/doc-governance/scripts/manage-backlog.py) (785 L) + `audit_backlog` (245 L) + [backlog-specification.md](../../../skills/doc-governance/references/backlog-specification.md) (281 L) + 测试 (226 L) | **~73 KB**（1,537 行） | **严重越界寄宿！** 含 140 行手写零依赖 YAML 编解码器，因状态语义冲突被迫在 4 处门禁打豁免补丁 |

---

## 2. 12 个脚本跨仓可移植性审计（零修改拷入外部业务仓实测推演【A】）

| 脚本 | 跨仓可移植度 | 精确硬编码证据（`文件:行号`） | 外部普通业务仓运行结局 |
| :--- | :---: | :--- | :--- |
| `check-golden-tasks.py` | **0%** | `L26` `parents[2]`、`L108` `reference/rules/commit-evidence.md`、`L113` `REPO_ROOT/skills/*/SKILL.md`、`L137` `【A】/一手`、`L204` `docs/AGENTS.md` 中文键 | 必然 `rc=1` 满屏 FAIL |
| `check-all.py` | **0%** | `L24` `parents[2]`、`L50,60,81` 写死 `skills/doc-governance/...`、`L75` 必跑 `check-golden-tasks.py`、`L64` 必跑 `--fail-on-drift --staged` | 全局安装后甚至会扫错仓库根并直接失败 |
| `audit-doc-health.py` | **15%** | `L84-98` 强绑 Diátaxis 6 目录、`L211` 中文 `读取顺序/硬约束`、`L476` 中文 `文档状态`、`L729-974` BK-XXXX 审计、`L1041-1048` 缺控制头直扣 25 分跌破 80 门槛 | 几乎必然 REJECTED |
| `scaffold-doc.py` / `.sh` | **30%** | `L32-309` 7 套全中文专有模板、`L634` `--lang` 死参数丢弃、`L503` 仍硬编码推荐已废弃 `scaffold-doc.sh` | 英文仓不可用；任意仓 `--help` 报 `rc=1` |
| `check-doc-drift.py` | **35%** | `L297,321,343` `--staged`/同提交豁免硬编码中文 `"复核于"`、`L783` 无 `.doc-truth-baseline.json` 即 `rc=2` | 英文仓走 `--staged` 失效，首次无账本即 `rc=2` |
| `manage-doc-index.py` | **40%** | `L33,46-75,183,211` 强绑中文控制头与 `修订历史记录` 表格正则 | 仅限采用同套中文控制头仓库 |
| `generate-llms-txt.py` | **55%** | `L171-178` 写死 Diátaxis 6 象限中文名、`L412` 强绑固定英文 H1 模板 | 非 Diátaxis 仓全部落入 `Other` |
| `check-doc-control-sync.py` & `trim-revision.py` | **65–75%** | 依赖本技能自造的「手写控制头版本 + 修订表」契约，硬编码 `project/reviews` 与 `backlog` 豁免 | 常规外部仓基本全程 no-op |
| `manage-backlog.py` | **80%** | 零依赖可独立运行，但输出中文卡片与中文 `index.md` | **可移植但放错了技能归属** |
| **`check-doc-links.py`** | **85%** | 仅 `L26` 硬编码豁免 `project/reviews`，相对路径与 `#anchor` 校验高度通用 | **全套 12 脚本中唯一真正高普适的公共资产** |

---

## 3. 实证「文档治理税」与源码级真实缺陷审计【A】

### 3.1 Git 全史 390 Commits 的治理税量化账单

对仓库建仓至今全部 **390 次提交**执行逐笔变更面统计，结果极具冲击力：

| 指标 | 全史（390 commits） | 近 80 commits | 架构含义 |
| :--- | :---: | :---: | :--- |
| 触及 `skills/doc-governance/` | **92（23.6%）** | **35（43.8%）** | 近期近半数提交都在修补或堆叠文档治理自身 |
| 触及 `docs/llms.txt` 或 `_llms/` | **80（20.5%）** | **19（23.8%）** | 每 5 次提交就有 1 次被迫顺手重生成机器地图 |
| **纯 `docs/` + `doc-governance/` + `.githooks/` 提交** | **194（49.7%）** | **62（77.5%）** | **全史一半、近期近八成提交没有产出任何业务/其他技能代码** |
| 卷入文档治理/门禁/索引/复核点/Backlog 税并集 | **271（69.5%）** | **71（88.8%）** | 治理仪式已成为全仓最沉重的工程成本项 |
| 近 50 commits 纯「重钉 `复核于 SHA` / 修重钉格式」提交 | — | **≥11 / 50（22%）** | `check-doc-drift.py` 引发的典型**自激振荡噪音**（如 `a38cc85` 脚本漏填 SHA 紧接 `c45c71f` 修换行） |

### 3.2 实证揪出的 7 处真实源码 Bug 与契约漂移（均经主智能体源码复核【A】）

复杂的自建门禁体系已开始反噬自身正确性：

1. **死参数 Bug #1（`audit-doc-health.py:1207-1233`）**：CLI 声明并解析了 `--max-doc-bytes` 与 `--max-doc-line`，但在调用 `audit_health()` 时完全未透传，体检模式下用户传入阈值静默失效；
2. **死参数 Bug #2（`scaffold-doc.py:29, 634`）**：`--lang zh|en` 解析后赋给 `_lang` 丢弃，传英文照样输出全中文；且 `--help` 直接返回 `rc=1`；
3. **行区间锚点空承诺（`check-doc-drift.py:114-120, 579`）**：解析了 `path:start-end` 行区间却在查 Git 时剥离行号，退化为文件级 `git log -1 -- path`，改动文件任意无关行均误报全篇漂移；
4. **规范与代码漂移（`docs/GOVERNANCE.md:142` vs `audit-doc-health.py:333-343`）**：规范白纸黑字宣称 `docs/reference/articles/**` 豁免体量三指标，但 `_size_docs()` 实际只排除了 `reviews` / `_llms` / `AGENTS.md`，根本没排除 `reference/articles`（一旦新增 >64 KB 转摘文献即违规阻断）；
5. **技能自身版本漂移（`references/change-impact-matrix.md:4` vs `L73`）**：控制头写 `V1.3.1`，底部修订表首行已到 `V1.4.0`；`L34` 还将表格第 8 行误写为「第 7 行」；
6. **MADR 规范内部自相矛盾（`references/adr-specification.md:40-45` vs `audit-doc-health.py:1041-1048`）**：MADR 3.0 模板天生无版本号字段，体检脚本却强扣无 `当前版本` 文档 25 分，倒逼脚手架私自往 ADR 里塞修订表；
7. **`check-all.py` 文案/修复建议错误 + 双重全量扫描 I/O 浪费（`check-all.py:6, 10, 60` + `audit-doc-health.py:73-77`）**：docstring 写「五道门禁」实跑六道；L60 版本一致失败错误推荐 `trim-revision.py --fix`（裁行修不好版本号不一致）；且 `check-all.py` 先跑 4 个子脚本，第 5 步 `audit-doc-health.py` 又用 `importlib` 把这 4 个脚本全量重跑一遍，导致每次 `pre-commit` 单篇文档被重复读盘 **6–8 次**！

此外还存在跨脚本大面积复制粘贴（`in_evidence_archive()` 在 **6 个脚本**里逐字复制、`parse_frontmatter()` 两套分叉实现），以及旧仓库路径 `/home/hui/workspace/projects/cr-public-skills`（`doc-governance-design.md:317, 401`）与旧项目 `DeepResearcher` / `file:///` 违规链接（`backlog-specification.md:77`）残留【A】。

---

## 4. 真正值得保留的 4 项核心护城河

瘦身绝不意味着放弃文档工程严肃性；以下 4 项是 `doc-governance` 真正高价值、应予提纯保留的真资产：

1. **Diátaxis 写作纯度边界与 RFC → Diátaxis 结晶生命周期**：防止文档变成“大杂烩”，明确临时提案（`proposals/`）向长期真相源（`reference/`、`explanation/`、`how-to/`）结晶归位的纪律；
2. **纯正 MADR 3.0 架构决策流**：将不可逆架构选型与背景/备选/后果沉淀为 Append-Only 的 ADR 记录；
3. **代码变更 → 文档影响面联动核查清单**：提醒 Agent 在改动契约、模型或流程时同步更新关联文档（经修复版本漂移后精简保留）；
4. **轻量零依赖物理断链扫描器 `check-doc-links.py`**：作为目标环境未安装 `lychee` 时的开箱即用兜底校验（剥离硬编码 `project/reviews`，改为通用 `--exclude` 参数）。

---

## 5. 三刀切割重构路线图与三档执行方案【C】

### 5.1 「三刀切割」架构瘦身蓝图

| 切刀 | 剥离对象与规模 | 新归属 / 替代方案 | 直接收益 |
| :---: | :--- | :--- | :--- |
| **第一刀：公私分离** | `check-golden-tasks.py` (297 L)、`check-all.py` (111 L) 及对应测试 | 迁出 `skills/doc-governance/` 至**仓库根私有工具目录 `scripts/doc-gates/`**（随 `.githooks/pre-commit` 仅服务本仓） | 公共技能瞬间清除 0% 可移植的本仓私有断言 |
| **第二刀：拆出 Mini-Jira** | `manage-backlog.py` (785 L) + `backlog-specification.md` (281 L) + `audit_backlog` (245 L) + 测试 (226 L) = **1,537 行 / ~73 KB** | 独立为可选微技能 `file-backlog`（或仅留本仓 `scripts/`；通用仓库直接用 GitHub Issues / Linear） | 消除最大跨界寄生，清空 4 处门禁里的 backlog 豁免补丁 |
| **第三刀：去仪式税与自激振荡** | ① 废除每篇文档强制手写版本号+修订表 → 退役 `trim-revision.py` (230 L) + `check-doc-control-sync.py` (306 L)；<br>② `check-doc-drift.py` + 测试（**2,516 行**）改用 Git 拓扑祖先（`git merge-base --is-ancestor`，如 `addyosmani` 6 行模式）或异步巡检，取消手钉 `复核于 SHA`；<br>③ `llms.txt` / `_llms/` / `manage-doc-index.py`（~118 KB）退出同步 `pre-commit` 硬阻断，降级为按需可选工具；<br>④ 拆解 1,457 行 `audit-doc-health.py` 与空 `.doc-size-baseline.json`，优先推荐 `lychee` + `markdownlint-cli2` + `vale` | 公共技能核收敛为 **Convention-First（先适配宿仓既有规范）**的轻巧规范集 + 通用可配置 `check-doc-links.py`（~250 行） | **公共技能体量从 598.6 KB 暴降至 ~45–65 KB（-90%）**；彻底消灭 22% 重钉 SHA 提交税与 20.5% `llms.txt` 刷写税 |

### 5.2 三档决策方案对比

| 方案 | 范围 | 预计技能体量变化 | 优点 | 代价与风险 |
| :--- | :--- | :---: | :--- | :--- |
| **方案 A（推荐）：三刀完整重构（公私分离 + 拆 Backlog + 去仪式税）** | 公共 `doc-governance` 瘦身为 Convention-First 轻内核 + 通用 `check-doc-links.py`；本仓私有门禁下沉 `scripts/doc-gates/`；Backlog 独立；退役手写修订表、2,516 行重型 drift 与强制 `llms.txt` pre-commit | **598.6 KB → ~55 KB（公共核 -91%）** | 一次根治 God Skill、跨仓 0% 可移植、7 处代码 Bug 与 77.5% 近期治理税；公共技能重获可对外分发能力 | 需更新 `docs/GOVERNANCE.md`、`.githooks/pre-commit` 与相关 RFC 状态流转（`RFC-0005/0006/0008`），工程量属 Heavy Track |
| **方案 B（温和渐进）：先做第一、二刀 + 修 7 处 Bug（暂留本仓现有门禁口径）** | 仅把 `check-golden-tasks.py`/`check-all.py` 移出公共技能、将 `manage-backlog.py` 拆出独立模块、修复 7 处源码 Bug 与重复扫描 I/O 浪费、合并 6 处重复 `in_evidence_archive` 到共享模块 | **598.6 KB → ~360 KB（-40%）** | 不改变本仓现有 `GOVERNANCE.md` 治理习惯与历史 RFC 契约，风险可控 | 仍保留高维护税的 `check-doc-drift.py`（4% 覆盖率）与 `llms.txt` 强同步负担 |
| **方案 C（最小止血）：原地不动架构，仅修 7 处实证 Bug 与超千行拆分** | 透传 `--max-doc-bytes`、修 `--lang` 与 `reference/articles` 豁免、修 `check-all` 重复扫描与错误提示、拆分 3 个超千行文件、清旧仓路径 | ~598 KB（基本不变） | 零契约变动，改动极小 | 无法解决跨仓不可移植、God Skill 膨胀与高达 22% 的重钉 SHA 治理税 |

> **实施前置提醒**：由于 `doc-governance` 牵动 `.githooks/pre-commit`、`docs/GOVERNANCE.md` 及多份已实现 RFC，无论选用方案 A 还是方案 B，建议作为独立 Heavy Track 专项实施，并先以 ADR 明确「公共技能面 vs 本仓私有治理面」的永久边界。
