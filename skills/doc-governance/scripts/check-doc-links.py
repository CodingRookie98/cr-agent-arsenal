#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-doc-links.py - 零依赖 Markdown 物理链接与锚点断链静态扫描器

校验相对路径、目录入口 (index.md/README.md)、.md 后缀、#anchor 标题锚点与可选 llms.txt，
忽略行内代码与围栏代码块（3+ 反引号/波浪线精确配对闭合），支持 --exclude 根内豁免。
"""

import argparse
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

LINK_PATTERN = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
INLINE_CODE_PATTERN = re.compile(r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)")
FENCE_LINE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
EXTERNAL_SCHEME_PATTERN = re.compile(
    r"^(https?://|mailto:|ftp:|javascript:|conversation://)", re.I
)
IGNORED_DIR_PARTS = ("node_modules", ".git", ".next", "dist", "build")


def _iter_unfenced_lines(lines: List[str]) -> Iterator[Tuple[int, str]]:
    """逐行产出围栏代码块之外的 (1-based 行号, 原行文本)，按字符与长度精确闭合。"""
    fence_char = ""
    fence_len = 0
    for line_no, line in enumerate(lines, start=1):
        match = FENCE_LINE_PATTERN.match(line)
        if match:
            token, rest = match.group(1), match.group(2)
            if not fence_char:
                if token[0] == "~" or "`" not in rest:
                    fence_char, fence_len = token[0], len(token)
                    continue
            elif token[0] == fence_char and len(token) >= fence_len and not rest.strip():
                fence_char, fence_len = "", 0
                continue
        if not fence_char:
            yield line_no, line


def slugify_heading(heading: str) -> str:
    """将 Markdown 标题转换为 GitHub 规范的锚点 Slug。"""
    text = re.sub(r"^#+\s*", "", heading).strip()
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`~]", "", text).lower()
    text = re.sub(r"[^\w\s\-_\u4e00-\u9fff]", "", text)
    return re.sub(r"[\s]+", "-", text)


def extract_headings(file_path: Path) -> Set[str]:
    """提取文件围栏代码块外的所有标题 Slug（支持重复标题 -1, -2）。"""
    slugs: Set[str] = set()
    slug_counts: Dict[str, int] = {}
    if not file_path.is_file():
        return slugs
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return slugs

    for _, line in _iter_unfenced_lines(content.splitlines()):
        trimmed = line.strip()
        if not (trimmed.startswith("#") and re.match(r"^#{1,6}\s+", trimmed)):
            continue
        raw_slug = slugify_heading(trimmed)
        if not raw_slug:
            continue
        if raw_slug in slug_counts:
            count = slug_counts[raw_slug]
            slug_counts[raw_slug] += 1
            slugs.add(f"{raw_slug}-{count}")
        else:
            slug_counts[raw_slug] = 1
        slugs.add(raw_slug)
    return slugs


def _check_anchor(
    target_file: Path, anchor: str, headings_cache: Dict[Path, Set[str]], same_file: bool
) -> Optional[str]:
    """校验目标文件中的标题锚点是否存在，缺失时返回错误描述。"""
    cache_key = target_file.resolve()
    if cache_key not in headings_cache:
        headings_cache[cache_key] = extract_headings(target_file)
    if anchor not in headings_cache[cache_key]:
        prefix = "当前文件内未找到锚点" if same_file else "目标文件存在但未找到对应锚点"
        return f"{prefix} '#{anchor}'"
    return None


def _validate_link_target(
    file_path: Path,
    root_dir: Path,
    raw_target: str,
    headings_cache: Dict[Path, Set[str]],
    strict_md_extension: bool,
) -> Optional[str]:
    """解析并校验单条相对链接目标及锚点，合法返回 None，失败返回错误原因。"""
    if raw_target.startswith("#"):
        anchor = raw_target[1:].strip().lower()
        return _check_anchor(file_path, anchor, headings_cache, same_file=True) if anchor else None

    path_part, anchor_part = raw_target.split("#", 1) if "#" in raw_target else (raw_target, "")
    anchor = anchor_part.strip().lower()
    decoded_path = urllib.parse.unquote(path_part)
    if decoded_path.startswith("/"):
        target_file = (root_dir / decoded_path.lstrip("/")).resolve()
    else:
        target_file = (file_path.parent / decoded_path).resolve()

    if not target_file.exists():
        return f"目标路径不存在 (404 Not Found): {target_file}"
    if target_file.is_dir():
        has_index = (target_file / "index.md").exists() or (target_file / "README.md").exists()
        return None if has_index else f"链接指向目录但缺失 index.md/README.md: {target_file}"
    if strict_md_extension and target_file.is_file():
        if target_file.suffix == ".md" and not path_part.lower().endswith(".md"):
            return "违背显式文件链接规范：指向 Markdown 文件的超链接缺失 '.md' 后缀"
    if anchor and target_file.suffix == ".md":
        return _check_anchor(target_file, anchor, headings_cache, same_file=False)
    return None


def check_file_links(
    file_path: Path,
    root_dir: Path,
    headings_cache: Dict[Path, Set[str]],
    strict_md_extension: bool = True,
) -> List[Tuple[int, str, str, str]]:
    """检查单个文件中的所有链接，返回 [(line_no, link_text, raw_target, error_reason)]。"""
    errors: List[Tuple[int, str, str, str]] = []
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return [(0, "", "", f"无法读取文件: {exc}")]

    for line_idx, line in _iter_unfenced_lines(lines):
        sanitized_line = INLINE_CODE_PATTERN.sub("", line)
        for match in LINK_PATTERN.finditer(sanitized_line):
            link_text = match.group(1).strip()
            raw_target = match.group(2).strip()
            if " " in raw_target and not raw_target.startswith("http"):
                raw_target = raw_target.split(None, 1)[0]
            if EXTERNAL_SCHEME_PATTERN.match(raw_target):
                continue
            reason = _validate_link_target(
                file_path, root_dir, raw_target, headings_cache, strict_md_extension
            )
            if reason:
                errors.append((line_idx, link_text, raw_target, reason))
    return errors


def _is_root_scan(root_dir: Path, search_roots: List[Path]) -> bool:
    """判定本次扫描的搜索根是否覆盖文档根本身（--dir 收窄到子目录时为 False）。"""
    root = root_dir.resolve()
    return any(s_root.exists() and s_root.resolve() == root for s_root in search_roots)


def _validate_target_dirs(root_path: Path, target_dirs: Optional[List[str]]) -> List[str]:
    """校验 --dir 作用域落在 --root 之内且真实存在，防止越界或静默空扫。"""
    problems: List[str] = []
    root_resolved = root_path.resolve()
    for raw in target_dirs or []:
        candidate = (root_path / raw).resolve()
        try:
            rel = candidate.relative_to(root_resolved)
        except ValueError:
            problems.append(f"--dir 越出根目录: {raw} → {candidate}")
            continue
        if not candidate.exists():
            problems.append(f"--dir 指向不存在的路径: {raw} → {rel.as_posix()}")
    return problems


def _is_unsafe_raw_prefix(raw: str) -> bool:
    """判断 --exclude 原始前缀是否为空串或绝对路径写法。"""
    if not raw or not raw.strip():
        return True
    if raw.startswith(("/", "\\")) or Path(raw).is_absolute():
        return True
    return bool(re.match(r"^[A-Za-z]:", raw))


def _validate_exclude_prefixes(
    root_path: Path, exclude_prefixes: Optional[List[str]]
) -> Tuple[List[Path], List[str]]:
    """校验 --exclude 为根内相对前缀（允许目标尚不存在），返回 (已解析路径列表, 错误列表)。"""
    resolved_excludes: List[Path] = []
    problems: List[str] = []
    root_resolved = root_path.resolve()
    for raw in exclude_prefixes or []:
        if _is_unsafe_raw_prefix(raw):
            problems.append(f"--exclude 必须为非空根内相对路径（禁止绝对路径）: {raw!r}")
            continue
        candidate = (root_resolved / raw).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            problems.append(f"--exclude 越出根目录: {raw} → {candidate}")
            continue
        resolved_excludes.append(candidate)
    return resolved_excludes, problems


def _is_excluded(file_path: Path, excluded_paths: List[Path]) -> bool:
    """判定文件是否落在任一 --exclude 路径自身或其子树下。"""
    if not excluded_paths:
        return False
    file_resolved = file_path.resolve()
    return any(
        file_resolved == exc_resolved or exc_resolved in file_resolved.parents
        for exc_resolved in excluded_paths
    )


def _collect_markdown_files(root_dir: Path, target_dirs: Optional[List[str]]) -> List[Path]:
    """收集待扫描的 Markdown 文件及可选的根级 llms.txt。"""
    search_roots = [root_dir / d for d in target_dirs] if target_dirs else [root_dir]
    md_files: List[Path] = []
    for s_root in search_roots:
        if not s_root.exists():
            continue
        if s_root.is_file() and s_root.suffix == ".md":
            md_files.append(s_root)
        elif s_root.is_dir():
            md_files.extend(s_root.rglob("*.md"))

    if _is_root_scan(root_dir, search_roots):
        llms_map = root_dir / "llms.txt"
        if llms_map.is_file():
            md_files.append(llms_map)
    return sorted(set(md_files))


def _safe_rel_path(file_path: Path, root_path: Path) -> Path:
    """尽力返回相对路径，无法相对化时退回原路径。"""
    try:
        return file_path.relative_to(root_path)
    except ValueError:
        return file_path


def scan_directory(
    root_dir: Path,
    target_dirs: Optional[List[str]] = None,
    strict_md: bool = True,
    verbose: bool = False,
    exclude_prefixes: Optional[List[str]] = None,
) -> Tuple[int, int, Dict[Path, List[Tuple[int, str, str, str]]]]:
    """扫描指定目录下的 Markdown 链接，跳过构建目录与 --exclude 前缀。"""
    excluded_paths, exc_problems = _validate_exclude_prefixes(root_dir, exclude_prefixes)
    if exc_problems:
        raise ValueError("; ".join(exc_problems))

    root_resolved = root_dir.resolve()
    headings_cache: Dict[Path, Set[str]] = {}
    total_files = 0
    total_errors = 0
    file_errors: Dict[Path, List[Tuple[int, str, str, str]]] = {}

    for md_file in _collect_markdown_files(root_dir, target_dirs):
        rel_parts = _safe_rel_path(md_file.resolve(), root_resolved).parts
        if any(part in rel_parts for part in IGNORED_DIR_PARTS):
            continue
        if _is_excluded(md_file, excluded_paths):
            continue

        total_files += 1
        errs = check_file_links(md_file, root_dir, headings_cache, strict_md_extension=strict_md)
        if errs:
            file_errors[md_file] = errs
            total_errors += len(errs)
        elif verbose:
            print(f"  [PASS] {_safe_rel_path(md_file, root_dir)}")

    return total_files, total_errors, file_errors


def _print_error_report(
    root_path: Path, total_errors: int, file_errors: Dict[Path, List[Tuple[int, str, str, str]]]
) -> None:
    """格式化输出断链错误汇总。"""
    print(f"❌ 警告: 发现 {total_errors} 处无效链接或断链违规：\n")
    for f_path, errs in file_errors.items():
        print(f"📄 【{_safe_rel_path(f_path, root_path)}】:")
        for line_no, text, target, reason in errs:
            print(f"   第 {line_no} 行 | 链接文本: '{text}' ➔ 目标: '{target}'")
            print(f"   ↳ 错误原因: {reason}")
        print()
    print(f"🚫 审计未通过 (Exit Code 1): 请就地修复上述 {total_errors} 处断链后重新运行。")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="全域 Markdown 物理链接与锚点断链静态扫描器")
    parser.add_argument("--root", default="docs", help="扫描根目录 (默认为 docs)")
    parser.add_argument("--dir", action="append", help="指定扫描子目录或文件 (可多次指定)")
    parser.add_argument(
        "--exclude", action="append", default=None,
        help="排除的根内相对路径前缀或文件 (可多次指定，如 --exclude project/reviews)",
    )
    parser.add_argument(
        "--no-strict-ext", action="store_true", help="允许链接指向 Markdown 时省略 .md 后缀 (不推荐)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="输出通过的正常文件")
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = _parse_args()
    root_path = Path(args.root).resolve()

    if not root_path.exists():
        print(f"❌ 错误: 目标根目录不存在: {root_path}", file=sys.stderr)
        sys.exit(1)

    _, exc_problems = _validate_exclude_prefixes(root_path, args.exclude)
    problems = _validate_target_dirs(root_path, args.dir) + exc_problems
    if problems:
        for problem in problems:
            print(f"❌ 错误: {problem}", file=sys.stderr)
        sys.exit(2)

    print(f"🔍 启动物理链接与锚点静态审计: 根目录={root_path} ...")
    total_files, total_errors, file_errors = scan_directory(
        root_dir=root_path, target_dirs=args.dir,
        strict_md=not args.no_strict_ext, verbose=args.verbose, exclude_prefixes=args.exclude,
    )
    print(f"\n📊 审计汇总: 共扫描 {total_files} 个 Markdown 文件")
    if total_errors == 0:
        print("✅ 恭喜！未发现任何 404 断链或非法相对引用，所有链接 100% 物理有效！")
        sys.exit(0)
    _print_error_report(root_path, total_errors, file_errors)
    sys.exit(1)


if __name__ == "__main__":
    main()
