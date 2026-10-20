# Delta-r2 元审查终审报告（8de971e..1f6a826）

> **文档控制信息**
> - **文档标识**: REVIEW-DELTA-R2-p3-six-backlog-batch
> - **复核对象**: `8de971e`（Delta-r1 基线）→ `1f6a826`（本轮修复提交）
> - **周期基线**: `7f35a33`（delta-r1 起点，归档配对键；见 §1.3）
> - **落盘名**: 任务规定名为 `delta-r2-8de971e..1f6a826.md`（与本批归档的配对键不兼容，实测见 §1.3）；主调度已在闭包时将其重命名为 `delta-r2-7f35a33..1f6a826.md`，本报告即该文件（改名时字节与 SHA256 不变；闭包后编辑见 §3.4）。
> - **前置指纹核验（`sha256sum` 实测，非采信自报）**:
>   - R2 首轮 `r2-7a2a3a0..7f35a33.md`: 37922 B / `efdaf03adcd36ea919f69e29fe7c27257b3d6315c26ded96907cc2256171dc29` ✅
>   - Delta-r1 `delta-r1-7f35a33..8de971e.md`: 30332 B / `13db2d6d5baba244bb299d934b2e90787873a6e6be882873580e787cb67f9b24` ✅
>   - R1 首轮 `r1-7a2a3a0..7f35a33.md`: 17780 B / `3ea790f6960b243b05106d1a6f54edf944d77f296bcbb9a2e67e030e18ec34e6` ✅
>   - 计划 `2026-10-20-p3-six-backlog-batch.md`: 21917 B / `41da6b6c73d6…` ✅
> - **复核者**: Delta R2 元审查（Principal Pragmatic System Architect；与实现者、Delta-r1 复核者上下文隔离）
> - **取证环境**: WSL2 Python 3.12（Linux 树）；Windows `.venv` Python 3.12（`PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8`）；复核时仓库工作树 `git status` 干净，HEAD=`1f6a826`；闭包动作留下 `docs/index.md`、计划、README 与本报告的工作树改动（未提交）。
> - **取证边界**: 本报告所有数字均为本人重跑所得；Windows 闭包态（登记 delta-r2 之后）未重跑，标注为“推算、待闭包提交实测”。临时副本均在 `/tmp`，原仓库除本报告外零改动。
> - **闭包后复核**: 主调度已执行改名/登记/计划回填；本人实测门禁 rc=0、WSL 503P/0F；最终判定 ✅（见 §3.4）。

---

## 1. 元审查辩证质询

### 1.1 Delta-r1 判决质量：DR-1 成立、DR-7/DR-8 定位准确、DR-2/3/4 独立可复现、DR-6 降级合规

**DR-1（阻断）成立。** Delta-r1 指认 `8de971e` 树的 `docs/index.md:5/:15/:95` 把交付写成“已完成 / Delta 闭环 Zero Blockers”，而计划 `:18` 写“进行中”、审查归档 README `:13` 写“未定”、门禁 `--require-verdict=PASS` rc=1、且归档目录当时无 delta 报告——宣称宽于取证。我复核了 `git show 8de971e:docs/index.md` 的原文：`:5` 为“P3 批次六项 backlog 卡片闭环交付：计划行标注已完成，双轮审查 + Delta 闭环归档见……”，`:15` 为“**P3 批次六项 backlog 闭环交付登记**：§4 计划行由「进行中」改为「已完成」……（R1 红队 + R2 元审判 + Delta 闭环 Zero Blockers）；……Windows UTF-8 模式失败集 ⊆ 基线且新增失败 0”，`:95` 为“（**已完成**，Heavy Track；六卡迁入 `archive/2026-Q4/`……）”。三处均与 `docs/project/plans/2026-10-20-p3-six-backlog-batch.md:18`（进行中）、`docs/project/reviews/2026-10-20-p3-six-backlog-batch/README.md:13`（未定）、以及当时 `check-review-report.py` 的 rc=1 直接冲突。**判决成立，定级 P1 阻断合规。**

**DR-7（P2）定位准确。** Delta-r1 指认 `prepare-review-context.py` 的 git 解码侧已用 `surrogateescape`（`:74`），但输出侧 `sys.stdout` 仍是 strict UTF-8（`:78`、`:503-504`），非 UTF-8 文件名会以 `\udcff` 代理字符到达 `sys.stdout.write` 并抛 `UnicodeEncodeError`。我按 Delta-r1 的取证实测复现：BASE（`8de971e` 副本）创建 `bad\xff.md` 后 `--working` rc=1，traceback 指向 `base-prepare.py:78` 的 `sys.stdout.write(text)`，异常为 `UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' in position 3: surrogates not allowed`；HEAD（`1f6a826`）rc=0、stderr 空、stdout 保留 `bad\udcff.md`。**定位与复现均成立。**

**DR-8（P2）定位准确，但其“修复”在本轮仍不彻底（见 §1.5）。** Delta-r1 指认计划 `:34` 的 473/16 与提交信息 475/15、实测 475/15 及 `f1f2189` 树的 collect=501（12+473+16）不符，属“取错树”。该判断成立：`f1f2189` 树是 R1 修复树，不是当前 `1f6a826` 树；当前树 collect=503。

**DR-2/DR-3/DR-4 的“已根治”有独立实测支撑。** 我在临时副本上用 BASE 脚本/回退变体逐项变异，结果与 Delta-r1 的结论方向一致（详见 §1.4、§1.6 与附录 A.3）：
- DR-2（R1-2 fail-closed）：`manage-doc-index.py:126-143` 的 `validate_file_arg` 拒绝空白 / `#` / `?` / `(` / `)`，`register_doc:289` 先于 `ensure_doc_index` 调用；非法名 rc=1 且 `index_exists=no`（零写盘），连续 3 次 rc=1 幂等；HEAD 定向 `test_doc_index_convention.py` 40 passed。
- DR-3（R1-4 空转消除）：`test_check_review_report.py:229-240` 的 `test_unclosed_fence_message_identifies_report_and_parity` 对 `7a2a3a0` 的 BASE 脚本运行 → **1 failed**（断言 `'嵌套围栏演示请避免行首标记' in line` 失败）；HEAD 定向 `test_check_review_report.py` 50 passed。若删掉该断言，用例对 BASE 会重归空转——该断言是承重的。
- DR-4（R1-7 `-z` 解析）：`prepare-review-context.py:211-224` 解析 `git status --porcelain -z`；HEAD 用例覆盖中文/空格/换行路径、`tracked.txt` 不误列；对 `7a2a3a0` 的 BASE 脚本变异 → **6 failed**（`test_untracked_lists_new_files`、`test_untracked_block_lists_none…`、`test_untracked_block_preserves_unicode_and_space_paths`、`test_untracked_block_preserves_non_utf8_path_without_crash`、`test_archive_root_empty_rejected`、`test_archive_root_filesystem_root_rejected`），HEAD 40 passed。

**DR-6（历史既有）降级合规。** `prepare-review-context.py:239` 的“原始状态块”仍直通 `git status -s` 的 C-quote 输出；该行在 `8de971e` 与 `1f6a826` 完全相同（`git diff 8de971e..1f6a826 -- prepare-review-context.py` 不含该行），blame 指向本 delta 之前。Delta-r1 判 P3、历史既有、后续项，符合其自述的“仅对本区间新引入或直接次生退化行使阻断权”门槛；本轮未把它当阻断，正确。

### 1.2 DR-1 处置核验：三处口径已回到“进行中/未定”，但计划检查点仍有绿色宣称

逐条核对当前 `1f6a826` 树：
- `docs/index.md:5`：“交付**进行中**：R1+R2 已完成（R2 判阻断），Delta 定向复核进行中，终审裁决未定” ✅
- `docs/index.md:15`：“**P3 批次六项 backlog 交付进展登记（未定稿）**……`--require-verdict=PASS` 尚未通过” ✅
- `docs/index.md:95`：“**进行中**：R1/R2 双轮审查已完成、Delta 定向复核中，终审裁决未定” ✅
- 审查归档 `README.md:13`：“终审裁决: 未定” ✅；`README.md:39` 待办仍为“DR-1/DR-7/DR-8 处置 → delta-r2 终审 → `--require-verdict=PASS`” ✅
- 计划 `:18`：“状态: 进行中” ✅

**“已完成 / Zero Blockers / 准予交付”在本批次文档中已无残留。** 我对三份控制文档做了全文 grep：`docs/index.md` 中仍出现这些词的行（`:79`、`:82`、`:84-88`、`:92`）均属于更早批次（RFC-0003、`dual-round-review` V2.1.0、批次 A-D、`doc-governance` 目录索引、AGENTS 重构），不是本批次；本批次三处已收口。因此 **DR-1 的原始宣称已处置，判“降级（阻断→关闭）”成立。**

> **闭包后状态更新（2026-10-20，主调度执行）**：主调度已在门禁 PASS 后将 `docs/index.md:5/:15/:95` 推进为“已完成/准予交付/门禁 PASS”，属合法状态流转；本节上文是复核时（`1f6a826`）的快照，二者不矛盾。

但必须指出一处**残留的绿色宣称**（归入 DR-8，而非重开 DR-1）：计划 `:34` 仍写“WSL 全量 `502 passed / 0 failed`（修复后工作树）……Windows……12 failed / 475 passed / 16 skipped（失败集逐条相同、新增失败 0）”，`:36` 仍写“阻断原因: 无”。在 `1f6a826` 树上，WSL 实测 **1 failed / 502 passed**，Windows 实测 **13 failed / 474 passed / 16 skipped**；门禁 rc=1。该两个字段是“单一可读真相源”的验证状态，其宣称宽于当前树取证，必须在闭包提交中改写（见 §1.5、§3 处置）。

### 1.3 闭包结构阻断（🔴，无稳定 ID）：归档配对键与规定落盘名不兼容

这是本轮元审发现的**唯一新增阻断**，且是**本 diff 的直接次生退化**：`1f6a826` 把 delta-r1 报告（`delta-r1-7f35a33..8de971e.md`）加入归档，但归档中尚无与它同基线配对的 delta-r2。

**证据链：**
1. `git ls-tree 8de971e docs/project/reviews/2026-10-20-p3-six-backlog-batch/` 只有 `README.md`、`r1-7a2a3a0..7f35a33.md`、`r2-7a2a3a0..7f35a33.md`；`git show --stat 1f6a826` 显示 delta-r1 报告为 **+220 新增**。即：`8de971e` 树无 delta-r1，门禁当时可配对 r1/r2；`1f6a826` 树新增 delta-r1 后，base=`7f35a33` 只剩 R1 无 R2。
2. `check-review-report.py:279-287` 的 `_base_key` 明确“轮次配对键 = 报告文件名的**基线**段”；`:477-480` 在 `r2_by_base` 缺同 base 时直接追加 `错误: 基线 7f35a33 的 R1 报告未配同基线 R2 报告（轮次未闭环，禁止靠他轮 R2 顶包放行）`。
3. 当前仓库实测：`python3 -B skills/dual-round-review/scripts/check-review-report.py docs/project/reviews/2026-10-20-p3-six-backlog-batch` → rc=1，仅上述配对错误 + `结构校验未通过`；其余结构/指纹/区块/ID 检查未报错。
4. **规定名探针 A**：把归档复制到 `/tmp/probe-a`，加入同内容报告并命名为任务规定的 `delta-r2-8de971e..1f6a826.md`，台账追加一行 → rc=1，错误仍是“基线 `7f35a33` 的 R1 报告未配同基线 R2 报告”。即：**按任务规定名登记后，闭包仍不通过。**
5. **周期基线名探针 B**：同内容改名为 `delta-r2-7f35a33..1f6a826.md`（与 delta-r1 共享 base）→ rc=0，输出 `结构校验通过: 索引齐备 · 报告 4 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐`。
6. **完整闭包探针 C**：在 B 基础上把 README `:13` 改为“准予交付”，执行 `--require-verdict=PASS` → rc=0，输出追加 `· 终审裁决 准予交付`；闭包态 WSL 全量实测 **503 passed / 0 failed in 78.75s**（`/tmp/headcopy` 副本）。
7. 既有归档惯例支持“同 base 配对”：`docs/project/reviews/2026-10-12-spec-evolution-v1/delta-r1-fe8da78..9db83c7.md` 与 `delta-r2-fe8da78..2100136.md` 共享 base `fe8da78`；`prepare-review-context.py:494` 也按 `{round}-{base}..{head}.md` 生成文件名。delta-r2 的正确归档名是 `delta-r2-7f35a33..1f6a826.md`，不是任务规定的 `delta-r2-8de971e..1f6a826.md`。

**实现缺陷判定：** 这不是“报告还没写”的暂时红，而是**确定性闭包路径缺陷**——按任务规定名登记后门禁仍红；同时它使 `test_existing_archives_all_pass_gate` 在 `1f6a826` 树红（WSL 全量 1F/502P；Windows 全量 13F/474P/16S，新增的 1 条正是该测试），与计划 `:34` 的“0 failed / 新增失败 0”直接冲突。归因：**本 diff 引入（归档 delta-r1 未配 R2）+ 规定落盘名与配对键不兼容**。修复是机械的（改名/登记/改 README 台账与终审裁决），已用探针 C 证明可达成，但当前树未达成，故定级 **🔴 阻断**。

> **闭包后复核（2026-10-20）**：主调度已按 §3.3 执行改名/登记（README V1.0.4 `[!NOTE]`：`delta-r2-7f35a33..1f6a826.md`，字节与 SHA256 在改名时不变），README `:13` 置为 `✅ 准予交付`。本人闭包后实测 `--require-verdict=PASS` rc=0、WSL 全量 503 passed / 0 failed in 292.39s。§1.3 的 🔴 是复核时（闭包前）的判定，现已被闭包动作消除；证据链保留供追溯。

> 说明：本报告按任务规定路径落盘，是为了遵守“唯一写权限”；归档时请**重命名**为 `delta-r2-7f35a33..1f6a826.md`。重命名不改变字节与 SHA256，README 台账/清单/指纹可直接复用同一哈希。

### 1.4 DR-7 修复核验：输出侧 `surrogateescape` 与 git 解码对称，非 UTF-8 文件名不再崩溃

**代码对称性：**
- 解码侧（既有）：`prepare-review-context.py:74` `_run_git` 用 `errors="surrogateescape"` 解码 git 字节；`git status --porcelain -z` 的路径是原始字节，0xff 不被 C-quote。
- 输出侧（本 diff）：`:503-506` 在 `main` 入口执行
  `sys.stdout.reconfigure(encoding="utf-8", newline="\n", errors="surrogateescape")` 与 `sys.stderr.reconfigure(...)`；`:247` 的 `_emit(untracked_text)` 与 `:78` 的 `sys.stdout.write` 因此不再抛 `UnicodeEncodeError`。
- 非输出通道：`_write_text`（`:415-417`）仍是 strict UTF-8，但只写锚点文件与归档 README（base=working、head=短 SHA，不含代理字符），不构成对称性缺口。

**手工复现（临时副本，原仓库零改动）：**
- git 原始字节：`git status --porcelain -z` 返回 `3f3f 20 62 61 64 ff 2e 6d 64 00`（`?? bad\xff.md\0`）。
- BASE（`8de971e` 的 `prepare-review-context.py`）：`--working` rc=1，stderr 含 `UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' in position 3: surrogates not allowed`，栈指向 `base-prepare.py:78`，调用来自 `:247`/`:523`。
- HEAD（`1f6a826`）：rc=0，stderr 空，stdout 含“未跟踪的新增文件”与 `bad\udcff.md`。
- 用例：`test_prepare_review_context.py:138-153` 的 `test_untracked_block_preserves_non_utf8_path_without_crash` 在 `os.name == 'nt'` 时 skip（`:141-142`），用 `os.open(..., 0o600)` 创建 `b"bad\xff.md"`（`:145`），以 `subprocess.run(..., text=True, encoding="utf-8", errors="surrogateescape")` 调用（`:147-149`），断言 rc==0、stderr 无 `UnicodeEncodeError`、stdout 含 `bad\udcff.md`（`:150-153`）。Windows 全量因此多 1 个 skip（16 vs `8de971e` 的 15），与实现一致。
- 结论：**DR-7 修复对称、可杀死 BASE、无次生退化；判“降级（P2→关闭）”。** Windows 覆盖缺口（POSIX-only 用例 skip）是既有 §1.4 第 4 项允许的平台口径，不构成新阻断；但建议在计划 §1.4 明示“该用例 POSIX-only”以免后续误读。

### 1.5 DR-8 修复核验：473 已清除，但数字仍取自“非当前树”

**已消除的旧值：** 计划 `:34` 与 `:134` 的 Windows 数字已从 473 改为 475；`:139` 也登记“DR-8 → 计划 Windows 数字更正为 475 passed / 16 skipped”。**473 不再被引用**（全文 grep 无 473/16 组合）。这部分成立。

**仍存在的“取错树”类陈述（P2 维持）：**

| 位置 | 当前文字 | 当前树 `1f6a826` 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| 计划 `:34` | WSL `502 passed / 0 failed`（“修复后工作树”） | WSL **1 failed / 502 passed**（`8de971e` 树才是 502P/0F） | 取自 `8de971e` 树，非当前树 |
| 计划 `:34` | Windows `12 failed / 475 passed / 16 skipped`，`新增失败 0` | Windows **13 failed / 474 passed / 16 skipped** | 12F/475P/16S 只在“闭包态”成立；当前树新增的 1 failed 正是归档门禁 |
| 计划 `:45` | HEAD `12 failed / 475 passed / **15 skipped**` | 当前树 16 skipped（新增用例 skip） | 与 `:134` 的 16 自相矛盾；15 是 `8de971e` 值 |
| 计划 `:134` | `HEAD（修复后）= 12 failed / 475 passed / 16 skipped`，`新增失败 0` | 13F/474P/16S；新增失败 1（归档门禁） | 标签“HEAD（修复后）”与当前树不符 |
| 计划 `:35` | `最新有效提交: f1f2189` | HEAD=`1f6a826` | 未更新 |
| 计划 `:36` | `阻断原因: 无` | 门禁 rc=1、全量红 | 与当前树冲突 |
| 计划 `:139` | “DR-8 → 计划 Windows 数字更正为 475/16” | `:45` 仍 15 | “更正”未覆盖全部位置 |

**补充实测（用于闭包判定，不作为当前树绿色宣称）：** 在 `/tmp/headcopy` 副本中按探针 C 完成登记后，WSL 全量 **503 passed / 0 failed**；Windows 闭包态**未重跑**，按失败集推算应为 12F/475P/16S，必须在闭包提交中实测确认。计划若要在闭包提交中写“12F/475P/16S”，应同时更新 `:45` 为 16、`:35` 为闭包提交号、`:36` 改写为“无未处置代码阻断；闭包结构项见 delta-r2”，并删除/改写“新增失败 0”。

**结论：** DR-8 的“473→475”单点修复成立，但整体仍是“拿旧树/未来树的数字写当前检查点”，属同一缺陷的未完成修复；**维持 P2（🟡）**，要求闭包提交按上表统一。它不是新的代码缺陷，但它是“宣称宽于取证”的文档级问题，不能以“后续可优化”放过。

> **闭包后状态更新（2026-10-20，主调度执行）**：主调度已将计划 `:34/:45/:134` 统一为闭包态（WSL 503P/0F；Windows 12F/475P/16S；`:45` 16 skipped），473 与 15 旧值清除；`:35` 为 `CLOSURE_COMMIT_PLACEHOLDER`（待闭包提交号），`:36` 仍留“Delta 复核中”。前者与当前树一致；`:36`/`:35` 为闭包提交前的文本残项（⚪），不构成新阻断。DR-8 因此在闭包后关闭（见 §2 表）。

### 1.6 DR-5 修复核验：可选锚点/查询串 + 右括号收尾，负例可杀死

`manage-doc-index.py:267-284` 的 `has_doc_link` 现使用
`pattern = re.compile(r"\]\(\s*\./([^)\s?#]+)(?:[?#][^)\s]*)?\)")`（`:280`）：
- 目标文件名后只允许“可选 `#...` / `?...` + 右括号”收尾；
- 不再用“前缀包含”把 `[x](./a.md`、`[x](./a.md garbage)`、`[x](./a.md "title")` 误判为已登记。

**直接探针（HEAD 副本，导入模块后逐条调用）：**

| 输入 | 结果 | 期望 |
| :--- | :--- | :--- |
| `[x](./a.md)` | True | 已登记 |
| `[x](./a.md#install)` | True | 锚点变体仍识别 |
| `[x](./a.md?tab=1)` | True | 查询串变体仍识别 |
| `[x](./a.md#)` | True | 空锚点变体仍识别 |
| `[x](./a.md#a?b)` | True | 复合变体仍识别 |
| `[x](./a.md` | False | 半截链接不算 |
| `[x](./a.md garbage)` | False | 尾巴不算 |
| `[x](./a.md "title")` | False | title 不算 |
| `[x](./a.md extra)` | False | 尾巴不算 |
| `[x](./b.md#a-b)` 对 `a.md` | False | 文件名不符不算 |

**用例与变异：**
- `test_doc_index_convention.py:75-81` 新增 4 条负例（`[x](./a.md`、`[x](./a.md garbage)`、`[x](./a.md "title")`、`[x](./a.md extra)`）与 3 条正例（plain / `#install` / `?tab=1`）。
- 把 `manage-doc-index.py` 回退为 `8de971e` 版（字面 `f"](./{filename})" in text` 比较）→ `test_doc_index_convention.py` **1 failed**：`test_link_target_grammar_stops_at_unsafe_characters` 在 `[x](./a.md` 上断言 `True is not false`。HEAD 40 passed，说明新用例可杀死旧实现，不是空转。
- 真实归档幂等：`test_register_is_idempotent_for_anchor_and_query_variants` 在 HEAD 通过；`docs` 下 149 个 md 无 title 式/锚点式相对链接（`grep` 实测仅审查报告散文中的行内代码），收紧不破坏现存归档。
- 与 DR-2 的分工：`validate_file_arg:126-143` 在 `register_doc:289` 之前拒绝含空白 / `#` / `?` / `(` / `)` 的新文件名（fail-closed）；`has_doc_link` 的可选锚点/查询串只用于识别既有链接，不放松新文件名约束。二者同源、不矛盾。
- **结论：DR-5 修复正确；判“降级（P3→关闭）”。**

### 1.7 反过度工程与边界锁：9 文件均在 DR-1/5/7/8 + 必要校验器容忍度内

`git diff --stat 8de971e..1f6a826` 共 9 文件 +274/−16：
- `docs/index.md`（6 行，DR-1 三处口径）
- 计划（9 行，DR-8 数字 + §5 两条归档/处置日志）
- 审查归档 README（11 行，台账/链接/指纹/待办/版本）
- delta-r1 报告（220 行，新增归档）
- `manage-doc-index.py`（8 行，DR-5 正则 + docstring）
- `test_doc_index_convention.py`（7 行，DR-5 负例/正例）
- `check-review-report.py`（5 行，**校验器容忍度**）
- `prepare-review-context.py`（6 行，DR-7 输出侧重配）
- `test_prepare_review_context.py`（18 行，DR-7 POSIX 用例）

**边界判定：**
- 没有借机重构、没有新增机制、没有改公共契约、没有把 DR-6 当阻断。DR-6 仍在计划 §5 `:139` 登记为“历史既有 P3、后续项不修”，`prepare-review-context.py:239` 未动。
- `check-review-report.py:244-248` 的 `cell.strip(SPACE).strip("*`_").strip()` + `_ID_CELL_RE.fullmatch(cell)`（`_ID_CELL_RE` 在 `:94`）是**必要容忍度**：delta-r1 报告以 `| **DR-1** |` 粗体 ID 直写归档（`delta-r1-7f35a33..8de971e.md:180-188`），不剥离强调符号则门禁无法解析其 ID 表，归档会因“ID 未抽取”而红。该改动只剥离强调符号，不放宽 ID 语义；HEAD `test_check_review_report.py` 50 passed，既有归档仍通过。
- 未发现“顺手重构”“批量重排”“新增机制”类越界；DR-7 的 `reconfigure` 是 3 行输出侧修复，未改 `_write_text` 的 strict 语义（其写入面不含代理字符），属于最小修复。
- **反过度工程判定：通过。**

### 1.7b 记录锚点与流程观察（非阻断）

`.review-context/review-8de971e.md` 仍是未填模板（`[full|light|delta]`、`[1|2|...]`、`[0/3]`、`[待填写]`、`未定`），且被 `.gitignore:8` 忽略。它不参与门禁、不进入版本化交付，故不构成实现缺陷；但若作为审查上下文记录使用，应在派发/复核时填充。本轮我未修改它（写入权限仅限本报告）。列为非阻断观察 S3。

### 1.8 归档保真：delta-r1 以 `direct` 登记，台账/指纹/链接一致

只读核验：
- 文件：`docs/project/reviews/2026-10-20-p3-six-backlog-batch/delta-r1-7f35a33..8de971e.md`，30332 B，SHA256 `13db2d6d5baba244bb299d934b2e90787873a6e6be882873580e787cb67f9b24`。
- 台账：`README.md:20` 行 `delta-r1 | 7f35a33..8de971e | 子智能体 eeb36673 | delta-r1-7f35a33..8de971e.md | 13db2d6d5bab | ... | direct`；`:27` 链接存在且相对路径正确；`:32` 指纹全值与实测一致；`:42` 修订行写 30332 B / `13db2d6d5bab…`；计划 §5 `:138` 同文（30332 B / `13db2d6d5baba…` / 句柄 `eeb36673` / 不放行）。
- 门禁解析：`check-review-report.py` 对该归档的结构校验除“配对 R2”外未报指纹/链接/区块/ID 错误；delta-r1 报告 `:180-188` 的 DR-1..DR-9 表可被解析（粗体已由 `:244-248` 容忍）。
- 内容一致性：delta-r1 报告 `:12` 的 WSL 502/0 是 `8de971e` 树（归档前）的实测，不是 `1f6a826` 树；该报告本身不宣称当前树绿色，故不构成归档失真。报告 `:16` 的 Windows 12F/475P/15S 同样是 `8de971e` 树，与计划 `:45` 的 15 同源——这正说明计划 `:34/:134` 的 16 是闭包态数字，未回写 `:45`。
- **归档保真判定：通过（只读；本轮未修改任何归档文件）。**

### 1.9 终审定性小结

- **代码修复全部通过**：DR-2/3/4 的“已根治”有独立变异支撑；DR-5 负例可杀死、正例不破坏幂等；DR-7 输出侧对称、BASE 可复现崩溃、HEAD 修复；DR-9 在位。
- **DR-1 已关闭**：三处控制文档口径回到“进行中/未定”，无“已完成/Zero Blockers/准予交付”残留；计划 `:34/:36` 的绿色宣称转 DR-8 处置。
- **DR-6 历史既有**：登记后续，不阻断。
- **DR-8 部分修复**：473 已清除，但 WSL/Windows 数字、`:45` 的 15、`:35` 的提交号、`:36` 的“无阻断”、“新增失败 0”仍与当前树不符；维持 P2。
- **唯一新增阻断（复核时）**：归档配对键与规定落盘名不兼容，门禁在 `1f6a826` 树 rc=1、全量测试红；按周期基线名登记后探针 C rc=0、闭包态 WSL 503P/0F，证明可修复。
- **闭包后复核**：主调度已执行 §3.3（改名/登记/计划回填）；本人实测门禁 rc=0、WSL 503P/0F；因此 **最终判定 ✅ 准予交付**。上文“维持 P2 / 唯一新增阻断”是复核时（闭包前）快照，保留供追溯。

---

## 2. 最终裁决明细表

| 稳定 ID | 检查点-文件位置 | 原始评级（R1/Delta-r1） | 变更归属 | 终审裁决 | 最终定性分析与裁决理由 | 处置要求 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DR-1 | `docs/index.md:5`、`:15`、`:95`；计划 `:18`；README `:13`；门禁 rc=1 | Delta-r1 🔴 P1 阻断 | 本 diff 修复（缺陷由 `8de971e` 引入） | 降级（阻断→关闭） | 三处已恢复“进行中/未定稿/`--require-verdict=PASS` 尚未通过”，与本批次计划 `:18`、README `:13`、门禁 rc=1 一致；全文 grep 本批次无“已完成/Zero Blockers/准予交付”残留（其余命中属更早批次）。计划 `:34/:36` 的“0 failed/新增失败 0/阻断原因 无”另见 DR-8。 | 无（闭包提交勿再写“已完成”；计划 `:34/:36` 按 DR-8 改写） |
| DR-2 | `manage-doc-index.py:126-143`、`:289`；`test_doc_index_convention.py` | Delta-r1：已根治（R1 原 P1→P2） | 历史既有（R1 轮修复；本 diff 未触碰） | 维持（已根治） | `validate_file_arg` 拒绝空白/`#`/`?`/`(`/`)`，`register_doc:289` 先校验后建索引；非法名 rc=1 且 `index_exists=no`（零写盘）、3 连发 rc=1 幂等；HEAD 定向 40 passed。 | 无 |
| DR-3 | `test_check_review_report.py:229-240` | Delta-r1：已根治（R1 原 P2） | 历史既有（R1 轮修复） | 维持（已根治） | 对 `7a2a3a0` BASE 脚本变异 → 1 failed（断言“嵌套围栏演示请避免行首标记”承重）；HEAD 50 passed，空转已消除。 | 无 |
| DR-4 | `prepare-review-context.py:211-224`；`test_prepare_review_context.py` | Delta-r1：已根治（R1 原 P3） | 历史既有（R1 轮修复） | 维持（已根治） | `git status --porcelain -z` 解析；BASE 变异 6 failed（中文/空格/换行/非 UTF-8/tracked 排除/空归档根/fs 根），HEAD 40 passed；路径原样、不误列 `tracked.txt`。 | 无 |
| DR-5 | `manage-doc-index.py:267-284`、`:280`；`test_doc_index_convention.py:75-81` | Delta-r1 🟡 P3 | 本 diff 修复（缺陷由 `8de971e` 引入） | 降级（P3→关闭） | 正则要求“可选锚点/查询串 + 右括号”收尾；`[x](./a.md`、`[x](./a.md garbage)`、`[x](./a.md "title")`、`[x](./a.md extra)` 均 False，plain/`#install`/`?tab=1`/`#`/`#a?b` 均 True；对 `8de971e` 字面比较变异 1 failed；HEAD 40 passed（含幂等锚点/查询串用例）。 | 保持现正则，勿再放宽；闭包时无需改动 |
| DR-6 | `prepare-review-context.py:239` | Delta-r1 ⚪ P3（历史既有） | 历史既有（`8de971e` 前） | 维持（后续项） | 原始状态块仍直通 `git status -s` 的 C-quote；该行在 `8de971e` 与 `1f6a826` 完全相同，blame 非本 delta；`-z` 结构化路径已由 R1-7 覆盖。 | 登记后续（BK 或备注），本批不修；不得当阻断 |
| DR-7 | `prepare-review-context.py:74`、`:78`、`:247`、`:503-506`；`test_prepare_review_context.py:138-153` | Delta-r1 🟡 P2 | 本 diff 修复（缺陷由 `8de971e` 引入） | 降级（P2→关闭） | 解码侧 `:74` 与输出侧 `:503-506` 均 `surrogateescape`；BASE `--working` rc=1 抛 `UnicodeEncodeError`（`\udcff`，`base-prepare.py:78`），HEAD rc=0、stderr 空、stdout 保留 `bad\udcff.md`；git 原始字节 `bad\xff.md`；Windows 因 POSIX-only 用例 skip（16 vs 15）。 | 无（若要求 Windows 覆盖，另立 POSIX-only 说明，不改实现） |
| DR-8 | 计划 `:34`、`:45`、`:134`、`:35`、`:36`、`:139` | Delta-r1 🟡 P2 | 本 diff 部分修复（缺陷由 `8de971e` 引入） | 降级（P2→关闭） | 复核时（`1f6a826`）数字仍取自非当前树（详见 §1.5）；闭包后主调度已把 `:34/:45/:134` 统一为 WSL 503P/0F、Windows 12F/475P/16S、`:45` 16 skipped，473/15 旧值清除；`:35` 为闭包提交占位符、`:36` 仍留“Delta 复核中”，属 ⚪ 文本残项。DR-8 关闭。 | 闭包提交时替换 `:35` 占位符并把 `:36` 改为“已闭环”；其余无 |
| DR-9 | `skills/dual-round-review/SKILL.md:117-119`、`:169` | Delta-r1 ⚪（在位确认） | 历史既有 | 维持（在位） | `--archive-root` 守卫面已收窄为“空值或文件系统根（含 realpath）”，异常分支 7 与 §1.6 同构；本轮 diff 未触碰，抽查在位。 | 无 |

**表外阻断（无稳定 ID，禁止在 r2 凭空引入新 ID）：** 归档配对键与规定落盘名不兼容（§1.3）。`check-review-report.py:454-459` 规定 R2 新增 ID 必须能在 R1 清单中找到，否则报“稳定 ID 未在 R1 缺陷清单中定义”；因此本项不以新 ID 形式入表，而在 §3 单列并作为交付判定依据。**闭包后该项已由主调度处置（改名/登记），门禁 rc=0；见 §3.4。**

---

## 3. 终审放行结论

### 3.1 统计

- **阻断项统计**: 🔴 **0** / 🟡 **0** / ⚪ **9**。
  - 在案 9 个稳定 ID 全部关闭/确认：DR-1（阻断→关闭）、DR-2/DR-3/DR-4（已根治）、DR-5（关闭）、DR-6（历史既有、后续项）、DR-7（关闭）、DR-8（闭包后关闭）、DR-9（在位）。
  - 复核时（`1f6a826` 树）曾发现 **1 项无稳定 ID 的闭包结构阻断**（归档配对键与规定落盘名不兼容，门禁 rc=1）；主调度已按 §3.3 改名/登记，本人闭包后复核门禁 rc=0、WSL 503P/0F，该阻断已消除（§3.4）。
- **优化建议统计**: **2** 条（非阻断，S1-S2）。
  - S1：计划 `:36` 仍保留“Delta 复核中”字样（闭包后应为“已闭环”）；`:35` 仍是 `CLOSURE_COMMIT_PLACEHOLDER`，闭包提交时替换为真实提交号并回填 §5 的闭包行。二者是文本收口，不影响门禁。
  - S2：`.review-context/review-8de971e.md` 仍是未填模板（`[待填写]`/`未定`），建议在派发/复核时填充；它被 `.gitignore` 忽略，不影响交付。
- **驳回统计**: **0** 条（本报告未驳回任何稳定 ID；DR-6 的“历史既有”降级与 DR-2/3/4/9 的“已根治/在位”均维持，不构成驳回）。

### 3.2 交付判定

**✅ 准予交付**

理由：
1. **代码修复全部通过**：DR-1（三处宣称收口）、DR-5（负例可杀死、正例不破坏幂等）、DR-7（BASE 崩溃可复现、HEAD 对称修复）均关闭；DR-2/3/4/9 独立变异复核维持“已根治/在位”；DR-6 历史既有登记后续；未发现借机重构、新增机制或把 DR-6 当阻断。
2. **闭包结构阻断已消除**：主调度按 §3.3 将 delta-r2 改名为 `delta-r2-7f35a33..1f6a826.md`（与 delta-r1 同基线键；改名时字节与 SHA256 不变），README V1.0.4→V1.0.5 台账/链接/指纹/终审裁决 `✅ 准予交付` 已登记；闭包后实测 `--require-verdict=PASS` rc=0、WSL 全量 **503 passed / 0 failed in 292.39s**、文档四件套全绿。
3. **DR-8 闭包后关闭**：计划 `:34/:45/:134` 已统一为闭包态（WSL 503P/0F；Windows 12F/475P/16S；`:45` 16 skipped），473 与 15 旧值已清除；残留 `:36` 的“Delta 复核中”与 `:35` 的 `CLOSURE_COMMIT_PLACEHOLDER` 仅文本收口（S1），不构成阻断。
4. **边界锁**：本轮 diff 严格限于 DR-1/5/7/8 + 必要校验器容忍度；无越界重构/新机制；DR-6 未被当阻断。

### 3.3 闭包路径（已由主调度执行；复核结果）

1. ✅ 报告改名为 `delta-r2-7f35a33..1f6a826.md`（README `[!NOTE]` 留痕；字节与 SHA256 在改名时不变）。
2. ✅ README 台账/链接/指纹/待办/终审裁决已更新（V1.0.4；v2 采纳后升 V1.0.5）。
3. ✅ 计划 `:34/:45/:134` 数字已按闭包态改写；`:35` 为闭包提交占位符、`:36` 仍留“Delta 复核中”，列为 S1。
4. ✅ 门禁 `--require-verdict=PASS` rc=0；WSL 全量 503 passed / 0 failed；文档四件套全绿。
5. 若未来需保留 `delta-r2-8de971e..1f6a826.md` 名字，则必须改配对键并迁移历史归档——**不推荐**（违背既有同 base 惯例）。

> 结论：**本报告最终判定为 ✅ 准予交付**。复核时（`1f6a826` 树）的 🔴 与 DR-8 P2 是历史快照，已分别由主调度闭包动作与计划回写消除；证据链保留在 §1.3/§1.5/§2，供追溯。**注意**：本报告在闭包后经编辑（v3）；README `:20/:38` 与计划 §5 现登记 v2 指纹（`91283779af60…` / 36135 B），须更新为 v3 的最终字节/SHA256，否则门禁的指纹一致性检查会失败（见 §3.4）。

### 3.4 闭包后复核记录（本人实测）

```bash
python3 -B skills/dual-round-review/scripts/check-review-report.py docs/project/reviews/2026-10-20-p3-six-backlog-batch --require-verdict=PASS
# 结构校验通过: 索引齐备 · 报告 4 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐 · 终审裁决 准予交付  (rc=0；v2 登记态实测。v3 落盘后 README 仍登记 v2 指纹，门禁当前仅报 SHA256 指纹不一致；回填本文件最终指纹后复跑 rc=0，见本节末条)
bash -lc 'cd /mnt/d/workspace/projects/cr-agent-arsenal && python3 -B -m pytest skills/ -q -p no:cacheprovider'
# 503 passed in 292.39s  (0 failed)
```
- 计划 `:34`：闭包态 WSL 503P/0F；Windows 12F/475P/16S（Windows 闭包态本人未重跑，沿用主调度 §5 实测；失败集与 BASE 相同）。
- `docs/index.md:5/:15/:95` 已由主调度在门禁 PASS 后推进为“已完成/准予交付/门禁 PASS”，属合法状态流转；§1.2 的“进行中”是复核时快照。
- 报告自身新指纹：本文件为 v3（复审后终版）；README V1.0.6 与计划 §5 的 delta-r2 行须以 v3 的最终字节/SHA256 回填。

---

## 附录 A：独立取证命令与关键输出

### A.1 指纹与环境
```bash
sha256sum docs/project/reviews/2026-10-20-p3-six-backlog-batch/{r1-7a2a3a0..7f35a33.md,r2-7a2a3a0..7f35a33.md,delta-r1-7f35a33..8de971e.md}
git status --short; git log --oneline -1
```
实测：r1 17780 B / `3ea790f6960b…`；r2 37922 B / `efdaf03adcd3…`；delta-r1 30332 B / `13db2d6d5bab…`；HEAD `1f6a826`，工作树干净。

### A.2 全量与定向
```bash
bash -lc 'cd /mnt/d/workspace/projects/cr-agent-arsenal && python3 -B -m pytest skills/ -q -p no:cacheprovider'
bash -lc 'cd /mnt/d/workspace/projects/cr-agent-arsenal && python3 -B -m pytest skills/dual-round-review/tests skills/doc-governance/tests/test_doc_index_convention.py -q -p no:cacheprovider'
```
- WSL 全量（`1f6a826`）：**1 failed, 502 passed in 186.76s**（collect 503）；唯一失败 `test_existing_archives_all_pass_gate`（`test_artifact_schema_contract.py:131-146`），内容为基线 `7f35a33` 未配 R2 + 结构校验未通过。
- WSL 定向：**1 failed, 160 passed in 44.35s**（同一失败）。
- Windows 全量（`PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8`）：**13 failed, 474 passed, 16 skipped, 28 subtests passed in 228.84s**；13 = 既有 12（doc-governance 5 + spec-evolution 7，见 delta-r1 `:16`）+ 归档门禁 1。
- Windows 定向 `skills/dual-round-review/tests`：1 failed（归档门禁）、117 passed、3 skipped。
- 闭包态副本（`/tmp/headcopy`，同 base 报告 + verdict 准予交付）：WSL 全量 **503 passed in 78.75s**。

### A.3 变异矩阵（临时副本；原仓库零改动）
| 被测脚本 | 变异 | 结果 |
| :--- | :--- | :--- |
| `manage-doc-index.py` | 回退为 `8de971e` 版（字面比较） | `test_doc_index_convention.py` **1 failed**（grammar 用例在 `[x](./a.md` 上 `True is not false`）；HEAD 40 passed |
| `check-review-report.py` | 回退为 `7a2a3a0` 版 | `test_check_review_report.py` **1 failed**（`test_unclosed_fence_message_identifies_report_and_parity`）；HEAD 50 passed |
| `prepare-review-context.py` | 回退为 `7a2a3a0` 版 | `test_prepare_review_context.py` **6 failed**（untracked 列表/中文空格/非 UTF-8/空归档根/fs 根）；HEAD 40 passed |
| `prepare-review-context.py` | 仅取 `8de971e` 版的非 UTF-8 用例 | **1 failed**（`test_untracked_block_preserves_non_utf8_path_without_crash`） |

### A.4 门禁与探针
```bash
python3 -B skills/dual-round-review/scripts/check-review-report.py docs/project/reviews/2026-10-20-p3-six-backlog-batch
# rc=1：错误: 基线 7f35a33 的 R1 报告未配同基线 R2 报告（轮次未闭环，禁止靠他轮 R2 顶包放行）；结构校验未通过
```
- 探针 A（规定名 `delta-r2-8de971e..1f6a826.md` + 台账行）：rc=1，仍报“基线 `7f35a33` 的 R1 报告未配同基线 R2 报告”。
- 探针 B（周期基线名 `delta-r2-7f35a33..1f6a826.md` + 台账行）：rc=0，`结构校验通过: 索引齐备 · 报告 4 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐`。
- 探针 C（B + README `:13` 改“准予交付” + `--require-verdict=PASS`）：rc=0，输出追加 `· 终审裁决 准予交付`。

### A.5 文档四件套（`--root docs`）
| 检查 | 实测 |
| :--- | :--- |
| `check-doc-links.py` | 88 md，0 断链，PASS |
| `check-doc-control-sync.py` | 42 md，0 漂移 |
| `trim-revision.py --keep 5` | 87 文件，0 超限 |
| `audit-doc-health.py` | 100/100 PASS，62 个审查归档按规则跳过 |

### A.6 关键文件行号索引
- `docs/index.md:5/:15/:95`
- `docs/project/plans/2026-10-20-p3-six-backlog-batch.md:18/:31/:34/:35/:36/:45/:134/:139`
- `docs/project/reviews/2026-10-20-p3-six-backlog-batch/README.md:13/:20/:27/:32/:39/:42`
- `skills/doc-governance/scripts/manage-doc-index.py:126-143/:138/:267-284/:280/:289`
- `skills/doc-governance/tests/test_doc_index_convention.py:62-81/:75-81`
- `skills/dual-round-review/scripts/check-review-report.py:94/:244-248/:279-287/:454-459/:477-480/:489-493`
- `skills/dual-round-review/scripts/prepare-review-context.py:74/:78/:239/:247/:494/:503-506/:523`
- `skills/dual-round-review/tests/test_prepare_review_context.py:138-153`
- `skills/dual-round-review/tests/test_check_review_report.py:229-240`
- `skills/dual-round-review/tests/test_artifact_schema_contract.py:131-146`
- `docs/project/reviews/2026-10-20-p3-six-backlog-batch/delta-r1-7f35a33..8de971e.md:12/:16/:180-188/:204/:208`
