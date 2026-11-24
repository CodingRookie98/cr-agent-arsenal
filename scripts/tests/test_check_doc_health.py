#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for scripts/doc-gates/check-doc-health.py."""

import os
import subprocess
import sys
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "doc-gates" / "check-doc-health.py"


def _write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _make_root(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    _write(root, "AGENTS.md", "# 路由\n\n## 读取顺序\n1. 先读索引\n\n## 硬约束\n- 不猜路径\n")
    return root


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_valid_three_states_and_quiet_zero_output(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "a.md", "# A\n\n> - **文档状态**: Active\n")
    _write(root, "b.md", "# B\n\n> - **文档状态**: Contested\n")
    _write(root, "c.md", "# C\n\n无状态字段，隐式 Active。\n")
    _write(root, "sub/old.md", "# Old\n\n> - **文档状态**: Superseded\n> - **取代于**: ../a.md#sec\n")
    res = _run(root, "--quiet")
    assert res.returncode == 0
    assert res.stdout == ""


def test_invalid_status_blocked(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "bad.md", "# Bad\n\n> - **文档状态**: Deprecated\n")
    res = _run(root)
    assert res.returncode == 1
    assert "文档状态非法" in res.stdout


@pytest.mark.parametrize("target", [
    "", "#only-anchor", "/abs/a.md", "\\win\\a.md", "C:\\a.md",
    "https://example.com/a.md", "../../outside.md", "./self.md#h1",
    "./missing.md", "./note.txt",
])
def test_superseded_invalid_targets_blocked(tmp_path: Path, target: str) -> None:
    root = _make_root(tmp_path)
    _write(root, "note.txt", "plain")
    (tmp_path / "outside.md").write_text("# out\n", encoding="utf-8")
    header = "> - **文档状态**: Superseded\n" + (f"> - **取代于**: {target}\n" if target else "")
    _write(root, "sub/self.md", f"# Self\n\n{header}")
    res = _run(root)
    assert res.returncode == 1
    assert "状态机违规" in res.stdout


def test_active_and_contested_with_pointer_blocked(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "target.md", "# T\n")
    _write(root, "exp_active.md", "# A\n\n> - **文档状态**: Active\n> - **取代于**: ./target.md\n")
    res1 = _run(root)
    assert res1.returncode == 1
    (root / "exp_active.md").unlink()

    _write(root, "imp_active.md", "---\nsuperseded-by: ./target.md\n---\n# Implicit\n")
    res2 = _run(root)
    assert res2.returncode == 1
    (root / "imp_active.md").unlink()

    _write(root, "contested.md", "# C\n\n> - **文档状态**: Contested\n> - **取代于**: ./target.md\n")
    res3 = _run(root)
    assert res3.returncode == 1


def test_body_explanation_tables_not_misread(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "with_marker.md", (
        "# 规则\n\n> **文档控制信息**\n> - **文档状态**: Active\n\n"
        "| 字段 | 值 |\n| :--- | :--- |\n| **取代于** | 说明示例 |\n"
    ))
    _write(root, "under_heading.md", (
        "# 规则\n\n## 字段说明\n\n| 字段 | 值 |\n| :--- | :--- |\n"
        "| **文档状态** | Deprecated |\n| **取代于** | ./none.md |\n"
    ))
    _write(root, "explain_col.md", (
        "# 规则\n\n| 字段 | 说明 |\n| :--- | :--- |\n"
        "| **文档状态** | 三态 |\n| **取代于** | 相对路径 |\n"
    ))
    res = _run(root)
    assert res.returncode == 0


def test_table_and_yaml_headers_and_fences(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "target.md", "# Target\n")
    _write(root, "tbl_top.md", "# Top\n\n| 字段 | 值 |\n| :--- | :--- |\n| **文档状态** | Superseded |\n| **取代于** | ./target.md |\n")
    _write(root, "tbl_marker.md", "## 文档控制头\n\n| 字段 | 值 |\n| :--- | :--- |\n| **文档状态** | Superseded |\n| **取代于** | ./target.md |\n")
    _write(root, "yaml_doc.md", "---\n文档状态: Superseded\nsuperseded-by: ./target.md\n---\n# Y\n")
    _write(root, "fenced.md", "# F\n\n```markdown\n> - **文档状态**: Bogus\n```\n")
    assert _run(root).returncode == 0

    _write(root, "tbl_bad.md", "## 文档控制信息\n\n| 字段 | 值 |\n| :--- | :--- |\n| **文档状态** | Active |\n| **取代于** | ./target.md |\n")
    assert _run(root).returncode == 1


def test_active_ref_to_superseded_warns_only(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "new.md", "# New\n")
    _write(root, "old.md", "# Old\n\n> - **文档状态**: Superseded\n> - **取代于**: ./new.md\n")
    _write(root, "adr.md", "# ADR\n\nInline [old](./old.md#s \"t\") and ref [r].\n\n[r]: ./old.md\n")
    res = _run(root)
    assert res.returncode == 0
    assert "Active 引用 Superseded [adr.md]: old.md" in res.stdout


def test_exemptions_for_reviews_and_backlog(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "project/reviews/r1/r1.md", "# R1\n\n> - **文档状态**: InvalidState\n\n" + ("x" * 1500))
    _write(root, "project/backlog/active/BK-0001.md", "---\nstatus: planned\n文档状态: Invalid\n---\n# Card\n")
    res = _run(root)
    assert res.returncode == 0


def test_size_limits_and_u2028_crlf_passthrough(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "small.md", "# Hi\n" + ("a" * 30) + "\n")
    assert _run(root, "--max-doc-bytes", "20").returncode == 1
    assert _run(root, "--max-doc-line", "20").returncode == 1
    assert _run(root, "--max-doc-bytes", "200", "--max-doc-line", "50").returncode == 0

    u2028_doc = ("a" * 600) + "\u2028" + ("b" * 600) + "\r\n"
    _write(root, "u2028.md", u2028_doc)
    res = _run(root)
    assert res.returncode == 1
    assert "单行超限 [u2028.md]" in res.stdout


def test_reference_articles_exempt_and_800_lines_warn_only(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "reference/articles/ext.markdown", ("x" * 70000) + "\n")
    _write(root, "long_ok.md", "\n".join(["line"] * 805) + "\n")
    res = _run(root)
    assert res.returncode == 0
    assert "行数建议拆分 [long_ok.md]" in res.stdout


def test_bad_utf8_and_unreadable_fail_closed(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    bad = root / "bad_utf8.md"
    bad.write_bytes(b"\xff\xfe\x00\x01")
    res = _run(root)
    assert res.returncode == 1
    assert "不可读或非法 UTF-8" in res.stdout
    bad.unlink()

    if hasattr(os, "geteuid") and os.geteuid() != 0:
        locked = _write(root, "locked.md", "# Locked\n")
        locked.chmod(0)
        try:
            assert _run(root).returncode == 1
        finally:
            locked.chmod(0o644)


def test_router_guardrail_and_missing_root(tmp_path: Path) -> None:
    assert _run(tmp_path / "missing").returncode == 2
    root = tmp_path / "docs"
    root.mkdir()
    assert _run(root).returncode == 1  # AGENTS.md missing

    _write(root, "AGENTS.md", "# 路由\n\n> 本文件只写读取顺序与硬约束\n\n## 读取顺序\n1. a\n")
    res_sec = _run(root)
    assert res_sec.returncode == 1
    assert "硬约束" in res_sec.stdout

    _write(root, "AGENTS.md", "# 路由\n\n## 读取顺序\n1. a\n\n## 硬约束\n" + "\n".join(["- r"] * 26) + "\n")
    assert _run(root).returncode == 1
    assert _run(root, "--max-router-lines", "40").returncode == 0


def test_r1_1_inline_backticks_at_line_start_not_ghost_fence(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "ghost.md", (
        "# Ghost Fence\n\n"
        "```inline``` 说明文本\n\n"
        "> - **文档状态**: Deprecated\n"
        "> - **取代于**: /etc/passwd\n"
    ))
    res = _run(root)
    assert res.returncode == 1
    assert "文档状态非法 [ghost.md]" in res.stdout

    # 合法围栏与含 info string 的波浪线行不会误闭合，内部示例保持忽略
    (root / "ghost.md").unlink()
    _write(root, "real_fence.md", (
        "# Real Fence\n\n"
        "~~~markdown\n"
        "~~~not-closing\n"
        "> - **文档状态**: Deprecated\n"
        "~~~\n"
    ))
    assert _run(root).returncode == 0


def test_r1_2_yaml_priority_marker_note_blank_and_bom(tmp_path: Path) -> None:
    # 1. YAML 优先级高于正文前 80 行引用块（禁止洗白，禁止误杀）
    root1 = _make_root(tmp_path / "c1")
    _write(root1, "launder.md", "---\n文档状态: Deprecated\n---\n# L\n\n> - **文档状态**: Active\n")
    res1 = _run(root1)
    assert res1.returncode == 1
    assert "文档状态非法 [launder.md]" in res1.stdout

    root2 = _make_root(tmp_path / "c2")
    _write(root2, "safe.md", "---\n文档状态: Active\n---\n# S\n\n> - **文档状态**: Deprecated\n")
    assert _run(root2).returncode == 0

    # 2. ## 文档控制信息 下先写 > 备注 + 空行 + 表格，不漏扫
    root3 = _make_root(tmp_path / "c3")
    _write(root3, "marker_note.md", (
        "# M\n\n## 文档控制信息\n\n> 备注说明\n\n"
        "| 字段 | 值 |\n| :--- | :--- |\n| **文档状态** | Deprecated |\n"
    ))
    res3 = _run(root3)
    assert res3.returncode == 1
    assert "文档状态非法 [marker_note.md]" in res3.stdout

    # 3. 带 UTF-8 BOM 的 YAML frontmatter 仍正确解析
    root4 = _make_root(tmp_path / "c4")
    _write(root4, "bom.md", "\ufeff---\n文档状态: Deprecated\n---\n# BOM\n")
    res4 = _run(root4)
    assert res4.returncode == 1
    assert "文档状态非法 [bom.md]" in res4.stdout


def test_r1_4_outside_symlink_superseded_no_crash(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("当前平台不支持 os.symlink")
    root = _make_root(tmp_path)
    _write(root, "new.md", "# New\n")
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n\n> - **文档状态**: Superseded\n> - **取代于**: ./new.md\n", encoding="utf-8")
    link_path = root / "old_link.md"
    try:
        link_path.symlink_to(outside)
    except OSError:
        pytest.skip("当前环境无创建符号链接权限")
    _write(root, "active.md", "# Active\n\nSee [old](./old_link.md).\n")
    res = _run(root)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "ValueError" not in res.stderr
    assert "Active 引用 Superseded [active.md]: old_link.md" in res.stdout


def test_r1_5_double_backtick_inline_code_no_false_warning(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "new.md", "# New\n")
    _write(root, "old.md", "# Old\n\n> - **文档状态**: Superseded\n> - **取代于**: ./new.md\n")
    _write(root, "active.md", "# Active\n\n示例：``use ` to quote [old](./old.md)`` 不应告警。\n")
    res = _run(root)
    assert res.returncode == 0
    assert "Active 引用 Superseded" not in res.stdout


def test_r1_6_superseded_url_unquote_query_and_encoded_escape_blocked(tmp_path: Path) -> None:
    root = _make_root(tmp_path)
    _write(root, "my new.md", "# My New\n")
    _write(root, "old_ok.md", "# Old\n\n> - **文档状态**: Superseded\n> - **取代于**: ./my%20new.md?v=1#sec\n")
    assert _run(root).returncode == 0

    (tmp_path / "outside.md").write_text("# Out\n", encoding="utf-8")
    for bad in ("%2e%2e/outside.md", "%2fetc%2fpasswd.md", "./bad%00.md"):
        _write(root, "old_bad.md", f"# Bad\n\n> - **文档状态**: Superseded\n> - **取代于**: {bad}\n")
        res = _run(root)
        assert res.returncode == 1
        assert "Traceback" not in res.stderr
        assert "状态机违规 [old_bad.md]" in res.stdout
