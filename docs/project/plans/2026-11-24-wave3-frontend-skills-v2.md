# Wave 3 实施计划：`taste-driven-designer` 与 `frontend-qa-gate` V2.0 瘦身与真实证据化升级

> **文档控制信息**
> - **文档标识**: PLAN-WAVE3-FRONTEND-SKILLS-V2-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **执行通道**: **Heavy Track（前端双技能架构重构与真实证据门禁升级）** —— 独立分支 + Full Mode 独立双轮对抗审查（R1 → R2 → Delta-R1 零缺陷放行）
> - **状态**: 已完成
> - **分支**: `refactor/wave3-frontend-skills-v2`（基于 `master` `7768359`）
> - **评估与调研依据**: [taste-driven-designer 评估报告](../../explanation/analysis/2026-11-23-taste-driven-designer-architecture-evaluation.md) · [taste-driven-designer 同类调研](../../explanation/analysis/2026-11-23-taste-driven-designer-peer-research.md) · [frontend-qa-gate 评估报告](../../explanation/analysis/2026-11-23-frontend-qa-gate-architecture-evaluation.md) · [frontend-qa-gate 同类调研](../../explanation/analysis/2026-11-23-frontend-qa-gate-peer-research.md) · [全仓组合总纲](../../explanation/analysis/2026-11-23-arsenal-skills-portfolio-overview.md)

---

### Active Checkpoint

- **当前阶段**: `DONE`（已完成并终审放行）
- **状态**: 已完成
- **已完成**:
  - 在分支 `refactor/wave3-frontend-skills-v2`（基线 `7768359`）并行完成 W3-1（`taste-driven-designer` V2.0）、W3-2（`frontend-qa-gate` V2.0）、W3-3（跨技能引用与仓级文档同步），并经 Plan Review 补充 W3-Fix-Docs（清理 3 份存量文档断链与 `cross-skill-link-policy.json` consumers）与 W3-Fix-QA（`--evidence-root` 默认值收紧为清单所在目录 + 12B 流式魔数），原子提交为 `151a4f3`；
  - 独立 Full Mode R1（`d36d44a00b67`）与 R2（`5cfb331b61be`，裁定 `阻断交付`，坐实 `R1-1` 并保留 `R1-2`/`R1-3` 优化建议） → 独立 W3-Delta 修复提交 `2e7df5e`（根治 `R1-1` 并顺并 `R1-2`/`R1-3`） → 独立 Scoped Delta (`delta-r1`，`862f2b8375b9`) 复核 **🔴 0 / 🟡 0 / ⚪ 0** 免派 `delta-r2` 直接收口放行，归档见 [wave3-frontend-skills-v2](../reviews/2026-11-24-wave3-frontend-skills-v2/README.md)；
  - 实测 Git 追踪体量变化（`master` `7768359` → `2e7df5e`）：`taste-driven-designer` 13 → 10 文件 / 1,437 → 554 行（-61.4%）/ 78,208 B → 31,187 B（-60.1%，核心 7 文件 18,485 B）；`frontend-qa-gate` 8 → 9 文件 / 1,568 → 978 行（-37.6%）/ 76,647 B → 49,007 B（-36.1%，核心 7 文件 29,178 B，从 0 实采纯正则升级为 209 行磁盘物证/魔数门禁 + 282 行真实物证单测）；两技能合计 154,855 B → 80,194 B（-48.2%）；全仓 `skills/` 544,365 B → 470,384 B（-13.6%）。
- **待办**: 无（复跑全量门禁后 Fast-Forward 合入 `master` 并推送）

---

## 1. Wave 3 核心架构裁决

针对评估报告揭示的「官僚文书流水线（`taste-driven-designer`）」、「只验表不验真（5 组对抗探针击穿 `check-qa-report.py`）」、「无头环境 100% `BLOCKED` 死锁」与「SSOT 双向倒挂」四大核心病灶，按两项前端技能的**方案 A 瘦身提纯与实采化路线**实施 V2.0 升级：

1. **`taste-driven-designer` V2.0 瘦身提纯**：
   - **D1 表面模式分流与一体化 SSoT**：区分 `Persuade`（叙事展示/落地页）与 `Operate`（高频工具/控制台），合并原独立种子步骤至 `references/discover-phase.md`；
   - **2026 10 大 AI Tells**：在原有 7 项反模式基础上扩展第 8–10 项以覆盖 2026 新一代模式坍缩与交互伪装特征（`references/ai-tells-audit.md`）；
   - **D2 极简 Critic 闭环**：拆除 9 列评审账本与 `round-nonce` 文本回执官僚负担，收敛为 **5 列评审记录表**（保留盲比匿名去标识、空白截图作废、鉴别力自检、原则优先与防乒乓、5 轮上限）；将无截图降级与多模态能力门控并入 `references/critic-loop-protocol.md`；
   - **SSOT 分工纠偏与种子脚本重铸**：移除冗余状态矩阵，确立五域运行时断言 SSOT 归位 `frontend-qa-gate`；将 `scripts/generate-seed.py` 升级为纯标准库 `argparse` + `secrets` + `hashlib.sha256` 拒绝采样无偏流（根治 Park-Miller 零状态钳位死锁）；退役冗余外壳与旧文案测试，新建 `test_taste_generate_seed.py` 与 `test_taste_designer_v2_surface.py`。
2. **`frontend-qa-gate` V2.0 双轨门禁与真实磁盘证据升级**：
   - **双轨门禁破除无头死锁**：拆分为 **Tier 1 Automated Block-Merge Gate（23 项：`D-R` 5 + `D-S` 8（移除越界代码项 `S9`）+ `D-A` 7 + `D-P` 3）** 与 **Tier 2 Human & Device Sign-Off Checklist（4 项：`H-A5`/`H-V4/V5`/`H-V6`/`H-B1/B2`，标 `pending_human` 不阻断自动化放行）**；
   - **现代探针编排协议**：新增 `references/probe-orchestration.md`，按宿主能力路由至 `chrome-devtools-mcp` / `agent-browser` / Playwright + axe + Lighthouse CI / `webapp-testing`；
   - **真实磁盘证据 JSON 门禁（Schema v2）**：废弃 433 行中文 Markdown 正则解析器、`.sh` 兼容壳与重型手工模板，重铸 `scripts/check-qa-report.py` 实施 Fail-Closed 磁盘文件存在性、非空、symlink 防逃逸、`.png`/`.jpg`/`.webp`/`.json` 魔数格式、占位符拦截、`runtime_signals` 计数清零与 `verdict` 推导一致性校验；提供 `templates/qa-evidence-template.json` 与 `templates/qa-summary-template.md`，新建 `test_frontend_qa_evidence_gate.py` 与 `test_frontend_qa_v2_surface.py`；
   - **SSOT 归位**：`references/acceptance-matrix.md` 确立为五域运行时断言的唯一真相源（不再自称 `taste` 内联副本）。

---

## 2. 并行任务划分（零文件交集）

| 任务包 | 独占写边界 | 核心交付目标 |
| :--- | :--- | :--- |
| **W3-1** | `skills/taste-driven-designer/` | 精简 `SKILL.md` 与 `references/`；新增 `Persuade`/`Operate` 表面模式分流、2026 10 大 AI Tells、5 列盲比记录表与内置多模态门控；重铸纯标准库无偏 `generate-seed.py`；移除冗余外壳与状态矩阵；新建 `test_taste_generate_seed.py` 与 `test_taste_designer_v2_surface.py` |
| **W3-2** | `skills/frontend-qa-gate/` | 确立双轨 23+4 门禁并移除越界 `S9`；新增 `probe-orchestration.md`；废弃正则验表，重构 Schema v2 Fail-Closed 真实磁盘证据 JSON 门禁 `check-qa-report.py` 及 JSON/摘要模板；新建 `test_frontend_qa_evidence_gate.py` 与 `test_frontend_qa_v2_surface.py` |
| **W3-3** | `skills/goal-loop/` 两文件 + 两份前端设计书 + `README.md` + `docs/index.md` + `docs/project/changelog.md` + 本计划 | 同步 `goal-loop` 前端门禁命令与双轨放行口径；升级 `taste-driven-designer-design.md` 与 `frontend-qa-gate-design.md` 至 V2.0.0；同步 `README.md`、`docs/index.md`（V1.53.0）、`docs/project/changelog.md`（V1.8.0）并创建本实施计划 |

---

## 3. 验收硬门禁与目标成果

### 3.1 五项验收硬门禁

1. `python3 scripts/doc-gates/check-all.py --full` → `Exit 0`（断链 / 健康体检 / 可回答性 / 全仓测试 4/4 全绿）
2. `python3 scripts/doc-gates/check-golden-tasks.py --root docs` → `Exit 0`（0 FAIL）
3. `python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews` → `Exit 0`（0 断链）
4. `python3 -m pytest skills/ scripts/ -q` → `Exit 0`（含 `_shared` 表面与跨技能链接哨兵、`goal-loop`、`taste-driven-designer` 与 `frontend-qa-gate` 全套行为/契约测试）
5. Full Mode 独立双轮对抗审查（R1 → R2 → 如需 Scoped Delta）取得 **Zero Blockers / 准予交付**终审裁决并通过 `check-review-report.py --require-verdict=PASS`

### 3.2 目标成果

- **消除结构性缺陷**：彻底消除 Park-Miller LCG 零状态死锁、5 组探针击穿正则假门禁、无头环境永久 `BLOCKED` 死锁与跨技能 SSOT 倒挂；
- **公共技能高可移植与低维护税**：双技能均遵循跨仓可独立安装原则，摆脱脆弱中文散文正则锁死测试，转向行为边界测试与真实磁盘物证校验（最终追踪体量与实跑测试数待三方汇合后在验收阶段实测落盘）。
