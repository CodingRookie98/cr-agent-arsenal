# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

审查模式：DELTA_RE_LOOP · LIGHT_REVIEW（批次 D · BK-0030 / BK-0031 · Maintenance-Patch）
审查区间：1a4e0c24647d5cc56c3f26141a6a3de03d384e2c..3e55cad06541e25fdb59b1e0cb52d16e1080d553
上轮阻断面：无 P0/P1（2×P2 + 5×P3）。本轮结论：**仍无 P0/P1；3×P2 + 5×P3**，其中 2×P3 由本 diff 引入，1×P2 为 DR1-2 未闭合的半面。

复现范式：全部实验在单条自包含命令内以 mktemp -d + git archive HEAD 隔离副本完成，对可能阻塞的调用（FIFO / 字符设备）施加显式超时与 RLIMIT_AS，收尾清理。报告正文不含真实控制字节，全部以 U+XXXX / 0xXX 记法表示。收尾复验：git status --porcelain 仅含预创建的未跟踪归档目录；工作树内全部 __pycache__ 产物 mtime ≤ 17:09:56，早于本会话起始（17:10:32），即本次审查未向工作树写入任何字节。

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **真根因修复（DR1-1） + 语义对齐收口（DR1-2 的机器可检测半边） + 回归网补强但半边空转（DR1-6）**。
  - DR1-1 触到了不变量本体。生成前闸门的真实语义应为「name 必须能被写出为字节，且写出的 H1 必须能被读者逐字反解」。本 diff 补上 `name.encode("utf-8")` 这一**写出半程**，使闸门第一次成为**落盘前唯一且闭环的门**——实测 9 种原始非法字节载荷（孤立 0xFF / 0x80 / 0xFE、混合合法非法字节、截断多字节序列、WTF-8 编码代理）全部 rc=1、**零残 file、零 traceback**，既有地图场景下 356 字节逐字节不变。这是本区间唯一真正闭合的修复。
  - 我不满足于「9 条载荷通过」，而是对**全码点空间**做了等价性证明：闸门判定与「真实写盘 → 真实读回 → fullmatch」在 0x0..0x10FFFF 全域**逐点等价**，既无漏放（guard=True 而 round-trip 破损 = 0 例），也无过拒（guard=False 而 round-trip 成立 = 0 例，代理区除外）。DR1-4 删除死断言后，函数只剩两条**都承重**的分支（M11 杀 encode 半程、M13 杀 splitlines 半程，各自单点打红）。
  - DR1-2 的修复方向正确（审计与生成器共用同一反解语义），但**只闭合了机器可检测的半边**：审计不再下发 `--name=` token，而它的 fail-closed 文案仍规定了一条生成器**必然拒绝**的操作（§3 攻击路径 2）。即把一个不可执行命令换成了另一个不可执行指引，并与 GOVERNANCE §4.1:125 契约漂移。
  - DR1-6 的三条新用例中，FIFO 用例**确实承重且写法正确**（M9 单点打红、27.4s 含 15s 超时燃烧、-x 下同样是首个且唯一失败）；但 DR1-2 的守卫用例在其唯一输入上**必然走空转早退分支**，可执行性断言从未执行（变异 MV 反证）。
- **物理与业务一致性**: 契约的四段闭环是 name → H1 文本 → encode(utf-8) → 字节 → decode(utf-8) → H1 文本 → splitlines()[0] + fullmatch → name。本 diff 之后，**身份通道**上这四段第一次全部被同一个前置闸门覆盖，且我以 2,228,224 例逻辑遍历 + 578,780 例真实文件 I/O 证明闸门与该闭环**等价**。但闭环的**兄弟通道**（正文条目的相对链接 rel_link 由文件名派生）未被同一闸门保护：docs 下出现非法 UTF-8 字节文件名的 .md 时，`write_text` 依旧先 open('w') 建 0 字节地图、后 UnicodeEncodeError，落盘后生成器与审计**同时**楔死（§3 攻击路径 5）。故「生成前即被拒且零残留」这一承诺**严格只在身份通道成立**，在内容通道不成立——根因（非原子落盘 + 先创建后失败）仍未被触及，与已登记的 DR1-7 待办同源，其触发条件比我上轮的认识更弱：**无需任何中断即可确定性触发**。
- **过度设计审计**: 无独立脚本层、无裁决语义解析器、无 .docignore 机制、无共享模块重构、无新增依赖。re / os 均为既有导入（生成器内 re 仍有 4 处调用，无悬挂 import）。净增 92 行中测试占 83 行，生产代码仅 +3/-6 行。**唯一死代码（DR1-4 的 fullmatch 死断言）已按要求删除，删除后无新增不可达分支**。DR1-3 / DR1-5 / DR1-7 确未被本次改动扩大（我独立复现：6 种行尾边界字符仍 rc=0 静默改写；自指软链仍 RuntimeError 裸 traceback），与「登记待办」口径一致，不计入阻断面。
- **奥卡姆剃刀**: 是否还有更精简的等价解法？有——把闸门与读者反解合并为**同一个** `_parse_identity(head_line) -> Optional[str]` 并由「写前断言 parse(f"# {name} …") == name」驱动，可同时消灭 DR1-4 的构造性冗余与跨组件分叉风险。但本 diff 的两处改动已是「零新增抽象」的最小形态，**不构成过度设计**，故仅作为架构建议提出，不定级。

**复核矩阵（(a)–(e) 逐项，全部独立复跑，不采信编排者自验）**

| 命题 | 我的独立判据 | 实测结果 | 裁决 |
|:---|:---|:---|:---|
| (a) DR1-1 根治 | argv 原始 0xFF 等 9 种载荷 ×（无既有地图 / 有既有地图） | 全部 rc=1、地图文件不存在、目录内零残 file、stderr 无 traceback；既有地图 356B 逐字节不变 | **已根治（身份通道）** |
| (a′) 闸门完备性 | 全码点 2,228,224 例逻辑等价 + 578,780 例真实文件 I/O 校验模型 + 1,600 例双读者一致性 | 漏放 0 例、过拒 0 例、模型↔真实读者分歧 0 例、audit↔generator 分歧 0 例 | **精确等价，可采信** |
| (b) DR1-2 根治 | 行首缩进 / 行尾 SP / TAB / U+00A0 / BOM / ZWSP 六变体闭环 | 生成器全部 rc=1 且字节不变；审计全部报漂移且**不下发任何 `--name=`**；token 可执行性判据恒真（无 token 可判） | **token 面已根治；prose 面未根治（R1-2）** |
| (c) M9–M12 承重 | 逐条注入变异 + 全量 99 用例 + -x 对照 + 非特权环境 | M9/M10/M11/M12 **各 1 failed / 98 passed** 且各杀中预期用例；M9 耗时 27.4s（15s 超时燃烧）证实 `TimeoutExpired` 而非挂起；-x 下同样为首个失败（63 passed 后停止） | **四条全部承重** |
| (d) 次生缺陷 | 全码点暴力比对 + 合法地图退化路径 + GOVERNANCE §4.1 契约 | 通过 round-trip 但写入后不可反解：**0 例**；行尾空白合法地图由「沿用」退化为「拒绝」，该退化**可由 §4.1:125-126 解释** | **无次生破坏；契约可解释** |
| (e) YAGNI | 死代码 / 新抽象 / 新依赖 / 共享模块扫描 | 无新抽象、无新依赖、无共享模块；DR1-4 死断言已删且无残留不可达分支 | **合规** |

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

> 未激活（非客户端/SSR 改动）

- **Rules of Hooks 合规性**: 不适用（本 diff 仅 Python CLI：`audit-doc-health.py` 一处正则语义调整、`generate-llms-txt.py` 一处前置断言扩写、测试文件追加 5 个用例；无 TSX/JSX/Vue/Svelte，无 react/next 导入）。
- **SSR 水合与 Storage 防御**: 不适用（无客户端渲染、无 localStorage/sessionStorage/window 访问、无浏览器 API）。
- **渲染纯度与全局可变状态**: 不适用（无组件渲染路径；本 diff 未新增模块级可变状态，`DEFAULT_PROJECT_NAME` 为只读字符串）。

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

- **攻击路径 1: argv 非法字节项目名 → 0 字节残 file（上轮 DR1-1）—— 已闸死，复核通过**
  - **触发条件**: `--name` 携带原始非 UTF-8 字节（shell 单字节 0xFF/0x80/0xFE；CI 变量来自非法编码来源；外部脚本按字节文件名派生）。
  - **复现推演**: argv 经 os.fsdecode(surrogateescape) 得孤立代理 U+DCFF → `_can_roundtrip_as_identity` 首发 `name.encode("utf-8")` 抛 UnicodeEncodeError → 返回 False → `_resolve_outgoing_name` 在 `out_path.exists()` **之前** `sys.exit(1)` → 从未进入 `generate_llms_txt` → 从未 mkdir、从未 open('w')。
  - **影响结果**: rc=1、地图文件不存在、零残 file、stderr 为单行受控文案（无 traceback）。既有地图场景字节逐字节不变。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:169-172, 186-192
  - **残留（R1-1，P3）**: 拒因文案仍写「项目名含行分隔符…请改用不含换行/分隔符的项目名」——0xFF 名**不含任何行分隔符**，真实拒因是不可编码，该处方对本次新增的拒因无效，会误导 CI 排查。

- **攻击路径 2: fail-closed 文案开出必然失败的处方 → 修复指引不可执行（DR1-2 残留半面）**
  - **触发条件**: 既有 `docs/llms.txt` 首行含行边界空白（尾随 SP / TAB / U+00A0、行首缩进、BOM、ZWSP）且正文漂移。
  - **复现推演**: 生成器 fullmatch 失败 → rc=1（正确，字节不变）。审计侧 `_resolve_project_name` 同样 fullmatch 失败 → name_resolved=False → 字节比对不一致 → 打印「机器地图与生成物不一致，且既有地图首行不符合标准 H1 格式…请先人工确认正确的项目名，再以显式 `--name` 重新生成后再提交」。操作者照做 `--name=Foo` → 生成器在 :212 的 H1 格式闸门**再次 rc=1**（落点存在且 H1 畸形时，任何 `--name` 都必然被拒，因为 requested 分支在 exists 分支之前只做可编码性检查）→ 状态零变化；裸重生成同样 rc=1。唯一有效通道（先删除既有地图）**只出现在生成器 stderr**，审计处方中缺失。
  - **影响结果**: 审计处方在本分支**不可执行**；其前置论断「缺省项目名会把地图身份静默改写」在该分支**已不成立**（裸重生成同样被拒，实测 rc=1）；与 GOVERNANCE §4.1:125「确需改名须先人工移除既有地图文件」的契约口径漂移。因下一步生成器 stderr 即给出 rm 指引，可自愈，故非阻断。
  - **与上轮的差异（防误判为「已修好」）**: 上轮 DR1-2 形态是审计下发 `--name=Foo` token；本 diff 后 token 不再出现（**机器可检测的半边确实根治**），但同一输入类仍被路由到一个同样不可执行的 prose 处方——缺陷被改名而非消灭。
  - **涉及代码**: skills/doc-governance/scripts/audit-doc-health.py:141-147 ↔ skills/doc-governance/scripts/generate-llms-txt.py:186-212 ↔ docs/GOVERNANCE.md:125

- **攻击路径 3: 新回归用例在其唯一输入上空转 → DR1-2 的守卫实为零断言**
  - **触发条件**: 运行 `TestBatchDIdentityContract::test_audit_suggestion_is_executable_by_generator`（HEAD 状态，零变异）。
  - **复现推演**: 用例唯一输入是「首行尾随两空格」的地图 → 修复后该输入必然走 fail-closed 分支、审计不下发 token → `next(...)` 返回 None → `if line is None: return` **提前返回**，可执行性断言（assertEqual(gen.returncode, 0)）从未执行。变异 MV（把该 return 换成 raise）**单点打红**，反证 HEAD 下该分支必然被走到 ⇒ 本用例对 DR1-2 契约零保护。
  - **次生缺陷（同一用例）**: 即便走到断言，其 token 抽取器以 `segment.find(" 运行")` 定位命令末尾，对合法名 `A 运行 B` 会把 token 截断为 `'A` 并误判失败。实测：审计真实建议 `--name='A 运行 B'` 完全可执行（引号正确），抽取器却让生成器 rc=1 ⇒ 该用例同时具备「空转」与「假阳性」双重缺陷。
  - **影响结果**: DR1-6 声称补上的 DR1-2 回归保护实际不存在；若日后把 whitespace 类重新路由回 token 分支，套件不会报警。
  - **涉及代码**: skills/doc-governance/tests/test_doc_governance_scripts.py:1457-1468

- **攻击路径 4: 非规则文件落在读路径 → 审计永久挂死（生成器已闸、审计未闸）**
  - **触发条件**: `<docs>/llms.txt` 为 FIFO（`mkfifo docs/llms.txt`）或指向字符设备的软链（`ln -s /dev/zero docs/llms.txt`）。
  - **复现推演**: 生成器侧已被 R1-6 闸门覆盖，同输入 0.05s 干净拒绝（rc=1）。审计侧无任何非规则文件闸门：`llms_file.exists()` 为真 → `_resolve_project_name` 在 :108 直接 `read_text()` → FIFO 的 open(O_RDONLY) **无写者则永久阻塞**（实测 8.01s 无任何输出、无退出）；字符设备形态下为无界读取直至 MemoryError，且该异常在 :108 抛出，**不在 :109 的 (OSError, IndexError, UnicodeDecodeError) 元组内**，裸 traceback 退出。
  - **影响结果**: CI / 本地审计永久挂起（无超时、无诊断）；设备形态下为无界内存增长 + 裸 traceback。同一威胁模型（「不得进入无界读取面」）在写路径已加固、在读路径未加固，加固不对称。
  - **定级说明**: 该读路径行位于本次变更行（:114）**上游 6 行**，落在允许的紧邻窗口内；缺陷本体为历史既有，按范围锁强制封顶 P2，**不阻断**，建议登记待办——与 DR1-6 同一根因，宜复用同一 `is_file()` 闸门。
  - **涉及代码**: skills/doc-governance/scripts/audit-doc-health.py:108-109, 128, 138 ↔ skills/doc-governance/scripts/generate-llms-txt.py:197-200

- **攻击路径 5: 内容通道的确定性 0 字节残 file → 双工具楔死（与 DR1-1 同构，未被本次闸门覆盖）**
  - **触发条件**: `<docs 根>` 下存在文件名含非法 UTF-8 字节的 .md（从其他文件系统拷入、git checkout 到历史坏名、程序生成）。**无需任何中断、无需任何并发**。
  - **复现推演**: `--name` 干净 → 身份闸门通过 → `rel_link = f.relative_to(root_dir).as_posix()` 保留 surrogateescape 代理 → output_lines 含代理 → `output_file.write_text(content, encoding="utf-8")` **先 open('w') 建 0 字节文件**、后编码失败抛 UnicodeEncodeError（rc=1、裸 traceback）→ 磁盘留下 0 字节 llms.txt → 此后生成器读空串、`splitlines()[0]` IndexError 被 :204 吞入 fail-closed ⇒ 永久拒绝（实测 rc=1「既有地图无法安全读取（IndexError…）」）；审计侧同样不可反解，且因 missing_meta_files 样例名含代理，在 :678 打印时再次 UnicodeEncodeError **裸 traceback 中断整份体检报告**（机器地图缺陷项根本没输出）⇒ **双工具同时失去自愈能力，仅 rm 可解**。
  - **影响结果**: SSOT 路径残留可被提交的 0 字节地图；生成器对该路径永久不可用；审计整份报告崩溃。
  - **定级说明**: 内容通道不属本次身份契约的变更范围（历史既有），按范围锁强制封顶 P2，**不阻断**。但它是已登记 DR1-7（落盘非原子）**最有价值的新证据**：原登记描述依赖「中断」前提，实测证明存在**无中断的确定性触发**，建议上调其处置优先级（tmp + os.replace 原子写可同时消灭本项与 DR1-1 的残 file 面）。
  - **涉及代码**: skills/doc-governance/scripts/generate-llms-txt.py:114, 153-155, 202-209 ↔ skills/doc-governance/scripts/audit-doc-health.py:108, 678

- **次生破坏与回归审计结论（对应 (d)）**:
  - **「通过 round-trip 但写入后不可反解」的名字：0 例。** 全码点逻辑遍历 2,228,224 例（两种名字形态）零漏放；其中 578,780 例走真实文件 I/O，与模型零分歧，证明模型可信、结论可外推全域。
  - **过拒面：仅 11 类行边界字符 + 代理区。** 除 U+000A / U+000D / U+000B / U+000C / U+001C / U+001D / U+001E / U+0085 / U+2028 / U+2029 与代理码位外，闸门**不误伤任何合法名字**（U+00A0 等非边界空白可正常写入 H1 并被逐字反解）。
  - **合法地图退化是否可解释：可解释。** 行尾空白 H1 在本 diff 后既不被生成器沿用、也不被审计反解，由「静默归一化」退化为「干净拒绝 + 需人工删除」。该退化正落在 GOVERNANCE §4.1:126「首行不符合标准 H1 格式时一律拒绝覆盖（不得归一化或回落占位名后静默改写）」与 §4.1:125「确需改名须先人工移除既有地图文件」的登记口径内，**非契约外行为**；生成器 stderr 亦给出「请先删除该文件再生成」。可采信。
  - **双读者一致性：1,600 例（20 个风险字符两两组合 × 4 种名字形态）零分歧。** 审计 :114 与生成器 :212 现在逐字同源，R1-3 的贪婪捕获语义亦一致。

- **测试保真度审计（对应 (c)）**:
  - 四条变异**全部承重**且各只杀中预期用例（1 failed / 98 passed），无连带误伤——回归网定位精确，编排者自验可信。
  - M9 的 FIFO 用例写法正确：timeout=15 使闸门被删时以 `TimeoutExpired` → `self.fail` 打红而非静默挂起；非特权环境（uid 非 0）下 mkfifo 无需特权，实测阻塞 >8s 被超时捕获。**-x 与否不改变裁决**（-x 下同样 1 failed、63 passed 后停止），只改变总耗时。
  - 但 FIFO 用例的**目录半边不承重**：M9 下目录落点仍因 IsADirectoryError 被 :204 的通用 OSError 元组兜住，rc=1 照常成立（实测 0.06s）。即「目录必须拒绝」这一断言在闸门被删时依然绿，真正承重的只有 FIFO 半边。
  - 自主补充变异 M13（删 splitlines 半程）与 M15（审计忽略 name_resolved）均单点打红（M15 连带 4 例，含两条 BatchC 用例），说明闸门两半与 R1-1 保护各有独立承重网。M14（整段删除守卫）与 M11+M13 的并集等价，不另行计数。

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | P3 (Suggestion) | 是 | skills/doc-governance/scripts/generate-llms-txt.py:186-192 | 新增的「不可编码」拒因复用了「含行分隔符」的旧文案，处方（改用不含换行/分隔符的名字）对该拒因无效 | 0xFF/孤立代理等载荷不含任何行分隔符，操作者按文案排查方向错误；无功能后果，仅误导 CI 定位 |
| R1-2 | P2 | 部分（文案历史既有；本 diff 把行边界空白类新增路由进该分支） | skills/doc-governance/scripts/audit-doc-health.py:141-147 ↔ generate-llms-txt.py:186-212 ↔ docs/GOVERNANCE.md:125 | fail-closed 分支给出的处方「以显式 --name 重新生成」在既有 H1 畸形时**必然被生成器拒绝**，且前置论断「缺省项目名会静默改写」在该分支已不成立；与 §4.1:125 契约口径漂移 | 尾随空白/缩进/BOM 的 H1 → 审计不下发 token 但下发不可执行 prose → 用户按处方 rc=1、状态零变化；唯一有效通道（先 rm）仅在生成器 stderr 出现。可自愈，非阻断 |
| R1-3 | P3 (Suggestion) | 是 | skills/doc-governance/tests/test_doc_governance_scripts.py:1457-1468 | DR1-2 的守卫用例在其唯一输入上必然空转（可执行性断言从不执行，变异 MV 反证）；且 token 抽取器用 find(" 运行") 截断，对合法名 A 运行 B 误判失败 | 对 DR1-2 零回归保护；若日后重新引入 token 分支，套件不报警；对含「 运行」的合法名产生假阳性红 |
| R1-4 | P2 | 历史既有（位于变更行上游 6 行的紧邻窗口） | skills/doc-governance/scripts/audit-doc-health.py:108-109, 128, 138 | 审计读路径缺少非规则文件闸门：FIFO 落点使审计永久挂死；字符设备软链触发无界读取并以未被捕获的异常裸 traceback 退出 | mkfifo docs/llms.txt → read_text 的 open(O_RDONLY) 无写者则永久阻塞（实测 >8s 无输出无退出）；生成器同输入 0.05s 干净拒绝 ⇒ 「无界读取面」加固不对称 |
| R1-5 | P2 | 历史既有（与已登记 DR1-7 同源，本次未修） | skills/doc-governance/scripts/generate-llms-txt.py:114, 153-155, 202-209 ↔ audit-doc-health.py:108, 678 | 内容通道（非法 UTF-8 字节的 .md 文件名）在**无中断**前提下确定性留下 0 字节地图，随后生成器永久 fail-closed、审计整份报告裸 traceback 中断，双双失去自愈能力 | rel_link 携带 surrogateescape 代理 → write_text 先 open('w') 建 0 字节文件后编码失败 → 后续 read 空串 splitlines()[0] IndexError ⇒ 楔死；审计打印样例名时再次 UnicodeEncodeError |
| R1-6 | P3 (Suggestion) | 历史既有（本次声明登记待办） | skills/doc-governance/scripts/generate-llms-txt.py:203, 212 | DR1-3 未修：行尾 VT(U+000B) / FF(U+000C) / NEL(U+0085) / LS(U+2028) / PS(U+2029) / FS(U+001C) 仍被 splitlines 先行切割并静默归一化 | read_text().splitlines()[0] 在该字符处先行分行 → fullmatch 反而成功 → rc=0 重写、该字符被静默丢弃（实测 6/6 变体 rc=0 且字节被改写） |
| R1-7 | P3 (Suggestion) | 历史既有（本次声明登记待办） | skills/doc-governance/scripts/generate-llms-txt.py:242 | DR1-5 未修：自指软链使 Path.resolve() 抛未捕获 RuntimeError（Python 3.12），未走「非规则文件一律拒绝」的干净通道 | ln -s self.txt self.txt → resolve 抛 Symlink loop → 裸 traceback rc=1（无残 file、无楔死） |
| R1-8 | P3 (Suggestion) | 是 | skills/doc-governance/tests/test_doc_governance_scripts.py:1415-1433 | 新增 FIFO 用例的目录半边不承重：闸门被删（M9）时目录仍被通用 OSError 兜住 rc=1，「目录必须拒绝」断言恒绿 | 只有 FIFO 半边真正承重；目录断言给出虚假的覆盖面感，掩盖闸门缺失 |

补充说明（范围边界合规）：R1-4 / R1-5 / R1-6 / R1-7 均标记为历史既有或已登记待办，按 Diff 范围锁**强制封顶 P2/P3、一律不阻断当前提交**；上表不含任何由本次改动直接引入的 P0/P1。DR1-3 / DR1-5 / DR1-7 确未被本次改动扩大或破坏，与编排者的待办登记口径一致。

## 5. 第一轮结论概要

**终审建议：无 P0/P1 阻断项，可移交第二轮（R2）元对抗审判；本轮 3×P2 + 5×P3，其中 2×P3（R1-1 / R1-3）由本 diff 引入。**

1. **已根治 / 已承重（可采信，均经独立复跑与变异验证）**
   - DR1-1 在**身份通道**上完成了真根因修复：闸门前置到 out_path.exists() 之前，先做 UTF-8 可编码性、再做 H1 单行性；9 种原始非法字节载荷端到端 rc=1、零残 file、零 traceback，既有地图字节不变。并且闸门与「写盘 → 读回 → fullmatch」闭环在全码点空间**精确等价**（2,228,224 例逻辑遍历 + 578,780 例真实 I/O，两个方向均 0 例外），既无漏放也无过拒。
   - DR1-2 的**机器可检测半边**已根治：六种行边界空白变体下审计与生成器结论一致（双双拒绝、字节不变），审计不再下发任何生成器会拒绝的 --name= token；审计与生成器反解语义在 1,600 例组合上零分歧。
   - DR1-6 的回归网**主体承重**：M9 / M10 / M11 / M12 各以 1 failed / 98 passed 单点打红且各杀中预期用例；FIFO 用例在非特权环境下以 TimeoutExpired → self.fail 打红而非静默挂起，-x 与否不改变裁决。
   - 无次生破坏：不存在「通过 round-trip 但写入后不可反解」的名字；不 strip 导致的「行尾空白地图由沿用退化为拒绝」可由 GOVERNANCE §4.1:125-126 完整解释，非契约外行为。
   - 无过度设计：零新增抽象、零新增依赖、零共享模块重构；DR1-4 的死断言已删除且无残留不可达分支。
2. **未闭合（建议在 R2 或后续迭代处置，均不阻断）**
   - **R1-2（P2）**：DR1-2 只是把不可执行的 --name= 命令换成了不可执行的 prose 处方，且与 §4.1:125 漂移。建议在 audit-doc-health.py:141-147 的文案中补上「先移除既有地图」这一步（契约已明载，只是渲染缺失），成本一行。
   - **R1-4（P2，历史既有，紧邻变更行）**：审计读路径的非规则文件闸门缺失，FIFO 永久挂死 / 字符设备无界读取 + 裸 traceback。与 DR1-6 同一根因，建议复用 is_file() 闸门并纳入同一用例。
   - **R1-5（P2，历史既有）**：内容通道存在**无中断的确定性** 0 字节残 file + 双工具楔死。建议将其作为 DR1-7 的强化证据，把落盘改为 tmp + os.replace 原子写（可一并消灭 DR1-1 的残 file 面）。
   - **R1-1 / R1-3（P3，本 diff 引入）**：拒因文案与拒因不符；DR1-2 守卫用例空转 + 抽取器假阳性。均为低成本定点修复（一句文案 + 一个用例输入换成「干净 H1 + 漂移正文」）。
3. **移交 R2 的裁决点（三点）**
   - **DR1-2 应判「已根治」还是「改名未消灭」？** 判据是：本轮的验收标准是「审计不得下发生成器必然拒绝的 --name=」（已满足），还是「审计给出的**任何修复指引**都必须可执行」（未满足，§3 攻击路径 2）。
   - **R1-3 空转用例是否应计入 DR1-6 的修复成效？** 变异 MV 已证明该用例在 HEAD 上零断言；若 R2 采信「DR1-6 已补强」，则须接受一条不承重用例充当回归保护。
   - **R1-5 提供的新证据是否足以把 DR1-7 从待办升格为下一轮阻断项？** 其触发不再依赖「中断」这一低概率前提，而是任何非法字节文件名——这改变了该待办的风险权重。
