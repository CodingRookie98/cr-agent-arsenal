#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage-backlog.py - Backlog 形态 B (Issue-as-File) 自动化管理与可编程查询工具

用法: python3 scripts/backlog/manage-backlog.py <command> [options]

功能:
  1. 脚本化提取与解析: list 命令支持按状态 (active/in-progress/completed)、优先级 (P0-P3)、
     类型 (Feature/TechDebt 等) 过滤，支持 --json 输出供 AI 智能体或外部脚本消费；
  2. 索引自动同步: sync-index 命令扫描 active/ 与 archive/ 目录，自动重构 docs/project/backlog/index.md；
  3. 待办生命周期流转:
     - create: 自动计算下一编号 BK-XXXX，创建带标准 Frontmatter 的待办卡片文件并刷新索引；
     - close: 更新元数据 (status, closed_at, resolution, destination)，将文件物理迁入 archive/ 并刷新索引；
     - reopen: 将待办从 archive/ 重新移回 active/ 并重置状态。
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None


VALID_TYPES = ["Feature", "TechDebt", "Bug", "Security", "Governance", "Performance"]
VALID_STATUSES = ["active", "in-progress", "completed", "rejected", "deferred"]
VALID_PRIORITIES = ["P0", "P1", "P2", "P3"]

# 建卡期占位语：close 归档时机械收敛，不代表对验收结论的判断
PLACEHOLDER_PATTERN = re.compile(r"^\*\(未开工[^\n]*\n?", re.MULTILINE)
# DoD 勾选属作者人工职责：close 只做机械统计与提示，不代勾验收准则
DOD_DUTY_NOTE = (
    "\n*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；"
    "`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*\n"
)

# §3 (DoD) 小节：提示项数只统计该小节内的复选框，避免把其他小节的复选框算进 DoD
DOD_SECTION_PATTERN = re.compile(r"^##\s*3\..*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)


def count_unchecked_dod(body: str) -> int:
    """统计 §3 (DoD) 小节内未勾选的复选框数；卡片无 §3 小节时返回 0"""
    section = DOD_SECTION_PATTERN.search(body)
    if not section:
        return 0
    return len(re.findall(r"^- \[ \] ", section.group(0), flags=re.MULTILINE))


def slugify(text: str) -> str:
    """将标题转换为合法的 URL/文件名 slug (保留英文、数字、汉字，以连字符分隔)"""
    text = text.strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:40] or "task"


# YAML 标量的最小加引号判据：只对「直写会改变结构或语义」的值做双引号转义编码，
# 其余保持裸标量（status: active / priority: P1 这类），避免零依赖写出的卡片
# 与 PyYAML 写出的卡片在文本层大面积分叉，也避免简单只读解析器（不剥引号）
# 把带引号的状态值读成 '"active"'。
_YAML_INDICATOR_START = "-?:,[]{}#&*!|>'\"%@`"

# PyYAML 会把下列裸标量解析成 bool / None / int / date，字符串字段必须加引号才不会
# 在「零依赖写、PyYAML 读」的方向上发生类型漂移（PyYAML 自己的 dump 也如此加引号）。
_YAML_RESERVED_WORDS = {
    "true", "false", "yes", "no", "on", "off", "y", "n", "null", "~",
}
_YAML_NUMBER_LIKE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?$")
_YAML_DATE_LIKE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[Tt ].*)?$")


def _needs_quoting(text: str) -> bool:
    """判断裸标量直写是否会破坏 YAML 结构或改变语义"""
    if text == "" or text.strip() != text:
        return True
    if any(ch in text for ch in ("\n", "\r", "\t", "\\", '"')):
        return True
    if text[0] in _YAML_INDICATOR_START:
        return True
    if ": " in text or " #" in text or text.endswith(":"):
        return True
    if text.lower() in _YAML_RESERVED_WORDS:
        return True
    if _YAML_NUMBER_LIKE.match(text) or _YAML_DATE_LIKE.match(text):
        return True
    return False


def _encode_scalar(value) -> str:
    """把元数据值编码为单行 YAML 标量（必要时双引号 + 转义）

    多行值改走 \n 转义而非块标量（| / |-）：块标量会引入多行缩进语法，序列化与
    解析两侧都要各自实现缩进推断与 -> 折行语义，回归面扩大；转义式编码保持
    「一键一行」，PyYAML 与本模块降级解析器都能读回。
    """
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return str(value).lower() if isinstance(value, bool) else str(value)
    text = str(value)
    if not _needs_quoting(text):
        return text
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _decode_scalar(raw: str) -> str:
    """还原 _encode_scalar 的双引号转义；其余形态沿用旧行为（去首尾引号）"""
    text = raw.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        inner = text[1:-1]
        out = []
        i = 0
        escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
        while i < len(inner):
            ch = inner[i]
            if ch == "\\" and i + 1 < len(inner):
                out.append(escapes.get(inner[i + 1], inner[i + 1]))
                i += 2
                continue
            out.append(ch)
            i += 1
        return "".join(out)
    return text.strip("\"'")


def parse_item_file(file_path: Path) -> Tuple[Dict, str]:
    """解析待办卡片文件的 Frontmatter 元数据与正文内容"""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    metadata: Dict = {}
    body = content

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        body = match.group(2).strip()
        if yaml:
            try:
                parsed = yaml.safe_load(yaml_content)
                if isinstance(parsed, dict):
                    metadata = parsed
            except Exception:
                metadata = {}
        else:
            # BK-0047 批次 C：无 PyYAML 时的降级解析器（本模块刻意保持零依赖可选）。
            # 原实现只认 "key: value"，会把 dump 出来的 "key:\n  - a" 列表读成空串，
            # 于是 source / acceptance_criteria 在无 PyYAML 环境下静默丢失（Windows
            # .venv 实测：create 出的卡片 source 被读成 ''）。此处按「键行 + 列表项」
            # 两态推进：空值键先占位为 ''，遇到 "- " 行才升级为列表——无列表项时
            # 语义与旧实现逐字一致。
            #
            # 跨行折行：PyYAML dump 会按 best_width 把长 plain scalar 与长列表项折成
            # 「缩进续行」。续行既不是键行也不是 "- " 行，旧实现整段丢弃，长字段因此被
            # 截断（索引里 BK-0041 的 destination 停在「…；C-04」即此形态）。按 YAML
            # 折行语义，续行以单个空格拼回上一标量值或上一列表项。
            current_key: Optional[str] = None
            current_is_list = False
            for raw_line in yaml_content.splitlines():
                stripped = raw_line.strip()
                if not stripped:
                    continue
                if stripped.startswith("- ") and current_key is not None:
                    if not isinstance(metadata.get(current_key), list):
                        metadata[current_key] = []
                    metadata[current_key].append(_decode_scalar(stripped[2:]))
                    current_is_list = True
                    continue
                if raw_line[:1] in (" ", "\t") and current_key is not None:
                    if current_is_list and metadata.get(current_key):
                        metadata[current_key][-1] = (
                            f"{metadata[current_key][-1]} {stripped.strip(chr(39) + chr(34))}"
                        ).strip()
                    elif not current_is_list and isinstance(metadata.get(current_key), str):
                        metadata[current_key] = (
                            f"{metadata[current_key]} {stripped}".strip().strip("\"'")
                        )
                    continue
                if ":" in raw_line:
                    k, v = raw_line.split(":", 1)
                    key = k.strip()
                    if v.strip() == "[]":
                        metadata[key] = []
                        current_key = None
                        current_is_list = False
                    else:
                        metadata[key] = _decode_scalar(v)
                        current_key = key
                        current_is_list = False

            # 与 PyYAML 对齐：裸 null / ~ / 空值在 YAML 语义上是 None，而不是字面串。
            # 旧实现把 "null" 读成字符串，零依赖环境与 PyYAML 环境看到的元数据不一致。
            for key, value in list(metadata.items()):
                if isinstance(value, str) and value in ("", "null", "~"):
                    metadata[key] = None

    return metadata, body


def dump_item_file(file_path: Path, metadata: Dict, body: str):
    """序列化写入待办卡片文件"""
    if yaml:
        yaml_str = yaml.dump(
            metadata,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ).strip()
    else:
        lines = []
        for k, v in metadata.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {_encode_scalar(item)}")
            elif v is None:
                lines.append(f"{k}: null")
            else:
                lines.append(f"{k}: {_encode_scalar(v)}")
        yaml_str = "\n".join(lines)

    full_content = f"---\n{yaml_str}\n---\n\n{body.strip()}\n"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(full_content, encoding="utf-8")


def find_backlog_dir(root_dir: Path) -> Path:
    """定位 project/backlog 目录 (优先检测 docs/project/backlog 或 project/backlog)"""
    candidates = [
        root_dir / "docs" / "project" / "backlog",
        root_dir / "project" / "backlog",
        root_dir / "backlog",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    if (root_dir / "docs").exists() or not (root_dir / "project").exists():
        return root_dir / "docs" / "project" / "backlog"
    return root_dir / "project" / "backlog"


def collect_all_items(backlog_dir: Path) -> List[Dict]:
    """收集 active/ 与 archive/ 下的所有待办条目"""
    items = []
    if not backlog_dir.exists():
        return items

    for f in sorted(backlog_dir.rglob("*.md")):
        if f.name == "index.md":
            continue
        meta, body = parse_item_file(f)
        bk_id = meta.get("id") or ""
        m = re.match(r"^BK-(\d{4})", f.name)
        if not bk_id and m:
            bk_id = f"BK-{m.group(1)}"
            meta["id"] = bk_id

        if not bk_id:
            continue

        # Markdown 链接必须是 POSIX 分隔符：Windows 下 str(Path) 会写出反斜杠，
        # 渲染侧与 check-doc-links.py 均判为 404（backlog 索引 20 处断链即此形态）。
        rel_path = f.relative_to(backlog_dir).as_posix()
        is_archived = "archive" in f.parts
        status = meta.get("status") or ("completed" if is_archived else "active")

        items.append({
            "id": bk_id,
            "title": meta.get("title") or f.stem,
            "type": meta.get("type") or "TechDebt",
            "priority": meta.get("priority") or "P2",
            "status": status,
            "trigger": meta.get("trigger"),
            "created_at": str(meta.get("created_at") or ""),
            "updated_at": str(meta.get("updated_at") or ""),
            "closed_at": str(meta.get("closed_at") or ""),
            "resolution": meta.get("resolution"),
            "destination": meta.get("destination"),
            "source": meta.get("source") or [],
            "acceptance_criteria": meta.get("acceptance_criteria") or [],
            "file_path": str(f),
            "rel_path": rel_path,
            "is_archived": is_archived,
            "metadata": meta,
            "body": body,
        })

    return items


def get_next_id(items: List[Dict]) -> str:
    """计算下一个递增的 BK-XXXX 编号"""
    max_num = 0
    for item in items:
        m = re.match(r"^BK-(\d{4})$", item["id"])
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return f"BK-{max_num + 1:04d}"


def get_current_quarter() -> str:
    """获取当前季度标签 (如 2026-Q4)"""
    today = date.today()
    q = (today.month - 1) // 3 + 1
    return f"{today.year}-Q{q}"


# ==============================================================================
# 命令实现
# ==============================================================================

def cmd_list(args):
    """提取与查询待办列表 (支持可编程 --json 输出)"""
    root_path = Path(args.root).resolve()
    backlog_dir = find_backlog_dir(root_path)
    all_items = collect_all_items(backlog_dir)

    filtered = []
    for item in all_items:
        if args.status and args.status.lower() != "all":
            if item["status"].lower() != args.status.lower():
                continue
        elif not args.status:
            # 默认只看活跃项 (未归档)
            if item["is_archived"]:
                continue

        if args.priority and item["priority"].upper() != args.priority.upper():
            continue
        if args.type and item["type"].lower() != args.type.lower():
            continue

        filtered.append(item)

    if args.json:
        # 纯机器 JSON 输出
        clean_items = []
        for it in filtered:
            c = dict(it)
            c.pop("metadata", None)
            c.pop("body", None)
            clean_items.append(c)
        print(json.dumps(clean_items, ensure_ascii=False, indent=2))
        return 0

    if args.format == "id-only":
        for it in filtered:
            print(it["id"])
        return 0

    if not filtered:
        print("未检索到符合条件的待办条目。")
        return 0

    # 表格输出
    print(f"共检索到 {len(filtered)} 项待办:")
    print(f"{'编号':<10} {'状态':<12} {'优先级':<8} {'类型':<12} {'标题'}")
    print("-" * 75)
    for it in filtered:
        trig = f" [{it['trigger']}]" if it.get("trigger") else ""
        print(f"{it['id']:<10} {it['status']:<12} {it['priority']:<8} {it['type']:<12} {it['title']}{trig}")

    return 0


def cmd_get(args):
    """查看单条待办的完整元数据与正文"""
    root_path = Path(args.root).resolve()
    backlog_dir = find_backlog_dir(root_path)
    all_items = collect_all_items(backlog_dir)

    target = None
    for it in all_items:
        if it["id"].upper() == args.id.upper():
            target = it
            break

    if not target:
        print(f"❌ 错误: 未找到编号为 {args.id} 的待办卡片。", file=sys.stderr)
        return 1

    if args.json:
        c = dict(target)
        c.pop("metadata", None)
        print(json.dumps(c, ensure_ascii=False, indent=2))
        return 0

    print("=" * 60)
    print(f"📄 待办详情: {target['id']} - {target['title']}")
    print("=" * 60)
    print(f"  * 状态:     {target['status']}")
    print(f"  * 优先级:   {target['priority']}")
    print(f"  * 类型:     {target['type']}")
    if target["trigger"]:
        print(f"  * 触发时机: {target['trigger']}")
    print(f"  * 创建日期: {target['created_at']}")
    if target["closed_at"]:
        print(f"  * 结项日期: {target['closed_at']} (结论: {target['resolution']})")
    if target["destination"]:
        print(f"  * 交付去向: {target['destination']}")
    if target["source"]:
        print(f"  * 来源追溯: {', '.join(target['source']) if isinstance(target['source'], list) else target['source']}")
    if target["acceptance_criteria"]:
        print(f"  * 验收准则: {', '.join(target['acceptance_criteria']) if isinstance(target['acceptance_criteria'], list) else target['acceptance_criteria']}")
    print(f"  * 物理文件: {target['file_path']}")
    print("\n[正文描述]:\n")
    print(target["body"])
    return 0


def cmd_create(args):
    """创建新的待办卡片文件 (形态 B)"""
    root_path = Path(args.root).resolve()
    backlog_dir = find_backlog_dir(root_path)
    active_dir = backlog_dir / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    all_items = collect_all_items(backlog_dir)
    next_id = get_next_id(all_items)
    slug = slugify(args.title)
    file_name = f"{next_id}-{slug}.md"
    file_path = active_dir / file_name

    today_str = date.today().isoformat()
    sources = args.source if args.source else []
    acs = args.acceptance if args.acceptance else []

    metadata = {
        "id": next_id,
        "title": args.title,
        "type": args.type,
        "status": "active",
        "priority": args.priority,
        "trigger": args.trigger or None,
        "created_at": today_str,
        "updated_at": today_str,
        "closed_at": None,
        "resolution": None,
        "destination": None,
        "source": sources,
        "acceptance_criteria": acs,
    }

    body = f"""## 1. 背景与问题陈述
{args.description or "待补充具体问题描述与上下文分析。"}

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
"""
    if acs:
        for ac in acs:
            body += f"- [ ] {ac}\n"
    else:
        body += "- [ ] 核心功能通过自动化单元测试验证\n- [ ] 无架构契约回归与漂移\n"

    body += DOD_DUTY_NOTE

    body += "\n## 4. 实施去向与结项记录\n*(未开工)*\n"

    dump_item_file(file_path, metadata, body)
    print(f"✅ 成功创建待办卡片: {file_path.relative_to(root_path)}")
    print(f"   编号: {next_id} | 优先级: {args.priority} | 类型: {args.type}")

    # 自动刷新索引
    sync_index(backlog_dir, root_path)
    return 0


def cmd_close(args):
    """结项并归档待办卡片"""
    root_path = Path(args.root).resolve()
    backlog_dir = find_backlog_dir(root_path)
    all_items = collect_all_items(backlog_dir)

    target = None
    for it in all_items:
        if it["id"].upper() == args.id.upper():
            target = it
            break

    if not target:
        print(f"❌ 错误: 未找到编号为 {args.id} 的待办卡片。", file=sys.stderr)
        return 1

    if target["is_archived"]:
        print(f"⚠️ 提示: 条目 {args.id} 已经在归档目录中。", file=sys.stderr)

    today_str = date.today().isoformat()
    version_folder = args.version or get_current_quarter()
    archive_sub_dir = backlog_dir / "archive" / version_folder
    archive_sub_dir.mkdir(parents=True, exist_ok=True)

    meta = target["metadata"]
    meta["status"] = "rejected" if args.resolution == "wontfix" else "completed"
    meta["closed_at"] = today_str
    meta["updated_at"] = today_str
    meta["resolution"] = args.resolution
    meta["destination"] = args.destination or "已交付"

    # 追加结项说明到正文；同时机械收敛建卡期占位语（不代表对验收结论的判断）
    body = PLACEHOLDER_PATTERN.sub("", target["body"]).rstrip()
    unchecked_dod = count_unchecked_dod(body)
    close_log = (
        f"\n\n### 结项记录 ({today_str})\n"
        f"- **结论**: {args.resolution}\n"
        f"- **去向/凭据**: {args.destination or '无'}\n"
        f"- **归档目录**: archive/{version_folder}/\n"
    )
    if unchecked_dod:
        close_log += (
            f"- **提示**: §3 DoD 仍有 {unchecked_dod} 项未勾选 —— `close` 不代勾验收准则，"
            f"请作者核验后更新卡片（本项为机械统计）。\n"
        )
    body += close_log

    old_file = Path(target["file_path"])
    new_file = archive_sub_dir / old_file.name

    dump_item_file(new_file, meta, body)
    if old_file.resolve() != new_file.resolve() and old_file.exists():
        old_file.unlink()

    print(f"✅ 成功结项并归档条目: {args.id}")
    print(f"   归档目标: {new_file.relative_to(root_path)}")
    print(f"   结论: {args.resolution} | 目标版本/季度: {version_folder}")

    # 自动刷新索引
    sync_index(backlog_dir, root_path)
    return 0


def cmd_reopen(args):
    """重新激活已归档的待办条目，移回 active/ 目录并重置状态为 active"""
    root_path = Path(args.root).resolve()
    backlog_dir = find_backlog_dir(root_path)
    all_items = collect_all_items(backlog_dir)

    target = None
    for it in all_items:
        if it["id"].upper() == args.id.upper():
            target = it
            break

    if not target:
        print(f"❌ 错误: 未找到编号为 {args.id} 的待办卡片。", file=sys.stderr)
        return 1

    if not target["is_archived"]:
        print(f"⚠️ 提示: 条目 {args.id} 已经在活跃目录 active/ 中，无需重新激活。")
        return 0

    active_dir = backlog_dir / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    today_str = date.today().isoformat()
    meta = target["metadata"]
    meta["status"] = "active"
    meta["updated_at"] = today_str
    meta.pop("closed_at", None)
    meta.pop("resolution", None)
    meta.pop("destination", None)

    body = target["body"]
    reopen_log = (
        f"\n\n### 重启记录 ({today_str})\n"
        f"- **操作**: 重新激活并移回 active/\n"
        f"- **说明**: 上文的历史结项记录仅作留痕，当前状态以元数据 `status: active` 为准。\n"
    )
    body += reopen_log

    old_file = Path(target["file_path"])
    new_file = active_dir / old_file.name

    dump_item_file(new_file, meta, body)
    if old_file.resolve() != new_file.resolve() and old_file.exists():
        old_file.unlink()

    print(f"✅ 成功重新激活条目: {args.id}")
    print(f"   迁移目标: {new_file.relative_to(root_path)}")

    # 自动刷新索引
    sync_index(backlog_dir, root_path)
    return 0


def sync_index(backlog_dir: Path, root_path: Path):
    """自动重新生成 docs/project/backlog/index.md 索引页"""
    all_items = collect_all_items(backlog_dir)
    index_file = backlog_dir / "index.md"

    active_items = [it for it in all_items if not it["is_archived"] and it["status"] != "completed"]
    archived_items = [it for it in all_items if it["is_archived"] or it["status"] == "completed"]

    in_progress = [it for it in active_items if it["status"] == "in-progress"]
    planned = [it for it in active_items if it["status"] != "in-progress"]

    # 按优先级排序: P0 -> P1 -> P2 -> P3
    pri_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    in_progress.sort(key=lambda x: (pri_order.get(x["priority"], 9), x["id"]))
    planned.sort(key=lambda x: (pri_order.get(x["priority"], 9), x["id"]))
    archived_items.sort(key=lambda x: x.get("closed_at") or "", reverse=True)

    lines = [
        "# 项目待办与后续演进清单 (Backlog Index)",
        "",
        "> **文档控制信息**",
        "> - **文档标识**: BK-INDEX-GOV",
        "> - **当前版本**: V2.0.0 (动态索引)",
        "> - **维护模式**: 机器脚本自动化生成 (请勿手写对账日记，运行 `manage-backlog.py sync-index` 自动刷新)",
        f"> - **更新日期**: {date.today().isoformat()}",
        "",
        "---",
        "",
        "## 1. 待办健康度仪表盘 (Metrics Dashboard)",
        "",
        f"- **现役活跃待办**: **{len(active_items)}** 项 (进行中: {len(in_progress)}, 计划中: {len(planned)})",
        f"- **历史已归档项**: **{len(archived_items)}** 项 (物理归档于 `archive/` 目录)",
        "",
        "| 优先级 | P0 (阻断级) | P1 (高优) | P2 (中优) | P3 (低优) |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **活跃数量** | {sum(1 for x in active_items if x['priority']=='P0')} | {sum(1 for x in active_items if x['priority']=='P1')} | {sum(1 for x in active_items if x['priority']=='P2')} | {sum(1 for x in active_items if x['priority']=='P3')} |",
        "",
        "---",
        "",
        "## 2. 🔄 进行中待办 (In Progress)",
        "",
    ]

    if in_progress:
        lines.append("| 编号 | 优先级 | 类型 | 标题 | 触发条件 | 卡片入口 |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for it in in_progress:
            trig = it.get("trigger") or "—"
            lines.append(f"| **{it['id']}** | `{it['priority']}` | `{it['type']}` | {it['title']} | {trig} | [{it['id']}](./{it['rel_path']}) |")
    else:
        lines.append("*(当前暂无进行中的待办)*")

    lines.extend([
        "",
        "---",
        "",
        "## 3. 📋 计划中待办 (Planned Backlog)",
        "",
    ])

    if planned:
        lines.append("| 编号 | 优先级 | 类型 | 标题 | 触发条件 | 卡片入口 |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for it in planned:
            trig = it.get("trigger") or "—"
            lines.append(f"| **{it['id']}** | `{it['priority']}` | `{it['type']}` | {it['title']} | {trig} | [{it['id']}](./{it['rel_path']}) |")
    else:
        lines.append("*(计划待办池已清空)*")

    lines.extend([
        "",
        "---",
        "",
        "## 4. 🗄️ 历史已结项归档 (Archive Summary)",
        "",
        f"> 共收录 {len(archived_items)} 条已关闭历史条目，详情参见 `archive/` 各版本目录。",
        "",
    ])

    custom_tail = ""
    if index_file.exists():
        old_text = index_file.read_text(encoding="utf-8", errors="replace")
        m_tail = re.search(r"(\n---\s*\n\s*##\s*5\..*)$", old_text, re.DOTALL)
        if m_tail:
            custom_tail = m_tail.group(1).rstrip()

    if archived_items:
        lines.append("| 编号 | 类型 | 标题 | 结项日期 | 结论 | 交付去向 | 归档卡片 |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for it in archived_items[:20]:  # 仅展示最近 20 条，防止索引过长
            c_date = it.get("closed_at") or "—"
            res = it.get("resolution") or "delivered"
            dest = it.get("destination") or "已完成"
            lines.append(f"| **{it['id']}** | `{it['type']}` | {it['title']} | {c_date} | {res} | {dest} | [{it['id']}](./{it['rel_path']}) |")
        if len(archived_items) > 20:
            lines.append(f"\n*(其余 {len(archived_items)-20} 条历史记录已隐藏，可查看 archive/ 目录)*")

    if custom_tail:
        lines.append(custom_tail)

    index_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"📊 成功刷新待办索引总表: {index_file.relative_to(root_path)}")


def cmd_sync_index(args):
    """刷新 index.md 命令入口"""
    root_path = Path(args.root).resolve()
    backlog_dir = find_backlog_dir(root_path)
    sync_index(backlog_dir, root_path)
    return 0


# ==============================================================================
# CLI 入口
# ==============================================================================

def main():
    # Windows 控制台缺省 cp936：入口处固化为 UTF-8，否则 emoji / 富符号 print 直接抛
    # UnicodeEncodeError（BK-0047 批次 A）。与仓库既有多脚本同源写法保持一致。
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="Backlog 形态 B (Issue-as-File) 自动化管理与可编程查询工具")
    parser.add_argument("--root", default="docs", help="文档根目录 (默认: docs)")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list
    p_list = subparsers.add_parser("list", help="提取与查询待办列表")
    p_list.add_argument("--status", help="按状态过滤 (active/in-progress/completed/rejected/all)")
    p_list.add_argument("--priority", help="按优先级过滤 (P0/P1/P2/P3)")
    p_list.add_argument("--type", help="按类型过滤 (Feature/TechDebt/Bug/Security 等)")
    p_list.add_argument("--format", choices=["table", "json", "id-only"], default="table", help="输出格式 (默认: table)")
    p_list.add_argument("--json", action="store_true", help="等同于 --format json")

    # get
    p_get = subparsers.add_parser("get", help="查看单条待办详情")
    p_get.add_argument("id", help="待办编号 (如 BK-0001)")
    p_get.add_argument("--json", action="store_true", help="输出完整 JSON")

    # create
    p_create = subparsers.add_parser("create", help="新建待办卡片文件")
    p_create.add_argument("title", help="待办标题")
    p_create.add_argument("--type", choices=VALID_TYPES, default="TechDebt", help="条目类型 (默认: TechDebt)")
    p_create.add_argument("--priority", choices=VALID_PRIORITIES, default="P2", help="优先级 (默认: P2)")
    p_create.add_argument("--trigger", help="触发时机与前置条件")
    p_create.add_argument("--source", action="append", help="来源追溯 (支持多次指定)")
    p_create.add_argument("--acceptance", action="append", help="验收准则 (支持多次指定)")
    p_create.add_argument("--description", help="详细问题描述")

    # close
    p_close = subparsers.add_parser("close", help="结项归档待办卡片")
    p_close.add_argument("id", help="待办编号 (如 BK-0001)")
    p_close.add_argument("--resolution", choices=["delivered", "superseded", "wontfix"], default="delivered", help="结项结论")
    p_close.add_argument("--destination", "--dest", help="交付物去向或关联 Commit / PR")
    p_close.add_argument("--version", help="归档版本或季度子目录 (默认: 当前季度如 2026-Q4)")

    # reopen
    p_reopen = subparsers.add_parser("reopen", help="重新激活已归档待办并移回 active/")
    p_reopen.add_argument("id", help="待办编号 (如 BK-0001)")

    # sync-index
    subparsers.add_parser("sync-index", help="扫描待办文件并重新生成 index.md")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if hasattr(args, "json") and args.json:
        args.format = "json"

    handlers = {
        "list": cmd_list,
        "get": cmd_get,
        "create": cmd_create,
        "close": cmd_close,
        "reopen": cmd_reopen,
        "sync-index": cmd_sync_index,
    }

    rc = handlers[args.command](args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
