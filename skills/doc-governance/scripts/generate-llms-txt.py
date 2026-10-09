#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate-llms-txt.py - 机器可读 llms.txt 自动化生成器
功能:
  1. 扫描 docs/ 目录下的所有 Markdown 文档；
  2. 提取每篇文档的标题、Diátaxis 象限分类与精炼摘要；
  3. 按照 llmstxt.org 标准规范生成紧凑、结构化的 docs/llms.txt；
  4. 赋予 AI 智能体在毫秒级掌握全域知识拓扑与权威入口的能力。
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")


def in_evidence_archive(path: Path, root_dir: Path) -> bool:
    """判定路径是否落在交付凭据归档根内（<root>/project/reviews/**）。"""
    try:
        rel = path.relative_to(root_dir)
    except ValueError:
        return False
    return rel.parts[:2] == EVIDENCE_ARCHIVE_PARTS

def is_archive_path(path: Path) -> bool:
    """不依赖 root 锚定的写入侧安全闸：任一祖先含相邻 project/reviews 段即判定为交付凭据归档。

    in_evidence_archive 以 --root 锚定，当 --root 收窄至归档子树内时会失效（R1-2）；
    本函数保证在任何 --root 取值下都正确识别归档（G1 逐字归档红线不可写/不可收录）。
    """
    parts = path.parts
    return any(parts[i:i + 2] == EVIDENCE_ARCHIVE_PARTS for i in range(len(parts) - 1))


def extract_doc_info(file_path: Path) -> Tuple[str, str]:
    """提取文档的标题与摘要描述"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return file_path.stem, ""

    lines = content.splitlines()
    title = file_path.stem
    description = ""

    # 1. 查找第一个 Markdown 一级标题
    for line in lines:
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            title = m.group(1).strip()
            # 移除标题中的 Markdown 格式
            title = re.sub(r"[*_`]", "", title)
            break

    # 2. 查找元数据描述或首段非标题文本
    # 模式 A: 检查 Frontmatter 中的 description / 描述 / 修订描述
    desc_match = re.search(r"(?:description|描述|修订描述|简述)\s*:\s*([^\n]+)", content, re.I)
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        # 模式 B: 查找第一个有意义的正文段落
        in_code = False
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith("```"):
                in_code = not in_code
                continue
            if in_code or not trimmed:
                continue
            if trimmed.startswith("#") or trimmed.startswith(">") or trimmed.startswith("|") or trimmed.startswith("-"):
                continue
            # 找到了普通正文行
            description = trimmed[:120] + "..." if len(trimmed) > 120 else trimmed
            break

    return title, description


SECTION_ORDER = [
    ("proposals", "Proposals & RFCs (需求与设计孵化层)"),
    ("tutorials", "Tutorials (学习导向 / 新手上手教程)"),
    ("how-to", "How-To Guides (操作指南 / 问题与任务 SOP)"),
    ("reference", "Reference (技术参考 / 机器事实唯一真相源)"),
    ("explanation", "Explanation (深度剖析 / 系统架构与 ADR 决策)"),
    ("project", "Project Governance (工程演进 / 发布日志与待办)"),
]


def generate_llms_txt(root_dir: Path, output_file: Path, project_name: str = "Project") -> int:
    """生成 llms.txt。返回收录文档数；收录 0 篇时**不落盘**并返回 0（BK-0023 零覆盖守卫）。"""
    sections: Dict[str, List[Tuple[str, str, str]]] = {k: [] for k, _ in SECTION_ORDER}
    other_docs: List[Tuple[str, str, str]] = []

    all_files = sorted(list(root_dir.rglob("*.md")))

    for f in all_files:
        if any(p in f.parts for p in ("node_modules", ".git", ".next", "dist", "build")):
            continue
        if in_evidence_archive(f, root_dir) or is_archive_path(f):
            continue
        rel_parts = f.relative_to(root_dir).parts
        if len(rel_parts) == 1:
            # 根文件（如 index.md, GOVERNANCE.md）
            continue

        top_dir = rel_parts[0]
        title, desc = extract_doc_info(f)
        rel_link = f.relative_to(root_dir).as_posix()

        if top_dir in sections:
            sections[top_dir].append((title, rel_link, desc))
        else:
            other_docs.append((title, rel_link, desc))

    output_lines = [
        f"# {project_name} Machine-Readable Knowledge Base Map",
        "",
        f"> 本文件遵循 llmstxt.org 规范，为 AI 智能体提供全景知识拓扑与物理文件导航地图。",
        f"> 严禁凭空猜测路径，查阅具体模块前请通过下述相对链接精准索引对应文件。",
        "",
    ]

    for sec_key, sec_title in SECTION_ORDER:
        docs = sections.get(sec_key, [])
        if not docs:
            continue
        output_lines.append(f"## {sec_title}")
        output_lines.append("")
        for title, link, desc in docs:
            desc_text = f": {desc}" if desc else ""
            output_lines.append(f"- [{title}]({link}){desc_text}")
        output_lines.append("")

    if other_docs:
        output_lines.append("## Other Documentation (其他文档)")
        output_lines.append("")
        for title, link, desc in other_docs:
            desc_text = f": {desc}" if desc else ""
            output_lines.append(f"- [{title}]({link}){desc_text}")
        output_lines.append("")

    total_docs = sum(len(v) for v in sections.values()) + len(other_docs)
    if total_docs == 0:
        # 零覆盖守卫：绝不用空壳地图覆盖既有 SSOT 地图（BK-0023 / R1-17）
        return 0

    content = "\n".join(output_lines)
    output_file.parent.mkdir(parents=True, exist_ok=True)  # R1-7：仅在确认落盘时才创建父目录
    output_file.write_text(content, encoding="utf-8")
    print(f"✅ 机器可读地图成功生成至: {output_file} (共收录 {total_docs} 篇有效文档)")
    return total_docs


def main():
    parser = argparse.ArgumentParser(description="机器可读 llms.txt 自动化生成器")
    parser.add_argument("--root", default="docs", help="文档根目录 (默认 docs)")
    parser.add_argument("--output", default=None, help="输出路径 (缺省为 <root>/llms.txt，随 --root 派生)")
    parser.add_argument("--name", default="System", help="项目名称")

    args = parser.parse_args()
    root_path = Path(args.root).resolve()
    # BK-0023：显式与缺省落点统一 resolve()，使符号链接穿透同样落入归档判定
    out_path = Path(args.output).resolve() if args.output else (root_path / "llms.txt").resolve()

    if is_archive_path(out_path) or in_evidence_archive(out_path, root_path):
        print(f"❌ 拒绝写入交付凭据归档（G1 逐字归档红线）: {out_path}", file=sys.stderr)
        sys.exit(1)

    if not root_path.exists():
        print(f"❌ 错误: 目标根目录不存在: {root_path}", file=sys.stderr)
        sys.exit(1)

    written = generate_llms_txt(root_path, out_path, project_name=args.name)
    if written == 0:
        print(f"❌ 机器地图收录 0 篇文档，拒绝落盘（零覆盖守卫，避免覆盖既有 SSOT 地图）: {out_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
