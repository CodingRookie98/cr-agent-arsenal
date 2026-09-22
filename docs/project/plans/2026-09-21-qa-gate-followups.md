# frontend-qa-gate 后续待办闭环 维护修复计划 (Maintenance-Patch Plan)

> **文档控制信息**
> - **文档标识**: PLAN-FIX-QA-GATE-FOLLOWUPS-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-21

> **目标元数据**
> - **所属项目**: CR Agent Arsenal
> - **执行通道**: Maintenance-Patch（存量维护；保留 3-Tries 熔断、修复前先复现、回归测试、定向单轮红队审查）
> - **目标简述**: 闭环 `frontend-qa-gate` 交付遗留的三项待办 —— FU-1 门禁对「无」声明变体的误拒；FU-2 跨技能相对链接与示例路径断链（7 + 5 处）并补仓库级自检；FU-3 结论列 `N/A` 白名单。
> - **创建日期**: 2026-09-21
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-09-21（"先把后续待办做完，我们再push"）
> - **状态**: 进行中
> - **隔离分支**: 直接维护 `master`（维护补丁，非功能分支）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P4 定向单轮红队审查（P3 修复已完成）
- **当前活跃子任务**: Task P4.1
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: `pytest skills/ -q` = **113 passed**（新增 7 用例：qa-gate 4 + 仓库级链接自检 3）；全技能链接验证 broken=0 / cross-skill=0；`bash -n` / `git diff --check` / 断链 0 / 健康度 PASS
- **最新有效提交**: `f189039`（frontend-qa-gate 交付结项）
- **阻断原因**: 无

---

## 1. 复现证据 (Reproduction)

| 待办 | 复现命令/样本 | 实测 | 期望 |
|:---:|---|---|---|
| FU-1a | PASS 报告第 4 章写 `- 无未验证项` | exit 1（错误：第 4 章列出了未验证项） | exit 0 |
| FU-1b | PASS 报告第 5 章写 `- 未验证：（无）` | exit 1（错误：第 5 章列出了具体未验证项） | exit 0 |
| FU-3 | PASS 报告某域结论列写 `N/A` | exit 1（错误：结论表存在非 PASS 结论） | exit 0（N/A = 本轮该域无适用断言，需可追溯） |
| FU-2a | 单装模拟：`dual-round-review` 4 处 `../goal-loop/references/host-adapters.md` | 断链 4 | 0（改命名引用） |
| FU-2b | 单装模拟：`goal-loop/references/host-adapters.md` 3 处 `../../dual-round-review/SKILL.md` | 断链 3 | 0（改命名引用） |
| FU-2c | 单装模拟（剥离围栏后）：`doc-governance` 5 处示例路径链接 | 断链 5 | 0（示例改行内代码） |

复现脚本：`/tmp/fu_repro.py`、`/tmp/fu_scan2.py`（扫描剥离围栏，避免示例代码块误报）。

---

## 2. 修复范围 (Fix Scope — Diff 锁定)

- `skills/frontend-qa-gate/scripts/check-qa-report.sh` —— FU-1「无」声明放宽；FU-3 结论列白名单扩展 `N/A` 并加可追溯要求
- `skills/frontend-qa-gate/tests/test_qa_gate_contract.py` —— 新增 FU-1/FU-3 契约用例（含滥用防护：N/A 无说明必须拒绝）
- `skills/dual-round-review/SKILL.md` —— 4 处跨技能链接改命名引用
- `skills/goal-loop/references/host-adapters.md` —— 3 处跨技能链接改命名引用
- `skills/doc-governance/{SKILL.md, references/diataxis-standard.md, references/rfc-crystallization-lifecycle.md}` —— 5 处示例路径改行内代码
- `skills/_shared/tests/test_cross_skill_links.py`（新增）—— 仓库级自检：全部技能文档（剥离围栏）跨技能相对链接 = 0 且技能内断链 = 0
- `skills/_shared/cross-skill-link-policy.json` —— coverage 更新为全覆盖
- `docs/project/plans/2026-09-21-frontend-qa-gate.md` §4.4 —— 待办状态流转
- **严禁越界**：不改动三信号门禁、五域断言语义、Critic 协议；不引入新依赖。

---

## 3. 回归测试 (Regression Tests)

- [x] **Task P3.1**: 契约测试先红 —— checker 的 FU-1/FU-3 用例 + 仓库级链接自检（实测 red：5 failed）
  - **验收命令**: `python3 -m pytest skills/frontend-qa-gate/tests/ skills/_shared/tests/ -q`
- [x] **Task P3.2**: 文档链接整改 —— dual-round-review 4 处 + goal-loop 3 处改命名引用；doc-governance 经核查为行内代码/围栏示例（扫描器修正，非真实断链）
- [x] **Task P3.3**: checker 实现转绿（FU-1「无」变体放宽 + FU-3 N/A 白名单与可追溯检查 + 围栏识别含缩进）
  - **验收命令**: 同上（预期 green）
- [x] **Task P3.4**: 全量回归 —— `python3 -m pytest skills/ -q` = **113 passed**，零回归
- [x] **Task P3.5**: L0 + L-Doc 门禁全过；全技能链接验证 broken=0 / cross-skill=0

---

## 4. 终审与归档 (Review & Closure)

- [ ] **Task P4.1**: 定向单轮红队审查（Maintenance-Patch 通道；子智能体独立复现 FU-1/FU-2/FU-3 与滥用防护）
- [ ] **Task P4.2**: 阻断项修复与复验
- [ ] **Task P4.3**: 结项登记与 §4.4 状态流转

---

## 5. 修订历史 (Revision History)
- **[2026-09-21]**: 计划创建（V1.0.0，Maintenance-Patch，三项待办复现证据与修复范围锁定）。