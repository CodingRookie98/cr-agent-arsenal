#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-doc-control-sync.py - 文档控制头与修订历史版本一致性扫描器
功能:
  1. 递归扫描指定根目录下的所有 Markdown 文档；
  2. 提取文档头部元数据中的版本标识（Frontmatter / 引用块 / 表格）；
  3. 提取修订历史记录（Revision History）表格中的最新版本号；
  4. 断言「控制头版本号 == 修订历史最新行版本号」，防止静默漂移；
  5. 发现版本漂移时输出详细差异并以 Exit Code 1 阻断，一致时返回 Exit Code 0。
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")


def in_evidence_archive(path: Path, root_dir: Path) -> bool:
    """判定路径是否落在交付凭据归档根内（<root>/project/reviews/**）。"""
    try:
        rel = path.relative_to(root_dir)
    except ValueError:
        return False
    return rel.parts[:2] == EVIDENCE_ARCHIVE_PARTS


def parse_frontmatter(content: str) -> Dict[str, str]:
    """解析文档头部的 Frontmatter 或文档控制信息块"""
    metadata: Dict[str, str] = {}
    # 模式 A: YAML Frontmatter (--- ... ---)
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if yaml_match:
        for line in yaml_match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                metadata[k.strip().lower()] = v.strip()
        return metadata

    # 模式 B: 引用块元数据 (> - **当前版本**: V1.4.0)
    for line in content.splitlines()[:50]:
        trimmed = line.strip()
        if trimmed.startswith(">"):
            clean = re.sub(r"^[>\s\-*]+", "", trimmed).strip()
            if ":" in clean or "：" in clean:
                sep = ":" if ":" in clean else "："
                k, v = clean.split(sep, 1)
                k_clean = re.sub(r"[*_`]", "", k).strip().lower()
                metadata[k_clean] = v.strip()

    # 模式 C: 表格型元数据 (| 当前版本 | V1.4.0 |)
    if "文档标识" in content or "当前版本" in content or "version" in content.lower() or "文档版本" in content:
        for m in re.finditer(r"\|\s*(?:\*\*)?([^|\n*]+?)(?:\*\*)?\s*\|\s*([^|\n]+?)\s*\|", content):
            k_raw = m.group(1).strip().lower()
            v_raw = m.group(2).strip()
            if k_raw in ("文档标识", "当前版本", "规范版本", "文档版本", "version", "id", "文档所有者", "生效日期"):
                metadata[k_raw] = v_raw

    return metadata


def normalize_version(raw_version: str) -> Optional[str]:
    """从原始版本字符串中提取归一化的纯数字版本串（例如 'V1.4.0 (Draft)' -> '1.4.0'）"""
    m = re.search(r"V?(\d+(?:\.\d+)*)", raw_version, re.IGNORECASE)
    return m.group(1) if m else None


def version_tuple(ver_str: str) -> Tuple[int, ...]:
    """将版本字符串转换为整数元组以便比较"""
    try:
        return tuple(int(x) for x in ver_str.split("."))
    except ValueError:
        return (0,)


REVISION_HEADER_PATTERN = re.compile(
    r"^#+\s*(?:修订历史(?:记录)?|Revision\s*History)",
    re.IGNORECASE,
)


def extract_revision_versions(content: str) -> List[Tuple[str, str, int]]:
    """
    提取修订历史表格中的版本数据行。
    返回: [(raw_row_version, normalized_version, lineno), ...]
    """
    lines = content.splitlines()
    in_revision_section = False
    in_table = False
    table_header_seen = 0
    results = []

    for idx, line in enumerate(lines, start=1):
        trimmed = line.strip()

        if REVISION_HEADER_PATTERN.search(trimmed):
            in_revision_section = True
            continue

        if in_revision_section and re.match(r"^#{1,3}\s+", trimmed):
            if in_table:
                break
            in_revision_section = False

        if in_revision_section:
            if trimmed.startswith("|") and trimmed.endswith("|"):
                if table_header_seen < 2:
                    table_header_seen += 1
                    in_table = True
                else:
                    # 数据行，提取首列或包含版本号的列
                    cols = [c.strip() for c in trimmed.strip("|").split("|")]
                    row_ver_raw = cols[0] if cols else trimmed
                    norm_ver = normalize_version(row_ver_raw)
                    if not norm_ver:
                        # 尝试在整个行中搜索版本号
                        norm_ver = normalize_version(trimmed)
                    if norm_ver:
                        results.append((row_ver_raw, norm_ver, idx))
            else:
                if in_table:
                    break

    return results


def check_file_version_sync(file_path: Path) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    检查单个文件的控制头版本与修订历史最新版本是否一致。
    返回: (is_synced, header_ver, rev_ver, error_msg)
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, None, None, f"无法读取文件: {e}"

    meta = parse_frontmatter(content)
    # 查找控制头版本号
    raw_header_ver = None
    for k in ("当前版本", "version", "文档版本", "规范版本", "版本"):
        if k in meta:
            raw_header_ver = meta[k]
            break

    rev_versions = extract_revision_versions(content)

    # 若没有修订历史，且没有声明版本，跳过
    if not raw_header_ver and not rev_versions:
        return True, None, None, None

    # 若声明了版本，但没有修订历史表格（部分极简说明或短文档允许无修订表）
    if raw_header_ver and not rev_versions:
        return True, raw_header_ver, None, None

    # 若有修订历史表格，但缺少控制头版本声明
    if not raw_header_ver and rev_versions:
        latest_rev = rev_versions[0][1]
        return False, None, latest_rev, f"修订历史中存在版本记录 ({rev_versions[0][0]})，但头部缺少标准控制头版本声明"

    norm_header = normalize_version(raw_header_ver)
    if not norm_header:
        return True, raw_header_ver, None, None

    # 分析修订历史最新行（标准降序下为第 1 行）
    first_row_raw, first_row_norm, first_row_line = rev_versions[0]

    # 判断表格排序模式：降序 vs 升序
    latest_norm = first_row_norm
    latest_raw = first_row_raw

    if len(rev_versions) > 1:
        last_row_raw, last_row_norm, _ = rev_versions[-1]
        v_first = version_tuple(first_row_norm)
        v_last = version_tuple(last_row_norm)
        if v_last > v_first:
            # 升序排列（追加在末尾）
            latest_norm = last_row_norm
            latest_raw = last_row_raw

    if norm_header != latest_norm:
        return (
            False,
            raw_header_ver,
            latest_raw,
            f"控制头版本 ('{raw_header_ver}' -> {norm_header}) 与修订历史最新记录 ('{latest_raw}' -> {latest_norm}) 不一致，存在版本漂移",
        )

    return True, raw_header_ver, latest_raw, None


def scan_version_sync(
    root_dir: Path,
    target_dirs: Optional[List[str]] = None,
) -> Tuple[int, List[Dict]]:
    """
    扫描目录下的 Markdown 文件，校验版本联动一致性。
    返回: (total_checked_files, drift_errors)
    """
    all_files: List[Path] = []
    if target_dirs:
        for t in target_dirs:
            p = root_dir / t
            if p.is_file() and p.suffix == ".md":
                all_files.append(p)
            elif p.is_dir():
                all_files.extend(p.rglob("*.md"))
    else:
        all_files = list(root_dir.rglob("*.md"))

    drift_errors: List[Dict] = []
    checked_count = 0

    for f in sorted(all_files):
        if any(p in f.parts for p in ("node_modules", ".git", ".next", "dist", "build")):
            continue
        if in_evidence_archive(f, root_dir):
            continue
        # 形态 B 待办卡片不强制包含修订历史
        if "backlog" in f.parts and ("active" in f.parts or "archive" in f.parts):
            continue

        checked_count += 1
        is_synced, h_ver, r_ver, err_msg = check_file_version_sync(f)
        if not is_synced and err_msg:
            try:
                rel_path = str(f.relative_to(root_dir))
            except ValueError:
                rel_path = str(f)
            drift_errors.append({
                "file": rel_path,
                "header_ver": h_ver,
                "revision_ver": r_ver,
                "message": err_msg,
            })

    return checked_count, drift_errors


def main():
    parser = argparse.ArgumentParser(description="文档控制头与修订历史版本联动一致性检查器")
    parser.add_argument("--root", default="docs", help="文档根目录 (默认为 docs)")
    parser.add_argument("--dir", action="append", help="指定检查的子目录或文件 (可多次指定)")
    parser.add_argument("--verbose", action="store_true", help="输出详细扫描信息")

    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    if not root_path.exists():
        print(f"❌ 错误: 目标文档目录不存在: {root_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 启动文档控制头与修订历史版本联动一致性扫描: 根目录={root_path} ...")
    total_checked, drift_errors = scan_version_sync(root_path, args.dir)

    print(f"\n📊 扫描汇总: 共检查 {total_checked} 个 Markdown 文件")
    if not drift_errors:
        print("✅ 恭喜！所有文档控制头与修订历史版本 100% 保持一致，无版本漂移！")
        sys.exit(0)
    else:
        print(f"❌ 发现 {len(drift_errors)} 处版本联动漂移错误:\n")
        for idx, err in enumerate(drift_errors, 1):
            print(f"   [{idx}] {err['file']}")
            print(f"       控制头版本: {err['header_ver'] or '未声明'}")
            print(f"       修订表最新: {err['revision_ver'] or '无'}")
            print(f"       问题描述:   {err['message']}\n")
        print("💡 修复建议: 升级控制头版本时，必须同步在修订历史表格首行追加对应的版本记录；反之亦然。")
        sys.exit(1)


if __name__ == "__main__":
    main()
