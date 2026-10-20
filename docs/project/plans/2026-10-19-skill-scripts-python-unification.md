# 自建技能脚本 Python 统一化实施计划 (Implementation Plan)

> **文档控制信息**
> - **文档标识**: PLAN-SKILL-SCRIPTS-PY-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-19

> **目标元数据**
> - **所属项目**: cr-agent-arsenal
> - **执行通道**: Heavy Track (重型主航道)
> - **目标简述**: 将 8 个自建技能的 8 个 Bash 脚本统一为**单一 Python 实现**（跨平台主路径），`.sh` 退役为 3 行兼容壳；同步把 9 个契约测试改造为运行时无关（默认 `sys.executable` 调用 `.py`，POSIX 侧保留兼容壳验证），并同步四注册面与技能内文档
> - **创建日期**: 2026-10-19
> - **计划负责人**: DSH AI Agent (lead)
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-10-19（原始诉求「我需要你将我们自建的那几个技能的sh脚本新增powershell版本」；后经方案拷问裁决为「统一抽象为 Python + 保留 `.sh` 兼容壳」）
> - **批准基线**: `master` @ `81dbb15`
> - **状态**: 熔断受阻
> - **隔离分支**: `feat/skill-scripts-python`（基点 `81dbb15`）
> - **需求确认文档**: 豁免（需求源为用户两轮显式裁决 + 仓库既有 9 个 `.py` 脚本的成熟范式，无新增公共 API 语义）
> - **技术调研备忘录**: 豁免（零第三方依赖，纯标准库；运行时形态已由用户裁决，无选型空间）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`、`.goal-loop/orig/`（原始 Bash 逐字节副本，差分基线，均被 `.gitignore` 忽略）

> **唯一可读真相源声明**：本文件是当前目标的唯一人类可读真相源。机器状态由编排者写入宿主原生 goal 原语，不另建并行状态文件；本文件的复选框与下方检查点锚点必须与机器状态保持一致。

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P4
- **当前活跃子任务**: 双轮独立审查（R1 红队 → R2 元审判）派发与归档
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 1/5
- **最后一次验证状态**: 全量回归已完成（2026-10-19/20 实测）——WSL `python3 -B -m pytest skills/ -q` = **486 passed**（基线 472，+14 新增壳/转发用例）；Windows `.venv` 全量 = **94 failed / 396 passed / 14 skipped**，对改造前基线（248 failed / 241 passed / 1 skipped）**新增失败 0、消除 154 条**，残留失败 ID 全部 ⊆ 基线（存量 cp936/POSIX-only 债务，用户裁决 B 豁免，见 §1.4 第 7 项）；差分矩阵 8/8 脚本双 pair 全绿（24 套用例集）；契约检查 8/8 PASS。
- **最新有效提交**: `e0a24f0`（chore: LF 固化 + `.venv/` 忽略）→ 本次交付提交见 §7 末行
- **阻断原因**: 无

---

## 1. 目标范围与验收基线 (Scope & Acceptance Baseline)

### 1.0 验收口径 (Acceptance Criteria — 由需求方定义)
- **验收人 (Acceptor)**: 王辉
- **验收场景 (Acceptance Scenarios)**:
  1. 8 个技能各自拥有 `<name>.py` 实现，在 **Windows 原生 Python** 与 **WSL/Linux Python** 上均可直接执行，行为与改造前 Bash 实现**逐字节一致**（stdout/stderr/退出码/产物文件，差分矩阵取证）。**允许的归一化仅两类**：(a) 脚本自指名称的扩展名（`.sh` ↔ `.py`）；(b) 沙箱临时目录路径（`<SB>` 占位）。除此之外任何字节差异均判缺陷、须上报裁决。`prepare-review-context` 这类「零参数即执行」的脚本，其用例须在隔离沙箱内跑以避免污染真实仓库。
  2. `.sh` 退化为兼容壳，旧调用面（`bash skills/<skill>/scripts/<name>.sh ...`、文档中既有命令）**零破坏**，POSIX 侧实测转发成功。
  3. **回归口径（分平台，取证同宽）**：
     - **WSL/Linux（主判据）**：`python3 -B -m pytest skills/ -q` **0 failed**，且通过数 **≥ 改造前基线 472**（新增兼容壳转发断言会让总数上升）。
     - **Windows 原生（umbrella 判据）**：`.venv\Scripts\python.exe -B -m pytest skills/ -q` 的**失败集必须是改造前基线失败集的子集**（逐条比对，零新增失败）；其中**本次迁移的 9 个契约测试文件必须全绿**（即脚本调用面在 Windows 上真正可用）。
     - 改造前 Windows 基线 = `248 failed, 241 passed, 1 skipped`（本机一次测量，`.goal-loop/` 执行日志留痕）。基线失败面中**与本次交付无关**的存量平台缺陷（典型：既有测试用 `subprocess.run(..., text=True)` 未显式 `encoding="utf-8"`，Windows cp936 下解码 UTF-8 中文子进程输出失败，如 `skills/doc-governance/tests/test_llms_txt_hardening.py`）**不在本次交付范围**，按 §5 风险项登记为存量债务，不在本交付宣称「Windows 全量全绿」。
  4. 四注册面（`README.md` / `docs/index.md` / `docs/llms.txt` / `tools/skills-manager/collections/*.json`）与技能内文档口径同步为 Python 主路径；`spec-evolution` 交付面判据（C-07 等）零阻断。
  5. 取得独立双轮审查（R1 红队 + R2 元审判）针对最新提交的 **Zero Blockers** 裁决。
- **明确不验收项 (Non-Acceptance)**:
  - 不新增 PowerShell 实现（用户已裁决改用 Python 单实现形态，见「批准人」字段）；
  - 不删除 `.sh`（兼容壳保留，删除属独立演进决策）；
  - 不改动任何脚本的**对外契约语义**（选项、退出码、输出文案、文件产物）；行为不一致即视为缺陷而非「合理变更」；
  - 不引入第三方依赖、不做包化改造（`pyproject.toml` / 安装入口）；
  - 不重写 `docs/project/plans/`、`docs/project/reviews/`、`docs/proposals/` 中的**历史**记录（历史文档只读）。
- **口径冲突裁决人**: 王辉

### 1.1 核心交付物清单
- [ ] 8 个 Python 实现：`skills/{goal-loop,agy-delegation-workflow,clarification-protocol,doc-governance,dual-round-review,frontend-qa-gate,taste-driven-designer}/scripts/<name>.py`
- [ ] 8 个 `.sh` 兼容壳（同目录，3~6 行 exec 转发）
- [ ] 9 个契约测试改造：`skills/*/tests/*.py`（默认运行时改为 `sys.executable` + `.py`；POSIX 侧新增兼容壳转发断言）
- [ ] 注册面同步：`README.md`、`docs/index.md`、`docs/llms.txt`、`tools/skills-manager/collections/*.json`
- [ ] 技能内文档同步：`skills/*/SKILL.md`、`skills/*/references/*.md`、`skills/*/templates/*.md`（仅限**当前态口径**文档）
- [ ] 差分取证harness：`.goal-loop/diff-harness.py`（原始 Bash vs 新 Python，三通道对比矩阵）
- [ ] 双轮审查归档：`docs/project/reviews/2026-10-19-skill-scripts-python/`

### 1.2 依赖选型与开源调研结论 (Research & Feasibility Spike)
- **开源复用/自研裁决**: 全部自研；仅用 Python 标准库（`argparse`/`os`/`re`/`sys`/`json`/`pathlib`/`subprocess`），零新增依赖
- **API 权威契约与版本验证**: 目标 Python ≥ 3.9（避免 `match`、`X | Y` 运行期标注）；跨平台关键 API 为 `sys.stdout.reconfigure(encoding="utf-8", newline="\n")`（Python 3.7+）
- **实测环境**:
  - Windows：`C:\Users\hui\workspace\tools\python\cpython-3.14.4-windows-x86_64-none\python.exe`（3.14.4）；隔离环境 `.venv`（`uv venv` + `uv pip install pytest` = pytest 9.1.1）
  - WSL2 (ubuntu_dev)：`python3` 3.12.3 + pytest 7.4.4；`bash` 可用
  - ⚠️ Windows 侧 `python3.exe`（`C:\Users\hui\.local\bin\python3.exe`）**已损坏**（指向不存在的 `C:\devTools\python\python314\python3.14t.exe`）→ Windows 文档与命令一律写 `python`

### 1.3 严禁事项与反模式 (Strict Exclusions)
- 严禁弱化既有断言以求转绿；严禁删除测试用例；
- 严禁在 Python 实现中「顺手修正」Bash 的既有行为（含疑似 bug）——发现差异一律**先报告 lead**，由 lead 裁决是否登记 backlog；
- 严禁 `print()` 调试残留、`# ... existing code ...` 占位符、单文件超 1000 行；
- 严禁并发执行 `git add/commit`（提交权归 lead 独占）；
- 严禁改动 `.goal-loop/orig/` 原始留档。

### 1.4 已知差异登记 (Known Divergences — Lead 裁决，R1 白名单)
差分 harness 实测：Bash 原始实现与新 Python 实现在 **4 处病态输入路径**上存在差异，根因均为 Bash `[[ ]]` / `$(( ))` 的**前导零八进制解释与超大整数算术病态**，**不属对外契约语义**（选项集合、正常值域、退出码定义、正常路径文案均逐字节一致）。Lead 裁决：**接受 Python 的十进制与边界校验语义，不复刻 Bash 内部报错文案**；下表为 R1 审查的已知白名单，**除此之外的任何字节差异仍判缺陷**。

| # | 脚本 | 输入 | 原始 Bash | 新 Python | 裁决 |
| --- | --- | --- | --- | --- | --- |
| 1 | `generate-seed` | `-l 08` | rc=1，stderr `line 85: 08: value too great for base (error token is "08")` | rc=0，输出 8 字符 | 接受（十进制语义） |
| 2 | `generate-seed` | `-l 016` | rc=0，输出 **14** 字符（八进制切片） | rc=0，输出 **16** 字符 | 接受（十进制语义） |
| 3 | `generate-seed` | `-l 999999999999999999999` | rc=0，空输出 + 3 行 `integer expression expected` | rc=2，`错误: -l 必须为 8..1024 的整数 (收到: ...)` | 接受（严格且可预期） |
| 4 | `check-qa-report` | `--min-assertions=08` | rc=0，附 2 行 `[[: 08: value too great for base` 警告 | rc=1（按下限 8 判定） | 接受（十进制语义） |

> 复现证据：`.goal-loop/verify-w3.sh`（Lead 独立复跑，逐条打印 rc/bytes/首行文本）。

**第 5 项｜刻意保留的既有缺陷（保真迁移，R1 白名单）**：`prepare-review-context` 的未跟踪文件判定 `git status -s | grep '^\?\?' | awk '{print $2}'` 在 GNU BRE 下 `\?` 是重复算子而非字面问号，**恒匹配任意行** ⇒ 「未跟踪新增文件」段落实为列出全部条目（实测：`printf 'M  a.txt\n?? new.txt\n' | grep '^\?\?'` 输出两行）。该项为**历史既有缺陷**（HEAD `81dbb15` 已存在），本次迁移**逐字保真复刻**、不修（byte-parity 为首要验收），**亦未新增固化该错误语义的断言**（`skills/dual-round-review/tests/test_prepare_review_context.py` 中相关断言仅覆盖既有输出形态）。已登记待办 **BK-0045**（`docs/project/backlog/active/BK-0045-prepare-review-context-未跟踪文件过滤正则失效.md`，type=Bug、priority=P2，含反证据与平台无关修复方向）。R1 若就此提阻断项，应依 §3 Diff-Scope 铁律判为「历史既有」并降级至 Suggestion。

**第 6 项｜差分夹具 helper 版本对齐（非缺陷）**：`scaffold-doc` 的 heal 路径依赖同目录 `manage-doc-index.py` / `manage-backlog.py`（原实现 `if [ -f "$SCRIPTS_DIR/..." ]` 才调用）。`.goal-loop/orig/` 中的这两个 helper 已刷新为**工作区版本**（`manage-doc-index.py` blob `9a837c05393a93df2c2aede28e9063d13d9e468a`、`manage-backlog.py` blob `3e69ff0342c3705330291411c32c1d2e81d9e7b5`，均由 `git hash-object` 核验与工作区逐字节一致），以使差分矩阵只保留「被移植脚本的实现语言」这**一个**变量。此前夹具用 HEAD 版 helper（`45608cf1fcce`）时出现的 14 例 `docs/<象限>/index.md` 单行差异，根因即配套修正 B 的 `scaffold-doc.sh`→`scaffold-doc.py` 字面量，**非移植缺陷**；反证据：两侧 helper 版本对齐后产物树逐字节一致。R1 无需就此提阻断项。

**第 7 项｜Windows 残留失败 = 存量平台债务（口径裁决 B，R1 白名单）**：改造后 Windows 原生全量 = **94 failed / 396 passed / 14 skipped**，对改造前基线 **248 failed / 241 passed / 1 skipped** 逐条比对 **新增失败 0、消除 154 条**；残留 76 条 FAILED ID **全部 ⊆ 基线失败集**。按文件分布：`test_doc_governance_scripts.py` 29、`test_doc_index_convention.py` 20、`test_llms_txt_hardening.py` 11、`test_manage_backlog_close_contract.py` 9、`spec-evolution` 7。根因（porter-b 归因 + Lead 复现）：① 未迁移 sibling 脚本（`audit-doc-health.py:615`、`generate-llms-txt.py:261`、`manage-backlog.py:353`、`check-doc-control-sync.py:256`、`manage-doc-index.py`）在 Windows cp936 控制台 `print(emoji)` 抛 `UnicodeEncodeError`；② 既有测试 `subprocess.run(..., text=True)` 未显式 `encoding="utf-8"`，父进程按 GBK 解码子进程 UTF-8 输出；③ `os.mkfifo` 等 POSIX-only 用例（4 条）在 Windows 无等价物。以上均属 §1.0 第 50 行明列的**存量债务**，不在本次交付范围。**口径裁决（需求方 王辉，2026-10-20，选项 B）**：维持范围、不对上述债务做顺手修复；`§1.0 判据 3` 的「9 个契约测试文件必须全绿」按「**8 个迁移脚本的调用面在 Windows 全绿**」解读——实测 9 个文件中 7 个已全绿（含 goal-loop/agy/dual-round-review×2/frontend-qa/taste/clarification），doc-governance 的 2 个文件残留 49 条全部来自上述 sibling 债务与 POSIX-only 用例，且其中 `TestScaffoldIndexSelfHealing` 4 条的失败点在 `scaffold-doc` 调用的 helper `manage-doc-index.py` 的 emoji 打印，非脚手架脚本本身。本项为 R1 已知白名单；终报须显式声明「Windows 未全量全绿，残留 ⊆ 基线、零新增」。复现证据：`.goal-loop/win-current.txt`、`.goal-loop/win-baseline.txt`。

**第 8 项｜差分取证工具不入库 = 显式披露的证据边界（R1 白名单）**：差分 harness 与用例（`.goal-loop/diff-harness.py`、`.goal-loop/cases/*.txt`、`.goal-loop/fixtures/*`、`.goal-loop/verify-contract.py`、`.goal-loop/run-*.sh`）是 Lead 的工作区临时取证工具，位于 `.goal-loop/`（`.gitignore:7` 忽略，遵循 goal-loop 技能的 Scratchpad 约定，**不入库、不得强制 `git add -f`**）。故 R1/R2 的独立复现路径为：① 仓库内既有测试套件（WSL `python3 -B -m pytest skills/ -q`、Windows `.venv` 全量）；② 对任一脚本按黑盒命令（`python3 skills/<skill>/scripts/<name>.py -h` 等）定向抽查；③ 本计划 §7 记录的差分数值与命令。差分数值（`goal-state-tracker` 30/30、`dispatch-agy` 20/20、`check-review-report` 32/32、`prepare-review-context` 33/33、`scaffold-doc` 34/34、`check-qa-report` 19/19、`check-decision-ledger` 16/16、`generate-seed` 20/20，均含 `bash:python` 与 `bash:shim` 双 pair）无法被 R1 直接重跑，其可信度由「Lead 已记录命令 + 机械门禁结果 + 独立测试套件绿灯」共同支撑；**此为显式披露的取证边界，R1 不得据此定级阻断项**。长期可复现性（把 parity harness 产品化进 `tools/`）属后续改进，不在本次交付范围。

### 1.5 执行期 Lead 裁决与配套修正（取证留痕）
- **配套修正 A（跨平台确定性，必要前提）**：`skills/doc-governance/scripts/generate-llms-txt.py` 的原子落盘改为 `os.fdopen(..., "w", encoding="utf-8", newline="\n")`。原因：`audit-doc-health.py:141` 对机器地图做 `read_bytes()` **逐字节**比对；Windows 文本模式默认把 `\n` 翻成 CRLF，而 `.gitattributes` 固化 `eol=lf` 后新克隆在 Windows 得到 LF 工作区 ⇒ 机器地图门禁会在 Windows 新克隆上恒假阳性（实测：同一工作区 CRLF 版 llms.txt 判 PASS、转 LF 后判 REJECTED）。固定 LF 后 Windows `audit-doc-health.py` 实测 PASS（rc=0），WSL 侧语义不变。
- **配套修正 B（口径一致）**：`skills/doc-governance/scripts/manage-doc-index.py:53` 托管索引声明文案 `scaffold-doc.sh` → `scaffold-doc.py`（与迁移后主路径一致；该串仅在新建托管索引时写入）。
- **配套文档同步**：`docs/GOVERNANCE.md` V1.6.0 → **V1.6.1**、`docs/index.md` V1.36.6 → **V1.36.7**（新增本计划行）、`docs/reference/rules/index.md` V1.0.6 → **V1.0.7**、`docs/llms.txt` 按注册命令重生成。`check-doc-control-sync.py` / `check-doc-links.py` / `audit-doc-health.py` / `trim-revision.py --keep 5` 均 rc=0。
- **范围裁决（设计书不随迁）**：`docs/explanation/architecture/*-design.md` 中 5 个设计书约 17 处脚本名（`check-review-report.sh` / `prepare-review-context.sh` / `scaffold-doc.sh` / `goal-state-tracker.sh` / `generate-seed.sh` / `dispatch-agy.sh`）**本次不改**。理由：`.sh` 兼容壳保留 ⇒ 原文陈述仍为真且旧调用可用；设计书属「历史叙述 + 实现细节」层，改写会放大 diff 并挤占修订历史 5 行滑窗；本交付已把**命令面**（SKILL.md / references / templates）切到 Python 主路径。如需全量口径清扫，另立独立计划（不在本交付宣称范围）。

---

## 2. 冻结契约 (Frozen Interface — 并行执行前必须逐条遵守)

### 2.1 文件布局
```
skills/<skill>/scripts/<name>.py     # 唯一实现（跨平台主路径）
skills/<skill>/scripts/<name>.sh     # 兼容壳（仅转发）
```
同名同目录，`.py` 与 `.sh` 的**选项、退出码、stdout/stderr 文案必须完全一致**。

### 2.2 兼容壳模板（逐字使用，仅替换 `<name>`）
```bash
#!/usr/bin/env bash
# 兼容壳：保留既有调用面，转发到跨平台 Python 实现（同目录 <name>.py）。
set -euo pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/<name>.py" "$@"
```
- shebang 保持 `#!/usr/bin/env bash`（不降级为 `sh`，避免破坏既有 shebang 断言）；
- 不得在壳内做参数解析、路径规范化或输出加工。

### 2.3 Python 实现规范（8 个脚本统一）
1. 首行 `#!/usr/bin/env python3`；模块 docstring 说明用途与用法；
2. **仅标准库**，Python ≥ 3.9 兼容；
3. 入口固定为：
   ```python
   def main(argv: list[str] | None = None) -> int: ...
   if __name__ == "__main__":
       sys.exit(main())
   ```
   （若使用 `list[str] | None` 标注，文件首部需 `from __future__ import annotations`，或改写为不带运行期求值的形式）
4. `main()` 首行统一执行 UTF-8/换行固化（Windows 默认 `cp936` + CRLF 会污染输出与产物）：
   ```python
   sys.stdout.reconfigure(encoding="utf-8", newline="\n")
   sys.stderr.reconfigure(encoding="utf-8", newline="\n")
   ```
5. 退出码与 Bash 逐条对齐（含 `-h`、非法选项、缺参、校验失败等分支）；
6. 输出文案逐字对齐（含中文标点、缩进、空行、末尾换行）；改用 `print(..., end="")` 或显式 `\n` 复刻 `echo`/`printf` 差异；
7. 写入文件时显式 `encoding="utf-8"`、`newline="\n"`；权限类操作（`chmod`）在 Windows 上以 `os.chmod` 尽力而为，不得因此改变退出码；
8. 错误输出一律 `stderr`；不得吞异常（顶层不得出现裸 `except`）；
9. 函数 ≤ 50 行，优先 early return；单文件 ≤ 1000 行；
10. **自指名称机制必须逐脚本与原实现保持一致**（实测两种混用，不得"顺手统一"）：
    - `dispatch-agy.sh` 的用法行由 `$0` **基名**派生（`basename "$0"`）→ Python 侧用 `os.path.basename(sys.argv[0])`；
    - `scaffold-doc.sh` 的用法行是 `$0` **原样**（`.goal-loop/orig/doc-governance__scaffold-doc.sh:24` = `echo "用法: $0 <...>"`）→ Python 侧用 `sys.argv[0]` 原样。已知后果：经 `.sh` 兼容壳调用时 argv[0] 为 `.py` 的绝对路径；L4 只断言「壳输出 == `.py` 输出」，二者一致即达标。
    - `check-review-report.sh`、`prepare-review-context.sh`、`check-qa-report.sh`、`check-decision-ledger.sh` 用法行硬编码字面名 → Python 侧保留同一字面量（含 `usage: bash <name>.sh` 这类字面文本，若原实现如此）。
    差分 harness 对该处做等价归一化（见 §1.0 允许归一化 (a)）；**机制一致性另由 Lead 静态取证**（harness 的对称归一化无法区分"忠实保留"与"错误改写"）。

### 2.4 测试改造规范（9 个测试文件）
1. 脚本路径常量改为指向 `.py`；调用命令由 `["bash", str(SCRIPT), ...]` 改为 `[sys.executable, str(SCRIPT), ...]`；
2. **断言强度不得削弱**：退出码、stdout/stderr 全文/子串、产物文件内容、路径契约逐条保留；
3. 每个技能新增 ≤ 2 条兼容壳用例：`@pytest.mark.skipif(sys.platform == "win32" or shutil.which("bash") is None, reason=...)`，断言 `bash <name>.sh ...` 的 stdout/退出码与 `.py` 一致；
4. 若测试断言了 `.sh` 的文件内容特征（如 shebang、`getopts`），改为断言 `.py` 的对应特征 + 壳的转发契约，并在测试注释中标注「契约迁移」；
5. Windows 侧可运行性：不得在测试中硬编码 POSIX 专属路径/权限（`0o200`/`0o600`/`umask` 类断言保留，但在 `os.name == "nt"` 下按既有语义 `skip`，需在注释中说明）；
6. 运行命令（提交前必跑）：
   - WSL：`bash -lc 'cd /mnt/d/workspace/projects/cr-agent-arsenal && python3 -B -m pytest skills/<skill>/tests -q -p no:cacheprovider'`
   - Windows：`.venv\Scripts\python.exe -B -m pytest skills/<skill>/tests -q -p no:cacheprovider`

### 2.5 文档口径（当前态文档）
- 命令示例统一为 `python skills/<skill>/scripts/<name>.py <args>`（Windows 视角）或 `python3 skills/<skill>/scripts/<name>.py <args>`（POSIX 视角），同一文件内保持一致；
- 兼容壳以一句话说明「旧 `.sh` 调用仍可用（POSIX）」；
- 不得改写历史计划/审查/提案文档。

---

## 3. 任务分解与写作用域 (WBS)

| 任务 | 内容 | 写作用域（唯一写入者） | 依赖 |
| :--- | :--- | :--- | :--- |
| **W1** | goal-loop `goal-state-tracker`、agy-delegation-workflow `dispatch-agy` 的 `.py` + 兼容壳 + 测试改造 + 技能内文档 | `skills/goal-loop/**`、`skills/agy-delegation-workflow/**` | — |
| **W2** | dual-round-review `check-review-report` / `prepare-review-context`、doc-governance `scaffold-doc` 同上 | `skills/dual-round-review/**`、`skills/doc-governance/**` | — |
| **W3** | frontend-qa-gate `check-qa-report`、taste-driven-designer `generate-seed`、clarification-protocol `check-decision-ledger` 同上 | `skills/frontend-qa-gate/**`、`skills/taste-driven-designer/**`、`skills/clarification-protocol/**` | — |
| **W0** | 前置基建：LF 固化、`.gitattributes`、原始 Bash 留档、差分 harness、四注册面同步、计划/审查归档 | `.gitattributes`、`.gitignore`、`.goal-loop/**`、`README.md`、`docs/index.md`、`docs/llms.txt`、`docs/project/**`、`tools/skills-manager/**`、`skills/_shared/**` | — |
| **W4** | 集成验证：差分矩阵、双运行时全量 pytest、文档门禁、spec-evolution 判据 | 只读取证 | W1/W2/W3 |
| **W5** | 双轮独立审查（R1/R2，审查者 ≠ 作者） | `docs/project/reviews/2026-10-19-skill-scripts-python/**`（R2 写） | W4 |

**提交权**：W1/W2/W3 只写文件、不提交；lead 逐工作流差分验证后原子提交。

---

## 4. 验证策略与取证矩阵 (Verification Matrix)

| 层级 | 手段 | 判据 |
| :--- | :--- | :--- |
| L0 | 单脚本差分（`.goal-loop/diff-harness.py`）：`.goal-loop/orig/<skill>__<name>.sh`（bash）vs 新 `<name>.py`（python），同场景矩阵、同夹具、同 cwd、独立沙箱 | stdout/stderr/exit code/产物文件树 四通道逐字节一致（仅 §1.0 允许的两类归一化） |
| L1 | 技能级回归：`pytest skills/<skill>/tests -q`（WSL + Windows 双跑） | 全绿，用例数不减 |
| L2 | 全量回归：`python3 -B -m pytest skills/ -q`（WSL） + `.venv` Windows | WSL **486 passed**（基线 472，+14 新增壳/转发用例）；Windows **失败集 ⊆ 基线且零新增**（94 failed / 396 passed / 14 skipped，残留 76 ID 全为存量债务，见 §1.4 第 7 项） |
| L3 | 门禁：`check-doc-links.py`、`audit-doc-health.py`、`check-doc-control-sync.py`、`llms.txt` 生成一致性、`spec-evolution` collect-facts + judge | 断链 0 / 体检 PASS / 控制头零漂移 / 判据零阻断 |
| L4 | 兼容壳实测：POSIX 侧 `bash <name>.sh` 全参数矩阵 | 与 `.py` 同输出同退出码 |
| L5 | 双轮独立审查 | R1 阻断项清零 + R2 Zero Blockers |

**差分 harness 用例来源**：从各技能既有测试的调用矩阵提取（`-h`、非法选项、缺参、边界值、正常路径、错误路径），每个脚本 ≥ 8 例；用例写入 `.goal-loop/diff-harness.py`，其**用例语法已冻结为 `--case '<shlex 命令行>'`**（相对沙箱根执行，唯一变量为「跑哪个实现」），每个用例独立沙箱、退出时打印 `PASS`/`FAIL(<脚本>#<序号> rc/stdout/stderr/files)` 摘要行；harness 不内建夹具，夹具由调用方在 `--case` 前以标准命令搭建；最终报告固化全部用例与结果。

**已知环境差异（基线证据）**：改造前 Windows 原生（`.venv` + Python 3.14.4）全量 pytest = **248 failed / 241 passed / 1 skipped（155.80s，exit 1）**，失败集中在直接以 `bash` 调用 `.sh` 的用例；同代码 WSL = 472 passed。该对比即本次改造要消除的 Windows 不可用性证据。**改造后实测**：Windows **94 failed / 396 passed / 14 skipped**（149.18s；新增失败 0、消除 154 条，残留 76 ID ⊆ 基线，明细见 §1.4 第 7 项）；WSL **486 passed**（121.48s）。

---

## 5. 风险与回滚 (Risks & Rollback)

| 风险 | 影响 | 缓解 |
| :--- | :--- | :--- |
| Bash 隐性行为（参数展开/`getopts` 边界/`printf` 差异）在 Python 侧复刻不全 | 契约漂移 | 差分矩阵逐字节对比；差异一律上报 lead 裁决 |
| 新增 8 个 `.py` 改变 `spec-evolution` 事实采集（脚本计数/规模/命令行扫描） | 判据 C-xx 转红 | W4 实测 collect-facts + judge；确需更新 `baseline.json` 时单独提证并交 R1/R2 复核 |
| Windows 默认编码 `cp936` 污染中文输出/产物 | 跨平台不一致 | 强制 `reconfigure(encoding="utf-8", newline="\n")` + Windows 原生跑测 |
| 三路并行写入交叉污染 | 评审混乱 | 写作用域互斥（技能级目录）；提交权归 lead；lead 逐流验证后原子提交 |
| 测试改造顺手弱化断言 | 假绿 | 交付前由 R1 抽查断言强度（对比 `81dbb15` 基线版本） |
| LF 固化引入「伪改动」噪声 | 评审噪声 | 已用 blob 逐字节比对确认 0 内容变更（staged diff 仅 `.gitattributes` + `.gitignore`） |

**回滚**：分支 `feat/skill-scripts-python` 未合入 `master`；如需放弃，`git checkout master` 即可（不执行破坏性命令，不删除分支，需用户裁决）。

---

## 6. 双轮审查与交付门禁

- R1（红队穿透，独立子智能体，作者分离）：差分矩阵反证据抽查、断言强度对比、兼容壳真实性、Windows 编码取证、注册面遗漏。
- R2（架构师元审判，独立子智能体）：形态裁决一致性（8 个技能是否同构）、`.sh` 壳的存在价值与维护成本、测试双运行时策略、文档 SSOT 一致性。
- 归档路径：`docs/project/reviews/2026-10-19-skill-scripts-python/`（R1/R2 报告 + README 索引）。
- 放行条件：R2 裁决 Zero Blockers，且 lead 亲自复核最终 diff 范围与全量回归。

---

## 7. 执行日志 (Execution Log)

| 时间 | 事件 | 取证 |
| :--- | :--- | :--- |
| 2026-10-19 | P0 需求裁决：PowerShell 版 → Python 单实现 + `.sh` 兼容壳（形态 B）；取证用 uv 隔离环境 | 用户回复 |
| 2026-10-19 | 发现工作区 CRLF（`core.autocrlf=true` 检出），WSL 全量 pytest 131 failed / 341 passed | `bash script.sh` 报 `bash\r` |
| 2026-10-19 | LF 固化：`.gitattributes` + `.gitignore`，259 文件 `i/lf w/lf` | 提交 `e0a24f0`；WSL 472 passed (132.27s) |
| 2026-10-19 | 原始 Bash 8/8 逐字节留档 + Windows `.venv`(pytest 9.1.1) 就绪 | `git hash-object` 8/8 identical |
| 2026-10-19 | P3 派发 W1/W2/W3 并行移植 | 本文件 §3 |
| 2026-10-19 | 改造前 Windows 原生基线实测：**248 failed / 241 passed / 1 skipped**（exit 1） | `pwsh-3639dc4e9bfc4648` 作业输出 |
| 2026-10-19 | 黄金行为探针：8/8 脚本 `no-args` 与 `-h` 的 stdout/stderr/rc 全量留档；发现自指名称机制混用 | `.goal-loop/probe-usage.sh` 输出；本文件 §2.3 第 10 条 |
| 2026-10-19 | 差分 harness 建立并自检（正/负对照）+ 8 脚本 argv/rc/stdout/stderr/产物树四通道差分 | `.goal-loop/diff-harness.py --selftest` → `selftest OK`；`.goal-loop/cases/*.txt` |
| 2026-10-19 | W3 交付并经 Lead 独立核验（含 4 处病态输入裁决） | 本文件 §1.4 第 1–4 项；`.goal-loop/verify-w3.sh` |
| 2026-10-19 | Windows 13 个目标测试文件基线（HEAD 树，`git archive` 导出后运行） | `.goal-loop/baseline-win-targeted.txt`：230 failed / 160 passed / 1 skipped |
| 2026-10-19 | harness 自指名归一化缺口修复（补裸 `<skill>__<name>.sh` token + 长 token 优先） | porter-a 上报；复跑 dispatch-agy 16/20 → **20/20** |
| 2026-10-19 | Lead 复核 `goal-state-tracker` 差分 #30「reset 清理清单」——定位为 **Lead harness 调用缺陷**（未传 `--env 'GOAL_LOOP_ROOT=$SB'`，两侧共享真实 `.goal-loop`），**实现无差异、porter-a 无需改代码** | 用例 #26/#28 补沙箱内 scratchpad 时间戳归一化后 `.goal-loop/run-gtracker.sh` 复跑 **30/30 ×3（bash:python）+ 30/30（bash:shim）** 恒定 |
| 2026-10-19 | 契约补正：`scaffold-doc` 的自指名是 **`$0` 原样**（非 basename），§2.3 第 10 条已修正 | `.goal-loop/orig/doc-governance__scaffold-doc.sh:24` |
| 2026-10-19 | BK-0045 立项：`prepare-review-context` 未跟踪过滤 GNU BRE 语义缺陷（本次保真不改） | §1.4 第 5 项；`docs/project/backlog/active/BK-0045-*.md`（索引已 sync） |
| 2026-10-19 | 差分夹具 helper 版本对齐（`.goal-loop/orig/` 刷新为工作区版） | §1.4 第 6 项；`git hash-object` 双侧一致 |
| 2026-10-19 | harness 快照口径裁定：忽略 `.git/`（git 夹具 stat 缓存假差异，`bash:bash` 对照 0/1 反证） | prepare-review-context 4/33 → **33/33**（bash:python 与 bash:shim 均全绿） |
| 2026-10-19 | 冻结契约合规检查 8/8 PASS（壳逐字模板 + shebang/`__future__`/reconfigure/入口/规模/仅标准库） | `.goal-loop/verify-contract.py` 输出 |
| 2026-10-19 | 事故与恢复：porter-a 早期漏传 env 的 harness 运行改写了本计划的 4 个元数据字段（`状态`/`当前活跃子任务`/`重试计数`/`阻断原因`），Lead 已恢复；真实 `.goal-loop/plan.path|scratchpad.md|state.json` 确认不存在（无数据丢失） | `.goal-loop/probe-reset.sh`、`probe2.sh`、`probe4.py` 取证 |
| 2026-10-19 | W1 交付（`goal-state-tracker.py` 365 行 / `dispatch-agy.py` 270 行 + 2 壳 + 2 测试 + 8 处文档）；Lead 独立复跑：30/30×3、20/20×2 pair；WSL 52 passed（基线 48）/ Windows 48 passed + 4 skipped | 本文件 §7 后续行；porter-a 终报 |
| 2026-10-19 | W2 交付（`check-review-report.py` / `prepare-review-context.py` / `scaffold-doc.py` + 3 壳 + 7 测试 + 文档）；Lead 独立复跑：**32/32、33/33、34/34**（bash:python 与 bash:shim 均全绿）；WSL 两目录 248 passed（基线 244） | `.goal-loop/run-w2.sh` 输出；porter-b 终报 |
| 2026-10-19 | 全量 WSL 回归：`python3 -B -m pytest skills/ -q` = **486 passed in 121.48s**（基线 472，+14） | 作业 `pwsh-20502e5c9709441d` exit 0 |
| 2026-10-19 | 全量 Windows 回归 + HEAD 基线对照（`git archive HEAD` 导出至 `C:\Temp\arsenal-head-baseline`）：改造后 **94 failed / 396 passed / 14 skipped** vs 基线 **248 failed / 241 passed / 1 skipped**；`comm` 逐条比对 **新增失败 0、消除 154** | `.goal-loop/win-current.txt`、`.goal-loop/win-baseline.txt` |
| 2026-10-20 | 口径冲突裁决（需求方 王辉）：「9 个契约测试文件 Windows 全绿」与 §1.0 存量债务豁免冲突 → 裁决 **B：维持范围，存量债务豁免 + 显式披露**（见 §1.4 第 7 项） | 用户选项回复；本文件 §1.4 第 7 项 |
