#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate-seed.py — 为 taste-driven-designer 生成设计灵感种子字符串。

原理: String Seed of Thought (SSoT, Sakana AI) —— 随机性必须来自模型外部。
本脚本从操作系统密码学随机源（Bash 实现为 /dev/urandom）抽取真随机 base62 串,
供技能 Discover 阶段作为创意方向的灵感来源; 提供确定性模式 (-s) 供团队共享同一设计方向。

跨平台实现，与 generate-seed.sh 的选项、退出码、stdout/stderr 文案逐字节一致
（脚本路径前缀取自 argv[0], 与 Bash getopts 的 $0 语义对应）。

用法: python3 generate-seed.py [-l LENGTH] [-c COUNT] [-s SEED]
退出码: 0 = 成功; 2 = 参数/版本/用法错误
"""
from __future__ import annotations

import base64
import os
import re
import sys

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
DEFAULT_LENGTH = "64"
DEFAULT_COUNT = "1"
PARK_MILLER_MOD = 2147483647  # 2^31 - 1
PARK_MILLER_A = 48271
NON_CHARSET_VALUE = 97  # 与 awk 分支 index(cs, ch)==0 -> v=97 严格对应

USAGE = (
    "用法: generate-seed.sh [-l LENGTH] [-c COUNT] [-s SEED]\n"
    "\n"
    "生成 base62 字母数字字符串, 作为设计灵感的外部随机性种子 (String Seed of Thought)。\n"
    "\n"
    "选项:\n"
    "  -l LENGTH  种子字符串长度 (默认 64, 有效范围 8..1024)\n"
    "  -c COUNT   生成条数 (默认 1, 有效范围 1..64)\n"
    "  -s SEED    确定性模式: 以给定字符串为种子经 Park-Miller LCG 生成可复现输出;\n"
    "             不传则从 /dev/urandom 取真随机 (每次运行结果不同)\n"
    "  -h         显示本帮助\n"
    "\n"
    "示例:\n"
    "  bash generate-seed.sh                  # 64 位真随机种子\n"
    "  bash generate-seed.sh -l 128 -c 3      # 3 条 128 位种子, 供多方向并行探索\n"
    "  bash generate-seed.sh -s team-2026 -l 48   # 团队可复现同一设计方向\n"
)


class Getopts:
    """复刻 bash getopts 的解析语义（含内置错误消息、组合短选项与停止条件）。"""

    def __init__(self, args, optstring, prog):
        self._args = list(args)
        self._spec = self._parse_spec(optstring)
        self._prog = prog
        self._index = 0
        self._pos = 0
        self._current = ""

    @staticmethod
    def _parse_spec(optstring):
        spec = {}
        index = 0
        while index < len(optstring):
            char = optstring[index]
            if char == ":":
                index += 1
                continue
            requires = index + 1 < len(optstring) and optstring[index + 1] == ":"
            spec[char] = requires
            index += 2 if requires else 1
        return spec

    def next(self):
        """返回 (选项字符, 选项值) —— 选项值为 None 表示无参；无更多选项时返回 None。"""
        if self._pos == 0:
            if self._index >= len(self._args):
                return None
            arg = self._args[self._index]
            if arg == "--":
                self._index += 1
                return None
            if not arg.startswith("-") or arg == "-":
                return None  # getopts 在首个非选项参数处停止（其后参数不解析）
            self._current = arg
            self._pos = 1
        char = self._current[self._pos]
        self._pos += 1
        exhausted = self._pos >= len(self._current)
        if exhausted:
            self._index += 1
            self._pos = 0
        if char not in self._spec:
            sys.stderr.write("{0}: illegal option -- {1}\n".format(self._prog, char))
            return "?", None
        if not self._spec[char]:
            return char, None
        if not exhausted:
            value = self._current[self._pos:]
            self._index += 1
            self._pos = 0
            return char, value
        if self._index >= len(self._args):
            sys.stderr.write("{0}: option requires an argument -- {1}\n".format(self._prog, char))
            return "?", None
        value = self._args[self._index]
        self._index += 1
        return char, value


def validate_bound(raw, lower, upper, flag):
    """复刻 `! [[ $v =~ ^[0-9]+$ ]] || [ $v -lt lower ] || [ $v -gt upper ]` 的边界校验。"""
    if not re.fullmatch(r"[0-9]+", raw):
        error = "错误: {0} 必须为 {1}..{2} 的整数 (收到: {3})\n".format(flag, lower, upper, raw)
        sys.stderr.write(error)
        return False
    if int(raw) < lower or int(raw) > upper:
        error = "错误: {0} 必须为 {1}..{2} 的整数 (收到: {3})\n".format(flag, lower, upper, raw)
        sys.stderr.write(error)
        return False
    return True


def generate_deterministic(seed, length, count):
    """确定性模式: charset 索引哈希求初始状态, 再用 Park-Miller LCG 生成可复现输出。

    LCG 状态跨行连续（与 awk 实现的单次 BEGIN 过程一致）。
    """
    state = 0
    for char in seed:
        index = CHARSET.find(char)
        value = NON_CHARSET_VALUE if index < 0 else index
        state = (state * 31 + value) % PARK_MILLER_MOD
    lines = []
    for _ in range(count):
        chars = []
        for _ in range(length):
            state = (PARK_MILLER_A * state) % PARK_MILLER_MOD
            chars.append(CHARSET[state % 62])
        lines.append("".join(chars))
    return lines


def generate_random(length, count):
    """真随机模式: os.urandom -> base64 -> 过滤出 base62 字符, 不足则续取。

    与 Bash 实现的 /dev/urandom 路径等价（随机流本身不可逐字节复现, 契约只约束
    「base62 字符集 + 指定长度 + 跨运行多样性」）。
    """
    lines = []
    for _ in range(count):
        out = ""
        while len(out) < length:
            chunk = base64.b64encode(os.urandom(length * 3)).decode("ascii")
            out += "".join(char for char in chunk if char in CHARSET)
        lines.append(out[:length])
    return lines


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(sys.argv[1:] if argv is None else argv)
    length = DEFAULT_LENGTH
    count = DEFAULT_COUNT
    seed = ""
    parser = Getopts(args, "l:c:s:h", sys.argv[0])
    while True:
        parsed = parser.next()
        if parsed is None:
            break
        option, value = parsed
        if option == "l":
            length = value
        elif option == "c":
            count = value
        elif option == "s":
            seed = value
        elif option == "h":
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write(USAGE)
            return 2
    if not validate_bound(length, 8, 1024, "-l"):
        return 2
    if not validate_bound(count, 1, 64, "-c"):
        return 2
    if seed:
        lines = generate_deterministic(seed, int(length), int(count))
    else:
        lines = generate_random(int(length), int(count))
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
