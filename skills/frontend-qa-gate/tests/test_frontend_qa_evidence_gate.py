"""Fail-closed disk evidence and adversarial tests for V2.0 check-qa-report.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
CHECKER = SKILL_DIR / "scripts" / "check-qa-report.py"
TEMPLATE_JSON = SKILL_DIR / "templates" / "qa-evidence-template.json"

PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
JPG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF"
WEBP_BYTES = b"RIFF\x24\x00\x00\x00WEBPVP8 "


def _run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECKER), *argv], capture_output=True, text=True, encoding="utf-8")


def _setup_bundle(root: Path) -> Path:
    (root / "shots").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "shots" / "v1.png").write_bytes(PNG_BYTES)
    (root / "shots" / "s1.jpg").write_bytes(JPG_BYTES)
    (root / "shots" / "a7.webp").write_bytes(WEBP_BYTES)
    (root / "logs" / "a7-axe.json").write_text('{"violations": []}', encoding="utf-8")
    (root / "logs" / "p1.log").write_text("bundle=42KB\n", encoding="utf-8")
    return root / "qa-evidence.json"


def _base_manifest() -> dict:
    return {
        "schema_version": 2,
        "artifact": {
            "name": "checkout-web",
            "url": "http://127.0.0.1:4173",
            "commit": "abc1234",
            "captured_at": "2026-11-24T10:00:00Z",
            "probe_tool": "playwright",
        },
        "runtime_signals": {"console_errors": 0, "page_errors": 0, "axe_critical_serious": 0},
        "automated_assertions": [
            {"id": "V1", "domain": "D-R", "status": "passed", "steps": "Check 320px width", "evidence": ["shots/v1.png", "logs/p1.log"]},
            {"id": "S1", "domain": "D-S", "status": "passed", "steps": "Cold load route", "evidence": "shots/s1.jpg"},
            {"id": "A7", "domain": "D-A", "status": "passed", "steps": "Run axe scan", "evidence": ["shots/a7.webp", "logs/a7-axe.json"]},
            {"id": "P1", "domain": "D-P", "status": "passed", "steps": "Check bundle delta", "evidence": "logs/p1.log"},
        ],
        "human_signoff": [
            {"id": "H-A5", "item": "VoiceOver primary flow", "status": "pending_human"},
            {"id": "H-V4/V5", "item": "Keyboard & safe-area", "status": "signed_off", "signer": "qa-lead", "signed_at": "2026-11-24"},
        ],
        "verdict": "PASS",
    }


def _write_manifest(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_happy_path_pass_with_pending_human_and_explicit_root(tmp_path: Path):
    manifest = _write_manifest(_setup_bundle(tmp_path), _base_manifest())
    res = _run(str(manifest), "--require-verdict=PASS")
    assert res.returncode == 0, res.stderr
    assert "VERDICT=PASS" in res.stdout and "Human sign-off pending: 1" in res.stdout

    sub = tmp_path / "sub"
    _setup_bundle(sub)
    (sub / "reports").mkdir(parents=True, exist_ok=True)
    nested = _write_manifest(sub / "reports" / "qa-evidence.json", _base_manifest())
    res_nested = _run(str(nested), "--require-verdict=PASS", f"--evidence-root={sub}")
    assert res_nested.returncode == 0, res_nested.stderr


def test_rejects_sibling_evidence_outside_manifest_dir_by_default(tmp_path: Path):
    sub = tmp_path / "sub"
    _setup_bundle(sub)
    (sub / "reports").mkdir(parents=True, exist_ok=True)
    nested = _write_manifest(sub / "reports" / "qa-evidence.json", _base_manifest())
    res = _run(str(nested))
    assert res.returncode == 1
    assert "evidence missing or empty" in res.stderr


@pytest.mark.parametrize(
    ("rel", "payload"),
    [
        ("shots/missing.png", None),
        ("shots/empty.png", b""),
        ("shots/fake.png", b"not a png image"),
        ("shots/fake.jpg", b"not a jpeg"),
        ("shots/fake.webp", b"RIFF0000FAKE"),
        ("logs/broken.json", b"{not-json"),
    ],
)
def test_rejects_missing_empty_and_forged_evidence(tmp_path: Path, rel: str, payload: bytes | None):
    manifest = _setup_bundle(tmp_path)
    if payload is not None:
        (tmp_path / rel).write_bytes(payload)
    data = _base_manifest()
    data["automated_assertions"][0]["evidence"] = rel
    _write_manifest(manifest, data)
    res = _run(str(manifest), "--require-verdict=PASS")
    assert res.returncode == 1


@pytest.mark.parametrize(
    "bad_path",
    ["/tmp/abs.png", "C:\\temp\\win.png", "../outside.png", "shots/../outside.png", "shots/v1.png\x00.txt"],
)
def test_rejects_absolute_and_traversal_paths(tmp_path: Path, bad_path: str):
    manifest = _setup_bundle(tmp_path)
    data = _base_manifest()
    data["automated_assertions"][0]["evidence"] = bad_path
    _write_manifest(manifest, data)
    assert _run(str(manifest)).returncode == 1


def test_rejects_symlink_escaping_evidence_root(tmp_path: Path):
    bundle = tmp_path / "bundle"
    manifest = _setup_bundle(bundle)
    secret = tmp_path / "outside.png"
    secret.write_bytes(PNG_BYTES)
    link = bundle / "shots" / "escape.png"
    try:
        link.symlink_to(secret)
    except OSError:
        pytest.skip("symlinks unavailable on current filesystem")
    data = _base_manifest()
    data["automated_assertions"][0]["evidence"] = "shots/escape.png"
    _write_manifest(manifest, data)
    res = _run(str(manifest))
    assert res.returncode == 1 and "escapes" in res.stderr


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d["runtime_signals"].update({"console_errors": 1}),
        lambda d: d["runtime_signals"].update({"page_errors": 2}),
        lambda d: d["runtime_signals"].update({"axe_critical_serious": 1}),
        lambda d: d["runtime_signals"].update({"console_errors": True}),
        lambda d: d["runtime_signals"].update({"page_errors": False}),
        lambda d: d["runtime_signals"].update({"axe_critical_serious": True}),
        lambda d: d.update({"schema_version": True}),
        lambda d: d["automated_assertions"][0].update({"status": "failed"}),
        lambda d: d["automated_assertions"][0].update({"status": "unverified"}),
        lambda d: [a.update({"status": "na", "na_reason": "not applicable"}) for a in d["automated_assertions"]],
        lambda d: d["human_signoff"][0].update({"status": "failed"}),
    ],
)
def test_rejects_pass_when_signals_booleans_or_statuses_fail(tmp_path: Path, mutator):
    manifest = _setup_bundle(tmp_path)
    data = _base_manifest()
    mutator(data)
    _write_manifest(manifest, data)
    assert _run(str(manifest), "--require-verdict=PASS").returncode == 1


def test_rejects_na_without_reason_duplicate_ids_and_min_assertions(tmp_path: Path):
    manifest = _setup_bundle(tmp_path)
    for mutate in (
        lambda d: d["automated_assertions"][0].update({"status": "na"}),
        lambda d: d["automated_assertions"][1].update({"id": "V1"}),
        lambda d: d["human_signoff"][1].pop("signer"),
        lambda d: d["human_signoff"][0].update({"status": "na"}),
    ):
        data = _base_manifest()
        mutate(data)
        _write_manifest(manifest, data)
        assert _run(str(manifest)).returncode == 1
    assert _run(str(_write_manifest(manifest, _base_manifest())), "--min-assertions=5").returncode == 1


def test_domain_coverage_and_no_domain_check_flag(tmp_path: Path):
    manifest = _setup_bundle(tmp_path)
    data = _base_manifest()
    data["automated_assertions"] = data["automated_assertions"][:3]
    _write_manifest(manifest, data)
    assert _run(str(manifest), "--min-assertions=3").returncode == 1
    res = _run(str(manifest), "--min-assertions=3", "--no-domain-check", "--require-verdict=PASS")
    assert res.returncode == 0, res.stderr


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d["artifact"].update({"url": "<http://localhost:3000>"}),
        lambda d: d["automated_assertions"][0].update({"steps": "<fill steps>"}),
        lambda d: d["automated_assertions"][0].update({"evidence": "shots/<v1.png>"}),
        lambda d: d.update({"verdict": "<PASS | FAIL>"}),
        lambda d: d.update({"verdict": "pass"}),
    ],
)
def test_rejects_placeholders_and_lowercase_verdict(tmp_path: Path, mutator):
    manifest = _setup_bundle(tmp_path)
    data = _base_manifest()
    mutator(data)
    _write_manifest(manifest, data)
    assert _run(str(manifest)).returncode == 1


def test_repo_evidence_template_fails_gate():
    assert _run(str(TEMPLATE_JSON)).returncode == 1


def test_valid_fail_blocked_and_partial_na_pass_reports(tmp_path: Path):
    manifest = _setup_bundle(tmp_path)
    fail_data = _base_manifest()
    fail_data["runtime_signals"]["console_errors"] = 1
    fail_data["verdict"] = "FAIL"
    _write_manifest(manifest, fail_data)
    assert _run(str(manifest)).returncode == 0
    assert _run(str(manifest), "--require-verdict=PASS").returncode == 1

    blocked_data = _base_manifest()
    for a in blocked_data["automated_assertions"]:
        a.update({"status": "na", "na_reason": "static landing without interaction"})
    blocked_data["verdict"] = "BLOCKED"
    _write_manifest(manifest, blocked_data)
    assert _run(str(manifest)).returncode == 0
    assert _run(str(manifest), "--require-verdict=PASS").returncode == 1

    partial_na = _base_manifest()
    for a in partial_na["automated_assertions"][1:]:
        a.update({"status": "na", "na_reason": "not applicable in this slice"})
    assert _run(str(_write_manifest(manifest, partial_na)), "--require-verdict=PASS").returncode == 0


def test_cli_usage_missing_file_and_bad_json_exit_codes(tmp_path: Path):
    valid = _write_manifest(_setup_bundle(tmp_path), _base_manifest())
    assert _run().returncode == 2
    assert _run(str(valid), "--unknown-flag").returncode == 2
    assert _run(str(tmp_path / "nonexistent.json")).returncode == 2
    assert _run(str(valid), "--min-assertions=0").returncode == 2
    assert _run(str(valid), f"--evidence-root={tmp_path / 'no-dir'}").returncode == 2

    broken = tmp_path / "broken.json"
    broken.write_text("{broken json", encoding="utf-8")
    assert _run(str(broken)).returncode == 1
