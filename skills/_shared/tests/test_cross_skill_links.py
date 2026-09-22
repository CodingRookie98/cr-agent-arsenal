"""test_cross_skill_links.py — 仓库级技能文档链接纪律自检。

覆盖两条判据：
1. 跨技能相对路径硬链接 = 0（独立分发会断链）；
2. 技能文档内的相对链接目标必须存在（单技能安装后可达）。

扫描纪律（避免把文档示例误判为真实链接）：
- 剥离围栏代码块（含缩进围栏）；
- 剥离行内代码（反引号包裹的示例路径，如 `[规则.md](./rules/rule.md)`）；
- 豁免命令行示例行（bash / python3 / npx ...）。

背景：frontend-qa-gate 交付的 FU-2 待办 —— dual-round-review / goal-loop 存在真实跨技能相对链接。
"""

import re
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = SHARED_DIR.parent
SKILL_NAMES = [
    "taste-driven-designer",
    "dual-round-review",
    "goal-loop",
    "frontend-qa-gate",
    "doc-governance",
    "agy-delegation-workflow",
]
LINK = re.compile(r"\]\(([^)]+)\)")
CROSS = re.compile(
    r"(?:^|[\s(=/\"\'>、，（])(?:[^)\s\"\'<>]*?[\\/])*(?<![.])(?:" + "|".join(SKILL_NAMES) + r")[\\/]",
    re.IGNORECASE,
)
COMMAND_EXAMPLE = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")
INLINE_CODE = re.compile(r"`[^`]*`")


def strip_fences(text):
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def strip_inline_code(line):
    return INLINE_CODE.sub("", line)


def skill_docs():
    for name in SKILL_NAMES:
        root = SKILLS_DIR / name
        if not root.is_dir():
            continue
        for md in sorted(root.rglob("*.md")):
            if "__pycache__" in str(md):
                continue
            yield md


def test_no_cross_skill_relative_links():
    offenders = []
    for md in skill_docs():
        body = strip_fences(md.read_text(encoding="utf-8"))
        for i, line in enumerate(body.splitlines(), 1):
            # 命令行示例豁免收紧：行内若含 markdown 链接语法则不豁免（防借命令示例藏链接）
            if COMMAND_EXAMPLE.match(line) and "](" not in line:
                continue
            if CROSS.search(strip_inline_code(line)):
                offenders.append(f"{md.relative_to(SKILLS_DIR)}:{i}")
    assert not offenders, "跨技能相对路径硬链接（单技能安装会断链）: " + "; ".join(offenders)


def test_relative_links_resolve_within_skill():
    broken = []
    for md in skill_docs():
        body = strip_fences(md.read_text(encoding="utf-8"))
        for i, line in enumerate(body.splitlines(), 1):
            for target in LINK.findall(strip_inline_code(line)):
                t = target.strip()
                if t.startswith(("http", "#", "mailto:")):
                    continue
                if not (md.parent / t.split("#")[0]).resolve().exists():
                    broken.append(f"{md.relative_to(SKILLS_DIR)}:{i} -> {t}")
    assert not broken, "技能文档内断链: " + "; ".join(broken)


def test_scanner_self_check():
    """扫描器自检：行内代码示例与围栏内链接不得被误判；真实链接必须命中。"""
    sample_doc = "（如 `[规则.md](./rules/rule.md)`）\n\n```markdown\n> [api/xxx.md](../reference/api/xxx.md)\n```\n"
    body = strip_fences(sample_doc)
    targets = []
    for line in body.splitlines():
        targets += LINK.findall(strip_inline_code(line))
    assert targets == [], f"示例链接被误判为真实链接: {targets}"
    real = "见 [dual-round-review](../../dual-round-review/SKILL.md) 铁律 1"
    assert CROSS.search(strip_inline_code(real)), "真实跨技能链接未被命中"
    inline = "见 `[x](../goal-loop/SKILL.md)` 示例"
    assert not CROSS.search(strip_inline_code(inline)), "行内代码中的示例被误判为跨技能链接"


def test_fences_balanced():
    """围栏必须成对闭合：未闭合会导致其后内容（含真实链接）被静默跳过。"""
    unbalanced = []
    for md in skill_docs():
        text = md.read_text(encoding="utf-8")
        n = sum(1 for line in text.splitlines() if line.strip().startswith("```"))
        if n % 2 != 0:
            unbalanced.append(f"{md.relative_to(SKILLS_DIR)} ({n})")
    assert not unbalanced, "围栏未闭合: " + "; ".join(unbalanced)
