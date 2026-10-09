# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **混合定性 —— 2 项本质根因修复 + 1 项半程加固（非浅层修补，但未达其宣称的完整效果）**。
  - **D1-4（`shlex.quote`）= 根治**：原缺陷的物理成因是「仓库可控文本被原样拼成一个 shell 词，词的边界由双引号定义，而双引号不阻断 `$()` 与反引号展开」。单引号 + 转义把该词的边界改为「除单引号外全部字面」，实测 16 组恶意首行中凡能进入 shell 解析的载荷全部坍缩为**单个字面 argv**，注入 canary 零创建（矩阵见第 5 节）。这不是换文案，是把「数据 → 代码」的边界判断修正了。
  - **R1-6/D1-1（新增 `test_audit_blocks_drift_on_a_perfect_tree`）= 根治**：上轮空转的物理根因是「漂移夹具自身是零控制头裸树，`总分 65.0 < 80.0` 已独立满足 `rc≠0`，与硬阻断接线无关」。本轮不再更换断言字符串，而是改变夹具的**物理状态**：先构造合规树并**断言 baseline `rc==0`**，再注入漂移。实测 baseline 与 drift 同为 `总得分 100.0`（`llms.txt` 是 `.txt`，不参与评分/断链扫描），drift 的唯一 REJECT 原因是 `机器地图不一致`——于是 drifted `rc≠0` 与 PASS 条件中的 `and not res.get("llms_map_issue")`（`audit-doc-health.py:679`）构成**充要关系**。独立重跑 MUT-E1（仅删该行）→ 本用例打红，其余 8 条全绿（上轮为 8/8 全绿）。
  - **R1-1/D1-2（两条零覆盖夹具补根文件）= 半程根治**：`..._map_exists_but_nothing_indexable` 已真正承重（MUT-A 打红，pre-fix 夹具 + MUT-A 则全绿）；`..._nothing_indexable` 仍**不承重**（MUT-A 下仍绿），详见 D2-1。宣称的「使检查真正被执行」对第一条成立、对第二条只成立到「函数被调用」为止。
- **物理与业务一致性**: 门禁的物理对象是「`<root>/llms.txt` 与注册命令生成物逐字节相等」。新用例第一次把「漂移是唯一阻断源」这一**因果唯一性**工程化：评分维度与 `llms.txt` 完全解耦（`llms.txt` 不在 `all_md_files`，也不被 `scan_directory` 的 `*.md` 扫描覆盖），因此 baseline 与 drift 的一切非地图维度逐字节同构，唯余地图差异——断言与物理因果同构，而非与某个字符串同构。`shlex.quote` 同样是把「仓库可控文本 → shell 词」的边界放回正确层级。但两条边界仍未闭合：① 同一数据流仍**无转义地跨越到终端层**（裸 ESC 原样落到 stdout/CI 日志，D2-3）；② 提示命令的 **argv 形状**未归一（以 `-` 开头的名字使修复建议不可执行，D2-4）。另有结构性事实：PASS 条件（`:679`）与 REJECT 原因清单（`:694`）仍是两份真源，这正是新加的 `reject_lines` 断言**抓不住 MUT-E1** 的原因（MUT-E1 下原因行仍打印 `机器地图不一致`，用例仍绿）——该断言只锁文案、不锁接线，属历史 D1-7② 的残留，本轮未修且不影响新用例的承重性。
- **过度设计审计**: **YAGNI 合规，未发现投机性抽象或新的中间层。** 生产代码仅 `import shlex` + 2 行（`:21,113-116`），无新增依赖（stdlib）；测试仅 +39 行（1 个类常量 `_CTRL` + 1 个私有助手 + 1 条用例），未引入独立脚本层、裁决语义解析器、`.docignore` 或共享模块重构。唯一结构债是 DRY：`_CTRL`（`tests:1055`）与本文件内 8 处内联控制头模板重复，且被放在两个测试方法之间（风格上类常量宜置顶）；该债为历史既有，**不建议本轮顺手重构**（会扩大 blast radius 且与目标无关）。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

未激活（非客户端/SSR 改动）

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

- **攻击路径 1: 无地图守卫被删 —— 全量 76 条用例全绿，而每一次无地图仓库体检都变成硬阻断（测试盲区）**:
  - **触发条件**: 任一后续重构删除 `audit-doc-health.py:99-100` 的 `if not llms_file.exists(): return ""`（例如统一「三态返回值」时最容易发生）。
  - **复现推演**: ① 隔离树删除该守卫；② 造普通仓库树（`explanation/a.md` 有可收录文档、**无** `llms.txt`）→ 实测输出 `⛔ 机器地图一致性缺陷: 机器地图一致性检查无法完成: [Errno 2] No such file or directory: '…/llms.txt'` + `🚫 REJECTED（得分 65.0 < 门槛 80.0；机器地图不一致）`；③ 同一变异跑全量测试 → `76 passed`。加固后的 `test_audit_skips_when_nothing_indexable` 恰是唯一「无地图」的 audit 用例，但其夹具的 `index.md` 是**根文件**（`generate-llms-txt.py:127-129` 对 `len(rel_parts)==1` 直接 `continue`），可收录数为 0，于是「无地图 ⇒ 跳过」与「零覆盖 ⇒ 豁免」在输出上不可区分，用例对二者都不敏感。
  - **影响结果**: 该守卫失效不会打红任何一条用例，却把所有尚未接入 `llms.txt` 的仓库（或地图被误删的仓库）从「PASS」翻成「REJECT 且原因不可收敛」——门禁可用性静默失效，且失败信息把「引入 llms.txt 之前」的历史项目判为不健康。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:99-100`；`skills/doc-governance/scripts/generate-llms-txt.py:127-129`；`skills/doc-governance/tests/test_doc_governance_scripts.py:1011-1024`。
- **攻击路径 2: R1-1 豁免被删 —— 单点拦截，第二条「零覆盖」用例仍恒真**:
  - **触发条件**: 删除 `audit-doc-health.py:108-110` 的 `if written == 0: return ""`（即回退 R1-1 的修复）。
  - **复现推演**: 隔离树 A/B。MUT-A + 全量套件 → `1 failed, 75 passed`，唯一失败者 `test_audit_skips_when_map_exists_but_nothing_indexable`；`test_audit_skips_when_nothing_indexable` 仍绿。插桩（在函数入口/无地图早退/生成返回值/`written==0` 分支各打标记）实跑两条夹具：no-map 夹具 → `MARK:CALLED` → `MARK:NO_MAP_EARLY_RETURN`（**豁免分支不可达**）；map-exists 夹具 → `MARK:CALLED` → `MARK:GEN_WRITTEN=0` → `MARK:ZERO_EXEMPTION`（真实触达）。pre-fix 夹具 + MUT-A → 两条全绿；pre-fix 夹具 + 未变异脚本 → `76 passed`，与上轮「空转」判定完全一致。
  - **影响结果**: R1-1 的回归保护是**单点**的；第一条用例提供的保护力为零，却以 docstring 声称覆盖「不可修复死胡同」；若后续仅重构/移动 map-exists 场景，保护即整体消失。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:108-110`；`skills/doc-governance/tests/test_doc_governance_scripts.py:1011-1024,1038-1051`。
- **攻击路径 3: 终端控制序列注入（`shlex.quote` 的能力边界之外）**:
  - **触发条件**: `<root>/llms.txt` 首行被可控（外部 PR / 被污染分支），且该地图处于漂移态。
  - **复现推演**: 首行 `# A\x1b]0;PWNED\x07 Machine-Readable Knowledge Base Map` → `_map_project_name` 反解出含裸 ESC/BEL 的名字 → `shlex.quote` 只做 shell 层转义（ESC 属不安全字符，被包进单引号，但**字节原样保留**）→ 审计 stdout 实测 `raw_ESC=True`：`请以 --name 'A<ESC>]0;PWNED<BEL>' 运行 …`。同理 NUL：实测提示命令在 execve 层不可执行（`ValueError: embedded null byte`）。
  - **影响结果**: 不构成本轮指控的 RCE（命令替换已闭合），但攻击者仍可借 OSC 0/OSC 52 篡改维护者终端标题或（在脆弱终端上）剪贴板，并把裸控制字节写进 CI 日志；量化影响需人工查看门禁输出，故仅为残留面。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:83-91,113-116`。
- **攻击路径 4: 选项伪装名让「修复建议」变成死巷**:
  - **触发条件**: 首行项目名形如 `--root`（`-` 属 `shlex` 安全字符集，不会被引号包裹）。
  - **复现推演**: 提示命令逐字为 `--name --root 运行 generate-llms-txt.py --root docs --output docs/llms.txt`；把该 argv 交给**真实** `generate-llms-txt.py` → 实测 `rc=2`、`error: argument --name: expected one argument`、不落盘。因 `shlex.quote` 保证输出恒为**单个 shell 词**，攻击者无法借此重定向 `--root/--output` 或注入第二个参数（已实测 `--name` 位置被 stub 收到的 argv 恒为单值）。
  - **影响结果**: 攻击者可让门禁的修复指引不可执行（误导/耗时），但不产生执行或写入；修复前 `--name "--root"` 经 shell 解析同样是 `--root`，故行为等价、非本 diff 引入。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:113-116`。
- **攻击路径 5: 反解正则非幂等 → 静默改名（历史既有，本 diff 未改）**:
  - **触发条件**: 项目名自身包含哨兵子串 `" Machine-Readable Knowledge Base Map"`。
  - **复现推演**: 首行 `# A Machine-Readable Knowledge Base Map Machine-Readable Knowledge Base Map` → 非贪婪 `(.+?)` 反解出 `A` → 提示改为 `--name A`；维护者照做即静默丢掉原名。反向：名以空格开头时反解可保留前导空格（实测 ` LeadSpace` 往返一致），真正的不可逆点是**空名**（`#  Machine-…` 双空格 → 不匹配 → 回落 `System`）。
  - **影响结果**: 合法/边界输入被判漂移或静默改名（非死胡同，按提示可收敛）；D1-5 已在上一轮登记为待办，本轮无恶化。
  - **涉及代码**: `skills/doc-governance/scripts/audit-doc-health.py:83-91`。

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| D2-1 | P3 (Suggestion) | 是（本 diff 的半程修复未闭合） | `tests/test_doc_governance_scripts.py:1011-1024`；`scripts/audit-doc-health.py:99-100,108-110` | `test_audit_skips_when_nothing_indexable` 加固后仍**不承重**：其 `index.md` 是根文件（不入选收录域），函数在 map-absent 守卫处早退，**永远到不了** R1-1 的 `written==0` 豁免分支。MUT-A 下本用例仍绿（全量仅 1 failed），插桩实测 `MARK:NO_MAP_EARLY_RETURN` 而非 `MARK:ZERO_EXEMPTION` | 断言对象是「输出不含『机器地图』」，在无地图时对豁免分支天然不敏感；docstring 宣称的属性实际由另一条用例单点覆盖 |
| D2-2 | P3 (Suggestion) | 历史既有（本 diff 未闭合） | `scripts/audit-doc-health.py:99-100`；`tests/…:1011-1024` | 「无地图 ⇒ 本项不适用」这条守卫**全量零覆盖**：MUT-B（删除守卫）→ `76 passed`，而行为变为对所有「有可收录文档但无 `llms.txt`」的仓库硬阻断（实测 `机器地图一致性检查无法完成: [Errno 2]` + `REJECTED（…；机器地图不一致）`）。加固后的 test 1 是唯一无地图 audit 用例，但根-only 夹具使其可收录数为 0，无法区分两种跳过语义 | 该守卫一旦被重构删除，测试网无感；门禁把「尚未接入 llms.txt」的存量仓库判为不健康，属可用性静默回归 |
| D2-3 | P3 (Suggestion) | 历史既有（同一数据流的残留面，本 diff 未覆盖） | `scripts/audit-doc-health.py:113-116` | `shlex.quote` 只做 shell 层转义，不剥离终端控制字符：含 `ESC/OSC` 的首行被原样写进 stdout（实测 `raw_ESC=True`），含 `NUL` 时提示命令在 execve 层不可执行 | 输出跨越到终端语义域：OSC 0/OSC 52 可篡改窗口标题/剪贴板，裸控制字节污染 CI 日志；无代码执行 |
| D2-4 | P3 (Suggestion) | 历史既有（等价行为，非本 diff 引入） | `scripts/audit-doc-health.py:113-116` | 以 `-` 开头的名字（`--root` 等）不被引号包裹，提示命令变成 `--name --root …`；真实 generate 实测 `rc=2 expected one argument`，不落盘 | 攻击者可控首行可让修复建议不可执行（误导/耗时）；因输出恒为单 shell 词，无法重定向 `--root/--output`，无 RCE |
| D2-5 | P3 (Suggestion) | 历史既有 | `scripts/audit-doc-health.py:83-91,113-116` | 反解结果无「可打印字符 + 长度」校验：NUL/ESC 原样进入提示文案，10 万字符名字使缺陷行膨胀 10 万字节 | 与 D2-3 同源；建议合并为一条最小修法（`isprintable()` 校验 + 长度上限，非法即回落占位名） |
| D2-6 | P2 (Suggestion) | 历史既有（上轮 D1-3，本轮被测试**固化为期望行为**） | `tests/…:1038-1051`；`scripts/audit-doc-health.py:108-110`；`scripts/check-doc-links.py:216` | 零覆盖豁免仍是真实假阴性：无可收录文档时 `written==0 → return ""`，含死链/过期的**手写** `llms.txt` 被 `rc=0 PASS 100.0` 接受；`llms.txt` 为 `.txt`，断链扫描只覆盖 `*.md`，其条目无任何其他门禁兜底。本轮加固后的 test 2 恰好**断言**该状态下「不得出现『机器地图』」，等于把假阴性写成绿色契约 | 唯一残留的对外拓扑地图退化为无鉴权文本，AI 消费者按图索骥必然 404；若不在 GOVERNANCE 显式登记该边界，下一轮会把该测试当正确性契约，永久锁死漏检 |
| D2-7 | P3 (Suggestion) | 历史既有（上轮已登记，本 diff 未触及） | 汇总项 | D1-5/D1-6（反解非幂等、项目名自证循环）、D1-7（路径硬编码与 PASS/REJECT 双真源）、D1-8（双读 TOCTOU）、R1-3（硬链接穿透）、R1-4（删除即放行）、R1-8（`.pyc` 回写）、R1-9（收录域含未跟踪文档）——维持上轮定性与 P2/P3 级别，本轮不重复考古 | 与本次变更行无直接因果，登记备查 |

**定级口径说明**: 本轮**未判定任何 P0/P1，不阻断交付**。D2-1/D2-2 是**回归保护力**缺口（属性本身由 `..._map_exists_but_nothing_indexable` 单点覆盖且实测可打红，不改变当前交付行为）；D2-3/D2-4/D2-5 是 D1-4 已闭合后的**同数据流残留面**（均需人工查看输出才可触发，无执行、无写入）；D2-6 为历史既有、需登记而非修码。**没有任何一项由本 diff 直接造成新的执行/写入/状态机破坏。**

## 5. 第一轮结论概要

- **总体裁决**: **Zero P0 / Zero P1（不阻断交付）。** 三项二次加固复核结果：**D1-4 根治、R1-6 根治、R1-1 半程根治**；无次生缺陷。独立复现证据：隔离树（`git archive 141cf99` + `mktemp -d`）内全量 **76 passed**；实仓自体检 **总得分 100.0 / 100，PASS，rc=0**；MUT-E1 删除 `:679` 的 PASS 接线 → `test_audit_blocks_drift_on_a_perfect_tree` **打红（此前该变异 8/8 全绿）**，其余 8 条绿；MUT-G 删除 `:545` 的 `llms_map_issue` 键 → 2 条漂移用例同时打红（双保险）。实验全部在 `/tmp` 隔离副本内完成，实验尾部 `git status --porcelain` 仅含编排者预创建的未跟踪归档目录。
- **本轮变异实验矩阵（A/B 实测，非阅读推断）**:

| 变异 | 内容 | 观测结果 | 结论 |
|:---|:---|:---|:---|
| MUT-E1 | 删 `audit-doc-health.py:679` 的 `and not res.get("llms_map_issue")` | 新用例 FAIL（`0 == 0`），8 passed | 接线承重 ✓ 根治 |
| MUT-G | 删 `:545` 的 `llms_map_issue` 键 | 新用例 + `test_audit_detects_llms_map_drift` 双红 | 双保险 ✓ |
| MUT-A | 删 `:108-110` 零覆盖豁免 | 仅 `..._map_exists...` 红，全量 1 failed/75 passed | 单点覆盖，test 1 空转（D2-1） |
| MUT-A + pre-fix 夹具 | 同上 + 移除两处 `index.md` 行 | 两条全绿 | 印证上轮「空转」判定 |
| pre-fix 夹具（脚本未变异） | 仅移除两处 `index.md` 行 | 76 passed | 加固价值来自本次夹具 |
| MUT-B | 删 `:99-100` 无地图守卫 | 全量 76 passed；行为变为全仓硬阻断 | 历史盲区（D2-2） |
- **对编排者五个问题的直接回答**:
  1. **(a) D1-4 是否根治**：**根治（针对其指控的 shell 命令注入面）**。16 组恶意首行实测：`$(touch …)`、反引号、双/单引号闭合、`${IFS}`、`$(id)` 全部被 `shlex.quote` 收敛为单个字面 argv，canary 零创建；提示词与 `shlex.quote(project_name)` 逐字符相等（`token == shlex.quote(name)` 全 True）。**残留（均 P3）**：终端控制字符未清洗（D2-3）、NUL 使提示不可执行（D2-5）、`-` 开头名字使修复建议变成死巷（D2-4，行为等价于修复前）。复制粘贴**不再可能执行任意代码**，但「攻击者可控首行影响人读文案」这一性质本身未消除。
  2. **(b) R1-6 是否真正根治**：**是**。独立重跑 MUT-E1 打红（关键断言 `assertNotEqual(drifted.returncode, 0)`）；新用例**无其他空转路径**：baseline 断言是硬 `assertEqual(rc==0)`（未弱化，夹具实测 100.0 PASS）；因 `llms.txt` 与评分/断链扫描完全解耦，drift 与 baseline 的同名维度逐项相同、REJECT 原因**仅** `机器地图不一致`，故 `rc≠0` 只可能由该接线提供；夹具未来若失效则 baseline 断言先打红（fail-closed，不会静默转绿）。唯一口径提醒：新加的 `reject_lines` 断言（`:979-983`）**不承重**——MUT-E1 下它仍绿（原因清单与 PASS 条件是两份真源），它锁的是文案而非接线；接线由新用例独立锁定。
  3. **(c) R1-1 用例是否真的触达判定**：**一条是，一条否**。`..._map_exists_but_nothing_indexable` 实测走完 `CALLED → GEN_WRITTEN=0 → ZERO_EXEMPTION`，MUT-A 打红（此前空转，现已根治）；`..._nothing_indexable` 实测 `CALLED → NO_MAP_EARLY_RETURN`，**到不了** R1-1 豁免分支，MUT-A 下仍绿——其加固只到「函数被调用」，宣称的「检查真正被执行」对该用例名不副实（D2-1）。此外暴露一条历史盲区：无地图守卫零覆盖（D2-2）。
  4. **(d) 是否引入次生缺陷**：**未发现**。① 可读性：`System` 现输出 `--name System`（无引号）、含空格/中文名输出 `--name 'CR 公共技能库'`、含撇号名输出 `'O'"'"'Brien Docs'`——风格由 `""` 变为 `''`，但复制粘贴语义经实测完全等价，无功能退化；② 夹具隔离：`setUp` 每例 `mkdtemp`，打乱顺序执行 4 条相关用例 → 4 passed，无跨用例污染；③ `_CTRL` 与 unittest 收集机制无冲突：`getTestCaseNames` 收集 9 条、`_CTRL`/`_prepare_compliant_tree` 未被收集、模板无残留花括号；④ 新增标准差集导入不改变任何现有断言；⑤ 新用例的副作用仅为自身临时目录，`tearDown` 清理。
  5. **(e) YAGNI**：**合规**。未引入独立脚本层、裁决语义解析器、`.docignore` 或共享模块重构；仅 stdlib `shlex` + 1 个类常量 + 1 个助手函数 + 1 条用例；无投机性抽象、无新依赖、无跨模块契约变更。
- **移交第二轮架构师的元审判题**: ① D2-6（零覆盖假阴性）是否正式登记为显式豁免（若登记，必须写明「`llms.txt` 条目在零覆盖态无任何门禁兜底」），否则本轮绿测将把漏检固化为契约；② 是否为 D2-1/D2-2 补一条「有可收录文档 + 无 `llms.txt`」用例（一条用例可同时让 test 1 承重并闭合无地图守卫盲区，且不触碰生产代码）；③ D2-3/D2-5 是否以「`isprintable()` + 长度上限」在本次补丁内顺手闭合（约 3 行，不影响任何现有断言）。
- **未闭合项登记（不阻断本次提交）**: D2-1、D2-2、D2-3、D2-4、D2-5、D2-7 为 P3；D2-6 为 P2（历史既有，待登记/排期）。
