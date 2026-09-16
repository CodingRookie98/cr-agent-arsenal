# CR Agent Arsenal (CodingRookie Agent Arsenal)

> 🚀 **面向现代 AI 智能体（Claude Code / Antigravity / OpenCode / Codex / Hermes 等）的工业级工程化武器库与资产沉淀中枢**。

本项目全面收纳、标准化与沉淀在智能体实际工程落地中积累的四维资产：
- 🎯 **标准技能包 (Skills)**：遵循 [`agentskills.io`](https://agentskills.io) 开放规范的确定性可执行技能；
- 🧠 **上下文基线 (Contexts)**：统一的多智能体微内核规范 (`AGENTS.md`) 与跨环境一键链接分发；
- 🛠️ **编排与运维工具链 (Tools)**：技能批量包管理 CLI (`skills-manager`) 与自动化运维工具；
- 📚 **架构与治理文档 (Docs)**：涵盖 Diátaxis 架构设计、RFC 演进与长程长任务方法论。

---

## 🏛️ 仓库架构总览 (Repository Layout)

```text
cr-agent-arsenal/
├── skills/                     # 1.【标准技能包】(遵循 agentskills.io，支持 npx skills 直接拉取)
│   ├── goal-loop/              # 工业级长程任务目标实现循环
│   ├── dual-round-review/      # 对抗性非讨好型双轮代码终审硬门禁
│   ├── agy-delegation-workflow/# Antigravity CLI 后台工人委派规程
│   └── doc-governance/         # 工业级文档工程与知识库治理体系
│
├── contexts/                   # 2.【上下文工程与系统基线】
│   ├── AGENTS.md               # 统一的智能体运行规范基线与微内核路由
│   └── install.py              # 一键建立系统全局符号链接 (Opencode/Gemini/Codex/Hermes/DSH)
│
├── tools/                      # 3.【智能体编排与运维工具链】
│   └── skills-manager/         # 智能体技能批量包管理器
│       ├── skills_manager.py   # 核心管理 CLI (支持 list/install/uninstall)
│       └── collections/        # 技能集分类预设 (common, frontend, architecture 等)
│
├── docs/                       # 4.【方法论与架构文档】
│   ├── index.md                # 知识库全景索引
│   ├── GOVERNANCE.md           # 知识库治理规程
│   └── explanation/architecture/
│
├── .agents/skills/             # 本地 Agent 开发环境软链接
└── skills-lock.json
```

---

## 📦 1. 核心技能清单 (Skills Catalog)

| 技能名称 | 目录路径 | 核心功能与应用场景 | 适用智能体环境 |
|---|---|---|---|
| **`goal-loop`** | [`skills/goal-loop`](./skills/goal-loop/SKILL.md) | **工业级端到端长任务目标实现循环**。<br/>以计划文件为唯一可读真相源；具备上下文工程（2-Action Rule）、自适应测试分级裁定（L0~L3）、宿主无关执行后端适配、外部技能深度编排与 3-Tries 熔断自愈机制。 | Claude Code / Antigravity / DSH / 全局 Shell |
| **`dual-round-review`** | [`skills/dual-round-review`](./skills/dual-round-review/SKILL.md) | **对抗性非讨好型双轮代码终审硬门禁**。<br/>第一轮红队第一性原理极限穿透 + 第二轮资深元架构师审判校准，彻底终结浅层创可贴补丁与大模型讨好型盲目交付；支持 Full / Light / Delta 三模式。 | 具备子智能体派发能力的智能体 / CLI |
| **`agy-delegation-workflow`** | [`skills/agy-delegation-workflow`](./skills/agy-delegation-workflow/SKILL.md) | **Antigravity CLI (agy) 后台工人自适应委派规程**。<br/>无头后台长程任务派发、环境隔离、代理清洗、黄金 7 维任务规约、WSL 守护与前后台边界管控。 | Antigravity / Linux / WSL |
| **`doc-governance`** | [`skills/doc-governance`](./skills/doc-governance/SKILL.md) | **工业级文档工程与知识库治理体系**。<br/>立足 Diátaxis 四象限、RFC 提案结晶流转模型与 Docs-as-Code 自动化门禁，彻底杜绝文档与代码漂移。 | Claude Code / Antigravity / 全局 Shell |

---

## 🧠 2. 上下文工程与基线分发 (Contexts)

仓库提供全局统一的系统指令提示词 [`contexts/AGENTS.md`](./contexts/AGENTS.md)，并通过 [`contexts/install.py`](./contexts/install.py) 一键将配置链接到系统各智能体客户端：

```bash
# 执行上下文分发（AGENTS.md 全局链接 + 本仓库技能的本地软连接）
python3 contexts/install.py
```

> **两种分发形态，不要混用**：
> - **本仓库内开发**：`install.py` 以**相对软连接**把 `skills/<name>` 暴露到 `.agents/skills/<name>`，保证单一真相源——修改源目录即时生效，绝不产生副本漂移；
> - **外部仓库使用**：不复制、不软链，直接用 `npx` 从 GitHub `master` 分支安装：
>   ```bash
>   npx --yes skills@latest add -y \
>     https://github.com/CodingRookie98/cr-agent-arsenal \
>     --skill goal-loop --agent <agent> --full-depth
>   ```
>   批量安装可用 `tools/skills-manager/skills_manager.py install -a <agent>`（来源配置见 `tools/skills-manager/collections/cr-agent-arsenal.json`）。

分发目标对应关系：
- `~/.config/opencode/AGENTS.md` -> OpenCode 配置
- `~/.gemini/GEMINI.md` -> Google Gemini / Antigravity 配置
- `~/.codex/AGENTS.md` -> Codex 配置
- `~/.hermes/SOUL.md` -> Hermes 配置
- `~/.dsh/AGENTS.md` -> DSH 配置

---

## 🛠️ 3. 技能管理工具链 (Skills Manager)

位于 [`tools/skills-manager/`](./tools/skills-manager/)，基于 `npx skills` 封装，提供分类技能集的批量查看与安装：

```bash
# 查看默认基础技能清单
python3 tools/skills-manager/skills_manager.py list

# 查看指定预设 (frontend, architecture, superpowers 等)
python3 tools/skills-manager/skills_manager.py list -f frontend

# 为指定智能体批量安装技能
python3 tools/skills-manager/skills_manager.py install -a opencode -f common
```

---

## 📚 4. 架构与设计规范文档 (Documentation)

* 📖 **[知识库总索引 (Knowledge Base Index)](./docs/index.md)** & **[知识库治理规程 (Governance Specification)](./docs/GOVERNANCE.md)**
* 📐 **`doc-governance` 总体架构设计书**: [docs/explanation/architecture/doc-governance-design.md](./docs/explanation/architecture/doc-governance-design.md)
* 📐 **`goal-loop` 总体架构设计书**: [docs/explanation/architecture/goal-loop-design.md](./docs/explanation/architecture/goal-loop-design.md)
* 🧩 **`goal-loop` 宿主执行后端适配规程**: [skills/goal-loop/references/host-adapters.md](./skills/goal-loop/references/host-adapters.md)

---

## 📄 规范与许可 (License & Standards)

本项目所有技能严格遵循 `agentskills.io` 协议标准与开源规范。
