# CR Public Skills (CodingRookie Public Skills)

> 🚀 **面向现代 AI 智能体（Claude Code / Antigravity / Cursor 等）的工业级开源技能库**，严格遵循 [`agentskills.io`](https://agentskills.io) 开放规范。

---

## 📦 技能目录清单 (Skills Catalog)

| 技能名称 | 目录路径 | 核心功能与应用场景 | 适用智能体环境 |
|---|---|---|---|
| **`goal-loop`** | [`skills/goal-loop`](./skills/goal-loop/SKILL.md) | **工业级端到端长任务目标实现循环**。<br/>以计划文件为唯一可读真相源；具备上下文工程（2-Action Rule）、自适应测试分级裁定（L0~L3）、宿主无关执行后端适配（P3 开工前询问用户）、外部技能深度编排（需求澄清/方案拷问/计划制定/TDD/双轮终审）与 3-Tries 熔断自愈机制。 | Claude Code / Antigravity / DSH / 全局 Shell |
| **`dual-round-review`** | [`skills/dual-round-review`](./skills/dual-round-review/SKILL.md) | **对抗性非讨好型双轮代码终审硬门禁**。<br/>第一轮红队第一性原理极限穿透 + 第二轮资深元架构师审判校准，彻底终结浅层创可贴补丁与大模型讨好型盲目交付；支持 Full / Light / Delta 三模式、审查记录锚点与条件维度。 | 具备子智能体派发能力的智能体 / CLI |
| **`agy-delegation-workflow`** | [`skills/agy-delegation-workflow`](./skills/agy-delegation-workflow/SKILL.md) | **Antigravity CLI (agy) 后台工人自适应委派规程**。<br/>无头后台长程任务派发、环境隔离、代理清洗、黄金 7 维任务规约、WSL 守护与前后台边界管控。 | Antigravity / Linux / WSL |
| **`doc-governance`** | [`skills/doc-governance`](./skills/doc-governance/SKILL.md) | **工业级文档工程与知识库治理体系**。<br/>立足 Diátaxis 四象限、RFC 提案结晶流转模型与 Docs-as-Code 自动化门禁，彻底杜绝文档与代码漂移。 | Claude Code / Antigravity / 全局 Shell |

---

## 🛠️ 安装与使用指南 (Installation & Usage)

### 方式 1：使用标准 Skills CLI 安装 (推荐)

通过 [`agentskills.io`](https://agentskills.io) 官方推荐工具一键安装指定技能：

```bash
# 安装目标闭环技能 (goal-loop)
npx skills add <repo-url> --skill goal-loop

# 安装双轮代码审查门禁技能 (dual-round-review)
npx skills add <repo-url> --skill dual-round-review

# 安装后台委派工作流技能 (agy-delegation-workflow)
npx skills add <repo-url> --skill agy-delegation-workflow

# 安装文档治理技能 (doc-governance)
npx skills add <repo-url> --skill doc-governance
```

### 方式 2：Git 克隆并软链接至 Agent 技能目录

将技能直接链接到您的智能体配置路径（例如 `.agents/skills` 或 `~/.claude/skills`）：

```bash
git clone <repo-url> ~/workspace/projects/cr-public-skills

# 软链接至目标工程的 .agents/skills
mkdir -p .agents/skills
ln -s ~/workspace/projects/cr-public-skills/skills/goal-loop .agents/skills/goal-loop
ln -s ~/workspace/projects/cr-public-skills/skills/dual-round-review .agents/skills/dual-round-review
ln -s ~/workspace/projects/cr-public-skills/skills/agy-delegation-workflow .agents/skills/agy-delegation-workflow
ln -s ~/workspace/projects/cr-public-skills/skills/doc-governance .agents/skills/doc-governance
```

---

## 📚 架构与设计规范文档 (Documentation)

* 📖 **[知识库总索引 (Knowledge Base Index)](./docs/index.md)** & **[知识库治理规程 (Governance Specification)](./docs/GOVERNANCE.md)**
* 📐 **`doc-governance` 总体架构设计书**: [docs/explanation/architecture/doc-governance-design.md](./docs/explanation/architecture/doc-governance-design.md) (V1.2.0)
  - Diátaxis 两维四象限心智矩阵
  - RFC 提案孵化与结晶流转模型 (RFC-to-Crystallization)
  - Docs-as-Code 自动化断链与修订历史裁剪门禁
* 📐 **`goal-loop` 总体架构设计书**: [docs/explanation/architecture/goal-loop-design.md](./docs/explanation/architecture/goal-loop-design.md) (V2.0.0)
  - 计划文件唯一真相源与宿主原生 goal 原语适配
  - 宿主无关执行后端（P3 开工前询问用户）与能力矩阵
  - Manus AI 上下文工程规范与 Read-Modify-Verify
  - L0~L3 自适应分级测试决策矩阵
  - 双轮对抗审查与 3-Tries 熔断恢复协议
* 🧩 **`goal-loop` 宿主执行后端适配规程**: [skills/goal-loop/references/host-adapters.md](./skills/goal-loop/references/host-adapters.md)
* 🧪 **`goal-loop` 状态脚本单测**: [test_goal_state_tracker.py](./skills/goal-loop/tests/test_goal_state_tracker.py)

---

## 📄 规范与许可 (License & Standards)

本项目所有技能均严格遵循 `agentskills.io` 标准：
* 独立的 `SKILL.md` 格式契约
* 确定性的前置依赖与脚本工具集成
* 结构化 References 参考库与 Templates 模板
