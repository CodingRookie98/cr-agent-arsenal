# 定向单轮红队审查（Maintenance-Patch 通道 P4 · Light 模式）
## 计划 §9 四项收口（R2D56-1 / R2D56-3 / R2D56-4 / R2D56-2）

> **文档控制信息**
> - **文档标识**: REVIEW-R3-FOLLOWUP-LIGHT-doc-truth-axis-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: 定向单轮红队审查者（独立上下文，Reviewer ≠ Author）
> - **生效日期**: 2026-11-22
> - **审查对象**: `4545b55`（fix: 收口计划 §9 四项）+ `5818d07`（仅文档：复核点重钉）
> - **审查基线**: `49c6d55`（真值轴交付收尾，终审 Blockers=0）
> - **审查边界**: **只审** `git diff 49c6d55..HEAD -- skills/`；不越界审计历史代码，不重审已裁决项
> - **契约依据**: RFC-0005 V0.1.8、GOVERNANCE V1.7.8、实施计划 V1.6.0 §9
> - **审查模式**: Light（定向单轮；五项定点穿透 + 回归面）
> - **取证方式**: 全部结论为本机实跑。夹具仓库建于 `/tmp/r3fu` `/tmp/r3fu2` `/tmp/r3fu3` `/tmp/r3fu4` `/tmp/r3fu5`（共 26 个夹具仓库），提交时间用 `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` 钉死，不依赖"同秒提交"的偶然性
> - **唯一写入面**: 本报告文件（未提交）；仓库工作区开工 `git status --porcelain` 为空，落盘前仍为空
> - **git 写操作**: 无（仓库内零写；`init/add/commit/rm` 全部发生在 `/tmp/r3fu*` 夹具仓库）
> - **环境**: Linux / Python 3.12.3 / git 2.56.1 / HEAD = `5818d072719c6101f7572501158cd0629307f5d0`
> - **未验证项**: Windows 反斜杠路径在真实 Windows 文件系统下的 stat 行为（本轮以 POSIX 夹具 + 归一化逻辑静态推演）；CI 流水线（仓库无 `.github`，门禁全为人工触发）；千篇级文档下逐锚点 `git log` 的性能

---

## 0. 一句话结论

四项修复在**其自身声明的验收点**上全部实测通过（R2D56-1 的判定集剔除、R2D56-3 的加粗剥离、R2D56-4 的散文不硬红、R2D56-2 的豁免留痕，逐条有原始输出）；**但 R2D56-4 的实现是过度矫正**：路径形态白名单 `[A-Za-z0-9._/\-]+` 把**合法路径**（含空格、中文、`@`、反斜杠、非 ASCII 拉丁字母）一并归为 `invalid`，再被 R2D56-1 新引入的"判定集剔除"机制静默丢弃——结果是**锚点文件被删除后，文档仍判 `fresh`、真值分 15.0/15、默认门禁 `--fail-on-drift` rc=0**（D1 实测），而等价的无空格路径同场景 rc=1（D2 对照）。

这正是真值轴存在的理由（`change-impact-matrix.md` 第 30 行 DoD 场景："被锚定路径改动/移动/删除"）被静默击穿。**Blockers = 1（R3-1，P1）→ 阻断**，其余 4 条为 P2/P3 非阻断。

---

## 1. 会话与基线事实

| 项 | 值 |
| :--- | :--- |
| 分支 | `feat/doc-truth-axis` |
| 开工 / 收工 HEAD | `5818d07`（会话期间无新提交） |
| 审定增量（skills/） | `4545b55`：`check-doc-drift.py` +46/-7、`test_doc_drift.py` +187 |
| 审定增量（docs/，仅作契约依据，不判定） | `docs/GOVERNANCE.md` +6/-3、`docs/proposals/RFC-0005-doc-truth-axis.md` +7/-2、计划 §9 +14/-4、设计书 2 行 |
| 工作区 | `git status --porcelain` 开工 0 行；本报告落盘前仍 0 行 |
| 受控文件改动 | 无（本报告为唯一写入，且不提交） |

> **边界声明（诚实标注）**：`docs/` 的重钉与契约行（RFC-0005 V0.1.8 §4.2 新增的「不可核验锚点 / 加粗锚点 / 豁免留痕」三行）**不在本轮判定范围**，仅在 §3.3 作为"实现忠实于错误规则"的定性依据被引用；本轮所有缺陷计数只落在 `skills/` 的实现与测试上。

---

## 2. ① Diff 边界

### 2.1 边界实测

```console
$ git diff --stat 49c6d55..HEAD -- skills/
 skills/doc-governance/scripts/check-doc-drift.py |  46 +++++-
 skills/doc-governance/tests/test_doc_drift.py    | 187 +++++++++++++++++++++++
 2 files changed, 226 insertions(+), 7 deletions(-)
```

边界干净：**只有 2 个文件、无文件模式变更**（`git ls-files -s` → `100644`）、无新增依赖、无新增写文件路径、`skills/` 下无其它脚本被波及。`audit-doc-health.py` 零改动，但其 `truth` 块的数据源 `analyze()` 返回值新增了两个键（见 2.2），属"只增键"兼容改动。

### 2.2 改动点清单（逐行定位）

| # | 位置 | 改动 | 对应项 |
| :--- | :--- | :--- | :--- |
| 1 | `check-doc-drift.py:41` | 新增 `_PATH_SHAPE = re.compile(r"[A-Za-z0-9._/\-]+(?::\d+(?:-\d+)?)?")` | R2D56-4 |
| 2 | `check-doc-drift.py:68-73` | 新增"整体加粗"剥离：`re.fullmatch(r"\*\*(.+)\*\*", text)` 且内部无 `*` 才剥离 | R2D56-3 |
| 3 | `check-doc-drift.py:77-79` | glob 分支返回值新增 `"invalid": False`（键补齐） | R2D56-1/4 |
| 4 | `check-doc-drift.py:80-83` | 新增 `invalid` 分支：`not _PATH_SHAPE.fullmatch(text)` ⇒ `unverifiable=True, invalid=True` | R2D56-4 |
| 5 | `check-doc-drift.py:96` | 正常路径分支返回值新增 `"invalid": False` | — |
| 6 | `check-doc-drift.py:160-170` | `classify_doc` 由"任一不可核验即整篇 `unverified` 短路"改为"构造 `decidable` 索引集，只对可核验锚点判定" | R2D56-1 |
| 7 | `check-doc-drift.py:426-427` | 文档记录新增 `invalid_anchors` / `unverifiable_anchors` 两个数组 | R2D56-4/1 |
| 8 | `check-doc-drift.py:555-563` | `--allow-unverified` 生效时强制打印豁免行；`--json` 时走 stderr | R2D56-2 |
| 9 | `test_doc_drift.py:798-890` | 新增 `TestFollowupP2P3`（4 条）——**从未被收集，见 R3-4** | 回归测试 |
| 10 | `test_doc_drift.py:891-985` | 同名 `TestFollowupP2P3` 第二次定义（4 条）——生效版本 | 回归测试 |

### 2.3 边界外但影响判定的耦合点（仅登记，不计缺陷）

- `audit-doc-health.py` 的 `truth_block`（:677-699）**未透出** `invalid_anchors` / `unverifiable_anchors`，因此 R2D56-4 引入的 `invalid` 语义在健康报告面不可见（见 R3-3）。
- `check-doc-links.py` / `check-doc-control-sync.py` 与本 diff 无数据耦合，仅作回归面复验。

---

## 3. ② 五项逐条结论

### 3.1 R2D56-1 是否真解 —— **结论：真解（4/4 + 墓碑 1/1 通过）**

**夹具构造**：`git init` 后以 `GIT_AUTHOR_DATE` 钉死提交时间（init `2026-11-01` / doc `2026-11-02` / 漂移 `2026-11-10`），`复核于` 用日期型（`2026-11-05` 制造漂移、`2026-11-20` 制造新鲜），避免依赖同秒提交。

```console
$ python3 /tmp/r3fu_harness.py
[F1 drift+glob]     rc=0 status=drifted        anchors=['src/x.py','src/**']    unver=['src/**'] invalid=[]
[F2 missing+glob]   rc=0 status=missing_anchor anchors=['src/gone.py','src/**'] unver=['src/**'] invalid=[]
[F3 glob-only]      rc=0 status=unverified     anchors=['src/**']               unver=['src/**'] invalid=[]
[F4 tombstone-glob] rc=0 status=fresh anchors=['src/x.py'] removed=1 base=ok
  fail-on-drift rc= 1 | ['   ⛔ 基线墓碑违规（声明被删除/缩减）:', '      - d.md 缺失: src/**']
```

| 验收点 | 期望 | 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| 同文档「真实锚点 + glob」，真实锚点漂移 | `drifted` | `drifted`（summary.drifted=1） | ✅ |
| 同文档「真实锚点缺失 + glob」 | `missing_anchor` | `missing_anchor` | ✅ |
| 仅 glob | `unverified` | `unverified` | ✅ |
| glob 锚点登记进基线后删除 | 墓碑违规 + rc=1 | `removed_from_baseline=1`、`缺失: src/**`、rc=1 | ✅ |

**墓碑穿透复核（重点）**：`--write-baseline` 写入的是 `a["path"]`，**glob 锚点确实进账本**：

```json
{ "docs": { "d.md": [ "src/**", "src/x.py" ] }, "version": 1 }
```

删除该声明后 `_removed_from_baseline` 按全局多重集计出缺口 → `removed=1` → rc=1。**glob 不能借"不可核验"逃出墓碑**，R2D56-1 的修复没有在墓碑侧开口子。

**代码面复核**：`classify_doc:160-170` 的 `decidable` 索引集由 `analyze()` 同源构造的 `unverifiable` 掩码驱动，长度恒等于 `anchor_paths`（同一次 `for anchor in anchors` 循环 append），无 `IndexError` 面；`decidable` 为空时显式返回 `unverified`（F3 覆盖）。

**残留（不构成缺陷，属设计取舍）**：被剔除的不可核验锚点**永远不参与任何判定**，只出现在 `unverifiable_anchors` 数组里。这本身是 R2D56-1 的设计意图，但它把"什么算不可核验"的判定权重全部压给了 R2D56-4 的形态白名单——而该白名单过宽（见 3.3）。

---

### 3.2 R2D56-3 边界 —— **结论：主用例通过，2 处残留（R3-2 / 归一化不对称）**

```console
[B1 **src/x.py**]     status=fresh      paths=['src/x.py']        invalid=[] unver=[]
[B2 src/**]           status=unverified paths=['src/**']          invalid=[] unver=['src/**']
[B3 **src/*.py**]     status=unverified paths=['**src/*.py**']    invalid=[] unver=['**src/*.py**']
[B4 a**b]             status=unverified paths=['a**b']            invalid=[] unver=['a**b']
[B5 ***src/x.py***]   status=unverified paths=['***src/x.py***']  invalid=[] unver=['***src/x.py***']
[B6 ** src/x.py **]   status=fresh      paths=['src/x.py']        invalid=[] unver=[]
[B7 src/x.py**]       status=unverified paths=['src/x.py**']      invalid=[] unver=['src/x.py**']
```

| 形态 | 契约期望 | 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| `**src/x.py**`（整体加粗真实路径） | `fresh` | `fresh`，path 归一为 `src/x.py` | ✅ 修复达成 |
| `src/**`（glob） | `unverified` | `unverified` | ✅ 未误伤 |
| `**src/*.py**`（加粗 + 内部 glob） | 语义未定义 | `unverified`，**path 保留 `**src/*.py**`** | ⚠️ 见下 |
| `a**b`（路径名含星号） | — | `unverified`，path=`a**b` | ⚠️ 真文件名不可锚定（Linux 可存在，现实概率≈0） |
| `***src/x.py***`（粗斜体） | — | `unverified`（仍是假红） | ⚠️ 残留 |
| `** src/x.py **`（内层空格） | `fresh` | `fresh` | ✅ |
| `src/x.py**`（单侧加粗） | — | `unverified` | ⚠️ 残留（与修复前同） |

**新引入的解析歧义（两点，均有实测）**：

1. **归一化不对称**：`**src/x.py**` → `src/x.py`，但 `**src/*.py**` → `**src/*.py**`（`**` 被当作 glob 字符留在 path 里）。这使**同一语义的两种写法在账本里是两个不同键**，进而产生假墓碑违规（见 R3-2 的 H1 实测）。
2. **加粗跨分隔符失效**：剥离发生在 `_ANCHOR_SPLIT` **之后**，所以 `**src/x.py, src/y.py**` 被切成 `**src/x.py` 与 `src/y.py**` 两个残片，双双落 glob：

```console
[g1] anchors='**src/x.py, src/y.py**'     status=unverified paths=['**src/x.py', 'src/y.py**'] unver=[同上] invalid=[]
[g2] anchors='**src/x.py**, **src/y.py**' status=fresh      paths=['src/x.py','src/y.py']
[g3] anchors='**src/x.py:1-3**'           status=fresh      paths=['src/x.py']
[g4] anchors='`**src/x.py**`'            status=fresh      paths=['src/x.py']
[g5] anchors='**src/x.py**、src/y.py'      status=fresh      paths=['src/x.py','src/y.py']
[g6] anchors='**src/**'                   status=fresh      paths=['src']      ← 加粗后成目录锚点（歧义）
[g7] anchors='**docs/**'                  status=fresh      paths=['docs']
```

**假墓碑违规实测（H1）**：以 `**src/x.py, src/y.py**` 写账本 → 账本记为 `["**src/x.py","src/y.py**"]`；作者把同一断言改成等价的 `src/x.py, src/y.py` 后 → `removed=1`、rc=1、status=fresh。**去加粗（纯排版动作）触发"删锚点洗绿"的硬红**，这是 R2D56-3 修复未覆盖的负向激励（会诱导作者去 `--write-baseline` 洗账本）。详见 R3-2。

---

### 3.3 R2D56-4 边界 —— **结论：过度矫正，产生静默绿灯（P1，见 R3-1）**

#### 3.3.1 合法路径形态白名单误伤（5/5 误伤）

```console
[C1 含空格 docs/my file.md]   status=unverified invalid=['docs/my file.md']   ← 文件真实存在
[C2 含中文 文档/说明.md]        status=unverified invalid=['文档/说明.md']        ← 文件真实存在
[C3 含 @ pkg@1.2/x.py]        status=unverified invalid=['pkg@1.2/x.py']       ← 文件真实存在
[C4 含 + a+b.py]              status=unverified invalid=['a+b.py']             ← 文件真实存在
[C5 反斜杠 src\x.py]          status=unverified invalid=['src\\x.py']          ← 目标 src/x.py 存在
[C6 行区间 src/x.py:1-3]      status=fresh      （对照：形态白名单放行）
[C7 普通路径 src/x.py]        status=fresh      （对照）
[C8 非 ASCII 拉丁 src/ü.py]    status=unverified invalid=['src/ü.py']
```

**误伤面**：`[A-Za-z0-9._/\-]` 之外的一切字符 ⇒ 空格、CJK、`@`、`+`、`~`、`%`、`#`、`&`、单引号、括号、`!`、非 ASCII 拉丁、以及**反斜杠**。仓库现状 `git ls-files` 无非 ASCII 路径、无含空格路径，故**当前零实例**；但契约 §4.1 只要求"路径按仓库根解析，禁止 `..` 越界"，从未限定 ASCII——CJK 路径对本仓库（中文文档体系）不是理论风险。

**反斜杠属确定性回归（死代码证据）**：`normalize_anchor:66` 仍保留 `re.match(r"^[A-Za-z]:[\\/]", text)` 的盘符守卫，`:92` 仍有 `body.replace("\\", "/")` 的归一化——即"相对反斜杠路径"原本被**显式设计为可用**，但新白名单在 `:81` 先行拦截，导致 `:92` 的反斜杠分支对相对路径**不可达**。这不是"没考虑到"，是"新判据把既有能力关掉了"。

#### 3.3.2 复合掩蔽：与 R2D56-1 的判定集剔除叠加 ⇒ 静默绿灯

```console
[C9  真实锚点 src/a.py + 含空格锚点 docs/my file.md，后者文件已被删除]
    status=fresh  invalid=['docs/my file.md']
    📊 声明 1/1 篇｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
    🎯 真值分: 15.0 / 15

[C10 对照：同场景，路径换成 docs/my_file.md（无空格）]
    status=missing_anchor

[C11 中文锚点 文档/说明.md 在复核后被修改]
    status=fresh   ← 漂移被掩蔽
```

**门禁面（D1/D2，含已提交账本，排除 rc=2 干扰）**：

```console
D1  baseline 已写并提交 → git rm "docs/my file.md" → 提交
    $ check-doc-drift.py --root docs --repo . --fail-on-drift
    📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
    🎯 真值分: 15.0 / 15
    rc= 0
    json summary: {'drifted':0,'missing_anchor':0,'unverified':0,'fresh':1,
                   'removed_from_baseline':0,'baseline_status':'ok','freshness_score':15.0}

D2  同场景，路径 docs/my_file.md（无空格）
    $ check-doc-drift.py --root docs --repo . --fail-on-drift
    📊 声明 1/1 篇｜fresh 0｜drifted 0｜missing 1｜stale 0｜unverified 0
    🎯 真值分: 0.0 / 15
    rc= 1
```

**因果链**：路径含空格 → `invalid=True` → `unverifiable=True` → `classify_doc` 的 `decidable` 把它剔除 → 只剩 `src/a.py`（fresh）→ 整篇 `fresh` → 真值分 15.0 → 默认门禁 rc=0。**墓碑不救**：锚点**声明**没变，`removed_from_baseline=0`。**文本输出不救**：`invalid_anchors` 只进 `--json` 的 docs 记录，人读输出里连一行提示都没有。

#### 3.3.3 契约层冲突（定性依据，不计入 skills 缺陷计数）

RFC-0005 V0.1.8 §4.2 新增行把「散文锚点（**含空格/中文**）」直接定义成不可核验：

> `| 不可核验锚点 | glob/占位符（* ? [] {} <>）与散文锚点（含空格/中文）只从判定集剔除……|`

这与同一份契约的 §4.1（"路径按仓库根解析，禁止 `..` 越界"）和术语表（"代码锚点 = 文档断言所依赖的仓库内路径"）冲突：**仓库内路径本来就可以含空格与中文**。实现忠实执行了这条错误规则，所以缺陷不能只归给实现——修复必须同时改契约行与实现判据（见 R3-1 建议）。

---

### 3.4 R2D56-2 —— **结论：部分达成（留痕可见，但不持久、不入机器可读面）**

```console
E1  --json --allow-unverified --fail-on-drift
    rc= 1
    stdout_is_json= True | keys: ['baseline_docs','baseline_status','coverage','declared','drifted',
                                  'enabled','fresh','freshness_score','max_age_days','missing_anchor',
                                  'removed_from_baseline','stale','total_docs','unverified']
    stderr= '⚠️  --allow-unverified 已生效：豁免 stale 0 + unverified 0（共 0 篇不阻断；drifted/missing/墓碑仍阻断）'
    JSON 内是否有豁免字段: 无

E2  文本模式（同一夹具）
    ⚠️  --allow-unverified 已生效：豁免 stale 0 + unverified 0（共 0 篇不阻断；…）   ← 追加在末尾，单行，可 grep
    stderr= ''

E3  waived=0（全部 fresh）仍打印"已生效"
    rc= 0
    ⚠️  --allow-unverified 已生效：豁免 stale 0 + unverified 0（共 0 篇不阻断；…）
```

| 验收点 | 期望 | 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| `--json` 时提示不污染 stdout | stdout 纯 JSON | `json.loads(stdout)` 成功；提示在 stderr | ✅ |
| 文本模式可解析 | 追加单行、不破坏既有行 | 汇总/真值分/明细行格式未变，提示为末行 | ✅ |
| 豁免是否"留痕" | 有可见痕迹 | stdout/stderr 有行 | ✅（人读面） |
| 机器可读面留痕 | — | JSON **无** `waived` / `allow_unverified` 字段；stderr 在 CI 中常被丢弃 | ⚠️ R3-5 |
| 措辞准确性 | 仅在真有豁免时报 | `waived=0` 仍报"已生效" | ⚠️ R3-5 |

**结论**：从"零痕迹"到"有痕迹"这一步是真做了，且 JSON 不污染这条硬要求达成；但"豁免"这一人因通道在**产物（JSON/审计报告）里仍不可追溯**，只活在当次终端输出里。属 P3 残留，不阻断。

---

### 3.5 回归面 —— **结论：全部通过（5/5）**

```console
$ python3 -m pytest skills/doc-governance/tests -q
203 passed in 21.75s

$ python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 3/46 篇（覆盖度 6.5%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc=0

$ python3 skills/doc-governance/scripts/check-doc-links.py
📊 审计汇总: 共扫描 95 个 Markdown 文件
✅ 未发现任何 404 断链或非法相对引用
rc=0

$ python3 skills/doc-governance/scripts/check-doc-control-sync.py
📊 扫描汇总: 共检查 47 个 Markdown 文件
✅ 所有文档控制头与修订历史版本 100% 保持一致
rc=0

$ python3 skills/doc-governance/scripts/audit-doc-health.py
🎯 [真值轴 · 代码锚点漂移]: 模式 warn｜3/46 篇 (6.5%)｜fresh 3｜真值分 15.0/15
🏁 诊断结论: PASS (健康度达标，准予交付) ✅
rc=0
```

**`--truth=require` 的 rc=1 不是本 diff 引入**（诚实标注）：

```console
$ audit-doc-health.py --truth=require
🚫 诊断结论: REJECTED（声明覆盖率 6.5% < 下限 50.0%（删锚点不能替代修复漂移）），请修复后重测
rc=1

$ git show 49c6d55:skills/doc-governance/scripts/check-doc-drift.py > /tmp/old_drift.py
$ python3 /tmp/old_drift.py --root docs --repo . --json | ...
{'declared': 3, 'total_docs': 46, 'coverage': 0.0652, 'fresh': 3, 'drifted': 0,
 'missing_anchor': 0, 'unverified': 0, 'freshness_score': 15.0}
```

两版覆盖度/真值分逐字段一致 ⇒ require 模式的 rc=1 是既存口径（`--min-coverage` 0.5 未达标），与本轮四项修复无关，不计缺陷。

**测试面**：`test_doc_drift.py` 共收集 42 条，其中 `TestFollowupP2P3` 只收集到 **4** 条——文件里却有 **8** 条（两个同名类），见 R3-4。

---

## 4. ③ 新缺陷

### R3-1 【P1 · 阻断】路径形态白名单过度矫正：合法锚点被静默剔除，锚点文件删除后仍判 fresh / 15.0 / rc=0

| 项 | 内容 |
| :--- | :--- |
| **位置** | `skills/doc-governance/scripts/check-doc-drift.py:41`（`_PATH_SHAPE`）、`:80-83`（invalid 分支）、与 `:160-170`（`decidable` 剔除）叠加 |
| **现象** | 锚点值只要含 `[A-Za-z0-9._/\-]` 之外字符（空格 / 中文 / `@` / `+` / 反斜杠 / 非 ASCII 拉丁…），即被归 `invalid` → `unverifiable` → 退出判定集。同文档其余锚点全 fresh 时，整篇判 `fresh`，真值分 15.0，默认门禁 rc=0 |
| **证据** | C1–C5 / C8（误伤）、C9（`fresh`，missing 0）、C11（漂移被掩蔽）、D1（rc=0 + 15.0）vs D2（rc=1 + missing 1） |
| **影响** | ① 真值轴对这类锚点**完全失效**：删除/移动/改动锚点文件均无信号，且给满分；② 墓碑不覆盖（声明未变，`removed_from_baseline=0`）；③ 人读输出零提示（`invalid_anchors` 只在 `--json`）；④ 与 RFC §4.1 的路径定义冲突，实现忠实于一条错误契约行；⑤ 相对反斜杠路径的原生支持被关掉（`:92` 归一化分支对相对路径不可达） |
| **触发条件** | 锚点路径含空格/CJK/`@`/`+`/反斜杠等 + 同文档存在至少一条可核验且 fresh 的锚点。**无需任何豁免参数**，默认门禁即静默 |
| **为何定 P1 而非 P2** | R2D56-1 原缺陷需 `--allow-unverified` 才完全静默（故当时判 P2）；R3-1 **在默认 `--fail-on-drift` 下就静默**，且直接命中 `change-impact-matrix.md:30` 的 DoD 场景（"被锚定路径改动/移动/删除"），并颁发满分——属"假声明颁发满分"，与 RFC §1「零声明不颁发满分」的诚实性主张同源反向 |
| **建议修复（最小面）** | ① 判据顺序反转：**先 stat**——路径（含空格/CJK）存在即按真实锚点判定；仅当不存在时才用形态启发式区分"散文"与"错路径"；② `invalid` 单独成态或至少计为**声明缺陷**（不得无条件从判定集剔除），并在文本输出与 `audit-doc-health.truth` 中透出；③ 反斜杠先归一化再判形态（恢复 `:92` 的可达性）；④ 契约行改为「无法 stat 且不像路径 ⇒ invalid」，删掉"含空格/中文"的绝对化措辞 |
| **回归测试建议** | ① 含空格真实路径 + 漂移 ⇒ drifted；② 含空格真实路径被删 ⇒ missing_anchor；③ 含中文路径 fresh；④ 反斜杠路径 fresh；⑤ 纯散文（`见附录 A`）仍 invalid 且不硬红（保住 R2D56-4 的原目标） |

### R3-2 【P2】整体加粗跨锚点分隔符失效 + 归一化不对称 ⇒ 假 unverified 与假墓碑违规

| 项 | 内容 |
| :--- | :--- |
| **位置** | `check-doc-drift.py:68-73`（剥离在 `_ANCHOR_SPLIT` 之后执行，见 `:128-131` 的切分顺序）、`:77-79`（glob 分支保留 `**` 于 path） |
| **现象** | `**src/x.py, src/y.py**`（整体加粗一个锚点列表）→ 切成 `**src/x.py` + `src/y.py**` → 两条都判 glob → `unverified`（默认 rc=1 假红）；且账本记为 `["**src/x.py","src/y.py**"]`，作者去加粗后触发**假墓碑违规** rc=1 |
| **证据** | g1（`status=unverified`，paths 含 `**`）、H1（`removed=1`、rc=1、status=fresh） |
| **影响** | R2D56-3 要消灭的假红换个位置复发；更糟的是"去加粗"这一纯排版动作会让门禁变红，诱导 `--write-baseline` 洗账本（与 R2D56-2 的负向激励同型） |
| **定级理由** | 与 R2D56-3 同因同型（假红 + 可豁免），沿用其 P2 定级；当前仓库零实例（7 条锚点全为 ASCII 无空格路径，且加粗只出现在字段名上） |
| **建议修复** | 先对**整个字段值**做一次"整体加粗"剥离（`^\*\*(.+)\*\*$` 且内部无 `*`），再按分隔符切分；或对每个 chunk 做成对残片配对（`**a` + `b**` ⇒ 合并后剥离）。同时保证 path 归一化对称（glob 分支也剥掉成对 `**`） |

### R3-3 【P3】`invalid` 锚点无人类可读提示，且不进 `audit-doc-health` 的 truth 块

| 项 | 内容 |
| :--- | :--- |
| **位置** | `check-doc-drift.py:80`（注释宣称"给修复提示"）、`:426-427`（只进 JSON）、`audit-doc-health.py:677-699`（truth_block 未透出） |
| **现象** | 代码注释与计划 §9 均称"归 invalid 并给修复提示"，但文本输出对 invalid 一字不提（D1 输出只有 `fresh 1`），`audit-doc-health` 的 truth 块也无该字段；用户唯一能看到的地方是 `check-doc-drift --json` 的 docs 明细 |
| **影响** | 宣称与取证不同宽（"给修复提示"未落地）；invalid 成为无信号的静默分类，正是 R3-1 得以长期不被发现的观测面缺陷 |
| **建议修复** | 文本模式对 `invalid_anchors` 逐条打印（如 `- [invalid] a.md: "docs/my file.md"（非路径形态，请改为仓库相对路径或删除该锚点）`），并同步进 `audit-doc-health.truth` 的 `invalid_anchors` 字段 |

### R3-4 【P3】新增测试类被同名定义覆盖：93 行死代码，4 条"作者自认为在跑"的用例从未被收集

| 项 | 内容 |
| :--- | :--- |
| **位置** | `test_doc_drift.py:798-890`（第一份）与 `:891-985`（第二份），同名 `TestFollowupP2P3` |
| **证据** | `pytest --collect-only` → `TestFollowupP2P3` 仅 4 条；`grep -n 'class Test'` → 两处同名；第一份用中文字面量断言（"正文"、"环境无 git"），第二份用 Unicode 转义并多 `time.sleep(1)` ⇒ 第一份是残留副本 |
| **影响** | ① 93 行死代码（违反"精准修改/清理自身死代码"）；② 若日后有人删除第二份，第一份的 `test_r2d56_1` 无 `sleep`、依赖同秒提交顺序，将变成 flaky；③ 报告与计划里"4 条回归测试"的计数掩盖了"文件里有 8 条"的事实 |
| **建议修复** | 删除第一份（`:798-890`），保留带 `time.sleep(1)` 的第二份 |

### R3-5 【P3】豁免留痕不入机器可读产物；`waived=0` 仍报"已生效"

| 项 | 内容 |
| :--- | :--- |
| **位置** | `check-doc-drift.py:555-563` |
| **证据** | E1（JSON 无 `waived` / `allow_unverified` 字段，提示仅 stderr）、E3（`waived=0` 仍打印"已生效…共 0 篇不阻断"） |
| **影响** | CI 采集 JSON 作为审计凭据时，豁免仍不可追溯（"零痕迹"只从终端消失，未从产物消失）；措辞在无豁免时失真，长期会钝化读者对告警的敏感度 |
| **建议修复** | ① `summary` 增加 `"allow_unverified": bool` 与 `"waived": {"stale": n, "unverified": n}`；② `waived > 0` 才打印，或改为"已启用（本次豁免 0 篇）"的中性措辞 |

---

## 5. ④ 裁决

### 5.1 计数

| 定级 | 计数 | 编号 |
| :--- | :--- | :--- |
| P0 | 0 | — |
| **P1（Blocker）** | **1** | **R3-1** |
| P2 | 1 | R3-2 |
| P3 | 3 | R3-3 / R3-4 / R3-5 |

**Blockers = 1。**

### 5.2 裁决：🔴 **阻断（不准予交付）**

**裁决理由**：

1. 四项修复的**声明验收点**全部达成，回归面 5/5 通过，Blockers 不是"修复没做"，而是"修复引入的新判据把真值轴的判定面挖了一个默认门禁下不可见的洞"。
2. R3-1 的失效形态是**静默绿灯 + 满分**：锚点文件被删除，文档判 `fresh`、真值分 15.0/15、`--fail-on-drift` rc=0，墓碑与文本输出均无信号。这与真值轴的立项理由（"测得到写得规不规范，测不到还对不对"）正面冲突。
3. 该缺陷**不需要任何豁免参数**即可触发（对比 R2D56-1 需 `--allow-unverified`），且直接命中 `change-impact-matrix.md:30` 的 DoD 场景，属"契约承诺 vs 实测行为"的硬背离，不是风格问题。
4. 修复面小且局部（判据顺序：先 stat 再形态；invalid 不得无条件退出判定集；反斜杠先归一化），不涉及架构返工，具备同轮收口条件。

### 5.3 放行条件（最小集）

1. **R3-1**：合法路径（空格 / CJK / `@` / `+` / 反斜杠）恢复为真实锚点；`invalid` 不再无条件退出判定集（或单独成阻断态）；补 5 条回归测试（见 R3-1 建议）；同步修订 RFC-0005 §4.2 的"含空格/中文"措辞。
2. **R3-4**：删除 `:798-890` 的重复测试类。
3. **R3-2 / R3-3 / R3-5**：可延后到下一轮，但需在计划 §9 显式登记（不得静默）。

> R3-2 若与 R3-1 同轮修复更优：两者都在 `normalize_anchor` 的同一段判据里，一次改完可避免二次触碰同一热点。

---

## 6. 残留风险（Top 3）

1. **`invalid` 的语义天花板**：即便按建议改成"先 stat 再形态"，`invalid` 仍是"启发式"，仍存在"像路径但不存在"的灰区（如 `src/a,b.py` 被逗号切碎后两片都不存在）。该灰区目前落 `missing_anchor`（硬红），是**有意保留的假红**；若日后为降噪把它也归 invalid，将立刻重演 R3-1 的静默化。需在契约里写死"灰区必须硬红"。
2. **墓碑只保护"声明不减少"，不保护"声明不降级"**：把 `src/x.py` 改成 `src/**` 或 `src/x.py `（加空格）在多锚点文档里不触发墓碑（计数未减），却把该锚点移出判定集。本轮 R3-1 就是这条通道的一次实例化；后续任何"不可核验"分类扩容都会复用这条通道。
3. **`--allow-unverified` 的人因通道仍无产物级凭据**（R3-5）：审计只留终端 stderr 时，事后复盘无法区分"当时真的没有 unverified"与"当时用了豁免"。一旦进入常规 CI，豁免会变成不可审计的免检开关。

---

## 7. 附录：夹具与复现

| 脚本 | 覆盖 | 夹具数 |
| :--- | :--- | :--- |
| `/tmp/r3fu_harness.py` | F1–F4：R2D56-1 判定集 + 墓碑 | 4 |
| `/tmp/r3fu_harness2.py` | B1–B7（R2D56-3 边界）、C1–C11（R2D56-4 边界 + 复合掩蔽） | 18 |
| `/tmp/r3fu_harness3.py` | D1/D2（门禁面）、E1–E3（R2D56-2 留痕） | 3 |
| `/tmp/r3fu_harness4.py` | g1–g7（加粗跨分隔符 / 目录歧义） | 7 |
| `/tmp/r3fu_harness5.py` | H1（加粗写法 ↔ 账本键不一致 ⇒ 假墓碑违规） | 1 |

夹具统一约定：`git init` → 以 `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` 钉死 `2026-11-01 / 11-02 / 11-03 / 11-05 / 11-10 / 11-20` → `复核于` 用日期型（`_verified_ts` 按当日末刻起算）→ 断言取 `--json` 的 `docs[0].status` 与 `summary` 字段，不解析 emoji 文本。

**关键命令（可逐条复跑）**：

```bash
# 边界
git diff --stat 49c6d55..HEAD -- skills/
# 回归面
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
python3 skills/doc-governance/scripts/check-doc-links.py
python3 skills/doc-governance/scripts/check-doc-control-sync.py
python3 skills/doc-governance/scripts/audit-doc-health.py
# R3-1 复现（D1/D2）
python3 /tmp/r3fu_harness3.py
# R3-2 / R3-4 复现
python3 /tmp/r3fu_harness4.py && python3 /tmp/r3fu_harness5.py
python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q --collect-only | grep P2P3
```

---

**审查者签名**：定向单轮红队审查者（独立上下文，Reviewer ≠ Author）
**裁决**：🔴 阻断 —— **Blockers = 1（R3-1，P1）**；四项修复本身达标，但 R2D56-4 的判据需按 §5.3 收口后方可放行。
