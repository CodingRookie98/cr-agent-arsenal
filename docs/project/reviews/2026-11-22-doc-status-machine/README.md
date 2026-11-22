# 审查归档 · doc-status-machine

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-doc-status-machine
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: 2026-11-22

- **交付单元**: doc-status-machine（RFC-0007 文档状态机）
- **归档根**: docs/project/reviews/2026-11-22-doc-status-machine/
- **审查模式**: light
- **当前迭代计数**: 2/3（Light 红队 + Delta 复核；1×P1 与 9×P2/3×P3 及 TD-1~TD-9 全部收口）
- **终审裁决**: 准予交付

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| r1 | `79d031c..a53a0db` | DSH 原生 subagent（同步派发，无外部句柄） | round-1-light.md | c3dd9aa003dc | 🔴 阻断（Blockers=1：T-1 模板必然过不了门禁）→ 已修 `4fe9801` | direct（22,367 B；主智能体独立复算 sha256 一致） |
| delta-r1 | `a53a0db..7354819` | DSH 原生 subagent（同步派发，无外部句柄） | round-1-delta.md | 0bb650678711 | ✅ **Blockers=0，准予交付**（另列 9 条 TD 项，已收口 `26fc8fc`） | direct（20,078 B；主智能体独立复算 sha256 一致） |

## 报告清单
- [round-1-light.md](./round-1-light.md) — 文档状态机定向红队（T-1~T-11）
- [round-1-delta.md](./round-1-delta.md) — T 修复 Delta 复核（**Blockers=0**，TD-1~TD-9）

## 待办与后续轮次
- [x] R1 派发与归档
- [x] T-1（P1）与 T-2~T-11 收口
- [x] Delta 复核：**0 Blockers，准予交付**
- [x] TD-1~TD-9 收口（`26fc8fc`），含对上一轮「全部收口」口径的显式更正

## 已知边界：与 check-review-report.py 的关系

本归档的 R1/Delta 报告按 `dual-round-review` 的 **Light 模式**规程产出（R1 红队正文 + 轻量裁决表），
而 `check-review-report.py` 校验的是 **Full 模式**的 R1 模板区块（如「## 5. 第一轮结论概要」）。
因此该脚本对本归档返回 rc=1 属**预期结果**，不代表凭据缺失：

- 报告全文已逐字落盘（字节数与 sha256 均经主智能体独立复算一致）；
- 轮次台账的「写入形态」「轮次标记」两列已按脚本口径对齐（r1 / delta-r1）；
- 若后续要把 Light 归档纳入该门禁，应先在 `dual-round-review` 侧增加 light schema，
  而不是改写已归档的报告正文（逐字归档红线）。
