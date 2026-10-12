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


def base_facts(root: Path) -> dict:
    """在合成仓库上跑一次 `--no-gates` 采集，返回可被测试点状修改的 facts 字典。"""
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))
