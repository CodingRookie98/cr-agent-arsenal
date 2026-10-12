"""test_gate_invariants.py — RFC-0004 §3.7 的 GI-1~GI-6 回归门禁。

对象是 spec-evolution 自身：确定性、留白、锚点一致、退出码语义、只读。
"""

import hashlib
import importlib.util
import json
import re
from pathlib import Path

from conftest import build_repo, run_collect, run_judge

SPEC_DIR = Path(__file__).resolve().parents[1]
ANCHOR_RX = re.compile(r"\[(?:SKILL|REPO|RULE):[^\]]+\]")
PLACEHOLDER_RX = re.compile(r"\{\{(\w+)\}\}")
EXPECTED_PLACEHOLDERS = {
    "DATE", "REPO_HEAD", "SKILL_COUNT", "CRITERIA_COUNT",
    "VERDICT", "BLOCKER_SECTION", "FINDINGS_TABLE", "VERDICT_TABLE",
}


def _judge_module():
    spec = importlib.util.spec_from_file_location(
        "spec_evo_judge", SPEC_DIR / "scripts" / "judge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _facts(root: Path, *extra: str) -> dict:
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out), *extra)
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def _run(root: Path, facts: dict, tmp_path: Path, *extra: str):
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    js = tmp_path / "f.json"
    proc = run_judge(src, "--repo-root", str(root), "--json", str(js), *extra)
    data = json.loads(js.read_text(encoding="utf-8")) if js.exists() else None
    return proc, data


def _files(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


# --- GI-1 确定性 --------------------------------------------------------------

def test_gi1_template_placeholders_are_exactly_the_rendered_set():
    tpl = (SPEC_DIR / "templates" / "evolution-report.md").read_text(encoding="utf-8")
    assert set(PLACEHOLDER_RX.findall(tpl)) == EXPECTED_PLACEHOLDERS


def test_gi1_no_unreplaced_placeholders_in_report(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 0, proc.stderr
    assert "{{" not in report.read_text(encoding="utf-8")


def test_gi1_report_and_json_are_byte_identical_across_runs(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    outs = []
    for i in (1, 2):
        rep, js = tmp_path / f"r{i}.md", tmp_path / f"j{i}.json"
        proc = run_judge(src, "--repo-root", str(root),
                         "--report", str(rep), "--json", str(js))
        assert proc.returncode == 0, proc.stderr
        outs.append((rep.read_bytes(), js.read_bytes()))
    assert outs[0] == outs[1], "GI-1：同一 facts 必须产出逐字节相同的报告与 JSON"


# --- GI-2 排列稳定 ------------------------------------------------------------

def test_gi2_findings_are_stable_under_gate_input_permutation(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["has_templates"] = False
    facts["skills"][0]["has_tests"] = False
    facts["gates"] = {
        "pytest": {"cmd": "c", "exit_code": 1, "summary": "s"},
        "audit_doc_health": {"cmd": "d", "exit_code": 1, "summary": "t"},
    }
    _, first = _run(root, facts, tmp_path)

    shuffled = json.loads(json.dumps(facts))
    shuffled["gates"] = dict(reversed(list(shuffled["gates"].items())))
    _, second = _run(root, shuffled, tmp_path)
    assert first == second, "GI-2：findings 排列不得依赖输入字典顺序"


# --- GI-3 锚点一致 ------------------------------------------------------------

def test_gi3_report_anchors_are_a_subset_of_findings_json(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    facts["skills"][0]["has_templates"] = False
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    report = tmp_path / "report.md"
    proc, data = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 1
    anchors = set(ANCHOR_RX.findall(report.read_text(encoding="utf-8")))
    assert anchors, "报告必须携带可核验锚点"
    assert anchors <= {f["anchor"] for f in data}, "GI-3：报告出现 finding 之外的锚点"


def test_gi3_anchor_validator_rejects_phantom_and_malformed(tmp_path):
    mod = _judge_module()
    root = build_repo(tmp_path / "repo")
    headings = ["# SYSTEM RULES", "## 3. 基础工程规范与防御底线",
                "### 质量门槛 (Definition of Done)"]
    accepted = ["[SKILL:demo/SKILL.md]", "[REPO:docs/index.md]", "[RULE:§3-质量门槛]"]
    rejected = ["[SKILL:nope/SKILL.md]", "[SKILL:demo/ghost.md]",
                "[SKILL:demo/SKILL.md:9999]", "[REPO:docs/ghost.md]",
                "[RULE:§3-不存在的条款]", "[RULE:§9-质量门槛]",
                "SKILL:demo/SKILL.md", "[SKILL:demo/]", ""]
    for anchor in accepted:
        assert mod.validate_anchor(anchor, root, headings) is None, anchor
    for anchor in rejected:
        assert mod.validate_anchor(anchor, root, headings) is not None, anchor


# --- GI-4 留白 ----------------------------------------------------------------

def test_gi4_template_verdict_section_is_blank():
    tpl = (SPEC_DIR / "templates" / "evolution-report.md").read_text(encoding="utf-8")
    _, sep, tail = tpl.partition("## 人类裁决 (Human Verdict)")
    assert sep, "模板必须含人类裁决区"
    assert "[x]" not in tail
    for token in ("BLOCKER", "HIGH", "MID"):
        assert token not in tail, f"GI-4：模板裁决区混入 {token}"


def test_gi4_rendered_verdict_rows_are_empty(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    facts["gates"] = {"pytest": {"cmd": "c", "exit_code": 1, "summary": "s"}}
    report = tmp_path / "report.md"
    _run(root, facts, tmp_path, "--report", str(report))
    _, sep, tail = report.read_text(encoding="utf-8").partition("## 人类裁决 (Human Verdict)")
    assert sep
    rows = [ln for ln in tail.splitlines() if ln.startswith("| F-")]
    assert len(rows) == 2, rows
    for ln in rows:
        assert ln.count("[ ] 采纳 / [ ] 驳回") == 1
        assert ln.endswith("| | | |"), ln


# --- GI-5 退出码语义 ----------------------------------------------------------

def test_gi5_exit_code_semantics(tmp_path):
    root = build_repo(tmp_path / "repo")
    clean, _ = _run(root, _facts(root), tmp_path)
    assert clean.returncode == 0, "无 HIGH/BLOCKER 必须退出 0"

    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 1100  # C-05 HIGH
    blocking, _ = _run(root, facts, tmp_path)
    assert blocking.returncode == 1, "存在 HIGH 必须退出 1"

    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert run_judge(bad).returncode == 2, "输入非法必须退出 2"


# --- GI-6 只读 ----------------------------------------------------------------

def test_gi6_collector_is_read_only_without_gates(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = run_collect(root, "--no-gates", "--out", str(tmp_path / "facts.json"))
    assert proc.returncode == 0, proc.stderr
    assert _files(root) == before, "GI-6：采集改动了仓库"


def test_gi6_gates_run_without_leaving_artifacts(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = run_collect(root, "--out", str(tmp_path / "facts.json"))
    assert proc.returncode == 0, proc.stderr
    after = _files(root)
    assert after == before, f"GI-6：门禁留下产物 {sorted(set(after) - set(before))}"
    assert not (root / ".pytest_cache").exists(), "GI-6：-p no:cacheprovider 未生效"


def test_gates_recorded_when_enabled(tmp_path):
    root = build_repo(tmp_path / "repo")
    out = tmp_path / "facts.json"
    proc = run_collect(root, "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    gates = json.loads(out.read_text(encoding="utf-8"))["gates"]
    assert set(gates) == {"pytest", "check_doc_links", "audit_doc_health", "cross_skill_links"}
    assert all(g["exit_code"] == 0 for g in gates.values()), gates
