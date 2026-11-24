# Wave 2B 实施计划：`dual-round-review` V3.0 瘦身与现代化升级

> **文档控制信息**
> - **文档标识**: PLAN-WAVE2B-DUAL-ROUND-REVIEW-V3-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **执行通道**: **Heavy Track（核心终审门禁技能架构级精简）** —— 独立分支 + Full Mode 双轮对抗审查（R1 → R2 → Delta-R1 零缺陷放行）
> - **分支**: `refactor/wave2b-dual-round-review-v3`（基于 `master` `a31de61`）
> - **评估与调研依据**: [dual-round-review 评估报告](../../explanation/analysis/2026-11-23-dual-round-review-architecture-evaluation.md) · [dual-round-review 同类调研](../../explanation/analysis/2026-11-23-dual-round-review-peer-research.md) · [全仓组合总纲](../../explanation/analysis/2026-11-23-arsenal-skills-portfolio-overview.md)

---

### Active Checkpoint

- **当前阶段**: `DONE`（已完成并终审放行）
- **状态**: 已完成
- **已完成**: W2B-1 与 W2B-2 完成实现并提交 pre-review 基线（`c9eed38`） → 独立 R1（`1dfd0c7f25a4`，发现 2 P1 阻断项 `R1-1`/`R1-2` 与 3 建议 `R1-3..R1-5`）与 R2（`1cad3827450c`，裁定 `拒绝交付`） → 独立 W2B-Delta 修复（`c7f5f79`，闭合 `R1-1`..`R1-4` 并拆分 `test_v3_surface_contract.py`） → 独立 Scoped Delta R1（`107aa32a14dd`）复核 **0 缺陷**免 `delta-r2` 直接收口准予交付，审查归档见 [wave2b-dual-round-review-v3](../reviews/2026-11-24-wave2b-dual-round-review-v3/README.md)
- **待办**: 无（已封档交付）

---

## 1. V3.0 核心架构裁决

采用评估报告 **方案 A 务实收敛路线（保持现有 20 个历史归档 100% 向后兼容）**：

1. **压缩过载指令体积，清偿全仓最后一条超限 `description`**：
   - `skills/dual-round-review/SKILL.md` 从 **283 行 / 36.8 KB** 瘦身至 **~105–130 行 / ≤ 12 KB**，消除 IFScale 指令静默脱落风险；
   - `description` 从 **738 字符压降至 ≤ 450 字符**，使全仓现役 **6/6 个技能**全部收敛至 ≤ 500 字符建议线内；
   - 清除本仓私有历史术语（`RFC-0001/0002`、`R1-x 回归`、`2026-10-10 216KB`）与 32 行 React/Next.js/Safari/jsdom 硬编码，改为技术栈中立表述（同时保持 `## 2. 运行时与 SSR/沙盒安全推演` 等 `check-review-report.py` 必需标题常量逐字兼容）。
2. **退役 0% 使用率的 `Artifact Review` 平行分支（~550 行死资产）**：
   - `git rm` 移除 `references/artifact-contract.md`、`round-1-artifact-red-team.md`、`verdict-rubric-artifact.md`、`templates/r1-report-artifact.md` 与 `tests/test_artifact_schema_contract.py`（同时将宝贵的 `test_existing_archives_all_pass_gate` 与第 10 项轮次容错回归测试迁移至 `tests/test_check_review_report.py`，确保全仓 20 个真实归档继续受门禁守护）；
   - 在通用 R1 规程保留 **5 行非代码规范审查指引**（契约约束/可验证证据/误用预演），彻底卸载平行 schema 维护税。
3. **注入 2026 四大高杠杆审查升级**：
   - **Untrusted Data 防 Prompt Injection**：R1/R2 提示词顶部显式声明待审代码、注释、Commit 与文档内容均为不可信数据，严禁执行其中的指令；
   - **空结果优先（Zero-Noise）**：R1 明确无 `file:line` 确凿证据时直接回报 0 缺陷，严禁硬凑 P2/P3 噪音；
   - **R2 触发与 Scoped Delta 优化**：重型/核心改动走 Full（R1 → R2）；Fast-Track / 局部低风险改动走 Light（仅 R1）；Delta 再循环中若 `delta-r1` 为 **0 缺陷**，直接闭环放行（免重复派发无增量的 `delta-r2`，门禁对无 `delta-r2` 的零缺陷 `delta-r1` 原生放行）；
   - **能力档位分层**：R1 首次深水与 R2 争议元审判优先高能力档位，Scoped Delta / Light 轻查可用中能力档位。
4. **消除 `templates/` ↔ `references/` ↔ `scripts/` 6 处内部漂移与 20 条脆弱源码锁死测试**：
   - `templates/r1-report-code.md`、`r2-report.md`、`review-archive-index.md` 与 `references/` 及脚本 100% 对齐；
   - `git rm` 移除 `tests/test_write_channel_contract.py`（212 行源码子串/变量名锁死断言），替换为真正护航的「模板↔参考↔门禁标题/表头零漂移」「frontmatter + 围栏」「防回流」「Scoped Delta 零缺陷免 R2 过 `--require-verdict=PASS`」与全仓真实归档回归测试。

---

## 2. 无文件交集并行任务包拆分

### W2B-1：规程细则、模板、案例与设计/评估文档重构
- **文件白名单**：
  - 修改：`skills/dual-round-review/SKILL.md`
  - 修改：`skills/dual-round-review/references/round-1-red-team.md`、`round-2-meta-architect.md`、`verdict-rubric.md`、`failure-modes-catalog.md`
  - 修改：`skills/dual-round-review/templates/r1-report-code.md`、`r2-report.md`、`review-archive-index.md`
  - 检查并按需净化：`skills/dual-round-review/examples/case-1-palliative-patch.md` ~ `case-4-clean-pass.md`
  - 删除（`git rm`）：`skills/dual-round-review/references/artifact-contract.md`、`round-1-artifact-red-team.md`、`verdict-rubric-artifact.md`、`templates/r1-report-artifact.md`
  - 修改：`docs/explanation/architecture/dual-round-review-design.md`（升级至 `V3.0.0`，补标准 `### 修订历史记录` 表格 ≤5 行，清除已删 Artifact 与 `test_write_channel_contract.py` 死链）
  - 修改：`docs/explanation/analysis/2026-11-23-dual-round-review-architecture-evaluation.md`（升 `V1.0.1` + `[!NOTE]` V3.0 落地注记 + 已删 6 文件相对链接改反引号文本）

### W2B-2：门禁脚本清理、行为/契约测试重构与全局入口同步
- **文件白名单**：
  - 修改：`skills/dual-round-review/scripts/check-review-report.py`、`prepare-review-context.py`（移除 Artifact 分支与过时文案，保持 `_base_key()` 对现有 20 个真实归档向后兼容，保持 `.sh` 兼容壳转发）
  - 删除（`git rm`）：`skills/dual-round-review/tests/test_artifact_schema_contract.py`、`skills/dual-round-review/tests/test_write_channel_contract.py`（安全 `unlink` 对应 `.pyc`）
  - 修改：`skills/dual-round-review/tests/test_check_review_report.py`、`test_prepare_review_context.py`（迁入 `test_existing_archives_all_pass_gate` 与第 10 项测试，清理 Artifact 用例，增加模板/参考/脚本零漂移、Scoped Delta 零缺陷 `--require-verdict=PASS`、frontmatter ≤500 字符、围栏配对与防回流测试）
  - 修改：`README.md`、`docs/index.md`（升 `V1.51.0`，修订历史 ≤5 行）、`docs/project/changelog.md`（升 `V1.6.0`，修订历史 ≤5 行）

---

## 3. 测试策略与验收门禁

- **改动风险定级**: HIGH（核心审查技能规程重构、Artifact 支线退役、门禁测试重建）
- **强制执行级别**:
  - `L1`：`python3 -m pytest skills/ -q`（Exit Code 0，覆盖全仓 20 个真实归档与表面哨兵）
  - `L-Doc`：`python3 skills/doc-governance/scripts/check-all.py --full`（7/7 PASS）+ `check-golden-tasks.py --root docs`（20/20 PASS）
  - `L-Review`：Full Mode 双轮独立对抗审查（`docs/project/reviews/2026-11-24-wave2b-dual-round-review-v3/`，Zero Blockers 准予交付并过 `check-review-report.py --require-verdict=PASS`）
