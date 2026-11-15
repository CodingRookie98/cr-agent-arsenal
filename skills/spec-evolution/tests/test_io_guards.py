"""BK-0036 双守卫回归：输入范围（未知技能名）与输出落点（被跟踪文件）。

两条守卫都以**退出码**为断言对象，不看文案存在性——本技能的承诺是「退出码即结论」，
守卫若只改文案不改码，等于没拦。
"""
from __future__ import annotations

import shutil
import subprocess

import pytest

from conftest import build_repo, run_collect, run_judge, write

GIT = shutil.which("git")
NEEDS_GIT = pytest.mark.skipif(GIT is None, reason="需要 git 判定被跟踪状态")


def _git(root, *args):
    return subprocess.run([GIT, *args], cwd=str(root), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _init_repo(root):
    assert _git(root, "init", "-q").returncode == 0
    assert _git(root, "add", "-A").returncode == 0
    return root


# --- 输入范围守卫 ------------------------------------------------------------------

def test_unknown_skill_name_exits_2_and_names_it(repo):
    """拼错的技能名必须 exit 2，且报错要能直接指出错在哪、有哪些合法值。"""
    r = run_collect(repo, "--no-gates", "--skills", "demo,no-such-skill")
    assert r.returncode == 2, f"未知技能名必须拒绝：rc={r.returncode}\n{r.stdout}"
    assert "no-such-skill" in r.stderr
    assert "demo" in r.stderr, "报错须列出已知技能名，否则使用者无法自查"


def test_known_skill_subset_still_accepted(repo):
    r = run_collect(repo, "--no-gates", "--skills", "demo")
    assert r.returncode == 0, r.stderr


def test_no_skills_argument_is_still_accepted(repo):
    """省略 --skills 表示全量，不得因守卫误伤。"""
    r = run_collect(repo, "--no-gates")
    assert r.returncode == 0, r.stderr


# --- 输出落点守卫 ------------------------------------------------------------------

@NEEDS_GIT
def test_collect_refuses_tracked_output(tmp_path):
    root = _init_repo(build_repo(tmp_path / "repo"))
    target = root / "docs" / "index.md"
    before = target.read_bytes()

    r = run_collect(root, "--no-gates", "--out", str(target))

    assert r.returncode == 2, f"覆盖被跟踪文件必须拒绝：rc={r.returncode}\n{r.stdout}"
    assert "跟踪" in r.stderr
    assert target.read_bytes() == before, "拒绝时零副作用：目标字节不得变化"


@NEEDS_GIT
def test_collect_force_allows_tracked_output(tmp_path):
    root = _init_repo(build_repo(tmp_path / "repo"))
    target = root / "docs" / "index.md"

    r = run_collect(root, "--no-gates", "--out", str(target), "--force")

    assert r.returncode == 0, r.stderr
    assert target.read_text(encoding="utf-8").lstrip().startswith("{"), "--force 应真的写出产物"


def test_untracked_existing_output_is_overwritable(repo):
    """未被跟踪的既有文件必须可覆盖，否则 --out 无法重跑（守卫只拦不可恢复的那类）。"""
    target = repo / "_facts.json"
    write(target, "stale\n")

    r = run_collect(repo, "--no-gates", "--out", str(target))

    assert r.returncode == 0, r.stderr


@NEEDS_GIT
def test_judge_refuses_tracked_report_and_json(tmp_path):
    root = _init_repo(build_repo(tmp_path / "repo"))
    facts = root / "facts.json"
    assert run_collect(root, "--no-gates", "--out", str(facts)).returncode == 0
    tracked = root / "docs" / "index.md"
    before = tracked.read_bytes()

    r_report = run_judge(facts, "--report", str(tracked))
    assert r_report.returncode == 2, r_report.stdout
    assert "跟踪" in r_report.stderr
    assert tracked.read_bytes() == before

    r_json = run_judge(facts, "--json", str(tracked))
    assert r_json.returncode == 2, r_json.stdout
    assert tracked.read_bytes() == before, "两个落点都不得写入"


@NEEDS_GIT
def test_judge_force_allows_tracked_report(tmp_path):
    root = _init_repo(build_repo(tmp_path / "repo"))
    facts = root / "facts.json"
    assert run_collect(root, "--no-gates", "--out", str(facts)).returncode == 0
    target = root / "docs" / "index.md"

    r = run_judge(facts, "--report", str(target), "--force")

    assert r.returncode == 0, r.stderr
    assert "演进报告" in target.read_text(encoding="utf-8"), "--force 应真的写出报告"
