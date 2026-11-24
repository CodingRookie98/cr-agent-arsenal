# 文档治理故障排查 (How-To)

> **文档控制信息**
> - **文档标识**: HOW-TROUBLESHOOT-DOC-GOV-2026
> - **当前版本**: V2.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V2.0.0** | 2026-11-24 | AI Agent | 王辉 | 随 Wave 2C（ADR-0005）重构排障条目：移除真值轴/机器地图/修订表与托管索引脚本等已退役项，更新为 `scripts/doc-gates/`、`--exclude` 与 `scripts/backlog/` 口径 |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：按症状索引的排障手册 |

---

**适用场景**：门禁报错看不懂、hook 拦截、参数退出码非预期，或不知道该修文档还是登记 backlog。按**症状**查，不按脚本查。

## 症状索引

| 症状 | 跳到 |
| :--- | :--- |
| hook 不生效 | [pre-commit hook 不生效](#pre-commit-hook-不生效) |
| hook 拒绝提交但门禁是绿的 | [hook 拒绝提交但门禁是绿的](#hook-拒绝提交但门禁是绿的) |
| 断链指向的目录明明存在 | [断链指向目录但目录存在](#断链指向目录但目录存在) |
| `check-doc-links.py` 返回 exit 2 | [`--exclude` 或 `--dir` 返回 exit 2](#--exclude-或---dir-返回-exit-2) |
| 体量门禁把文档判红 | [体量门禁把文档判红](#体量门禁把文档判红) |
| 可回答性 GAP 一堆 | [可回答性 GAP 一堆](#可回答性-gap-一堆) |
| 文档状态判我非法 | [文档状态判非法](#文档状态判非法) |
| `docs/AGENTS.md` 被拦截 | [`docs/AGENTS.md` 路由守卫失败](#docsagentsmd-路由守卫失败) |
| Python 报编码错误 | [Windows 下 Python 报编码错误](#windows-下-python-报编码错误) |

## pre-commit hook 不生效

```bash
git config --get core.hooksPath    # 期望输出 .githooks
ls -l .githooks/pre-commit         # 期望有可执行位
```

若为空：`git config core.hooksPath .githooks`。若无执行位：`chmod +x .githooks/pre-commit`。

## hook 拒绝提交但门禁是绿的

hook 会先检查「工作树是否等于索引」：

```text
🚫 工作树存在未暂存改动，pre-commit 校验结果不可信：
```

原因：门禁读工作树，你提交的是索引，二者不一致时门禁结论没有意义。**处置**：`git add` 后再提交。

## 断链指向目录但目录存在

本仓库规则：**链接指向目录时，该目录必须有 `index.md` 或 `README.md`**。否则视为断链。

**处置**：按需在该目录手工创建 `index.md`（携带标准 `文档控制信息` 头，并按本目录文件清单格式登记直属文档），或改链到具体 `.md` 文件。

## `--exclude` 或 `--dir` 返回 exit 2

`check-doc-links.py` 对作用域参数实行 **fail-closed（exit 2）**：

* `--exclude` 或 `--dir` 传了绝对路径、空字符串、或包含 `..` 越出 `--root` 边界时，直接拒绝执行并返回 `2`；
* `--dir` 指向 `--root` 内不存在的子路径时同样返回 `2`。

**处置**：使用相对于 `--root` 的合法路径前缀，例如：

```bash
python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews
```

## 体量门禁把文档判红

`scripts/doc-gates/check-doc-health.py` 按 RFC-0008 执行体量硬上限：

* 单文档 `> 65,536` 字节（64 KB）阻断；
* 最长单行 `> 1,000` 字符阻断；
* 行数 `> 800` 仅警告。

**处置**：采用「总纲 + 子册」拆分大文档并互相链接，或按语义边界折行。外部文献转载请放在 `docs/reference/articles/`（享有体系豁免）。

## 可回答性 GAP 一堆

GAP 表示知识库**确实缺**这类内容，不是脚本坏了。正确动作是登记 backlog：

```bash
python3 scripts/backlog/manage-backlog.py create "知识库缺口：<主题>" --type Feature --priority P2
```

**不要**为了消 GAP 写空壳文档——那只会把缺口变成噪音。如果是 `FAIL` 项，说明结构性元数据或索引已损坏，必须立即修复。

## 文档状态判非法

```text
⛔ 文档状态违规: x.md: 文档状态取值非法（Deprecated），只允许 Active/Contested/Superseded
```

三态只有 `Active` / `Contested` / `Superseded`。另外：

* `Superseded` 必须带 `取代于`（仓库内相对 `.md` 路径、非自身、不越出仓库根、目标存在）；
* `Active`（含缺省未写该字段）不得带 `取代于`；
* `Contested` 建议带 `争议点`。

`docs/project/backlog/**` 目录的 YAML `status` 是待办生命周期字段，豁免此项检查。

## `docs/AGENTS.md` 路由守卫失败

`docs/AGENTS.md` 必须满足：**总行数 ≤ 30 行**，且包含「读取顺序」与「硬约束」两个小节。若超行，请删减冗余说明，将领域规范迁回 [GOVERNANCE.md](../GOVERNANCE.md)。

## Windows 下 Python 报编码错误

所有门禁与工具脚本入口已显式设 UTF-8，但若你在自己的脚本里调用或串联输出：

```python
import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')
```

向仓库写回 Markdown 文件时请统一使用 UTF-8 编码与 LF 换行（`encoding='utf-8', newline='\n'`）。

## 还是不行

1. 跑 `python3 scripts/doc-gates/check-all.py --full`，把完整输出留下；
2. 看 [GOVERNANCE.md](../GOVERNANCE.md) §4.1 的豁免表——部分目录（`project/reviews` / `reference/articles` / `project/backlog` / `docs/AGENTS.md`）**故意**享有特定维度的豁免；
3. 仍无解则用 `python3 scripts/backlog/manage-backlog.py create ...` 登记 backlog 并附完整输出与复现命令。
