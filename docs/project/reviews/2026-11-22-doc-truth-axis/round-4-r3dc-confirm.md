# R3DC-1 根治修复独立确认审查（Round 4）

> **文档控制信息**
> - **文档标识**: REVIEW-R4-R3DC-CONFIRM-doc-truth-axis-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: R3DC-1 根治独立确认审查者（独立上下文，Reviewer ≠ Author）
> - **生效日期**: 2026-11-22
> - **审查对象**: ```f0468f9```（`fix(doc-governance): 根治锚点判据顺序（存在性 → 基线登记 → 形态）`）。`git show f0468f9 --numstat` = `check-doc-drift.py` +21/−2、`test_doc_drift.py` +81、RFC-0005 +3/−3、GOVERNANCE +2/−2、计划 +2/−2、`round-3-delta-confirm.md` +341（新增）
> - **审查基线**: `round-3-delta-confirm.md`（27,365 B，sha256 `7deaf7dbd1975152f0213c42deaf509bb8b04735e7fdd63b785a54051e98cfaa` 实测与派发句柄前 8 位一致）
> - **契约依据（审查时点）**: RFC-0005 **V0.2.1**、GOVERNANCE **V1.7.11**、实施计划 **V1.9.0**（提交 `9ca589f` 的三处 `当前版本` 行实测逐字一致）
> - **取证方式**: 全部本机实跑。夹具建于 `/tmp/r4`（14 个临时 git 仓库 + 1 个 pristine 导出树 + 1 个变异体目录 + 11 个脚本）；旧版对照从 `git show 51e7d6a:` / `git show 940b355:` 导出到 `/tmp/r4/scripts/` 运行；**未改动任何受审文件**
> - **唯一写入面**: 本报告文件。仓库内零改动（`git status --porcelain` 在本报告落盘前为空）；无任何 git 写操作（`init/add/commit/rm` 全部发生在 `/tmp/r4/*` 夹具）
> - **环境**: Linux 6.18.58.1（WSL2）/ Python 3.12.3 / pytest 7.4.4 / git 2.56.1；受审脚本 `check-doc-drift.py` sha256 `193a62078325db7297c157869db4fadc9da16870e012814e38748a57cd6616ff`
> - **未验证项**: Windows 真实文件系统下 `Path.is_file()` 对大小写/反斜杠/UNC 的行为；CI 流水线（仓库无 `.github`，门禁全人工触发）；万篇级文档下逐锚点 `git log` 的耗时；行区间语义（本轴只校验「文件是否变动」，行号仅解析不使用）

---

## 0. 一句话结论

**五项里 4 项通过、1 项不通过**：三次指名事故（`docs/my file.md` / `Makefile:2` / `说明:3`）在「账本已登记该锚点」的前提下**全部真解**，且经变异测试证明回归用例有效；但「**根治**」这一宣称不成立——存在性判据只在文件仍在盘上时生效，基线判据只在账本晚于锚点登记时生效，二者皆否时锚点仍落 `invalid` 并被剔除出判定集。**构造「形态白名单失败 + 盘上不存在 + 基线未登记」的锚点并让它与一条真实 fresh 锚点同文档，实测 `status=fresh` / 真值分 15.0 / `rc=0`**（§1.3.2 场景 X 逐字输出），与 R3DC-1 的失效形态完全同型。故 **Blockers = 1（R4-1，P1）→ 阻断**；另登记 2×P2 + 3×P3 非阻断。

---

## 1. ① 命令与输出

### 1.1 判定矩阵：`normalize_anchor` 直调，prefix(51e7d6a) vs head(f0468f9)

```console
$ python3 /tmp/r4/s12.py            # 22 条锚点形态 × 2 版本
form                   prefix                             head                               change
Makefile:2             path(Makefile,2)                   path(Makefile,2)
LICENSE:3              path(LICENSE,3)                    path(LICENSE,3)
Dockerfile:5-9         path(Dockerfile,5)                 path(Dockerfile,5)
Makefile               path(Makefile,None)                path(Makefile,None)
docs/my file.md        path(docs/my file.md,None)         path(docs/my file.md,None)
中文/文档.md           path(中文/文档.md,None)            path(中文/文档.md,None)
说明:3                 invalid(说明:3,None)               invalid(说明,3)                    CHANGED
附录A:3                invalid(附录A:3,None)              invalid(附录A,3)                   CHANGED
见附录 A               invalid(见附录 A,None)             invalid(见附录 A,None)
见 3.2 节              path(见 3.2 节,None)               path(见 3.2 节,None)
A/B                    path(A/B,None)                     path(A/B,None)
N/A                    path(N/A,None)                     path(N/A,None)
v1.2                   path(v1.2,None)                    path(v1.2,None)
src/**                 unverif(src/**,None)               unverif(src/**,None)
src/a.py:10-20         path(src/a.py,10)                  path(src/a.py,10)
Release Notes          invalid(Release Notes,None)        invalid(Release Notes,None)
设计稿(旧)             invalid(设计稿(旧),None)           invalid(设计稿(旧),None)
说明                   invalid(说明,None)                 invalid(说明,None)
CHANGELOG              path(CHANGELOG,None)               path(CHANGELOG,None)
a@b.py / c+d.py        path                               path
src\a.py               path(src/a.py)                     path(src/a.py)
```

**差分结论**：`normalize_anchor` 的**分类结果零变化**——只有 2 条 invalid 锚点的 `path` 字段被改写（`说明:3` → `说明`、`附录A:3` → `附录A`），它们**仍是 invalid**。也就是说：本次改动**没有**在归一化层新增任何 path↔invalid 迁移，全部行为增量发生在 `analyze()` 的翻转逻辑（`check-doc-drift.py:431-438`）。这一点很重要——它说明「白名单仍是白名单」，被改的只是白名单**失配后的补救顺序**。

### 1.2 ① 三次事故原型：隔离夹具 × 双版本（文件存在 → git rm）

每格一个独立临时 git 仓库：文件与 `seed.txt` 于 2026-11-20 提交 → 文档（`代码锚点: seed.txt, <A>`，`复核于: 2026-11-22`）于 11-21 提交 → 用**该版本自己**写账本 → 跑门禁 → `git rm` 锚点文件（11-23）→ 再跑门禁。`seed.txt` 是「陪跑的真实锚点」，用于复现「invalid 被剔除但整篇仍 fresh」的现场。

```console
$ python3 /tmp/r4/s1.py
########## prefix(51e7d6a) ##########
[docs/my file.md]  wb_rc=0
   EXISTS : rc=0 docs=[('a.md', 'fresh', [])]
   AFTERRM: rc=1 docs=[('a.md', 'missing_anchor', [])]
[Makefile:2]  wb_rc=0
   EXISTS : rc=0 docs=[('a.md', 'fresh', [])]
   AFTERRM: rc=1 docs=[('a.md', 'missing_anchor', [])]
[说明:3]  wb_rc=0
   EXISTS : rc=0 docs=[('a.md', 'fresh', ['说明:3'])]
   AFTERRM: rc=0 docs=[('a.md', 'fresh', ['说明:3'])]        <-- R3DC-1 失效形态逐字复现

########## head(f0468f9) ##########
[docs/my file.md]  wb_rc=0
   EXISTS : rc=0 docs=[('a.md', 'fresh', [])]
   AFTERRM: rc=1 docs=[('a.md', 'missing_anchor', [])]
[Makefile:2]  wb_rc=0
   EXISTS : rc=0 docs=[('a.md', 'fresh', [])]
   AFTERRM: rc=1 docs=[('a.md', 'missing_anchor', [])]
[说明:3]  wb_rc=0
   EXISTS : rc=0 docs=[('a.md', 'fresh', [])]
   AFTERRM: rc=1 docs=[('a.md', 'missing_anchor', [])]        <-- 真解（前提：账本登记过该锚点）
```

`说明:3` 现场逐字输出（HEAD）：

```console
[文件存在]
🔍 文档代码锚点漂移检测: root=/tmp/r4/fx/s13-W/docs repo=/tmp/r4/fx/s13-W
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc= 0
[git rm 后]
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 0｜drifted 0｜missing 1｜stale 0｜unverified 0
🎯 真值分: 0.0 / 15
   - [missing_anchor] a.md  ←  seed.txt, 说明
rc= 1
```

> **注意路径名**：翻转为路径后，明细行显示的锚点名是 `说明`（行区间已被剥掉，`check-doc-drift.py:104-110`），不再回显作者写的 `说明:3`。属可定位性小回退（R4-6，P3）。

### 1.3 ② 静默通道：形态失配 + 盘上不存在 + 基线未登记

#### 1.3.1 六组对照（同一脚本，只改夹具）

```console
$ python3 /tmp/r4/s2.py            # 组 A/B/C/D/F 用 head，E 用 prefix
=== A. 非 ASCII 无扩展名锚点，文件从未存在（混合真实锚点） ===
    BEFORE: rc=0 [('a.md', 'fresh', ['说明'])]      AFTER : rc=0 [('a.md', 'fresh', ['说明'])]

=== B. 关键：文件存在时加锚点，但基线早于锚点（账本滞后窗口）→ 随后删除 ===
    BEFORE: rc=0 [('a.md', 'fresh', [])]            AFTER : rc=0 [('a.md', 'fresh', ['说明'])]     <== 静默

=== C. 对照组：ASCII 带扩展名（gone.txt:2），同样流程 ===
    BEFORE: rc=0 [('a.md', 'fresh', [])]            AFTER : rc=1 [('a.md', 'missing_anchor', [])]

=== D. 对照组：ASCII 无扩展名根文件（Makefile:2），同样流程 ===
    BEFORE: rc=0 [('a.md', 'fresh', [])]            AFTER : rc=1 [('a.md', 'missing_anchor', [])]

=== E. 同一窗口用 prefix(51e7d6a) 跑 ===
    BEFORE: rc=0 [('a.md', 'fresh', ['说明:3'])]    AFTER : rc=0 [('a.md', 'fresh', ['说明:3'])]
```

#### 1.3.2 场景 X 的完整文本输出（HEAD，默认门禁）

夹具步骤：`说明` 与 `seed.txt` 提交（11-20）→ 文档只写 `seed.txt` → `--write-baseline`（账本 = `{"a.md": ["seed.txt"]}`）→ 文档改写成 `seed.txt, 说明:3` 并提交（11-21）→ `git rm 说明`（11-23）→ 跑默认门禁：

```console
🔍 文档代码锚点漂移检测: root=/tmp/r4/fx/s13-X/docs repo=/tmp/r4/fx/s13-X
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
   ⚠️  invalid 锚点（不像路径，无法机械核验；请改写为仓库内相对路径）:
      - a.md: 说明
rc= 0
账本: {'a.md': ['seed.txt']}
```

**结论**：一条**真实存在过、已被删除**的锚点文件，在默认门禁下拿到 **fresh / 15.0 / rc=0**。告警行确实打印了，但它不参与 `blocking`（`check-doc-drift.py:615-621` 只累加 drifted/missing/墓碑/stale/unverified），**rc 仍是 0**——对流水线而言这是静默通过。对照组 C/D 只把锚点写成 ASCII 形态，同一流程即 `missing_anchor/rc=1`，**差别只来自文件名形态**。

#### 1.3.3 「只有这一个锚点」时不洗绿（fail-loud 边界）

```console
$ python3 /tmp/r4/s11.py            # T：a.md 只有 说明:3，账本未登记
    (1, [('a.md', 'unverified', ['说明']), ('b.md', 'fresh', [])])
    text: 📊 声明 2/2 篇｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 1
          🎯 真值分: 7.5 / 15
          - [unverified] a.md  ←  说明
          ⚠️  invalid 锚点（不像路径，无法机械核验；请改写为仓库内相对路径）:
```

即：invalid 锚点是文档**唯一**锚点时落 `unverified`（阻断）；一旦同文档还有一条可判定的 fresh 锚点，整篇就回到 `fresh`。这正是 R3DC-1 事故的成因（文档 = `seed.txt, 说明:3`），本次**未被关闭**。

### 1.4 ③ 基线登记救回逻辑的副作用

#### 1.4.1 glob 登记：没有被误判成路径（符合预期）

```console
$ python3 /tmp/r4/s3.py             # G / P
=== G. 基线登记 src/**，删除 src/ ===
    glob-exists     : rc=0 [('a.md', 'fresh', [])]
    glob-src-deleted: rc=0 [('a.md', 'fresh', [])]
    baseline: {'docs': {'a.md': ['seed.txt', 'src/**']}}
=== P. 文档只有 src/** 一个锚点 ===
    exists : (1, [('a.md', 'unverified', [])])
    deleted: (1, [('a.md', 'unverified', [])])
```

翻转条件带 `anchor.get("invalid")` 门（`:436`），glob 锚点 `invalid=False` ⇒ 永不进入翻转分支 ⇒ 删掉 `src/` 也不会被当成路径判 `missing`。**任务假设的「glob 被当路径判 missing」不成立。** G 组文档仍 fresh 的原因是 glob 属「不可核验」被剔除、同文档 `seed.txt` 可判定且新鲜（R2D56-1 设计），不是翻转副作用。

#### 1.4.2 但散文锚点被账本「登记」后会被翻转成 missing_anchor（**新行为**）

```console
$ python3 /tmp/r4/s3.py             # I
=== I. 散文锚点被基线登记后 ===
    [prefix] baseline: {'a.md': ['seed.txt', '见附录 A']}
    prefix-prose-after-baseline: rc=0 [('a.md', 'fresh', ['见附录 A'])]
    text-rc= 0 | fresh 1｜missing 0 … ⚠️ invalid 锚点…
    [head]   baseline: {'a.md': ['seed.txt', '见附录 A']}
    head-prose-after-baseline  : rc=1 [('a.md', 'missing_anchor', [])]
    text-rc= 1 | fresh 0｜missing 1 … - [missing_anchor] a.md  ←  seed.txt, 见附录 A
```

```console
$ python3 /tmp/r4/s11.py            # U：用当前 HEAD 的 audit 脚本复核
    刷新账本前 audit rc=0 | 声明覆盖: 2/2｜fresh 1｜unverified 1 | 真值分: 7.5 / 15
    刷新账本后 audit rc=0 | 声明覆盖: 2/2｜fresh 0｜missing 2 | 真值分: 0.0 / 15
      - [missing_anchor] a.md
      - [missing_anchor] b.md
```

根因：`write_baseline` 把**每条锚点的 path 原样**写进账本（`:345`，不区分 invalid），于是散文锚点 `见附录 A` 以「路径」身份入账；下一轮 `analyze` 命中 `anchor["path"] in baseline_paths` 即翻转成路径 ⇒ `missing_anchor`。**只要跑一次 `--write-baseline`，全仓所有散文锚点立刻由 fresh(rc=0) 变成 missing(rc=1)，且 invalid 修复提示消失**（`invalid_anchors` 已被清空）。方向是 fail-loud（不产生静默漏检），但属误报 + 判决随账本状态漂移。

#### 1.4.3 锚点写法变更是否误报

```console
$ python3 /tmp/r4/s13.py            # V：说明:3 ↔ 说明
    '说明:3' → '说明': rc=0 status=['fresh'] removed=0
    '说明' → '说明:3': rc=0 status=['fresh'] removed=0
$ python3 /tmp/r4/s4.py             # H2：src/** → src/a.py（glob 改具体路径）
    [prefix] rc=1 removed=1 status=['fresh']
    [head]   rc=1 removed=1 status=['fresh']
```

- 行区间增删（`说明:3` ↔ `说明`）**不误报**——归一路径相同，墓碑多重集不变。
- glob → 具体路径**会**误报墓碑（`removed_from_baseline=1`），但 **prefix 与 head 完全一致** ⇒ 属既有设计（R2D-2 多重集判据），非本轮引入。

#### 1.4.4 迁移：旧账本 + 新脚本

```console
$ python3 /tmp/r4/s8.py             # M
    prefix --write-baseline rc: 0
    账本内容: {'a.md': ['seed.txt', '说明:3']}
    [prefix] rc=0 status=[('a.md', 'fresh', ['说明:3'])] removed=0
    [head]   rc=1 status=[('a.md', 'fresh', [])]         removed=1
    head 文本面: ⛔ 基线墓碑违规（声明被删除/缩减）: | - a.md 缺失: 说明:3
```

旧版账本里 invalid 锚点存的是 `说明:3`，新版归一成 `说明` ⇒ 多重集对不上 ⇒ 升级即红（false red）。本仓账本实测**零此类条目**（§6.2），故当前不受影响；但对任何已启用真值轴的仓库是升级阻断项（R4-3，P2）。

### 1.5 ④ 性能与幂等

```console
$ python3 /tmp/r4/s12.py
=== 探针微基准（精确表达式） ===
单锚点探针 ≈ 37.1 µs → 100 锚点 ≈ 3.71 ms，300 锚点 ≈ 11.14 ms
裸 is_file() ≈ 4.1 µs
=== analyze 端到端（invalid 锚点，零 git 调用），7 次取中位数 ===
N= 100: head=  9.19 ms prefix=  5.18 ms Δ= +4.01 ms
N= 300: head= 20.43 ms prefix=  8.57 ms Δ=+11.86 ms

$ python3 /tmp/r4/s6.py             # 真实锚点：git log 才是大头
git log 单次 ≈ 3.9 ms
analyze 耗时 579 ms, _run_git 调用 150 次        # 150 真实锚点 ≈ 0.58 s

$ python3 /tmp/r4/s4.py             # K / L
=== K. --write-baseline 幂等 ===
    identical: True | content: {'a.md': ['seed.txt', '说明', '见附录 A', 'src/**']}
    gate after baseline: 1 [('a.md', 'missing_anchor', [])]
=== L. --json 稳定性（同状态跑 3 次逐字节比较） ===
    identical across 3 runs: True | bytes: 1301
```

- **per-anchor stat 成本 ≈ 37 µs**（含 `Path` 构造 + 正则剥区间 + 两次 stat），100 锚点 **+4.0 ms**、300 锚点 **+11.9 ms**；而每锚点一次 `git log` 约 **3.9 ms**（150 锚点 ≈ 0.58 s）。**新增开销 < 总耗时的 1%**，规模上无风险。
- 冗余：探针对**所有**锚点执行，但只有 `invalid` 锚点会消费结果（`:432-436`）——把 `probe` 挪进 `if anchor.get("invalid")` 可省掉全部非 invalid 锚点的 37 µs（R4-4，P3）。
- `--write-baseline` 幂等（两次写账本逐字节相同）；`--json` 同状态 3 次输出逐字节相同，字段序稳定（R3DC 报告未覆盖项，本次补验）。

### 1.6 ⑤ 回归面

```console
$ cd /tmp/r4/clean && python3 -m pytest skills/doc-governance/tests -q     # 9ca589f 的 pristine 导出
217 passed in 34.11s

$ cd <repo> && python3 -m pytest skills/doc-governance/tests -q            # 当前 HEAD 0cfdbea
229 passed in 30.62s
# 差额 12 = 8b48bdb 带进来的 test_llms_split.py（与本次审查无关），故 217 与 f0468f9 的宣称一致

$ 变异测试：把 check-doc-drift.py 换回 51e7d6a 版，只跑新增类
python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q -k TestR3DC1ExistenceFirst
FAILED ::test_r3dc_1_baseline_registered_prose_like_path_is_missing_not_invalid
FAILED ::test_r3dc_1_existing_cjk_file_with_line_range_is_a_path
2 failed, 1 passed, 53 deselected in 1.04s
# 第 3 条 test_r3dc_1_prose_still_invalid_when_never_existed 是「防过度矫正」护栏，两版都过 ⇒ 符合预期
```

四道门禁（**审查时点 9ca589f 的 pristine 导出**，与 f0468f9 提交信息同口径）：

```console
$ python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 3/46 篇（覆盖度 6.5%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15                                                        rc=0
$ python3 skills/doc-governance/scripts/check-doc-links.py --root docs
📊 审计汇总: 共扫描 95 个 Markdown 文件 ✅ 100% 物理有效                    rc=0
$ python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
📊 扫描汇总: 共检查 47 个 Markdown 文件 ✅ 100% 一致                        rc=0
$ python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
🏁 诊断结论: PASS (健康度达标，准予交付) ✅                                   rc=0
```

四道门禁（**真实仓库当前 HEAD 0cfdbea**，工作区干净）：

```console
$ git rev-parse --short HEAD && git status --porcelain | wc -l
0cfdbea
0
$ check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 3/54 篇（覆盖度 5.6%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15                                                        rc=0
$ check-doc-links.py --root docs        → 共扫描 103 个 Markdown 文件 ✅     rc=0
$ check-doc-control-sync.py --root docs → 共检查 55 个 Markdown 文件 ✅      rc=0
$ audit-doc-health.py --root docs --repo . → 🏁 PASS                        rc=0
```

> **环境漂移声明（诚实标注）**：审查开始时 HEAD = `9ca589f`（GOVERNANCE V1.7.11，与派发口径一致）；审查进行中分支被并行工作流推进到 `0cfdbea`（`8b48bdb` 分层机器地图 RFC-0006，GOVERNANCE 升至 V1.8.0）。经核：`git diff 9ca589f..0cfdbea -- skills/doc-governance/scripts/check-doc-drift.py` **为空**（sha256 仍 `193a6207…`），受审对象未变；四道门禁的「同口径数字」以 9ca589f 导出为准，0cfdbea 的 3/54、103、55 是文档增量所致，非门禁行为变化。

---

## 2. ② 五项逐条结论

| # | 验收项 | 期望 | 实测 | 结论 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 三次事故原型（含空格 / 行区间 / 非 ASCII+行区间）：文件存在 → fresh + invalid=[]；git rm → missing_anchor + rc=1 | 三形态全绿→红 | `docs/my file.md` 与 `Makefile:2` 两版都通过（前者 R3-1 已修、后者 R3D-1 已修，无回归）；`说明:3` **HEAD 通过、prefix 复现失效**（fresh + invalid + rc=0 两次）；但通过的前提是「账本登记过该锚点」——账本早于锚点时仍失效（§1.3） | ✅ **真解（带前提）** |
| 2 | 构造「白名单失败 + 盘上不存在 + 基线未登记」，确认落 invalid（unverified）而非 fresh；再看默认门禁 rc | 不得洗绿 | 单锚点文档 → `unverified`/rc=1（阻断）；**同文档再挂一条 fresh 锚点 → fresh / 15.0 / rc=0**（场景 X 逐字复现）。对照组 ASCII 形态同流程 rc=1 | ❌ **仍可洗绿 → R4-1** |
| 3 | 基线救回副作用：glob 是否被当路径判 missing；写法变更是否误报 | 不得误判 | `src/**` **永不进入翻转分支**（`invalid=False` 门），删 `src/` 仍 `unverified`，不判 missing；写法变更（`说明:3` ↔ `说明`）不误报；glob→具体路径的墓碑误报 pre-existing。**新发现**：散文锚点经 `--write-baseline` 入账后被翻转成 `missing_anchor`（prefix fresh/rc=0 → head missing/rc=1），invalid 提示同时消失 | ⚠️ **glob 无误判；散文翻转是新副作用 → R4-2** |
| 4 | per-anchor stat 在 100+ 锚点规模下的粗测；`--json` 是否稳定 | 可接受 | 探针 37 µs/锚点：100 锚点 +4.0 ms、300 锚点 +11.9 ms；同规模 `git log` 约 3.9 ms/锚点（150 锚点 0.58 s）⇒ 新增 <1%；`--write-baseline` 幂等、`--json` 3 次逐字节相同 | ✅ |
| 5 | `pytest skills/doc-governance/tests -q`；真实仓库四道门禁 | 全绿 | 9ca589f 导出 **217 passed**（与提交信息一致）；HEAD **229 passed**（+12 为 RFC-0006 新用例）；四门禁：9ca589f → 3/46·15.0·rc=0 / 95 / 47 / PASS；0cfdbea → 3/54·15.0·rc=0 / 103 / 55 / PASS；变异测试 2/3 红（第 3 条为护栏） | ✅ |

---

## 3. ③ 新缺陷

### R4-1 【P1 · Blocker · 同族静默通道未清，非本次引入】账本滞后窗口内，白名单失配的**真实已删锚点**仍落 invalid → fresh / 15.0 / rc=0

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/scripts/check-doc-drift.py:431-438`（翻转只在 `exists_on_disk or path in baseline_paths` 时发生）；`:196-198`（`decidable` 过滤掉 invalid）；`:615-621`（`blocking` 不含 invalid 篇） |
| **现象** | 锚点形态失配白名单（`说明:3` / `Release Notes` / `设计稿(旧)`）→ 文件不在盘上 → 账本未登记 ⇒ 保持 `invalid` ⇒ 退出判定集；同文档另有一条 fresh 锚点时整篇判 `fresh`，真值分 15.0，默认门禁 **rc=0** |
| **证据** | §1.3.2 场景 X 逐字输出（`fresh 1｜missing 0｜unverified 0` / `15.0 / 15` / `rc=0`，告警行仅提示不阻断）；§1.3.1 组 B 与组 C/D 的对照（唯一变量是锚点形态）；§1.2 prefix 列证明这是 R3DC-1 原形态 |
| **为何是 P1 而非 P2** | ① 后果与 R3-1 / R3D-1 / R3DC-1 **完全同型**：真实文件已删、锚点仍被声明、门禁放行、满分；② 触发不需要任何人为篡改，只需「加锚点后忘了重写账本」——而加锚点**不会**触发墓碑检查（只查减少），仓库里没有任何信号提示账本已滞后；③ 本项目已通过派发 f0468f9 明确采纳「任何被判 invalid 的真实路径都等同 R3D-1」的口径（R3DC 报告 §3 的升级条件），本场景正落在该口径内；④ RFC V0.2.1 与提交信息宣称「删除后落 missing_anchor 而非 invalid」，未标注「账本必须晚于锚点登记」这一前提，属**宣称宽于取证** |
| **降级条件（诚实标注）** | 若维护方在 RFC §4.2 把前提写死（「仅对账本已登记的锚点成立」）、撤回「根治」表述、并给提交信息里的「git rm 后 → missing_anchor」补上「账本登记过」限定，则本条可按「契约已声明的已知边界」降为 P2——但届时「根治」二字必须从 GOVERNANCE V1.7.11 行与计划 §9 中删除 |
| **最小修复** | 在 `analyze()` 得到 `status` 后补一行：`if status == "fresh" and any(a.get("invalid") for a in anchors): status = "unverified"`（invalid 锚点存在即禁止满分；对「账本已登记」的文档不产生任何新增红灯，因为它本来就已经是 missing）。补 1 条回归：场景 X 的 6 步夹具，断言 `status != "fresh"` 且 rc≠0 |

### R4-2 【P2 · 非阻断 · 本次引入】散文锚点被 `--write-baseline` 登记后翻转成 `missing_anchor`，判决随账本状态漂移

| 项 | 内容 |
| :--- | :--- |
| **位置** | `write_baseline`（`:339-350`，把每条锚点 path 原样入账，不区分 invalid）+ 翻转分支（`:436`） |
| **现象** | 文档写 `代码锚点: seed.txt, 见附录 A`：刷新账本前 `fresh/rc=0`（invalid 可见）；`--write-baseline` 之后同一棵树零改动 → `missing_anchor/rc=1`，且 `invalid_anchors` 被清空、"请改写为仓库内相对路径"提示消失 |
| **证据** | §1.4.2 的 I 组（prefix vs head 对照）与 U 组（用 HEAD 的 audit 复算：`7.5/15` → `0.0/15`，`unverified 1` → `missing 2`） |
| **影响** | 方向 fail-loud（不产生漏检），但 ① 违反 RFC §4.2「散文锚点归 invalid、不计 missing」的既有语义；② 判决取决于「有没有人跑过 `--write-baseline`」，而非仓库内容，可复现性受损；③ 报错文案把散文当路径，误导作者 |
| **建议** | `write_baseline` 跳过 `invalid` 锚点（不为其立墓碑），或在翻转分支加二次确认；二者择一即可让「invalid 语义」与「墓碑语义」不再互相污染 |

### R4-3 【P2 · 非阻断 · 本次引入】旧账本迁移即红：invalid 锚点 path 被剥行区间后与旧账本多重集不一致

| 项 | 内容 |
| :--- | :--- |
| **位置** | `:104-110`（invalid 分支剥行区间改写 `path`）+ `_removed_from_baseline`（`:353-387`，多重集判据） |
| **现象** | 用 ≤51e7d6a 写的账本含 `"说明:3"`，新版当前声明归一为 `"说明"` ⇒ deficit ⇒ `removed_from_baseline=1` ⇒ rc=1，报「缺失: 说明:3」，而文档一个字都没改 |
| **证据** | §1.4.4 M 组（prefix 写账本 rc=0 → head 跑 rc=1）；反向 N 组（新账本 + 旧脚本）同样红，属对称代价 |
| **影响** | 本仓账本**零此类条目**（§6.2），当前不受影响；但真值轴是通用技能，任何已启用并含非 ASCII 行区间锚点的下游仓库升级即被阻断，且报错指向一个「从未被删除」的锚点 |
| **建议** | 迁移期在 `_removed_from_baseline` 比对前，对两侧 path 做同一套归一（或提供 `--migrate-baseline`）；至少在 RFC 修订记录里写明「升级需重写账本一次」 |

### R4-4 【P3 · 非阻断】`load_baseline` 每次运行读两遍；探针对所有锚点执行但只对 invalid 有用

| 项 | 内容 |
| :--- | :--- |
| **位置** | `:406`（新增预载）与 `:480`（原有读取）；`:432-436`（探针未加 `invalid` 门） |
| **证据** | §1.5：探针 37 µs/锚点，而只有 invalid 锚点会消费结果；账本 JSON 被 `json.loads` 两次 |
| **影响** | 纯开销，100 锚点约 4 ms（<1%），不阻断；但「同一函数里读两遍同一文件」是后续改动的隐患（两份结果可能不一致） |

### R4-5 【P3 · 非阻断】契约与提交信息宽于实现：缺「账本须晚于锚点登记」前提

| 项 | 内容 |
| :--- | :--- |
| **位置** | `docs/proposals/RFC-0005-doc-truth-axis.md` §4.2 判据顺序行；`f0468f9` 提交信息「git rm 后 → missing_anchor（修复前 invalid→fresh）」 |
| **证据** | §1.3.1 组 B/E：账本早于锚点登记时，`git rm` 后仍 `fresh/rc=0`，与提交信息表述相反 |
| **影响** | 下一轮审查者按契约文字复核会得出「已根治」的相反结论；属宣称与取证同宽原则的偏差（AGENTS.md §2） |

### R4-6 【P3 · 非阻断】翻转后明细回显剥掉行区间的锚点名，且 invalid 修复提示消失

| 项 | 内容 |
| :--- | :--- |
| **位置** | `:104-110`（path 只留主体）、`:586-589`（明细用 `a["path"]` 回显）、`:594-599`（invalid 提示依赖 `invalid_anchors`） |
| **证据** | §1.2 文本输出：作者写 `说明:3`，明细显示 `说明`；§1.4.2：翻转后 `invalid_anchors=[]`，提示行整段消失 |
| **影响** | 可定位性回退（与 R3D 已收口的「明细带锚点名」方向相反），仅影响人工排障效率 |

---

## 4. ④ 裁决

### 4.1 计数

| 定级 | 计数 | 编号 |
| :--- | :--- | :--- |
| P0 | 0 | — |
| **P1（Blocker）** | **1** | **R4-1**（账本滞后窗口内白名单失配的真实已删锚点仍 fresh/15.0/rc=0） |
| P2 | 2 | R4-2（散文锚点入账后翻 missing，判决随账本漂移）/ R4-3（旧账本迁移即红） |
| P3 | 3 | R4-4（双读账本 + 探针未设门）/ R4-5（契约宽于实现）/ R4-6（明细与提示回显退化） |

**Blockers = 1（R4-1，P1）。**

### 4.2 裁决：🔴 **阻断（不予准予交付）**

裁决理由（按证据强度排序）：

1. **三项指名事故确实真解，但「根治」不成立**。`docs/my file.md` / `Makefile:2` / `说明:3` 在「账本已登记」流程下全部 `invalid=[]` 且删除即 `missing_anchor/rc=1`（§1.2 head 列），变异测试 2/3 红证明用例有效（§1.6）。这部分做得对，应当保留。
2. **同族静默通道仍在，且可无篡改复现**。场景 X（§1.3.2）：文件存在时加锚点、账本未刷新、随后删除 ⇒ `fresh / 15.0 / rc=0`。对照组只把锚点写成 ASCII（组 C/D）即 rc=1 ⇒ 差异**只来自文件名形态**，正是 R3-1 → R3D-1 → R3DC-1 的同一条因果链，第四次出现。
3. **判据顺序是「补救」而非「优先」**。实现是「先按形态判 invalid，再用存在性/账本把它捞回来」（`:436` 带 `anchor.get("invalid")` 门）；因此「优先级」只在**能被捞回**的两类里成立，第三类（不存在 + 未登记）原样退回白名单。§1.1 的 22 形态矩阵显示归一化层**分类零变化**，可佐证改动没有触及白名单本身。
4. **契约与宣称宽于实现**（R4-5）。RFC V0.2.1 与提交信息都写成「删除后落 missing_anchor」，未标注「账本须晚于锚点登记」。按 AGENTS.md §2「宣称与取证同宽」，这是必须收口的表述缺陷，否则下一轮会按文字判「已根治」。
5. **不能按「不移动球门」放行**。R3DC-1 之所以在上一轮定 P2，理由是「pre-existing + 契约已声明 + 仓库零实例」；而本次提交的**唯一目的**就是消灭该族，且已把「invalid 即等同 R3D-1」写进契约意图。此时残留同类通道若再定 P2，等于承认「根治」是空话——故本轮定 P1。
6. **修复成本极低**（一行判定 + 一条回归），不构成交付阻塞理由，但必须先修再放行。

### 4.3 放行条件（最小集，全部满足即可转 ✅）

1. **R4-1（P1）**：`analyze()` 中「文档含未翻转的 invalid 锚点」时禁止判 `fresh`（落到 `unverified` 即可，默认门禁下 rc=1）；补场景 X 的 6 步回归。**或**：RFC §4.2 写死前提 + 撤回 GOVERNANCE/计划里的「根治」表述 + 修正提交信息口径，二者择一。
2. **R4-2（P2）**：`write_baseline` 不为 invalid 锚点立墓碑（或翻转前做形态二次确认），使「invalid 语义」与「墓碑语义」解耦。
3. **R4-3（P2）**：迁移路径择一——两侧 path 同归一 / 提供 `--migrate-baseline` / RFC 修订记录写明「升级需重写账本一次」。
4. **R4-4/5/6（P3）**：可并入同一提交，不单独阻断。

---

## 5. 残留风险（Top 3）

1. **「invalid」这个桶同时承担了两种语义**：既表示「这是散文，不是路径」（应放行），又表示「这是路径但我认不出来」（应阻断）。只要二者共用一个桶，任何白名单失配都会把第二种误当第一种。R4-1 是其第四次发作；R4-2 是其反向发作（散文被误当路径）。真正的收敛点不是判据顺序，而是**把「无法判定」与「判定为散文」拆成两个状态**，并让前者阻断。
2. **判决依赖账本新鲜度，而账本新鲜度不可自检**。`--write-baseline` 只在人工记得时执行；墓碑判据只查「减少」不查「滞后」，新增锚点没有任何提示。于是「刷新过账本」与「没刷新过账本」的同一棵树会得到 green / red 两种结果（§1.3.2、§1.4.2）。这是比单条缺陷更值得单独立 RFC 的结构问题。
3. **观测面在收窄**：翻转会清空 `invalid_anchors` 并把行区间从锚点名里剥掉（R4-6），R3D 轮刚补上的「明细带锚点名 + invalid 文本可见」在翻转路径上又丢了一半。评审者若只看 `audit` 文本，看到的是「missing 2 篇」而非「2 篇散文锚点无法核验」，归因方向会被带偏。

---

## 6. 附录

### 6.1 夹具清单（全部在 `/tmp/r4`，仓库零写入）

| 路径 | 覆盖 |
| :--- | :--- |
| `/tmp/r4/scripts/drift-{prefix,head,r3d}.py` | 三个版本对照体（sha256 见 §6.3） |
| `/tmp/r4/clean/` | 9ca589f 的 `git archive` pristine 导出（`git init` 后重提交，用于同口径四门禁 + pytest） |
| `/tmp/r4/s1.py` | 三次事故原型 × 2 版本（§1.2），6 个仓库 |
| `/tmp/r4/s2.py` | 静默通道 A/B/C/D/E/F 六组（§1.3.1），6 个仓库 |
| `/tmp/r4/s3.py` | glob / 写法变更 / 散文翻转（§1.4.1–1.4.3），4 个仓库 |
| `/tmp/r4/s4.py` | 墓碑 pre-existing 对照 + 账本幂等 + JSON 稳定（§1.4.3、§1.5） |
| `/tmp/r4/s5.py / s7.py / s12.py` | 性能粗测与形态矩阵（§1.1、§1.5） |
| `/tmp/r4/s6.py` | `_run_git` 计数与 `git log` 单次成本 |
| `/tmp/r4/s8.py` | 旧账本迁移 / 回滚（§1.4.4） |
| `/tmp/r4/s9.py / s10.py / s11.py` | audit truth 块、glob-only、未跟踪锚点、单 invalid 阻断、audit 翻转复核 |
| `/tmp/r4/s13.py` | 逐字取证输出（§1.2、§1.3.2） |
| `/tmp/r4/mut/` | 变异体：51e7d6a 脚本 + HEAD 测试（§1.6） |
| 夹具合计 | **14 个临时 git 仓库** + 1 个 pristine 导出树 + 1 个变异体目录；`/tmp` 内 init/add/commit/rm 共 60+ 次 |

### 6.2 仓库账本实测（确认 R4-3 当前零实例）

```console
$ sha256sum docs/.doc-truth-baseline.json
a9e3b4b7d83e5a16d373a1032be0c24218f6b5b18c603b599c93c89d04eb3b23  docs/.doc-truth-baseline.json
$ cat docs/.doc-truth-baseline.json
{"docs": {"GOVERNANCE.md": ["skills/doc-governance/scripts/audit-doc-health.py",
                           "skills/doc-governance/scripts/check-doc-drift.py"],
          "explanation/architecture/doc-governance-design.md": [ ... 3 条，同上 ... ],
          "project/plans/2026-11-22-doc-truth-axis.md": [ ... 2 条 ... ]}, "version": 1}
# 全部为 ASCII .py 路径，无 invalid、无行区间 ⇒ R4-3 在本仓不触发
```

### 6.3 对照体指纹

```console
3f970a7ee2beab2d10060d98a2daf99f3244ebfbb3a8cf2685483b2cc4d3e190  drift-prefix.py   (= 51e7d6a 版)
193a62078325db7297c157869db4fadc9da16870e012814e38748a57cd6616ff  drift-head.py     (= 仓库内 f0468f9 版，逐字节一致)
21a18229e6a411b69f0689f59cbba108ff45772f24f9a2e133dafbd1d8f7c01b  drift-r3d.py      (= 940b355 版)
1fdf6764bedc08d56ad2a253cfe80dd69d86df61fbc05c746ec736c3cb1bcac6  audit-head.py     (= 9ca589f 版)
```

### 6.4 关键命令（可逐条复跑）

```bash
python3 /tmp/r4/s12.py     # 形态矩阵 + 探针微基准
python3 /tmp/r4/s1.py      # 三次事故原型 × 2 版本
python3 /tmp/r4/s2.py      # 静默通道六组
python3 /tmp/r4/s3.py      # 基线副作用
python3 /tmp/r4/s11.py     # 单 invalid 阻断 + audit 翻转复核
python3 /tmp/r4/s13.py     # 逐字取证输出
# 变异测试
cp -a <repo>/skills/doc-governance/{tests,scripts} /tmp/r4/mut/skills/doc-governance/
git show 51e7d6a:skills/doc-governance/scripts/check-doc-drift.py > /tmp/r4/mut/skills/doc-governance/scripts/check-doc-drift.py
(cd /tmp/r4/mut && python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q -k TestR3DC1ExistenceFirst)
# 回归面
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
```

### 6.5 已排查并主动驳回的疑点

| 疑点 | 结论 |
| :--- | :--- |
| 「存在性探测可被路径穿越利用（`../../x`）」 | 不成立：invalid 分支的 body 必无 `/`、无 `.`（否则走 path 分支），构造不出 `..`；path 分支对 `..` 已返回 None（`:121-122`） |
| 「glob 锚点被当路径判 missing」 | 不成立（§1.4.1）：翻转带 `invalid` 门，glob 是 `unverifiable` 不是 `invalid` |
| 「探针命中目录会误判为 fresh」 | 不会：目录同样进入判定集，未跟踪则落 `unverified`（Q 组实测 rc=1） |
| 「`--json` 输出顺序不稳定」 | 不成立：同状态 3 次逐字节相同（§1.5） |
| 「`--write-baseline` 不幂等」 | 不成立：连续两次写账本逐字节相同（§1.5） |

---

**审查者签名**：R3DC-1 根治独立确认审查者（独立上下文，Reviewer ≠ Author）
**裁决**：🔴 **阻断 —— Blockers = 1（R4-1，P1）**；三次指名事故真解且回归用例有效，但「根治」不成立：账本滞后窗口内，白名单失配的真实已删锚点仍可得 fresh / 15.0 / rc=0。另登记 2×P2（散文锚点入账后翻 missing、旧账本迁移即红）+ 3×P3，均给最小修复。
