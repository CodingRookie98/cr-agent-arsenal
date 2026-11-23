# Wave 1 架构清场计划：退役 `agy-delegation-workflow` 与去壳提纯 `clarification-protocol`

> **文档控制信息**
> - **文档标识**: PLAN-WAVE1-CLEANUP-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **执行通道**: **Heavy Track（公共技能退役与架构级契约简化）** —— 走完整双轮独立对抗审查（R1 红队 → R2 元架构师审判，Zero Blockers 放行）
> - **分支**: `refactor/wave1-retire-agy-and-slim-clarification`（基于 `master` `c19152a`）
> - **架构决策与依据**: [ADR-0004](../../explanation/decisions/0004-retire-agy-delegation-workflow.md) · [全仓组合总纲](../../explanation/analysis/2026-11-23-arsenal-skills-portfolio-overview.md) · [clarification-protocol 评估报告](../../explanation/analysis/2026-11-23-clarification-protocol-architecture-evaluation.md)

---

### Active Checkpoint

- **当前阶段**: `DONE`（已完成并终审放行）
- **状态**: 已完成
- **已完成**:
  - 需求与优先级裁决、分支切出、`ADR-0004` 定稿；
  - 并行委派 W1-A（按 `ADR-0004` 抽离三项资产并退役 `agy-delegation-workflow`）、W1-B（提纯 `clarification-protocol` V2.0.0 至 67 行 / 362 字符微技能并清理 6 个冗余外壳）与 W1-C（全仓注册面、入口摘要、`docs/index.md`、`docs/project/changelog.md` 与分层机器地图同步），基线提交 `1928f1e`；
  - 完整四轮独立双轮对抗审查（R1 `5a232df30ec7` → R2 `11e41ff7a806` 坐实 1 项 P1 阻断项 `R1-1` → W1-Delta 修复提交 `244c6b3` → Delta-R1 `1e8affcac24c` 0 缺陷 → Delta-R2 `a12417f6e089` **准予交付 Zero Blockers**），归档见 [审查归档 README](../reviews/2026-11-23-wave1-retire-agy-and-slim-clarification/README.md)；
  - 全量验证：`python3 -m pytest skills/ -q`（`589 passed`，Exit 0）、`check-all.py --full`（7/7 PASS，Exit 0）、`check-golden-tasks.py`（20/20 PASS，Exit 0）与 `check-review-report.py --require-verdict=PASS`（Exit 0）。
- **待办**: 无（准备 Fast-Forward 合入 `master` 并推送）

---

## 1. 任务包拆分（严格零文件交集）

### W1-A：`agy-delegation-workflow` 抽资产 + 退役（ADR-0004）
1. **吸收真资产**：
   - `skills/goal-loop/references/host-adapters.md`：并入「Silent Landing（假失败 / 延迟落盘）判别 SOP」与「Direct-Write 四条止损准则」；将外部无头 CLI 描述改为后端无关（不再依赖已退役的 `agy-delegation-workflow`）；
   - `skills/goal-loop/references/stage-progression-protocol.md`：更新 P3 后端联动说明，移除对 `agy-delegation-workflow` 的引用；
   - `skills/dual-round-review/references/failure-modes-catalog.md`：在模式 2 与模式 4 精简补充「编造未定义组件/库 API 属性与硬编码绕过设计规范」「隐蔽放宽共享类型破坏全量构建」。
2. **物理退役与注册面同步**：
   - 使用 `git rm` 移除 `skills/agy-delegation-workflow/` 全部 8 个源文件并 `unlink .agents/skills/agy-delegation-workflow`；
   - 同步更新 `skills/_shared/tests/test_cross_skill_links.py`、`skills/_shared/cross-skill-link-policy.json`、`tools/skills-manager/collections/cr-agent-arsenal.json`、`README.md`、`docs/how-to/install-skills.md`、`docs/tutorials/quick-start.md`、`skills/taste-driven-designer/tests/test_gate_contract.py`、`skills/frontend-qa-gate/tests/test_qa_gate_contract.py`；
   - `docs/explanation/architecture/agy-delegation-workflow-design.md` 流转为 `Superseded`（指向 `ADR-0004`）；更新 `goal-loop-design.md` 与 `2026-11-23-agy-delegation-workflow-architecture-evaluation.md` 移除指向已删文件的相对死链（改反引号路径文本）。

### W1-B：`clarification-protocol` 去壳提纯（48 KB → ~7 KB 精品微技能）
1. **重构 `skills/clarification-protocol/SKILL.md`**：
   - 精简至 65–85 行高信噪比微技能，`description` 压至 **≤ 400 字符**；
   - 保留 4 大核心认知精华：术语先行（全局前置、仅限易歧义词）、依赖×影响排序 + 低影响转默认假设、极简 **4 列单表决策台账**（`编号 | 类型 | 条目 | 依据`，对齐本仓 RFC-0005~0008 实战形态 + 禁重开已排除边界）、目标/边界/矛盾三问内联自核；
   - 吸收 2026 标杆精华：① **先读代码自查事实，只问人类决策（Lookup Before Asking）**；② **提问软预算锚点（单次核心澄清默认 ≤ 5 关键题，超限先收口主干并将次要分叉记为默认假设或升级裁决）**——彻底修复原 L72「提问层：本节」空指针；
   - 剥离越界杂项（原 §5 错误/审查层熔断与 §6 显式化思考）。
2. **清理损坏脚本与冲突外壳**：
   - 使用 `git rm` 删除 `scripts/check-decision-ledger.py`、`.sh`、`references/decision-ledger.md`、`references/convergence-checklist.md`、`templates/decision-ledger-template.md`、`templates/requirement-confirmation-template.md`；
   - 将 `tests/test_clarification_protocol_contract.py` 从 428 行重构为 ~55–75 行轻巧高信噪比表面哨兵（满足 C-01，校验 frontmatter、description ≤ 500、无跨技能相对外链、不含已退役脚本/模板/空指针、围栏成对闭合）。
3. **文档同步与断链净化**：
   - 更新 `docs/explanation/architecture/clarification-protocol-design.md` 至 `V2.0.0`（完整记录去壳提纯演进与 4 列单表统一，去除指向已删 6 文件的相对死链）；
   - 更新 `docs/explanation/analysis/2026-11-23-clarification-protocol-architecture-evaluation.md` 将指向已删 5 文件的相对链接转为反引号路径文本。

---

## 2. 测试策略与级别裁定

- **改动风险定级**: HIGH（公共技能退役、跨技能注册面 7→6 收敛、技能契约大幅精简）
- **强制执行级别**: L1 全仓技能与共享哨兵测试（`python3 -m pytest skills/ -q`）+ L-Doc 全套治理门禁（`python3 skills/doc-governance/scripts/check-all.py --full`）
- **终审门禁**: 独立双轮对抗审查（R1 红队穿透 → R2 元架构师审判，Zero Blockers 准予交付）
