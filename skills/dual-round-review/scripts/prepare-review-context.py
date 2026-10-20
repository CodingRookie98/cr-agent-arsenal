#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prepare-review-context.py — 提取双轮审查所需的 Git Diff 与统计信息。

支持工作区未提交审查 (--working)、暂存区审查 (--staged) 以及版本范围审查 (BASE...HEAD)。

功能编号：
  1) 帮助优先（无需位于 Git 仓库）；
  2) 前置环境检查：必须在 Git 仓库工作区内运行；
  3) 参数解析（选项顺序无关）+ slug / 轮次参数校验（RFC-0001 §3.3、RFC-0002 §3.2）；
  4) 四种审查模式的上下文输出（working / staged / root / range）；
  5) 写入审查记录锚点 .review-context/review-<baseline>.md（Delta Re-Loop 读取源）；
  6) 交付凭据归档 scaffold（--slug）+ 幂等 upsert 归档索引段；
  7) 预授权报告目标路径（--round，Write-Once 保护）。

用法: python3 prepare-review-context.py [选项] [BASE_SHA [HEAD_SHA]]
退出码: 0 = 成功；1 = 用法错误/环境错误/无效 Commit Ref
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date

USAGE = """用法: prepare-review-context.sh [选项] [BASE_SHA [HEAD_SHA]]

提取双轮审查所需上下文，并生成审查记录锚点 .review-context/review-<baseline>.md

选项:
  -w, --working      审查工作区未提交改动（默认有改动时自动选择）
  -s, --staged       审查暂存区改动
      --no-record    只打印上下文，不写审查记录锚点与归档目录
      --slug=<slug>  启用交付凭据归档 scaffold（RFC-0001）；不传则仅生成运行时锚点
      --round=<轮次>  输出本轮「预授权报告目标路径」（RFC-0002 子智能体直写通道）；
                     取值 r1|r2|delta-r1|delta-r2，必须与 --slug 同时使用
      --archive-root=<路径>
                     归档根（默认 docs/project/reviews，仅与 --slug 联动）
  -h, --help         显示本帮助

参数:
  BASE_SHA [HEAD_SHA]  审查指定提交区间（默认 BASE...HEAD）

记录锚点: .review-context/review-<baseline>.md（已 gitignore），供 Delta Re-Loop 读取 Previous Blockers 与迭代计数。
交付凭据归档: 传 --slug 时另在 <archive-root>/<YYYY-MM-DD>-<slug>/ 生成归档索引 README.md（进版本库，
              供人类与子智能体阅读报告全文）；复用既有同 slug 目录，Delta 再循环不新建。
"""

SEP_EQ = "=" * 70
SEP_DASH = "-" * 70
ROUND_VALUES = ("r1", "r2", "delta-r1", "delta-r2")


class _Exit(Exception):
    """用法错误/环境错误导致的提前退出（携带退出码）。"""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def _run_git(args: list[str], capture: bool = False, quiet: bool = False) -> tuple[int, str]:
    """执行 git 子命令：capture=True 时返回 (退出码, 剥尾换行后的 stdout)。"""
    sys.stdout.flush()
    sys.stderr.flush()
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.DEVNULL if quiet else None,
    )
    if not capture:
        return proc.returncode, ""
    return proc.returncode, proc.stdout.decode("utf-8", "surrogateescape").rstrip("\n")


def _emit(text: str) -> None:
    sys.stdout.write(text)


def _parse_args(argv: list[str]) -> dict[str, object]:
    """3) 参数解析（选项顺序无关）——帮助优先，非法选项报错并打印用法。"""
    opts: dict[str, object] = {
        "mode": "range",
        "no_record": False,
        "slug": "",
        "round": "",
        "round_set": False,
        "archive_root": "docs/project/reviews",
        "positional": [],
    }
    positional: list[str] = opts["positional"]  # type: ignore[assignment]
    for arg in argv:
        if arg in ("-h", "--help"):
            sys.stdout.write(USAGE)
            raise _Exit(0)
        if arg in ("-w", "--working"):
            opts["mode"] = "working"
        elif arg in ("-s", "--staged"):
            opts["mode"] = "staged"
        elif arg == "--no-record":
            opts["no_record"] = True
        elif arg.startswith("--slug="):
            opts["slug"] = arg[len("--slug="):]
        elif arg.startswith("--round="):
            opts["round"] = arg[len("--round="):]
            opts["round_set"] = True
        elif arg.startswith("--archive-root="):
            opts["archive_root"] = arg[len("--archive-root="):]
        elif arg.startswith("-"):
            sys.stderr.write(f"❌ 错误: 未知选项 '{arg}'\n")
            sys.stderr.write(USAGE)
            raise _Exit(1)
        else:
            positional.append(arg)
    return opts


def _validate(opts: dict[str, object]) -> None:
    """3) 归档参数与轮次参数校验（RFC-0001 §3.3 / RFC-0002 §3.2）。"""
    slug = str(opts["slug"])
    if slug and not _is_kebab_case(slug):
        sys.stderr.write(f"❌ 错误: --slug 必须为小写 kebab-case（^[a-z0-9][a-z0-9-]*$）: {slug}\n")
        raise _Exit(1)
    # BK-0010：归档根空值/文件系统根会在写盘阶段把归档散落到任意位置，必须在解析后立即拦截。
    archive_root = str(opts["archive_root"])
    if archive_root == "":
        sys.stderr.write(
            "❌ 错误: --archive-root 值不能为空（空值会回退当前目录，报告可能落在任意位置；"
            "请显式给出仓库内相对路径，如 --archive-root=docs/project/reviews）\n"
        )
        raise _Exit(1)
    root_abs = os.path.realpath(archive_root)
    if os.path.dirname(root_abs) == root_abs:
        sys.stderr.write(
            f"❌ 错误: --archive-root 不能为文件系统根目录: {archive_root}"
            "（含经符号链接解析后指向根的情形；报告会散落在根目录；"
            "请改用仓库内相对路径，如 --archive-root=docs/project/reviews）\n"
        )
        raise _Exit(1)
    if not opts["round_set"]:
        return
    round_value = str(opts["round"])
    # R1-7 回归：以独立标志记录「选项已出现」——空值 `--round=` 不得被静默短路。
    if round_value == "":
        sys.stderr.write("❌ 错误: --round 值不能为空（空值会静默禁用预授权路径输出）\n")
        raise _Exit(1)
    if opts["no_record"]:
        sys.stderr.write("❌ 错误: --round 与 --no-record 互斥（--no-record 不落盘，无预授权写入面可言）\n")
        raise _Exit(1)
    if slug == "":
        sys.stderr.write("❌ 错误: --round 必须与 --slug 同时使用（报告目标路径依赖归档目录）\n")
        raise _Exit(1)
    if round_value not in ROUND_VALUES:
        sys.stderr.write(f"❌ 错误: --round 取值必须为 r1|r2|delta-r1|delta-r2，实际: {round_value}\n")
        raise _Exit(1)


def _is_kebab_case(value: str) -> bool:
    """复刻 `^[a-z0-9][a-z0-9-]*$`。"""
    if not value:
        return False
    if not (value[0].isascii() and (value[0].islower() or value[0].isdigit())):
        return False
    for char in value[1:]:
        if not (char.isascii() and (char.islower() or char.isdigit() or char == "-")):
            return False
    return True


def _resolve_mode(opts: dict[str, object]) -> tuple[str, str, str]:
    """4) 决定审查模式与区间；返回 (MODE, BASE_REF, HEAD_REF)。"""
    mode = str(opts["mode"])
    positional = opts["positional"]
    base_ref = ""
    head_ref = ""
    if len(positional) >= 2:  # type: ignore[arg-type]
        base_ref = str(positional[0])  # type: ignore[index]
        head_ref = str(positional[1])  # type: ignore[index]
        mode = "range"
    elif len(positional) == 1:  # type: ignore[arg-type]
        base_ref = str(positional[0])  # type: ignore[index]
        head_ref = "HEAD"
        mode = "range"
    elif mode not in ("working", "staged"):
        # RFC-0002 §3.2（R1-1 回归）：预授权路径必须是基线的**确定函数**。
        if opts["round_set"]:
            sys.stderr.write(
                "❌ 错误: --round 要求确定性基线——请显式指定 BASE_SHA [HEAD_SHA]，或显式给出 --working / --staged。\n"
            )
            sys.stderr.write(
                "   原因: 自适应模式会在两次调用间切换 working/range，导致预授权路径漂移（RFC-0002 §3.2 / R1-1）。\n"
            )
            raise _Exit(1)
        # 未指定模式与区间时智能自适应：有改动优先未提交审查，否则检查最近一次提交
        _, dirty = _run_git(["status", "--porcelain"], capture=True)
        dirty_count = len(dirty.split("\n")) if dirty else 0
        if dirty_count > 0:
            mode = "working"
        else:
            rc, count = _run_git(["rev-list", "--count", "HEAD"], capture=True, quiet=True)
            if rc != 0 or not count.strip().isdigit():
                count = "0"
            if int(count) <= 1:
                mode = "root"
            else:
                base_ref, head_ref, mode = "HEAD~1", "HEAD", "range"
    return mode, base_ref, head_ref


def _untracked_paths(status_z: str) -> str:
    """提取未跟踪文件路径（BK-0045；R1-7 改用 NUL 分隔输出）。

    历史实现复刻了 `git status -s | grep '^\\?\\?' | awk '{print $2}'` 在 GNU BRE 下的
    缺陷：`\\?` 是「前一项出现 0 或 1 次」的重复算子而非字面问号，过滤恒匹配全部行，
    导致「未跟踪新增文件」清单实际列出所有变更条目。此处改为平台无关的显式判定。

    输出解析使用 `git status --porcelain -z`（NUL 分隔）：git 在该模式下不对路径加
    引号，也不做 C 风格八进制转义，因此中文/空格路径按原样呈现（R1-7）。
    """
    paths = []
    for entry in status_z.split("\0"):
        if not entry.startswith("?? "):
            continue
        path = entry[3:]
        if path:
            paths.append(path)
    return "\n".join(paths)


def _emit_working(record: dict[str, str]) -> int:
    """4) 工作区变更审查输出块。"""
    record["base"] = "working"
    _, head = _run_git(["rev-parse", "--short", "HEAD"], capture=True, quiet=True)
    record["head"] = head or "none"
    _emit("📌 审查模式: 工作区变更审查 (Working Tree & Staged vs HEAD)\n")
    _emit(SEP_DASH + "\n")
    _emit("📊 工作区未提交状态 (Git Status):\n")
    rc, _ = _run_git(["status", "-s"])
    if rc != 0:
        return rc
    _emit("\n")
    _, status_z = _run_git(["status", "--porcelain", "-z"], capture=True)
    untracked_text = _untracked_paths(status_z)
    if untracked_text:
        _emit("⚠️ 发现未跟踪的新增文件 (Untracked Files):\n")
        _emit(untracked_text + "\n")
        _emit("\n")
        _emit("💡 提示: Git 默认不对比未跟踪文件。若要审查新增代码，请先执行:\n")
        _emit("   git add -N .   # 标记为 intent-to-add（不暂存内容，但使其可被 git diff 完整捕获）\n")
        _emit("   然后再运行本脚本以生成完整 Diff。\n")
        _emit("\n")
    _emit(SEP_DASH + "\n")
    _emit("📊 变更统计 (Diff Stat vs HEAD):\n")
    _run_git(["diff", "HEAD", "--stat"])
    _emit("\n")
    _emit("📋 变动文件清单:\n")
    _run_git(["diff", "HEAD", "--name-only"])
    _emit("\n")
    _emit("💡 审查子智能体 Diff 命令建议:\n")
    _emit("   git diff HEAD\n")
    return 0


def _emit_staged(record: dict[str, str]) -> int:
    """4) 暂存区审查输出块。"""
    record["base"] = "staged"
    _, head = _run_git(["rev-parse", "--short", "HEAD"], capture=True, quiet=True)
    record["head"] = head or "none"
    _emit("📌 审查模式: 暂存区审查 (Staged / Cached vs HEAD)\n")
    _emit(SEP_DASH + "\n")
    _emit("📊 暂存区变更统计 (Diff Stat --cached):\n")
    rc, _ = _run_git(["diff", "--cached", "--stat"])
    if rc != 0:
        return rc
    _emit("\n")
    _emit("📋 暂存文件清单:\n")
    rc, _ = _run_git(["diff", "--cached", "--name-only"])
    if rc != 0:
        return rc
    _emit("\n")
    _emit("💡 审查子智能体 Diff 命令建议:\n")
    _emit("   git diff --cached\n")
    return 0


def _emit_root(record: dict[str, str]) -> int:
    """4) 仓库初始提交审查输出块。"""
    _emit("📌 审查模式: 仓库初始提交审查 (Root Commit)\n")
    rc, _ = _run_git(["rev-parse", "--verify", "HEAD"], capture=True, quiet=True)
    if rc != 0:
        _emit("⚠️ 当前分支尚无任何提交 (0 commits)。请先完成首次提交或添加工作区修改后再触发审查。\n")
        return -1
    _, root_commit = _run_git(["rev-list", "--max-parents=0", "HEAD"], capture=True)
    root_commit = root_commit.split("\n")[0]
    _, short = _run_git(["rev-parse", "--short", root_commit], capture=True)
    record["base"] = short
    record["head"] = short
    _emit(f"Root Commit: {root_commit}\n")
    _emit("\n")
    _emit("📊 初始提交统计:\n")
    rc, _ = _run_git(["show", "--stat", root_commit])
    if rc != 0:
        return rc
    _emit("\n")
    _emit("💡 审查子智能体 Diff 命令建议:\n")
    _emit(f"   git show {root_commit}\n")
    return 0


def _emit_range(record: dict[str, str], base_ref: str, head_ref: str) -> int:
    """4) 提交区间审查输出块（严格校验必须为 Commit 对象）。"""
    rc, _ = _run_git(["rev-parse", "--verify", f"{base_ref}^{{commit}}"], capture=True, quiet=True)
    if rc != 0:
        sys.stderr.write(f"❌ 错误: 无效的 Base Commit Ref: {base_ref}\n")
        return 1
    rc, _ = _run_git(["rev-parse", "--verify", f"{head_ref}^{{commit}}"], capture=True, quiet=True)
    if rc != 0:
        sys.stderr.write(f"❌ 错误: 无效的 Head Commit Ref: {head_ref}\n")
        return 1
    _, base_sha = _run_git(["rev-parse", f"{base_ref}^{{commit}}"], capture=True)
    _, head_sha = _run_git(["rev-parse", f"{head_ref}^{{commit}}"], capture=True)
    _, short_base = _run_git(["rev-parse", "--short", base_sha], capture=True)
    _, short_head = _run_git(["rev-parse", "--short", head_sha], capture=True)
    record["base"] = short_base
    record["head"] = short_head
    _emit(f"📌 审查模式: 提交区间审查 ({base_ref}...{head_ref})\n")
    _emit(f"Base SHA: {base_sha}\n")
    _emit(f"Head SHA: {head_sha}\n")
    _emit("\n")
    _, dirty = _run_git(["status", "--porcelain"], capture=True)
    if dirty:
        _emit("⚠️ 提醒: 检测到工作区存在未提交变更（不包含在本次 commit 区间中）：\n")
        _emit(dirty + "\n")
        _emit("\n")
    _emit(SEP_DASH + "\n")
    _emit("📊 提交区间统计 (基于 Merge-Base 的三点式 Diff Stat):\n")
    rc, _ = _run_git(["diff", "--stat", f"{base_sha}...{head_sha}"])
    if rc != 0:
        return rc
    _emit("\n")
    _emit("📝 包含的提交列表 (Commits on Head):\n")
    rc, _ = _run_git(["log", "--oneline", f"{base_sha}..{head_sha}"])
    if rc != 0:
        return rc
    _emit("\n")
    _emit("📋 变动文件清单:\n")
    rc, _ = _run_git(["diff", "--name-only", f"{base_sha}...{head_sha}"])
    if rc != 0:
        return rc
    _emit("\n")
    _emit("💡 审查子智能体 Diff 命令建议 (推荐三点式防止上游逆向污染):\n")
    _emit(f"   git diff {base_sha}...{head_sha}\n")
    return 0


def _resolve_archive_dir(root: str, slug: str) -> str:
    """6) 解析归档目录：复用既有同 slug 目录，否则按当天日期新建。"""
    matched = sorted(
        (f"{root}/{name}" for name in _glob_entries(root) if name.endswith("-" + slug)),
        key=lambda value: value.encode("utf-8", "surrogateescape"),
    )
    if matched:
        return matched[-1]
    return f"{root}/{date.today().isoformat()}-{slug}"


def _glob_entries(root: str) -> list[str]:
    """复刻 `ls -d "<root>"/*-"<slug>"` 的目录名枚举（bash glob 不匹配点开头项）。"""
    try:
        return [name for name in os.listdir(root) if not name.startswith(".")]
    except OSError:
        return []


def _upsert_archive_index(path: str, archive_dir: str) -> None:
    """6) 锚点内「归档索引」段：存在则先移除旧段再追加，保证幂等。"""
    text = _read_text(path)
    if "## 归档索引" in text:
        kept: list[str] = []
        skip = False
        for line in _split_lines(text):
            if line.startswith("## 归档索引"):
                skip = True
                continue
            if line.startswith("## "):
                skip = False
            if not skip:
                kept.append(line)
        text = "".join(line + "\n" for line in kept)
    block = (
        "\n"
        "## 归档索引 (Archive Index)\n"
        f"- **归档根**: {archive_dir}\n"
        f"- **轮次台账**: {archive_dir}README.md\n"
    )
    _write_text(path, text + block)


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        return handle.read()


def _split_lines(text: str) -> list[str]:
    """按 awk/grep 的记录语义切行：文件末尾换行不产生额外空记录。"""
    if text == "":
        return []
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _write_record(record: dict[str, str], slug: str, archive_root: str, round_value: str) -> int:
    """5)+6)+7) 审查记录锚点、归档 scaffold、预授权报告目标路径。"""
    os.makedirs(".review-context", exist_ok=True)
    base = record.get("base") or "unknown"
    head = record.get("head") or "unknown"
    record_file = f".review-context/review-{base}.md"
    if not os.path.isfile(record_file):
        _write_text(
            record_file,
            f"# 审查记录 · {base}\n"
            "- **模式**: [full | light | delta]\n"
            f"- **基线**: {base}..{head}\n"
            "- **轮次**: [1 | 2 | ...]\n"
            "- **迭代计数**: [0/3]\n"
            "- **Previous Blockers**: 无\n"
            "- **Round 1 结论**: [待填写]\n"
            "- **终审裁决**: 未定\n"
            "- **阻断项统计**: [🔴 0 / 🟡 0 / ⚪ 0]\n",
        )
        _emit(f"📝 已生成审查记录锚点: {record_file}\n")
    else:
        _emit(f"📝 复用既有审查记录锚点: {record_file}\n")
    if slug == "":
        return 0
    archive_dir = _resolve_archive_dir(archive_root, slug)
    try:
        os.makedirs(archive_dir, exist_ok=True)
    except OSError:
        sys.stderr.write(f"❌ 错误: 无法创建归档目录: {archive_dir}\n")
        return 1
    return _scaffold_archive(record_file, archive_dir, slug, round_value, base, head)


def _scaffold_archive(
    record_file: str, archive_dir: str, slug: str, round_value: str, base: str, head: str
) -> int:
    """6)+7) 归档索引模板、幂等 upsert、预授权报告目标路径。"""
    archive_index = os.path.join(archive_dir, "README.md")
    if not os.path.isfile(archive_index):
        _write_text(
            archive_index,
            f"# 审查归档 · {slug}\n"
            "\n"
            "> **文档控制信息**\n"
            f"> - **文档标识**: REVIEW-ARCHIVE-{slug}\n"
            "> - **当前版本**: V1.0.0\n"
            "> - **维护负责人**: 主调度智能体\n"
            f"> - **生效日期**: {date.today().isoformat()}\n"
            "\n"
            f"- **交付单元**: {slug}\n"
            f"- **归档根**: {archive_dir}/\n"
            "- **审查模式**: [full | light | delta]\n"
            "- **当前迭代计数**: [0/3]\n"
            "- **终审裁决**: 未定（取值必须**精确**为 准予交付 / 阻断交付 / 未定 三者之一；"
            "禁止保留占位符方括号或附加解释）\n"
            "\n"
            "## 轮次台账\n"
            "| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            "\n"
            "## 报告清单\n"
            "> 每轮归档后在此追加一行 markdown 链接，供人类与子智能体按路径直达：\n"
            "> - [<报告文件>](./<报告文件>)\n"
            "\n"
            "## 待办与后续轮次\n"
            "- [ ] 待第一次审查派发后登记\n",
        )
        _emit(f"📦 已生成归档索引: {archive_index}\n")
    else:
        _emit(f"📦 复用既有归档索引: {archive_index}\n")
    _upsert_archive_index(record_file, archive_dir + "/")
    _emit(f"📦 归档根已登记至锚点: {archive_dir}/\n")
    if round_value == "":
        return 0
    report_path = f"{archive_dir}/{round_value}-{base}..{head}.md"
    _emit(f"📄 本轮报告目标路径 (预授权写入面): {report_path}\n")
    if os.path.exists(report_path):
        _emit(f"⚠️ 目标文件已存在（Write-Once 保护）: {report_path}\n")
        _emit("   ↳ 视为基线漂移缺陷，严禁覆盖；请排查命名冲突后再派发。\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(sys.argv[1:] if argv is None else argv)
    # 0) 帮助优先（无需位于 Git 仓库）：仅当**首个**参数即 -h/--help 时短路
    if args and args[0] in ("-h", "--help"):
        sys.stdout.write(USAGE)
        return 0
    # 1) 前置环境检查：必须在 Git 仓库工作区内运行（先于其余参数解析）
    if _run_git(["rev-parse", "--is-inside-work-tree"], capture=True, quiet=True)[0] != 0:
        sys.stderr.write("❌ 错误: 当前目录并非 Git 工作区。\n")
        return 1
    try:
        opts = _parse_args(args)
        _validate(opts)
        mode, base_ref, head_ref = _resolve_mode(opts)
        _emit(SEP_EQ + "\n")
        _emit("🔍 准备双轮审查上下文 (Dual-Round Review Context)\n")
        _emit(SEP_EQ + "\n")
        record: dict[str, str] = {}
        if mode == "working":
            rc = _emit_working(record)
        elif mode == "staged":
            rc = _emit_staged(record)
        elif mode == "root":
            rc = _emit_root(record)
        else:
            rc = _emit_range(record, base_ref, head_ref)
        if rc == -1:
            return 0
        if rc != 0:
            return rc
        if not opts["no_record"]:
            rc = _write_record(record, str(opts["slug"]), str(opts["archive_root"]), str(opts["round"]))
            if rc != 0:
                return rc
        _emit(SEP_DASH + "\n")
        _emit(
            "⛔ 边界锁与审查重点见 verdict-rubric.md §3 与 round-1-red-team.md；"
            "运行时/SSR 维度仅在 diff 触及客户端代码时激活。\n"
        )
        _emit(SEP_EQ + "\n")
        return 0
    except _Exit as exc:
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
