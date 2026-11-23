"""test_skill_surface_sentinels.py — 仓库级技能交付面与注册面哨兵测试。

承接自退役技能 spec-evolution 中不可被 doc-governance / _shared 替代的三项硬护栏
（详见 ADR-0003）：
1. C-01：每个技能均具备 tests/ 且至少包含一条 test_*.py；
2. C-05 + YAML：SKILL.md frontmatter 为合法 YAML、name 与目录同名、license 为 MIT、
   description 非空且长度 < 1024（防宿主静默丢弃或未加引号的 ": " 解析失败）；
3. C-07：技能清单与四个注册面严格一致（test_cross_skill_links.SKILL_NAMES、
   cross-skill-link-policy.json、cr-agent-arsenal.json、README.md、docs/index.md），
   既防新增漏登记，也防已删除技能残留幻影条目。
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - 仅无 PyYAML 的纯标准库环境触发
    yaml = None

REPO_ROOT = Path(__file__).resolve().parents[3]
NON_SKILL_DIRS = {"_shared"}
DESC_HARD_LIMIT = 1024

FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
README_SKILL_LINK_RX = re.compile(r"\]\((?:\./)?skills/([a-z0-9_-]+)/SKILL\.md\)")
INDEX_SKILL_LINK_RX = re.compile(r"\]\(\.\./skills/([a-z0-9_-]+)/SKILL\.md\)")
UNQUOTED_COLON_SPACE_RX = re.compile(r":(?:\s|$)")


def discover_skill_dirs(repo_root: Path = REPO_ROOT) -> list[Path]:
    """返回 skills/ 下所有非隐藏、非 _shared 的子目录。"""
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return []
    return sorted(
        p for p in skills_root.iterdir()
        if p.is_dir() and p.name not in NON_SKILL_DIRS and not p.name.startswith(".")
    )


def _fallback_parse_frontmatter(body: str) -> tuple[dict | None, str | None]:
    """无 PyYAML 时的最小 frontmatter 校验，显式拦截未引号的 ': ' 陷阱。"""
    meta: dict[str, str] = {}
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            return None, f"非法 YAML 键值对行: {line!r}"
        key, raw_val = line.split(":", 1)
        key = key.strip()
        val = raw_val.strip()
        if val in (">", "|", ">-", "|-"):
            block_lines: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block_lines.append(lines[i].strip())
                i += 1
            meta[key] = " ".join(x for x in block_lines if x)
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            meta[key] = val[1:-1]
        else:
            if UNQUOTED_COLON_SPACE_RX.search(val):
                return None, f"字段 {key} 含未加引号的 ': '，YAML 将解析失败"
            meta[key] = val
        i += 1
    return meta, None


def parse_skill_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """解析 SKILL.md frontmatter；返回 (dict, None) 或 (None, error_message)。"""
    match = FRONTMATTER_RX.match(text)
    if not match:
        return None, "缺少合法的 YAML frontmatter 分隔符 ---"
    body = match.group(1)
    if yaml is not None:
        try:
            parsed = yaml.safe_load(body)
        except yaml.YAMLError as exc:
            return None, f"YAML 解析失败: {exc}"
        if not isinstance(parsed, dict):
            return None, f"frontmatter 顶层必须为 mapping，实测: {type(parsed).__name__}"
        return parsed, None
    return _fallback_parse_frontmatter(body)


def _extract_skill_names_ast(test_file: Path) -> set[str]:
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SKILL_NAMES":
                    values = ast.literal_eval(node.value)
                    return set(values)
    raise AssertionError(f"{test_file} 未找到 SKILL_NAMES 列表赋值")


def check_surface_contracts(repo_root: Path = REPO_ROOT) -> list[str]:
    """收集跨技能交付面与注册面的全部缺陷，空列表表示全通过。"""
    issues: list[str] = []
    dirs = discover_skill_dirs(repo_root)
    if not dirs:
        return ["skills/ 下未发现任何技能目录"]

    skill_names: set[str] = set()
    for skill_dir in dirs:
        name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            issues.append(f"skills/{name}: 缺少 SKILL.md（非技能目录请移出或放入 _shared）")
            continue
        skill_names.add(name)

        # C-01: 技能必须具备可回归的 tests/test_*.py
        tests_dir = skill_dir / "tests"
        test_files = list(tests_dir.glob("test_*.py")) if tests_dir.is_dir() else []
        if not test_files:
            issues.append(f"C-01: skills/{name} 缺少 tests/test_*.py")

        # C-05 + YAML: frontmatter 合法性、name/license 与 description < 1024 硬限
        meta, err = parse_skill_frontmatter(skill_md.read_text(encoding="utf-8"))
        if err is not None or meta is None:
            issues.append(f"C-05/YAML: skills/{name}/SKILL.md {err}")
            continue
        if meta.get("name") != name:
            issues.append(f"YAML: skills/{name}/SKILL.md name={meta.get('name')!r} 与目录名不一致")
        if str(meta.get("license", "")).strip().upper() != "MIT":
            issues.append(f"YAML: skills/{name}/SKILL.md license={meta.get('license')!r}（期望 MIT）")
        desc = meta.get("description")
        if not isinstance(desc, str) or not desc.strip():
            issues.append(f"C-05: skills/{name}/SKILL.md 缺少非空字符串 description")
        elif len(desc) >= DESC_HARD_LIMIT:
            issues.append(
                f"C-05: skills/{name}/SKILL.md description 为 {len(desc)} 字符（硬限 < {DESC_HARD_LIMIT}）"
            )

    # C-07: 四处注册面 + 策略文件与实际技能集合严格双向对齐
    surfaces: dict[str, set[str]] = {}
    cross_test = repo_root / "skills" / "_shared" / "tests" / "test_cross_skill_links.py"
    if cross_test.is_file():
        surfaces["test_cross_skill_links.SKILL_NAMES"] = _extract_skill_names_ast(cross_test)
    else:
        issues.append("C-07: 缺少 skills/_shared/tests/test_cross_skill_links.py")

    policy_file = repo_root / "skills" / "_shared" / "cross-skill-link-policy.json"
    if policy_file.is_file():
        policy = json.loads(policy_file.read_text(encoding="utf-8"))
        surfaces["cross-skill-link-policy.covered"] = set(policy.get("coverage", {}).get("covered", []))
        surfaces["cross-skill-link-policy.forbidden"] = set(policy.get("forbidden_skill_names", []))
    else:
        issues.append("C-07: 缺少 skills/_shared/cross-skill-link-policy.json")

    collection_file = repo_root / "tools" / "skills-manager" / "collections" / "cr-agent-arsenal.json"
    if collection_file.is_file():
        col = json.loads(collection_file.read_text(encoding="utf-8"))
        col_names: list[str] = []
        for entry in col.get("skills", []):
            col_names.extend(entry.get("names", []))
        if len(col_names) != len(set(col_names)):
            issues.append("C-07: cr-agent-arsenal.json 存在重复技能名")
        surfaces["cr-agent-arsenal.json"] = set(col_names)
    else:
        issues.append("C-07: 缺少 tools/skills-manager/collections/cr-agent-arsenal.json")

    readme_file = repo_root / "README.md"
    if readme_file.is_file():
        surfaces["README.md"] = set(README_SKILL_LINK_RX.findall(readme_file.read_text(encoding="utf-8")))
    else:
        issues.append("C-07: 缺少 README.md")

    index_file = repo_root / "docs" / "index.md"
    if index_file.is_file():
        surfaces["docs/index.md"] = set(INDEX_SKILL_LINK_RX.findall(index_file.read_text(encoding="utf-8")))
    else:
        issues.append("C-07: 缺少 docs/index.md")

    for surface_name, registered in sorted(surfaces.items()):
        missing = sorted(skill_names - registered)
        phantom = sorted(registered - skill_names)
        if missing:
            issues.append(f"C-07: {surface_name} 漏登记技能: {missing}")
        if phantom:
            issues.append(f"C-07: {surface_name} 含不存在的残留技能: {phantom}")

    return issues


# --- 真实仓库哨兵测试 -----------------------------------------------------------

def test_repo_skill_surface_sentinels_pass():
    issues = check_surface_contracts(REPO_ROOT)
    assert not issues, "技能交付面或注册面哨兵检测到缺陷:\n- " + "\n- ".join(issues)


# --- 合成仓库负向自检（防止哨兵恒真） ---------------------------------------------

def _make_minimal_repo(root: Path, skill_name: str = "alpha-skill", desc: str = "Valid skill description.") -> None:
    sdir = root / "skills" / skill_name
    (sdir / "tests").mkdir(parents=True, exist_ok=True)
    (sdir / "tests" / "test_contract.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (sdir / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: {desc}\nlicense: MIT\n---\n\n# {skill_name}\n",
        encoding="utf-8",
    )
    shared = root / "skills" / "_shared"
    (shared / "tests").mkdir(parents=True, exist_ok=True)
    (shared / "tests" / "test_cross_skill_links.py").write_text(
        f'SKILL_NAMES = [\n    "{skill_name}",\n]\n', encoding="utf-8"
    )
    (shared / "cross-skill-link-policy.json").write_text(
        json.dumps({"coverage": {"covered": [skill_name]}, "forbidden_skill_names": [skill_name]}),
        encoding="utf-8",
    )
    col = root / "tools" / "skills-manager" / "collections"
    col.mkdir(parents=True, exist_ok=True)
    (col / "cr-agent-arsenal.json").write_text(
        json.dumps({"skills": [{"names": [skill_name]}]}), encoding="utf-8"
    )
    (root / "README.md").write_text(f"[`{skill_name}`](./skills/{skill_name}/SKILL.md)\n", encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "index.md").write_text(f"[{skill_name}](../skills/{skill_name}/SKILL.md)\n", encoding="utf-8")


def test_sentinel_catches_missing_tests_and_missing_skill_md(tmp_path: Path):
    _make_minimal_repo(tmp_path)
    assert check_surface_contracts(tmp_path) == []

    (tmp_path / "skills" / "alpha-skill" / "tests" / "test_contract.py").unlink()
    issues = check_surface_contracts(tmp_path)
    assert any("C-01" in item and "alpha-skill" in item for item in issues), issues

    (tmp_path / "skills" / "ghost-dir").mkdir()
    issues = check_surface_contracts(tmp_path)
    assert any("ghost-dir" in item and "SKILL.md" in item for item in issues), issues


def test_sentinel_catches_description_limit_and_yaml_colon_trap(tmp_path: Path):
    _make_minimal_repo(tmp_path, desc="x" * 1024)
    issues = check_surface_contracts(tmp_path)
    assert any("C-05" in item and "1024" in item for item in issues), issues

    _make_minimal_repo(tmp_path, desc="Use when: unquoted colon breaks npx skills")
    issues = check_surface_contracts(tmp_path)
    assert any("YAML" in item for item in issues), issues

    # 同时验证无 PyYAML 时的降级解析器也能拦住未加引号的 ": "
    meta, err = _fallback_parse_frontmatter("name: demo\ndescription: Use when: unquoted\nlicense: MIT\n")
    assert meta is None and err is not None and "': '" in err


def test_sentinel_catches_missing_and_phantom_registrations(tmp_path: Path):
    _make_minimal_repo(tmp_path)
    (tmp_path / "README.md").write_text("empty\n", encoding="utf-8")
    (tmp_path / "tools" / "skills-manager" / "collections" / "cr-agent-arsenal.json").write_text(
        json.dumps({"skills": [{"names": ["alpha-skill", "retired-skill"]}]}), encoding="utf-8"
    )
    issues = check_surface_contracts(tmp_path)
    assert any("README.md" in item and "漏登记" in item for item in issues), issues
    assert any("cr-agent-arsenal.json" in item and "retired-skill" in item for item in issues), issues
