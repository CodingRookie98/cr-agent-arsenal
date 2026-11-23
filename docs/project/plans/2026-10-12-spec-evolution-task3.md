# spec-evolution 实施计划 · 子册 Task 3（判定器与判定契约测试）

> **文档控制信息**
> - **文档标识**: PLAN-SPEC-EVOLUTION-2026-T3
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-12
> - **状态**: 母计划子册（历史原文归档，不再增量维护）

> **母计划**: [2026-10-12-spec-evolution.md](./2026-10-12-spec-evolution.md)（本文件为原文逐字迁移，仅作历史实施细节，**不再增量维护**）

---

#### Task 3: 判定器 `judge.py`、报告模板与判定契约测试

**Files**
- Create: `skills/spec-evolution/scripts/judge.py`
- Create: `skills/spec-evolution/templates/evolution-report.md`
- Create: `skills/spec-evolution/tests/test_judge_contract.py`
- Modify: `skills/spec-evolution/tests/conftest.py`（仅**追加** `base_facts()` 便利函数，不改既有签名）

**Goal**：把 `facts.json` 确定性映射为 finding 列表与演进报告；实现三锚点存在性硬门禁（GI-3）与人类裁决区留白（GI-4）。

> **执行偏差记录 (Deviation Log) —— 2026-10-12 P3 执行期实测修正**
>
> 本任务块下方内嵌的代码为设计稿；实际实现以 `skills/spec-evolution/scripts/judge.py` 为准。执行期实测发现 5 处设计稿缺陷，已按下表修正（修正同时回写本计划与 `references/checks-spec.md`）：
>
> | # | 缺陷 | 修正 | 依据 |
> | :--- | :--- | :--- | :--- |
> | D-1 | 夹具 `DEFAULT_AGENTS_MD` 使用了 `### 禁止占位符与规模控制 (No Placeholders / Size Limits)` 标题，该标题在真实 `contexts/AGENTS.md` 中**不存在**（真实 §3 的 H3 只有 精准修改与代码卫生 / 工具链与环境防御 / 质量门槛；「禁止占位符与规模控制」是前者下的**加粗条目**） | 夹具标题改为 `### 工具链与环境防御 (Read-Modify-Verify)`，镜像真实层级（行数仍为 11，故 `test_root_prompt_facts_and_headings` 的 `lines == 11` 断言不变） | 实测 `grep -n '^###' contexts/AGENTS.md` |
> | D-2 | `RULE_SIZE = "[RULE:§3-禁止占位符与规模控制]"` 在真实仓库**无法解析**，导致 `judge.py` 恒以退出码 2 拒绝产出（工具不可用） | 改为 `"[RULE:§3-精准修改与代码卫生]"` | `references/anchor-contract.md:13` 早已声明该锚点示例；RFC-0004 §3.4 的锚点契约是**标题树**，不含加粗条目 |
> | D-3 | 设计稿按**嵌套** schema 消费 facts（`sk["paths"]["has_tests"]`、`sk["missing_surfaces"]`、`sk["registration"][s]["registered"]`），与 Task 2 已冻结的**扁平** schema 不一致 | `judge.py` 改按扁平 schema 消费（`sk["has_tests"]`；缺失面由 `has_references/has_scripts/has_templates` 推导；`sk["registrations"][s]` 为布尔），并新增 `REGISTRATION_SURFACES` 常量把 4 个注册面映射到 `[REPO:*]` 锚点路径 | Task 2 Interfaces 明示「`facts.json` schema 键名不得改动」 |
> | D-4 | `--no-gates` 时 `facts["gates"] is None`，设计稿的 `sorted(facts["gates"].items())` 抛 `AttributeError` | `build_findings` 与 `render_report` 均改用 `facts.get("gates") or {}` | 实测 `test_clean_repo_yields_no_findings` 路径 |
> | D-5 | `load_facts` 用 `raise SystemExit("❌ …")` 表达输入错误，但 `SystemExit` 携带非空字符串时退出码为 **1**，与契约「2 = 用法或输入错误」冲突 | 新增 `FactsError` 异常，`main()` 捕获后 `return 2` | RFC-0004 §3.3 退出码契约 |
>
> 另：`test_report_and_json_written_to_requested_paths` 的旧注记已过时（`_run` 恒传 `--json`，该断言实际检查的是**未被请求**的路径不存在），实现时按新注记执行。

- [ ] **Step 1: 写入 `skills/spec-evolution/scripts/judge.py`**

```python
#!/usr/bin/env python3
"""spec-evolution 判定器 judge.py —— 把 facts.json 转成结构化 finding 与演进报告。

确定性、零 LLM、零网络。判定语义与退出码见 skills/spec-evolution/references/checks-spec.md。

退出码：
  0 = 无 BLOCKER / HIGH
  1 = 存在 HIGH 或 BLOCKER
  2 = 输入无效、facts 结构不合法、或 finding 锚点不可解析
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "1.0"
SEVERITY_ORDER = {"BLOCKER": 0, "HIGH": 1, "MID": 2}
DESC_SOFT_LIMIT = 500
DESC_HARD_LIMIT = 1024
REQUIRED_TOP_KEYS = ("repo_root", "skills", "gates", "root_prompt")

RULE_DOD = "[RULE:§3-质量门槛]"
RULE_SIZE = "[RULE:§3-精准修改与代码卫生]"

GATE_ANCHORS = {
    "pytest": "skills/",
    "check_doc_links": "skills/doc-governance/scripts/check-doc-links.py",
    "audit_doc_health": "skills/doc-governance/scripts/audit-doc-health.py",
    "cross_skill_links": "skills/_shared/tests/test_cross_skill_links.py",
}

SKILL_ANCHOR_RX = re.compile(r"^\[SKILL:([^/\]]+)/([^\]:]+)(?::(\d+))?\]$")
REPO_ANCHOR_RX = re.compile(r"^\[REPO:([^\]:]+)(?::(\d+))?\]$")
RULE_ANCHOR_RX = re.compile(r"^\[RULE:§(\d+)-(.+)\]$")
H2_RX = re.compile(r"^##\s+(\d+)\.\s*(.*)$")
H3_RX = re.compile(r"^###\s+(.*)$")

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "evolution-report.md"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def validate_anchor(anchor: str, repo_root: Path, headings: list) -> str | None:
    """锚点可解析返回 None，否则返回人可读的失败原因。"""
    m = SKILL_ANCHOR_RX.match(anchor)
    if m:
        name, rel, line = m.group(1), m.group(2), m.group(3)
        target = repo_root / "skills" / name / rel
        if not target.exists():
            return f"技能锚点文件不存在: skills/{name}/{rel}"
        if line is not None and int(line) > _count_lines(target):
            return f"技能锚点行号越界: skills/{name}/{rel}:{line}（共 {_count_lines(target)} 行）"
        return None
    m = REPO_ANCHOR_RX.match(anchor)
    if m:
        rel, line = m.group(1), m.group(2)
        target = repo_root / rel
        if not target.exists():
            return f"仓库锚点路径不存在: {rel}"
        if line is not None and int(line) > _count_lines(target):
            return f"仓库锚点行号越界: {rel}:{line}（共 {_count_lines(target)} 行）"
        return None
    m = RULE_ANCHOR_RX.match(anchor)
    if m:
        section, title = m.group(1), _norm(m.group(2))
        current = None
        for heading in headings:
            h2 = H2_RX.match(heading)
            if h2:
                current = h2.group(1)
                continue
            h3 = H3_RX.match(heading)
            if h3 and current == section and _norm(h3.group(1)).startswith(title):
                return None
        return f"根提示词锚点无对应标题: {anchor}"
    return f"锚点格式非法: {anchor}"


def _mk(criterion, severity, skill, anchor, rule, evidence_cmd, observed, expected, message):
    return {
        "id": None,
        "criterion": criterion,
        "severity": severity,
        "skill": skill,
        "anchor": anchor,
        "rule": rule,
        "evidence_cmd": evidence_cmd,
        "observed": observed,
        "expected": expected,
        "message": message,
    }


def build_findings(facts: dict) -> list:
    out: list = []

    for key, info in sorted(facts["gates"].items()):
        if info.get("exit_code") != 0:
            out.append(_mk(
                "C-09", "BLOCKER", "<repo>",
                f"[REPO:{GATE_ANCHORS.get(key, 'skills/')}]", None, info.get("cmd", ""),
                f"exit_code={info.get('exit_code')}", "exit_code == 0",
                "既有门禁非零退出，交付基线不成立。"))

    for sk in facts["skills"]:
        name = sk["name"]
        skill_anchor = f"[SKILL:{name}/SKILL.md]"

        if not sk["paths"]["has_tests"]:
            out.append(_mk(
                "C-01", "HIGH", name, skill_anchor, RULE_DOD,
                f"ls skills/{name}/tests", "目录不存在", "存在 tests/ 且至少 1 个 test_*.py",
                "技能缺少契约测试，其判据不可机械回归。"))

        if not sk["design_doc"]:
            out.append(_mk(
                "C-02", "MID", name, skill_anchor, RULE_DOD,
                f"test -f docs/explanation/architecture/{name}-design.md", "文件不存在",
                "存在架构设计书", "技能无架构设计书，架构决策不可追溯。"))

        if sk["missing_surfaces"] or sk["empty_surface_dirs"]:
            parts = []
            if sk["missing_surfaces"]:
                parts.append("缺失: " + ", ".join(sk["missing_surfaces"]))
            if sk["empty_surface_dirs"]:
                parts.append("为空: " + ", ".join(sk["empty_surface_dirs"]))
            out.append(_mk(
                "C-03", "MID", name, skill_anchor, None, f"ls skills/{name}",
                "；".join(parts), "references/scripts/templates 存在且非空",
                "技能交付面不完整。"))

        chars = sk["description_chars"]
        if chars >= DESC_HARD_LIMIT:
            out.append(_mk(
                "C-05", "HIGH", name, skill_anchor, None,
                f"python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills {name}",
                f"{chars} 字符", f"< {DESC_HARD_LIMIT} 字符（规范硬限）",
                "description 超过规范硬限，技能会被宿主静默丢弃。"))
        elif chars > DESC_SOFT_LIMIT:
            out.append(_mk(
                "C-04", "MID", name, skill_anchor, None,
                f"python3 skills/spec-evolution/scripts/collect-facts.py --no-gates --skills {name}",
                f"{chars} 字符", f"≤ {DESC_SOFT_LIMIT} 字符（建议值）",
                "description 超出仓库建议上限，常驻注入成本偏高。"))

        for rel in sk["oversized_files"]:
            short = rel.split("/", 2)[2] if rel.count("/") >= 2 else rel
            out.append(_mk(
                "C-06", "MID", name, f"[SKILL:{name}/{short}]", RULE_SIZE,
                f"wc -l {rel}", "超过 1000 行", "单文件 ≤ 1000 行",
                "单文件越过规模红线，拆分前不得新增内容。"))

        for surface, info in sorted(sk["registration"].items()):
            if not info["registered"]:
                out.append(_mk(
                    "C-07", "HIGH", name, f"[REPO:{info['path']}]", None,
                    f"grep -nF '{name}' {info['path']}", info["detail"],
                    "注册面已登记", f"注册面 {surface} 缺登记，技能无法被发现。"))

        for link in sk["cross_skill_links"]:
            short = link.split("/", 2)[2] if link.count("/") >= 2 else link
            out.append(_mk(
                "C-08", "HIGH", name, f"[SKILL:{name}/{short}]", None,
                "python3 -m pytest skills/_shared/tests/test_cross_skill_links.py -q",
                link, "无跨技能相对链接", "跨技能相对链接在单技能安装后断链。"))

    rp = facts["root_prompt"]
    baseline = rp.get("baseline") or {}
    grew = [
        f"{key}: {baseline[key]} -> {rp[key]}"
        for key in ("lines", "bytes")
        if key in baseline and rp[key] > baseline[key]
    ]
    if grew:
        out.append(_mk(
            "C-10", "MID", "<repo>", f"[REPO:{rp['path']}]", None,
            f"wc -l {rp['path']}", "；".join(grew), "不超过 baseline",
            "根提示词净增长，须同提交给出等量删减或不可压缩理由。"))

    out.sort(key=lambda f: (
        SEVERITY_ORDER[f["severity"]], f["skill"], f["criterion"],
        f["anchor"], f["evidence_cmd"], f["observed"]))
    for i, f in enumerate(out, 1):
        f["id"] = f"F-{i:02d}"
    return out


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(facts: dict, findings: list) -> str:
    raw_gates = facts.get("gates")
    gates = raw_gates or {}
    failed = [(k, v) for k, v in sorted(gates.items()) if v.get("exit_code") != 0]
    if failed:
        lines = ["| 门禁 | 证据命令 | 退出码 | 摘要 |", "| :--- | :--- | :--- | :--- |"]
        for key, info in failed:
            lines.append("| {} | `{}` | {} | {} |".format(
                key, _cell(info.get("cmd", "")), info.get("exit_code"),
                _cell(info.get("summary", ""))))
        blocker_section = "## BLOCKER\n\n" + "\n".join(lines)
    elif raw_gates is None:
        blocker_section = ("## BLOCKER\n\n（未采集门禁事实 —— C-09 未执行；"
                           "本报告对既有门禁是否失败不作任何结论）")
    else:
        blocker_section = "## BLOCKER\n\n（已采集门禁事实，无失败）"

    rest = [f for f in findings if f["severity"] != "BLOCKER"]
    if rest:
        rows = ["| ID | 判据 | 严重度 | 技能 | 锚点 | 实测 | 期望 | 证据命令 |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
        for f in rest:
            rows.append("| {} | {} | {} | {} | {} | {} | {} | `{}` |".format(
                f["id"], f["criterion"], f["severity"], _cell(f["skill"]),
                _cell(f["anchor"]), _cell(f["observed"]), _cell(f["expected"]),
                _cell(f["evidence_cmd"])))
        findings_table = "\n".join(rows)
    else:
        findings_table = "（无）"

    verdict_rows = ["| ID | 裁决 | 裁决人 | 裁决日期 | 驳回理由 |",
                    "| :--- | :--- | :--- | :--- | :--- |"]
    for f in findings:
        verdict_rows.append(f"| {f['id']} | [ ] 采纳 / [ ] 驳回 | | | |")
    if not findings:
        verdict_rows.append("| — | （无 finding，无需裁决） | | | |")
    verdict_table = "\n".join(verdict_rows)

    if any(f["severity"] == "BLOCKER" for f in findings):
        verdict = "BLOCKER"
    elif any(f["severity"] == "HIGH" for f in findings):
        verdict = "HIGH"
    elif findings:
        verdict = "MID"
    else:
        verdict = "CLEAN"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (template
            .replace("{{DATE}}", (facts.get("generated_at") or "")[:10])
            .replace("{{REPO_HEAD}}", str(facts.get("repo_head") or "unknown"))
            .replace("{{SKILL_COUNT}}", str(len(facts["skills"])))
            .replace("{{CRITERIA_COUNT}}", "10")
            .replace("{{VERDICT}}", verdict)
            .replace("{{BLOCKER_SECTION}}", blocker_section)
            .replace("{{FINDINGS_TABLE}}", findings_table)
            .replace("{{VERDICT_TABLE}}", verdict_table))


def load_facts(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"❌ 找不到 facts 文件: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ facts 不是合法 JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("❌ facts 顶层必须是对象")
    missing = [k for k in REQUIRED_TOP_KEYS if k not in data]
    if missing:
        raise SystemExit("❌ facts 缺少必需键: " + ", ".join(missing))
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="spec-evolution 判定器（确定性、零 LLM）")
    ap.add_argument("--facts", required=True)
    ap.add_argument("--repo-root", default=None,
                    help="锚点解析根；缺省取 facts.repo_root")
    ap.add_argument("--report", default=None, help="演进报告输出路径")
    ap.add_argument("--json", dest="json_out", default=None, help="finding JSON 输出路径")
    args = ap.parse_args(argv)

    facts = load_facts(Path(args.facts))
    findings = build_findings(facts)

    repo_root = Path(args.repo_root or facts["repo_root"])
    headings = facts["root_prompt"].get("headings") or []
    problems = []
    for f in findings:
        for key in ("anchor", "rule"):
            anchor = f.get(key)
            if anchor is None:
                continue
            reason = validate_anchor(anchor, repo_root, headings)
            if reason:
                problems.append(f"{f['id']} {f['criterion']} {key}: {reason}")
    if problems:
        sys.stderr.write("❌ 锚点存在性校验失败（GI-3），拒绝写出任何产物：\n")
        for p in problems:
            sys.stderr.write(f"  - {p}\n")
        return 2

    if args.report:
        path = Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_report(facts, findings), encoding="utf-8")
        print(f"✅ 演进报告已写出: {path}")
    if args.json_out:
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"✅ finding JSON 已写出: {path}")

    blocking = [f for f in findings if f["severity"] in ("BLOCKER", "HIGH")]
    print(f"📊 findings={len(findings)} blocker/high={len(blocking)}")
    for f in blocking:
        print(f"  ⛔ {f['id']} {f['severity']} {f['criterion']} {f['skill']} {f['anchor']}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
```

> **注意**：C-04 / C-05 互斥（`elif`），同一技能不会同时产出两条 description 判据。

- [ ] **Step 2: 写入 `skills/spec-evolution/templates/evolution-report.md`**

````markdown
# spec-evolution 演进报告 · {{DATE}}

- 仓库基线: `{{REPO_HEAD}}`
- 扫描技能数: {{SKILL_COUNT}} | 判据数: {{CRITERIA_COUNT}}
- 判定结论: **{{VERDICT}}**

{{BLOCKER_SECTION}}

## 判据发现 (Findings)

{{FINDINGS_TABLE}}

## 人类裁决 (Human Verdict)

> 本节由人类填写。判定器在此标题处停止写入；任何由模型生成、或预先勾选的裁决内容均视为门禁违规（RFC-0004 §3.7 / GI-4）。

{{VERDICT_TABLE}}
````

- [ ] **Step 3: 向 `skills/spec-evolution/tests/conftest.py` 追加 `base_facts()`**

在文件末尾追加（不改动既有函数签名）：

```python
def base_facts(root: Path) -> dict:
    """在合成仓库上跑一次 `--no-gates` 采集，返回可被测试点状修改的 facts 字典。"""
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))
```

- [ ] **Step 4: 写入 `skills/spec-evolution/tests/test_judge_contract.py`（第一部分：十条判据）**

```python
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
    facts["skills"][0]["missing_surfaces"] = ["templates"]
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
    facts = _facts(root)
    facts["gates"] = {"pytest": {"cmd": "c", "exit_code": 1, "summary": "s"}}
    facts["skills"][0]["paths"]["has_tests"] = False
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    proc, data = _run(root, facts, tmp_path)
    assert [(f["severity"], f["criterion"]) for f in data] == [
        ("BLOCKER", "C-09"), ("HIGH", "C-01"), ("MID", "C-03")]
```

- [ ] **Step 5: 追加 `test_judge_contract.py` 第二部分（锚点硬门禁与退出码 2）**

```python
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
```

- [ ] **Step 6: 追加 `test_judge_contract.py` 第三部分（报告不变式）**

```python
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
    # facts 由 --no-gates 采集 → gates 为 null，报告必须如实说「未采集」，
    # 不得对既有门禁状态作肯定陈述（RFC-0004 交付审查 R1-3）。
    assert "未采集门禁事实" in text
    assert "无既有门禁失败" not in text


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
```

> **注意**：`test_report_and_json_written_to_requested_paths` 中 `_run` 总是传 `--json`，因此该断言检查的是**未被请求的路径**（`out/report.md`）不存在，而不是 `--json` 被禁用。

- [ ] **Step 7: 跑判定契约测试**

```bash
python3 -m pytest skills/spec-evolution/tests/test_judge_contract.py -q
```

期望：全绿。若 `test_c04` 的期望字符数不符，用 Step 8 的采集命令核对实际值后修正断言（**禁止弱化断言迎合实现**）。

- [ ] **Step 8: 在真实仓库跑一遍判定器（冒烟）**

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --out /tmp/facts.json
python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json --report /tmp/evolution-report.md --json /tmp/findings.json
echo "exit=$?"
```

期望：`exit=1`（存在 F-1/F-2/F-4/F-8/F-9 等 HIGH）；报告含 `判定结论: **HIGH**`；`/tmp/findings.json` 中 `C-04` 的 `observed` = `738 字符`（dual-round-review）、`C-05` 为空（738 < 1024）、`C-01` 命中 `agy-delegation-workflow`。

- [ ] **Step 9: 提交**

```bash
git add skills/spec-evolution/scripts/judge.py skills/spec-evolution/templates/ skills/spec-evolution/tests/
git commit -m "feat(spec-evolution): 判定器 judge.py、报告模板与判定契约测试

Task 3/7：facts.json → finding 列表 + 演进报告；三锚点存在性硬门禁（GI-3，
锚点不可解析即退出 2 且不写产物）与人类裁决区留白（GI-4）。"
```

**Acceptance（Task 3）**：⑪ `python3 -m pytest skills/spec-evolution/tests/test_judge_contract.py -q` 全绿；⑫ `python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts.json --json /tmp/findings.json; echo $?` 输出 `1`；⑬ 真实仓库 findings 中 `dual-round-review` 的 C-04 `observed` 为 `738 字符`。

---

