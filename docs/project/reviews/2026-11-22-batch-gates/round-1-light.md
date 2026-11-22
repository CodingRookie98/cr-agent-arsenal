# 第一轮对抗审查报告（Light）—— 批量交付 P0/P1/P2 定向红队

**审查区间**: `14166b1..HEAD`（6 个提交，`skills/` 净增 742 行 / 删 1 行）
**审查对象**: RFC-0008 体量门禁（P0）· BK-0048 门禁自动化（P1）· BK-0049 可回答性评测（P2）
**审查模式**: Light 单轮定向红队；只审 diff 边界，攻击面按任务书六问定向穿透
**口径**: 仅 P0/P1 计入 Blockers；P2/P3 记录不阻断
**只读边界**: 全程未写入仓库任何被跟踪文件（`git status --short` 收尾为空）；攻击实验一律在 `/tmp` 隔离副本内进行；本文件是唯一落盘产物

---

## 0. 裁决前置摘要

| 项 | 结果 |
| :--- | :--- |
| Blockers（P0/P1） | **2**（B-01、B-02，均为 P1） |
| P0 体量门禁 | **无阻断项**：AC-1…AC-7 全部实测成立；8 项绕过探测中 6 项为加固缺口（P2/P3） |
| P1 门禁自动化 | **2 项阻断**：HEAD 门禁红灯 + hook 对本次提交结构性失明 |
| P2 可回答性 | 无阻断项；发现 3 项断言有效性问题（假 GAP、目录级豁免、空过） |
| 裁决 | **阻断（不准予交付）** |

---

## 1. 命令与输出

### 1.1 回归：`pytest skills/doc-governance/tests -q`

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest skills/doc-governance/tests -q -p no:cacheprovider
FAILED skills/doc-governance/tests/test_check_all.py::TestCheckAll::test_all_gates_pass_on_current_tree
FAILED skills/doc-governance/tests/test_check_all.py::TestCheckAll::test_quiet_mode_is_silent_on_success
2 failed, 282 passed in 21.94s
```

两个失败用例的断言体是「当前树六道门禁全绿」，失败原因即 B-01（见 §1.2）。**交付自带的新测试在自己的交付物上是红的。**

### 1.2 聚合器：`check-all.py`

```text
$ python3 skills/doc-governance/scripts/check-all.py
✅ 机器地图
✅ 断链
✅ 版本一致
❌ 真值轴
✅ 健康体检
✅ 可回答性

【真值轴】失败输出（尾部）:
📊 声明 3/63 篇（覆盖度 4.8%）｜fresh 2｜drifted 1｜missing 0｜stale 0｜unverified 0
🎯 真值分: 10.0 / 15
   - [drifted] explanation/architecture/doc-governance-design.md
     ←  skills/doc-governance/SKILL.md, skills/doc-governance/scripts/audit-doc-health.py,
        skills/doc-governance/scripts/check-doc-drift.py
🚫 门禁未通过：1/6 项失败
exit=1
```

运行时 1.20 s（GOVERNANCE V1.11.0 声称 1.5 s，属实）。

### 1.3 hook：`.githooks/pre-commit`（`core.hooksPath=.githooks` 已配置）

```text
$ sh .githooks/pre-commit            → exit 1（真值轴红灯，提交被阻断）
$ PYTHON_BIN=true sh .githooks/pre-commit        → exit 0（整体旁路）
$ PYTHON_BIN=/nonexistent/python sh .githooks/pre-commit → exit 0（静默跳过）
```

### 1.4 体量门禁端到端（隔离副本 `/tmp/e2e` = docs 拷贝）

```text
# E2E-1 新增 120 KB 文档
⛔ 文档体量超限: project/plans/huge.md: 120107 字节 > 65536，最长单行 1200 > 1000（新增超限，无基线记录）
🚫 诊断结论: REJECTED（…；1 处文档体量超限）      exit=1

# E2E-2 删除基线文件（AC-5）
⛔ 文档体量超限: project/plans/2026-10-12-spec-evolution.md: 127747 字节 > 65536（新增超限，无基线记录）
⛔ 文档体量超限: project/plans/2026-10-19-skill-scripts-python-unification.md: 最长单行 1269 > 1000（新增超限，无基线记录）
🚫 诊断结论: REJECTED（…；3 处文档体量超限）      exit=1
```

### 1.5 真实 docs 体量分布 vs 基线

```text
扫描 107 篇（docs 下 .md 共 192 篇 → 豁免 85 篇：reviews 79 + _llms 5 + AGENTS.md 1）
top bytes : 127747 (project/plans/2026-10-12-spec-evolution.md)
            58416 (explanation/analysis/llm-wiki-implementation-research.md)
            40431 (project/plans/2026-10-19-skill-scripts-python-unification.md)
top line  : 1269 (2026-10-19-skill-scripts-python-unification.md)
            879  (2026-10-12-spec-evolution.md)
over64k   : 仅 2026-10-12-spec-evolution.md
over1000L : 仅 2026-10-19-skill-scripts-python-unification.md
```

基线两条记录（127747/879、40431/1269）与实测**逐值一致**，无漂移、无遗漏、无多余条目。**基线一致性通过。**

### 1.6 可回答性评测

```text
$ check-golden-tasks.py --json
{'pass': 15, 'gap': 5, 'fail': 0}      exit=0
G-02 gap 3 篇 RFC 缺落地计划链接
G-08 gap 缺设计书: taste-driven-designer
G-12 gap how-to 象限为空     G-13 gap tutorials 象限为空
G-16 gap project/changelog.md 缺失
```

> 上述为**本报告落盘前**的基线快照。本报告创建 `docs/project/reviews/2026-11-22-batch-gates/` 后，G-17 因该目录缺 `README.md` 转 FAIL（rc=1）——受「禁止改除该报告外的文件」约束未补 README，机制与后果见 B-13。

---

## 2. 六项结论

| # | 门禁 | 结论 | 证据 |
| :--- | :--- | :--- | :--- |
| 1 | 机器地图 | ✅ PASS | `generate-llms-txt.py --split --check` rc=0 |
| 2 | 断链 | ✅ PASS | `check-doc-links.py` rc=0 |
| 3 | 版本一致 | ✅ PASS | `check-doc-control-sync.py` rc=0 |
| 4 | 真值轴 | ❌ **FAIL** | `doc-governance-design.md` drifted；`复核于 = 2026-11-22 / commit a5686f2`，而 `SKILL.md` 最后一次提交是 `9d03d22`（本批最后一个提交） |
| 5 | 健康体检 | ✅ PASS | 体量 3 条全为 warning（1 行数 + 2 存量未恶化），退出码 0；与 AC-3 / AC-6 一致 |
| 6 | 可回答性 | ✅ PASS | 15 PASS / 5 GAP / 0 FAIL，rc=0 |

**结论**：六项中第 4 项红。第 5 项的体量判定语义**正确**（存量只警告、行数只警告、新增阻断），但该项的 warning 分支把 `has_issues` 置真（audit-doc-health.py:1350-1352），仅抑制「完美」文案、不影响退出码——与既有 doc_status 处理同构，不构成缺陷。

---

## 3. 攻击实验矩阵（定向六问的实测答案）

### 3.1 体量门禁可绕过性（P0）

| 攻击 | 构造 | 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| 空基线 `{"docs":{}}` 是否等价无基线 | 超限文档 + 空对象基线 | issues=1「新增超限，无基线记录」 | ✅ **等价，仍阻断**（符合 AC-5 语义） |
| 超限文档改名 | `a/big.md` → `a/renamed.md`（基线键未变） | issues=1「新增超限」 | ✅ **不改写放行**（fail-closed） |
| 改名换扩展名 | `big.md` → `upper.MD` | **docs 扫描 0 篇，issues=0** | ⛔ **逃逸**（B-03） |
| 基线文档被删除 | 基线含 `a/gone.md`，磁盘无此文件 | issues=0，warnings=0，**无任何残留提示** | ⚠️ 静默残留（B-06 同族） |
| `--write-size-baseline` 是否写入达标文档 | 1 达标 + 1 超限 | 基线仅含 `bad.md` | ✅ **不削弱棘轮**（该问排除） |
| 预置基线投毒 | 基线预先登记 `future/plan.md` 巨值，再落 120 KB 文档 | **issues=0** | ⛔ **永久豁免**（B-06） |
| 不可读文件 | `chmod 000` 超限文档 | `{bytes:0, longest_line:0}` → 视为达标 | ⛔ fail-open（B-05） |
| 基线值类型畸形 | `{"bytes":"abc"}` | `ValueError: invalid literal for int()` 裸 traceback | ⛔ 崩溃（B-07） |

### 3.2 度量正确性（P0）

| 用例 | 实测 metrics | 结论 |
| :--- | :--- | :--- |
| `len(line)` 是字符还是字节 | 1000 个「中」→ `bytes=3001, longest_line=1000` | **字符数**，与 RFC-0008 §2/§4.1「最长单行**字符数**」一致，非缺陷 |
| CRLF | `a*1200 + \r\n` → `longest_line=1200` | ✅ `splitlines()` 已剥 `\r` |
| 无换行长文件 | 1500 字节单行 → `longest_line=1500` | ✅ 正确阻断 |
| 空文件 | `bytes=0, longest_line=0, lines=0` | ✅ 不误报 |
| 制表符 | 1200 个 tab → 1200 字符 | ✅ 按字符计，符合契约 |
| 非 UTF-8（GBK） | 200 字节 → `bytes=200, longest_line=200` | ⚠️ 以 U+FFFD 计长（每非法字节 1 字符），度量语义退化但不误放行（B-05 备注） |
| U+2028 行分隔 | 600 + U+2028 + 600 | `longest_line=600`，**不阻断** | ⛔ 绕过 1000 字符上限（B-04） |

### 3.3 聚合器可靠性（P1）

| 问 | 实测 | 结论 |
| :--- | :--- | :--- |
| `REPO_ROOT = parents[2]` | 经 `/tmp/repo-link` 符号链接导入 → 仍解析为真实仓库根 | ✅ 符号链接安全（`Path.resolve()` 先行） |
| 嵌套/复制安装 | 把脚本复制到 `/tmp/nest/skills/doc-governance/scripts/` → 6 项全 ❌，exit=1 | ✅ fail-closed（噪声大但不放行） |
| 300 s 超时是否误判通过 | `TimeoutExpired` ⊂ `SubprocessError`（实测 `True`）→ 命中 `except` → 返回失败 | ✅ 不会误判为通过 |
| `--quiet` 是否真静默 | 成功时 stdout 为空（测试断言通过）；失败时打印 ❌ + 尾部 12 行（设计如此） | ✅ 符合「只输出失败项」 |

### 3.4 hook 安全性（P1）

| 问 | 实测 / 机制 | 结论 |
| :--- | :--- | :--- |
| `PYTHON_BIN` 缺失 `exit 0` | 实测 exit 0（stderr 有提示） | ⚠️ fail-open，非静默但放行（B-09） |
| 任意可执行文件 | `PYTHON_BIN=true` → exit 0 | ⛔ 整体旁路（B-09） |
| `set -e` 是否提前退出漏报 | `if ! cmd` 在条件位置，`set -e` 不触发 | ✅ 无漏报 |
| 非 POSIX / Windows Git Bash | `#!/usr/bin/env sh` + `command -v` 可用；但 Windows 无 `python3` 时静默跳过，或命中 App Execution Alias 存根返回 9009 被当成「门禁未通过」 | ⚠️ 两种误行为（B-09 备注） |
| 本次提交引入的漂移能否被拦 | `check-doc-drift.py:258` 用 `git log -1 --format=%ct -- <anchor>`；**未提交改动对 git log 不可见** | ⛔ **结构性失明**（B-02） |
| 暂存区 vs 工作树 | hook 跑的是工作树，提交的是索引 | ⛔ 可提交未受检内容（B-02） |

### 3.5 断言有效性（P2）

| 攻击 | 实测 | 结论 |
| :--- | :--- | :--- |
| G-14 目录删除空过 | `rmtree(project/backlog/active)` → `('pass','无活跃待办')` | ⛔ 恒真通道（B-12） |
| G-17 与报告归档耦合 | 新建 `reviews/2026-11-22-batch-gates/`（仅报告、无 README）→ `('fail','缺索引: 2026-11-22-batch-gates')` | ⛔ 本报告落盘即打红（B-13） |
| G-20 目录级豁免 | 在 decisions/backlog/articles 各放一个**零元数据**文件 → 仍 `('pass','46 篇均有控制头')` | ⛔ 豁免按目录不按头部（B-11） |
| G-20 豁免是否过宽 | 非根文档 105 篇，其中 59 篇被三类目录整目录豁免（2 ADR + 55 卡片 + 2 文章），实际只校验 46 篇 | ⛔ 过半豁免 |
| G-02 假 GAP | RFC-0003 有 `**实施计划请查阅**` 链接，仍判 GAP | ⛔ 字面匹配（B-10） |

---

## 4. 新缺陷清单

### B-01 [P1 · 阻断] HEAD 门禁红灯：真值轴 drifted，交付自带 2 例测试失败

- **证据**：`check-all.py` exit 1（§1.2）；`pytest` 2 failed / 282 passed（§1.1）。
  `docs/explanation/architecture/doc-governance-design.md:7` 声明 `复核于: 2026-11-22 / commit a5686f2`；`skills/doc-governance/SKILL.md` 的最后一次提交是本批收尾提交 `9d03d22`（19:44:03），晚于 `a5686f2`（19:39:05）。
- **归因**：本批最后一个提交只改 SKILL.md 正文（新增「一键门禁」条目、改写红线 6），未同步设计书 `复核于`/版本，直接触发漂移判定。
- **影响**：① `.githooks/pre-commit` 在 HEAD 上对任何后续提交返回 exit 1，仓库进入「不可提交」状态；② BK-0048 的验收陈述「六项全绿」不成立；③ 新测试 `test_check_all.py` 两例永久红，`--full` 通道失效。
- **修复**：重跑真值轴确认无实质漂移后，把设计书 `复核于` 升到 `9d03d22` 并同步 `当前版本`（V1.4.3）与修订历史；或回退 SKILL.md 该两处改动。修完必须重跑 `check-all.py --full` 取零红灯证据。

### B-02 [P1 · 阻断] pre-commit hook 对「本次提交引入的漂移」结构性失明

- **机制**：`check-doc-drift.py:258` 以 `git log -1 --format=%ct -- <anchor_path>` 取锚点文件的**最后一次已提交**时间；hook 在提交**之前**运行，此刻锚点的改动还只在索引/工作树中，git log 仍指向旧提交 → 判为 fresh → hook 放行 → 提交完成后立刻转 drifted。
  叠加第二个口径差：hook 校验**工作树**，而 git 提交的是**索引**；`git add` 后再把文件改回达标即可提交未受检内容。
- **证据**：本批 `9d03d22` 改 SKILL.md 后 HEAD 立即红灯（§1.2），而 hook 已安装（`core.hooksPath=.githooks`，安装时刻 19:39 < 提交时刻 19:44）。是否使用 `--no-verify` 不可观测，但**机制上 hook 不可能拦住该提交**——这正是 B-01 得以落地的通道。
- **影响**：BK-0048 的核心承诺「让忘记跑门禁不再是失败模式」在最常见的一类改动（改被锚定的代码/规程文件）上失效，红灯被推迟到下一次提交才出现，且以「阻断他人」的形式暴露。
- **修复（择一或组合）**：① hook 内对 `git diff --cached --name-only` 命中的锚点文件按「mtime/hash 与 HEAD 不一致」直接判 drifted；② 用 `git stash create`/临时索引导出提交快照后再跑门禁；③ 把漂移判定移交服务端（post-receive / CI），hook 只做快速子集并明确声明「不覆盖漂移」。

### B-03 [P2] 体量门禁对扩展名大小写失明（`.MD`/`.markdown` 完全逃逸）

- `_size_docs`（audit-doc-health.py:319-327）用 `rglob("*.md")`，Linux 下大小写敏感。实测把超限文档改名为 `upper.MD` 后**扫描 0 篇、issues 0**。
- 影响：一次改名即让文档脱离全部体量约束（同时也脱离元数据/孤儿计分，属跨门禁逃逸面）。
- 修复：按 `f.suffix.lower() in {".md", ".markdown"}` 枚举；或对 `rglob("*")` 过滤后缀。

### B-04 [P2] `splitlines()` 按 Unicode 行分隔符切分，长单行可被 U+2028 等切碎

- `_measure_doc`（:280-291）用 `text.splitlines()`，该方法在 `\v`、`\f`、`\x1c-\x1e`、`\x85`、`\u2028`、`\u2029` 处同样断行。实测 600 + U+2028 + 600 的一行被判为 `longest_line=600`，绕过 1000 字符上限。
- 修复：`text.split("\n")`，再对每行 `rstrip("\r")`。

### B-05 [P2] 不可读文件 fail-open：OSError → 0 字节视为达标

- `_measure_doc` 的 `except OSError: return {"bytes": 0, ...}`（:283-285）。实测 `chmod 000` 后 `{bytes:0, longest_line:0}`，门禁静默放行。
- 影响：权限错配 / IO 故障 / 竞态删除时门禁给出假绿；同一缺陷也让「读不了的大文档」永久隐形。
- 修复：返回 `None` 并生成 issue「无法度量（<errno>）」，或 fail-closed 计为超限。

### B-06 [P2] 基线可被预置条目投毒；删除后的残留条目永不清理

- 实测：基线预置 `future/plan.md: {bytes: 1e9, longest_line: 1e6}`，再落 120 KB 文档 → **issues=0**，永久豁免。
- 实测：基线含 `a/gone.md` 而磁盘无此文件 → issues=0、warnings=0，**无任何「基线残留」提示**；只有下一次 `--write-size-baseline` 才会顺带清掉。
- 修复：`load_size_baseline` 之后按 `_size_docs` 实存集合求差，残留项产出 warning；对「基线键在磁盘不存在」直接拒绝该条记录（fail-closed 到「新增超限」）。

### B-07 [P2] 基线值类型畸形未捕获 → 裸 traceback

- `load_size_baseline`（:294-317）只在 `json.loads` 外层捕获 `ValueError`；内层 `int(metrics.get("bytes"))` 未防护。实测 `{"bytes":"abc"}` → `ValueError: invalid literal for int() with base 10: 'abc'`，整份体检崩溃。
- 影响：AC-5 只覆盖「JSON 语法损坏」，值类型损坏走的是崩溃路径；虽然退出码非零（fail-closed），但没有诊断、且把与体量无关的提交一并阻断。
- 修复：`try/except (TypeError, ValueError)` 包裹转换，降级为 `baseline_status="corrupt"` 并按「无基线」处理（与 truth 轴的 corrupt 语义对齐）。

### B-08 [P2] `--write-size-baseline` 是一键棘轮复位，无任何守卫

- 实测（`/tmp/e2e`）：新增 120 KB 文档 → 门禁 REJECT → 执行 `--write-size-baseline` → 基线写入 `huge.md: 120107/1200` → 再体检体量项转 PASS。
- RFC-0008 §7 声称「基线值只降不升（增长即阻断）」，但该 CLI 让「升」变成一条命令；唯一约束是提交信息里人工登记原因。
- 修复：写入时读取旧基线，拒绝「比旧值更大」的条目（除非显式 `--force`）；或在 CI 对基线 diff 做单调性校验。

### B-09 [P2] hook 的 `PYTHON_BIN` 语义 fail-open

- 缺失 → `exit 0`（stderr 有提示，非静默但放行）；`PYTHON_BIN=true` → `exit 0` 整体旁路（实测）。
- Windows Git Bash：无 `python3` 时静默跳过；若命中 Microsoft Store 的 App Execution Alias 存根，则返回 9009 被当作「门禁未通过」，给出误导性阻断。
- 修复：缺失时 `exit 1`（或 `--allow-missing-python` 显式降级）；执行前用 `"$PYTHON_BIN" -c 'import sys' ` 探测解释器真伪。

### B-10 [P2] G-02 字面匹配产生假 GAP，并派生事实错误的 backlog 卡片

- `g02_rfc_has_plan`（check-golden-tasks.py:66-71）只认字符串「落地计划」。RFC-0003 第 18 行用的是 `**实施计划请查阅**` 且链接有效，仍被判 GAP。
- 连带：BK-0053 标题「3 篇 rfc 无落地计划链接」与实测不符——RFC-0001/0002 确实没有任何指向自身计划的链接，RFC-0003 有。
- 修复：等价标签集（落地计划|实施计划|实施计划请查阅），或直接解析控制头中指向 `project/plans/` 的任意链接。

### B-11 [P2] G-20 豁免按目录而非按头部类型，豁免面 59/105 且 articles 未登记

- `g20_all_have_header`（:204-219）整目录跳过 `decisions`/`backlog`/`reference/articles`。实测在这三处各放一个**零元数据**文件后，G-20 仍报 `46 篇均有控制头`。
- 代码注释称「GOVERNANCE §4.1 已登记」，实际 GOVERNANCE 只登记了 backlog 的**状态机**豁免（V1.9.1 行），没有登记控制头豁免；`reference/articles` 的豁免在全库文档中**零登记**。
- 修复：把豁免从「目录」改为「头部白名单」（`文档控制信息` | `提案元数据` | `ADR 控制元数据` | YAML frontmatter），并对 articles 补登记。

### B-12 [P2] G-14 可被目录删除/改名空过，且只扫顶层

- 实测 `rmtree(project/backlog/active)` → `('pass','无活跃待办')`。`active.glob("*.md")` 亦不递归，嵌套卡片不可见。
- 修复：目录缺失但 `project/backlog/index.md` 仍声明活跃卡片时判 FAIL；改用 `rglob("*.md")`。

### B-13 [P2] 新增审查归档目录会把 G-17 打红（报告交付与门禁耦合）

- 实测：新建 `docs/project/reviews/2026-11-22-batch-gates/` 且只放报告 → `('fail','缺索引: 2026-11-22-batch-gates')`。
- **本报告的直接后果**：受「禁止改除该报告外的文件」约束，本目录**未创建 README.md**，因此在本次落盘后运行 `check-all.py`，第 6 项将由绿转红。这不是本轮代码缺陷，而是 B-13 的现场证明；归档流程须由脚手架同时生成带控制头的 README。
- 修复：G-17 对「仅含报告、无 README」降级为 GAP，或由 `prepare-review-context.py` 强制 scaffold README。

### B-14 [P3] 断言普遍是存在性检查，与「可回答性」命名有落差

- G-07/G-16/G-17 仅判文件存在；G-12/G-13 只要有任意一篇即 PASS；G-03 只要任意一篇 RFC 含 `C-n` 即 PASS；G-06 的「必须|禁止」子串在规则文档里近乎恒真；G-10/G-11 只要任意一篇达标即 PASS。
- 脚本 docstring 已诚实声明「测的是知识可检索性，不是 agent 答题成功率」，但门禁命名与 GOVERNANCE §3 的表述仍偏强。建议在工具表注明「存在性/可定位性」边界。

### B-15 [P3] 契约与登记缺口（体量门禁）

- RFC-0008 未登记豁免面：实测 107/192 篇受检，`project/reviews/**`（79 篇）、`_llms/**`（5 篇）、`AGENTS.md` 全部跳过；GOVERNANCE 的豁免表也只列了控制头/孤儿两类，未含体量。一份 10 MB 的审查报告对体量门禁完全隐形。
- `max_lines` 未暴露 CLI，而 RFC 称「三个阈值均可配」；`--max-doc-bytes 0` 因 `or` 回落静默变成 65536（:1183-1190）。
- `check-all.py` docstring 与 usage 写「五道门禁」（:6、:10），实际 6 道，SKILL.md 写「六道」——交付物内部口径不一致。

### B-16 [P3] 测试覆盖缺口（恰好落在本轮攻击点上）

- `test_write_baseline_roundtrip` 只断言「超限文档在基线里」，**未断言达标文档不在**——正是「削弱棘轮」这一问的回归盲区。
- `test_check_all` 无超时/失败传播用例；超时行为经 `TimeoutExpired ⊂ SubprocessError` 保证，实测类关系成立，但无红灯保护。
- `check-golden-tasks` 只有形状与退出码测试，无逐条断言单测 → B-10 的假 GAP 无法被红灯捕获。

---

## 5. 裁决

```text
Blockers（仅计 P0/P1）: 2
  B-01 [P1] HEAD 门禁红灯（真值轴 drifted）+ 自带测试 2 例失败
  B-02 [P1] pre-commit hook 对本次提交引入的漂移结构性失明
P0 阻断项: 0（体量门禁 AC-1…AC-7 全部成立）
P2/P3 记录: 14 项（B-03…B-16）

裁决: 阻断（不准予交付）
```

**准予条件（全部满足后可复审）**：
1. 修复 B-01：设计书 `复核于` 对齐 `9d03d22`，`check-all.py --full` 六项全绿 + pytest 0 failed（须出示原始输出）。
2. 修复 B-02：hook 具备「提交快照/索引」视角，或明确降级其承诺并在 GOVERNANCE §5 登记该盲区；给出「改锚点文件后 hook 能拦住」的 A-B 反证。
3. 建议同批消化 B-03/B-05/B-07（同一函数内三处 fail-open/崩溃，改动面小、回归成本低），B-06/B-08 至少登记为 backlog 并在 RFC-0008 §7 修订「只降不升」的机械保证。

---

## 6. 残留风险（≤3）

1. **体量门禁覆盖率 56%**：reviews（79 篇）/_llms（5 篇）/AGENTS.md 免检且未在 RFC-0008 登记；报告类产物可无上限增长，棘轮只约束知识文档。
2. **断言层仍是「存在性」检查**：GAP/FAIL 的边界靠人工判断，结构缺陷（如 RFC 缺计划链接）可持续沉淀为 backlog 而不被阻断；B-10/B-12 已给出两条可复现的空过通道。
3. **棘轮与 hook 都依赖人工纪律**：`--write-size-baseline` 一键复位、`PYTHON_BIN=true` 与 `--no-verify` 可整体旁路，且当前无服务端强制点；一旦 CI 缺位，「门禁自动化」的保证退化为本地提示。

---

## 7. 边界声明

- 全程只读：未修改任何被跟踪文件，未执行任何 git 写操作（无 add/commit/checkout/reset）；`/tmp` 下的副本（`/tmp/e2e`、`/tmp/gdocs`、`/tmp/nest`、`/tmp/repo-link`）为一次性实验环境。
- 所有结论均来自实跑输出或代码定位（`文件:行`），未采信实现者陈述；`/tmp` 实验与真实树结论已交叉验证（§1.5 与 §3.1 的数值一致）。
- 本报告自身未携带文档控制头（`docs/project/reviews/**` 按 RFC-0001 逐字归档，禁止添加控制头）；该目录缺少 README.md 的后果见 B-13。
