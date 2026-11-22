# Delta 复核确认报告（BD-1/BD-2）— 终审确认

> **审查基线**: `08ebce5`（含修复提交 `e80f8c2` / `90eb094`，分支 `feat/doc-truth-axis`）
> **依据**: `round-1-delta.md`（23,368 B，sha256 `fb593a0b…`）判定的 BD-1 / BD-2 两条 P1
> **契约**: RFC-0008 V0.1.1、GOVERNANCE V1.11.1 ｜ **日期**: 2026-11-22
> **口径**: 只读复核；夹具全部落 `/tmp/bd1fix/`，仓库仅新增本报告

## 0. 裁决摘要

| 项 | 结果 |
| :--- | :--- |
| BD-1 | ⛔ **未闭合（P1）**：非 staged 口径已修（改锚点+一行注释 → drifted/rc=1）；但 **pre-commit 的 `--staged` 口径仍 fresh/rc=0**，真实 hook 实测攻击提交可落库（HEAD `aebbf79`）；且 staged 分支 `status="fresh"` 会无条件覆盖 `missing_anchor`/`drifted` |
| BD-2 | ✅ **闭合**：三夹具全过（① rc=1 并列出未暂存文件；② rc=0；③ `PYTHON_BIN=true` → rc=1）；原始反例（staged 80,432 B + 工作树回退）被拦；残留 `assume-unchanged` 绕行 P2 |
| 回归面 | ✅ `check-all.py` 六项全绿 rc=0；`pytest -q` **293 passed** |
| **Blockers（仅 P0/P1）** | **1**：BD-1 预提交口径未收口 ｜ **裁决：阻断（不准予交付）** |

## 1. BD-1 同提交豁免内容盲区

### 1.1 要求夹具：非 staged 口径（提交后）— 通过
夹具 `/tmp/bd1fix/mA|mB`（独立 `git init` 仓库：`src/x.py` 锚点、`docs/a.md` 控制头、已 `--write-baseline`）：
```text
A 改锚点 + 文档只加一行注释（复核点不动）:
$ python3 check-doc-drift.py --root docs --repo . --fail-on-drift
📊 fresh 0｜drifted 1｜…    - [drifted] a.md ← src/x.py      rc=1   ✅
B 改锚点 + 刷新「复核于」指向父提交（同一次提交）:
📊 fresh 1｜drifted 0｜…    🎯 15.0 / 15                     rc=0   ✅
```

### 1.2 关键反例：staged 口径（pre-commit 实际入参）仍放行 — P1 未闭合
`check-all.py:63-65` 给真值轴固定传 `--staged`，hook 只走 staged 分支。夹具 `/tmp/bd1fix/mC|mC2`：
```text
C  改锚点 + 文档一行注释（暂存）:
$ python3 check-doc-drift.py --root docs --repo . --fail-on-drift --staged
📊 fresh 1｜drifted 0｜…    🎯 15.0 / 15                     rc=0   ⛔
$ git commit -qm C                                  → commit rc=0（落库）
C2 改锚点 + 文档仅加一个空行（暂存）: 同上 fresh 1 / rc=0        ⛔
```
真实仓库克隆 + 真实 hook（`/tmp/bd1fix/repo`，`core.hooksPath=.githooks`；三篇声明同一锚点的文档各加一行注释、锚点脚本加一行注释）：
```text
$ git commit -qm "probe: anchor + one comment"
   commit rc=0   HEAD -> aebbf79
   anchor_sha=aebbf79；三篇文档 复核于 仍为 commit e80f8c2   ⛔ 复核点落后 1 个提交
   提交后 check-doc-drift（非 staged）: drifted 3 / rc=1（仅事后可见）；再提交无关改动被 hook 拦
```
**根因**（`check-doc-drift.py:579-584`）：
```python
if touched:
    if doc_repo_rel in staged and _verified_line_changed_staged(...):
        status = "fresh"          # 无条件覆盖，missing_anchor/drifted 也被洗白
    elif doc_repo_rel not in staged:
        status = "drifted"
# 缺 else：文档已暂存但「复核于」未刷新 → 维持 classify_doc 的 fresh
```
补充夹具（同一 staged 分支缺陷）：
```text
F 删除锚点文件 + 只改「复核于」日期（暂存）:  staged fresh 1 / rc=0 ⛔；提交后 missing_anchor / rc=1
G 两锚点：A1 已单独漂移；仅暂存 A2 + 复核于日期 → staged fresh 1 / rc=0 ⛔（A1 漂移被洗白）
```

### 1.3 P2 残留（不计 Blockers）
`/tmp/bd1fix/f2` 单锚点：改锚点 + 只把「复核于」日期 22→23（commit 仍指旧提交）→ fresh/rc=0。判据只要求该行文本变化，不校验其指向的提交覆盖本次锚点变更。

## 2. BD-2 pre-commit 校验工作树、提交的是索引
真实克隆 `/tmp/bd1fix/repo`，`core.hooksPath=.githooks`，逐项实测：
```text
① git add 后再改工作树:
   $ git diff --name-only → docs/project/plans/2026-11-22-doc-truth-axis.md
   $ git commit … → rc=1，HEAD 不变
   stderr: 🚫 工作树存在未暂存改动，pre-commit 校验结果不可信：
              docs/project/plans/2026-11-22-doc-truth-axis.md
              请先 git add 使工作树与索引一致，再提交。            ✅
② 工作树 == 索引:
   $ git commit --allow-empty -m probe → rc=0，HEAD -> 90d8ffc      ✅
   正常提交（staged 文档改动、工作树一致）→ rc=0，HEAD -> 33dbc5a   ✅
③ PYTHON_BIN=true:
   $ PYTHON_BIN=true git commit … → rc=1，HEAD 不变
   🚫 PYTHON_BIN 不是可用的 Python 3 解释器：true                   ✅
   （另测 PYTHON_BIN=/nonexistent/python3 → rc=1，同类通过）
原始 BD-2 反例：staged 80,432 B 文档 + 工作树回退 40,431 B
   $ git show :FILE | wc -c → 80432；工作树 40431；git diff --name-only 列出该文件
   $ git commit → rc=1，HEAD 不变                                   ✅ 被拦
```
**P2 残留**：`git update-index --assume-unchanged FILE` 可让 `git diff --name-only` 为空 → 提交 80,432 B 内容 rc=0（实测 HEAD `5ba2dbd`，committed bytes=80432）。需显式 plumbing，非默认路径，不计 Blocker。

## 3. 回归面
```text
$ python3 skills/doc-governance/scripts/check-all.py
✅ 机器地图 ✅ 断链 ✅ 版本一致 ✅ 真值轴 ✅ 健康体检 ✅ 可回答性
🏁 全部门禁通过（6 项）                                          rc=0
$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest skills/doc-governance/tests -q -p no:cacheprovider
293 passed in 25.14s                                            rc=0
```
（注：`e80f8c2` 提交信息写 292 passed；`90eb094` 后为 293，与实测一致。）

## 4. 新缺陷清单
### BD-1-R [P1 · 阻断] 同提交豁免在 pre-commit（--staged）口径仍可被「改锚点 + 一行注释/空行」蒙混，且 staged 分支将 missing_anchor/drifted 洗成 fresh
- **位置**：`skills/doc-governance/scripts/check-doc-drift.py:579-584`。
- **机制**：staged 分支仅在「文档未暂存」时置 drifted；文档已暂存但「复核于」未刷新时无处理，维持 `classify_doc` 的 fresh（pre-commit 时 `git log` 看不见本次改动）。「文档已暂存且复核于行变过」时无条件 `status="fresh"`，覆盖 `missing_anchor`/`drifted`（F/G 实测）。
- **证据**：§1.2；真实 hook 提交 `aebbf79` 落库，三篇文档复核点落后一个提交；`e80f8c2` 提交信息仅出示非 staged 的 drifted 证据，未覆盖 hook 口径。
- **修复**：staged 分支补 `else: status = "drifted"`，并仅在 `status not in ("missing_anchor","drifted")` 时允许提升为 fresh；补两条 staged 回归用例（注释/空行）。
### BD-8 [P2] `assume-unchanged`/skip-worktree 可让 BD-2 的「工作树==索引」断言失明（见 §2）。
### BD-9 [P2] 「复核于」内容判据只比行文本，不比其指向提交是否覆盖本次锚点变更（日期 22→23、commit 仍旧即可 fresh，见 §1.3）。

## 5. 裁决
```text
Blockers（仅计 P0/P1）: 1
  BD-1-R [P1] pre-commit(--staged) 口径仍放行「改锚点 + 一行注释」，且可洗白 missing_anchor/drifted
BD-2: ✅ 闭合（①②③ + 原始反例全部符合）
回归: ✅ check-all 6/6；pytest 293 passed
裁决: 阻断（不准予交付）
```
