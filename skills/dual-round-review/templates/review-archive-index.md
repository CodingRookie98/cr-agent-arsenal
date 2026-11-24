# 审查归档 · <slug>

> **本文件是归档索引骨架**：由 `prepare-review-context.py --slug=<slug>` 在 `<归档根>/README.md` 生成（手工建档时按本骨架创建），由 `check-review-report.py` 机械校验。落地时替换 `<...>` 槽位。

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-<slug>
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: YYYY-MM-DD

- **交付单元**: <slug>
- **归档根**: docs/project/reviews/YYYY-MM-DD-<slug>/
- **审查模式**: full | light | delta
- **当前迭代计数**: 0/3
- **终审裁决**: 未定

> **终审裁决字段（`--require-verdict=PASS` 硬校验）**：允许取值 `准予交付`、`阻断交付`、`未定`。交付放行时（剥除可选前导 `✅` 与 `**` 加粗后）须精确为 `准予交付`，或 `准予交付（<含数字的全角括号统计串>）`（如 `✅ **准予交付**（delta-r2：Blockers = 0；🔴 0 / 🟡 1 / ⚪ 0）`）；占位符、否定式或无数字括号后缀一律不成立。

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| r1 | `<base>..<head>` | 子智能体 `R1` | `r1-<base>..<head>.md` | `<12 位十六进制>` | 🔴 n / 🟡 n / ⚪ n | direct |
| r2 | `<base>..<head>` | 子智能体 `R2` | `r2-<base>..<head>.md` | `<12 位十六进制>` | ✅ 准予交付（Blockers = 0） | direct |

> - **轮次列**：前导标记须为 `r1` / `r2` / `delta-r1` / `delta-r2` 之一（允许带人类描述如 `delta-r1 · 第2轮`）；Light 模式或 `delta-r1` 产出 0 缺陷直接收口时，无需配对 R2 行。
> - **写入形态列**：合法值仅 `direct`（子智能体直写）与 `transcribed`（主智能体转录）。发生转录降级或轮次作废重派时，须在下方留痕区（`> [!WARNING]` / `> [!NOTE]`）登记原因，严禁将附加文本拼入本列单元格。
> - **SHA256**：落盘后由主智能体独立复算 64 位全值并与子智能体回报全值比对，一致后取前 12 位入账。

## 报告清单
> 每轮归档后在此追加一行 markdown 链接，供人类与子智能体按路径直达（槽位未替换前保持反引号文本，避免断链）：
- `r1-<base>..<head>.md` — R1 红队报告全文
- `r2-<base>..<head>.md` — R2 终审裁决书全文

## 待办与后续轮次
- [ ] 待审查派发并核验指纹后登记

## 机械门禁 (Gate)

```bash
python3 skills/dual-round-review/scripts/check-review-report.py <归档目录>
python3 skills/dual-round-review/scripts/check-review-report.py <归档目录> --require-verdict=PASS   # 交付放行用法
```

退出码：`0` 通过 / `1` 结构或证据缺陷 / `2` 用法错误。10 项校验：索引三字段齐全且裁决字段唯一、台账文件安全在位非空、SHA256 前 12 位一致、R1 五区块齐备且围栏闭合、R2 三区块齐备（存在 R2 时）、稳定 ID 按基线逐轮对齐、`--require-verdict=PASS` 裁决校验、写入形态合法（`direct` / `transcribed`）、轮次列前导标记容错、归档内无未登记孤儿报告。
