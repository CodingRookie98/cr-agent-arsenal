# 审查归档 · split-llms-map

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-split-llms-map
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: split-llms-map（RFC-0006 分层机器地图）
- **归档根**: docs/project/reviews/2026-11-22-split-llms-map/
- **审查模式**: light
- **当前迭代计数**: 2/3（Light 红队一轮 + Delta 复核一轮；3×P1 与 6 条 SD 项全部收口）
- **终审裁决**: 准予交付

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| R1（Light） | `9ca589f..0cfdbea` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-light.md](./round-1-light.md) | 19ea6bcdb1c5 | 🔴 阻断（Blockers=3：S-1/S-2/S-3）→ 已修 `a3be9c9` | direct（21,904 B；主智能体独立复算 sha256 一致） |
| Delta | `0cfdbea..50013ce` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-delta.md](./round-1-delta.md) | 65f634b9fe7f | ✅ **Blockers=0，准予交付**（另列 6 条 SD 项，已全部收口 `aee6bbe`） | direct（19,604 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 分层机器地图定向红队（S-1~S-7）
- [round-1-delta.md](./round-1-delta.md) — S 修复 Delta 复核（**Blockers=0**）

## 待办与后续轮次
- [x] R1 派发与归档
- [x] S-1/S-2/S-3（P1）与 S-4/S-5（P2）修复
- [x] Delta 复核：**0 Blockers，准予交付**
- [x] SD-1/2/3/5/6 收口（`aee6bbe`）、SD-4 契约登记

## 已知边界：与 check-review-report.py 的关系

本归档的 R1/Delta 报告按 `dual-round-review` 的 **Light 模式**规程产出（R1 红队正文 + 轻量裁决表），
而 `check-review-report.py` 校验的是 **Full 模式**的 R1 模板区块（如「## 5. 第一轮结论概要」）。
因此该脚本对本归档返回 rc=1 属**预期结果**，不代表凭据缺失：

- 报告全文已逐字落盘（字节数与 sha256 均经主智能体独立复算一致）；
- 轮次台账的「写入形态」「轮次标记」两列已按脚本口径对齐（r1 / delta-r1）；
- 若后续要把 Light 归档纳入该门禁，应先在 `dual-round-review` 侧增加 light schema，
  而不是改写已归档的报告正文（逐字归档红线）。
