#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage-doc-index.py - 象限索引托管维护器 (RFC-0003 目录级索引约定)
功能:
  1. ensure   : 确保指定象限目录存在托管索引 index.md（不存在则创建合规骨架）;
  2. register : ensure + 幂等登记文档链接 + 控制头/修订表版本联动（补丁位递增，窗口 <= 5）;
  3. 人工索引保护: 不含托管标记 <!-- doc-index:managed --> 的索引一律不改写（安全 no-op）。

用法:
  python3 manage-doc-index.py ensure   --root docs --dir how-to [--title "操作指南"]
  python3 manage-doc-index.py register --root docs --dir how-to --file deployment.md \
                                       --title "生产部署 SOP" --kind HowTo

退出码: 0 = 成功或安全 no-op; 1 = 真实故障（参数非法、写入失败）。
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

MANAGED_MARKER = "<!-- doc-index:managed -->"
INVENTORY_HEADING = "## 文档清单 (Document Inventory)"
MAX_REVISION_ROWS = 5
HEADER_VERSION_RE = re.compile(r"^> - \*\*当前版本\*\*: (V\d+(?:\.\d+)*)\s*$", re.MULTILINE)


def derive_title(dir_rel: str) -> str:
    """由目录名派生象限标题（how-to -> How To; explanation/decisions -> Explanation / Decisions）"""
    parts = [p.replace("-", " ").replace("_", " ").strip().title() for p in dir_rel.split("/") if p]
    return " / ".join(parts) if parts else dir_rel


def build_skeleton(dir_rel: str, title: str, today: str) -> str:
    """生成托管象限索引骨架（含控制头、修订历史、文档清单段）。"""
    slug = dir_rel.replace("/", "-").upper()
    year = today[:4]
    return f"""# {title} 象限索引 (Quadrant Index)

{MANAGED_MARKER}
> ⚙️ **托管索引声明**: 本文件由 `manage-doc-index.py` 自动创建与维护（`scaffold-doc.sh` 生成文档时同步登记）。删除上方托管标记即可转为人工维护，届时脚本将不再改写本文件。

> **文档控制信息**
> - **文档标识**: DOCIDX-{slug}-{year}
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: {today}
> - **文档所有者**: AI Agent / 工程师

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | {today} | AI Agent | 架构师 | 初始化 `{dir_rel}/` 托管象限索引 |

---

{INVENTORY_HEADING}

<!-- 本清单由 manage-doc-index.py 自动维护；全库总入口见根级 docs/index.md -->
"""


def next_patch_version(version: str) -> str:
    """V1.0.0 -> V1.0.1（补丁位递增，缺失位补 0）。"""
    nums = version.lstrip("Vv").split(".")
    while len(nums) < 3:
        nums.append("0")
    nums[2] = str(int(nums[2]) + 1)
    return "V" + ".".join(nums)


def bump_header_version(text: str):
    """升级控制头版本号。返回 (新文本, 新版本号或 None)。"""
    match = HEADER_VERSION_RE.search(text)
    if not match:
        return text, None
    new_version = next_patch_version(match.group(1))
    return text[: match.start(1)] + new_version + text[match.end(1):], new_version


def insert_revision_row(text: str, version: str, today: str, description: str) -> str:
    """在修订历史表格首行插入记录，并裁剪至 MAX_REVISION_ROWS 条滑动窗口。"""
    lines = text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("| 版本号"):
            header_idx = idx
            break
    if header_idx is None:
        return text

    insert_at = header_idx + 2
    lines.insert(insert_at, f"| **{version}** | {today} | AI Agent | 架构师 | {description} |")

    end = insert_at + 1
    while end < len(lines) and lines[end].strip().startswith("|"):
        end += 1
    data_rows = list(range(insert_at, end))
    if len(data_rows) > MAX_REVISION_ROWS:
        for idx in reversed(data_rows[MAX_REVISION_ROWS:]):
            del lines[idx]
    return "\n".join(lines) + "\n"


def read_index(index_file: Path):
    try:
        return index_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def ensure_index(root: Path, dir_rel: str, title=None):
    """确保象限索引存在。返回 (status, index_file)。"""
    index_file = root / dir_rel / "index.md"
    if index_file.exists():
        content = read_index(index_file)
        if content is not None and MANAGED_MARKER in content:
            return "exists-managed", index_file
        return "skipped-manual", index_file

    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(
        build_skeleton(dir_rel, title or derive_title(dir_rel), date.today().isoformat()),
        encoding="utf-8",
    )
    return "created", index_file


def register_doc(root: Path, dir_rel: str, filename: str, title: str, kind: str):
    """登记文档至象限索引（幂等）。返回 (status, index_file)。"""
    status, index_file = ensure_index(root, dir_rel)
    if status == "skipped-manual":
        return "skipped-manual", index_file

    text = read_index(index_file)
    if text is None or MANAGED_MARKER not in text:
        return "skipped-manual", index_file

    if f"](./{filename})" in text:
        return "already", index_file

    today = date.today().isoformat()
    text, new_version = bump_header_version(text)
    if new_version:
        text = insert_revision_row(text, new_version, today, f"登记 {filename}")
    text = text.rstrip("\n") + f"\n- [{title}](./{filename}) — {kind}\n"
    index_file.write_text(text, encoding="utf-8")
    return "registered", index_file


def main() -> int:
    parser = argparse.ArgumentParser(description="象限索引托管维护器（RFC-0003 目录级索引约定）")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ensure_parser = subparsers.add_parser("ensure", help="确保象限索引存在（不存在则创建托管骨架）")
    ensure_parser.add_argument("--root", default="docs", help="文档根目录 (默认为 docs)")
    ensure_parser.add_argument("--dir", dest="dir_rel", required=True, help="相对根目录的象限目录")
    ensure_parser.add_argument("--title", help="象限标题（缺省由目录名派生）")

    register_parser = subparsers.add_parser("register", help="幂等登记文档至象限索引")
    register_parser.add_argument("--root", default="docs", help="文档根目录 (默认为 docs)")
    register_parser.add_argument("--dir", dest="dir_rel", required=True, help="相对根目录的象限目录")
    register_parser.add_argument("--file", required=True, help="待登记文档文件名（含 .md）")
    register_parser.add_argument("--title", required=True, help="待登记文档标题")
    register_parser.add_argument("--kind", default="Doc", help="文档类型标签（如 HowTo / Reference）")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    try:
        if args.command == "ensure":
            status, index_file = ensure_index(root, args.dir_rel, args.title)
        else:
            status, index_file = register_doc(root, args.dir_rel, args.file, args.title, args.kind)
    except OSError as exc:
        print(f"❌ 象限索引维护失败: {exc}", file=sys.stderr)
        return 1

    messages = {
        "created": f"✅ 已创建托管象限索引: {index_file}",
        "exists-managed": f"ℹ️  象限索引已存在（托管），无需变更: {index_file}",
        "skipped-manual": f"⚠️  检测到人工索引（无托管标记），跳过自动维护: {index_file}",
        "registered": f"✅ 已登记文档至象限索引: {getattr(args, 'file', '')} ➔ {index_file}",
        "already": f"ℹ️  文档已登记，跳过: {getattr(args, 'file', '')}",
    }
    print(messages.get(status, f"ℹ️  完成 ({status})"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
