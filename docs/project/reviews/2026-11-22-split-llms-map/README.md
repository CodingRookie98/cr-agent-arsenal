# 审查归档 · split-llms-map

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-split-llms-map
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: split-llms-map（RFC-0006 分层机器地图）
- **归档根**: docs/project/reviews/2026-11-22-split-llms-map/
- **审查模式**: light
- **当前迭代计数**: 1/3（Light 定向红队一轮，3×P1 已收口）
- **终审裁决**: 未定

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| R1（Light） | `9ca589f..0cfdbea` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-light.md](./round-1-light.md) | 19ea6bcdb1c5 | 🔴 阻断（Blockers=3：S-1/S-2/S-3）→ 已修 `a3be9c9` | direct（21,904 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 分层机器地图定向红队（S-1~S-7）
- round-1-delta.md — S 修复 Delta 复核（进行中）

## 待办与后续轮次
- [x] R1 派发与归档
- [x] S-1/S-2/S-3（P1）与 S-4/S-5（P2）修复
- [ ] Delta 复核与最终裁决
