# R1 红队审查报告 · wave2b-dual-round-review-v3 · `c9eed38..c7f5f79`

> **审查轮次**: delta-r1
> **审查模式**: DELTA_RE_LOOP（Scoped Delta 定向再循环复核）
> **基线**: `c9eed38..c7f5f79`（全量 `git diff c9eed389b4313d6ad9f666fc4b0cd1932a61d624...c7f5f79ee7377bfe3c77e923856e873037f97733`，7 files changed, +430 / -241；同步核对整体分支 `a31de61...c7f5f79`，27 files changed, +949 / -1,589）
> **Previous Blockers**: `[R1-1, R1-2]`（同批建议收口：`[R1-3, R1-4]`；前序 R2 终审裁决书 [r2-a31de61..c9eed38.md](./r2-a31de61..c9eed38.md)，实测 SHA256 `1cad3827450c8c39b77dbe409787f9d7345598447743be6d0e70352c1dbb391a`，前 12 位 `1cad3827450c` 与归档索引一致）
> **Write-Scope（唯一授权写入路径）**: `docs/project/reviews/2026-11-24-wave2b-dual-round-review-v3/delta-r1-c9eed38..c7f5f79.md`

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **本质根因修复**。提交 `c7f5f79` 精准对照前序 R2 裁决书维持的两项 P1 阻断项（`R1-1`、`R1-2`）与两项同批收口建议（`R1-3`、`R1-4`）完成闭环修复，未引入投机性抽象或越界重构。
- **Previous Blockers 与同批收口项回源核验**:
  1. **`R1-1`（P1 阻断项）根治核验 — 已彻底闭合**：
     - `skills/dual-round-review/scripts/check-review-report.py:327-344` 新增 `_stage_and_base()` 与 `_display_key()`，将轮次配对键由单纯 `<base>` 升级为 `(stage, base)`（严格区分 `("initial", base)` 与 `("delta", base)`），彻底消除了 `--working`、`--staged` 或共享 `BASE_SHA` 下首轮 `r2` 替含缺陷 `delta-r1` 顶包放行的结构性碰撞；
     - `:488-585` 通过 `_AlignmentData`、`_collect_alignment_data()`、`_check_cross_round_pairing()` 与 `_check_id_alignment()` 实现按 `(stage, base)` 校验 `r2_count >= nonempty_r1_count`（阻断同基线 2 份含缺陷 `delta-r1` 仅配 1 份 `delta-r2`），且将 `unparsed_errors` 改为按文件独立记录并无条件在 `r2_files` 非空时报错（消除原 `:490-496` 因嵌套在 `if not round_r1:` 下导致同键正常兄弟文件掩盖解析失败报告的控制流缺陷）；
     - 真正 0 缺陷的 `delta-r1`（无论 `--working` 或普通提交区间）在 `_collect_alignment_data()` 中不计入 `nonempty_r1_count`，Scoped Delta 免 `delta-r2` 过 `--require-verdict=PASS` 放行路径保持完整。
  2. **`R1-2`（P1 阻断项）根治核验 — 已彻底闭合**：
     - `skills/dual-round-review/scripts/check-review-report.py:93,271-324` 引入 `_TABLE_SEP_RE`、`_section_pipe_blocks()` 与 `_has_unparsed_id_rows(..., strict_table=bool(r2_files))`；
     - 当 `r2_files` 非空（`strict_table=True`）时，凡 `## 4. 潜在缺陷清单` 抽取到 0 个契约 ID 且存在「分隔行后有非空数据行」或「无分隔行但有 ≥ 2 条非空管道行」的表格块，一律按单文件 fail-closed 报错；
     - 合法零缺陷空表（仅有表头+分隔行、或附纯空 ASCII 管道行 `| | |` / 单格全角空白 `|　|`）、纯散文（0 管道行）、单行管道备注、Light 模式（`r2_files == []`，如 `2026-10-09-batch-b-llms-integrity`）及多表格共存且可抽到 ID 的归档（如 `2026-10-09-batch-a-archive-exemption`、`2026-10-09-batch-d-identity-contract`）全部 `0` 误伤。
  3. **`R1-3`（P2 同批收口）核验 — 已精准闭合**：
     - AST 逐函数实测 `check-review-report.py` 全部新增/修改函数均 ≤ 40 行（`_section_pipe_blocks` 25 行、`_has_unparsed_id_rows` 27 行、`_stage_and_base` 14 行、`_display_key` 2 行、`_collect_alignment_data` 40 行、`_check_cross_round_pairing` 30 行、`_check_id_alignment` 13 行、`_check_orphan_reports` 26 行、`main` 46 行；仅未受波及的历史既有 `_check_reports` 为 51 行，R2 已豁免澄清）；
     - 测试文件拆分为 `skills/dual-round-review/tests/test_check_review_report.py`（944 行）与新建 `skills/dual-round-review/tests/test_v3_surface_contract.py`（170 行），均低于单文件 1,000 行上限；
     - `test_check_review_report.py:474-478` 已将旧 4 列 R2 夹具重命名为 `LEGACY_FOUR_COL_R2_TABLE_HEAD` 并修正注释；`test_v3_surface_contract.py:31-46,112-170` 已覆盖 R1/R2 区块常量与模板一致性、R2 三源（`templates/r2-report.md:14`、`references/round-2-meta-architect.md:106`、`references/verdict-rubric.md:79`）7 列表头逐字对齐、`SKILL.md` 体积预算（实测 105 行 ≤ 130 行、9,846 字节 ≤ 12 KB）与 `description` 长度（≤ 500 字符）、`*.md` 围栏配对以及 5 项退役 `Artifact Review` 关键词在非 `tests`/`__pycache__` 全目录文件中的防回流扫描（且实测注入 `yaml = None` 降级分支同样通过）。
  4. **`R1-4`（P3 同批收口）核验 — 已精准闭合**：
     - `skills/dual-round-review/SKILL.md:91-93` 明确区分首轮 R1 过结构门禁进 R2 与 Scoped Delta（含缺陷 `delta-r1` 待 `delta-r2` 落盘后再一并过机械门禁；0 缺陷直接收口放行并过 `--require-verdict=PASS`）；
     - `skills/dual-round-review/scripts/prepare-review-context.py:507-508` 已补充「必须使用全角中文括号」并明示拒绝半角括号，与 `check-review-report.py:104` 及 `templates/review-archive-index.md:17` 一致；
     - `check-review-report.py` 模块 docstring（`:9-26`）`1)–10)`、`USAGE`（`:69-76`）校验项 `8–10`、`:221` 注释「第 9 项」及 `:619` `_check_orphan_reports` `10)` 与 `templates/review-archive-index.md:44`、`docs/explanation/architecture/dual-round-review-design.md:93` 的「10 项校验」连续对齐。
- **过度设计审计**: 解法克制简洁，纯标准库实现，未引入外部 Markdown 解析依赖或过度抽象；`docs/project/changelog.md:42` 与 `docs/explanation/architecture/dual-round-review-design.md:93` 同步到位。

## 2. 运行时与 SSR/沙盒安全推演

本节未激活（非运行时/客户端适用改动）。

补充核查本次修改的离线 CLI 脚本边界：`check-review-report.py` 新增函数仅在已由 `_is_safe_filename()`（`:177-183`）校验的单层文件名上调用只读 `_read_lines()`（`UTF-8` + `surrogateescape` + `newline=""`）；全部新增正则（`_TABLE_SEP_RE`、`_FENCE_RE` 等）均为无嵌套量词线性匹配，无 ReDoS、无子进程拼装、无目录写入副作用。`prepare-review-context.py:507-508` 仅更新脚手架文本字面量，不改变路径拼接与 Write-Once 保护逻辑。

## 3. 红队攻击路径推演

未构造出确凿攻击路径。

以下为针对本次 Delta 提交（`c9eed38...c7f5f79`）执行的只读渗透与全仓回归验证实证（均在进程内存临时目录 `tempfile.TemporaryDirectory()` 或只读命令下完成，未改写工作区文件）：

1. **`R1-1` 阶段与数量配对渗透测试（全数拦截）**：
   - `--working`（`r1-working..aaa1111` + `r2-working..aaa1111` 配 `delta-r1-working..bbb2222` 含 `R1-1` 且无 `delta-r2`）、`--staged`（`staged..aaa1111` 配 `staged..bbb2222`）及共享分支基线（`aaa1111..bbb2222` 配 `aaa1111..ccc3333`）跑 `check-review-report.py --require-verdict=PASS` 均返回 **`rc=1`**（命中「轮次未闭环，禁止靠他轮 R2 顶包放行」）；
   - 同 `(delta, working)` 下 2 份含缺陷 `delta-r1` 仅配 1 份 `delta-r2` 返回 **`rc=1`**；
   - 同 `(delta, bbb2222)` 下 1 份正常闭环 `delta-r1`/`delta-r2` 混合 1 份未解析出 ID 的 `delta-r1-bbb2222..ddd4444.md` 返回 **`rc=1`** 且准确点名异常文件名；
   - `--working` 与普通提交区间下的 0 缺陷空表 `delta-r1`（无 `delta-r2`）过 `--require-verdict=PASS` 均返回 **`rc=0`**。
2. **`R1-2` 畸形表格与边缘 Markdown 渗透测试**：
   - 构造 `r2_files` 非空场景下的 `DELTA-1`、`D2-1`、变体表头 `| ID |`、`  | ID |`（前导空白缩进）、无分隔行仅 2 行管道表格、最小双连字符分隔行 `|--|--|`、首表空表+次表 `| ID |` 含 `DELTA-1`、以及 CRLF（`\r\n`）换行文件，均 100% fail-closed 返回 **`rc=1`**；
   - 合法空表（标准表头+分隔行、CRLF 空表、居中 `:---:` / `--` 分隔行、双分隔行空表、`| | |`、`|　|`、`|	|	|`）均正常放行返回 **`rc=0`**；
   - 边界口径说明（非本次引入缺陷，属既有行首管道正则启发式边界）：`check-review-report.py` 沿用自 V2.1.0 起的「`|` 起始行表格」约定（与 `_ledger_rows` / `_section_ids` 一致），故无前导 `|` 的表格、纯散文列表或数据行后才出现分隔行的非标准块不触发表格分支（安全避免散文含 `|` 被误杀）；另 `:313` 的 `.strip("|" + SPACE).strip()` 在 2 列及以上纯全角空白填充行（如 `|　|　|`）会因外层截断保留中间 `|` 而表现为安全的 fail-closed（模板 `r1-report-code.md:29` 已明文禁止 0 缺陷表保留任何数据行，且实测全仓 21 个真实归档 0 例触发）。
3. **全仓归档与门禁基线独立复验**：
   - 遍历 `docs/project/reviews/` 全仓 21 个归档目录执行 `check-review-report.py`：16 个非冻结历史归档与 `2026-11-24-wave2b-dual-round-review-v3` 全部 **`rc=0`**，4 个 `2026-11-22-*` 冻结历史归档维持 **`rc=1`**；
   - `python3 skills/doc-governance/scripts/check-all.py --full`：**`rc=0`**（7 项门禁全部通过）；
   - `python3 skills/doc-governance/scripts/check-golden-tasks.py --root docs`：**`rc=0`**（`PASS 20｜GAP 0｜FAIL 0`）；
   - `python3 -m pytest skills/ -q`：**`rc=0`**（`548 passed in 63.41s`，一次测量）；
   - `python3 -m pytest skills/dual-round-review/tests/ -v`：**`rc=0`**（`129 passed in 9.32s`，一次测量）；
   - `python3 -m pytest skills/dual-round-review/tests/test_v3_surface_contract.py -v`：**`rc=0`**（`4 passed in 0.08s`，一次测量；强制 `yaml=None` 降级实测同样通过）。

## 4. 潜在缺陷清单

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|

## 5. 第一轮结论概要

- 分级统计：🔴 0 / 🟡 0 / ⚪ 0，无新增或残留缺陷，可按 Scoped Delta 规则直接收口放行（免派发 `delta-r2`）。
- 是否存在阻断项（P0/P1）：否（前序 R2 阻断项 `R1-1`、`R1-2` 均已从根因层面根治，同批建议 `R1-3`、`R1-4` 均已准确收口且无次生回归）。
- 本轮未取证的不确定性：无
