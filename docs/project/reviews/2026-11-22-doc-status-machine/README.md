# 审查归档 · doc-status-machine

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-doc-status-machine
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: doc-status-machine（RFC-0007 文档状态机）
- **归档根**: docs/project/reviews/2026-11-22-doc-status-machine/
- **审查模式**: light
- **当前迭代计数**: 1/3（Light 定向红队一轮，1×P1 + 9×P2 + 3×P3 已收口）
- **终审裁决**: 未定

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| R1（Light） | `79d031c..a53a0db` | DSH 原生 subagent（同步派发，无外部句柄） | [round-1-light.md](./round-1-light.md) | c3dd9aa003dc | 🔴 阻断（Blockers=1：T-1 模板必然过不了门禁）→ 已修 `4fe9801` | direct（22,367 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 文档状态机定向红队（T-1~T-11）

## 待办与后续轮次
- [x] R1 派发与归档
- [x] T-1（P1）与 T-2~T-11 收口
- [ ] Delta 复核与最终裁决
