#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for scripts/backlog/manage-backlog.py."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "backlog" / "manage-backlog.py"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_create_and_increment_ids(tmp_path: Path) -> None:
    r1 = _run(
        tmp_path, "create", "First Task",
        "--type", "Feature", "--priority", "P1",
        "--trigger", "v1.0", "--source", "RFC-0001",
        "--acceptance", "tests pass", "--acceptance", "docs updated",
    )
    assert r1.returncode == 0
    r2 = _run(tmp_path, "create", "Second Task")
    assert r2.returncode == 0

    backlog = tmp_path / "docs" / "project" / "backlog"
    c1 = backlog / "active" / "BK-0001-first-task.md"
    c2 = backlog / "active" / "BK-0002-second-task.md"
    assert c1.is_file() and c2.is_file()
    assert (backlog / "index.md").is_file()
    text1 = c1.read_text(encoding="utf-8")
    assert "*(未开工)*" in text1
    assert "- [ ] tests pass" in text1
    assert "- [ ] docs updated" in text1


def test_list_filters_and_json_and_get(tmp_path: Path) -> None:
    assert _run(tmp_path, "create", "Alpha", "--type", "Bug", "--priority", "P0").returncode == 0
    assert _run(tmp_path, "create", "Beta", "--type", "TechDebt", "--priority", "P2").returncode == 0

    res_json = _run(tmp_path, "list", "--priority", "P0", "--type", "Bug", "--json")
    assert res_json.returncode == 0
    items = json.loads(res_json.stdout)
    assert len(items) == 1
    assert items[0]["id"] == "BK-0001"
    assert items[0]["title"] == "Alpha"

    res_ids = _run(tmp_path, "list", "--format", "id-only")
    assert res_ids.returncode == 0
    assert res_ids.stdout.strip().splitlines() == ["BK-0001", "BK-0002"]

    res_get = _run(tmp_path, "get", "BK-0002", "--json")
    assert res_get.returncode == 0
    assert json.loads(res_get.stdout)["title"] == "Beta"
    assert _run(tmp_path, "get", "BK-9999").returncode == 1


def test_close_archives_and_converges_placeholder(tmp_path: Path) -> None:
    assert _run(
        tmp_path, "create", "Close Me",
        "--acceptance", "AC-1", "--acceptance", "AC-2",
    ).returncode == 0
    assert _run(tmp_path, "create", "Wontfix Card").returncode == 0

    res = _run(
        tmp_path, "close", "BK-0001",
        "--resolution", "delivered", "--dest", "commit abc123", "--version", "2026-Q4",
    )
    assert res.returncode == 0

    backlog = tmp_path / "docs" / "project" / "backlog"
    archived = backlog / "archive" / "2026-Q4" / "BK-0001-close-me.md"
    assert archived.is_file()
    assert not (backlog / "active" / "BK-0001-close-me.md").exists()

    body = archived.read_text(encoding="utf-8")
    assert "*(未开工)*" not in body
    assert "status: completed" in body
    assert "destination: commit abc123" in body
    assert "- [ ] AC-1" in body
    assert "仍有 2 项未勾选" in body

    assert _run(tmp_path, "close", "BK-0002", "--resolution", "wontfix", "--version", "2026-Q4").returncode == 0
    items = json.loads(_run(tmp_path, "list", "--status", "rejected", "--json").stdout)
    assert [i["id"] for i in items] == ["BK-0002"]


def test_reopen_restores_active_and_clears_close_meta(tmp_path: Path) -> None:
    assert _run(tmp_path, "create", "Bounce").returncode == 0
    assert _run(tmp_path, "close", "BK-0001", "--dest", "pr1", "--version", "v1").returncode == 0

    res = _run(tmp_path, "reopen", "BK-0001")
    assert res.returncode == 0

    backlog = tmp_path / "docs" / "project" / "backlog"
    restored = backlog / "active" / "BK-0001-bounce.md"
    assert restored.is_file()
    assert not (backlog / "archive" / "v1" / "BK-0001-bounce.md").exists()

    detail = json.loads(_run(tmp_path, "get", "BK-0001", "--json").stdout)
    assert detail["status"] == "active"
    assert detail["closed_at"] == ""
    assert detail["resolution"] is None
    assert detail["destination"] is None
    assert "### 重启记录" in detail["body"]


def test_sync_index_preserves_custom_tail_and_posix_links(tmp_path: Path) -> None:
    assert _run(tmp_path, "create", "Keep Tail").returncode == 0
    index_path = tmp_path / "docs" / "project" / "backlog" / "index.md"
    orig = index_path.read_text(encoding="utf-8")
    index_path.write_text(orig + "\n---\n\n## 5. 自定义尾部说明\n保留这一段。\n", encoding="utf-8")

    res = _run(tmp_path, "sync-index")
    assert res.returncode == 0
    updated = index_path.read_text(encoding="utf-8")
    assert "## 5. 自定义尾部说明" in updated
    assert "保留这一段。" in updated
    assert "(./active/BK-0001-keep-tail.md)" in updated
