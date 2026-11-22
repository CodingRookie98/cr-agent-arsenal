# RFC-0006 分层机器地图 · 第一轮红队审查（Light）

> **审查模式**: LIGHT_REVIEW（单轮 R1 + 轻量裁决）
> **审查对象**: `git diff 9ca589f..HEAD -- skills/`（实现提交 `8b48bdb`；审查期间 HEAD 由 `0cfdbea` 前进到 `f87c99f`，但 `generate-llms-txt.py` 与 `audit-doc-health.py` 自 `0cfdbea` 起**逐字节未变**，故全部结论对当前 HEAD 同样成立）
> **冻结契约**: [RFC-0006](../../../proposals/RFC-0006-split-llms-map.md)（AC-1 ~ AC-8）+ [实施计划](../../plans/2026-11-22-split-llms-map.md) §5
> **审查立场**: Non-Compliant（默认「实现宣称不成立」，一切结论以复算为准）
> **只读约束**: 未修改任何代码；未执行 git 写操作；除本报告外未落盘任何文件
> **审查者**: split-redteam（与实现者上下文隔离）

---

## ① 命令与输出

### 1.1 基线与改动面

```console
$ git log --oneline 9ca589f..HEAD          # 审查开始时止于 0cfdbea，收尾时为 f87c99f
f87c99f fix(doc-governance): 收口 R4-1（不可核验锚点不得被 fresh 掩盖）等三项
0cfdbea docs(doc-governance): 复核点跟随 8b48bdb 重钉（分层机器地图落地后）
8b48bdb feat(doc-governance): 分层机器地图（RFC-0006）—— 根 llms.txt 降为象限入口

$ git diff --quiet 0cfdbea..f87c99f -- skills/doc-governance/scripts/generate-llms-txt.py \
                                       skills/doc-governance/scripts/audit-doc-health.py
UNCHANGED since 0cfdbea

$ git diff --stat 9ca589f..HEAD -- skills/
 skills/doc-governance/SKILL.md                     |   6 +-
 skills/doc-governance/references/change-impact-matrix.md |   3 +-
 skills/doc-governance/scripts/audit-doc-health.py  | 220 ++++++++++++++++++++-
 skills/doc-governance/scripts/generate-llms-txt.py | 183 +++++++++++++++--
 skills/doc-governance/tests/test_llms_split.py     | 188 ++++++++++++++++++
 5 files changed, 566 insertions(+), 34 deletions(-)

$ wc -c docs/llms.txt docs/_llms/*.md ; wc -l docs/AGENTS.md
  883 docs/llms.txt
 4618 docs/_llms/explanation.md
  538 docs/_llms/other.md
15060 docs/_llms/project.md
 1883 docs/_llms/proposals.md
 1465 docs/_llms/reference.md
   28 docs/AGENTS.md
```

实测子地图 **5 个**（tutorials / how-to 为空，按 AC-4 不产子文件）、条目合计 **94 条**（12+1+70+6+5），与根中「6/5/12/70/1 篇」逐项吻合。

### 1.2 AC-1：默认模式与旧实现逐字节对比（独立 oracle，不复用新实现）

```console
$ git show 9ca589f:skills/doc-governance/scripts/generate-llms-txt.py > /tmp/r6rt/old_gen.py   # 17,644 B
$ cp -a docs /tmp/r6rt/ac1/docs && rm -rf /tmp/r6rt/ac1/docs/_llms      # 保持 docs 根在仓库同深度
$ python3 /tmp/r6rt/old_gen.py --root .../docs --output old.txt          # rc=0
$ python3 skills/.../generate-llms-txt.py --root .../docs --output new.txt --max-root-bytes 0
$ cmp old.txt llms.txt
AC1_REAL_DOCS_BYTE_IDENTICAL (22967 B)
```

夹具矩阵（同一 old/new 双跑，`build_llms_map(split=False)` 直接比对旧产物）：

| 夹具 | 内容 | 结果 |
| :--- | :--- | :--- |
| F1 空描述 / 无描述 / other 象限 / 根级文件 | `描述:` 空串、无描述行、`misc/stray.md`、`index.md`、`GOVERNANCE.md` | **逐字节一致**（410 B） |
| F2 含链接描述 | `](./b.md)`、`](c.md)`、`https://…`、`#sec`、`../../index.md`、`../../../outside.md`、`ftp://`、`mailto:` | **逐字节一致** |
| 真实 docs（94 条，含 2 处描述内链接） | 上列 22,967 B | **逐字节一致** |

结论：**渲染层零破坏**（`_render_single` 与旧 `generate_llms_txt` 同源）。但「命令层」不成立，见 S-3。

### 1.3 链接正确性夹具（split 模式）

```text
- [A](../reference/api/a.md): 见 [B](../reference/api/b.md) 与 [C](../reference/api/c.md) 以及 [站点](https://example.com/x) 和 [锚](../reference/api/a.md#sec)
- [RFC9](../proposals/RFC-9.md): 上跳 根、越界 外、协议 [ftp](../ftp://h/x.txt)、邮件 [m](mailto:a@b.c)
```

真实 docs 全量链接解析（自写解析器，不复用 check-doc-links）：

```text
root: ./_llms/{proposals,reference,explanation,project,other}.md -> 全部 OK
sub-maps: broken links: none      # 94 条条目链接 + 全部描述内链接
```

### 1.4 门禁绕过矩阵（audit 一致性）

| # | 篡改手法 | `check_llms_map_consistency` |
| :-- | :--- | :--- |
| S1 | 手改子地图 | **判不一致** ✅ |
| S2 | 删除子地图 | **判不一致** ✅ |
| S3 | 新增多余子地图（`_llms/stray.md`） | **判不一致** ✅ |
| S4 | 根换成单文件旧格式 + 保留 `_llms/` | **判不一致** ✅ |
| S4b | 根单文件 + 删 `_llms/`（回滚态） | 一致（合法回滚态，符合预期） |
| S5 | 真实文档塞进 `_llms/sub/real.md`（嵌套） | **静默放行** ❌ |
| S5b | 真实文档塞进 `_llms/real-doc.md`（顶层） | 判不一致 ✅ |
| S6 | `_llms/notes.txt`（非 .md） | 静默放行（可接受，但见 S-5） |
| S7 | 根 `llms.txt` 直接删除 | 静默放行（`llms_map_issue` 为空） |
| S8 | split 根 + 删除 `_llms/` | 判不一致 ✅ |

### 1.5 体量门禁与 `--check` 写盘面

```console
$ ... --split --max-root-bytes 10            # 预置陈旧子地图 + 删除根
rc=1  ❌ 根机器地图 656 字节 > 上限 10 字节，拒绝落盘…
根存在? NO        子地图 sha 未变 (4a4346b1…)

$ ... --split --check                        # 已手改子地图 + 多余 stray.md
rc=1  ❌ 机器地图与生成物不一致: _llms/proposals.md, _llms/stray.md
树指纹一致? YES   stray 仍在? YES            # 不写盘、不删多余文件
```

### 1.6 豁免副作用 A/B（同一文件、两个落点）

```text
基线（docs 副本）                        : 65.0 / 100
+ docs/_llms/sub/real-knowledge.md       : 65.0 / 100   该文件名出现 0 次
+ docs/reference/tmp/real-knowledge.md   : 64.6 / 100   该文件名出现 2 次，并触发「机器地图不一致」
```

（`/tmp` 副本会放大断链数，故只看**同树增量**：`_llms/sub/` 内文件对分数与提示的贡献恒为 0。）

### 1.7 回归面

```console
$ python3 -m pytest skills/doc-governance/tests -q
235 passed in 22.93s          # @f87c99f，连跑两次一致
229 passed in 23.07s          # @0cfdbea（首轮）；f87c99f 的 test_doc_drift.py +6 例即差值来源

$ generate-llms-txt.py --root docs --output docs/llms.txt --split --check
✅ 机器地图校验通过（6 个文件，根 883 字节）        rc=0

$ check-doc-links.py --root docs
共扫描 103 个 Markdown 文件 / 零 404               rc=0

$ check-doc-control-sync.py --root docs
共检查 55 个 Markdown 文件 / 无版本漂移             rc=0

$ check-doc-drift.py --root docs --repo . --fail-on-drift
声明 3/54 篇｜fresh 3｜drifted 0｜stale 0｜真值分 15.0/15   rc=0

$ audit-doc-health.py --root docs --repo .
总得分 100.0/100（门槛 80）｜孤儿 0/96｜PASS        rc=0
```

---

## ② 六项结论

### 2.1 默认模式零破坏（AC-1）—— **产物通过，命令不通过**

- `build_llms_map(split=False)` 与 9ca589f 的 `generate_llms_txt` 在三类夹具 + 真实 docs（22,967 B）上**逐字节一致**，渲染层零破坏成立。
- 但 `--max-root-bytes` 默认 8192 **对所有模式生效**：默认模式在 >8 KB 树上从「rc=0 写出」变为「rc=1 不落盘」。**该行为变更未在 RFC / GOVERNANCE / SKILL 任何一处登记**，且使 RFC §7 的回滚路径失效（S-3）。
- 另：`build_llms_map(split=False)` 在**含 `_llms/` 的树**上与旧实现不再一致（新实现跳过 `_llms`，RFC §4.3 有意为之）。AC-1 的「逐字节相同」因此只在「无 `_llms/`」前提下成立，契约文本未加限定（S-9）。

### 2.2 链接正确性 —— **主路径通过，非 http(s) scheme 不通过**

- 条目链接 `../<docs 根相对路径>` 与描述内链接 rebase 在 `./x.md`、`y.md`、`#sec`、`https://`、越界降级五类夹具上**全部可解析**；真实 docs 94 条零断链；`_llms/*.md` 已被 `check-doc-links` 覆盖（103 篇）。
- **缺陷**：`_rebase_desc_links` 的排除白名单只有 `http(s)://`、`mailto:`、`#`，其余 scheme 与协议相对 URL 被当成相对路径改写 → `[t](tel:123)` 变 `[t](../tel:123)`、`[p](//cdn/x.md)` 变 `[p](../cdn/x.md)`，**静默断链**（S-4）。
- **契约矛盾**：RFC §4.2 要求子地图链接「相对 docs 根」，实现写 `../`（这是唯一可解析形态）；契约文本与实现互斥（S-6）。

### 2.3 门禁是否可被绕过 —— **四种指定手法全部拦截，但存在一类新静默区**

- 手改 / 删子地图 / 多余子地图 / 根换单文件旧格式（保留 `_llms/`）：**四种全部判不一致** ✅（AC-6 / AC-7 成立）。
- **但提示的修复命令不可用**：audit 给出 `generate-llms-txt.py --root docs --output docs/llms.txt`（**无 `--split`**）。照做：小树上 rc=0 写出单文件根 → 再跑 audit **仍报同一缺陷**；真实 docs 上直接 rc=1（22,967 B > 8192）。修复命令**必然不收敛**（S-2，AC-6 违反）。
- 新增静默区：`_llms/` **嵌套子目录**内的真实文档对生成器、audit 元数据/孤儿计分、子地图多余集合判据**三重不可见**（S-5）。根 `llms.txt` 被删除时一致性项直接「不适用」（S-7 残留）。

### 2.4 体量门禁 —— **通过**

- `--max-root-bytes 10`：根不落盘、**子地图一字节未动**、无空目录残留（AC-5 成立）。
- `--check`：树指纹（全文件 sha 集合）运行前后**完全一致**，多余子地图**不被删除**，rc=1 且给出差异明细（AC-3 校验语义成立）。
- 边角：`--max-root-bytes 0` 会静默关闭闸门（`if args.max_root_bytes and …`），负值则恒拒；默认模式 `--check` 超限时输出「拒绝落盘」而 `--check` 本不落盘（S-8/S-10）。

### 2.5 豁免副作用 —— **顶层可控，嵌套形成静默区**

- `_llms/*.md` 顶层新增文件会被「多余子地图」判据拦住（S5b）；`docs/AGENTS.md` 仅受 ≤30 行 + 两个必需小节约束，30 行内可塞任意文本（RFC 设计如此，可接受）。
- **不可接受面**：`_llms/` 下的嵌套目录、非 `.md` 文件既不被生成器收录、也不被 audit 计分、也不被多余集合判据覆盖（`section_dir.glob("*.md")` 只有一层）。A/B 实测：同一篇无控制头文档放 `_llms/sub/` 分数与提示**零变化**，放 `reference/tmp/` 立刻降分并触发漂移（S-5）。

### 2.6 回归面 —— **通过**

`pytest` 229 passed @0cfdbea / 235 passed @f87c99f（差值 6 例来自 `f87c99f` 新增的 `test_doc_drift.py`）；四道门禁 + `--split --check` 全 rc=0；audit 100/100 PASS、孤儿 0/96。**测试绿但漏网**：AC-1 的自动化用例是同义反复（新函数对比已被改为调用新函数的旧入口），无法拦住 S-1 / S-3 这类命令层回归（S-9）。

---

## ③ 新缺陷

> 定级口径：P0 = 数据损坏/不可恢复；P1 = 契约违反或不可收敛的修复闭环；P2 = 局部错误/静默降级；P3 = 文案与卫生。**仅 P0/P1 计入 Blockers。**

### S-1 · P1 · `--output` 基名被丢弃，身份闸门读 A 写 B

- **证据（代码）**：`skills/doc-governance/scripts/generate-llms-txt.py:499-503` —— `base = out_path.parent`、`for rel, content in built.items(): target = base / rel`，而 `rel` 恒为 `"llms.txt"`（或 `_llms/<sec>.md`），**`out_path.name` 从未参与落点**。`--check`（:475-489）同锚定，自洽但校验的不是请求路径。
- **证据（实测）**：
  ```text
  OLD: --output /tmp/o1/custom-map.txt  -> 生成 custom-map.txt           (rc=0)
  NEW: --output /tmp/o3/custom-map.txt  -> 生成 /tmp/o3/llms.txt         (rc=0，stdout 仍宣称写到 custom-map.txt)
  ```
- **后果**：① 静默写到错误路径并谎报落点；② `_resolve_outgoing_name` 读的是 `out_path`、写的是 `base/llms.txt` ⇒ **BK-0030 身份写保护旁路**：实测目录内 `llms.txt` 身份为 `Beta`、`other.txt` 为 `Alpha`，执行 `--output other.txt --name=Alpha` 后 `llms.txt` 首行被改写为 `# Alpha …`（rc=0，无任何告警）。
- **触发面**：任何基名非 `llms.txt` 的 `--output`。仓库内现有调用面均为 `docs/llms.txt`，故门禁全绿——这正是它没被测试发现的原因。
- **引入**：是（重构把 `_atomic_write(output_file, …)` 换成 `base / rel`）。

### S-2 · P1 · audit 提示的重生成命令缺 `--split`，对 split 地图不可收敛（AC-6 违反）

- **根因（代码）**：`audit-doc-health.py` 中 `check_llms_map_consistency` 被**重复定义两次**——:233-309（含 `split_flag` 与 `detail`）与 :365-432（生效），后者覆盖前者。同批重复的还有 `_resolve_project_name`（:180/:312）、`AGENTS_MD_MAX_LINES`、`AGENTS_MD_REQUIRED`（:202-203/:334-335）、`check_agents_md`（:206/:338），合计约 110 行死代码。
- **证据（实测）**：手改 `_llms/proposals.md` 后
  ```text
  audit: 机器地图与生成物不一致 —— 请以 --name=Demo 运行 generate-llms-txt.py --root docs --output docs/llms.txt 重新生成后再提交
  照做: rc=0（写出单文件根 534 B）→ 再跑 audit: 同一缺陷（仍不一致）
  真实 docs 上照做: rc=1（22,967 B > 8192，拒绝落盘）
  ```
- **后果**：AC-6 要求的「给出重生成命令」形同虚设；修复闭环无限循环。同时**丢失 `detail`**（不再列出哪些文件不一致），只剩笼统「不一致」，诊断能力较被覆盖版本退化。
- **引入**：是（新实现插入时未删除旧定义，旧定义反而覆盖了新实现——即「本应生效的那份被静默丢弃」）。

### S-3 · P1 · 默认模式被 8192 体量闸门接管，RFC §7 回滚路径失效

- **证据（代码）**：`generate-llms-txt.py:465-473` —— 闸门位于 `--check` 与写盘之前，且不区分 `--split`；默认值 8192。
- **证据（实测）**：
  ```text
  $ ... --root docs --output new2.txt            # 无 --split，即 RFC §7 的回滚命令
  rc=1  ❌ 根机器地图 22967 字节 > 上限 8192 字节，拒绝落盘。请使用 --split…
  written? NO
  ```
- **后果**：RFC §7「删除 `_llms/` + 以默认模式重生成根文件即可恢复单文件形态（**一条命令**）」**不可执行**；且这是公共技能，任何下游项目以旧命令重生成 >8 KB 地图都会突然 rc=1，属未登记的行为破坏（AC-1 的「零破坏」只覆盖产物，未覆盖命令）。GOVERNANCE / SKILL 已把默认模式命令整体替换为 `--split`，未登记任何放行方式（`--max-root-bytes 0` 属未文档化的后门）。
- **引入**：是。

### S-4 · P2 · split 模式描述内链接 rebase 白名单过窄，非 http(s) scheme 静默断链

- **证据**：`generate-llms-txt.py:233` `_MD_LINK = r"\]\((?!https?://|mailto:|#)([^)\s]+)"`；夹具实测 `[t](tel:123)` → `[t](../tel:123)`、`[p](//cdn.example.com/y.md)` → `[p](../cdn.example.com/y.md)`、`[ftp](ftp://h/x.txt)` → `[ftp](../ftp://h/x.txt)`。
- **说明**：默认模式不受影响（`ABSOLUTE_LINK_PATTERN` 保留原样），故 AC-1 不破；当前仓库无此类描述，属潜伏缺陷。修法：把排除条件改为「`ABSOLUTE_LINK_PATTERN` 命中或 `//` 开头则原样保留」。

### S-5 · P2 · `_llms/` 嵌套子目录构成新静默区（真实文档可免检）

- **证据（代码）**：生成器 `generate-llms-txt.py:191-192` 按 `rel_parts[0] == "_llms"` 整树跳过；audit `in_generated_map`（:41-46）同口径排除计分；多余集合判据（audit :402-406 / generator :483-489）只 `glob("*.md")` **一层**。
- **证据（实测）**：`docs/_llms/sub/real-knowledge.md` → 生成器不收录、audit 分数不变（65.0 → 65.0）、输出中零次出现；同文件放 `docs/reference/tmp/` → 分数 65.0 → 64.6、出现 2 次、触发机器地图不一致。
- **后果**：一篇无控制头、无入链的真实文档放进 `_llms/sub/` 即可完全免于元数据/孤儿/地图门禁（仅 `check-doc-links` 仍扫得到它）。建议判据改为「`_llms/` 下只允许生成器产出的扁平 `.md` 白名单集合，其余（子目录、非 .md、多余 .md）一律判漂移」。

### S-6 · P2 · RFC §4.2 与实现互斥（子地图链接基准）

- **证据**：RFC §4.2「链接为**相对 docs 根**的路径（与根文件同基准）」+「条目格式与单文件模式**逐字一致**」；实现 `_render_section_map`（:252）输出 `- [A](../reference/a.md)`，描述链接亦补 `../`。若按契约字面写 `reference/a.md`，从 `_llms/` 解析必 404（`check-doc-links` 会红）。
- **后果**：验收判据（契约）与被验对象（实现）不可能同时成立；本仓库「文档即真相」立场下属规范性缺陷。修法：契约改为「相对子地图所在目录（即 `../` 前缀），保证从 `_llms/` 解析」。

### S-7 · P2 · AC-1 自动化用例同义反复，无法拦截命令层回归

- **证据**：`tests/test_llms_split.py:54-64` 用 `build_llms_map(split=False)` 对比 `generate_llms_txt(...)` 的产物，而后者（`generate-llms-txt.py:309-318`）**已改为调用前者** ⇒ 自证。无 9ca589f 基准 golden 样本。
- **后果**：S-1（`--output` 落点）与 S-3（默认模式闸门）这类「产物相同、命令行为改变」的回归天然漏网；本次审查靠外部复算才发现。

### S-8 · P3 · `--max-root-bytes 0` 静默关闭体量闸门

- `generate-llms-txt.py:467` `if args.max_root_bytes and root_bytes > args.max_root_bytes`：0 关闭、负数恒拒。未在任何文档登记；建议显式拒绝 `<= 0` 或写明语义。

### S-9 · P3 · 契约与计划中的数字/前提与实测不符

- 计划 §5「预期：…**6 个子地图**」与检查点「6 个子地图（explanation 4,618 / other 538 / project 15,060 / proposals 1,880 / reference 1,462）」**自相矛盾**：宣称 6 个却只列 5 个，实测亦为 **5 个**（tutorials / how-to 为空，AC-4 明确不产子文件）。该预期对本仓库不可满足。
- 同一行的子地图字节数已失真：`proposals 1,880` / `reference 1,462` 实测为 **1,883 / 1,465**（差 3 B，生成器不写入时间戳，属陈旧测量值）。
- RFC AC-1「产物与 RFC-0005 前逐字节相同」未限定「树中不含 `_llms/`」；含 `_llms/` 时新旧默认产物必然不同（RFC §4.3 的排除所致）。

### S-10 · P3 · `--check` 超限时文案误导

- 默认模式 `--check` 在超限时输出「拒绝落盘」（`--check` 本就不落盘），真实 docs 实测 rc=1 但理由是体量而非「不一致」。建议在 `--check` 分支改为「根体量超限」。

---

## ④ 裁决

| 编号 | 缺陷 | 原始 R1 评级 | 终审裁决 | 是否本次引入 | 计入 Blocker |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S-1 | `--output` 基名丢弃 + 身份闸门读写错位 | P1 | **P1 维持**（实测 BK-0030 旁路，证据充分） | 是 | ✅ |
| S-2 | audit 重生成命令缺 `--split`、不可收敛 | P1 | **P1 维持**（AC-6 直接违反，实测不收敛） | 是 | ✅ |
| S-3 | 默认模式被体量闸门接管，回滚命令失效 | P1 | **P1 维持**（RFC §7 明载路径实测不可执行） | 是 | ✅ |
| S-4 | 非 http(s) scheme 描述链接被改写 | P2 | P2（潜伏，当前无触发样本） | 是 | ❌ |
| S-5 | `_llms/` 嵌套静默区 | P2 | P2（需显式构造，且链接仍受检） | 是 | ❌ |
| S-6 | RFC §4.2 与实现互斥 | P2 | P2（契约文本需改，非实现错误） | 是 | ❌ |
| S-7 | AC-1 用例同义反复 | P2 | P2（测试承重不足，是 S-1/S-3 漏网原因） | 是 | ❌ |
| S-8 | `--max-root-bytes 0` 关闭闸门 | P3 | P3 | 是 | ❌ |
| S-9 | 计划「6 个子地图」/ AC-1 前提未限定 | P3 | P3 | 是 | ❌ |
| S-10 | `--check` 超限文案误导 | P3 | P3 | 是 | ❌ |

### 裁决：**阻断（Blockers = 3）**

**Blockers**：S-1、S-2、S-3（均为 P1，均有可复现命令与实测输出）。

**准予条件（三条修复后即可进入 Delta 复核）**：

1. 落点改为 `out_path`（根）与 `out_path.parent/_llms/`（子地图），并让身份闸门读写同一文件；补一条「`--output` 基名非 `llms.txt`」的落点用例与一条身份旁路反例。
2. 删除 audit 中重复的 4 组定义，保留含 `detail` 与 `split_flag` 的版本；补一条「按提示命令执行后 audit 转绿」的收敛用例（`--split` 场景）。
3. 体量闸门只对 `--split` 生效，或在默认模式超限时回落到「写盘 + 告警」并同步修订 RFC §7 与 GOVERNANCE 的回滚命令；补一条「默认模式 >8 KB 树 rc=0」的用例。

**未通过项之外的正面结论**：AC-2（根 ≤8192 B、非空象限各有子文件）、AC-3（幂等）、AC-4（空象限删子文件）、AC-5（超限不落盘）、AC-7（缺失/多余子地图）、AC-8（AGENTS.md 行数/小节）实测全部成立；四道门禁 + 235 项测试全绿。

---

## 残留风险（≤3）

1. **`_llms/` 与 `AGENTS.md` 的豁免面是新增的「无门禁区」**：顶层多余 `.md` 能被拦，但嵌套目录 / 非 `.md` / 根 `llms.txt` 删除后「不适用」三条口子叠加，足以让一篇真实文档完全绕过机器地图与健康度计分。
2. **描述内链接 rebase 的 scheme 白名单**：任何 `tel:`/`ftp:`/`data:`/协议相对 URL 一旦进入描述即静默断链，且断链只在 `check-doc-links` 层面可见，不影响地图生成成功。
3. **公共技能的默认命令语义变更**：`--max-root-bytes` 默认值作用于所有模式，下游项目沿用旧命令会在升级后突然 rc=1；需在升级说明中显式给出 `--split` 迁移路径与 `--max-root-bytes` 放行口径。
