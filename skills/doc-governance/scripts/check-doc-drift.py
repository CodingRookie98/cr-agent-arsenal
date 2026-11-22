#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-doc-drift.py - 文档代码锚点漂移检测器（真值轴 · 读侧）

功能:
  1. 解析文档控制头的三个可选真值字段：来源 / 代码锚点 / 复核于；
  2. 逐锚点校验路径存在性，并按 git 提交时间判定「复核之后锚点是否又被改过」；
  3. 输出 drifted / missing_anchor / stale / unverified / fresh 五态与覆盖度；
  4. 供 audit-doc-health.py 复用（真值分维度），自身只读、绝不写文件。

设计要点（见 docs/proposals/RFC-0005-doc-truth-axis.md）:
  - 漂移判定用 **git 提交时间**，不用文件 mtime（checkout/CI 中 mtime 不可靠，D-3）；
  - 零声明不颁发满分：declared == 0 时 enabled=False 且 freshness_score=0；
  - git 不可用属环境错误，fail-closed 退出 2，不静默通过。

退出码: 0 = 无阻断漂移；1 = 存在漂移且指定 --fail-on-drift；2 = 入参/环境错误。
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

_scripts_dir = Path(__file__).resolve().parent

EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")
ENTRY_DOC_NAMES = ("index.md", "README.md", "GOVERNANCE.md")

FRESHNESS_MAX_SCORE = 15.0
SECONDS_PER_DAY = 86400

# R1（加固）：英文逗号只在**后接空白**时视为分隔符，否则 `src/a,b.py` 这类合法路径会被切碎。
_ANCHOR_SPLIT = re.compile(r"[，、;；]|,(?=\s)")
_ANCHOR_LINE = re.compile(r"^(?P<path>[^:]+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$")
_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_COMMIT = re.compile(r"commit\s+([0-9a-fA-F]{7,40})")


def in_evidence_archive(path: Path, root_dir: Path) -> bool:
    """判定路径是否落在交付凭据归档根内（<root>/project/reviews/**）。"""
    try:
        rel = path.relative_to(root_dir)
    except ValueError:
        return False
    return rel.parts[:2] == EVIDENCE_ARCHIVE_PARTS


def _clean_value(raw: str) -> str:
    return raw.replace("**", "").replace("`", "").strip()


def normalize_anchor(raw: str) -> Optional[Dict]:
    """把一条锚点声明归一为 {"path", "line_start", "line_end"}；越界/绝对路径返回 None。"""
    text = _clean_value(raw)
    if not text:
        return None
    if text.startswith("/") or text.startswith("\\") or re.match(r"^[A-Za-z]:[\\/]", text):
        return None
    body = text
    line_start = line_end = None
    m = _ANCHOR_LINE.match(text)
    if m:
        body = m.group("path").strip()
        if m.group("start"):
            line_start = int(m.group("start"))
            line_end = int(m.group("end")) if m.group("end") else line_start
    parts = [p for p in body.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        return None
    return {"path": "/".join(parts), "line_start": line_start, "line_end": line_end}


def parse_truth_fields(content: str) -> Dict:
    """解析控制头三字段。缺失字段返回空值，不抛异常。"""
    fields: Dict = {
        "sources": [],
        "anchors": [],
        "verified_at": None,
        "verified_commit": None,
    }
    in_fence = False
    for line in content.splitlines()[:60]:
        trimmed = line.strip()
        # R2-3（文档即输入）：围栏内的示例（模板/教程里的控制头骨架）不是真声明，
        # 未加围栏感知会把「讲解」当成「登记」。
        if trimmed.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not trimmed.startswith(">"):
            continue
        clean = re.sub(r"^[>\s\-*]+", "", trimmed).strip()
        sep = ":" if ":" in clean else ("：" if "：" in clean else None)
        if sep is None:
            continue
        key, value = clean.split(sep, 1)
        key_clean = _clean_value(key).lower()
        value = _clean_value(value)
        if not value:
            continue
        if key_clean in ("来源", "sources", "source"):
            fields["sources"] = [v for v in (_clean_value(x) for x in _ANCHOR_SPLIT.split(value)) if v]
        elif key_clean in ("代码锚点", "锚点", "anchors", "code-anchors"):
            anchors = []
            for chunk in _ANCHOR_SPLIT.split(value):
                anchor = normalize_anchor(chunk)
                if anchor is not None:
                    anchors.append(anchor)
            fields["anchors"] = anchors
        elif key_clean in ("复核于", "复核", "verified", "verified-at"):
            date_m = _DATE.search(value)
            commit_m = _COMMIT.search(value)
            fields["verified_at"] = date_m.group(1) if date_m else None
            fields["verified_commit"] = commit_m.group(1) if commit_m else None
    return fields


def classify_doc(
    anchor_paths: Sequence[str],
    anchor_exists: Sequence[bool],
    anchor_last_commits: Sequence[Optional[int]],
    verified_ts: Optional[int],
    now_ts: int,
    max_age_days: int,
    anchor_tracked: Optional[Sequence[bool]] = None,
) -> str:
    """五态判定，优先级：missing_anchor > drifted > stale > unverified > fresh。

    R2-1（R1-5 升级）：锚点文件存在但**未被版本控制**时没有提交时间可用，
    既不能判漂移也不能判新鲜——必须落 unverified，否则「未提交的改动」会被当成 fresh。
    """
    if any(not exists for exists in anchor_exists):
        return "missing_anchor"
    if anchor_tracked is not None and any(exists and not tracked for exists, tracked in zip(anchor_exists, anchor_tracked)):
        return "unverified"
    if verified_ts is None:
        return "unverified"
    if any(ts is not None and ts > verified_ts for ts in anchor_last_commits):
        return "drifted"
    if max_age_days > 0 and (now_ts - verified_ts) > max_age_days * SECONDS_PER_DAY:
        return "stale"
    return "fresh"


def _run_git(repo: Path, args: Sequence[str]) -> Optional[str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def is_git_repo(repo: Path) -> bool:
    return _run_git(repo, ["rev-parse", "--is-inside-work-tree"]) == "true"


def is_shallow_repo(repo: Path) -> bool:
    """浅克隆下 `git log -1 -- path` 只返回克隆 tip，会把一切锚点判成漂移（R1-3）。"""
    return _run_git(repo, ["rev-parse", "--is-shallow-repository"]) == "true"


def git_resolve_commit_ts(repo: Path, sha: str) -> Optional[int]:
    out = _run_git(repo, ["show", "-s", "--format=%ct", sha])
    try:
        return int(out) if out else None
    except ValueError:
        return None


def git_last_commit_ts(repo: Path, rel_path: str) -> Optional[int]:
    out = _run_git(repo, ["log", "-1", "--format=%ct", "--", rel_path])
    try:
        return int(out) if out else None
    except ValueError:
        return None


def _verified_ts(fields: Dict, repo: Optional[Path]) -> Optional[int]:
    commit = fields.get("verified_commit")
    if repo is not None and commit:
        ts = git_resolve_commit_ts(repo, commit)
        if ts is not None:
            return ts
    date_str = fields.get("verified_at")
    if not date_str:
        return None
    try:
        import datetime

        # R1-1：日期型「复核于」必须按**当日末刻**起算。按 UTC 零点起算会把「今天复核、
        # 今天提交锚点」判成漂移（同日复核必红），这是把复核语义读成了「当天开始前」。
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        ) + datetime.timedelta(days=1, seconds=-1)
        return int(dt.timestamp())
    except ValueError:
        return None


def _iter_docs(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in ("node_modules", ".git", "dist", "build") for part in path.parts):
            continue
        if in_evidence_archive(path, root):
            continue
        if "archive" in path.parts or "archived" in path.parts:
            continue
        # 根级入口文档（index/README/GOVERNANCE）默认不期望锚点，但它们**显式声明**锚点时
        # 照常受检——否则「声明了却不算」会让真值轴出现静默的覆盖黑洞（RFC-0005 §4.2）。
        if path.parent == root and path.name in ENTRY_DOC_NAMES and not _declares_anchor(path):
            continue
        yield path


def _declares_anchor(path: Path) -> bool:
    try:
        return bool(parse_truth_fields(path.read_text(encoding="utf-8", errors="replace"))["anchors"])
    except OSError:
        return False


DEFAULT_BASELINE_NAME = ".doc-truth-baseline.json"


def load_baseline(path: Optional[Path]) -> Dict[str, List[str]]:
    """读取锚点基线（墓碑），返回 {doc: [anchor_path, ...]}；缺失/损坏一律降级为空。"""
    if path is None:
        return {}
    try:
        if not Path(path).is_file():
            return {}
        import json as _json

        data = _json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    docs = data.get("docs") if isinstance(data, dict) else None
    if not isinstance(docs, dict):
        return {}
    return {
        str(doc): [str(a) for a in anchors]
        for doc, anchors in docs.items()
        if isinstance(anchors, list)
    }


def write_baseline(path: Path, docs_records: Sequence[Dict]) -> int:
    """把当前声明写为基线（墓碑）。返回登记的文档数。"""
    import json as _json

    manifest = {
        "version": 1,
        "docs": {rec["doc"]: [a["path"] for a in rec["anchors"]] for rec in docs_records},
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return len(manifest["docs"])


def _removed_from_baseline(baseline: Dict[str, List[str]], current: Dict[str, List[str]]) -> List[Dict]:
    """R2-1（R1-2 维持）：锚点声明一旦登记为基线，删除/缩减即视为违规——
    否则「删掉失败文档的锚点」可以同时缩小分子与分母把真值分洗白。"""
    removed = []
    for doc, anchors in baseline.items():
        now_anchors = current.get(doc, [])
        missing = [a for a in anchors if a not in now_anchors]
        if missing or not now_anchors:
            removed.append({"doc": doc, "missing": missing, "declared_now": now_anchors})
    return removed


def analyze(
    root: Path,
    repo: Optional[Path] = None,
    now_ts: Optional[int] = None,
    max_age_days: int = 180,
    baseline_path: Optional[Path] = None,
) -> Dict:
    """只读分析，返回 {'enabled', 'total_docs', 'declared', 'coverage', 'freshness_score', ...}。"""
    import time as _time

    root = Path(root).resolve()
    repo_path = Path(repo).resolve() if repo is not None else None
    now = int(now_ts if now_ts is not None else _time.time())
    current_anchors: Dict[str, List[str]] = {}

    docs: List[Dict] = []
    total_docs = 0
    declared = 0
    buckets = {"drifted": [], "missing_anchor": [], "stale": [], "unverified": [], "fresh": []}

    for doc_path in _iter_docs(root):
        total_docs += 1
        try:
            content = doc_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fields = parse_truth_fields(content)
        anchors = fields["anchors"]
        if not anchors:
            continue
        declared += 1
        rel_doc = doc_path.relative_to(root).as_posix()
        current_anchors[rel_doc] = [a["path"] for a in anchors]
        exists: List[bool] = []
        commits: List[Optional[int]] = []
        tracked: List[bool] = []
        for anchor in anchors:
            if repo_path is not None:
                anchor_exists = (repo_path / anchor["path"]).is_file()
            else:
                anchor_exists = (root / anchor["path"]).is_file()
            exists.append(anchor_exists)
            commit_ts = (
                git_last_commit_ts(repo_path, anchor["path"]) if (repo_path is not None and anchor_exists) else None
            )
            commits.append(commit_ts)
            tracked.append(commit_ts is not None)
        status = classify_doc(
            anchor_paths=[a["path"] for a in anchors],
            anchor_exists=exists,
            anchor_last_commits=commits,
            verified_ts=_verified_ts(fields, repo_path),
            now_ts=now,
            max_age_days=max_age_days,
            anchor_tracked=tracked if repo_path is not None else None,
        )
        record = {
            "doc": rel_doc,
            "status": status,
            "anchors": anchors,
            "verified_at": fields["verified_at"],
            "verified_commit": fields["verified_commit"],
        }
        docs.append(record)
        buckets[status].append(record)

    fresh_count = len(buckets["fresh"])
    score = round(FRESHNESS_MAX_SCORE * fresh_count / declared, 1) if declared else 0.0
    baseline = load_baseline(baseline_path)
    removed = _removed_from_baseline(baseline, current_anchors) if baseline else []
    return {
        "removed_from_baseline": removed,
        "baseline_docs": len(baseline),
        "enabled": declared > 0,
        "total_docs": total_docs,
        "declared": declared,
        "coverage": round(declared / total_docs, 4) if total_docs else 0.0,
        "drifted": buckets["drifted"],
        "missing_anchor": buckets["missing_anchor"],
        "stale": buckets["stale"],
        "unverified": buckets["unverified"],
        "fresh": buckets["fresh"],
        "freshness_score": score,
        "max_age_days": max_age_days,
        "docs": docs,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="文档代码锚点漂移检测器")
    parser.add_argument("--root", default="docs", help="文档根目录（默认 docs）")
    parser.add_argument("--repo", default=None, help="仓库根（默认取 --root 的父目录）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--fail-on-drift", action="store_true", help="存在漂移时退出码 1")
    parser.add_argument("--max-age-days", type=int, default=180, help="复核时效上限（天，0 表示不检查）")
    parser.add_argument("--baseline", default=None,
                        help=f"锚点基线（墓碑）路径，默认 <root>/{DEFAULT_BASELINE_NAME}")
    parser.add_argument("--write-baseline", action="store_true",
                        help="把当前声明写为基线（阻断「删锚点洗绿」的机械依据）")
    parser.add_argument("--fail-on-unverified", action="store_true",
                        help="连 unverified / stale 一并视为失败（默认只对 drifted 与 missing_anchor 失败）")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"❌ 错误: 文档目录不存在: {root}", file=sys.stderr)
        return 2
    repo = Path(args.repo).resolve() if args.repo else root.parent
    if not is_git_repo(repo):
        print(f"❌ 错误: 不是 git 仓库（无法判定漂移）: {repo}", file=sys.stderr)
        return 2
    if is_shallow_repo(repo):
        print(
            "❌ 错误: 检测到浅克隆（shallow repository），历史提交时间不可得，无法判定漂移。"
            "请使用 fetch-depth: 0 拉全历史后重试。",
            file=sys.stderr,
        )
        return 2

    baseline_path = Path(args.baseline).resolve() if args.baseline else root / DEFAULT_BASELINE_NAME

    if args.write_baseline:
        res = analyze(root, repo=repo, max_age_days=args.max_age_days, baseline_path=None)
        written = write_baseline(baseline_path, res["docs"])
        print(f"🧱 已写入锚点基线: {baseline_path}（{written} 篇声明）")
        return 0

    res = analyze(root, repo=repo, max_age_days=args.max_age_days, baseline_path=baseline_path)
    summary = {
        "enabled": res["enabled"],
        "total_docs": res["total_docs"],
        "declared": res["declared"],
        "coverage": res["coverage"],
        "drifted": len(res["drifted"]),
        "missing_anchor": len(res["missing_anchor"]),
        "stale": len(res["stale"]),
        "unverified": len(res["unverified"]),
        "fresh": len(res["fresh"]),
        "freshness_score": res["freshness_score"],
        "max_age_days": res["max_age_days"],
        "removed_from_baseline": len(res["removed_from_baseline"]),
        "baseline_docs": res["baseline_docs"],
    }

    if args.json:
        print(json.dumps({"summary": summary, "docs": res["docs"]}, ensure_ascii=False, indent=2))
    else:
        print(f"🔍 文档代码锚点漂移检测: root={root} repo={repo}")
        if not res["enabled"]:
            print("⚠️  未启用：没有任何文档声明「代码锚点」，真值分不颁发（0.0/15）")
        print(
            f"📊 声明 {summary['declared']}/{summary['total_docs']} 篇（覆盖度 {summary['coverage']:.1%}）｜"
            f"fresh {summary['fresh']}｜drifted {summary['drifted']}｜missing {summary['missing_anchor']}｜"
            f"stale {summary['stale']}｜unverified {summary['unverified']}"
        )
        print(f"🎯 真值分: {summary['freshness_score']} / {FRESHNESS_MAX_SCORE:g}")
        for bucket in ("missing_anchor", "drifted", "stale", "unverified"):
            for item in res[bucket]:
                print(f"   - [{bucket}] {item['doc']}")
        if res["removed_from_baseline"]:
            print("   ⛔ 基线墓碑违规（声明被删除/缩减）:")
            for item in res["removed_from_baseline"]:
                print(f"      - {item['doc']} 缺失: {', '.join(item['missing']) or '全部锚点'}")

    # R2-2（R1-6 升级）：missing_anchor 是硬断裂（锚点被删除/移动），必须与 drifted 同权。
    if args.fail_on_drift and (
        summary["drifted"] or summary["missing_anchor"] or summary["removed_from_baseline"]
    ):
        return 1
    if args.fail_on_unverified and (summary["unverified"] or summary["stale"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
