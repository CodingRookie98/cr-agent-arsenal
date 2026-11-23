"""test_goal_loop_contract.py — goal-loop V3.0 交接脚本行为单测与轻量表面哨兵。"""
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
PACK_SCRIPT = SKILL_DIR / "scripts" / "pack-handoff.py"
PLAN_TEMPLATE = SKILL_DIR / "templates" / "goal-plan-template.md"
FENCE_RX = re.compile(r"^\s*(`{3,}|~{3,})")
FRONTMATTER_RX = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)

SAMPLE_PLAN = (
    "# 示例实施计划：认证模块重构\n\n### Active Checkpoint\n- **当前阶段**: `Execute`\n- **待办**: 完成 E-1 与 E-2\n\n---\n\n"
    "## 任务清单\n- [ ] **Task E-10**: 干扰项十号任务\n  - 不应被 E-1 误匹配\n"
    "- [ ] **Task E-1**: 实现令牌刷新接口\n  - 修改 `auth/refresh.py`\n  - 验收: `pytest tests/test_refresh.py`\n"
    "- [ ] **Task E-2**: 清理旧会话表\n  - 修改 `auth/cleanup.py`\n\n"
    "### W2A-1：标题型任务块\n- 验证标题形态匹配\n\n---\n\n"
    "## 3. 测试策略与验收门禁\n- 强制级别: L1 单元 + L2 集成\n"
    + "\n".join(f"- 策略明细行 {n}" for n in range(1, 45)) + "\n"
)


def _run_pack(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(PACK_SCRIPT), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False, env=env)


def _load_pack_module():
    spec = importlib.util.spec_from_file_location("pack_handoff_mod", PACK_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False)


def _parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RX.match(text)
    assert m, "SKILL.md 缺少合法 YAML frontmatter"
    body = m.group(1)
    if yaml is not None:
        parsed = yaml.safe_load(body)
        assert isinstance(parsed, dict), "frontmatter 顶层必须为 mapping"
        return parsed
    meta, lines, i = {}, body.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            i += 1
            continue
        key, sep, raw = ln.partition(":")
        assert sep, f"非法 YAML 行: {ln!r}"
        v = raw.strip()
        if v in (">", "|", ">-", "|-"):
            blk, i = [], i + 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                blk.append(lines[i].strip())
                i += 1
            meta[key.strip()] = " ".join(x for x in blk if x)
            continue
        v = v[1:-1] if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"') else v
        if not (len(raw.strip()) >= 2 and raw.strip()[0] == raw.strip()[-1] and raw.strip()[0] in ("'", '"')):
            assert not re.search(r":(?:\s|$)", v), f"{key} 含未加引号的 ': '"
        meta[key.strip()], i = v, i + 1
    return meta


def _fences_balanced(text: str) -> bool:
    fence = ""
    for line in text.splitlines():
        m = FENCE_RX.match(line)
        if not m:
            continue
        tok, rest = m.group(1), line[m.end():]
        if not fence and (tok[0] == "~" or "`" not in rest):
            fence = tok
        elif fence and tok[0] == fence[0] and len(tok) >= len(fence) and not rest.strip():
            fence = ""
    return not fence


def _init_sample_repo(repo: Path) -> tuple[str, str]:
    assert _git(repo, "init").returncode == 0
    commit_cmd = ("-c", "user.name=Tester", "-c", "user.email=tester@example.com", "commit")
    for fname, content, msg in (("base.txt", "v0\n", "chore: base commit"), ("alpha.py", "x = 1\n", "feat: add alpha module"), ("beta.py", "y = 2\n", "feat: add beta module")):
        (repo / fname).write_text(content, encoding="utf-8")
        assert _git(repo, "add", fname).returncode == 0 and _git(repo, *commit_cmd, "-m", msg).returncode == 0
        if fname == "base.txt":
            base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return base_sha, _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_brief_extracts_target_task_and_summary(tmp_path: Path):
    plan = tmp_path / "plan.md"
    plan.write_text(SAMPLE_PLAN, encoding="utf-8")
    r = _run_pack("brief", str(plan), "--task", "e-1")
    assert r.returncode == 0, r.stderr
    assert "# 示例实施计划：认证模块重构" in r.stdout and "Active Checkpoint" in r.stdout
    assert "## 3. 测试策略与验收门禁" in r.stdout and "策略明细行 30" in r.stdout and "策略明细行 44" not in r.stdout
    assert "**Task E-1**: 实现令牌刷新接口" in r.stdout and "修改 `auth/refresh.py`" in r.stdout
    assert "Task E-2" not in r.stdout and "Task E-10" not in r.stdout
    r_head = _run_pack("brief", str(plan), "--task", "W2A-1")
    assert r_head.returncode == 0 and "标题型任务块" in r_head.stdout


def test_brief_writes_out_file_and_errors_on_missing(tmp_path: Path):
    missing = _run_pack("brief", str(tmp_path / "nope.md"), "--task", "E-1")
    assert missing.returncode == 1 and missing.stderr.strip()
    plan = tmp_path / "plan.md"
    plan.write_text(SAMPLE_PLAN, encoding="utf-8")
    no_task = _run_pack("brief", str(plan), "--task", "E-999")
    assert no_task.returncode == 1 and no_task.stderr.strip()
    out = tmp_path / "nested" / "handoff" / "e1.md"
    r = _run_pack("brief", str(plan), "--task", "E-1", "--out", str(out))
    assert r.returncode == 0 and Path(r.stdout.strip()) == out
    content = out.read_text(encoding="utf-8")
    assert "**Task E-1**" in content and "Task E-2" not in content


def test_review_pkg_captures_multi_commit_range_and_out_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    base_sha, head_sha = _init_sample_repo(repo)
    r = _run_pack("review-pkg", base_sha, "HEAD", "--repo", str(repo))
    assert r.returncode == 0, r.stderr
    assert "feat: add alpha module" in r.stdout and "feat: add beta module" in r.stdout
    assert "alpha.py" in r.stdout and "beta.py" in r.stdout and f"git diff {base_sha}...{head_sha}" in r.stdout
    out = tmp_path / "out" / "review.md"
    r_out = _run_pack("review-pkg", base_sha, "--repo", str(repo), "--out", str(out))
    assert r_out.returncode == 0 and Path(r_out.stdout.strip()) == out and out.read_text(encoding="utf-8") == r.stdout


def test_review_pkg_rejects_invalid_ref_and_non_repo(tmp_path: Path):
    repo, plain = tmp_path / "repo", tmp_path / "plain_dir"
    repo.mkdir()
    plain.mkdir()
    _init_sample_repo(repo)
    for cmd in (
        ("review-pkg", "nonexistent-ref-xyz", "HEAD", "--repo", str(repo)),
        ("review-pkg", "--repo", str(repo), "--", "--all", "HEAD"),
        ("review-pkg", "HEAD", "--repo", str(plain)),
    ):
        res = _run_pack(*cmd)
        assert res.returncode == 1 and res.stderr.strip()


def test_skill_frontmatter_fences_and_core_surface():
    meta = _parse_frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    assert meta.get("name") == SKILL_DIR.name == "goal-loop" and str(meta.get("license", "")).strip().upper() == "MIT"
    desc = meta.get("description", "")
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 500, f"description 非法或超 500 字符: {len(desc)}"
    for path in sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in str(p)):
        assert _fences_balanced(path.read_text(encoding="utf-8")), f"围栏未闭合: {path.relative_to(SKILL_DIR)}"
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    for stage in ("Align", "Plan", "Execute", "Verify", "Close"):
        assert stage in skill_text, f"SKILL.md 缺少核心阶段声明: {stage}"
    assert "scripts/pack-handoff.py" in skill_text and PACK_SCRIPT.is_file()
    opt_text = (SKILL_DIR / "references" / "optional-skill-dependencies.md").read_text(encoding="utf-8")
    assert "不提问" in opt_text and "不得伪称已激活" in opt_text and (SKILL_DIR / "templates" / "goal-plan-template.md").is_file()


def test_brief_extracts_all_official_template_tasks_and_utf8_on_gbk():
    for task_id in ("E-0", "E-1", "E-2", "V-1", "V-2", "V-3", "C-1", "C-2"):
        r = _run_pack("brief", str(PLAN_TEMPLATE), "--task", task_id)
        assert r.returncode == 0, f"模板任务 {task_id} 抽取失败: {r.stderr}"
        assert f"Task {task_id}" in r.stdout and _fences_balanced(r.stdout)
    r_v2 = _run_pack("brief", str(PLAN_TEMPLATE), "--task", "V-2")
    assert "Task V-2（条件 · 仅前端产物交付）" in r_v2.stdout and "check-qa-report.py" in r_v2.stdout and "Task V-3" not in r_v2.stdout
    gbk_env = {**os.environ, "PYTHONIOENCODING": "gbk"}
    r_gbk = _run_pack("brief", str(PLAN_TEMPLATE), "--task", "V-2", env=gbk_env)
    assert r_gbk.returncode == 0 and "🚀" in r_gbk.stdout and "Task V-2" in r_gbk.stdout


def test_brief_task_id_boundaries_and_hyphen_compat(tmp_path: Path):
    plan = tmp_path / "ids.md"
    plan.write_text(
        "# 任务边界测试\n\n## 任务清单\n"
        "- [ ] **Task 1.1**: 子项一点一\n"
        "- [ ] **Task 1**: 主项一号\n"
        "- [ ] **Task E-1-a**: 分支项\n"
        "- [ ] **Task E-1**: 精确项\n"
        "- [ ] **Task-9**: 连字符九号\n",
        encoding="utf-8",
    )
    r1 = _run_pack("brief", str(plan), "--task", "1")
    assert r1.returncode == 0 and "主项一号" in r1.stdout and "子项一点一" not in r1.stdout
    re1 = _run_pack("brief", str(plan), "--task", "E-1")
    assert re1.returncode == 0 and "精确项" in re1.stdout and "分支项" not in re1.stdout
    for query in ("Task-9", "Task 9", "9"):
        r9 = _run_pack("brief", str(plan), "--task", query)
        assert r9.returncode == 0 and "连字符九号" in r9.stdout
    only_sub = tmp_path / "only_sub.md"
    only_sub.write_text("# 仅子项\n\n- [ ] **Task 1.1**: 子项\n- [ ] **Task E-1-a**: 分支\n", encoding="utf-8")
    assert _run_pack("brief", str(only_sub), "--task", "1").returncode == 1
    assert _run_pack("brief", str(only_sub), "--task", "E-1").returncode == 1


def test_brief_truncated_code_fence_stays_balanced_and_inline_backticks(tmp_path: Path):
    long_code = "\n".join(f"  echo step-{i}" for i in range(1, 45))
    plan = tmp_path / "fenced.md"
    plan.write_text(
        "# 围栏截断测试\n\n## 2. 测试策略与级别裁定\n- 命令清单:\n  ```bash\n"
        + long_code
        + "\n  ```\n\n---\n\n## 任务清单\n```inline```\n- [ ] **Task E-1**: 目标不应被吞噬\n",
        encoding="utf-8",
    )
    r = _run_pack("brief", str(plan), "--task", "E-1")
    assert r.returncode == 0, r.stderr
    assert _fences_balanced(r.stdout), f"截断后围栏失衡:\n{r.stdout}"
    assert "> ...（节选已截断）" in r.stdout and "## 目标任务\n- [ ] **Task E-1**: 目标不应被吞噬" in r.stdout
    mod = _load_pack_module()
    assert mod._fence_flags(["```inline```", "- [ ] Task E-1: ok"]) == [False, False]


def test_review_pkg_cjk_filenames_and_error_guards(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    base_sha, head_sha = _init_sample_repo(repo)
    (repo / "说明文档.md").write_text("# 中文路径测试\n", encoding="utf-8")
    commit_cmd = ("-c", "user.name=Tester", "-c", "user.email=tester@example.com", "commit")
    assert _git(repo, "add", "说明文档.md").returncode == 0 and _git(repo, *commit_cmd, "-m", "docs: add cjk file").returncode == 0
    r_cjk = _run_pack("review-pkg", base_sha, "HEAD", "--repo", str(repo))
    assert r_cjk.returncode == 0, r_cjk.stderr
    assert "- `说明文档.md`" in r_cjk.stdout and "\\350" not in r_cjk.stdout

    plan = tmp_path / "plan.md"
    plan.write_text(SAMPLE_PLAN, encoding="utf-8")
    bad_utf8 = tmp_path / "bad.md"
    bad_utf8.write_bytes(b"\xff\xfe\x80\x81")
    out_dir = tmp_path / "existing_dir"
    out_dir.mkdir()
    for cmd in (
        ("brief", str(plan), "--task", "E-1", "--out", ""),
        ("brief", str(plan), "--task", "E-1", "--out", str(out_dir)),
        ("brief", str(bad_utf8), "--task", "E-1"),
        ("review-pkg", head_sha, head_sha, "--repo", str(repo)),
        ("review-pkg", "HEAD", base_sha, "--repo", str(repo)),
    ):
        res = _run_pack(*cmd)
        assert res.returncode == 1 and res.stderr.strip() and "Traceback" not in res.stderr, f"意外结果 {cmd}: rc={res.returncode}, err={res.stderr}"
    no_git = _run_pack("review-pkg", base_sha, "HEAD", "--repo", str(repo), env={**os.environ, "PATH": ""})
    assert no_git.returncode == 1 and no_git.stderr.strip() and "Traceback" not in no_git.stderr


def test_retired_and_corrupted_tokens_do_not_regress():
    retired = (
        "goal-state-tracker",
        "HALF-OPEN",
        "2-Action Rule",
        "docs/project/evaluation/",
        "docs/architecture/",
        "evaluation-report-template",
        "research-spike-template",
        "create_goal",
        "get_goal",
        "update_goal",
        "docs/design/",
        "docs/adr/",
        "阶段 3.5",
    )
    for path in (SKILL_MD, *sorted((SKILL_DIR / "references").glob("*.md")), *sorted((SKILL_DIR / "templates").glob("*.md"))):
        text = path.read_text(encoding="utf-8")
        for token in retired:
            assert token not in text, f"已退役/腐化词回流进 {path.relative_to(SKILL_DIR)}: {token}"
