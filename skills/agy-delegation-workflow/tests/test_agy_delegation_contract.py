"""test_agy_delegation_contract.py — agy-delegation-workflow 硬边界契约的静态回归测试。

背景：本技能的存在价值是把委派约束在明确的前台/后台责任边界内。边界一旦被侵蚀
（宿主原生反触发失效、设计文档或 Git 写操作被下发给 agy、SSOT 细则被复制回全局层、
优先级链顺序漂移、派发脚本悄悄放宽参数或代理清除），委派就会越权或产生双份真相源。

契约要点：
1. frontmatter：name == "agy-delegation-workflow"、license == MIT、description 非空、
   以 "Use when" 开头且 < 1024 字符（Agent Skills 规范硬限）；
2. 反触发四类齐备：宿主原生反触发（invoke_subagent 优先、严禁终端套娃）、架构与设计文档、
   Git 写操作与破坏性操作、安全凭据与交互式决策；
3. SSOT 边界句在位：委派完整规程「以本技能为准」且「不在全局层复制」；
4. 优先级链三级顺序：宿主原生派发 -> 无头命令行执行 -> 兜底前台直接编写；
5. 标准委派 SOP 五个步骤标题齐备且有序；
6. 技能内相对链接目标必须存在且不得逸出技能目录；跨技能链接扫描器自检覆盖 ../ 逃逸形态；
7. scripts/dispatch-agy.py 行为契约：--help / 无参数 / -f 文件缺失 / PATH 无 agy /
   前台派发 argv 与代理清除 / 后台模式 PID + 日志落盘。
   脚本测试全程使用临时 git 仓库与假 agy shim，绝不调用真实 agy、绝不写入本仓库、绝不触网。
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
DISPATCH = SKILL_DIR / "scripts" / "dispatch-agy.py"
COMPAT_SHELL = DISPATCH.with_suffix(".sh")

# 子进程默认使用绝对路径的 bash，避免 PATH 被测试改写后找不到解释器。
BASH = shutil.which("bash") or "/bin/bash"
POSIX_ONLY = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="兼容壳为 POSIX Bash 转发实现，Windows 原生环境不适用",
)

DEFAULT_MODEL = "Gemini 3.8 Flash (High)"
DEFAULT_TIMEOUT = "20m"
PROXY_VARS = ("HTTPS_PROXY", "HTTP_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy")


def read(path):
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# A. frontmatter
# ---------------------------------------------------------------------------

def frontmatter(text):
    assert text.startswith("---\n"), "SKILL.md 必须以 YAML frontmatter 开头"
    end = text.find("\n---", 4)
    assert end != -1, "SKILL.md frontmatter 未闭合"
    return text[4:end]


def fm_field(front, key):
    m = re.search(r"^" + re.escape(key) + r":\s*(.*)$", front, re.MULTILINE)
    assert m, f"frontmatter 缺少字段: {key}"
    return m.group(1).strip()


def test_frontmatter_name_and_license():
    front = frontmatter(read(SKILL_MD))
    assert fm_field(front, "name") == "agy-delegation-workflow"
    assert fm_field(front, "license") == "MIT"


def test_description_obeys_agent_skills_limit():
    description = fm_field(frontmatter(read(SKILL_MD)), "description")
    assert description, "description 不得为空"
    assert description.startswith("Use when"), (
        'description 必须以 "Use when" 开头（触发语义前置）: ' + description[:40]
    )
    assert len(description) < 1024, (
        f"description 长度 {len(description)} 字符，超出 Agent Skills 规范硬限 (< 1024)"
    )


# ---------------------------------------------------------------------------
# B. 反触发四类
# ---------------------------------------------------------------------------

ANTI_TRIGGER_HEADING = "### 严禁委派（反触发条件）"
REQUIRED_ANTI_TRIGGERS = (
    ("宿主原生反触发", ("invoke_subagent", "终端套娃", "原生子智能体")),
    ("架构与设计文档", ("架构与设计文档", "IMPLEMENTATION_PLAN.md", "task.md", "严禁")),
    ("Git 写操作与破坏性操作", ("Git 写操作", "git commit", "git push", "破坏性")),
    ("安全凭据与交互式决策", ("安全凭据", "密钥", "交互")),
)


def extract_section(text, heading, stop="## "):
    """截取 heading 行到下一个同级/更高级标题之间的正文。"""
    m = re.search(r"^" + re.escape(heading) + r"\s*$", text, re.MULTILINE)
    assert m, f"SKILL.md 缺少小节标题: {heading}"
    rest = text[m.end():]
    nxt = re.search(r"^" + re.escape(stop) + r"[^#]", rest, re.MULTILINE)
    return rest[: nxt.start()] if nxt else rest


def test_anti_trigger_four_categories_present():
    section = extract_section(read(SKILL_MD), ANTI_TRIGGER_HEADING)
    bullets = [line.strip() for line in section.splitlines() if line.strip().startswith("* ")]
    assert len(bullets) == 4, f"反触发条件必须恰好四条，实际 {len(bullets)} 条: {bullets}"
    for label, needles in REQUIRED_ANTI_TRIGGERS:
        hits = [b for b in bullets if all(n in b for n in needles)]
        assert len(hits) == 1, (
            f"反触发「{label}」必须由独立且唯一的一条要点声明（命中 {len(hits)} 条）"
        )


# ---------------------------------------------------------------------------
# C. SSOT 边界
# ---------------------------------------------------------------------------

def test_ssot_boundary_sentence_is_pinned():
    text = read(SKILL_MD)
    m = re.search(r"^>\s*\*\*SSOT 边界\*\*.*$", text, re.MULTILINE)
    assert m, "SKILL.md 必须声明 SSOT 边界段"
    line = m.group(0)
    assert "以本技能为准" in line, "SSOT 边界必须声明委派细则以本技能为准"
    assert "不在全局层复制" in line, "SSOT 边界必须声明不在全局层复制细则"


# ---------------------------------------------------------------------------
# D. 优先级链三级顺序
# ---------------------------------------------------------------------------

PRIORITY_SECTION = "## 执行智能体优先级链与宿主自适应 (Priority Chain & Host Awareness)"
PRIORITY_CHAIN = ("宿主环境原生派发", "无头命令行执行", "兜底 前台直接编写")


def test_priority_chain_has_three_ordered_levels():
    section = extract_section(read(SKILL_MD), PRIORITY_SECTION)
    positions = [section.find(marker) for marker in PRIORITY_CHAIN]
    assert all(p >= 0 for p in positions), (
        f"优先级链缺少级别: {[m for m, p in zip(PRIORITY_CHAIN, positions) if p < 0]}"
    )
    assert positions == sorted(positions), (
        "优先级链顺序必须是 宿主原生派发 -> 无头命令行执行 -> 兜底直接编写"
    )
    assert re.findall(r"^(\d)\. \*\*", section, re.MULTILINE) == ["1", "2", "3"], (
        "优先级链三级必须以 1./2./3. 顺序编号"
    )


# ---------------------------------------------------------------------------
# E. 标准委派 SOP 五步
# ---------------------------------------------------------------------------

SOP_SECTION = "## 标准委派 SOP (5-Step Delegation Procedure)"
SOP_STEPS = (
    "### 1. 编写自包含任务 Prompt",
    "### 2. 清理环境代理并启动任务",
    "### 3. 多任务编排与并行准则",
    "### 4. 假失败排查与超时防御",
    "### 5. 严格 6 步验收审查",
)


def test_standard_sop_has_five_ordered_steps():
    section = extract_section(read(SKILL_MD), SOP_SECTION)
    positions = [section.find(step) for step in SOP_STEPS]
    assert all(p >= 0 for p in positions), (
        f"SOP 缺少步骤: {[s for s, p in zip(SOP_STEPS, positions) if p < 0]}"
    )
    assert positions == sorted(positions), "SOP 五步必须按 1..5 顺序出现"
    assert len(re.findall(r"^### \d+\. ", section, re.MULTILINE)) == 5, (
        "SOP 小节必须恰好包含五个编号步骤标题"
    )


# ---------------------------------------------------------------------------
# F. 技能内链接完整性 / 跨技能链接
# ---------------------------------------------------------------------------

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(\s*([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\s*\)")
LINK_EXEMPT = re.compile(r"^(?:https?://|mailto:|#)")

# 跨技能相对链接 / 逃逸链接：../、./../、绝对路径、Windows 反斜杠形态。
# 正则自身由 test_cross_skill_link_scanner_self_check 自检，防止出现恒真空断言。
CROSS_SKILL_LINK = re.compile(r"(?:^|[\\/])\.\.(?:[\\/]|$)|^[\\/]|^[A-Za-z]:")


def is_cross_skill_link(target):
    """相对链接中任何父目录逃逸（../）或绝对路径都是跨技能/越界硬链接。"""
    norm = target.replace("\\", "/")
    return bool(CROSS_SKILL_LINK.search(norm)) or (".." in norm.split("/"))


def iter_relative_links(text):
    """逐行产出技能内相对链接: (行号, 原始 target, 去掉 fragment 的路径部分)。"""
    for line_no, line in enumerate(text.splitlines(), 1):
        for m in MARKDOWN_LINK.finditer(line):
            target = m.group(1)
            if LINK_EXEMPT.match(target):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            yield line_no, target, path_part


def test_skill_md_relative_links_exist_inside_skill_dir():
    links = list(iter_relative_links(read(SKILL_MD)))
    assert links, "SKILL.md 必须包含指向 references/templates/scripts 的相对链接"
    prefixes = {target.split("/", 1)[0] for _, _, target in links}
    assert {"references", "templates", "scripts"} <= prefixes, (
        f"SKILL.md 交付面链接不完整（缺失: {({'references', 'templates', 'scripts'} - prefixes)}）"
    )
    root = SKILL_DIR.resolve()
    for line_no, target, path_part in links:
        assert not is_cross_skill_link(target), (
            f"SKILL.md:{line_no} 出现跨技能/越界相对链接: {target}"
        )
        resolved = (SKILL_DIR / path_part).resolve()
        assert resolved.is_relative_to(root), f"SKILL.md:{line_no} 链接逸出技能目录: {target}"
        assert resolved.is_file(), f"SKILL.md:{line_no} 链接目标不存在: {target}"


def test_no_cross_skill_relative_links_in_skill_docs():
    offenders = []
    for doc in sorted(SKILL_DIR.rglob("*.md")):
        for line_no, target, _ in iter_relative_links(read(doc)):
            if is_cross_skill_link(target):
                offenders.append(f"{doc.relative_to(SKILL_DIR)}:{line_no}: {target}")
    assert not offenders, "禁止跨技能相对路径硬链接（独立分发会断链）: " + "; ".join(offenders)


def test_cross_skill_link_scanner_self_check():
    illegal = [
        "../goal-loop/SKILL.md",
        "../taste-driven-designer/references/x.md",
        "./../dual-round-review/SKILL.md",
        "../../skills/doc-governance/SKILL.md",
        "references/../../other-skill/x.md",
        "..\\goal-loop\\SKILL.md",
        "/abs/skills/goal-loop/SKILL.md",
    ]
    for sample in illegal:
        assert is_cross_skill_link(sample), f"跨技能/逃逸链接漏检: {sample}"
    legal = [
        "references/priority-fallback-chain.md",
        "templates/task-prompt-template.md",
        "scripts/dispatch-agy.py",
        "#when-to-use",
        "https://example.com/agy-delegation-workflow.md",
    ]
    for sample in legal:
        assert not is_cross_skill_link(sample), f"技能内链接被误判为跨技能: {sample}"


# ---------------------------------------------------------------------------
# G. scripts/dispatch-agy.py 行为契约（假 agy + 临时 git 仓库，离线确定）
# ---------------------------------------------------------------------------

FAKE_AGY_HELPER = '''# 测试用假 agy：仅记录 argv/env 后立即退出；绝不触达真实 CLI、仓库或网络。
import os
import sys

argv_file, env_file, marker_file = sys.argv[1], sys.argv[2], sys.argv[3]
with open(argv_file, "wb") as handle:
    for value in sys.argv[4:]:
        handle.write(value.encode("utf-8") + b"\\0")
with open(env_file, "w", encoding="utf-8", newline="\\n") as handle:
    for key, value in os.environ.items():
        handle.write(f"{key}={value}\\n")
sys.stdout.write("fake-agy-stdout\\n")
sys.stdout.flush()
open(marker_file, "w", encoding="utf-8").close()
sys.exit(0)
'''


def install_fake_agy(bindir, argv_file, env_file, marker_file):
    """安装跨平台假 agy shim：POSIX 为 bash 包装，Windows 为 .cmd 包装（PATHEXT 可发现）。"""
    bindir.mkdir(parents=True, exist_ok=True)
    helper = bindir / "fake_agy.py"
    helper.write_text(FAKE_AGY_HELPER, encoding="utf-8")
    quoted = " ".join(
        f'"{item}"' for item in (sys.executable, helper, argv_file, env_file, marker_file)
    )
    if os.name == "nt":
        shim = bindir / "agy.cmd"
        shim.write_text(
            f"@echo off\r\n{quoted} %*\r\n", encoding="utf-8", newline=""
        )
    else:
        shim = bindir / "agy"
        shim.write_text(f'#!/usr/bin/env bash\nexec {quoted} "$@"\n', encoding="utf-8")
        shim.chmod(0o755)
    return shim


@pytest.fixture
def dispatch_env(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    bindir = tmp_path / "fake-bin"
    argv_file = tmp_path / "agy-argv.bin"
    env_file = tmp_path / "agy-env.txt"
    marker_file = tmp_path / "agy-ran.marker"
    install_fake_agy(bindir, argv_file, env_file, marker_file)
    return SimpleNamespace(
        tmp_path=tmp_path,
        repo=repo,
        root=os.path.realpath(str(repo)),
        path=str(bindir) + os.pathsep + os.environ.get("PATH", ""),
        argv_file=argv_file,
        env_file=env_file,
        marker_file=marker_file,
    )


def run_dispatch(env, args, cwd=None, path=None):
    # 契约迁移：实现已迁至跨平台 dispatch-agy.py，统一用当前解释器执行（Windows 原生可用）。
    child_env = dict(os.environ)
    child_env["PATH"] = env.path if path is None else path
    child_env.pop("AGY_MODEL", None)
    for var in PROXY_VARS:
        child_env[var] = "http://127.0.0.1:9/proxy-must-be-stripped"
    return subprocess.run(
        [sys.executable, str(DISPATCH), *args],
        cwd=str(cwd if cwd is not None else env.repo),
        env=child_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )


def run_compat_shell(env, args, cwd=None, path=None):
    child_env = dict(os.environ)
    child_env["PATH"] = env.path if path is None else path
    child_env.pop("AGY_MODEL", None)
    for var in PROXY_VARS:
        child_env[var] = "http://127.0.0.1:9/proxy-must-be-stripped"
    return subprocess.run(
        [BASH, str(COMPAT_SHELL), *args],
        cwd=str(cwd if cwd is not None else env.repo),
        env=child_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )


def same_path(left, right):
    """跨平台路径等价判定（Windows 上 git 返回正斜杠形态，归一化后比较）。"""
    return os.path.normcase(os.path.realpath(left)) == os.path.normcase(os.path.realpath(right))


def read_agy_argv(env):
    assert env.argv_file.is_file(), "假 agy 未被调用（argv 记录文件不存在）"
    return [part.decode("utf-8") for part in env.argv_file.read_bytes().split(b"\0") if part]


def read_env_file(path):
    entry = {}
    for line in read(path).splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            entry[key] = value
    return entry


def flag_value(argv, flag):
    assert flag in argv, f"argv 缺少 {flag}: {argv}"
    idx = argv.index(flag)
    assert idx + 1 < len(argv), f"{flag} 缺少取值: {argv}"
    return argv[idx + 1]


def wait_for(path, timeout=5.0, interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not path.exists():
        time.sleep(interval)
    return path.exists()


def test_g1_help_exits_zero_and_lists_task_flags(dispatch_env):
    r = run_dispatch(dispatch_env, ["--help"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "-f, --file" in r.stdout, r.stdout
    assert "-p, --prompt" in r.stdout, r.stdout


def test_g2_without_task_requires_prompt_content(dispatch_env):
    r = run_dispatch(dispatch_env, [])
    assert r.returncode != 0, "无参数时必须非零退出"
    assert "指定任务内容" in r.stdout + r.stderr, r.stdout + r.stderr


def test_g3_missing_task_file_is_rejected(dispatch_env):
    missing = dispatch_env.tmp_path / "no-such-task.md"
    r = run_dispatch(dispatch_env, ["-f", str(missing)])
    assert r.returncode == 1, r.stdout + r.stderr
    assert "文件不存在" in r.stdout + r.stderr, r.stdout + r.stderr


def test_g4_missing_agy_binary_is_reported(dispatch_env):
    empty_bin = dispatch_env.tmp_path / "empty-bin"
    empty_bin.mkdir()
    r = run_dispatch(dispatch_env, ["-p", "x"], path=str(empty_bin))
    assert r.returncode == 1, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert "未找到" in out and "agy" in out, out


def test_g5_foreground_dispatch_argv_and_proxy_stripping(dispatch_env):
    r = run_dispatch(dispatch_env, ["-p", "CONTRACT CONTENT 42"])
    assert r.returncode == 0, r.stdout + r.stderr
    argv = read_agy_argv(dispatch_env)
    assert same_path(flag_value(argv, "--add-dir"), dispatch_env.root), argv
    assert flag_value(argv, "-p") == "CONTRACT CONTENT 42", argv
    assert flag_value(argv, "--model") == DEFAULT_MODEL, argv
    assert flag_value(argv, "--print-timeout") == DEFAULT_TIMEOUT, argv
    assert "--dangerously-skip-permissions" in argv, argv

    child_env = read_env_file(dispatch_env.env_file)
    leaked = [var for var in PROXY_VARS if var in child_env]
    assert not leaked, f"子进程环境仍带代理变量（WSL proxyconnect 根因，脚本必须清除）: {leaked}"
    assert same_path(child_env.get("HINDSIGHT_MCP_PROJECT_CWD", ""), dispatch_env.root), (
        "脚本必须把仓库根同时导出给 Hindsight MCP server（bank 归属修复）"
    )


def test_g5_file_dispatch_reads_prompt_and_registers_repo_root(dispatch_env):
    task_dir = dispatch_env.repo / ".agy-tasks"
    task_dir.mkdir()
    task = task_dir / "task-a.md"
    task.write_text("FILE CONTENT 7\n", encoding="utf-8")
    outside = dispatch_env.tmp_path / "outside"
    outside.mkdir()

    r = run_dispatch(dispatch_env, ["-f", str(task)], cwd=outside)
    assert r.returncode == 0, r.stdout + r.stderr
    argv = read_agy_argv(dispatch_env)
    assert same_path(flag_value(argv, "--add-dir"), dispatch_env.root), argv
    assert flag_value(argv, "-p") == "FILE CONTENT 7", argv


def test_g6_background_mode_reports_pid_and_writes_log(dispatch_env):
    r = run_dispatch(dispatch_env, ["-p", "BG CONTENT", "-b"])
    assert r.returncode == 0, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert re.search(r"PID:\s*\d+", out), out

    log_match = re.search(r"日志输出至:\s*(\S+)", out)
    assert log_match, out
    log_rel = log_match.group(1)
    assert log_rel.startswith(".agy-tasks/logs/"), log_rel

    assert wait_for(dispatch_env.marker_file), "假 agy 未在后台运行完成"
    log_path = dispatch_env.repo / log_rel
    assert log_path.is_file(), f"后台模式必须生成日志文件: {log_path}"
    assert "fake-agy-stdout" in read(log_path), "后台日志必须承载 agy 输出"


# ---------------------------------------------------------------------------
# H. 兼容壳契约（契约迁移：.sh 退化为 §2.2 兼容壳，必须与 .py 输出/退出码一致）
# ---------------------------------------------------------------------------

@POSIX_ONLY
def test_h1_compat_shell_help_matches_python(dispatch_env):
    direct = run_dispatch(dispatch_env, ["--help"])
    shell = run_compat_shell(dispatch_env, ["--help"])
    assert shell.returncode == direct.returncode
    assert shell.stdout == direct.stdout


@POSIX_ONLY
def test_h2_compat_shell_failure_matches_python(dispatch_env):
    # 用「任务文件不存在」这一错误路径对照：兼容壳经 python3 转发，需保留宿主 PATH。
    missing = dispatch_env.tmp_path / "no-such-task.md"
    direct = run_dispatch(dispatch_env, ["-f", str(missing)])
    shell = run_compat_shell(dispatch_env, ["-f", str(missing)])
    assert shell.returncode == direct.returncode == 1
    assert shell.stderr == direct.stderr
