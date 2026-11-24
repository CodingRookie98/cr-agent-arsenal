# Delta 第一轮红队与第一性原理对抗审查报告 (Wave 2A: `goal-loop` V3.0)

> - **审查模式**: Full Mode · Delta Round 1（针对 R2 裁决的最小增量红队复核）
> - **增量基线**: `b49109ca9f444b56d592e82af135bef1153435ac...6fe71c05334aaca65c547e20c755f67ab07af917`（分支 `refactor/wave2a-goal-loop-v3`，9 files changed, +179/-42）
> - **前序裁决基线**: `docs/project/reviews/2026-11-23-wave2a-goal-loop-v3/r2-1a1c112..b49109c.md`（独立核验 `sha256sum` 全值 `d8b3b49382eea7441af009430bf456ac72fe03fb867a5382a751f60f808934ae`，前 12 位 `d8b3b49382ee` 与归档索引一致）
> - **审查视角**: Non-Compliant Principal Staff Engineer & Red-Team Security/Architecture Auditor

---

## 1. 第一性原理与本质溯源分析

### 1.1 Delta 修复架构收敛性评估

本次增量提交 `6fe71c0` 严格锁定 R2 裁决书 `r2-1a1c112..b49109c.md` 坐实的 5 项 P1 阻断项（`R1-1`～`R1-5`）与 6 项被采纳的 P2/P3 优化项（`R1-6`、`R1-7①`、`R1-8` 空/倒置区间、`R1-9`、`R1-10`、`R1-11①②`），未引入过度工程或越界重构：

1. **脚本极简化预算与工程不变量统一达成平衡**：
   - `skills/goal-loop/scripts/pack-handoff.py` 由 119 行扩展至 **144 行**（纯标准库，无外部依赖），同步更新 `docs/explanation/architecture/goal-loop-design.md:119,173` 与 `docs/project/changelog.md:37` 的口径为 `≤145 行`，未出现文档数字与实际代码脱节。
   - 未采纳已被 R2 驳回的过度设计（未实现动态反引号长度计算算法，未在 `review-pkg` 中重复造轮子扫描 `git status --porcelain` 脏树），保持与 `dual-round-review` 边界清晰。
2. **核心状态机与内部契约闭合情况**：
   - `skills/goal-loop/references/testing-decision-matrix.md`（L14–18, L24, L41, L78–85）全部 6 处阶段引用已精确对齐 V3.0 五主阶段（`Plan` 阶段 2、`Execute` 阶段 3、`Verify` 阶段 4 原 P3.5/P4、`Close` 阶段 5），彻底清除 `阶段 3.5` 残留，且矩阵内 L0–L3 分级标准与 Mock 防逃逸红线（L52）零弱化。
   - `skills/goal-loop/references/host-adapters.md:91` 已修正悬空编号为「受第 4 项重派上限约束」，`contexts/AGENTS.md:50` 已同步为「三轨五主阶段状态机（Align ➔ Plan ➔ Execute ➔ Verify ➔ Close）」且全文件严格保持 **98 行**无净增。
   - `skills/goal-loop/SKILL.md` 维持 **88 行**、`description` 为 **369 字符**，L74 已补齐 `[--repo <dir>]`；`skills/goal-loop/references/context-engineering.md:16` 已将 `.goal-loop/` 绝对断言修改为「推荐加入 `.gitignore`」。
3. **测试套件真实性核验**：
   - `skills/goal-loop/tests/test_goal_loop_contract.py` 扩充至 **10 条行为与表面哨兵测试**，经逐行审查确认**零空洞断言**（全部基于真实子进程执行、临时 Git 仓库与官方模板）；L258–277 防回流黑名单准确纳入 `create_goal`/`get_goal`/`update_goal`/`docs/design/`/`docs/adr/`/`阶段 3.5`，且正确避开了 `docs/requirements/`（避免误杀 `stage-progression-protocol.md:67` 合规禁令）。

### 1.2 前序 R2 阻断项与选纳项逐条核验总览

| 原 R2 条目 | 核验结论 | 实证摘要（代码位置与实测结果） |
|:---|:---:|---|
| 原 `R1-1` (P1) | ✅ 已修复 | `pack-handoff.py:75,78`：官方模板 `E-0..C-2`（含 `Task V-2（条件 · 仅前端产物交付）`）全部 `rc=0` 精确提取；`1` vs `1.1`/`1-a`/`1_1`/`10` 与 `E-1` vs `E-1-a`/`E-1.2` 无错抓；`Task-9`/`Task 9`/`9` 全兼容。（另于 §4 登记 1 项低风险裸词 `--task Task` P3 边界遗漏） |
| 原 `R1-2` (P1) | ✅ 已修复 | `pack-handoff.py:30-39,59-64`：`_slice_block` 截断后追踪 `_fence_step` 围栏状态，未闭合时补齐缩进一致的闭合围栏及 `> ...（节选已截断）`，实测 44 行 `  ```bash`、`  ~~~python`、` ````markdown ` 嵌套围栏截断均闭合，`## 目标任务` 零吞噬。 |
| 原 `R1-3` (P1) | ✅ 已修复 | `pack-handoff.py:26,128-130`：`main()` 首部重配置 `stdout`/`stderr` 为 `utf-8` + `newline="\n"`，`_emit` 显式传 `newline="\n"`；实测 `PYTHONIOENCODING=gbk`/`cp1252`/`ascii` 叠加 `PYTHONUTF8=0` 输出含 `🚀` 与中文路径均 `rc=0`。 |
| 原 `R1-4` (P1) | ✅ 已修复 | `pack-handoff.py:103,118,123`：`_git()` 统一注入 `-c core.quotePath=false`，`diff --name-only` 改 `-z` 按 `\0` 切分；实测含中文目录、空格及 `git mv` 重命名文件均输出原始 UTF-8 路径，无 `\344`/`\346` 八进制转义。 |
| 原 `R1-5` (P1) | ✅ 已修复 | `testing-decision-matrix.md:14-18,24,41,78-85`：阶段名称与编号完全对齐 `stage-progression-protocol.md`，全局检出零 `阶段 3.5` 残留。 |
| 原 `R1-6` (P2) | ✅ 已修复 | `pack-handoff.py:19-28,138-141`：区分 `out is None` 与 `not out.strip()`，外层捕获 `(OSError, UnicodeDecodeError)` 走 `_fail()`；实测 `--out ""`、`"   "`、已存在目录、父路径为文件、非 UTF-8 文件、无 `git` 均返回 `rc=1` 且无裸 Traceback。 |
| 原 `R1-7①` (P2) | ✅ 已修复 | `pack-handoff.py:35`：反引号围栏开启校验 ``"`" not in rest``；实测行首 ` ```inline``` ` 不再误开围栏吞噬后续任务。 |
| 原 `R1-8` (P2) | ✅ 已修复 | `pack-handoff.py:116-122`：`base == head` 与 `base..head` 无提交且 `head..base` 有提交时均返回 `rc=1` 明确报错，且正常分叉分支 `main_sha..feat_sha` 不误报。 |
| 原 `R1-9` (P2) | ✅ 已修复 | `host-adapters.md:91` 与 `contexts/AGENTS.md:50` 均精确对齐且后者保持 98 行。 |
| 原 `R1-10` (P2) | ✅ 已修复 | `test_goal_loop_contract.py` 扩充至 10 条真实测试，全部实测通过，无虚假/脆弱断言。 |
| 原 `R1-11①②` (P3) | ✅ 已修复 | `SKILL.md:74`（74/88 行，desc 369 字符）补 `[--repo <dir>]`，`context-engineering.md:16` 改温和推荐表述。 |

---

## 2. 运行时与 SSR/沙盒安全推演

本节未激活（非客户端/SSR 改动）。

以下针对增量修改后的 `skills/goal-loop/scripts/pack-handoff.py`（144 行）执行 **CLI / Subprocess / 编码 / 路径 / 文件写入安全审计**：

| 审计维度 | 代码位置 | 核查结论与实证状态 |
|---|---|---|
| **Shell 与 Git 选项注入防护** | `pack-handoff.py:102-103,110-114` | `_git()` 固定 `shell=False` 且 `-c core.quotePath=false` 仅置于子命令前、无用户输入拼接；`base_ref` 与 `head_ref` 仍严格执行 `not ref or ref.startswith("-")` 与 `rev-parse --verify --quiet f"{ref}^{commit}"` SHA 规范化。实测 `--repo ... -- --all HEAD` 返回 `rc=1` ✅ |
| **子进程缺失与仓库异常兜底** | `pack-handoff.py:106-108,138-141` | `repo.is_dir()` 先行短路不存在目录；缺失 `git`（`PATH=""`）时 `subprocess.run` 抛出 `FileNotFoundError` 被 `main()` 的 `except (OSError, UnicodeDecodeError)` 拦截并调用 `_fail()`，返回 `rc=1` 无 Traceback；空仓库（0 提交）`HEAD` 校验返回 `rc=1` ✅ |
| **路径与文件写入边界** | `pack-handoff.py:17-28,90-93,138-141` | `out is None` 输出 stdout；`--out ""` 与 `--out "   "` 均命中 `not out.strip()` 返回 `rc=1`；`--out <existing_dir>`、`--out <existing_file>/sub.md` 与非 UTF-8 计划文件均被 `except (OSError, UnicodeDecodeError)` 拦截返回 `rc=1` 且无裸堆栈 ✅ |
| **跨平台 stdio 与 CRLF 一致性** | `pack-handoff.py:26,128-130` | `reconfigure(encoding="utf-8", errors="replace", newline="\n")` 位于 `ap.parse_args()` 之前，确保连同 `--help` / `argparse` 错误在内的全部中文输出在 `gbk`/`cp1252`/`ascii` 控制台均不触发 `UnicodeEncodeError`；`path.write_text` 强制 `newline="\n"` ✅ |
| **非 ASCII 路径与分叉/空区间边界** | `pack-handoff.py:116-123` | `-c core.quotePath=false` + `diff --name-only -z` + `\0` 切分正确还原中文目录、含空格路径与 `git mv` 重命名路径；`base == head` 与单向倒置区间均 Fail-Closed（`rc=1`），双向有提交的分叉分支正常放行（`rc=0`）✅ |
| **任务 ID 前缀剥离空值边界** | `pack-handoff.py:75-78` | 存在 1 处低风险边缘遗漏（见 §4 `R1-1` P3）：`--task "Task-"` 被剥离为空返回 `rc=1`，但裸词 `--task "Task"` / `--task "Task "` 未被视作缺省编号而命中首个任务。 |

---

## 3. 红队攻击路径推演

所有红队对抗探测均在隔离临时目录（`tempfile.TemporaryDirectory()`，未修改仓库任何文件）或只读命令行中独立实证执行：

### 探针 1：全仓门禁与全量技能单元测试复算
- **命令与结果**：
  1. `python3 -m pytest skills/goal-loop/tests/test_goal_loop_contract.py -v` → **10 passed in 4.44s**（Exit 0）；
  2. `python3 skills/doc-governance/scripts/check-all.py --full` → **7 项门禁全部通过**（机器地图、断链、版本一致、真值轴、健康体检、可回答性、测试套件，Exit 0）；
  3. `python3 -m pytest skills/ -q` → **558 passed in 65.19s**（Exit 0）。

### 探针 2：官方模板全任务提取 & 跨平台极端编码矩阵（`gbk` / `cp1252` / `ascii` + `PYTHONUTF8=0`）
- **攻击假设**：在 `PYTHONUTF8=0` 强制关闭 PEP 540 UTF-8 模式下，分别注入 `PYTHONIOENCODING=gbk`、`cp1252`、`ascii` 运行 `brief` 抽取含 `🚀`、`·`、中文括号的 `Task V-2（条件 · 仅前端产物交付）` 与 Top-level `--help`。
- **实测结果**：三种编码下均返回 **`rc=0`**，`Task V-2（条件 · 仅前端产物交付）` 与 `🚀` 完整输出，未混入 `Task V-3`，围栏平衡校验为 `True`；`cp1252` 下 `--help` 正常输出中文帮助无崩溃。

### 探针 3：任务 ID 边界冲突 & 裸词前缀旁路探针
- **攻击假设**：构造 `1.1` / `1-a` / `1_1` / `10` 全部排在 `1` 之前、`E-1-a` / `E-1.2` 排在 `E-1` 之前，以及 `Task-9`、`### Task H-1（带中文括号标题）` 的混合计划文件，分别使用正常 ID 与空/畸形前缀（`""`, `"   "`, `"Task"`, `"Task-"`, `"Task "`）探测。
- **实测结果**：
  - 所有合法 ID 查询（`1`、`E-1`、`9`、`Task-9`、`Task 9`、`H-1`）全部精准命中唯一目标，**零错抓子任务**；
  - `""`、`"   "`、`"Task-"` 返回 `rc=1`；
  - **命中边缘缺陷（P3）**：传入 `--task "Task"` 或 `--task "Task "` 时，`pack-handoff.py brief skills/goal-loop/templates/goal-plan-template.md --task Task` 返回 **`rc=0`** 并抽出计划首个任务 `Task E-0`。原因：`task_id.strip()` 先去掉尾部空格，`re.sub(r"^task[\s-]+", ...)` 不匹配无后缀的 `"Task"`，残余 `tid="Task"` 直接匹配 `- [ ] **Task E-0**` 里的 `Task `。

### 探针 4：35 行围栏截断与 CommonMark 嵌套/行内反引号对抗
- **攻击假设**：分别构造（a）`  ~~~python` 缩进波浪号围栏恰好在第 34 行开启、第 35 行被 `limit=35` 截断；（b）4 反引号外围栏 ` ````markdown ` 内嵌套 3 反引号 ` ```bash ` 并跨第 35 行截断；（c）`测试策略` 与 `Task 1` 正前方出现行首 ` ```inline``` ` 行内代码。
- **实测结果**：三种场景均返回 `rc=0`，输出全部保持 `_fences_balanced == True`，且 `## 目标任务` 与目标任务内容完整保留在围栏之外。

### 探针 5：Git `review-pkg` 非 ASCII、重命名、分叉分支与全异常 Fail-Closed 探针
- **攻击假设**：在临时 Git 仓库提交 `中文目录/带空格 文件.md` 与 `git mv 旧名字.md 新名字.md` 并构造分叉分支（`main` 与 `feat` 各自独立前向提交）、倒置区间（`feat_sha..base_sha`）、同提交符号引用（`main..HEAD`）、零提交空仓库，以及 `PATH=""` / `--out "   "` / `--out <file>/sub.md`。
- **实测结果**：
  - `cp1252` 下分叉分支 `main_sha..feat_sha` 成功输出 `- \`中文目录/带空格 文件.md\`` 与 `新名字.md`，无八进制转义且无误报倒置；
  - 倒置区间、同提交符号引用、空仓库、`PATH=""`、`--out "   "`、`--out <file>/sub.md` 均返回 `rc=1` 且 stderr 仅输出可读 `ERROR:` 诊断，零 Python Traceback。

---

## 4. 潜在缺陷清单

| 稳定 ID | 严重等级 | 文件与行号 | 变更归属 | 缺陷描述与根因 | 复现/攻击路径与证据 | 修复建议 |
|---|---|---|---|---|---|---|
| R1-1 | P3 | `skills/goal-loop/scripts/pack-handoff.py:75` | 历史遗留边界（Delta 修改同行未顺手闭合） | `_extract_task` 第 75 行执行 `tid = re.sub(r"^task[\s-]+", "", task_id.strip(), flags=re.IGNORECASE)`，要求 `task` 后必须紧跟至少一个空白或连字符。当调用方误传裸词 `--task "Task"` 或 `--task "Task "`（缺少任务编号）时，`strip()` 后仅剩 `"Task"` 无法匹配 `^task[\s-]+`，导致 `tid` 保持 `"Task"`，随后被 `tail` 正则 `(?:\*\*)?(?:Task[\s-]+)?Task(?:\*\*)?(?=$|[\s...])` 命中计划中首个含 `**Task ...**` 的条目并返回 `rc=0`，而非 Fail-Closed 报错（`Task-` 可正常报错）。 | 实测执行 `python3 skills/goal-loop/scripts/pack-handoff.py brief skills/goal-loop/templates/goal-plan-template.md --task Task`（及 `--task "Task "`）返回 `rc=0`，输出提取了首个任务 `- [ ] **Task E-0**`。注：此行为在 `b49109c` 即已存在，属极罕见畸形输入防呆，不影响正常任务编号抽取。 | 若在后续维护中顺手收口，仅需将 L75 改为 `r"^task(?:[\s-]+|$)"`（或 L76 改为 `if not tid or tid.lower() == "task":`），即可令 `--task Task` 统一返回 `rc=1`（+0 行，**不阻断当前交付**）。 |

---

## 5. 第一轮结论概要

- **增量缺陷统计**: 🔴 **P0 = 0 / P1 = 0（阻断项共 0 项）** · 🟡 **P2 = 0** · ⚪ **P3 = 1**（`R1-1`：裸词 `--task Task` 低风险输入防呆边界）。
- **核心核验结论**:
  1. 前序 R2 裁决的 **5 项 P1 阻断项（`R1-1`～`R1-5`）与 6 项选纳优化项（`R1-6`～`R1-11①②`）已全部准确落地并通过独立对抗复测**，未见绕过、弱化断言或未同步残留。
  2. `skills/goal-loop/scripts/pack-handoff.py`（144 行）、`testing-decision-matrix.md`、`host-adapters.md:91`、`contexts/AGENTS.md:50`（98 行）、`SKILL.md:74`（88 行 / 369 字符）、`context-engineering.md:16`、`goal-loop-design.md`、`changelog.md` 及 `test_goal_loop_contract.py`（10/10 passed）均与 V3.0 契约及文档口径一致。
  3. 本仓库独立门禁实测全部通过：`test_goal_loop_contract.py` **10 passed**、`check-all.py --full` **7 项全绿**、`pytest skills/ -q` **558 passed**。
- **Delta 第一轮建议**: **✅ 无阻断项（Zero Blockers）**，建议交由 Delta 第二轮元架构师（`delta-r2`）独立核对本轮实证与 `R1-1`（P3）处置口径后出具最终放行裁决。
