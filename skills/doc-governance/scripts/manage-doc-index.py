#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage-doc-index.py - 象限索引托管维护器 (RFC-0003 目录级索引约定)
功能:
  1. ensure   : 确保指定象限目录存在托管索引 index.md（不存在则创建合规骨架）;
  2. register : ensure + 幂等登记文档链接 + 控制头/修订表版本联动（补丁位递增，窗口 <= 5）;
  3. 人工索引保护: 判据为「H1 之后首个非空行精确等于托管标记」（位置契约），仅正文引用该
     字符串的人工索引不会被误判；目标目录已有 README.md 入口时按 DA-4 跳过生成;
  4. 入参校验: --dir 拒绝绝对路径/'..'/root 本身（不得越出 --root）; --file 必须是
     --root/--dir 内真实存在的纯文件名（拒绝 ghost 登记制造 404）。

用法:
  python3 manage-doc-index.py ensure   --root docs --dir how-to [--title "操作指南"]
  python3 manage-doc-index.py register --root docs --dir how-to --file deployment.md \
                                       --title "生产部署 SOP" --kind HowTo

退出码: 0 = 成功或安全 no-op（含"检测到人工索引/README 入口，跳过"）; 1 = 真实故障
        （入参非法、目标文档缺失、索引结构不可识别、写入失败）——失败时绝不留下半成品改写。
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

MANAGED_MARKER = "<!-- doc-index:managed -->"
INVENTORY_HEADING = "## 文档清单 (Document Inventory)"
MAX_REVISION_ROWS = 5
# 容忍 "V1.0.0 (Draft)" 等注记后缀（注释号语义与门禁 normalize_version 一致）；
# 已知差异：本正则大小写敏感，小写 "v1.0.0" 会被拒绝并显式报错（方向保守、不写盘），不追求与校验器逐字符等价（DR1-9）
HEADER_VERSION_RE = re.compile(r"^> - \*\*当前版本\*\*: (V?\d+(?:\.\d+)*)(.*)$", re.MULTILINE)


class IndexMaintenanceError(Exception):
    """象限索引维护失败：入参非法或索引结构不可识别（调用方须以非 0 退出）。"""


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


def strip_leading_noise(text: str) -> str:
    """剥离 BOM 与其后的 YAML frontmatter 围栏，返回正文起点（DR1-2 最小硬化）。"""
    lines = text.lstrip("\ufeff").splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and lines[idx].strip() == "---":
        idx += 1
        while idx < len(lines) and lines[idx].strip() != "---":
            idx += 1
        idx += 1
    return "\n".join(lines[idx:])


def is_managed(text: str) -> bool:
    """托管判据（RFC §3.2 位置契约）：H1 之后的首个非空行精确等于托管标记。

    仅正文引用该标记字符串的人工索引不得被判为托管（R1-1 回归）；
    前导 BOM / frontmatter 围栏不影响锚点（DR1-2）。
    """
    h1_seen = False
    for raw_line in strip_leading_noise(text).splitlines():
        line = raw_line.strip()
        if not h1_seen:
            if line.startswith("# "):
                h1_seen = True
            continue
        if not line:
            continue
        return line == MANAGED_MARKER
    return False


def validate_dir_arg(dir_rel: str) -> str:
    """校验 --dir：拒绝空值、root 本身、绝对路径与 '..' 逃逸（R1-7 / R1-10）。"""
    normalized = (dir_rel or "").strip()
    if normalized in ("", ".", "./"):
        raise IndexMaintenanceError("--dir 不得为空或指向 --root 本身（N3：根级索引为人工唯一入口）")
    if Path(normalized).is_absolute():
        raise IndexMaintenanceError(f"--dir 不得为绝对路径: {dir_rel}")
    parts = [p for p in normalized.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        raise IndexMaintenanceError(f"--dir 非法: {dir_rel}")
    if ".." in parts:
        raise IndexMaintenanceError(f"--dir 不得包含 '..'（禁止越出 --root）: {dir_rel}")
    return "/".join(parts)


def validate_file_arg(file_name: str) -> str:
    """校验 --file：必须是纯文件名（禁止路径分隔符与相对路径片段，R1-6 / SH-1）。"""
    name = file_name or ""
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise IndexMaintenanceError(f"--file 必须是纯文件名（不含路径分隔符）: {file_name}")
    return name


def resolve_within_root(root: Path, dir_rel: str) -> Path:
    """解析后必须仍位于 --root 之内（校验的确定性兜底）。"""
    target = (root / dir_rel).resolve()
    root_resolved = root.resolve()
    if target == root_resolved:
        raise IndexMaintenanceError(f"--dir 解析后为 --root 本身，拒绝（N3：根级索引为人工唯一入口）: {dir_rel}")
    if root_resolved not in target.parents:
        raise IndexMaintenanceError(f"--dir 解析后越出 --root: {dir_rel}")
    return target


def next_patch_version(version: str) -> str:
    """V1.0.0 -> V1.0.1（补丁位递增，缺失位补 0）。"""
    nums = version.lstrip("Vv").split(".")
    while len(nums) < 3:
        nums.append("0")
    nums[2] = str(int(nums[2]) + 1)
    return "V" + ".".join(nums)


def bump_header_version(text: str):
    """升级控制头版本号（保留注记后缀）。无法解析时显式报错（R1-4）。"""
    match = HEADER_VERSION_RE.search(text)
    if not match:
        raise IndexMaintenanceError(
            "控制头缺少可解析的『当前版本』声明，已放弃本次登记（保证零版本漂移）"
        )
    new_version = next_patch_version(match.group(1))
    return text[: match.start(1)] + new_version + text[match.end(1):], new_version


def insert_revision_row(text: str, version: str, today: str, description: str) -> str:
    """在修订历史表格首行插入记录并裁剪至滑动窗口。表头不可识别时显式报错（R1-5）。"""
    lines = text.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("| 版本号"):
            header_idx = idx
            break
    if header_idx is None:
        raise IndexMaintenanceError(
            "修订历史表结构无法识别（表头须以『| 版本号』开头），已放弃本次登记（保证零版本漂移）"
        )

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
    """确保象限索引存在。返回 (status, entry_file)。

    status: created | exists-managed | skipped-manual | skipped-readme
    """
    dir_path = root / dir_rel
    index_file = dir_path / "index.md"

    if index_file.exists():
        content = read_index(index_file)
        if content is not None and is_managed(content):
            return "exists-managed", index_file
        return "skipped-manual", index_file

    # DA-4：既有 README.md 目录入口则不生成第二份索引
    readme_file = dir_path / "README.md"
    if readme_file.exists():
        return "skipped-readme", readme_file

    dir_path.mkdir(parents=True, exist_ok=True)
    index_file.write_text(
        build_skeleton(dir_rel, title or derive_title(dir_rel), date.today().isoformat()),
        encoding="utf-8",
    )
    return "created", index_file


def register_doc(root: Path, dir_rel: str, filename: str, title: str, kind: str):
    """登记文档至象限索引（幂等）。返回 (status, entry_file)。"""
    filename = validate_file_arg(filename)
    dir_path = resolve_within_root(root, dir_rel)

    if not (dir_path / filename).is_file():
        raise IndexMaintenanceError(
            f"--file 目标不存在，拒绝登记（避免制造 404 清单行）: {dir_rel}/{filename}"
        )

    status, index_file = ensure_index(root, dir_rel)
    if status in ("skipped-manual", "skipped-readme"):
        return status, index_file

    text = read_index(index_file)
    if text is None or not is_managed(text):
        return "skipped-manual", index_file

    if f"](./{filename})" in text:
        return "already", index_file

    today = date.today().isoformat()
    text, new_version = bump_header_version(text)
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
        dir_rel = validate_dir_arg(args.dir_rel)
        resolve_within_root(root, dir_rel)
        if args.command == "ensure":
            status, entry_file = ensure_index(root, dir_rel, args.title)
        else:
            status, entry_file = register_doc(root, dir_rel, args.file, args.title, args.kind)
    except IndexMaintenanceError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"❌ 象限索引维护失败: {exc}", file=sys.stderr)
        return 1

    messages = {
        "created": f"✅ 已创建托管象限索引: {entry_file}",
        "exists-managed": f"ℹ️  象限索引已存在（托管），无需变更: {entry_file}",
        "skipped-manual": f"⚠️  检测到人工索引（无托管标记），跳过自动维护: {entry_file}",
        "skipped-readme": f"ℹ️  检测到 README.md 目录入口，按 DA-4 跳过生成与登记: {entry_file}",
        "registered": f"✅ 已登记文档至象限索引: {getattr(args, 'file', '')} ➔ {entry_file}",
        "already": f"ℹ️  文档已登记，跳过: {getattr(args, 'file', '')}",
    }
    print(messages.get(status, f"ℹ️  完成 ({status})"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
