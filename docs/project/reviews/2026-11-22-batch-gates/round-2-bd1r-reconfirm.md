# BD-1-R 独立确认报告（第 2 轮 · 修复后）

> **审查基线**: 工作树（未提交）——`check-doc-drift.py` + `test_doc_drift.py` 两文件改动；文档改动为并发收口，与本次无关
> **审查模式**: 同一隔离子智能体续轮（Reviewer ≠ Author）
> **日期**: 2026-11-23
> **口径**: 夹具 `/tmp/bd1r-confirm-3WJobf/fx_r2|fx_edge|fx_edge2/`；仓库只读

## 0. 裁决

| 项 | 结果 |
| :--- | :--- |
| **裁决** | **PASS** |
| Blockers（P0/P1） | **0** |
| 上一轮 Blocker BD-1-R2 | ✅ 已闭合：`check-doc-drift.py:587` 判据为 `status not in ("missing_anchor", "drifted")` |
| 非 ASCII 路径（上轮 P2） | ✅ 已修复：`staged_paths()`（`:461-470`）使用 `-c core.quotePath=false` |
| 回归面 | `pytest skills/doc-governance/tests -q` = **298 passed**（295+3）；`check-all.py` = **6/6 全绿** |

## 1. 夹具实测表

| 夹具 | 场景 | 实际 rc / 状态 | 期望 | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| C | 改锚点 + 加一行注释 | rc=1｜drifted 1 | rc=1/drifted | ✅ |
| C2 | 改锚点 + 仅加空行 | rc=1｜drifted 1 | rc=1/drifted | ✅ |
| F | 删锚点文件 + 只改日期 | rc=1｜missing 1 | rc=1/missing | ✅ |
| **G** | 双锚点：A1 已提交漂移，仅暂存 A2 + 刷新日期 | **rc=1｜drifted 1** | rc=1/drifted | ✅ **关口** |
| L | 改锚点 + 日期刷新，同次暂存 | rc=0｜fresh 1 | rc=0/fresh | ✅ |
| L2 | 锚点已提交，复核于指向该提交 sha | rc=0｜fresh 1 | rc=0/fresh | ✅ |
| E1 | 锚点路径含空格 | rc=1｜drifted 1 | rc=1 | ✅ |
| **E2** | 中文锚点路径 `src/锚点.py` | **rc=1｜drifted 1** | rc=1 | ✅（上轮 rc=0） |
| **E3** | 中文文档名 `文档.md` + 合法刷新 | **rc=0｜fresh 1** | rc=0 | ✅（上轮 rc=1） |
| E6 | 干净索引 | rc=0｜fresh 1 | rc=0 | ✅ |
| E4 / E4b | 新锚点未跟踪 / 已 add 未提交 | rc=1 unverified / rc=1 drifted | rc=1 | ✅ |
| E5 | 非 git 仓库 | rc=2 + 明确报错 | rc=2 | ✅ |
| E7 | 删锚点声明 + 刷新 | rc=1（基线墓碑违规） | rc=1 | ✅ |
| E8 | 中文+空格路径 `src/中文 文件.py` | rc=1｜drifted 1 | rc=1 | ✅ |
| E10 | 中文文档名 + 中文空格锚点 + 合法刷新 | rc=0｜fresh 1 | rc=0 | ✅ |

### 真实 pre-commit hook

```text
baseline check-all --quiet → rc=0（6/6）
seed: 改 audit-doc-health.py，git commit --no-verify → 6f90dc0；复检 drifted 3 / rc=1
probe: 仅暂存 check-doc-drift.py 注释 + 三篇文档「复核于」日期刷新
  git commit → rc=1
  ❌ 真值轴 … fresh 0｜drifted 3 … 🚫 提交被阻断
  HEAD_before = 6f90dc04…；HEAD_after = 6f90dc04… → HEAD 未移动 ✔
```

合法路径 hook 反证（无历史漂移）：改锚点 + 三篇文档复核于刷新 → `commit_rc=0`，HEAD `ef7e325→eaab0d0`，提交后复检 `fresh 3 / drifted 0 / rc=0` → 不误伤。

## 2. 新增 3 条测试的承重结论

| 测试 | 792f68e^ | 792f68e | 当前工作树 | 结论 |
| :--- | :--- | :--- | :--- | :--- |
| `test_bd1r_staged_blank_line_only_is_drifted`（:1552，C2） | FAIL | PASS | PASS | 承重（防 C2 回归；C2 行为首轮已对，属护栏用例） |
| `test_bd1r_multi_anchor_partial_drift_not_masked`（:1568，G） | FAIL | **FAIL** | PASS | **承重**：本轮 `drifted` 子句的回归锁 |
| `test_bd1r_unicode_anchor_and_doc_paths_detected`（:1590） | FAIL | **FAIL** | PASS | **承重**：quotePath 修复的回归锁 |

## 3. 工作树核对

- 在审改动 2 个文件：`check-doc-drift.py`（2 hunk，+9 行）、`test_doc_drift.py`（+89/−1，删 `self.mod` 死代码 + `_setup_multi` + 3 条用例），与描述一致，无夹带。
- 其余 12 个改动文件为并发文档收口，与本次修复无关；`check-all` 6/6 说明未与门禁冲突。

## 4. 残余风险（均不阻断）

| 级别 | 位置 | 说明 | 处置 |
| :--- | :--- | :--- | :--- |
| P2 | `check-doc-drift.py:288-291` | 新增/改名文档 `git show HEAD:path` 失败即 `return True`，留「新建文档洗白」窄缝 | BK-0055 |
| P2 | `check-doc-drift.py:326-345` | 纯日期型「复核于」可单独洗白单锚点（BD-9） | BK-0055 |
| P3 | `test_doc_drift.py:1590` | Unicode 用例只覆盖「漂移必报」负向，缺「中文文档名 + 合法刷新 → fresh」正例 | BK-0055 |
| P3 | `check-doc-drift.py:467` | `--name-only` 对含 `"`、反斜杠、换行的文件名仍加引号 | BK-0055（按需改 `-z`） |
| P3 | 基线墓碑（既有） | 锚点文件 `git mv` 改名触发 rc=1 | 操作约束：改名时同步 `--write-baseline` |

## 5. 终审结论

> **BD-1-R / BD-1-R2 终审确认：PASS。** `check-doc-drift.py:587` 的 `status not in ("missing_anchor","drifted")` 与 `staged_paths()`（`461-470`）的 `core.quotePath=false` 均已落地；独立夹具 C/C2/F/G/L/L2/E1/E2/E3/E6 及扩展 E4/E5/E7/E8/E10 全数符合预期（G=rc=1/drifted、E2=rc=1、E3=rc=0）；真实 pre-commit hook 对「仅暂存 A2 + 刷新复核于」探针 rc=1 且 HEAD 不动，合法路径 commit rc=0 零回归；`pytest` 298 passed、`check-all` 6/6。残留仅 P2/P3，已登记 BK-0055，不阻断交付。
