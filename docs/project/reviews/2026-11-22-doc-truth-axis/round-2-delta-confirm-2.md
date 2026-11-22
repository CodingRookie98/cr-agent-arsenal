# 收口确认审查报告 2（Round 2 Delta · Confirm 2：R2D-5 / R2D-6 / 墓碑归属 / --repo 基准）

> **文档控制信息**
> - **文档标识**: REVIEW-R2D-CONFIRM2-doc-truth-axis-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: 收口确认审查者 2（独立上下文，Reviewer ≠ Author）
> - **生效日期**: 2026-11-22
> - **审查对象基线**: `3120d5a`（R2D-5/R2D-6 修复）+ `405d93b`（复核点重钉，仅文档）+ `d388c22`（仅文档：登记人类裁决 B 与轮次台账）；实测 HEAD = `d388c22206883145b9c1f44bb3d3077a2a47b2f7`
> - **脚本等价性**: `git diff --stat 3120d5a..HEAD -- skills/` 输出为空 ⇒ 本轮实测脚本与 `3120d5a` 逐字节一致；`405d93b` / `d388c22` 只改文档，不改变任何判定
> - **前序裁决**: `round-2-delta-confirm.md`（24,971 B / sha256 `d416cc2bfcf0554ad5577b9bef962b32cab5f17bdb65ab4f0d827f995dd89d3c`——本轮开工复算一致）
> - **审查模式**: 收口确认（只做五件事：R2D-5 / R2D-6 / R2D2-2 / R2D-4 残留 / 回归面）
> - **取证方式**: 全部结论为本机实跑；夹具建于 `/tmp/r2d56`（18 个夹具仓库），提交时间用 `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE` 钉死；仓库工作区零写入（开工与收工 `git status --porcelain` 均为空），git 调用只有 `init/add/commit/log/rev-parse/ls-files/diff/show`，`cwd` 全在 `/tmp/r2d56/*`
> - **唯一写入面**: 本报告文件（未提交）
> - **环境**: Linux / Python 3.12.3 / git 2.56.1
> - **未验证项**: macOS 与 Windows 的大小写不敏感文件系统、Windows 路径分隔符、真实 CI 流水线（仓库无 `.github`，门禁全为人工触发）、千篇级文档规模下逐锚点 `git log` 的性能

---

## 0. 一句话结论

五项主验收条款**实测全部通过**（逐条有原始输出）：

1. **R2D-5**：「声明锚点但无复核于」默认 `rc=1`、加 `--allow-unverified` 后 `rc=0`；且 drifted / missing_anchor / 墓碑违规在豁免下**仍 `rc=1`**；账本缺席/损坏在豁免下**仍 `rc=2`**（豁免没有打穿 fail-closed）。
2. **R2D-6**：`src/**`、`<path>/x.py` 落 `unverified`（`missing_anchor=0`）；目录锚点 `src` 在与提交对齐时判 `fresh`。
3. **R2D2-2**：共享锚点的两篇文档只删一侧声明，墓碑只列该文档、路径每文档只计一次、未改动文档不连坐；整篇删除同样只归因被删文档。
4. **R2D-4 残留**：`--root docs/sub --repo .` 下 audit 与 drift 结论同向（drifted 1 / fresh 1）；不带 `--repo` 时两脚本也同向（missing 2 / missing 2）。
5. **回归面**：`pytest skills/doc-governance/tests -q` → 199 passed；真仓库 drift `--fail-on-drift` rc=0（3/46 篇、15.0/15）；check-doc-links rc=0；check-doc-control-sync rc=0；audit-doc-health PASS rc=0。

**未发现 P0/P1：Blockers = 0，准予交付。** 本轮另检出 3 条 P2 + 1 条 P3（R2D56-1…4）。其中 **R2D56-1 建议优先回填**：一篇文档只要混入**一个** glob/占位符锚点，其真实 `drifted` / `missing_anchor` 会被 `classify_doc` 的短路优先序降级成 `unverified`，继而被 `--allow-unverified` 一并豁免——这既是第一项「豁免不误伤」的破口，也正是第五项「`--allow-unverified` 会不会变成永久免检」的那个洞。默认门禁仍 rc=1，故未构成静默绿灯，定级 P2。

---

## 1. 基线与会话事实

| 项 | 值 |
| :--- | :--- |
| 分支 | `feat/doc-truth-axis` |
| 开工 HEAD | `405d93b` |
| 收工 HEAD | `d388c22`（会话期间由主智能体新增的**纯文档**提交：计划书 2 行、审查台账 7+/2-） |
| 审定增量 | `3120d5a`（脚本 + 文档 + 测试，160+/28-）、`405d93b`、`d388c22` |
| 脚本等价性核验 | `git diff --stat 3120d5a..HEAD -- skills/` → 空（无输出） |
| 工作区 | 开工 / 收工 `git status --porcelain` 均为 0 行（本报告落盘前）；`pytest` 未污染工作区 |
| git 写操作 | 无（仓库内零写；夹具仓库 `init/add/commit` 全部发生在 `/tmp/r2d56/*`） |
| 受控文件改动 | 无（本报告为唯一写入，且不提交） |

> **基线漂移声明（诚实标注）**：本轮开工 HEAD 为 `405d93b`，落盘时已推进到 `d388c22`。该提交经 `git show --stat` 核实**只改文档**（计划书 2 行 + 审查台账 7 行），且 `skills/` 自 `3120d5a` 起零改动，故不影响本轮任何判定。

---

## 2. 复验环境与夹具

- 脚本（绝对路径调用）：`skills/doc-governance/scripts/{check-doc-drift,audit-doc-health,check-doc-links,check-doc-control-sync}.py`
- 夹具根：`/tmp/r2d56/`，共 18 个夹具仓库；全部提交用 `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` 钉死时间。首版夹具曾因 `ENV=... git add -A && git commit` 只把环境变量作用于 `git add` 而使全部提交落到当前时间，已用 `ci()` 包装函数重建，并逐条复核 `git log --format='%h %ci %s'` 日期后重跑全部结论（本文所有数据均来自重建后的夹具）。
- 输出留档：`/tmp/r2d56/out*`（下文「关键输出」为逐字摘录，仅删空行）。

| 夹具 | 构造要点 | 验证目标 |
| :--- | :--- | :--- |
| `f5a` | `src/a.py` + 文档仅声明锚点、**无复核于** | R2D-5 默认阻断 / 豁免放行 |
| `f5b` | 锚点在 `2026-11-20` 又改，文档 `复核于: 2026-01-01` | drifted 在豁免下仍阻断 |
| `f5c` | 锚点指向不存在的 `src/nope.py` | missing_anchor 在豁免下仍阻断 |
| `f5d` | 账本记 2 锚点，文档删掉其中 1 个 | 墓碑违规在豁免下仍阻断 |
| `f5e` | 锚点 `2026-01-01`、`复核于: 2026-01-02`（超 180 天） | stale 的阻断 / 豁免口径 |
| `f5f` | 有声明、**账本缺席** | fail-closed 是否被豁免打穿 |
| `f5f2` | 有声明、**账本坏 JSON** | 同上（corrupt 分支） |
| `f6` | 4 篇：`src/**`、`src`（目录）、`<path>/x.py`、`**src/pkg/x.py**`（加粗） | R2D-6 三类锚点 + 加粗副作用 |
| `f6b` | `代码锚点: src/x.py, src/**`，`复核于: 2026-01-01` | 混合锚点是否掩蔽真实漂移 |
| `f6b-solo` | 同上但**去掉 glob** | 对照组（应为 drifted） |
| `f6c` | `代码锚点: src/gone.py, <path>/x.py` | 混合锚点是否掩蔽硬断裂 |
| `f6c-solo` | 同上但**去掉占位符** | 对照组（应为 missing_anchor） |
| `f6d` | `代码锚点: 见附录 A`（散文）+ `src`（目录） | 散文锚点语义 |
| `f6g` | `代码锚点: src/pkg/x.py`（**未加粗**，与 `f6/bold.md` 同路径） | R2D56-3 的对照组（应为 fresh） |
| `f4` | `--root docs/sub`；`x.md` drifted、`y.md` fresh，锚点写仓库相对路径 `src/lib.py` | R2D-4 残留：两脚本基准是否同向 |
| `f22` | `a.md`:[shared, other]、`b.md`:[shared]；只删 `a.md` 对 shared 的声明 | R2D2-2 归属与连坐 |
| `f22b` | 同上，但**整篇删掉 `a.md`** | 归属在「文档消失」时的表现 |
| `f22c` | 两篇**各自**删掉同一锚点 | 逐文档归属是否被错误合并 |

---

## 3. ① 命令与关键输出

### 3.1 第一项 · R2D-5 门禁口径（声明锚点但无复核于 / 豁免边界）

```bash
S=/home/hui/workspace/projects/cr-agent-arsenal/skills/doc-governance/scripts/check-doc-drift.py
for f in f5a f5b f5c f5d; do
  cd /tmp/r2d56/$f
  python3 $S --root docs --repo . --fail-on-drift;                    echo "rc=$?"
  python3 $S --root docs --repo . --fail-on-drift --allow-unverified; echo "rc=$?"
done
```

关键输出（`f5a`：仅「声明锚点、无复核于」，其余桶全 0）：

```
🔍 文档代码锚点漂移检测: root=/tmp/r2d56/f5a/docs repo=/tmp/r2d56/f5a
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 0｜drifted 0｜missing 0｜stale 0｜unverified 1
🎯 真值分: 0.0 / 15
   - [unverified] a.md
rc=1
---- 加 --allow-unverified ----
（输出逐字节相同，仅退出码不同）
rc=0
```

关键输出（`f5d`：墓碑违规在豁免下仍阻断）：

```
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
   ⛔ 基线墓碑违规（声明被删除/缩减）:
      - d.md 缺失: src/d2.py
rc=1        ← 默认
rc=1        ← 加 --allow-unverified 仍 1
```

退出码矩阵（本轮实跑，全部 `--root docs --repo .`，账本均存在且结构合法）：

| 夹具 | 场景 | 默认 `--fail-on-drift` | 加 `--allow-unverified` | 期望 | 判定 |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `f5a` | 仅 unverified（声明锚点、无复核于） | **1** | **0** | 1 / 0 | ✅ |
| `f5b` | 仅 drifted（复核后锚点又改） | 1 | **1** | 1 / 1 | ✅ |
| `f5c` | 仅 missing_anchor | 1 | **1** | 1 / 1 | ✅ |
| `f5d` | 仅墓碑违规（删锚点） | 1 | **1** | 1 / 1 | ✅ |
| `f5e` | 仅 stale（超 180 天） | 1 | **0** | 1 / 0（`--help` 与 SKILL 明示豁免 stale） | ✅ |
| `f5f` | 账本**缺席** + unverified | **2** | **2** | 2 / 2（fail-closed 不可被豁免绕过） | ✅ |
| `f5f2` | 账本**损坏** + unverified | **2** | **2** | 2 / 2 | ✅ |

fail-closed 原文（`f5f` / `f5f2` 两分支一致，加不加豁免都一样）：

```
❌ 错误: 锚点基线不可用（missing）：/tmp/r2d56/f5f/docs/.doc-truth-baseline.json。墓碑判据无法成立，按 fail-closed 处理；首次启用请先运行 --write-baseline 并提交该账本。
❌ 错误: 锚点基线不可用（corrupt）：/tmp/r2d56/f5f2/docs/.doc-truth-baseline.json。墓碑判据无法成立，按 fail-closed 处理；...
```

**本项结论：通过。** R2D-5 三条要求（默认阻断 / 显式豁免 / 豁免不误伤 drifted·missing·墓碑）全部成立；额外确认豁免**没有**打穿 R2D-1 的 fail-closed（账本不可用仍 rc=2）。

> 附带发现（非本项要求）：`f5d` 同时打印「真值分 15.0 / 15」与「⛔ 墓碑违规 → rc=1」。真值分只度量「已声明文档的新鲜度」，墓碑是另一条轴，二者并存不算矛盾，但读数时需知悉分数不等于门禁。

### 3.2 第二项 · R2D-6 锚点语义（glob / 目录 / 占位符）

```bash
cd /tmp/r2d56/f6
python3 $S --root docs --repo . --json --fail-on-drift --allow-unverified
python3 $S --root docs --repo . --fail-on-drift;                     echo "rc=$?"
python3 $S --root docs --repo . --fail-on-drift --allow-unverified;  echo "rc=$?"
```

关键输出（逐文档状态，`--json` 摘要 + 归一化后的锚点值）：

```
summary: {"declared": 4, "fresh": 1, "drifted": 0, "missing_anchor": 0, "stale": 0,
          "unverified": 3, "freshness_score": 3.8, "removed_from_baseline": 0,
          "baseline_docs": 4, "baseline_status": "ok"}
  bold.md -> unverified | anchors: ["**src/pkg/x.py**"] | unverifiable: [true]
  dir.md  -> fresh      | anchors: ["src"]             | unverifiable: [false]
  glob.md -> unverified | anchors: ["src/**"]          | unverifiable: [true]
  ph.md   -> unverified | anchors: ["<path>/x.py"]     | unverifiable: [true]
default gate rc=1        ← 3 篇 unverified 阻断（R2D-5 口径）
allow rc=0               ← 显式豁免后放行
```

补充：账本由 `--write-baseline` 自写（不是手工构造），因此 `removed_from_baseline=0` 可信；`src` 为真实目录锚点且其最后一次提交（`2026-11-01`）早于 `复核于: 2026-11-22`，判 `fresh` 正确。

**本项结论：通过（三类锚点全部符合预期，`missing_anchor` 归零）。** 但同批夹具暴露了三处语义副作用：混合锚点短路（R2D56-1）、加粗锚点降级（R2D56-3）、散文锚点仍硬红（R2D56-4），见 §5。

### 3.3 第三项 · R2D2-2 墓碑归属（共享锚点、只删一侧声明）

夹具 `/tmp/r2d56/f22`：`a.md` 声明 `src/shared.py, src/other.py`，`b.md` 声明 `src/shared.py`；账本由 `--write-baseline` 生成（两篇各 1–2 条），随后**只把 `a.md` 对 `shared` 的声明删掉**。

```bash
cd /tmp/r2d56/f22
python3 $S --root docs --repo . --fail-on-drift; echo "rc=$?"
# 明细（直接调用 analyze，避开 CLI 只打印计数）
python3 - <<'PY'
import importlib.util, json, pathlib
spec = importlib.util.spec_from_file_location("cdd", "/home/hui/workspace/projects/cr-agent-arsenal/skills/doc-governance/scripts/check-doc-drift.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
res = m.analyze(pathlib.Path("docs"), repo=pathlib.Path("."), baseline_path=pathlib.Path("docs/.doc-truth-baseline.json"))
print("docs:", [(d["doc"], d["status"], [a["path"] for a in d["anchors"]]) for d in res["docs"]])
print("removed_from_baseline:", json.dumps(res["removed_from_baseline"], ensure_ascii=False))
PY
```

关键输出：

```
🔍 文档代码锚点漂移检测: root=/tmp/r2d56/f22/docs repo=/tmp/r2d56/f22
📊 声明 2/2 篇（覆盖度 100.0%）｜fresh 2｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
   ⛔ 基线墓碑违规（声明被删除/缩减）:
      - a.md 缺失: src/shared.py
rc=1
--- analyze 明细 ---
docs: [('a.md', 'fresh', ['src/other.py']), ('b.md', 'fresh', ['src/shared.py'])]
removed_from_baseline: [{"doc": "a.md", "missing": ["src/shared.py"], "declared_now": ["src/other.py"]}]
```

逐条核对：

| 断言 | 实测 | 判定 |
| :--- | :--- | :---: |
| 墓碑只列「自身声明数下降」的文档 | 只有 `a.md`，`b.md` 未出现在违规清单 | ✅ |
| 路径只计一次 | `missing: ["src/shared.py"]`（单元素），CLI 只打印一行 | ✅ |
| 未改动文档不连坐 | `b.md` 保持 `fresh`、仍计 1 条 `shared`（全局多重集 `shared: 2 → 1` 的亏空被精确归因到 `a.md`） | ✅ |

补充探针（`f22b`：整篇删除）：删除 `a.md` 整篇文件后，违规清单仍只列 `a.md`，`b.md` 不连坐：

```
📊 声明 1/1 篇（覆盖度 100.0%）｜fresh 1｜drifted 0｜missing 0｜stale 0｜unverified 0
   ⛔ 基线墓碑违规（声明被删除/缩减）:
      - a.md 缺失: src/shared.py
rc=1
```

补充探针（`f22c`：两篇**各自**删掉同一路径）：逐文档各记一次（不合并成「某篇缺失 2 条」、也不虚增）：

```
⚠️  未启用：没有任何文档声明「代码锚点」，真值分不颁发（0.0/15）
📊 声明 0/2 篇（覆盖度 0.0%）｜fresh 0｜drifted 0｜missing 0｜stale 0｜unverified 0
   ⛔ 基线墓碑违规（声明被删除/缩减）:
      - a.md 缺失: src/shared.py
      - b.md 缺失: src/shared.py
rc=1
```

**本项结论：通过。** 归属精确到自身缩减的文档、路径每文档只计一次、未改动文档零连坐；整篇删除与「双篇各自缩减」两个边界同样正确（后者按文档各记一次，属逐文档归属而非重复计数）。

### 3.4 第四项 · R2D-4 残留（`--root <非 docs 子目录>` + `--repo .` 基准是否同向）

夹具 `/tmp/r2d56/f4`：仓库根有 `src/lib.py`（`2026-11-20` 改动），`docs/sub/x.md` 复核于 `2026-01-01`（应 drifted）、`docs/sub/y.md` 复核于 `2026-11-21`（应 fresh）、`docs/other/z.md` 同类；锚点写**仓库相对路径** `src/lib.py`；`--root docs/sub`，账本写在 `docs/sub/`。

```bash
cd /tmp/r2d56/f4
python3 $S --root docs/sub --repo . --fail-on-drift          # drift 带 --repo
python3 $S --root docs/sub --fail-on-drift                   # drift 默认 repo=root.parent
python3 $A --root docs/sub --repo . --truth warn             # audit 带 --repo
python3 $A --root docs/sub --truth warn                      # audit 默认
```

关键输出（两脚本 × 两种基准）：

| 调用 | fresh | drifted | missing_anchor | unverified |
| :--- | :---: | :---: | :---: | :---: |
| `check-doc-drift --root docs/sub --repo .` | 1 | **1** | 0 | 0 |
| `audit-doc-health --root docs/sub --repo .` | 1 | **1** | 0 | 0 |
| `check-doc-drift --root docs/sub`（默认） | 0 | 0 | **2** | 0 |
| `audit-doc-health --root docs/sub`（默认） | 0 | 0 | **2** | 0 |

原文（audit 一侧）：

```
   * 声明覆盖: 2/2 篇 (100.0%)｜fresh 1｜drifted 1｜missing 0｜stale 0｜unverified 0
   * 声明覆盖: 2/2 篇 (100.0%)｜fresh 0｜drifted 0｜missing 2｜stale 0｜unverified 0
```

结论：**两脚本在「带 `--repo .`」与「不带 `--repo`」两种情况下都同向**——带 `--repo` 时基准是仓库根（锚点解析正确、drifted 1 / fresh 1），不带时双双退回 `--root` 的父目录（`docs`，锚点被解析成 `docs/src/lib.py` ⇒ missing 2）。R2D-4 残留（audit 缺 `--repo` 导致基准错位）**已闭合**；`audit-doc-health.py:741-742` 新增的 `--repo` 与 `check-doc-drift.py:438` 的语义一致（默认取 `--root` 父目录）。

> 说明：该夹具 audit 的结构分 75.0 < 80 被 REJECT，与真值轴无关（夹具只放了 3 篇文档、无控制头）；本项只比对真值块计数。

### 3.5 第五项 · 回归面 + `--allow-unverified` 误用抽查

```bash
cd /home/hui/workspace/projects/cr-agent-arsenal
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
```

关键输出：

```
........................................................................ [ 36%]
........................................................................ [ 72%]
.......................................................                  [100%]
199 passed in 17.58s

🔍 文档代码锚点漂移检测: root=.../docs repo=.../cr-agent-arsenal
📊 声明 3/46 篇（覆盖度 6.5%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
🎯 真值分: 15.0 / 15
rc=0

📊 审计汇总: 共扫描 95 个 Markdown 文件
✅ 恭喜！未发现任何 404 断链或非法相对引用，所有链接 100% 物理有效！
rc=0

📊 扫描汇总: 共检查 47 个 Markdown 文件
✅ 恭喜！所有文档控制头与修订历史版本 100% 保持一致，无版本漂移！
rc=0

🌟 完美！未检测到任何健康缺陷，知识库处于极佳健康状态！
🏁 诊断结论: PASS (健康度达标，准予交付) ✅
rc=0

🎯 [真值轴 · 代码锚点漂移]:
   * 模式: warn（结构分 100.0 分不含真值分）
   * 声明覆盖: 3/46 篇 (6.5%)｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0
   * 真值分: 15.0 / 15
🏁 诊断结论: PASS (健康度达标，准予交付) ✅
rc=0
```

回归面五项**全绿**。

**`--allow-unverified` 误用抽查（本项的可疑面）**：

| 检查点 | 实测 | 判定 |
| :--- | :--- | :--- |
| 是否有文档说明 | 有：`skills/doc-governance/SKILL.md:140`、`docs/proposals/RFC-0005-doc-truth-axis.md:95`、`docs/GOVERNANCE.md:17`，`--help` 亦写明「豁免 unverified / stale 的阻断」 | 有说明 |
| 是否有使用边界（时效/比例/仅限迁移窗口） | **无**：三处文档只描述「可显式豁免」，未限定时长、未约定仅限迁移窗口、未要求登记原因 | ⚠️ |
| 是否有自动化调用（可能常开） | 无：仓库**不存在** `.github/`；`*.yml/*.yaml/Makefile/*.sh` 中 `allow-unverified` 零命中；SKILL 模式 2 的标准调用不带该参数 | ✅ |
| 豁免生效时输出是否留痕 | **无**：同一夹具加/不加该参数，stdout+stderr **逐字节相同**（`diff` 无输出），只有退出码 0/1 之差；无「已豁免 N 篇」提示 | ⚠️ |
| 报告面是否同口径 | audit-doc-health **没有**对应开关，`--truth=warn` 仍打印「真值轴未清零 … unverified n」（`audit-doc-health.py:912-923`）——门禁 rc=0 与报告「未清零」并存 | ⚠️（口径差） |

**本项结论：回归面全绿；`--allow-unverified` 的误用风险不来自「无文档」，而来自「无使用边界 + 无痕迹 + 与 R2D56-1 叠加」**，记 R2D56-2（P3），详见 §5。

---

## 4. ② 五项逐条结论

| 项 | 验收条款 | 关键证据（§3 对应小节） | 结论 |
| :--- | :--- | :--- | :---: |
| 1 | 声明锚点但无「复核于」⇒ `--fail-on-drift` rc=1；加 `--allow-unverified` rc=0；drifted / missing_anchor / 墓碑**仍 rc=1** | §3.1 退出码矩阵 7 行（含 stale 与 fail-closed） | ✅ 通过 |
| 2 | glob（`src/**`）落 `unverified` 而非 `missing_anchor`；目录（`src`）与提交对齐时 `fresh`；占位符（`<path>`）不硬红 | §3.2：`missing_anchor=0`、glob/ph 两篇 unverified、dir 篇 fresh | ✅ 通过 |
| 3 | 共享锚点只删一侧：墓碑只列该文档、路径只计一次、未改动文档不连坐 | §3.3：`removed_from_baseline` 仅 a.md、单元素 missing、b.md 保持 fresh；另测整篇删除与双篇各自缩减 | ✅ 通过 |
| 4 | `--root <非 docs 子目录>` + `--repo .`：audit 与 drift 基准/结论同向 | §3.4：带 `--repo` 双双 drifted 1 / fresh 1；不带双双 missing 2 | ✅ 通过（残留闭合） |
| 5 | pytest 全绿；真仓库 drift / link / control-sync rc=0；audit PASS；抽查 `--allow-unverified` 误用 | §3.5：199 passed、rc=0×4、PASS；误用面见 R2D56-2 | ✅ 通过（回归面）/ ⚠️ 见 R2D56-2 |

---

## 5. ③ 新缺陷（R2D56-n）

### R2D56-1（P2）混合锚点短路：一个 glob/占位符锚点即可把真实 drifted / missing_anchor 降级为 unverified，并被 `--allow-unverified` 豁免

**现象**：`classify_doc` 的**第一判定**是「任一锚点不可核验 ⇒ 直接返回 unverified」，早于「锚点不存在 ⇒ missing_anchor」与「锚点提交时间晚于复核点 ⇒ drifted」。因此同一文档里只要混入**一个** glob 或占位符锚点，其余**可核验**锚点的真实断裂/漂移永不进入判定；`--allow-unverified` 随后按 unverified 把它们一并豁免。

**反证据（文件:行）**：

- `skills/doc-governance/scripts/check-doc-drift.py:146-149`——`if anchor_unverifiable is not None and any(anchor_unverifiable): return "unverified"` 位于 missing_anchor 判定（同函数 :148-149）与 drifted 判定（:157-158）**之前**；
- `skills/doc-governance/scripts/check-doc-drift.py:66-70`——`*?[]{}<>` 任一字符即标记整条锚点 `unverifiable`；调用方再补 `exists=True / tracked=False`（:373-378），使「可核验性」被整体短路。

**复现命令与输出**：

```bash
S=/home/hui/workspace/projects/cr-agent-arsenal/skills/doc-governance/scripts/check-doc-drift.py
for f in f6b f6b-solo f6c f6c-solo; do
  cd /tmp/r2d56/$f
  python3 $S --root docs --repo . --json | python3 -c 'import json,sys; p=json.load(sys.stdin); s=p["summary"]; print(s["drifted"], s["missing_anchor"], s["unverified"], "|", [(d["doc"], d["status"]) for d in p["docs"]])'
  python3 $S --root docs --repo . --fail-on-drift --allow-unverified >/dev/null 2>&1; echo "  allow rc=$?"
done
```

```
f6b        : 0 0 1 | [("mask.md", "unverified")]     ← src/x.py 实际已被改动（应 drifted）
f6b-solo   : 1 0 0 | [("mask.md", "drifted")]        ← 去掉 glob 后立即现形
  f6b        allow rc=0      ← 真实漂移被豁免
  f6b-solo   allow rc=1      ← 豁免拦得住「纯 drifted」
f6c        : 0 0 1 | [("mix.md", "unverified")]      ← src/gone.py 实际已不存在（应 missing_anchor）
f6c-solo   : 0 1 0 | [("mix.md", "missing_anchor")]  ← 去掉占位符后立即现形
  f6c        allow rc=0      ← 硬断裂被豁免
  f6c-solo   allow rc=1      ← 豁免拦得住「纯 missing」
```

**影响**：（a）**默认门禁不受影响**——两种情形默认均 rc=1，未构成静默绿灯；（b）一旦启用 `--allow-unverified`（其正当用途是容忍迁移期未复核），真实漂移/硬断裂被静默放行，与本轮第一项「豁免不误伤」的断言直接冲突；（c）audit 的 `--truth=warn` 报告同样把 drifted/missing 记成 0、unverified 记成 N，缺陷在报告面也不可见。

**定级理由（P2）**：与上一轮 R2D-5（P2，默认免检通道）同类但**影响面更窄**（需显式开关）；仓库当前无任何自动化调用该开关（§3.5 抽查）。**升级条件**：若把 `--allow-unverified` 纳入常规门禁/CI 默认参数，本条升级为 P1。

**建议修法**：把可核验锚点判定前置——先按存在性判 missing_anchor，再按提交时间判 drifted，只有「全部锚点不可核验」或「仅剩不可核验锚点且无失败」才落 unverified；或引入复合态（drifted+unverified）并让 `--allow-unverified` 只减后者。

### R2D56-2（P3）`--allow-unverified` 豁免无痕、无使用边界，与 R2D56-1 叠加构成「永久免检」人因通道

**现象**：豁免只做减法、不留证据；文档只描述「可显式豁免」，未约定「仅限迁移窗口 / 单次 / 需在提交信息登记原因」；报告面（audit）无对应开关，导致「门禁 rc=0」与「报告未清零」长期并存。

**反证据（文件:行）**：

- `skills/doc-governance/scripts/check-doc-drift.py:530-533`——豁免只是 `blocking -= stale + unverified` 后 `return 0`，输出路径无任何「已豁免」提示；
- `skills/doc-governance/SKILL.md:140`——仅一句「`--allow-unverified` 显式豁免后两类」，无时效/比例/登记要求；`docs/GOVERNANCE.md:17`、`docs/proposals/RFC-0005-doc-truth-axis.md:95` 同；
- `skills/doc-governance/scripts/audit-doc-health.py:912-923`——audit 无该开关，warn 模式仍报「真值轴未清零」。

**复现命令与输出**：

```bash
cd /tmp/r2d56/f5a
python3 $S --root docs --repo . --fail-on-drift                    > /tmp/deny.txt  2>&1; echo "deny  rc=$?"
python3 $S --root docs --repo . --fail-on-drift --allow-unverified > /tmp/allow.txt 2>&1; echo "allow rc=$?"
diff /tmp/deny.txt /tmp/allow.txt && echo "两文件逐字节相同（豁免零痕迹）"
```

```
deny  rc=1
allow rc=0
两文件逐字节相同（豁免零痕迹）
```

**定级理由（P3）**：文档**有**说明（不满足「无文档说明即 P2」的判据），且当前无自动化调用；但它把豁免做成不可审计的静默行为，是 R2D56-1 从「理论 P2」滑向「实际 P1」的放大器。

**建议修法**：rc=0 时打印「已豁免 stale×n / unverified×m」并写入 JSON summary；SKILL 增补「仅限迁移窗口；长期容忍须改文档或走 `--write-baseline` 登记」。

### R2D56-3（P2）加粗包裹的真实锚点被判「不可核验」⇒ 由 fresh 降为 unverified（默认门禁假红）

**现象**：修复 R2D-6 时关掉锚点值的去加粗（避免 `src/**` 被抹成 `src/`），副作用是把「用加粗强调真实路径」的 `**src/pkg/x.py**` 也当成含 glob 的不可核验锚点。

**反证据（文件:行）**：`check-doc-drift.py:53-56`（`strip_bold=False` 分支）+ `check-doc-drift.py:66-70`（任一 `*` 即 unverifiable）。

**复现命令与输出**（`/tmp/r2d56/f6/docs/bold.md`，锚点路径真实存在且提交早于复核点）：

```
bold.md -> unverified | anchors: ["**src/pkg/x.py**"] | unverifiable: [true]
default gate rc=1
```

**对照实验（夹具 `f6g`，与 `f6/bold.md` 同路径、仅去掉加粗）**：不加粗时判 `fresh`（`[('plain.md', 'fresh', ['src/pkg/x.py'], [False])]`、`gate rc=0`），加粗后判 `unverified` 且 `gate rc=1`——差异**只来自加粗**，不是路径或时间问题。

**影响**：同一份内容加粗前 fresh、加粗后 unverified（默认 rc=1 阻断）——这是**假红**，并会诱导作者用 `--allow-unverified` 消红（与 R2D56-2 形成负向激励）。当前仓库零实例：`check-doc-drift --json` 显示 3 篇声明文档共 7 条锚点，其中**锚点值含 `*?[]{}<>` 的计数为 0**（加粗只出现在字段名 `**代码锚点**` 上，不在值上），故现实影响为 0。

**定级理由（P2）**：语义静默降级 + 默认阻断（假红），但现网零实例、方向偏保守（不会把坏文档洗绿）。

**建议修法**：glob 判定改为「末段含 `*` 或含 `?[]{}<>`」，并在 `**...**` 首尾成对时先剥一次加粗再判 glob。

### R2D56-4（P2）散文锚点仍判 missing_anchor 硬红——R2D-6 的四个案例只收了三个

**现象**：上一轮 Delta 报告（`docs/project/reviews/2026-11-22-doc-truth-axis/round-2-delta.md:136`）把「非文件型锚点」列为**四**个案例：`skills/**`（glob）、`见附录 A`（散文）、`skills/doc-governance/scripts`（目录）、`<src/a.py:120-168>`（模板占位）。本次修复后 glob/目录/占位符三类分别落 unverified / fresh / unverified，**散文仍判 missing_anchor**。

**反证据（文件:行）**：`check-doc-drift.py:66-70`——散文不含 `*?[]{}<>` 任一字符，不被标记 unverifiable；随后 `check-doc-drift.py:148-149` 因路径不存在而落 missing_anchor。

**复现命令与输出**（`/tmp/r2d56/f6d`）：

```bash
cd /tmp/r2d56/f6d
python3 $S --root docs --repo . --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print({k:p["summary"][k] for k in ("fresh","missing_anchor","unverified")}); [print(" ", d["doc"], "->", d["status"]) for d in p["docs"]]'
python3 $S --root docs --repo . --fail-on-drift                    >/dev/null 2>&1; echo "default rc=$?"
python3 $S --root docs --repo . --fail-on-drift --allow-unverified >/dev/null 2>&1; echo "allow rc=$?"
```

```
{'fresh': 1, 'missing_anchor': 1, 'unverified': 0}
  dir.md -> fresh
  prose.md -> missing_anchor
default rc=1
allow rc=1
```

**影响**：写散文锚点的文档现在**永久红灯**（豁免也救不了），与 R2D-6「不可机械核验的锚点不该硬红」的口径自相矛盾；两种处置都可接受，但必须**显式写进规范**，而不是留给实现细节。

**定级理由（P2）**：同一判据下的一处语义不一致；影响面取决于团队是否写散文锚点（本仓库当前 0 实例）。

**建议修法**（二选一，须落文件）：（a）散文/非路径值在 `normalize_anchor` 阶段即标记 unverifiable（与 glob 同路）；或（b）在 `docs/GOVERNANCE.md` 与 `docs/proposals/RFC-0005-doc-truth-axis.md` 明文写「非路径锚点属声明错误，按 missing_anchor 阻断」，并在 `--help` 里点明。

---

## 6. ④ 终审裁决

**Blockers = 0（P0 = 0 / P1 = 0）。终审裁决：准予交付。**

- 五项主验收条款的验收断言全部实测成立（§3、§4），且**没有**发现「默认门禁静默绿灯」的新通道：drifted / missing_anchor / 墓碑 / unverified / stale 在默认 `--fail-on-drift` 下逐一阻断（§3.1 矩阵 7 行），账本不可用时 rc=2（fail-closed 未被豁免打穿）。
- 4 条新缺陷全部落在 P2/P3：R2D56-1、-3、-4 为 P2，R2D56-2 为 P3。它们都不满足「默认门禁可被静默洗绿」的 P1 判据——R2D56-1 需显式 `--allow-unverified`，R2D56-3/-4 是**假红**（偏保守方向）。
- 遗留动作（不阻断交付，建议本轮回填或下一轮）：
  1. R2D56-1 判定优先序——**建议优先**，它同时消解 R2D56-2 的放大器效应；
  2. R2D56-3 glob 判定收窄（顺带恢复加粗锚点）；
  3. R2D56-4 二选一并写进 GOVERNANCE / RFC-0005；
  4. 台账登记（`docs/project/reviews/2026-11-22-doc-truth-axis/README.md` 的轮次行与报告清单）由主智能体完成，本轮不动该文件。

---

## 7. 残留风险（交付后仍需盯的）

1. **永久免检的人因通道**：`--allow-unverified` 无痕 + 无边界（R2D56-2），叠加「加一个 glob 锚点即可把真实漂移降级」（R2D56-1）。当前无自动化风险，但没有机制阻止人这么做。
2. **散文锚点口径冲突**：R2D56-4 未定策前，同一类「不可机械核验」写法一半容忍、一半硬红，会制造难解释的红灯与「就地改脚本」的冲动。
3. **跨平台未覆盖面**：本轮只在 Linux + Python 3.12.3 + git 2.56.1 取证；大小写不敏感文件系统（macOS/Windows）下 `src/A.py` 与 `src/a.py` 的锚点相等性、Windows 反斜杠归一化未测；仓库无 CI，门禁执行力度依赖人工。

---

## 8. 未验证项与边界

- 未在 macOS / Windows 复跑（大小写不敏感、路径分隔符、`git log -- path` 大小写行为）；
- 未在真实 CI 复跑（仓库**无** `.github/`；门禁是 SKILL 模式 2 的人工调用）；
- 未做千篇级性能测量（46 篇 / 3 篇声明，逐锚点一次 `git log` 未成瓶颈，但未在万级验证）；
- 未验证与他人分支并发改动的冲突（本轮单分支、单工作区、零写操作）。

---

## 附录 A · 夹具复现脚本（核心部分）

```bash
set -u
R=/tmp/r2d56; rm -rf $R; mkdir -p $R
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.com GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.com
S=/home/hui/workspace/projects/cr-agent-arsenal/skills/doc-governance/scripts/check-doc-drift.py
ci() { ( cd "$1" && GIT_AUTHOR_DATE="$2" GIT_COMMITTER_DATE="$2" git add -A >/dev/null \
        && GIT_AUTHOR_DATE="$2" GIT_COMMITTER_DATE="$2" git commit -q -m "$3" ); }
newrepo() { d=$R/$1; mkdir -p $d; ( cd $d && git init -q ); }

# f5a：声明锚点但无复核于
newrepo f5a; mkdir -p $R/f5a/src; echo 'x=1' > $R/f5a/src/a.py
ci $R/f5a "2026-11-01T10:00:00+0800" init
mkdir -p $R/f5a/docs
printf '# A\n\n> 代码锚点: src/a.py\n' > $R/f5a/docs/a.md
ci $R/f5a "2026-11-02T10:00:00+0800" docs
( cd $R/f5a && python3 $S --root docs --repo . --write-baseline >/dev/null )

# f6b：混合锚点（真实漂移 + glob）；f6b-solo 为对照
for f in f6b f6b-solo; do
  newrepo $f; mkdir -p $R/$f/src; echo 'x=1' > $R/$f/src/x.py
  ci $R/$f "2026-11-01T10:00:00+0800" init
  mkdir -p $R/$f/docs
  if [ "$f" = "f6b" ]; then A='src/x.py, src/**'; else A='src/x.py'; fi
  printf '# M\n\n> 代码锚点: %s\n> 复核于: 2026-01-01\n' "$A" > $R/$f/docs/mask.md
  ci $R/$f "2026-11-02T10:00:00+0800" docs
  ( cd $R/$f && python3 $S --root docs --repo . --write-baseline >/dev/null )
done

# 断言：混合锚点把 drifted 洗成 unverified（R2D56-1）
cd $R/f6b-solo && python3 $S --root docs --repo . --fail-on-drift >/dev/null 2>&1; echo "solo  rc=$?  (期望 1)"
cd $R/f6b      && python3 $S --root docs --repo . --fail-on-drift >/dev/null 2>&1; echo "mixed rc=$?  (期望 1)"
cd $R/f6b      && python3 $S --root docs --repo . --fail-on-drift --allow-unverified >/dev/null 2>&1; echo "mixed+allow rc=$? (期望 0 ⇒ R2D56-1)"
```

> 其余夹具（f5b…f5f2、f6/f6c/f6d/f4/f22/f22b/f22c）同构：先用 `ci()` 钉死两次以上提交，再用 `--write-baseline` 生成账本，最后改文档或删声明触发目标状态；断言一律以 `rc` 与 `--json` 的 `summary` 计数为准。
