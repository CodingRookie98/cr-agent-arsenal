# Delta 放行确认审查报告（Round 2 Delta · Confirm）

> **文档控制信息**
> - **文档标识**: REVIEW-R2D-CONFIRM-doc-truth-axis-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: Delta 放行确认审查者（独立上下文，Reviewer ≠ Author）
> - **生效日期**: 2026-11-22
> - **审查对象基线**: `eb8a9c0`（R2D 修复提交）+ `eef817d`（仅文档重钉）+ `baafa66`（仅文档：归档 round-2-delta 并登记台账）；实测 HEAD = `baafa669aa7559b12eb2a00accf9e4ead828343b`
> - **前序裁决**: `round-2-delta.md`（26,672 B / sha256 `a50e5952aae8255cfacb0fb545189cdcf16c175575617d911b8239b5738898a6`——本轮开工复算一致）
> - **审查模式**: 放行确认（只做四件事：R2D-1 放行条件 / R2D-2 多重集 / R2D-3·4 / 回归面）
> - **取证方式**: 全部结论为本机实跑；夹具建于 `/tmp/r2d2`（12 个夹具仓库 + 1 个浅克隆），**仓库工作区、索引、暂存区零写入**（开工与收工 `git status --porcelain` 两次均为空），无任何 git 写操作
> - **唯一写入面**: 本报告文件（未提交）
> - **未验证项**: macOS / Windows 大小写不敏感文件系统、真实 CI（GitHub Actions 默认 `fetch-depth`）、Windows 路径分隔符——本轮仅在 Linux + Python 3.12 实测

---

## 0. 一句话结论

**四件事的主验收条款全部实测通过**（R2D-1 三条 / R2D-2 三条 / R2D-3·4 两条 / 回归面五项，逐条有原文输出），但本轮在 R2D-1 的**同一类内**找到一条未闭合的洗绿路径：**账本"有效但为空"**（`{"docs": {}}`，或 `docs` 值非列表被静默过滤）时 `baseline_status=ok`、`baseline_docs=0`，墓碑判据完全失效，门禁仍给 `rc=0` + `PASS` + `🌟完美` + `15.0`——与 R2D-1 判 P1 时的"洗白后状态"逐项同形，成本同为**一次文件编辑**。据此**Blockers = 1，阻断交付**（并按仓库台账 3/3 迭代上限，须升级人类裁决）。

---

## 1. 基线与会话事实

| 项 | 值 |
| :--- | :--- |
| 分支 | `feat/doc-truth-axis` |
| 开工 HEAD | `eef817d`（审定增量为 `eb8a9c0` + `eef817d`） |
| 收工 HEAD | `baafa66`（会话期间由主智能体新增的**纯文档**提交：仅改 `docs/project/reviews/2026-11-22-doc-truth-axis/README.md`，登记 Delta 轮次） |
| 工作区 | 开工 / 收工两次 `git status --porcelain` 均为空；`--untracked-files=all` 亦为空 |
| 受控文件改动 | 无（本报告为唯一写入，且不提交） |
| git 写操作 | 无（全部 `git` 调用为 `init/add/commit/mv/rm/log/show`，且 `cwd` 全在 `/tmp/r2d2/*`） |

> `baafa66` 只改审查台账 README，不改脚本、不改文档控制头、不改账本，故不改变本轮任何判定；为消除歧义，**回归面五项在 `baafa66` 上重跑**（见 §5）。

---

## 2. 复验环境与夹具

- 脚本（绝对路径调用）：`skills/doc-governance/scripts/{check-doc-drift,audit-doc-health,check-doc-links,check-doc-control-sync}.py`
- 夹具根：`/tmp/r2d2/`（`f1`…`f12` 共 12 个夹具仓库 + 浅克隆 `shallow8`）
- 所有夹具提交用 `GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE` 钉死时间；python 全程 `PYTHONDONTWRITEBYTECODE=1`，pytest 追加 `-p no:cacheprovider`，确保不写仓库字节码/缓存。
- 全部输出原文留档于 `/tmp/r2d2/*.out|*.err`（下文的"关键输出"均为逐字摘录）。

---

## 3. 四项逐条复验

### 3.1 第一项 · R2D-1 放行条件（账本缺席/损坏 fail-closed）

**夹具 `/tmp/r2d2/f1`**：`src/a.py` + `docs/a.md`（`代码锚点: src/a.py`、`复核于: 2026-11-01`），init `2026-11-01`、doc `2026-11-05`。

```bash
S=/home/hui/workspace/projects/cr-agent-arsenal/skills/doc-governance/scripts
F=/tmp/r2d2/f1
# ① 无账本 + --fail-on-drift
python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-drift; echo "rc=$?"
# ② 账本坏 JSON（截断）
printf '{"version": 1, "docs": {"a.md": ["src/a.py"' > $F/docs/.doc-truth-baseline.json
python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-drift; echo "rc=$?"
# ③ 正常账本
python3 $S/check-doc-drift.py --root $F/docs --repo $F --write-baseline
python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-drift; echo "rc=$?"
```

| # | 场景 | 实测关键输出 | 期望 | 判定 |
| :--- | :--- | :--- | :--- | :---: |
| 1a | 无账本 + `--fail-on-drift` | **rc=2**；stderr：`❌ 错误: 锚点基线不可用（missing）：/tmp/r2d2/f1/docs/.doc-truth-baseline.json。墓碑判据无法成立，按 fail-closed 处理；首次启用请先运行 --write-baseline 并提交该账本。` | rc=2 + 引导 | ✔ |
| 1b | 账本坏 JSON | **rc=2**；stderr：`… 锚点基线不可用（corrupt）…` | rc=2 | ✔ |
| 1c | 正常账本（`--write-baseline` 产出 1 篇声明） | **rc=0**；`声明 1/1 篇（覆盖度 100.0%）｜fresh 1…｜真值分: 15.0 / 15` | rc=0 | ✔ |
| 1d | 非门禁模式（**无** `--fail-on-drift`）+ 账本缺失 | rc=0（契约：非门禁模式降级报告） | 0 | ✔（契约如此） |
| 1e | `--baseline /tmp/r2d2/nope.json` + `--fail-on-drift` | **rc=2**；stderr 指向该显式路径 | rc=2 | ✔ |
| 1f | `--json` + 账本缺失 + `--fail-on-drift` | **rc=2**，且 JSON `summary.baseline_status="missing"`、`baseline_docs=0` | rc=2 且状态可机读 | ✔ |
| 1g | **有效但为空的账本** `{"version":1,"docs":{}}` + `--fail-on-drift` | **rc=0**；`baseline_status=ok`、`baseline_docs=0`、`removed=0`、`score=15.0` | 应不可用 | ✘ **R2D2-1（P1）** |
| 1h | 账本 `{"docs":{"tutorials/a.md":"src/a.py"}}`（值非列表 ⇒ 被过滤为空） | `baseline_status=ok`、`baseline_docs=0`（同类，无告警） | 应不可用 | ✘ **R2D2-1** |

**额外核验（与本条直接相关的边界）**：账本路径是目录 ⇒ `IsADirectoryError` ⇒ `corrupt` ⇒ **rc=2**（已拦）；账本 `docs` 是数组 ⇒ `corrupt` ⇒ **rc=2**（已拦）。**空的 `docs` 字典是唯一未被覆盖的"不可用"形态。**

**结论**：放行条件明列的三条（① rc=2+引导 ② 坏 JSON rc=2 ③ 正常账本 rc=0）**逐条达成**。但 Delta 判 P1 时所列五条证据行（B5 / B6 / M1b / M2 / M3）中，**M2（`{"docs":{}}`）仍为 rc=0**，且这是修复提交自己写下的不变量（`check-doc-drift.py:243-244`「『保护不可得』必须与『无违规』在退出码上可区分」）的**直接反例**。故 R2D-1 记「**主路径闭合、类内残余未闭合**」，残余升 **R2D2-1（P1）**。

### 3.2 第二项 · R2D-2 墓碑多重集判据

**夹具 `/tmp/r2d2/f2`**：`docs/d1.md ← src/a.py`、`docs/d2.md ← src/b.py, src/a.py`；基线 2 篇 / 3 条锚点。

```bash
F=/tmp/r2d2/f2
python3 $S/check-doc-drift.py --root $F/docs --repo $F --write-baseline   # 基线
git -C $F mv docs/d1.md docs/d1-renamed.md                                # 纯改名
python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-drift; echo "rc=$?"
```

| # | 场景 | 实测关键输出 | 期望 | 判定 |
| :--- | :--- | :--- | :--- | :---: |
| 2a | 纯 `git mv` 改名（内容逐字节不变，锚点集合不变） | **rc=0**；`声明 2/2｜fresh 2｜…｜真值分 15.0`，**无任何墓碑行** | rc=0 且无墓碑 | ✔ |
| 2b | 删一条锚点（`d2.md` 由 `src/b.py, src/a.py` 改为 `src/b.py`） | **rc=1**；`⛔ 基线墓碑违规（声明被删除/缩减）` | rc=1 | ✔ |
| 2c | 删整篇文档（`git rm docs/d2.md`） | **rc=1**；`⛔ … d2.md 缺失: src/b.py, src/a.py` | rc=1 | ✔ |
| 2d | 合法拆分（锚点总量不变，迁到新文档） | **rc=0** | 0（合法） | ✔（设计如此） |
| 2e | 多锚点文档缩减一条（`f11`，`src/a.py, src/b.py` → `src/b.py`） | **rc=1**，`缺失: src/a.py` | rc=1 | ✔ |

**结论**：多条集判据**三条验收全部达成**，且"改名合法"确实免除了 R2 判 P2 时"改名必红"的误红——这是本轮**最有价值的修复**。副作用见 **R2D2-2（P2，报告面归属失真）**：`f9` 夹具只从 `two.md` 删掉 `src/a.py`（`one.md` 完全未动），输出却为

```
      - one.md 缺失: src/a.py
      - two.md 缺失: src/a.py
```

且 `removed_from_baseline=2`（"墓碑违规 2 处"）——**1 条锚点缺口被计成 2 处、并把仍持有该锚点的文档列为缺失**。

### 3.3 第三项 · R2D-3（未来日期）/ R2D-4（warn 报告面）

**夹具 `/tmp/r2d2/f4`**（`K0` 对照：`复核于 2026-11-01` + 锚点 `2026-11-10` 被改 ⇒ drifted）。

```bash
# K1：只把「复核于」改成 2030-12-31（R2D-3 的洗绿动作）
python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-drift; echo "rc=$?"
python3 $S/check-doc-drift.py --root $F/docs --repo $F --json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["docs"][0]["status"], d["summary"]["freshness_score"])'
python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-unverified; echo "rc=$?"
python3 $S/audit-doc-health.py --root $F/docs --truth=require; echo "rc=$?"
```

| # | 场景 | 实测关键输出 | 判定 |
| :--- | :--- | :--- | :---: |
| K0 | 对照（复核于 2026-11-01） | `drifted 1`、真值分 0.0、`--fail-on-drift` **rc=1** | 基线 |
| **K1** | **复核于 → 2030-12-31** | **`status=unverified`、真值分 0.0**；`--fail-on-drift` rc=0（见 R2D-5 残留）；`--fail-on-unverified` **rc=1**；audit require **REJECTED（真值分 0.0 < 门槛 12.0）** | ✔ **洗绿失效** |
| K2 | 复核于 → 2999-12-31 | `status=unverified`、真值分 0.0 | ✔ |
| K3 | 边界：今天 `2026-11-22` / 明天 `2026-11-23` | 今天 ⇒ `fresh 15.0`（+1d 容忍生效）；明天 ⇒ `unverified 0.0`（当日末刻折算后超前 > 1d） | ✔ 与 RFC:92 字面一致 |

**warn 报告面（夹具 `f3a`=健康对照、`f3b`=墓碑违规 1 处、`f3c`=账本缺失、`f3d`=账本坏 JSON；四者除被测变量外结构全健康，meta 25/25、结构分 100.0）**

| # | 场景 | 实测关键输出 | 判定 |
| :--- | :--- | :--- | :---: |
| 3-control | 全健康 + 账本在位，`--truth=warn` | `🌟 完美！未检测到任何健康缺陷…`（**证明"抑制"不是偶然**） | 对照 |
| 3d | 墓碑违规 1 处，`--truth=warn` | **无「🌟 完美」**；`⚠️ 锚点基线墓碑违规 1 处（声明被删除/缩减）`；`PASS`（warn 不改判） | ✔ |
| 3e | 账本缺失，`--truth=warn` | **无「🌟 完美」**；`⛔ 锚点基线不可用（missing）…` + `⚠️ 锚点基线不可用（missing）` | ✔ |
| 3f | 账本坏 JSON，`--truth=warn` | **无「🌟 完美」**；`⛔/⚠️ 锚点基线不可用（corrupt）` | ✔ |
| 5b | 多锚点缩减（仍 enabled），`--truth=warn` | **无「🌟 完美」**；`⚠️ 锚点基线墓碑违规 1 处`；真值分 15.0 | ✔ |
| 5c | 同上 `--truth=require` | **REJECTED（锚点基线墓碑违规 1 处…）** | ✔ |
| 3g | `--truth=warn` + **drifted 1 篇 / 真值分 0.0** | **仍打印 `🌟 完美`**（同屏：`drifted 1｜真值分 0.0` + 完美） | ✘ **R2D2-3（P2）** |
| 3h | `--truth=off` + 账本缺失 | 真值轴展示块被跳过，但**诊断段仍打印 `⚠️ 锚点基线不可用（missing）` 并抑制「完美」** | ✘ **R2D2-4（P3）** |

**结论**：两条验收条款**均达成**——未来日期不再是复核（不再产出 `fresh + 15.0 + PASS`），warn 模式在账本异常/墓碑违规时不再打印「🌟 完美」，且"全健康时仍打印完美"的对照成立。残留见 R2D2-3/R2D2-4（均非 P0/P1）与 R2D-5（未修，见 §6）。

### 3.4 第四项 · 回归面

```bash
cd /home/hui/workspace/projects/cr-agent-arsenal
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest skills/doc-governance/tests -q -p no:cacheprovider
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --fail-on-drift; echo "rc=$?"
python3 skills/doc-governance/scripts/check-doc-links.py --root docs; echo "rc=$?"
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs; echo "rc=$?"
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs; echo "rc=$?"
python3 skills/doc-governance/tests/test_doc_drift.py   # 直接执行路径（R2D-10）
```

| # | 命令 | 实测关键输出 | 判定 |
| :--- | :--- | :--- | :---: |
| 4.1 | `pytest skills/doc-governance/tests -q` | `192 passed in 23.96s` | ✔ 全绿 |
| 4.2 | `check-doc-drift.py --root docs --repo . --fail-on-drift` | `声明 3/46 篇（覆盖度 6.5%）｜fresh 3｜drifted 0｜missing 0｜stale 0｜unverified 0`、`真值分 15.0/15`、**rc=0** | ✔ |
| 4.3 | `check-doc-links.py --root docs` | `共扫描 95 个 Markdown 文件`、`未发现任何 404 断链…`、**rc=0** | ✔ |
| 4.4 | `check-doc-control-sync.py --root docs` | `共检查 47 个 Markdown 文件`、`控制头与修订历史版本 100% 一致`、**rc=0** | ✔ |
| 4.5 | `audit-doc-health.py --root docs` | `总得分: 100.0 / 100 分`、`🌟 完美…`、`诊断结论: PASS`、**rc=0** | ✔ |
| 4.6 | `python3 tests/test_doc_drift.py`（直接执行） | `Ran 31 tests … OK`（修复前为 13） | ✔ R2D-10 已修 |

**结论**：回归面四项全绿，且提交信息宣称的两处数字（`192 passed`、`Ran 31 tests`）在 `baafa66` 上逐位复现——**自证层无失真**。这一轮修复提交延续了上一轮"不再虚报"的取向，必须记正分。

---

## 4. 新发现缺陷（R2D2-n）

> 计数口径沿用 R2：**仅 P0/P1 计入 Blockers**；P2 优化建议；P3 Backlog。"是否本轮引入"以 `fb62d02..baafa66` 为界。

| 编号 | 定级 | 缺陷 | 证据（实跑） | 机理与落点 | 是否本轮引入 |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **R2D2-1** | **🔴 P1** | **有效但为空的账本 ⇒ 墓碑判据整体失效，且 `rc=0` + `PASS` + `🌟完美` + `15.0`：与 R2D-1 判 P1 时的"洗白后状态"逐项同形** | `f11`（12.1）：账本改 `{"docs":{}}` + 多锚点缩减一条 ⇒ `drift rc=0`、`baseline_status=ok`、`baseline_docs=0`、`score=15.0`、`audit --truth=require rc=0 / PASS / 🌟完美`；同一缩减在账本完好时（12.2）⇒ `rc=1` + 墓碑。`f7`（7.1）：账本清空后 `require` 仍 `rc=0 / PASS / 完美`。`f12`：`docs` 值非列表被静默过滤 ⇒ `status=ok, docs=0` | `load_baseline` 对"可解析但无锚点"返回 `({}, "ok")`（`check-doc-drift.py:260-265`），`analyze` 再以 `if baseline else []` 短路（`:384`），门禁只对 `missing/corrupt` 拦（`:484-490`），audit 的判定梯同样只认 `missing/corrupt`（`audit-doc-health.py:116-117`）。于是"账本被清空"与"从未违规"再次同形——**修复提交自己在 `:243-244` 写下的不变量被自己的状态集合反例化**；RFC:90 的"账本可用性"行亦只覆盖 missing/corrupt，属**契约+实现同缺**。成本仍是**一次文件编辑**（与 `rm` 等价） | 是（新增 `ok` 状态却未定义"空即不可用"） |
| **R2D2-2** | 🟡 P2 | 墓碑报告**归属失真 + 计数膨胀**：未改动的文档被列为"缺失"，1 条缺口计成 2 处 | `f9`（9.1）：只从 `two.md` 删 `src/a.py`，`one.md` 一字未动，输出 `- one.md 缺失: src/a.py` / `- two.md 缺失: src/a.py`，`removed_from_baseline=2` | `_removed_from_baseline` 先算全局 deficit，再**遍历所有基线文档、凡其锚点命中 deficit 即整条登记**（`check-doc-drift.py:302-309`）——归属维度丢失，同一缺口被多文档重复计数 | 是 |
| **R2D2-3** | 🟡 P2 | `--truth=warn` 下 **drifted（真值分 0.0）仍打印「🌟 完美」**，与"墓碑违规即抑制完美"自相矛盾 | `f7`（7.3）：`声明覆盖 1/1｜drifted 1｜真值分 0.0` + `🌟 完美！…` + `PASS` | R2D-4 的补丁把 unavailable / 账本异常 / 墓碑 纳入 `has_issues`（`audit-doc-health.py:889-900`），却未纳入**同轴更强的信号** drifted / missing_anchor / stale / 低真值分；`完美` 仍由 `:902-903` 统一打印 | 否（半继承：合并了三个信号，遗漏四个） |
| **R2D2-4** | 🟡 P3 | `--truth=off` 仍被真值轴影响：打印账本告警并抑制「完美」，与"off 不参与"口径不一致 | `f3c`（3h）：`--truth=off` ⇒ 无真值轴展示块，但诊断段打印 `⚠️ 锚点基线不可用（missing）`，且无「🌟 完美」 | 展示块按 `truth.get("mode") != "off"` 跳过（`:772`），诊断段 `:889` 的 `else` 分支**未按 mode 门控** | 是 |

**复现命令（R2D2-1，自包含，可直接粘贴执行）**

```bash
S=/home/hui/workspace/projects/cr-agent-arsenal/skills/doc-governance/scripts
F=/tmp/r2d2-repro; rm -rf $F; mkdir -p $F/docs/tutorials $F/src
cd $F && git init -q
printf 'a = 1\n' > src/a.py; printf 'b = 1\n' > src/b.py
hdr(){ printf '# 指南 A\n\n> **文档控制信息**\n> - **文档标识**: DOC-A\n> - **当前版本**: V1.0.0\n> - **代码锚点**: %s\n> - **复核于**: 2026-11-01\n' "$1"; }
hdr 'src/a.py, src/b.py' > docs/tutorials/a.md
git add -A && GIT_AUTHOR_DATE=2026-11-01T00:00:00Z GIT_COMMITTER_DATE=2026-11-01T00:00:00Z git commit -q -m init

# 基线：1 篇 / 2 条锚点
python3 $S/check-doc-drift.py --root $F/docs --repo $F --write-baseline

# 洗绿两连：① 账本改写为 {"docs":{}}（不删文件）② 锚点由两条缩为一条
printf '{"version":1,"docs":{}}\n' > $F/docs/.doc-truth-baseline.json
hdr 'src/b.py' > $F/docs/tutorials/a.md
git add -A && GIT_AUTHOR_DATE=2026-11-20T00:00:00Z GIT_COMMITTER_DATE=2026-11-20T00:00:00Z git commit -q -m wash

python3 $S/check-doc-drift.py --root $F/docs --repo $F --fail-on-drift; echo "rc=$?"   # 实测 0（期望 2）
python3 $S/audit-doc-health.py --root $F/docs --truth=require;       echo "rc=$?"      # 实测 0 / PASS（期望阻断）
# 对照：把账本恢复（cp /tmp/r2d2/f11.baseline.json 或重跑 --write-baseline 前先 git revert）⇒ rc=1 + 墓碑
```

**建议最小修复（约 4 行代码 + 1 行契约 + 2 条回归，与 R2D-1 同构）**

1. `check-doc-drift.py:260-265`：`parsed` 为空且 `parsed` 与"当前声明"矛盾时返回新状态——精确条件为 **`baseline_docs == 0 且 declared > 0`** 记为 `"empty"`（与 `missing/corrupt` 同列）。
2. `check-doc-drift.py:484`：状态集合改为 `("missing", "corrupt", "empty")`，沿用同一句 stderr 引导。
3. `audit-doc-health.py:116`：同样纳入 `empty`（require 阻断 + warn 抑制完美）。
4. RFC §4.2「账本可用性」行补"空账本且存在声明 ⇒ 同样 fail-closed"；补 2 条回归（空账本 rc=2；`docs` 值非列表 ⇒ rc=2）。
   > 该条件**不会产生误红**：`--write-baseline` 在存在声明的树上必然写出非空账本；`declared == 0` 时不触发。

---

## 5. 前轮 P2/P3 状态核对（非本轮验收项，仅登记事实）

| 前轮编号 | 本轮实测状态 | 证据 |
| :--- | :--- | :--- |
| R2D-2（改名必红） | **已闭合** | 2a：纯 `git mv` ⇒ rc=0、无墓碑 |
| R2D-3（未来日期洗绿） | **已闭合** | K1：`unverified` + 真值分 0.0 + require REJECTED |
| R2D-4（报告面） | **部分闭合** | unavailable 已展示（8）；**但**浅克隆仍打印 `missing 1｜真值分 0.0`（未置 N/A）；非标准 `--root docs/tutorials` 下 audit 判 `missing 1`、drift 判 `drifted 1`（基准仍不一致，9）；warn+drifted 仍打印完美（R2D2-3） |
| R2D-5（`--fail-on-drift` 不含 unverified） | **未修** | K1：`unverified 1` 时 `--fail-on-drift` 仍 rc=0；须显式 `--fail-on-unverified` |
| R2D-6（非文件型锚点硬红） | **未修** | `代码锚点: skills/**` ⇒ `missing 1` ⇒ rc=1；`<src/a.py:120-168>` ⇒ `missing 1` ⇒ rc=1（且被记入墓碑 `缺失: skills`） |
| R2D-7（契约字面量冲突） | **部分闭合** | RFC:89「幂等」已改为"默认只读 + 显式 `--write-baseline`"；**仍存**：RFC:98 / SKILL:142 仍写"按序判定三条"（实现已 6 条并列）、脚本 docstring:4 仍自称"绝不写文件"、:17 退出码说明未含账本级 2 |
| R2D-8（操作面未接线） | **已闭合** | `--write-baseline` 已出现在 SKILL:140、matrix:30、GOVERNANCE:96 与 RFC:89-91 |
| R2D-9（弱断言） | **未修（新增用例已改进）** | 旧 `assertIn("unverified", stdout)` 仍在；新增用例改断 `returncode` + 具体文案，方向正确 |
| R2D-10（直接执行死区） | **已闭合** | `python3 test_doc_drift.py` ⇒ `Ran 31 tests OK` |
| R2D-11（已跟踪但工作区被改） | **未修（Backlog）** | 维持原判定，不建议本轮做 |

---

## 6. 终审裁决

### 6.1 统计

| 类别 | 数量 | 明细 |
| :--- | :---: | :--- |
| 🔴 **Blockers（P0/P1）** | **1** | **R2D2-1**（有效但为空的账本 ⇒ 墓碑失效且 rc=0/PASS/完美/15.0） |
| ✅ 本轮验收条款达成 | 4/4 项 | R2D-1 三条主验收全达成（类内残余另计 R2D2-1）；R2D-2 三条全达成；R2D-3/4 两条全达成；回归面五项全绿 |
| 🟡 P2 | 2 | R2D2-2（墓碑归属/计数失真）、R2D2-3（warn+drifted 仍打印完美） |
| 🟡 P3 | 1 | R2D2-4（`--truth=off` 仍受真值轴告警影响） |
| ⚪ 驳回 | 0 | — |

### 6.2 裁决

> ## 🔴 **阻断交付（Blockers = 1 > 0）**
>
> **判定理由（一句话）**：R2D-1 的主验收三条**确已达成**且取证扎实（缺账本/坏 JSON ⇒ rc=2 + 引导；正常账本 ⇒ rc=0），R2D-2 的多重集改判也确实把"改名必红"这一误红解除；但**修复把不变量收缩到了它自己的状态集合**——账本"存在、可解析、但内容为空"时，`baseline_status` 仍报 `ok`，墓碑判据整体失效，而门禁给 `rc=0`、`audit` 给 `PASS + 🌟完美 + 15.0`（12.1 实测）。这与 Delta 判 R2D-1 为 P1 的原始理由（"保护不可得"与"无违规"在退出码上完全同形）**逐项同形，触发成本同为一次文件编辑**，而修复提交在 `check-doc-drift.py:243-244` 自述的不变量恰是这条更宽的命题。依据"宣称与取证同宽"，该 P1 只能记**未闭合**。
>
> **放行条件（最小集，见 §4 建议修复）**：① `baseline_docs == 0 且 declared > 0` ⇒ 与 missing/corrupt 同列（rc=2 + 同一引导，audit require 阻断、warn 抑制完美）；② RFC §4.2「账本可用性」补该行；③ 补 2 条回归（空账本 rc=2、`docs` 值非列表 rc=2）；④ 以新提交为基线再走一次**定向**复验（仅复跑 §3.1 的 1a–1h + §3.4 五项即可，无需再开整轮）。修完 Blockers 归零即准予交付。
>
> **流程提示（必须由人类裁决）**：仓库台账 `docs/project/reviews/2026-11-22-doc-truth-axis/README.md` 已登记**迭代计数 3/3**（"按铁律 6 已达循环上限，若再阻断须升级人类裁决"）。本报告按任务口径给出技术裁决 = **阻断**；若人类认为 R2D2-1 可接受（即"账本内容由 PR 评审负责"的口径），可显式下调为 P2 并直接放行——本审查者不代行该决定，但**反对**把它写成"账本一致由人工保证"而不改任何代码：那正是 R2 曾用来拦截墓碑方案的同一理由。

### 6.3 残留风险（移交下一次交付）

1. **账本仍是单一可编辑信任锚（结构性）**：本轮堵住"不存在/不可解析"，未堵"存在但空"与"存在但滞后"——**任何未登记的新声明都不在保护范围内**，而"何时登记"只靠提交信息自觉。真正的解法是把判据从"账本比对"改为"可从 git 历史重算的不变量"（例如"任一提交不得使声明锚点多重集减少"，用 `git log -p` 逐提交计算），代价是性能，收益是不再需要账本。
2. **R2D-5/R2D-6 未修，二者互相喂养（可机械发现）**：提交前门禁对 `unverified` 仍 rc=0；非文件型锚点（glob/目录/散文/占位符）永久硬红。前者的窗口期正是后者最常出现的时刻，而唯一出路是 `--write-baseline`——**那条一键洗白命令**。
3. **报告面与门禁面仍在两张纸上（可观测性）**：warn 下 `drifted 1 / 真值分 0.0` 仍打印「🌟 完美」；浅克隆仍显示具体 `missing 1 / 0.0` 而非 N/A；非标准 `--root` 的锚点基准仍与 `--repo` 错位。评审者读到的数字仍可能与被门禁结论相反。

---

## 7. 自证边界

- 本报告全部结论均在 `baafa66` 上本机实跑取得；未采信任何"已修复"的提交信息。
- 夹具、输出原文、重复实验命令均在 `/tmp/r2d2/`，可按 §3 的代码块逐条复现。
- 未验证：Windows / macOS 文件系统语义、真实 CI 的 `fetch-depth` 默认值、并发提交下的账本冲突（本地无并发写场景）。
- 本报告为唯一写入，未提交、未改仓库任何受控文件、未执行任何 git 写操作。

---

*本确认书由 Delta 放行确认审查者（独立上下文）基于本机实跑证据作出；四件事的主验收条款均已达成，唯 R2D-1 类内残余（R2D2-1）仍为 P1，故 Blockers = 1，阻断交付。*
