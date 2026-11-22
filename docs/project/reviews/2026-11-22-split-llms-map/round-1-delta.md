# RFC-0006 分层机器地图 · S-1~S-5 修复 Delta 复核（Light）

> **审查模式**: LIGHT_DELTA（定向复核：只验六件事，不重开全量红队）
> **审查对象**: `a3be9c9`（fix(doc-governance): 收口分层机器地图红队 S-1~S-5）+ 其后仅文档重钉 `9e8b5a4` / `50013ce`
> **冻结契约**: RFC-0006 **V0.1.1**（AC-1 ~ AC-8）+ 实施计划 §6 偏差登记 **D-01~D-05**
> **上一轮基线**: round-1-light.md（21,904 B，sha256 `19ea6bcdb1c5…`，Blockers=3：S-1/S-2/S-3）
> **审查立场**: Non-Compliant（不采信提交信息中的自证，一切结论以本树复跑为准）
> **只读约束**: 未修改任何被审代码；未执行任何 git 写操作；全部夹具位于 `/tmp/splitdelta/`；除本报告外未落盘任何仓库文件
> **审查者**: split-delta（与实现者、R1 审查者均上下文隔离）

---

## ⓪ 基线与改动面

```console
$ git log --oneline -6
50013ce docs(review): 归档分层机器地图红队报告与轮次台账（Blockers=3）
9e8b5a4 docs(doc-governance): 复核点跟随 a3be9c9 重钉（S-1~S-5 修复后）
a3be9c9 fix(doc-governance): 收口分层机器地图红队 S-1~S-5
f87c99f fix(doc-governance): 收口 R4-1（不可核验锚点不得被 fresh 掩盖）等三项

$ git show --stat a3be9c9
 docs/project/plans/2026-11-22-split-llms-map.md          |   6 +-
 docs/project/reviews/.../round-1-light.md                | 290 ++++++
 docs/proposals/RFC-0006-split-llms-map.md                |   9 +-
 skills/doc-governance/scripts/audit-doc-health.py        | 139 +--------
 skills/doc-governance/scripts/generate-llms-txt.py       |  28 +-
 skills/doc-governance/tests/test_llms_split.py           |  79 ++++++
 6 files changed, 409 insertions(+), 142 deletions(-)
```

`9e8b5a4` 只改 3 处复核点（GOVERNANCE / 设计文档 / 计划），`50013ce` 只加审查归档 README，均不含代码，故全部结论对 `HEAD=50013ce` 成立。

---

## ① 命令与输出

### 1.1 S-1：`--output` 基名与身份闸门读写同源

```console
$ python3 generate-llms-txt.py --root /tmp/splitdelta/s1a/docs --output /tmp/splitdelta/s1a/out/custom.txt
✅ 机器可读地图成功生成至: /tmp/splitdelta/s1a/out/custom.txt (根 442 字节；共 1 个文件)   rc=0
$ find /tmp/splitdelta/s1a/out -type f
/tmp/splitdelta/s1a/out/custom.txt          # 只有 custom.txt
llms.txt 被创建? NO
```

「读 A 写 B」复现（目录内 `llms.txt`=Beta、`other.txt`=Alpha）：

```text
before: llms.txt=[# Beta Machine-Readable Knowledge Base Map]  other.txt=[# Alpha Machine-Readable Knowledge Base Map]
$ ... --output /tmp/splitdelta/s1b/other.txt --name=Alpha
✅ 机器可读地图成功生成至: /tmp/splitdelta/s1b/other.txt (根 441 字节；共 1 个文件)   rc=0
after:  llms.txt=[# Beta Machine-Readable Knowledge Base Map]   other.txt=[# Alpha Machine-Readable Knowledge Base Map]
llms.txt sha256: ab3b3105b543…9a4c → ab3b3105b543…9a4c   （前后一致，未被改写）
```

身份闸门本身仍拦截（读 A 写 A 时拒绝改名）：

```console
$ ... --output /tmp/splitdelta/s1b/llms.txt --name=Alpha
❌ 拒绝改写机器地图身份：既有地图项目名为 'Beta'，本次请求名为 'Alpha'；…   rc=1
llms.txt 首行仍为 Beta
```

补测（`--split` 与 `--check` 是否同样跟随基名）：

```console
$ ... --output /tmp/splitdelta/s1d/out/map.txt --split --name=Demo
✅ … (根 531 字节；共 3 个文件)   rc=0
/tmp/splitdelta/s1d/out/map.txt
/tmp/splitdelta/s1d/out/_llms/proposals.md
/tmp/splitdelta/s1d/out/_llms/reference.md        # 子地图落 <output 目录>/_llms/，llms.txt 未创建
$ ... --output .../map.txt --split --check          → ✅ 校验通过 rc=0
$ （向 map.txt 追加一行后）... --check              → ❌ 机器地图与生成物不一致: llms.txt   rc=1
```

代码位置：`generate-llms-txt.py:486`（`--check` 分支）与 `:508`（写盘分支）均为 `target = out_path if rel == "llms.txt" else base / rel`；`_resolve_outgoing_name(out_path, …)` 读的也是 `out_path` ⇒ **读写同源**。

### 1.2 S-2：重复定义与提示收敛性

```console
$ grep -c '^def check_llms_map_consistency' audit-doc-health.py   → 1
$ grep -c '^def _resolve_project_name'      audit-doc-health.py   → 1
$ grep -c '^def check_agents_md'            audit-doc-health.py   → 1
$ grep -c '^AGENTS_MD_MAX_LINES'            audit-doc-health.py   → 1
$ grep -c '^AGENTS_MD_REQUIRED'             audit-doc-health.py   → 1
$ grep -c '^PROJECT_NAME_FALLBACK'          audit-doc-health.py   → 1
$ grep -c '^REGEN_COMMAND'                  audit-doc-health.py   → 1
```

AST 全量重复扫描（不只上述 7 名）：audit 顶层名 33 个、gen 顶层名 27 个，**重复 = 无**。

收敛性实测（**全仓副本**，避免 /tmp 单拷 docs 导致的 55 处越界断链把得分压到 65.0，从而干扰 PASS 判读）：

```text
副本 /tmp/splitdelta/s2repo（tar 排除 .git / __pycache__，20 MB）
基线:  python3 audit-doc-health.py --root <副本>/docs --repo <副本> --truth off
       总得分 100.0 / 100｜诊断结论 PASS｜rc=0
手改:  echo '- 手改注入' >> <副本>/docs/_llms/proposals.md
       ⛔ 机器地图一致性缺陷: 机器地图与生成物不一致（_llms/proposals.md）—— 请以 --name=System 运行
          generate-llms-txt.py --root docs --output docs/llms.txt --split 重新生成后再提交
       🚫 诊断结论 REJECTED｜rc=1
照做:  generate-llms-txt.py --root <副本>/docs --output <副本>/docs/llms.txt --split --name=System
       ✅ (根 883 字节；共 6 个文件)｜rc=0
再验:  总得分 100.0 / 100｜诊断结论 PASS｜rc=0        ← 收敛
```

提示中同时含 `--split` 与差异明细（`_llms/proposals.md`），`detail` 未再丢失。

### 1.3 S-3：体量门限作用域

```console
$ ... --root docs --output /tmp/splitdelta/s3/single.txt          # 默认模式（= RFC §7 回滚命令）
✅ 机器可读地图成功生成至: /tmp/splitdelta/s3/single.txt (根 22967 字节；共 1 个文件)   rc=0
bytes=22967                                                     # > 8192 仍写出

$ ... --split --name=<9,000 字符长名>  (夹具根 9,527 B)
❌ 根机器地图 9527 字节 > 上限 8192 字节，拒绝落盘。请使用 --split 把条目下沉到 _llms/ 子地图。  rc=1
root written? NO                                                # --split 下默认 8192 仍生效

$ ... --split --max-root-bytes 0 --name=<同长名>
✅ … (根 9527 字节；共 3 个文件)   rc=0                          # 显式 0 关闭闸门

$ ... --max-root-bytes 10   (默认模式显式给上限)
❌ 根机器地图 442 字节 > 上限 10 字节 …   rc=1                    # 显式上限在默认模式仍生效
```

RFC §7 回滚路径（副本目录名保持 `docs`，否则描述里 `../../docs/…` 的越界链接会退化，产物变 22,920 B）：

```console
$ rm -rf <副本>/docs/_llms && ... --root <副本>/docs --output <副本>/docs/llms.txt
✅ (根 22967 字节；共 1 个文件)   rc=0
$ cmp <副本>/docs/llms.txt /tmp/splitdelta/s3/single.txt   → 逐字节一致
```

代码位置：`generate-llms-txt.py:472` `root_limit = args.max_root_bytes if args.max_root_bytes is not None else (8192 if args.split else 0)`。

### 1.4 S-4 / S-5

S-4 夹具（同一篇描述的 7 类链接，split 子地图与默认单文件双跑）：

```text
split : - [A](../proposals/a.md): 电话 [t](tel:123) 文件 [f](ftp://h/x.txt) 协议相对 [p](//cdn.example/y.md)
        数据 [d](data:text/plain,hi) 邮件 [m](mailto:a@b.c) 站点 [s](https://e.com/z) 锚 [a](../proposals/a.md#sec) 相对 [r](../proposals/b.md)
single: … [t](tel:123) [f](ftp://h/x.txt) [p](//cdn.example/y.md) [d](data:text/plain,hi) [m](mailto:a@b.c) [s](https://e.com/z) …
```

断言矩阵（`grep -qF "($tok)"`）：`tel:` / `ftp://` / `//cdn.example/y.md` / `data:` / `mailto:` / `https://` 六类在 **split 与 single 两侧均 KEEP（逐字未改写）**；相对链接 `./b.md` 正常 rebase 为 `../proposals/b.md`（split）/ `proposals/b.md`（single）；纯片段 `#sec` 按设计解析为源文档自身。

S-5：

```text
基线（split 一致）                                     → ''
塞入 _llms/sub/sneaky.md                              → 机器地图与生成物不一致（_llms/sub/sneaky.md）… --split …
同一棵树 generate-llms-txt.py --split --check          → ✅ 校验通过（3 个文件）rc=0   ← 双门口径分裂
照 audit 提示重生成（--split，非 --check）             → nested stray 仍在 → audit 仍报同一缺陷   ← 不收敛
对照：顶层 _llms/stray.md                              → 重生成后文件被删除 → audit 转 ''        ← 收敛
_llms/notes.txt（非 .md）                              → ''（契约未要求，保持原状）
_llms/sub → 外部目录（符号链接）                        → ''（rglob 不跟随目录符号链接，仍为静默区）
```

### 1.5 S-7：AC-1 用例是否仍同义反复

用例本体（`tests/test_llms_split.py:54-64`）仍是 `build_llms_map(split=False)` 对比 `generate_llms_txt(...)`，而后者（`generate-llms-txt.py:314`）**内部调用前者**。

变异实验（`/tmp/splitdelta/mut`，只改副本，不碰仓库）：

| 变异 | 内容 | 结果 |
| :--- | :--- | :--- |
| M1 | 改 `_render_single` 的固定文案（渲染层） | `-k ac1` → **1 passed**（用例无法感知渲染层变化 ⇒ 同义反复成立） |
| M2 | 落点回退为 `base / rel`（S-1 旧行为） | `test_s1_custom_output_basename_is_honoured` **FAILED**（新用例有承重） |
| M3 | `root_limit` 回退为恒 8192（S-3 旧行为） | `test_s3_default_mode_has_no_byte_limit` **FAILED**（新用例有承重） |

独立 oracle（R1 已指出可用、本轮实测可用）：

```console
$ git show 9ca589f:skills/doc-governance/scripts/generate-llms-txt.py > /tmp/splitdelta/oracle/old_gen.py   # 17,644 B
$ python3 old_gen.py --root <副本>/docs --output old.txt   → rc=0 (94 篇)
$ python3 现版      --root <副本>/docs --output new.txt    → rc=0 (22,967 B)
$ cmp old.txt new.txt                                      → O1: BYTE-IDENTICAL (22,967 B)
```

但 oracle 同时暴露 S-4 修复对**默认模式**的波及（描述含 `//host` 的夹具）：

```text
old: - [A](proposals/a.md): 协议相对 [p](cdn.example/y.md) …      # 440 B，协议相对 URL 被降级成断链相对路径
new: - [A](proposals/a.md): 协议相对 [p](//cdn.example/y.md) …     # 442 B，原样保留（正确）
O2: DIFF (440 → 442)
```

即：S-4 改的是 `ABSOLUTE_LINK_PATTERN`（`:31`，双模式共用），因此默认模式在该输入类上**不再是「逐字节同产物」**；真实 docs 无此类描述，O1 仍逐字节一致。

### 1.6 回归面

```console
$ python3 -m pytest skills/doc-governance/tests -q
241 passed in 21.72s

$ check-doc-links.py --root docs            → 103 个 Markdown / 零 404            rc=0
$ check-doc-control-sync.py --root docs     → 55 个 Markdown / 无版本漂移          rc=0
$ check-doc-drift.py --root docs --repo . --fail-on-drift
  声明 3/54 篇｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0｜真值分 15.0/15   rc=0
$ audit-doc-health.py --root docs --repo .  → 总得分 100.0 / 100｜PASS             rc=0
$ generate-llms-txt.py --root docs --output docs/llms.txt --split --check
  ✅ 机器地图校验通过（6 个文件，根 883 字节）                                      rc=0

$ wc -c docs/llms.txt
883 docs/llms.txt        # sha256 93ff31b7912719afb5cc0fc074d97b3758183300a6a8094e08e56720c5016f1e
$ wc -c docs/_llms/*.md  → explanation 4,618 / other 538 / project 15,060 / proposals 1,883 / reference 1,465（5 个）
$ git status --porcelain → 0 项（写入本报告前）
```

---

## ② 六项结论

| # | 待验项 | 结论 | 证据 |
| :--- | :--- | :--- | :--- |
| 1 | S-1 真解 | **成立** | 自定义基名落 `custom.txt` 且不产 `llms.txt`；`llms.txt`=Beta / `other.txt`=Alpha 场景下执行 `--output other.txt --name=Alpha` 后 `llms.txt` sha256 未变；`--split` 子地图落 `<output 目录>/_llms/`；`--check` 同样跟随基名 |
| 2 | S-2 真解 | **成立** | 7 个符号 `grep -c` 全为 1，AST 全量无重复；提示含 `--split` + 差异明细；照做后 audit 由 REJECTED 转 **PASS（100.0）**，闭环收敛 |
| 3 | S-3 真解 | **成立** | 默认模式真实 docs `rc=0 / 22,967 B`（>8192）；`--split` 下默认 8192 仍拒写（9,527 B 夹具）；`--max-root-bytes 0` 关闭闸门；显式上限在默认模式仍生效；RFC §7 回滚命令实测可用且与默认模式产物逐字节一致 |
| 4 | S-4 / S-5 | **S-4 成立；S-5 检测侧成立、清理侧残留** | `tel:`/`ftp:`/`//host`/`data:` 双模式逐字保留；`_llms/sub/x.md` 被判多余。但生成器 `--check` 与写盘清理仍只 `glob` 一层 ⇒ 提示不收敛、双门口径分裂（SD-1） |
| 5 | S-7 是否仍同义反复 | **仍同义反复（P2 维持）** | M1 渲染层变异后 `-k ac1` 仍 1 passed；独立 oracle（`9ca589f`）存在且实测可用（O1 逐字节一致），但未入测 |
| 6 | 回归面 | **通过** | 241 passed；五道门禁 rc=0；真实 docs 根 883 B、5 个子地图；工作树干净 |

**补充判读**：S-1 的修复顺带把「身份闸门读 A 写 B」这一 BK-0030 旁路关闭，且未削弱闸门本身（改名仍 fail-closed）；S-3 的修复没有把体量闸门整体废掉——`--split` 下默认值、显式值、`0` 语义三者自洽。

---

## ③ 新缺陷

> 定级口径同 R1：P0 = 数据损坏/不可恢复；P1 = 契约违反或不可收敛的修复闭环；P2 = 局部错误/静默降级；P3 = 文案与卫生。**仅 P0/P1 计入 Blockers。**

### SD-1 · P2 · S-5 只修了检测侧：嵌套多余文件不收敛，且 audit 与 `--check` 口径分裂

- **代码**：audit `:280` 已改 `section_dir.rglob("*.md")`；生成器 `:493`（`--check` 多余集合）与 `:516`（写盘后清理）仍是 `section_dir.glob("*.md")` 单层。
- **实测**：`_llms/sub/sneaky.md` 存在时 —— audit 判「不一致（`_llms/sub/sneaky.md`）」，`--check` 判「校验通过 rc=0」；照 audit 提示重生成后 nested 文件仍在，audit 仍红（顶层 `_llms/stray.md` 则会被清理并转绿）。
- **后果**：① 同一棵树上两道门禁结论相反，CI 里 `--check` 绿、audit 红；② audit 下发的命令对该类缺陷不可收敛，用户只能手工 `rm`。触发需人为构造 `_llms/` 子目录，故维持 P2（R1 对 S-5 的原始定级），不计入 Blockers。
- **修法**：生成器两处同步改 `rglob`，或把「`_llms/` 下允许集合」抽成单一函数供 audit / `--check` / 写盘清理共用。

### SD-2 · P2 · AC-1 用例仍同义反复（R1 S-7 未修）

- **证据**：`tests/test_llms_split.py:54-64` 仍是新函数对「已改为调用新函数的旧入口」；M1 变异（改 `_render_single` 固定文案）后该用例仍 passed。
- **后果**：渲染层漂移无自动化防线；命令层已被 `test_s1`/`test_s3` 补上（M2/M3 变异即红），故承重缺口较 R1 收窄，但 AC-1 这一条验收仍无独立证据。
- **修法（成本极低）**：把 `git show 9ca589f:…/generate-llms-txt.py` 固化为 `tests/fixtures/legacy_generate_llms_txt.py`（17,644 B），对同一夹具双跑 `cmp`，并显式加限定「树中不含 `_llms/`」。

### SD-3 · P3 · `--check` 不一致信息回显逻辑名而非实际落点

- `--output …/map.txt --split --check` 在根被改动后输出 `❌ 机器地图与生成物不一致: llms.txt`，而实际文件是 `map.txt`（`:486` 收集的是 `rel`）。S-1 修好落点后，这条文案成了残留的「读 A 写 B」式表述。建议根项回显 `str(out_path)`。

### SD-4 · P3 · RFC §4.3「兼容」行被 S-4 修复打破，V0.1.1 未登记

- 契约仍写「无 `--split` 时行为与现行完全一致（单文件、逐字节同产物）」，但 `ABSOLUTE_LINK_PATTERN`（`:31`）双模式共用，含 `//host` 描述时默认模式产物由 440 B 变 442 B（O2）。新行为是正确的，缺的是契约限定语；建议改为「除 `//host` 描述外逐字节同产物」或在 AC-1 加注。

### SD-5 · P3 · `_llms/` 下的符号链接子目录仍是静默区

- `ln -s <外部目录> docs/_llms/sub` 后，`rglob`（Python 3.12 pathlib）不递归符号链接目录，audit 返回 `''`。实际危害有限（链接目标内容不在仓库内），但「`_llms/` 下只允许扁平产物」的判据仍未闭合；建议对 `section_dir` 做 `os.walk(followlinks=False)` 并单独判「非目录 / 符号链接」项。

### SD-6 · P3 · RFC §4.5「根体量超限计入缺陷」audit 侧未实现（既有缺口，非本轮引入）

- `grep -n '8192\|root_bytes' audit-doc-health.py` → 无命中；audit 只做逐字节比对。因根被撑大必然导致内容不一致，实际无静默洞，但 §4.5 的承诺仍无对应实现；V0.1.1 修订时未登记为偏差（D-01~D-05 未覆盖）。
- **卫生残留**：删除重复块后 `audit-doc-health.py:314-317` 留有 4 连空行，建议顺手压平（不计级）。

---

## ④ 裁决

| 编号 | R1 评级 | Delta 复核 | 证据强度 | 计入 Blocker |
| :--- | :--- | :--- | :--- | :--- |
| S-1 | P1 | **已真解** | 落点 + 身份闸门双场景实测 | — |
| S-2 | P1 | **已真解** | 定义唯一 + 照提示命令后 audit 转 PASS | — |
| S-3 | P1 | **已真解** | 默认 rc=0/22,967 B + split 默认 8192 + 回滚逐字节一致 | — |
| S-4 | P2 | **已真解** | 6 类 scheme 双模式逐字保留 | — |
| S-5 | P2 | **部分修复** | 检测侧成立；清理侧与 `--check` 未同步（SD-1，P2） | ❌ |
| S-7 | P2 | **未修（维持 P2）** | M1 变异仍绿（SD-2） | ❌ |

### 裁决：**准予（Blockers = 0）**

三条 P1 全部真解且可复现；两条 P2 中 S-4 真解、S-5 的检测面真解（残留清理面不收敛，SD-1 定 P2，按「仅 P0/P1 计入 Blockers」不计入阻断）；回归面 241 passed、五道门禁全绿、真实 docs 根仍 883 B。

**准予交付的非阻断跟进（建议下一提交收口，不必再开红队轮次）**：

1. SD-1：生成器 `--check` 与写盘清理改 `rglob`（或抽公共「`_llms/` 允许集合」函数），让 audit 与 `--check` 同口径、提示可收敛。
2. SD-2：把 `9ca589f` 旧生成器固化为 golden 夹具，给 AC-1 一个独立 oracle。
3. SD-4：修 RFC §4.3 兼容行的限定语；SD-3/SD-5/SD-6 按 P3 排期。

**台账交接**：本报告为 R1 之后的 Delta 复核，README 轮次台账的 Delta 行与「终审裁决」由主调度智能体按本报告结论登记（本审查者只读，不改台账）。

---

## 残留风险（≤3）

1. **`_llms/` 清理面与检测面尚未同口径**：嵌套多余 `.md` 会让 audit 常红而 `--check` 常绿，提示命令不收敛；符号链接子目录仍可绕过递归扫描（SD-1 / SD-5）。
2. **AC-1 无自动化独立 oracle**：渲染层回归仍只能靠人工 `git show 9ca589f` 复算；且 S-4 的修复已使「默认模式逐字节同产物」在 `//host` 描述上不再成立，契约文本尚未限定（SD-2 / SD-4）。
3. **契约-实现仍有未登记偏差**：RFC §4.5 的根体量判据在 audit 侧不存在，V0.1.1 未在 D 台账登记；后续若有人只读契约即认定该门禁已生效，会误判防线宽度（SD-6）。
