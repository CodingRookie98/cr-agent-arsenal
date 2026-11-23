# BD-1-R 独立确认报告（第 1 轮）

> **审查基线**: `792f68e`（被审修复）+ 工作树 `ef7e325`（文档收口进行中，无关）
> **审查模式**: 隔离子智能体只读复核（Reviewer ≠ Author）
> **日期**: 2026-11-23
> **口径**: 夹具全部落 `/tmp/bd1r-confirm-3WJobf/`；仓库仅读取与跑测（`PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`）

## 0. 裁决

| 项 | 结果 |
| :--- | :--- |
| **裁决** | **FAIL（阻断）** |
| Blockers（P0/P1） | **1**：BD-1-R2 —— `drifted` 子句未实现，多锚点部分漂移可被 `--staged` 刷新洗成 fresh |
| 已闭合部分 | 机制 A（文档已暂存但未刷新 → 无 else）已修；机制 B 的 `missing_anchor` 半边已修 |
| 回归面 | `pytest skills/doc-governance/tests -q` = **295 passed**（与提交信息一致） |

## 1. 夹具实测表

统一命令：`python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --staged --fail-on-drift`（夹具均在独立 `git init` 仓库，已 `--write-baseline`）。

| 夹具 | 场景（全部已暂存） | 实际 rc / 状态 | 期望 | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| C | 改锚点 + 文档加一行注释 | rc=1｜fresh 0 / drifted 1 | rc=1/drifted | ✅ |
| C2 | 改锚点 + 文档仅加一个空行 | rc=1｜fresh 0 / drifted 1 | rc=1/drifted | ✅ |
| F | 删锚点文件 + 只改「复核于」日期 | rc=1｜missing 1 | rc=1/missing_anchor | ✅ |
| **G** | 双锚点：A1 已提交漂移，仅暂存 A2 + 刷新「复核于」日期 | **rc=0｜fresh 1** | rc=1/drifted | ❌ **假阴性（Blocker）** |
| L | 改锚点 + 「复核于」刷新（日期），同次暂存 | rc=0｜fresh 1 | rc=0/fresh | ✅ |
| L2 | 锚点变更已提交，暂存「复核于」指向该提交 sha | rc=0｜fresh 1 | rc=0/fresh | ✅ |
| E1 | 锚点路径含空格 `src/my file.py` | rc=1｜drifted 1 | rc=1 | ✅ |
| E2 | 锚点路径中文 `src/锚点.py` | **rc=0｜fresh 1** | rc=1 | ❌ 假阴性（父版本同形，既有缺陷） |
| E3 | 文档名中文 `文档.md` + 合法刷新 | **rc=1｜drifted 1** | rc=0 | ❌ 假阳性（父版本同形，既有缺陷） |
| E4 | 新锚点文件未跟踪 + 文档已暂存 | rc=1｜unverified 1 | rc=1 | ✅ |
| E4b | 新锚点文件已 `git add` 未提交 | rc=1｜drifted 1 | rc=1 | ✅ |
| E5 | `--staged` 但目录非 git 仓库 | rc=2 + `❌ 不是 git 仓库` | rc=2 | ✅ |
| E6 | 干净索引（hook 常态，staged 为空集） | rc=0｜fresh 1 | rc=0 | ✅ |
| E7 | 文档内删掉一个锚点声明 + 刷新复核于 | rc=1（基线墓碑违规） | rc=1 | ✅ |

### G 的归因隔离

```text
(a) 非 staged 复检（HEAD 已含 A1 漂移）: drifted 1 / rc=1        ← 漂移真实存在
(b) staged + 文档未刷新:  drifted 1 / rc=1                       ← else 分支生效
(c) staged + 刷新复核于:  fresh 1 / rc=0                          ← drifted 被覆盖（缺陷点）
```

### 真实 hook 端到端

```text
1) 种入历史漂移: commit --no-verify → e3c058a；复检 drifted 3 / rc=1
2) 探针: 仅暂存 check-doc-drift.py + 三篇文档「复核于」日期刷新
   git commit → commit_rc=0，HEAD=ffc1cd5 落库
3) 提交后非 staged 复检: drifted 3 / rc=1（复核点仍落后）
4) 对照: 只暂存 A2、文档不动 → commit_rc=1，门禁输出「❌ 真值轴 … drifted 3」→ hook 确实在跑
5) 反事实克隆（只改 584 行）: 同一探针 commit_rc=1，HEAD 停在 seed → 该子句必要且充分
```

**审的是实际路径**：`check-all.py:65` 真值轴项为 `--root docs --repo . --fail-on-drift --staged`；`.githooks/pre-commit:33` 调用 `check-all.py --quiet`；仓库 `core.hooksPath=.githooks` 已安装；全仓无 `.github` CI 另一路径。

## 2. 逐条对照审查者建议

审查者原文（`round-1-delta-confirm.md:100`）："staged 分支补 `else: status = "drifted"`，并仅在 `status not in ("missing_anchor","drifted")` 时允许提升为 fresh；补两条 staged 回归用例（注释/空行）。"

| 子句 | 结论 | 位置 / 证据 |
| :--- | :--- | :--- |
| ① 补 `else: status = "drifted"` | **已实现** | `check-doc-drift.py:586-588`；夹具 C/C2 rc=1 |
| ② 仅 `status not in ("missing_anchor","drifted")` 时提升 fresh | **半实现**：只写 `missing_anchor`，漏 `"drifted"` | `check-doc-drift.py:584` `if status != "missing_anchor":`；夹具 G rc=0/fresh，反事实改回原句即 rc=1 |
| ③ 两条 staged 回归用例（注释/空行） | **半实现**：注释有；空行缺（第二条换成了 missing_anchor） | `test_doc_drift.py:1502`（注释 ✅）、`:1517`（missing_anchor ❌） |
| ④ 「禁止覆盖硬断裂」（作者声称） | 已实现（仅 missing_anchor） | 夹具 F rc=1/missing_anchor |

## 3. 测试承重

```text
$ git archive 792f68e^ | tar -x -C /tmp/bd1r-confirm-3WJobf/parent
$ (在父版本树上跑 TestBD1Staged)
FAILED ...::test_bd1r_missing_anchor_not_masked_by_staged_refresh      (0 != 1, fresh 1)
FAILED ...::test_bd1r_staged_doc_without_refreshing_verified_is_drifted (0 != 1, fresh 1)
2 failed, 65 deselected in 1.55s
$ (HEAD 同一命令) 2 passed, 65 deselected in 1.49s
```

**承重面不足**：无 G（多锚点部分漂移）用例；全仓 `--staged` 仅 3 处调用且全部断言 rc=1，无 rc=0 正例。

## 4. 新缺陷清单

### BD-1-R2 [P1 · 阻断] `drifted` 子句缺失导致多锚点部分漂移可被 `--staged` 刷新洗白
- **位置**：`skills/doc-governance/scripts/check-doc-drift.py:584`
- **机制**：判据写成 `if status != "missing_anchor":`，缺 `"drifted"`；`classify_doc` 已判 `drifted` 的文档，在暂存「另一锚点 + 复核于刷新」后被无条件提升为 `fresh`。
- **证据**：§1 夹具 G；真实 hook 探针提交落库 `ffc1cd5`，三篇 drifted 文档被洗白。
- **修复建议**：`if status not in ("missing_anchor", "drifted"):`，并补 G 与空行用例。

### P2/P3 残余（不计 Blockers）
- `staged_paths` 未关 `core.quotePath`：非 ASCII 路径被转义 → 中文锚点失明（E2 rc=0）、中文文档名合法刷新被误判漂移（E3 rc=1）。
- `_verified_line_changed_staged` 在 `git show HEAD:path` 失败（新增文档/改名）时 `return True`：新文档一律视为已刷新，与 drifted 子句叠加仍是洗白通道。
- BD-9（既有 P2）：单锚点只改「复核于」日期即可 fresh，未校验其指向提交是否覆盖本次锚点变更。
- 测试卫生：`test_doc_drift.py:1460-1462` 三个空行；`TestBD1Staged.setUp` 的 `self.mod` 未使用。

## 5. 结论

本轮判 **FAIL**。BD-1-R 的 `drifted` 半边未闭合，且真实 pre-commit hook 可被绕过落库；须修复后重派确认。
