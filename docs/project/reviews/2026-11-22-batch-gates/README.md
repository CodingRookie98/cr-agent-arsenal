# 审查归档 · batch-gates

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-batch-gates
> - **当前版本**: V1.1.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: batch-gates（RFC-0008 体量门禁 + BK-0048 门禁自动化 + BK-0049 可回答性评测）
- **归档根**: docs/project/reviews/2026-11-22-batch-gates/
- **审查模式**: light
- **当前迭代计数**: 5/5（Light 红队 + Delta 复核 + 最终确认 + BD-1-R 独立确认 ×2；五轮合计 6 个 P1 全部收口）
- **终审裁决**: 准予交付

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| r1 | `14166b1..9d03d22` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-light.md](./round-1-light.md) | a43546c7723e | 🔴 阻断（Blockers=2：B-01 门禁红灯 / B-02 hook 结构性失明） | direct（23,227 B；主智能体独立复算 sha256 一致） |
| delta-r1 | `9d03d22..c45c71f` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-delta.md](./round-1-delta.md) | fb593a0bd556 | 🔴 阻断（Blockers=2：BD-1 同提交豁免可蒙混 / BD-2 索引与工作树不一致）→ 已修 `e80f8c2`、`90eb094` | direct（23,368 B；主智能体独立复算 sha256 一致） |
| delta-r2 | `c45c71f..08ebce5` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-delta-confirm.md](./round-1-delta-confirm.md) | 5f02bb49f8ea | 🔴 阻断（Blockers=1：BD-1 在 --staged 口径未闭合）→ 已修 `792f68e` | direct（7,432 B；主智能体独立复算 sha256 一致） |
| bd1r-r1 | `792f68e`（+ 工作树） | DSH 原生 subagent（隔离子智能体，续轮复用） | [round-1-bd1r-confirm.md](./round-1-bd1r-confirm.md) | 44b3384d4609 | 🔴 阻断（Blockers=1：BD-1-R2 `drifted` 子句缺失，真实 hook 探针可落库）→ 修复后进入下一轮 | direct（6,738 B；主智能体独立复算 sha256 一致） |
| bd1r-r2 | 工作树（未提交） | 同上（续轮） | [round-2-bd1r-reconfirm.md](./round-2-bd1r-reconfirm.md) | 33c7511378d9 | ✅ 准予（Blockers=0：G=rc=1/drifted、E2=rc=1、E3=rc=0，真实 hook 拦截，298 passed） | direct（5,161 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 批量门禁定向红队（B-01~B-16）
- [round-1-delta.md](./round-1-delta.md) — B 修复 Delta 复核（Blockers=2：BD-1/BD-2）
- [round-1-delta-confirm.md](./round-1-delta-confirm.md) — BD 修复最终确认（Blockers=1：BD-1-R）
- [round-1-bd1r-confirm.md](./round-1-bd1r-confirm.md) — BD-1-R 独立确认第 1 轮（Blockers=1：BD-1-R2 `drifted` 子句缺失）
- [round-2-bd1r-reconfirm.md](./round-2-bd1r-reconfirm.md) — BD-1-R 修复后独立确认第 2 轮（Blockers=0：准予）

## 待办与后续轮次
- [x] R1 派发与归档
- [x] B-01 / B-02 与 B-03~B-14 收口（`a38cc85`）
- [x] BD-1 / BD-2 与 B-06 / B-12 / BD-4 收口（`e80f8c2`、`90eb094`）
- [x] Delta 复核完成
- [x] BD-1-R 收口（`792f68e`）
- [x] BD-1-R 独立确认第 1 轮：**FAIL**（BD-1-R2）
- [x] BD-1-R2 修复（`check-doc-drift.py`：`drifted` 守卫 + `core.quotePath`）
- [x] BD-1-R 独立确认第 2 轮：**PASS（Blockers=0）**

## 已知边界（诚实登记）

`792f68e` 对 BD-1-R 的修复当时未经独立确认。2026-11-23 补派两轮隔离子智能体确认，结论已闭环：

- **第 1 轮**（`round-1-bd1r-confirm.md`）：**FAIL（Blockers=1，BD-1-R2）** —— `--staged` 分支只保护 `missing_anchor`、漏 `drifted`；多锚点部分漂移可被「暂存另一锚点 + 刷新复核于」洗白，真实 pre-commit hook 探针可落库。另发现非 ASCII 路径在 `--staged` 下失明/误判（P2）。
- **修复**：`check-doc-drift.py` 判据改为 `status not in ("missing_anchor", "drifted")`；`staged_paths()` 关闭 `core.quotePath`；新增 3 条回归（空行 / 多锚点 / 中文路径）。
- **第 2 轮**（`round-2-bd1r-reconfirm.md`）：**PASS（Blockers=0）** —— 夹具 C/C2/F/G/L/L2/E1~E10 全数符合预期；真实 hook 对攻击探针 rc=1 且 HEAD 不动，合法路径 rc=0 零回归；`pytest` 298 passed、`check-all` 6/6。

剩余 P2/P3（新增文档复核判据、纯日期复核 BD-9、Unicode 正例缺回归等）已登记 `BK-0055`，不阻断交付。

## 已知边界：与 check-review-report.py 的关系

本归档的 R1 报告按 `dual-round-review` 的 **Light 模式**规程产出（R1 红队正文 + 轻量裁决表），
而 `check-review-report.py` 校验的是 **Full 模式**的 R1 模板区块。该脚本对本归档返回 rc=1 属预期，
不代表凭据缺失；报告全文已逐字落盘且 sha256 经独立复算一致。
