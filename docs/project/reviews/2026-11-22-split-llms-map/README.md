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
