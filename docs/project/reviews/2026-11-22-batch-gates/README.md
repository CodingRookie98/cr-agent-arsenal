# 审查归档 · batch-gates

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-batch-gates
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: batch-gates（RFC-0008 体量门禁 + BK-0048 门禁自动化 + BK-0049 可回答性评测）
- **归档根**: docs/project/reviews/2026-11-22-batch-gates/
- **审查模式**: light
- **当前迭代计数**: 1/3（Light 定向红队一轮，2×P1 + 14×P2/P3）
- **终审裁决**: 未定

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| r1 | `14166b1..9d03d22` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-light.md](./round-1-light.md) | a43546c7723e | 🔴 阻断（Blockers=2：B-01 门禁红灯 / B-02 hook 结构性失明） | direct（23,227 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 批量门禁定向红队（B-01~B-16）

## 待办与后续轮次
- [x] R1 派发与归档
- [ ] B-01 / B-02 与 P2/P3 收口
- [ ] Delta 复核与最终裁决

## 已知边界：与 check-review-report.py 的关系

本归档的 R1 报告按 `dual-round-review` 的 **Light 模式**规程产出（R1 红队正文 + 轻量裁决表），
而 `check-review-report.py` 校验的是 **Full 模式**的 R1 模板区块。该脚本对本归档返回 rc=1 属预期，
不代表凭据缺失；报告全文已逐字落盘且 sha256 经独立复算一致。
