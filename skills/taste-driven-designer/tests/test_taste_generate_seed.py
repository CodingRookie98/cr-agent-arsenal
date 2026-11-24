"""test_taste_generate_seed.py — scripts/generate-seed.py 真实 CLI 行为测试。"""
from __future__ import annotations

import hashlib
import string
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate-seed.py"
BASE62 = string.ascii_uppercase + string.ascii_lowercase + string.digits
BSET = set(BASE62)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")


def ref(seed: str, row: int, length: int) -> str:
    out, c = [], 0
    while len(out) < length:
        out.extend(BASE62[b % 62] for b in hashlib.sha256(f"{seed}\0{row}\0{c}".encode()).digest() if b < 248)
        c += 1
    return "".join(out[:length])


def test_default_help_and_boundaries():
    assert run("-h").returncode == 0
    d = run()
    assert d.returncode == 0 and len(d.stdout.strip()) == 64 and set(d.stdout.strip()) <= BSET
    for l, c in (("8", "1"), ("1024", "1"), ("16", "64")):
        r = run("-l", l, "-c", c)
        rows = r.stdout.strip().splitlines()
        assert r.returncode == 0 and len(rows) == int(c) and all(len(x) == int(l) and set(x) <= BSET for x in rows)
    for bad in (("-l", "0"), ("-l", "7"), ("-l", "1025"), ("-l", "x"), ("-c", "0"), ("-c", "65"), ("-c", "x"), ("--bogus",)):
        r = run(*bad)
        assert r.returncode == 2 and r.stderr.strip()


def test_deterministic_and_random_modes():
    r1, r2 = run("-s", "team-2026", "-l", "48"), run("--seed", "team-2026", "--length", "48")
    assert r1.returncode == 0 and r1.stdout == r2.stdout and r1.stdout.strip() == ref("team-2026", 0, 48)
    assert run("-s", "a").stdout != run("-s", "b").stdout
    rows = run("-s", "multi", "-l", "32", "-c", "3").stdout.strip().splitlines()
    assert len(rows) == 3 and len(set(rows)) == 3
    seen = set()
    for s in ("", "A", "AAAA", "团队-2026"):
        a, b = run("-s", s, "-l", "32"), run("-s", s, "-l", "32")
        v = a.stdout.strip()
        assert a.returncode == 0 and a.stdout == b.stdout and len(v) == 32 and set(v) <= BSET and len(set(v)) >= 8 and v == ref(s, 0, 32)
        seen.add(v)
    assert len(seen) == 4
    rnd = [run("-l", "32").stdout.strip() for _ in range(3)]
    assert all(len(x) == 32 and set(x) <= BSET for x in rnd) and len(set(rnd)) == 3
