#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-doc-health.py - 本仓私有精简文档健康门禁

只承载三项高价值机械门禁（零棘轮基线税、零外部依赖、单文件单遍读取）：
  1. 文档三态状态机（RFC-0007）：Active / Contested / Superseded 与取代指针校验
  2. 文档体量门禁（RFC-0008）：单文件字节与最长单行上限（仅按 \\n 断行）
  3. 路由文件护栏（<root>/AGENTS.md）：存在性、行数上限与必需小节

退出码: 0 = 无阻塞错误；1 = 存在阻塞错误；2 = 用法或根目录错误。
"""

import argparse
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

VALID_STATES = {"Active", "Contested", "Superseded"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build"}
EXPLAIN_HEADERS = {"说明", "含义", "描述", "解释", "示例", "备注", "description", "meaning"}

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
_INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)([\s\S]*?)(?<!`)\1(?!`)")
_QUOTE_KV_RE = re.compile(r"^(?:[-*+]\s+)?([^:：\n]+?)\s*[:：]\s*(.*)$")
_MARKER_RE = re.compile(r"^(?:文档控制信息|文档控制头)(?:$|\s|\(|（|:|：|\*)")
_THEMATIC_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})\s*$")
_COMMENT_RE = re.compile(r"<!--.*?-->")
_INLINE_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(\s*(?:<([^>\n]+)>|([^)\s]+))")
_REF_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(?:<([^>\n]+)>|(\S+))")


def _split_lf_lines(text: str) -> List[str]:
    """仅按 \\n 断行（兼容 CRLF，绝不用 splitlines() 防 U+2028/U+2029 绕过）."""
    lines = [ln.rstrip("\r") for ln in text.split("\n")]
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _unfenced_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    fence: Optional[Tuple[str, int]] = None
    for line in lines:
        m = _FENCE_RE.match(line)
        if m:
            token, rest = m.group(1), m.group(2)
            if fence is None:
                if token[0] == "~" or "`" not in rest:
                    fence = (token[0], len(token))
                    continue
            elif token[0] == fence[0] and len(token) >= fence[1] and not rest.strip():
                fence = None
                continue
        if fence is None:
            out.append(line)
    return out


def _canon_key(raw: str) -> Optional[str]:
    key = raw.strip().strip("*_` \t").strip()
    if key in ("文档状态", "取代于"):
        return key
    return "取代于" if key.lower() == "superseded-by" else None


def _clean_val(raw: str) -> str:
    val = _COMMENT_RE.sub("", raw).strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        return val[1:-1].strip()
    return val


def _parse_yaml_frontmatter(lines: List[str]) -> Tuple[Dict[str, str], int]:
    meta: Dict[str, str] = {}
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        return meta, 0
    end_idx = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end_idx is None:
        return meta, 0
    for line in lines[1:end_idx]:
        if line and line[0] not in (" ", "\t", "#", "-") and ":" in line:
            k, v = line.split(":", 1)
            if canon := _canon_key(k):
                meta[canon] = _clean_val(v)
    return meta, end_idx + 1


def _parse_table_row(line: str) -> Optional[List[str]]:
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells = [c.strip() for c in s.strip("|").split("|")]
    if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c):
        return None
    return cells


def _scan_marker_table(block_lines: List[str]) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    is_quote_marker = block_lines[0].lstrip().startswith(">")
    in_table = block_lines[0].lstrip().startswith("|")
    for line in block_lines[1:40]:
        s = line.lstrip()
        if s.startswith((">", "|")):
            if s.startswith("|"):
                in_table = True
            inner = re.sub(r"^(?:\s*>\s*)+", "", line) if s.startswith(">") else line
            cells = _parse_table_row(inner)
            if cells and len(cells) == 2 and (canon := _canon_key(cells[0])):
                meta.setdefault(canon, _clean_val(cells[1]))
            continue
        if not line.strip() and not is_quote_marker and not in_table:
            continue
        break
    return meta


def _scan_fallback_table(head_lines: List[str]) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    in_table = skip_table = False
    for line in head_lines:
        s = line.strip()
        if re.match(r"^#{2,6}\s+", s) or _THEMATIC_RE.match(s):
            break
        cells = _parse_table_row(line)
        if cells is None:
            if not s.startswith("|"):
                in_table = skip_table = False
            continue
        if len(cells) != 2:
            in_table = skip_table = True
            continue
        if not in_table:
            in_table = True
            if cells[1].strip("*_` \t").lower() in EXPLAIN_HEADERS:
                skip_table = True
                continue
        if not skip_table and (canon := _canon_key(cells[0])):
            meta[canon] = _clean_val(cells[1])
    return meta


def _parse_header_meta(lines: List[str]) -> Tuple[Dict[str, str], List[str]]:
    meta, body_start = _parse_yaml_frontmatter(lines)
    body_lines = lines[body_start:]
    if body_start == 0 and body_lines:
        body_lines = [body_lines[0].lstrip("\ufeff"), *body_lines[1:]]
    unfenced = _unfenced_lines(body_lines)
    for line in unfenced[:80]:
        if line.lstrip().startswith(">"):
            inner = re.sub(r"^(?:\s*>\s*)+", "", line).strip()
            if (m := _QUOTE_KV_RE.match(inner)) and (canon := _canon_key(m.group(1))):
                meta.setdefault(canon, _clean_val(m.group(2)))
    marker_idx = next((i for i, ln in enumerate(unfenced[:80]) if _MARKER_RE.match(re.sub(r"^[#>\s*_`]+", "", ln).strip())), None)
    tbl = _scan_marker_table(unfenced[marker_idx:]) if marker_idx is not None else _scan_fallback_table(unfenced[:40])
    for k, v in tbl.items():
        meta.setdefault(k, v)
    return meta, unfenced


def _validate_superseded_target(doc: Path, root: Path, raw_target: str) -> Optional[str]:
    raw_part = raw_target.split("#", 1)[0].split("?", 1)[0].strip() if raw_target else ""
    part = urllib.parse.unquote(raw_part).strip()
    if not part:
        return "Superseded 文档缺少有效「取代于」相对路径"
    if "\x00" in part or "\x00" in raw_part:
        return f"「取代于」包含非法空字节: {raw_target}"
    for candidate in (raw_part, part):
        if candidate.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", candidate) or "://" in candidate:
            return f"「取代于」必须是相对路径: {raw_target}"
    depth = len(doc.parent.relative_to(root).parts)
    for seg in part.replace("\\", "/").split("/"):
        if seg not in ("", "."):
            depth += -1 if seg == ".." else 1
            if depth < 0:
                return f"「取代于」越出文档根目录: {raw_target}"
    resolved = (doc.parent / part).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return f"「取代于」越出文档根目录: {raw_target}"
    if resolved == doc.resolve():
        return f"「取代于」不能指向自身: {raw_target}"
    if not resolved.is_file() or resolved.suffix.lower() != ".md":
        return f"「取代于」目标须为存在的 .md 文件: {raw_target}"
    return None


def _extract_md_links(unfenced: List[str]) -> List[str]:
    links: List[str] = []
    for line in unfenced:
        clean_line = _INLINE_CODE_RE.sub("", line)
        links.extend(m.group(1) or m.group(2) for m in _INLINE_LINK_RE.finditer(clean_line))
        if rm := _REF_DEF_RE.match(clean_line):
            links.append(rm.group(1) or rm.group(2))
    return links


def _check_size(
    rel_posix: str, raw: bytes, lines: List[str], max_bytes: int, max_line: int,
    errors: List[str], warnings: List[str],
) -> None:
    max_len = max((len(ln) for ln in lines), default=0)
    if len(raw) > max_bytes:
        errors.append(f"体量超限 [{rel_posix}]: {len(raw)} 字节 > {max_bytes}")
    if max_len > max_line:
        errors.append(f"单行超限 [{rel_posix}]: {max_len} 字符 > {max_line}")
    if len(lines) > 800:
        warnings.append(f"行数建议拆分 [{rel_posix}]: {len(lines)} 行 > 800")


def _check_router(root: Path, max_router_lines: int, errors: List[str]) -> None:
    router = root / "AGENTS.md"
    if not router.is_file():
        errors.append("路由文件缺失: <root>/AGENTS.md")
        return
    try:
        text = router.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"路由文件不可读或编码错误 [AGENTS.md]: {exc}")
        return
    lines = _split_lf_lines(text)
    if len(lines) > max_router_lines:
        errors.append(f"路由文件超限 [AGENTS.md]: {len(lines)} 行 > {max_router_lines}")
    for sec in ("读取顺序", "硬约束"):
        if not re.search(rf"^#{{1,6}}\s+.*{re.escape(sec)}", text, re.M):
            errors.append(f"路由文件缺必需小节 [AGENTS.md]: {sec}")


def _evaluate_status(
    path: Path, rel_posix: str, root: Path, lines: List[str], counts: Dict[str, int],
    errors: List[str], active_links: List[Tuple[str, Path, List[str]]], superseded: Dict[Path, str],
) -> None:
    meta, unfenced = _parse_header_meta(lines)
    status = meta.get("文档状态", "Active")
    if status not in VALID_STATES:
        errors.append(f"文档状态非法 [{rel_posix}]: {status!r}")
        return
    counts[status] += 1
    if status == "Superseded":
        superseded.setdefault(path.resolve(), rel_posix)
        if err := _validate_superseded_target(path, root, meta.get("取代于", "")):
            errors.append(f"状态机违规 [{rel_posix}]: {err}")
    elif "取代于" in meta:
        errors.append(f"状态机违规 [{rel_posix}]: {status} 文档不得携带「取代于」")
    if status == "Active" and (links := _extract_md_links(unfenced)):
        active_links.append((rel_posix, path, links))


def _collect_superseded_warnings(
    active_links: List[Tuple[str, Path, List[str]]], superseded: Dict[Path, str], warnings: List[str],
) -> None:
    seen: Set[Tuple[str, str]] = set()
    for rel_posix, doc_path, links in active_links:
        for raw_url in links:
            clean = urllib.parse.unquote(raw_url.split("#", 1)[0].split("?", 1)[0].strip())
            if (
                not clean or "\x00" in clean or "://" in clean
                or clean.startswith(("/", "\\", "mailto:")) or not clean.lower().endswith(".md")
            ):
                continue
            if (target := (doc_path.parent / clean).resolve()) in superseded:
                target_rel = superseded[target]
                if (rel_posix, target_rel) not in seen:
                    seen.add((rel_posix, target_rel))
                    warnings.append(f"Active 引用 Superseded [{rel_posix}]: {target_rel}")


def _scan_docs(root: Path, args: argparse.Namespace) -> Tuple[List[str], List[str], Dict[str, int]]:
    errors, warnings = [], []
    counts = {"Active": 0, "Contested": 0, "Superseded": 0}
    superseded: Dict[Path, str] = {}
    active_links: List[Tuple[str, Path, List[str]]] = []
    _check_router(root, args.max_router_lines, errors)

    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.suffix.lower() not in {".md", ".markdown"}:
            continue
        rel = path.relative_to(root)
        if any(p in rel.parts for p in SKIP_DIRS) or rel.parts[:2] == ("project", "reviews") or rel.parts == ("AGENTS.md",):
            continue
        need_status = path.suffix.lower() == ".md" and rel.parts[:2] != ("project", "backlog")
        need_size = rel.parts[:2] != ("reference", "articles")
        if not (need_status or need_size):
            continue
        try:
            raw = path.read_bytes()
            lines = _split_lf_lines(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"不可读或非法 UTF-8 [{rel.as_posix()}]: {exc}")
            continue
        if need_size:
            _check_size(rel.as_posix(), raw, lines, args.max_doc_bytes, args.max_doc_line, errors, warnings)
        if need_status:
            _evaluate_status(path, rel.as_posix(), root, lines, counts, errors, active_links, superseded)

    _collect_superseded_warnings(active_links, superseded, warnings)
    return errors, warnings, counts


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="本仓私有精简文档健康门禁（状态机 / 体量 / 路由）")
    parser.add_argument("--root", default="docs", help="文档根目录（默认 docs）")
    parser.add_argument("--max-doc-bytes", type=int, default=65536, help="单文档最大字节数（默认 65536）")
    parser.add_argument("--max-doc-line", type=int, default=1000, help="单行最大字符数（默认 1000）")
    parser.add_argument("--max-router-lines", type=int, default=30, help="AGENTS.md 最大行数（默认 30）")
    parser.add_argument("--quiet", action="store_true", help="仅输出缺陷")
    args = parser.parse_args()

    if args.max_doc_bytes < 0 or args.max_doc_line < 0 or args.max_router_lines < 0:
        print("❌ 阈值参数不得为负数", file=sys.stderr)
        return 2
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"❌ 文档根目录不存在: {root}", file=sys.stderr)
        return 2

    errors, warnings, counts = _scan_docs(root, args)
    for w in warnings:
        print(f"⚠️ {w}")
    for e in errors:
        print(f"❌ {e}")
    if not args.quiet:
        print(f"📊 状态统计: Active={counts['Active']} Contested={counts['Contested']} Superseded={counts['Superseded']}")
        print(f"{'🚫 门禁未通过' if errors else '✅ 健康门禁通过'}: {len(errors)} 项阻断, {len(warnings)} 项警告")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
