# Delta R1 定向复核报告 · p3-six-backlog-batch（7f35a33..8de971e）

> **复核角色**: Delta R1 红队审查员（Non-Compliant Reviewer，上下文与实现者隔离）
> **复核区间**: `7f35a3366eec5fe45f47da818919dca43b499892...8de971edf86cf06e5bb5a4efb8d5dd4adf920585`（三点式，21 文件 +656/−188）
> **被测树**: `git rev-parse HEAD` = `8de971edf86cf06e5bb5a4efb8d5dd4adf920585`；`git status --porcelain` 输出 0 行（工作树干净，实测对象即该树）
> **提交链**: `7a2a3a0`(批次前基线) → `7f35a33`(六项闭环) → `f1f2189`(R1 阻断修复) → `8de971e`(R2 §3.3 前置条件)
> **前置指纹核验**（`sha256sum` 实测，非采信自报）:
> - `r1-7a2a3a0..7f35a33.md` → `3ea790f6960b243b05106d1a6f54edf944d77f296bcbb9a2e67e030e18ec34e6`（17780 B）
> - `r2-7a2a3a0..7f35a33.md` → `efdaf03adcd36ea919f69e29fe7c27257b3d6315c26ded96907cc2256171dc29`（37922 B）
> - 与任务给定前 12 位 `3ea790f6960b` / `efdaf03adcd3` 及归档 README §审计指纹 全部吻合 → 指纹核验通过
> **独立取证汇总**（全部本机实测）:
> - WSL 全量 `python3 -B -m pytest skills/ -q -p no:cacheprovider` → **502 passed, 0 failed in 177.19s**
> - 定向 `python3 -B -m pytest skills/dual-round-review/tests skills/doc-governance/tests/test_doc_index_convention.py -q` → **160 passed in 38.50s**
> - collect 数（`git archive` 解包后 `--collect-only`）: `7a2a3a0`=490、`7f35a33`=499、`f1f2189`=501、`8de971e`=502
> - 文档四件套（WSL）: `check-doc-links.py --root docs` 88 md / **0 断链**；`check-doc-control-sync.py --root docs` 42 md / **无版本漂移**；`trim-revision.py --root docs --keep 5` 87 文件 / **全部 ≤5 条**；`audit-doc-health.py --root docs` → **PASS**
> - Windows（`.venv\Scripts\python.exe`，`PYTHONUTF8=1`）: 全量 **12 failed / 475 passed / 15 skipped / 28 subtests passed in 260.31s**；基线树同两目录 **12 failed / 192 passed / 2 skipped**，失败清单逐条相同 → 新增失败 0
> **取证限制（如实声明）**: Windows 侧以 `git archive 7a2a3a0 | tar -x` 解包 BASE 时，tar 因代码页对中文文件名报 `Invalid empty pathname`，部分中文名文件未落地；本次判定的 12 条失败均在 `doc-governance`/`spec-evolution` 两目录且与 HEAD 清单一一对应，不受该缺失影响。WSL 侧 `-z` 中文/空格路径与非法字节名实验在 ext4 临时仓库进行，不在本仓库内落任何文件。

---

## 1. 第一性原理与本质溯源分析

### 1.1 判据与边界锁（先立尺，再量物）

本次复核只对**本区间新引入**的缺陷、或**直接破坏既有调用**的次生退化行使阻断权；凡在 `7a2a3a0` 基线即已存在的形态，一律降为 P2/P3 并标注「历史既有」。R2 §3.5 的 delta 门槛同时适用：不以 YAGNI 之外的重构或新机制要求作为阻断依据。以下四类判据按第一性原理排序：

1. **宣称与物证同宽**：交付状态是证据的函数，不是作者意志的产物。任何写入 SSOT（`docs/index.md`、计划、归档 README）的完成度断言，必须能由仓库内可复跑的物证链支撑，否则就是用文档伪造状态。
2. **fail-closed 优于猜测**：当输入不可被机械解析时，正确方向是在**输入侧拒绝**，而不是让识别器在**识别侧兼容**——后者会把不确定性扩散到所有下游读取者。
3. **契约对称**：解码契约与编码契约必须同构。以 `surrogateescape` 容忍解码、却以 strict UTF-8 编码输出，等于把「容忍」在出口处反转成崩溃。
4. **变异可杀**：新增用例必须是承重断言——把它跑在修复前的实现上应当失败，否则用例只是给实现盖章。

### 1.2 R1-1（唯一阻断）的复核：结项链条已闭环，但「宣称」这一环被同一次提交重新扯断

**结项物证链（逐项实测，全部成立）**：

| 判据 | 实测结果 | 反证据位置 |
| :--- | :--- | :--- |
| 六卡在归档目录 | `archive/2026-Q4/` 下 6 张卡片全部存在 | `docs/project/backlog/archive/2026-Q4/BK-0007/0008/0010/0014/0016/0045*.md` |
| 状态/结项字段 | 六卡均 `status: completed`、`closed_at: 2026-10-20`、`resolution: delivered` | 卡片 frontmatter 头部 |
| DoD 全勾 | 未勾选计数 = 0；勾选数 BK-0045=4、BK-0008=2、BK-0014=1、BK-0007=2、BK-0010=1、BK-0016=1 | 卡片 §3 |
| 索引计数 | 活跃 **15**（进行中 0 / 计划中 15）、归档 **30**；§3 表 15 行、§4 含六卡 delivered 行 | `docs/project/backlog/index.md:13`、`:14`、`:18`、`:56-61` |
| 计划行 | 已为「**已完成**，Heavy Track」并链接审查归档 README | `docs/index.md:95` |
| 计划 §5 | 结项事实已入日志（六卡 DoD + close + 迁档 + sync-index 21→15、24→30） | 计划 `:122`、`:125`、`:135` |

关于「状态须为 `delivered`」这一字面判据：本仓 `skills/doc-governance/scripts/manage-backlog.py:32` 定义 `VALID_STATUSES = ["active","in-progress","completed","rejected","deferred"]`，`:386` 规定 `meta["status"] = "rejected" if args.resolution == "wontfix" else "completed"`——即「`status: completed` + `resolution: delivered`」才是本仓落地约定；归档目录全量 24 completed + 6 rejected，无一条 `status: delivered`。故该项**不能**作为未结项的反证据，实际语义已由 `resolution: delivered` 满足。

**但同一次提交（`8de971e`）在 SSOT 写入了无法由物证支撑的终态宣称**：

- `docs/index.md:5`：「V1.36.9 (P3 批次六项 backlog 卡片闭环交付：计划行标注已完成，**双轮审查 + Delta 闭环归档**见 `docs/project/reviews/2026-10-20-p3-six-backlog-batch/`)」——被链接目录内实有 `r1-…md`、`r2-…md`、`README.md` 三个文件，**无任何 delta 报告**（`git ls-files` 与目录列举双重确认）。
- `docs/index.md:15`：「§4 计划行由「进行中」改为「已完成」并链接审查归档（R1 红队 + R2 元审判 + **Delta 闭环 Zero Blockers**）」——`Delta` 轮次的第一轮即本报告，第二轮尚未派发；`Zero Blockers` 是一个**尚未作出的裁决**。
- `docs/index.md:95`：「（**已完成**，Heavy Track…）」——与同树计划文档 `:18` `> - **状态**: 进行中` 直接矛盾（该行 blame=`7f35a336`，本次未改）。
- 归档 README `:13` 终审裁决仍为 `未定`，`:35` 待办「Delta 闭环（修复提交后 delta-r1 → delta-r2）与 `--require-verdict=PASS`」未勾选。
- 门禁实测：`python3 -B skills/dual-round-review/scripts/check-review-report.py --require-verdict=PASS docs/project/reviews/2026-10-20-p3-six-backlog-batch` → **rc=1**，`错误: 终审裁决字段值必须精确等于「准予交付」（实际: '未定（…）'）`。
- 计划 `:31` 的活跃检查点自述：「R2 终审已完成（不予交付，Blockers=1）→ R1 阻断修复已提交 → **delta-r1 派发** → delta-r2 终审 → 归档定稿」；`:36`「阻断原因: 无（R2 唯一阻断 R1-1 已由 `f1f2189` 结项，**Delta 复核中**）」。

**本质溯源**：R1-1 的根因不是「卡片没关」，而是「宣称跑在证据前面」。`f1f2189` 把卡片、计数、DoD 全部补齐（根因的一半被真正修掉），`8de971e` 却在 `docs/index.md` 里把「已完成 + Delta 闭环 Zero Blockers」提前写死——**同一根因换了宿主**：从「提交信息宣称闭环」迁移为「版本登记表宣称闭环」。这不是措辞瑕疵：`docs/index.md` 是本仓版本登记 SSOT，后续任何代理或人类读取该行都会得到「本批次已通过双轮审查并 Zero Blockers」的错误事实，而归档 README 与门禁同时给出相反信号。与 BK-0044 登记的「提交信息取证据口径」同族——该卡已记录 V8/V11 两次因同类问题被判阻断。

**定级理由（P1 而非 P2）**：其一，这是**完成度宣称**而非实现缺陷，恰好落在本项目反复以阻断处置的红线上；其二，它与 R1-1 同构（宣称与仓库状态冲突），本次修复的任务书明确要求「提交信息不再与仓库状态冲突」，而该要求在文档面被违反；其三，它污染的是不可变历史（`docs/index.md` 修订表按追加维护，错误行会永久留在 V1.36.9 行）；其四，修复代价极低（一处措辞回退为「待 Delta 终审」），不构成返工。

### 1.3 R1-2：从「识别侧兼容」到「输入侧拒绝」的范式切换（已根治）

修复前：`has_doc_link` 用字面 `f"](./{filename})"` 比较，而 `register` 对任何文件名照单全收——含空格/`#`/`?`/`(`/`)` 的名字写进索引后，链接目标在首个空白处断句，下游解析（`check-doc-links.py`）与人工阅读同时失效，且重复 `register` 会因匹配不到而**重复追加**（版本漂移）。修复后切换为 fail-closed：

```python
# skills/doc-governance/scripts/manage-doc-index.py:138-142
if any(ch.isspace() or ch in "#?()" for ch in name):
    raise IndexMaintenanceError(
        f"--file 含不允许的字符（空白 / # / ? / ( / )）: {file_name}；"
        "链接目标需可被机械解析，请改用 kebab-case 文件名（如 my-doc.md）"
    )
```

关键不只在「拒」，更在**拒绝发生的时机**：`register_doc:287` 首行即 `filename = validate_file_arg(filename)`，早于 `resolve_within_root`（:288）与 `ensure_index`（:290）——非法输入在**任何写盘动作之前**被截断，因此天然满足「零写入」。这比「先建索引再回滚」在原理上更强：不存在中间态。

### 1.4 R1-4：从弱断言到承重断言（已根治）

BK-0008 的新增语义是「未闭合围栏告警需提示嵌套围栏演示时避免行首标记」。若断言只检查 `R1 报告`、`围栏标记`、`应为偶数` 这类 BASE 也成立的子串，用例对 BASE 同样通过——是给实现盖章而非约束实现。实测 HEAD 用例通过、BASE 版 `check-review-report.py` 同样跑该用例 **failed**（断言原文 `assert '嵌套围栏演示请避免行首标记' in line, line`；BASE 消息 `错误: 围栏代码块未闭合（R1 报告（r1-940e0f3..a1b2c3d.md） 围栏标记 1 个，应为偶数）`），变异可杀成立。

### 1.5 R1-7：从文本解析到 NUL 分隔协议（解析面已根治，出口面新裂）

旧实现 `git status -s | awk '{print $2}'` 有两个叠加缺陷：按空白断词（空格路径被截断）、C-quote 转义（非 ASCII 变成 `\346…`）。`-z` 协议把「路径」变成不可再分字段，从根本上消除断词与引号二义性；`_untracked_paths`（:211-224）只识别 `?? ` 条目并以 `\0` 切分，语义干净。实测未跟踪块原文 `plain.txt` / `with space.txt` / `文档 名.md` 原样输出，且不再误列已跟踪且被修改的 `tracked.txt`（BASE 会列出）。

**但同一函数族的出口契约未同步**：`_run_git:74` 以 `surrogateescape` 解码（容忍任意字节），`main:503-504` 却以默认 strict 的 UTF-8 重定向 stdout——容忍在出口反转成崩溃。这是本 delta 新引入的机制性缺陷（BASE 因 `git status -s` 的 C-quote 只产出 ASCII，永不触发），详见 §3 场景 S3 与 §4 DR-7。

### 1.6 附带发现的两处「收紧捕获类却放宽整体匹配面」

`has_doc_link` 在 `f1f2189` 由字面比较改为 `re.compile(r"\]\(\s*\./([^)\s?#]+)")`。捕获类 `[^)\s?#]+` 确实比原实现的语义更明确（且未放宽为任意字符），但**整体匹配面被放宽**：旧实现要求 `](./name)` 完整闭合（含可选 `#`/`?` 尾缀），新正则只要出现 `](./name` 前缀即命中。实测 `"[x](./a.md"`、`"[x](./a.md garbage)"`、`"[x](./a.md \"title\")"` 三者均返回 `True`，BASE 字面比较则均为 `False`。这与 R2 §3.4「禁止放宽 `has_doc_link` 正则」的字面禁令相抵；因唯一调用点是幂等判据（`:303`）且误报后果仅为「跳过登记」，定 P3。

### 1.7 数字取证漂移：501 与 502 的错位

计划 `:34`（blame=`8de971ed`）写 Windows UTF-8 模式「HEAD 12 failed / **473 passed / 16 skipped**」，同一提交信息写「HEAD = 12 failed / **475 passed / 15 skipped**」，本机实测 = **12/475/15**（合计 502 = HEAD collect 数）。`12+473+16 = 501` 恰为 `f1f2189` 树的 collect 数——即该行取的是**上一棵树**的测量值却标注为 HEAD。与 R1-5 同根因（数字取自错误的树），故并入 DR-8。

---

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

**未激活（非客户端/SSR 改动）**：本区间全部改动为本地 Python CLI 脚本、Markdown 文档与 Python 测试，无浏览器渲染、无 React Server Components、无 CSR/SSR 边界、无客户端状态机。

以**同维度替代推演**（运行时 × 输入域矩阵）补足该维度，覆盖本次新增的 `-z` 解析与 fail-closed 校验：

| 运行时 | 文件名输入域 | 修复前（BASE） | 修复后（HEAD） | 实测结论 |
| :--- | :--- | :--- | :--- | :--- |
| POSIX / ext4 | 合法 UTF-8（中文 + 空格） | `awk {print $2}` 断词 + C-quote → 截断为 `"\346\226\207\346\241\243` | 原样输出 `文档 名.md`、`with space.txt` | 通过（DR-4） |
| POSIX / ext4 | 含空白 / `#` / `?` / `(` / `)`（索引登记输入） | 照单全收 → 索引链接断句、重复登记漂移 | `rc=1`、零写盘、kebab-case 建议；3 次重放 `index_exists=no` | 通过（DR-2） |
| POSIX / ext4 | **非法 UTF-8 字节**（`bad\377.md`） | C-quote 为 ASCII 八进制，`rc=0` | **UnicodeEncodeError，rc=1**，输出在未跟踪块标题处截断 | **新崩溃**（DR-7） |
| Windows / NTFS | 中文、空格 | 同 POSIX 的断词问题 | 依赖 git for Windows 的 UTF-8 `-z` 输出；理论一致 | 该单测在 Windows 侧 2 skipped，**未独立验证**（如实声明） |

**沙盒与副作用面**（同维度安全推演）：

1. **无网络、无提权**：三个脚本均为纯本地文件读写，无 `subprocess` 之外的系统调用面；`prepare-review-context.py` 的 `subprocess.run` 仅执行 `git`，`shell=False`。
2. **崩溃的爆炸半径**：DR-7 的崩溃发生在**输出阶段**（`:247`），此前已完成的只读 git 采集与模板渲染均在内存中；`main` 在崩溃前未写任何文件（`--no-record` 路径更是零写盘），故不产生半写产物。但脚本以 `rc=1` 中止整份审查上下文的生成——在自动化流水线里，一个恶意或意外的文件名即可**拒绝服务**审查准备环节。
3. **fail-closed 的副作用边界**：`validate_file_arg` 只作用于 `--file` 参数，不触碰既有文档扫描路径；`find docs -name "* *"` = 0、`find docs \( -name "*(*" -o -name "*)*" \)` = 0，故不会阻断任何现存文档的登记。
4. **写权限面**：本报告只创建目标文件；所有变异实验均在 `%TEMP%`/`/tmp` 副本中进行，仓库内 `git status --porcelain` 复核为空。

---

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

### S1 · 非法文件名污染索引（已修复，攻击失败）

攻击者（或误操作）执行 `manage-doc-index.py register --file "my doc.md"`，期望在索引里制造一条断句链接，使后续 `check-doc-links.py` 与人工审阅都看不到该文档，同时靠重复 `register` 制造版本漂移。

- **演练**：temp root 预置 `how-to/my doc.md`，连续 3 次执行 `register --file "my doc.md"`。
- **结果**：三次均 `rc=1`，stderr 均为同一句「❌ --file 含不允许的字符（空白 / # / ? / ( / )）…kebab-case 文件名（如 my-doc.md）」；`find` 显示只剩预置的 `my doc.md`，`index_exists=no` → **零写入、无重复行、无版本漂移**。`a#b.md`、`a?b.md`、`a(b).md`、`a)b.md`、含 TAB 名逐一实试同样 `rc=1`。
- **对照变异**：把 `7a2a3a0` 版脚本换入 temp 副本，新用例 `-k "link_target_grammar or register_rejects_non_compliant"` → **2 failed**（`AssertionError: 0 != 1 : 非法文件名应被拒绝`）；HEAD 同选择 → **2 passed**。

### S2 · 中文/空格未跟踪文件在审查上下文中被抹除（已修复，攻击失败）

攻击场景：交付者把关键证据文件命名为 `文档 名.md` 且未 `git add`，期望 `prepare-review-context.py --working` 的未跟踪清单里看不到它，从而在审查前置上下文中隐藏改动。

- **演练**：临时仓库 = 已提交并修改的 `tracked.txt` + 未跟踪 `文档 名.md`、`with space.txt`、`plain.txt`。
- **结果（HEAD）**：未跟踪块为 `plain.txt` / `with space.txt` / `文档 名.md`，原样、无引号、无 `\346` 八进制；已跟踪的 `tracked.txt` **不再**被误列。
- **结果（BASE 对照）**：同场景输出列出 `tracked.txt`（误列）＋ 截断的 `"\346\226\207\346\241\243`。

### S3 · 一个非法字节文件名即可拒绝服务审查准备（新引入，攻击成功）

攻击场景：在 Linux/macOS 工作区里放一个文件名为非法 UTF-8 字节的文件（如 `printf 'x' > $'bad\xff.md'`），使 `prepare-review-context.py --working` 直接崩溃，令"生成审查上下文"这一步无法完成；在自动化流程中表现为审查流程卡死或被迫跳过上下文生成。

- **演练（WSL，ext4 临时仓库，HEAD 脚本）**：`python3 -B prepare-review-context.py --working --no-record` → **rc=1**；stdout 在「⚠️ 发现未跟踪的新增文件 (Untracked Files):」之后截断；stderr：

```
File ".../prepare-review-context.py", line 247, in _emit_working
    _emit(untracked_text + "\n")
File ".../prepare-review-context.py", line 78, in _emit
    sys.stdout.write(text)
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' in position 3: surrogates not allowed
```

- **对照（BASE 脚本，同场景）**：`rc=0`，输出 `"bad\377.md"`（C-quote ASCII，永不产生代理字符）。
- **机理**：`_run_git:74` `decode("utf-8","surrogateescape")` 与 `main:503-504` `reconfigure(encoding="utf-8")`（errors 默认 strict）契约不对称。
- **影响面**：不是数据损坏，而是**可用性**——审查准备环节被环境中的单个文件名击穿，且报错为 Python traceback（无用户可读的兜底提示）。

### S4 · 破损链接行被误判为「已登记」（新引入，影响有限）

攻击场景：索引中已存在被手动写坏的行（如 `- [x](./a.md` 未闭合，或 `](./a.md)` 后跟自由文本），随后 `register` 一本真文档 `a.md`。

- **演练（模块内直调 `has_doc_link`）**：`"[x](./a.md"` → True；`"[x](./a.md garbage)"` → True；`"[x](./a.md \"title\")"` → True；`"[x](./a (b).md)"` → False。（BASE 字面比较对前三者均为 False。）
- **后果**：`register` 打印「ℹ️ 文档已登记，跳过」，索引中该文档仍无一条**合规**链接行。触发前提是索引已被写坏（正常 fail-closed 路径不会产生这种行，因为非法名已在写盘前被拒），故影响有限，定 P3。

### S5 · 用 SSOT 伪造终审状态（新引入，攻击成功，且本次已实际发生）

攻击场景：交付者在门禁尚未通过时，把「已完成」「Delta 闭环 Zero Blockers」写进版本登记表，使后续读者/代理绕过 `--require-verdict=PASS` 的实质含义，直接宣告交付。

- **演练**：`docs/index.md:5`/`:15`/`:95` 三处（blame 均为 `8de971ed`）宣称已完成与 Zero Blockers；同时 `计划:18` 仍「进行中」、`计划:31` 写「delta-r1 派发」、`计划:36` 写「Delta 复核中」、`README:13` 终审裁决「未定」、`:35` 待办未勾选；归档目录无 delta 报告；门禁 `--require-verdict=PASS` 返回 **rc=1**。
- **后果**：仓库内同时存在两套互相矛盾的终态陈述，且**权威登记表站在错误一侧**。这正是 R1-1 被定 P1 的同一红线（宣称宽于取证），只是在 delta 区间换了载体。

### S6 · 取证数字在计划与提交信息之间漂移（新引入，攻击成功）

攻击场景：复核者依据计划 `:34` 的「473 passed / 16 skipped」判断 Windows 侧取证面，与同一提交信息的「475 / 15」冲突，无法判定哪一份是实测。

- **演练**：本机 Windows UTF-8 全量实测 = **12 failed / 475 passed / 15 skipped**（合计 502 = HEAD collect 数）；`12+473+16 = 501` = `f1f2189` 树 collect 数。
- **后果**：数字取自错误的树并标注为 HEAD，属「凭据不实」；不影响功能，但污染检查点记录。

---

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 结论 / 缺陷 | 严重级别 | 位置（文件:行） | 是否由当前 Diff 引入 | 反证据（可复现命令 / 夹具） |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DR-1** | **复核 R1-1：未根治（根因复现）**。卡片结项、DoD、索引计数、归档迁移、计划行、§5 日志六项均已闭环；但同一提交在 `docs/index.md` 写入「已完成」与「Delta 闭环 Zero Blockers」，与同树计划「进行中」、归档 README「未定」、门禁 rc=1、归档目录无 delta 报告同时冲突——宣称宽于取证 | **P1（阻断）** | `docs/index.md:5`、`:15`、`:95`；对照 `docs/project/plans/2026-10-20-p3-six-backlog-batch.md:18`、`:31`、`:36`；`docs/project/reviews/2026-10-20-p3-six-backlog-batch/README.md:13`、`:35` | **是**（`8de971ed`；`git blame -L5,5` / `-L15,15` / `-L95,95 docs/index.md` 均指向该提交） | `python3 -B skills/dual-round-review/scripts/check-review-report.py --require-verdict=PASS docs/project/reviews/2026-10-20-p3-six-backlog-batch` → rc=1「终审裁决字段值必须精确等于「准予交付」（实际: '未定…'）」；`ls docs/project/reviews/2026-10-20-p3-six-backlog-batch/` → 仅 r1/r2/README；`grep -n "状态" 计划` → `进行中` |
| **DR-2** | **复核 R1-2：已根治**。空白 / `#` / `?` / `(` / `)` 全部 fail-closed 拒绝并给 kebab-case 建议；拒绝先于建索引（零写盘）；3 连发无重复行/版本漂移；捕获类未放宽为任意字符；新用例可杀死 BASE | 无残余阻断（已根治） | `skills/doc-governance/scripts/manage-doc-index.py:126-143`（拒绝块 `:138-142`）、`:287`（校验先于 `ensure_index`） | 是（`f1f2189`） | 3 次 `register --file "my doc.md"` → 均 rc=1、`index_exists=no`；合规名 `deployment.md` → rc=0 且 V1.0.1，重复 → 「ℹ️ 文档已登记，跳过」版本不变，再登 `rollback.md` → V1.0.2；BASE 脚本变异 → `-k "link_target_grammar or register_rejects_non_compliant"` **2 failed**，HEAD **2 passed** |
| **DR-3** | **复核 R1-4：已根治**。断言承重到 BK-0008 新增语义（「嵌套围栏演示请避免行首标记」），非 BASE 也成立的四子串空转 | 无残余阻断（已根治） | `skills/dual-round-review/tests/test_check_review_report.py`（`test_unclosed_fence_message_identifies_report_and_parity`）；被测脚本 `skills/dual-round-review/scripts/check-review-report.py` | 是（`f1f2189`） | HEAD 跑该用例 → 1 passed；换入 BASE（`7a2a3a0`）版 `check-review-report.py` → **1 failed**，断言 `assert '嵌套围栏演示请避免行首标记' in line, line`，BASE 实际消息缺该提示 |
| **DR-4** | **复核 R1-7：解析面已根治**。`git status --porcelain -z` + `\0` 切分，中文/空格路径原样输出（无 `\346`、无引号），且消除「误列已跟踪文件」；出口面残留见 DR-6 / DR-7 | 解析面无残余阻断（已根治） | `skills/dual-round-review/scripts/prepare-review-context.py:211-224`（`_untracked_paths`）、`:74`（解码） | 是（`f1f2189`） | 临时仓库（修改的 `tracked.txt` + 未跟踪 `文档 名.md`/`with space.txt`/`plain.txt`）→ 未跟踪块原文三行原样、`tracked.txt` 不出现；BASE 同场景列出 `tracked.txt` 与截断的 `"\346\226\207\346\241\243` |
| **DR-5** | `has_doc_link` 捕获类未放宽，但**整体匹配面放宽**：未闭合 `](./a.md`、带尾随文本、带 title 的链接均被判为「已登记」；与 R2 §3.4「禁止放宽该正则」字面禁令相抵；误报后果仅为跳过登记 | **P3** | `skills/doc-governance/scripts/manage-doc-index.py:278`（`pattern = re.compile(r"\]\(\s*\./([^)\s?#]+)")`）、`:279-282`、唯一调用点 `:303` | **是**（`f1f2189`，由字面比较改为前缀正则） | 模块直调探针：`"[x](./a.md"` / `"[x](./a.md garbage)"` / `"[x](./a.md \"title\")"` → 均 True；`"[x](./a (b).md)"` → False；BASE 字面比较对前三者均 False。另：`8de971e` 提交信息称「链接识别正则保持严格…不为兼容非法文件名而放宽」，与实际改动不符 |
| **DR-6** | 同一次 `--working` 输出中，原始状态块（直通 `git status -s`）仍打印 C-quote 八进制：`?? "\346\226\207\346\241\243 \345\220\215.md"`。解析面已干净、展示面未统一 | **P3** | `skills/dual-round-review/scripts/prepare-review-context.py:239`（`_run_git(["status","-s"])` 直通输出） | **否**（历史既有形态；本 delta 未覆盖该行） | 上述 S2 夹具的完整 stdout 第 8 行原文即含 `?? "\346\226\207\346\241\243 \345\220\215.md"`；BASE 与 HEAD 在该行无差异 |
| **DR-7** | 非 UTF-8 文件名使 `--working` 崩溃：`surrogateescape` 解码 + strict UTF-8 输出，触发 `UnicodeEncodeError`（`'\udcff'`），rc=1，输出在未跟踪块标题处截断 | **P2** | `skills/dual-round-review/scripts/prepare-review-context.py:74`（解码）、`:247`（`_emit(untracked_text + "\n")`）、`:78`（`sys.stdout.write`）、`:503-504`（`reconfigure(encoding="utf-8")`，errors 默认 strict） | **是**（`f1f2189`；BASE 走 `git status -s` 只产 ASCII，无此路径） | ext4 仓库创建 `bad\377.md` → HEAD rc=1（traceback 见 §3 S3），BASE rc=0（输出 `"bad\377.md"`）；修法仅为 `reconfigure(..., errors="surrogateescape")` 或 `backslashreplace` 一行 |
| **DR-8** | 计划检查点 Windows 数字与实测/提交信息不同宽：`:34` 写「HEAD 473 passed / 16 skipped」，同提交信息写「475 / 15」，实测 475 / 15；`12+473+16=501` 为 `f1j2189` 树 collect 数（取错树） | **P2** | `docs/project/plans/2026-10-20-p3-six-backlog-batch.md:34` | **是**（`8de971ed`） | Windows UTF-8 全量实测 12F/475P/15S（合计 502）；`12+473+16=501` 与 `f1f2189` collect 数一致；`git blame -L34,34` → `8de971ed` |
| **DR-9** | **抽查 R1-3 / R1-10 / R1-11：在位**。SKILL.md 已把 `--archive-root` 守卫面收窄为「空值或文件系统根（含 realpath 后指向根）」，与 `_validate` 实际行为一致；例外分支补「与 §1.6 同构」并追加结构同构要求；R1-10 的 Windows UTF-8 取证口径已补，但数字问题并入 DR-8 | 无残余阻断（在位） | `skills/dual-round-review/SKILL.md:117-119`（收窄声明）、`:169`（异常分支 7 同构表述）；`prepare-review-context.py:119-140`（实现） | 是（`f1f2189`） | 文本框与代码逐条对照：声明只承诺「空值/根目录拒绝」，实现亦只拒 `""` 与 realpath 根，`../` 外跳由调用方保证——无超额声明 |

> 边界锁声明：DR-6 为历史既有（非本 delta 引入）已降 P3；DR-5 / DR-7 / DR-8 为本区间新引入；DR-1 为本区间新引入的**同根因复现**。除此以外未发现本 delta 破坏既有调用（真实归档校验、未跟踪输出、幂等登记三项均在 DR-2/DR-4 中实测通过）。

---

## 5. 第一轮结论概要

### 5.1 统计

| 类别 | 数量 | 明细 |
| :--- | :--- | :--- |
| **阻断项（P1）** | **1** | DR-1（复核 R1-1：卡片结项已闭环，但 `docs/index.md` 宣称「已完成 / Delta 闭环 Zero Blockers」宽于取证） |
| 建议项 P2 | 2 | DR-7（非 UTF-8 文件名崩溃）、DR-8（计划 Windows 数字取错树） |
| 建议项 P3 | 2 | DR-5（`has_doc_link` 匹配面放宽）、DR-6（原始状态块 C-quote 残留，历史既有） |
| 已根治（无残余） | 3 | DR-2（R1-2 fail-closed）、DR-3（R1-4 承重断言）、DR-4（R1-7 解析面） |
| 在位确认 | 1 | DR-9（R1-3 / R1-10 / R1-11 抽查） |

### 5.2 阻断项判定说明

- **R1-1 未根治（DR-1）**：结项维度的六项判据全部达成（六卡 `completed`/`closed_at`/`resolution: delivered`、DoD 全勾、索引 15/30、计划行已完成并链归档、§5 结项日志、链接/控制/裁剪/健康四门禁全绿、WSL 全量 502 passed）。但「宣称与物证同宽」这一根因在 `8de971e` 以 `docs/index.md` 为载体复现，且与同树计划、归档 README、门禁裁决三者同时冲突。当前 Diff 引入，定 P1。
- **R1-2 / R1-4 / R1-7 已按 R2 §3.3 落实**：fail-closed 输入侧拒绝（含零写盘与 3 连发幂等）、承重断言（BASE 变异可杀）、`-z` NUL 协议（中文/空格原样）均经独立实测成立；R1-2 未采用「放宽识别正则」的兼容路径，方向正确。
- **次生退化**：`-z` 与 fail-closed 未破坏真实归档校验（`--require-verdict` 语义正确、链接门禁 0 断链）、未跟踪输出（`tracked.txt` 不再误列）、幂等登记（重复 register 不增行不升版）；但 `-z` 引入了一处新的崩溃面（DR-7）与一处匹配面放宽（DR-5），二者均不构成交付阻断。

### 5.3 结论

**不放行（Zero Blockers 未达成）**。阻断项 1 项（DR-1，P1），须以最小改动处置后方可进入 delta-r2：

1. 将 `docs/index.md:5` / `:15` 的「已完成 / Delta 闭环 Zero Blockers」改为与当前物证一致的表述（例如「Delta 复核中，待终审裁决」），或撤回该行至 delta-r2 通过后再登记；`:95` 的「已完成」须与计划 `:18` 的状态字段同源。
2. 建议同批处理 P2：DR-8 更正计划 `:34` 的 Windows 数字为实测 475/15（并注明取自 HEAD 树 502）；DR-7 在 `:504` 的 `reconfigure` 补 `errors="surrogateescape"`（一行）。
3. P3（DR-5 / DR-6）可登记为后续 backlog，不阻断。

> 本报告全部结论均基于本机可复跑命令与仓库内 `文件:行` 反证据；未采信任何实现者自报数字，未修改仓库内除本文件外的任何内容（`git status --porcelain` 复核为空）。
