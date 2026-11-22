#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-doc-health.py - 知识库全面健康度体检引擎
功能:
  1. 扫描整个文档目录，统计 Diátaxis 四象限与工程演进分布；
  2. 审计 Frontmatter 元数据控制头（版本号、标识、所有者、状态）合规率；
  3. 审计修订历史滑动窗口合规率（<= 5 条）；
  4. 审计全域物理断链与 404 错误；
  5. 探测孤儿文档（未被 index.md 或其他文档引用的孤立文件）；
  6. 审计 backlog.md 顶层条目 BK 编号合规（缺号/格式不合规/重号，违规直接阻断 PASS）；
  7. 支持 --compat 模式：探测既有瀑布老目录（requirements, design 等）并出具平滑迁移映射建议；
  8. 综合计算健康评分 (0-100 分)，出具结构化诊断报告；
  9. 真值轴（RFC-0005）：复用 check-doc-drift.py 的代码锚点漂移分析，输出独立 truth 分（默认 warn，不改变结构分语义）。
"""

import argparse
import contextlib
import io
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import importlib.util

# 交付凭据归档（RFC-0001 / R1-2）：审查报告以**逐字原文**归档（G1 红线——添加控制头会
# 改变内容并污染 SHA256 指纹），报告之间亦无 markdown 入链。故该目录豁免文档治理扫描，
# 否则每次真实审查交付都会单调侵蚀知识库健康度（外推约 11 次交付即跌破 80 分门槛）。
# 豁免语义登记见 docs/GOVERNANCE.md。
EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")
# RFC-0006：分层机器地图的子地图是**生成物**（无控制头、无入链），路由文件是**规则**而非知识；
# 二者都不参与元数据/孤儿/修订计分，但仍参与断链扫描（链接必须有效）。
GENERATED_MAP_DIR = "_llms"
ROUTER_FILE_NAME = "AGENTS.md"


def in_generated_map(path: Path, root_dir: Path) -> bool:
    try:
        rel = path.relative_to(root_dir)
    except ValueError:
        return False
    return rel.parts[:1] == (GENERATED_MAP_DIR,)


def is_router_file(path: Path, root_dir: Path) -> bool:
    return path.parent == root_dir and path.name == ROUTER_FILE_NAME


def in_evidence_archive(path: Path, root_dir: Path) -> bool:
    """判定路径是否落在交付凭据归档根内（<root>/project/reviews/**）。"""
    try:
        rel = path.relative_to(root_dir)
    except ValueError:
        return False
    return rel.parts[:2] == EVIDENCE_ARCHIVE_PARTS

# 动态加载同目录下带有短横线名称的兄弟脚本
_scripts_dir = Path(__file__).resolve().parent

def _load_sibling(filename: str, module_name: str):
    script_path = _scripts_dir / filename
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载兄弟模块: {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_links_mod = _load_sibling("check-doc-links.py", "check_doc_links")
_trim_mod = _load_sibling("trim-revision.py", "trim_revision")
_sync_mod = _load_sibling("check-doc-control-sync.py", "check_doc_control_sync")
_llms_mod = _load_sibling("generate-llms-txt.py", "generate_llms_txt")
_drift_mod = _load_sibling("check-doc-drift.py", "check_doc_drift")

scan_directory = _links_mod.scan_directory
process_markdown_file = _trim_mod.process_markdown_file
check_file_version_sync = _sync_mod.check_file_version_sync


DIATAXIS_CATEGORIES = {
    "tutorials": "🎓 教程象限 (Tutorials)",
    "how-to": "🛠️ 操作指南象限 (How-To Guides)",
    "reference": "📖 技术参考象限 (Reference)",
    "explanation": "💡 深度剖析象限 (Explanation)",
    "proposals": "💡 需求设计孵化层 (Proposals / RFC)",
    "project": "🚀 工程演进与管理 (Project Governance)",
}

LEGACY_CATEGORIES = {
    "requirements": "⚠️ 历史需求目录 (建议迁移至 reference/ 或 proposals/)",
    "design": "⚠️ 历史设计目录 (建议迁移至 explanation/architecture/)",
    "planning": "⚠️ 历史规划目录 (建议迁移至 explanation/analysis/ 或 project/)",
    "operations": "⚠️ 历史运维目录 (建议迁移至 how-to/ 或 tutorials/)",
}


PROJECT_NAME_MAX_LEN = 64
PROJECT_NAME_FALLBACK = "System"
REGEN_COMMAND = "generate-llms-txt.py --root docs --output docs/llms.txt"


def _is_safely_displayable(name: str) -> bool:
    """BK-0026：名字能否安全回显为**人读且可复制执行**的命令（全可打印、非空、不超长）。

    - D2-3：裸 ESC/OSC/BEL 等控制字符会穿透终端层（可篡改窗口标题/剪贴板并污染 CI 日志）；
    - D2-5：NUL 使提示命令在 execve 层不可执行，超长名把缺陷行膨胀；
    - 前后空格属可打印范畴，不做 strip（R1-10：strip 会把合法名 `" Foo "` 误诊为畸形）；
    - NBSP（U+00A0）等分隔符**不可打印**（实测 `'\xa0'.isprintable()` 为 False），会走 fail-closed 分支。
    """
    return bool(name) and len(name) <= PROJECT_NAME_MAX_LEN and all(ch.isprintable() for ch in name)


def truth_blockers(truth: Dict, truth_threshold: float, min_coverage: float) -> List[str]:
    """真值轴的唯一判定梯（BK-0028 口径：PASS 与 REJECT 由同一组判定产生）。

    打印侧与裁决侧都调用本函数，禁止各自重算——R1-4/R2 均指出过「两处复制判定梯」
    会导致同屏出现 PASS 文案与 REJECT 理由。
    """
    if truth.get("mode") != "require":
        return []
    if truth.get("unavailable"):
        return [f"真值轴不可判定（{truth['unavailable']}）"]
    reasons: List[str] = []
    if not truth.get("enabled"):
        reasons.append("真值轴未启用（无文档声明代码锚点）")
        return reasons
    # R2D-1：账本缺席/损坏 ⇒ 墓碑判据不成立，require 必须 fail-closed。
    if truth.get("baseline_status") in ("missing", "corrupt"):
        reasons.append(f"锚点基线不可用（{truth.get('baseline_status')}），墓碑判据不成立")
    elif truth.get("baseline_status") == "empty":
        reasons.append("锚点基线为空，墓碑判据不成立（保护不可得 ≠ 无违规）")
    if truth.get("removed_from_baseline"):
        reasons.append(f"锚点基线墓碑违规 {truth['removed_from_baseline']} 处（声明被删除/缩减）")
    if truth.get("coverage", 0.0) < min_coverage:
        reasons.append(
            f"声明覆盖率 {truth.get('coverage', 0.0):.1%} < 下限 {min_coverage:.1%}"
            "（删锚点不能替代修复漂移）"
        )
    if truth.get("freshness_score", 0.0) < truth_threshold:
        reasons.append(f"真值分 {truth.get('freshness_score')} < 门槛 {truth_threshold}")
    return reasons


def evaluate_verdict(
    res: Dict,
    threshold: float,
    truth_threshold: float = 12.0,
    min_coverage: float = 0.5,
) -> Tuple[bool, List[str]]:
    """PASS 条件与 REJECT 原因由**同一组判定**产生（BK-0028 D1-7）。

    此前 PASS 分支与 REJECT 分支各自重算同一批条件，两处漂移即出现「同一份体检结果既
    满足 PASS 又给出 REJECT 原因」的自相矛盾。现在只在这里判一次：`reasons` 为空即 PASS，
    非空即 REJECT，理由原样输出。
    """
    reasons: List[str] = []
    if res["total_score"] < threshold:
        reasons.append(f"得分 {res['total_score']} < 门槛 {threshold}")
    if res["total_link_errors"]:
        reasons.append(f"{res['total_link_errors']} 处断链")
    if res.get("version_drift_files"):
        reasons.append(f"{len(res['version_drift_files'])} 处版本漂移")
    if res["backlog_issues"]:
        reasons.append(f"{len(res['backlog_issues'])} 处 backlog 编号违规")
    if res.get("llms_map_issue"):
        reasons.append("机器地图不一致")
    if res.get("agents_md_issue"):
        reasons.append("路由文件不合规")
    status_issues = (res.get("doc_status") or {}).get("issues") or []
    if status_issues:
        reasons.append(f"{len(status_issues)} 处文档状态违规")
    # 真值轴（RFC-0005 §4.3）：默认 warn 不参与判定；require 模式下「未启用」同样阻断，
    # 否则一条都未声明的知识库会因为 enabled=False 而静默跳过真值门禁（等于自我豁免）。
    truth = res.get("truth") or {}
    reasons.extend(truth_blockers(truth, truth_threshold, min_coverage))
    return (not reasons), reasons


def _resolve_project_name(text: str) -> Tuple[str, bool]:
    """反解既有机器地图首行的项目名。

    返回 `(name, resolved)`：`resolved=False` 表示首行不符合标准 H1 格式，**名字不可信**
    （此时调用方不得据此下发任何 `--name` 命令 —— 否则会把地图身份静默改写为回落占位名，R1-1）。

    判定路径必须使用本函数返回的**未净化原名**（生成物 H1 用的就是它），保证逐字同源。
    """
    try:
        # BK-0031：严格解码已在调用方完成（非法 UTF-8 不得被 errors="replace" 归一化后
        # 当作可信身份）；此处只取首行。
        first_line = text.splitlines()[0]
    except IndexError:
        return PROJECT_NAME_FALLBACK, False
    # fullmatch + 贪婪捕获：名中含契约短语时不得被非贪婪截断（R1-3）；
    # 不 strip：与生成器同语义，避免审计下发一个生成器必然拒绝的 --name（DR1-2）
    match = re.fullmatch(r"# (.*) Machine-Readable Knowledge Base Map", first_line)
    if match is None:
        return PROJECT_NAME_FALLBACK, False
    return match.group(1), True


AGENTS_MD_MAX_LINES = 30
# 与 generate-llms-txt.py 的 --split 默认上限保持一致
LLMS_ROOT_MAX_BYTES = 8192
AGENTS_MD_REQUIRED = ("读取顺序", "硬约束")


def check_agents_md(root_dir: Path) -> str:
    """路由文件 docs/AGENTS.md 的门禁（RFC-0006 §4.4）。

    不存在 ⇒ 不判缺陷（可选文件，存量项目零破坏）；
    存在 ⇒ 行数 ≤ 30 且必须含「读取顺序」「硬约束」两个小节。
    """
    path = root_dir / "AGENTS.md"
    if not path.exists():
        return ""
    if not path.is_file():
        return f"路由文件落点不是常规文件（{path}）"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"路由文件读取失败: {exc}"
    lines = text.splitlines()
    if len(lines) > AGENTS_MD_MAX_LINES:
        return (
            f"路由文件 {path.name} 共 {len(lines)} 行 > 上限 {AGENTS_MD_MAX_LINES} 行"
            "（路由文件只写读取顺序与硬约束，知识应下沉到文档）"
        )
    missing = [sec for sec in AGENTS_MD_REQUIRED if sec not in text]
    if missing:
        return f"路由文件 {path.name} 缺少必需小节: {', '.join(missing)}"
    return ""


DOC_STATUS_VALUES = ("Active", "Contested", "Superseded")
CONTESTED_MAX_AGE_DAYS = 90
_DATE_IN_ROW = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _latest_revision_date(content: str) -> Optional[str]:
    """取修订历史表格中的**最新**日期（T-7：不能假定降序——RFC-0004 等真实文档是升序表）。"""
    lines = content.splitlines()
    in_rev = False
    dates: List[str] = []
    for line in lines:
        if re.match(r"^#+\s*(?:修订历史(?:记录)?|Revision\s*History)", line.strip(), re.I):
            in_rev = True
            continue
        if in_rev:
            if line.strip().startswith("|"):
                m = _DATE_IN_ROW.search(line)
                if m:
                    dates.append(m.group(1))
            elif line.strip() and dates:
                break
    return max(dates) if dates else None


def check_doc_status(
    root_dir: Path,
    now: Optional[str] = None,
    max_age_days: int = CONTESTED_MAX_AGE_DAYS,
) -> Dict:
    """文档状态机门禁（RFC-0007）。

    C-1 取值非法 / C-2 Superseded 的「取代于」缺失·失效·自指 / C-3 Active 带「取代于」⇒ 阻断；
    C-4（Active 引用 Superseded）/ C-5（Contested 超期）只进报告。
    """
    import datetime

    root_dir = Path(root_dir)
    today = datetime.date.fromisoformat(now) if now else datetime.date.today()
    counts = {v: 0 for v in DOC_STATUS_VALUES}
    contested: List[Dict] = []
    superseded: List[Dict] = []
    issues: List[str] = []
    warnings: List[str] = []
    active_docs: List[Path] = []

    docs = [
        f for f in sorted(root_dir.rglob("*.md"))
        if not any(p in f.parts for p in ("node_modules", ".git", "dist", "build"))
        and not in_evidence_archive(f, root_dir)
        and not in_generated_map(f, root_dir)
        and not is_router_file(f, root_dir)
        # T-10：只排除 project/backlog（待办卡片的 YAML status 是生命周期字段）；
        # 此前按绝对路径分量判断，会把任何检出路径含 backlog 的仓库整道门禁归零
        and not (
            len(f.relative_to(root_dir).parts) >= 2
            and f.relative_to(root_dir).parts[:2] == ("project", "backlog")
        )
    ]
    status_map: Dict[Path, str] = {}
    for f in docs:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta = parse_frontmatter(content)
        # 只认「文档状态」：backlog 卡片的 YAML `status: completed` 是生命周期字段，
        # 与文档状态机语义无关，不得混用（否则 47 张卡片会被误判为非法状态）。
        raw = (meta.get("文档状态") or "").strip()
        rel = f.relative_to(root_dir).as_posix()
        if not raw:
            status_map[f] = "Active"
            counts["Active"] += 1
            active_docs.append(f)
            continue
        if raw not in DOC_STATUS_VALUES:
            counts.setdefault("Unknown", 0)
            counts["Unknown"] = counts.get("Unknown", 0) + 1
            issues.append(f"{rel}: 文档状态取值非法（{raw}），只允许 {'/'.join(DOC_STATUS_VALUES)}")
            continue
        status_map[f] = raw
        counts[raw] += 1
        pointer = (meta.get("取代于") or meta.get("superseded-by") or "").strip()
        if raw == "Superseded":
            if not pointer:
                issues.append(f"{rel}: 状态为 Superseded 但缺少「取代于」")
            else:
                # T-5：允许锚点（./new.md#sec），与全库链接体系一致
                pointer_path = pointer.split("#", 1)[0]
                target = (f.parent / pointer_path).resolve()
                if target == f.resolve():
                    issues.append(f"{rel}: 「取代于」指向自身")
                elif pointer_path.startswith(("/", "\\")) or ".." in Path(pointer_path).parts:
                    # T-6：RFC 要求「仓库内相对路径」，绝对路径与越界写法一律阻断
                    issues.append(f"{rel}: 「取代于」必须是仓库内相对路径（{pointer}）")
                elif not target.is_file() or target.suffix != ".md":
                    issues.append(f"{rel}: 「取代于」目标不存在或不是 .md（{pointer}）")
                else:
                    superseded.append({"doc": rel, "by": pointer})
        else:
            if pointer:
                issues.append(f"{rel}: 状态为 {raw} 却出现「取代于」（仅 Superseded 允许）")
            if raw == "Contested":
                reason = (meta.get("争议点") or "").strip() or "未填写"
                revised = _latest_revision_date(content)
                age_days = None
                if revised:
                    try:
                        age_days = (today - datetime.date.fromisoformat(revised)).days
                    except ValueError:
                        age_days = None
                contested.append({"doc": rel, "reason": reason, "age_days": age_days})
            if raw == "Active":
                active_docs.append(f)

    # C-4：Active 文档引用 Superseded 文档 ⇒ 警告（不阻断）
    superseded_paths = {p.resolve() for p, s in status_map.items() if s == "Superseded"}
    for f in active_docs:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)", content):
            target = (f.parent / m.group(1)).resolve()
            if target in superseded_paths:
                warnings.append(
                    f"{f.relative_to(root_dir).as_posix()}: Active 文档引用了已被取代的 {m.group(1)}"
                )

    return {
        "counts": counts,
        "contested": contested,
        "superseded": superseded,
        "issues": issues,
        "warnings": warnings,
    }


def check_llms_map_consistency(root_dir: Path) -> str:
    """机器地图一致性门禁（BK-0025 / RFC-0006）：以注册命令语义重生成并与磁盘逐字节比对。

    split 模式（存在 _llms/ 目录）下比对根 + 全部子地图，多余/缺失均判漂移。
    返回缺陷描述；空串表示一致或本项不适用（未生成机器地图的项目不参与判定）。
    """
    llms_file = root_dir / "llms.txt"
    if not llms_file.exists():
        return ""
    if not llms_file.is_file():
        # R1-4：非规则文件（FIFO/字符设备/目录）不得进入无界读取面
        return f"机器地图落点不是常规文件（{llms_file}），无法安全比对"
    try:
        snapshot = llms_file.read_bytes()   # BK-0028 D1-8：单次快照，后续判定不再重读
    except OSError as exc:
        return f"机器地图一致性检查无法完成: {exc}"
    section_dir = root_dir / _llms_mod.SECTION_MAP_DIR
    is_split = section_dir.is_dir()
    try:
        snapshot_text = snapshot.decode("utf-8")
    except UnicodeDecodeError:
        project_name, name_resolved = PROJECT_NAME_FALLBACK, False
    else:
        project_name, name_resolved = _resolve_project_name(snapshot_text)
    try:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            built = _llms_mod.build_llms_map(root_dir, project_name=project_name, split=is_split)
        if not built:
            # R1-1：无可收录文档时本项不适用——否则修复命令必然 rc=1，形成不可修复的死胡同
            return ""
        # RFC-0006：split 模式下逐文件比对根 + 全部子地图；多余/缺失均判漂移
        mismatched: List[str] = []
        for rel, content in built.items():
            target = root_dir / rel
            try:
                same = target.is_file() and target.read_bytes() == content.encode("utf-8")
            except OSError:
                same = False
            if not same:
                mismatched.append(rel)
        if is_split:
            # SD-6：根体量超限也计入缺陷（契约 §4.5 此前只在生成器侧实现）
            if len(snapshot) > LLMS_ROOT_MAX_BYTES:
                mismatched.append(f"根体量 {len(snapshot)} 字节 > {LLMS_ROOT_MAX_BYTES}")
            expected = {
                Path(rel).name for rel in built
                if rel.startswith(_llms_mod.SECTION_MAP_DIR + "/")
            }
            # S-5：递归扫描——嵌套子目录里的 .md 同样是「多余」，否则 _llms/sub/ 会成为静默区
            # SD-5：符号链接目录不会被 rglob 跟随，显式检测并判为多余（防静默区）
            for link in sorted(section_dir.rglob("*")):
                if link.is_symlink() and link.is_dir():
                    mismatched.append(link.relative_to(root_dir).as_posix() + "（符号链接目录）")
            for extra in sorted(section_dir.rglob("*.md")):
                rel_extra = extra.relative_to(root_dir).as_posix()
                if rel_extra not in {
                    f"{_llms_mod.SECTION_MAP_DIR}/{name}" for name in expected
                }:
                    mismatched.append(rel_extra)
        if mismatched:
            detail = "、".join(mismatched[:5]) + ("…" if len(mismatched) > 5 else "")
            # R1-1：反解不可信或名字不可安全回显时，**绝不下发任何 --name 命令**
            # （否则用户照做会把地图 H1 静默改写为占位名或截断名，项目身份在 SSOT 中丢失）
            if not name_resolved:
                return (
                    f"机器地图与生成物不一致（{detail}），且既有地图首行不符合标准 H1 格式"
                    "（应形如 `# <项目名> Machine-Readable Knowledge Base Map`），无法反解项目名。"
                    "**请勿直接重新生成**：缺省项目名会把地图身份静默改写；"
                    "如需重建，请**先移除既有地图文件**，再以显式 --name 重新生成后再提交"
                )
            if not _is_safely_displayable(project_name):
                return (
                    f"机器地图与生成物不一致（{detail}），且既有地图首行项目名不可安全回显"
                    "（为空、含不可打印字符或超长）。既有首行格式合法，直接**以注册命令重新生成即可无损修复**"
                    "（生成器会沿用既有身份，不会改写它）；无需移除地图。"
                )
            # D1-4：项目名源自仓库可控内容，须 shell 转义后再拼入提示命令（防命令注入）
            # D2-4：以 --name=<value> 赋值形式拼装，使 `-` 开头的名字同样可执行（否则 argparse rc=2）
            quoted_name = shlex.quote(project_name)
            split_flag = " --split" if is_split else ""
            return (
                f"机器地图与生成物不一致（{detail}）—— 请以 --name={quoted_name} 运行 "
                + REGEN_COMMAND + split_flag + " 重新生成后再提交"
            )
    except Exception as exc:  # noqa: BLE001 - 门禁不得因单点异常中断整体体检
        return f"机器地图一致性检查无法完成: {exc}"
    return ""




def _iter_unfenced_lines(lines, limit: int):
    """T-4：跳过围栏代码块内的行——示例/模板片段不得被当作真声明。"""
    in_fence = False
    for idx, line in enumerate(lines[:limit]):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield idx, line


def parse_frontmatter(content: str) -> Dict[str, str]:
    """解析文档头部的 Frontmatter 或文档控制信息块。

    T-2：YAML 与引用块**并存时两者都解析**（此前 YAML 命中即早退，引用块被整体遮蔽）。
    T-4：围栏代码块内的行不参与解析。
    """
    metadata = {}
    # 模式 A: YAML Frontmatter (--- ... ---)
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if yaml_match:
        for line in yaml_match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                metadata[k.strip().lower()] = v.strip()

    # 模式 B: 引用块元数据 (支持 > **文档控制信息** 或直接 > **文档标识** / > **文档版本**)
    for _, line in _iter_unfenced_lines(content.splitlines(), 80):
        trimmed = line.strip()
        if trimmed.startswith(">"):
            clean = re.sub(r"^[>\s\-*]+", "", trimmed).strip()
            if ":" in clean or "：" in clean:
                sep = ":" if ":" in clean else "："
                k, v = clean.split(sep, 1)
                k_clean = re.sub(r"[*_`]", "", k).strip().lower()
                metadata.setdefault(k_clean, v.strip())

    # 模式 C: 表格型元数据 (| **文档标识** | DR-xxx | 或 | 文档标识 | ... |)
    # T-3：白名单补齐文档状态机三字段，否则表格形态的状态声明完全失明
    if (
        "文档标识" in content or "当前版本" in content or "version" in content.lower()
        or "文档版本" in content or "文档状态" in content
    ):
        for m in re.finditer(r"\|\s*(?:\*\*)?([^|\n*]+?)(?:\*\*)?\s*\|\s*([^|\n]+?)\s*\|", content):
            k_raw = m.group(1).strip().lower()
            v_raw = m.group(2).strip()
            if k_raw in (
                "文档标识", "当前版本", "规范版本", "文档版本", "version", "id", "文档所有者", "生效日期",
                "文档状态", "取代于", "争议点",
            ):
                metadata.setdefault(k_raw, v_raw)

    return metadata


def audit_backlog(root_dir: Path, all_md_files: List[Path]) -> Tuple[List[str], List[str], Dict]:
    """审计 Backlog 体系（同时支持形态 B 目录分片卡片式与形态 A 单文件紧凑行）。"""
    backlog_issues: List[str] = []
    backlog_warnings: List[str] = []
    metrics: Dict = {
        "has_backlog": False,
        "mode": None,  # "form_b" 或 "form_a"
        "location": None,
        "active_total": 0,
        "in_progress": 0,
        "planned": 0,
        "hot_completed_count": 0,
        "cold_archived_total": 0,
        "priority_counts": {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "other": 0},
        "type_counts": {},
    }

    global_seen_ids: Dict[str, Tuple[str, int]] = {}

    # 1. 优先探测形态 B (Issue-as-File 目录分片拓扑)
    form_b_dir = None
    for cand in [
        root_dir / "docs" / "project" / "backlog",
        root_dir / "project" / "backlog",
        root_dir / "backlog",
    ]:
        if cand.exists() and cand.is_dir() and ((cand / "active").exists() or (cand / "archive").exists() or (cand / "index.md").exists()):
            form_b_dir = cand
            break

    if form_b_dir:
        metrics["has_backlog"] = True
        metrics["mode"] = "form_b"
        metrics["topology"] = "form_b"
        rel_b = str(form_b_dir.relative_to(root_dir))
        metrics["location"] = rel_b

        active_dir = form_b_dir / "active"
        archive_dir = form_b_dir / "archive"
        index_file = form_b_dir / "index.md"

        if not index_file.exists():
            backlog_warnings.append(
                f"{rel_b}/index.md 索引文件不存在，建议运行 `python3 scripts/manage-backlog.py sync-index` 生成索引总表"
            )

        # 扫描 active/ 目录
        if active_dir.exists():
            for f in sorted(active_dir.rglob("*.md")):
                if f.name == "index.md":
                    continue
                rel_f = str(f.relative_to(root_dir))
                content = f.read_text(encoding="utf-8", errors="replace")
                meta = parse_frontmatter(content)

                # 校验 ID
                bk_id = meta.get("id") or ""
                m_file = re.match(r"^BK-(\d{4})", f.name)
                if not bk_id and m_file:
                    bk_id = f"BK-{m_file.group(1)}"

                m_id = re.match(r"^BK-(\d{4})$", bk_id)
                if not m_id:
                    backlog_issues.append(f"{rel_f} 缺少合规的 BK-XXXX 编号 (当前 id: '{bk_id}')")
                else:
                    id_num = m_id.group(1)
                    if id_num in global_seen_ids:
                        prev_file, _ = global_seen_ids[id_num]
                        backlog_issues.append(f"{rel_f} 编号 BK-{id_num} 与 {prev_file} 重复")
                    else:
                        global_seen_ids[id_num] = (rel_f, 1)

                    if not f.name.startswith(f"BK-{id_num}"):
                        backlog_warnings.append(f"{rel_f} 文件名未以编号 BK-{id_num} 开头")

                # 校验状态
                st = (meta.get("status") or "active").lower()
                if st in ("completed", "rejected", "closed"):
                    backlog_warnings.append(
                        f"{rel_f} 状态为 '{st}'，滞留在 active/ 目录中，建议运行 `manage-backlog.py close {bk_id}` 归档至 archive/"
                    )
                    metrics["hot_completed_count"] += 1
                else:
                    metrics["active_total"] += 1
                    if st == "in-progress":
                        metrics["in_progress"] += 1
                    else:
                        metrics["planned"] += 1

                # 提取优先级与类型
                pri = (meta.get("priority") or "P2").upper()
                if pri in ("P0", "P1", "P2", "P3"):
                    metrics["priority_counts"][pri] += 1
                else:
                    metrics["priority_counts"]["other"] += 1

                tp = (meta.get("type") or "TechDebt").capitalize()
                metrics["type_counts"][tp] = metrics["type_counts"].get(tp, 0) + 1

        # 扫描 archive/ 目录
        if archive_dir.exists():
            for f in sorted(archive_dir.rglob("*.md")):
                if f.name == "index.md":
                    continue
                rel_f = str(f.relative_to(root_dir))
                content = f.read_text(encoding="utf-8", errors="replace")
                meta = parse_frontmatter(content)

                bk_id = meta.get("id") or ""
                m_file = re.match(r"^BK-(\d{4})", f.name)
                if not bk_id and m_file:
                    bk_id = f"BK-{m_file.group(1)}"

                m_id = re.match(r"^BK-(\d{4})$", bk_id)
                if not m_id:
                    backlog_issues.append(f"{rel_f} 归档卡片缺少合规的 BK-XXXX 编号")
                else:
                    id_num = m_id.group(1)
                    if id_num in global_seen_ids:
                        prev_file, _ = global_seen_ids[id_num]
                        backlog_issues.append(f"{rel_f} 编号 BK-{id_num} 与 {prev_file} 重复")
                    else:
                        global_seen_ids[id_num] = (rel_f, 1)

                metrics["cold_archived_total"] += 1

        return backlog_issues, backlog_warnings, metrics

    # 2. 回退探测形态 A (单文件 backlog.md)
    top_checkbox = re.compile(r"^- \[[ xX]\]\s+")
    numbered_checkbox = re.compile(r"^- \[[ xX]\]\s+(?:\*\*)?BK-(\d{4})\b(?:\*\*)?")
    pri_pattern = re.compile(r"\[(?:Pri|Priority):\s*(P[0-3])\]", re.I)
    type_pattern = re.compile(r"\[(?:Type):\s*([a-zA-Z]+)\]", re.I)

    hot_backlog = None
    archive_backlogs: List[Path] = []

    for f in all_md_files:
        if f.name == "backlog.md":
            hot_backlog = f
        elif f.name.startswith("backlog-") and f.name.endswith(".md"):
            archive_backlogs.append(f)

    if not hot_backlog and not archive_backlogs:
        return backlog_issues, backlog_warnings, metrics

    metrics["has_backlog"] = True
    metrics["mode"] = "form_a"

    if hot_backlog:
        rel_hot = str(hot_backlog.relative_to(root_dir))
        metrics["location"] = rel_hot
        lines = hot_backlog.read_text(encoding="utf-8", errors="replace").splitlines()

        if len(lines) > 300:
            backlog_warnings.append(
                f"{rel_hot} 物理行数达 {len(lines)} 行（超过 300 行红线），请及时将已结项条目归档至 docs/project/archive/"
            )

        current_section = ""
        for lineno, line in enumerate(lines, 1):
            trimmed = line.strip()
            if trimmed.startswith("## "):
                current_section = trimmed[3:].strip()
                if "已关闭" in current_section or "已完成" in current_section:
                    backlog_warnings.append(
                        f"{rel_hot}:{lineno} 发现「{current_section}」分区：根据冷热分离规范，已关闭条目应迁出至 docs/project/archive/，热区仅保留进行中与计划中"
                    )
                continue

            if not top_checkbox.match(line):
                continue

            is_completed = line.startswith("- [x]") or line.startswith("- [X]")
            m = numbered_checkbox.match(line)
            if not m:
                backlog_issues.append(
                    f"{rel_hot}:{lineno} 顶层条目缺 BK-XXXX 编号前缀: {line.strip()[:40]}"
                )
                continue

            bk_id = m.group(1)
            if bk_id in global_seen_ids:
                prev_file, prev_line = global_seen_ids[bk_id]
                backlog_issues.append(
                    f"{rel_hot}:{lineno} BK-{bk_id} 与 {prev_file}:{prev_line} 编号重复"
                )
            else:
                global_seen_ids[bk_id] = (rel_hot, lineno)

            if is_completed:
                metrics["hot_completed_count"] += 1
                backlog_warnings.append(
                    f"{rel_hot}:{lineno} BK-{bk_id} 为已完成状态 `[x]`，滞留在热区文档中，建议迁入 docs/project/archive/"
                )
            else:
                metrics["active_total"] += 1
                if "进行中" in current_section or "In Progress" in current_section:
                    metrics["in_progress"] += 1
                else:
                    metrics["planned"] += 1

                pri_m = pri_pattern.search(line)
                if pri_m:
                    pri_val = pri_m.group(1).upper()
                    metrics["priority_counts"][pri_val] = metrics["priority_counts"].get(pri_val, 0) + 1
                else:
                    metrics["priority_counts"]["other"] += 1

                type_m = type_pattern.search(line)
                if type_m:
                    type_val = type_m.group(1).capitalize()
                    metrics["type_counts"][type_val] = metrics["type_counts"].get(type_val, 0) + 1
                else:
                    metrics["type_counts"]["Unclassified"] = metrics["type_counts"].get("Unclassified", 0) + 1

        if metrics["active_total"] > 60:
            backlog_warnings.append(
                f"{rel_hot} 活跃条目达 {metrics['active_total']} 条（超过 60 条预警线），请定期执行 Backlog 理牌与修剪"
            )

    for cold_f in archive_backlogs:
        rel_cold = str(cold_f.relative_to(root_dir))
        for lineno, line in enumerate(
            cold_f.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if not top_checkbox.match(line):
                continue
            m = numbered_checkbox.match(line)
            if not m:
                backlog_issues.append(
                    f"{rel_cold}:{lineno} 归档条目缺 BK-XXXX 编号前缀: {line.strip()[:40]}"
                )
                continue
            bk_id = m.group(1)
            if bk_id in global_seen_ids:
                prev_file, prev_line = global_seen_ids[bk_id]
                backlog_issues.append(
                    f"{rel_cold}:{lineno} BK-{bk_id} 与 {prev_file}:{prev_line} 编号重复"
                )
            else:
                global_seen_ids[bk_id] = (rel_cold, lineno)

            metrics["cold_archived_total"] += 1

    return backlog_issues, backlog_warnings, metrics


def audit_health(
    root_dir: Path,
    compat_mode: bool = False,
    truth_mode: str = "warn",
    max_age_days: int = 180,
    repo_path: Optional[Path] = None,
) -> Dict:
    """执行全面的健康度体检"""
    all_md_files = [
        f for f in root_dir.rglob("*.md")
        if not any(p in f.parts for p in ("node_modules", ".git", ".next", "dist", "build"))
        and not in_evidence_archive(f, root_dir)
        and not in_generated_map(f, root_dir)
        and not is_router_file(f, root_dir)
    ]

    total_files = len(all_md_files)
    if total_files == 0:
        return {"error": f"未在 {root_dir} 下找到任何 Markdown 文档"}

    # 1. 拓扑分类统计
    category_counts: Dict[str, List[Path]] = {cat: [] for cat in DIATAXIS_CATEGORIES}
    legacy_counts: Dict[str, List[Path]] = {cat: [] for cat in LEGACY_CATEGORIES}
    root_level_docs = []

    for f in all_md_files:
        rel_parts = f.relative_to(root_dir).parts
        if len(rel_parts) == 1:
            root_level_docs.append(f)
            continue
        top_dir = rel_parts[0]
        if top_dir in DIATAXIS_CATEGORIES:
            category_counts[top_dir].append(f)
        elif top_dir in LEGACY_CATEGORIES:
            legacy_counts[top_dir].append(f)
        else:
            category_counts.setdefault("other", []).append(f)

    # 2. 控制信息基线检查
    valid_meta_files = 0
    missing_meta_files = []
    version_drift_files = []

    # 3. 修订历史检查
    overflow_rev_files = []

    # 4. 收集出链目标，计算引用图与孤儿文档
    referenced_files: Set[Path] = set()
    link_pattern = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")

    for f in all_md_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(content)
        # 判定控制元数据是否合规：至少包含 version 或 当前版本
        # 形态 B 待办卡片判定 (backlog/active 或 backlog/archive 下的卡片，以 BK-XXXX 为标识)
        is_backlog_card = ("backlog" in f.parts and ("active" in f.parts or "archive" in f.parts))
        if is_backlog_card:
            has_bk_id = any(k in meta for k in ("id", "文档标识", "标识")) and bool(re.match(r"^BK-\d{4}", str(meta.get("id") or meta.get("文档标识") or "")))
            if has_bk_id:
                valid_meta_files += 1
            else:
                missing_meta_files.append(f)
            continue

        has_version = any(k in meta for k in ("version", "当前版本", "规范版本", "文档版本", "版本"))
        # "决策编号" 为 MADR 3.0 的 ADR 标识字段（见 references/adr-specification.md），与 Diátaxis 文档的"文档标识"等价
        has_id = any(k in meta for k in ("id", "文档标识", "标识", "name", "doc_id", "决策编号"))
        is_archived = "archived" in f.parts
        if (has_version and has_id) or (compat_mode and is_archived):
            valid_meta_files += 1
        else:
            missing_meta_files.append(f)

        # 控制头版本与修订历史最新行版本一致性校验
        is_synced, h_ver, r_ver, sync_err = check_file_version_sync(f)
        if not is_synced and sync_err:
            version_drift_files.append((f, h_ver, r_ver, sync_err))

        # 修订历史检查
        overflow, count, _ = process_markdown_file(f, max_keep=5, fix=False)
        if overflow:
            overflow_rev_files.append((f, count))

        # 解析链接目标
        for m in link_pattern.finditer(content):
            target = m.group(2).strip().split("#")[0].split(" ")[0]
            if not target or re.match(r"^(https?://|mailto:|javascript:|ftp:)", target, re.I):
                continue
            try:
                resolved = (f.parent / target).resolve()
                if resolved.exists() and resolved.is_file() and resolved.suffix == ".md":
                    referenced_files.add(resolved)
            except Exception:
                pass

    # 孤儿文档判定。三类排除，各有理由：
    #   1) **入口象限**（<root> 根级文档）不参与（BK-0019）：DA-4 明令该象限不生成托管索引，
    #      其文档在结构上不可能被机械登记；把规范强制的结构计入缺陷是对同一决策的双重惩罚。
    #      代价：根级真孤儿不再由本指标发现——根级本应只有入口文档，其健康度由链接完整率
    #      与人工评审覆盖（已登记于 GOVERNANCE §3）。
    #   2) 导航入口文件名（index / README / GOVERNANCE / llms.txt）不是叶子文档；
    #   3) 归档区不参与（冷区凭据按签发时点固化）。
    orphan_docs = []
    for f in all_md_files:
        if f.parent == root_dir:
            continue
        if f.name in ("index.md", "README.md", "GOVERNANCE.md", "llms.txt"):
            continue
        if "archive" in f.parts or "archived" in f.parts:
            continue
        if f not in referenced_files:
            orphan_docs.append(f)

    # 4.5 Backlog 体系与编号合规检查（支持热区 backlog.md 与冷区 archive/backlog-*.md）
    backlog_issues, backlog_warnings, backlog_metrics = audit_backlog(root_dir, all_md_files)

    # 5. 断链扫描
    _, total_link_errors, file_link_errors = scan_directory(
        root_dir=root_dir,
        target_dirs=[],
        strict_md=True,
        verbose=False,
    )

    # 计算各项得分 (满分 100)
    # 权重: 链接完整率 (35分), 元数据基线率 (25分), 修订历史合规率 (20分), 孤儿文档率 (10分), 架构规范度 (10分)
    link_score = 35 if total_link_errors == 0 else max(0, 35 - total_link_errors * 5)
    meta_score = (valid_meta_files / total_files) * 25
    rev_score = ((total_files - len(overflow_rev_files)) / total_files) * 20
    orphan_score = ((total_files - len(orphan_docs)) / total_files) * 10
    
    # 架构规范度：在标准模式下若存在大量 legacy 目录扣分，compat 模式下给予豁免
    legacy_count = sum(len(v) for v in legacy_counts.values())
    if compat_mode:
        arch_score = 10
    else:
        arch_score = 10 if legacy_count == 0 else max(0, 10 - legacy_count * 2)

    total_score = round(link_score + meta_score + rev_score + orphan_score + arch_score, 1)

    # 真值轴（RFC-0005 §4.3）：与结构分**并行**，不合并进 total_score。零声明时
    # enabled=False 且分数为 0——「未启用」不得被读成「满分」。
    truth_unavailable = None
    repo_root = repo_path if repo_path is not None else root_dir.parent
    try:
        if _drift_mod.is_shallow_repo(repo_root):
            truth_unavailable = "shallow repository（历史提交时间不可得，需 fetch-depth: 0）"
    except Exception:
        truth_unavailable = "git 探测失败"
    truth_raw = _drift_mod.analyze(
        root_dir,
        repo=repo_root if truth_unavailable is None else None,
        max_age_days=max_age_days,
        baseline_path=root_dir / _drift_mod.DEFAULT_BASELINE_NAME,
    )
    truth_block = {
        "mode": truth_mode,
        "unavailable": truth_unavailable,
        "removed_from_baseline": len(truth_raw.get("removed_from_baseline") or []),
        "baseline_docs": truth_raw.get("baseline_docs", 0),
        "baseline_status": truth_raw.get("baseline_status", "disabled"),
        "enabled": truth_raw["enabled"],
        "declared": truth_raw["declared"],
        "total_docs": truth_raw["total_docs"],
        "coverage": truth_raw["coverage"],
        "fresh": len(truth_raw["fresh"]),
        "drifted": len(truth_raw["drifted"]),
        "missing_anchor": len(truth_raw["missing_anchor"]),
        "stale": len(truth_raw["stale"]),
        "unverified": len(truth_raw["unverified"]),
        "freshness_score": truth_raw["freshness_score"],
        "max_age_days": truth_raw["max_age_days"],
        "drift_docs": [item["doc"] for item in truth_raw["drifted"]],
        "missing_anchor_docs": [item["doc"] for item in truth_raw["missing_anchor"]],
        # R3D-4：invalid 锚点（散文/无法核验）必须在 audit 的 truth 块可见，
        # 否则「只看 audit 报告」的评审者看不到这类声明被静默排除。
        "invalid": sum(1 for item in truth_raw["docs"] if item.get("invalid_anchors")),
        "invalid_docs": [item["doc"] for item in truth_raw["docs"] if item.get("invalid_anchors")],
    }

    return {
        "total_files": total_files,
        "total_score": total_score,
        "category_counts": category_counts,
        "legacy_counts": legacy_counts,
        "root_docs": root_level_docs,
        "valid_meta_files": valid_meta_files,
        "missing_meta_files": missing_meta_files,
        "version_drift_files": version_drift_files,
        "overflow_rev_files": overflow_rev_files,
        "total_link_errors": total_link_errors,
        "file_link_errors": file_link_errors,
        "orphan_docs": orphan_docs,
        "backlog_issues": backlog_issues,
        "backlog_warnings": backlog_warnings,
        "backlog_metrics": backlog_metrics,
        "llms_map_issue": check_llms_map_consistency(root_dir),
        "agents_md_issue": check_agents_md(root_dir),
        "doc_status": check_doc_status(root_dir),
        "truth": truth_block,
        "scores": {
            "link_score": round(link_score, 1),
            "meta_score": round(meta_score, 1),
            "rev_score": round(rev_score, 1),
            "orphan_score": round(orphan_score, 1),
            "arch_score": round(arch_score, 1),
        },
    }


def main():
    # Windows 控制台缺省 cp936：入口处固化为 UTF-8，否则 emoji / 富符号 print 直接抛
    # UnicodeEncodeError（BK-0047 批次 A）。与仓库既有多脚本同源写法保持一致。
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="知识库全面健康度体检引擎")
    parser.add_argument("--root", default="docs", help="文档根目录 (默认为 docs)")
    parser.add_argument("--compat", action="store_true", help="启用既有项目老目录兼容模式")
    parser.add_argument("--threshold", type=float, default=80.0, help="合格通过分数门槛 (默认 80.0)")
    parser.add_argument("--truth", choices=["off", "warn", "require"], default="warn",
                        help="真值轴模式: off 不报告 / warn 只报告(默认) / require 低于门槛即 REJECT")
    parser.add_argument("--truth-threshold", type=float, default=12.0, help="真值分门槛，满分 15 (默认 12.0)")
    parser.add_argument("--min-coverage", type=float, default=0.5,
                        help="require 模式下的锚点声明覆盖率下限 (默认 0.5，防「删锚点洗绿」)")
    parser.add_argument("--max-age-days", type=int, default=180, help="复核时效上限（天，0 表示不检查）")
    parser.add_argument("--repo", default=None,
                        help="仓库根（真值轴锚点基准；默认取 --root 的父目录）")

    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    if not root_path.exists():
        print(f"❌ 错误: 目标文档目录不存在: {root_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🏥 启动知识库全面健康度体检: 根目录={root_path} ...")
    res = audit_health(
        root_path,
        compat_mode=args.compat,
        truth_mode=args.truth,
        max_age_days=args.max_age_days,
        repo_path=Path(args.repo).resolve() if args.repo else None,
    )
    if "error" in res:
        print(f"❌ {res['error']}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"📊 知识库健康体检综合诊断报告")
    print(f"   总得分: {res['total_score']} / 100 分  (通过门槛: {args.threshold}分)")
    print("=" * 60)

    # 1. 维度细分评分
    scores = res["scores"]
    print("\n📈 [各项细分评分]:")
    print(f"   * 物理链接与断链防护: {scores['link_score']} / 35 分 (断链数: {res['total_link_errors']})")
    print(f"   * 控制信息元数据基线: {scores['meta_score']} / 25 分 (合规文档: {res['valid_meta_files']}/{res['total_files']})")
    print(f"   * 修订历史滑动窗口:   {scores['rev_score']} / 20 分 (超标文档: {len(res['overflow_rev_files'])}/{res['total_files']})")
    print(f"   * 孤儿文档引用度:     {scores['orphan_score']} / 10 分 (孤立文档: {len(res['orphan_docs'])}/{res['total_files']})")
    print(f"   * Diátaxis 架构规范:  {scores['arch_score']} / 10 分")

    # 1.5 真值轴（独立双轴，不并入 total_score）
    truth = res.get("truth") or {}
    if truth.get("mode") != "off":
        print("\n🎯 [真值轴 · 代码锚点漂移]:")
        print(f"   * 模式: {truth.get('mode')}（结构分 {res['total_score']} 分不含真值分）")
        print(
            f"   * 声明覆盖: {truth.get('declared', 0)}/{truth.get('total_docs', 0)} 篇"
            f" ({truth.get('coverage', 0.0):.1%})｜fresh {truth.get('fresh', 0)}"
            f"｜drifted {truth.get('drifted', 0)}｜missing {truth.get('missing_anchor', 0)}"
            f"｜stale {truth.get('stale', 0)}｜unverified {truth.get('unverified', 0)}"
        )
        if not truth.get("enabled"):
            print("   ⚠️  未启用：无文档声明「代码锚点」，真值分不颁发（0.0/15 而非满分）")
        if truth.get("unavailable"):
            print(f"   ⛔ 不可判定：{truth['unavailable']}（不编造漂移数字）")
        if truth.get("baseline_status") in ("missing", "corrupt"):
            print(
                f"   ⛔ 锚点基线不可用（{truth['baseline_status']}）：墓碑判据不成立，",
                "请运行 check-doc-drift.py --write-baseline 重建并提交该账本",
            )
        if truth.get("mode") == "require":
            print(
                f"   * require 口径: 覆盖率下限 {args.min_coverage:.1%}"
                f"｜真值分门槛 {args.truth_threshold}/15（仅当真值不达标时进入阻断理由，正常态不打印「完美」）"
            )
        print(f"   * 真值分: {truth.get('freshness_score', 0.0)} / 15")
        for name in (truth.get("missing_anchor_docs") or [])[:5]:
            print(f"      - [missing_anchor] {name}")
        for name in (truth.get("drift_docs") or [])[:5]:
            print(f"      - [drifted] {name}")
        if truth.get("invalid"):
            print(f"   * invalid 锚点文档: {truth['invalid']} 篇（无法机械核验，需改写为仓库内相对路径）")

    # 2. 目录拓扑分布
    print("\n📂 [知识库拓扑分布]:")
    for cat, name in DIATAXIS_CATEGORIES.items():
        docs = res["category_counts"].get(cat, [])
        print(f"   * {name}: {len(docs)} 篇")
    
    legacy_total = sum(len(v) for v in res["legacy_counts"].values())
    if legacy_total > 0:
        print(f"\n⚠️  [探测到历史瀑布结构文档 ({legacy_total} 篇)]:")
        for cat, name in LEGACY_CATEGORIES.items():
            docs = res["legacy_counts"].get(cat, [])
            if docs:
                print(f"   * {name}: {len(docs)} 篇")

    # 2.5 Backlog 演进与待办健康仪表盘
    if res.get("backlog_metrics", {}).get("has_backlog"):
        bm = res["backlog_metrics"]
        mode_label = "形态 B (Issue-as-File 目录分片)" if bm.get("mode") == "form_b" else "形态 A (单文件紧凑行)"
        print(f"\n📋 [Backlog 演进与待办健康仪表盘 - {mode_label}]:")
        if bm.get("location"):
            print(f"   * 物理拓扑定位: {bm['location']}")
        print(f"   * 活跃待办总数: {bm['active_total']} 条 (进行中: {bm['in_progress']} 条, 计划中: {bm['planned']} 条)")
        print(f"   * 历史已归档数: {bm['cold_archived_total']} 条 (冷区: archive/)")
        pris = bm["priority_counts"]
        print(f"   * 优先级分布:   P0: {pris.get('P0', 0)}, P1: {pris.get('P1', 0)}, P2: {pris.get('P2', 0)}, P3: {pris.get('P3', 0)}")
        types_str = ", ".join(f"{k}: {v}" for k, v in sorted(bm["type_counts"].items()))
        if types_str:
            print(f"   * 领域类型分布: {types_str}")
        if bm["hot_completed_count"] > 0:
            print(f"   ⚠️  热区滞留已完成项: {bm['hot_completed_count']} 条 (建议及时迁出归档)")

    # 3. 诊断发现与整改建议
    print("\n💡 [体检诊断与修复建议]:")
    has_issues = False

    if res["total_link_errors"] > 0:
        has_issues = True
        print(f"   ❌ 存在 {res['total_link_errors']} 处断链，运行 `python3 check-doc-links.py --root {args.root}` 查看详情并修复。")

    if res["overflow_rev_files"]:
        has_issues = True
        print(f"   ⚠️  存在 {len(res['overflow_rev_files'])} 篇文档修订历史超过 5 条，运行 `python3 trim-revision.py --root {args.root} --fix` 自动自愈。")

    if res["missing_meta_files"]:
        has_issues = True
        sample = [f.name for f in res["missing_meta_files"][:3]]
        print(f"   ⚠️  存在 {len(res['missing_meta_files'])} 篇文档缺少标准控制头 (示例: {', '.join(sample)})。")

    if res.get("version_drift_files"):
        has_issues = True
        print(f"   ⛔ 存在 {len(res['version_drift_files'])} 篇文档控制头与修订历史版本漂移（未同步升级）:")
        for f, h_ver, r_ver, msg in res["version_drift_files"][:5]:
            try:
                rel_f = f.relative_to(root_path)
            except ValueError:
                rel_f = f
            print(f"      - {rel_f}: {msg}")
        print(f"      运行 `python3 scripts/check-doc-control-sync.py --root {args.root}` 查看详情并修复。")

    if res["orphan_docs"]:
        has_issues = True
        sample = [f.name for f in res["orphan_docs"][:3]]
        print(f"   ⚠️  存在 {len(res['orphan_docs'])} 篇孤儿文档未被索引引用 (示例: {', '.join(sample)})，建议在 index.md 中收录。")

    if res.get("backlog_warnings"):
        has_issues = True
        print(f"   ⚠️  存在 {len(res['backlog_warnings'])} 处 Backlog 冷热分离与体积预警:")
        for w in res["backlog_warnings"][:5]:
            print(f"      - {w}")

    if res["backlog_issues"]:
        has_issues = True
        print(f"   ⛔ 存在 {len(res['backlog_issues'])} 处 Backlog 条目编号违规（缺号/格式不合规/重号）:")
        for issue in res["backlog_issues"][:5]:
            print(f"      - {issue}")
        print("      赋号与格式规范见 references/backlog-specification.md。")

    if res.get("llms_map_issue"):
        has_issues = True
        print(f"   ⛔ 机器地图一致性缺陷: {res['llms_map_issue']}")

    if res.get("agents_md_issue"):
        has_issues = True
        print(f"   ⛔ 路由文件缺陷: {res['agents_md_issue']}")

    # RFC-0007：文档状态机——阻断项进缺陷，未决冲突清单独立成节
    doc_status = res.get("doc_status") or {}
    for issue in (doc_status.get("issues") or [])[:10]:
        has_issues = True
        print(f"   ⛔ 文档状态违规: {issue}")
    for warn in (doc_status.get("warnings") or [])[:5]:
        has_issues = True
        print(f"   ⚠️  文档状态警告: {warn}")

    # R1-4：真值轴的阻断理由必须与「完美/无缺陷」互斥，否则同一屏会同时出现
    # PASS 文案与 REJECT 理由（BK-0028 明令禁止的自相矛盾）。
    truth_reasons = truth_blockers(truth, args.truth_threshold, args.min_coverage)
    if truth_reasons:
        has_issues = True
        for reason in truth_reasons:
            print(f"   ⛔ 真值轴阻断: {reason}")
    else:
        # R2D-4：warn 模式也必须把「不可判定 / 账本不可用 / 墓碑违规」计入缺陷——
        # 报告面不得在门禁已知有缺陷时打印「完美」。
        if truth.get("unavailable"):
            has_issues = True
            print(f"   ⚠️  真值轴不可判定：{truth['unavailable']}")
        if truth.get("baseline_status") in ("missing", "corrupt"):
            has_issues = True
            print(f"   ⚠️  锚点基线不可用（{truth['baseline_status']}）")
        if truth.get("removed_from_baseline"):
            has_issues = True
            print(f"   ⚠️  锚点基线墓碑违规 {truth['removed_from_baseline']} 处（声明被删除/缩减）")
        if truth.get("baseline_status") == "empty":
            has_issues = True
            print("   ⚠️  锚点基线为空，墓碑判据不成立")
        # R2D2-3：warn 模式下的漂移/缺失同样属缺陷，不得与「完美」并存。
        drift_total = (
            truth.get("drifted", 0) + truth.get("missing_anchor", 0)
            + truth.get("stale", 0) + truth.get("unverified", 0)
        )
        if drift_total:
            has_issues = True
            print(
                "   ⚠️  真值轴未清零："
                f"drifted {truth.get('drifted', 0)} / missing {truth.get('missing_anchor', 0)}"
                f" / stale {truth.get('stale', 0)} / unverified {truth.get('unverified', 0)}"
                "（warn 不阻断，但属缺陷）"
            )

    if not has_issues:
        print("   🌟 完美！未检测到任何健康缺陷，知识库处于极佳健康状态！")

    # RFC-0007：未决冲突清单——把「哪份该信」从读全文降级为看状态
    doc_status = res.get("doc_status") or {}
    if doc_status:
        counts = doc_status.get("counts") or {}
        print("\n📌 [文档状态机 · 未决冲突清单]:")
        print(
            f"   * 状态分布: Active {counts.get('Active', 0)}｜Contested {counts.get('Contested', 0)}"
            f"｜Superseded {counts.get('Superseded', 0)}"
            + (f"｜非法 {counts['Unknown']}" if counts.get("Unknown") else "")
        )
        for item in (doc_status.get("contested") or [])[:10]:
            age = f"{item['age_days']} 天" if item.get("age_days") is not None else "未知"
            flag = "⚠️ 超期" if (item.get("age_days") or 0) > CONTESTED_MAX_AGE_DAYS else ""
            print(f"   - [Contested] {item['doc']}（{age}{'，' + flag if flag else ''}）：{item['reason']}")
        for item in (doc_status.get("superseded") or [])[:10]:
            print(f"   - [Superseded] {item['doc']} → {item['by']}")
        # T-11：存在非法状态时不得宣称「全库 Active」（BK-0028 禁止的自相矛盾）
        if not (doc_status.get("contested") or doc_status.get("superseded")) and not doc_status.get("issues"):
            print("   （无争议、无取代：全库 Active）")

    print("\n" + "=" * 60)
    passed, reasons = evaluate_verdict(res, args.threshold, args.truth_threshold, args.min_coverage)
    if passed:
        print("🏁 诊断结论: PASS (健康度达标，准予交付) ✅")
        sys.exit(0)
    print(f"🚫 诊断结论: REJECTED（{'；'.join(reasons) or '存在阻断项'}），请修复后重测")
    sys.exit(1)


if __name__ == "__main__":
    main()
