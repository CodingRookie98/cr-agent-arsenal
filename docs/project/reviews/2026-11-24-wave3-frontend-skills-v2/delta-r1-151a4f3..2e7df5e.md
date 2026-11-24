# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析
- **改动性质定性**: 本次 Scoped Delta 变更（`151a4f3..2e7df5e`，涉及 `3` 个文件、`+93 / -17`）定向修复 R1/R2 指出的 `R1-1`（P1 阻断项）及顺并的 `R1-2`、`R1-3`（P2 优化建议）：（1）在 `skills/frontend-qa-gate/scripts/check-qa-report.py` 中将严格子串占位校验 `_ok_str` 与自由文本整串模板校验 `_ok_text` 解耦，并在 `automated_assertions` 与 `human_signoff` 的 `status` 检查前补齐 `isinstance(st, str)` 守卫；（2）在 `skills/frontend-qa-gate/tests/test_frontend_qa_evidence_gate.py` 中补充尖括号自由文本放行、整串占位符/模板拦截及不可哈希 `status` 回归测试；（3）在 `skills/taste-driven-designer/tests/test_taste_designer_v2_surface.py` 中补充 `PyYAML` 缺失时的纯标准库 `_parse_frontmatter` 降级分支及对应单测。
- **物理与业务一致性**:
  - **R1-1 字段语义分层准确**：`check-qa-report.py:8,16-21` 保留 `PLACEHOLDER_RE = re.compile(r"<(?:[^>\s][^>\n]*)?>")` 服务于 `_ok_str`，用于结构化标识、URL、时间戳、日期与证据路径（`id` `L31-32`、`artifact.{name,url,commit,captured_at,probe_tool}` `L48`、`evidence` `L61`、`signed_at` `L138`）；同时引入 `FULL_PLACEHOLDER_RE = re.compile(r"^<[^>\n]+>$")` 服务于 `_ok_text`，用于自由文本字段（`steps` `L106`、`automated_assertions[].na_reason` `L110`、`item` `L133`、`signer` `L138`、`human_signoff[].na_reason` `L140`）。因 `[^>\n]+` 禁止内部出现 `>`，类似 `"<button> triggers <dialog> with focus"` 在首个 `>` 后不再匹配整串，得以放行；而 `qa-evidence-template.json` 中的 `"<Set viewport to 375x812, scroll to bottom, check scrollWidth <= innerWidth>"` 等未填模板仅末尾含 `>`，仍被精确拦截，且 `"shots/<v1.png>"` 类路径由 `_ok_str` 继续拦截。
  - **R1-2 类型前置与错误聚合一致**：`check-qa-report.py:108,136` 与同文件 `dom`（`L102`）、`verdict`（`L162`）保持同构守卫，将后续分支改为 `elif`，且在 `steps`/`item` 校验之后执行，非字符串 `status` 不会中断其余字段与区块的错误收集。
  - **R1-3 表面测试一致性**：`test_taste_designer_v2_surface.py:8-11,26-46` 采用与同仓 `test_frontend_qa_v2_surface.py`、`test_clarification_protocol_contract.py` 一致的 `try/except ImportError` + 键值降级解析及未加引号冒号（`unquoted colon`）陷阱检测。
- **过度设计审计**: 未引入 HTML 解析器、词法状态机或外部依赖；`check-qa-report.py` 全长 `209` 行（守住 `<= 210` 行预算，单函数最大 `30` 行 `<= 50` 行），`test_frontend_qa_evidence_gate.py` `282` 行（最大函数 `23` 行），`test_taste_designer_v2_surface.py` `124` 行（最大函数 `21` 行）。唯一权衡是 `_ok_text` 未拦截如 `"Step: <fill>"` 类仅在片段内出现占位符的自由文本及 `"<>"` 空尖括号，属无词法分析器前提下按 R2 裁决收敛的刻意边界；且 `passed` 断言仍受磁盘文件魔数与 `runtime_signals` 强制约束，不构成实质性门禁绕过。

## 2. 运行时与 SSR/沙盒安全推演
- **状态纯度与初始化安全**: `check-qa-report.py` 仅在模块顶层新增不可变编译正则 `FULL_PLACEHOLDER_RE`（`L8`），`_ok_text` 仅使用局部变量 `s := val.strip()`，无共享可变状态。`test_taste_designer_v2_surface.py:118` 通过 pytest `monkeypatch.setitem(globals(), "yaml", None)` 在单个测试内切换降级分支，夹具卸载时自动还原模块全局命名空间，不污染后续用例。
- **沙盒/权限边界与跨端安全**:
  - `_check_ev_file`（`check-qa-report.py:60-89`）继续通过 `_ok_str` 校验相对证据路径（`L61`），未放宽对 `"shots/<v1.png>"`、空字节、绝对路径、Windows 盘符、`..` 穿越与 symlink 逃逸的阻断。
  - `skills/taste-driven-designer/tests/` 在模拟移除 `PyYAML` 的独立环境下可无依赖通过全部测试。
- **生命周期与资源清理**: 本次变更未新增文件句柄、子进程或网络资源；`check-qa-report.py` 的 CLI 退出码语义（`0`/`1`/`2`）与错误聚合流保持不变。

## 3. 红队攻击路径推演
1. **R1-1 回归与模板绕过探测（已证伪）**:
   - **构造探针**: （a）合法 `qa-evidence.json` 在 `steps`、`na_reason`、`item`、`signer` 中混合注入 `"Check scrollWidth <= innerWidth and height > 0"`、多行 `"1. Click <button>\n2. Check <dialog> open && width <= 375 && height > 0"`、`"<300ms paint and no >2s freeze; <input> has <label>"`、`"No <img> or <picture> rendered"`、`"VoiceOver navigates <nav> -> <main>"` 与 `"Alice <alice@example.com>"`；（b）模板与未填项注入 `"  <fill steps>  \n"`、`"<reason>"`、`"\t<item>\t"`、`"<signer>"`、`"2026-<MM>-<DD>"`、`"http://localhost:<port>"`、`"shots/<v1.png>"` 以及仓库 `qa-evidence-template.json`。
   - **实测结果**: 合规报告在 `--require-verdict=PASS` 下返回 `Exit 0`；全部模板与片段占位探针均被 Fail-Closed 拦截返回 `Exit 1`。
2. **R1-2 非字符串与不可哈希 `status` 探测（已证伪）**:
   - **构造探针**: 向 `automated_assertions[0].status` 与 `human_signoff[0].status` 分别传入 `[]`、`["passed"]`、`{}`、`{"x": 1}`、`123`、`3.14`、`None`、`True`、`False`，同时刻意留空同条目 `steps`/`item` 以检验错误聚合是否继续。
   - **实测结果**: `_check_assertions`（`L108`）与 `_check_human`（`L136`）全部短路至 `"invalid status ..."`；`_validate`（`L155,157,168,169`）仅使用 `==` 比对未再次哈希 `st`；所有用例均返回 `Exit 1`、stderr 无 `TypeError` 或 `Traceback`，且并发报告 `steps missing` / `item missing`。
3. **R1-3 无 PyYAML 独立环境收集崩溃探测（已证伪）**:
   - **构造探针**: 通过 `sys.meta_path` 拦截 `yaml` 导入抛出 `ModuleNotFoundError` 后运行 `pytest skills/taste-driven-designer/tests/ -v`。
   - **实测结果**: 含 `test_frontmatter_links_and_budgets` 与 `test_frontmatter_stdlib_fallback_and_unquoted_colon_trap` 在内 `5 passed in 2.91s`（`Exit 0`），且未加引号冒号输入触发预期 `AssertionError("unquoted colon")` 拦截。

## 4. 潜在缺陷清单
| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|

## 5. 第一轮结论概要
- **分级统计**: 🔴 **0 个阻断项** / 🟡 **0 个优化建议** / ⚪ **0 个驳回项**
- **是否存在阻断项（P0/P1）**: **否**（`R1-1` 已从字段语义分层根治，顺并项 `R1-2` 与 `R1-3` 均已验证关闭，Scoped Delta 未引入次生回归）
- **本轮实测与未取证范围**:
  - `python3 -m pytest skills/frontend-qa-gate/ skills/taste-driven-designer/ -v` → `48 passed in 5.10s`（`Exit 0`）；
  - `python3 -m pytest skills/ scripts/ -q && python3 scripts/doc-gates/check-all.py --full` → `258 passed in 27.96s`，`断链`/`健康体检`/`可回答性`/`测试套件` 4/4 全通过（`Exit 0`）；
  - 模拟无 `PyYAML` 环境运行 `skills/taste-driven-designer/tests/` → `5 passed in 2.91s`（`Exit 0`）；
  - `git diff --check 151a4f33337848f4476486b74afbd2283ebd5dfc..2e7df5ee90e4734d8c0d90dc7d084e43ad17c4c7` 与 `python3 -m py_compile` → `Exit 0`；
  - 独立红队探针脚本（覆盖富尖括号自由文本、首尾空白占位符、`[]`/`{}`/`int`/`float`/`None`/`bool` 异常 `status`）→ 全部符合 Fail-Closed 预期；
  - 未取证范围：未卸载系统全局 `PyYAML` 包验证（采用 `sys.meta_path` 导入阻断模拟）；`258 passed` 与 `5 passed` 等耗时为单次实测。
