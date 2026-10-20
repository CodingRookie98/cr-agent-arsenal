#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dispatch-agy.py — 辅助分发 agy (Antigravity CLI) 后台执行任务的标准调度脚本

自动清理 WSL/Linux 代理变量、注入 Gemini 3.8 Flash 模型与安全超时参数。

用法（Windows / 跨平台）:
    python skills/agy-delegation-workflow/scripts/dispatch-agy.py [选项] <任务Prompt文件或提示词>
用法（POSIX）:
    python3 skills/agy-delegation-workflow/scripts/dispatch-agy.py [选项] <任务Prompt文件或提示词>

原实现为同目录 dispatch-agy.sh（Bash）。本文件是其逐字节等价的跨平台 Python 实现：
选项、退出码与 stdout/stderr 文案保持一致。POSIX 下旧 .sh 调用仍可用（兼容壳转发到本文件）。

自指名称机制沿用原实现：帮助信息中的脚本名由 `basename $0` 派生，故此处取
`os.path.basename(sys.argv[0])`，而不是硬编码字面量。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import NoReturn

DEFAULT_MODEL = "Gemini 3.8 Flash (High)"
DEFAULT_TIMEOUT = "20m"
PROXY_VARS = (
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
)


def _program_name() -> str:
    """返回脚本自指名称（对齐 Bash 的 `basename "$0"`）。"""
    return os.path.basename(sys.argv[0])


def usage(exit_code: int = 1, timeout: str = DEFAULT_TIMEOUT) -> NoReturn:
    """打印帮助信息并退出。默认退出码 1，`-h/--help` 传 0。

    注意 `timeout` 取「当前」超时值（Bash 版 heredoc 内的 ${TIMEOUT} 在调用时展开，
    因此 `-t 5m -h` 的帮助文本显示 5m），而模型默认值始终是 DEFAULT_MODEL 常量。
    """
    program = _program_name()
    sys.stdout.write(
        f"""用法: {program} [选项] <任务Prompt文件或提示词>

选项:
  -f, --file <path>     指定任务提示词文件 (.agy-tasks/task.md)
  -p, --prompt <text>   直接指定单行任务描述文本
  -m, --model <name>    指定执行模型 (默认: {DEFAULT_MODEL})
  -t, --timeout <time>  指定无头超时时间 (默认: {timeout})
  -b, --background      后台执行并在完成后输出日志提示
  -h, --help            显示本帮助信息

示例:
  {program} -f .agy-tasks/task-a.md -b
  {program} -p "为 src/utils/math.ts 补充 100% 单元测试"
"""
    )
    sys.exit(exit_code)


def _require_value(argv: list[str], index: int, line: int) -> str:
    """取选项值；缺值时报错退出。

    原 Bash 在 `set -u` 下读取未绑定的 `$2` 会立即中止（rc=1，stderr 为
    `<脚本>: line N: $2: unbound variable`）。为保持差分逐字节一致，此处复刻
    同一文案与退出码，`line` 沿用原脚本中触发该分支的行号。
    """
    if index >= len(argv):
        sys.stderr.write(f"{sys.argv[0]}: line {line}: $2: unbound variable\n")
        sys.exit(1)
    return argv[index]


def _parse_args(argv: list[str]) -> tuple[str, str, str, str, bool]:
    """按原 Bash `while [[ $# -gt 0 ]]` + `case` 的语义解析命令行参数。"""
    task_file = ""
    prompt_text = ""
    model = os.environ.get("AGY_MODEL") or DEFAULT_MODEL
    timeout = DEFAULT_TIMEOUT
    background = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("-f", "--file"):
            task_file = _require_value(argv, index + 1, 42)
            index += 2
        elif arg in ("-p", "--prompt"):
            prompt_text = _require_value(argv, index + 1, 46)
            index += 2
        elif arg in ("-m", "--model"):
            model = _require_value(argv, index + 1, 50)
            index += 2
        elif arg in ("-t", "--timeout"):
            timeout = _require_value(argv, index + 1, 54)
            index += 2
        elif arg in ("-b", "--background"):
            background = True
            index += 1
        elif arg in ("-h", "--help"):
            usage(0, timeout)
        else:
            # 原实现：TASK_FILE 为空且位置参数是真实文件 → 当作任务文件；
            # 否则 PROMPT_TEXT 为空 → 当作提示词；都不满足 → 报未知参数。
            if not task_file and os.path.isfile(arg):
                task_file = arg
            elif not prompt_text:
                prompt_text = arg
            else:
                sys.stderr.write(f"❌ 错误: 未知参数 {arg}\n")
                usage(1, timeout)
            index += 1
    return task_file, prompt_text, model, timeout, background


def _git_repo_root(*args: str) -> str:
    """调用 git 取仓库根；失败（含 git 不存在）时返回空串（对齐 `|| true`）。"""
    try:
        completed = subprocess.run(
            ["git", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.decode("utf-8", "surrogateescape").rstrip("\n")


def _load_content(task_file: str, prompt_text: str, timeout: str) -> str:
    """确定任务内容：文件内容（剥离尾部换行，对齐 `$(cat ...)`）或命令行提示词。"""
    if task_file:
        if not os.path.isfile(task_file):
            sys.stderr.write(f"❌ 错误: 任务提示词文件不存在: {task_file}\n")
            sys.exit(1)
        with open(task_file, "rb") as handle:
            raw = handle.read()
        return raw.decode("utf-8", "surrogateescape").rstrip("\n")
    if prompt_text:
        return prompt_text
    sys.stderr.write("❌ 错误: 必须通过 -f <文件> 或 -p <文本> 指定任务内容。\n")
    usage(1, timeout)
    raise AssertionError("usage() 不可返回")  # pragma: no cover


def _prepare_workspace(task_file: str) -> list[str]:
    """解析 git 仓库根、切换工作目录并返回 `--add-dir` 参数（无仓库时为空）。"""
    if task_file:
        base_dir = os.path.dirname(task_file) or "."
        repo_root = _git_repo_root("-C", base_dir, "rev-parse", "--show-toplevel")
    else:
        repo_root = _git_repo_root("rev-parse", "--show-toplevel")
    if not repo_root:
        return []
    os.chdir(repo_root)
    os.environ["HINDSIGHT_MCP_PROJECT_CWD"] = repo_root
    return ["--add-dir", repo_root]


def _clear_proxy_env() -> None:
    """清除代理环境变量，杜绝 WSL/Linux 下 Go 客户端 proxyconnect connection refused。"""
    for name in PROXY_VARS:
        os.environ.pop(name, None)


def _print_banner(model: str, timeout: str) -> None:
    """打印与原 Bash 逐字一致的执行横幅。"""
    separator = "=" * 70
    print(separator)
    print("🚀 启动 agy 后台执行任务")
    print(separator)
    print(f"📌 执行模型: {model}")
    print(f"⏱️  超时时限: {timeout}")
    print(f"📂 工作目录: {os.getcwd()}")
    print("-" * 70)


def _dispatch_background(executable: str, agy_args: list[str]) -> int:
    """后台执行：日志落到 .agy-tasks/logs/，打印 PID 与 tail 提示后返回 0。"""
    log_dir = ".agy-tasks/logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = f"{log_dir}/agy-{timestamp}-{os.getpid()}.log"
    print(f"📡 后台执行模式已激活，日志输出至: {log_file}")
    sys.stdout.flush()
    with open(log_file, "wb") as log_handle:
        # 对齐 `nohup agy ... > "$LOG_FILE" 2>&1 &`：stdin 接 /dev/null、脱离会话、
        # 不等待子进程（脚本退出后任务继续）。
        process = subprocess.Popen(
            [executable, *agy_args],
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print(f"✅ agy 任务已在后台启动 (PID: {process.pid})")
    print(f"💡 提示: 您可以使用 'tail -f {log_file}' 实时跟踪执行进展。")
    return 0


def _dispatch_foreground(executable: str, agy_args: list[str]) -> int:
    """前台同步执行：POSIX 下用 exec 替换进程（对齐原 Bash 的 `exec agy`）。"""
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == "nt":
        # Windows 无法对 .cmd 做参数保真的 exec，改用 subprocess 并透传退出码。
        return subprocess.run([executable, *agy_args]).returncode
    os.execvp("agy", ["agy", *agy_args])
    raise AssertionError("execvp() 不可返回")  # pragma: no cover


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(sys.argv[1:] if argv is None else argv)

    task_file, prompt_text, model, timeout, background = _parse_args(args)

    # 先校验 agy CLI 是否存在（原实现顺序：参数解析 → agy 校验 → 内容获取）。
    executable = shutil.which("agy")
    if executable is None:
        sys.stderr.write(
            "❌ 错误: 系统中未找到 'agy' (Antigravity CLI) 可执行文件。请确认已安装并加入 PATH。\n"
        )
        return 1

    content = _load_content(task_file, prompt_text, timeout)
    workspace_args = _prepare_workspace(task_file)
    if workspace_args:
        print(f"📂 记忆库归属根目录: {workspace_args[1]}")
    else:
        cwd_name = os.path.basename(os.getcwd())
        sys.stderr.write(
            "⚠️  警告: 未能定位 git 仓库根 —— Hindsight 的 bank 会退化为目录名\n"
        )
        sys.stderr.write(
            f"           (coding-agent::{cwd_name})。请先 cd 到项目仓库根，"
            "或用 -f 指定仓库内的任务文件。\n"
        )

    _clear_proxy_env()
    _print_banner(model, timeout)

    agy_args = [
        *workspace_args,
        "-p",
        content,
        "--model",
        model,
        "--dangerously-skip-permissions",
        "--print-timeout",
        timeout,
    ]
    if background:
        return _dispatch_background(executable, agy_args)
    return _dispatch_foreground(executable, agy_args)


if __name__ == "__main__":
    sys.exit(main())
