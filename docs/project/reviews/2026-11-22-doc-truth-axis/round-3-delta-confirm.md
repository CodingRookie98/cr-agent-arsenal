# R3D-1 修复确认审查（独立上下文 · Light 模式）
## 审查对象：`51e7d6a`（+ `2180b95` 文档重钉；会话期 HEAD `2906114` 仅动 `reviews/README.md`）

> **文档控制信息**
> - **文档标识**: REVIEW-R3D-CONFIRM-doc-truth-axis-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: R3D-1 修复确认审查者（独立上下文，Reviewer ≠ Author）
> - **生效日期**: 2026-11-22
> - **审查对象**: `51e7d6a`（fix(doc-governance): 收口 R3D-1 回归（行区间锚点被误判 invalid））。`git show --name-only 51e7d6a` = `check-doc-drift.py`、`audit-doc-health.py`、`test_doc_drift.py`、`round-3-delta.md`、RFC-0005、GOVERNANCE、计划；`2180b95` 仅 `docs/` 三处复核点重钉；`git diff --stat 2180b95..HEAD -- skills/` 为空 ⇒ 行为基线 = `51e7d6a`
> - **审查基线**: `round-3-delta.md`（28,721 B，sha256 `d855ebee0ac1c6864944ab00e3dccfa89e230a2248bbc6c220df3f0b05a9efcc` 实测与台账前 12 位 `d855ebee0ac1` 一致）
> - **契约依据**: RFC-0005 **V0.2.0**、GOVERNANCE **V1.7.10**、实施计划 **V1.8.0**（三处 `当前版本` 行实测逐字一致）
> - **审查模式**: 修复确认 · Light（只验五项：R3D-1 真解 / 新判据反向风险 / R3D-3·4 / 明细可定位性 / 回归面）
> - **取证方式**: 全部本机实跑。夹具建于 `/tmp/r3dc`（8 个临时 git 仓库 + 1 个变异体目录 + 4 个脚本，清单见 §6），提交时间用 `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` 钉死（`2026-11-20 / 11-21 / 11-22`）；旧版对照从 `git show 940b355:` / `49c6d55:` 导出到 `/tmp` 运行，**未改动任何受审文件**
> - **唯一写入面**: 本报告文件。仓库内零改动（`git status --porcelain` 开工 / 收工均为空）；无任何 git 写操作（`init/add/commit/rm` 全部发生在 `/tmp/r3dc/*` 夹具）
> - **环境**: Linux / Python 3.12.3 / pytest 7.4.4 / git 2.56.1 / 审定提交 `51e7d6ac87ec3219480bddab911ce8aa598b17bc`
> - **未验证项**: Windows 真实文件系统下反斜杠锚点的 stat 行为；CI 流水线（仓库无 `.github`，门禁全人工触发）；千篇级文档逐锚点 `git log` 的性能；`Dockerfile:5-9` 的**行号语义**（本轴只校验「文件是否变动」，行区间仅解析不使用，见 R3DC-1 说明）

---

## 0. 一句话结论

**五项全过，R3D-1 是真回归修复而非"换了个洞"**：`Makefile:2` / `LICENSE:3` / `Dockerfile:5-9` 恢复为真实锚点（`invalid_anchors=[]`），三个锚点文件**各自单独改动**均实测 `drifted` + `rc=1`，删除 `Makefile` 实测 `missing_anchor`；同夹具同提交下旧版 `940b355` 仍 `fresh/15.0/rc=0`（Delta 原文现象逐字复现），前 R3 版 `49c6d55` `drifted/rc=1` ⇒ 修复把语义**还原到 R3 之前**，且 36 条锚点形态的判定差分显示**唯一变化就是这 3 个行区间形态 invalid→path，没有任何形态反向退化为 invalid**。R3D-2 指名的 `见 3.2 节` / `A/B` / `N/A` / `v1.2` 实测落 `missing_anchor`（硬红），**未**变成 invalid 静默放行；R3D-3 死代码已删、R3D-4 的 truth 块已有 `invalid` + `invalid_docs`；明细行已带锚点名；回归面 `214 passed` + 四门禁全绿 + audit PASS(100.0)。

**Blockers = 0 → ✅ 准予交付。** 另登记 1×P2 + 3×P3 非阻断（含一条**同族窄口**：非 ASCII 无扩展名根文件 + 行区间仍落 invalid，属 `940b355` 遗留而非本次引入）。

---

## 1. ① 命令与关键输出

### 1.1 判定矩阵：同一形态在三个版本下的结果（`normalize_anchor` 直调，36 形态）

```console
$ python3 /tmp/r3dc/forms.py
form                   49c6d55                940b355                HEAD                       change(940->HEAD)
Makefile:2             path(Makefile:2-2)     invalid                path(Makefile:2-2)        *** CHANGED
LICENSE:3              path(LICENSE:3-3)      invalid                path(LICENSE:3-3)         *** CHANGED
Dockerfile:5-9         path(Dockerfile:5-9)   invalid                path(Dockerfile:5-9)      *** CHANGED
Makefile               path(Makefile)         path(Makefile)         path(Makefile)
LICENSE                path(LICENSE)          path(LICENSE)          path(LICENSE)
Makefile:2-            path(Makefile:2-)      invalid                invalid
Makefile:2-9-10        path(Makefile:2-9-10)  invalid                invalid
src/a.py:10-20         path(src/a.py:10-20)   path(src/a.py:10-20)   path(src/a.py:10-20)
docs/my file.md        path(docs/my file.md)  path(docs/my file.md)  path(docs/my file.md)
中文/文档.md             path(中文/文档.md)       path(中文/文档.md)       path(中文/文档.md)
a@b.py / c+d.py        path                   path                   path
src\a.py               path(src/a.py)         path(src/a.py)         path(src/a.py)
src/** / *.py          unverifiable           unverifiable           unverifiable
见 3.2 节               path(见 3.2 节)         path(见 3.2 节)         path(见 3.2 节)
A/B · N/A · v1.2       path                   path                   path
见附录 A / see appendix A  path               invalid                invalid
附录A:3 · 说明:3        path(附录A:3-3)         invalid                invalid
/abs/path.py · C:\x\y.py · ../escape.py   DROPPED  DROPPED              DROPPED
```

**差分结论**：`940b355 → HEAD` 只有 3 条变化，全部是 `invalid → path`（R3D-1 的三个指名形态）；**零条 `path → invalid`**，即修复没有把任何原本可核验的锚点推进 invalid 黑洞。`49c6d55 → 940b355` 共 9 条形态发生退化：本轮修回 **3 条良构行区间**（`Makefile:2` / `LICENSE:3` / `Dockerfile:5-9`）；**2 条畸形区间**（`Makefile:2-` / `Makefile:2-9-10`）与 **2 条非 ASCII 行区间**（`附录A:3` / `说明:3`）仍为 invalid（见 R3DC-1）；余下 **2 条散文**（`见附录 A` / `see appendix A`）按 R3D-2 有意保留 invalid。

### 1.2 R3D-1 真解：三个锚点文件**各自隔离**改动（每夹具独立建库）

```console
$ bash /tmp/r3dc/isolate.sh
=== 隔离夹具：仅改 Makefile ===
  pre : rc=0 status=fresh
  post: rc=1 status=drifted  (期望 drifted / rc=1)
  anchors: [('seed.txt', None, None), ('Makefile', 2, 2), ('LICENSE', 3, 3), ('Dockerfile', 5, 9)] invalid: []
=== 隔离夹具：仅改 LICENSE ===
  pre : rc=0 status=fresh
  post: rc=1 status=drifted  (期望 drifted / rc=1)
  anchors: [('seed.txt', None, None), ('Makefile', 2, 2), ('LICENSE', 3, 3), ('Dockerfile', 5, 9)] invalid: []
=== 隔离夹具：仅改 Dockerfile ===
  pre : rc=0 status=fresh
  post: rc=1 status=drifted  (期望 drifted / rc=1)
  anchors: [('seed.txt', None, None), ('Makefile', 2, 2), ('LICENSE', 3, 3), ('Dockerfile', 5, 9)] invalid: []
```

删除形态（`git rm Makefile`，5 阶段矩阵 E）：HEAD / 49c6d55 均 `missing_anchor=2`、`rc=1`；940b355 仍 `guide.md=fresh`、`pure.md=unverified`（无 missing 信号）。

### 1.3 Delta 原文现象的最小复现（同夹具、同提交、仅换脚本）

```console
$ bash /tmp/r3dc/step2.sh          # 文档锚点：seed.txt, Makefile:2；基线由「该版本自己」写出（复现现场）
--- [pre-change] 49c6d55 rc=0   status=fresh   invalid=None              paths=['seed.txt','Makefile'(2-2)]
--- [pre-change] 940b355 rc=0   status=fresh   invalid=['Makefile:2']    paths=['seed.txt','Makefile:2']
--- [pre-change] HEAD    rc=0   status=fresh   invalid=[]                paths=['seed.txt','Makefile'(2-2)]

>>> 改动 Makefile 并提交（锚点文件已被改）<<<
--- [POST-change] 49c6d55 rc=1  status=drifted
--- [POST-change] 940b355 rc=0  status=fresh   score=15.0  invalid=['Makefile:2']   <-- Delta 原文现象逐字复现
--- [POST-change] HEAD    rc=1  status=drifted
```

⇒ **旧版 `fresh/15.0/rc=0`、新版 `drifted/rc=1`、前 R3 版 `drifted/rc=1`**：三行同时成立，证明这是**回归修复**（把 `940b355` 的退化还原到 `49c6d55` 语义），而不是用新判据换了个洞。

### 1.4 新测试是否真钉住回归（变异测试：把脚本换回 `940b355`）

```console
$ cp -a tests/ scripts/ /tmp/r3dc/mut/skills/doc-governance/ && 用 940b355 覆盖两个脚本
$ cd /tmp/r3dc/mut && python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q -k TestR3DFixes
FAILED ...::TestR3DFixes::test_r3d_1_line_range_anchor_still_detects_drift
FAILED ...::TestR3DFixes::test_r3d_1_root_level_file_with_line_range_is_a_path
FAILED ...::TestR3DFixes::test_r3d_3_prose_hint_dead_code_removed
FAILED ...::TestR3DFixes::test_r3d_4_audit_truth_block_exposes_invalid
FAILED ...::TestR3DFixes::test_r3d_missing_detail_names_the_anchor
5 failed, 48 deselected in 1.61s
```

5/5 新用例在旧代码上全红 ⇒ 回归测试有效，非"写完即绿"的装饰用例（`48+5=53` 与文件内用例总数自洽）。

### 1.5 反向风险：剥行区间后散文会不会被放行

```console
$ cd /tmp/r3dc/probe-forms2 && python3 .../check-doc-drift.py --root docs --repo . --fail-on-drift
🔍 文档代码锚点漂移检测: root=/tmp/r3dc/probe-forms2/docs repo=/tmp/r3dc/probe-forms2
📊 声明 2/2 篇（覆盖度 100.0%）｜fresh 0｜drifted 0｜missing 1｜stale 0｜unverified 1
🎯 真值分: 0.0 / 15
   - [missing_anchor] forms.md  ←  seed.txt, 见 3.2 节, A/B, N/A, v1.2, 见附录 A, see appendix A
   - [unverified] prose-only.md  ←  见附录 B
   ⚠️  invalid 锚点（不像路径，无法机械核验；请改写为仓库内相对路径）:
      - forms.md: 见附录 A, see appendix A
      - prose-only.md: 见附录 B
rc=1
```

- `见 3.2 节` / `A/B` / `N/A` / `v1.2` → **`missing_anchor`（硬红、rc=1）**，未进 invalid 名单 ⇒ **不会静默放行**（且 `940b355` 对同四条的判定与 HEAD 完全一致，非本轮引入）。
- 真散文 `见附录 A` / `see appendix A` → `invalid`，且**文本可见**、同文档其它锚点照常判 `missing_anchor`（不短路整篇，R2D56-1 语义保持）。
- 反向兜底：任何「剥行区间后像标识符」的散文（如 `Appendix:3`）会落 `path → missing_anchor` 硬红，方向是 fail-loud 而非静默。

### 1.6 R3D-3 / R3D-4

```console
$ grep -rn "_PROSE_HINT" . --include='*.py' --include='*.md'
./skills/doc-governance/tests/test_doc_drift.py:1082:        self.assertFalse(hasattr(self.mod, "_PROSE_HINT"))
./docs/project/reviews/.../round-3-delta.md:302/306          # 历史报告文本
./docs/proposals/RFC-0005-doc-truth-axis.md:19               # 修订记录文本
```

⇒ 脚本内**零残留**，仅剩"断言其不存在"的测试与历史文档文本。

```console
$ python3 audit-doc-health.py（夹具 probe-forms2，truth 块）
{ "mode": "warn", "enabled": true, "declared": 2, "missing_anchor": 1, "unverified": 1,
  "freshness_score": 0.0, "drift_docs": [], "missing_anchor_docs": ["forms.md"],
  "invalid": 2, "invalid_docs": ["forms.md", "prose-only.md"] }
```

文本面（`audit-doc-health.py` 输出原文）：

```console
🎯 [真值轴 · 代码锚点漂移]:
   * 声明覆盖: 2/2 篇 (100.0%)｜fresh 0｜drifted 0｜missing 1｜stale 0｜unverified 1
   * 真值分: 0.0 / 15
      - [missing_anchor] forms.md
   * invalid 锚点文档: 2 篇（无法机械核验，需改写为仓库内相对路径）
```

⇒ truth 块**同时含计数（`invalid`）与文档列表（`invalid_docs`）**；文本面透出**计数**（篇名仅 JSON/漂移脚本可见，见 R3DC-3）。

### 1.7 明细可定位性（missing / drifted / unverified 三种文本行原文）

```console
   - [drifted] guide.md  ←  seed.txt, Makefile
   - [missing_anchor] forms.md  ←  seed.txt, 见 3.2 节, A/B, N/A, v1.2, 见附录 A, see appendix A
   - [unverified] prose-only.md  ←  见附录 B
```

⇒ 每个桶的明细行都带**锚点名**（`check-doc-drift.py:567-570`），Delta R3D-2「作者只能开 `--json` 定位」的观测面债已收口。

### 1.8 回归面

```console
$ python3 -m pytest skills/doc-governance/tests -q
214 passed in 24.41s
$ python3 -m pytest skills/doc-governance/tests -q --collect-only | tail -1
214 tests collected in 0.09s

$ for f in test_*.py; do python3 "$f"; done            # 直接执行
test_doc_drift.py                      ran=53  OK
test_doc_governance_scripts.py         ran=78  OK
test_doc_index_convention.py           ran=43  OK
test_llms_txt_hardening.py             ran=19  OK
test_manage_backlog_close_contract.py  ran=10  OK
SUM_DIRECT=203                                         # ≠ 214，见 R3DC-2

$ check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 3/46 篇（覆盖度 6.5%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15                                          rc=0
$ check-doc-links.py --root docs
📊 审计汇总: 共扫描 95 个 Markdown 文件 ✅ 100% 物理有效        rc=0
$ check-doc-control-sync.py --root docs
📊 扫描汇总: 共检查 47 个 Markdown 文件 ✅ 100% 一致            rc=0
$ audit-doc-health.py --root docs --repo .
🏁 诊断结论: PASS (健康度达标，准予交付) ✅   总得分 100.0/100   rc=0
```

**重复测试类**：逐文件 `grep -oE "^class [A-Za-z_0-9]+" | sort | uniq -d` 全仓库**零命中** ⇒ R3 轮删除的重复类未回流。

---

## 2. ② 五项逐条结论

| # | 验收项 | 期望 | 实测 | 结论 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `Makefile:2` / `LICENSE:3` / `Dockerfile:5-9` 判为路径；改动后 `drifted`+rc=1；与旧版对照 | `invalid=[]`、改动即红、旧版复现漏检 | 三形态全部 `path`（行区间解析为 `2-2 / 3-3 / 5-9`）、`invalid=[]`；**三个文件各自隔离改动**均 `fresh/rc=0 → drifted/rc=1`；删除 `Makefile` → `missing_anchor/rc=1`；旧 `940b355` 同夹具仍 `fresh/15.0/rc=0`，前 R3 版 `49c6d55` `drifted/rc=1` | ✅ **真回归修复**（还原至 R3 前语义，非换洞） |
| 2 | 剥行区间是否把散文放行（`见 3.2 节`/`A/B`/`N/A`/`v1.2`） | 不得变 invalid 静默 | 四条全部 `path → missing_anchor`（rc=1，文本可见）；`940b355` 对同四条判定相同 ⇒ 非本轮引入；真散文仍 `invalid` 且文本/JSON/audit 三面可见；36 形态差分**零条 path→invalid** | ✅ 无静默放行（P3 假红维持"有意"口径） |
| 3 | R3D-3 死代码删除 / R3D-4 audit truth 块含 invalid 计数与列表且文本可见 | 二者成立 | `_PROSE_HINT` 脚本内零残留（仅测试断言其不存在）；truth 块 `invalid=2` + `invalid_docs=["forms.md","prose-only.md"]`，文本打印 `invalid 锚点文档: 2 篇` | ✅ 达成（篇名文本面缺口 → R3DC-3，P3） |
| 4 | missing/drifted 文本行含锚点名 | 可定位 | 三种桶明细均带 `← <锚点名列表>`（`:567-570`） | ✅ |
| 5 | `pytest` 全绿；直接执行用例数 == pytest 收集数；四门禁 | 全绿且计数自洽 | `214 passed` = `214 collected`；**直接执行 203 ≠ 214**（11 例模块级 pytest 函数，`unittest.main()` 不跑）；drift `rc=0`、links `rc=0`、control-sync `rc=0`、audit `PASS 100.0` | ⚠️ 门禁全绿、**计数不自洽**（R3DC-2，P3，pre-existing） |

---

## 3. ③ 新缺陷

### R3DC-1 【P2 · 非阻断 · 同族窄口未清，非本次引入】非 ASCII 无扩展名根文件 + 行区间仍落 invalid

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/scripts/check-doc-drift.py:63`（`_LINE_RANGE = :\d+(?:-\d+)?$`，只剥**良构**区间）、`:66-76`（`_PATH_TOKEN` 仍是 ASCII 白名单 `[A-Za-z0-9._@+~\-]+`）、`:101-103`（不像路径 ⇒ invalid ⇒ 退出判定集） |
| **现象** | `说明:3` / `附录A:3`（剥区间后是**非 ASCII** 无扩展名根文件名）→ `invalid`；`Makefile:2-` / `Makefile:2-9-10`（畸形区间）→ `invalid`。二者都被 `decidable` 剔除，同文档其它锚点 fresh 时整篇 `fresh` + 15.0 + `rc=0`，与 R3D-1 失效形态**完全同型** |
| **证据** | §1.1 矩阵：`附录A:3`/`说明:3` 在 `49c6d55` 为 `path(附录A:3-3)`，在 `940b355` 与 **HEAD** 均为 `invalid`；`Makefile:2-` 同理（`49c6d55` → `path` → `missing_anchor` 硬红，HEAD → `invalid` 静默） |
| **为何定 P2 而非 P1** | ① **不是本次修复引入**：`940b355` 即已如此（`git show 940b355:…` 实测），本轮 `51e7d6a` 未扩大该面；② 该形态**不在 RFC-0005 V0.2.0 §4.2 已写死的判据内**（判据为「无 `/`、无扩展名点、且整体不是**标识符形态**」，ASCII 白名单即其实现），属"契约与实现一致的已知边界"而非"未登记静默洞"；③ Delta 的放行条件只点名良构 `Makefile:2 / LICENSE:3 / Dockerfile:5-9`，已 100% 达成；④ 仓库零实例（根级无扩展名文件仅 `LICENSE`，3 篇声明文档均未锚定它） |
| **升级条件（诚实标注）** | 若项目口径是「**任何**被判 invalid 的真实路径都等同 R3D-1」（即失效形态优先于触发概率），则本条应升 P1；升级后与 R3D-1 的差别仅在"触发面更窄 + 契约已声明"两点 |
| **最小修复** | `_PATH_TOKEN` 改用 `[\w.@+~\-]+`（`re.UNICODE`，覆盖 CJK 标识符）+ `_LINE_RANGE` 放宽为 `:\d+(?:-\d*)?$`；补 2 条测试（`说明:3` 改动 ⇒ drifted；`Makefile:2-` ⇒ missing_anchor 而非 invalid）。**根治方向**（同 Delta §6 残留风险 1）：invalid 不再无条件退出判定集，或改为「存在即路径，不存在才判形态」 |

### R3DC-2 【P3 · 非阻断 · pre-existing】直接执行测试文件少 11 例（`unittest.main()` 不跑模块级 pytest 函数）

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/tests/test_doc_governance_scripts.py` 的 11 个模块级 `def test_*(tmp_path)`（如 `:1` 起的 `test_dir_escaping_root_is_usage_error`、`test_verdict_single_source_passes_clean_result`），文件尾用 `unittest.main()` 收口 |
| **证据** | §1.8：`SUM_DIRECT=203` vs `214 collected`；集合差分精确列出 11 条（`pytest 有 / unittest 无 = 11`，反向差集为 0）；`git show 940b355:…test_doc_governance_scripts.py | grep -c "^def test_"` = **11** ⇒ 该缺口在本次修复前已存在 |
| **影响** | 只用 `python3 test_x.py` 跑测试的人会漏 11 例（含 `verdict` 单源、`--dir` 逃逸等门禁相关断言），**pytest 面不受影响**（CI/门禁口径全绿） |
| **建议** | 文件尾改 `if __name__ == "__main__": sys.exit(pytest.main([__file__, "-q"]))`，或把这 11 个函数收进 `unittest.TestCase`；并在测试卫生条款里把"三数相等"的检查脚本化 |

### R3DC-3 【P3 · 非阻断】audit 文本面只透出 invalid 计数，不给篇名

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/scripts/audit-doc-health.py:811-812`（`print(f"   * invalid 锚点文档: {truth['invalid']} 篇（…）")`，未遍历 `truth['invalid_docs']`）；同文件 `:804-807` 的 missing/drifted 明细同样不带锚点名 |
| **证据** | §1.6 文本原文：`invalid 锚点文档: 2 篇`，篇名只在 `truth["invalid_docs"]`；对照 `check-doc-drift.py:567-580` 已同时打印篇名 + 锚点名 |
| **影响** | 只看 `audit-doc-health` 文本的评审者知道"有 2 篇"，仍需二次运行漂移脚本或开 JSON 才能定位；属观测面不一致，非判定错误 |
| **建议** | 文本面补 `invalid_docs` 前 5 条（与 `drift_docs` 同款 `[:5]` 截断）；`audit` 的 missing/drifted 明细也补锚点名，与漂移脚本对齐 |

### R3DC-4 【P3 · 非阻断 · 过程】审查报告被修复提交顺带纳入

| 项 | 内容 |
| :--- | :--- |
| **位置** | `51e7d6a` 的 `--name-only` 含 `docs/project/reviews/2026-11-22-doc-truth-axis/round-3-delta.md`（+14/-14） |
| **证据** | `git show 51e7d6a -- round-3-delta.md` 内容 = 该报告自述的"两处数字订正（夹具数、numstat）+ HEAD 推进说明"，与报告正文声明一致，**无结论篡改**（R3D-1 判定、P1 定级、§5.3 放行条件均未被改动） |
| **影响** | 审查产物与被审代码同提交，违反"证据与被审对象分离"的洁净度；未来若有人 `git show 51e7d6a` 核证修复，会把审查者的未提交订正误读为修复者改写 |
| **建议** | 审查报告单独提交（或至少单独 commit message 声明"纳入审查者未提交订正"）；后续轮次注意工作区里 reviewer 的未暂存改动 |

> **已排查并主动驳回的疑点**（避免下一轮误判）：`51e7d6a` 同时删掉了 `RFC-0005` 的 `V0.1.5` 行与 `GOVERNANCE` 的 `V1.7.5` 行，初看像"修订历史被抹"。核对后为**规则要求**：`audit-doc-health.py:8` 明确"修订历史滑动窗口合规率（<= 5 条）"，两份文档原本各 5 行，新增 1 行必须裁掉最旧 1 行，删除项恰为最旧行 ⇒ 合规，`check-doc-control-sync` `rc=0` 亦印证。

---

## 4. ④ 裁决

### 4.1 计数

| 定级 | 计数 | 编号 |
| :--- | :--- | :--- |
| P0 | 0 | — |
| **P1（Blocker）** | **0** | — |
| P2 | 1 | R3DC-1（非 ASCII 无扩展名根文件 + 行区间仍落 invalid；pre-existing、契约已声明边界） |
| P3 | 3 | R3DC-2（直接执行少 11 例）/ R3DC-3（audit 文本无 invalid 篇名）/ R3DC-4（报告被顺带纳入） |

**Blockers = 0。**

### 4.2 裁决：✅ **准予交付（R3D-1 真解）**

裁决理由：

1. **R3D-1 的失效形态已被连根拔掉**：三个指名锚点形态 `invalid → path`，且**三个锚点文件各自隔离改动**都实测 `drifted/rc=1`、删除实测 `missing_anchor/rc=1`——不是"某条路径碰巧能过"，而是判定集真正重新纳入了这些锚点。
2. **是回归修复，不是换洞**：同夹具同提交下 `940b355` 仍 `fresh/15.0/rc=0`（Delta 现象逐字复现），`HEAD` 与 `49c6d55` 同为 `drifted/rc=1`；36 形态差分显示 `940b355→HEAD` **只有 3 条 invalid→path、零条 path→invalid**。
3. **回归测试有效**：新增 `TestR3DFixes` 5 条在 `940b355` 上 **5/5 全红**，不存在"写完即绿"。
4. **反向风险未扩大**：`见 3.2 节`/`A/B`/`N/A`/`v1.2` 一律硬红（`missing_anchor`），真散文仍 invalid 且三面可见——判据没有向"静默放行"方向滑。
5. **门禁面全绿**：`214 passed` / drift `rc=0`（3 篇 fresh、15.0）/ links `rc=0`（95 文件）/ control-sync `rc=0`（47 文件）/ audit `PASS 100.0`。
6. 剩余 1×P2 + 3×P3 均为**非阻断**且已给最小修复与升级条件；其中 P2 明确不是本次修复引入，按"不移动球门"原则不阻断本轮。

### 4.3 放行后建议（不阻断）

1. **R3DC-1（P2）**：下一轮把 `_PATH_TOKEN` 放宽到 `\w`（UNICODE）+ 放宽畸形区间，补 2 条测试；同时在 RFC §4.2 把"非 ASCII 无扩展名根文件名 + 行区间"显式写成**已知限制**（二者择一，不得留空）。
2. **R3DC-2（P3）**：测试文件尾改用 `pytest.main`，让"直接执行 == 收集"重新成立。
3. **R3DC-3（P3）**：audit 文本补 invalid 篇名（`[:5]` 截断）与 missing/drifted 锚点名。
4. **归档簿记（实测已确认不影响门禁）**：`reviews/README.md` 的 `round-3-delta-confirm.md` 行仍是纯文本（"（待落盘）"）。本报告落盘后复跑四门禁：drift `rc=0`（3/46，15.0）、links `rc=0`（**95 文件，与本报告落盘前同数**）、control-sync `rc=0`（47 文件）、audit `PASS 100.0`（孤儿 `0/94`、总文件数 94 未变）——原因是 `project/reviews/**` 属**交付凭据归档**，被 `audit-doc-health.py:34` 与 `check-doc-links.py:26` 的 `EVIDENCE_ARCHIVE_PARTS` 整体排除。故 README 清单行**不是门禁项**，仅影响人类可点击性，按本会话"禁止改仓库文件"约束我未改；主调度补一行链接即可。

---

## 5. 残留风险（Top 3）

1. **invalid 判据仍是"字符类白名单"而非"先 stat 后判形态"**：R3-1（含空格/中文）→ R3D-1（行区间）→ R3DC-1（非 ASCII/畸形区间）已是**第三次同族事故**。只要 invalid 仍无条件退出判定集（`:183-190`），每次白名单失配都会复现"静默满分 + 默认门禁 rc=0"。根治需结构改动（把 `repo_root` 传进 `normalize_anchor`，或 invalid 不再剔除判定集），建议单独立 RFC。
2. **契约文字与实现的边界未对齐**：RFC §4.2 用"标识符形态"表述，实现是 ASCII 白名单（`_PATH_TOKEN`）；`说明:3` 这类"合法但非 ASCII"的文件名因此落在契约文字的灰区。文字不写死，下一轮还会被不同审查者判成不同等级。
3. **观测面仍有两处"必须开 `--json` 才看得全"**：audit 文本只给 invalid 计数（R3DC-3）、`missing_anchor` 的 audit 明细不带锚点名；而测试执行口径 `203 ≠ 214`（R3DC-2）意味着"直接跑测试文件"的读者会低估覆盖。三处都是"证据可得性"债，会在下一次判据争议里放大处理成本。

---

## 6. 附录：夹具与逐条复跑

| 路径 | 覆盖 |
| :--- | :--- |
| `/tmp/r3dc/scripts/drift-{49c6d55,940b355,HEAD}.py` | 三个版本对照体（sha256 见 §6.1） |
| `/tmp/r3dc/forms.py` | 36 条锚点形态 × 3 版本判定差分（§1.1） |
| `/tmp/r3dc/isolate.sh` | 三夹具隔离改动（§1.2），3 个临时 git 仓库 |
| `/tmp/r3dc/step2.sh` | Delta 最小复现 + audit truth 探针（§1.3 / §1.6），2 个仓库 |
| `/tmp/r3dc/matrix.sh` | 5 阶段（pre / Makefile / LICENSE / Dockerfile / rm）× 3 版本（§1.2 删除形态） |
| `/tmp/r3dc/probe.sh` | 反向风险探针（§1.5） |
| `/tmp/r3dc/mut/` | 变异体：`940b355` 脚本 + HEAD 测试（§1.4） |
| 夹具合计 | **8 个临时 git 仓库** + 1 变异体目录；`/tmp` 内 `init/add/commit/rm` 共 40+ 次 |

### 6.1 对照体指纹（便于复算）

```console
1fdf6764…  /tmp/r3dc/scripts/audit-HEAD.py
040faf84…  /tmp/r3dc/scripts/drift-49c6d55.py
21a18229…  /tmp/r3dc/scripts/drift-940b355.py
3f970a7e…  /tmp/r3dc/scripts/drift-HEAD.py      (= 仓库内 51e7d6a 版，逐字节一致)
```

### 6.2 关键命令（可逐条复跑）

```bash
# 判定矩阵与真解
python3 /tmp/r3dc/forms.py
bash /tmp/r3dc/isolate.sh
bash /tmp/r3dc/step2.sh
# 反向风险
bash /tmp/r3dc/probe.sh
# 回归测试有效性（变异）
cp -a skills/doc-governance/{tests,scripts} /tmp/r3dc/mut/skills/doc-governance/ \
  && git show 940b355:skills/doc-governance/scripts/check-doc-drift.py > /tmp/r3dc/mut/skills/doc-governance/scripts/check-doc-drift.py \
  && (cd /tmp/r3dc/mut && python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q -k TestR3DFixes)
# 回归面
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
```

---

**审查者签名**：R3D-1 修复确认审查者（独立上下文，Reviewer ≠ Author）
**裁决**：✅ **准予交付 —— Blockers = 0**；R3D-1 真解且经旧版对照证明为回归修复（非换洞），R3D-2/3/4 与明细可定位性全部达成，回归面全绿；另登记 1×P2（R3DC-1，同族窄口，pre-existing）+ 3×P3 非阻断。
