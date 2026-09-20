"""test_generate_seed.py — scripts/generate-seed.sh 的确定性行为校验。

覆盖:
1. 默认参数: 64 位 base62 字符集单条输出
2. 自定义长度与条数 (-l / -c)
3. 参数边界校验: 非法长度/条数必须非零退出且输出错误信息
4. 确定性模式 (-s): 相同种子输出逐字节一致, 且与 Python 复刻的
   Park-Miller LCG 计算结果完全一致 (防脚本侧回归漂移)
5. 不同种子输出互异
6. 真随机模式 (/dev/urandom): 多次运行存在多样性
"""

import string
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate-seed.sh"

BASE62 = set(string.ascii_letters + string.digits)
CHARSET = string.ascii_uppercase + string.ascii_lowercase + string.digits
MOD = 2147483647  # 2^31 - 1
A = 48271  # Park-Miller 乘数


def run(*args):
    return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True)


def park_miller(seed_text, length):
    """复刻脚本内嵌的「charset 索引哈希 + Park-Miller LCG」, 用于断言确定性输出。"""
    h = 0
    for ch in seed_text:
        idx = CHARSET.find(ch)
        if idx == -1:
            idx = 97  # 与脚本的 index()==0 兜底分支严格对应
        h = (h * 31 + idx) % MOD
    x = h
    out = []
    for _ in range(length):
        x = (A * x) % MOD
        out.append(CHARSET[x % 62])
    return "".join(out)


def test_default_output_length_and_charset():
    r = run()
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 1
    assert len(lines[0]) == 64
    assert lines[0] != ""
    assert set(lines[0]) <= BASE62


def test_custom_length_and_count():
    r = run("-l", "32", "-c", "3")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 3
    assert all(len(line) == 32 for line in lines)
    assert all(set(line) <= BASE62 for line in lines)


def test_invalid_length_rejected():
    for bad in ("0", "7", "1025", "abc", "-5", "1.5"):
        r = run("-l", bad)
        assert r.returncode != 0, f"-l {bad} 应被拒绝"
        assert r.stderr.strip(), f"-l {bad} 应输出错误信息"


def test_invalid_count_rejected():
    for bad in ("0", "65", "xyz"):
        r = run("-c", bad)
        assert r.returncode != 0, f"-c {bad} 应被拒绝"
        assert r.stderr.strip()


def test_deterministic_seed_mode_reproducible():
    r1 = run("-s", "team-design-2026", "-l", "48")
    r2 = run("-s", "team-design-2026", "-l", "48")
    assert r1.returncode == 0, r1.stderr
    assert r1.stdout == r2.stdout


def test_deterministic_seed_matches_park_miller():
    seed, length = "team-design-2026", 48
    r = run("-s", seed, "-l", str(length))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == park_miller(seed, length)


def test_deterministic_seed_matches_for_multiline():
    # LCG 状态跨行连续: 40 位连续流切两半即为两行输出
    seed = "z9@kickstart"
    r = run("-s", seed, "-l", "20", "-c", "2")
    assert r.returncode == 0, r.stderr
    stream = park_miller(seed, 40)
    lines = r.stdout.strip().splitlines()
    assert lines == [stream[:20], stream[20:]]
    assert lines[0] != lines[1]  # 两行互异, 便于并行探索不同方向


def test_different_seeds_differ():
    a = run("-s", "seed-one", "-l", "64").stdout
    b = run("-s", "seed-two", "-l", "64").stdout
    assert a != b


def test_random_mode_variety():
    outs = {run("-l", "16", "-c", "1").stdout for _ in range(5)}
    assert len(outs) >= 2, "真随机模式 5 次运行应产生至少 2 种不同输出"


def test_help_flag_succeeds():
    r = run("-h")
    assert r.returncode == 0
    assert "用法" in r.stdout or "usage" in r.stdout


def test_min_length_boundary():
    r = run("-l", "8")
    assert r.returncode == 0, r.stderr
    assert len(r.stdout.strip()) == 8


def test_max_length_and_count_combination():
    r = run("-l", "1024", "-c", "64")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.strip().splitlines()
    assert len(lines) == 64
    assert all(len(line) == 1024 for line in lines)


def test_empty_seed_falls_back_to_random():
    # -s "" 与不传等价: 回退真随机模式, 输出合规且跨运行存在多样性
    r = run("-s", "", "-l", "24")
    assert r.returncode == 0, r.stderr
    out = r.stdout.strip()
    assert len(out) == 24
    assert set(out) <= BASE62
    outro = run("-s", "", "-l", "24").stdout
    assert out != outro
