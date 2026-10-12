"""采集器契约测试：只回答「是什么」，只读，schema 稳定。"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import build_repo, run_collect, snapshot, write


def collect_json(root: Path, *args: str) -> dict:
    out = root / "_facts.json"
    r = run_collect(root, "--no-gates", "--out", str(out), *args)
    assert r.returncode == 0, r.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def test_schema_top_level_keys(repo: Path):
    facts = collect_json(repo)
    assert set(facts) == {
        "schema_version", "generated_at", "repo_root", "repo_head",
        "gates", "skills", "root_prompt",
    }
    assert facts["schema_version"] == "1.0"
    assert facts["gates"] is None, "--no-gates 时 gates 必须为 null"


def test_skill_structure_facts(repo: Path):
    skill = collect_json(repo)["skills"][0]
    assert skill["name"] == "demo"
    assert skill["has_skill_md"] is True
    assert skill["has_tests"] is True
    assert skill["test_files"] == ["test_demo.py"]
    assert skill["has_references"] and skill["has_scripts"] and skill["has_templates"]
    assert skill["empty_surface_dirs"] == []
    assert skill["design_doc"] == "docs/explanation/architecture/demo-design.md"
    assert skill["max_file_lines"] >= 1
    assert skill["oversized_files"] == []
    assert skill["cross_skill_links"] == []


def test_description_chars_counts_value_only(repo: Path):
    desc = "Use when testing."
    skill = collect_json(repo)["skills"][0]
    assert skill["description_chars"] == len(desc), "description_chars 只计值，不含 'description: ' 前缀"
    assert skill["frontmatter_chars"] > len(desc), "frontmatter_chars 计整个 frontmatter 正文"


def test_quoted_description_value_is_unwrapped(tmp_path: Path):
    root = build_repo(tmp_path / "repo2", skill_description='"Use when quoted."')
    skill = collect_json(root)["skills"][0]
    assert skill["description_chars"] == len("Use when quoted.")


def test_missing_surfaces_and_tests(tmp_path: Path):
    root = build_repo(tmp_path / "repo3")
    for rel in ("references", "scripts", "templates", "tests"):
        target = root / "skills" / "demo" / rel
        for f in sorted(target.rglob("*"), reverse=True):
            f.unlink() if f.is_file() else f.rmdir()
        target.rmdir()
    skill = collect_json(root)["skills"][0]
    assert skill["has_tests"] is False
    assert [skill["has_references"], skill["has_scripts"], skill["has_templates"]] == [False, False, False]


def test_empty_surface_dir_is_reported(tmp_path: Path):
    root = build_repo(tmp_path / "repo4")
    (root / "skills" / "demo" / "references" / "notes.md").unlink()
    skill = collect_json(root)["skills"][0]
    assert skill["empty_surface_dirs"] == ["references"]


def test_oversized_file_is_reported(tmp_path: Path):
    root = build_repo(tmp_path / "repo5")
    write(root / "skills" / "demo" / "references" / "big.md", "x\n" * 1001)
    skill = collect_json(root)["skills"][0]
    assert skill["oversized_files"] == ["skills/demo/references/big.md"]
    assert skill["max_file_lines"] == 1001


def test_cross_skill_link_is_detected(tmp_path: Path):
    root = build_repo(tmp_path / "repo6")
    write(root / "skills" / "demo" / "references" / "link.md",
          "见 [demo](../demo/SKILL.md) 与 [other](../../other/SKILL.md)\n")
    skill = collect_json(root)["skills"][0]
    assert any("link.md" in hit for hit in skill["cross_skill_links"])


def test_inline_code_link_is_not_flagged(tmp_path: Path):
    root = build_repo(tmp_path / "repo7")
    write(root / "skills" / "demo" / "references" / "ok.md", "示例 `[x](../demo/SKILL.md)` 不算链接\n")
    skill = collect_json(root)["skills"][0]
    assert skill["cross_skill_links"] == []


def test_registration_surfaces(repo: Path):
    reg = collect_json(repo)["skills"][0]["registrations"]
    assert reg == {"cross_skill_names": True, "docs_index": True, "readme": True, "collection": True}


def test_registration_gap_detected(tmp_path: Path):
    root = build_repo(tmp_path / "repo8")
    write(root / "tools" / "skills-manager" / "collections" / "cr-agent-arsenal.json",
          json.dumps({"skills": [{"source": "x", "mode": "all", "names": []}]}) + "\n")
    assert collect_json(root)["skills"][0]["registrations"]["collection"] is False


def test_root_prompt_facts_and_headings(repo: Path):
    rp = collect_json(repo)["root_prompt"]
    assert rp["path"] == "contexts/AGENTS.md"
    assert rp["lines"] == 11
    assert rp["baseline"]["lines"] == 11
    assert rp["headings"][0] == "# SYSTEM RULES"
    assert "## 3. 基础工程规范与防御底线 (Engineering Invariants)" in rp["headings"]
    assert "### 精准修改与代码卫生" in rp["headings"]
    assert "### 工具链与环境防御 (Read-Modify-Verify)" in rp["headings"]
    assert "### 质量门槛 (Definition of Done)" in rp["headings"]


def test_skill_filter_narrows_scope(tmp_path: Path):
    root = build_repo(tmp_path / "repo9")
    write(root / "skills" / "other" / "SKILL.md", "---\nname: other\ndescription: x\n---\n\n# other\n")
    names = [s["name"] for s in collect_json(root, "--skills", "demo")["skills"]]
    assert names == ["demo"]


def test_collector_is_read_only(repo: Path):
    before = snapshot(repo)
    out = repo / "_facts.json"
    r = run_collect(repo, "--no-gates", "--out", str(out))
    assert r.returncode == 0, r.stderr
    after = snapshot(repo, skip={"_facts.json"})
    assert after == before, "采集器在 --no-gates 下不得改动仓库内任何文件"


def test_missing_repo_root_exits_2(tmp_path: Path):
    r = run_collect(tmp_path / "nope", "--no-gates")
    assert r.returncode == 2, "用法/输入错误须以退出码 2 终止"
