# cr-agent-arsenal 仓库协作规程 (Repository Agent Guidelines)

> 本文件是本仓库的**项目级 Agent 入口规程**（严控 ≤60 行，仅记录跨任务普遍适用且不可由目录树自发现的硬约束）。
> 文档导航见 [docs/AGENTS.md](./docs/AGENTS.md)；文档治理标准见 [docs/GOVERNANCE.md](./docs/GOVERNANCE.md)；提交取证口径见 [docs/reference/rules/commit-evidence.md](./docs/reference/rules/commit-evidence.md)。

## 1. 任务执行委派铁律（主从分离）

- **任务执行类必须委派给子智能体**：凡属具体执行类工作——代码实现、Bug 修复、测试编写与回归补齐、批量重构、脚手架生成、批量文档修订——**默认必须委派给独立子智能体执行**（优先宿主原生子智能体；并行改写彼此无文件冲突的任务可批内并行，同文件任务必须合并串行）。
- **主智能体坚守「认知不外包」**：主智能体亲自负责需求对齐与拆解、方案与架构设计、任务边界划定（自包含 Prompt + 精确验收命令）、执行结果的 **Zero-Trust 独立验收**（亲审 `git diff` 并独立重跑测试/门禁，绝不轻信子智能体自报）、独立对抗审查派发与终审裁决放行。
- **允许主智能体直接操作的窄边界**：仅限快速只读核查、计划/架构文档裁决性定稿、以及最终验证通过后的原子 `git add` / `git commit` / `git push`。

## 2. 仓库开发与分支纪律

- **分支隔离**：代码或技能实质修改必须在独立功能/修复分支进行，严禁直接在 `master` 编写改动；严禁破坏性 Git 命令（`reset` / `rebase` / `revert` / `restore` / `clean -fd` / `push -f` / `branch -D`）。
- **公私边界**：`skills/<name>/` 内的技能资产面向跨仓复用，禁止写入个人绝对路径、个人真名、单项目私有组件约定或硬编码过时具体模型名。
- **文档与测试同步**：改动技能脚本/契约后必须同步对应测试与架构设计书；涉及 `docs/` 增删改名或结构变动须同步更新 `docs/index.md` 与受影响的象限索引。

## 3. 核心验收门禁命令

```bash
# 全量文档治理门禁与测试（断链 / 健康体检 / 可回答性 / pytest，4 项）
python3 scripts/doc-gates/check-all.py --full

# 全仓库技能与私有工具单元测试
python3 -m pytest skills/ scripts/ -q

# 通用物理断链扫描（排除 Write-Once 审查凭据归档）
python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews
```

## 4. 提交信息与取证红线

- 严格遵守 [docs/reference/rules/commit-evidence.md](./docs/reference/rules/commit-evidence.md)：可复核的退出码直接写，具体数字必须附可复现命令，耗时等一次测量须显式标注，未取证部分必须明确标「未验证」。
- 重大技能或契约交付前必须由**与编码者隔离的独立子智能体**执行审查并取得 Zero Blockers 裁决。
