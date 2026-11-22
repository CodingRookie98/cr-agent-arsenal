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
import contextlib
import os
import re
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple


EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")

# D1：HTML 注释（含跨行/未闭合形态）——托管标记等机器指令不得泄漏进机器地图描述
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
# D2：描述内 Markdown 链接/图片：[text](target "title")、![alt](target)
DESCRIPTION_LINK_PATTERN = re.compile(r"(!?)\[([^\]]*)\]\(\s*([^)\s]+)(\s+\"[^\"]*\")?\s*\)")
# D2：绝对协议链接（http(s)/mailto/…）保持原样，不参与 docs 根相对重写
# S-4：协议相对 URL（//host/path）同样是绝对地址，必须一并排除，否则会被改写成断链
ABSOLUTE_LINK_PATTERN = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.\-]*:|//)")


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


def strip_html_comments(content: str) -> str:
    """剥离 HTML 注释（D1）：含内部换行/缩进的跨行注释与未闭合注释一律消除。

    - 闭合注释整体替换为单个空格而非空串——避免跨行注释被删除后前后文本直接粘连；
    - 未闭合注释按「延伸至文末」处理，截断/半写文件不得把注释残余留在描述里。
    """
    without_comments = HTML_COMMENT_PATTERN.sub(" ", content)
    open_index = without_comments.find("<!--")
    if open_index != -1:
        without_comments = without_comments[:open_index]
    return without_comments


def normalize_description(text: str) -> str:
    """压缩描述中的连续空白（注释剥离与原文换行/缩进产生的多余空白）并去除首尾空白。"""
    return re.sub(r"\s+", " ", text).strip()


def _resolve_link_within_root(source_file: Path, root_dir: Path, path_part: str) -> Optional[str]:
    """把源文档内的链接路径解析为 docs 根相对路径；逃出根或指向根本身时返回 None（D2）。

    解析基准是**源文档所在目录**（不是 llms.txt 所在目录）；`/` 开头按 docs 根锚定；
    仅做词法归一（normpath），不做符号链接解析，保证「逃出 docs 根」判定与物理路径一致。
    """
    if not path_part:
        candidate = source_file
    else:
        decoded = urllib.parse.unquote(path_part)
        if decoded.startswith("/"):
            candidate = Path(os.path.normpath(os.path.join(str(root_dir), decoded.lstrip("/"))))
        else:
            candidate = Path(os.path.normpath(os.path.join(str(source_file.parent), decoded)))
    try:
        rel = candidate.relative_to(Path(os.path.normpath(str(root_dir))))
    except ValueError:
        return None
    if not rel.parts:
        return None
    # 仅转义会截断 Markdown 行内链接语法的字符（空白与括号），中文等路径字符保持可读原样
    return re.sub(r"[()\s]", lambda m: urllib.parse.quote(m.group(0)), rel.as_posix())


def rewrite_description_links(description: str, source_file: Path, root_dir: Path) -> str:
    """把描述内的相对 Markdown 链接重写为相对 docs 根的可达形态（D2）。

    llms.txt 位于 docs 根，链接解析基准随之改变：源文档里合法的 `../../docs/a.md`
    搬进 llms.txt 后会解析到 docs 根之外（实测 404）。因此：
      - 绝对协议链接（http(s)/mailto/…）逐字保留；
      - 相对 href 先按源文档所在目录解析，再相对 docs 根重写（纯片段链接解析为源文档自身）；
      - 解析结果逃出 docs 根时退化为纯文本（保留链接文字、去掉链接语法）。
    """
    def _replace(match: "re.Match") -> str:
        bang, text, target, title = match.groups()
        if ABSOLUTE_LINK_PATTERN.match(target):
            return match.group(0)
        path_part, separator, anchor = target.partition("#")
        rel_path = _resolve_link_within_root(source_file, root_dir, path_part)
        if rel_path is None:
            return text
        anchor_part = separator + anchor if separator else ""
        return f"{bang}[{text}]({rel_path}{anchor_part}{title or ''})"

    return DESCRIPTION_LINK_PATTERN.sub(_replace, description)


def extract_doc_info(file_path: Path, root_dir: Optional[Path] = None) -> Tuple[str, str]:
    """提取文档的标题与摘要描述。

    root_dir 非空时，描述内的相对 Markdown 链接会被重写为相对该根的形态（D2）；
    缺省 None 保持「逐字提取」语义，供不产出机器地图的调用方使用。
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return file_path.stem, ""

    content = strip_html_comments(content)  # D1：注释（含跨行）不得进入标题/描述
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

    description = normalize_description(description)
    if root_dir is not None:
        description = rewrite_description_links(description, file_path, root_dir)
    return title, description


SECTION_MAP_DIR = "_llms"

SECTION_ORDER = [
    ("proposals", "Proposals & RFCs (需求与设计孵化层)"),
    ("tutorials", "Tutorials (学习导向 / 新手上手教程)"),
    ("how-to", "How-To Guides (操作指南 / 问题与任务 SOP)"),
    ("reference", "Reference (技术参考 / 机器事实唯一真相源)"),
    ("explanation", "Explanation (深度剖析 / 系统架构与 ADR 决策)"),
    ("project", "Project Governance (工程演进 / 发布日志与待办)"),
]


def _collect_sections(root_dir: Path):
    """扫描并分组。返回 (sections, other_docs)。"""
    sections: Dict[str, List[Tuple[str, str, str]]] = {k: [] for k, _ in SECTION_ORDER}
    other_docs: List[Tuple[str, str, str]] = []
    for f in sorted(list(root_dir.rglob("*.md"))):
        if any(p in f.parts for p in ("node_modules", ".git", ".next", "dist", "build")):
            continue
        if in_evidence_archive(f, root_dir) or is_archive_path(f):
            continue
        rel_parts = f.relative_to(root_dir).parts
        # RFC-0006：分层产物落点目录与路由文件不进地图（否则自引用膨胀 / 路由被当知识）
        if rel_parts[0] == SECTION_MAP_DIR:
            continue
        if len(rel_parts) == 1:
            continue
        top_dir = rel_parts[0]
        title, desc = extract_doc_info(f, root_dir)
        rel_link = f.relative_to(root_dir).as_posix()
        if top_dir in sections:
            sections[top_dir].append((title, rel_link, desc))
        else:
            other_docs.append((title, rel_link, desc))
    return sections, other_docs


def _render_single(project_name: str, sections, other_docs) -> str:
    output_lines = [
        f"# {project_name} Machine-Readable Knowledge Base Map",
        "",
        "> 本文件遵循 llmstxt.org 规范，为 AI 智能体提供全景知识拓扑与物理文件导航地图。",
        "> 严禁凭空猜测路径，查阅具体模块前请通过下述相对链接精准索引对应文件。",
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
    return "\n".join(output_lines)


# S-4：除 http(s)/mailto/锚点外，任何 scheme（tel:/ftp:/data:…）与协议相对 URL（//host）
# 都不是仓库内相对路径，rebase 会把它们改写成静默断链。
_MD_LINK = re.compile(r"\]\((?!//|[a-zA-Z][a-zA-Z0-9+.-]*:|#)([^)\s]+)")


def _rebase_desc_links(desc: str) -> str:
    """子地图位于 _llms/ 下：描述里的相对链接（相对 docs 根）需补 ../ 才能解析。"""
    return _MD_LINK.sub(lambda m: "](../" + m.group(1).lstrip("./"), desc)


def _render_section_map(sec_title: str, docs) -> str:
    lines = [
        f"# {sec_title}",
        "",
        "> 本文件由 `generate-llms-txt.py --split` 生成，请勿手改。",
        "> 上级入口：[../llms.txt](../llms.txt)",
        "",
    ]
    for title, link, desc in docs:
        desc_text = f": {_rebase_desc_links(desc)}" if desc else ""
        # 子地图位于 _llms/ 下 ⇒ 条目链接需补 ../ 才能相对 docs 根解析
        lines.append(f"- [{title}](../{link}){desc_text}")
    lines.append("")
    return "\n".join(lines)


def _render_split_root(project_name: str, root_dir: Path, sections, other_docs) -> str:
    lines = [
        f"# {project_name} Machine-Readable Knowledge Base Map",
        "",
        "> 本文件是**象限级入口**：只回答「去哪找」，不罗列全部文档。",
        "> 读取顺序：本文件 → `_llms/<象限>.md` → 该象限 `index.md` → 正文。",
        "> 严禁凭空猜测路径；条目级清单在各象限子地图中。",
        "",
    ]
    blocks = list(SECTION_ORDER)
    if other_docs:
        blocks = blocks + [("__other__", "Other Documentation (其他文档)")]
    for sec_key, sec_title in blocks:
        docs = other_docs if sec_key == "__other__" else sections.get(sec_key, [])
        if not docs:
            continue
        map_name = "other" if sec_key == "__other__" else sec_key
        lines.append(f"## {sec_title} — {len(docs)} 篇")
        lines.append("")
        lines.append(f"- 全量清单：[{map_name}.md](./{SECTION_MAP_DIR}/{map_name}.md)")
        if sec_key != "__other__":
            quadrant_index = root_dir / sec_key / "index.md"
            if quadrant_index.is_file():
                lines.append(f"- 象限索引：[index.md](./{sec_key}/index.md)")
        lines.append("")
    return "\n".join(lines)


def build_llms_map(root_dir: Path, project_name: str = "Project", split: bool = False) -> Dict[str, str]:
    """构建机器地图：返回 {相对路径: 内容}（RFC-0006）。

    split=False 时只有 {"llms.txt": ...}，与既有单文件产物逐字节一致；
    split=True 时根只含象限入口，全量条目下沉 _llms/<section>.md。
    收录 0 篇时返回 {}（零覆盖守卫由调用方保持）。
    """
    root_dir = Path(root_dir)
    sections, other_docs = _collect_sections(root_dir)
    total = sum(len(v) for v in sections.values()) + len(other_docs)
    if total == 0:
        return {}
    if not split:
        return {"llms.txt": _render_single(project_name, sections, other_docs)}
    result: Dict[str, str] = {"llms.txt": _render_split_root(project_name, root_dir, sections, other_docs)}
    for sec_key, sec_title in SECTION_ORDER:
        docs = sections.get(sec_key, [])
        if docs:
            result[f"{SECTION_MAP_DIR}/{sec_key}.md"] = _render_section_map(sec_title, docs)
    if other_docs:
        result[f"{SECTION_MAP_DIR}/other.md"] = _render_section_map("Other Documentation (其他文档)", other_docs)
    return result


def generate_llms_txt(root_dir: Path, output_file: Path, project_name: str = "Project") -> int:
    """生成单文件 llms.txt（向后兼容入口）。返回收录文档数；0 篇时**不落盘**（BK-0023）。"""
    built = build_llms_map(root_dir, project_name=project_name, split=False)
    if not built:
        return 0
    content = built["llms.txt"]
    total_docs = content.count("\n- [")
    _atomic_write(output_file, content)
    print(f"✅ 机器可读地图成功生成至: {output_file} (共收录 {total_docs} 篇有效文档)")
    return total_docs


def _atomic_write(output_file: Path, content: str) -> None:
    """原子写盘（R1-5/21/22/24/27 的既有约束集中在此）。"""
    output_file.parent.mkdir(parents=True, exist_ok=True)  # R1-7：仅在确认落盘时才创建父目录
    # R1-5：先写临时文件再原子替换 —— 编码/写入失败不得留下 0 字节地图把双工具楔死
    # R1-21/22/24：用 mkstemp 生成**不可预测**的唯一临时名（与目标同目录）
    #   · 不可预测 ⇒ 无法预置同名软/硬链接劫持写入面（归档写保护之外的影子路径）
    #   · 唯一 ⇒ 并发同名输出不再互相消耗，也不会因失败残留固定名文件
    handle_fd, tmp_name = tempfile.mkstemp(
        dir=str(output_file.parent), prefix=output_file.name + ".", suffix=".tmp"
    )
    try:
        # R1-27：mkstemp 默认 0600，且 os.replace 会把模式位带到产物上 ⇒ 显式按 umask 放开
        # （必须走 fchmod(fd)：按名 chmod 会重新引入影子路径）
        os.fchmod(handle_fd, 0o666 & ~_current_umask())
        # 跨平台确定性（技能脚本 Python 统一化配套）：显式 newline="\n"，使产物在 Windows /
        #   POSIX 下同为 LF 字节流。否则 Windows 文本模式会把 \n 翻译为 CRLF，而
        #   audit-doc-health.py 的机器地图门禁是 read_bytes() 逐字节比对，两种平台各自自洽却
        #   与版本库里的 LF blob（`.gitattributes: * text=auto eol=lf`）不一致 —— 新克隆在 Windows
        #   上会因工作区得到 LF 而误判「机器地图与生成物不一致」。固定 LF 即让门禁跨平台同判。
        with os.fdopen(handle_fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_name, output_file)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


DEFAULT_PROJECT_NAME = "System"


def _current_umask() -> int:
    """读取当前进程 umask（临时置 0 后立即还原）。"""
    current = os.umask(0)
    os.umask(current)
    return current


def _can_roundtrip_as_identity(name: str) -> bool:
    """BK-0030 ②：名字写入 H1 后能否被逐字反解还原。

    行分隔符（LF/CR/U+2028/U+000B/U+0085…）会破坏 H1 的单行性，使生成物永久落在
    fail-closed 态（此后任何重生成都被拒、只能删除文件恢复），故在生成前即拒绝。
    """
    try:
        name.encode("utf-8")  # 写出半程：孤立代理（surrogateescape 读入的非法字节）不可编码
    except UnicodeEncodeError:
        return False
    # 载荷全部在 splitlines 半边：它识别的行分隔符远多于 "\n"（含 U+2028/U+2029/U+0085 等）；
    # H1 一旦被切成多行，读取端的 fullmatch 必然失败 ⇒ 生成物永久不可反解。
    return len(f"# {name} Machine-Readable Knowledge Base Map".splitlines()) == 1


def _resolve_outgoing_name(out_path: Path, requested: Optional[str]) -> str:
    """确定本次生成写入的项目名（BK-0030 身份写保护闸门）。

    - 无既有地图：用显式 --name，缺省 DEFAULT_PROJECT_NAME；
    - 既有地图身份可解析：未显式指定则**沿用既有身份**（正常重生成不改名）；
      显式指定且与既有身份相同则放行；不同则拒绝（改名须先移除既有地图）；
    - 既有地图存在但不可读、非合法 UTF-8 或 H1 不可反解：**fail-closed 拒绝**。
    """
    if requested is not None and not _can_roundtrip_as_identity(requested):
        print(
            "❌ 拒绝生成：项目名无法安全写入 H1 —— 含行分隔符或不可编码字节，"
            "写入后无法被逐字反解还原（会铸出永久不可修复的地图身份）；"
            "请改用不含换行/分隔符、且为合法 UTF-8 的项目名",
            file=sys.stderr,
        )
        sys.exit(1)

    if not out_path.exists():
        return requested if requested is not None else DEFAULT_PROJECT_NAME

    if not out_path.is_file():
        # R1-6：目录/设备等非规则文件不得进入无界读取面（/dev/urandom 会挂起）
        print(f"❌ 拒绝改写机器地图身份：既有落点不是常规文件（{out_path}）", file=sys.stderr)
        sys.exit(1)

    try:
        head_line = out_path.read_text(encoding="utf-8").splitlines()[0]
    except (OSError, IndexError, UnicodeDecodeError) as exc:
        print(
            f"❌ 拒绝改写机器地图身份：既有地图无法安全读取（{type(exc).__name__}: {exc}）",
            file=sys.stderr,
        )
        sys.exit(1)

    # R1-5：不 strip —— 行边界空白属身份的一部分，strip 会把「沿用」变成「归一化改写」
    match = re.fullmatch(r"# (.*) Machine-Readable Knowledge Base Map", head_line)
    if match is None:
        print(
            "❌ 拒绝改写机器地图身份：既有地图首行不符合标准 H1 格式"
            "（应形如 [# <项目名> Machine-Readable Knowledge Base Map]），无法确认其项目身份；"
            "请先人工核对；如确需重建，请先删除该文件再生成",
            file=sys.stderr,
        )
        sys.exit(1)

    existing = match.group(1)
    if requested is None or requested == existing:
        return existing

    print(
        f"❌ 拒绝改写机器地图身份：既有地图项目名为 {existing!r}，本次请求名为 {requested!r}；"
        f"如确需改名，请先移除既有地图文件，再以显式 --name 生成",
        file=sys.stderr,
    )
    sys.exit(1)

def main():
    # Windows 控制台缺省 cp936：入口处固化为 UTF-8，否则 emoji / 富符号 print 直接抛
    # UnicodeEncodeError（BK-0047 批次 A）。与仓库既有多脚本同源写法保持一致。
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="机器可读 llms.txt 自动化生成器")
    parser.add_argument("--root", default="docs", help="文档根目录 (默认 docs)")
    parser.add_argument("--output", default=None, help="输出路径 (缺省为 <root>/llms.txt，随 --root 派生)")
    parser.add_argument("--name", default=None, help="项目名称 (缺省：沿用既有地图身份；无既有地图时为 System)")
    parser.add_argument("--split", action="store_true",
                        help="分层输出（RFC-0006）：根只含象限入口，全量条目下沉 _llms/<section>.md")
    parser.add_argument("--max-root-bytes", type=int, default=None,
                        help="根机器地图字节上限（--split 下默认 8192；显式给 0 表示不限制）；超限不落盘并 exit 1")
    parser.add_argument("--check", action="store_true",
                        help="只校验磁盘内容与生成物是否一致，不写盘（一致 rc=0，不一致 rc=1）")

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

    project_name = _resolve_outgoing_name(out_path, args.name)
    built = build_llms_map(root_path, project_name=project_name, split=args.split)
    if not built:
        print(f"❌ 机器地图收录 0 篇文档，拒绝落盘（零覆盖守卫，避免覆盖既有 SSOT 地图）: {out_path}", file=sys.stderr)
        sys.exit(1)

    # AC-5：根体量门禁——超限不落盘，避免「精炼入口」再次退化为全集清单。
    # S-3：默认模式（无 --split）**不设限**，保持旧命令语义与 RFC §7 的回滚路径；
    # 分层模式默认 8192，显式传 0 可关闭。
    root_bytes = len(built["llms.txt"].encode("utf-8"))
    root_limit = args.max_root_bytes if args.max_root_bytes is not None else (8192 if args.split else 0)
    if root_limit and root_bytes > root_limit:
        print(
            f"❌ 根机器地图 {root_bytes} 字节 > 上限 {root_limit} 字节，拒绝落盘。"
            "请使用 --split 把条目下沉到 _llms/ 子地图。",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.check:
        # 只校验：根 + 全部子地图逐字节比对，多余/缺失均判不一致
        base = out_path.parent
        mismatched = []
        for rel, content in built.items():
            target = out_path if rel == "llms.txt" else base / rel
            if not target.is_file() or target.read_bytes() != content.encode("utf-8"):
                mismatched.append(rel)
        if args.split:
            section_dir = base / SECTION_MAP_DIR
            if section_dir.is_dir():
                expected = {Path(rel).name for rel in built if rel.startswith(SECTION_MAP_DIR + "/")}
                # SD-1：与 audit 同口径用 rglob——单层 glob 会让嵌套多余文件「audit 红 / --check 绿」
                for extra in sorted(section_dir.rglob("*.md")):
                    if extra.relative_to(section_dir).as_posix() not in expected:
                        mismatched.append(extra.relative_to(base).as_posix())
        if mismatched:
            # SD-3：回显实际基名，避免自定义 --output 时提示错位
            shown = [out_path.name if m == "llms.txt" else m for m in mismatched]
            print("❌ 机器地图与生成物不一致: " + ", ".join(shown), file=sys.stderr)
            sys.exit(1)
        print(f"✅ 机器地图校验通过（{len(built)} 个文件，根 {root_bytes} 字节）")
        sys.exit(0)

    # 写盘：根 + 子地图；split 模式下删除不再需要的子地图（空象限）
    # S-1：根文件必须落在 --output 指定的**完整路径**上（含自定义基名），
    # 不能恒写 <dir>/llms.txt —— 否则 --output 基名被静默丢弃，且身份闸门会读 A 写 B。
    base = out_path.parent
    written_files = []
    for rel, content in built.items():
        target = out_path if rel == "llms.txt" else base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(target, content)
        written_files.append(str(target))
    if args.split:
        section_dir = base / SECTION_MAP_DIR
        if section_dir.is_dir():
            expected = {Path(rel).name for rel in built if rel.startswith(SECTION_MAP_DIR + "/")}
            # SD-1：清理面同样递归，保证「照提示重生成」一定收敛
            for extra in sorted(section_dir.rglob("*.md")):
                if extra.relative_to(section_dir).as_posix() not in expected:
                    extra.unlink()
                    with contextlib.suppress(OSError):
                        extra.parent.rmdir()  # 顺手清理已空的嵌套目录（非空会抛，忽略）
    print(
        f"✅ 机器可读地图成功生成至: {out_path} "
        f"(根 {root_bytes} 字节；共 {len(written_files)} 个文件)"
    )


if __name__ == "__main__":
    main()
