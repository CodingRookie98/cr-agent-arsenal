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
- **当前活跃阶段**: 已完成（红队初审 + Delta 复核均判定可放行；推送待确认）
- **当前活跃子任务**: 无
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/3
- **最后一次验证状态**: `pytest skills/ -q` = **126 passed**（红队 D 系列 + D1c 残留 + 分句级漏洞修复后新增 11 用例）；全技能链接验证 broken=0 / cross-skill=0；红队 D 样本 11/11、分句攻击 6/6 符合预期；`bash -n` / `git diff --check` / 断链 0 / 健康度 PASS
- **最新有效提交**: `3f9a734`；补丁链 `6230451` → `96c8ff9` → `de3f61e` → `aeed3d2` → `0ec5e50` → `3f9a734`
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

**全量回归**：`pytest skills/ -q` = **126 passed**（qa-gate 50 + 仓库级链接自检 4 + 既有）。
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
| D9 | 接受 | 计划 checkpoint 记录修正（113 → 126 passed） |
| D1c 残留 | 追加自查 | `- 本报告无未验证项与阻断` 仍被误拒（原否定式判定只看行首「无」）→ 改为「任意否定词修饰实词」，红队 D 样本 11/11 通过 |
| 分句漏洞 | 追加自查 | `- 无阻断，性能未验证`（否定在前、肯定在后）4 种分隔符全部误放行 → 第 4 章判定升级为 awk 分句级扫描 + 否定位置比较（实词只有在**其前**有否定词时才视为被否定）；分句攻击 6/6 拦截 |

**验证**：`pytest skills/ -q` = **126 passed**；红队 D 样本 11/11、分句攻击 6/6 符合预期；`bash -n` / `git diff --check` 干净。

- [x] **Task P4.3**: 结项登记（Delta 复核终版）

**Delta 复核终版**（红队 `3de9d0a9`，基线 `6a16eec..0ec5e50`；报告 `.review-context/delta-r1-followups-report.md`）：

- 终审定性：**✅ 可放行（🔴 阻断项 0 / 🟡 残留 7）**
- 上一轮唯一 🔴（分句级 fail-open 回归）**已彻底闭环**：4 种中文分隔符的「否定在前 + 肯定在后」夹带全部 exit 1；`- A5 未验证：宿主无性能测量能力`（实词后的「无」）正确判为未否定；D1 全部合法变体（含此前误拒的 `- 本报告无未验证项与阻断`）exit 0
- D2–D9 声明目标全部达成（N/A 三列、说明章节约束、未闭合围栏 fail-closed、命令行藏链接检出、policy 边界声明）
- 复核者自我更正：曾基于工作区未提交版本误判 R4/R5/R6 已闭环，改用 `git show aeed3d2:checker.sh` 双版本对照后纠正——`0ec5e50` 才真正闭环

### 4.1 后续待办：Delta 复核残留 7 项 (M1–M7)

| ID | 样本 | 方向 | 根因与建议修法 |
|:---:|---|:---:|---|
| M1 | `- 未验证项：无（全部 31 条已跑）` | 误拒（安全） | 实词在冒号前、「无」为值 → 位置比较判为未否定；建议对「`- <实词>…：无`」加白名单 |
| M2 | `- 阻断项：无` | 误拒（安全） | 同 M1 |
| M3 | `- 无未验证项, 性能未验证`（英文逗号） | 漏检 | 分句符 `[，。；、]` 未含英文标点；建议扩展为 `[，。；、,.;]` |
| M4 | `- 无阻断性能未验证`（无分隔） | 漏检 | 位置比较只取「第一个否定词 vs 第一个实词」；建议遍历句内**全部**实词 |
| M5 | `- 无阻断 性能未验证`（空格） | 漏检 | 同 M4 |
| M6 | `- 无未验证项（A5 pending）` | 漏检 | 括号先删除 + 词表仅中文；建议括号内容删除前先做实词检测，词表补 `pending\|TODO\|未跑\|待测\|尚未\|未执行` |
| M7 | `\| A5 \| 未验证 无性能测量 \|`（表格无冒号） | 漏检 | OTHER_SUSPECT 强制要求冒号；建议改表头白名单（实词后紧跟 `\|` 视为表头） |

**风险判断**（红队）：5 项漏检均需**非标准写法**触发；第 5 章未验证清单 + 计数一致性 + 第 8 章 verdict 锚定三重兜底未被绕过。2 项误拒为 fail-closed 方向。
**处置**：需求方选择「先修再推送」→ 已修复（提交 `6cd7c95`）：第 4 章判定统一为**抹除否定配对 + 残留检测**——① M1/M2 加「`- <实词>…：无`」白名单；② 表头白名单（含 原因/说明/描述 且无冒号）；③ 循环抹除「否定词 + 实词（可连接重复）」配对，抹除至稳定后残留实词即视为有内容（替代位置比较）。实测：M1–M7 **7/7**、红队 D 样本 **11/11**、分句攻击 **6/6** 符合预期；回归 **128 passed**。待红队聚焦复核。

- [x] **Task P4.4**: 推送准备（本地领先 `origin/master` 19 提交；**推送待需求方确认**）

---

## 5. 修订历史 (Revision History)
- **[2026-09-21]**: 计划创建（V1.0.0，Maintenance-Patch，三项待办复现证据与修复范围锁定）。
- **[2026-09-21]**: 红队审查 ✅ 可放行（🔴 0）；D1–D9 建议项全部处置（D1 经父代理裁定按未闭环修复）；父代理追加自查修复 D1c 残留（否定词位置比较）与分句级 fail-open 漏洞（awk 分句扫描）；回归 **126 passed**。