# spec-evolution 实施计划 · 子册 Task 2（事实采集器与契约测试）

> **文档控制信息**
> - **文档标识**: PLAN-SPEC-EVOLUTION-2026-T2
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-12

> **母计划**: [2026-10-12-spec-evolution.md](./2026-10-12-spec-evolution.md)（本文件为原文逐字迁移，仅作历史实施细节，**不再增量维护**）

---

#### Task 2: 事实采集器 `collect-facts.py` 与契约测试

**Files:**
- Create: `skills/spec-evolution/scripts/collect-facts.py`
- Create: `skills/spec-evolution/tests/conftest.py`
- Create: `skills/spec-evolution/tests/test_collect_facts.py`

**Interfaces:**
- Consumes: `skills/spec-evolution/references/baseline.json` 的 `root_prompt.{lines,bytes}`（Task 1 产出）
- Produces:
  - CLI `python3 collect-facts.py [--repo-root PATH] [--out FILE] [--no-gates] [--skills a,b]`，退出码 `0`/`2`
  - `facts.json` 完整 schema（**Task 3 的 `judge.py` 按此消费，键名不得改动**）：

```
schema_version   str   固定 "1.0"
generated_at     str   ISO8601 带时区
repo_root        str   绝对路径
repo_head        str   git rev-parse --short HEAD，非 git 仓库时为 null
gates            obj|null   null 当且仅当 --no-gates；否则 4 个键
                          pytest/check_doc_links/audit_doc_health/cross_skill_links
                          每键 {cmd: str, exit_code: int, summary: str}
skills           array  按 name 升序
  name                str
  dirs                [str]  技能目录下顶层条目名，升序
  has_skill_md        bool
  has_tests           bool   tests/ 存在且含 test_*.py
  test_files          [str]  相对技能根的测试文件名，升序
  has_references      bool
  has_scripts         bool
  has_templates       bool
  empty_surface_dirs  [str]  references/scripts/templates 中「存在但为空」者，升序
  design_doc          str|null  仓库相对路径
  frontmatter_chars   int    frontmatter 正文（不含 --- 行）字符数；无 frontmatter 为 0
  description_chars   int    description 值字符数（去引号）；缺失为 0
  max_file_lines      int    技能内被扫描文件的最大行数
  oversized_files     [str]  行数 > 1000 的仓库相对路径，升序
  cross_skill_links   [str]  "skills/<n>/<file>:<line>"，升序
  registrations       obj    cross_skill_names/docs_index/readme/collection → bool
root_prompt      obj   {path, lines, bytes, baseline:{lines,bytes}, headings:[str]}
```

- [ ] **Step 1: 写失败测试——`tests/conftest.py`（合成仓库夹具）**

```python
"""spec-evolution 测试夹具：在 tmp_path 中合成一个最小可审计仓库。

不使用任何第三方依赖；所有夹具均为纯 `pathlib` 文件写入。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
COLLECT = REPO_ROOT / "skills" / "spec-evolution" / "scripts" / "collect-facts.py"
JUDGE = REPO_ROOT / "skills" / "spec-evolution" / "scripts" / "judge.py"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


DEFAULT_AGENTS_MD = (
    "# SYSTEM RULES\n"
    "\n"
    "## 3. 基础工程规范与防御底线 (Engineering Invariants)\n"
    "\n"
    "### 精准修改与代码卫生\n"
    "\n"
    "### 工具链与环境防御 (Read-Modify-Verify)\n"
    "\n"
    "### 质量门槛 (Definition of Done)\n"
    "\n"
    "正文。\n"
)


def make_skill_md(name: str, description: str, extra: str = "license: MIT") -> str:
    return f"---\nname: {name}\ndescription: {description}\n{extra}\n---\n\n# {name}\n\n正文。\n"


def build_repo(root: Path, *, skill_description: str = "Use when testing.",
               agents_md: str = DEFAULT_AGENTS_MD) -> Path:
    """合成一个含 1 个技能（demo）的最小仓库，且 demo 满足全部判据。

    `agents_md` 默认镜像真实 `contexts/AGENTS.md` §3 的 `###` 标题层级
    （精准修改与代码卫生 / 工具链与环境防御 / 质量门槛），以便 C-01/C-02 的
    `[RULE:§3-质量门槛]` 与 C-06 的 `[RULE:§3-精准修改与代码卫生]` 锚点可解析；
    传入精简版本可用于断言锚点校验失败路径。
    """
    write(root / "contexts" / "AGENTS.md", agents_md)
    write(root / "skills" / "demo" / "SKILL.md", make_skill_md("demo", skill_description))
    write(root / "skills" / "demo" / "references" / "notes.md", "# notes\n")
    write(root / "skills" / "demo" / "scripts" / "run.sh", "#!/bin/sh\nexit 0\n")
    write(root / "skills" / "demo" / "templates" / "tpl.md", "# tpl\n")
    write(root / "skills" / "demo" / "tests" / "test_demo.py", "def test_ok():\n    assert True\n")
    write(root / "docs" / "explanation" / "architecture" / "demo-design.md", "# demo design\n")
    write(root / "docs" / "index.md", "| demo | [demo 规程](../skills/demo/SKILL.md) |\n")
    write(root / "README.md", "| **`demo`** | [`skills/demo`](./skills/demo/SKILL.md) |\n")
    write(root / "tools" / "skills-manager" / "collections" / "cr-agent-arsenal.json",
          json.dumps({"skills": [{"source": "x", "mode": "all", "names": ["demo"]}]}, indent=2) + "\n")
    write(root / "skills" / "_shared" / "tests" / "test_cross_skill_links.py",
          'SKILL_NAMES = [\n    "demo",\n]\n\n\ndef test_ok():\n    assert True\n')
    # 门禁桩：让合成仓库能真的跑通四道门禁（GI-6 需要门禁真实执行后才可断言无残留产物）。
    # 这两个桩不放在 skills/<skill>/ 下带 SKILL.md 的目录中，故不会被 discover_skills 识别为技能。
    write(root / "skills" / "doc-governance" / "scripts" / "check-doc-links.py",
          "#!/usr/bin/env python3\nimport sys\n\nsys.exit(0)\n")
    write(root / "skills" / "doc-governance" / "scripts" / "audit-doc-health.py",
          "#!/usr/bin/env python3\nimport sys\n\nsys.exit(0)\n")
    write(root / "skills" / "spec-evolution" / "references" / "baseline.json",
          json.dumps({"root_prompt": {"path": "contexts/AGENTS.md",
                                      "lines": len(agents_md.splitlines()),
                                      "bytes": len(agents_md.encode("utf-8"))}}) + "\n")
    return root


def snapshot(root: Path, skip: set[str] | None = None) -> dict[str, tuple[int, int]]:
    """目录清单：{仓库相对路径: (字节数, mtime_ns)}，用于只读断言。"""
    skip = skip or set()
    out: dict[str, tuple[int, int]] = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if any(rel == s or rel.startswith(s + "/") for s in skip):
            continue
        if "__pycache__" in p.parts or ".git" in p.parts:
            continue
        st = p.stat()
        out[rel] = (st.st_size, st.st_mtime_ns)
    return out


def run_collect(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(COLLECT), "--repo-root", str(root), *args],
        capture_output=True, text=True, timeout=120,
    )


def run_judge(facts: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(JUDGE), "--facts", str(facts), *args],
        capture_output=True, text=True, timeout=120,
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    return build_repo(tmp_path / "repo")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -v`
Expected: FAIL —— 采集器脚本尚不存在（`can't open file ... collect-facts.py`）

- [ ] **Step 3: 写 `tests/test_collect_facts.py`**

```python
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
```

- [ ] **Step 4: 运行测试确认失败**

Run: `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -v`
Expected: FAIL —— `collect-facts.py` 不存在

- [ ] **Step 5: 写 `scripts/collect-facts.py`**

```python
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
     ["python3", "skills/doc-governance/scripts/check-doc-links.py", "--root", "docs"]),
    ("audit_doc_health",
     ["python3", "skills/doc-governance/scripts/audit-doc-health.py"]),
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
            "readme": f"skills/{name}" in readme_text,
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


def collect_gates(repo: Path) -> dict:
    gates = {}
    for key, cmd in GATES:
        try:
            proc = subprocess.run(cmd, cwd=str(repo), capture_output=True,
                                  text=True, timeout=GATE_TIMEOUT)
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
                              cwd=str(repo), capture_output=True, text=True, timeout=30)
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
```

- [ ] **Step 6: 运行测试确认通过**

Run: `python3 -m pytest skills/spec-evolution/tests/test_collect_facts.py -v`
Expected: PASS（全部用例绿）

- [ ] **Step 7: 对真实仓库冒烟，核对 F-1~F-9 事实**

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --out /tmp/facts.json
python3 - <<'PY'
import json
f = json.load(open('/tmp/facts.json'))
assert len(f['skills']) == 7, f"技能数应为 7，实际 {len(f['skills'])}"
by = {s['name']: s for s in f['skills']}
print('dual-round-review desc =', by['dual-round-review']['description_chars'], '(期望 738)')
print('clarification-protocol desc =', by['clarification-protocol']['description_chars'], '(期望 623)')
print('agy has_tests =', by['agy-delegation-workflow']['has_tests'], '(期望 False)')
print('doc-governance oversized =', by['doc-governance']['oversized_files'])
print('clarification registrations =', by['clarification-protocol']['registrations'])
print('root_prompt =', f['root_prompt']['lines'], f['root_prompt']['bytes'])
PY
```

期望：技能数 7；`dual-round-review` = 738；`clarification-protocol` = 623；`agy-delegation-workflow` `has_tests` = False；`doc-governance` `oversized_files` 含 `skills/doc-governance/tests/test_doc_governance_scripts.py`；`clarification-protocol` 的 `collection` 为 `False`（**F-9**）；`root_prompt` = 97 / 10746。

- [ ] **Step 8: 提交**

```bash
git add skills/spec-evolution/scripts/collect-facts.py skills/spec-evolution/tests/
git commit -m "feat(spec-evolution): 事实采集器 collect-facts.py 与契约测试

Task 2/7：只读采集 S1 门禁事实 / S2 结构事实 / S3 注册事实 → facts.json。
门禁调用统一加 -B 与 -p no:cacheprovider，保证只读不变式（GI-6）。
真实仓库冒烟核对 F-1/F-2/F-4/F-8/F-9 事实值。"
```

---

