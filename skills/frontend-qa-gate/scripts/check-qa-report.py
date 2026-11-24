#!/usr/bin/env python3
"""check-qa-report.py — Fail-closed V2.0 frontend QA evidence JSON gate."""
from __future__ import annotations

import argparse, json, re, sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"<(?:[^>\s][^>\n]*)?>")
WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:")
CORE_DOMAINS, VALID_DOMAINS = frozenset({"D-R", "D-S", "D-A", "D-P"}), frozenset({"D-R", "D-S", "D-A", "D-P", "D-B"})
AUTO_STATUSES, HUMAN_STATUSES = frozenset({"passed", "failed", "unverified", "na"}), frozenset({"pending_human", "signed_off", "failed", "na"})
MAGIC = {".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff"}
SIGNAL_KEYS = ("console_errors", "page_errors", "axe_critical_serious")


def _ok_str(val: object) -> bool:
    return isinstance(val, str) and bool(val.strip()) and not PLACEHOLDER_RE.search(val)


def _collect_records(raw: list[object], kind: str, errs: list[str]) -> list[tuple[dict[str, object], str]]:
    seen, records = set(), []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            errs.append(f"{kind}[{idx}] must be an object")
            continue
        val = entry.get("id")
        tag = val if _ok_str(val) else f"{kind}[{idx}]"
        if not _ok_str(val):
            errs.append(f"{kind}[{idx}].id missing, blank, or placeholder")
        elif val in seen:
            errs.append(f"duplicate {kind} id: {val!r}")
        else:
            seen.add(val)
        records.append((entry, tag))
    return records


def _check_meta(data: dict[str, object], errs: list[str]) -> dict[str, object]:
    art, sig = data.get("artifact"), data.get("runtime_signals")
    if not isinstance(art, dict):
        errs.append("artifact must be an object")
    else:
        for k in ("name", "url", "commit", "captured_at", "probe_tool"):
            if not _ok_str(art.get(k)):
                errs.append(f"artifact.{k} missing, blank, or placeholder")
    if not isinstance(sig, dict):
        errs.append("runtime_signals must be an object")
        return {}
    for k in SIGNAL_KEYS:
        val = sig.get(k)
        if (k != "axe_critical_serious" or k in sig) and not (type(val) is int and val >= 0):
            errs.append(f"runtime_signals.{k} must be non-negative int")
    return sig


def _check_ev_file(rel: object, root: Path, errs: list[str], aid: str) -> None:
    if not _ok_str(rel) or "\x00" in rel:
        errs.append(f"{aid}: invalid evidence path {rel!r}")
        return
    norm = rel.replace("\\", "/")
    if norm.startswith("/") or WIN_DRIVE_RE.match(norm) or Path(rel).is_absolute() or ".." in norm.split("/"):
        errs.append(f"{aid}: forbidden absolute or '..' evidence path: {rel!r}")
        return
    try:
        path = (root / norm).resolve()
    except (OSError, ValueError) as exc:
        errs.append(f"{aid}: cannot resolve path {rel!r}: {exc}")
        return
    if not path.is_relative_to(root):
        errs.append(f"{aid}: path escapes evidence-root: {rel!r}")
    elif not path.is_file() or path.stat().st_size == 0:
        errs.append(f"{aid}: evidence missing or empty: {rel!r}")
    else:
        ext = path.suffix.lower()
        try:
            with path.open("rb") as fh:
                head = fh.read(12)
            if ext in MAGIC and not head.startswith(MAGIC[ext]):
                errs.append(f"{aid}: invalid {ext} magic header: {rel!r}")
            elif ext == ".webp" and not (len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP"):
                errs.append(f"{aid}: invalid WEBP magic header: {rel!r}")
            elif ext == ".json":
                json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errs.append(f"{aid}: invalid evidence {rel!r}: {exc}")


def _check_assertions(
    data: dict[str, object], min_n: int, no_dom: bool, root: Path, errs: list[str]
) -> list[dict[str, object]]:
    raw = data.get("automated_assertions")
    if not isinstance(raw, list) or not raw:
        errs.append("automated_assertions must be a non-empty array")
        return []
    if len(raw) < min_n:
        errs.append(f"automated_assertions count {len(raw)} < min-assertions {min_n}")
    doms, records = set(), _collect_records(raw, "automated_assertions", errs)
    for item, tag in records:
        dom, st = item.get("domain"), item.get("status")
        if isinstance(dom, str) and dom in VALID_DOMAINS:
            doms.add(dom)
        else:
            errs.append(f"{tag}: invalid domain {dom!r}")
        if st not in AUTO_STATUSES:
            errs.append(f"{tag}: invalid status {st!r}")
        if not _ok_str(item.get("steps")):
            errs.append(f"{tag}: steps missing or placeholder")
        if st == "na" and not _ok_str(item.get("na_reason")):
            errs.append(f"{tag}: na requires na_reason")
        if st == "passed":
            ev = item.get("evidence")
            paths = [ev] if isinstance(ev, str) else ev if isinstance(ev, list) and ev else []
            if not paths:
                errs.append(f"{tag}: passed requires non-empty string/list evidence")
            for p in paths:
                _check_ev_file(p, root, errs, tag)
    if not no_dom and not CORE_DOMAINS.issubset(doms):
        errs.append(f"missing core domains: {', '.join(sorted(CORE_DOMAINS - doms))}")
    return [item for item, _ in records]


def _check_human(data: dict[str, object], errs: list[str]) -> list[dict[str, object]]:
    if "human_signoff" not in data:
        return []
    raw = data["human_signoff"]
    if not isinstance(raw, list):
        errs.append("human_signoff must be an array")
        return []
    records = _collect_records(raw, "human_signoff", errs)
    for entry, tag in records:
        if not _ok_str(entry.get("item")):
            errs.append(f"{tag}: item missing or placeholder")
        st = entry.get("status")
        if st not in HUMAN_STATUSES:
            errs.append(f"{tag}: invalid human status {st!r}")
        elif st == "signed_off" and not (_ok_str(entry.get("signer")) and _ok_str(entry.get("signed_at"))):
            errs.append(f"{tag}: signed_off requires signer and signed_at")
        elif st == "na" and not _ok_str(entry.get("na_reason")):
            errs.append(f"{tag}: na requires na_reason")
    return [entry for entry, _ in records]


def _validate(data: object, args: argparse.Namespace, root: Path) -> tuple[list[str], str, dict[str, int], int]:
    if not isinstance(data, dict):
        return ["manifest root must be a JSON object"], "BLOCKED", {}, 0
    errs: list[str] = []
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 2:
        errs.append(f"schema_version must be integer 2 (got {data.get('schema_version')!r})")
    sig = _check_meta(data, errs)
    auto = _check_assertions(data, args.min_assertions, args.no_domain_check, root, errs)
    human = _check_human(data, errs)
    sig_bad = any(type(sig.get(k)) is int and sig[k] > 0 for k in SIGNAL_KEYS)
    if sig_bad or any(a.get("status") == "failed" for a in auto) or any(h.get("status") == "failed" for h in human):
        derived = "FAIL"
    elif any(a.get("status") == "unverified" for a in auto) or not any(a.get("status") == "passed" for a in auto):
        derived = "BLOCKED"
    else:
        derived = "PASS"
    verdict = data.get("verdict")
    if not isinstance(verdict, str) or verdict not in {"PASS", "FAIL", "BLOCKED"}:
        errs.append(f"verdict must be PASS/FAIL/BLOCKED (got {verdict!r})")
    elif verdict != derived:
        errs.append(f"declared verdict {verdict!r} != derived {derived!r}")
    if args.require_verdict == "PASS" and derived != "PASS":
        errs.append(f"--require-verdict=PASS rejected derived verdict {derived}")
    counts = {s: sum(1 for a in auto if a.get("status") == s) for s in AUTO_STATUSES}
    return errs, derived, counts, sum(1 for h in human if h.get("status") == "pending_human")


def _die(msg: str, code: int = 2) -> int:
    sys.stderr.write(f"error: {msg}\n")
    return code


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        getattr(s, "reconfigure", lambda **_: None)(encoding="utf-8", newline="\n")
    p = argparse.ArgumentParser(description="Validate V2.0 frontend QA evidence JSON manifest.")
    p.add_argument("manifest")
    p.add_argument("--require-verdict", choices=("PASS",))
    p.add_argument("--min-assertions", type=int, default=4)
    p.add_argument("--evidence-root")
    p.add_argument("--no-domain-check", action="store_true")
    args = p.parse_args(argv)
    if args.min_assertions < 1:
        return _die(f"--min-assertions must be >= 1 (got {args.min_assertions})")
    manifest = Path(args.manifest)
    if not manifest.is_file():
        return _die(f"manifest not found: {manifest}")
    root = Path(args.evidence_root) if args.evidence_root is not None else manifest.resolve().parent
    if args.evidence_root is not None and not root.is_dir():
        return _die(f"--evidence-root is not a directory: {root}")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except OSError as exc:
        return _die(f"cannot read manifest: {exc}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _die(f"invalid JSON manifest: {exc}", 1)
    errs, derived, counts, pending = _validate(data, args, root.resolve())
    if errs:
        return _die("\nerror: ".join(errs), 1)
    summary = ", ".join(f"{s}={counts[s]}" for s in ("passed", "failed", "unverified", "na"))
    print(f"VERDICT={derived} | assertions={sum(counts.values())} ({summary}) | Human sign-off pending: {pending}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
