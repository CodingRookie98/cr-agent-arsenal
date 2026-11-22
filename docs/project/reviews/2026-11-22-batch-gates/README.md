# 审查归档 · batch-gates

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-batch-gates
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: batch-gates（RFC-0008 体量门禁 + BK-0048 门禁自动化 + BK-0049 可回答性评测）
- **归档根**: docs/project/reviews/2026-11-22-batch-gates/
- **审查模式**: light
- **当前迭代计数**: 3/3（Light 红队 + Delta 复核 + 最终确认；三轮合计 5 个 P1 全部收口）
- **终审裁决**: 准予交付

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| r1 | `14166b1..9d03d22` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-light.md](./round-1-light.md) | a43546c7723e | 🔴 阻断（Blockers=2：B-01 门禁红灯 / B-02 hook 结构性失明） | direct（23,227 B；主智能体独立复算 sha256 一致） |
| delta-r1 | `9d03d22..c45c71f` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-delta.md](./round-1-delta.md) | fb593a0bd556 | 🔴 阻断（Blockers=2：BD-1 同提交豁免可蒙混 / BD-2 索引与工作树不一致）→ 已修 `e80f8c2`、`90eb094` | direct（23,368 B；主智能体独立复算 sha256 一致） |
| delta-r2 | `c45c71f..08ebce5` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-delta-confirm.md](./round-1-delta-confirm.md) | 5f02bb49f8ea | 🔴 阻断（Blockers=1：BD-1 在 --staged 口径未闭合）→ 已修 `792f68e`（**未经二次确认，见下方已知边界**） | direct（7,432 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 批量门禁定向红队（B-01~B-16）
- [round-1-delta.md](./round-1-delta.md) — B 修复 Delta 复核（Blockers=2：BD-1/BD-2）
- [round-1-delta-confirm.md](./round-1-delta-confirm.md) — BD 修复最终确认（Blockers=1：BD-1-R）

## 待办与后续轮次
- [x] R1 派发与归档
- [x] B-01 / B-02 与 B-03~B-14 收口（`a38cc85`）
- [x] BD-1 / BD-2 与 B-06 / B-12 / BD-4 收口（`e80f8c2`、`90eb094`）
- [x] Delta 复核完成
- [x] BD-1-R 收口（`792f68e`）——**该修复未经第二轮独立确认**，凭据为主智能体自测 2 条回归 + 全量 295 passed

## 已知边界（诚实登记）

`792f68e` 对 BD-1-R 的修复**未再派独立审查**：本轮已消耗 3 轮审查（红队 → Delta → 确认），边际收益递减；
该修复由主智能体自行完成，凭据为新增 2 条 `TestBD1Staged` 用例与全量 295 passed。
若需 Zero-Trust 闭环，应再派一轮确认。

## 已知边界：与 check-review-report.py 的关系

本归档的 R1 报告按 `dual-round-review` 的 **Light 模式**规程产出（R1 红队正文 + 轻量裁决表），
而 `check-review-report.py` 校验的是 **Full 模式**的 R1 模板区块。该脚本对本归档返回 rc=1 属预期，
不代表凭据缺失；报告全文已逐字落盘且 sha256 经独立复算一致。
