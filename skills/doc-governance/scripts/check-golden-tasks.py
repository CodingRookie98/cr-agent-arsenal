#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-golden-tasks.py - 知识库可回答性评测（BK-0049）

把「agent 能否从知识库答出某类问题」转成 20 条**机械可判**的断言：
每条 = 一个真实问题 + 一个检索式判据。三态输出：

  PASS  断言成立（知识存在且可定位）
  GAP   知识库确实缺这块内容（真实缺口，只报告）
  FAIL  元数据/链接结构性缺失（阻断，说明知识库自身坏了）

边界（诚实声明）：本脚本测的是**知识可检索性**，不是 agent 答题成功率。
后者需要宿主配合采集步数与 token，属后续工作。

退出码: 0 = 无 FAIL；1 = 存在 FAIL；2 = 环境错误。
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[2]

Status = str  # "pass" | "gap" | "fail"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _md_files(root: Path, sub: str = "") -> List[Path]:
    base = root / sub if sub else root
    if not base.is_dir():
        return []
    return sorted(
        f for f in base.rglob("*.md")
        if not any(p in f.parts for p in ("node_modules", ".git", "dist", "build"))
        and "reviews" not in f.parts
        and "_llms" not in f.parts
    )


# ---------------------------------------------------------------- 断言实现

def g01_rfc_status(root: Path) -> Tuple[Status, str]:
    rfcs = _md_files(root, "proposals")
    if not rfcs:
        return "gap", "proposals 象限为空"
    bad = []
    for f in rfcs:
        text = _read(f)
        # 状态值可能含空格（如 "In Review"），按行取值而非 \S+
        m = re.search(r"\*\*当前状态\*\*:\s*([^|\n]+?)\s*$", text, re.M)
        if not m or m.group(1) not in ("In Review", "Accepted", "Implemented", "Superseded", "Draft"):
            bad.append(f.name)
    return ("fail", f"状态字段缺失或非法: {', '.join(bad[:3])}") if bad else ("pass", f"{len(rfcs)} 篇 RFC 状态合法")


def g02_rfc_has_plan(root: Path) -> Tuple[Status, str]:
    missing = []
    for f in _md_files(root, "proposals"):
        if "落地计划" not in _read(f):
            missing.append(f.name)
    return ("gap", f"{len(missing)} 篇 RFC 缺落地计划链接") if missing else ("pass", "全部 RFC 有落地计划")


def g03_rfc_criteria_ids(root: Path) -> Tuple[Status, str]:
    with_ids = [f for f in _md_files(root, "proposals") if re.search(r"\bC-\d+\b|AC-\d+\b", _read(f))]
    return ("pass", f"{len(with_ids)} 篇 RFC 含可引用的判据编号") if with_ids else ("gap", "无 RFC 使用 C-n/AC-n 判据编号")


def g04_rules_indexed(root: Path) -> Tuple[Status, str]:
    idx = root / "reference" / "rules" / "index.md"
    if not idx.is_file():
        return "fail", "reference/rules/index.md 缺失"
    text = _read(idx)
    missing = [f.name for f in _md_files(root, "reference/rules")
               if f.name != "index.md" and f.stem not in text]
    return ("fail", f"未登记: {', '.join(missing[:3])}") if missing else ("pass", "规则文档全部登记于象限索引")


def g05_rules_have_header(root: Path) -> Tuple[Status, str]:
    bad = [f.name for f in _md_files(root, "reference/rules")
           if f.name != "index.md" and "文档控制信息" not in _read(f)]
    return ("fail", f"缺控制头: {', '.join(bad[:3])}") if bad else ("pass", "规则文档控制头齐全")


def g06_rules_have_criteria(root: Path) -> Tuple[Status, str]:
    with_criteria = [f for f in _md_files(root, "reference/rules")
                     if f.name != "index.md" and re.search(r"判据|约束|红线|必须|禁止", _read(f))]
    total = len([f for f in _md_files(root, "reference/rules") if f.name != "index.md"])
    return ("pass", f"{len(with_criteria)}/{total} 规则文档含可判定表述") if total and len(with_criteria) == total \
        else ("gap", f"仅 {len(with_criteria)}/{total} 含可判定表述")


def g07_commit_evidence(root: Path) -> Tuple[Status, str]:
    f = root / "reference" / "rules" / "commit-evidence.md"
    return ("pass", "提交信息取证口径存在") if f.is_file() else ("fail", "commit-evidence.md 缺失")


def g08_skill_design_docs(root: Path) -> Tuple[Status, str]:
    skills_dir = REPO_ROOT / "skills"
    skills = [d.name for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()] if skills_dir.is_dir() else []
    designs = {f.stem.replace("-design", "") for f in _md_files(root, "explanation/architecture")}
    missing = [s for s in skills if s not in designs]
    return ("gap", f"缺设计书: {', '.join(missing[:4])}") if missing else ("pass", f"{len(skills)} 个技能均有设计书")


def g09_adr_sequence(root: Path) -> Tuple[Status, str]:
    adrs = sorted((root / "explanation" / "decisions").glob("[0-9][0-9][0-9][0-9]-*.md")) \
        if (root / "explanation" / "decisions").is_dir() else []
    if not adrs:
        return "gap", "decisions 象限为空"
    nums = [int(f.name[:4]) for f in adrs]
    ok = nums == list(range(1, len(nums) + 1))
    return ("pass", f"{len(adrs)} 篇 ADR，编号连续") if ok else ("fail", f"ADR 编号不连续: {nums}")


def g10_research_evidence_grading(root: Path) -> Tuple[Status, str]:
    analysis = _md_files(root, "explanation/analysis")
    graded = [f for f in analysis if "证据" in _read(f) and ("【A】" in _read(f) or "一手" in _read(f))]
    return ("pass", f"{len(graded)}/{len(analysis)} 篇调研含证据分级") if graded \
        else ("gap", "调研文档未标注证据等级")


def g11_design_cites_skill(root: Path) -> Tuple[Status, str]:
    designs = _md_files(root, "explanation/architecture")
    citing = [f for f in designs if "SKILL.md" in _read(f)]
    return ("pass", f"{len(citing)}/{len(designs)} 篇设计书引用 SKILL.md") if citing \
        else ("gap", "设计书未回链 SKILL.md")


def g12_howto_quadrant(root: Path) -> Tuple[Status, str]:
    files = _md_files(root, "how-to")
    return ("pass", f"how-to 象限 {len(files)} 篇") if files else ("gap", "how-to 象限为空（操作类知识缺位）")


def g13_tutorial_quadrant(root: Path) -> Tuple[Status, str]:
    files = _md_files(root, "tutorials")
    return ("pass", f"tutorials 象限 {len(files)} 篇") if files else ("gap", "tutorials 象限为空（上手路径缺位）")


def g14_backlog_acceptance(root: Path) -> Tuple[Status, str]:
    active = root / "project" / "backlog" / "active"
    if not active.is_dir():
        return "pass", "无活跃待办"
    cards = sorted(active.glob("*.md"))
    bad = [f.name for f in cards if "验收" not in _read(f)]
    return ("fail", f"缺验收准则: {', '.join(bad[:3])}") if bad else ("pass", f"{len(cards)} 张活跃卡片均有验收准则")


def g15_plans_have_status(root: Path) -> Tuple[Status, str]:
    plans = _md_files(root, "project/plans")
    with_status = [f for f in plans if re.search(r"\*\*状态\*\*|状态:", _read(f))]
    return ("pass", f"{len(with_status)}/{len(plans)} 篇计划含状态字段") if plans and len(with_status) == len(plans) \
        else ("gap", f"仅 {len(with_status)}/{len(plans)} 篇计划含状态字段")


def g16_changelog(root: Path) -> Tuple[Status, str]:
    f = root / "project" / "changelog.md"
    return ("pass", "changelog 存在") if f.is_file() else ("gap", "project/changelog.md 缺失（交付叙事无归档）")


def g17_reviews_indexed(root: Path) -> Tuple[Status, str]:
    reviews = root / "project" / "reviews"
    if not reviews.is_dir():
        return "pass", "无审查归档"
    dirs = [d for d in reviews.iterdir() if d.is_dir()]
    missing = [d.name for d in dirs if not (d / "README.md").is_file()]
    return ("fail", f"缺索引: {', '.join(missing[:3])}") if missing else ("pass", f"{len(dirs)} 个归档均有 README")


def g18_llms_root_budget(root: Path) -> Tuple[Status, str]:
    f = root / "llms.txt"
    if not f.is_file():
        return "fail", "llms.txt 缺失"
    size = len(f.read_bytes())
    sections = len(re.findall(r"^## ", _read(f), re.M))
    if size > 8192:
        return "fail", f"根机器地图 {size} 字节 > 8192"
    return ("pass", f"{size} 字节 / {sections} 个象限节") if sections >= 4 \
        else ("fail", f"仅 {sections} 个象限节")


def g19_agents_router(root: Path) -> Tuple[Status, str]:
    f = root / "AGENTS.md"
    if not f.is_file():
        return "fail", "docs/AGENTS.md 缺失"
    text = _read(f)
    lines = len(text.splitlines())
    if lines > 30:
        return "fail", f"路由文件 {lines} 行 > 30"
    missing = [s for s in ("读取顺序", "硬约束") if s not in text]
    return ("fail", f"缺小节: {missing}") if missing else ("pass", f"{lines} 行，小节齐全")


def g20_all_have_header(root: Path) -> Tuple[Status, str]:
    # ADR 用「ADR 控制元数据」+ MADR 格式；backlog 卡片用 YAML frontmatter——两者各有契约，
    # 不套用标准控制头（GOVERNANCE §4.1 已登记）。
    files = [
        f for f in _md_files(root)
        if f.parent != root
        and "decisions" not in f.parts
        and "backlog" not in f.parts
        and not (len(f.relative_to(root).parts) >= 2 and f.relative_to(root).parts[:2] == ("reference", "articles"))
    ]
    # RFC 用「提案元数据」、其余用「文档控制信息」——两者都是有效控制头
    bad = [
        f.name for f in files
        if "文档控制信息" not in _read(f) and "提案元数据" not in _read(f)
    ]
    return ("fail", f"{len(bad)} 篇缺控制头: {', '.join(bad[:3])}") if bad else ("pass", f"{len(files)} 篇均有控制头")


TASKS: List[Dict] = [
    {"id": "G-01", "q": "任一 RFC 的当前状态是什么？", "fn": g01_rfc_status},
    {"id": "G-02", "q": "某 RFC 落地到哪个计划？", "fn": g02_rfc_has_plan},
    {"id": "G-03", "q": "某条契约的判据编号是什么？", "fn": g03_rfc_criteria_ids},
    {"id": "G-04", "q": "某条规则文档在哪登记？", "fn": g04_rules_indexed},
    {"id": "G-05", "q": "这条规则的版本与所有者是谁？", "fn": g05_rules_have_header},
    {"id": "G-06", "q": "这条规则允许/禁止什么？", "fn": g06_rules_have_criteria},
    {"id": "G-07", "q": "提交信息该怎么写才合规？", "fn": g07_commit_evidence},
    {"id": "G-08", "q": "某技能为什么这样设计？", "fn": g08_skill_design_docs},
    {"id": "G-09", "q": "历史上做过哪些架构决策？", "fn": g09_adr_sequence},
    {"id": "G-10", "q": "这个结论有几手证据支撑？", "fn": g10_research_evidence_grading},
    {"id": "G-11", "q": "设计书对应的技能规程在哪？", "fn": g11_design_cites_skill},
    {"id": "G-12", "q": "某个操作的具体步骤是什么？", "fn": g12_howto_quadrant},
    {"id": "G-13", "q": "新人怎么快速上手？", "fn": g13_tutorial_quadrant},
    {"id": "G-14", "q": "这张待办完成的判据是什么？", "fn": g14_backlog_acceptance},
    {"id": "G-15", "q": "这个计划执行到哪一步了？", "fn": g15_plans_have_status},
    {"id": "G-16", "q": "上次发布交付了什么？", "fn": g16_changelog},
    {"id": "G-17", "q": "这次交付的审查结论在哪？", "fn": g17_reviews_indexed},
    {"id": "G-18", "q": "知识库有哪些象限？", "fn": g18_llms_root_budget},
    {"id": "G-19", "q": "读文档的顺序是什么？", "fn": g19_agents_router},
    {"id": "G-20", "q": "这篇文档的版本与所有者是谁？", "fn": g20_all_have_header},
]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="知识库可回答性评测（20 条机械断言）")
    parser.add_argument("--root", default="docs", help="文档根目录（默认 docs）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--quiet", action="store_true", help="只输出非 PASS 项")
    args = parser.parse_args()

    root = (REPO_ROOT / args.root).resolve() if not Path(args.root).is_absolute() else Path(args.root)
    if not root.is_dir():
        print(f"❌ 文档根不存在: {root}", file=sys.stderr)
        return 2

    results = []
    for task in TASKS:
        try:
            status, detail = task["fn"](root)
        except Exception as exc:  # noqa: BLE001
            status, detail = "fail", f"断言异常: {exc}"
        results.append({"id": task["id"], "question": task["q"], "status": status, "detail": detail})

    counts = {k: sum(1 for r in results if r["status"] == k) for k in ("pass", "gap", "fail")}
    if args.json:
        import json

        print(json.dumps({"counts": counts, "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"🔎 知识库可回答性评测：{len(results)} 条断言")
        for r in results:
            if args.quiet and r["status"] == "pass":
                continue
            icon = {"pass": "✅", "gap": "🕳️", "fail": "❌"}[r["status"]]
            print(f"   {icon} {r['id']} {r['question']} —— {r['detail']}")
        print(f"\n📊 PASS {counts['pass']}｜GAP {counts['gap']}｜FAIL {counts['fail']}")

    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
