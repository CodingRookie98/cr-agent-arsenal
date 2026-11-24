"""doc-governance V3.0 表面契约、围栏配对、断链与去私货防回流测试。"""

from __future__ import annotations

import getpass
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

SKILL_DIR = Path(__file__).resolve().parents[1]
CHECKER = SKILL_DIR / "scripts" / "check-doc-links.py"
FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FENCE_RX = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
PERSONAL_PATH_RX = re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\)")

RETIRED_PRIVATE_KEYWORDS = (
    "audit-doc-health",
    "check-doc-drift",
    "check-doc-control-sync",
    "check-golden-tasks",
    "manage-backlog",
    "manage-doc-index",
    "trim-revision",
    "scaffold-doc",
    "backlog-specification",
    "doc-control-header",
    "check-all.py",
)


def _fallback_parse_frontmatter(body: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    lines, i = body.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            i += 1
            continue
        key, sep, raw = ln.partition(":")
        assert sep, f"非法 YAML 行: {ln!r}"
        val = raw.strip()
        if val in (">", "|", ">-", "|-"):
            blk, i = [], i + 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                blk.append(lines[i].strip())
                i += 1
            meta[key.strip()] = " ".join(x for x in blk if x)
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        else:
            assert not re.search(r":(?:\s|$)", val), f"{key} 含未加引号的 ': '"
        meta[key.strip()], i = val, i + 1
    return meta


def _parse_frontmatter(text: str, *, force_fallback: bool = False) -> dict:
    match = FRONTMATTER_RX.match(text)
    assert match, "SKILL.md 缺少合法 YAML frontmatter"
    body = match.group(1)
    if yaml is not None and not force_fallback:
        parsed = yaml.safe_load(body)
        assert isinstance(parsed, dict), "frontmatter 顶层必须为 mapping"
        return parsed
    return _fallback_parse_frontmatter(body)


def _fences_balanced(text: str) -> bool:
    fence_char, fence_len = "", 0
    for line in text.splitlines():
        match = FENCE_RX.match(line)
        if not match:
            continue
        tok, rest = match.group(1), match.group(2)
        if not fence_char and (tok[0] == "~" or "`" not in rest):
            fence_char, fence_len = tok[0], len(tok)
        elif fence_char and tok[0] == fence_char and len(tok) >= fence_len and not rest.strip():
            fence_char, fence_len = "", 0
    return not fence_char


def _local_identities() -> list[str]:
    generic = {"root", "runner", "user", "admin", "nobody", "ci", "actions", "github-actions", "vscode", "codespace"}
    candidates = {
        raw for raw in (getpass.getuser(), Path.home().name)
        if raw and len(raw) >= 3 and raw.lower() not in generic
    }
    try:
        proc = subprocess.run(
            ["git", "config", "--get", "user.name"],
            cwd=str(SKILL_DIR), capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        git_user = proc.stdout.strip() if proc.returncode == 0 else ""
        if git_user and len(git_user) >= 3 and git_user.lower() not in generic:
            candidates.add(git_user)
    except (OSError, subprocess.SubprocessError):
        pass
    return sorted(candidates)


def test_skill_frontmatter_and_size_budget():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    lines, raw_bytes = text.splitlines(), text.encode("utf-8")
    assert len(lines) <= 130, f"SKILL.md 行数超 130: {len(lines)}"
    assert len(raw_bytes) <= 12 * 1024, f"SKILL.md 字节超 12 KB: {len(raw_bytes)}"

    meta = _parse_frontmatter(text)
    assert meta == _parse_frontmatter(text, force_fallback=True)
    assert meta.get("name") == "doc-governance"
    assert str(meta.get("license", "")).strip() == "MIT"
    desc = meta.get("description", "")
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 500, f"description 长度异常: {len(desc)}"


def test_markdown_fences_balanced_and_self_links_clean():
    md_files = sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in p.parts)
    assert md_files
    for path in md_files:
        assert _fences_balanced(path.read_text(encoding="utf-8")), f"围栏未闭合: {path.relative_to(SKILL_DIR)}"

    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(SKILL_DIR)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert proc.returncode == 0, f"技能自身断链扫描失败:\n{proc.stdout}\n{proc.stderr}"


def test_no_retired_private_keywords_or_personal_info():
    scanned = [
        p for p in sorted(SKILL_DIR.rglob("*"))
        if p.is_file() and not set(p.relative_to(SKILL_DIR).parts).intersection({"tests", "__pycache__"})
    ]
    assert scanned
    identities = _local_identities()
    for path in scanned:
        rel, text = path.relative_to(SKILL_DIR), path.read_text(encoding="utf-8")
        for kw in RETIRED_PRIVATE_KEYWORDS:
            assert kw not in text, f"{rel} 含已退役私有关键词: {kw}"
        assert not PERSONAL_PATH_RX.search(text), f"{rel} 含个人绝对路径"
        for ident in identities:
            assert not re.search(rf"(?<![A-Za-z0-9_-]){re.escape(ident)}(?![A-Za-z0-9_-])", text, re.I), (
                f"{rel} 疑似含个人真名/用户名: {ident}"
            )
