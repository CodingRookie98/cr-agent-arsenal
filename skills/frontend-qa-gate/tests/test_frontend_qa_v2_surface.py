"""V2.0 surface contract, link safety, AST size guards, and anti-score tests for frontend-qa-gate."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

SKILL_DIR = Path(__file__).resolve().parents[1]
FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FENCE_RX = re.compile(r"^\s*(`{3,}|~{3,})")
LINK_RX = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RX = re.compile(r"`[^`]*`")
CROSS_SKILL_RX = re.compile(
    r"(?:^|[\s(=/\"'>、，（])(?:[^)\s\"'<>]*?[\\/])*(?<![.])"
    r"(taste-driven-designer|dual-round-review|goal-loop|frontend-qa-gate|doc-governance|clarification-protocol)[\\/]",
    re.IGNORECASE,
)
CMD_EXAMPLE_RX = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")
SCORE_WORDS = re.compile(r"评分|打分|分数|得分|分值|满分|分级|等级|百分比|通过率|[0-9]+\s*分(?!钟)")
GATE_WORDS = re.compile(r"完成|放行|通过|达标|准入|交付|上线|发版|发布|合并|验收判据")
PROHIBITION_WORDS = re.compile(r"不得|禁止|不输出|不许|不含|不涉及|不参与|不作为|不构成|不以|不设|不采用|不提供|不用于|不计算|仅作|不作|非门禁|非判据|非验收|严禁")


def _md_files() -> list[Path]:
    return sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in str(p))


def _parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RX.match(text)
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


def _strip_fences(text: str) -> str:
    out, fence = [], ""
    for line in text.splitlines():
        m = FENCE_RX.match(line)
        if m:
            tok, rest = m.group(1), line[m.end():]
            if not fence and (tok[0] == "~" or "`" not in rest):
                fence = tok
                continue
            if fence and tok[0] == fence[0] and len(tok) >= len(fence) and not rest.strip():
                fence = ""
                continue
        if not fence:
            out.append(line)
    return "\n".join(out)


def _check_no_score_gate(text: str, label: str) -> None:
    for sentence in re.split(r"[。！？；\n]", text):
        if SCORE_WORDS.search(sentence) and GATE_WORDS.search(sentence):
            assert PROHIBITION_WORDS.search(sentence), f"{label} score-gate violation: {sentence.strip()[:100]}"


def test_skill_frontmatter_and_size_budgets():
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert len(skill_text.splitlines()) <= 95
    assert len(skill_text.encode("utf-8")) <= 6.5 * 1024
    meta = _parse_frontmatter(skill_text)
    assert meta.get("name") == "frontend-qa-gate"
    assert str(meta.get("license", "")).strip() == "MIT"
    desc = meta.get("description", "")
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 350
    assert len((SKILL_DIR / "references" / "acceptance-matrix.md").read_text(encoding="utf-8").splitlines()) <= 95
    assert len((SKILL_DIR / "references" / "probe-orchestration.md").read_text(encoding="utf-8").splitlines()) <= 85
    assert len((SKILL_DIR / "references" / "regression-routing.md").read_text(encoding="utf-8").splitlines()) <= 55
    assert len((SKILL_DIR / "templates" / "qa-summary-template.md").read_text(encoding="utf-8").splitlines()) <= 35


def test_python_line_and_ast_function_budgets():
    checker = SKILL_DIR / "scripts" / "check-qa-report.py"
    assert len(checker.read_text(encoding="utf-8").splitlines()) <= 210
    for py in [checker, *sorted((SKILL_DIR / "tests").glob("*.py"))]:
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                span = (node.end_lineno or node.lineno) - node.lineno + 1
                assert span <= 50, f"{py.name}:{node.name} is {span} lines (> 50)"


def test_retired_v1_files_deleted_and_template_valid():
    for rel in (
        "scripts/check-qa-report.sh",
        "references/browser-verification-protocol.md",
        "templates/qa-report-template.md",
        "tests/test_qa_gate_contract.py",
    ):
        assert not (SKILL_DIR / rel).exists(), f"retired V1 file still present: {rel}"
    tpl = json.loads((SKILL_DIR / "templates" / "qa-evidence-template.json").read_text(encoding="utf-8"))
    assert tpl.get("schema_version") == 2
    assert {"D-R", "D-S", "D-A", "D-P"} <= {a["domain"] for a in tpl["automated_assertions"]}


def test_markdown_fences_links_and_cross_skill_isolation():
    assert not CROSS_SKILL_RX.search("(references/acceptance-matrix.md)")
    assert CROSS_SKILL_RX.search("(../taste-driven-designer/SKILL.md)")
    for md in _md_files():
        raw = md.read_text(encoding="utf-8")
        fence_lines = [ln for ln in raw.splitlines() if FENCE_RX.match(ln)]
        assert len(fence_lines) % 2 == 0, f"unclosed fence in {md.name}"
        body = _strip_fences(raw)
        for line in body.splitlines():
            clean = INLINE_CODE_RX.sub("", line)
            if not CMD_EXAMPLE_RX.match(line):
                assert not CROSS_SKILL_RX.search(clean), f"cross-skill link in {md.name}: {line}"
            for target in LINK_RX.findall(clean):
                if target.startswith(("http", "#", "mailto:")):
                    continue
                assert (md.parent / target.split("#")[0]).resolve().exists(), f"broken link in {md.name}: {target}"


def test_v2_anchors_ssot_dual_track_probes_routing_and_anti_score():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    matrix = (SKILL_DIR / "references" / "acceptance-matrix.md").read_text(encoding="utf-8")
    probe = (SKILL_DIR / "references" / "probe-orchestration.md").read_text(encoding="utf-8")
    routing = (SKILL_DIR / "references" / "regression-routing.md").read_text(encoding="utf-8")

    for doc in _md_files():
        _check_no_score_gate(doc.read_text(encoding="utf-8"), doc.name)
    _check_no_score_gate("评分仅作遥测，禁止用于放行。", "legal")
    assert "Tier 1" in skill and "Tier 2" in skill and "pending_human" in skill
    assert "唯一真相源" in skill and "唯一真相源" in matrix and "内联最小" not in matrix
    assert "人类" in skill and ("签收" in skill or "放行" in skill)
    for token in ("chrome-devtools-mcp", "agent-browser", "Playwright"):
        assert token in probe
    for token in ("行为修复", "结构", "根因", "方向", "D2", "dual-round-review", "taste-driven-designer"):
        assert token in routing
    tier1_rows = [ln for ln in matrix.splitlines() if re.match(r"^\|\s*(?:V|S|A|P)\d+\s*\|", ln)]
    tier2_rows = [ln for ln in matrix.splitlines() if re.match(r"^\|\s*H-", ln)]
    assert len(tier1_rows) == 23 and len(tier2_rows) == 4
    assert not any(ln.startswith("| S9 |") for ln in tier1_rows)
    for p in sorted(SKILL_DIR.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and "tests" not in p.parts:
            txt = p.read_text(encoding="utf-8")
            assert "/home/" not in txt and "/Users/" not in txt and "docs/" not in txt, f"boundary leak in {p.name}"
