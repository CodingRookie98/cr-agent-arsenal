#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = CURRENT_DIR.parent


def setup_symlinks():
    # AGENTS.md 的绝对路径
    source_file = CURRENT_DIR / "AGENTS.md"

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

def link_local_skills():
    """把仓库自有技能目录以相对软连接暴露到 .agents/skills/。

    单一真相源：源目录始终是 skills/<name>，.agents/ 仅作宿主发现的入口视图。
    使用相对软连（../../skills/<name>）保证仓库整体移动后链接依然有效。
    外部仓库不使用本函数，改为通过 npx 从 GitHub master 安装。
    """
    skills_dir = REPO_ROOT / "skills"
    agents_dir = REPO_ROOT / ".agents" / "skills"
    if not skills_dir.is_dir():
        print(f"警告: 未找到技能源目录 {skills_dir}，跳过技能链接。")
        return
    agents_dir.mkdir(parents=True, exist_ok=True)
    for skill in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").is_file()):
        target = agents_dir / skill.name
        if target.is_symlink():
            if target.resolve() == skill.resolve():
                print(f"跳过: 软连接已正确 {target} -> {os.readlink(target)}")
                continue
            target.unlink()
        elif target.exists():
            print(f"警告: {target} 是实体副本（可能与源目录漂移），已移除并改为软连接。")
            shutil.rmtree(target)
        try:
            os.symlink(os.path.relpath(skill, target.parent), target)
            print(f"成功: 已创建软连接 {target} -> {os.readlink(target)}")
        except Exception as e:
            print(f"错误: 无法为 {skill.name} 创建软连接: {e}")


if __name__ == "__main__":
    setup_symlinks()
    link_local_skills()
