#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-decision-ledger.py — 决策台账结构校验器（离线 / 只读 / 无写入）。

定位：把 SKILL.md §3「决策台账」的三类登记纪律变成机械门禁，供 §4 收敛自检前使用。
不判断结论是否正确、依据是否成立（那是人的裁决），只校验**类别与必填字段是否登记**。

契约（与 references/decision-ledger.md、templates/decision-ledger-template.md 同源）：
  1) 三类小节齐备：二级及以下标题恰为「已决项」「已排除边界」「默认假设」（允许形如 "## 3.1 已决项" 的编号前缀）；
  2) 每个类别至少 1 条数据行；数据行 = 表格行且首个单元格是编号（形如 D-01 / E-02 / A-03）；
  3) 已决项数据行必须含「出处」，已排除边界数据行必须含「排除依据」，默认假设数据行必须含「影响级别」；
  4) 围栏代码块内的示例不计入（防止模板示例冒充真实登记）。

跨平台实现，与 check-decision-ledger.sh 的选项（无选项）、退出码、stdout/stderr 文案逐字节一致。
用法: python3 check-decision-ledger.py <决策台账 markdown 文件>
退出码: 0 = 合规；1 = 不合规（❌ 指明缺什么）；2 = 用法错误（缺参数 / 参数多于 1 个 / 文件不存在）
"""
from __future__ import annotations

import os
import re
import sys

USAGE = "usage: bash check-decision-ledger.sh <决策台账 markdown 文件>"

SP = "[ \t\r\n\f\v]"  # POSIX [[:space:]]
CATEGORIES = ["已决项", "已排除边界", "默认假设"]
REQUIRED_FIELD = {"已决项": "出处", "已排除边界": "排除依据", "默认假设": "影响级别"}

FENCE_MARK = "```"
HEADING_RE = re.compile("^#{2,}" + SP)
HASH_PREFIX_RE = re.compile("^#+" + SP + "*")
NUMBER_PREFIX_RE = re.compile(r"^[0-9]+(\.[0-9]+)*[.]?" + SP + "*")
DATA_ROW_RE = re.compile("^" + SP + r"*\|")
ROW_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-[0-9]+$")
TRIM_RE = re.compile("^[ \t]+|[ \t]+$")


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


def trim(value: str) -> str:
    """复刻 awk trim()：只去空格与制表符（不动 \\r 等其它空白）。"""
    return TRIM_RE.sub("", value)


def check_ledger(text: str) -> tuple[list[str], bool]:
    """复刻 awk 状态机，返回 (输出消息列表, 是否不合规)。"""
    messages = []
    failed = False
    seen = set()
    counts = {category: 0 for category in CATEGORIES}
    category = ""
    in_fence = False
    for line in split_lines(text):
        if FENCE_MARK in line:
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if HEADING_RE.match(line):
            heading = HASH_PREFIX_RE.sub("", line, count=1)
            heading = NUMBER_PREFIX_RE.sub("", heading, count=1)
            heading = trim(heading)
            if heading in REQUIRED_FIELD:
                category = heading
                seen.add(heading)
            else:
                category = ""
            continue
        if category == "":
            continue
        if DATA_ROW_RE.match(line):
            cells = line.split("|")
            row_id = trim(cells[1]) if len(cells) > 1 else ""
            if ROW_ID_RE.match(row_id):
                counts[category] += 1
                if REQUIRED_FIELD[category] not in line:
                    messages.append(
                        "❌ {0} 行缺少「{1}」: {2}".format(category, REQUIRED_FIELD[category], trim(line))
                    )
                    failed = True
    for name in CATEGORIES:
        if name not in seen:
            messages.append("❌ 缺少「{0}」小节（三类登记必须齐备）".format(name))
            failed = True
        elif counts[name] == 0:
            messages.append("❌ 「{0}」小节没有数据行（编号形如 D-01）".format(name))
            failed = True
    return messages, failed


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        sys.stderr.write(USAGE + "\n")
        sys.stderr.write("错误: 需要且仅需要一个台账文件参数（实收 {0} 个）\n".format(len(args)))
        return 2
    ledger = args[0]
    if not os.path.isfile(ledger):  # 复刻 bash [[ ! -f "$LEDGER" ]]（目录/设备/不存在一律视为不存在）
        sys.stderr.write("错误: 台账文件不存在: {0}\n".format(ledger))
        return 2
    try:
        text = read_text(ledger)
    except OSError:
        sys.stderr.write("错误: 台账文件不存在: {0}\n".format(ledger))
        return 2
    messages, failed = check_ledger(text)
    if messages:
        sys.stdout.write("\n".join(messages) + "\n")
    if not failed:
        sys.stdout.write("✅ 决策台账结构合规: {0}\n".format(ledger))
        return 0
    sys.stderr.write("❌ 决策台账结构不合规: {0}（详见上方缺失项）\n".format(ledger))
    return 1


if __name__ == "__main__":
    sys.exit(main())
