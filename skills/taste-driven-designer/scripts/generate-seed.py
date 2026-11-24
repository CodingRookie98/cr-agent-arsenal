#!/usr/bin/env python3
"""generate-seed.py — 生成外部随机或可复现 base62 设计灵感种子。"""
from __future__ import annotations

import argparse
import hashlib
import secrets
import sys

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def random_seed(length: int) -> str:
    """使用密码学安全随机源生成指定长度的 base62 串。"""
    return "".join(secrets.choice(CHARSET) for _ in range(length))


def deterministic_seed(seed: str, row: int, length: int) -> str:
    """用 SHA-256 与拒绝采样 (byte < 248) 生成无模偏差的可复现 base62 串。"""
    chars: list[str] = []
    counter = 0
    while len(chars) < length:
        digest = hashlib.sha256(f"{seed}\0{row}\0{counter}".encode("utf-8")).digest()
        chars.extend(CHARSET[b % 62] for b in digest if b < 248)
        counter += 1
    return "".join(chars[:length])


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(prog="generate-seed.py", description="生成 base62 设计灵感种子 (SSoT)。")
    parser.add_argument("-l", "--length", type=int, default=64, help="长度 (8..1024)")
    parser.add_argument("-c", "--count", type=int, default=1, help="条数 (1..64)")
    parser.add_argument("-s", "--seed", default=None, help="确定性种子 (不传则真随机)")
    args = parser.parse_args(argv)
    if not 8 <= args.length <= 1024:
        parser.error(f"-l/--length 须为 8..1024 整数 (收到: {args.length})")
    if not 1 <= args.count <= 64:
        parser.error(f"-c/--count 须为 1..64 整数 (收到: {args.count})")
    for row in range(args.count):
        print(random_seed(args.length) if args.seed is None else deterministic_seed(args.seed, row, args.length))
    return 0


if __name__ == "__main__":
    sys.exit(main())
