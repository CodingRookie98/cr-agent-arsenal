# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **本质根因修复**（BK-0023 / BK-0025 两项验收均经隔离树 A/B 与变异实验证实为真修复），但新增的「机器地图一致性」硬阻断存在**判定面与修复面不对称**的结构性工程缺陷（判定从严、修复命令不可执行、逃逸路径不设防），需登记补强，不构成本次交付阻断。
  - BK-0023 双路径等强：回退缺省分支 `resolve()`（变异 MUT-F）→ 符号链接回归用例打红；三条绕法实测均被拒且归档零泄漏——① `--output` 父目录为指向归档的符号链接（A1，`rc=1`）、② 缺省落点为悬空符号链接（A2，`rc=1`）、③ `--output` 相对路径落归档（A3，`rc=1`）。
  - BK-0023 零覆盖守卫：删除守卫（变异 MUT-G）→ 零覆盖回归用例打红；隔离根实跑生成器 `rc=1` 且不落盘（M5c）。
  - BK-0025 硬阻断接线是承重的：从 PASS 条件删除 `llms_map_issue`（变异 MUT-E）→ 100.0 分的漂移树由 REJECT 翻转为 **PASS rc=0**。
  - 交付物自洽：`docs/llms.txt` = 12273 B / 收录 53 篇 / SHA256 `6da4a9f798a47ccedb2018b74204202a91f672fda16c38ed669a725939351905`，与注册命令重生成**逐字节相同**（`cmp` 通过）；真实树 `audit-doc-health.py --root docs` = 100.0 分 PASS；`pytest skills/doc-governance/tests` = **71 passed**（卡片宣称属实），`pytest skills` = 271 passed。
- **物理与业务一致性**: `resolve()` 统一把归档判定建立在**路径的物理终态**上，方向正确；零覆盖守卫把「地图必须是全量拓扑的投影」这一物理不变量写成代码，方向正确。但**硬链接不属于路径解析的可解空间**（POSIX 下 `resolve()`/`realpath()` 对硬链接无解），因此「禁止穿透归档」的承诺在硬链接面前不成立：实测归档文件被逐字节改写且 `rc=0`（R1-3）。这不是 `resolve()` 用错，而是**守卫的判据（路径字符串）与要保护的资产（inode）不是同一个东西**。同时门禁把「应当有多篇」隐式写成「必须等于某个固定参数调用的产物」，使修复面被冻结（R1-1 / R1-2）。
- **过度设计审计**: **YAGNI 合规**。区间 `git diff --name-status` 仅 6 改 + 1 新增计划文档（无新增脚本层）；未引入独立脚本层、未引入裁决语义解析器、未引入 `.docignore`（实测 `./.docignore` 与 `docs/.docignore` 均不存在）；复用既有 `_load_sibling` 与既有 audit 入口，与 BK-0023/BK-0025 的显式约束一致。反向的瑕疵是**抽象缺位**（不是过度设计）：硬阻断缺少最小豁免面（项目名 / 生成来源 / 最小收录数），也没有「无地图即合规」的可执行出路。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

未激活（非客户端/SSR 改动）

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

- **攻击路径 1: 归档硬链接穿透（写入侧，G1 逐字归档红线被击穿）**
  - **触发条件**: `docs/llms.txt` 与 `docs/project/reviews/**` 内某文件互为硬链接（同文件系统、具备本地写权限），随后任何人按注册命令正常重生成。
  - **复现推演**: `ln docs/project/reviews/victim.md docs/llms.txt` → `resolve()` 只解析符号链接，`out_path` 仍是 `.../docs/llms.txt` 的普通路径 → `is_archive_path()` 与 `in_evidence_archive()` 均判否（`:170`）→ `write_text` 截断并改写**同一 inode** → 归档凭据内容被替换，`rc=0`，零告警。
  - **影响结果**: 实测 `victim.md` SHA256 `5eac78daaaf3380d…` → `6da4a9f798a47cce…`（被替换为机器地图），链接数 2，`rc=0`。归档指纹与逐字凭据被静默破坏。威胁模型需本地写权限（无权限提升），故不阻断交付，但守卫承诺与实测行为不符。另含 `resolve()` 与 `write_text` 之间的 TOCTOU 窗口（检查通过后再被换成符号链接即可穿透），本轮未做并发实测，仅记录为残余风险。
  - **涉及代码**: `skills/doc-governance/scripts/generate-llms-txt.py:168-172`、`:154`。
- **攻击路径 2: 零覆盖死胡同 → 唯一出路是删除 SSOT 地图**
  - **触发条件**: `--root` 下可收录文档为 0（仅有根级文档，或全部落在 `project/reviews` 豁免区），而 `<root>/llms.txt` 已存在（手写或历史遗留）。
  - **复现推演**: audit 调 `check_llms_map_consistency()` → 生成器 `total_docs==0` 返回 0 → 检查返回「收录 0 篇…不可信」→ 硬阻断 REJECT（得分仍为 100.0）；用户执行提示中的修复命令 `generate-llms-txt.py --root docs --output docs/llms.txt` → 生成器同样因零覆盖 `rc=1`（**提示的修复命令在数学上不可能成功**）→ 用户删除 `<root>/llms.txt` → 门禁回到 PASS 100.0。
  - **影响结果**: 实测 M5a（无地图）= PASS 100.0；M5b（有手写地图）= REJECT 100.0；M5c（执行提示命令）= `rc=1`；M5d（删除地图）= PASS 100.0。门禁把「非本工具生成」的合法产物（llmstxt.org 公开约定下的手写地图）判为不可修复缺陷，并在事实上教会维护者用「删文件」过关。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:82-105`、`:98-101`；`generate-llms-txt.py:148-151,178-182`；文案 `audit-doc-health.py:669`。
- **攻击路径 3: `--name` 假阳性（合法 CLI 参数被门禁冻结）**
  - **触发条件**: 维护者使用 CLI 既有公开参数 `--name` 生成地图。
  - **复现推演**: `generate-llms-txt.py --root docs --output docs/llms.txt --name "CR 公共技能库"` → `rc=0`，地图首行变为 `# CR 公共技能库 Machine-Readable Knowledge Base Map`；audit 内部固定以 `project_name="System"` 重生成（`:95`）→ 逐字节比对失败 → **100.0 分 REJECT**；按其提示重生成（提示命令不含 `--name`）会再次得到同一 REJECT。
  - **影响结果**: 实测 M2：生成 `rc=0`、audit `rc=1`、总得分 100.0。同一语义在代码中存在**三处不一致的默认值**：函数签名 `"Project"`（`generate-llms-txt.py:95`）、CLI `--name` 默认 `"System"`（`:163`）、门禁硬编码 `"System"`（`audit-doc-health.py:95`）。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:95`；`skills/doc-governance/scripts/generate-llms-txt.py:95,163`。
- **攻击路径 4: 删除地图逃逸（最彻底的漂移反而无告警）**
  - **触发条件**: `<root>/llms.txt` 被删除，且树内无 markdown 链接指向它。
  - **复现推演**: `check_llms_map_consistency()` 首行 `if not llms_file.exists(): return ""`（`:88-89`）→ 门禁静默通过 → 无任何缺陷输出。
  - **影响结果**: 实测 M5d = PASS 100.0。本仓因 `docs/index.md:28` 存在 `[docs/llms.txt](./llms.txt)` 入链，删除会触发**既有断链门禁**（M1 `rc=1`、得分 95.0），但提示文案写成「得分 95.0 < 门槛 80.0」，把断链错误归因到分数，误导排障方向。与攻击路径 2 组合后，「删文件」成为唯一可行且被放行的操作。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:88-89`；`docs/index.md:28`。
- **攻击路径 5: 门禁接线被移除或被改坏，回归测试仍全绿（测试保真度）**
  - **触发条件**: 后续维护误删 PASS 条件中的 `llms_map_issue`，或该检查退化为对任意树的通用假阳性。
  - **复现推演**: MUT-E（删除 PASS 接线）→ 漂移地图的 100.0 分树 `rc=0` 输出 PASS，同一份输出里还打印着「⛔ 机器地图一致性缺陷」；4 条新用例仍 **4 passed**。MUT-D（强制返回其它假阳性文案）→ 完全一致的地图被 REJECT（`rc=1`）；4 条新用例仍 **4 passed**。
  - **影响结果**: `test_audit_detects_llms_map_drift` 的 `rc!=0` 断言被该树「得分 65 < 80」满足，与硬阻断接线无关；`test_audit_accepts_consistent_llms_map` 只断言「不含某一固定字符串」，对其它假阳性类别完全失明。对照组 MUT-F（回退 `resolve()`）/ MUT-G（删除零覆盖守卫）均能精确打红对应用例，说明**写入侧用例有效、判定侧用例空转**。
  - **涉及代码**: `skills/doc-governance/tests/test_doc_governance_scripts.py:921-995`（漂移用例 `:968-979`，一致用例 `:981-995`）。
- **攻击路径 6: 零覆盖拒绝落盘仍产生目录副作用**
  - **触发条件**: 零覆盖树下显式指定 `--output <不存在目录>/llms.txt`。
  - **复现推演**: `out_path.parent.mkdir(parents=True, exist_ok=True)` 在 `generate_llms_txt()` **之前**执行（`:178`）→ 守卫拒绝落盘、`rc=1`，但父目录已被创建。
  - **影响结果**: 实测 M16 `rc=1` 且 `brand_new_dir` 存在；失败操作留下半成品副作用。
  - **涉及代码**: `skills/doc-governance/scripts/generate-llms-txt.py:178-182`。

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:82-105,651-664`；`skills/doc-governance/scripts/generate-llms-txt.py:148-151,178-182` | 零覆盖场景下硬阻断形成**不可修复死胡同**：提示的修复命令必然 `rc=1`，唯一出路是删除地图 | 门禁把「文件存在」等同于「必须由本工具产出」，缺少最小豁免面；实测 M5a/M5b/M5c/M5d 四态闭环 |
| R1-2 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:95`；`skills/doc-governance/scripts/generate-llms-txt.py:95,163` | 合法公开参数 `--name` 被门禁冻结为 `"System"`，用户按文档化参数生成的地图被判漂移（100.0 分 REJECT），且提示命令对其无效 | 同一语义三处默认值不一致（函数 Project / CLI System / 门禁 System）；实测 M2 |
| R1-3 | P2 (Suggestion) | 否（历史既有；本次仅改动同一定言行） | `skills/doc-governance/scripts/generate-llms-txt.py:168-172,154` | **硬链接穿透**：`resolve()` 对硬链接无解，归档内文件被逐字节改写且 `rc=0`；另有「检查→写入」TOCTOU 残余窗口 | 守卫判据是路径字符串，被保护资产是 inode；实测 victim SHA256 `5eac78da…` → `6da4a9f7…` |
| R1-4 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:88-89` | 地图缺失时静默通过，构成「删除即放行」的负向激励（最彻底的漂移反而无告警） | 早退把「不适用」与「合规」混同；实测 M5d PASS 100.0；本仓仅被 `docs/index.md:28` 的既有断链门禁间接兜住 |
| R1-5 | P3 (Suggestion) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:669`（及 `:100-101`） | REJECT 文案未同步新增阻断项，且输出自相矛盾的「得分 100.0 < 门槛 80.0」；提示命令硬编码 `--root docs --output docs/llms.txt`，与实际 `--root/--name` 无关 | 判定面新增条件而用户可见文案未联动，误导排障；实测 M8b/M2/M5b 均复现该文案 |
| R1-6 | P3 (Suggestion) | 是 | `skills/doc-governance/tests/test_doc_governance_scripts.py:968-995` | 判定侧回归用例**空转**：删掉 PASS 接线（MUT-E）或注入通用假阳性（MUT-D）后 4 条用例仍全绿 | 漂移用例的 `rc!=0` 被「得分 65 < 80」满足；一致用例只断言不含某一固定字符串。对照 MUT-F/MUT-G 能打红 |
| R1-7 | P3 (Suggestion) | 是 | `skills/doc-governance/scripts/generate-llms-txt.py:178-182` | 零覆盖拒绝落盘前已执行 `mkdir(parents=True)`，失败操作留下空目录副作用 | 副作用先于产物校验；实测 M16 `rc=1` 且目录已创建 |
| R1-8 | P3 (Suggestion) | 否（历史既有；本次新增第 4 个同级依赖） | `skills/doc-governance/scripts/audit-doc-health.py:44-58,94` | `_load_sibling` 以 `exec_module` 加载兄弟模块，实测每次 audit 运行向源码树写回 4 个 `.pyc`（含本次新增的 `generate-llms-txt.cpython-312.pyc`）；并新增 import 期硬依赖 | 只读体检工具产生文件系统副作用（`.gitignore` 已忽略，不改 git 状态）；无循环依赖、无模块级副作用、临时目录零残留 |
| R1-9 | P3 (Suggestion) | 否（历史既有；新硬阻断放大其影响） | `skills/doc-governance/scripts/generate-llms-txt.py:100-119` | 地图收录域为**文件系统**（含未跟踪/被忽略的 `.md`，仅跳过 `node_modules/.git/.next/dist/build`），本地临时文档会被新硬阻断放大为交付级 REJECT | 收录逻辑本次未改动，属预存在语义；但新增门禁使其从「人工 diff 不一致」升级为「机械拒绝交付」 |

**评分口径一致性（审查维度 d 结论）**: `llms_map_issue` 已正确计入 `has_issues`（`audit-doc-health.py:651-653`）与 PASS 硬条件（`:664`），并被 MUT-E 证明为承重接线；**未计入 100 分评分**——与既有硬阻断 `version_drift_files`、`backlog_issues` 的记分口径完全一致（二者同样不扣分），故判定为口径一致、非缺陷；其唯一副作用是 REJECT 文案出现自相矛盾（R1-5）。

**假阴性排查（维度 b 结论）**: ① 生成器异常未被吞掉——`except Exception`（`:103-104`）将异常转成**缺陷字符串**并阻断 PASS，属 fail-closed（实测 M8b：`llms.txt` 为目录时输出「检查无法完成: [Errno 21] Is a directory」并 REJECTED）；② 临时文件与目标同源恒等——不成立，`TemporaryDirectory()` 为随机子目录且重生成确定性（真实树重生成 SHA256 完全相同）；③ 时间戳类易变内容——生成器无时间戳，重生成逐字节稳定；④ `--root` 相对路径与符号链接根——`--root ./docs` 与 `--root docs_link` 均 PASS 100.0（M7a/M7b），无误报。

**资源与并发（维度 c 结论）**: `tempfile.TemporaryDirectory()` 在成功路径与异常路径的 TMPDIR 残留实测均为 0（M8a/M8b）；`contextlib.redirect_stdout` 为进程级全局替换，异常时由上下文管理器恢复——M8b 证明异常后体检报告仍完整打印；本工具是单线程 CLI，未发现并发改写风险，但若未来把 `audit_health()` 当库在多线程中调用，`redirect_stdout` 会互相干扰，建议登记为演进约束。

## 5. 第一轮结论概要

- **裁决**: **P0 = 0，P1 = 0 → Zero Blockers（准予交付）**。BK-0023（符号链接穿透 + 零覆盖守卫）与 BK-0025（一致性门禁固化）的验收准则均经**独立复算 + 隔离树 A/B + 变异测试**证实为真修复，非表面补丁；新增硬阻断在本仓真实树产生 100.0 分 PASS 且不误报。
- **本轮 4 项 P2 建议登记 backlog（不阻断本次提交）**: R1-1（零覆盖死胡同与修复命令悖论）、R1-2（`--name` 默认值三处不一致）、R1-3（硬链接穿透，历史既有）、R1-4（删除逃逸与负向激励）。其中 R1-1 / R1-2 / R1-4 为**同一根因**的三个观测面：门禁的判定面（固定参数的逐字节产物）与修复面（用户可执行的命令集合）不封闭。建议的最小修复方向是让判定与修复共用同一个参数来源（例如由既有地图首行/显式注册参数推导项目名），并为「无地图」给出明确合规语义，而非新增抽象层。
- **已验证关闭的红队假设（避免 R2 重复投喂）**: 归档判定双路径等强（A1/A2/A3 三绕法全拒、MUT-F 打红）；零覆盖守卫有效（MUT-G 打红、M5c 不落盘）；`--output` 与缺省落点无强弱差；无临时文件泄漏；生成器异常 fail-closed；无 `--root` 形态误报；无时间戳易变内容；无循环依赖；无新增脚本层、无 `.docignore`、无裁决语义解析器（YAGNI 合规）。
- **移交第二轮架构师元对抗审判（R2）**: 请重点裁定三件事——① R1-1/R1-2/R1-4 是否应升级为 P1（若将「消费者项目合法 llms.txt 被永久硬阻断且无豁免开关」视为门禁正确性问题）；② R1-6 的测试空转是否单独构成阻断（判定侧用例无法防止接线被移除）；③ R1-3 硬链接穿透是否需要在「逐字归档」红线层面加设 inode/链接数校验。本轮未发现任何 P0/P1，故 Light 单轮未触发 Delta；若 R2 将上述任一项重新定级为 P1，按 Light-Delta 规则仅重跑 R1 即可。
- **审查过程事故与恢复（诚实披露）**: 本轮 R1 在执行对抗实验时，因运行环境 `/tmp` 在程序调用之间不持久，两条实验命令的 `cd` 失败后回落到会话工作目录，在真实工作树内产生了写入：覆盖了 `docs/llms.txt`（用 `--name "CR 公共技能库"`），随后删除该文件、在 `docs/project/reviews/` 下创建 `hardlink_victim.md` 并建立硬链接。发现后立即恢复：删除硬链接与该误建文件，并以 `git show HEAD:docs/llms.txt` 逐字节还原。复核证据：`git status --porcelain` 仅剩编排者预创建的未跟踪目录 `docs/project/reviews/2026-10-09-batch-b-llms-integrity/`；`git diff --stat` 为空；`docs/llms.txt` SHA256 = `6da4a9f798a47ccedb2018b74204202a91f672fda16c38ed669a725939351905` 且与 `git show HEAD:docs/llms.txt` 逐字节 `cmp` 相等。该事故同时意外提供了攻击路径 2/3 的实仓证据；此后所有实验均改为 `git archive` 隔离树 + 单次自包含命令，并在每次实验尾部复验工作树。本次任务唯一被授权的持久化写入仅为本报告文件。
