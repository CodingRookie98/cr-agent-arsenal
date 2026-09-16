#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import sys

# 获取脚本所在目录，用于构建绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTIONS_DIR = os.path.join(SCRIPT_DIR, "collections")
SKILLS_JSON_PATH = os.path.join(COLLECTIONS_DIR, "common.json")

def resolve_config_path(file_path):
    """解析配置文件路径，支持直接路径、collections 相对路径或无后缀简称。"""
    candidates = [
        file_path,
        os.path.join(SCRIPT_DIR, file_path),
        os.path.join(COLLECTIONS_DIR, file_path),
        os.path.join(COLLECTIONS_DIR, f"{file_path}.json"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return c
    return None

def load_skills_config(file_path):
    """加载指定的技能 JSON 配置。"""
    resolved_path = resolve_config_path(file_path)
    if not resolved_path:
        print(f"Error: 找不到配置文件 {file_path}。可选预设 (collections/):")
        if os.path.exists(COLLECTIONS_DIR):
            for f in sorted(os.listdir(COLLECTIONS_DIR)):
                if f.endswith(".json"):
                    print(f"  - {f[:-5]}")
        sys.exit(1)

    with open(resolved_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing {resolved_path}: {e}")
            sys.exit(1)

def run_command(cmd, dry_run=False):
    """执行命令并打印输出。"""
    print(f"Executing: {cmd}")
    if dry_run:
        print("  (Dry-run mode, skipping actual execution)")
        return True

    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True, encoding='utf-8', errors='replace')
        print("  Success")
        if result.stdout and result.stdout.strip():
            print(f"  Output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Failed with exit code: {e.returncode}")
        if e.stderr and e.stderr.strip():
            print(f"  Error Output:\n{e.stderr}")
        return False

def list_config(config):
    """列出当前的 skills。"""
    print("--- Configured Skills ---")
    for group in config.get('skills', []):
        source = group.get('source')
        mode = group.get('mode', 'names')
        if mode == 'all':
            print(f"  - * (All skills) (Source: {source})")
            if group.get('names'):
                names_str = ', '.join(group.get('names'))
                print(f"    Specified names: {names_str}")
        else:
            for name in group.get('names', []):
                print(f"  - {name} (Source: {source})")

def do_action(action, config, args):
    """执行安装或卸载动作。"""
    skills_config = config.get('skills', [])

    # 准备 agents 列表
    target_agents = [args.agent]
    if not target_agents or not target_agents[0]:
        print("No agents to process.")
        return

    agents_str = ' '.join(target_agents)
    success_count = 0
    fail_count = 0

    if action == 'uninstall':
        # 准备要卸载的 skills
        target_skills = []
        if args.skill:
            found = False
            for group in skills_config:
                if args.skill in group.get('names', []):
                    found = True
                    break
            if not found:
                print(f"Warning: Skill '{args.skill}' not found in skills.json. Continuing anyway.")
            target_skills.append(args.skill)
        else:
            # 卸载配置中列出的所有 skill names
            for group in skills_config:
                for name in group.get('names', []):
                    target_skills.append(name)
        
        if not target_skills:
            print("No skills to uninstall.")
            return

        # 全局二次确认 (仅当非 yes 且非干跑模式时)
        if not args.yes and not args.dry_run:
            print(f"You are about to execute uninstall for {len(target_skills)} skills across {len(target_agents)} agents.")
            confirm = input("Are you sure you want to continue? [y/N]: ")
            if confirm.lower() not in ['y', 'yes']:
                print("Operation cancelled.")
                sys.exit(0)

        skills_str = ' '.join(target_skills)
        cmd = f"npx skills@latest remove -y --skill {skills_str} --agent {agents_str}"
        if getattr(args, 'remaining_args', []):
            cmd += " " + " ".join(args.remaining_args)
        if run_command(cmd, dry_run=args.dry_run):
            success_count += 1
        else:
            fail_count += 1

    elif action == 'install':
        if args.skill:
            # 安装特定 skill
            source = None
            for group in skills_config:
                if args.skill in group.get('names', []):
                    source = group.get('source')
                    break
            if not source:
                print(f"Warning: Skill '{args.skill}' not found in skills.json. Continuing anyway.")
                source = "unknown_source"

            # 全局二次确认 (仅当非 yes 且非干跑模式时)
            if not args.yes and not args.dry_run:
                print(f"You are about to execute install for skill '{args.skill}' across {len(target_agents)} agents.")
                confirm = input("Are you sure you want to continue? [y/N]: ")
                if confirm.lower() not in ['y', 'yes']:
                    print("Operation cancelled.")
                    sys.exit(0)

            cmd = f"npx skills@latest add -y {source} --skill {args.skill} --agent {agents_str} --full-depth"
            if getattr(args, 'remaining_args', []):
                cmd += " " + " ".join(args.remaining_args)
            if run_command(cmd, dry_run=args.dry_run):
                success_count += 1
            else:
                fail_count += 1
        else:
            # 按 mode 安装配置中的 skills
            # 按 source 合并/分组配置
            source_configs = {}  # source -> {"mode": "all"/"names", "names": set()}
            for group in skills_config:
                source = group.get('source')
                mode = group.get('mode', 'names')
                names = group.get('names', [])
                
                if source not in source_configs:
                    source_configs[source] = {"mode": mode, "names": set(names)}
                else:
                    if mode == 'all':
                        source_configs[source]["mode"] = 'all'
                    source_configs[source]["names"].update(names)

            if not source_configs:
                print("No skills to install.")
                return

            all_mode_sources = [s for s, c in source_configs.items() if c["mode"] == 'all']
            names_mode_skills_count = sum(len(c["names"]) for s, c in source_configs.items() if c["mode"] == 'names')

            # 全局二次确认 (仅当非 yes 且非干跑模式时)
            if not args.yes and not args.dry_run:
                print(f"You are about to execute install for {len(all_mode_sources)} full sources and {names_mode_skills_count} individual skills across {len(target_agents)} agents.")
                confirm = input("Are you sure you want to continue? [y/N]: ")
                if confirm.lower() not in ['y', 'yes']:
                    print("Operation cancelled.")
                    sys.exit(0)

            for source, s_config in source_configs.items():
                if s_config["mode"] == 'all':
                    cmd = f"npx skills@latest add -y {source} --agent {agents_str} --full-depth"
                else:
                    skill_names = sorted(list(s_config["names"]))
                    if not skill_names:
                        continue
                    skills_str = ' '.join(skill_names)
                    cmd = f"npx skills@latest add -y {source} --skill {skills_str} --agent {agents_str} --full-depth"
                
                if getattr(args, 'remaining_args', []):
                    cmd += " " + " ".join(args.remaining_args)
                if run_command(cmd, dry_run=args.dry_run):
                    success_count += 1
                else:
                    fail_count += 1

    print(f"\nOperation '{action}' completed.")
    print(f"  Success (Commands): {success_count}")
    print(f"  Failed (Commands):  {fail_count}")

def main():
    parser = argparse.ArgumentParser(description="Manage opencode skills based on skills.json")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform", required=True)

    # list command
    list_parser = subparsers.add_parser('list', help="List configured skills and agents")
    list_parser.add_argument('-f', '--file', default=SKILLS_JSON_PATH, help=f'Custom skills JSON file. Defaults to {SKILLS_JSON_PATH}')

    # install command
    install_parser = subparsers.add_parser('install', help="Install skills for agents")

    # uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help="Uninstall skills from agents")

    # 动态添加通用参数到 install 和 uninstall 子解析器
    def add_parser_args(p):
        p.add_argument('-s', '--skill', help='Specific skill to process. If omitted, applies to ALL skills.')
        p.add_argument('-a', '--agent', required=True, help='Specific agent to apply to.')
        p.add_argument('-f', '--file', default=SKILLS_JSON_PATH, help=f'Custom skills JSON file. Defaults to {SKILLS_JSON_PATH}')
        p.add_argument('--dry-run', action='store_true', help='Print commands without executing them')
        p.add_argument('-y', '--yes', action='store_true', help='Automatic yes to prompts')

    # 添加参数
    add_parser_args(install_parser)
    add_parser_args(uninstall_parser)

    args, remaining_args = parser.parse_known_args()
    args.remaining_args = remaining_args
    config = load_skills_config(args.file)

    if args.action == 'list':
        list_config(config)
    elif args.action in ['install', 'uninstall']:
        do_action(args.action, config, args)

if __name__ == "__main__":
    main()
