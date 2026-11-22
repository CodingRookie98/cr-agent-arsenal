# Delta 复核报告（Light 模式）— 批量门禁 B-01~B-14 修复

> **审查基线**: `a38cc85`（B 修复 + 复核点重钉）→ `c45c71f`（格式修正）= `HEAD`
> **上一轮**: `round-1-light.md`（23,227 B，sha256 `a43546c7723ed3d6d7bbd0cd081752319254adfa90c3f67a487de07f61c3b7e6`，Blockers=2：B-01 / B-02）
> **契约**: RFC-0008 V0.1.1（体量门禁）、GOVERNANCE V1.11.1（B 项收口登记）、RFC-0005（真值轴）
> **口径**: 仅 P0/P1 计入 Blockers；只读复核，夹具全部落 `/tmp`，仓库工作树除本报告外零改动
> **审查日期**: 2026-11-22

---

## 0. 裁决前置摘要

| 项 | 结果 |
| :--- | :--- |
| Blockers（仅 P0/P1） | **2**：BD-1（同提交豁免内容盲区，P1）· BD-2（pre-commit 校验工作树而非索引，P1，属 B-02 第二口径未闭合） |
| B-01 | ✅ **闭合**：`check-all.py` 六项全绿、`--full` 七项全绿、`pytest` 292 passed |
| B-02 | ⚠️ **三夹具全过**（暂存锚点 rc=1 / 同提交 fresh / 分离提交 fresh）；第二口径未闭合，见 BD-2 |
| B-03 / B-04 / B-05 / B-06 | ✅ 四项行为齐备（.MD/.markdown 扫描、U+2028 不再绕过、非数值基线不崩溃、chmod 000 fail-closed） |
| B-10 / B-14 | ✅ 行为达成（G-02 接受「实施计划」；G-14 空 active 目录报 GAP）；G-02 判据过度放宽，见 BD-4 |
| 新风险（同提交豁免） | ⛔ **属实**：改锚点 + 文档加一行注释即可永久判 fresh，反例见 §1.6 / BD-1 |
| 回归面 | ✅ `pytest 292 passed`；`check-all.py` 6/6；真实 docs 体量分布与基线逐值一致 |
| **裁决** | **阻断（不准予交付）** |

---

## 1. 命令与输出

### 1.1 基线与工作树

```bash
$ git log --oneline -3
c45c71f docs(doc-governance): 修正复核点格式（补回被正则吃掉的换行）
a38cc85 docs(doc-governance): 复核点跟随  重钉（B 项收口后）
9d03d22 docs(doc-governance): 门禁自动化与可回答性评测的规程登记

$ git status --porcelain        # （空）
$ wc -c docs/project/reviews/2026-11-22-batch-gates/round-1-light.md
23227 docs/project/reviews/2026-11-22-batch-gates/round-1-light.md
$ sha256sum docs/project/reviews/2026-11-22-batch-gates/round-1-light.md
a43546c7723ed3d6d7bbd0cd081752319254adfa90c3f67a487de07f61c3b7e6  round-1-light.md
```

上轮报告字节数与 sha256 与本报告读到的实物逐字一致，可作为基线。

### 1.2 B-01：真实仓库门禁与测试

```text
$ python3 skills/doc-governance/scripts/check-all.py
✅ 机器地图
✅ 断链
✅ 版本一致
✅ 真值轴
✅ 健康体检
✅ 可回答性
🏁 全部门禁通过（6 项）                     rc=0

$ python3 skills/doc-governance/scripts/check-all.py --full
✅ 机器地图 ✅ 断链 ✅ 版本一致 ✅ 真值轴 ✅ 健康体检 ✅ 可回答性 ✅ 测试套件
🏁 全部门禁通过（7 项）                     rc=0

$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest skills/doc-governance/tests -q -p no:cacheprovider
292 passed in 27.22s                        rc=0
```

复核点与锚点最后提交逐项核验：

```text
skills/doc-governance/SKILL.md                    -> a38cc85 2026-11-22 19:55:19
skills/doc-governance/scripts/audit-doc-health.py -> a38cc85 2026-11-22 19:55:19
skills/doc-governance/scripts/check-doc-drift.py  -> a38cc85 2026-11-22 19:55:19
docs/explanation/architecture/doc-governance-design.md:7  -> 复核于: 2026-11-22 / commit a38cc85
docs/GOVERNANCE.md:9                                     -> 复核于: 2026-11-22 / commit a38cc85
docs/project/plans/2026-11-22-doc-truth-axis.md:9        -> 复核于: 2026-11-22 / commit a38cc85
```

> B-01 的修复路径是**真实重钉**（复核点 = 锚点最后提交 = `a38cc85`），不是靠同提交豁免混过：`c45c71f` 又改过设计书正文，`doc_sha = c45c71f ≠ anchor_sha = a38cc85`，豁免不成立，仍是 fresh。

### 1.3 B-02：三夹具（真实 CLI，`git init` 临时仓库，`/tmp/b02fix2`）

夹具结构：`docs/a.md` 控制头 `代码锚点: src/x.py`、`复核于: <base 提交>`；首次提交后已 `--write-baseline` 并提交账本，排除「账本缺失 rc=2」干扰。

**① 只暂存锚点改动（文档未动）**

```text
-- staged: src/x.py
$ python3 check-doc-drift.py --root docs --repo . --fail-on-drift --staged
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 0｜drifted 1｜missing 0｜stale 0｜unverified 0
🎯 真值分: 0.0 / 15
   - [drifted] a.md  ←  src/x.py
rc=1                                  ✅ 符合预期

对照（不带 --staged，即修复前语义）:
📊 fresh 1｜drifted 0            rc=0   ← B-02 的原始失明面
```

**② 锚点与文档同一次提交改动**

```text
-- HEAD=288bcd9  anchor_sha=288bcd9  doc_sha=288bcd9
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc=0                                  ✅ 符合预期（同提交豁免生效）
```

**③ 分离提交（先提交锚点，再改文档复核点指向该提交）**

```text
-- anchor_sha=6479a29  doc_sha=31b0d1c
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc=0                                  ✅ 符合预期
```

**端到端（真实仓库克隆 `/tmp/hookdemo2`，`core.hooksPath=.githooks`）**

```text
A：只改 SKILL.md（锚点），不碰文档
   git commit exit=1
   🚫 提交被阻断：文档门禁未通过。          ✅ hook 拦住
   HEAD 仍为 c45c71f（提交未落）

B：改 SKILL.md + 设计书只加一行注释（复核点不动）
   git commit exit=0
   HEAD -> b7c1c05 B: anchor + one comment
   SKILL.md 最后提交 = b7c1c05；文档复核点 = commit a38cc85   ← 复核点已落后 1 个提交
   提交后 check-doc-drift --staged：
   📊 fresh 3｜drifted 0｜stale 0｜unverified 0    🎯 15.0 / 15    rc=0   ⛔ 见 BD-1
```

> 三夹具本身**全部成立**；但「同提交豁免」把「同提交改过文档」等同于「同提交完成复核」，见 §1.6。

### 1.4 B-03 / B-04 / B-05 / B-06：体量门禁四项

直调 `audit-doc-health.check_doc_size`，每例独立 `/tmp` 根：

```text
=== B-03 扩展名 ===
  big.MD         scanned=['big.MD']        issues=1  -> 最长单行 1200 > 1000（新增超限，无基线记录）
  big.markdown   scanned=['big.markdown']  issues=1
  big.MARKDOWN   scanned=['big.MARKDOWN']  issues=1
  big.md         scanned=['big.md']        issues=1
=== B-04 U+2028 ===
  600+U+2028+600 -> {'bytes': 1203, 'longest_line': 1201, 'lines': 1, 'unreadable': False}
                    issues: ['sep.md: 最长单行 1201 > 1000（新增超限，无基线记录）']     ✅ 不再绕过
=== B-05 非数值基线 ===
  {"bytes":"abc","longest_line":"xyz"} -> 无崩溃
     issues=['big.md: 70000 字节 > 65536，最长单行 70000 > 1000（较基线恶化：0→70000 字节）']
  {"bytes":null,"longest_line":[1,2]}  -> 无崩溃，同上
=== B-06 chmod 000 ===
  metrics: {'bytes': 0, 'longest_line': 0, 'lines': 0, 'unreadable': True}
  issues: ['locked.md: 文件不可读，无法测量体量（fail-closed）']                        ✅ fail-closed
```

### 1.5 B-10 / B-14：断言层

```text
=== G-02（隔离 proposals 目录逐例）===
  a 实施计划链接           -> ('pass', '全部 RFC 有落地计划')     ✅ B-10 目标用例
  b 正文含「计划」二字      -> ('pass', '全部 RFC 有落地计划')     ⛔ 假 PASS（见 BD-4）
  c 全文无「计划」          -> ('gap',  '1 篇 RFC 缺落地计划链接')
  d 仅修订历史提「计划」    -> ('pass', '全部 RFC 有落地计划')     ⛔ 假 PASS
  e 只有「计划中」形容词    -> ('pass', '全部 RFC 有落地计划')     ⛔ 假 PASS

=== G-14 ===
  active 存在且为空        -> ('gap',  'active 目录存在但为空（需确认是否已全部结项）')   ✅
  active 不存在            -> ('pass', '无活跃待办（目录不存在）')  ⚠️ 目录删除通道仍在（上轮 B-12 原攻击面）
  active 有 1 张带验收卡片  -> ('pass', '1 张活跃卡片均有验收准则')
```

真实仓库全量：`PASS 15｜GAP 5｜FAIL 0`，rc=0；G-02 仅剩 RFC-0002 一条 GAP（该文全文无「计划」二字，属真 GAP）。

### 1.6 新风险：同提交豁免的内容盲区（重点）

判据实现（`check-doc-drift.py:216-220`）：只要 `git log -1 -- <锚点>` 的 SHA 与 `git log -1 -- <文档>` 的 SHA **相等**，就跳过 `commits[i] > verified_ts` 的漂移判定。**不看文档 diff 内容、不要求 `复核于` 字段被刷新。**

```text
夹具 RISK-A：改 src/x.py + docs/a.md 追加一行注释（复核点仍指旧提交 6968b51）
  HEAD=7836430  anchor_sha=7836430  doc_sha=7836430
  📊 fresh 1｜drifted 0｜stale 0｜unverified 0    🎯 15.0 / 15    rc=0     ⛔ 蒙混过关

夹具 RISK-B：仅暂存（不提交）锚点改动 + 文档一行注释
  -- staged: docs/a.md src/x.py
  📊 fresh 1｜drifted 0｜unverified 0              rc=0                    ⛔ 预提交同样放行

夹具 RISK-D：改锚点 + 文档只加一个空行
  📊 fresh 1｜drifted 0｜stale 0｜unverified 0     🎯 15.0 / 15    rc=0     ⛔ 蒙混过关
```

真实仓库克隆反例（`/tmp/hookdemo2`，见 §1.3 实验 B）：`SKILL.md` 最后提交 `b7c1c05`，设计书 `复核于` 仍为 `a38cc85`，门禁 `fresh 3/3 · 15.0/15 · rc=0`。**一行注释即可让「复核点落后于锚点」永久隐身。**

### 1.7 回归面

```text
$ pytest skills/doc-governance/tests -q
292 passed in 27.22s                        ✅（上轮 2 failed / 282 passed）

$ python3 skills/doc-governance/scripts/check-all.py
六项全绿 rc=0                                ✅
$ python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
🏁 诊断结论: PASS (健康度达标，准予交付) ✅（体量仅 3 条 warning：1 条行数、2 条存量）

真实 docs 体量分布：
  受检 107 篇｜docs 下 .md/.MD/.markdown 194 篇｜豁免 87 篇（reviews 79+2 新增、_llms 5、AGENTS.md 1）
  top bytes : 127747 (project/plans/2026-10-12-spec-evolution.md)
              58416  (explanation/analysis/llm-wiki-implementation-research.md)
              40431  (project/plans/2026-10-19-skill-scripts-python-unification.md)
  top line  : 1269 (2026-10-19-skill-scripts-python-unification.md)
              879  (2026-10-12-spec-evolution.md)
  over64k   : 仅 2026-10-12-spec-evolution.md
  over1000L : 仅 2026-10-19-skill-scripts-python-unification.md
  基线两条：(127747, 879) / (40431, 1269) 与实测逐值一致，无漂移、无遗漏、无多余条目。✅
```

> 与上轮 107/192/85 的差异仅为 `reviews/2026-11-22-batch-gates/` 新增的 2 篇归档（README + 上轮报告），全部在豁免面内，扫描面 107 篇未变。

---

## 2. 六项结论

| # | 检查项 | 结论 | 证据 |
| :--- | :--- | :--- | :--- |
| 1 | **B-02 真解**（三夹具） | ✅ 通过：① 只暂存锚点 rc=1；② 同提交 fresh；③ 分离提交 fresh。端到端 hook：只改锚点 commit exit=1 | §1.3 |
| 2 | **B-01**（真实仓库） | ✅ 闭合：`check-all.py` 6/6、`--full` 7/7、`pytest` 292 passed；设计书复核点 = `a38cc85` = 三个锚点最后提交 | §1.2 |
| 3 | **B-03/B-04/B-05/B-06** | ✅ .MD/.markdown 均受检（各 1 issue）；600+U+2028+600 → longest_line 1201 阻断；`{"bytes":"abc"}` 不崩溃且仍阻断；chmod 000 → unreadable + issue | §1.4 |
| 4 | **B-10/B-14** | ✅ G-02 接受「实施计划」；G-14 空 active 目录报 GAP。附：G-02 判据放宽为裸「计划」子串（BD-4），G-14 目录缺失仍 pass | §1.5 |
| 5 | **新风险（同提交豁免）** | ⛔ **属实**：SHA 相等即豁免、不校验内容；一行注释/空行即可让复核点落后的文档判 fresh。见 BD-1 | §1.6 |
| 6 | **回归面** | ✅ 292 passed；check-all 6/6；体量分布与基线逐值一致 | §1.7 |

---

## 3. 新缺陷清单

### BD-1 [P1 · 阻断] 同提交豁免只比 SHA 不比内容，「一行注释」即可让复核点落后的文档永久判 fresh

- **位置**：`skills/doc-governance/scripts/check-doc-drift.py:216-220`（`stale_indices` 的豁免条件 `anchor_shas[i] == doc_sha`）、`:268-271`（`git_last_commit_sha`）、`:505-515`。
- **机制**：豁免只要求「锚点文件与文档的最后一次提交是同一提交」，不要求该提交里 `复核于` 字段被刷新，也不看文档 diff 是否触及控制头。任何对文档的改动（注释、空行、无关错别字）都能让 `anchor_sha == doc_sha`，从而跳过 `commits[i] > verified_ts` 的漂移判定。
- **反例**：`/tmp/hookdemo2`（真实仓库 `feat/doc-truth-axis` 克隆，真实 hook）：`SKILL.md` 追加一行注释 + 设计书追加一行注释，提交 `b7c1c05`；`SKILL.md` 最后提交 `b7c1c05`，设计书 `复核于` 仍为 `a38cc85`（落后 1 个提交）；提交后 `check-doc-drift --fail-on-drift --staged` 输出 `fresh 3/3｜15.0/15｜rc=0`，`check-all.py` 亦 rc=0。夹具 RISK-A/B/D 同现象（§1.6）。
- **影响**：B-01 的原始失效形态（复核点落后于锚点提交）在「顺手改了一行文档」的提交里重新变为**静默绿灯**；且该状态会一直保持到锚点下一次单独变更。这与「宣称与取证同宽」直接冲突——文档控制头写 `复核于 a38cc85`，实际锚点已到 `b7c1c05`，门禁却报 15/15。
- **修复建议（最小改动）**：同提交豁免必须增加内容判据，三者取一即可：① 该提交中文档 diff 必须触及 `复核于` 行（`git diff <doc_sha>^ <doc_sha> -- <doc>` 命中 `复核于`）；② 或要求 `verified_commit == doc_sha`（同提交重钉只能指向父提交，故应显式登记父提交并校验）；③ 或把豁免限定为「`复核于` 日期 = 该提交日期」且锚点 diff 非空白变更。当前实现把「同提交触碰」当成「同提交复核」，属浅层补丁。
- **备注**：GOVERNANCE V1.11.1 仅一行提到「同一次提交视为同步」豁免，RFC-0005 契约文本未同步登记该语义（`grep 同一次提交 RFC-0005` 无命中），契约与实现已分叉。

### BD-2 [P1 · 阻断] pre-commit 校验工作树、提交的却是索引（B-02 第二口径未闭合）

- **位置**：`.githooks/pre-commit:20` 调用 `check-all.py --quiet`；`check-all.py:63-66` 只给真值轴加了 `--staged`，体量/健康等其余门禁仍读工作树文件（`audit-doc-health._size_docs/_measure_doc` 直接 `read_bytes()`）。Git 提交的是索引对象，不是工作树。
- **反例**：`/tmp/hookidx2`（真实仓库克隆）：`docs/project/plans/2026-10-19-skill-scripts-python-unification.md`（基线 40431 B）先写至 80432 B 并 `git add`，再把工作树恢复为 40431 B：
  - `git commit` **成功**（hook 无输出，exit=0），`HEAD` 内该文件 **80432 B**（= 基线 2 倍）；
  - 提交后工作树 40431 B，`check-all.py --quiet` **rc=0**（门禁读工作树，看不到索引里的超限内容）；
  - 干净克隆该提交后跑门禁：`🚫 诊断结论: REJECTED（1 处文档体量超限）` → 说明被提交的内容确已违反棘轮基线，本地 hook 完全失明。
- **影响**：与 B-02 同等性质（「可提交未受检内容」），且直接击穿 RFC-0008 的「基线只降不升」机械保证：一次 `git add` + 工作树回退即可把 2× 基线文档送进历史，而**提交时门禁是绿的**。上轮 B-02 的验收条件「hook 具备提交快照/索引视角」未达成（只对锚点路径名做了暂存区比对，未对内容做快照）。
- **修复建议**：hook 内用 `git stash create`/临时索引（`GIT_INDEX_FILE=$(mktemp)` + `git read-tree`）导出提交快照后，对所有门禁（不止真值轴）跑快照树；或明确在 GOVERNANCE 登记该盲区并降级承诺（当前未登记）。
- **备注**：该口径差在 `feb4f75` 引入 hook 时即存在，**并非 a38cc85 新增**；但它是上轮 B-02 判定面的一部分，B-02 的修复只闭合了「git log 对暂存改动不可见」这一半，故按未闭合 Blocker 计。

### BD-3 [P2] `--root` 不在 `--repo` 之下时 `analyze()` 抛 ValueError 裸 traceback（新回归）

- **位置**：`check-doc-drift.py:509-511`：`doc_sha=git_last_commit_sha(repo_path, doc_path.relative_to(repo_path).as_posix())`，无 try/except。
- **反例**：`python3 check-doc-drift.py --root /tmp/extdocs --repo /home/hui/workspace/projects/cr-agent-arsenal --fail-on-drift` → `ValueError: '/tmp/extdocs/a.md' is not in the subpath of '...'`，rc=1（traceback）。修复前版本（`9d03d22`）同一命令正常输出 `fresh 1/1 / rc=2`（账本缺失 fail-closed），无崩溃。`audit-doc-health.py --root /tmp/crlftree --repo .` 同样在 `audit_health → analyze` 崩溃。
- **影响**：外部 docs 树审计（本仓审查流程常用 `/tmp` 副本 + `--repo .`）从「可诊断的 rc=2」退化为「裸异常」；不影响仓库内默认路径（`docs` 在 `.` 之下），故 P2。
- **修复**：`try: doc_rel = doc_path.relative_to(repo_path).as_posix() except ValueError: doc_rel = None`，同 `staged` 分支一样按「无 doc_sha」处理。

### BD-4 [P2] G-02 由「字面落地计划」放宽为裸「计划」子串，断言近乎恒真（B-10 修复过冲）

- **位置**：`check-golden-tasks.py:66-71`，`re.search(r"(落地|实施|执行)?计划", text)`。
- **反例**：`本文不涉及任何计划，仅描述动机。` → pass；`该能力计划中。` → pass；修订历史 `计划后续补充` → pass（§1.5 b/d/e）。即任何出现「计划」二字的 RFC 都通过，且不检查是否有指向 `project/plans/` 的链接。
- **影响**：B-10 的「假 GAP」问题被替换为「假 PASS」：G-02 回答「某 RFC 落地到哪个计划」时，只要正文提到「计划」就报「全部 RFC 有落地计划」，与实际是否有可点击计划链接无关。属断言有效性回退（P2，非阻断）。
- **修复**：改为「`(落地|实施|执行)计划` 标签 + 同一行/同段内指向 `project/plans/` 的相对链接」双条件，或直接解析控制头 `来源`/`落地计划` 链接。

### BD-5 [P3] `split("\n")` 把 `\r` 计入最长单行：CRLF 文件恒 +1，且 `lines` 恒 +1

- **位置**：`audit-doc-health.py:280-295`，`lines = text.split("\n")`。
- **实测**：`a*1200 + \r\n` → `longest_line=1201`（上轮 `splitlines()` 实测 1200，正确）；`a*1000 + \r\n` → 1001 > 1000，**误阻断**；空文件 → `lines=1`（上轮 0）；800 行 + 末换行 → `lines=801`（仅 warning）。
- **影响**：本仓 `.gitattributes` 为 `* text=auto eol=lf`，工作树恒 LF，当前 0 个 CRLF 文档，故无现网影响；但 RFC-0008 口径是「最长单行**字符数**」，`\r` 不是行内容。属 B-04 修复引入的度量回归，P3。
- **修复**：`lines = [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]`。

### BD-6 [P3] `--staged` 仅按路径字符串精确匹配，目录锚点仍失明

- **位置**：`check-doc-drift.py:516-524`，`touched = [a["path"] for a in anchors if a["path"] in staged]`。
- **实测**（`/tmp/b02dir/d1`）：文档锚点 `skills/pkg`（目录），暂存 `skills/pkg/a.py` → `fresh 1/1 · rc=0`；同场景改文件锚点 `skills/pkg/a.py` → `drifted · rc=1`（D-2 对照）。
- **影响**：目录锚点是代码显式支持的形态（R2D-6），但 pre-commit 对目录锚点依旧结构性失明。真实仓库当前 7 个锚点全为文件路径、0 个目录锚点，潜伏 P3。

### BD-7 [P3] `anchor_shas` 与 `commits` 索引基准不一致：含 glob 锚点时真实漂移降级为 unverified

- **位置**：`check-doc-drift.py:505-515` 传入**全量** `anchor_shas`，而 `classify_doc:216-220` 的 `commits` 是**按 decidable 过滤后**的列表，`i` 直接复用造成错位。
- **实测**（`/tmp/idxmis2`）：文档锚点 `docs/**, src/a.py`，先改文档（pin 到 c1）再单独改 `src/a.py`；期望 `drifted`，实得 `unverified`（`docs/**` 的 sha == doc_sha 命中豁免，真实锚点的漂移被吞）。默认 `--fail-on-drift` 仍 rc=1；但 `--allow-unverified` 可把它当 unverified 豁免为 rc=0。
- **影响**：只影响「glob/散文锚点在前 + 真实锚点在后」的文档（真实仓库 0 例），属 P3。

---

## 4. 裁决

```text
Blockers（仅计 P0/P1）: 2
  BD-1 [P1] 同提交豁免只判 SHA 不判内容：「改锚点 + 一行注释」即可让复核点落后的文档永久 fresh
  BD-2 [P1] pre-commit 校验工作树而非索引（B-02 第二口径未闭合）：2× 基线的文档可在绿灯下提交
P2/P3 记录: 5 项（BD-3 ~ BD-7）
B-01: ✅ 闭合（check-all 6/6、--full 7/7、pytest 292 passed）
B-02: ⚠️ 三夹具全过，第二口径未闭合

裁决: 阻断（不准予交付）
```

**准予条件（全部满足后可再复核）**：
1. 修复 BD-1：同提交豁免增加内容判据（文档 diff 必须触及 `复核于` 行，或 `verified_commit == doc_sha`），并给出「改锚点 + 一行注释 / 一行空行」两个反例均判 drifted 的 A-B 证据。
2. 修复 BD-2：hook 在**提交快照**（临时索引/`git stash create`）上跑全部门禁，并给出「`git add` 超限文档 + 工作树回退」被阻断的 A-B 证据；若决定不修，须在 GOVERNANCE 显式登记「hook 只校验工作树」的盲区并降级 BK-0048 的承诺。
3. 回归：`check-all.py --full` 零红灯 + `pytest` 全绿（须出示原始输出）。

---

## 5. 残留风险（≤3）

1. **未收口的 P2/P3（上轮遗留）**：B-06 基线投毒/残留仍未修（预置 `future/plan.md: {bytes:1e9}` 后落 120 KB 文档 → `issues=[]`）；B-08 `--write-size-baseline` 一键棘轮复位；B-09 `PYTHON_BIN=true` 可整体旁路 hook；B-11 G-20 仍按目录豁免（decisions/backlog/articles 零元数据文件可通过）；B-12 的「删除 active 目录」通道仍在（目录不存在 → pass）。这些均不阻断本轮，但会把「门禁自动化」的保证逐级降级。
2. **G-02 断言已近恒真**（BD-4）：任何正文含「计划」二字的 RFC 都报 pass，无法回答「落地到哪个计划」；建议按链接而非词根判定。
3. **体量门禁覆盖率 107/194（55%）**：`project/reviews/**`（87 篇，含本报告）、`_llms/**`（5 篇）、`AGENTS.md` 不在体量约束内，报告类产物可无上限增长；此豁免未在 RFC-0008 登记（上轮 B-15 遗留）。

---

## 6. 边界声明

- 全程只读：未修改任何被跟踪文件，未执行任何 git 写操作（无 add/commit/reset/checkout 作用于真实仓库）；`/tmp` 下的全部 `git init`/`git clone`/`git commit`/`git reset` 仅作用于一次性实验副本（`/tmp/b02fix2`、`/tmp/b02risk`、`/tmp/hookdemo2`、`/tmp/hookidx2` 等）。
- 所有结论均来自实跑输出或代码定位（`文件:行`）；B-01 的修复证据取自真实仓库，B-02 第二口径取自真实仓库克隆 + 真实 hook。
- 本报告自身按 RFC-0001 逐字归档（`docs/project/reviews/**` 豁免控制头），未携带文档控制头；归档 README 已存在，G-17 不受影响。
