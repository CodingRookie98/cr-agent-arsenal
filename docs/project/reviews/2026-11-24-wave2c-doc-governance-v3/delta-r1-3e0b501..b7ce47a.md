# R1 红队审查报告 · wave2c-doc-governance-v3 · `3e0b501..b7ce47a`

> **审查轮次**: delta-r1
> **审查模式**: DELTA_RE_LOOP
> **基线**: `3e0b501..b7ce47a`（完整分支 `d63ee31..b7ce47a`，分支 `refactor/wave2c-doc-governance-v3`）
> **Previous Blockers**: `R1-1`、`R1-2`、`R1-3`、`R1-4`（同批顺并收口 `R1-5`、`R1-6`、`R1-9`）
> **Write-Scope（唯一授权写入路径）**: `docs/project/reviews/2026-11-24-wave2c-doc-governance-v3/delta-r1-3e0b501..b7ce47a.md`

## 1. 第一性原理与本质溯源分析

- **改动性质定性**: **本质根因修复（Root-Cause Fix）+ 契约/文案同步收口**。本次 Delta（`3e0b501..b7ce47a`）共改动 8 个文件（`+161 / -34` 行），未引入外部依赖或投机性抽象层，逐一从底层语法、优先级、路径解析与映射数据结构根治了 `R1-1`~`R1-4` 阻断项并顺并收口 `R1-5`、`R1-6`、`R1-9`：
  1. **`R1-1` 幽灵围栏根因修复（`scripts/doc-gates/check-doc-health.py:25,43-59`）**：将 `_FENCE_RE` 扩展为捕获 info string（由 `r"^\s*(`{3,}|~{3,})"` 改为 `r"^\s*(`{3,}|~{3,})(.*)$"`），在 `_unfenced_lines` 中按 CommonMark 规则校验：仅当波浪线围栏或反引号围栏的 info string 不含反引号（`token[0] == "~" or "`" not in rest`）时才开围栏，且闭合围栏须同字符、长度 `>= fence[1]` 且剥除空白后无尾随字符（`not rest.strip()`），与 `skills/doc-governance/scripts/check-doc-links.py:19,26-42` 的配对逻辑完全对齐。行首 ```` ```inline``` ```` 不再触发永久幽灵围栏。
  2. **`R1-2` 控制头优先级、标记块空行与 BOM 根因修复（`scripts/doc-gates/check-doc-health.py:76-88,101-118,146-161`）**：
     - `_parse_yaml_frontmatter:78` 对首行执行 `lines[0].lstrip("\ufeff")`，`_parse_header_meta:149-150` 在 `body_start == 0` 时同样剥除首行 `\ufeff` 并置于 `_unfenced_lines` 之前，确保带 BOM 的 YAML、Quote 控制头、表格控制头与首行围栏均可正常识别；
     - `_parse_header_meta:156` 与 `_scan_marker_table:113` 恢复 `meta.setdefault`（与 `meta.setdefault(k, v)` 配合），锁定「YAML Frontmatter > 顶部 Quote > 控制头表格」优先级，彻底消除正文前 80 行引文对 YAML 状态的洗白或误杀；
     - `_scan_marker_table:103-117` 以 `is_quote_marker` 与 `in_table` 双态区分「`## 文档控制信息` 章节标题」与「`> **文档控制信息**` 引用块 / 已进入的表格」，并限制扫描窗口为 `block_lines[1:40]`：非引用块、尚未进入表格的空行允许跳过（从而正确抓取 `## 文档控制信息` 后先写 `> 备注` 再跟空行与表格的 `文档状态`），而一旦出自 `>` 标记块或已进入表格后的空行即触发 `break`，防止正文解释性表格越界污染控制头。
  3. **`R1-3` `--exclude` 根自指静默全跳修复（`skills/doc-governance/scripts/check-doc-links.py:206-208`）**：在 `_validate_exclude_prefixes` 校验 `candidate.relative_to(root_resolved)` 通过后追加 `if candidate == root_resolved:` 拦截（CLI 返回退出码 `2`，`scan_directory` 抛出 `ValueError`），与 `_is_excluded` 的父路径判定形成严密闭环——所有合法放行的 `candidate` 必为 `root_resolved` 的真子路径，从根源消灭 `共扫描 0 个 Markdown 文件` 的假绿。
  4. **`R1-4` 根外符号链接 `Superseded` 异常修复（`scripts/doc-gates/check-doc-health.py:233-270`）**：将 `superseded` 集合升级为 `Dict[Path, str]`（键为 `path.resolve()`，值为扫描阶段已基于根内逻辑路径计算好的 `rel_posix`），使 `_collect_superseded_warnings:266` 直接读取 `superseded[target]`，彻底消除对可能指向根外的已解析 `target` 再调用 `target.relative_to(root)` 所致的未捕获 `ValueError`。
  5. **同批顺并收口（`R1-5` / `R1-6` / `R1-9`）与文档契约/代码卫生**：
     - `R1-5`：`check-doc-health.py:26,195` 引入 `_INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)")` 对齐 `check-doc-links.py:18`，消除双反引号内含单反引号跨度导致的虚假 `Active 引用 Superseded` 警告。
     - `R1-6`：`check-doc-health.py:164-189` 对 `取代于` 先剥 `#` 与 `?`，再执行 `urllib.parse.unquote`；在任何路径拼接前先拦截 `\x00` 空字节，并对编码前后（`raw_part` 与 `part`）统一校验绝对路径/盘符/协议头，再行深度预算与 `resolved.relative_to(root)` 检查；同时 `docs/GOVERNANCE.md:117`、`docs/how-to/run-doc-gates.md:84` 与 `docs/how-to/troubleshoot-doc-governance.md:103` 已统一修正为「文档根（`--root`，如 `docs/`）内」。
     - `R1-9`：`docs/explanation/architecture/doc-governance-design.md:58` 已对齐实存模板 `change-registration.md`（经核查 `skills/doc-governance/templates/` 仅存该文件）；`docs/how-to/run-doc-gates.md:74` 与 `docs/how-to/troubleshoot-doc-governance.md:98` 的报错示例已与 `check-doc-health.py:208,240,327` 实际输出前缀 `❌ 体量超限 [...]` / `❌ 文档状态非法 [...]` 一致。
     - **代码规模与公私边界**：AST 实测 4 个修改/新增的 Python 文件总行数均远低于 `1,000` 行，全部函数/测试函数长度均 `<= 35` 行（阈值 `<= 50`）：`check-doc-health.py` 共 `335` 行（最长函数 `_scan_docs` 30 行）、`check-doc-links.py` 共 `347` 行（最长函数 `scan_directory` 34 行）、`test_check_doc_health.py` 共 `288` 行（最长 28 行）、`test_check_doc_links.py` 共 `245` 行（最长 35 行）；`skills/doc-governance/` 11 个受跟踪文件非测试目录下无个人绝对路径、个人真名、具体模型名及已退役私有关键词。
- **过度设计审计**: **无过度设计**。所有修复均采用标准库原生字符串/正则/路径集合操作，函数简短直接，未引入外部 Markdown AST 解析库或多余抽象层。

## 2. 运行时与 SSR/沙盒安全推演

本节未激活（非运行时/客户端适用改动）。

针对本次 CLI 工具变更，已完成以下只读沙盒、路径编码与文件系统边界复现核查：
- **CLI `--exclude` 沙盒边界（`check-doc-links.py:189-210`）**：在独立临时目录构造含断链 `[broken](./missing.md)` 的根与子目录，并创建指向根自身的符号链接 `self_sym -> .`；实测 `--exclude` 传入 `.`、`./`、`sub/..`、`dir/../.`、`../<root_name>`、`self_sym`（含单独传参及与 `--exclude sub` 组合传参）在 CLI 下均返回 `rc=2`（stderr 含 `根目录自身`），直接调用 `scan_directory()` 均抛出 `ValueError`；合法 `--exclude project/reviews` 与 `--exclude sub/` 仍正常排除并准确扫描剩余文件。
- **URL 编码与空字节注入边界（`check-doc-health.py:164-189`）**：实测 `取代于` 传入 `%2e%2e/outside.md`、`%2fetc%2fpasswd.md`、`./bad%00.md`、`%252e%252e/x`、`%252e%252e/outside.md`、`https%3a//evil.com/a.md`、`C%3a\a.md`、`%5cetc%5cpasswd.md`、`a%5c..%5c../outside.md`、`./new%2f..%2f..%2foutside.md`、`./%FF.md`、`%ZZ.md`、`?v=1`、`#sec` 均确定性返回 `rc=1` 且 stderr 无 `Traceback`；合法 `./my%20new.md?v=1#sec` 与 `./my%20new.md#sec?x=1` 返回 `rc=0`。
- **字符集 / CRLF / UTF-8 BOM 边界（`check-doc-health.py:35-40,78,149-150`）**：实测 `\ufeff---\r\n文档状态: Deprecated\r\n---\r\n` 与 `\ufeff` 前导的无 YAML Quote / 表格 / 围栏文档均按预期判定，无吞字符或解析逃逸。
- **符号链接跨根边界（`check-doc-health.py:180-184,244,265-269`）**：根内指向根外 `Superseded` 目标的符号链接被 `Active` 文档引用时无 `ValueError` 崩溃并正常输出警告；反之 `Superseded` 的 `取代于` 指向「位于根内但实际指向根外」的符号链接时，L182 `resolved.relative_to(root)` 拦截为 `状态机违规`（`rc=1`）。

## 3. 红队攻击路径推演

针对本次 Delta 变更（`3e0b501..b7ce47a`）涵盖的全部阻断项与顺并修复点执行独立只读渗透构造，**未构造出确凿攻击路径**。已验证的对抗尝试及收敛表现如下：
- **围栏状态机绕过尝试（针对 `R1-1`）**：构造行首 ```` ```inline``` text ````、含反引号 info string 的 ```` ```foo`bar ````、4 反引号嵌套 ```` ````python ```` 含 ```` ``` ````、带说明的 `~~~python` 内嵌 `~~~not-closing` 及缩进闭合行 `   ~~~   ` / `   ```   `、短闭合 `~~~` 试图提前结束 `~~~~python` 共 8 组用例，全部与 CommonMark 围栏语义一致，`Deprecated` 状态无一逃逸且围栏内示例无误报。
- **控制头优先级与结构混淆尝试（针对 `R1-2`）**：构造带 BOM 的 YAML `Deprecated` 企图用正文 `> - **文档状态**: Active` 洗白、合法 YAML `Active` 正文附 `> - **文档状态**: Deprecated` 诱发误杀、合法 YAML `Active` 正文前 40 行附无 `说明` 列名的表格诱发误杀、`## 文档控制信息` 下接 `> 备注` + 空行 + 表格、`> **文档控制信息**`（及含 `> - **文档状态**: Active`）后接空行 + 正文表格、以及 `## 文档控制信息` 后接双表格共 11 组用例，全部精确命中或豁免；确认 `is_quote_marker` 与 `in_table` 边界未出现漏扫或误扫。
- **`--exclude` 变形全跳尝试（针对 `R1-3`）**：覆盖 `.`、`./`、`./.`、`sub/..`、`dir/../.`、`a/b/../..`、`../<root>` 与根内指向自身的符号链接，全部在入口校验即 fail-closed（`rc=2` / `ValueError`）。
- **符号链接与内联代码跨度尝试（针对 `R1-4` / `R1-5`）**：覆盖根外符号链接 `Superseded` 被引用、根内符号链接试图将 `取代于` 越出根目录、双反引号包裹单反引号及 `[old](./old.md)` 同行混合真实链接等场景，行为均与契约一致。
- **全仓实跑门禁与测试验证（分支终态 `b7ce47a`）**：
  - `python3 scripts/doc-gates/check-doc-health.py --root docs` → `rc=0`（`Active=80 Contested=0 Superseded=6`，`0 项阻断, 16 项警告`）；
  - `python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews` → `rc=0`（`共扫描 144 个 Markdown 文件`，`0` 断链）；
  - `python3 skills/doc-governance/scripts/check-doc-links.py --root skills/doc-governance` → `rc=0`（`共扫描 8 个 Markdown 文件`，`0` 断链）；
  - `python3 scripts/doc-gates/check-golden-tasks.py --root docs` → `rc=0`（`PASS 20｜GAP 0｜FAIL 0`）；
  - `python3 -m pytest skills/ scripts/ -q` → `rc=0`（`299 passed in 20.56s`，一次测量，本机；较 R2 的 290 例新增 `test_check_doc_health.py` 5 例与 `test_check_doc_links.py` 4 例参数化用例）；
  - `python3 scripts/doc-gates/check-all.py --full` → `rc=0`（4/4 全绿）。
  - 历史归档不变性核查：`git diff --name-only d63ee31..b7ce47a -- docs/project/reviews/` 返回空输出（历史归档 0 改动）。

## 4. 潜在缺陷清单

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|

## 5. 第一轮结论概要

- 分级统计：🔴 0 / 🟡 0 / ⚪ 0
- 是否存在阻断项（P0/P1）：否（`R1-1`、`R1-2`、`R1-3`、`R1-4` 均已从根因层面验证消除，同批顺并收口的 `R1-5`、`R1-6`、`R1-9` 均已完成对齐，Delta 补丁未引入次生回归；按 Scoped Delta 规则可免派 `delta-r2` 直接收口放行）
- 本轮未取证的不确定性：Windows 原生分隔符（`\` / 盘符）与 Windows 控制台及符号链接权限分支在本 Linux 环境未实机验证（未验证）
