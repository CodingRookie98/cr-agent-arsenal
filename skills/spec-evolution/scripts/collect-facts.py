#!/usr/bin/env python3
"""spec-evolution 事实采集器（只读）。

只回答「是什么」，不回答「好不好」：把技能与根提示词的客观状态导出为结构化
`facts.json`，供 `judge.py` 做确定性判定。本脚本不含任何判据逻辑，也不修改
仓库内任何文件（`--out` 指定的输出路径除外）。

用法:
    python3 collect-facts.py [--repo-root PATH] [--out FILE] [--no-gates] [--skills a,b]

退出码:
    0 = 成功；2 = 用法或输入错误
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"

SKILLS_DIRNAME = "skills"
NON_SKILL_DIRS = {"_shared"}
SURFACE_DIRS = ("references", "scripts", "templates")
ARCH_RELDIR = Path("docs/explanation/architecture")
ROOT_PROMPT_REL = Path("contexts/AGENTS.md")
COLLECTION_REL = Path("tools/skills-manager/collections/cr-agent-arsenal.json")
CROSS_TEST_REL = Path("skills/_shared/tests/test_cross_skill_links.py")
INDEX_REL = Path("docs/index.md")
README_REL = Path("README.md")
BASELINE_REL = Path("skills/spec-evolution/references/baseline.json")

LINE_LIMIT = 1000
GATE_TIMEOUT = 300
SCANNED_SUFFIXES = {".py", ".sh", ".md", ".json", ".yaml", ".yml", ".txt", ".cfg", ".toml"}

FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
DESC_RX = re.compile(r"^description:[ \t]*(.*)$", re.MULTILINE)
NAME_RX = re.compile(r"^name:[ \t]*(.*)$", re.MULTILINE)
SKILL_NAMES_RX = re.compile(r"SKILL_NAMES\s*=\s*\[(.*?)\]", re.DOTALL)
STRING_RX = re.compile(r"[\"']([^\"']+)[\"']")
HEADING_RX = re.compile(r"^(#{1,3})[ \t]+(.*?)[ \t]*$", re.MULTILINE)

LINK_RX = re.compile(r"\]\(([^)]+)\)")
INLINE_CODE_RX = re.compile(r"`[^`]*`")
COMMAND_EXAMPLE_RX = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")

# 与 skills/_shared/tests/test_cross_skill_links.py 同源的跨技能链接正则
CROSS_RX_TEMPLATE = r"(?:^|[\s(=/\"'>、，（])(?:[^)\s\"'<>]*?[\\/])*(?<![.])(?:{names})[\\/]"

GATES = (
    ("pytest", ["python3", "-B", "-m", "pytest", "skills/", "-q", "-p", "no:cacheprovider"]),
    ("check_doc_links",
     ["python3", "-B", "skills/doc-governance/scripts/check-doc-links.py",
      "--root", "docs"]),
    ("audit_doc_health",
     ["python3", "-B", "skills/doc-governance/scripts/audit-doc-health.py"]),
    ("cross_skill_links",
     ["python3", "-B", "-m", "pytest", "skills/_shared/tests/test_cross_skill_links.py",
      "-q", "-p", "no:cacheprovider"]),
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def line_count(path: Path) -> int:
    return len(read_text(path).splitlines())


def strip_fences(text: str) -> str:
    """剥离围栏代码块（与 test_cross_skill_links.py 同源语义）。"""
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def strip_inline_code(line: str) -> str:
    return INLINE_CODE_RX.sub("", line)


def unquote(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_frontmatter(text: str) -> tuple[int, int, str | None]:
    """返回 (frontmatter_chars, description_chars, name)。"""
    m = FRONTMATTER_RX.match(text)
    if not m:
        return 0, 0, None
    body = m.group(1)
    name_m = NAME_RX.search(body)
    desc_m = DESC_RX.search(body)
    desc = unquote(desc_m.group(1)) if desc_m else ""
    name = unquote(name_m.group(1)) if name_m else None
    return len(body), len(desc), name


def discover_skills(repo: Path) -> list[str]:
    """技能 = `skills/` 下含 `SKILL.md` 的目录。

    要求 `SKILL.md` 存在是刻意的：`skills/spec-evolution/references/baseline.json`
    等旁挂资产所在的目录不应被误认为一个技能。
    """
    root = repo / SKILLS_DIRNAME
    if not root.is_dir():
        return []
    return sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and p.name not in NON_SKILL_DIRS and not p.name.startswith(".")
        and (p / "SKILL.md").is_file()
    )


def scan_cross_skill_links(skill_dir: Path, repo: Path, names: list[str]) -> list[str]:
    if not names:
        return []
    pattern = re.compile(
        CROSS_RX_TEMPLATE.format(names="|".join(re.escape(n) for n in names)), re.IGNORECASE
    )
    hits: list[str] = []
    for md in sorted(skill_dir.rglob("*.md")):
        if "__pycache__" in md.parts:
            continue
        for i, line in enumerate(strip_fences(read_text(md)).splitlines(), 1):
            if COMMAND_EXAMPLE_RX.match(line) and "](" not in line:
                continue
            if pattern.search(strip_inline_code(line)):
                hits.append(f"{md.relative_to(repo).as_posix()}:{i}")
    return hits


def scan_files(skill_dir: Path, repo: Path) -> tuple[int, list[str]]:
    max_lines, oversized = 0, []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        if p.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        n = line_count(p)
        max_lines = max(max_lines, n)
        if n > LINE_LIMIT:
            oversized.append(p.relative_to(repo).as_posix())
    return max_lines, oversized


def parse_skill_names_from_test(path: Path) -> list[str]:
    m = SKILL_NAMES_RX.search(read_text(path))
    return STRING_RX.findall(m.group(1)) if m else []


def parse_collection_names(path: Path) -> list[str]:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return []
    names: list[str] = []
    for entry in data.get("skills", []):
        names.extend(entry.get("names", []))
    return names


def collect_skill(repo: Path, name: str, all_names: list[str],
                  registered: dict[str, list[str]]) -> dict:
    skill_dir = repo / SKILLS_DIRNAME / name
    entries = sorted(p.name for p in skill_dir.iterdir()) if skill_dir.is_dir() else []
    tests_dir = skill_dir / "tests"
    test_files = sorted(
        p.name for p in tests_dir.glob("test_*.py")
    ) if tests_dir.is_dir() else []

    empty_dirs = [d for d in SURFACE_DIRS
                  if (skill_dir / d).is_dir() and not any((skill_dir / d).iterdir())]

    design_doc = None
    candidate = repo / ARCH_RELDIR / f"{name}-design.md"
    if candidate.is_file():
        design_doc = candidate.relative_to(repo).as_posix()

    fm_chars, desc_chars = 0, 0
    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        fm_chars, desc_chars, _ = parse_frontmatter(read_text(skill_md))

    max_lines, oversized = scan_files(skill_dir, repo)
    idx_text = read_text(repo / INDEX_REL)
    readme_text = read_text(repo / README_REL)

    return {
        "name": name,
        "dirs": entries,
        "has_skill_md": skill_md.is_file(),
        "has_tests": bool(test_files),
        "test_files": test_files,
        "has_references": (skill_dir / "references").is_dir(),
        "has_scripts": (skill_dir / "scripts").is_dir(),
        "has_templates": (skill_dir / "templates").is_dir(),
        "empty_surface_dirs": empty_dirs,
        "design_doc": design_doc,
        "frontmatter_chars": fm_chars,
        "description_chars": desc_chars,
        "max_file_lines": max_lines,
        "oversized_files": oversized,
        "cross_skill_links": scan_cross_skill_links(skill_dir, repo, all_names),
        "registrations": {
            "cross_skill_names": name in registered["cross_skill_names"],
            "docs_index": f"skills/{name}/SKILL.md" in idx_text,
            # 与 docs_index 同一严格形式：裸子串 `skills/{name}` 会被
            # `skills/{name}-suffix` 之类的前缀命中，造成 C-07 假阴性。
            "readme": f"skills/{name}/SKILL.md" in readme_text,
            "collection": name in registered["collection"],
        },
    }


def collect_root_prompt(repo: Path) -> dict:
    path = repo / ROOT_PROMPT_REL
    text = read_text(path)
    baseline = {"lines": 0, "bytes": 0}
    baseline_path = repo / BASELINE_REL
    if baseline_path.is_file():
        try:
            baseline = json.loads(read_text(baseline_path))["root_prompt"]
            baseline = {"lines": baseline["lines"], "bytes": baseline["bytes"]}
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return {
        "path": ROOT_PROMPT_REL.as_posix(),
        "lines": len(text.splitlines()),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "baseline": baseline,
        "headings": [f"{m.group(1)} {m.group(2)}" for m in HEADING_RX.finditer(text)],
    }


def subprocess_env() -> dict:
    """子进程环境：强制 `PYTHONDONTWRITEBYTECODE=1`，保住只读不变式（GI-6）。

    仅靠命令行 `-B` 不足以覆盖全部门禁：`audit-doc-health.py` 内部用
    `importlib` 动态加载兄弟脚本，该路径不受 `-B` 影响，会写出 `__pycache__`。
    在此统一注入环境变量，使**任意**新增门禁也结构性免疫。
    """
    return {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def collect_gates(repo: Path) -> dict:
    gates = {}
    for key, cmd in GATES:
        try:
            proc = subprocess.run(cmd, cwd=str(repo), capture_output=True, env=subprocess_env(),
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=GATE_TIMEOUT)
            exit_code, stdout = proc.returncode, proc.stdout
        except subprocess.TimeoutExpired:
            exit_code, stdout = 124, f"TIMEOUT after {GATE_TIMEOUT}s"
        except OSError as exc:
            exit_code, stdout = 125, f"OSError: {exc}"
        lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
        gates[key] = {
            "cmd": " ".join(cmd),
            "exit_code": exit_code,
            "summary": lines[-1] if lines else "",
        }
    return gates


def git_head(repo: Path) -> str | None:
    try:
        proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=str(repo), capture_output=True, env=subprocess_env(),
                              text=True, encoding="utf-8", errors="replace", timeout=30)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def build_facts(repo: Path, *, with_gates: bool, only: list[str] | None) -> dict:
    all_names = discover_skills(repo)
    selected = [n for n in all_names if only is None or n in only]
    registered = {
        "cross_skill_names": parse_skill_names_from_test(repo / CROSS_TEST_REL),
        "collection": parse_collection_names(repo / COLLECTION_REL),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "repo_root": str(repo),
        "repo_head": git_head(repo),
        "gates": collect_gates(repo) if with_gates else None,
        "skills": [collect_skill(repo, n, all_names, registered) for n in selected],
        "root_prompt": collect_root_prompt(repo),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="collect-facts.py",
        description="spec-evolution 事实采集器（只读）：导出技能与根提示词的客观状态。",
    )
    ap.add_argument("--repo-root", default=".", help="仓库根目录（默认当前目录）")
    ap.add_argument("--out", default=None, help="facts.json 输出路径；省略则打印到 stdout")
    ap.add_argument("--no-gates", action="store_true", help="跳过 S1 门禁事实采集（纯文件系统扫描）")
    ap.add_argument("--skills", default=None, help="逗号分隔的技能名子集；省略为全部")
    args = ap.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    if not repo.is_dir():
        print(f"❌ repo-root 不存在或不是目录: {repo}", file=sys.stderr)
        return 2
    if not (repo / SKILLS_DIRNAME).is_dir():
        print(f"❌ 仓库根下缺少 {SKILLS_DIRNAME}/ 目录: {repo}", file=sys.stderr)
        return 2

    only = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else None
    facts = build_facts(repo, with_gates=not args.no_gates, only=only)
    payload = json.dumps(facts, ensure_ascii=False, indent=2, sort_keys=False)

    if args.out:
        out = Path(args.out)
        if not out.parent.is_dir():
            print(f"❌ 输出目录不存在: {out.parent}", file=sys.stderr)
            return 2
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"✅ 事实已导出: {out}（技能 {len(facts['skills'])} 个，门禁 {'已采集' if facts['gates'] else '已跳过'}）")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
