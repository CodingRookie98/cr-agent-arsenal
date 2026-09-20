# taste-driven-designer 技能沉淀 实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-SKILL-TASTE-DRIVEN-DESIGNER-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-20

> **目标元数据**
> - **所属项目**: CR Agent Arsenal
> - **执行通道**: Heavy Track (重型主航道；P4 按用户裁定执行定向单轮红队审查 Light 模式)
> - **目标简述**: 基于外部前沿文献《How to Turn Your AI into a World-Class Designer》（Anshu Chimala 双钻模型），新建 `taste-driven-designer` 技能，将「外部随机种子 + 独立 Critic 闭环 + 多模态增强（能力门控）+ 残酷减法」沉淀为可执行的三阶段设计流程技能。
> - **创建日期**: 2026-09-20
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-09-20（需求对齐轮，Q1 命名 taste-driven-designer，Q2/Q3/Q4 按推荐）
> - **批准基线**: 计划的 4 项关键决策（命名/范围/执行依赖/交付规格）经用户逐项确认；基线变更需重新确认
> - **状态**: 已完成（P4 取得 Zero Blockers）
> - **隔离分支**: `feature/taste-driven-designer`
> - **技术调研备忘录**: [豁免: 方法论直接来源于已归档文献 docs/reference/articles/how-to-turn-your-ai-into-a-world-class-designer.md，无第三方技术选型]
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。进度、复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: 已完成（P4 取得 Zero Blockers，全部阶段闭合）
- **当前活跃子任务**: 无（P3~P5 全部闭合）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: L0 exit 0；L1 pytest 13 passed；L-Doc 断链 0、健康度 PASS。P4 Light 红队终审 Zero Blockers（🔴 0 / 🟡 2 / ⚪ 3，全部闭环）
- **最新有效提交**: `f00e44a`（P4 复验基线；终审后边界用例与结项登记待最终提交）
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收口径 (Acceptance Criteria — 由需求方定义)
- **验收人**: 王辉
- **验收场景**:
  1. 新技能 `skills/taste-driven-designer/` 存在且结构完整（SKILL.md + references + templates + scripts + tests）；
  2. 用户要求「做一版不像 AI 生成的落地页 / 给出艺术方向 / 打磨现有界面」时，技能描述足以触发；
  3. `scripts/generate-seed.sh` 可运行，pytest 全绿；种子确定性模式可复现团队同一方向；
  4. 三阶段方法论文档（Discover / Define / Deliver）覆盖文章全部 8 技法的可执行化；
  5. 仓库全套注册完成（架构设计书 + docs/index.md + docs/llms.txt + README 目录表 + .agents 软链）。
- **明确不验收项**: 不实现截图捕获/图像/视频生成的宿主绑定实现（仅能力门控协议）；不涉及任何运行时 UI 产品代码。
- **口径冲突裁决人**: 王辉

### 1.1 核心交付物清单
- [ ] 技能主体: `skills/taste-driven-designer/SKILL.md`
- [ ] 参考资料: `skills/taste-driven-designer/references/{discover-phase,critic-loop-protocol,ai-tells-audit,multimodal-enrichment}.md`
- [ ] 提示词模板: `skills/taste-driven-designer/templates/{design-brief-template,critic-prompt-template,seed-string-procedure}.md`
- [ ] 可执行脚本: `skills/taste-driven-designer/scripts/generate-seed.sh`
- [ ] 自动化测试: `skills/taste-driven-designer/tests/test_generate_seed.py`
- [ ] 架构设计书: `docs/explanation/architecture/taste-driven-designer-design.md`
- [ ] 注册与治理: `docs/index.md`（V1.8.0）、`docs/llms.txt`、`README.md` 目录表、`.agents/skills/` 软链（install.py）

### 1.2 依赖选型与开源调研结论 (Research & Feasibility Spike)
- **P0.5 备忘录**: 豁免。方法论唯一来源为已归档文献（SSoT 种子技巧引用 Sakana AI 公开论文）；无第三方库引入。
- **复用裁决**: 复用仓库既有模式 —— 技能结构对标 goal-loop/dual-round-review；Critic 派发的宿主无关原则复用 dual-round-review 派发模型的既定约定；文档治理复用 doc-governance 门禁脚本。
- **API 权威契约**: `/dev/urandom` + `base64` + `tr` 为 POSIX/GNU 基础工具；确定性模式采用 Park-Miller LCG（a=48271, m=2^31−1，乘积 < 2^53，awk 浮点精确）。

### 1.3 严禁事项与反模式 (Strict Exclusions)
- 严禁抄袭或以「禁用一切 xxx」清单取代方法论（文章明确：首轮提示词禁止过度禁令，AI Tells 审计必须在打磨阶段执行）；
- 严禁把 Critic 达标线（9/10）写进 Critic 提示词内部（保持评分的客观性）；
- 严禁新增任何第三方依赖与包管理变更；
- 严禁修改仓库既有技能本体与锁定技能（mattpocock/anthropics 系列）；
- 严禁让 critter 看到实现代码/历史迭代（上下文隔离是 Critic 闭环的成立前提）；
- 严禁执行破坏性 Git 命令。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: MEDIUM（新增技能包与文档注册，含一个确定性 shell 脚本）
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `git diff --check`（空白/冲突残留）+ bash 语法检查 `bash -n`
  - [x] **L1 单元测试**: `scripts/generate-seed.sh` 默认长度/字符集、长度与条数参数、边界校验、确定性复现、不同种子互异、真随机多样性
  - [x] **L-Doc 文档/元数据检查**: `check-doc-links.py`（断链 + 锚点）、`audit-doc-health.py`（健康度 PASS）
  - [ ] **L2 模块集成测试**: 豁免（无跨模块运行时接口）
  - [ ] **L3 端到端测试**: 豁免（不涉及用户交互链路的运行时产品）
- **豁免依据**: testing-decision-matrix —— 纯文档 + 单脚本独立单元；脚本无外部依赖，L1 已覆盖全部确定性行为。
- **精确验证命令清单**:
  ```bash
  # L0 静态门禁
  git diff --check
  bash -n skills/taste-driven-designer/scripts/generate-seed.sh

  # L1 单元测试
  python3 -m pytest skills/taste-driven-designer/tests/ -v

  # L-Doc 文档门禁
  python3 skills/doc-governance/scripts/check-doc-links.py --root docs
  python3 skills/doc-governance/scripts/audit-doc-health.py --root docs
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P1: 计划制定
- [x] **Task P1.1**: 目标范围、验收口径与 4 项关键决策经用户确认（命名 taste-driven-designer / UI 界面主战场 / 能力门控分层 / 全规格交付）

### P3: 核心功能原子实现 (TDD 循环)
- [x] **Task P3.1**: 种子脚本 TDD —— 先写 `tests/test_generate_seed.py`（红）→ 实现 `scripts/generate-seed.sh`（绿）
  - **涉及文件**: `skills/taste-driven-designer/tests/test_generate_seed.py`, `skills/taste-driven-designer/scripts/generate-seed.sh`
  - **TDD 步骤**: 🔴 失败单测 ➔ 🟢 最简实现 ➔ ✅ 单测通过 ➔ 💾 原子提交
  - **验收命令**: `python3 -m pytest skills/taste-driven-designer/tests/ -v`（Exit Code 0）
- [x] **Task P3.2**: 技能主文档 `SKILL.md`（frontmatter 触发描述 + 铁律 + D1/D2/D3 阶段路由 + 快速清单 + 降级规则 + 参考导航）
- [x] **Task P3.3**: 参考资料 ×4 —— `discover-phase.md`（种子字符串规程 + 雄心 Prompt 三步入炉法）、`critic-loop-protocol.md`（闭环结构/降级路径/评分量规/收敛预算/基线对比法）、`ai-tells-audit.md`（7 大反模式表 + 减法规则 + 文案重写规则）、`multimodal-enrichment.md`（能力门控矩阵 + 图像/视频增强协议）
- [x] **Task P3.4**: 提示词模板 ×3 —— `design-brief-template.md`、`critic-prompt-template.md`（固定 Critic 提示词，每轮原样复用）、`seed-string-procedure.md`（种子施工步骤）
- [x] **Task P3.5**: 架构设计书 `docs/explanation/architecture/taste-driven-designer-design.md`（文档控制信息 + 理论支柱 + 三阶段拓扑 + 能力门控矩阵 + 角色模型 + 质量指标 + 与既有技能协同）

### P3.5: 集成验证与端到端贯通
- [x] **Task P3.5.1**: 文档注册 —— `docs/index.md` V1.8.0（技能表/架构表/计划表三处联动 + 修订历史）、`docs/llms.txt`（Explanation/Project Governance 两节）、`README.md` 技能目录表
- [x] **Task P3.5.2**: `python3 contexts/install.py` 创建 `.agents/skills/taste-driven-designer` 相对软链；全量验证命令执行（L0 + L1 + L-Doc 三条命令全部 Exit Code 0）

### P4: 对抗终审与再循环闭环硬门禁
- [x] **Task P4.1**: 按用户裁定执行**定向单轮红队审查（Light 模式）**—— 独立子智能体以 `9353ac0..f00e44a` 为基线审查，取得终审裁决：**Zero Blockers ✅**（🔴 0 / 🟡 2 / ⚪ 3），8 技法方法论保真、触发质量、仓库约定、脚本断言、五处注册、内部一致性、安全红线 7 维度全部通过
- [x] **Task P4.2**: 阻断项为零；审稿建议项全部闭环 —— ① 边界用例追加（-l 8 最小 / -l 1024 -c 64 最大组合 / -s "" 回退随机，pytest 10→13）；② discover-phase 排版笔误修复；③ ⚪#6 LCG 低位提取为理论弱随机点，经评估**登记为接受项**（设计灵感用途无实际影响，且改动将破坏已被单测固化的确定性契约）
- [x] **Task P4.3**: 阻断项清零终审放行 → 本计划登记 Zero Blockers 结项（见第 6 节）

### P5: 文档全向归档与联动升级
- [x] **Task P5.1**: 对照 `documentation-sync-matrix.md` 复核（index/llms/README/设计书/计划五处状态一致；红队维度 5 已实测核对）
- [x] **Task P5.2**: 本计划标记为「已完成」，登记执行总结与提交 SHA（见第 6 节）

---

## 4. 研究发现与环境状态记录 (Context Log)

- **[2026-09-20 10:40] 探查记录 1**: 仓库技能惯例确认 —— SKILL.md 采用 YAML frontmatter（name/description）+ 中文路由层正文；references/templates/scripts/tests 四件套；`skills-lock.json` 与 `.agents/` 为 gitignored 本地生成物（npx skills 维护），无需手工注册；`.agents/skills/` 软链由 `contexts/install.py` 自动创建（相对软连锁死单一真相源）。
- **[2026-09-20 10:40] 探查记录 2**: 治理门禁确认 —— `check-doc-links.py --root docs`（断链+锚点）、`audit-doc-health.py --root docs`（健康度）、`generate-llms-txt.py`（llms.txt 生成器，本次手工增量更新保持既有条目格式）；llms.txt 无技能 SKILL.md 直链惯例，只收设计书与计划条目。
- **[2026-09-20 10:45] 探查记录 3**: seed 脚本确定性模式采用 Park-Miller LCG（a=48271, m=2^31−1），乘积约 1.0e14 < 2^53，awk 双精度精确无溢出；种子字符串经 charset 索引哈希后入 LCG，ASCII 种子与 Python 复刻实现完全一致（单测联动断言）。
- **[2026-09-20 11:00] 探查记录 4**: 集成验证暴露 2 个问题并已闭合 —— ① 设计书引用文章的相对路径一级不足（`../reference` 404，需 `../../reference`）；② SKILL.md description 647 字符超出 writing-skills 建议 500 上限，分两轮精简至 490（frontmatter 总计 531 < 1024 合规）。index.md 修订历史因新增 V1.8.0 超 5 条上限，经 trim-revision.py --fix 自愈裁剪至 5 条。全部门禁复验 PASS（断链 0 / 健康度 PASS / pytest 10 passed / bash -n / diff --check）。脚本跨目录调用、-s 与 -c 组合、随机多样性、非法参数退出码 2 均抽检通过。

---

## 6. 结项登记 (Closure Record)

- **终审凭据**: P4 Light 红队终审（子智能体 928177e4）—— **Zero Blockers ✅**（🔴 0 / 🟡 2 / ⚪ 3），基线 `9353ac0..f00e44a`
- **审稿闭环**: 🟡 #2 checkpoint 更新（本节）、🟡 #3 工作区漂移随最终提交闭合、⚪ #4 边界用例已固化（pytest 10→13）、⚪ #5 笔误已修、⚪ #6 LCG 低位提取**登记为接受项**（设计灵感用途无实际影响；改动将破坏已被单测固化的确定性契约）
- **验收复核**: 五种验收场景全部满足（技能结构完整 / 触发描述合规 / 脚本可运行 pytest 全绿 / 8 技法可寻址 / 全套注册完成）
- **交付清单**: 技能包 `skills/taste-driven-designer/`（SKILL.md + references×4 + templates×3 + scripts + tests）、设计书 `docs/explanation/architecture/taste-driven-designer-design.md`、注册（index V1.8.0 / llms.txt / README）、软链 `.agents/skills/taste-driven-designer`
- **提交链**: `c258811`（P3）→ `ca47366`（P3.5）→ `f00e44a`（desc 合规）→ 最终提交（边界用例 + 结项登记）

---

## 5. 修订历史 (Revision History)
- **[2026-09-20]**: 计划创建（V1.0.0）。
- **[2026-09-20]**: 结项（P4 取得 Zero Blockers，追加第 6 节结项登记）。
