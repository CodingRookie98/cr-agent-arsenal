"""test_judge_contract.py — judge.py 判定契约、锚点硬门禁与报告不变式。"""

import json
from pathlib import Path

from conftest import build_repo, run_collect, run_judge


def _rm(path: Path) -> None:
    for p in sorted(path.rglob("*"), reverse=True):
        p.unlink() if p.is_file() else p.rmdir()
    path.rmdir()


def _facts(root: Path) -> dict:
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def _run(root: Path, facts: dict, tmp_path: Path, *extra):
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    js = tmp_path / "f.json"
    proc = run_judge(src, "--repo-root", str(root), "--json", str(js), *extra)
    data = json.loads(js.read_text(encoding="utf-8")) if js.exists() else None
    return proc, data


def _only(data, criterion):
    hits = [f for f in data if f["criterion"] == criterion]
    assert len(hits) == 1, f"{criterion} 命中 {len(hits)} 条: {data}"
    return hits[0]


# --- 第一部分：十条判据 -------------------------------------------------------

def test_clean_repo_yields_no_findings(tmp_path):
    root = build_repo(tmp_path / "repo")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert data == []


def test_c01_missing_tests_is_high(tmp_path):
    root = build_repo(tmp_path / "repo")
    _rm(root / "skills" / "demo" / "tests")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-01")
    assert f["severity"] == "HIGH" and f["skill"] == "demo"
    assert f["anchor"] == "[SKILL:demo/SKILL.md]"
    assert f["rule"] == "[RULE:§3-质量门槛]"


def test_c02_missing_design_doc_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    (root / "docs" / "explanation" / "architecture" / "demo-design.md").unlink()
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-02")
    assert f["severity"] == "MID" and f["rule"] == "[RULE:§3-质量门槛]"


def test_c03_missing_surface_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    _rm(root / "skills" / "demo" / "templates")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-03")
    assert f["severity"] == "MID" and f["observed"] == "缺失: templates"


def test_c04_description_over_soft_limit_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo", skill_description="Use when " + "x" * 500 + ".")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-04")
    assert f["severity"] == "MID" and f["observed"] == "510 字符"


def test_c05_description_over_hard_limit_is_high(tmp_path):
    root = build_repo(tmp_path / "repo", skill_description="Use when " + "x" * 1100 + ".")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-05")
    assert f["severity"] == "HIGH" and f["observed"] == "1110 字符"
    assert not [x for x in data if x["criterion"] == "C-04"], "C-04/C-05 必须互斥"


def test_c06_oversized_file_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    (root / "skills" / "demo" / "references" / "big.md").write_text(
        "行\n" * 1010, encoding="utf-8")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-06")
    assert f["severity"] == "MID"
    assert f["anchor"] == "[SKILL:demo/references/big.md]"
    assert f["rule"] == "[RULE:§3-精准修改与代码卫生]"


def test_c07_registration_gap_is_high(tmp_path):
    root = build_repo(tmp_path / "repo")
    idx = root / "docs" / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8").replace("skills/demo/SKILL.md", ""),
                   encoding="utf-8")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-07")
    assert f["severity"] == "HIGH" and f["anchor"] == "[REPO:docs/index.md]"


def test_c08_cross_skill_link_is_high(tmp_path):
    root = build_repo(tmp_path / "repo")
    (root / "skills" / "demo" / "references" / "link.md").write_text(
        "见 [demo](../demo/SKILL.md) 不算。\n", encoding="utf-8")
    proc, data = _run(root, _facts(root), tmp_path)
    assert proc.returncode == 1
    f = _only(data, "C-08")
    assert f["severity"] == "HIGH"
    assert f["anchor"].startswith("[SKILL:demo/references/link.md:")


def test_c09_gate_failure_is_blocker(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    facts["skills"][0]["has_templates"] = False
    proc, data = _run(root, facts, tmp_path)
    assert proc.returncode == 1
    assert data[0]["criterion"] == "C-09" and data[0]["severity"] == "BLOCKER"
    assert data[0]["anchor"] == "[REPO:skills/]"


def test_c10_root_prompt_growth_is_mid(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["root_prompt"]["lines"] += 1
    facts["root_prompt"]["bytes"] += 30
    proc, data = _run(root, facts, tmp_path)
    assert proc.returncode == 0
    f = _only(data, "C-10")
    assert f["severity"] == "MID"
    assert f["anchor"] == "[REPO:contexts/AGENTS.md]"
    assert "lines:" in f["observed"] and "bytes:" in f["observed"]


def test_finding_order_is_severity_then_skill_then_criterion(tmp_path):
    root = build_repo(tmp_path / "repo")
    _rm(root / "skills" / "demo" / "tests")
    _rm(root / "skills" / "demo" / "templates")
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "c", "exit_code": 1, "summary": "s"}}
    proc, data = _run(root, facts, tmp_path)
    assert [(f["severity"], f["criterion"]) for f in data] == [
        ("BLOCKER", "C-09"), ("HIGH", "C-01"), ("MID", "C-03")]


# --- 第二部分：锚点硬门禁与退出码 2 -------------------------------------------

def test_phantom_skill_anchor_exits_2_without_writing(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["oversized_files"] = ["skills/demo/references/ghost.md"]
    report = tmp_path / "report.md"
    js = tmp_path / "f.json"
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    proc = run_judge(src, "--repo-root", str(root), "--report", str(report), "--json", str(js))
    assert proc.returncode == 2
    assert "ghost.md" in proc.stderr
    assert not report.exists() and not js.exists(), "GI-3：锚点失败时不得写出任何产物"


def test_invalid_rule_anchor_exits_2(tmp_path):
    root = build_repo(tmp_path / "repo", agents_md="# SYSTEM RULES\n")
    (root / "skills" / "demo" / "references" / "big.md").write_text(
        "行\n" * 1010, encoding="utf-8")
    facts = _facts(root)
    facts["skills"][0]["oversized_files"] = ["skills/demo/references/big.md"]
    proc, data = _run(root, facts, tmp_path)
    assert proc.returncode == 2
    assert "根提示词锚点无对应标题" in proc.stderr


def test_missing_facts_file_exits_2(tmp_path):
    proc = run_judge(tmp_path / "nope.json")
    assert proc.returncode == 2
    assert "找不到 facts 文件" in proc.stderr


def test_invalid_json_exits_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    proc = run_judge(bad)
    assert proc.returncode == 2
    assert "不是合法 JSON" in proc.stderr


def test_missing_required_key_exits_2(tmp_path):
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"repo_root": str(tmp_path)}), encoding="utf-8")
    proc = run_judge(partial)
    assert proc.returncode == 2
    assert "缺少必需键" in proc.stderr


# --- 第三部分：报告不变式 -----------------------------------------------------

def test_report_written_to_requested_path(tmp_path):
    root = build_repo(tmp_path / "repo")
    report = tmp_path / "out" / "report.md"
    js = tmp_path / "out" / "findings.json"
    src = root / "_in.json"
    src.write_text(json.dumps(_facts(root), ensure_ascii=False), encoding="utf-8")
    proc = run_judge(src, "--repo-root", str(root), "--report", str(report), "--json", str(js))
    assert proc.returncode == 0, proc.stderr
    assert report.exists() and js.exists()
    assert json.loads(js.read_text(encoding="utf-8")) == []


def test_report_is_written_with_requested_name(tmp_path):
    root = build_repo(tmp_path / "repo")
    report = tmp_path / "sub" / "report.md"
    js = tmp_path / "f.json"
    src = root / "_in.json"
    src.write_text(json.dumps(_facts(root), ensure_ascii=False), encoding="utf-8")
    proc = run_judge(src, "--repo-root", str(root), "--report", str(report), "--json", str(js))
    assert proc.returncode == 0
    assert report.exists()


def test_report_head_contains_verdict_and_metadata(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 0
    text = report.read_text(encoding="utf-8")
    assert "spec-evolution 演进报告" in text
    assert "判定结论: **MID**" in text
    assert "扫描技能数: 1" in text
    assert "C-04" in text
    # facts 由 --no-gates 采集而来 → gates 为 null，报告必须如实说「未采集」，
    # 不得对既有门禁状态作肯定陈述（RFC-0004 交付审查 R1-3）。
    assert "未采集门禁事实" in text
    assert "无既有门禁失败" not in text


def test_report_says_clean_only_when_gates_were_collected(tmp_path):
    """三态判据必须要求**结构合法且有内容**的门禁事实。

    只有「≥1 条 well-formed 的 `{cmd, exit_code, summary}`」才构成「已采集」的
    证据。`None` / `[]` / `{}` / `0` / 畸形值一律归「未采集」—— 用 `is not None`
    会把 falsy-but-not-None 与畸形结构误判为「已采集且无失败」，重新打开 R1-3 想
    关闭的 fail-open（Delta R1 DR1-5；`--facts` 接受外部输入，故该分支可达）。
    """
    root = build_repo(tmp_path / "repo")
    for bad in (None, [], {}, 0, "", "junk", {"pytest": "junk"}):
        facts = _facts(root)
        facts["gates"] = bad
        report = tmp_path / "report.md"
        proc, _ = _run(root, facts, tmp_path, "--report", str(report))
        assert proc.returncode == 0, bad
        text = report.read_text(encoding="utf-8")
        assert "未采集门禁事实" in text, f"{bad!r} 未按未采集处理"
        assert "已采集门禁事实，无失败" not in text, f"{bad!r} 被误判为已采集且无失败"

    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 0, "summary": "376 passed"}}
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 0
    text = report.read_text(encoding="utf-8")
    assert "已采集门禁事实，无失败" in text
    assert "未采集门禁事实" not in text


def test_report_blocker_section_lists_failed_gate(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 1
    text = report.read_text(encoding="utf-8")
    assert "判定结论: **BLOCKER**" in text
    assert "| pytest |" in text and "1 failed" in text


def test_report_human_verdict_section_is_never_prefilled(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    _run(root, facts, tmp_path, "--report", str(report))
    text = report.read_text(encoding="utf-8")
    head, sep, tail = text.partition("## 人类裁决 (Human Verdict)")
    assert head and sep, "报告必须含人类裁决区"
    assert "[x]" not in tail, "GI-4：裁决区不得被预勾选"
    for token in ("BLOCKER", "HIGH", "MID", "建议", "推荐"):
        assert token not in tail, f"GI-4：裁决区混入判定器内容 {token!r}"
    assert "[ ] 采纳 / [ ] 驳回" in tail


def test_no_findings_still_renders_verdict_header(tmp_path):
    root = build_repo(tmp_path / "repo")
    report = tmp_path / "report.md"
    proc, _ = _run(root, _facts(root), tmp_path, "--report", str(report))
    assert proc.returncode == 0
    text = report.read_text(encoding="utf-8")
    assert "判定结论: **CLEAN**" in text
    assert "| ID | 裁决 | 裁决人 | 裁决日期 | 驳回理由 |" in text
    assert "[x]" not in text
