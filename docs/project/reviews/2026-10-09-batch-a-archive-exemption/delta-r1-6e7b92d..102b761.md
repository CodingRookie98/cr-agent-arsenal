# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **混合体 —— 写入侧硬化是本质根因修复，单文件同构判定为半根治，文档/索引/健康度为实质闭合，唯上轮唯一阻断项 R1-1 未根治（仅换了一种更隐蔽的形式）。**
  - **① 归档写入侧（R1-2）= 本质根因修复**：新增 `is_archive_path()`（不依赖 `--root` 的路径段扫描）并同时挂到目录遍历与单文件两个入口后，CLI 面 8 种 `--root` 形态全部只读（实测见下），`audit-doc-health.py` 自愈建议链可达的三种收窄根（`.` / `docs/project` / `docs/project/reviews`）均已闭合。这是对「root 锚定词法前缀在非 docs 根下不成立」这一**根因**的直接处理，不是外层 `try/except` 式补丁。
  - **② 单文件同构（R1-3）= 同构已根治、结论语义半根治**：两入口的**判定**已统一（同一枚 `is_archive_path()`），「同文件两入口结论相反」的病态消失；但被拒检后脚本仍以 rc=0 在 **stdout** 打印 `共检查 0 个文件` + `✅ 完美！所有文档的修订历史记录行数均 <= 5 条，符合滑动窗口规范！` —— 豁免说明只落在 stderr，上轮明确要求的「禁止输出『完美』结论性文案」未落地。
  - **③ 交付物一致性（R1-1）= 未根治**：head 树上按 `docs/GOVERNANCE.md:87` 注册命令重生成，产物与提交物**仍非逐字节一致**（sha256 `250dc7c1…` vs `899c2b4e…`，命中且仅命中 1 行）。上一轮阻断项的判定属性（交付物 ≠ 生成物 / 刷新即脏树 / 零门禁可检出）**原样成立**，只是从「H1 错 + 缺 1 条」两处显式漂移收缩为「条目描述滞后」一处隐式漂移。
  - **④ 文档闭合（R1-4/R1-5/R1-6）= 实质闭合**：health 100.0/100、孤儿 0/51；`GOVERNANCE.md:109-113` 五行齐备且与全仓消费者集合相等；`68 − 17 归档 − 2 根文件 = 49` 逐项实测成立。

- **物理与业务一致性**（全部为隔离树真实调用，未采信任何自述）：
  - **R1-1 反证链（决定性）**：`git archive 102b761` 还原到 /tmp 后执行注册命令 `python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output <out>`：
    - 提交物 `docs/llms.txt` = `250dc7c1fd1e89dd56d1383b6850b3bd84c5fe8e24efeae3f557f001825c6cc7`（49 条、H1 `System`、归档条目 0）；
    - 生成物 = `899c2b4e0aca61a3451c43ebf85435d88798978fadde804586c19c9a863e5354`（49 条、H1 `System`、归档条目 0）；
    - `diff` 结果唯一：第 63 行，提交物**无描述**，生成物**带描述**「R1 判定：三项待办**技术内核均为本质根因修复**（经 git archive 隔离三树 A/B 反证：…」（120 字截断）。
    - **机理已反证到确定性**：把 head 树的 `docs/project/plans/2026-10-09-backlog-batch-a-archive-exemption.md` 换成 **6e7b92d 版本**（即尚无 §5.1）后重生成，产物与提交物**逐字节一致**。即 102b761 的机器地图是在计划文档 §5.1 落盘**之前**生成的 —— 同一提交内交付物滞后于其自身内容，与 6e7b92d 的那次漂移同源（先出图、后改文）。
    - 提取器口径坐实：`extract_doc_info` 模式 B 取「首个非标题/非引用/非表格/非列表正文行」；base 版计划书该值 = 空串，head 版 = §5.1 段落（`…-backlog-batch-a-archive-exemption.md:64`）。因此任何人在 head 上刷新一次地图，都必然改写受版本控制文件。
  - **R1-2 实测矩阵（CLI 面全绿）**：合成树 `docs/project/reviews/report.md`（7 行修订表）+ 对照 `docs/sub/normal.md`，`--fix` 逐入口复算 —— `--root .` / `--root docs` / `--root docs/project` / `--root docs/project/reviews` / 绝对仓库根：归档 SHA256 **UNCHANGED**，对照文件正常裁剪（`[FIXED] normal.md`，共检查 1 个文件）；cwd 陷阱组（在归档目录内 `--root .`、在 `docs/project` 内 `--root reviews`、`--root ./`、`--root ./docs/project/../../docs/project/reviews`）：归档 **UNCHANGED**（`main()` 的 `Path(args.root).resolve()` 把相对形态归一为绝对形态，使段扫描生效）。R1-2 在 CLI 契约面**闭合**；残余仅存在于库调用面（DR1-2）。
  - **R1-2 机器地图侧**：`--root docs` → 1 条（不含 reviews）、`--root docs/project` → 1 条（不含 reviews，新豁免生效）、`--root docs/project/reviews` → 0 条、`--root .` → 1 条（不含 reviews）。上轮「深根重生成令归档条目整体回流」的攻击路径**失效**。
  - **R1-6 口径复算**：head 树 docs 下 md **68**（8ea3f65 = **67**，增量恰为同批次计划文档）、归档 **17**、根级 md **2**（`index.md`/`GOVERNANCE.md`），机器地图条目 **49** —— `68 − 17 − 2 = 49` 逐项吻合；「归档条目 17 → 0」成立（唯一 `project/reviews` 字面命中在第 61 行 `2026-10-04-review-report-archive.md` 条目的**描述文本**里，非条目链接，不构成归档收录）。
  - **R1-4/R1-5 复算**：head 树与真实工作树 `audit-doc-health.py --root docs` 均为 `总得分: 100.0 / 100`、`孤立文档: 0/51`、`PASS`；`check-doc-links.py` rc=0（51 文件）、`check-doc-control-sync.py` rc=0（29 文件，无版本漂移）；`docs/index.md` V1.20.0（:5）与修订行（:15）一致且修订表裁剪回 5 行（V1.15.0 出窗），本批次计划已登记（:79）；`GOVERNANCE.md:109-113` 登记 5 行，与 `grep -l EVIDENCE_ARCHIVE_PARTS` 得到的 5 个脚本集合**完全相等**，无漏登（scaffold/manage/backlog 不触及归档）。
  - **不一致项（登记）**：计划书检查点（`…-backlog-batch-a-archive-exemption.md:29`）载「llms.txt 以注册命令重生成可复现：49 条、H1 `System`、归档条目 0」——「49 条 / H1 / 归档条目 0」为真，「**可复现**」为伪（一行 `diff` 即可证伪）；另 §5.1 的 R1-3 行称「补 3 条覆盖用例」，实际本区间新增 **4** 条测试方法（pytest 60→64），属同一类「文档计数与实际不符」的残留口径偏差。

- **过度设计审计**: **无过度设计，YAGNI 禁令遵守**。本区间新增实体仅：两个脚本各 1 个 9 行纯函数（逐字节同构副本，与既有 3 份 `in_evidence_archive` 副本同一「以重复换隔离」范式）、2 处 `or is_archive_path(...)` 调用点、4 条回归用例；**未**引入裁决语义解析器、**未**引入 `.docignore` 配置机制、**未**做共享模块重构。纯函数无副作用、无 I/O、无全局态。唯二需登记的语义代价：判定面超出登记边界（DR1-1）、`--output` 缺省落点在归档根下会写入归档（DR1-3），均 P3。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）
> 未激活（非客户端/SSR 改动）

- **Rules of Hooks 合规性**: 未激活（本区间无 `*.tsx`/`*.jsx`/`*.vue`/`*.svelte`，无 `react`/`next` 导入，仅 Python 治理脚本 + Markdown + 机器地图）
- **SSR 水合与 Storage 防御**: 未激活（无 `localStorage`/`sessionStorage`/`window` 访问面，无首次渲染路径，无水合失配与沙盒 `SecurityError` 语义）
- **渲染纯度与全局可变状态**: 未激活（无 render 阶段、无跨组件全局单例）。与之等价的写盘风险面为 `trim-revision.py` 的 `--fix` 就地改写（`:161` 调用点、`:203` 落盘），已按数据完整性/凭据指纹维度在 §3 攻击路径 1/3/4 与 §4 表中覆盖

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

- **攻击路径 1: 交付物滞后于自身内容 —— 任何人跑一次注册命令即得脏树（R1-1 未根治）**
  - **触发条件**: 任何人依 `docs/GOVERNANCE.md:87` / `skills/doc-governance/SKILL.md:142` 的注册命令 `python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt` 在 head 树上刷新一次机器地图（这正是计划书 §3 自己登记的收尾动作）。
  - **复现推演**: `git archive 102b761` → 生成 → `docs/llms.txt` 第 63 行被改写为带描述版本；反向验证：把 head 树的计划文档回退到 6e7b92d 版本再生成，产物与提交物逐字节相同。时序为「先落 §5.1 前的地图 → 再写 §5.1 → 未再生成」，与 6e7b92d 那次的「先出图 → 后落计划文档」是同一根因的镜像。
  - **影响结果**: (a) 交付物与生成器在该树上的输出不一致，上一轮阻断项的判定属性成立；(b) 交付凭据自述（计划书检查点 `:29`「可复现」）被一行 `diff` 证伪，属**验证声明失真**；(c) 该文件仍**零门禁消费**（全仓仅 `generate-llms-txt.py` 写入、`audit-doc-health.py:450` 按文件名跳过、测试只在自己临时树里生成），漂移不可机械检出；(d) 智能体读到的本批次计划条目缺少描述，导航信息弱化。
  - **涉及代码**: `docs/llms.txt:63`；`docs/project/plans/2026-10-09-backlog-batch-a-archive-exemption.md:29,64`；`skills/doc-governance/scripts/generate-llms-txt.py`（`extract_doc_info` 模式 B + `:105` 收录循环）。

- **攻击路径 2: 假绿残留 —— 零文件被检却宣告「完美」（R1-3 半根治）**
  - **触发条件**: 以单文件形态把归档报告接入门禁：`trim-revision.py --root <...>/docs/project/reviews/report.md`（check 模式或 `--fix` 皆可），或在 CI 中以 `--root docs/project` / `--root docs/project/reviews` 运行。
  - **复现推演**: 豁免分支置空 `md_files` → `total_scanned = 0` → `:197-199` 打印 `📊 审计汇总: 共检查 0 个文件` 与 `✅ 完美！所有文档的修订历史记录行数均 <= 5 条，符合滑动窗口规范！`，rc=0；豁免说明只进 stderr（`:153`）。目录形态落在归档内时连 stderr 说明都没有（stdout 完美、stderr 空）。
  - **影响结果**: 门禁可读面（rc + stdout）仍对**从未被读取**的文件宣告全库合规；CI 只采集 stdout 或只看 rc 时，这是一个确定性假绿。相较上轮已消除「两入口结论相反」，故降为 P2 残留而非阻断。
  - **涉及代码**: `skills/doc-governance/scripts/trim-revision.py:152-154,197-199`（`:186` 的 `resolve()` 使该分支只在显式单文件/归档内根时进入）。

- **攻击路径 3: `is_archive_path` 的无界豁免 —— 归档语义蔓延到 `docs` 树之外**
  - **触发条件**: 仓库内任何位置出现相邻 `project/reviews` 路径段（非 docs 树，例如未来新增 `contexts/project/reviews/` 或 `tools/project/reviews/`）。
  - **复现推演**: 合成 `/tmp/x/fp/src/project/reviews/legit.md`（7 行修订表）→ `trim-revision.py --root /tmp/x/fp --fix` 输出 `共检查 0 个文件 / ✅ 完美`，文件**未被裁剪**；`is_archive_path('src/project/reviews/legit.md') = True`。即新判定不再要求路径位于 `--root` 下的 `project/reviews`，而只要字面相邻两段命中即豁免。
  - **影响结果**: 与 `docs/GOVERNANCE.md:117`「豁免仅覆盖 `<docs 根>/project/reviews/**`」**同一节内自相矛盾**；今天是零实例（本仓仅 docs 树有该段），但豁免是静默的（无 warning），未来任何同名相对路径会被 `trim-revision.py` 与 `generate-llms-txt.py` 双双静默跳过。极端情形：若检出/工作目录自身绝对路径含相邻 `project/reviews` 段，`--root .` 可令**整树**被豁免（判定退化为恒真）。
  - **涉及代码**: `skills/doc-governance/scripts/generate-llms-txt.py:31-38,105`；`skills/doc-governance/scripts/trim-revision.py:36-44,161`；`docs/GOVERNANCE.md:115,117`。

- **攻击路径 4: 库调用面（非 CLI）仍可改写归档 —— 新守卫依赖调用方给的路径形态**
  - **触发条件**: 以模块方式调用 `scan_and_trim(Path('.'))` 且 cwd 已在归档目录内（本仓测试即采用 `import trim_revision` 的模块调用范式）。
  - **复现推演**: `cd docs/project/reviews && scan_and_trim(Path('.'), fix=True)` → `rglob` 产出 `report.md`（parts 无 `project/reviews` 段）→ `is_archive_path` False、`in_evidence_archive(rel=('report.md',))` False → 实测输出 `[FIXED] report.md: 修订历史从 7 行成功裁剪至 5 行`、`archive_rewritten=True`。
  - **影响结果**: CLI 面因 `main()` 先 `resolve()` 而安全，故危害仅限直接 import 的调用方；但两个新回归用例均以**绝对路径**调用 `scan_and_trim`，未覆盖该形态，属写入侧守卫的最后一个未闭合角。
  - **涉及代码**: `skills/doc-governance/scripts/trim-revision.py:36-44,152,161,186`。

- **攻击路径 5: `--output` 缺省落点把生成物写进交付凭据归档**
  - **触发条件**: 不带 `--output` 且以归档子树为根运行：`generate-llms-txt.py --root docs/project/reviews`。
  - **复现推演**: `out_path = root_path / "llms.txt"`（`:161`）+ `out_path.parent.mkdir(parents=True, exist_ok=True)`（`:167`）→ 实测在 `docs/project/reviews/` 下新建 `llms.txt`（261 B，`共收录 0 篇有效文档`）。既有报告未被覆盖，但归档目录被写入了一个**所有 5 个消费者都豁免**的新文件（links/health/control-sync 均不看它）。
  - **影响结果**: `docs/GOVERNANCE.md:115` 本轮新增的表述「保证 `--root` 被收窄或放宽时仍**不写入**交付凭据」在字面上不成立。行为本身由 7d86d96（BK-0021）引入、不在本区间 diff 内，按边界锁降级为 P3 历史既有；但**该声明是本轮新写入的**，声明与实现不符需一并修正。
  - **涉及代码**: `skills/doc-governance/scripts/generate-llms-txt.py:161,167`；`docs/GOVERNANCE.md:115`。

## 4. 潜在缺陷清单 (Identified Defect Candidates)

**修复核验矩阵（先给结论，再入表）**

| 上轮 ID | 上轮定级 | 本轮独立实测结论 | 证据 |
|:---|:---:|:---|:---|
| R1-1 | P1 | ❌ **未根治**：提交物 ≠ 该树生成物（仅剩 1 行描述漂移），检查点「可复现」为伪 | sha256 `250dc7c1…` vs `899c2b4e…`；换回 base 版计划书后逐字节一致 |
| R1-2 | P2 | ✅ **CLI 面闭合**：8 种根形态 `--fix` 后归档不变、对照正常裁剪；库调用面残留见 DR1-2 | 合成树 SHA256 前后比对 + 对照文件 `[FIXED]` |
| R1-3 | P2 | 🟡 **半根治**：同构 ✔、stderr 显式提示 ✔、stdout 假绿 ✘ | `共检查 0 个文件` + `✅ 完美`（`:197-199`） |
| R1-4 | P2 | ✅ **闭合**：health 100.0/100、孤儿 0/51、index.md:79 已登记并升版 V1.20.0 | head 树 + 真实工作树双跑 |
| R1-5 | P3 | ✅ **闭合**：登记表 5 行，与全仓 5 个消费者集合相等 | `GOVERNANCE.md:109-113` / `grep -l EVIDENCE_ARCHIVE_PARTS` |
| R1-6 | P3 | ✅ **实质闭合**（残留口径 3 vs 4）：68−17−2=49 成立、17→0 成立 | md 计数 + 条目计数 |
| R1-7 | P3（封顶） | ⏸ **未改动**：三个只读消费者 root 锚定债原样保留 | 本轮 diff 未触及 |

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | **P1 (Blocker)** | 是（本轮修复未闭合，仅换形式） | `docs/llms.txt:63`；`docs/project/plans/2026-10-09-backlog-batch-a-archive-exemption.md:29,64` | 交付的机器地图仍不是其生成器在该树上的输出：注册命令重生成会改写第 63 行（提交物无描述、生成物有描述），且系同提交内「先出图、后写 §5.1」所致 | 反证：把计划文档回退到 6e7b92d 版本后生成结果与提交物逐字节一致 → 漂移成因确定；跑一次注册命令即得脏树；`docs/llms.txt` 全仓零门禁消费（`audit-doc-health.py:450` 仅按文件名跳过），漂移不可机械检出；计划书 `:29` 的「可复现」自述被一行 `diff` 证伪 |
| R1-3 | P2 (残留建议) | 是（部分修复） | `skills/doc-governance/scripts/trim-revision.py:152-154,197-199` | 单文件/归档内目录入口在**未被读取任何文件**时仍以 rc=0 在 stdout 断言「所有文档……均 <= 5 条，符合滑动窗口规范」；豁免说明只在 stderr，目录形态连 stderr 都没有 | 门禁可读面（rc + stdout）产生确定性假绿；上轮处置要求 (b)「禁止输出『完美』结论性文案」未执行；同构与显式提示两项已达标，故不阻断 |
| DR1-1 | P3 (优化建议) | 是 | `skills/doc-governance/scripts/generate-llms-txt.py:31-38,105`；`skills/doc-governance/scripts/trim-revision.py:36-44,161`；`docs/GOVERNANCE.md:115,117` | `is_archive_path` 是无界段扫描：任何位置的相邻 `project/reviews` 段都被豁免，超出 `GOVERNANCE.md:117` 登记的 `<docs 根>/project/reviews/**` 边界 | 实测 `src/project/reviews/legit.md` 被静默跳过（7 行未裁剪）；极端情形（检出路径自身含该段）可令整树豁免；今天零实例，故 P3 |
| DR1-2 | P3 (优化建议) | 是 | `skills/doc-governance/scripts/trim-revision.py:36-44,152,161,186` | 新守卫依赖「路径字面含段」这一形态：库调用 `scan_and_trim(Path('.'))` 且 cwd 在归档内时仍改写归档（CLI 因 `resolve()` 安全） | 实测 `archive_rewritten=True`、`[FIXED] report.md`；两条新用例均以绝对路径调用，未覆盖该形态 |
| DR1-3 | P3 (优化建议) | 行为：历史既有（7d86d96 引入，不在本区间）；声明：是本轮新增文档 | `skills/doc-governance/scripts/generate-llms-txt.py:161,167`；`docs/GOVERNANCE.md:115` | `--output` 缺省随 `--root` 派生，`--root docs/project/reviews` 时会向交付凭据归档内新建 `llms.txt`（实测 261 B） | 生成物落入 5 个消费者全部豁免的盲区；`GOVERNANCE.md:115` 本轮新增的「任意 root 下不写入交付凭据」表述与实现不符。按边界锁封顶 P3 |
| R1-7 | P3 (强制封顶) | 历史既有 | `check-doc-links.py`/`check-doc-control-sync.py`/`audit-doc-health.py` 的 `in_evidence_archive` 三副本 | 三个只读消费者的豁免仍为 root 锚定，`--root` 一变即失效 | 未被本区间改动，原样保留，留待后续统一排期，不参与阻断 |

## 5. 第一轮结论概要

**总体判定: 上轮唯一阻断项 R1-1 未被从根因层面消除（仅由两处显式漂移收缩为一处隐式描述漂移），本轮仍存在 1 项 P1 阻断，不建议签收。** R1-2（写入侧 root 无关化）与 R1-4/R1-5/R1-6（索引/健康度/登记表/算式）经独立实测确认为**真实闭合**；R1-3 为**半根治**（同构 ✔ / 显式提示 ✔ / stdout 假绿 ✘）。

- **独立复核为「真」的项（供 R2 免于重算）**：① CLI 面归档只读 —— 8 种 `--root` 形态（含仓库根、`docs/project`、`docs/project/reviews`、归档内 cwd、含 `../..` 路径）`--fix` 后归档 SHA256 全不变，同树对照正常裁剪；② 机器地图窄根豁免 —— `docs/project` 1 条不含 reviews、`docs/project/reviews` 0 条、`.` 1 条不含 reviews；③ 健康度 —— head 树与真实工作树均 100.0/100、孤儿 0/51，links rc=0（51 文件）、control-sync rc=0（29 文件）；④ 登记表 —— `GOVERNANCE.md:109-113` 五行与全仓 5 个 `EVIDENCE_ARCHIVE_PARTS` 消费者集合相等；⑤ 算术 —— 68 md − 17 归档 − 2 根文件 = 49 条，归档条目 0；⑥ 测试 —— `pytest skills/doc-governance/tests` = **64 passed** 属实（60→64，恰为本轮 +4）；⑦ YAGNI 合规（无裁决语义解析器、无 `.docignore`、无共享模块重构）。
- **测试保真度（变异反证）**：把两个脚本的 `is_archive_path()` 一并变异为 `return False` 后，4 条新用例**全部变红**（narrow root / wide root / single-file / llms narrow root），全仓变为 `4 failed, 60 passed` —— 四处守卫均具鉴别力，上轮「单文件分支零覆盖」已消除。**唯未覆盖** DR1-2 所述的库调用形态（相对路径 + 归档内 cwd）。
- **必须移交 R2 元对抗审判的三个争点**：
  1. **R1-1 是否维持 P1**：主张维持。上轮定义的属性是「交付物必须等于其生成器在该树上的输出」，该属性在 head 上仍为假，且本轮**在同一提交内**再次复现了「先出图、后改文」的成因；检查点自述「可复现」被证伪属验证声明失真。反方最强论据是「残余仅 1 行描述、零门禁消费、危害有界」，若采纳则降 P2 —— 但无论级别，**必须**在计划文档定稿后重跑一次注册命令并复核 `diff` 为空，同时把「重生成逐字节一致」纳入某处机械门禁或至少纳入验收清单，否则下次刷新依旧复发。
  2. **DR1-1 的豁免边界**：是维持「路径段扫描」的宽松语义（并在 `GOVERNANCE.md:117` 把边界改写为「任意 `project/reviews` 段」以消除同节自相矛盾），还是把判定收紧为「root 锚定 ∪ 归档内 root 时的段扫描」。当前是「文档说边界、代码不认边界」。
  3. **R1-3 的 stdout 契约**：建议在 `total_scanned == 0` 时不再输出「所有文档……均 <= 5 条」这类全量结论（改为「本次未扫描任何文件（全部命中豁免），未产生合规结论」），并让目录形态也打印跳过原因，使 stdout 与 rc 语义自洽。
- **范围与合规声明**: 本报告全部结论来自 `git archive` 还原的隔离树（8ea3f65 / 6e7b92d / 102b761）上的真实脚本调用、真实门禁复算、逐字节 SHA256 比对与变异测试；未采信实现者与编排者的任何自述（其中「llms.txt 重生成可复现」经实测为伪，已计入 R1-1）。上轮报告的指纹核验为真：`r1-8ea3f65..6e7b92d.md` = 20268 B / `sha256 99ee1b14c37d27f7df9ec7ec3db3a2e8402e5d0a0b05f588b535b9edb7738c51`。历史既有技术债按 Diff 边界锁强制封顶 P3（R1-7 / DR1-3 行为面），不参与本轮阻断判定。审查期间未修改工作树、分支与索引（`audit-doc-health.py` 前后 `git status` 与三份受控文件哈希不变）。
