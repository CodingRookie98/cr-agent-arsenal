# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

> **审查模式**: LIGHT_REVIEW · DELTA_RE_LOOP（第 3 轮 / 迭代 3/3）｜**区间**: 88fc92f..ee1258b｜**上一轮阻断项**: [R1-1]（唯一 P1，本次维持未闭）
> **证据基线**: 隔离树 = 工作树 HEAD（ee1258b）逐字归档；全部实验在单条自包含命令内 完成（mktemp -d → git archive → 实验 → rm -rf）。区间外写盘仅本报告路径；实验前后 git status --porcelain 均仅含预创建的未跟踪归档目录。

## 1. 第一性原理与本质溯源分析
- **改动性质定性**: **浅层修补为主，R1-1 未根治（换形保留）。** 本次修复把「反解不可信即不下发 --name」写成两个 fail-closed 分支（audit-doc-health.py:136-148），但这两个分支的文案里**内嵌了一条完整可执行、可复制粘贴的生成命令**，而该命令缺省解析到 generate-llms-txt.py:164 的 argparse 默认值 `--name="System"`（与 PROJECT_NAME_FALLBACK 同值）。于是占位符只是从「显式 --name=System」搬进了「缺省参数」：机械断言（输出中不含 `--name=`）变绿，而用户可见后果**逐字不变**——照做 → H1 被永久改写为 # System Machine-Readable Knowledge Base Map → 门禁转 rc=0 PASS、零告知。这是典型的「在消息文本层打补丁、把毒留在下游默认值里」，不是根因修复。
- **物理与业务一致性**: 门禁契约「地图必须等于注册命令以**地图自身身份**生成的产物」仍被门禁自身的修复建议破坏。实测（隔离树、真实漂移正文触发）：上轮四条链路 **100% 可原样复现**——空名、A\nB、A\u2028B、含契约短语；另加 ESC/BEL 名、NBSP 合法边缘名，共 5 类走 fail-closed 分支后「照做 → System → PASS」，1 类（契约短语）走 `--name=X` 截断后 PASS。更严重的是**门禁拒绝自己生成的合规产物**：以注册命令 `--name="A\u2028B"`、`--name="A\nB"`、`--name="X Machine-Readable Knowledge Base Map Y"` 生成（gen rc=0，逐字产物）后，audit 一律 rc=1 REJECTED；随后给出的「修复」路径把身份改写掉。判定（维度 d）本身是健全的：首行不标准时 System 再生成的 H1 必然不同，故**未发现假 PASS**；破坏发生在**修复建议与生成器默认值**这一段。
- **过度设计审计**: YAGNI 合规。区间仅 4 文件 +72/-27，无独立脚本层、无裁决语义解析器、无 .docignore、无共享模块重构；`_resolve_project_name` / `_is_safely_displayable` 各仅 1 处调用，被删的 `_sanitize_project_name` / `_map_project_name` 全仓（含测试、SKILL.md、GOVERNANCE）**无悬挂引用**（grep 命中仅历史审查报告文本）→ 无死代码；上轮 R1-8（长度守卫在物化之后）随旧函数删除而自然消解。但有两处新债：(i) 同一决策现在由两个真源判断（`resolved` 与 `_is_safely_displayable`），其中 `resolved` 的语义只是「正则前缀命中」，不是「名字可复原」，因而不健全；(ii) 提示命令尾巴字面量由 2 份增至 **3 份**（:141、:147、:154），R1-11 恶化。docstring:92 断言「前后空格与 NBSP 属可打印范畴」，实测 `'\xa0'.isprintable()` 为 **False**，事实错误。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）
未激活（非客户端/SSR 改动）。区间仅触及 Python 治理脚本、unittest 用例与 Markdown 文档，无 `*.tsx/*.jsx/*.vue/*.svelte`、无 `use client/use server`、无 `react`/`next/*` 导入，不存在可推演的浏览器运行时、水合或 Storage 语义。
- **Rules of Hooks 合规性**: 未激活（非客户端/SSR 改动）。
- **SSR 水合与 Storage 防御**: 未激活（非客户端/SSR 改动）。
- **渲染纯度与全局可变状态**: 未激活（非客户端/SSR 改动）。

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)
- **攻击路径 1: fail-closed 分支内嵌可执行命令 → argparse 缺省 System → SSOT 身份永久改写 + 转 PASS（P1 主证）**
  - **触发条件**: 地图真实漂移（新增文档未重生成，正文含过期条目）且首行名无法反解或不可安全回显：空名、含 \n / \u2028、含 ESC/BEL/NUL、NBSP、超长、任意旧格式手写 H1。均无需对抗权限。
  - **复现推演**: audit-doc-health.py:123 反解 → :133 逐字节不等 → :136 或 :143 进入 fail-closed → 返回文案「…请人工核对后以正确项目名重新运行 generate-llms-txt.py --root docs --output docs/llms.txt 再提交」→ **该文案本身不含 --name，但含一条可执行命令** → 维护者/代理照做 → generate-llms-txt.py:164 缺省 `--name="System"` → :122 写出 `# System Machine-Readable Knowledge Base Map` → 再 audit：反解 System、再生成逐字节相等 → **rc=0 PASS**，全程不告知发生身份改写。
  - **影响结果**: 隔离树实测 5/5 条链路（空名、A\nB、A\u2028B、ESC/BEL 名、NBSP 名）`IDENTITY_KEPT=False`、re-audit rc=0；与上轮 P1 的用户可见后果逐字相同。新用例 `test_malformed_names_never_emit_a_name_option` 只断言 `--name=` 字面量缺席，因此在这 5 条链路上**全绿**——守卫存在，后果未消除。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:136-148,153-155`；`skills/doc-governance/scripts/generate-llms-txt.py:122,164`
- **攻击路径 2: `resolved` 信任标志不健全（前缀匹配 + 无 $ 锚定）→ 截断名作为权威 --name 下发 → 身份尾段不可逆丢失**
  - **触发条件**: 项目名含契约短语且有后续文本（如 X Machine-Readable Knowledge Base Map Y），或 H1 在短语后带任意后缀（如 # CR 公共技能库 Machine-Readable Knowledge Base Map v2）。
  - **复现推演**: `re.match(r"# (.*?) Machine-Readable Knowledge Base Map", :109)` 非贪婪且**无 $ 锚定** → 反解出前缀 X → :112 返回 `(X, True)` → :143 前缀名可安全回显 → :151 shlex.quote → :153 下发 `--name=X` → 照做 → H1 由 `# X Machine-Readable Knowledge Base Map Y Machine-Readable Knowledge Base Map` 变为 `# X Machine-Readable Knowledge Base Map`，尾段 Y 不可逆丢失 → 再 audit PASS。同一缺陷使**门禁拒绝注册命令自身的产物**：gen `--name="X Machine-Readable Knowledge Base Map Y"` rc=0 → audit rc=1（parse=X）。
  - **影响结果**: 隔离树实测 `IDENTITY_KEPT=False`、re-audit rc=0；带后缀 H1 的 v2 被静默删除。上轮 R1-1 的「含契约短语」链路**未被本次修复触及**。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:109-112,143,151-155`
- **攻击路径 3: 合法边缘名 + 真实漂移 → 唯一可执行修复被扣留，只剩毁身份的那条**
  - **触发条件**: 合法项目名含 NBSP 或长度 > 64（本项目自称的「合法边缘名」），地图因真实漂移被判缺陷。
  - **复现推演**: 名 A\u00a0B 的 H1 可被正确反解（resolved=True）且无假阳性（干净地图 PASS），但一旦漂移：:143 `_is_safely_displayable` 为 False（`'\xa0'.isprintable()==False`）→ 走 fail-closed 文案 → 内嵌的无 --name 命令 → System。即「合法身份 + 真实漂移」这一最常见的运维场景，被唯一给出的命令行导向身份改写。
  - **影响结果**: 把攻击路径 1 的触发面从「病态名」扩大到「合规边缘名 + 正常漂移」，削弱了「触发前提太病态」的抗辩。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:87-94,143-148`
- **攻击路径 4（未遂反证）: 新原始名引用路径的注入面复验**
  - **触发条件**: H1 = `# a'; touch PWNED_FILE; echo ' Machine-Readable Knowledge Base Map` + 真实漂移。
  - **复现推演**: 新代码把**未净化的原始名**交给 `shlex.quote(:151)` 后拼命令，逐字交 bash 执行。
  - **影响结果**: **未发现可达注入面**：bash rc=0、PWNED_FILE 未创建、H1 逐字保留载荷原文、re-audit rc=0。该面较上轮无回归。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:151-155`

- **修复核验矩阵（对编排者自验与上轮指控的独立复核，全部在隔离树实测）**

| 核验项 | 方法 | 实测结论 |
|:---|:---|:---|
| 全量回归 | HEAD 隔离树 pytest | **83 passed in 6.79s** ✓ 与计划 :29 一致 |
| 实仓健康度 | audit-doc-health.py --root docs（只读） | **PASS / 100.0**，运行前后 git status 无差异 ✓ |
| R1-9 修复有效性 | 加固前实现（88fc92f 的 audit 脚本）+ HEAD 两条新用例 | **2 failed**（malformed、hint_name_matches）→ 新用例对旧缺陷确有判别力 ✓ |
| MUT-C3 | 两个守卫分支置不可达 | **4 failed / 3 passed**（NUL、超长、终端控制、malformed）✓ 与自验一致 |
| MUT-C4 | `match is None` 改回 resolved=True | **1 failed**（malformed）✓ 与自验一致 |
| R1-10（" Foo "） | 真实漂移 → 提示 → **逐字执行** | 提示 `--name=' Foo '`；执行后 H1 逐字保身份、re-audit rc=0，**IDENTITY_KEPT=True** ✓ 已根治 |
| R1-1 残余（本次核心） | 上轮四条链路 + ESC/BEL + NBSP，**逐字执行文案内嵌命令** | 5 类改为 System、1 类截断 → **6/6 IDENTITY_KEPT=False 且 re-audit PASS** → **未根治** |
| 用例语料盲区 | 把契约短语名注入两条新用例的 name 元组（隔离树副本） | **2 failed** → 盲区可证：语料选择正是测试全绿的原因 |
| 门禁自身产物一致性 | gen 注册命令 → audit | `A\u2028B`/`A\nB`/`X … Map Y` **gen rc=0 → audit rc=1**（拒绝自身产物） |
| 注入面 | 原始名 + shlex.quote 逐字 bash | 未创建载荷文件、H1 保真 ✓ |
| 非法 UTF-8 首行 | 写 \xff 字节 + 真实漂移 | 解析为 A\ufffdB、判定 resolved/safe、执行后 H1 被归一化为替换字符再 PASS（不可逆） |

## 4. 潜在缺陷清单 (Identified Defect Candidates)
| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | **P1 (Blocker)** | **是**（两个 fail-closed 分支 :136-148 为本次新增文案） | `skills/doc-governance/scripts/audit-doc-health.py:136-148`；`generate-llms-txt.py:164` | R1-1 未根治：fail-closed 分支在「绝不下发 --name」的同时**下发了一条缺省 --name=System 的可执行命令**；占位符从显式参数移入 argparse 默认值，机械断言变绿而后果不变 | 实测 5 类链路（空名/A\nB/A\u2028B/ESC-BEL/NBSP）+ 真实漂移 → 照做 → H1 永久改写为 System → audit 转 rc=0 PASS、零告知；上轮 R1-1 用户可见后果 100% 复现 |
| R1-3 | P2（**并入 R1-1，不重复计数**） | 是（承重行 :109/:112 由本次改写；非贪婪语义历史既有） | `skills/doc-governance/scripts/audit-doc-health.py:109-112,151-155` | `resolved=True` 语义不健全：仅代表正则**前缀**命中，不代表名字可复原；正则无 $ 锚定，非贪婪在首个契约短语处截断 | 名含契约短语/H1 带后缀 → 下发截断名 `--name=X` → 照做后 H1 尾段不可逆丢失并 PASS；同时使门禁拒绝注册命令自身的产物（gen rc=0 → audit rc=1） |
| R1-4 | P2 (Suggestion) | 部分（本次只改到 :5；:15/:79 与 plan:50 未触及） | `docs/index.md:15,79`；`docs/project/plans/2026-10-09-backlog-batch-c-llms-hardening.md:50` | 文档仍描述已被推翻的设计与不成立的承诺 | :15 仍称「可打印字符校验 + 长度上限…消除…畸形名死巷」、:79 仍称「修复建议恒可执行」；plan:50 的「一律不下发 --name 命令，改以 prose 指引」在字面上成立却在语义上掩盖了 prose 内嵌可执行命令（与 R1-1 同源）。均为 P2 文档债，**不阻断** |
| R1-9 | P2 (Suggestion) | 是 | `skills/doc-governance/tests/test_doc_governance_scripts.py:1198-1210,1212-1227` | 新用例判据是**字面量缺席**（`--name=`）而非**用户可见后果**；语料刻意不含契约短语名，也没有「照做后 H1 不得改变」的后果级断言 | 反例注入（把契约短语名加入两条用例的 name 元组）实测 2 条打红；当前测试在 R1-1 完整复现的同时保持全绿——MUT-C3/C4 只证明守卫存在，不证明后果消失 |
| R1-10 | P3 (Suggestion，残余) | 是（新文案 :145、新 docstring :92） | `skills/doc-governance/scripts/audit-doc-health.py:92,145` | 空名场景进入「含不可打印字符或超长」分支，诊断失实；docstring 断言 NBSP 属可打印范畴，实测为 False | " Foo " 已根治（实测保身份）；残余仅为诊断噪声与注释事实错误，**不阻断** |
| R1-11 | P3 (Suggestion，较上轮恶化) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:141,147,154` | 提示命令尾巴 `--root docs --output docs/llms.txt` 字面量由 2 份增至 **3 份** | 三处独立真源、漂移风险上升；抽 1 个模块级常量即可闭合 |
| R1-13 | P3 (Suggestion，历史既有读法 + 新信任模型未覆盖) | 部分 | `skills/doc-governance/scripts/audit-doc-health.py:106,109-112` | `errors="replace"` 把非法 UTF-8 首行无损化为 U+FFFD 后仍判 resolved/safe 并下发 --name | 执行后 H1 被归一化为替换字符（不可逆）且 audit 转 PASS；需手工构造非法字节文件，影响面窄 |
| R1-5 | P3 (Suggestion) | 否（历史既有，本次未改语义） | `skills/doc-governance/scripts/audit-doc-health.py:94` | `isprintable` 仍放行 Mn 组合标记与 U+3164（实测 A+U+3164+B、A+U+0301+B 均判 safe） | 视觉欺骗/渲染异常；64 字符上限约束下无注入面。上轮已登记待办，**不阻断** |
| R1-7 | P3 (Suggestion) | 否（历史既有，本次未改） | `skills/doc-governance/scripts/audit-doc-health.py:120-122` | 「收录数 > 0 但地图缺失」仍跳过判定且治理条文未登记 | 删除 llms.txt 即成永久逃逸面；上轮已登记待办，**不阻断** |
| R1-8 | P3（**可关闭**） | 否（由本次删除 `_sanitize_project_name` 消解） | 已删除函数 | 上轮「长度守卫在物化完整净化串之后」的问题随旧函数删除而消失；新谓词 `all(...)` 提前短路且不物化副本 | 已无对应代码路径 |
| R1-12 | P3 (Suggestion) | 否（历史既有，本次未改） | `skills/doc-governance/scripts/audit-doc-health.py:156-157` | `except Exception` 把异常文本直出为缺陷串，是未净化文本的潜在洗白通道 | 当前无实测可达路径；登记残余风险 |

## 5. 第一轮结论概要
**裁决倾向：不予放行（维持 1 个 P1 阻断项 R1-1）。** 本次修复是「一半真修复、一半换形保留」：

1. **已确证的真修复**：R1-10 对 ASCII 空白包裹名成立——`" Foo "` 现在下发 `--name=' Foo '`，逐字执行后 H1 保身份、audit 转 rc=0（IDENTITY_KEPT=True）；R1-9 的判别力确实建立（加固前实现跑两条新用例 2 failed；MUT-C3 4 failed；MUT-C4 1 failed）；全量 **83 passed**、实仓 **100.0 PASS**、无死代码、注入面闭合、上轮 R1-8 自然消解。
2. **R1-1 未根治（P1，换形保留）**：fail-closed 分支把「不下发 --name」实现为「不下发 --name 字面量，但下发一条缺省即 System 的可执行命令」。隔离树逐字执行文案内嵌命令实测：空名 / A\nB / A\u2028B / ESC-BEL / NBSP 五类全部 → H1 永久改写为 `# System Machine-Readable Knowledge Base Map` → audit 转 rc=0 PASS、零告知；含契约短语名则被 `--name=X` 截断后 PASS。上轮四条链路**无一被实质关闭**，且新增「门禁拒绝注册命令自身产物」的反向不变量破坏（gen rc=0 → audit rc=1）。
3. **测试保真度缺口（R1-9 残余）**：新用例以字面量缺席为判据，因此对上述后果完全无感；反例注入证明只要把契约短语名加入语料，两条用例即打红。当前「全绿」不能作为 R1-1 已闭环的证据。
4. **移交第二轮架构师裁决的焦点**：
   - 唯一 P1 是否维持？正方：用户可见后果与上轮 P1 逐字相同、判定域与修复域仍不自洽、且合规边缘名（NBSP）+真实漂移即可触发；反方最强论据：文案已明示「请人工核对后以正确项目名重新运行」，且实仓（H1 = System）100.0 PASS 不受影响。
   - 若降级，**必须同时处置生成器默认值**，否则降级等于接受「门禁可通过默认参数改写 SSOT 身份」。
   - **最小修法（不新增抽象层，三处可独立落地）**：(a) 两个 fail-closed 分支**删除可执行命令**，仅保留 prose 并显式警告「缺省 --name=System 会改写地图身份」；(b) 生成器侧 fail-closed——当 --output 已存在且其 H1 名与显式/派生名不一致时拒绝落盘（这是唯一能覆盖全部提示路径的根因闸门）；(c) 反解正则加 $ 锚定并改贪婪（`re.fullmatch(r"# (.*) Machine-Readable Knowledge Base Map", …)`）以关闭契约短语截断。
   - **R1-9 同批收口**：补「照做后 H1 不变」的后果级断言 + 契约短语语料；(d) 顺手把命令尾巴抽成 1 个模块常量（R1-11）。
