"""test_clarification_protocol_contract.py — clarification-protocol 交付面与硬约束的静态契约回归测试。

契约要点：
1. frontmatter：name 与目录同名、license 为 MIT、description 非空且 < 1024（规范硬限，超限技能会被静默丢弃）；
2. §1–§6 六节齐备，且硬约束句在位：重复提问即违规 / 不以穷尽问题为出口 / 三项皆否定…即收敛 / 不得用「没问题了」自证收敛；
3. SKILL.md 与技能内文档的相对链接全部可达，且不得出现跨技能相对链接（单技能安装会断链）；
4. 交付面齐备且非空：references / templates / scripts / tests（tests 下必须有 test_*.py）；
5. 台账校验脚本的退出码契约：0 合规 / 1 不合规（❌ 指明缺什么）/ 2 用法错误（缺参数或文件不存在）。

本文件只做静态与行为契约，不评价规程内容的质量。
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
DECISION_LEDGER = SKILL_DIR / "references" / "decision-ledger.md"
CONVERGENCE = SKILL_DIR / "references" / "convergence-checklist.md"
LEDGER_TEMPLATE = SKILL_DIR / "templates" / "decision-ledger-template.md"
RFC_TEMPLATE = SKILL_DIR / "templates" / "requirement-confirmation-template.md"
CHECKER = SKILL_DIR / "scripts" / "check-decision-ledger.py"
CHECKER_SH = SKILL_DIR / "scripts" / "check-decision-ledger.sh"

# 兼容壳（旧 .sh 调用面）转发测试仅在 POSIX + bash 环境执行；Windows 保留 .py 调用面。
BASH_AVAILABLE = sys.platform != "win32" and shutil.which("bash") is not None

DELIVERABLES = [DECISION_LEDGER, CONVERGENCE, LEDGER_TEMPLATE, RFC_TEMPLATE, CHECKER]

REQUIRED_SECTIONS = [
    "## 1. 术语先行",
    "## 2. 提问排序",
    "## 3. 决策台账",
    "## 4. 提问收敛律与三项收敛自检",
    "## 5. 熔断预算与升级",
    "## 6. 显式化思考",
]

HARD_SENTENCES = [
    ("去重纪律", re.compile(r"重复提问即违规")),
    ("收敛出口", re.compile(r"不以穷尽问题为出口")),
    ("三项收敛判据", re.compile(r"三项皆否定[^。\n]*即收敛")),
    ("禁止自证收敛", re.compile(r"不得用「没问题了」自证收敛")),
]

SKILL_NAMES = [
    "taste-driven-designer",
    "dual-round-review",
    "goal-loop",
    "frontend-qa-gate",
    "doc-governance",
    "agy-delegation-workflow",
    "clarification-protocol",
    "spec-evolution",
]
CROSS_SKILL_LINK = re.compile(
    r"(?:^|[\s(=/\"\'>、，（])(?:[^)\s\"\'<>]*?[\\/])*(?<![.])(?:"
    + "|".join(SKILL_NAMES)
    + r")[\\/]",
    re.IGNORECASE,
)
LINK = re.compile(r"\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"\x60[^\x60]*\x60")
COMMAND_EXAMPLE = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")
FENCE = chr(96) * 3
CQ = chr(96)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_fences(text: str) -> str:
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith(FENCE):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def strip_inline_code(line: str) -> str:
    return INLINE_CODE.sub("", line)


def skill_docs():
    return sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in str(p))


def is_command_example(line: str) -> bool:
    return bool(COMMAND_EXAMPLE.match(line))


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta


def missing_hard_sentences(text: str) -> list:
    return [label for label, rx in HARD_SENTENCES if not rx.search(text)]


# --- 1. frontmatter -----------------------------------------------------------

def test_frontmatter_name_matches_directory_and_license():
    meta = parse_frontmatter(read(SKILL_MD))
    assert meta, "SKILL.md 必须含 YAML frontmatter"
    assert meta.get("name") == SKILL_DIR.name == "clarification-protocol"
    assert meta.get("license", "").strip().upper() == "MIT"


def test_description_present_and_under_hard_limit():
    desc = parse_frontmatter(read(SKILL_MD)).get("description", "")
    assert len(desc) > 100, f"description 解析结果可疑（{len(desc)} 字符）: {desc[:80]}"
    assert len(desc) < 1024, f"description {len(desc)} 字符，达到/超过规范硬限 1024（技能会被静默丢弃）"


def test_frontmatter_parser_self_check():
    # 防恒真空断言：解析器必须能处理值内含冒号的行，且无 frontmatter 时返回空
    sample = "---\nname: demo\nlicense: MIT\ndescription: Use when a:b matters\n---\n\n# demo\n"
    meta = parse_frontmatter(sample)
    assert meta == {"name": "demo", "license": "MIT", "description": "Use when a:b matters"}
    assert parse_frontmatter("没有 frontmatter") == {}


# --- 2. 六节与硬句 -------------------------------------------------------------

def test_six_protocol_sections_present():
    text = read(SKILL_MD)
    for section in REQUIRED_SECTIONS:
        assert text.count(section) == 1, f"SKILL.md 缺少或重复章节: {section}"
    assert text.index("## 6.") > text.index("## 1."), "章节顺序必须为 §1..§6"


def test_hard_constraints_present():
    missing = missing_hard_sentences(read(SKILL_MD))
    assert not missing, f"SKILL.md 缺少硬约束句: {missing}"


def test_hard_sentence_scanner_self_check():
    text = read(SKILL_MD)
    assert missing_hard_sentences(text) == []
    for label, rx in HARD_SENTENCES:
        stripped = rx.sub("", text)
        assert label in missing_hard_sentences(stripped), f"扫描器漏检被移除的硬句: {label}"


# --- 3. 链接纪律 ---------------------------------------------------------------

def test_no_cross_skill_relative_links():
    offenders = []
    for path in skill_docs():
        body = strip_fences(read(path))
        for i, line in enumerate(body.splitlines(), 1):
            if is_command_example(line) and "](" not in line:
                continue
            if CROSS_SKILL_LINK.search(strip_inline_code(line)):
                offenders.append(f"{path.relative_to(SKILL_DIR)}:{i}")
    assert not offenders, "禁止跨技能相对链接（独立分发会断链）: " + "; ".join(offenders)


def test_cross_skill_link_scanner_self_check():
    illegal = [
        "(../goal-loop/SKILL.md)",
        "(./dual-round-review/SKILL.md)",
        "(spec-evolution/SKILL.md)",
        "(../../skills/doc-governance/SKILL.md)",
        "(/abs/skills/clarification-protocol/SKILL.md)",
        "../Goal-Loop/SKILL.md",
    ]
    for sample in illegal:
        assert CROSS_SKILL_LINK.search(sample), f"跨技能链接正则漏检: {sample}"
    legal = [
        "(references/decision-ledger.md)",
        "(../templates/requirement-confirmation-template.md)",
        "(../SKILL.md)",
        "goal-loop 技能（命名引用，不带路径）",
    ]
    for sample in legal:
        assert not CROSS_SKILL_LINK.search(strip_inline_code(sample)), f"正则误伤技能内路径: {sample}"


def link_defects(root: Path = SKILL_DIR, docs=None):
    """返回 (断链, 越界链接)：断链指目标不存在；越界指目标存在但落在技能目录之外。"""
    skill_root = root.resolve()
    paths = skill_docs() if docs is None else docs
    broken, escaped = [], []
    for path in paths:
        body = strip_fences(read(path))
        for i, line in enumerate(body.splitlines(), 1):
            for target in LINK.findall(strip_inline_code(line)):
                t = target.strip()
                if t.startswith(("http", "#", "mailto:")):
                    continue
                resolved = (path.parent / t.split("#")[0]).resolve()
                where = f"{path.relative_to(root)}:{i} -> {t}"
                if not resolved.exists():
                    broken.append(where)
                elif resolved != skill_root and skill_root not in resolved.parents:
                    escaped.append(where)
    return broken, escaped


def test_relative_links_resolve_within_skill():
    broken, escaped = link_defects()
    assert not broken, "技能文档断链: " + "; ".join(broken)
    assert not escaped, "相对链接不得越出技能目录（单技能安装会断链）: " + "; ".join(escaped)


def test_link_containment_scanner_self_check(tmp_path):
    skill_root = tmp_path / "skills" / "demo"
    (skill_root / "references").mkdir(parents=True)
    (skill_root / "references" / "inside.md").write_text("y", encoding="utf-8")
    outside = tmp_path / "docs" / "index.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("z", encoding="utf-8")
    doc = skill_root / "SKILL.md"
    doc.write_text(
        "见 [技能内](references/inside.md)、[越界](../../docs/index.md)、[幽灵](references/ghost.md)\n",
        encoding="utf-8",
    )
    broken, escaped = link_defects(root=skill_root, docs=[doc])
    assert any("ghost.md" in b for b in broken), broken
    assert any("index.md" in e for e in escaped), escaped
    assert not any("inside.md" in x for x in broken + escaped), (broken, escaped)


def test_link_scanner_self_check():
    doc = (
        "见 [真链接](references/decision-ledger.md)\n\n"
        + FENCE + "\n[围栏内示例](ghost.md)\n" + FENCE + "\n\n"
        + "行内示例 " + CQ + "[行内](ghost2.md)" + CQ + "\n"
    )
    body = strip_fences(doc)
    collected = []
    for line in body.splitlines():
        collected += LINK.findall(strip_inline_code(line))
    assert collected == ["references/decision-ledger.md"], collected


# --- 4. 交付面 -----------------------------------------------------------------

def test_delivery_surface_is_complete_and_nonempty():
    for path in DELIVERABLES:
        assert path.is_file(), f"交付面缺失: {path.relative_to(SKILL_DIR)}"
        assert path.stat().st_size > 0, f"交付面文件为空: {path.relative_to(SKILL_DIR)}"
    test_files = sorted((SKILL_DIR / "tests").glob("test_*.py"))
    assert test_files, "tests/ 下必须存在 test_*.py（C-01）"
    assert any(p.name == Path(__file__).name for p in test_files)


def test_skill_md_appended_section_links_deliverables():
    text = read(SKILL_MD)
    marker = "## 何时使用 / 何时不用"
    assert marker in text, "SKILL.md 必须保留「何时使用 / 何时不用」节"
    tail = text[text.index(marker):]
    for path in DELIVERABLES:
        rel = path.relative_to(SKILL_DIR).as_posix()
        assert f"]({rel})" in tail, f"SKILL.md 文末追加节缺少指向 {rel} 的相对链接"


# --- 5. 台账校验脚本的行为契约 ---------------------------------------------------

GOOD_LEDGER = """# 决策台账 · 示例项目

## 决策台账

### 已决项

| 编号 | 结论（一句话可执行） | 出处 | 影响面 |
| :--- | :--- | :--- | :--- |
| D-01 | 首个交付形态为 Web 单页应用 | 出处: 用户裁决（第 1 轮） | 前端路由与构建目标 |
| D-02 | 持久化统一走服务端 API | 出处: 证据（2026-10-13 架构评审纪要 §2） | 前端数据层 |

### 已排除边界

| 编号 | 被排除的方案或范围 | 排除依据 | 复开条件 |
| :--- | :--- | :--- | :--- |
| E-01 | 本期不做移动端原生客户端 | 排除依据: 用户裁决（第 1 轮）——预算仅覆盖 Web | 无——除新证据外不得重开 |

### 默认假设

| 编号 | 取值 | 影响级别 | 可否决性 | 反转成本 |
| :--- | :--- | :--- | :--- | :--- |
| A-01 | 会话空闲过期取 30 分钟 | 影响级别: 低 | 可否决 | 改一个后端配置常量 |
"""


def run_checker(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def write_ledger(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "decision-ledger.md"
    # newline="\n" 固化台账行尾：Windows 下 write_text 默认把 \n 翻成 \r\n，
    # 而台账校验（与原 Bash/awk 行为一致）不把行尾 \r 视作空白，会产生平台相关假失败。
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_checker_script_declares_python_entrypoint():
    """契约迁移：原断言 .sh 的 `#!/usr/bin/env bash` + `set -euo pipefail`。

    实现迁移为 check-decision-ledger.py 后改为断言 .py 的入口契约；旧 .sh 调用面
    由下方兼容壳契约用例覆盖（壳仍保留 shebang 与 set -euo pipefail 并转发到 .py）。
    """
    text = read(CHECKER)
    assert text.startswith("#!/usr/bin/env python3"), "校验脚本必须声明 Python 3 shebang"
    assert 'if __name__ == "__main__":' in text, "校验脚本必须提供 __main__ 入口"


def test_checker_passes_on_compliant_ledger(tmp_path):
    r = run_checker(str(write_ledger(tmp_path, GOOD_LEDGER)))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "合规" in r.stdout


def test_checker_fails_when_exclusion_basis_missing(tmp_path):
    text = GOOD_LEDGER.replace("排除依据: 用户裁决（第 1 轮）——预算仅覆盖 Web", "（依据字段被漏写）")
    r = run_checker(str(write_ledger(tmp_path, text)))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "排除依据" in r.stdout + r.stderr, r.stdout + r.stderr
    assert "❌" in r.stdout + r.stderr


def test_checker_fails_when_impact_level_missing(tmp_path):
    text = GOOD_LEDGER.replace("影响级别: 低", "级别: 低")
    r = run_checker(str(write_ledger(tmp_path, text)))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "影响级别" in r.stdout + r.stderr, r.stdout + r.stderr


def test_checker_fails_when_decided_source_missing(tmp_path):
    text = GOOD_LEDGER.replace("出处: 用户裁决（第 1 轮）", "（来源未登记）")
    r = run_checker(str(write_ledger(tmp_path, text)))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "出处" in r.stdout + r.stderr, r.stdout + r.stderr


def test_checker_fails_when_category_section_missing(tmp_path):
    text = GOOD_LEDGER.split("### 默认假设")[0]
    r = run_checker(str(write_ledger(tmp_path, text)))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "默认假设" in r.stdout + r.stderr


def test_checker_fails_when_category_has_no_data_rows(tmp_path):
    text = GOOD_LEDGER.replace(
        "| A-01 | 会话空闲过期取 30 分钟 | 影响级别: 低 | 可否决 | 改一个后端配置常量 |\n", ""
    )
    r = run_checker(str(write_ledger(tmp_path, text)))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "数据行" in r.stdout + r.stderr


def test_checker_ignores_ledger_inside_code_fence(tmp_path):
    text = FENCE + "\n" + GOOD_LEDGER + FENCE + "\n"
    r = run_checker(str(write_ledger(tmp_path, text)))
    assert r.returncode == 1, "围栏内的模板示例不得充当真实登记"
    assert "已决项" in r.stdout + r.stderr


def test_checker_missing_file_is_usage_error():
    r = run_checker("/nonexistent/decision-ledger.md")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "不存在" in r.stdout + r.stderr


def test_checker_no_args_is_usage_error():
    r = run_checker()
    assert r.returncode == 2, r.stdout + r.stderr
    assert "usage" in (r.stdout + r.stderr).lower()


def test_checker_extra_args_is_usage_error(tmp_path):
    r = run_checker(str(write_ledger(tmp_path, GOOD_LEDGER)), "extra")
    assert r.returncode == 2, r.stdout + r.stderr


def test_checker_is_read_only(tmp_path):
    path = write_ledger(tmp_path, GOOD_LEDGER)
    before = {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}
    run_checker(str(path))
    after = {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}
    assert before == after, "校验脚本不得写入或触碰文件"


# --- 兼容壳（旧 .sh 调用面）----------------------------------------------------

@pytest.mark.skipif(not BASH_AVAILABLE, reason="兼容壳契约仅在 POSIX + bash 环境验证")
def test_compat_shell_declares_forward_contract():
    """旧 .sh 退役为兼容壳：保留 shebang/set -euo pipefail，并 exec 转发到同目录 .py。"""
    text = read(CHECKER_SH)
    assert text.startswith("#!/usr/bin/env bash"), "兼容壳必须是 bash 脚本"
    assert "set -euo pipefail" in text, "兼容壳必须 set -euo pipefail"
    assert "exec python3" in text, "兼容壳必须以 exec python3 转发（保留退出码）"
    assert "check-decision-ledger.py" in text, "兼容壳必须转发到同目录 Python 实现"


@pytest.mark.skipif(not BASH_AVAILABLE, reason="兼容壳转发仅在 POSIX + bash 环境验证")
def test_compat_shell_forwards_to_python_implementation(tmp_path):
    """旧 .sh 调用仍可用：stdout/退出码与 .py 完全一致（Windows 无 bash，由 .py 主路径覆盖）。"""
    ledger = write_ledger(tmp_path, GOOD_LEDGER)
    shell_run = subprocess.run(
        ["bash", str(CHECKER_SH), str(ledger)], capture_output=True, text=True, encoding="utf-8"
    )
    py_run = run_checker(str(ledger))
    assert shell_run.returncode == py_run.returncode == 0, shell_run.stdout + shell_run.stderr
    assert shell_run.stdout == py_run.stdout
    assert shell_run.stderr == py_run.stderr
