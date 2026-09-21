# frontend-qa-gate 前端产物验收技能 实施方案计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-SKILL-FRONTEND-QA-GATE-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-21

> **目标元数据**
> - **所属项目**: CR Agent Arsenal
> - **执行通道**: Heavy Track (重型主航道；P4 执行 dual-round-review Full 双轮终审)
> - **目标简述**: 基于外部文献《前端开发转向 AI Coding 的常见问题全景》的风险清单，新建 `frontend-qa-gate` 技能 —— 只做真实浏览器**产物级断言**（响应式视口矩阵 / 交互状态与错误恢复 / 无障碍键盘与读屏路径 / 浏览器覆盖 / 性能回归），审产物不审代码、不输出分数、不替代人类签收；同步补强 `taste-driven-designer` Gate A（A3/A4/A6/A7）与 `goal-loop` 的 P3.5 前端验收挂载点，形成「设计 → 验收 → 终审」前端全流程。
> - **创建日期**: 2026-09-21
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-09-21（"那就按A进行实施"）
> - **批准基线**: A 方案（taste Gate A 为验收基线 SSOT + qa-gate 内联最小可执行副本；qa-gate 置于 taste D3 之后作为独立阶段）与四点落地路径（P1 需求文档 → P3 TDD → 注册同步 → P4 终审）
> - **状态**: 进行中
> - **隔离分支**: `feature/frontend-qa-gate`
> - **技术调研备忘录**: [豁免: 风险清单直接来源于已归档外部文献；技能只定义协议与门禁，不绑定浏览器工具链实现]
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。进度、复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P1 需求确认（本文档）→ 待进入 P3 TDD 循环
- **当前活跃子任务**: Task P3.1（契约测试先红）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: 基线 `python3 -m pytest skills/ -q` 71 passed（改动前）
- **最新有效提交**: `39a3a0d`
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 需求确认与术语表 (Requirement Confirmation & Glossary)

> 术语先行（依据 `~/.dsh/AGENTS.md` §4 提问收敛律）：以下术语为本计划的唯一口径，全文不得另作解释。

| 术语 | 定义（本计划唯一口径） |
|:---|:---|
| **产物验收 (Product Acceptance)** | 仅依据**真实运行环境中的产物**（浏览器渲染结果、交互行为、运行时日志、性能测量）作出、且**可复现**的断言。判据是"照做一遍能否重现同一结论"，不使用主观评分。 |
| **断言 (Assertion)** | 二值可判定（pass / fail）且附可复现操作步骤与原件证据（截图 / 日志 / 测量数值 / 命令）的陈述。无法二值判定者不得进入验收项。 |
| **状态矩阵 (State Matrix)** | 每个受检查界面单元（页面/组件/流程节点）在 {初始, 加载, 空态, 错误, 禁用, 焦点可见, 提交中, 重试, 返回恢复} 九态下的**期望表现**与**实际表现**对照表；缺失态须显式标注"未实现"而非留空。 |
| **视口矩阵 (Viewport Matrix)** | 以**内容连续适配**为判据的检查点集合（代表性视口 × 长文本 / 软键盘 / 安全区 / 横屏 / 触控），而非以"断点数量"为判据。 |
| **可访问性基线 (A11y Baseline)** | 机器扫描（语义/可访问名称）**加**人工实测（键盘完成关键任务、焦点顺序与可见性、读屏关键流程、`prefers-reduced-motion`）的合并证据集；工具分数不构成验收结论。 |
| **回流路由 (Regression Routing)** | 验收发现缺陷后按缺陷类型确定修复位置与重验路径的静态路由表（§1.3）。 |
| **证据三态 (Evidence Tri-state)** | 对每一项要求，明确区分「已实现 / 已运行验证 / 未验证」三种状态；自然语言总结不得替代产物证据。 |
| **能力门控 (Capability Gating)** | 宿主能力（浏览器驱动 / 键盘仿真 / 读屏 / 性能测量）有无决定执行路径；**能力缺失不降级为"通过"**（与 taste Critic 的降级评审规则不同，见 §1.4）。 |

### 1.1 验收口径 (Acceptance Criteria — 由需求方定义)
- **验收人 (Acceptor)**: 王辉
- **验收场景 (Acceptance Scenarios)**:
  1. 新技能 `skills/frontend-qa-gate/` 结构完整（SKILL.md + references + templates + tests），description 能在"前端验收 / 响应式是否完整 / 键盘能不能用 / 无障碍 / 错误态 / 性能是否回归"类请求上触发；
  2. 对任一前端产物执行技能时，产出《前端验收报告》含：五维断言结论、每项断言的操作步骤与产物证据、证据三态标注、未验证项与阻断原因；
  3. 技能**不输出任何分数**、**不替用户签发设计放行**、**不进行代码级审查**（静态代码问题路由到 dual-round-review）；
  4. 缺陷按 §1.3 回流路由表分流，且路由记录可回放；
  5. `taste-driven-designer` Gate A 新增响应式 / 状态矩阵 / 无障碍基线 / 证据三态四项可核验清单，并在 D2 各轮内嵌"便宜自检"；
  6. `goal-loop` 阶段路由出现 P3.5 前端验收挂载点（taste → qa-gate → dual-round-review 全流程可在计划中声明）；
  7. 仓库注册全套同步（skills-manager 集合 + docs/index.md + docs/llms.txt + README + 设计书）。
- **明确不验收项 (Non-Acceptance)**: 不实现浏览器驱动/axe/Lighthouse 的宿主绑定代码（仅协议、门控与清单）；不覆盖 D 类安全与供应链（D1/D2/D4 明确归 CI 与宿主权限层，见 §1.4）；不改动 `taste-driven-designer` 的三信号门禁与 Critic 协议本体；不修改其他技能本体（除 goal-loop 挂载点与 taste 清单补强）。
- **口径冲突裁决人**: 王辉

### 1.2 风险面 → 交付映射 (Traceability)

> 来源：kejun《前端开发转向 AI Coding 的常见问题全景》（2026-09-20 修订版，风险分层与十条防御清单）

| 文献条目 | 本计划交付物 | 归属 |
|:---|:---|:---|
| A3 响应式与移动端适配不完整 | 视口矩阵 `references/acceptance-matrix.md` §2 + taste Gate A 清单项 | qa-gate（执行）/ taste（完成定义） |
| A4 交互状态与异常反馈缺失 | 状态矩阵 §1 + 错误恢复路径 §4 | qa-gate / taste |
| A6 无障碍缺失 | 可访问性基线 §3（扫描 + 键盘 + 焦点 + 读屏 + 减少动效） | qa-gate / taste |
| A7 完成报告失真 | 证据三态 + 《前端验收报告》模板强制字段 | qa-gate / taste D3 |
| B1 目标浏览器覆盖不足 | 浏览器矩阵 §5（最低支持版本记录 + 关键流程矩阵检查） | qa-gate |
| B3 性能回归 | 性能预算对比 §6（构建体积 + 关键交互 + 代表性设备/网络） | qa-gate |
| B2 Hydration / B4 竞态 / C1–C6 | **不在本技能重复**：代码级判据归 `dual-round-review`（已有条件维度 + failure-modes 模式 11），qa-gate 仅引用模式编号 | dual-round-review |
| D1/D2/D3/D4 安全与供应链 | **明确排除**：属 CI 与宿主权限层（文献防御清单第 7 条"把约束变成可执行规则"） | 宿主 CI / 权限 |
| E1–E5 / F1–F4 流程与长期能力 | 由 `goal-loop` 与组织流程承载；本技能补充 goal-loop 的 P3.5 挂载点 | goal-loop / 组织 |

### 1.3 回流路由表 (Regression Routing — 静态契约)

| 缺陷类型 | 修复位置 | 回流目标与重验路径 |
|:---|:---|:---|
| 行为修复类（aria 名称、断点微调、焦点样式、错误态实现、加载态文案） | qa-gate 循环内修正 | 就地修正 → 重跑受影响断言 → 无需重开设计阶段 |
| 结构/密度类（真实视口下布局崩坏、信息层级需重排） | 设计侧 | 回 `taste-driven-designer` **D2**（盲比记账后续跑），D3 后重新验收 |
| 方向级判断（错误态该怎样表达、空态语气） | 创意总监 | 升级人类裁决，qa-gate 记录待决项 |
| 实现/根因类（hydration 失配、异步竞态、类型逃逸、依赖边界、性能实现缺陷） | 代码侧 | 转 `dual-round-review` R1，按其裁定修复后回到 qa-gate 重验 |
| 安全类（XSS / 密钥 / 供应链） | CI 与权限层 | 不在技能内处理：记录并在报告中标注"超出验收范围"，升级宿主流程 |

### 1.4 显式默认假设与边界登记 (Registered Assumptions)

| # | 决策/边界 | 依据 |
|:---:|:---|:---|
| 1 | 验收基线清单采用 **A 方案**：`taste-driven-designer` Gate A 为 SSOT，qa-gate 内联最小可执行副本并标注来源版本号；**不做跨技能硬链接**（跨技能相对路径在独立 `npx skills add` 分发下会断链） | 用户已确认 A 方案；独立分发优先；若清单被证明漂移两次再迁 B 方案 |
| 2 | qa-gate 置于 taste **D3 之后**，作为独立阶段，不并入 D1–D3 编号 | 用户已确认；避免扰动 taste 已收敛的三信号门禁与阶段纪律 |
| 3 | **能力缺失不降级为通过**：无浏览器能力时报告标注"未验证 + 阻断"，由人类执行或升级裁决；不使用 taste 的降级摘要评审 | 产物验收的判据必须是真实运行证据；降级评审会让 A6/A3 类问题静默漏过 |
| 4 | 首版**不新增运行时脚本与依赖**：验收报告结构校验用轻量 shell 脚本 + pytest 覆盖，浏览器操作由宿主能力（agent-browser / Playwright / webapp-testing 等）承担 | 与 taste 设计书 §8"不实现宿主绑定代码"一致；避免引入异构依赖 |
| 5 | D 类安全与供应链**不在技能范围** | 文献防御清单第 7 条：能自动判定的事项进入 CI；技能文档无法提供权限与扫描的强制力 |
| 6 | qa-gate **不替代** Gate C 人类签收，**不与 Critic 盲比重叠**（盲比是相对比较，断言是二值判定）；A1 视觉还原偏差由 qa-gate 提供测量与对位证据、由 Critic 裁决是否属品味问题 | 用户已确认"交叉部分放 dual-round-review"；裁决权归属需保持与 taste §2 Gate C 一致 |
| 7 | 失败模式知识以 `dual-round-review/references/failure-modes-catalog.md` 为 SSOT，qa-gate 只引用模式编号，不复制正文 | 避免两处知识各自漂移 |

### 1.5 核心交付物清单
- [ ] 技能主体: `skills/frontend-qa-gate/SKILL.md`
- [ ] 参考协议: `skills/frontend-qa-gate/references/{acceptance-matrix,browser-verification-protocol,regression-routing}.md`
- [ ] 报告模板: `skills/frontend-qa-gate/templates/qa-report-template.md`
- [ ] 结构校验脚本: `skills/frontend-qa-gate/scripts/check-qa-report.sh`
- [ ] 契约测试: `skills/frontend-qa-gate/tests/test_qa_gate_contract.py`
- [ ] taste 补强: `skills/taste-driven-designer/{SKILL.md,references/ai-tells-audit.md,references/critic-loop-protocol.md}`
- [ ] goal-loop 挂载: `skills/goal-loop/{SKILL.md,references/stage-progression-protocol.md}`
- [ ] 架构设计书: `docs/explanation/architecture/frontend-qa-gate-design.md`
- [ ] 注册与治理: `tools/skills-manager/collections/cr-agent-arsenal.json`、`docs/index.md`、`docs/llms.txt`、`README.md`

### 1.6 严禁事项与反模式 (Strict Exclusions)
- 严禁把任何**绝对分数/等级**（x/10、pass rate%、A-F 评级）作为验收判据 —— taste V1.1 反证（E1/E2/E3）已证伪绝对分数门禁；
- 严禁 qa-gate 替代人类签收或替代 Critic 的品味裁决；
- 严禁在技能内做代码级静态审查（与 dual-round-review 的 Diff 边界锁冲突）；
- 严禁跨技能相对路径硬链接（独立分发断链）；
- 严禁把"工具扫描分数高"写成"无障碍验收通过"；
- 严禁修改 `taste-driven-designer` 的铁律 3（三信号门禁）与 §2/§3 门禁协议本体。

---

## 2. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: MEDIUM（文档型技能 + 契约测试 + 既有技能清单补强；不触及运行时产品代码）
- **强制执行测试级别**:
  - [x] **L0 静态代码门禁**: `bash -n` 脚本语法、`git diff --check` 空白残留、技能内相对链接有效性、doc-governance 断链扫描与健康度审计
  - [x] **L1 单元测试**: 契约测试（技能边界静态断言）+ 报告结构校验脚本行为测试
  - [x] **L2 模块集成测试**: 全仓 `pytest skills/ -q` 零回归（既有 taste 24 + goal-loop 等共 71 用例）
  - [ ] **L3 端到端测试**: 豁免 —— 本次交付物为文档型技能与静态契约，无用户主干交互链路；真实浏览器验收能力由宿主提供且不属本技能实现
- **豁免依据**: 与 `taste-driven-designer` V1.0 与门禁加固 V1.1 两次交付的先例一致（同为文档型技能，以 L0/L1/L2 + 双轮终审作为质量门禁）。
- **精确验证命令清单**:
  ```bash
  # L0 静态
  bash -n skills/frontend-qa-gate/scripts/check-qa-report.sh
  git diff --check
  python3 skills/doc-governance/scripts/check-doc-links.py
  python3 skills/doc-governance/scripts/audit-doc-health.py

  # L1 契约与脚本行为
  python3 -m pytest skills/frontend-qa-gate/tests/ -q

  # L2 全仓零回归
  python3 -m pytest skills/ -q

  # 技能包契约测试红灯基线（P3.1 改前）
  python3 -m pytest skills/frontend-qa-gate/tests/test_qa_gate_contract.py -q
  ```

---

## 3. 分阶段实施与子任务清单 (Phased Implementation & Tasks)

### P3 准备: 隔离分支与环境前置检查
- [ ] **Task P3.0**: 创建 `feature/frontend-qa-gate` 分支，固化基线（`pytest skills/ -q` = 71 passed）与 Diff 范围
  - **涉及文件**: 无（仅分支与基线记录）
  - **验收方式**: 基线测试 Exit Code 0；`git status` 干净

### P3: 核心功能原子实现 (TDD 循环)
- [ ] **Task P3.1**: 契约测试先红 —— `test_qa_gate_contract.py` 钉死五条边界（无分数判据 / 不替代签收 / 不审代码 / 五大断言维度锚点在位 / 回流路由表完备）+ 报告校验脚本行为测试
  - **涉及文件**: `skills/frontend-qa-gate/tests/test_qa_gate_contract.py`
  - **验收命令**: `python3 -m pytest skills/frontend-qa-gate/tests/ -q`（预期 red）
- [ ] **Task P3.2**: qa-gate 主体转绿 —— `SKILL.md` + `references/acceptance-matrix.md`（状态矩阵 / 视口矩阵 / 可访问性基线 / 错误恢复 / 浏览器矩阵 / 性能预算）+ `references/browser-verification-protocol.md`（能力门控 / 证据与回执 / 阻断语义）+ `references/regression-routing.md` + `templates/qa-report-template.md` + `scripts/check-qa-report.sh`
  - **验收命令**: 同 P3.1（预期 green）
- [ ] **Task P3.3**: taste Gate A/D3 补强（A3/A4/A6/A7）+ D2 内嵌便宜自检 + 内联基线版本标注
  - **涉及文件**: `skills/taste-driven-designer/SKILL.md`、`references/critic-loop-protocol.md`、`references/ai-tells-audit.md`
  - **验收命令**: `python3 -m pytest skills/taste-driven-designer/tests/ -q`（既有 24 用例零回归 + 新增清单锚点断言）
- [ ] **Task P3.4**: goal-loop P3.5 挂载点 —— 阶段路由表新增"前端验收"行 + `stage-progression-protocol.md` 联动说明（taste → qa-gate → dual-round-review 顺序与交接物）
  - **涉及文件**: `skills/goal-loop/SKILL.md`、`references/stage-progression-protocol.md`
  - **验收命令**: 断链扫描 + 健康度 PASS
- [ ] **Task P3.5**: 注册同步 —— skills-manager 集合补 `taste-driven-designer` 与 `frontend-qa-gate`；`docs/index.md` 技能表与计划表；`docs/llms.txt`；`README.md` 技能目录表；新增架构设计书
  - **涉及文件**: 上列四项 + `docs/explanation/architecture/frontend-qa-gate-design.md`
  - **验收命令**: 断链 0；健康度 PASS；`npx skills` 集合可见（静态校验）

### P3.5: 集成验证与端到端贯通
- [ ] **Task P3.5.1**: 全仓零回归 + L0 门禁全过
  - **验收命令**: `python3 -m pytest skills/ -q`（预期 ≥71 + 新增）、`bash -n`、`git diff --check`、断链 0、健康度 PASS
- [ ] **Task P3.5.2**: 技能内相对链接逐条可达（含新增设计书与集合 JSON 引用）

### P4: 双轮对抗终审与再循环闭环硬门禁 (Dual-Round Review & Re-Loop Gate)
- [ ] **Task P4.1**: 以 `37..HEAD` 为基线派发 `dual-round-review` **Full** 模式（R1 红队 → R2 元架构师）；R1 提示词中显式标注本次为文档型技能交付，并按条件维度激活要求核验前端运行时契约
  - **审查输入**: 本功能提交范围 + Diff 边界锁 + `taste-driven-designer` 门禁不可回退声明
  - **验收标准**: 取得独立子智能体终审裁决明细表
- [ ] **Task P4.2**: 阻断项修复与 Delta Re-Loop 再循环闭环（迭代上限 5 次）
- [ ] **Task P4.3**: 阻断项清零终审放行与合并回 `master`

### P5: 文档归档与生命周期流转
- [ ] **Task P5.1**: 按 `doc-governance` 执行状态流转（计划状态 → 已完成）、修订历史更新、`docs/index.md` 版本号与计划表更新
- [ ] **Task P5.2**: 设计书与技能文档一致性复核（术语、边界、回流路由三处不得出现第二口径）

---

## 4. 结项登记 (Closure Record)

- **终审凭据**: [待 P4 填写]
- **阻断项闭环**: [待填写]
- **验证证据**: [待填写]
- **交付清单**: [待填写]
- **提交链**: [待填写]

---

## 5. 修订历史 (Revision History)
- **[2026-09-21]**: 计划创建（V1.0.0，Heavy Track，A 方案；含需求确认、术语表、回归路由与显式默认假设登记）。
