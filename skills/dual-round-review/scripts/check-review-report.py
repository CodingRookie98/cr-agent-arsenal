#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-review-report.py — 《审查归档》结构与证据校验器（dual-round-review 机械门禁）。

定位：校验「归档索引完整 / 报告全文在位 / 指纹一致 / 两轮区块齐备 / 稳定 ID 对齐」。
      不判断审查结论本身是否正确——结论正确性由两轮对抗与人类裁决负责。

契约（RFC-0001 §3.5）：
  1) README.md 存在且含「交付单元 / 归档根 / 终审裁决」三个必需字段，
     且 `**终审裁决**` 字段名在索引中**唯一**（BK-0004：命中数 ≠ 1 即缺陷）；
  2) 轮次台账登记的每个报告文件实际存在且非空；
  3) 台账登记的 SHA256 前 12 位与文件实际值一致（防篡改与转录漂移）；
  4) R1 报告 5 个必需区块齐备，且不得仅出现在围栏代码块内；
  5) R2 报告 3 个必需区块齐备（仅当台账含 R2 / delta-r2 行）；
  6) 稳定 ID 对齐：R2 裁决明细表出现的 R1-<n> 必须全部存在于 R1 缺陷清单；
     且该方向**按文件名基线逐轮配对**施加，并断言「R1 清单非空 ⇒ 同基线 R2 明细表非空」
     （BK-0003：全局 ID 并集会让早轮 R2 行替新一轮顶包，空明细表静默放行）；
  7) 可选 --require-verdict=PASS：终审裁决必须为「准予交付」，或「准予交付」+ 一个含数字的
   括号统计串（真实归档形态，BK-0043）；占位/否定/无统计后缀一律不成立；
  8) 写入形态合法性：台账每行的「写入形态」列必须存在且取值 ∈ {direct, transcribed}
     （RFC-0002 §3.5——该列是唯一能区分「子智能体直写原文」与「主智能体转录产物」的可审计属性）。
  9) 轮次列容错（2026-10-11）：台账「轮次」列允许带人类描述（如 `delta-r1 · 第6轮`），
     门禁按**前导标记值**解析；标记值之外的写法（如 `round-1`）仍判为未登记 R1。

用法: python3 check-review-report.py <归档目录> [--require-verdict=PASS]
退出码: 0 = 通过；1 = 结构/证据缺陷；2 = 用法错误
"""

from __future__ import annotations

import hashlib
import os
import re
import sys

R1_SECTIONS = (
    "## 1. 第一性原理与本质溯源分析",
    "## 2. 运行时与 SSR/沙盒安全推演",
    "## 3. 红队攻击路径推演",
    "## 4. 潜在缺陷清单",
    "## 5. 第一轮结论概要",
)
R2_SECTIONS = (
    "## 1. 元审查辩证质询",
    "## 2. 最终裁决明细表",
    "## 3. 终审放行结论",
)
CODE_R1_ID_SECTION = "## 4. 潜在缺陷清单"
INDEX_FIELDS = ("**交付单元**", "**归档根**", "**终审裁决**")
LEDGER_HEADER = "## 轮次台账"
R2_ID_SECTION = "## 2. 最终裁决明细表"

USAGE = """用法: check-review-report.sh <归档目录> [--require-verdict=PASS]

校验双轮审查《交付凭据归档》的结构与证据完整性。

选项:
      --require-verdict=PASS  要求索引「终审裁决」为「准予交付」，或「准予交付」+ 含数字的括号统计串
                        （交付门禁用法；BK-0043）
  -h, --help                  显示本帮助

退出码:
  0 = 通过；1 = 结构/证据缺陷；2 = 用法错误

校验项 8：台账「写入形态」列必须存在且取值 ∈ {direct, transcribed}
  （RFC-0002 §3.5；缺失或第三值均判失败）

校验项 9：台账「轮次」列按前导标记值解析——允许带人类描述（如 `delta-r1 · 第6轮`），
  但标记值须为 r1 / r2 / delta-r1 / delta-r2 之一（如 `round-1` 判为未登记 R1）。

归档目录结构（推荐默认根 docs/project/reviews/）:
  README.md                   归档索引（交付单元 / 归档根 / 终审裁决 + 轮次台账）
  r1-<base>..<head>.md        R1 报告全文
  r2-<base>..<head>.md        R2 终审裁决书全文
"""

SPACE = " \t\n\v\f\r"
_FENCE_RE = re.compile(r"^[ \t\v\f\r]*(?:```|~~~)")
# R1-01 回归（fail-open 修复）：原实现用 gawk `[[:space:]]`（UTF-8 locale 下含 U+3000 等
# Unicode 空白）识别「稳定 ID」表头；若此处退回 ASCII 字符类，U+3000 缩进表头将抽取不到任何
# 稳定 ID，进而使下方「R2 空裁决表禁止放行」保护整体静默跳过。故此处使用 Unicode 感知 `\s`。
_ID_HEADER_RE = re.compile(r"^\|\s*(?:R1\s+)?稳定 ID")
_ID_CELL_RE = re.compile(r"^D?R1?-[0-9]+$")
# 仅用于 fail-closed 守卫的「ID 记号」探测（宽松匹配，不要求单元格列结构规范）。
_ID_TOKEN_RE = re.compile(r"D?R1?-[0-9]+")
_ROUND_PREFIX_RE = re.compile(r"^(delta-r1|delta-r2|r1|r2)")
_MD_LINK_RE = re.compile(r"^\[[^\]]*\]\(([^)]+)\)$")
_NON_FILE_CHARS_RE = re.compile(r"[^A-Za-z0-9._-]")
_NON_HEX_CHARS_RE = re.compile(r"[^0-9a-fA-F]")
_HAS_ALNUM_RE = re.compile(r"[A-Za-z0-9]")
_VERDICT_PREFIX_RE = re.compile(r"^.*\*\*终审裁决\*\*:[" + SPACE + r"]*")
# BK-0043：真实归档写法是 `✅ **准予交付**（delta-r2：Blockers = 0；🔴 0 / 🟡 19 / ⚪ 0）`，
# 而该目录属 Write-Once 证据面不可改写——旧的「精确相等」使门禁对合法归档永久失效。
# 放宽面被**结构化收窄**：只接受「准予交付」紧跟**含阿拉伯数字的单个全角括号串**，且其后
# 不得再有内容。`未准予交付` / `准予交付?` / `准予交付（见下）` / `准予交付（…）尾巴` 仍全败。
_VERDICT_PASS_STAT_RE = re.compile(r"^准予交付（[^（）]*[0-9][^（）]*）$")


class _Exit(Exception):
    """用法错误/帮助请求导致的提前退出（携带退出码）。"""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        return handle.read()


def _read_lines(path: str) -> list[str]:
    """按 awk/grep 的记录语义切行：文件末尾换行不产生额外空记录。"""
    text = _read_text(path)
    if text == "":
        return []
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def _strip_fences(lines: list[str]) -> list[str]:
    """围栏剥离状态机：反引号与波浪号围栏**均**需识别（R1-4 回归）。"""
    kept: list[str] = []
    inside = False
    for line in lines:
        if _FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    return kept


def _heading_present(lines: list[str], section: str) -> bool:
    """区块判定：必须为**行首标题**，行内散文提及不算（R1-4 回归）。"""
    return any(line.startswith(section) for line in lines)


def _sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _sort_u(text: str) -> str:
    """复刻 `sort -u`（字节序去重）+ 命令替换（剥尾部换行）。"""
    lines = sorted(set(text.split("\n")), key=lambda value: value.encode("utf-8", "surrogateescape"))
    return "\n".join(lines).rstrip("\n")


def _has_line(text: str, value: str) -> bool:
    return any(line == value for line in text.split("\n"))


def _read_fields(line: str) -> tuple[str, str, str, str]:
    """复刻 `IFS=$'\\t' read -r round fname declared write_mode` 的字段切分语义。

    IFS 制表符属 IFS 空白字符：首尾制表符被忽略、连续制表符折叠为单一分隔，
    因此「登记列为空」与「写入形态列为空」在 read 之后可能整体左移（与 bash 逐字一致）。
    """
    parts = [part for part in line.strip("\t").split("\t") if part != ""]
    padded = parts[:4] + [""] * (4 - min(len(parts), 4))
    return padded[0], padded[1], padded[2], padded[3]


def _is_safe_filename(name: str) -> bool:
    """仅接受归档目录内的单层文件名（禁止路径分隔符、`.`/`..` 及非法字符）。"""
    if name in ("", ".", ".."):
        return False
    if "/" in name or "\\" in name:
        return False
    return _NON_FILE_CHARS_RE.search(name) is None


def _parse_report_filename(raw_file: str) -> str:
    """解析台账「报告文件」单元格：支持 `[label](target)` 链接、反引号与裸文件名。

    Markdown 链接只接受当前目录 `./<fname>` 或裸 `<fname>`；含 `../`、子目录、
    反斜杠或绝对路径的目标保留非空白文本交由后续安全校验显式拒绝，
    既防路径穿越也防返回空串导致静默跳过（fail-open）。
    """
    cell = raw_file.strip().strip("`").strip()
    match = _MD_LINK_RE.match(cell)
    if not match:
        return _NON_FILE_CHARS_RE.sub("", raw_file)
    target = match.group(1).strip()
    candidate = target[2:] if target.startswith("./") else target
    if _is_safe_filename(candidate):
        return candidate
    return "".join(target.split()) or "".join(cell.split())


def _ledger_rows(lines: list[str]) -> list[str]:
    """台账行解析（awk -F'|'）：输出 `轮次\\t文件名\\tSHA256\\t写入形态` 文本行。"""
    rows: list[str] = []
    for line in lines:
        if not line.startswith("|"):
            continue
        fields = line.split("|")
        raw_round = fields[1] if len(fields) > 1 else ""
        raw_file = fields[4] if len(fields) > 4 else ""
        raw_hash = fields[5] if len(fields) > 5 else ""
        # 末列为「写入形态」（R1-12 回归）：台账行以 | 结尾时存在空的尾随字段，故取 NF-1；
        # 未以 | 结尾时退回固定第 8 字段。这样结论单元格含裸竖线时也不会错位读取。
        if len(fields) >= 9:
            raw_mode = fields[len(fields) - 2]
        else:
            raw_mode = fields[7] if len(fields) > 7 else ""
        round_name = raw_round.strip(SPACE)
        # 轮次列容错（第 10 项）：允许人类记述带描述（如 `delta-r1 · 第6轮`），只取前导标记值。
        matched = _ROUND_PREFIX_RE.match(round_name)
        if matched:
            round_name = matched.group(0)
        # R1-02 回归：原实现经 `[[:space:]]`（UTF-8 含 Unicode 空白）归一化单元格，
        # 此处用 `str.strip()`（Unicode 感知）保持一致，避免 U+3000/U+2002 填充把合法归档误判非法。
        write_mode = raw_mode.strip()
        fname = _parse_report_filename(raw_file)
        declared = _NON_HEX_CHARS_RE.sub("", raw_hash)
        if not _HAS_ALNUM_RE.search(round_name):
            continue
        if fname == "":
            continue
        rows.append("\t".join((round_name, fname, declared, write_mode)))
    return rows


def _section_ids(path: str, header: str) -> str:
    """稳定 ID 抽取（BK-0003）：只认**该区块内「稳定 ID」契约表格的首列**。"""
    lines = _strip_fences(_read_lines(path))
    found: set[str] = set()
    in_section = False
    in_table = False
    for line in lines:
        if line.startswith(header):
            in_section = True
            continue
        if line.startswith("## "):
            in_section = False
        if not in_section:
            continue
        if not in_table:
            # 表头契约有**两种**合法形态：官方模板 `| R1 稳定 ID | …` 与历史归档自拟的
            # `| 稳定 ID (沿用 R1) | …`。只认「稳定 ID」字面前缀会让模板产出的合规 R2 报告被判成空明细表。
            if _ID_HEADER_RE.match(line):
                in_table = True
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        cell = re.sub(r"^\|\s*", "", line)
        cell = re.sub(r"\s*\|.*$", "", cell)
        # 稳定 ID 单元格可能被 markdown 强调记号包裹（`**DR-1**` / `` `R1-1` ``），
        # 剥掉强调记号后再匹配；否则合规报告会被误判为「空明细表」而 fail-closed。
        cell = cell.strip(SPACE).strip("*`_").strip()
        if _ID_CELL_RE.fullmatch(cell):
            found.add(cell)
    return _sort_u("\n".join(found))


def _has_unparsed_id_rows(path: str, header: str) -> bool:
    """区块内存在「稳定 ID」表头与含 ID 记号的数据行，但 `_section_ids` 未抽取到任何 ID。

    R1-01 回归：仅做「解析失败」判别——只有表头之后确实出现形如 `R1-1`/`DR1-1` 的数据行、
    却一个都没被捕获时，才 fail-closed（防止空白字符/列结构漂移让两向对齐与「R2 空表放行」
    保护整体静默跳过）。真正的零缺陷报告（表头后无数据行）不触发，避免误拒干净审查。
    """
    lines = _strip_fences(_read_lines(path))
    in_section = False
    header_seen = False
    for line in lines:
        if line.startswith(header):
            in_section = True
            continue
        if line.startswith("## "):
            in_section = False
        if not in_section or not line.startswith("|"):
            continue
        if not header_seen:
            if "稳定 ID" in line:
                header_seen = True
            continue
        if _ID_TOKEN_RE.search(line):
            return True
    return False


def _base_key(path: str) -> str:
    """轮次配对键 = 报告文件名的**基线**段（`<前缀>-<base7>..<head7>.md` 的 <base7>）。"""
    name = os.path.basename(path)
    if name.endswith(".md"):
        name = name[: -len(".md")]
    for prefix in ("delta-", "r1-", "r2-"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name.split("..")[0]


def _check_sections(path: str, label: str, sections: tuple[str, ...], messages: list[str]) -> int:
    """4)+5) 报告必需区块齐备（围栏剥离后仍齐备）。返回新增缺陷数。"""
    lines = _read_lines(path)
    errors = 0
    fence_count = sum(1 for line in lines if _FENCE_RE.match(line))
    if fence_count % 2 != 0:
        messages.append(
            f"错误: 围栏代码块未闭合（{label} 围栏标记 {fence_count} 个，应为偶数；"
            "嵌套围栏演示请避免行首标记）"
        )
        errors += 1
    body = _strip_fences(lines)
    for section in sections:
        if not _heading_present(lines, section):
            messages.append(f"错误: {label} 缺少必需区块（须为行首标题）: {section}")
            errors += 1
        elif not _heading_present(body, section):
            messages.append(f"错误: {label} 必需区块仅出现在围栏代码块内（无效）: {section}")
            errors += 1
    return errors


def _parse_args(argv: list[str]) -> tuple[str, str]:
    if argv and argv[0] in ("-h", "--help"):
        sys.stdout.write(USAGE)
        raise _Exit(0)
    require_verdict = ""
    positional: list[str] = []
    for arg in argv:
        if arg in ("-h", "--help"):
            sys.stdout.write(USAGE)
            raise _Exit(0)
        if arg.startswith("--require-verdict="):
            require_verdict = arg[len("--require-verdict="):]
        elif arg.startswith("-"):
            sys.stderr.write(f"错误: 未知选项 '{arg}'\n")
            sys.stderr.write(USAGE)
            raise _Exit(2)
        else:
            positional.append(arg)
    if len(positional) != 1:
        sys.stderr.write("错误: 需要且仅需要一个归档目录参数\n")
        sys.stderr.write(USAGE)
        raise _Exit(2)
    archive = positional[0]
    if not os.path.isdir(archive):
        sys.stderr.write(f"错误: 归档目录不存在: {archive}\n")
        raise _Exit(2)
    if require_verdict and require_verdict != "PASS":
        sys.stderr.write("错误: --require-verdict 目前仅支持 PASS\n")
        raise _Exit(2)
    return archive, require_verdict


def _collect_rows(index: str) -> list[str]:
    """1) 轮次台账切片 + awk 行解析（返回 `轮次\\t文件名\\tSHA256\\t写入形态` 文本行）。"""
    ledger_lines: list[str] = []
    in_ledger = False
    for line in _read_lines(index):
        if line.startswith(LEDGER_HEADER):
            in_ledger = True
            continue
        if line.startswith("## "):
            in_ledger = False
        if in_ledger:
            ledger_lines.append(line)
    return _ledger_rows(ledger_lines)


def _check_index(index: str, messages: list[str]) -> int:
    """1) 索引齐备 + BK-0004 终审裁决唯一性。"""
    errors = 0
    text = _read_text(index)
    for field in INDEX_FIELDS:
        if field not in text:
            messages.append(f"错误: 索引缺少必需字段: {field}")
            errors += 1
    # BK-0004：`**终审裁决**` 必须**唯一**（命中数 ≠ 1 即缺陷）。第 7 项按首匹配取值，
    # 索引顶部/围栏示例里的同名行会抢答真实字段。此处只数命中数，不引入任何语义解析。
    verdict_hits = sum(1 for line in _read_lines(index) if "**终审裁决**" in line)
    if verdict_hits != 1:
        messages.append(
            f"错误: 索引中 **终审裁决** 必须唯一（实测命中 {verdict_hits} 处；示例行/重复行不得抢答真实字段）"
        )
        errors += 1
    return errors


def _check_reports(
    archive: str, rows: list[str], messages: list[str]
) -> tuple[int, list[str], list[str], int]:
    """2)+3)+8) 报告在位非空、指纹一致、写入形态合法。返回 (报告数, R1, R2, 新增缺陷数)。"""
    errors = 0
    report_count = 0
    r1_files: list[str] = []
    r2_files: list[str] = []
    for row in rows:
        round_name, fname, declared, write_mode = _read_fields(row)
        if round_name == "":
            continue
        if not _is_safe_filename(fname):
            messages.append(
                f"错误: 台账登记的报告文件路径非法（仅允许当前归档目录内文件名）: {fname}（轮次 {round_name}）"
            )
            errors += 1
            continue
        rfile = os.path.join(archive, fname)
        if not os.path.isfile(rfile):
            messages.append(f"错误: 台账登记的报告文件不存在: {fname}（轮次 {round_name}）")
            errors += 1
            continue
        if os.path.getsize(rfile) == 0:
            messages.append(f"错误: 报告文件为空: {fname}（轮次 {round_name}）")
            errors += 1
            continue
        actual12 = _sha256_of(rfile)[:12]
        if declared == "":
            messages.append(f"错误: 台账缺少 SHA256 登记: {fname}（实际前 12 位 {actual12}）")
            errors += 1
        elif declared.lower() != actual12.lower():
            messages.append(f"错误: SHA256 指纹不一致: {fname} 登记 {declared}，实际 {actual12}")
            errors += 1
        if write_mode == "":
            messages.append(
                f"错误: 台账缺少「写入形态」登记: {fname}（轮次 {round_name}；取值须为 direct 或 transcribed）"
            )
            errors += 1
        elif write_mode not in ("direct", "transcribed"):
            messages.append(
                f"错误: 写入形态取值非法: {fname} 登记 '{write_mode}'（合法值仅 direct / transcribed）"
            )
            errors += 1
        report_count += 1
        lowered = round_name.lower()
        if lowered in ("r1", "delta-r1"):
            r1_files.append(rfile)
        elif lowered in ("r2", "delta-r2"):
            r2_files.append(rfile)
    return report_count, r1_files, r2_files, errors


def _check_id_alignment(r1_files: list[str], r2_files: list[str], messages: list[str]) -> int:
    """6) 稳定 ID 对齐（方向一：凭空引入；方向二：按基线逐轮配对）。"""
    errors = 0
    r1_ids_text = ""
    r2_ids_text = ""
    r1_by_base: dict[str, str] = {}
    r2_by_base: dict[str, str] = {}
    bases: list[str] = []
    unparsed_r1: set[str] = set()
    for path in r1_files:
        ids = _section_ids(path, CODE_R1_ID_SECTION)
        r1_ids_text += ids + "\n"
        key = _base_key(path)
        if ids == "" and _has_unparsed_id_rows(path, CODE_R1_ID_SECTION):
            # R1-01 回归：表头之后出现 ID 记号行却抽不到任何 ID（解析失败）时 fail-closed。
            unparsed_r1.add(key)
        if not r1_by_base.get(key, ""):
            bases.append(key)
        r1_by_base[key] = r1_by_base.get(key, "") + ids + "\n"
    r1_ids = _sort_u(r1_ids_text)
    for path in r2_files:
        ids = _section_ids(path, R2_ID_SECTION)
        r2_ids_text += ids + "\n"
        key = _base_key(path)
        r2_by_base[key] = r2_by_base.get(key, "") + ids + "\n"
    r2_ids = _sort_u(r2_ids_text)

    # 方向一：R2 裁决表出现的 ID 必须在 R1 缺陷清单中定义（防凭空引入）
    for identity in r2_ids.split("\n"):
        if identity == "":
            continue
        if not _has_line(r1_ids, identity):
            messages.append(f"错误: 稳定 ID 未在 R1 缺陷清单中定义: {identity}（出现在 R2 裁决明细表）")
            errors += 1

    # 方向二：**按基线逐轮配对**施加——R1 的每一条缺陷都必须被**同一轮**的 R2 定性。
    # 仅当台账登记了 R2 报告时适用——Light 模式为单轮红队，无 R2，不做此校验；
    # Full 模式下的 Scoped Delta（delta-r1 零缺陷且未派发 delta-r2）在下方 round_r1 为空分支放行。
    if not r2_files:
        return errors
    for key in bases:
        if key == "":
            continue
        round_r1 = _sort_u(r1_by_base[key])
        if not round_r1:
            if key in unparsed_r1:
                messages.append(
                    f"错误: 基线 {key} 的 R1 缺陷清单存在「稳定 ID」表头但未抽取到任何稳定 ID"
                    "（禁止空表放行；请检查表头/单元格的空白字符与列结构）"
                )
                errors += 1
            continue
        if not r2_by_base.get(key, ""):
            messages.append(f"错误: 基线 {key} 的 R1 报告未配同基线 R2 报告（轮次未闭环，禁止靠他轮 R2 顶包放行）")
            errors += 1
            continue
        round_r2 = _sort_u(r2_by_base[key])
        if not round_r2:
            messages.append(f"错误: 基线 {key} 的 R1 缺陷清单非空，但同基线 R2 裁决明细表为空（禁止空表放行）")
            errors += 1
            continue
        for identity in round_r1.split("\n"):
            if identity == "":
                continue
            if not _has_line(round_r2, identity):
                messages.append(
                    f"错误: R1 缺陷 {identity} 未出现在**同基线** R2 裁决明细表中（禁止静默吞并；误报须显式登记为驳回项）"
                )
                errors += 1
    return errors


def _check_verdict(index: str, require_verdict: str, messages: list[str]) -> tuple[int, str]:
    """7) 可选：终审裁决必须为「准予交付」。返回 (新增缺陷数, 通过注记)。"""
    if require_verdict != "PASS":
        return 0, ""
    verdict_line = ""
    for line in _read_lines(index):
        if "**终审裁决**" in line:
            verdict_line = line
            break
    # 精确字段值判定：剥离 "- **终审裁决**:" 前缀、首尾空白与可选 ✅ 后，值必须**恰好等于**「准予交付」。
    # 严禁子串包含判定——RFC §3.4 的占位符串与否定式串自身即含 PASS 词元（R1-1 回归）。
    value = _VERDICT_PREFIX_RE.sub("", verdict_line).strip(SPACE)
    if value.startswith("✅"):
        value = value[len("✅"):]
    value = value.strip(SPACE)
    # 加粗是排版而非语义：真实归档写作 `**准予交付**`，与裸值等价（BK-0043）
    value = value.replace("**", "").strip(SPACE)
    if not (value == "准予交付" or _VERDICT_PASS_STAT_RE.match(value)):
        shown = value if value else "未登记"
        messages.append(
            "错误: 终审裁决必须为「准予交付」，或「准予交付」+ 一个含数字的括号统计串"
            f"（实际: '{shown}'；占位符 / 否定式 / 无统计的后缀一律不成立）"
        )
        return 1, ""
    return 0, " · 终审裁决 准予交付"


_REPORT_NAME_RE = re.compile(r"^(r1|r2|delta-r1|delta-r2)-.+\.md$")


def _check_orphan_reports(archive: str, index: str, messages: list[str]) -> int:
    """11) 归档目录内的**未登记**报告文件必须报缺陷（BK-0012）。

    背景：台账只校验「已登记项」，未入台账的报告文件此前完全不可见——它们在
    Write-Once 证据面里既不被门禁枚举、也不被任何结论引用，等于凭据黑盒。

    只认轮次前缀（`r1-` / `r2-` / `delta-r1-` / `delta-r2-`）的 `.md`：天真枚举整个
    目录会把 `README.md` 判成孤儿报告（假红），故文件名模式 + 台账交叉校验双条件。
    """
    registered = set()
    for row in _collect_rows(index):
        fname = _read_fields(row)[1]
        if fname and _is_safe_filename(fname):
            registered.add(fname)
    try:
        entries = os.listdir(archive)
    except OSError:
        return 0
    orphans = sorted(
        name for name in entries
        if _REPORT_NAME_RE.match(name) and name not in registered
    )
    for name in orphans:
        messages.append(
            f"错误: 归档内存在未登记的报告文件: {name}（轮次台账未登记，凭据不可枚举）")
    return len(orphans)


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        archive, require_verdict = _parse_args(args)
    except _Exit as exc:
        return exc.code

    messages: list[str] = []
    index = os.path.join(archive, "README.md")
    if not os.path.isfile(index):
        messages.append(f"错误: 归档缺少索引文件 README.md: {archive}")
        messages.append(f"结构校验未通过: {archive}")
        sys.stdout.write("".join(f"{line}\n" for line in messages))
        return 1

    errors = _check_index(index, messages)
    report_count, r1_files, r2_files, report_errors = _check_reports(archive, _collect_rows(index), messages)
    errors += report_errors
    errors += _check_orphan_reports(archive, index, messages)
    if report_count == 0:
        messages.append("错误: 轮次台账为空或未登记任何报告文件")
        errors += 1

    for path in r1_files:
        label = f"R1 报告（{os.path.basename(path)}）"
        errors += _check_sections(path, label, R1_SECTIONS, messages)
    for path in r2_files:
        errors += _check_sections(path, f"R2 报告（{os.path.basename(path)}）", R2_SECTIONS, messages)

    if not r1_files:
        messages.append("错误: 台账未登记任何 R1 报告（r1 / delta-r1）")
        errors += 1
    errors += _check_id_alignment(r1_files, r2_files, messages)
    verdict_errors, verdict_note = _check_verdict(index, require_verdict, messages)
    errors += verdict_errors

    sys.stdout.write("".join(f"{line}\n" for line in messages))
    if errors:
        sys.stdout.write(f"结构校验未通过: {archive}\n")
        return 1
    sys.stdout.write(
        f"结构校验通过: 索引齐备 · 报告 {report_count} 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐{verdict_note}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
