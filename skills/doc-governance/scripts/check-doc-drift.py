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
from typing import Dict, List, Optional, Sequence, Tuple

_scripts_dir = Path(__file__).resolve().parent

EVIDENCE_ARCHIVE_PARTS = ("project", "reviews")
ENTRY_DOC_NAMES = ("index.md", "README.md", "GOVERNANCE.md")

FRESHNESS_MAX_SCORE = 15.0
SECONDS_PER_DAY = 86400

# R1（加固）：英文逗号只在**后接空白**时视为分隔符，否则 `src/a,b.py` 这类合法路径会被切碎。
_ANCHOR_SPLIT = re.compile(r"[，、;；]|,(?=\s)")
_ANCHOR_LINE = re.compile(r"^(?P<path>[^:]+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$")
# R3-1：路径形态判据**不能**用「只允许 ASCII 无空格」——那会把含空格/中文/@/+ 的
# 合法路径一并判 invalid 并静默丢弃（漂移漏检且 rc=0）。判据改为「像路径」：
# 含分隔符 / 、含扩展名点、或纯标识符形态。散文（无 / 无 . 且非标识符）才判 invalid。
_PATH_TOKEN = re.compile(r"[A-Za-z0-9._@+~\-]+")
_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_COMMIT = re.compile(r"commit\s+([0-9a-fA-F]{7,40})")


def in_evidence_archive(path: Path, root_dir: Path) -> bool:
    """判定路径是否落在交付凭据归档根内（<root>/project/reviews/**）。"""
    try:
        rel = path.relative_to(root_dir)
    except ValueError:
        return False
    return rel.parts[:2] == EVIDENCE_ARCHIVE_PARTS


def _clean_value(raw: str, strip_bold: bool = True) -> str:
    """清洗控制头值。**锚点必须 strip_bold=False**：`src/**` 的 `**` 是 glob，不是加粗。"""
    text = raw.replace("`", "").strip()
    return text.replace("**", "").strip() if strip_bold else text


_LINE_RANGE = re.compile(r":\d+(?:-\d+)?$")


def _looks_like_path(text: str) -> bool:
    """像路径 ⇔ 剥掉行区间后，含分隔符、含扩展名点、或整体是标识符形态。

    R3D-1：行区间必须先剥——`Makefile:2` / `LICENSE:3` 是「根级无扩展名文件 + 行区间」，
    不剥会被判 invalid 并静默退出判定集（漂移漏检且 rc=0）。
    反例（散文）：`见附录 A`、`see appendix A` —— 无分隔符、无点、含空白/中文。
    """
    body = _LINE_RANGE.sub("", text)
    if "/" in body or "." in body:
        return True
    return bool(_PATH_TOKEN.fullmatch(body))


def normalize_anchor(raw: str) -> Optional[Dict]:
    """把一条锚点声明归一为 {"path", "line_start", "line_end"}；越界/绝对路径返回 None。"""
    text = _clean_value(raw, strip_bold=False)
    if not text:
        return None
    if text.startswith("/") or text.startswith("\\") or re.match(r"^[A-Za-z]:[\\/]", text):
        return None
    # R3-1：先归一化分隔符，再走后续判据（否则 src\a.py 的形态判断与路径解析会分叉）。
    text = text.replace("\\", "/")
    # R2D56-3：先剥「整体加粗」（两端 ** 且内部无 *），再判 glob——
    # 否则 **src/pkg/x.py** 会被任意 * 误判成 glob，真实锚点假红。
    bold = re.fullmatch(r"\*\*(.+)\*\*", text)
    if bold and "*" not in bold.group(1):
        text = bold.group(1).strip()
    # R2D-6：glob / 占位符锚点不是可 stat 的路径，标记为不可机械核验（后续落 unverified），
    # 而不是一律判 missing_anchor 硬红。
    if any(ch in text for ch in "*?[]{}<>"):
        clean = text.replace("\\", "/").strip("/")
        return {"path": clean or text, "line_start": None, "line_end": None,
                "unverifiable": True, "invalid": False}
    # R2D56-4：散文锚点不是「路径不存在」，归为 invalid 并给修复提示。
    # R3-1：判据必须是「不像路径」而非「含空格/中文」——后者会吞掉合法路径。
    if not _looks_like_path(text):
        # R3DC-1：invalid 分支也要把行区间拆出来，path 只留主体——
        # 否则存在性探测与基线比对会拿 "说明:3" 去 stat。
        body = _LINE_RANGE.sub("", text)
        m_invalid = _ANCHOR_LINE.match(text)
        start = end = None
        if m_invalid and m_invalid.group("start"):
            start = int(m_invalid.group("start"))
            end = int(m_invalid.group("end")) if m_invalid.group("end") else start
        return {"path": body, "line_start": start, "line_end": end,
                "unverifiable": True, "invalid": True}
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
    return {"path": "/".join(parts), "line_start": line_start, "line_end": line_end,
            "unverifiable": False, "invalid": False}


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
        # 值不做全局去加粗：锚点里的 ** 是 glob。各分支按自身语义清洗。
        value = value.strip()
        if not value:
            continue
        if key_clean in ("来源", "sources", "source"):
            fields["sources"] = [v for v in (_clean_value(x) for x in _ANCHOR_SPLIT.split(value)) if v]
        elif key_clean in ("代码锚点", "锚点", "anchors", "code-anchors"):
            anchors = []
            # R3-2：整体加粗可能**跨多个锚点**（**src/a.py, src/b.py**），
            # 必须在分割前剥离，否则两端星号会让两个锚点都落 glob。
            whole_bold = re.fullmatch(r"\*\*(.+)\*\*", value)
            if whole_bold and "**" not in whole_bold.group(1):
                value = whole_bold.group(1).strip()
            for chunk in _ANCHOR_SPLIT.split(value):
                anchor = normalize_anchor(_clean_value(chunk, strip_bold=False))
                if anchor is not None:
                    anchors.append(anchor)
            fields["anchors"] = anchors
        elif key_clean in ("复核于", "复核", "verified", "verified-at"):
            value = _clean_value(value)
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
    anchor_unverifiable: Optional[Sequence[bool]] = None,
    anchor_shas: Optional[Sequence[Optional[str]]] = None,
    doc_sha: Optional[str] = None,
) -> str:
    """五态判定，优先级：missing_anchor > drifted > stale > unverified > fresh。

    R2-1（R1-5 升级）：锚点文件存在但**未被版本控制**时没有提交时间可用，
    既不能判漂移也不能判新鲜——必须落 unverified，否则「未提交的改动」会被当成 fresh。
    """
    # R2D56-1：不可机械核验的锚点（glob/占位符/散文）只从**判定集**里剔除，
    # 不得短路整篇文档——否则一个 glob 就能盖住同文档真实锚点的漂移。
    mask = list(anchor_unverifiable) if anchor_unverifiable is not None else [False] * len(anchor_paths)
    decidable = [i for i, unverifiable in enumerate(mask) if not unverifiable]
    if not decidable:
        return "unverified"
    exists = [anchor_exists[i] for i in decidable]
    commits = [anchor_last_commits[i] for i in decidable]
    tracked = [anchor_tracked[i] for i in decidable] if anchor_tracked is not None else None

    if any(not e for e in exists):
        return "missing_anchor"
    if tracked is not None and any(e and not t for e, t in zip(exists, tracked)):
        return "unverified"
    if verified_ts is None:
        return "unverified"
    # R2D-3：未来日期的「复核于」不是复核。容忍 1 天时区漂移，超出即视为无效声明。
    if verified_ts > now_ts + SECONDS_PER_DAY:
        return "unverified"
    # B-02：锚点与文档在**同一次提交**中被改动 ⇒ 视为同步处理（复核点只能指向已存在的提交，
    # 若不做此豁免，任何「改锚点 + 刷新复核点」的提交都会立刻把文档判成漂移）。
    stale_indices = [
        i for i, ts in enumerate(commits)
        if ts is not None and ts > verified_ts
        and not (anchor_shas is not None and doc_sha is not None and anchor_shas[i] == doc_sha)
    ]
    if stale_indices:
        return "drifted"
    if max_age_days > 0 and (now_ts - verified_ts) > max_age_days * SECONDS_PER_DAY:
        return "stale"
    # R4-1：只要存在**不可核验**的锚点，即使其余锚点都新鲜，也不能判 fresh——
    # 否则「加一条 glob/散文锚点 + 一条正常锚点」即可让无法核验的声明静默通过。
    # 注意优先级：drifted/missing/stale 已在上方返回，真实漂移不会被本条掩盖。
    if any(mask):
        return "unverified"
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


def git_last_commit_sha(repo: Path, rel_path: str) -> Optional[str]:
    """B-02：锚点与文档是否在**同一次提交**中被改动（同步处理的判据）。"""
    return _run_git(repo, ["log", "-1", "--format=%H", "--", rel_path])


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


def load_baseline(path: Optional[Path]) -> Tuple[Dict[str, List[str]], str]:
    """读取锚点基线（墓碑），返回 ({doc: [anchor_path, ...]}, status)。

    status ∈ {ok, missing, corrupt, disabled}。R2D-1：**「保护不可得」必须与「无违规」
    在退出码上可区分**——账本缺席/损坏时 fail-closed（rc=2），不得静默当成零违规。
    """
    if path is None:
        return {}, "disabled"
    path = Path(path)
    if not path.exists():
        return {}, "missing"
    try:
        import json as _json

        data = _json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, "corrupt"
    docs = data.get("docs") if isinstance(data, dict) else None
    if not isinstance(docs, dict):
        return {}, "corrupt"
    parsed = {
        str(doc): [str(a) for a in anchors]
        for doc, anchors in docs.items()
        if isinstance(anchors, list)
    }
    # R2D2-1：结构合法但**为空**的账本同样是「保护不可得」——`{"docs":{}}` 只需一次
    # 文件编辑即可让墓碑整体失效，成本与删除账本相同。
    if not parsed:
        return {}, "empty"
    return parsed, "ok"


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
    """锚点墓碑判据：**全局多重集不得减少**（R2D-2）。

    早期版本按 doc 名逐条比对，导致「纯 git mv 改名」= 永远违规，而唯一出路
    `--write-baseline` 恰好也是能洗掉真实删除的命令。改为全局计数后：
    - 改名/拆分（锚点集合不变）→ 合法；
    - 删除文档、删锚点、缩减多锚点 → 计数下降 → 违规。
    """
    from collections import Counter

    # R4-3：旧账本可能存的是带行区间的原始形态（"src/ok.py:2"），比对前两侧统一归一，
    # 否则升级后会把「写法归一」误报成墓碑违规。
    def _norm(p: str) -> str:
        return _LINE_RANGE.sub("", p)

    base_counts: Counter = Counter()
    for anchors in baseline.values():
        base_counts.update(_norm(a) for a in anchors)
    cur_counts: Counter = Counter()
    for anchors in current.values():
        cur_counts.update(_norm(a) for a in anchors)
    deficits = {path: n - cur_counts.get(path, 0) for path, n in base_counts.items() if cur_counts.get(path, 0) < n}
    if not deficits:
        return []
    # R2D2-2：归属精确化——只把「该文档自身声明数下降」的路径算到它头上，
    # 未改动却共享同一锚点的文档不再被列成缺失；同一路径只计一次。
    removed = []
    for doc, anchors in baseline.items():
        base_c = Counter(_norm(a) for a in anchors)
        cur_c = Counter(_norm(a) for a in current.get(doc, []))
        missing = [p for p, n in base_c.items() if p in deficits and cur_c.get(p, 0) < n]
        if missing:
            removed.append({
                "doc": doc,
                "missing": sorted(set(missing)),
                "declared_now": current.get(doc, []),
            })
    if not removed:  # 防御：deficit 存在但无 doc 可归因（手改账本）
        removed.append({"doc": "<unknown>", "missing": sorted(deficits), "declared_now": []})
    return removed


def staged_paths(repo: Optional[Path]) -> Optional[set]:
    """B-02：返回暂存区变更路径集合；非 git 或无暂存区时返回 None。"""
    if repo is None:
        return None
    out = _run_git(repo, ["diff", "--cached", "--name-only"])
    if out is None:
        return None
    return {line.strip() for line in out.splitlines() if line.strip()}


def analyze(
    root: Path,
    repo: Optional[Path] = None,
    now_ts: Optional[int] = None,
    max_age_days: int = 180,
    baseline_path: Optional[Path] = None,
    staged: Optional[set] = None,
) -> Dict:
    """只读分析，返回 {'enabled', 'total_docs', 'declared', 'coverage', 'freshness_score', ...}。"""
    import time as _time

    root = Path(root).resolve()
    repo_path = Path(repo).resolve() if repo is not None else None
    now = int(now_ts if now_ts is not None else _time.time())
    current_anchors: Dict[str, List[str]] = {}
    # R3DC-1：存在性与「基线登记过」都必须**先于**形态判断生效——
    # 形态白名单已三次同族误伤（R3-1 → R3D-1 → R3DC-1），单靠字符类无法穷举合法文件名。
    baseline_preload, _ = load_baseline(baseline_path)
    baseline_paths = {p for anchors in baseline_preload.values() for p in anchors}

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
        unverifiable: List[bool] = []
        base_dir = repo_path if repo_path is not None else root
        for idx, anchor in enumerate(anchors):
            # 存在性优先：文件/目录真的在，就一定是路径（哪怕含空格/中文/行区间）。
            probe = base_dir / _LINE_RANGE.sub("", anchor["path"]).strip("/")
            exists_on_disk = probe.is_file() or probe.is_dir()
            # R4-2：基线救回只对「像路径」的写法生效（含 / 或 无空格）——
            # 否则散文锚点一旦被 --write-baseline 入账，就会翻转成 missing_anchor 硬红。
            rescue_by_baseline = anchor["path"] in baseline_paths and (
                "/" in anchor["path"] or " " not in anchor["path"]
            )
            if anchor.get("invalid") and (exists_on_disk or rescue_by_baseline):
                anchor = {**anchor, "invalid": False, "unverifiable": False}
                anchors[idx] = anchor
            if anchor.get("unverifiable"):
                unverifiable.append(True)
                exists.append(True)
                commits.append(None)
                tracked.append(False)
                continue
            unverifiable.append(False)
            # R2D-6：目录锚点（如 skills/doc-governance）按「存在」对待，git log 对目录有效。
            base = repo_path if repo_path is not None else root
            candidate = base / anchor["path"]
            anchor_exists = candidate.is_file() or candidate.is_dir()
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
            anchor_unverifiable=unverifiable,
            anchor_shas=(
                [git_last_commit_sha(repo_path, a["path"]) for a in anchors]
                if repo_path is not None else None
            ),
            doc_sha=(
                git_last_commit_sha(repo_path, doc_path.relative_to(repo_path).as_posix())
                if repo_path is not None else None
            ),
        )
        # B-02：pre-commit 场景——锚点被暂存而文档未同步，即为「本次提交引入的漂移」。
        # git log 对未提交改动不可见，因此必须显式比对暂存区。
        if staged is not None and status != "drifted":
            touched = [a["path"] for a in anchors if a["path"] in staged]
            # 暂存区路径相对**仓库根**，文档路径需按同一基准比对
            doc_repo_rel = (
                doc_path.relative_to(repo_path).as_posix() if repo_path is not None else rel_doc
            )
            if touched and doc_repo_rel not in staged:
                status = "drifted"
        record = {
            "doc": rel_doc,
            "status": status,
            "anchors": anchors,
            "invalid_anchors": [a["path"] for a in anchors if a.get("invalid")],
            "unverifiable_anchors": [a["path"] for a in anchors if a.get("unverifiable")],
            "verified_at": fields["verified_at"],
            "verified_commit": fields["verified_commit"],
        }
        docs.append(record)
        buckets[status].append(record)

    fresh_count = len(buckets["fresh"])
    score = round(FRESHNESS_MAX_SCORE * fresh_count / declared, 1) if declared else 0.0
    baseline, baseline_status = load_baseline(baseline_path)
    removed = _removed_from_baseline(baseline, current_anchors) if baseline else []
    return {
        "removed_from_baseline": removed,
        "baseline_status": baseline_status,
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
    parser.add_argument("--staged", action="store_true",
                        help="额外把「暂存区已改动但文档未同步」视为漂移（pre-commit 用）")
    parser.add_argument("--allow-unverified", action="store_true",
                        help="豁免 unverified / stale 的阻断（默认与 drifted 同权）")
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

    staged = staged_paths(repo) if args.staged else None
    res = analyze(
        root,
        repo=repo,
        max_age_days=args.max_age_days,
        baseline_path=baseline_path,
        staged=staged,
    )
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
        "baseline_status": res["baseline_status"],
        "waived": 0,
        "waiver_flag": None,
    }

    # R2D56-2 / R3-5：豁免必须在**产物**里留痕（JSON 可读），且 waived=0 时不得谎报已生效。
    if args.allow_unverified:
        summary["waived"] = summary["stale"] + summary["unverified"]
        summary["waiver_flag"] = "--allow-unverified"
        if summary["waived"]:
            print(
                f"⚠️  --allow-unverified 已生效：豁免 stale {summary['stale']} + unverified "
                f"{summary['unverified']}（共 {summary['waived']} 篇不阻断；drifted/missing/墓碑仍阻断）",
                file=sys.stderr if args.json else sys.stdout,
            )

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
        # R3D：明细必须带锚点名，否则 missing/drifted 只能靠 --json 定位。
        for bucket in ("missing_anchor", "drifted", "stale", "unverified"):
            for item in res[bucket]:
                paths = ", ".join(a["path"] for a in item["anchors"]) or "-"
                print(f"   - [{bucket}] {item['doc']}  ←  {paths}")
        if res["removed_from_baseline"]:
            print("   ⛔ 基线墓碑违规（声明被删除/缩减）:")
            for item in res["removed_from_baseline"]:
                print(f"      - {item['doc']} 缺失: {', '.join(item['missing']) or '全部锚点'}")
        # R3-3：invalid 锚点必须在文本输出可见并给修复提示，不能只藏在 --json 里。
        invalid_docs = [d for d in res["docs"] if d.get("invalid_anchors")]
        if invalid_docs:
            print("   ⚠️  invalid 锚点（不像路径，无法机械核验；请改写为仓库内相对路径）:")
            for item in invalid_docs:
                print(f"      - {item['doc']}: {', '.join(item['invalid_anchors'])}")

    # R2D-1：「保护不可得」不得与「无违规」同形。门禁模式下账本缺席/损坏 ⇒ rc=2。
    baseline_unusable = summary["baseline_status"] in ("missing", "corrupt") or (
        summary["baseline_status"] == "empty" and summary["declared"] > 0
    )
    if args.fail_on_drift and baseline_unusable:
        print(
            f"❌ 错误: 锚点基线不可用（{summary['baseline_status']}）：{baseline_path}。"
            "墓碑判据无法成立，按 fail-closed 处理；首次启用请先运行 --write-baseline 并提交该账本。",
            file=sys.stderr,
        )
        return 2
    # R2-2（R1-6 升级）：missing_anchor 是硬断裂（锚点被删除/移动），必须与 drifted 同权。
    # R2D-5：门禁口径改为「任何非 fresh 的已声明文档都阻断」——unverified 与 stale 不再是
    # 免检通道（否则「声明锚点但永不复核」可长期绿灯）。
    blocking = (
        summary["drifted"] + summary["missing_anchor"] + summary["removed_from_baseline"]
        + summary["stale"] + summary["unverified"]
    )
    blocking -= summary["waived"]
    if args.fail_on_drift and blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
