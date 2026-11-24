"""test_taste_designer_v2_surface.py — taste-driven-designer V2.0 表面契约与防回流测试。"""
from __future__ import annotations

import re
from pathlib import Path
import pytest

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD, SEED_PY = ROOT / "SKILL.md", ROOT / "scripts" / "generate-seed.py"
PROTOCOL, DISCOVER, AI_TELLS = (ROOT / "references" / f for f in ("critic-loop-protocol.md", "discover-phase.md", "ai-tells-audit.md"))
CRITIC_TMPL, BRIEF_TMPL = ROOT / "templates" / "critic-prompt-template.md", ROOT / "templates" / "design-brief-template.md"
FIXTURE = ROOT / "tests" / "fixtures" / "critic-gate-counter-evidence.md"

FM_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FENCE_RX, LINK_RX, CODE_RX = re.compile(r"^\s*(`{3,}|~{3,})(.*)$"), re.compile(r"\]\(([^)]+)\)"), re.compile(r"`[^`]*`")
CROSS_RX = re.compile(r"(?:^|[\s(=/\"'>、，（])(?:[^)\s\"\'<>]*?[\\/])*(?<![.])(?:taste-driven-designer|dual-round-review|goal-loop|frontend-qa-gate|doc-governance|clarification-protocol)[\\/]", re.I)
SCORE_RX, GATE_RX = re.compile(r"评分|分数|得分|分值|终分"), re.compile(r"完成|放行|通过|达标|准入|交付|上线|发版|发布|合并")
BAN_RX, PATH_RX = re.compile(r"不得|禁止|禁绝|不输出|不许|不含|不涉及|不参与|不作为|不构成|仅作|不作|遥测|非门禁|❌"), re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\)")


def _parse_frontmatter(text: str) -> dict:
    match = FM_RX.match(text)
    assert match, "SKILL.md missing YAML frontmatter"
    body = match.group(1)
    if yaml is not None:
        parsed = yaml.safe_load(body)
        assert isinstance(parsed, dict)
        return parsed
    meta = {}
    for line in body.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        k, sep, raw = line.partition(":")
        assert sep, f"invalid YAML line: {line!r}"
        v = raw.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        else:
            assert not re.search(r":(?:\s|$)", v), f"unquoted colon in {k}"
        meta[k.strip()] = v
    return meta


def _scan_fences(text: str) -> tuple[bool, str]:
    out, ch, ln = [], "", 0
    for line in text.splitlines():
        if m := FENCE_RX.match(line):
            tok, rest = m.group(1), m.group(2)
            if not ch and (tok[0] == "~" or "`" not in rest):
                ch, ln = tok[0], len(tok)
                continue
            if ch and tok[0] == ch and len(tok) >= ln and not rest.strip():
                ch, ln = "", 0
                continue
        if not ch:
            out.append(line)
    return (not ch), "\n".join(out)


def _no_score_gate(text: str, label: str) -> None:
    assert not re.search(r"9\s*/\s*10|[≥>]\s*9|达(?:到|满)\s*9(?:\.\d+)?\s*分", text), label
    for s in re.split(r"[。！？\n]", text):
        if SCORE_RX.search(s) and GATE_RX.search(s):
            assert BAN_RX.search(s), f"{label}: {s.strip()[:60]}"


def test_frontmatter_links_and_budgets():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 100 and len(text.encode("utf-8")) <= 6500
    assert len(SEED_PY.read_text(encoding="utf-8").splitlines()) <= 80
    meta = _parse_frontmatter(text)
    assert meta.get("name") == "taste-driven-designer" and str(meta.get("license")).strip() == "MIT"
    desc = meta.get("description", "")
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 500
    for rel in ("scripts/generate-seed.sh", "templates/seed-string-procedure.md", "references/multimodal-enrichment.md", "tests/test_generate_seed.py", "tests/test_gate_contract.py"):
        assert not (ROOT / rel).exists()
    for md in [SKILL_MD, PROTOCOL, DISCOVER, AI_TELLS, CRITIC_TMPL, BRIEF_TMPL]:
        ok, body = _scan_fences(md.read_text(encoding="utf-8"))
        assert ok, md.name
        for ln in body.splitlines():
            clean = CODE_RX.sub("", ln)
            assert not CROSS_RX.search(clean), f"{md.name}: {clean}"
            for tgt in LINK_RX.findall(clean):
                p = tgt.strip().split("#")[0]
                if p and not p.startswith(("http", "mailto:")):
                    assert (md.parent / p).resolve().exists(), f"{md.name} -> {p}"


def test_backflow_and_v2_contracts():
    retired = ("docs/reference/", "generate-seed.sh", "seed-string-procedure.md", "multimodal-enrichment.md", "round-nonce", "Receipt:")
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or set(path.relative_to(ROOT).parts) & {"tests", "__pycache__"}:
            continue
        txt = path.read_text(encoding="utf-8")
        assert not PATH_RX.search(txt) and all(tok not in txt for tok in retired), path.name
        if path.suffix == ".md":
            _no_score_gate(txt, path.name)
    fix = FIXTURE.read_text(encoding="utf-8")
    assert all(f"E{i}" in fix for i in range(1, 8)) and "6.2 → 5.8" in fix
    for doc in (SKILL_MD, DISCOVER, PROTOCOL, BRIEF_TMPL):
        t = doc.read_text(encoding="utf-8")
        assert "Persuade" in t and "Operate" in t
    ai, brief = AI_TELLS.read_text(encoding="utf-8"), BRIEF_TMPL.read_text(encoding="utf-8")
    assert all(f"| {i} |" in ai for i in range(1, 11)) and "模板字体与过度玻璃态" in ai and "3 列 Bento" in ai and "Emoji" in ai
    assert "| 编号 | 已决原则 | 裁决方 | 冲突记录 |" in brief and "| 轮次 | 版本 | 模式 | 结论（胜出/回归/名次） | 采纳与否决 |" in brief
    assert "Regressed dimensions" in CRITIC_TMPL.read_text(encoding="utf-8")
    _no_score_gate("通过条件不含分数，也不涉及评分。", "legal")
    with pytest.raises(AssertionError):
        _no_score_gate("仅当评分达到 9 分时才放行。", "illegal")


def test_frontmatter_stdlib_fallback_and_unquoted_colon_trap(monkeypatch):
    monkeypatch.setitem(globals(), "yaml", None)
    meta = _parse_frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    assert meta.get("name") == "taste-driven-designer" and str(meta.get("license")).strip() == "MIT"
    assert isinstance(meta.get("description"), str) and meta["description"].strip()
    bad = "---\nname: taste-driven-designer\ndescription: Triggers: landing page\n---\n"
    with pytest.raises(AssertionError, match="unquoted colon"):
        _parse_frontmatter(bad)
