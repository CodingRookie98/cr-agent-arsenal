# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析
- **改动性质定性**: **一半本质修复、一半浅层修补 —— R1-1 未根治。** 把 `_sanitize_project_name()` 从 `_map_project_name()` 出口（判定域）下移到提示插值点（显示域，`:133`），是对 R1-1 根因的**正确打击**：隔离合规树 A/B 实测，`L×65`、`中×65`、`" Foo "`@、`A+NBSP+B` 四类上轮误判名在 HEAD 上由硬 REJECT 回到 **audit rc=0 PASS**（另加 `A+ZWSP+B`、`A=B`、`-dash`、`Café 🚀`、组合字符 `e+U+0301`、`A×64` 边界，共 **10/10 PASS**，注册命令 `gen_rc=0` 原文生成 + 逐字节相等）。但**判定域的输入依然不是「生成参数」，而是「反解派生值」**：`_map_project_name()` 在正则不匹配时回落 `PROJECT_NAME_FALLBACK = "System"`（`:108,110`），而本次新增守卫的谓词是 `display_name != project_name`（`:134`）—— `System` 恒等于自身，**必然穿过守卫**，落入 `--name=` 提示分支（`:141-145`）。缺陷由此从「净化导致判定与生成不同源」变形为「**反解导致判定与生成不同源**」：同一根因的另一条腿未被处理，且 `_map_project_name()` docstring 自称的「保证判定参数与生成参数逐字同源（R1-1）」（`:104`）经实测为**假**。
- **物理与业务一致性**: **门禁的自我一致性被破坏**。`check_llms_map_consistency()` 的契约是「地图必须等于注册命令的产物」，但它下发的是**改名命令**：合规树上以 `--name=""`、`--name=$'A\nB'`、`--name=$'A\u2028B'` 生成的地图（`gen_rc=0`，是合法产物）被 REJECT，提示 `--name=System`；逐字执行提示后 H1 由 `#  Machine-Readable…` 永久改写为 `# System Machine-Readable…`，门禁随即 **rc=0 PASS**，全程不告知发生了身份改写。名含契约短语 `X <MARK> Y` 时提示 `--name=X`，执行后 H1 尾段 `@ Y` 被删除且同样转 PASS。门禁在此从「守门人」变成「SSOT 地图改名执行器」，正是 R1-1 定义的「提示下发会导致地图改名的命令」反噬。SSOT 侧自述亦先于裁决宣告闭环（见 §4 R1-4）。
- **过度设计审计**: **YAGNI 合规**。区间仅 3 文件 +42/−8，无新增脚本层、无「裁决语义解析器」、无 `.docignore`、无共享模块重构；新增逻辑为「1 个 7 行守卫分支 + 2 条断言拆分 + 1 条新用例」。死代码检查：`_sanitize_project_name`（被 `:133` 引用）、`PROJECT_NAME_MAX_LEN`（`:98`）、`PROJECT_NAME_FALLBACK`（`:99,108,110`）在 HEAD 上均有活引用，**无死代码**——但 `PROJECT_NAME_FALLBACK` 恰是 R1-1 残余的唯一入口。轻微冗余：`--root docs --output docs/llms.txt` 字面量在安全分支与提示分支各写一次（`:137`、`:144`），且均硬编码 `--root docs`（与 `SKILL.md:141` 文档化调用一致，故仅 P3）。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）
未激活（非客户端/SSR 改动）。本区间仅触及 Python 治理脚本、unittest 用例与 Markdown 索引，无 `*.tsx/*.jsx/*.vue/*.svelte`、无 `use client/use server`、无 `react`/`next/*` 导入；不存在可推演的浏览器运行时、水合或 Storage 语义。
- **Rules of Hooks 合规性**: 未激活（非客户端/SSR 改动）。
- **SSR 水合与 Storage 防御**: 未激活（非客户端/SSR 改动）。
- **渲染纯度与全局可变状态**: 未激活（非客户端/SSR 改动）。

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)
- **攻击路径 1: 反解失败回落 System → 门禁把机器地图项目名改写为占位名（P1 主证）**
  - **触发条件**: 维护者以注册命令 + 空名或含行分隔符的名生成/更新地图（`--name=`、`--name=$'A\nB'`、`--name=$'A\u2028B'`），或用首行不可反解的旧格式/手写地图。无需对抗权限，`gen_rc=0`。
  - **复现推演**: `generate-llms-txt.py:122` 写出 `# {name} Machine-Readable Knowledge Base Map` → `audit-doc-health.py:106` 取 `splitlines()[0]` → `:109` 正则 `(.+?)` 要求至少 1 字符 / 首行被行分隔符截断 → 不匹配 → `:110` 回落 `System` → `:127` 以 `System` 再生成 → `:131` 逐字节不等 → `:133` `display_name = _sanitize_project_name("System") == "System"` → **守卫不成立** → `:141-145` 下发 `--name=System` → 用户照做 → H1 改写 → audit **rc=0 PASS**。
  - **影响结果**: 合规树实测三条链路全部从 `REJECT(rc=1)` 翻转为 `PASS(rc=0)`，代价是**项目身份在 SSOT 机器地图中静默丢失**；门禁对该改写零告知，改写后不再有声。R1-1 第二半（提示不得下发改名命令）在 HEAD 上仍可复现。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:103-110,121,127,131-145`
- **攻击路径 2: 名含契约标记短语 → 提示值截断、H1 尾段被静默删除**
  - **触发条件**: 名本身含 `Machine-Readable Knowledge Base Map` 子串（如 `X Machine-Readable Knowledge Base Map Y`）。
  - **复现推演**: 非贪婪 `(.+?)` 在**第一个**标记处停止 → 反解出 `X` → 以 `X` 再生成 ≠ 原文件 → 缺陷串 → 守卫不成立（`X` 可打印且未超长）→ 下发 `--name=X`；实测执行后 H1 由 `# X Machine-Readable Knowledge Base Map Y Machine-Readable Knowledge Base Map` 变为 `# X Machine-Readable Knowledge Base Map`，尾段 `Y` **不可逆丢失**，audit 转 PASS。
  - **影响结果**: 与路径 1 同根因的第二观测面，证明「提示值 == 地图 H1 名」这一身份保真要求在反解失败链路上不成立（R1-3 残余）。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:109-110,133-145`
- **攻击路径 3: 守卫谓词过宽 → 合法「空白包裹名」被误诊为畸形并撤销唯一可执行修复**
  - **触发条件**: 合法名含首尾空白（`--name=" Foo "`）且地图因**真实正文漂移**（新增文档未重生成）被判定缺陷。
  - **复现推演**: `:97` 的 `.strip()` 使 `cleaned="Foo" != " Foo "` → `:134` 守卫成立 → `:135-138` 输出「**含不可打印字符或超长**，无法安全回显」——实测该名**全部可打印、长度 5**，诊断**事实错误**，且不再下发任何命令。对照实测：被扣留的 `--name=' Foo '`（`shlex.quote` 正确引用）可执行、H1 逐字保持 `#  Foo  Machine-Readable…`（保身份、无改名）、audit 转 `rc=0 PASS`。
  - **影响结果**: 分支把「显示需要归一化」误当作「不可安全回显」，对一整类合法名产出失实诊断并阻断自助修复（相对 R1-1 的授权范围是**过度收缩**）。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:97-100,133-138`
- **攻击路径 4: 新安全分支零回归保护 → 可被未来重构无声移除**
  - **触发条件**: 任何后续改动删除或绕过 `:134-138` 分支（等价于 R1-1 第二半回归）。
  - **复现推演**: 变异 MUT-C3（整段删除守卫 4 行）→ `TestBatchCLlmsHintHardening` **5 passed（全绿）**；同一变异体喂入含真实 NUL 的 H1，实测输出 `--name=AB`（改名命令照发），而 ESC/NUL/超长三条用例**全部无感**。
  - **影响结果**: 本次修复的第二半（「畸形名不得下发改名命令」）**无任何断言保护**；R1-3 的「提示若出现 `--name` 必须等于地图 H1」亦零覆盖。对照第一半已被正确保护：MUT-C2（净化重新引入判定路径）→ `test_legit_edge_names_are_not_misjudged_as_drift` **FAILED**，与编排者自验一致。
  - **涉及代码**: `skills/doc-governance/tests/test_doc_governance_scripts.py:1166-1179`；`skills/doc-governance/scripts/audit-doc-health.py:133-138`
- **攻击路径 5（未遂反证）: 判定路径不再净化 → 注入面复核**
  - **触发条件**: 地图首行为 `# $(id) ; echo PWNED <MARK>`、`# a' ; touch PWNEDFILE ; echo ' <MARK>`、`# $(touch PWNED2) <MARK>`。
  - **复现推演**: 把门禁打印的整条修复命令**逐字交给 bash 执行**（`python3 generate-llms-txt.py --name='…' --root docs --output docs/llms.txt`）：三条 payload 实测 `uid=` 未泄漏、`PWNEDFILE`/`PWNED2` 均未创建、H1 逐字保留载荷原文；`:141` 的 `shlex.quote` 对含单引号名产出 `'a'\"'\"' ; touch …'` 正确引用。
  - **影响结果**: **未发现可达注入面**；反解原值仅流向 `:127` 的内存缓冲与临时文件（生成器 `print` 被 `redirect_stdout` 捕获），不流向审计输出。残余风险仅剩 `:146-147` 的 `except Exception` 兜底（异常文本可能携带未净化原值；20+ 用例均未触发，登记为 R1-12）。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:21,121-127,133-147`；`skills/doc-governance/scripts/generate-llms-txt.py:122,149-157`

### 修复核验矩阵（对编排者自验的独立复核）
| 核验项 | 方法 | 实测结论 |
|:---|:---|:---|
| R1-2 的 NUL 断言不再恒真 | 加固前实现（`2f3a338` 的 `audit-doc-health.py`）+ HEAD 用例 | `test_hint_rejects_nul_name` **FAILED**、`test_hint_rejects_overlong_name` **FAILED**（2 failed / 48 deselected）→ **已根治** |
| R1-2 变异判别力 | MUT-C1 `if ch.isprintable()` → `if True`；MUT-C1-bis `cleaned = raw.strip()` | 两者均使 NUL + ESC 用例 **FAILED**（旧实现下 `raw.strip()` 变异体曾让 NUL 用例存活）→ 断言已具判别力 |
| R1-1 第一半（合法边缘名） | 合规树 A/B，注册命令原文生成 + 逐字节比对 | **10/10 rc=0 PASS**（`L×65`、`中×65`、`" Foo "`@、`A+NBSP+B`、ZWSP、`=`、`-dash`、emoji、组合字符、`A×64`）→ **已根治** |
| R1-1 第二半（提示不得改名） | 空名 / 换行 / U+2028 / 标记短语 4 类，逐字执行已下发命令 | 4/4 下发 `--name=System`/`--name=X`，执行后 H1 被改写且 audit 转 PASS → **未根治（P1）** |
| R1-3 身份保真 | 提示 `--name` 值与地图 H1 名逐字比对 | 普通漂移链路一致（`Foo`/`-dash`/`Just A Title` 执行后 PASS）；**反解失败链路不一致** → 残余 |
| 编排者自验 `81 passed` | 隔离树全量 pytest | **81 passed in 5.15s** ✓ |
| 实仓健康度 | `audit-doc-health.py --root <repo>/docs` | **PASS（100.0）**，运行前后 `git status --porcelain` 无差异 ✓ |
| MUT-C2 | 净化重新引入判定路径 | `test_legit_edge_names_are_not_misjudged_as_drift` **FAILED** ✓ |
| MUT-C3（新增反证） | 删除 `:134-138` 守卫分支 | 5 条 BK-0026 用例**全绿**（零保护）→ 见 R1-9 |

## 4. 潜在缺陷清单 (Identified Defect Candidates)
| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1（残余） | **P1 (Blocker)** | **是**（承重改动行 `:133-145`；反解器 `:103-110` 为批次 B 历史既有、本次未触及） | `skills/doc-governance/scripts/audit-doc-health.py:103-110,133-145` | R1-1 未根治：守卫以「显示是否被改写」为谓词，而反解失败回落 `System` 使 `display == project_name`，**结构性地绕过守卫**进入改名提示分支 | 4 类**注册命令 rc=0 生成**的地图被硬阻断并下发 `--name=System`/`--name=X`；逐字执行后 H1 永久改写、audit 转 PASS、零告知。与 `:104` 自称的「逐字同源」矛盾；沿用批次 B「判定与生成同源」红线 |
| R1-3（残余） | P2（**并入 R1-1，不重复计数**） | 是 | `skills/doc-governance/scripts/audit-doc-health.py:97-100,133-138` | 判定域身份碰撞已消除（`A+NBSP+B`/`A+ZWSP+B` 在 HEAD PASS）；但「提示 `--name` 值 == 地图 H1 名」在反解失败链路不成立 | 新形态碰撞：`""`→`System`、`X <MARK> Y`→`X`；维护者照做即静默接受改名（与 R1-1 同一根因的另一观测面） |
| R1-4（残余） | P2 (Suggestion) | 是（同一文件同一指控的最新一行未收口） | `docs/index.md:5,15,79`；`docs/project/plans/2026-10-09-backlog-batch-c-llms-hardening.md:18,29,50,57` | 「闭环」自述只改到表格行，未全量收口 | `docs/index.md:5` 仍写「BK-0026/BK-0027 **闭环**」；`:15` 修订历史仍描述本次被推翻的设计（「项目名新增可打印字符校验」）；`:79` 改为「交付」但与计划 `状态: 进行中`（`plans:18`）、两张卡 `status: active`/`closed_at: null` 冲突；计划 `:50` 仍称净化「在 `_map_project_name` 出口应用」（本次已否）、`:57` 仍列已不存在的用例名 `test_hint_rejects_nul_and_overlong_names`、`:29` 仍写 `pytest 79 passed`（实测 81） |
| R1-9 | P2 (Suggestion) | 是 | `skills/doc-governance/tests/test_doc_governance_scripts.py:1166-1179`；`skills/doc-governance/scripts/audit-doc-health.py:133-138` | 本次安全分支**零回归保护** | MUT-C3 删除守卫后 5 条用例全绿，变异体对 NUL 名输出 `--name=AB`；即 R1-1 第二半可被无声回退，R1-3 断言缺位 |
| R1-10 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:97-100,133-138` | 守卫谓词过宽：把「显示需归一化」误当「不可安全回显」 | `--name=" Foo "` + 真实漂移 → 文案称「含不可打印字符或超长」（实测假：全可打印/长度 5）且不下发命令；被扣留的 `--name=' Foo '` 实测可执行、保身份、audit 转 PASS |
| R1-5 | P3 (Suggestion) | 否（历史既有，本次未改） | `skills/doc-governance/scripts/audit-doc-health.py:97` | `isprintable()` 放行 `Mn` 组合标记与 U+3164 等不可见「可打印」字符 | 视觉等价欺骗与 Zalgo 式渲染异常；无控制序列注入/RCE，受 64 上限约束。**不阻断本批** |
| R1-6 | P3 (Suggestion) | 否（`rglob` 行为历史既有；新条文措辞非本次改动） | `docs/GOVERNANCE.md:120`；`skills/doc-governance/scripts/generate-llms-txt.py:100` | 条文排他性断言「仅在删净全部可收录文档时出现」不成立 | 象限目录为符号链接时收录数同样为 0 → 豁免被触发、陈旧地图原样保留。**不阻断本批** |
| R1-7 | P3 (Suggestion) | 否（`:119-120` 本次未改；新条文未登记） | `skills/doc-governance/scripts/audit-doc-health.py:119-120`；`docs/GOVERNANCE.md:118` | 「收录数 > 0 但地图缺失」同样跳过判定且未登记 | 删除 `llms.txt` 即成永久逃逸面（实测返回空串）。**不阻断本批**，建议顺手补 1 行登记 |
| R1-8 | P3 (Suggestion，防御性) | 否（历史既有，本次未改） | `skills/doc-governance/scripts/audit-doc-health.py:97-98` | 长度守卫在物化完整净化串之后才判定 | 超长单行先 `join` 复制再丢弃，内存约 2×；10 万字符无感。**不阻断本批** |
| R1-11 | P3 (Suggestion) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:136-137,143-144` | 修复命令尾巴字面量重复两份且硬编码 `--root docs` | 与 `SKILL.md:141` 文档化调用一致故影响小；两处漂移风险（抽取局部常量即可） |
| R1-12 | P3 (Suggestion，残余风险登记) | 否（`:146-147` 历史既有） | `skills/doc-governance/scripts/audit-doc-health.py:146-147` | `except Exception` 把异常文本直出为缺陷串，是未净化文本的潜在洗白通道 | 当前无实测可达路径（20+ 用例未触发）；若未来生成器把项目名写入异常消息，畸形名将绕过 `:133` 守卫直达输出 |

## 5. 第一轮结论概要
**裁决倾向：不予放行（维持 1 个 P1 阻断项）。** 本区间是「一半真修复、一半换形保留」的典型：

1. **R1-2 确已根治（实证）**：加固前实现（`2f3a338`）+ 新 NUL 用例实测打红（旧实现下该断言恒真），且 MUT-C1/MUT-C1-bis 两种变异均能使 NUL 用例失败——判别力已建立。
2. **R1-1 只根治了一半**：四类（乃至十类）合法边缘名的假阳性确已消失（合规树 10/10 PASS），但**判定参数的来源仍是反解派生值**；当反解失败回落 `System` 时，`display == project_name` 使新守卫结构性失效，门禁重新下发改名命令并静默改写 SSOT 地图 H1（4 类链路实测，执行后 audit 转 PASS）。这意味着上轮 P1 的**用户可见后果**（合规产物被硬阻断 + 门禁以改名作为修复）在本轮代码上仍可原样复现，只是入口从「净化」换成了「反解」。R1-3 的身份碰撞亦随之在提示域复现。
3. **次生问题**：新安全分支零测试保护（MUT-C3 全绿）且其诊断文案对合法空白包裹名失实、并撤销了本可安全执行的修复命令；R1-4 只改到表格行，`docs/index.md:5` 的「闭环」与计划/卡片状态仍在互相矛盾；计划 §3/§4 已与其自身实现的本次变更脱节。
4. **未见系统性过度设计**：YAGNI 合规，无新脚本层/解析器/`.docignore`/共享模块重构；注入面经逐字 bash 实测**未发现可达通道**；R1-5~R1-8 均为 P3，**我判断无一需要在交付前闭环**（若必须选一项顺手修，建议 R1-7：补 1 行登记即可关闭「收录>0 但地图缺失」的未登记逃逸面）。

**移交第二轮架构师裁决的焦点**:
1. **R1-1 残余是否维持 P1？** 正方：与上轮 P1 同一语义（门禁下发改名命令 + 静默改写 SSOT 身份 + 合规产物硬阻断），且本次改动的承重行正是该提示分支与守卫；反方最强论据：触发前提是空名/换行/标记短语等**病态名**，本仓真实项目名不触发（实仓 100.0 PASS）。若 R2 降级，**必须同时处置「反解失败仍下发 `--name`」这一语义**，否则降级等于接受「门禁可改名」。
2. **最小修法（不新增抽象层，三处可独立落地）**：(a) `:109` 正则 `(.+?)` → `(.*?)` 以容纳空名（1 字符）；(b) 反解失败时**不下发任何 `--name` 提示**（返回与「无法安全反解」同类的无命令诊断，1 个分支）；(c) 守卫谓词收窄为「存在不可打印字符 / 含 NUL / 超长」，空白包裹类走正常 `shlex.quote(原值)` 提示（消除 R1-10）。
3. **R1-9 必须同批处置**：为「畸形名 ⇒ 输出不得含 `--name=`」补 1 条断言，并把「提示 `--name` 值必须逐字等于地图 H1 名」固化为断言——这是 R1-3 的唯一机械防线，成本约 6 行。
4. **R1-4 建议同批收口**：`docs/index.md:5` 改「待 R2 裁决」、删除 `:15` 对已废弃设计的描述、计划 `:50/:57` 与 `"79 passed"` 同步为交付态。
