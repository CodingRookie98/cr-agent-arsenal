# CR Agent Arsenal (CodingRookie Agent Arsenal)

> 🚀 **面向现代 AI 智能体（Claude Code / Antigravity / OpenCode / Codex / Hermes / DSH 等）的工业级工程化武器库与资产沉淀中枢**。

本项目全面收纳、标准化与沉淀在智能体实际工程落地中积累的四维资产：
- 🎯 **标准技能包 (Skills)**：遵循 [`agentskills.io`](https://agentskills.io/specification) 开放规范的 6 个确定性可执行技能；
- 🧠 **上下文基线 (Contexts)**：统一的多智能体微内核规范 (`AGENTS.md`) 与跨环境一键链接分发；
- 🛠️ **编排与运维工具链 (Tools)**：技能批量包管理 CLI (`skills-manager`：`list` / `install` / `uninstall`)；
- 📚 **架构与治理文档 (Docs)**：涵盖 Diátaxis 架构设计、RFC 演进与长程长任务方法论。

---

## 🏛️ 仓库架构总览 (Repository Layout)

```text
cr-agent-arsenal/
├── skills/                     # 1.【标准技能包】(遵循 agentskills.io，支持 npx skills 直接拉取)
│   ├── goal-loop/              # 工业级长程任务目标实现循环
│   ├── dual-round-review/      # 对抗性非讨好型双轮代码终审硬门禁
│   ├── agy-delegation-workflow/# Antigravity CLI 后台工人委派规程
│   ├── doc-governance/         # 工业级文档工程与知识库治理体系
│   ├── taste-driven-designer/  # 品味驱动设计三阶段流程 (D1 发散 / D2 Critic 闭环 / D3 减法)
│   ├── frontend-qa-gate/       # 前端产物验收硬门禁 (五域断言 + 证据三态)
│   └── _shared/                # 跨技能共享策略与测试 (非技能包，无 SKILL.md)
│
├── contexts/                   # 2.【上下文工程与系统基线】
│   ├── AGENTS.md               # 统一的智能体运行规范基线与微内核路由
│   └── install.py              # 一键建立系统全局符号链接 (Opencode/Gemini/Codex/Hermes/DSH)
│
├── tools/                      # 3.【智能体编排与运维工具链】
│   └── skills-manager/         # 智能体技能批量包管理器
│       ├── skills_manager.py   # 核心管理 CLI (支持 list/install/uninstall)
│       └── collections/        # 技能集分类预设 (8 个：common / frontend / architecture / cr-agent-arsenal 等)
│
├── docs/                       # 4.【方法论与架构文档】
│   ├── index.md                # 知识库全景索引
│   ├── GOVERNANCE.md           # 知识库治理规程
│   ├── llms.txt                # 智能体机器可读地图 (由 doc-governance 脚本生成)
│   ├── explanation/architecture/   # 技能架构设计书 (5 份)
│   ├── project/plans/          # 实施计划与结项记录
│   └── reference/articles/     # 外部前沿文献与理论基准
│
├── .agents/skills/             # 本地开发软链接视图 (已 gitignore，由 contexts/install.py 生成)
└── skills-lock.json            # npx skills 本地安装台账 (已 gitignore，克隆后不存在)
```

---

## 📦 1. 核心技能清单 (Skills Catalog)

| 技能名称 | 目录路径 | 核心功能与应用场景 | 适用智能体环境 |
|---|---|---|---|
| **`goal-loop`** | [`skills/goal-loop`](./skills/goal-loop/SKILL.md) | **工业级端到端长任务目标实现循环**。<br/>以计划文件为唯一可读真相源；具备上下文工程（2-Action Rule）、自适应测试分级裁定（L0~L3）、宿主无关执行后端适配、外部技能深度编排与 3-Tries 熔断自愈机制。 | Claude Code / Antigravity / DSH / 全局 Shell |
| **`dual-round-review`** | [`skills/dual-round-review`](./skills/dual-round-review/SKILL.md) | **对抗性非讨好型双轮代码终审硬门禁**。<br/>第一轮红队第一性原理极限穿透 + 第二轮资深元架构师审判校准，彻底终结浅层创可贴补丁与大模型讨好型盲目交付；支持 Full / Light / Delta 三模式。 | 具备子智能体派发能力的智能体 / CLI |
| **`agy-delegation-workflow`** | [`skills/agy-delegation-workflow`](./skills/agy-delegation-workflow/SKILL.md) | **Antigravity CLI (agy) 后台工人自适应委派规程**。<br/>无头后台长程任务派发、环境隔离、代理清洗、黄金 7 维任务规约、WSL 守护与前后台边界管控。 | Antigravity / Linux / WSL |
| **`doc-governance`** | [`skills/doc-governance`](./skills/doc-governance/SKILL.md) | **工业级文档工程与知识库治理体系**。<br/>立足 Diátaxis 四象限、RFC 提案结晶流转模型与 Docs-as-Code 自动化门禁，彻底杜绝文档与代码漂移。 | Claude Code / Antigravity / 全局 Shell |
| **`taste-driven-designer`** | [`skills/taste-driven-designer`](./skills/taste-driven-designer/SKILL.md) | **品味驱动设计三阶段流程**（源于 Anshu Chimala AI 双钻模型）。<br/>D1 种子字符串发散（外部随机性）→ D2 独立 Critic 闭环（三信号门禁：结构清单 + 盲比改进 + 人类签收，分数仅作遥测）+ 每轮内嵌产物自检→ D3 AI Tells 审计与残酷减法；图像/视频增强能力门控，宿主无关、可降级。 | 具备子智能体派发能力的智能体 / CLI |
| **`frontend-qa-gate`** | [`skills/frontend-qa-gate`](./skills/frontend-qa-gate/SKILL.md) | **前端产物验收硬门禁**（源于 kejun《前端开发转向 AI Coding 的常见问题全景》）。<br/>五域断言：响应式视口 / 交互状态矩阵 / 无障碍键盘与读屏 / 浏览器覆盖 / 性能预算；证据三态（已实现 / 已运行验证 / 未验证）、结论仅 PASS / FAIL / BLOCKED，不做分数判据；审产物不审代码（代码级判据路由 `dual-round-review`），回流缺陷按路由表分流。 | 具备浏览器驱动能力的智能体 / CLI |

> ⚠️ **新增技能须知**：`SKILL.md` 的 frontmatter 必须是**合法 YAML**。`description` 若含 `": "`（冒号+空格，如 `evidence: xxx`）必须整体加引号，否则 `npx skills` 解析失败会**静默跳过该技能**（命令仍 exit 0，`Found N skills` 少一个）。规范细节见 [agentskills.io specification](https://agentskills.io/specification)。

---

## 🧠 2. 上下文工程与基线分发 (Contexts)

仓库提供全局统一的系统指令提示词 [`contexts/AGENTS.md`](./contexts/AGENTS.md)，并通过 [`contexts/install.py`](./contexts/install.py) 一键将配置链接到系统各智能体客户端：

```bash
# 执行上下文分发（AGENTS.md 全局链接 + 本仓库技能的本地软连接）
python3 contexts/install.py
```

> **两种分发形态，不要混用**：
> - **本仓库内开发**：`install.py` 以**相对软连接**把 `skills/<name>` 暴露到 `.agents/skills/<name>`，保证单一真相源——修改源目录即时生效，绝不产生副本漂移；
> - **外部仓库使用**：不引用本仓库工作区，直接用 `npx` 从 GitHub `master` 分支安装（技能内容由 CLI 落到目标项目的 `.agents/skills/`，不依赖本仓库本地路径）：
>   ```bash
>   npx --yes skills@latest add -y \
>     https://github.com/CodingRookie98/cr-agent-arsenal \
>     --skill goal-loop --agent <agent> --full-depth
>   ```
>   批量安装本仓库全部 6 个技能，用 `-f cr-agent-arsenal` 指定预设（**不带 `-f` 时默认预设是 `common`，即外部技能集，而非本仓库技能**）：
>   ```bash
>   python3 tools/skills-manager/skills_manager.py install -f cr-agent-arsenal -a <agent> -y
>   ```
>   预设来源配置见 [`tools/skills-manager/collections/cr-agent-arsenal.json`](./tools/skills-manager/collections/cr-agent-arsenal.json)。

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
# 查看默认基础技能清单 (默认预设 common.json：12 个来源组，含 55 条具名技能配置)
python3 tools/skills-manager/skills_manager.py list

# 查看指定预设 (frontend, architecture, superpowers 等)
python3 tools/skills-manager/skills_manager.py list -f frontend

# 为指定智能体批量安装技能
python3 tools/skills-manager/skills_manager.py install -a opencode -f common

# 安装本仓库自有的 6 个技能 (cr-agent-arsenal 预设，来源为本仓库 GitHub master)
python3 tools/skills-manager/skills_manager.py install -f cr-agent-arsenal -a antigravity -y
```

> `-f` / `--file` 决定技能来源预设，缺省为 `common`；全部 8 个预设与用法见 [`tools/skills-manager/README.md`](./tools/skills-manager/README.md)。

---

## 📚 4. 架构与设计规范文档 (Documentation)

* 📖 **[知识库总索引 (Knowledge Base Index)](./docs/index.md)** & **[知识库治理规程 (Governance Specification)](./docs/GOVERNANCE.md)** & **[智能体机器地图 (llms.txt)](./docs/llms.txt)**
* 📐 **技能架构设计书 (`docs/explanation/architecture/`)**
  * `doc-governance`: [doc-governance-design.md](./docs/explanation/architecture/doc-governance-design.md)
  * `goal-loop`: [goal-loop-design.md](./docs/explanation/architecture/goal-loop-design.md)
  * `dual-round-review`: [dual-round-review-design.md](./docs/explanation/architecture/dual-round-review-design.md)
  * `taste-driven-designer`: [taste-driven-designer-design.md](./docs/explanation/architecture/taste-driven-designer-design.md)
  * `frontend-qa-gate`: [frontend-qa-gate-design.md](./docs/explanation/architecture/frontend-qa-gate-design.md)
* 🧩 **`goal-loop` 宿主执行后端适配规程**: [skills/goal-loop/references/host-adapters.md](./skills/goal-loop/references/host-adapters.md)
* 🚀 **实施计划与结项记录**: 计划索引见 [docs/index.md](./docs/index.md) §4 工程演进与管理（计划文件归档于 `docs/project/plans/`）
* 📖 **外部前沿文献与理论基准 (`docs/reference/articles/`)**
  * [ai-coding-frontend-common-problems.md](./docs/reference/articles/ai-coding-frontend-common-problems.md) — kejun：AI Coding 前端常见问题全景（`frontend-qa-gate` 需求源）
  * [how-to-turn-your-ai-into-a-world-class-designer.md](./docs/reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md) — Anshu Chimala：AI 设计双钻模型（`taste-driven-designer` 理论源）

---

## 📄 规范与许可 (Standards & License)

* **技能规范**：本仓库 6 个技能均遵循 [`agentskills.io` 规范](https://agentskills.io/specification)——`name` 与所在目录同名、`description` 为合法 YAML 且不超过规范上限（1024 字符，本仓库现行技能均 ≤ 500）、`SKILL.md` 正文均 < 500 行，可直接被 `npx skills` 拉取。
* **许可**：仓库当前**未附带 `LICENSE` 文件**，技能 frontmatter 亦未声明 `license` 字段，因此默认保留所有权利（All rights reserved）；如需以开源方式对外分发，请先补充许可证文件。
