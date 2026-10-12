# 锚点契约 (Anchor Contract)

> **来源**：[RFC-0004](../../../docs/proposals/RFC-0004-spec-evolution.md) §3.4。
> **目的**：让每条 finding 都能被人类用一条命令直接核验，且**抗行号漂移**。

## 1. 三种锚点形式

| 形式 | 语法 | 解析域 | 例 |
| :--- | :--- | :--- | :--- |
| 技能内文件 | `[SKILL:<skill-name>/<relative-path>]` | `skills/<skill-name>/` | `[SKILL:clarification-protocol/SKILL.md]` |
| 技能内文件 + 行 | `[SKILL:<skill-name>/<path>:<line>]` | 同上 | `[SKILL:doc-governance/tests/test_doc_governance_scripts.py:1]` |
| 仓库内其它文件 | `[REPO:<repo-relative-path>[:<line>]]` | 仓库根 | `[REPO:tools/skills-manager/collections/cr-agent-arsenal.json]` |
| 根提示词条款 | `[RULE:§<N>-<title>]` | `contexts/AGENTS.md` 标题树 | `[RULE:§3-精准修改与代码卫生]` |

> **`[REPO:...]` 是本计划对 RFC-0004 §3.4 的扩展**。RFC 原列 `[SKILL:*]` 与 `[RULE:*]` 两种形式，
> 但 C-07（注册面）与 C-09（门禁）两类 finding 的核验位置落在技能目录之外，用 `[SKILL:*]` 表达会误导。
> 扩展理由与 RFC 回写动作登记于实现计划 §5 与 P4。

## 2. 存在性校验（硬门禁）

**判定器在输出任何 finding 之前，必须校验全部锚点。任一锚点解析失败，判定器以退出码 2 终止并打印失效锚点。**

| 形式 | 校验规则 |
| :--- | :--- |
| `[SKILL:<n>/<p>]` | `skills/<n>/<p>` 必须为已存在路径 |
| `[SKILL:<n>/<p>:<l>]` | 路径存在，且 `<l>` 为 `1 <= l <= 该文件行数` 的整数 |
| `[REPO:<p>]` / `[REPO:<p>:<l>]` | 同上去掉 `skills/` 前缀，以仓库根为基准 |
| `[RULE:§<N>-<title>]` | `contexts/AGENTS.md` 的 `## <N>.` 标题下，存在 `###` 标题其规范化文本以 `<title>` 开头 |

**理由**：这是「防锚点幻觉」的机械保证——模型无法伪造一个不存在的核验位置。

## 3. `[RULE:*]` 的解析规则

1. 解析域为 `contexts/AGENTS.md` 的标题树，**不记行号**，故天然抗行号漂移。
2. `§<N>` 指向 `## <N>. ...` 形式的二级标题（`N` 为阿拉伯数字）。
3. `<title>` 为该二级标题下某个 `###` 标题的文本，**规范化**后比较：
   - 去除首尾空白；
   - 连续空白折叠为单个空格；
   - 比较方式为「规范化后的 `###` 标题**以** `<title>` 开头」。
4. 例：`### 工具链与环境防御 (Read-Modify-Verify)` 可被 `[RULE:§3-工具链与环境防御]` 或
   `[RULE:§3-工具链与环境防御 (Read-Modify-Verify)]` 命中。

## 4. 采集侧契约

`collect-facts.py` 必须把标题树导出到 `facts.json`：

```json
"root_prompt": {
  "path": "contexts/AGENTS.md",
  "lines": 97,
  "bytes": 10746,
  "baseline": {"lines": 97, "bytes": 10746},
  "headings": ["# SYSTEM RULES", "## 0. ⛔ 安全红线 (Safety Red Lines)", "### Git 操作红线", "..."]
}
```

`headings` 为按文件顺序排列的 `#`~`###` 标题原文（含前缀 `#` 与空格）。
