"""test_gate_invariants.py — RFC-0004 §3.7 的 GI-1~GI-6 回归门禁。

对象是 spec-evolution 自身：确定性、留白、锚点一致、退出码语义、只读。
"""

import ast
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from conftest import COLLECT, build_repo, run_collect, run_judge

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


def test_gi6_rejects_pycache_prefix_inside_repo(tmp_path):
    """重定向根落在仓库内时必须 fail-closed（退出码 2），不得静默写进仓库。

    `PYTHONPYCACHEPREFIX` 是压制字节码的唯一充分机制（见 `subprocess_env`），但它的
    取值来自 `tempfile.gettempdir()`：受 `TMPDIR` 影响，且候选临时目录全不可写时
    回落 `os.getcwd()`。两条路都能把它指回**仓库内**，使 GI-6 静默失守
    （Delta R1 实测：`TMPDIR=<repo>` 的副本内新增 3 个镜像文件）。

    本用例把「仓库之外」从注释承诺钉成可执行契约：越界即退出码 2 + 仓库零写入。
    """
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = subprocess.run(
        [sys.executable, "-B", str(COLLECT), "--repo-root", str(root),
         "--out", str(tmp_path / "facts.json")],
        capture_output=True, text=True, env={**os.environ, "TMPDIR": str(root)},
    )
    assert proc.returncode == 2, f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    assert "仓库内" in proc.stderr, proc.stderr
    assert _files(root) == before, "GI-6：越界路径下仍写入了仓库"


def test_gi6_pycache_prefix_is_per_run_and_private(tmp_path):
    """重定向根必须**每次运行独占、随机、0700** —— 否则 /tmp 缓存投毒成立。

    `/tmp` 是 `drwxrwxrwt`：固定目录名可被本地用户抢先创建并植入与门禁模块同尺寸
    同 mtime 的畸形成员字节码，被门禁进程当作真实模块读取执行
    （Delta R1 R1-2 实测：注入代码已执行）。`mkdtemp` 的随机名 + 独占创建 + 0700
    是关闭该通道的最小充分形态。
    """
    root = build_repo(tmp_path / "repo")
    collect = SPEC_DIR / "scripts" / "collect-facts.py"
    script = (
        "import importlib.util, os, pathlib, stat\n"
        f"spec = importlib.util.spec_from_file_location('cf', {str(collect)!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        f"p = mod.pycache_prefix(pathlib.Path({str(root)!r}).resolve())\n"
        "print(p, oct(stat.S_IMODE(os.stat(p).st_mode)))\n"
    )
    seen = set()
    for _ in range(2):
        proc = subprocess.run([sys.executable, "-B", "-c", script],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        path, mode = proc.stdout.split()
        assert mode == "0o700", f"重定向根权限 {mode}，非独占私有"
        assert str(root) not in path, f"重定向根落在仓库内: {path}"
        seen.add(path)
    assert len(seen) == 2, f"重定向根可预测（两次同路径 {seen}）——缓存投毒通道未关闭"


def test_gi6_bytecode_suppression_is_structural():
    """GI-6 的结构性保障：`subprocess.run` 必须注入 env，且 env 必须含**两重**抑制。

    只给命令加 `-B` 不够 —— 它只覆盖直接子进程。完整的抑制链是：
    `-B`（直接子进程）→ `PYTHONDONTWRITEBYTECODE`（经 `subprocess` 派生的孙进程，
    `-B` 是命令行开关、不随环境传递）→ `PYTHONPYCACHEPREFIX`（显式
    `py_compile.compile()` 的写入，它按设计同时无视前两者）。

    本断言把后两者钉死在 `subprocess_env()` 的**返回字典字面量**上（而非仅仅
    「源码里出现过这个字符串」），并把 `env=None` 这种「形式上有 env、实质放弃
    抑制」的写法一并拒掉 —— 否则一次合法重构就能让测试全绿而 GI-6 已经失守。
    （RFC-0004 交付审查 R1-1 / R1-9；Delta R1 DR1-1 补强）
    """
    src = (SPEC_DIR / "scripts" / "collect-facts.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    env_fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "subprocess_env"), None)
    assert env_fn is not None, "采集器缺少 subprocess_env()（GI-6）"
    injected: set[str] = set()
    for node in ast.walk(env_fn):
        if isinstance(node, ast.Dict):
            injected |= {k.value for k in node.keys
                         if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    for var in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"):
        assert var in injected, f"subprocess_env() 未注入 {var}（GI-6：字节码抑制链不完整）"

    runs = [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "run" and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "subprocess"]
    assert runs, "采集器应当至少有一处 subprocess.run（git_head 或门禁）"
    for call in runs:
        kw = {k.arg: k.value for k in call.keywords}
        assert "env" in kw, f"collect-facts.py:{call.lineno} 的 subprocess.run 未注入 env（GI-6）"
        assert not (isinstance(kw["env"], ast.Constant) and kw["env"].value is None), (
            f"collect-facts.py:{call.lineno} 的 env=None 会放任孙进程写字节码（GI-6）")


def test_gates_recorded_when_enabled(tmp_path):
    root = build_repo(tmp_path / "repo")
    out = tmp_path / "facts.json"
    proc = run_collect(root, "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    gates = json.loads(out.read_text(encoding="utf-8"))["gates"]
    assert set(gates) == {"pytest", "check_doc_links", "audit_doc_health", "cross_skill_links"}
    assert all(g["exit_code"] == 0 for g in gates.values()), gates
