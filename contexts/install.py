#!/usr/bin/env python3
import os
from pathlib import Path

def setup_symlinks():
    # 获取当前脚本所在目录及 AGENTS.md 的绝对路径
    current_dir = Path(__file__).parent.resolve()
    source_file = current_dir / "AGENTS.md"

    if not source_file.exists():
        print(f"错误: 找不到源文件 {source_file}")
        return

    # 定义目标路径
    targets = [
        Path("~/.config/opencode/AGENTS.md").expanduser(),
        Path("~/.gemini/GEMINI.md").expanduser(),
        Path("~/.codex/AGENTS.md").expanduser(),
        Path("~/.hermes/SOUL.md").expanduser(),
        Path("~/.dsh/AGENTS.md").expanduser(),
    ]

    for target in targets:
        # 确保目标目录存在
        target.parent.mkdir(parents=True, exist_ok=True)

        # 如果目标已存在，先删除（处理旧链接或文件）
        if target.exists() or target.is_symlink():
            try:
                if target.is_dir() and not target.is_symlink():
                    print(f"警告: {target} 是一个目录，跳过。")
                    continue
                target.unlink()
            except Exception as e:
                print(f"错误: 无法删除现有文件 {target}: {e}")
                continue

        # 创建符号链接
        try:
            target.symlink_to(source_file)
            print(f"成功: 已创建链接 {target} -> {source_file}")
        except Exception as e:
            print(f"错误: 无法为 {target} 创建符号链接: {e}")

if __name__ == "__main__":
    setup_symlinks()
