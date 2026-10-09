# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

审查模式：DELTA_RE_LOOP（批次 D · BK-0030 / BK-0031 · Maintenance-Patch）
审查区间：d39f041d7f1cbf9664fc0ebc8b2585979d36a512..1a4e0c24647d5cc56c3f26141a6a3de03d384e2c
上轮阻断面：无 P0/P1（4×P2 + 6×P3）。本轮结论：**无 P0/P1；2×P2 + 5×P3**，其中 2×P2 均为本 diff 引入。

复现范式：全部实验在单条自包含命令内以 mktemp -d + git archive HEAD 隔离完成，收尾 rm -rf，工作树仅在实验后复验 git status --porcelain（仅剩预创建的未跟踪归档目录）。报告内不写入真实控制字节，全部以 U+XXXX / 反斜杠转义记法表示。

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **部分真根因修复 + 定点收口 + 1 项次生回归**。
  - R1-3② 触及了真不变量——「写出的身份必须能被自身的读者逐字反解」，并以 8,448 个码点的暴力比对验证了读回侧（splitlines + re.fullmatch）与真实读者语义**零不一致**；10 种 Unicode 行边界（U+000A/000D/000B/000C/001C/001D/001E/0085/2028/2029）与 3 种尾部变体端到端全部 rc=1 且**零残 file**。这是本轮唯一触及根因的修复。
  - 但该断言只覆盖了 round-trip 的**读出半程**，漏掉**写出半程**（UTF-8 可编码性）与**落盘时序**：str 在 Python 层可合法载荷孤立代理码位，splitlines 与 re 对其毫无感觉，直到 write 阶段才炸——这正是不变量未被 end-to-end 建模的证据（DR1-1）。
  - R1-5 / R1-6 / R1-8 为定点收口：正确关闭了被指控的具体输入类，但 R1-5 只改了生成器而未同步审计侧的同一语义，制造了跨组件解析分叉（DR1-2，次生回归）。
- **物理与业务一致性**: 契约的真实物理模型是四段闭环——
  name --f-string--> H1 文本 --encode(utf-8)--> 字节 --decode(utf-8)--> H1 文本 --splitlines()[0] + fullmatch--> name。
  新断言只验证了第 1 段与第 4 段，且在事务顺序上**不是**「任何文件被创建之前的唯一闸门」：落点不存在时 open('w') 先创建 0 字节文件，编码失败在创建之后才发生。实测后果与 R1-3② 指控完全同构（永久 fail-closed、仅 rm 可恢复），故「生成前断言」的完备性承诺**未被满足**。
  另需指出契约内部的语义分叉：审计侧 audit-doc-health.py:113 仍对首行做 strip，而其 docstring 自称「必须使用未净化原名…保证逐字同源」——本 diff 令生成器不再 strip 后，该不变量在两个消费者之间不再成立。
- **过度设计审计**: 无独立脚本层、无裁决语义解析器、无 .docignore 机制、无共享模块重构；re 与 os 均为既有导入；新增 85 行中生成器仅 31 行。唯一死代码是 「_can_roundtrip_as_identity」 中的 fullmatch 半边（DR1-4）：由 splitlines()==1 可推出 name 不含 LF，而点号在默认 flags 下除 LF 外匹配一切字符、捕获组按构造恒等于 name，故该断言**不可能改变任何判定结果**（变异 M7c 已证明：仅删除 regex 半程，全量 94 测试全绿）。属可删冗余，非过度封装；但它营造了「两道独立断言」的错觉。

**R1 修复核验与变异矩阵（独立复跑，非采信编排者自验）**

| 上轮 ID | 我独立复跑的判据 | 变异注入 | 结果 |
|:---|:---|:---|:---|
| R1-3② | 10×U+ 行边界 + 3×尾部变体 + 8,448 码点暴力比对 | M7 整段删除 / M7b 仅删 splitlines 半 / M7c 仅删 regex 半 | M7 红 5/5 子例；M7b 红 4/5（LF 子例被 regex 兜住）；M7c **全绿** ⇒ 载荷全在 splitlines 半边 |
| R1-1 | test_explicit_foreign_name_is_refused | M4 删除异名拒绝（return requested） | 红 ✅ 承重 |
| R1-2 | test_audit_reports_non_utf8_map | M5 恢复 errors="replace" | 红 ✅；并实测变异版 audit 实际打印「--name='A(U+FFFD)B'」，未变异版不下发任何 --name= ⇒ **「不得下发归一化名」这一关键判据确实承重**，非仅「报出缺陷」 |
| R1-4 | 拆分后两例是否真跑、有无新跳过面 | 非特权环境全量复跑 | 8/8 全跑、0 skip；全量 63+31=94 通过、0 skipped；跳过面收敛为 unreadable 例的特权分支，非 UTF-8 断言已独立 ✅ |
| R1-5 | 尾随空白 H1 的沿用/拒绝语义 | M10 生成器退回 strip | 生成器行为符合声称；但**M10 全量 94 全绿** ⇒ 零回归保护，且 audit↔generator 分叉完全不被套件感知 |
| R1-6 | 目录/FIFO//dev/urandom/软链各落点 | M9 删除非规则文件闸门 | 闸门行为正确；但 **M9 全量 94 全绿** ⇒ 零回归保护 |
| R1-8 | 空名端到端稳定性 + audit 一致性 | M8 退回 requested or DEFAULT_PROJECT_NAME | 空名 rc=0、H1 为「#」+两空格+「Machine-Readable…」、裸重生成逐字节稳定、audit 判定一致 ⇒ 不卡死、可反解；M8 红 ✅ 承重 |

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

> 未激活（非客户端/SSR 改动）

- **Rules of Hooks 合规性**: 不适用（本 diff 仅 Python CLI + 文件系统写保护闸门，无 TSX/JSX/Vue/Svelte、无 react/next 导入）。
- **SSR 水合与 Storage 防御**: 不适用（无客户端渲染、无 localStorage/sessionStorage/window 访问）。
- **渲染纯度与全局可变状态**: 不适用（无组件渲染路径；模块级常量 DEFAULT_PROJECT_NAME 为只读字符串）。

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

- **攻击路径 1: 非法 UTF-8 项目名 → 0 字节残 file → 地图永久 fail-closed（DR1-1）**
  - **触发条件**: --name 携带原始非 UTF-8 字节（shell 写作 --name 后接 $ 转义的单字节 0xFF 或 0xFE；或外部脚本按字节文件名派生 --name；CI 变量来自非法编码来源）。
  - **复现推演**: argv 经 os.fsdecode(surrogateescape) 得到含孤立代理码位（U+DCFF）的 name → 「_can_roundtrip_as_identity」里 splitlines() 与 re.fullmatch 对代理码位完全无感 ⇒ 返回 True → out_path 不存在 ⇒ 直接返回该 name（:193）→ generate_llms_txt 先 mkdir 再 output_file.write_text(...)（:154-155）→ Path.write_text 内部先 open('w') **创建/截断文件**，随后 f.write 编码失败 → 未捕获 UnicodeEncodeError（traceback、rc=1）→ 磁盘上留下 **0 字节 llms.txt** → 此后任何调用（含 --name=Clean Name）在 :201 读出空串、其 splitlines()[0] 抛 IndexError，被 :202 吞入 fail-closed 分支 ⇒ 永久拒绝，仅 rm 可恢复。
  - **影响结果**: SSOT 路径残留可被提交的 0 字节地图；生成器对该路径永久不可用；traceback 污染 CI 日志（违反「生成前即拒绝、不留残 file」的本轮承诺）。
  - **数据安全边界（已实测，用于定级）**: 既有地图 + 代理名时，写前即被异名闸门拒绝，字节不变（349B 完整）⇒ **无既有数据损坏**，故定 P2 而非 P1。
  - **与已登记待办 R1-7 的区别（防止误归待办）**: 实测「既有只读地图」走 open('w') 失败路径时 rc=1 有 traceback 但**无残 file、无楔死**（chmod 复原后立即 rc=0，349 字节不变）；本项是「落点不存在 → 先创建 → 后失败」，产出残 file 并锁死整条路径，属 R1-3② 的同缺陷类，不可并入 R1-7 待办。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:163-173, 184-190, 154-155, 200-207

- **攻击路径 2: 行尾空白 H1 → 审计下发必然失败的修复命令 → 修复死循环（DR1-2）**
  - **触发条件**: 既有地图首行形如「# Foo Machine-Readable Knowledge Base Map」加一个尾随空格或 TAB，或行首带一个缩进空格（历史文件、编辑器自动加尾随空白、人工编辑）。
  - **复现推演**: 生成器（不 strip）→ fullmatch 失败 → rc=1 干净拒绝；同一文件交给审计 → audit-doc-health.py:113 仍 strip → 反解出可信名 Foo → 重生成字节必不一致 → 「_is_safely_displayable("Foo")」为真 → :156-159 打印「请以 --name=Foo 运行 generate-llms-txt.py --root docs --output docs/llms.txt」→ 用户照做 → 生成器仍 rc=1（字节不变）→ 回到审计…用户被永久锁在该环内。
  - **归因证明（预 diff 对照）**: 对 d39f041 同一输入、同一命令，生成器 rc=0 且把尾随空格静默归一化掉（审计当时无需给建议）；本 diff 之后变为 rc=1 拒绝 + 审计仍下发命令 ⇒ **建议由「可执行」退化为「必然失败」，是本 diff 引入的次生回归**，而非历史既有。
  - **影响结果**: 修复指引不可执行（与 R1-10 同类但为新增实例）；审计自身「逐字同源」docstring 失效；地图漂移永久滞留。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:209-218 ↔ skills/doc-governance/scripts/audit-doc-health.py:107-116, 147-159

- **攻击路径 3: 行尾 U+000C / U+000B / U+0085 / U+2028 / U+2029 → 仍静默归一化（DR1-3）**
  - **触发条件**: 首行身份后紧跟 VT/FF/NEL/LS/PS 再换行（跨平台编辑器、富文本粘贴、旧版生成物）。
  - **复现推演**: read_text().splitlines()[0] 在该字符处**先行切割** → 不 strip 的 fullmatch 反而成功 → existing="Foo"，rc=0 重写文件 → 行尾分隔符被静默丢弃（实测 FF 变体 rc=0 且字节被改写）。
  - **影响结果**: 与 R1-5 自述策略（行边界空白属身份字节，应拒绝而非归一化）不一致；无破坏性后果（审计对该输入报漂移，其 --name=Foo 建议恰好可执行，不构成死胡同）。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:201, 210

- **攻击路径 4: 自指符号链接 → Path.resolve() 抛未捕获 RuntimeError（DR1-5）**
  - **触发条件**: docs/llms.txt 为自引用软链（ln -s llms.txt llms.txt）。
  - **复现推演**: main():240 处 Path(args.output).resolve() 在 Python 3.12 对软链环抛 RuntimeError（Symlink loop，3.13+ 才归为 OSError）→ 未捕获 → 直接 traceback；R1-6 的新闸门位于 :195，排在 :240 与 :192 之后，**永无机会给出承诺中的干净拒绝**。
  - **影响结果**: 裸 traceback 而非「非规则文件一律拒绝」；无残 file、无楔死（P3）。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:240, 192-198

- **攻击路径 5: 0 字节/半写地图 → 生成器与审计双楔死（DR1-7）**
  - **触发条件**: 任何中断（磁盘满、配额、进程被杀、编辑器崩溃、truncate -s0、空 LFS 指针）留下 0 字节 llms.txt。
  - **复现推演**: 实测生成器 rc=1（IndexError fail-closed）；审计 rc=1 且**不下发任何 --name 命令**（无法反解）⇒ 修复指导完全缺失，用户只能自行推断 rm；根因是 fail-closed 判定键为「文件存在」而非「身份可反解」，而落盘非原子（write_text 直写目标）⇒ 任何中断都必然产出楔死态。
  - **影响结果**: 双工具同时失去自愈能力（P3，架构建议：tmp + os.replace 原子写，可同时消灭 DR1-1 的残 file 面）。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:154-155, 192-207

- **次生缺陷扫描结论（对应编排者 (d) 项）**: 「_can_roundtrip_as_identity」前置、沿用路径后置的组合**未**产生新的死胡同——沿用路径回填的 existing 由 fullmatch 从首行切出，回写字符串与首行逐字相同，故不可能绕过 round-trip 校验；测试空转面方面，「assertIn("机器地图")」属宽泛前置断言但非空转（审计若完全静默仍会打红），真正承重的是 rc 与 --name= 两条；test_empty_explicit_name_is_not_silently_replaced 为 if/else 双分支结构（两种结局都放行），形状偏弱，但对 M8 这一具体回归仍能打红。

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| DR1-1 | P2 | 是 | skills/doc-governance/scripts/generate-llms-txt.py:163-173, 184-190, 154-155 | round-trip 断言漏掉 UTF-8 可编码性与落盘时序：非法 UTF-8 字节名通过校验后在 write 阶段炸出未捕获 UnicodeEncodeError，先创建后失败，残留 0 字节 llms.txt，此后仅 rm 可恢复（R1-3② 同缺陷类残留洞） | argv 单字节 0xFF → surrogateescape 得孤立代理 U+DCFF → splitlines/re 无感放行 → open('w') 建 0 字节文件 → encode 失败 → 后续 read 空串 → splitlines()[0] IndexError → 永久 fail-closed |
| DR1-2 | P2 | 是 | skills/doc-governance/scripts/generate-llms-txt.py:209-218 ↔ skills/doc-governance/scripts/audit-doc-health.py:113 | 生成器不 strip 而审计仍 strip，同一 H1 两侧解析语义分叉：审计反解出名字并下发 --name 修复命令，生成器却对该首行必然拒绝，用户陷入不可执行的修复死循环（预 diff 该命令可执行，属本 diff 次生回归） | 首行尾随空格/TAB 或行首缩进 → 审计 strip 放行并打印 --name=Foo → 生成器 fullmatch 失败 rc=1 → 无状态改变、循环不收敛 |
| DR1-3 | P3 | 是 | skills/doc-governance/scripts/generate-llms-txt.py:201, 210 | R1-5 的「行边界空白属身份字节」策略只对 splitlines 不切割的空白生效；行尾 VT/FF/NEL/LS/PS 仍被 splitlines 先行切割并静默归一化（rc=0，字节被改写），与自述策略不一致 | read_text().splitlines()[0] 在 U+000C 等处分行，fullmatch 反而成功，重写时丢弃该字符 |
| DR1-4 | P3 | 是 | skills/doc-governance/scripts/generate-llms-txt.py:172-173 | 新断言中 fullmatch + 捕获组比较为死代码：splitlines()==1 已推出无 LF，而点号在默认 flags 下除 LF 外匹配一切，捕获组按构造恒等于 name，该半边不可能改变判定结果（M7c 全绿佐证）；营造两道独立断言的错觉 | 无攻击面；维护者若日后改写 regex 将误以为删掉该行会削弱防线，实际载荷全在 splitlines 半边 |
| DR1-5 | P3 | 历史既有（R1-6 新闸门未覆盖） | skills/doc-governance/scripts/generate-llms-txt.py:240, 192-198 | 自指软链使 Path.resolve() 抛未捕获 RuntimeError（Python 3.12），未走新闸门的干净拒绝，违背 R1-6「落点非规则文件一律拒绝」的完备性声明 | ln -s llms.txt llms.txt → resolve 抛软链环异常 → traceback rc=1（无残 file、无楔死） |
| DR1-6 | P3 | 是 | skills/doc-governance/tests/test_doc_governance_scripts.py:1349-1402 | R1-5 与 R1-6 零回归保护：删除非规则文件闸门（M9）、把 no-strip 退回 strip（M10）后全量 94 测试仍全绿；行分隔符用例只覆盖 10 种边界中的 5 种且无尾部变体，未来若把 splitlines 换成按换行符 split 将静默漏测（U+000C/001C-001E/2029 无保护） | 修复可被无声回滚，回归不可机械检出 |
| DR1-7 | P3 | 历史既有（已声明待办 R1-7/R1-9/R1-10） | skills/doc-governance/scripts/generate-llms-txt.py:154-155, 192-207 | 落盘非原子（write_text 直写目标）叠加「文件存在即须反解成功」的 fail-closed 判定，使任何中断留下的 0 字节/半写地图同时楔死生成器与审计（审计亦不下发任何命令），仅 rm 可解 | 中断 → 0 字节地图 → 生成器 IndexError fail-closed + 审计不可反解不再给指引 |

补充说明（范围边界合规）：R1-7（只读地图未捕获 traceback）、R1-9（三处缺省并存与库入口 generate_llms_txt 无写保护）、R1-10（审计不可反解态建议不可执行）本轮确未修改，已由编排者登记待办，本报告不将其计入阻断面；上表 P3 仅记录与本 diff 有因果或未覆盖关系的部分。历史既有项一律未定 P0/P1。

## 5. 第一轮结论概要

无 P0/P1 阻断项，但「R1-3② 已根治」的结论**只在声明范围内成立**，不成立 end-to-end：

1. **已根治/已承重（可采信）**：R1-3② 的行分隔符面（10/10 Unicode 边界 + 尾部变体端到端拒绝、零残 file、8,448 码点读回侧零不一致）；R1-1（M4 红）；R1-2（M5 红，且关键判据「不得下发归一化名」确为承重断言）；R1-4（拆分隔离正确，非特权环境 8/8 全跑、全量 94 passed / 0 skipped）；R1-8（M8 红，空名可反解、不卡死、语义与契约一致）。
2. **未闭合（必须处置）**：DR1-1（P2，同一不变量上的残留洞：断言漏掉 encode 半程与「创建先于失败」的时序，后果与 R1-3② 完全同构）；DR1-2（P2，本 diff 次生回归：生成器与审计对同一 H1 的解析语义分叉，审计下发必然失败的命令）。
3. **建议的最小修复（不扩大任何写入面）**：
   - 在「_can_roundtrip_as_identity」内增补名字 UTF-8 可编码性断言（或统一改走 tmp + os.replace 原子写），使闸门成为落盘前唯一且闭环的门；
   - 让 audit-doc-health.py 的「_resolve_project_name」复用与生成器**同一套**反解语义（不 strip），反解失败即走既有 fail-closed 文案，消灭 DR1-2/DR1-3 的分叉；
   - 补 3 条测试消 DR1-6：FIFO/目录落点拒绝、软链→常规文件放行、行尾空白 H1 的 audit↔generator 一致性；并把行分隔符用例扩到 U+000C/001C-001E/2029 与尾部变体；
   - 删除或改为复用读者反解函数的死断言（DR1-4）。
4. **移交第二轮（R2）元对抗审判的两个裁决点**：
   - DR1-1 是否升级为阻断项——判据是「生成前断言 name 可从首行反解」这一承诺是否要求覆盖写出半程与残 file 时序；本报告按上轮对同类后果的 P2 定级口径维持 P2，但明确认定「根治」承诺未达成；
   - DR1-2 与已登记 R1-10 的定级一致性——两者同为「审计给出不可执行建议」，但 DR1-2 是把原本可执行的建议改坏（主动回归）且触发面更宽，故本报告定 P2 而非 P3。
