#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for scripts/doc-gates/check-all.py and check-golden-tasks.py."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

GATES_DIR = Path(__file__).resolve().parents[2] / "scripts" / "doc-gates"
CHECK_ALL = GATES_DIR / "check-all.py"
GOLDEN = GATES_DIR / "check-golden-tasks.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_minimal_docs(root: Path) -> None:
    _write(root / "AGENTS.md", "# 路由\n\n## 读取顺序\n1. 入口\n\n## 硬约束\n- 不猜路径\n")
    _write(root / "index.md", (
        "# 知识库总索引\n\n"
        "- [proposals](./proposals/RFC-0001.md)\n"
        "- [tutorials](./tutorials/start.md)\n"
        "- [how-to](./how-to/run.md)\n"
        "- [reference](./reference/rules/index.md)\n"
    ))
    _write(root / "proposals" / "RFC-0001.md", "# RFC\n\n> **提案元数据**\n> - **当前状态**: Implemented\n")
    _write(root / "tutorials" / "start.md", "# Start\n\n> **文档控制信息**\n> - **文档状态**: Active\n")
    _write(root / "how-to" / "run.md", "# Run\n\n> **文档控制信息**\n> - **文档状态**: Active\n")
    _write(root / "reference" / "rules" / "index.md", "# Rules\n\n> **文档控制信息**\n\n- [commit-evidence](./commit-evidence.md)\n")
    _write(root / "reference" / "rules" / "commit-evidence.md", "# Rule\n\n> **文档控制信息**\n\n禁止虚假宣称。\n")


def _run_py(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_check_all_help_describes_three_gates() -> None:
    res = _run_py(CHECK_ALL, "--help")
    assert res.returncode == 0
    assert "三道门禁" in res.stdout
    assert "六道门禁" not in res.stdout


def test_check_all_quiet_and_nonquiet_and_failures(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    _build_minimal_docs(root)

    res_q = _run_py(CHECK_ALL, "--root", str(root), "--quiet")
    assert res_q.returncode == 0
    assert res_q.stdout.strip() == ""

    res_v = _run_py(CHECK_ALL, "--root", str(root))
    assert res_v.returncode == 0
    for name in ("断链", "健康体检", "可回答性"):
        assert f"✅ {name}" in res_v.stdout

    (root / "AGENTS.md").unlink()
    res_fail = _run_py(CHECK_ALL, "--root", str(root), "--quiet")
    assert res_fail.returncode == 1
    assert "❌ 健康体检" in res_fail.stdout
    assert "→ 修复:" in res_fail.stdout

    res_missing = _run_py(CHECK_ALL, "--root", str(tmp_path / "no_such_docs"), "--quiet")
    assert res_missing.returncode == 1
    assert "失败" in res_missing.stdout


def test_check_all_full_builds_four_commands() -> None:
    spec = importlib.util.spec_from_file_location("check_all", CHECK_ALL)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)

    checks = mod._build_checks("python3", "docs", full=True)
    assert [c[0] for c in checks] == ["断链", "健康体检", "可回答性", "测试套件"]
    assert "--exclude" in checks[0][1] and "project/reviews" in checks[0][1]
    assert checks[3][1] == ["python3", "-m", "pytest", "skills/", "scripts/", "-q"]


def test_golden_tasks_help_and_missing_root() -> None:
    assert _run_py(GOLDEN, "--help").returncode == 0
    assert _run_py(GOLDEN, "--root", "/nonexistent/docs_path_xyz").returncode == 2


def test_golden_tasks_json_20_assertions_and_gap_nonblocking(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    _build_minimal_docs(root)
    res = _run_py(GOLDEN, "--root", str(root), "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert len(data["results"]) == 20
    assert data["counts"]["fail"] == 0
    assert data["counts"]["gap"] > 0


def test_golden_tasks_g18_index_without_llms_txt(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    _build_minimal_docs(root)
    assert not (root / "llms.txt").exists()

    ok_res = _run_py(GOLDEN, "--root", str(root), "--json")
    assert ok_res.returncode == 0
    g18_ok = next(r for r in json.loads(ok_res.stdout)["results"] if r["id"] == "G-18")
    assert g18_ok["status"] == "pass"

    _write(root / "index.md", "# 仅两象限\n\n- [proposals](./proposals/RFC-0001.md)\n- [rules](./reference/rules/index.md)\n")
    few_res = _run_py(GOLDEN, "--root", str(root), "--json")
    assert few_res.returncode == 1
    g18_few = next(r for r in json.loads(few_res.stdout)["results"] if r["id"] == "G-18")
    assert g18_few["status"] == "fail"

    (root / "index.md").unlink()
    miss_res = _run_py(GOLDEN, "--root", str(root), "--json")
    assert miss_res.returncode == 1
    g18_miss = next(r for r in json.loads(miss_res.stdout)["results"] if r["id"] == "G-18")
    assert g18_miss["status"] == "fail"
