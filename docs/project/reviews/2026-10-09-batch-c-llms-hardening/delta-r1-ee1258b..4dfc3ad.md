# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

> **审查模式**: LIGHT_REVIEW · DELTA_RE_LOOP（第 4 轮）｜**区间**: ee1258b..4dfc3ad｜**上一轮阻断项**: [R1-1]（唯一 P1；本轮裁决：**已根治，关闭**）
> **证据基线**: 隔离树 = 工作树 HEAD（4dfc3ad）经 git archive 逐字归档；全部实验在单条自包含命令内完成（mktemp -d → git archive → 实验 → rm -rf）。实验尾部 git status --porcelain 仅含预创建的未跟踪归档目录（唯一例外为本次报告写入）。
> **书写约定**: 本正文中一切控制字节均以转义字面量书写（例如 \n、\u2028、\x1b、\x07），不含真实控制字符。
> **独立复核范围**: 编排者自验四项（86 passed / 实仓 100.0 / MUT-D1 / MUT-D2）+ 我自设的 8 组变异（MUT-D3..D8 与两条 blank 变体）+ 19 类项目名的后果级重放。

## 1. 第一性原理与本质溯源分析
- **改动性质定性**: **本质根因修复（R1-1 已闭环），但写侧不变量仍不完整。** 本轮把闸门装在唯一能覆盖全部提示路径的层——生成器的 CLI 落盘通道（`generate-llms-txt.py:160-189,200`），而不再继续在提示文本上打补丁：提示文案里的字面量校验（上一轮的机械绿）不再是唯一防线。函数级 `generate_llms_txt()` 不加闸门是有意为之（audit 需生成到临时目录做逐字节比对），实测该决策**未形成可达绕过面**：全仓对该函数的调用只有 audit 的一致性检查（写临时文件）与 main()（走闸门），无第三方库式调用点。因此这不是"在外层强加 if 判断掩盖状态机错位"，而是把身份写保护放到了正确的物理位置（写盘前）。
- **物理与业务一致性**: 契约不变量 = "既有地图 H1 的项目身份是 SSOT，任何缺省/照做路径不得改写它"。判定域（audit 反解）、修复域（提示命令）、写入域（生成器）必须对同一身份达成逐字一致。**实测三者现已收敛**：19 类项目名 × 2 条操作（逐字执行门禁提示命令 / 缺省参数直接重新生成），H1 逐字节保持不变；缺省重生成在全部不匹配与不可反解类别上一律 rc=1 且 re-audit 仍 rc=1（**未转 PASS**），只有身份确实相等的类别放行且 H1 不变。上一轮的两条 P1 破坏链（"照做 → System → PASS" 与 "截断名 → PASS"）本轮均不可复现。
- **写侧不变量的残余缺口（本轮新发现）**: 闸门只校验"**已存在文件**的身份"与请求名是否相等，却**不校验待写入的 name 能否从首行反解**。于是首次生成仍可铸出一个永远无法反解的身份：`--name=A\nB` 首次生成 rc=0（闸门见文件不存在即返回），产出的地图首行为 `# A`；此后 audit 一律 rc=1（fail-closed），而**任何** --name 取值都被闸门拒绝（实测 A / A B / System / Old / 原值 全部 rc=1），唯一出路是 rm docs/llms.txt；删除后 audit 对"地图缺失"零登记（R1-7 历史既有），缺省重生成即把身份重置为回落名 System 并 PASS。即：**工具能铸出它自己修不好的状态**，而给出的修复指令不可能被满足。
- **过度设计审计**: **YAGNI 合规，无死代码。** 区间净增 91 行（3 文件），无独立脚本层、无裁决语义解析器、无 .docignore、无共享模块重构；`_reject_identity_rewrite` 仅 1 处调用（generate-llms-txt.py:200），职责单一；R1-11 已闭合（命令尾巴抽为单份常量 `REGEN_COMMAND`，audit-doc-health.py:85，全仓仅 1 处定义 + 1 处引用）。可变性残余：契约短语正则现为 **2 份字面量**（audit-doc-health.py:111 与 generate-llms-txt.py:172）加 **1 份写入格式**（generate-llms-txt.py:122）共 3 个耦合真源；`out_path` 表达式在 :200 与 :202 重复书写。
- **奥卡姆剃刀（更精简的原生解法）**: 现设计把"默认参数即身份改写"这一根因，转化为"任何不匹配一律拒绝"的更硬约束，安全性达标但引入了两类死胡同（不可反解类的提示不可执行、显式改名无任何合法通道）。更精简的等价加固只需在写侧补一条不变量：`--name` 缺省为 None，落盘前若目标已存在且未显式声明身份则**沿用既有 H1 反解出的 name**（默认路径零改写 = 直接消除 P1，且无需拒绝即可修复漂移）；再在 generate 前校验 `re.fullmatch` 能从 `f"# {name} Machine-Readable Knowledge Base Map"` 的首行反解出逐字相同的 name（一条断言即封死本轮的"陷阱门"）。当前实现的额外失败面（拒绝一切显式改名、fail-closed 文案不可执行）并非需求所必需。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）
未激活（非客户端/SSR 改动）。区间仅触及 Python 治理脚本、unittest 用例与 Markdown 报告，无 *.tsx/*.jsx/*.vue/*.svelte、无 "use client"/"use server"、无 react/next 导入。
- **Rules of Hooks 合规性**: 未激活（非客户端/SSR 改动）。
- **SSR 水合与 Storage 防御**: 未激活（非客户端/SSR 改动）。
- **渲染纯度与全局可变状态**: 未激活（非客户端/SSR 改动）。
- **（本维度内的等价检查）终端注入面**: 新闸门的拒绝信息对既有名与请求名均以 !r（repr）输出，实测含 \x1b]0;PWNED\x07 的名字在 stderr 中呈现为转义文本，无裸 ESC/BEL 落地；提示命令侧沿用 shlex.quote，逐字执行 4 类注入形状名（单引号+双引号+反斜杠+$、$(touch ...)、反引号命令替换、A;B|C&D）全部 h1_kept=True 且未生成载荷文件。该面较上轮无回归。

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

### 独立复核矩阵（全部在 4dfc3ad 隔离树实测）
| 核验项 | 方法 | 实测结论 |
|:---|:---|:---|
| 全量回归 | pytest skills/doc-governance/tests/ -q | **86 passed in 12.28s** ✓ 与编排者自验一致 |
| 实仓健康度 | audit-doc-health.py --root docs（只读） | **rc=0 / 100.0 PASS**；运行前后 git status 无差异 ✓ |
| R1-1 缺省重生成（19 类名） | 漂移地图 + 缺省命令（含 --output 与缺省落点两种） | 全部**H1 逐字节不变**；不匹配/不可反解类 rc=1 且 re-audit rc=1（未转 PASS）；仅身份相等类放行且 H1 不变 ✓ |
| R1-1 逐字执行门禁提示 | 提示中 --name= 片段交给 bash 逐字执行（8 类：契约短语名、" Foo "、--root、#Tag、CJK 名等） | 全部 H1 逐字节不变、漂移被合法修复、re-audit rc=0 ✓（上轮"截断名 --name=X → PASS"不可复现） |
| MUT-D1 拆闸门 | 删除 main() 中的闸门调用 | **1 failed**（test_generator_refuses_identity_rewrite_with_default_name）✓ |
| MUT-D2 安全谓词恒真 | _is_safely_displayable → return True | **5 failed** ✓ 与编排者自验一致 |
| MUT-D3 反解正则回退为非贪婪无锚定 | re.match(r"# (.*?) ...") | **1 failed**（test_contract_phrase_name_round_trips）✓ R1-9 的 audit 侧语料盲区已关闭 |
| MUT-D4 fail-closed 分支恢复可执行命令 | 改写分支文案含 generate-llms-txt.py | **1 failed**（test_failclosed_hints_contain_no_executable_command）✓ |
| MUT-D5 闸门正则回退为非贪婪 | 同 :172 换 re.match 非贪婪 | **86 passed（无感）**；行为探针：契约短语名的提示命令变为 rc=1 死胡同 ← 盲区 |
| MUT-D6 闸门对不可反解 H1 改为放行 | match is None → return | **1 failed** ✓ 该 fail-open 分支确被覆盖 |
| MUT-D7 不可读文件改为拒绝 | except OSError → sys.exit(1) | **86 passed（无感）** ← 该路径零覆盖 |
| MUT-D8 闸门无条件拒绝 | if match.group(1) == requested_name → if False | **86 passed（无感）** ← 放行路径零覆盖，闸门可退化为"全阻断"而全绿 |
| gen→audit 自洽性 | 首次生成 9 类名后立即 audit | 契约短语名/" Foo "/--root/#Tag/CJK/NBSP/超长名 **gen rc=0 → audit rc=0**（上轮"门禁拒绝注册命令自身产物"已修复）；仅 A\nB、A\u2028B 仍 gen rc=0 → audit rc=1（陷阱门） |
| 不可读但可写的地图 | chmod 0200 后跑缺省重生成 | **fail-open：rc=0、stderr 为空、H1 由 # Secret ... 静默改写为 # System ...** |
| 非法 UTF-8 身份（R1-13） | H1 写入 # A\xffB ... 后照做提示 | 提示 --name='A\uFFFDB' → gen rc=0 → 字节被归一化为 A\xef\xbf\xbdB → re-audit rc=0（不可逆，闸门未能拦截） |
| R1-7 缺失地图逃逸 | 删除 llms.txt 后 audit → 缺省重生成 | audit rc=0 且**不报机器地图缺陷** → 重生成 H1=System → re-audit PASS |

### 攻击路径 1（已封堵，反证）: 照做提示 / 缺省重生成 → 身份永久改写 → 转 PASS（上一轮 P1）
- **触发条件**: 地图真实漂移 + 首行名无法反解（空名 / A\nB / A\u2028B / A\u2029B / A\x85B / A\rB / ESC-BEL / NUL / 超长 / NBSP）或名含契约短语。
- **本轮复现推演**: audit 检出漂移 → 分支判定 → ① 可安全回显者给出 `--name=<原值>` 命令；② 否则纯 prose 且无脚本名。**逐字执行 ① 后 H1 逐字节不变**（Bash 往返 shlex 无损），漂移被修复，re-audit rc=0 属**正确的合法修复**；**逐字执行缺省重生成则一律 rc=1 且 H1 不变、re-audit 仍 rc=1**。
- **影响结果**: 身份改写链**已闭环**（19/19 类 H1 保持）。上一轮"5 类 → System、1 类被截断、6/6 IDENTITY_LOST 且转 PASS"不可复现。
- **涉及代码**: generate-llms-txt.py:160-189,200；audit-doc-health.py:138-157

### 攻击路径 2: 不可读但可写的地图 → 闸门 fail-open → 身份静默改写（新）
- **触发条件**: 既存 docs/llms.txt 权限为 0200（owner 可写不可读，例如异常 umask/chmod 事故、外部工具生成）。无需对抗权限。
- **复现推演**: :166 is_file() → True；:169 read_text() → PermissionError（属 OSError）→ :170-171 `except (OSError, IndexError): return`（**放行**）→ 继续落盘 → H1 由 `# Secret ...` 变为 `# System ...`，rc=0、stderr 为空、零告知。
- **影响结果**: 与上一轮 P1 同型的"静默身份改写 + 无告知"仍存在一条可达路径；但 audit 同样读不了该文件（走 fail-closed 且不下发命令），正常运维不会被引导至此，故定为 P2 而非阻断项。同一 fail-open 亦覆盖 0 字节地图（无身份可失，属可接受）。
- **涉及代码**: generate-llms-txt.py:166-171

### 攻击路径 3: 自铸陷阱门——工具产出它自己修不好的地图（新）
- **触发条件**: 首次生成时 `--name` 含行分隔符（A\nB、A\u2028B、A\u2029B、A\x85B、A\rB…），或历史上遗留此类 H1。
- **复现推演**: 目标不存在 → 闸门 :166 直接返回 → 落盘成功（rc=0，首行 `# A`）→ 之后 audit :111 fullmatch 失败 → fail-closed 文案要求"以显式 --name 重新生成" → 任何 `--name`（原值 / 前缀 / System）都被 :172-181 判为不可反解而 rc=1 → **提示的修复路径在本状态下不可执行**；唯一出路 rm docs/llms.txt，随后按 R1-7 逃逸面重置为 System。另注：generate-llms-txt.py:184-186 的"如确需改名，请显式传入 --name"出现在用户**正是**显式传入 --name（或未传而取缺省）的分支里，属自相矛盾的拒绝文案；据此无法完成任何合法改名（删文件除外）。
- **影响结果**: 地图进入"audit 永久 rc=1 + 无任何合法原地修复"的硬阻断态；逃生通道（删除 SSOT + 回落名）同时抹掉身份且不被 audit 登记。这是本轮**新引入**的运维死胡同（此前该状态可通过重生成就地修复，代价是身份被改写）。
- **涉及代码**: generate-llms-txt.py:166-167,172-189,200；audit-doc-health.py:112-114,138-144；audit-doc-health.py:123-124（R1-7）

### 攻击路径 4（未遂反证）: 提示命令的注入面与闸门输出污染
- **触发条件**: 身份名形如 `$(touch PWNED)` / 反引号 / 引号反斜杠混合，或含 \x1b]0;...\x07。
- **复现推演**: 提示经 shlex.quote 拼装、bash 逐字执行；闸门拒绝信息以 !r 输出。
- **影响结果**: **未发现可达注入面**——4/4 类名 h1_kept=True、无载荷文件落地；闸门 stderr 无裸 ESC/BEL。该面较上轮无回归。
- **涉及代码**: audit-doc-health.py:151-157；generate-llms-txt.py:184-189

## 4. 潜在缺陷清单 (Identified Defect Candidates)
| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | **P1 → 已闭环（关闭）** | 是（本轮落实生成器侧根因闸门） | generate-llms-txt.py:160-189,200；audit-doc-health.py:111,138-157 | 上一轮唯一阻断项：照做提示或缺省重生成会把既有地图身份静默改写并转 PASS | 19 类名 × 2 条操作实测 H1 逐字节不变、不匹配类 re-audit 仍 rc=1；MUT-D1/D6 打红。**根因面已消除**，仅余下述低可达性残余 |
| R1-14 | P2 (Suggestion) | 是 | tests/test_doc_governance_scripts.py:1182-1196,1166-1180,1243-1258 | 闸门**放行路径零覆盖**：MUT-D8（无条件拒绝）与 MUT-D5（闸门正则回退）均 **86 passed 全绿**；唯一"执行提示"的用例只断言 rc != 2，rc=1 同样通过；`test_legit_edge_names...` 先 unlink 再生成，绕开了闸门 | 闸门可退化为"全阻断"或把合法提示变成死胡同而不被任何测试发现；"误伤合法场景"这一维恰好无回归保护 |
| R1-15 | P2 (Suggestion) | 是 | audit-doc-health.py:138-144,111；generate-llms-txt.py:166-167,172-181 | fail-closed 文案"再以显式 --name 重新生成"在**不可反解类**（行分隔符名）永远无法执行：闸门对该类拒绝一切 --name 取值；且首次生成不受闸门约束，工具自铸此状态 | 实测 A\nB：gen(--name=A/A B/System/Old/原值) 全部 rc=1，仅 rm 可行；删除后按 R1-7 逃逸面重置为 System 并 PASS → 修复路径与保护目标互相抵消 |
| R1-16 | P2 (Suggestion) | 是 | generate-llms-txt.py:184-189,200 | 拒绝文案自相矛盾："如确需改名，请显式传入 --name"出现在用户**已经**显式传入 --name 的分支；且当前无任何合法改名通道（删文件除外） | 实测 --name=New 于旧名地图 rc=1；运维/智能体将按文案重试同一条被拒命令形成死循环；改名能力（--name 项目名称）实质丧失 |
| R1-17 | P2 (Suggestion) | 是（新增信任模型下的 fail-open 分支） | generate-llms-txt.py:166-171 | 闸门对**不可读但可写**的既有地图 fail-open（except OSError → return），对 0 字节地图同样放行 | 0200 权限下实测 rc=0、stderr 空、H1 由 # Secret ... 静默改写为 # System ...；与 P1 同型的静默改写仍有一条可达路径（触发需异常权限，故非阻断） |
| R1-13 | P3 (Suggestion，历史既有根因 + 新闸门继承) | 部分 | audit-doc-health.py:107,111；generate-llms-txt.py:169,172 | errors="replace" 使非法 UTF-8 首行被无损化后仍判 resolved/safe；闸门同样以替换字符读取并判"身份相等" | 实测 H1 # A\xffB ... → 提示 --name='A\uFFFDB' → gen rc=0 → 字节归一化为 A\xef\xbf\xbdB → re-audit PASS；"照做提示不可能改写 H1"的断言对该类过强。最小修法：闸门改按字节比较（或 strict/surrogateescape 读取） |
| R1-18 | P3 (Suggestion) | 是 | audit-doc-health.py:111；generate-llms-txt.py:122,172,200,202 | 契约短语正则 2 份 + 写入格式 1 份共 3 个耦合真源；out_path 表达式在 :200/:202 重复书写；闸门 sys.exit 内嵌使路径只能以子进程测试 | 正则/格式任一处漂移即静默产生"过度拒绝（死胡同）"或"fail-open"，且 MUT-D5 证明现有测试无感；建议抽 1 个模块常量供三侧共用 |
| R1-19 | P3 (Suggestion) | 是 | generate-llms-txt.py:200,204-210 | 闸门先于归档红线与 --root 存在性检查执行，错误归因错位 | 实测 --output 落在 project/reviews/** 或 --root 不存在时，报出的是"身份不匹配，请显式 --name 改名"而非归档红线/根目录缺失；照做改名后才会撞上真正原因，误导诊断 |
| R1-20 | P2 (Suggestion，文档同步) | 是 | docs/GOVERNANCE.md:87,97；skills/doc-governance/SKILL.md:142；docs/explanation/architecture/doc-governance-design.md | 新增的"身份写保护 + 拒绝改写"CLI 契约未在任何治理文档登记（全仓 grep 身份/写保护/identity 无命中）；GOVERNANCE 第 3 条所称"注册命令"现依赖地图身份恰等于 argparse 缺省 System | 实测自定义身份地图（# CR 公共技能库 ...）内容自洽且 audit rc=0，但**文档登记的注册命令（无 --name）rc=1 被拒**；文档与实现互相矛盾，且该技能面向下游仓库分发时缺省命令普遍失效 |
| R1-10 | P3 (Suggestion，残余，文案行本轮被重写) | 部分 | audit-doc-health.py:93,147 | 空名场景落入"含不可打印字符或超长"分支（真实原因是空值，既不不可打印也不超长）；docstring 仍称 NBSP 属可打印范畴 | 地面真值实测 '\u00a0'.isprintable() == False（上轮结论正确，我的初测曾因误写 repr(x).isprintable() 得到假 True，已更正如上）；诊断噪声与注释事实错误，不阻断 |
| R1-5 | P3 (Suggestion) | 否（历史既有，本次未改） | audit-doc-health.py:95 | isprintable 仍放行 Mn 组合标记与 U+3164（实测二者 isprintable()==True） | 视觉欺骗/渲染异常；64 字符上限约束下无注入面；上轮已登记待办 |
| R1-7 | P3 (Suggestion) | 否（历史既有，本次未改；但被 R1-15 的逃生通道放大） | audit-doc-health.py:123-124 | "收录 > 0 但地图缺失"仍跳过判定且治理条文未登记 | 实测删除 llms.txt 后 audit rc=0 且不报机器地图缺陷，成为永久逃逸面；本轮闸门把"不可反解身份"的唯一出路指向删除，故该逃逸面的现实权重上升 |
| R1-12 | P3 (Suggestion) | 否（历史既有，本次未改） | audit-doc-health.py:158-159 | except Exception 把异常文本直出为缺陷串 | 当前无实测可达路径；登记残余风险 |

**计数**: 0 × P0，0 × P1（唯一 P1 已闭环），4 × P2（R1-14/15/16/17 为新引入+1 个 P2 文档同步 R1-20），其余为 P3 残余与历史既有。**无新增阻断项。**

## 5. 第一轮结论概要
**裁决倾向：放行（R1-1 根治确认，阻断项清零）。** 上一轮唯一 P1 的修复是本轮唯一需要回答的问题，答案是肯定的：

1. **R1-1 已从根因层消除，且是后果级验证**：闸门装在生成器 CLI 落盘前（唯一覆盖全部提示路径的咽喉），19 类项目名 × 2 条操作实测 H1 **逐字节不变**；缺省重生成在全部不匹配/不可反解类别上一律 rc=1 且 re-audit **仍 rc=1（未转 PASS）**；可安全回显的提示命令逐字执行后是**合法的原地修复**（漂移修好、身份保住、re-audit rc=0）。上一轮"5 类 → System、1 类截断、6/6 转 PASS"零复现。
2. **上一轮 R1-3 的反向不变量破坏已修复**：契约短语名（X Machine-Readable Knowledge Base Map Y）现 gen rc=0 → audit rc=0，不再"门禁拒绝注册命令自身产物"；` Foo `、--root、#Tag、CJK、NBSP、超长名的自洽性亦全部通过（唯一例外是含行分隔符的名字，见 R1-15）。
3. **编排者自验独立复现**：86 passed ✓、实仓 100.0 PASS ✓、MUT-D1 打红 ✓、MUT-D2 打红 5 条 ✓；另加 MUT-D3（反解正则回退）打红 1 条 → **R1-9 的 audit 侧语料盲区确已关闭**；MUT-D4（恢复可执行命令）打红 1 条 → fail-closed 文案的机械门禁真实承重；MUT-D6（不可反解 fail-open）打红 1 条。
4. **新发现（不构成阻断，但建议同批收口）**：R1-14 闸门**放行路径零测试覆盖**（MUT-D8 全阻断 / MUT-D5 正则回退均 86 passed 全绿）；R1-15 fail-closed 提示在不可反解类**不可执行**，且工具首次生成即可自铸该状态（陷阱门 → 唯一出路是删除 SSOT）；R1-16 拒绝文案自相矛盾且**不存在任何合法改名通道**；R1-17 闸门对不可读（0200）/空文件 **fail-open**，实测静默把身份改写为 System。这四项的共同最小修法不是加抽象层，而是把写侧不变量补齐：① `--name` 缺省 None、落盘前由既有 H1 沿用身份（默认路径零改写）；② 生成前断言 name 能从首行反解，否则拒绝（封死陷阱门）；③ 闸门对 OSError 一律拒绝（不区分"不存在"与"读不了"）；④ 补一条"合法重生成必须 rc=0 且 H1 不变"的放行级用例，与既有拒绝级用例成对。
5. **移交第二轮架构师元审判的焦点**：(a) 是否认可 R1-1 关闭、本轮以零阻断项放行；(b) 若要求同批收口，优先级建议 R1-15 > R1-17 > R1-16 > R1-14（前者是硬阻断态与静默改写，后者是测试保真度）；(c) 请确认 R1-13（闸门字节盲区）、R1-5、R1-7、R1-10 残余、R1-12 作为已登记待办继续保留，本轮不以历史技术债阻断提交。
