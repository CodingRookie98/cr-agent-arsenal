#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_doc_drift.py - 文档漂移检测器 (check-doc-drift.py) 契约测试

覆盖:
  1. 控制头三字段解析（来源 / 代码锚点 / 复核于），含缺省、格式容错与锚点越界拒绝；
  2. 文档级分类状态机（missing_anchor > drifted > stale > unverified > fresh）；
  3. 真值分（freshness）计算：零声明不颁发满分（enabled=false, score=0）；
  4. L2 集成：临时 git 仓库中「复核后新增提交 ⇒ drifted」与 CLI 退出码 0/1/2。
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import importlib.util

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_doc(body: str, anchors: str = None, verified: str = None, sources: str = None) -> str:
    lines = ["# 标题", "", "> **文档控制信息**"]
    if sources is not None:
        lines.append(f"> - **来源**: {sources}")
    if anchors is not None:
        lines.append(f"> - **代码锚点**: {anchors}")
    if verified is not None:
        lines.append(f"> - **复核于**: {verified}")
    return "\n".join(lines) + "\n\n" + body


class TestParseTruthFields(unittest.TestCase):
    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")

    def test_parses_three_fields(self):
        content = make_doc(
            "正文",
            anchors="`src/api/routes.ts:120-168`, src/models/user.ts",
            verified="2026-11-20 / commit a1b2c3d",
            sources="raw/spec.md",
        )
        fields = self.mod.parse_truth_fields(content)
        self.assertEqual(fields["sources"], ["raw/spec.md"])
        self.assertEqual(fields["verified_at"], "2026-11-20")
        self.assertEqual(fields["verified_commit"], "a1b2c3d")
        self.assertEqual(
            [a["path"] for a in fields["anchors"]],
            ["src/api/routes.ts", "src/models/user.ts"],
        )
        self.assertEqual(fields["anchors"][0]["line_start"], 120)
        self.assertEqual(fields["anchors"][0]["line_end"], 168)

    def test_missing_fields_are_empty(self):
        fields = self.mod.parse_truth_fields("# 标题\n\n无控制头正文\n")
        self.assertEqual(fields["sources"], [])
        self.assertEqual(fields["anchors"], [])
        self.assertIsNone(fields["verified_at"])
        self.assertIsNone(fields["verified_commit"])

    def test_rejects_out_of_tree_anchor(self):
        fields = self.mod.parse_truth_fields(make_doc("x", anchors="../etc/passwd, /abs/path.py"))
        self.assertEqual([a["path"] for a in fields["anchors"]], [])

    def test_tolerates_fullwidth_separators_and_backticks(self):
        fields = self.mod.parse_truth_fields(make_doc("x", anchors="`a/b.py`、c/d.py；e/f.py"))
        self.assertEqual([a["path"] for a in fields["anchors"]], ["a/b.py", "c/d.py", "e/f.py"])


class TestClassifyDoc(unittest.TestCase):
    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")

    def test_missing_anchor_wins_over_drift(self):
        status = self.mod.classify_doc(
            anchor_paths=["src/gone.py"],
            anchor_exists=[False],
            anchor_last_commits=[None],
            verified_ts=1000,
            now_ts=2000,
            max_age_days=180,
        )
        self.assertEqual(status, "missing_anchor")

    def test_commit_after_verification_is_drift(self):
        status = self.mod.classify_doc(
            anchor_paths=["src/a.py"],
            anchor_exists=[True],
            anchor_last_commits=[2000],
            verified_ts=1000,
            now_ts=2100,
            max_age_days=180,
        )
        self.assertEqual(status, "drifted")

    def test_no_verified_ts_is_unverified(self):
        status = self.mod.classify_doc(
            anchor_paths=["src/a.py"],
            anchor_exists=[True],
            anchor_last_commits=[2000],
            verified_ts=None,
            now_ts=2100,
            max_age_days=180,
        )
        self.assertEqual(status, "unverified")

    def test_old_verification_is_stale(self):
        day = 86400
        status = self.mod.classify_doc(
            anchor_paths=["src/a.py"],
            anchor_exists=[True],
            anchor_last_commits=[1000],
            verified_ts=1000,
            now_ts=1000 + 200 * day,
            max_age_days=180,
        )
        self.assertEqual(status, "stale")

    def test_fresh(self):
        status = self.mod.classify_doc(
            anchor_paths=["src/a.py"],
            anchor_exists=[True],
            anchor_last_commits=[900],
            verified_ts=1000,
            now_ts=1100,
            max_age_days=180,
        )
        self.assertEqual(status, "fresh")


class TestAnalyze(unittest.TestCase):
    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_l1_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_zero_declared_docs_is_not_enabled_and_scores_zero(self):
        (self.root / "a.md").write_text(make_doc("正文"), encoding="utf-8")
        res = self.mod.analyze(self.root, repo=None, now_ts=2000, max_age_days=180)
        self.assertFalse(res["enabled"])
        self.assertEqual(res["declared"], 0)
        self.assertEqual(res["freshness_score"], 0.0)

    def test_declared_doc_requires_existing_anchor_file(self):
        (self.root / "a.md").write_text(make_doc("正文", anchors="src/a.py"), encoding="utf-8")
        res = self.mod.analyze(self.root, repo=None, now_ts=2000, max_age_days=180)
        self.assertTrue(res["enabled"])
        self.assertEqual(res["declared"], 1)
        self.assertEqual([d["doc"] for d in res["missing_anchor"]], ["a.md"])
        self.assertEqual(res["freshness_score"], 0.0)


NEEDS_GIT = unittest.skipUnless(shutil.which("git"), "环境无 git，跳过 L2 集成用例")


@NEEDS_GIT
class TestCliIntegration(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="doc_drift_l2_"))
        self.docs = self.repo / "docs"
        self.docs.mkdir()
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        self._git("init", "-q")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        self._git("add", "-A")
        self._commit("init")
        self.verify_sha = self._git("rev-parse", "HEAD").strip()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, capture_output=True, text=True, env=self.env, check=True
        ).stdout

    def _commit(self, msg):
        self._git("commit", "-q", "-m", msg)

    def _run(self, *extra):
        script = SCRIPTS_DIR / "check-doc-drift.py"
        return subprocess.run(
            [sys.executable, str(script), "--root", str(self.docs), "--repo", str(self.repo), *extra],
            capture_output=True,
            text=True,
        )

    def test_drift_after_anchor_change_with_fail_flag(self):
        (self.docs / "a.md").write_text(
            make_doc("正文", anchors="src/a.py", verified=f"2026-11-20 / commit {self.verify_sha}"),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._commit("doc")
        ok = self._run("--json")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        first = json.loads(ok.stdout)
        self.assertEqual(first["summary"]["drifted"], 0)

        time.sleep(1)
        (self.repo / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        self._git("add", "-A")
        self._commit("change code")

        drifted = self._run("--json", "--fail-on-drift")
        self.assertEqual(drifted.returncode, 1, drifted.stderr)
        payload = json.loads(drifted.stdout)
        self.assertEqual(payload["summary"]["drifted"], 1)
        self.assertEqual(payload["docs"][0]["status"], "drifted")

    def test_non_git_directory_exits_two(self):
        plain = Path(tempfile.mkdtemp(prefix="doc_drift_nogit_"))
        try:
            script = SCRIPTS_DIR / "check-doc-drift.py"
            proc = subprocess.run(
                [sys.executable, str(script), "--root", str(plain), "--repo", str(plain)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("git", proc.stderr.lower())
        finally:
            shutil.rmtree(plain, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

class TestAuditTruthIntegration(unittest.TestCase):
    """AC-1 / AC-5：真值块接入 audit-doc-health 的契约"""

    def setUp(self):
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_truth_audit_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel: str, text: str):
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_ac1_zero_declared_scores_zero_without_touching_structure_score(self):
        self._write("tutorials/a.md", "# A\n\n正文\n")
        self._write("index.md", "# Index\n\n- [A](./tutorials/a.md)\n")
        baseline = self.audit.audit_health(self.root, truth_mode="off")
        res = self.audit.audit_health(self.root)
        truth = res["truth"]
        self.assertFalse(truth["enabled"])
        self.assertEqual(truth["declared"], 0)
        self.assertEqual(truth["freshness_score"], 0.0)
        # 结构分语义不变：开/关真值轴得到同一个 total_score（A/B 对照，而非硬编码阈值）
        self.assertEqual(res["total_score"], baseline["total_score"])
        passed, reasons = self.audit.evaluate_verdict(res, 70.0)
        self.assertTrue(passed, reasons)

    def test_require_mode_blocks_when_axis_not_enabled(self):
        self._write("tutorials/a.md", "# A\n\n正文\n")
        self._write("index.md", "# Index\n\n- [A](./tutorials/a.md)\n")
        res = self.audit.audit_health(self.root, truth_mode="require")
        passed, reasons = self.audit.evaluate_verdict(res, 80.0)
        self.assertFalse(passed)
        self.assertTrue(any("真值轴未启用" in r for r in reasons), reasons)

    def test_ac5_evidence_archive_is_skipped(self):
        self._write("tutorials/a.md", make_doc("正文"))
        self._write(
            "project/reviews/r1.md",
            make_doc("凭据", anchors="src/a.py", verified="2026-11-20"),
        )
        self._write("index.md", "# Index\n\n- [A](./tutorials/a.md)\n")
        res = self.audit.audit_health(self.root)
        self.assertEqual(res["truth"]["declared"], 0)
        self.assertFalse(res["truth"]["enabled"])

    def test_declared_missing_anchor_is_reported(self):
        self._write("tutorials/a.md", make_doc("正文", anchors="src/not-there.py", verified="2026-11-20"))
        self._write("index.md", "# Index\n\n- [A](./tutorials/a.md)\n")
        res = self.audit.audit_health(self.root)
        truth = res["truth"]
        self.assertTrue(truth["enabled"])
        self.assertEqual(truth["declared"], 1)
        self.assertEqual(truth["missing_anchor"], 1)
        self.assertEqual(truth["missing_anchor_docs"], ["tutorials/a.md"])
        self.assertEqual(truth["freshness_score"], 0.0)

class TestReviewFixes(unittest.TestCase):
    """R1 阻断项回归（R1-1 / R1-2 / R1-3 + 路径切分加固）"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_fix_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, text):
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_r1_1_date_only_verification_covers_the_whole_day(self):
        """R1-1：日期型「复核于」按当日末刻起算，同日提交不得判成漂移。"""
        import datetime

        content = make_doc("正文", anchors="src/a.py", verified="2026-11-22")
        ts = self.mod._verified_ts(self.mod.parse_truth_fields(content), None)
        expected = int(
            datetime.datetime(2026, 11, 22, 23, 59, 59, tzinfo=datetime.timezone.utc).timestamp()
        )
        self.assertEqual(ts, expected)
        status = self.mod.classify_doc(
            anchor_paths=["src/a.py"],
            anchor_exists=[True],
            anchor_last_commits=[expected - 60],
            verified_ts=ts,
            now_ts=expected,
            max_age_days=180,
        )
        self.assertEqual(status, "fresh")

    def test_comma_inside_path_is_not_a_separator(self):
        fields = self.mod.parse_truth_fields(make_doc("x", anchors="src/a,b.py"))
        self.assertEqual([a["path"] for a in fields["anchors"]], ["src/a,b.py"])

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r1_3_shallow_repository_fails_closed(self):
        repo = self.root
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
        (repo / "src").mkdir()
        (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, env=env)
        docs = repo / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(make_doc("正文", anchors="src/a.py"), encoding="utf-8")
        git_dir = subprocess.run(
            ["git", "rev-parse", "--absolute-git-dir"], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()
        (Path(git_dir) / "shallow").write_text("", encoding="utf-8")

        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "check-doc-drift.py"),
                "--root",
                str(docs),
                "--repo",
                str(repo),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("浅克隆", proc.stderr)

    def test_r1_2_require_mode_blocks_on_low_coverage(self):
        """删锚点可以把 7.5 洗成 15.0；覆盖率下限必须拦住这条通道。"""
        for i in range(10):
            self._write(f"tutorials/t{i}.md", "# T\n\n正文\n")
        self._write("tutorials/anchor.md", make_doc("正文", anchors="src/a.py", verified="2026-11-22"))
        self._write("index.md", "# Index\n\n- [T](./tutorials/t0.md)\n")
        res = self.audit.audit_health(self.root, truth_mode="require")
        self.assertAlmostEqual(res["truth"]["coverage"], 1 / 11, places=4)
        passed, reasons = self.audit.evaluate_verdict(res, 70.0, 12.0, 0.5)
        self.assertFalse(passed)
        self.assertTrue(any("覆盖率" in r for r in reasons), reasons)
