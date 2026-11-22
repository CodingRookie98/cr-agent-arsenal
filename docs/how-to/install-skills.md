# 把本仓库技能安装到宿主 Agent (How-To)

> **文档控制信息**
> - **文档标识**: HOW-INSTALL-SKILLS-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：两种分发形态的选型与命令、验证与卸载 |

---

**适用场景**：让 Claude Code / Codex / Cursor / Gemini / DSH 等宿主识别并使用本仓库的技能。

## 决策：选哪种形态

| 你的情况 | 用哪种 | 命令 |
| :--- | :--- | :--- |
| 在本仓库里开发/修改技能 | **本地软连接**（改源码即时生效） | `python3 contexts/install.py` |
| 在**别的项目**里用这些技能 | **npx / skills-manager 安装**（独立副本） | 见下文 |

> ⚠️ 两种形态**不要混用**。软连接指向本仓库工作区，一旦移动或删除仓库，宿主里的技能会变成死链。

## 方式 A：本地软连接（仓库内开发）

```bash
python3 contexts/install.py
```

它会做两件事：

1. 把 `contexts/AGENTS.md` 链接到各宿主的全局指令位置；
2. 把 `skills/<name>` 以**相对软连接**暴露到 `.agents/skills/<name>`。

验证：

```bash
ls -l .agents/skills/ | head -5   # 期望是 -> ../../skills/xxx 的软连接
```

分发目标：

| 宿主 | 落点 |
| :--- | :--- |
| OpenCode | `~/.config/opencode/AGENTS.md` |
| Gemini / Antigravity | `~/.gemini/GEMINI.md` |
| Codex | `~/.codex/AGENTS.md` |
| Hermes | `~/.hermes/SOUL.md` |
| DSH | `~/.dsh/AGENTS.md` |

## 方式 B：装到外部项目

### B1. 单个技能（npx）

```bash
npx --yes skills@latest add -y \
  https://github.com/CodingRookie98/cr-agent-arsenal \
  --skill goal-loop --agent <agent> --full-depth
```

`--agent` 取值取决于宿主：`claude-code` / `codex` / `cursor` / `gemini` 等。

### B2. 批量装全部技能（skills-manager）

```bash
python3 tools/skills-manager/skills_manager.py install -f cr-agent-arsenal -a <agent> -y
```

> **必须带 `-f cr-agent-arsenal`**：不带 `-f` 时默认预设是 `common`（外部技能集），**不是**本仓库技能。

预设清单见 [`tools/skills-manager/collections/cr-agent-arsenal.json`](../../tools/skills-manager/collections/cr-agent-arsenal.json)。

## 验证安装

1. 让宿主列出技能（各宿主命令不同，通常为 `/skills` 或查看 `.agents/skills/`）。
2. 期望看到 8 个技能：`agy-delegation-workflow`、`clarification-protocol`、`doc-governance`、`dual-round-review`、`frontend-qa-gate`、`goal-loop`、`spec-evolution`、`taste-driven-designer`。
3. **数量少一个**通常意味着该技能的 `SKILL.md` frontmatter 不是合法 YAML——最常见原因是 `description` 含 `: `（冒号+空格）却未加引号，`npx` 会**静默跳过**且仍 exit 0。

## 卸载

```bash
# 方式 A
rm -rf .agents/skills/*

# 方式 B
python3 tools/skills-manager/skills_manager.py uninstall -f cr-agent-arsenal -a <agent> -y
```

## 常见失败

| 现象 | 原因 | 处置 |
| :--- | :--- | :--- |
| 技能数少一个，命令却 exit 0 | frontmatter 非法（多为 `description` 未加引号） | 用 `python3 -c "import yaml,sys; yaml.safe_load(open('skills/X/SKILL.md').read().split('---')[1])"` 验证 |
| 软连接指向不存在的路径 | 仓库被移动/删除 | 重新执行 `python3 contexts/install.py` |
| 装完宿主看不到 | 装到了另一个 `--agent` | 确认 `--agent` 与宿主匹配 |
