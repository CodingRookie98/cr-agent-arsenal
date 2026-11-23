#!/usr/bin/env python3
"""pack-handoff.py — goal-loop V3.0 极薄文件指针交接脚本（纯标准库，跨平台）。"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

FENCE_RX, HEADING_RX, HR_RX = re.compile(r"^(\s*)(`{3,}|~{3,})"), re.compile(r"^(#{1,6})\s+(.*)$"), re.compile(r"^\s*---+\s*$")

def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1

def _emit(content: str, out: str | None) -> int:
    text = content.rstrip() + "\n"
    if out is None:
        sys.stdout.write(text)
        return 0
    if not out.strip():
        return _fail("--out 路径不能为空")
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(str(path))
    return 0

def _fence_step(fence: str, line: str) -> tuple[bool, str]:
    m = FENCE_RX.match(line)
    if not m:
        return bool(fence), fence
    ws, tok, rest, cur = m.group(1), m.group(2), line[m.end():], fence.lstrip()
    if not cur and (tok[0] == "~" or "`" not in rest):
        return True, ws + tok
    if cur and tok[0] == cur[0] and len(tok) >= len(cur) and not rest.strip():
        return True, ""
    return bool(cur), fence

def _fence_flags(lines: list[str]) -> list[bool]:
    flags, fence = [], ""
    for line in lines:
        in_f, fence = _fence_step(fence, line)
        flags.append(in_f)
    return flags

def _slice_block(lines: list[str], fenced: list[bool], start: int, level: int = 0, indent: int = -1, limit: int | None = None) -> str:
    buf = [lines[start]]
    for j in range(start + 1, len(lines)):
        nxt = lines[j]
        if not fenced[j]:
            nh = HEADING_RX.match(nxt)
            if HR_RX.match(nxt) or (level and nh and len(nh.group(1)) <= level):
                break
            if indent >= 0 and (nh or (nxt.strip() and len(nxt.expandtabs(2)) - len(nxt.expandtabs(2).lstrip(" ")) <= indent)):
                break
        buf.append(nxt)
    if limit and len(buf) > limit:
        buf, fence = buf[:limit], ""
        for line in buf:
            _, fence = _fence_step(fence, line)
        if fence:
            buf.extend((fence, "> ...（节选已截断）"))
    return "\n".join(buf).rstrip()

def _extract_section(lines: list[str], fenced: list[bool], pat: str, limit: int | None = None) -> str:
    rx = re.compile(pat, re.IGNORECASE)
    for i, ln in enumerate(lines):
        if not fenced[i] and (hm := HEADING_RX.match(ln)) and rx.search(hm.group(2)):
            return _slice_block(lines, fenced, i, level=len(hm.group(1)), limit=limit)
    return ""

def _extract_task(lines: list[str], fenced: list[bool], task_id: str) -> str:
    tid = re.sub(r"^task[\s-]+", "", task_id.strip(), flags=re.IGNORECASE)
    if not tid:
        return ""
    tail = rf"(?:\*\*)?(?:Task[\s-]+)?{re.escape(tid)}(?:\*\*)?(?=$|[\s:：—–()\[\]（）【】\*`]|[.-](?![A-Za-z0-9_]))"
    list_rx = re.compile(rf"^(\s*)(?:[-*+]|\d+\.)\s+(?:\[[ xX]\]\s+)?{tail}", re.IGNORECASE)
    head_rx = re.compile(rf"^(#{{2,6}})\s+{tail}", re.IGNORECASE)
    for i, ln in enumerate(lines):
        if not fenced[i]:
            if lm := list_rx.match(ln):
                return _slice_block(lines, fenced, i, indent=len(lm.group(1).expandtabs(2)))
            if hm := head_rx.match(ln):
                return _slice_block(lines, fenced, i, level=len(hm.group(1)))
    return ""

def cmd_brief(args: argparse.Namespace) -> int:
    plan = Path(args.plan_file)
    if not plan.is_file():
        return _fail(f"计划文件不存在: {plan}")
    lines = plan.read_text(encoding="utf-8").splitlines()
    fenced = _fence_flags(lines)
    task_block = _extract_task(lines, fenced, args.task)
    if not task_block:
        return _fail(f"未在计划文件中找到任务: {args.task}")
    title = next((ln for ln, f in zip(lines, fenced) if not f and ln.startswith("# ")), f"# {plan.name}")
    summary = "\n\n".join(s for s in (title, _extract_section(lines, fenced, r"Active\s+Checkpoint"), _extract_section(lines, fenced, r"测试策略", 35)) if s)
    return _emit(f"# 任务交接简报：{args.task}\n> 来源计划: `{plan}`\n\n## 计划摘要\n{summary}\n\n## 目标任务\n{task_block}", args.out)

def _git(repo: Path, *git_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-c", "core.quotePath=false", *git_args], cwd=str(repo), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False)

def cmd_review_pkg(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    if not repo.is_dir() or _git(repo, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        return _fail(f"不是合法 Git 仓库: {repo}")
    shas: list[str] = []
    for label, ref in (("base_ref", args.base_ref), ("head_ref", args.head_ref)):
        r = None if (not ref or ref.startswith("-")) else _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if r is None or r.returncode != 0 or not r.stdout.strip():
            return _fail(f"无效提交引用 ({label}): {ref}")
        shas.append(r.stdout.strip())
    base, head = shas
    if base == head:
        return _fail(f"空提交区间: base 与 head 指向同一提交 ({base[:7]})")
    log_r, stat_r, name_r = (_git(repo, *c) for c in (("log", "--oneline", f"{base}..{head}"), ("diff", "--stat", f"{base}...{head}"), ("diff", "--name-only", "-z", f"{base}...{head}")))
    if any(r.returncode != 0 for r in (log_r, stat_r, name_r)):
        return _fail("采集 git 差异信息失败")
    if not log_r.stdout.strip() and _git(repo, "log", "--oneline", f"{head}..{base}").stdout.strip():
        return _fail(f"提交区间疑似倒置: {base[:7]}..{head[:7]} 无提交，反向存在提交")
    files = "\n".join(f"- `{f}`" for f in name_r.stdout.split("\0") if f) or "(无变更文件)"
    body = f"# 审查交接包 ({base[:7]}..{head[:7]})\n- **基线提交 (base)**: `{base[:7]}` (`{base}`)\n- **目标提交 (head)**: `{head[:7]}` (`{head}`)\n- **推荐三点式 Diff 命令**: `git diff {base}...{head}`\n\n## 提交清单\n```text\n{log_r.stdout.strip() or '(无提交)'}\n```\n\n## 变更统计\n```text\n{stat_r.stdout.strip() or '(无差异)'}\n```\n\n## 变更文件清单\n{files}"
    return _emit(body, args.out)

def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    ap = argparse.ArgumentParser(prog="pack-handoff.py", description="goal-loop 文件指针交接打包工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, specs in (("brief", (("plan_file", {}), ("--task", {"required": True}), ("--out", {}))), ("review-pkg", (("base_ref", {}), ("head_ref", {"nargs": "?", "default": "HEAD"}), ("--repo", {"default": "."}), ("--out", {})))):
        p = sub.add_parser(name)
        for flag, kw in specs:
            p.add_argument(flag, **kw)
    args = ap.parse_args(argv)
    try:
        return cmd_brief(args) if args.cmd == "brief" else cmd_review_pkg(args)
    except (OSError, UnicodeDecodeError) as exc:
        return _fail(str(exc))

if __name__ == "__main__":
    raise SystemExit(main())
