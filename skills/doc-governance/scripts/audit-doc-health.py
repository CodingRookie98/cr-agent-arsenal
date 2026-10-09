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
  8. 综合计算健康评分 (0-100 分)，出具结构化诊断报告。
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
from typing import Dict, List, Set, Tuple

import importlib.util

# 交付凭据归档（RFC-0001 / R1-2）：审查报告以**逐字原文**归档（G1 红线——添加控制头会
# 改变内容并污染 SHA256 指纹），报告之间亦无 markdown 入链。故该目录豁免文档治理扫描，
# 否则每次真实审查交付都会单调侵蚀知识库健康度（外推约 11 次交付即跌破 80 分门槛）。
# 豁免语义登记见 docs/GOVERNANCE.md。
EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")


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


def _map_project_name(llms_file: Path) -> str:
    """从既有机器地图首行反解项目名，使判定参数与生成参数同源（R1-2）。"""
    try:
        first_line = llms_file.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return "System"
    match = re.match(r"# (.+?) Machine-Readable Knowledge Base Map", first_line)
    return match.group(1) if match else "System"


def check_llms_map_consistency(root_dir: Path) -> str:
    """机器地图一致性门禁（BK-0025）：以注册命令语义重生成并与 <root>/llms.txt 逐字节比对。

    返回缺陷描述；空串表示一致或本项不适用（未生成机器地图的项目不参与判定）。
    """
    llms_file = root_dir / "llms.txt"
    if not llms_file.exists():
        return ""
    project_name = _map_project_name(llms_file)
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = Path(tmp_dir) / "llms.txt"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                written = _llms_mod.generate_llms_txt(root_dir, tmp_out, project_name=project_name)
            if written == 0:
                # R1-1：无可收录文档时本项不适用——否则修复命令必然 rc=1，形成不可修复的死胡同
                return ""
            if tmp_out.read_bytes() != llms_file.read_bytes():
                # D1-4：项目名源自仓库可控内容，须 shell 转义后再拼入提示命令（防命令注入）
                quoted_name = shlex.quote(project_name)
                return (
                    "机器地图与生成物不一致 —— 请以 --name " + quoted_name + " 运行 "
                    "generate-llms-txt.py --root docs --output docs/llms.txt 重新生成后再提交"
                )
    except Exception as exc:  # noqa: BLE001 - 门禁不得因单点异常中断整体体检
        return f"机器地图一致性检查无法完成: {exc}"
    return ""


def parse_frontmatter(content: str) -> Dict[str, str]:
    """解析文档头部的 Frontmatter 或文档控制信息块"""
    metadata = {}
    # 模式 A: YAML Frontmatter (--- ... ---)
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if yaml_match:
        for line in yaml_match.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                metadata[k.strip().lower()] = v.strip()
        return metadata

    # 模式 B: 引用块元数据 (支持 > **文档控制信息** 或直接 > **文档标识** / > **文档版本**)
    for line in content.splitlines()[:50]:
        trimmed = line.strip()
        if trimmed.startswith(">"):
            clean = re.sub(r"^[>\s\-*]+", "", trimmed).strip()
            if ":" in clean or "：" in clean:
                sep = ":" if ":" in clean else "："
                k, v = clean.split(sep, 1)
                k_clean = re.sub(r"[*_`]", "", k).strip().lower()
                metadata[k_clean] = v.strip()

    # 模式 C: 表格型元数据 (| **文档标识** | DR-xxx | 或 | 文档标识 | ... |)
    if "文档标识" in content or "当前版本" in content or "version" in content.lower() or "文档版本" in content:
        for m in re.finditer(r"\|\s*(?:\*\*)?([^|\n*]+?)(?:\*\*)?\s*\|\s*([^|\n]+?)\s*\|", content):
            k_raw = m.group(1).strip().lower()
            v_raw = m.group(2).strip()
            if k_raw in ("文档标识", "当前版本", "规范版本", "文档版本", "version", "id", "文档所有者", "生效日期"):
                metadata[k_raw] = v_raw

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


def audit_health(root_dir: Path, compat_mode: bool = False) -> Dict:
    """执行全面的健康度体检"""
    all_md_files = [
        f for f in root_dir.rglob("*.md")
        if not any(p in f.parts for p in ("node_modules", ".git", ".next", "dist", "build"))
        and not in_evidence_archive(f, root_dir)
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

    # 孤儿文档判定 (不包含根目录下的 index.md, llms.txt, GOVERNANCE.md 等入口)
    orphan_docs = []
    for f in all_md_files:
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
        "scores": {
            "link_score": round(link_score, 1),
            "meta_score": round(meta_score, 1),
            "rev_score": round(rev_score, 1),
            "orphan_score": round(orphan_score, 1),
            "arch_score": round(arch_score, 1),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="知识库全面健康度体检引擎")
    parser.add_argument("--root", default="docs", help="文档根目录 (默认为 docs)")
    parser.add_argument("--compat", action="store_true", help="启用既有项目老目录兼容模式")
    parser.add_argument("--threshold", type=float, default=80.0, help="合格通过分数门槛 (默认 80.0)")

    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    if not root_path.exists():
        print(f"❌ 错误: 目标文档目录不存在: {root_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🏥 启动知识库全面健康度体检: 根目录={root_path} ...")
    res = audit_health(root_path, compat_mode=args.compat)
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

    if not has_issues:
        print("   🌟 完美！未检测到任何健康缺陷，知识库处于极佳健康状态！")

    print("\n" + "=" * 60)
    if (
        res["total_score"] >= args.threshold
        and res["total_link_errors"] == 0
        and not res["backlog_issues"]
        and not res.get("version_drift_files")
        and not res.get("llms_map_issue")
    ):
        print("🏁 诊断结论: PASS (健康度达标，准予交付) ✅")
        sys.exit(0)
    else:
        reasons = []
        if res["total_score"] < args.threshold:
            reasons.append(f"得分 {res['total_score']} < 门槛 {args.threshold}")
        if res["total_link_errors"]:
            reasons.append(f"{res['total_link_errors']} 处断链")
        if res.get("version_drift_files"):
            reasons.append(f"{len(res['version_drift_files'])} 处版本漂移")
        if res["backlog_issues"]:
            reasons.append(f"{len(res['backlog_issues'])} 处 backlog 编号违规")
        if res.get("llms_map_issue"):
            reasons.append("机器地图不一致")
        print(f"🚫 诊断结论: REJECTED（{'；'.join(reasons) or '存在阻断项'}），请修复后重测")
        sys.exit(1)


if __name__ == "__main__":
    main()
