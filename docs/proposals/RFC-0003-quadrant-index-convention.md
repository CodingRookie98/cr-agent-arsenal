# RFC-0003: 目录级索引约定与 scaffold 索引自愈

> **提案元数据**
> - **标识**: RFC-2026-QUADRANT-INDEX-CONVENTION
> - **当前状态**: In Review
> - **发起人**: 工程师 / AI Agent
> - **当前版本**: V0.3.0
> - **初次发起日期**: 2026-10-09
> - **目标里程碑**: doc-governance V2.0.0（技能内部一致性收敛，不涉及仓库版本号变更）

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V0.3.0** | 2026-10-09 | DSH AI Agent | 王辉 | 依 Delta 审查裁决修订：§7.3 DA-2 并发后果描述更正为「静默丢弃登记行」（原「重复行」不实）；托管标记判据明确为位置契约、README 入口按 DA-4 跳过；门禁不变式 GI-1/GI-4 补充入参校验与防 ghost 登记语义 |
| **V0.2.0** | 2026-10-09 | DSH AI Agent | 王辉 | 补全术语表、决策台账与门禁不变式；P-1 裁定采用「方案 A（象限索引托管化 + 规范登记 + scaffold 自愈）」 |
| **V0.1.0** | 2026-10-09 | DSH AI Agent | 王辉 | 脚手架初始化，登记象限索引未定义区缺陷与三类候选方案 |

---

## 1. 背景与业务痛点 (Why)

### 1.1 现象：模板断言了一份规范未登记、脚本也不会生成的索引

`doc-governance` 的脚手架生成器 `scaffold-doc.sh` 在 `tutorial` 分支的产物模板中硬编码了一条跨象限链接：

```markdown
- 探索更多实战操作: [how-to 指南](../how-to/index.md)
```

但 `docs/how-to/index.md` 在本技能的目录拓扑（[SKILL.md:59](../../skills/doc-governance/SKILL.md) 与 [设计书 §3](../explanation/architecture/doc-governance-design.md)）中**从未被登记**，脚手架自身也**不会创建**它。实测（隔离临时根目录，仅含该模板产物）：`check-doc-links.py` 返回 **Exit Code 1**，报 `目标路径不存在 (404 Not Found)`。

### 1.2 根因：象限索引处于「未定义区」

| 视角 | 现状 |
|:---|:---|
| 规范（SKILL.md / 设计书 / GOVERNANCE） | 拓扑只登记根级 `docs/index.md`，**未定义**象限/子目录级 index.md 的地位 |
| 门禁脚本（check-doc-links.py:173-177） | 已实测支持多层：链接指向目录时，要求该目录含 `index.md` 或 `README.md` |
| 门禁脚本（audit-doc-health.py:447-451） | 已实测支持多层：任意层级的 `index.md`/`README.md` 均豁免孤儿判定 |
| 脚手架（scaffold-doc.sh） | 只有 `backlog` 分支做了索引同步（调 `manage-backlog.py sync-index`），其余分支断链自愈能力为零 |

即：**门禁与健康度体系早已承认"目录即入口"，只有规范与脚手架没有跟上**。规范缺位使象限索引既不被要求、也不被生成，模板却单方面假设它存在。

### 1.3 后果

1. **断链逃逸**：脚手架直接产出 404 链接，且现有回归测试 `TestScaffoldDocSh.test_scaffold_all_types` 只断言"文件已生成"，**不做断链闭环**，故缺陷长期不可见；
2. **规范悬空**：使用者在 `docs/` 下新建象限索引时无规可依（是否要控制头？谁维护？与根索引什么关系？）；
3. **知识库漂移**：本仓库已存在唯一的下层级索引实例 `docs/project/backlog/index.md`（由脚本自动维护），但该形态在规范中同样无定义，属于"事实先于规范"的隐性负债。

### 1.4 旁证：既有脚本已具备"目录即入口"的判定逻辑

`check-doc-links.py` 与 `audit-doc-health.py` 的实现（见上表）证明：多层级索引不是新增能力，而是**已实现但未成文**的约定。本提案不修改其判定语义，只把既有事实提升为规范并补齐生成侧。

---

## 2. 目标与非目标 (Goals & Non-Goals)

### 2.1 核心目标 (Goals)

- [ ] **G1 补规范**：在 SKILL.md、设计书、GOVERNANCE.md 中显式登记"目录级索引约定"，明确根级索引与象限索引的地位、形态与维护责任；
- [ ] **G2 脚本自愈**：`scaffold-doc.sh` 在生成任意象限文档后，自动确保该象限索引存在并**幂等登记**本文档；
- [ ] **G3 链接降级**：消除 `tutorial` 模板的硬编码断链——目标象限索引存在时保留链接，不存在时降级为纯文本提示；
- [ ] **G4 回归防护**：新增测试用例，建立"脚手架产物 → 断链审计/版本同步审计"的闭环断言，杜绝同类缺陷再次逃逸；
- [ ] **G5 零门禁回归**：交付后 `check-doc-links.py` / `check-doc-control-sync.py` rc=0，`audit-doc-health.py` 得分不下降。

### 2.2 明确非目标 (Non-Goals / 防蔓延红线)

- **N1 不追溯补齐**：不为本仓库现存目录批量补建 `index.md`（不产生空索引污染），仅由 scaffold 按需生成；
- **N2 不改门禁判定语义**：`check-doc-links.py`、`audit-doc-health.py`、`check-doc-control-sync.py` 的规则与阈值保持原样；
- **N3 不自动化根索引**：`docs/index.md` 保持人工维护与总入口地位，脚本不得改写；
- **N4 不新增 CLI 开关**：`scaffold-doc.sh` 的调用接口（`<type> <name> [--root] [--lang]`）不变，自愈行为内建；
- **N5 不处理 README.md 入口**：既有 `project/reviews/**/README.md` 形态维持现状，脚本不生成也不改写 README.md。

---

## 3. 核心设计与契约草案 (How - Technical Draft)

### 3.1 索引分层契约

| 层级 | 文件 | 地位 | 维护者 | 是否强制 |
|:---|:---|:---|:---|:---|
| 根级 | `docs/index.md` | **唯一**全局人类总索引入口（全景拓扑与分类） | 人工 | 强制存在 |
| 根级（机器） | `docs/llms.txt` | 机器可读拓扑地图 | `generate-llms-txt.py` | 强制存在 |
| 象限/子目录 | `<dir>/index.md` 或 `<dir>/README.md` | 层级**分流**入口 | 托管（脚本）或人工 | 按需 |
| 治理规程 | `docs/GOVERNANCE.md` | 分类、生命周期与门禁规则 | 人工 | 强制存在 |

**不变式**：指向目录的 markdown 链接，其目标目录必须含 `index.md` 或 `README.md`（沿用既有门禁规则，不新增判定）。

### 3.2 托管索引文件契约 (Managed Index)

由 scaffold 自动创建的象限索引必须满足：

1. **机器标记**：正文首行（H1 之后）含 HTML 注释 `<!-- doc-index:managed -->`，作为"脚本托管、允许自动变更"的唯一判据；
2. **标准控制头**：`文档标识` / `当前版本` / `文档状态` / `生效日期` / `文档所有者`，满足 `audit-doc-health.py` 元数据基线；
3. **修订历史表**：与 `check-doc-control-sync.py` 的提取规则兼容，控制头版本 == 修订表最新行版本；
4. **文档清单段**：形如 `## 文档清单`，登记行格式 `- [<标题>](./<file>.md) — <类型>`；
5. **版本联动**：每次登记追加清单行时，同步升补丁版本（`V1.0.0 → V1.0.1`）并在修订表首行插入对应记录，修订历史恒 ≤ 5 条（治理红线）。

**人工索引（无托管标记）为只读对象**：脚本检测到已存在的 `index.md` 不含托管标记时，**一律不改写**（ensure 与 register 均 no-op），仅输出提示。

### 3.3 脚本接口契约

新增 `scripts/manage-doc-index.py`（与 `manage-backlog.py` 同构的"配套索引脚本"）：

```bash
# 确保象限索引存在（不存在则创建托管骨架；已存在则 no-op）
python3 manage-doc-index.py ensure --root docs --dir how-to [--title "操作指南"]

# 幂等登记：ensure + 追加清单行 + 升补丁版本（已登记则 no-op，不重复升版本）
python3 manage-doc-index.py register --root docs --dir how-to --file deployment.md --title "生产部署 SOP" --kind HowTo
```

**退出码**：`0` = 成功或安全 no-op（含"检测到人工索引，跳过"）；非 0 = 真实故障（目录不可写、参数非法）。

### 3.4 脚手架集成契约

| 分支 | 索引目录 | 行为 |
|:---|:---|:---|
| `tutorial` | `tutorials` | register + 跨象限链接按 §3.5 降级判定 |
| `how-to` | `how-to` | register |
| `reference` | `reference` | register |
| `explanation` | `explanation` | register |
| `adr` | `explanation/decisions` | register |
| `rfc` | `proposals` | register |
| `backlog` | —（形态 B 专属） | 维持既有 `manage-backlog.py sync-index` 不变 |

调用模式沿用脚本既有的 `SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` 解析；索引自愈失败**不阻断**主产物生成，但必须打印显式警告（避免静默失配）。

### 3.5 链接降级契约 (Link Degradation)

`tutorial` 模板的"下一步探索"段为**条件渲染**：

- 若 `<root>/how-to/index.md` 存在 → 保留 `[how-to 指南](../how-to/index.md)`；
- 否则 → 降级为纯文本：`探索更多实战操作：运行 \`scaffold-doc.sh how-to <name>\` 创建 \`how-to/\` 象限指南`（不产生任何相对链接）。

该设计刻意**不**为一条装饰性链接去创建无关象限目录（最小副作用）。

### 3.6 门禁不变式 (Gate Invariants)

- **GI-1**：任意类型脚手架产物必须通过 `check-doc-links.py`（rc=0）；
- **GI-2**：托管索引必须通过 `check-doc-control-sync.py`（rc=0）；
- **GI-3**：`register` 幂等——重复执行不新增清单行、不重复升级版本；
- **GI-4**：人工索引零改写（逐字节不变）；
- **GI-5**：`audit-doc-health.py` 得分不下降（新增文件须携带控制头，不得拉低元数据基线率）。

---

## 4. 备选方案权衡与争议焦点 (Alternatives & Trade-offs)

### 方案 A（本提案选定）：象限索引托管化 + 规范登记 + scaffold 自愈

在规范中确立分层索引契约，新增索引脚本，脚手架按象限自动 ensure + register，模板断链按需降级。
**优点**：根治断链根因；规范与实现同时对账；复用既有"目录即入口"判定，零门禁语义变更；托管标记保证人工索引安全。
**代价**：新增一个脚本（约 150~200 行）与配套测试；登记涉及版本联动，实现需谨慎。

### 方案 B（未采纳）：仅修模板链接（最小改动）

把 `scaffold-doc.sh:99` 的链接改为 `../index.md` 或直接删除。
**优点**：改动最小、零新增文件。
**未采纳理由**：只消除症状，不解决"象限索引无规范地位"的根因；且门禁与健康度体系已支持多层级索引这一事实仍悬空，下一位使用者在 `docs/` 下建索引时依然无规可依。用户明确选择"补规范 + 脚本自愈"组合，B 被显式排除。

### 方案 C（未采纳）：强制所有象限标配 index.md + 追溯补齐

要求 Diátaxis 四象限与所有子目录必须存在索引，并一次性补齐本仓库现存目录。
**未采纳理由**：与"精益知识库"冲突——会批量产生空索引（本仓库 `tutorials/`、`how-to/` 目录当前并不存在），显著扩大改动面并拉低信噪比；强制性与"按需生成"相比缺乏收益。

### 争议焦点与裁决

| 焦点 | 裁决 |
|:---|:---|
| 是否强制每个象限必须有索引？ | **否**。按需生成；只有"被链接指向的目录"才必须含入口（既有门禁）。 |
| 托管索引是否纳入版本治理？ | **是**。携带标准控制头并随登记升补丁版本，避免拉低 `audit-doc-health.py` 元数据基线率，同时守住版本漂移门禁。 |
| tutorial 是否需要为 how-to 建目录？ | **否**。采用降级（§3.5），避免装饰性链接造成目录污染。 |
| 根索引是否自动登记？ | **否**。根索引为人工总入口（N3）。 |

---

## 5. 术语表与易歧义对齐 (Glossary & Terminology Alignment)

### 5.1 核心术语定义 (Core Term Definitions)

| 术语 | 定义 |
|:---|:---|
| **根级索引 (Root Index)** | `docs/index.md`，全库唯一的人类总入口，人工维护，纳入版本治理 |
| **象限索引 (Quadrant Index)** | 位于 `docs/` 下任意子目录的 `index.md`，承担该目录的分流导航，**非强制、按需存在** |
| **托管索引 (Managed Index)** | 含 `<!-- doc-index:managed -->` 标记的象限索引，由 `manage-doc-index.py` 创建与登记 |
| **人工索引 (Hand-authored Index)** | 不含托管标记的象限索引，脚本只读不改 |
| **索引自愈 (Index Self-Healing)** | 脚手架生成文档后自动 ensure 象限索引并登记本文档的行为 |
| **链接降级 (Link Degradation)** | 目标象限索引不存在时，模板将该链接渲染为纯文本提示，避免 404 |
| **象限 (Quadrant)** | 本提案中的泛称：Diátaxis 四象限目录（tutorials/how-to/reference/explanation）及 proposals、project 等顶层分区 |

### 5.2 易歧义与同义词裁决 (Ambiguity & Synonym Resolution)

| 歧义点 | 裁决 |
|:---|:---|
| "顶层 index.md" vs "文档索引" | **顶层索引唯一**（`docs/index.md`）≠ **索引机制唯一**。后者还包含 `llms.txt`（机器地图）与象限索引（分流入口） |
| `index.md` vs `README.md` | 在"目录入口"判定上**等价**；本提案只生成/维护 `index.md`，不触碰 `README.md`（N5） |
| "文档清单" vs 根索引的分类索引 | 象限索引的清单只收录**本目录**直属文档；跨象限收录仍归根索引 |
| "自动生成" vs "自动改写" | 托管索引允许自动改写；人工索引仅允许"检测不改写" |

### 5.3 禁用称谓与历史别名

- 禁用"二级索引""子索引"等含混表述，统一使用**象限索引**；
- 禁用"脚本生成索引"泛指，须区分**托管索引**（可自动变更）与**人工索引**（只读）。

---

## 6. 未决问题与对齐清单 (Open Questions & Grilling Checklist)

- [x] 象限索引是否强制？ → 否（§4 裁决）
- [x] 是否追溯补齐现存目录？ → 否（N1）
- [x] 门禁脚本是否需改？ → 否（N2；判定逻辑已支持多层级）
- [x] 是否新增 CLI 开关？ → 否（N4；自愈内建，保持接口稳定）
- [ ] `skills-lock.json` 的 `computedHash` 是否随 SKILL.md 变更同步刷新？ → 实施阶段确认（仓库内无校验实现，但需保持锁文件自洽）

---

## 7. 决策台账与默认假设 (Decision Ledger & Default Assumptions)

### 7.1 已决项 (Settled Decisions)

| 编号 | 决策 | 依据 |
|:---|:---|:---|
| DK-1 | 采用方案 A（补规范 + 脚本自愈 + 链接降级） | 用户 P-1 裁定 |
| DK-2 | 象限索引按需生成，不强制、不追溯补齐 | §4 裁决 / N1 |
| DK-3 | 托管索引携带标准控制头并随登记升补丁版本 | GI-5 / 治理红线 |
| DK-4 | 人工索引零改写（托管标记为唯一判据） | GI-4 |
| DK-5 | 新增 `manage-doc-index.py` 而非在 bash 内联实现 | 可测试性优先；与 `manage-backlog.py` 既有先例同构 |
| DK-6 | 执行后端 = 当前会话内联；分支 = `feature/quadrant-index-convention` | 用户 P3 前置裁定 |
| DK-7 | 交付通道 = Heavy Track（触及技能公共契约） | goal-loop 铁律 8 |

### 7.2 已排除边界 (Explicitly Excluded Boundaries)

| 编号 | 排除项 | 排除依据 |
|:---|:---|:---|
| EX-1 | 仅修模板链接（方案 B） | 用户显式选择补规范组合；B 不解决根因 |
| EX-2 | 强制象限索引 + 批量补齐（方案 C） | 与精益原则冲突，改动面失控 |
| EX-3 | 修改门禁脚本判定语义 | 无必要（既有逻辑已支持），且会扩大公共契约面 |
| EX-4 | 自动化根索引 `docs/index.md` | 根索引为人工 SSOT |

### 7.3 默认假设 (Default Assumptions)

| 编号 | 假设 | 若假设不成立的影响 |
|:---|:---|:---|
| DA-1 | 托管索引的"文档清单"只需收录 scaffold 生成的文档；人工新增的文档可手工补登记 | 清单完整性略降，不影响门禁 |
| DA-2 | 单进程顺序调用 scaffold，无并发写索引场景 | 极端并发下为**静默丢弃登记行**（非重复行；R2 终审按 YAGNI 否决加锁与原子替换，避免投机性加固）。当前无此用法，若并行脚手架成为常态用法再重新定级 |
| DA-3 | `--root` 指向 `docs`；脚本按传入 root 相对生成索引 | 自定义 root 亦正确（实现按参数解析） |
| DA-4 | 象限索引文件名固定为 `index.md` | 若项目既有 `README.md` 入口则不生成（N5），链接需人工处理 |

### 7.4 矛盾扫描记录 (Contradiction Scan)

| 检查项 | 结论 |
|:---|:---|
| 核心业务目标是否仍有未明确？ | 否——G1~G5 与验收场景逐条可测 |
| 关键边界与异常是否未确认？ | 否——已覆盖"人工索引已存在""目录不存在""重复登记""降级分支"四类边界 |
| 已决项之间是否互相矛盾？ | 否——N1（不追溯）与 G2（按需生成）方向一致；DK-3（升版本）与 GI-2（版本同步门禁）自洽 |

---

## 8. 结晶去向预告 (Crystallization Preview)

| 结晶物 | 去向 |
|:---|:---|
| 分层索引契约（§3.1~3.2） | `SKILL.md` 目录拓扑与新增"目录级索引约定"节 |
| 脚本接口与集成契约（§3.3~3.5） | `docs/explanation/architecture/doc-governance-design.md` |
| 治理规程同步（§3.6） | `docs/GOVERNANCE.md` 目录拓扑 |
| 变更联动要求 | `references/change-impact-matrix.md` |
| RFC 本体 | 交付后流转 `Implemented` 并置防腐声明（`proposals/archive/`） |
