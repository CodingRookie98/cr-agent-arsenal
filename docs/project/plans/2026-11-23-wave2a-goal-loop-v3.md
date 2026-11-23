# Wave 2A 实施计划：`goal-loop` V3.0 瘦身与现代化升级

> **文档控制信息**
> - **文档标识**: PLAN-WAVE2A-GOAL-LOOP-V3-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **执行通道**: **Heavy Track（核心主干技能架构级重构）** —— 独立分支 + 全量双轮对抗审查（R1 → R2 Zero Blockers 放行）
> - **分支**: `refactor/wave2a-goal-loop-v3`（基于 `master` `1a1c112`）
> - **评估与调研依据**: [goal-loop 评估报告](../../explanation/analysis/2026-11-23-goal-loop-architecture-evaluation.md) · [goal-loop 同类调研](../../explanation/analysis/2026-11-23-goal-loop-peer-research.md) · [全仓组合总纲](../../explanation/analysis/2026-11-23-arsenal-skills-portfolio-overview.md)

---

### Active Checkpoint

- **当前阶段**: `Verify`（预审查基线全绿，进入 Full Mode 双轮独立对抗审查）
- **状态**: 进行中
- **已完成**: 并行完成 W2A-1（五主阶段规程/模板/设计书 V3.0.0 与评估注记）与 W2A-2（退役零用 tracker 与 3 份旧测试，新增 119 行 `pack-handoff.py` 交接脚本与 164 行行为+表面单测，同步跨技能与索引/变更日志），刷新分层机器地图；主智能体独立验收全仓 `pytest`（`554 passed`）、`check-all.py --full`（7/7）与 `check-golden-tasks.py`（20/20）均 Exit 0
- **待办**: Full Mode 双轮独立对抗审查（R1 红队 → R2 元架构师审判至 Zero Blockers） → 归档审查凭据与计划结项 → Fast-Forward 合入 `master` 并推送

---

## 1. V3.0 核心架构裁决

采用评估报告 **方案 A（P0 止血瘦身 + P1 现代化升级）**：

1. **五主阶段收敛（保留历史编号映射）**：将历史补丁式 9–10 编号（`P-1 / P0 / P0.5 / P1 / P2 / P3 / P3.5 / P4 / P5`）收敛为 **`Align` → `Plan` → `Execute` → `Verify` → `Close`** 五主阶段，在三轨裁剪矩阵中显式保留历史编号对照，保证 28 份存量计划与跨技能引用平滑衔接。
2. **彻底清退 0% 实战使用的死重与伪运行时**：
   - 物理移除 `scripts/goal-state-tracker.py` + `.sh` 与 `tests/test_goal_state_tracker.py`（-667 行 / 23.1 KB），坚持由智能体直接精准编辑计划头部 `Active Checkpoint`；
   - 物理移除 `templates/evaluation-report-template.md` 与 `templates/research-spike-template.md`（-125 行 / 6.4 KB），调研落盘统一对齐 Diátaxis `docs/explanation/analysis/`；
   - 拆除不可度量且与 `host-adapters.md` 冲突的 `HALF-OPEN / G1–G4 / min(25%, 剩余÷3)` 伪运行时与 168 行文案锁死测试（`test_failure_recovery_contract.py` / `test_optional_skill_contract.py`），回归清晰可执行的 **3-Tries 熔断 + 场景子上限 + 非阻塞升级（`parked` + 人类裁决）**；
   - 废除零执行的机械「每 2 次只读强写盘（2-Action Rule）」，升级为**事件驱动落盘**（阶段切换 / 关键根因收敛 / 大块探索收束 / 上下文压缩前）。
3. **修平全部内部腐化与路径违例**：
   - 重写 `references/documentation-sync-matrix.md`：彻底移除违背 `GOVERNANCE.md` 的瀑布旧路径（`docs/architecture/`、`docs/design/`、`docs/adr/`、`docs/getting_started.md`、`docs/project/evaluation/` 等），全面对齐 Diátaxis 四象限；
   - 修复 `references/stage-progression-protocol.md`：补全三轨 ASCII 图、删除 React Rules of Hooks / SSR 特定栈硬编码、修正旧调研/评估路径；
   - 替换虚构的 `create_goal / get_goal / update_goal` 原语为真实宿主能力族（会话步骤清单、隔离工作区子智能体、工作流编排）。
4. **引入 2026 四大高杠杆能力**：
   - **极薄文件指针交接脚本 `scripts/pack-handoff.py`**（≤120 行纯标准库 Python）：提供 `brief`（按任务 ID 从计划精准抽取单任务简报落盘）与 `review-pkg`（打包 `BASE..HEAD` 提交、diff stat 与变更清单，防 `HEAD~1` 丢提交），配真实行为单测 + 轻量表面哨兵 `tests/test_goal_loop_contract.py`；
   - **四项现代执行纪律**（写入 `host-adapters.md` 与 `atomic-task-template.md`）：①「先裁决不卡死（Rulings, not stalls）」+ 四类硬停边界与 `Ruling:` 记录；② 通用高/中/低能力档位模型分层（含「轮次成本优于单价」提示，严禁写死品牌模型名）；③ 同形小改动合批 + 严禁子执行器套娃自派审查；④ 垂直曳光弹切片（DAG）优先。

---

## 2. 无文件交集并行任务包拆分

### W2A-1：规程细则、模板套件与设计/评估文档重构
- **文件白名单**：
  - `skills/goal-loop/SKILL.md`
  - `skills/goal-loop/references/stage-progression-protocol.md`
  - `skills/goal-loop/references/failure-recovery-protocol.md`
  - `skills/goal-loop/references/host-adapters.md`
  - `skills/goal-loop/references/context-engineering.md`
  - `skills/goal-loop/references/documentation-sync-matrix.md`
  - `skills/goal-loop/references/optional-skill-dependencies.md`
  - `skills/goal-loop/templates/goal-plan-template.md`
  - `skills/goal-loop/templates/atomic-task-template.md`
  - `git rm`：`skills/goal-loop/templates/evaluation-report-template.md`、`skills/goal-loop/templates/research-spike-template.md`
  - `docs/explanation/architecture/goal-loop-design.md`（升级至 `V3.0.0`，补标准修订历史表，核查零个人路径）
  - `docs/explanation/analysis/2026-11-23-goal-loop-architecture-evaluation.md`（升 `V1.0.1` + `[!NOTE]` V3.0 落地注记 + 已删 7 文件相对链接改反引号文本）

### W2A-2：脚本替换、行为契约测试与跨技能/总索引同步
- **文件白名单**：
  - `git rm`：`skills/goal-loop/scripts/goal-state-tracker.py`、`skills/goal-loop/scripts/goal-state-tracker.sh`、`skills/goal-loop/tests/test_goal_state_tracker.py`、`skills/goal-loop/tests/test_failure_recovery_contract.py`、`skills/goal-loop/tests/test_optional_skill_contract.py`（并安全 `unlink` 残留 `.pyc`）
  - 新增 `skills/goal-loop/scripts/pack-handoff.py`（≤120 行纯标准库跨平台 CLI）
  - 新增 `skills/goal-loop/tests/test_goal_loop_contract.py`（`pack-handoff.py` 真实行为单测 + 轻量表面与防回流哨兵）
  - `skills/frontend-qa-gate/SKILL.md`（同步 `goal-loop Verify（原 P3.5）` 挂载点表述）
  - `contexts/AGENTS.md`（同步 `Align（原 P0）` 阶段表述，保持总行数 98 行）
  - `README.md`（同步 `goal-loop` V3.0 表格描述，去除旧 `2-Action Rule`）
  - `docs/index.md`（升 `V1.50.0`，修订历史严控 ≤5 行，更新 §2/§3 `goal-loop` 描述并登记本计划）
  - `docs/project/changelog.md`（升 `V1.5.0`，修订历史严控 ≤5 行，新增 Wave 2A 交付条目）

---

## 3. 测试策略与验收门禁

- **改动风险定级**: HIGH（核心主干技能阶段重构、脚本替换、跨技能引用更新）
- **强制执行级别**:
  - `L1`：`python3 -m pytest skills/ -q`（Exit Code 0，含 `pack-handoff.py` 真实 Git/文件行为单测 + 全仓共享哨兵 C-01/C-05/C-07）
  - `L-Doc`：`python3 skills/doc-governance/scripts/check-all.py --full`（7/7 PASS，Exit Code 0）+ `check-golden-tasks.py --root docs`（20/20 PASS，Exit Code 0）
  - `L-Review`：Full Mode 双轮独立对抗审查（R1 → R2，取得 Zero Blockers 终审裁决并过 `check-review-report.py --require-verdict=PASS`）
