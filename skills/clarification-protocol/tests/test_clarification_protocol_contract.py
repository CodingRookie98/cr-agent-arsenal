"""test_clarification_protocol_contract.py — clarification-protocol 表面契约与防回流哨兵。"""

import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
ACTIVE_SKILLS = ("taste-driven-designer", "dual-round-review", "goal-loop", "frontend-qa-gate", "doc-governance", "clarification-protocol")
CROSS_SKILL_LINK = re.compile(r"(?:^|[\s(=/\"\'>、，（])(?:[^)\s\"\'<>]*?[\\/])*(?<![.])(?:" + "|".join(ACTIVE_SKILLS) + r")[\\/]", re.IGNORECASE)
MD_LINK, INLINE_CODE = re.compile(r"\]\(([^)]+)\)"), re.compile(r"`[^`]*`")
COMMAND_EXAMPLE = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")
FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


def _strip_fences(text: str) -> str:
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            out.append(line)
    return "\n".join(out)


def _parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RX.match(text)
    assert m, "SKILL.md 缺少合法 YAML frontmatter"
    body = m.group(1)
    if yaml is not None:
        parsed = yaml.safe_load(body)
        assert isinstance(parsed, dict), "frontmatter 顶层必须为 mapping"
        return parsed
    meta = {}
    for line in (ln for ln in body.splitlines() if ln.strip() and not ln.lstrip().startswith("#")):
        key, sep, val = line.partition(":")
        assert sep, f"非法 YAML 行: {line!r}"
        v = val.strip()
        if not (len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"')):
            assert not re.search(r":(?:\s|$)", v), f"{key} 含未加引号的 ': '"
        meta[key.strip()] = v.strip("'\"")
    return meta


def test_frontmatter_metadata_and_description_budget():
    meta = _parse_frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    assert meta.get("name") == SKILL_DIR.name == "clarification-protocol"
    assert str(meta.get("license", "")).strip().upper() == "MIT"
    desc = meta.get("description", "")
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 500, f"description 非法或超 500 字符: {len(desc)}"


def test_fences_balanced_and_links_clean():
    root = SKILL_DIR.resolve()
    docs = sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in str(p))
    assert SKILL_MD in docs
    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert sum(1 for ln in text.splitlines() if ln.strip().startswith("```")) % 2 == 0, f"围栏未闭合: {path.name}"
        for i, line in enumerate(_strip_fences(text).splitlines(), 1):
            clean = INLINE_CODE.sub("", line)
            if not (COMMAND_EXAMPLE.match(line) and "](" not in line):
                assert not CROSS_SKILL_LINK.search(clean), f"禁止跨技能相对外链: {path.name}:{i}"
            for t in (m.strip() for m in MD_LINK.findall(clean)):
                if not t.startswith(("http", "#", "mailto:")):
                    target = (path.parent / t.split("#")[0]).resolve()
                    assert target.exists() and (target == root or root in target.parents), f"断链或越界: {path.name}:{i} -> {t}"


def test_retired_artifacts_and_null_pointer_do_not_regress():
    text = SKILL_MD.read_text(encoding="utf-8")
    for retired in ("check-decision-ledger", "decision-ledger-template", "requirement-confirmation-template"):
        assert retired not in text, f"已废弃外壳回流进 SKILL.md: {retired}"
    assert not re.search(r"\|\s*提问层\s*\|\s*本节\s*\|", text), "旧空指针「提问层 | 本节」不得回流"
