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

SURFACE_DIRS = ("references", "scripts", "templates")

GATE_ANCHORS = {
    "pytest": "skills/",
    "check_doc_links": "skills/doc-governance/scripts/check-doc-links.py",
    "audit_doc_health": "skills/doc-governance/scripts/audit-doc-health.py",
    "cross_skill_links": "skills/_shared/tests/test_cross_skill_links.py",
}

# 注册面 → (仓库相对路径, 缺登记时的实测描述)。
# 键名与 collect-facts.py 产出的 `skills[].registrations` 严格同源。
REGISTRATION_SURFACES = {
    "collection": ("tools/skills-manager/collections/cr-agent-arsenal.json", "names 数组未收录"),
    "cross_skill_names": ("skills/_shared/tests/test_cross_skill_links.py", "SKILL_NAMES 未收录"),
    "docs_index": ("docs/index.md", "未登记技能行"),
    "readme": ("README.md", "技能表未收录"),
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


def _resolve_within(target: Path, repo_root: Path) -> Path | None:
    """把锚点目标解析到仓库内的**既有路径**；越界（含绝对路径逃逸）返回 None。

    绝对路径会让 `repo_root / rel` 直接丢弃 `repo_root`（`Path.__truediv__` 语义），
    故必须显式做 containment 校验。目录是合法的锚点目标（如 `[REPO:skills/]`
    指向测试套件根），但**不得带行号**——行号只对文件有意义。
    """
    try:
        resolved = target.resolve()
        resolved.relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.exists() else None


def _check_line(line: str | None, target: Path, label: str) -> str | None:
    if line is None:
        return None
    if not target.is_file():
        return f"锚点行号只能指向文件，但目标是目录: {label}:{line}"
    n = int(line)
    total = _count_lines(target)
    if n < 1 or n > total:
        return f"锚点行号越界: {label}:{line}（共 {total} 行，行号从 1 起）"
    return None


def validate_anchor(anchor: str, repo_root: Path, headings: list) -> str | None:
    """锚点可解析返回 None，否则返回人可读的失败原因。"""
    m = SKILL_ANCHOR_RX.match(anchor)
    if m:
        name, rel, line = m.group(1), m.group(2), m.group(3)
        label = f"skills/{name}/{rel}"
        target = _resolve_within(repo_root / "skills" / name / rel, repo_root)
        if target is None:
            return f"技能锚点不存在或越出仓库: {label}"
        return _check_line(line, target, label)
    m = REPO_ANCHOR_RX.match(anchor)
    if m:
        rel, line = m.group(1), m.group(2)
        target = _resolve_within(repo_root / rel, repo_root)
        if target is None:
            return f"仓库锚点路径不存在或越出仓库: {rel}"
        return _check_line(line, target, rel)
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


def missing_surfaces(skill: dict) -> list:
    """由扁平 `has_<dir>` 布尔推导缺失的交付面目录（与 collect-facts.py 契约同源）。"""
    return [d for d in SURFACE_DIRS if not skill.get(f"has_{d}")]


def build_findings(facts: dict) -> list:
    out: list = []

    for key, info in sorted((facts.get("gates") or {}).items()):
        if info.get("exit_code") != 0:
            out.append(_mk(
                "C-09", "BLOCKER", "<repo>",
                f"[REPO:{GATE_ANCHORS.get(key, 'skills/')}]", None, info.get("cmd", ""),
                f"exit_code={info.get('exit_code')}", "exit_code == 0",
                "既有门禁非零退出，交付基线不成立。"))

    for sk in facts["skills"]:
        name = sk["name"]
        skill_anchor = f"[SKILL:{name}/SKILL.md]"

        if not sk["has_tests"]:
            out.append(_mk(
                "C-01", "HIGH", name, skill_anchor, RULE_DOD,
                f"ls skills/{name}/tests", "目录不存在", "存在 tests/ 且至少 1 个 test_*.py",
                "技能缺少契约测试，其判据不可机械回归。"))

        if not sk["design_doc"]:
            out.append(_mk(
                "C-02", "MID", name, skill_anchor, RULE_DOD,
                f"test -f docs/explanation/architecture/{name}-design.md", "文件不存在",
                "存在架构设计书", "技能无架构设计书，架构决策不可追溯。"))

        absent = missing_surfaces(sk)
        if absent or sk["empty_surface_dirs"]:
            parts = []
            if absent:
                parts.append("缺失: " + ", ".join(absent))
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

        for surface, registered in sorted(sk["registrations"].items()):
            if registered:
                continue
            path, detail = REGISTRATION_SURFACES[surface]
            out.append(_mk(
                "C-07", "HIGH", name, f"[REPO:{path}]", None,
                f"grep -nF '{name}' {path}", detail,
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


class FactsError(Exception):
    """facts 输入无效。`main()` 捕获后统一以退出码 2 收口。"""


def load_facts(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FactsError(f"❌ 找不到 facts 文件: {path}")
    except json.JSONDecodeError as exc:
        raise FactsError(f"❌ facts 不是合法 JSON: {exc}")
    if not isinstance(data, dict):
        raise FactsError("❌ facts 顶层必须是对象")
    missing = [k for k in REQUIRED_TOP_KEYS if k not in data]
    if missing:
        raise FactsError("❌ facts 缺少必需键: " + ", ".join(missing))
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="spec-evolution 判定器（确定性、零 LLM）")
    ap.add_argument("--facts", required=True)
    ap.add_argument("--repo-root", default=None,
                    help="锚点解析根；缺省取 facts.repo_root")
    ap.add_argument("--report", default=None, help="演进报告输出路径")
    ap.add_argument("--json", dest="json_out", default=None, help="finding JSON 输出路径")
    args = ap.parse_args(argv)

    try:
        facts = load_facts(Path(args.facts))
    except FactsError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
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
