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
- **当前活跃阶段**: P4 定向单轮红队审查（子智能体 `3de9d0a9` 审查中）
- **当前活跃子任务**: Task P4.1
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: `pytest skills/ -q` = **123 passed**（红队 D 系列修复后新增 7 用例）；全技能链接验证 broken=0 / cross-skill=0；`bash -n` / `git diff --check` / 断链 0 / 健康度 PASS
- **最新有效提交**: `96c8ff9`（滥用防护加固）；补丁链 `6230451` → `96c8ff9`
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


---

## 3.1 验收矩阵证据 (Acceptance Matrix · 2026-09-21)

```text
FU-1（5/5 符合预期）
  [PASS] 合法：- 无未验证项 / - 性能域本轮未适用（…） / - 未验证：（无）
  [PASS] 非法：- 无阻断，但性能未验证 / - 性能未适用，但错误态未验证   → 均被拒
FU-3（3/3 符合预期）
  [PASS] 合法：N/A + 「未适用」说明
  [PASS] 非法：N/A 无说明 / N/A 域仍有断言                          → 均被拒
FU-2（6/6 技能干净）
  taste-driven-designer · dual-round-review · goal-loop · frontend-qa-gate · doc-governance · agy-delegation-workflow
  → 全部 broken=0 / cross-skill=0
```

**全量回归**：`pytest skills/ -q` = **116 passed**（qa-gate 40 + 仓库级链接自检 3 + 既有）。
**边界登记**：行内代码与围栏内容豁免（示例语义）；引用他技能必须用命名引用，不得把真实链接写进行内代码——已写入 `cross-skill-link-policy.json` 的 `exemption_boundary` 并由扫描器自检固化。

---


---

## 3.2 附加发现：本地技能软链接补齐 (FU-4)

- **现象**：`.agents/skills/frontend-qa-gate` 缺失（其余 5 个技能链接正常）。
- **根因**：`contexts/install.py` 的 `link_local_skills()` 上次运行于 2026-09-20（`taste-driven-designer` 创建时），而 `frontend-qa-gate` 于 2026-09-21 新建后未重新运行。
- **修复**：仅执行技能链接函数（不触碰全局 AGENTS.md 分发，避免影响用户既有环境配置）：
  ```bash
  python3 -c "import sys; sys.path.insert(0, 'contexts'); import install; install.link_local_skills()"
  ```
  → 输出「成功: 已创建软连接 …/frontend-qa-gate -> ../../skills/frontend-qa-gate」，复核 6/6 技能链接齐备。
- **结论**：`install.py` 的实现与 README §「本仓库内开发」声明**一致**（技能软链接自动化已存在），无需代码改动；此前判断「install.py 未实现」系仅读前 30 行导致的误判，已在计划中更正。
- **后续纪律**：**新增技能后必须重跑 `contexts/install.py`**（或 `link_local_skills()`），并纳入交付清单。
- **范围**：`.agents/` 已被 `.gitignore` 忽略，无需提交。

---

## 4. 终审与归档 (Review & Closure)

- [x] **Task P4.1**: 定向单轮红队审查（子智能体 `3de9d0a9`；基线 `f189039..6a16eec`）—— 裁决 **✅ 可放行（🔴 0 / 🟡 4 / ⚪ 5）**；报告 `.review-context/r1-followups-report.md`
- [x] **Task P4.2**: 红队建议项闭环（父代理裁定：**D1 视为未闭环**、D6 同批修复）

| ID | 裁定 | 修复与证据 |
|:---:|:---:|---|
| D1 | 接受 | 第 4 章判定从「标点形态」改为「实词 + 否定式」：列表行含「未验证/阻断」且非「无…」否定式即视为有内容；合法并列否定（顿号/逗号/完整句）不再误拒 |
| D2 | 接受 | 判定扩展到表格行与引用块行（表格行需带冒号实词，避免表头误判） |
| D3 | 接受 | 括号夹带（含「未验证/阻断/未测/未完成」）一律视为有内容 |
| D4 | 接受 | N/A 行的断言数/通过数/失败数必须均为 0 |
| D5 | 接受 | N/A 说明必须出现在第 4 或第 5 章（不再全文搜索） |
| D6 | 接受 | ① checker 未闭合围栏 fail-closed 报错（围栏标记奇数即失败）；② 自检新增 `test_fences_balanced`，命令行示例豁免收紧（行内含 `](` 时不豁免） |
| D7 | 接受 | policy `scope_note` 修正为准确的能力边界（自检按仓库根解析，单装可达性由安装模拟人工验证） |
| D8 | 登记 | 缩进代码块可伪装第 8 章（结构层；`--require-verdict=PASS` 锚定行首可拦） |
| D9 | 接受 | 计划 checkpoint 记录修正（113 → 123 passed） |

**验证**：`pytest skills/ -q` = **123 passed**（新增 D 系列 6 用例 + 自检围栏用例）；`bash -n` / `git diff --check` 干净。

- [ ] **Task P4.3**: 结项登记与推送（推送待用户确认）

---

## 5. 修订历史 (Revision History)
- **[2026-09-21]**: 计划创建（V1.0.0，Maintenance-Patch，三项待办复现证据与修复范围锁定）。
- **[2026-09-21]**: 红队审查 ✅ 可放行（🔴 0）；D1–D9 建议项全部处置（D1 经父代理裁定按未闭环修复）；回归 123 passed。