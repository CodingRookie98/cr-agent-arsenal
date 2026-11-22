# Delta 复核审查（R3 修复 · 独立上下文 · Light 模式）
## 审查对象：`940b355`（收口 R3 红队 P1）

> **文档控制信息**
> - **文档标识**: REVIEW-R3-DELTA-doc-truth-axis-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: Delta 复核审查者（独立上下文，Reviewer ≠ Author）
> - **生效日期**: 2026-11-22
> - **审查对象**: `940b355`（fix(doc-governance): 收口 R3 红队 P1（invalid 判据过度矫正））；HEAD 即该提交，其后无新提交
> - **审查基线**: `5818d07`（上一轮定向红队报告所审 HEAD）／缺陷来源 `round-3-followup-light.md`（31,004 B，sha256 `dc3a04f4…` 实测一致）
> - **契约依据**: RFC-0005 V0.1.9、GOVERNANCE V1.7.9、实施计划 V1.7.0 §9
> - **审查模式**: Delta 复核 · Light（只验四项：R3-1 正解 / R3-1 反向风险 / R3-2·3·5 / 回归面）
> - **取证方式**: 全部为本机实跑。夹具建于 `/tmp/r3d_*`（本轮新建 20 个临时 git 仓库），提交时间用 `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` 钉死（`2026-11-01 / 11-20 / 11-21`）
> - **唯一写入面**: 本报告文件（未提交）。仓库内零写：开工与收工 `git status --porcelain` 均为空
> - **git 写操作**: 无（`init/add/commit/rm` 全部发生在 `/tmp/r3d_*` 夹具仓库）
> - **环境**: Linux / Python 3.12.3 / git 2.56.1 / HEAD = `940b35571fd79108ffb60510b7dd359c5dce7ea9`
> - **未验证项**: Windows 真实文件系统下反斜杠锚点的 stat 行为（本轮以 POSIX 夹具 + `:82` 归一化路径静态推演）；CI 流水线（仓库无 `.github`，门禁全为人工触发）；千篇级文档逐锚点 `git log` 的性能

---

## 0. 一句话结论

**原 P1（R3-1）的指名场景已真解**：含空格 / 中文 / `@` / `+` / 反斜杠的合法路径全部恢复为真实锚点，`git rm` 后实测 `missing_anchor` + `rc=1`（修复前 `fresh` + `rc=0`），散文仍 `invalid` 且不硬红；R3-2 / R3-3 / R3-5 三条全部达成，回归面 5/5 全绿、重复测试类已彻底删除（48 defs = 48 collected = 48 direct-run）。

**但同一失效机制在新判据下留了一个窄口，且是本次修复引入的回归**：`_PATH_TOKEN` 不含行区间后缀，导致**根级无扩展名文件 + 行区间**（`Makefile:2` / `LICENSE:3` / `Dockerfile:5-9`）被归 `invalid` → 退出判定集 → 文档判 `fresh`、真值分 15.0/15、默认门禁 `rc=0`，而锚点文件**实际已被改动**（§4 R3D-1，实测旧版 `drifted/rc=1` vs 新版 `fresh/rc=0`）。失效形态与 R3-1 完全同型（静默绿灯 + 满分 + 默认门禁），只是触发面窄。

**Blockers = 1（R3D-1，P1）→ 阻断**。R3D-2/3/4 为 P3 非阻断。

---

## 1. 会话与基线事实

| 项 | 值 |
| :--- | :--- |
| 分支 | `feat/doc-truth-axis` |
| 开工 / 收工 HEAD | `940b355`（会话期间无新提交；`git status --porcelain` 开工 0 行、收工 0 行） |
| 审定增量（skills/） | `940b355`：`check-doc-drift.py` +60/-15、`test_doc_drift.py` +50/-42（删重复类 93 行、增 `TestR3Fixes` 6 条） |
| 审定增量（docs/，仅作契约依据，不单独判定） | `GOVERNANCE.md` V1.7.8→V1.7.9、`RFC-0005` V0.1.8→V0.1.9、计划 V1.6.0→V1.7.0 |
| 受控文件改动 | 无（本报告为唯一写入，且不提交） |

> **边界声明**：本轮只判 `git diff 5818d07..940b355 -- skills/` 的行为后果，不重审已裁决项（R1/R2/Delta/放行确认/收口确认 2 的结论不回看）；`docs/` 的契约行仅在"实现是否忠实于契约"时被引用。

---

## 2. ① 复现命令与输出

夹具统一构造（`/tmp/r3d/fixtures.py`）：`git init` → 钉死 `2026-11-01` 提交锚点文件 → `2026-11-20` 提交文档（`复核于: 2026-11-20 / commit <sha>`）→ `2026-11-21` 制造漂移/删除 → 先 `--write-baseline` 再跑门禁，以排除 `rc=2`（账本缺席）干扰。断言取 `--json` 的 `docs[0].status` / `invalid_anchors` 与 `summary` 字段，不解析 emoji 文本。

### 2.1 R3-1 主场景：含空格合法路径（原 P1 的 D1/D2 对照重跑）

```console
### A 含空格合法路径（已写账本，门禁口径）
$ check-doc-drift.py --root docs --repo . --fail-on-drift   # 文件存在
🔍 文档代码锚点漂移检测: root=/tmp/r3d_zdnlk5gi/docs repo=/tmp/r3d_zdnlk5gi
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc=0
$ git rm "docs2/my file.md" && git commit -m rm  → 同上命令
🔍 文档代码锚点漂移检测: root=/tmp/r3d_zdnlk5gi/docs repo=/tmp/r3d_zdnlk5gi
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 0｜drifted 0｜missing 1｜stale 0｜unverified 0
🎯 真值分: 0.0 / 15
   - [missing_anchor] a.md
rc=1
json summary: {"fresh": 0, "missing_anchor": 1, "drifted": 0, "stale": 0, "unverified": 0,
               "removed_from_baseline": 0, "freshness_score": 0.0}
doc0: {"doc": "a.md", "status": "missing_anchor", "invalid_anchors": []}

### A3 单锚点含空格路径（无其它锚点兜底）
存在: rc=0 status=fresh
删除: rc=1 status=missing_anchor
```

**判定：✅ 真解**。`invalid_anchors` 为空、锚点进入判定集、文件被删即 `missing_anchor` + `rc=1` + 真值分 0.0（修复前为 `fresh` / 15.0 / `rc=0`，见上一轮 D1）。A3 证明不是"靠同文档另一条 fresh 锚点兜底"才红的。

### 2.2 路径形态矩阵：是否都按路径处理

```console
$ python3 /tmp/r3d/harness_e2e.py   # B 组，每个形态一个独立夹具仓库
[B-CJK]       rc=2 status=fresh paths=['文档/说明.md']        invalid=[]     ← rc=2 为账本缺席，status 为准
[B-at]        rc=2 status=fresh paths=['pkg@1.2/x.py']      invalid=[]
[B-plus]      rc=2 status=fresh paths=['a+b.py']            invalid=[]
[B-backslash] rc=2 status=fresh paths=['src/a.py']          invalid=[]     ← 锚点写作 src\a.py
[B-latin1]    rc=2 status=fresh paths=['src/ü.py']          invalid=[]
[B-space-dir] rc=2 status=fresh paths=['my docs/file.md']   invalid=[]
```

单元面（`normalize_anchor` 直调，`/tmp/r3d/harness_unit.py`）：

```console
'docs2/my file.md'   -> path='docs2/my file.md'   invalid=False unver=False
'文档/说明.md'          -> path='文档/说明.md'          invalid=False unver=False
'pkg@1.2/x.py'       -> path='pkg@1.2/x.py'       invalid=False unver=False
'a+b.py'             -> path='a+b.py'             invalid=False unver=False
'src\a.py'           -> path='src/a.py'           invalid=False unver=False   ← 反斜杠先归一化（:82）
'src/ü.py'           -> path='src/ü.py'           invalid=False unver=False
'src/x.py:1-3'       -> path='src/x.py'           invalid=False lines=1-3
'src/**'             -> path='src/**'             invalid=False unver=True
'**src/x.py**'       -> path='src/x.py'           invalid=False unver=False
```

**判定：✅ 全部按路径处理**。反斜杠相对路径恢复了 `:82` 归一化后的可达性（上一轮指出的"`:92` 分支不可达"已消解）。

### 2.3 散文仍 invalid 且不硬红

```console
$ python3 /tmp/r3d/harness_v.py   # W1，含 --allow-unverified 的文本输出
⚠️  --allow-unverified 已生效：豁免 stale 0 + unverified 1（共 1 篇不阻断；drifted/missing/墓碑仍阻断）
🔍 文档代码锚点漂移检测: root=/tmp/r3d_3xhonmrp/docs repo=/tmp/r3d_3xhonmrp
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 0｜drifted 0｜missing 0｜stale 0｜unverified 1
🎯 真值分: 0.0 / 15
   - [unverified] a.md
   ⚠️  invalid 锚点（不像路径，无法机械核验；请改写为仓库内相对路径）:
      - a.md: see appendix A
```

| 锚点值 | status | invalid_anchors | 是否硬红（missing_anchor） |
| :--- | :--- | :--- | :--- |
| `see appendix A` | `unverified` | `['see appendix A']` | ❌ 不硬红 |
| `见附录 A` | `unverified` | `['见附录 A']` | ❌ 不硬红 |
| `src/a.py, see appendix A` | `fresh` | `['see appendix A']` | ❌ 不硬红，且不拖累真实锚点 |

**判定：✅ 达成**（"不硬红"= 非 `missing_anchor`；`unverified` 在默认门禁下阻断、可用 `--allow-unverified` 豁免，属 R2D56-1 既定口径，非本轮回归）。

### 2.4 R3-1 反向风险：新判据是否放过真散文

```console
=== [D'] 反向风险 · 写账本后的真实门禁 rc ===
[D1 A/B 测试]        rc=1 status=missing_anchor invalid=[] | {"fresh":0,"missing_anchor":1,"unverified":0,"removed_from_baseline":0}
[D2 见 3.2 节]        rc=1 status=missing_anchor invalid=[] | {"fresh":0,"missing_anchor":1,"unverified":0,"removed_from_baseline":0}
[D3 see appendix A.1] rc=1 status=missing_anchor invalid=[] | {"fresh":0,"missing_anchor":1,...}
[D4 v1.2 规范]        rc=1 status=missing_anchor invalid=[] | {"fresh":0,"missing_anchor":1,...}
[D6 真实+散文]         rc=1 status=missing_anchor invalid=[] | {"fresh":0,"missing_anchor":1,...}
```

```console
--- W2 反向风险（missing_anchor 硬红）---
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 0｜drifted 0｜missing 1｜stale 0｜unverified 0
🎯 真值分: 0.0 / 15
   - [missing_anchor] a.md
   rc= 1
```

**判定：⚠️ 确实存在，且是契约写死的**。含 `/` 或 `.` 的散文（`A/B 测试`、`见 3.2 节`、`see appendix A.1`、`v1.2 规范`、`N/A`）一律判 `missing_anchor` 硬红。**定级 P3（R3D-2）**，理由：① 失效方向是 **fail-loud**（硬红），不会像 R3-1 那样掩盖漂移；② RFC-0005 V0.1.9 §4.2 已把判据明写成"无分隔符 `/`、无扩展名点、且非标识符形态"，实现忠实于契约；③ 上一轮 §6 残留风险 1 明确要求"灰区必须硬红"；④ 仓库现状零实例（3 篇声明文档的锚点全部含 `/` 或 `.`）；⑤ 逃生通道被堵死：改写成散文 ⇒ `unverified` 仍阻断，删锚点 ⇒ 墓碑 `rc=1`，唯一出路是写真路径。**无需再收判据，但需登记**（见 R3D-2 建议）。

### 2.5 R3-2 / R3-3 / R3-5

**(a) R3-2 跨分隔符加粗**（`/tmp/r3d/harness_v.py` V 组 + `harness_gate.py` E 组）：

```console
[e1 **src/x.py, src/y.py**]  rc=0 status=fresh paths=['src/x.py', 'src/y.py'] invalid=[]
[e2 **src/x.py**、src/y.py]  rc=0 status=fresh paths=['src/x.py', 'src/y.py'] invalid=[]
[v1 **src/a.py、src/b.py**]  rc=0 status=fresh paths=['src/a.py', 'src/b.py'] invalid=[]   ← 中文顿号
[v2 **src/a.py**, **src/b.py**] rc=0 status=fresh paths=['src/a.py', 'src/b.py'] invalid=[]  ← 双段加粗
[v3 ** src/a.py , src/b.py **] rc=0 status=fresh paths=['src/a.py', 'src/b.py'] invalid=[]  ← 内层空格
[e5 **src/x.py:1-3**]        rc=0 status=fresh paths=['src/x.py'] invalid=[]
[e3 src/**]                  rc=0 status=unverified paths=['src/**'] invalid=[]              ← glob 未误伤
[e4 **src/**]                rc=0 status=fresh paths=['src'] invalid=[]                     ← 目录锚点（既有歧义，非本轮引入）
```

假墓碑复核（上一轮 H1 场景重跑，`/tmp/r3d/harness_reg.py` Y 组）：

```console
账本: {"docs": {"a.md": ["src/a.py", "src/b.py"]}, "version": 1}    ← 加粗跨分隔符已归一
[Y] 作者把 **src/a.py, src/b.py** 改成 src/a.py, src/b.py 后：
    rc=0 status=fresh removed_from_baseline=0
```

**判定：✅ 达成**。`parse_truth_fields:148` 在 `_ANCHOR_SPLIT` **之前**剥离整体加粗，账本键与去加粗写法同形，上一轮的假墓碑违规（`removed=1`、`rc=1`）不再复现。

**(b) R3-3 invalid 在文本输出可见**：见 §2.3 W1 输出——标题行 + `- a.md: see appendix A` 明细行，与 `:569-574` 实现一致；`--json` 的 `docs[].invalid_anchors` 仍在。**判定：✅ 达成（文本面）**；审计产物面见 R3D-4。

**(c) R3-5 豁免入 JSON + waived=0 不谎报**（`/tmp/r3d/harness_reg.py` Z 组）：

```console
[Z1 全fresh+豁免 json] rc=0 waived=0 waiver_flag=--allow-unverified stdout_已生效=False stderr_已生效=False
[Z2 全fresh 无豁免 json] rc=0 waived=0 waiver_flag=None               stdout_已生效=False stderr_已生效=False
[Z3 全fresh+豁免 文本] rc=0 已生效=False 末行='🎯 真值分: 15.0 / 15'
[Z4 unverified+豁免 json] rc=0 waived=1 waiver_flag=--allow-unverified
    stderr='⚠️  --allow-unverified 已生效：豁免 stale 0 + unverified 1（共 1 篇不阻断；drifted/missing/墓碑…'
[Z5 unverified 无豁免] rc=1 waived=0 waiver_flag=None
[Z6 unverified+豁免 非门禁] rc=0 waived=1
```

**判定：✅ 达成**。`summary.waived`（`:535/540`）+ `waiver_flag` 入机器可读产物；`waived=0` 时不再打印"已生效"（Z1/Z2/Z3 三面均无该串）；`blocking -= summary["waived"]`（`:593`）口径与豁免数一致。与上一轮建议的字段名（`allow_unverified` bool）不同但语义等价，不计缺陷。

### 2.6 回归面（5/5）与测试卫生

```console
$ python3 -m pytest skills/doc-governance/tests -q
209 passed in 39.69s

$ python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 3/46 篇（覆盖度 6.5%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc=0

$ python3 skills/doc-governance/scripts/check-doc-links.py
📊 审计汇总: 共扫描 95 个 Markdown 文件
✅ 恭喜！未发现任何 404 断链或非法相对引用，所有链接 100% 物理有效！
rc=0

$ python3 skills/doc-governance/scripts/check-doc-control-sync.py
📊 扫描汇总: 共检查 47 个 Markdown 文件
✅ 恭喜！所有文档控制头与修订历史版本 100% 保持一致，无版本漂移！
rc=0

$ python3 skills/doc-governance/scripts/audit-doc-health.py
🏁 诊断结论: PASS (健康度达标，准予交付) ✅
rc=0
```

**重复测试类是否彻底删除**（三种计数必须相等）：

```console
$ python3 skills/doc-governance/tests/test_doc_drift.py        # 直接执行
Ran 48 tests in 5.376s
OK

$ python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q --collect-only | tail -1
48 tests collected in 0.03s

$ grep -c "def test_" skills/doc-governance/tests/test_doc_drift.py
48

$ grep -h "^class " skills/doc-governance/tests/*.py | sort | uniq -c | sort -rn | head -3
      1 class TestUnclosedFrontmatterFence(unittest.TestCase):
      1 class TestTrimRevision(unittest.TestCase):
      1 class TestSkillSpecQuadrantIndexConvention(unittest.TestCase):     ← 全库无同名类
$ grep -h "def test_" skills/doc-governance/tests/*.py | sed 's/(.*//' | sort | uniq -d
（空输出：无同名测试函数）
```

**修复前后计数账**（旧树在 `/tmp/r3d/oldtree` 由 `git show 5818d07:…` 重建，仓库零写）：

```console
旧 5818d07：test_doc_drift.py 46 个 def，pytest 只收集 42 条  ← 重复类 TestFollowupP2P3 的 4 条被同名覆盖
新 940b355：test_doc_drift.py 48 个 def，pytest 收集 48 条    ← 重复类已删，新增 TestR3Fixes 6 条
旧全量：199 passed + 4 failed = 203 条（4 failed 为 /tmp 副本丢失仓库根上下文所致，非仓库缺陷）
新全量：209 passed                                          ← 203 + 6，账目自洽
```

**判定：✅ 达成**。`TestFollowupP2P3` 只剩一份（`:798`），`TestR3Fixes`（`:893`）6 条全部被收集，直接执行数 = pytest 收集数 = def 数 = 48。

---

## 3. ② 四项逐条结论

| # | 验收项 | 期望 | 实测 | 结论 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | R3-1 主场景（`docs2/my file.md` 存在 / `git rm` 后） | fresh → missing_anchor + rc=1 | `fresh/rc=0` → `missing_anchor/rc=1`、真值分 15.0→0.0 | ✅ 真解 |
| 1b | 中文 / `@` / `+` / 反斜杠 / 非 ASCII 拉丁 路径 | 按路径处理 | 6/6 `fresh`、`invalid=[]` | ✅ |
| 1c | 散文 `see appendix A` / `见附录 A` | invalid 且不硬红 | `invalid` + `unverified`（非 missing_anchor） | ✅ |
| 2 | 反向风险：像路径的散文 | —— | 含 `/` 或 `.` 的散文 ⇒ `missing_anchor` 硬红（5/5） | ⚠️ 存在，判 P3 可接受（R3D-2） |
| 3a | R3-2 跨分隔符加粗 | 正常解析且账本对称 | 4 种写法均 `fresh`、假墓碑 `removed=0` | ✅ |
| 3b | R3-3 invalid 文本可见 | 文本输出可见 | 标题 + 明细行，含路径与修复提示 | ✅（审计面见 R3D-4） |
| 3c | R3-5 `summary.waived` 入 JSON、waived=0 不谎报 | 两者均成立 | `waived=0/1` 均正确，零豁免无"已生效" | ✅ |
| 4 | 回归面 5/5 + 重复类删除 | 全绿且计数自洽 | 209 passed / rc=0 / rc=0 / rc=0 / PASS；48=48=48 | ✅ |
| **新** | **同一 invalid 机制是否仍有漏口** | **无** | **根级无扩展名文件 + 行区间 ⇒ 静默 `fresh`/15.0/rc=0** | ❌ **R3D-1（P1）** |

---

## 4. ③ 新缺陷

### R3D-1 【P1 · 阻断 · 本次修复引入的回归】根级无扩展名文件 + 行区间被判 invalid ⇒ 真实漂移被静默吞掉

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/scripts/check-doc-drift.py:43`（`_PATH_TOKEN = [A-Za-z0-9._@+~\-]+`，**不含 `:`**）、`:96-98`（`not _looks_like_path` ⇒ invalid）、`:183-188`（`decidable` 剔除）、`:39`（`_ANCHOR_LINE` 支持 `:N`/`:N-M` 行区间，但形态判断在其**之前**） |
| **现象** | 锚点形如 `Makefile:2` / `LICENSE:3` / `Dockerfile:5-9`（路径无 `/`、无 `.`、带行区间）时：`_looks_like_path` 对整串做 `fullmatch` 失败（`:` 不在字符类里）⇒ `invalid=True` ⇒ 被 `decidable` 剔除 ⇒ 同文档其它锚点全 fresh 时整篇 `fresh` ⇒ 真值分 15.0 ⇒ 默认 `--fail-on-drift` rc=0 |
| **证据（旧/新对照，同一夹具同一提交）** | ```console
$ python3 /tmp/r3d/harness_reg.py   # X 组：锚点 src/a.py, Makefile:2；复核后改动 Makefile 并提交
[旧 49c6d55] rc=1 status=drifted invalid=None paths=['src/a.py','Makefile'] lines=[None, 2]
[新 940b355] rc=0 status=fresh  invalid=['Makefile:2'] paths=['src/a.py','Makefile:2'] lines=[None, None]
``` |
| **门禁面原文（新）** | ```console
$ check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
   ⚠️  invalid 锚点（不像路径，无法机械核验；请改写为仓库内相对路径）:
      - a.md: Makefile:2
   rc= 0
``` |
| **影响** | ① 真值轴对该锚点**完全失效**：改动/移动/删除 `Makefile` 均无信号且颁发满分（命中 `change-impact-matrix.md:30` 的 DoD 场景"被锚定路径变动/移动/删除"）；② 墓碑不救（声明未变，`removed_from_baseline=0`）；③ 文本提示**误导**——它说"不像路径"，而 `Makefile:2` 恰恰是路径，作者会被引向"删掉行区间"甚至删锚点（后者触发墓碑硬红）；④ 这是**回归**而非取舍：旧版 `_PATH_SHAPE` 末尾有 `(?::\d+(?:-\d+)?)?`，该形态原本被显式支持 |
| **触发条件** | 锚点路径**根级、无 `/`、无扩展名点**，且带 `:N` / `:N-M` 行区间；同文档存在至少一条可核验且 fresh 的锚点（或该文档为唯一文档时落 `unverified`，属可见态）。**无需任何豁免参数** |
| **为何定 P1** | 与 R3-1 同型同源：默认门禁下静默、颁发满分、直接命中 DoD 场景；且 R3-1 的定级理由（"假声明颁发满分"）对本案逐条成立。触发面窄是"概率低"，不是"后果轻"——按上一轮对 R3-1 的口径，失效形态优先于触发概率 |
| **减轻情节（诚实标注）** | 文本面已有 invalid 提示行（R3-3 的副产品），不再是"零信号"；仓库现状零实例（`git ls-files` 根级无扩展名文件仅 `LICENSE`，3 篇声明文档均未锚定它） |
| **最小修复** | ① 形态判断前先剥行区间：把 `_ANCHOR_LINE` 的解析提到 `:96` 之前，对 `body`（而非整串）做 `_looks_like_path`；或 ② 给 `_PATH_TOKEN` 补 `(?::\d+(?:-\d+)?)?` 后缀。二者均 2-3 行 |
| **回归测试建议** | ① `Makefile:2` 存在且被改动 ⇒ `drifted` + rc=1；② `LICENSE:3` 删除 ⇒ `missing_anchor`；③ 保留 `see appendix A` ⇒ `invalid`（防二次矫正） |
| **若主张降级为 P2，须同时满足** | (a) 在 RFC-0005 §4.2 显式声明"根级无扩展名文件不支持行区间锚点"；(b) 补一条断言当前 `invalid` 行为的测试并注明为**已知限制**。否则它就是未登记静默洞 |

### R3D-2 【P3 · 非阻断】像路径的散文被硬红（`A/B 测试` / `见 3.2 节` / `v1.2 规范`）

| 项 | 内容 |
| :--- | :--- |
| **位置** | `check-doc-drift.py:69-71`（`"/" in text or "." in text ⇒ 视为路径`） |
| **现象** | 含 `/` 或 `.` 的散文一律进 `missing_anchor` 硬红，`rc=1`（D1–D4、D6 实测） |
| **定性** | **有意假红，可接受**：fail-loud；RFC-0005 V0.1.9 §4.2 已写死判据；上一轮 §6 残留风险 1 要求"灰区必须硬红"；逃生通道被封（改散文⇒`unverified` 阻断，删锚点⇒墓碑 `rc=1`） |
| **建议** | 在 RFC §4.2 / 计划 §9 增一句"含 `/` 或 `.` 的散文会被判 missing_anchor，属有意假红，改写为真实路径或删除声明（删除受墓碑约束）"；并给 `missing_anchor` 的文本明细补上**具体锚点值**（现状 `- [missing_anchor] a.md` 不含锚点名，作者无从定位，见 `:562-564`） |

### R3D-3 【P3 · 非阻断】`_PROSE_HINT` 定义后从未使用（死代码 + 未落地意图）

| 项 | 内容 |
| :--- | :--- |
| **位置** | `check-doc-drift.py:44`（`_PROSE_HINT = re.compile(r"[\s\u4e00-\u9fff]")`），全文件仅此一处出现（`grep -n _PROSE_HINT` 只命中定义行） |
| **现象** | 该正则显然是为"含空白/中文 ⇒ 散文"准备的，最终判据却换成了 `_looks_like_path` 且未引用它；死代码违反仓库"清理自身死代码"的工程规范，也让后来者误判判据意图（以为空白/中文仍参与判断） |
| **建议** | 删除该行；若确要保留"空白/CJK 提示"，必须在 `_looks_like_path` 中真实使用并配测试 |

### R3D-4 【P3 · 非阻断 · R3-3 半收口】审计产物面仍不透出 invalid

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/scripts/audit-doc-health.py:677-694`（`truth_block` 有 `drift_docs`/`missing_anchor_docs`，**无** `invalid_anchors`）；`grep -n invalid audit-doc-health.py` 零命中 |
| **现象** | R3-3 只收了文本面（`check-doc-drift.py:569-574`）；`audit-doc-health` 的健康报告仍看不到 invalid 分类，而它正是"长期不被发现"的观测面（R3D-1 在该面同样不可见） |
| **建议** | `truth_block` 增 `"invalid_anchors": {doc: [...]}` 或至少 `invalid_count`，并在 warn 模式计入缺陷提示 |

---

## 5. ④ 裁决

### 5.1 计数

| 定级 | 计数 | 编号 |
| :--- | :--- | :--- |
| P0 | 0 | — |
| **P1（Blocker）** | **1** | **R3D-1**（根级无扩展名文件 + 行区间 ⇒ 静默 fresh/15.0/rc=0，且为本次修复引入的回归） |
| P2 | 0 | — |
| P3 | 3 | R3D-2 / R3D-3 / R3D-4 |

**Blockers = 1。**

### 5.2 裁决：🔴 **阻断（不准予交付）**

**裁决理由**：

1. **R3-1 的指名场景真解了**（§2.1–2.3），R3-2/3/5 全部达成（§2.5），回归面 5/5 与测试卫生全绿（§2.6）——本轮不是"修复没做"，而是**修复把同一个洞换了个入口留着**。
2. R3D-1 与 R3-1 **失效形态完全同型**：合法锚点被 `invalid` 剔除 ⇒ 判定集失去该锚点 ⇒ 文档 `fresh` + 满分 15.0 + 默认 `--fail-on-drift` rc=0，而锚点文件**实际已改动**（旧版同夹具 `drifted/rc=1`，新版 `fresh/rc=0`）。这直接落在 `change-impact-matrix.md:30` 的 DoD 场景上，且是**回归**（旧判据显式支持 `:N` 后缀）。
3. 上一轮的 P1 定级依据（"默认门禁下静默 + 颁发满分 + 命中 DoD"）对 R3D-1 逐条成立；以"触发面窄"降级会把"同型缺陷"判成两套标准——而收口轮次的价值恰在于把这类"静默通道"清零。
4. 修复面极小（2-3 行：形态判断前剥行区间），具备同轮收口条件；不涉及契约重写。

### 5.3 放行条件（最小集）

1. **R3D-1（必须）**：`Makefile:2` / `LICENSE:3` / `Dockerfile:5-9` 恢复为真实锚点（改动⇒`drifted`、删除⇒`missing_anchor`），补 3 条回归测试；契约侧若选择"不支持该形态"，须在 RFC §4.2 显式声明并补"已知限制"测试（二者择一，不得留空）。
2. **R3D-2/3/4（可延后，但须登记）**：在计划 §9 追加三行（散文硬红的有意性、死正则清理、audit truth 透出 invalid），不得静默。
3. 复跑门槛与提交信息一致：`pytest → 212 passed`（209 + 3）、drift `rc=0`、links `rc=0`、control-sync `rc=0`、audit `PASS`。

---

## 6. 残留风险（Top 3）

1. **invalid 机制的"合法路径"边界仍在移动**：本轮把"含空格/中文/@/+"搬回来了，却漏掉"带行区间的无扩展名根文件"。判据是**字符类白名单**而不是"先 stat 再形态"，每加一种合法形态就要再补一次白名单——只要判定集剔除逻辑（`:183-188`）不变，任何一次白名单失配都会复现"静默满分"。根治方向：invalid 不再无条件退出判定集，或改为"存在即路径、不存在才判形态"（需要把 `repo_root` 传进 `normalize_anchor`，属结构改动，可另立 RFC）。
2. **墓碑只保护"声明不减少"，不保护"声明不降级"**：把 `src/x.py` 改成 `src/x.py `（加空格）或 `Makefile` 改成 `Makefile:2` 在多锚点文档里不触发墓碑（计数未减），却可能把锚点移出判定集。R3-1 与 R3D-1 都是这条通道的实例；后续任何"不可核验"分类扩容都会复用它。
3. **`missing_anchor` 的人读明细不含锚点名**（`check-doc-drift.py:562-564` 只打 `[bucket] doc`）：R3D-2 的硬红与 R3D-1 的误判都因此难以定位，作者只能开 `--json` 逐条翻 `anchors`。这是观测面债，不是本轮引入，但会放大任何判据争议的处理成本。

---

## 7. 附录：夹具清单与逐条复跑

| 脚本 | 覆盖 | 夹具数 |
| :--- | :--- | :--- |
| `/tmp/r3d/harness_unit.py` | 23 条锚点形态的 `normalize_anchor` 直调表（§2.2 单元面） | 0（纯函数） |
| `/tmp/r3d/harness_e2e.py` | A1–A3（含空格主场景）、B×6（CJK/`@`/`+`/反斜杠/拉丁/含空格目录）、C×3（散文）、D1–D6（反向风险）、D7（`Makefile:2`） | 13 |
| `/tmp/r3d/harness_gate.py` | D′/C′（写账本后的真实 rc）、D7′（掩蔽实测）、E1–E6（加粗变体） | 10 |
| `/tmp/r3d/harness_reg.py` | X（旧/新对照）、Y（假墓碑）、Z1–Z6（豁免留痕） | 8 |
| `/tmp/r3d/harness_v.py` | V1–V4（加粗写法变体）、W1–W3（文本输出原样） | 7 |
| `/tmp/r3d/harness_canon.py` | §2.1 的 A/A3 门禁原文 | 2 |

**关键命令（可逐条复跑）**：

```bash
# 回归面
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
python3 skills/doc-governance/scripts/check-doc-links.py
python3 skills/doc-governance/scripts/check-doc-control-sync.py
python3 skills/doc-governance/scripts/audit-doc-health.py
# 测试卫生（三数相等）
python3 skills/doc-governance/tests/test_doc_drift.py
python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q --collect-only | tail -1
# R3-1 复现与反向风险
python3 /tmp/r3d/harness_canon.py
python3 /tmp/r3d/harness_e2e.py
python3 /tmp/r3d/harness_v.py
# R3D-1 回归对照（旧/新）
python3 /tmp/r3d/harness_reg.py
```

---

**审查者签名**：Delta 复核审查者（独立上下文，Reviewer ≠ Author）
**裁决**：🔴 阻断 —— **Blockers = 1（R3D-1，P1）**；R3-1 指名场景与 R3-2/3/5 均达成，但同一 invalid 机制在"根级无扩展名文件 + 行区间"上仍可静默吞掉真实漂移，需按 §5.3 收口后方可放行。
