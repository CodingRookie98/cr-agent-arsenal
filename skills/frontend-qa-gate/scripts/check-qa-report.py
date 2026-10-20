#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-qa-report.py — 《前端验收报告》结构校验器。

定位：qa-gate 的机械门禁。校验「报告结构完整性」与（可选）「结论为 PASS」，
不判断验收证据本身是否真实（证据真实性由独立复核与人类签收负责）。

契约：
  1) 八个必需区块齐备，且不得仅出现在围栏代码块内（防围栏伪造）；
  2) 五域标题各出现恰好一次（五域覆盖）；
  3) 证据三态齐备（仅统计第 5 章）；
  4) 明细断言数与结论表「五维合计」声明值一致，且不低于下限（默认 5，可用 --min-assertions 提高，最小 1）；
  5) 未验证项一致性：结论表「未验证」列合计与「五维合计」声明必须相等；声明 > 0 时第 5 章必须列出具体项；
     结论为 BLOCKED 时未验证数不得为 0；
  6) 可选 --require-verdict=PASS：第 8 章必须声明「结论：PASS」（大小写归一，排除「建议结论」行），
     结论表所有结论列必须为 PASS，第 4 章不得列出未验证项，第 5 章不得列出具体未验证项。

跨平台实现，与 check-qa-report.sh 的选项、退出码、stdout/stderr 文案逐字节一致。
用法: python3 check-qa-report.py <报告文件> [--require-verdict=PASS] [--min-assertions=N]
退出码: 0 = 通过；1 = 结构/结论缺陷；2 = 用法错误
"""
from __future__ import annotations

import os
import re
import sys

USAGE = "usage: bash check-qa-report.sh <报告文件> [--require-verdict=PASS] [--min-assertions=N]"
SP = "[ \t\r\n\f\v]"  # POSIX [[:space:]]

REQUIRED_SECTIONS = (
    "## 1. 验收范围",
    "## 2. 断言结论表",
    "## 3. 五维断言明细",
    "## 4. 未验证项与阻断原因",
    "## 5. 证据三态标注",
    "## 6. 回流路由",
    "## 7. 全流程命令顺序",
    "## 8. 签收",
)
DOMAIN_TITLES = (
    "### 3.1 响应式视口断言",
    "### 3.2 交互状态断言",
    "### 3.3 无障碍断言",
    "### 3.4 浏览器覆盖断言",
    "### 3.5 性能断言",
)
TRI_STATES = ("已实现：", "已运行验证：", "未验证：")

FENCE_LINE_RE = re.compile("^" + SP + "*```")
SEC2_START = re.compile(r"^## 2\.")
SEC3_STOP = re.compile(r"^## 3\.")
TRI_START = re.compile(r"^## 5\. 证据三态标注")
TRI_STOP = re.compile(r"^## 6\.")
SEC4_START = re.compile(r"^## 4\. 未验证项与阻断原因")
SEC4_STOP = re.compile(r"^## 5\.")
SEC8_START = re.compile(r"^## 8\. 签收")

UNVERIFIED_NONE_RE = re.compile("未验证：" + SP + r"*[（(]?无[）)]?" + SP + "*$")
NA_ROW_RE = re.compile(r"\|" + SP + r"*N/A" + SP + r"*\|", re.IGNORECASE)
NA_JUSTIFY_RE = re.compile("未适用|不适用")
BLOCKED_RE = re.compile("^" + SP + "*-" + SP + "*结论[：:]" + SP + "*BLOCKED", re.IGNORECASE)
PASS_RE = re.compile("^" + SP + "*-" + SP + "*结论[：:]" + SP + "*PASS", re.IGNORECASE)
FAIL_BLOCKED_RE = re.compile("^" + SP + "*-" + SP + "*结论[：:]" + SP + "*(FAIL|BLOCKED)", re.IGNORECASE)
ASSERT_LINE_RE = re.compile("^" + SP + "*-" + SP + r"*\[[ xX]\]")
DECLARED_ASSERT_RE = re.compile("断言" + SP + "*[0-9]+")
DECLARED_UNV_RE = re.compile("未验证" + SP + "*[0-9]+")
DIGITS_RE = re.compile("[0-9]+")
NON_DIGITS_RE = re.compile("[^0-9]")
PASS_OR_NA_RE = re.compile(r"(?:PASS|N/A)", re.IGNORECASE)

OTHER4_LINE_RE = re.compile("^" + SP + "*[-|>]")
OTHER4_KEYWORD_RE = re.compile(
    "未验证项|未验证|阻断项|阻断|未测|未完成|未跑|待测|待验证|尚未|未执行|未确认|未经测试|未覆盖|未审计|未回归|pending|TODO"
)
OTHER4_STRIP1 = re.compile(
    "(未验证项|未验证|阻断项|阻断|未测|未完成)" + SP + "*[：:]" + SP + "*无(" + SP + "|（|\\(|[，。；、]|$)"
)
OTHER4_STRIP2 = re.compile(
    "(无|没有|不存在|未出现)"
    + SP
    + "*(任何|其它|其他|额外)?"
    + SP
    + "*((未验证项|未验证|阻断项|阻断|未测|未完成|未跑|待测|待验证|尚未|未执行|未确认|未经测试|未覆盖|未审计|未回归|pending|TODO)"
    + SP
    + "*([与和及、,，]?"
    + SP
    + "*)?)+"
)
HEADER_CELL_RE = re.compile("原因|说明|描述|项|编号|ID|Id|id")
WS_RE = re.compile(SP)


def read_text(path: str) -> str:
    """按字节读取后解码，保留 CRLF 中的 \\r（与 awk/grep 的逐行字节语义对齐）。"""
    with open(path, "rb") as handle:
        return handle.read().decode("utf-8", errors="replace")


def split_lines(text: str) -> list[str]:
    """复刻 awk 的记录语义：只按 \\n 切分；末尾换行不产生额外空记录。"""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def grep_count(pattern: re.Pattern, text: str) -> int:
    return sum(1 for line in split_lines(text) if pattern.search(line))


def grep_fixed_count(needle: str, text: str) -> int:
    return sum(1 for line in split_lines(text) if needle in line)


def grep_any(pattern: re.Pattern, text: str) -> bool:
    return any(pattern.search(line) for line in split_lines(text))


def grep_fixed_any(needle: str, text: str) -> bool:
    return any(needle in line for line in split_lines(text))


def strip_fences(text: str) -> str:
    """复刻 strip_fences 的 awk 状态机：围栏行翻转状态并跳过，围栏外才输出。"""
    collected = []
    in_fence = False
    for line in split_lines(text):
        if FENCE_LINE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            collected.append(line)
    return "\n".join(collected).rstrip("\n")


def extract_section(body: str, start: re.Pattern, stop: re.Pattern | None = None) -> str:
    """复刻 awk 章节提取（起止行本身不输出；结果按命令替换语义去掉尾部换行）。"""
    collected = []
    active = False
    for line in split_lines(body):
        if start.match(line):
            active = True
            continue
        if stop is not None and stop.match(line):
            active = False
            continue
        if active:
            collected.append(line)
    return "\n".join(collected).rstrip("\n")


def section_rows(body: str, start: re.Pattern, stop: re.Pattern) -> list[str]:
    """第 2 章表格行（以 '|' 开头），供列字段判定。"""
    return [line for line in split_lines(extract_section(body, start, stop)) if line.startswith("|")]


def column(line: str, index: int) -> str:
    cells = line.split("|")
    return cells[index] if len(cells) > index else ""


def first_declared(body: str, pattern: re.Pattern) -> str | None:
    """复刻 `grep -oE pattern | grep -oE '[0-9]+' | head -1`（取首个匹配中的数字段）。"""
    for line in split_lines(body):
        match = pattern.search(line)
        if match:
            digits = DIGITS_RE.search(match.group(0))
            if digits:
                return digits.group(0)
    return None


def unverified_lines(tri_section: str) -> list[str]:
    """复刻 `grep -F 未验证： | grep -vE '未验证：[[:space:]]*[（(]?无[）)]?[[:space:]]*$'`。"""
    return [
        line
        for line in split_lines(tri_section)
        if "未验证：" in line and not UNVERIFIED_NONE_RE.search(line)
    ]


def sec2_unverified_total(body: str) -> int:
    """结论表「未验证」列（第 6 字段）合计。"""
    total = 0
    for line in section_rows(body, SEC2_START, SEC3_STOP):
        value = NON_DIGITS_RE.sub("", column(line, 5))
        if value:
            total += int(value)
    return total


def na_bad_entries(body: str) -> list[str]:
    """N/A 域却声明了断言数/通过数/失败数（任一 >0）的条目，形如 'N/A(3/2/1)'。"""
    entries = []
    for line in section_rows(body, SEC2_START, SEC3_STOP):
        conclusion = WS_RE.sub("", column(line, 6))
        if conclusion.upper() != "N/A":
            continue
        counts = [NON_DIGITS_RE.sub("", column(line, idx)) for idx in (2, 3, 4)]
        if any(count and int(count) > 0 for count in counts):
            entries.append("{0}({1}/{2}/{3})".format(conclusion, counts[0], counts[1], counts[2]))
    return entries


def non_pass_conclusions(body: str) -> list[str]:
    """结论列去除空白后非空、非表头，且不是 PASS/N/A 的行。"""
    rows = []
    for line in section_rows(body, SEC2_START, SEC3_STOP):
        conclusion = WS_RE.sub("", column(line, 6))
        if not conclusion or conclusion in ("结论", "---"):
            continue
        if not PASS_OR_NA_RE.fullmatch(conclusion):
            rows.append(conclusion)
    return rows


def is_header_row(line: str) -> bool:
    """第 4 章表格表头白名单：含 |/｜、无冒号、无数字，且每个非空单元格都是表头词。"""
    if not re.search(r"[|｜]", line):
        return False
    if re.search(r"[：:]", line) or re.search(r"[0-9]", line):
        return False
    for cell in re.split(r"[|｜]", line):
        cell = re.sub("^" + SP + "+", "", cell)
        cell = re.sub(SP + "+$", "", cell)
        if cell == "":
            continue
        if not HEADER_CELL_RE.search(cell):
            return False
    return True


def sec4_offenders(sec4: str) -> list[str]:
    """复刻第 4 章「残留实词」判定：抹除否定式配对后仍含未验证/阻断实词的行。"""
    offenders = []
    for line in split_lines(sec4):
        if not OTHER4_LINE_RE.match(line):
            continue
        if is_header_row(line):
            continue
        work = line
        for _ in range(10):
            before = work
            work = OTHER4_STRIP1.sub("", work)
            work = OTHER4_STRIP2.sub("", work)
            if work == before:
                break
        if OTHER4_KEYWORD_RE.search(work):
            offenders.append(line)
    return offenders


def check_sections(report_text: str) -> int:
    failed = 0
    for section in REQUIRED_SECTIONS:
        if not grep_fixed_any(section, report_text):
            print("错误: 缺少必需区块: {0}".format(section))
            failed = 1
    return failed


def check_fence_parity(report_text: str) -> int:
    fence_count = grep_count(FENCE_LINE_RE, report_text)
    if fence_count % 2 != 0:
        print("错误: 围栏代码块未闭合（围栏标记 {0} 个，应为偶数）".format(fence_count))
        return 1
    return 0


def check_body_sections(body: str) -> int:
    failed = 0
    for section in REQUIRED_SECTIONS:
        if not grep_fixed_any(section, body):
            print("错误: 必需区块仅出现在围栏代码块内（无效）: {0}".format(section))
            failed = 1
    return failed


def check_domains(body: str) -> int:
    failed = 0
    for domain in DOMAIN_TITLES:
        hits = grep_fixed_count(domain, body)
        if hits != 1:
            print("错误: 五域覆盖不完整: {0} 出现 {1} 次（要求恰好 1 次）".format(domain, hits))
            failed = 1
    return failed


def check_tri_states(tri_section: str) -> int:
    failed = 0
    for state in TRI_STATES:
        if not grep_fixed_any(state, tri_section):
            print("错误: 证据三态标注缺少状态: {0}".format(state[:-1]))
            failed = 1
    return failed


def check_unverified_consistency(body: str, tri_section: str, sec4: str, sec8: str) -> int:
    failed = 0
    lines = unverified_lines(tri_section)
    unv_total = sec2_unverified_total(body)
    declared = first_declared(body, DECLARED_UNV_RE)
    if declared is not None and int(declared) != unv_total:
        print("错误: 结论表未验证列合计 {0} 与「五维合计」声明 {1} 不一致".format(unv_total, declared))
        failed = 1
    total_raw = str(unv_total)
    if declared is not None and int(declared) > unv_total:
        total_raw = declared
    if int(total_raw) > 0 and not lines:
        print("错误: 声明存在未验证项（{0}）但第 5 章未列出具体未验证项".format(total_raw))
        failed = 1
    if grep_any(BLOCKED_RE, sec8) and int(total_raw) == 0:
        print("错误: 第 8 章结论为 BLOCKED 但结论表声明未验证 0 项（自相矛盾）")
        failed = 1
    return failed


def check_assertions(body: str, min_assertions: str) -> tuple[int, int]:
    failed = 0
    assert_count = grep_count(ASSERT_LINE_RE, body)
    declared = first_declared(body, DECLARED_ASSERT_RE)
    if assert_count < int(min_assertions):
        print("错误: 五维断言明细不足（下限 {0}，实际 {1}）".format(min_assertions, assert_count))
        failed = 1
    if declared is None:
        print("错误: 结论表缺少「五维合计」断言行数声明")
        failed = 1
    elif int(declared) != assert_count:
        print("错误: 结论表声明断言 {0} 条，明细实际 {1} 条，合计不一致".format(declared, assert_count))
        failed = 1
    return failed, assert_count


def check_na(body: str, sec4: str, tri_section: str) -> int:
    failed = 0
    bad = na_bad_entries(body)
    if bad:
        print("错误: 结论为 N/A 的域其断言数/通过数/失败数必须均为 0（实际: {0}）".format(" ".join(bad) + " "))
        failed = 1
    if grep_any(NA_ROW_RE, body) and not grep_any(NA_JUSTIFY_RE, sec4 + tri_section):
        print("错误: 结论表存在 N/A 行但报告未说明「未适用/不适用」理由")
        failed = 1
    return failed


def check_verdict(body: str, tri_section: str, sec4: str, sec8: str) -> int:
    failed = 0
    if not grep_any(PASS_RE, sec8):
        print("错误: 第 8 章未声明「结论：PASS」（--require-verdict=PASS 校验；建议结论行不计数）")
        failed = 1
    if grep_any(FAIL_BLOCKED_RE, sec8):
        print("错误: 第 8 章声明结论为 FAIL/BLOCKED，与 --require-verdict=PASS 冲突")
        failed = 1
    bad_rows = non_pass_conclusions(body)
    if bad_rows:
        print("错误: 结论表存在非 PASS 结论: {0}".format(" ".join(bad_rows) + " "))
        failed = 1
    if sec4_offenders(sec4):
        print("错误: 结论为 PASS 但第 4 章列出了未验证项或阻断")
        failed = 1
    if unverified_lines(tri_section):
        print("错误: 结论为 PASS 但第 5 章列出了具体未验证项")
        failed = 1
    return failed


def check_report(report_text: str, report: str, require_verdict: str, min_assertions: str) -> bool:
    failed = 0
    failed |= check_sections(report_text)
    failed |= check_fence_parity(report_text)
    body = strip_fences(report_text)
    failed |= check_body_sections(body)
    failed |= check_domains(body)
    tri_section = extract_section(body, TRI_START, TRI_STOP)
    sec4 = extract_section(body, SEC4_START, SEC4_STOP)
    sec8 = extract_section(body, SEC8_START)
    failed |= check_tri_states(tri_section)
    failed |= check_unverified_consistency(body, tri_section, sec4, sec8)
    assert_failed, assert_count = check_assertions(body, min_assertions)
    failed |= assert_failed
    failed |= check_na(body, sec4, tri_section)
    if require_verdict == "PASS":
        failed |= check_verdict(body, tri_section, sec4, sec8)
    if failed:
        print("结构校验未通过: {0}".format(report))
        return False
    verdict_note = " · 结论 PASS" if require_verdict == "PASS" else ""
    print(
        "结构校验通过: 断言 {0} 条（下限 {1}） · 五域覆盖 · 三态齐备 · 必需区块齐备{2}".format(
            assert_count, min_assertions, verdict_note
        )
    )
    return True


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(sys.argv[1:] if argv is None else argv)
    require_verdict = ""
    min_assertions = "5"
    positional = []
    for arg in args:
        if arg.startswith("--require-verdict="):
            require_verdict = arg[len("--require-verdict="):]
        elif arg.startswith("--min-assertions="):
            min_assertions = arg[len("--min-assertions="):]
        else:
            positional.append(arg)
    if len(positional) != 1:
        sys.stderr.write(USAGE + "\n")
        return 2
    if not re.fullmatch(r"[0-9]+", min_assertions) or int(min_assertions) < 1:
        sys.stderr.write("错误: --min-assertions 必须是 >=1 的整数: {0}\n".format(min_assertions))
        return 2
    if require_verdict and require_verdict != "PASS":
        sys.stderr.write("错误: --require-verdict 目前仅支持 PASS\n")
        return 2
    report = positional[0]
    if not os.path.isfile(report):
        sys.stderr.write("错误: 报告文件不存在: {0}\n".format(report))
        return 2
    try:
        report_text = read_text(report)
    except OSError:
        sys.stderr.write("错误: 报告文件不存在: {0}\n".format(report))
        return 2
    return 0 if check_report(report_text, report, require_verdict, min_assertions) else 1


if __name__ == "__main__":
    sys.exit(main())
