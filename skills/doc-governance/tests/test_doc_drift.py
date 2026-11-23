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
        written = self._run("--write-baseline")
        self.assertEqual(written.returncode, 0, written.stderr)
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

class TestR2Blockers(unittest.TestCase):
    """R2 终审判定的 3 个 Blockers 回归（基线墓碑 / 未跟踪锚点 / missing_anchor 硬断裂）"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r2_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, text):
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_r2_1_deleting_anchor_is_a_tombstone_violation(self):
        """删掉锚点声明必须被基线墓碑捕获，否则 7.5 → 15.0 的洗绿通道仍然敞开。"""
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        doc = self._write("a.md", make_doc("正文", anchors="src/a.py", verified="2026-11-22"))
        baseline = self.root / self.mod.DEFAULT_BASELINE_NAME
        first = self.mod.analyze(self.root, now_ts=2000, baseline_path=None)
        self.mod.write_baseline(baseline, first["docs"])

        doc.write_text(make_doc("正文", verified="2026-11-22"), encoding="utf-8")
        res = self.mod.analyze(self.root, now_ts=2000, baseline_path=baseline)
        self.assertFalse(res["enabled"])
        self.assertEqual(len(res["removed_from_baseline"]), 1)
        self.assertEqual(res["removed_from_baseline"][0]["doc"], "a.md")

    def test_r2_1_baseline_survives_partial_shrink(self):
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        (self.root / "src" / "b.py").write_text("y=2\n", encoding="utf-8")
        doc = self._write("a.md", make_doc("正文", anchors="src/a.py, src/b.py", verified="2026-11-22"))
        baseline = self.root / self.mod.DEFAULT_BASELINE_NAME
        self.mod.write_baseline(baseline, self.mod.analyze(self.root, now_ts=2000, baseline_path=None)["docs"])
        doc.write_text(make_doc("正文", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8")
        res = self.mod.analyze(self.root, now_ts=2000, baseline_path=baseline)
        self.assertEqual(res["removed_from_baseline"][0]["missing"], ["src/b.py"])

    def test_fenced_examples_are_not_declarations(self):
        body = "# 教程\n\n```markdown\n> - **代码锚点**: src/demo.py\n> - **复核于**: 2026-11-22\n```\n"
        fields = self.mod.parse_truth_fields(body)
        self.assertEqual(fields["anchors"], [])

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2_2_untracked_anchor_is_unverified_not_fresh(self):
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
        (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")  # 故意不 add：未跟踪
        docs = repo / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            make_doc("正文", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8"
        )
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(repo), "--write-baseline"],
            capture_output=True, text=True, check=True,
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "check-doc-drift.py"),
                "--root",
                str(docs),
                "--repo",
                str(repo),
                "--fail-on-drift",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("unverified", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2_2_missing_anchor_fails_on_drift_flag(self):
        repo = self.root
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
        (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True, env=env)
        docs = repo / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(
            make_doc("正文", anchors="src/gone.py", verified="2026-11-22"), encoding="utf-8"
        )
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(repo), "--write-baseline"],
            capture_output=True, text=True, check=True,
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "check-doc-drift.py"),
                "--root",
                str(docs),
                "--repo",
                str(repo),
                "--fail-on-drift",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("missing_anchor", proc.stdout)


class TestR2DeltaBlockers(unittest.TestCase):
    """Delta 终审 R2D-1/R2D-2/R2D-3 回归"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_delta_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, text):
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def _git(self, args, env):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=env, capture_output=True, text=True)

    def _init_repo(self):
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        self._git(["init", "-q"], env)
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git(["add", "-A"], env)
        self._git(["commit", "-q", "-m", "init"], env)
        return env, docs

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d_1_missing_baseline_fails_closed(self):
        env, docs = self._init_repo()
        (docs / "a.md").write_text(make_doc("正文", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8")
        self._git(["add", "-A"], env)
        self._git(["commit", "-q", "-m", "doc"], env)
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("基线不可用", proc.stderr)

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d_1_corrupt_baseline_fails_closed(self):
        env, docs = self._init_repo()
        (docs / "a.md").write_text(make_doc("正文", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8")
        (docs / self.mod.DEFAULT_BASELINE_NAME).write_text("{not json", encoding="utf-8")
        self._git(["add", "-A"], env)
        self._git(["commit", "-q", "-m", "doc"], env)
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("corrupt", proc.stderr)

    def test_r2d_2_renaming_doc_keeps_anchor_multiset(self):
        """纯改名（锚点集合不变）不得触发墓碑违规。"""
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        doc = self._write("old.md", make_doc("正文", anchors="src/a.py", verified="2026-11-22"))
        baseline = self.root / self.mod.DEFAULT_BASELINE_NAME
        self.mod.write_baseline(baseline, self.mod.analyze(self.root, now_ts=2000, baseline_path=None)["docs"])
        doc.rename(self.root / "new.md")
        res = self.mod.analyze(self.root, now_ts=2000, baseline_path=baseline)
        self.assertEqual(res["removed_from_baseline"], [])
        self.assertEqual(res["baseline_status"], "ok")

    def test_r2d_2_deleting_anchor_still_violates_after_multiset_switch(self):
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        doc = self._write("a.md", make_doc("正文", anchors="src/a.py", verified="2026-11-22"))
        baseline = self.root / self.mod.DEFAULT_BASELINE_NAME
        self.mod.write_baseline(baseline, self.mod.analyze(self.root, now_ts=2000, baseline_path=None)["docs"])
        doc.write_text(make_doc("正文", verified="2026-11-22"), encoding="utf-8")
        res = self.mod.analyze(self.root, now_ts=2000, baseline_path=baseline)
        self.assertEqual(res["removed_from_baseline"][0]["missing"], ["src/a.py"])

    def test_r2d_3_future_verification_date_is_unverified(self):
        status = self.mod.classify_doc(
            anchor_paths=["src/a.py"],
            anchor_exists=[True],
            anchor_last_commits=[1000],
            verified_ts=10 ** 11,
            now_ts=1000,
            max_age_days=180,
        )
        self.assertEqual(status, "unverified")



class TestR2D2Blockers(unittest.TestCase):
    """放行确认 R2D2-1/R2D2-3 回归：空账本与 warn 报告诚实度"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r2d2_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _make_repo(self):
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "a.md").write_text(make_doc("正文", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d2_1_empty_baseline_fails_closed(self):
        docs = self._make_repo()
        (docs / self.mod.DEFAULT_BASELINE_NAME).write_text('{"version": 1, "docs": {}}', encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("empty", proc.stderr)

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d2_1_empty_baseline_without_declarations_is_not_an_error(self):
        self._git("init", "-q")
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("# A\n\n无锚点\n", encoding="utf-8")
        (docs / self.mod.DEFAULT_BASELINE_NAME).write_text('{"version": 1, "docs": {}}', encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d2_3_warn_mode_never_says_perfect_when_drifted(self):
        docs = self._make_repo()
        self.mod.write_baseline(
            docs / self.mod.DEFAULT_BASELINE_NAME,
            self.mod.analyze(docs, repo=self.root, baseline_path=None)["docs"],
        )
        (self.root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "change anchor")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(docs), "--truth=warn"],
            capture_output=True, text=True,
        )
        self.assertIn("drifted", proc.stdout)
        self.assertNotIn("完美", proc.stdout)



class TestR2D56AnchorsAndGate(unittest.TestCase):
    """R2D-5（非 fresh 即阻断）/ R2D-6（glob 与目录锚点）/ R2D2-2（墓碑归属）"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r2d56_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _repo_with(self, files):
        self._git("init", "-q")
        for rel, content in files.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs

    def _run(self, docs, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), *extra],
            capture_output=True, text=True,
        )

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d6_glob_anchor_is_unverified_not_missing(self):
        docs = self._repo_with({"src/a.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("正文", anchors="src/**", verified="2026-11-22"), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["status"], "unverified")
        self.assertEqual(payload["summary"]["missing_anchor"], 0)

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d6_directory_anchor_is_accepted(self):
        docs = self._repo_with({"src/a.py": "x=1\n"})
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        (docs / "a.md").write_text(
            make_doc("正文", anchors="src", verified=f"2026-11-22 / commit {sha}"), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--fail-on-drift").stdout)
        self.assertEqual(payload["docs"][0]["status"], "fresh")

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d5_unverified_blocks_gate_by_default(self):
        docs = self._repo_with({"src/a.py": "x=1\n"})
        (docs / "a.md").write_text(make_doc("正文", anchors="src/a.py"), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        blocked = self._run(docs, "--fail-on-drift")
        self.assertEqual(blocked.returncode, 1, blocked.stdout + blocked.stderr)
        allowed = self._run(docs, "--fail-on-drift", "--allow-unverified")
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_r2d2_2_tombstone_attribution_only_hits_shrinking_doc(self):
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        self._write_ok = True
        (self.root / "a.md").write_text(make_doc("甲", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8")
        (self.root / "b.md").write_text(make_doc("乙", anchors="src/a.py", verified="2026-11-22"), encoding="utf-8")
        baseline = self.root / self.mod.DEFAULT_BASELINE_NAME
        self.mod.write_baseline(baseline, self.mod.analyze(self.root, now_ts=2000, baseline_path=None)["docs"])
        (self.root / "a.md").write_text(make_doc("甲", verified="2026-11-22"), encoding="utf-8")
        res = self.mod.analyze(self.root, now_ts=2000, baseline_path=baseline)
        self.assertEqual([item["doc"] for item in res["removed_from_baseline"]], ["a.md"])
        self.assertEqual(res["removed_from_baseline"][0]["missing"], ["src/a.py"])



class TestFollowupP2P3(unittest.TestCase):
    """计划 §9 后续四项回归：R2D56-1 / R2D56-3 / R2D56-4 / R2D56-2"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_p2p3_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _init(self, files):
        self._git("init", "-q")
        for rel, content in files.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs, self._git("rev-parse", "--short", "HEAD").stdout.strip()

    def _run(self, docs, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), *extra],
            capture_output=True, text=True,
        )

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d56_1_glob_anchor_must_not_mask_real_drift(self):
        docs, sha = self._init({"src/x.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("正文", anchors="src/x.py, src/**", verified=f"2026-11-22 / commit {sha}"),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        time.sleep(1)  # 提交时间按秒计，同秒提交无法体现先后
        (self.root / "src" / "x.py").write_text("x=2\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "change code")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["status"], "drifted")
        self.assertEqual(payload["summary"]["drifted"], 1)

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d56_3_bold_wrapped_real_anchor_is_not_glob(self):
        docs, sha = self._init({"src/pkg/x.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("正文", anchors="**src/pkg/x.py**", verified=f"2026-11-22 / commit {sha}"),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["status"], "fresh")
        self.assertEqual(payload["docs"][0]["anchors"][0]["path"], "src/pkg/x.py")

    def test_r2d56_4_prose_anchor_is_invalid_not_missing(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_text(
            make_doc("正文", anchors="见附录 A", verified="2026-11-22"), encoding="utf-8"
        )
        res = self.mod.analyze(self.root / "docs", now_ts=2000)
        self.assertEqual(res["declared"], 1)
        self.assertEqual(len(res["missing_anchor"]), 0)
        self.assertEqual(res["docs"][0]["status"], "unverified")
        self.assertEqual(res["docs"][0]["invalid_anchors"], ["见附录 A"])

    @unittest.skipUnless(shutil.which("git"), "环境无 git")
    def test_r2d56_2_allow_unverified_leaves_a_trace(self):
        docs, _ = self._init({"src/x.py": "x=1\n"})
        (docs / "a.md").write_text(make_doc("正文", anchors="src/x.py"), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        proc = self._run(docs, "--fail-on-drift", "--allow-unverified")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("--allow-unverified", proc.stdout)
        self.assertIn("豁免", proc.stdout)




class TestR3Fixes(unittest.TestCase):
    """R3-1/2/3/5 回归：合法路径不得被 invalid 判据吞掉"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r3_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _run(self, docs, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), *extra],
            capture_output=True, text=True,
        )

    def _repo(self, files):
        self._git("init", "-q")
        for rel, content in files.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs, self._git("rev-parse", "--short", "HEAD").stdout.strip()

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3_1_deleted_path_with_space_is_missing_anchor(self):
        """含空格的合法路径被删后必须 missing_anchor，不得静默 fresh。"""
        docs, sha = self._repo({"docs2/my file.md": "x\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="docs2/my file.md", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        ok = self._run(docs, "--json", "--allow-unverified")
        self.assertEqual(json.loads(ok.stdout)["docs"][0]["status"], "fresh", ok.stdout)

        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        self._git("rm", "-q", "docs2/my file.md")
        self._git("commit", "-q", "-m", "remove")
        gone = self._run(docs, "--json", "--allow-unverified", "--fail-on-drift")
        self.assertEqual(gone.returncode, 1, gone.stdout + gone.stderr)
        self.assertEqual(json.loads(gone.stdout)["docs"][0]["status"], "missing_anchor")

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3_1_cjk_and_at_sign_paths_are_paths(self):
        docs, sha = self._repo({"src/\u6587\u6863/x@y+1.md": "x\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/\u6587\u6863/x@y+1.md", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["status"], "fresh")
        self.assertEqual(payload["docs"][0]["invalid_anchors"], [])

    def test_r3_1_prose_without_slash_is_still_invalid(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_text(
            make_doc("body", anchors="see appendix A", verified="2026-11-22"), encoding="utf-8"
        )
        res = self.mod.analyze(self.root / "docs", now_ts=2000)
        self.assertEqual(res["docs"][0]["status"], "unverified")
        self.assertEqual(res["docs"][0]["invalid_anchors"], ["see appendix A"])

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3_2_bold_spanning_multiple_anchors(self):
        docs, sha = self._repo({"src/a.py": "a\n", "src/b.py": "b\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="**src/a.py, src/b.py**", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual([a["path"] for a in payload["docs"][0]["anchors"]], ["src/a.py", "src/b.py"])
        self.assertEqual(payload["docs"][0]["status"], "fresh")

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3_5_waiver_is_recorded_in_json_and_not_reported_when_zero(self):
        docs, _ = self._repo({"src/x.py": "x\n"})
        (docs / "a.md").write_text(make_doc("body", anchors="src/x.py"), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        payload = json.loads(self._run(docs, "--json", "--fail-on-drift", "--allow-unverified").stdout)
        self.assertIn("waived", payload["summary"])
        self.assertEqual(payload["summary"]["waived"], 1)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3_3_invalid_anchor_is_announced_in_text_output(self):
        docs, _ = self._repo({"seed.txt": "seed\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="see appendix A", verified="2026-11-22"), encoding="utf-8"
        )
        proc = self._run(docs, "--allow-unverified")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("invalid", proc.stdout)
        self.assertIn("see appendix A", proc.stdout)



class TestR3DFixes(unittest.TestCase):
    """R3D-1/3/4 回归：行区间锚点、死代码、audit 的 invalid 可见性"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r3d_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _run(self, docs, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), *extra],
            capture_output=True, text=True,
        )

    def _repo(self, files):
        self._git("init", "-q")
        for rel, content in files.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs, self._git("rev-parse", "--short", "HEAD").stdout.strip()

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3d_1_root_level_file_with_line_range_is_a_path(self):
        """Makefile:2 是「根级无扩展名文件 + 行区间」，不得判 invalid。"""
        docs, sha = self._repo({"Makefile": "all:\n\techo hi\n", "LICENSE": "MIT\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="Makefile:2, LICENSE:1", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["invalid_anchors"], [])
        self.assertEqual(payload["docs"][0]["status"], "fresh")

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3d_1_line_range_anchor_still_detects_drift(self):
        docs, sha = self._repo({"Makefile": "all:\n\techo hi\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="Makefile:2", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        time.sleep(1)
        (self.root / "Makefile").write_text("all:\n\techo bye\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "change")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["status"], "drifted")

    def test_r3d_3_prose_hint_dead_code_removed(self):
        self.assertFalse(hasattr(self.mod, "_PROSE_HINT"))

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3d_4_audit_truth_block_exposes_invalid(self):
        docs, _ = self._repo({"seed.txt": "seed\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="see appendix A", verified="2026-11-22"), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        res = self.audit.audit_health(docs, repo_path=self.root)
        self.assertIn("invalid", res["truth"])
        self.assertEqual(res["truth"]["invalid"], 1)
        self.assertEqual(res["truth"]["invalid_docs"], ["a.md"])

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3d_missing_detail_names_the_anchor(self):
        docs, _ = self._repo({"seed.txt": "seed\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/gone.py", verified="2026-11-22"), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        proc = self._run(docs, "--allow-unverified")
        self.assertIn("src/gone.py", proc.stdout)



class TestR3DC1ExistenceFirst(unittest.TestCase):
    """R3DC-1 根治：存在性优先于形态判断（同族事故第三次）"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r3dc_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _run(self, docs, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), *extra],
            capture_output=True, text=True,
        )

    def _repo(self, files):
        self._git("init", "-q")
        for rel, content in files.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs, self._git("rev-parse", "--short", "HEAD").stdout.strip()

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3dc_1_existing_cjk_file_with_line_range_is_a_path(self):
        """\u8bf4\u660e:3 对应文件存在时必须是路径，不得判 invalid。"""
        docs, sha = self._repo({"\u8bf4\u660e": "line1\nline2\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="\u8bf4\u660e:3", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["invalid_anchors"], [])
        self.assertEqual(payload["docs"][0]["status"], "fresh")

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r3dc_1_baseline_registered_prose_like_path_is_missing_not_invalid(self):
        """基线登记过的锚点被删除后必须 missing_anchor，不得退化成 invalid 静默放行。"""
        docs, sha = self._repo({"\u8bf4\u660e": "line1\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="\u8bf4\u660e:3", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        self._git("rm", "-q", "\u8bf4\u660e")
        self._git("commit", "-q", "-m", "remove")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified", "--fail-on-drift").stdout)
        self.assertEqual(payload["docs"][0]["status"], "missing_anchor")
        self.assertEqual(payload["docs"][0]["invalid_anchors"], [])

    def test_r3dc_1_prose_still_invalid_when_never_existed(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_text(
            make_doc("body", anchors="\u89c1\u9644\u5f55 A", verified="2026-11-22"), encoding="utf-8"
        )
        res = self.mod.analyze(self.root / "docs", now_ts=2000)
        self.assertEqual(res["docs"][0]["status"], "unverified")
        self.assertEqual(res["docs"][0]["invalid_anchors"], ["\u89c1\u9644\u5f55 A"])



class TestR4Fixes(unittest.TestCase):
    """R4-1/2/3 回归：invalid 不得被其他 fresh 锚点掩盖；基线救回与墓碑比对的边界"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_r4_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _run(self, docs, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), *extra],
            capture_output=True, text=True,
        )

    def _repo(self, files):
        self._git("init", "-q")
        for rel, content in files.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir(exist_ok=True)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        return docs, self._git("rev-parse", "--short", "HEAD").stdout.strip()

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r4_1_invalid_anchor_must_not_be_masked_by_fresh_anchor(self):
        """场景 X：\u8bf4\u660e:3 与一条 fresh 锚点并存，删 \u8bf4\u660e 后不得判 fresh。"""
        docs, sha = self._repo({"\u8bf4\u660e": "a\n", "src/ok.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="\u8bf4\u660e:3, src/ok.py", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        self._git("rm", "-q", "\u8bf4\u660e")
        self._git("commit", "-q", "-m", "remove")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified", "--fail-on-drift").stdout)
        status = payload["docs"][0]["status"]
        self.assertIn(status, ("missing_anchor", "unverified"), payload)
        self.assertEqual(payload["summary"]["fresh"], 0)

    def test_r4_1_prose_plus_fresh_anchor_is_not_fresh(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "src").mkdir()
        (self.root / "docs" / "src" / "ok.py").write_text("x=1\n", encoding="utf-8")
        (self.root / "docs" / "a.md").write_text(
            make_doc("body", anchors="see appendix A, src/ok.py", verified="2026-11-22"),
            encoding="utf-8",
        )
        res = self.mod.analyze(self.root / "docs", now_ts=2000)
        self.assertEqual(res["docs"][0]["status"], "unverified")
        self.assertEqual(len(res["fresh"]), 0)

    def test_r4_1_drifted_still_wins_over_invalid(self):
        """R2D56-1 不得回退：真实锚点漂移必须仍判 drifted。"""
        (self.root / "docs").mkdir()
        (self.root / "docs" / "src").mkdir()
        (self.root / "docs" / "src" / "ok.py").write_text("x=1\n", encoding="utf-8")
        (self.root / "docs" / "a.md").write_text(
            make_doc("body", anchors="see appendix A, src/ok.py", verified="2026-11-22"), encoding="utf-8"
        )
        status = self.mod.classify_doc(
            anchor_paths=["see appendix A", "src/ok.py"],
            anchor_exists=[True, True],
            anchor_last_commits=[None, 2000],
            verified_ts=1000,
            now_ts=2100,
            max_age_days=180,
            anchor_unverifiable=[True, False],
        )
        self.assertEqual(status, "drifted")

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r4_1_unregistered_invalid_plus_fresh_must_not_be_fresh(self):
        """报告场景 X：锚点从未入账本，invalid + fresh 并存时不得判 fresh（rc 必须非 0）。"""
        docs, sha = self._repo({"\u8bf4\u660e": "a\n", "src/ok.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="\u8bf4\u660e:3, src/ok.py", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        # 故意不跑 --write-baseline：账本里没有该锚点
        self._git("rm", "-q", "\u8bf4\u660e")
        self._git("commit", "-q", "-m", "remove")
        payload = json.loads(self._run(docs, "--json", "--allow-unverified").stdout)
        self.assertEqual(payload["docs"][0]["status"], "unverified", payload)
        self.assertEqual(payload["summary"]["fresh"], 0)

    def test_r4_2_prose_registered_in_baseline_stays_invalid(self):
        """散文锚点入账后不得翻转成 missing_anchor。"""
        (self.root / "docs").mkdir()
        (self.root / "docs" / "a.md").write_text(
            make_doc("body", anchors="see appendix A", verified="2026-11-22"), encoding="utf-8"
        )
        baseline = self.root / "docs" / self.mod.DEFAULT_BASELINE_NAME
        self.mod.write_baseline(baseline, self.mod.analyze(self.root / "docs", now_ts=2000, baseline_path=None)["docs"])
        res = self.mod.analyze(self.root / "docs", now_ts=2000, baseline_path=baseline)
        self.assertEqual(res["docs"][0]["status"], "unverified")
        self.assertEqual(len(res["missing_anchor"]), 0)

    def test_r4_3_legacy_baseline_with_line_range_is_not_a_tombstone_violation(self):
        """旧账本存的是带行区间的原始形态，升级后不得误报墓碑违规。"""
        (self.root / "docs").mkdir()
        (self.root / "docs" / "src").mkdir()
        (self.root / "docs" / "src" / "ok.py").write_text("x=1\n", encoding="utf-8")
        (self.root / "docs" / "a.md").write_text(
            make_doc("body", anchors="src/ok.py:2", verified="2026-11-22"), encoding="utf-8"
        )
        baseline = self.root / "docs" / self.mod.DEFAULT_BASELINE_NAME
        baseline.write_text(
            '{"version": 1, "docs": {"a.md": ["src/ok.py:2"]}}', encoding="utf-8"
        )
        res = self.mod.analyze(self.root / "docs", now_ts=2000, baseline_path=baseline)
        self.assertEqual(res["removed_from_baseline"], [])



class TestStagedDrift(unittest.TestCase):
    """B-02：pre-commit 场景下「本次提交引入的漂移」必须可见"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_staged_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def test_staged_anchor_change_without_doc_update_is_drifted(self):
        """锚点被暂存、文档未同步 ⇒ 提交前即判 drifted（否则 hook 结构性失明）。"""
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip() if False else None
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-22 / commit " + sha), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(
            subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                            "--repo", str(self.root), "--write-baseline"], capture_output=True).returncode, 0
        )
        # 只暂存锚点改动，不动文档
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        self._git("add", "src/a.py")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)

    def test_same_commit_sync_is_not_drifted(self):
        """锚点与文档在**同一次提交**中改动 ⇒ 视为同步处理，提交后不得判漂移。"""
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-22 / commit " + sha), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                        "--repo", str(self.root), "--write-baseline"], capture_output=True)
        doc_sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        # 同一次提交里改锚点 + 刷新复核点
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-22 / commit " + doc_sha), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "sync anchor and doc")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)



class TestBD1BD2(unittest.TestCase):
    """BD-1/BD-2：同提交豁免的内容校验 + pre-commit 索引一致性"""

    def setUp(self):
        self.mod = load_module("check_doc_drift", SCRIPTS_DIR / "check-doc-drift.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_bd_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1_same_commit_without_refreshing_verified_date_is_drifted(self):
        """同一提交里改锚点 + 给文档加注释（未刷新复核日期）⇒ 仍应 drifted。"""
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        doc = docs / "a.md"
        doc.write_text(make_doc("body", anchors="src/a.py", verified="2026-11-22 / commit " + sha), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                        "--repo", str(self.root), "--write-baseline"], capture_output=True)
        time.sleep(1)
        # 改锚点 + 文档只加一行注释（复核点不动）
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        doc.write_text(doc.read_text(encoding="utf-8") + "\n补充说明\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "sneaky")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)



class TestBD1Staged(unittest.TestCase):
    """BD-1-R：--staged 口径的补充回归"""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="doc_drift_bd1r_"))
        self.env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True, env=self.env, capture_output=True, text=True)

    def _setup(self):
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-22 / commit " + sha), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                        "--repo", str(self.root), "--write-baseline"], capture_output=True)
        return docs

    def _setup_multi(self):
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "a1.py").write_text("a=1\n", encoding="utf-8")
        (self.root / "src" / "a2.py").write_text("b=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a1.py, src/a2.py", verified="2026-11-22 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                        "--repo", str(self.root), "--write-baseline"], capture_output=True)
        return docs, sha

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_staged_doc_without_refreshing_verified_is_drifted(self):
        docs = self._setup()
        time.sleep(1)
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        (docs / "a.md").write_text((docs / "a.md").read_text(encoding="utf-8") + "\n注释\n", encoding="utf-8")
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_missing_anchor_not_masked_by_staged_refresh(self):
        docs = self._setup()
        (self.root / "src" / "a.py").unlink()
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-22 / commit deadbee"), encoding="utf-8"
        )
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("missing_anchor", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_staged_blank_line_only_is_drifted(self):
        """C2：只加一个空行不得被视为刷新「复核于」。"""
        docs = self._setup()
        time.sleep(1)
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        (docs / "a.md").write_text((docs / "a.md").read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_multi_anchor_partial_drift_not_masked(self):
        """G（BD-1-R2）：A1 已提交漂移，仅暂存 A2 + 刷新日期时，A1 漂移不得被洗白。"""
        docs, sha = self._setup_multi()
        time.sleep(1)
        (self.root / "src" / "a1.py").write_text("a=2\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "drift-a1")
        (self.root / "src" / "a2.py").write_text("b=2\n", encoding="utf-8")
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a1.py, src/a2.py", verified="2026-11-23 / commit " + sha),
            encoding="utf-8",
        )
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_unicode_anchor_and_doc_paths_detected(self):
        """非 ASCII 路径：中文锚点与中文文档名在 --staged 下必须被正确识别。"""
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "锚点.py").write_text("x=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        doc = docs / "文档.md"
        doc.write_text(
            make_doc("body", anchors="src/锚点.py", verified="2026-11-22 / commit " + sha), encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                        "--repo", str(self.root), "--write-baseline"], capture_output=True)
        time.sleep(1)
        (self.root / "src" / "锚点.py").write_text("x=2\n", encoding="utf-8")
        doc.write_text(doc.read_text(encoding="utf-8") + "\n注释\n", encoding="utf-8")
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_staged_legit_refresh_to_head_passes(self):
        """L：锚点改动 + 「复核于」指向本次提交父提交（HEAD）⇒ 合法，rc=0/fresh。"""
        docs = self._setup()
        head = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        time.sleep(1)
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-23 / commit " + head), encoding="utf-8"
        )
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("fresh", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_unicode_doc_legit_refresh_passes(self):
        """P3 正例：中文文档名 + 合法刷新（复核于指向 HEAD）⇒ rc=0/fresh。"""
        self._git("init", "-q")
        (self.root / "src").mkdir()
        (self.root / "src" / "锚点.py").write_text("x=1\n", encoding="utf-8")
        docs = self.root / "docs"
        docs.mkdir()
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "init")
        sha = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        doc = docs / "文档.md"
        doc.write_text(make_doc("body", anchors="src/锚点.py", verified="2026-11-22 / commit " + sha), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        head = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
                        "--repo", str(self.root), "--write-baseline"], capture_output=True)
        time.sleep(1)
        (self.root / "src" / "锚点.py").write_text("x=2\n", encoding="utf-8")
        doc.write_text(make_doc("body", anchors="src/锚点.py", verified="2026-11-23 / commit " + head), encoding="utf-8")
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("fresh", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_new_doc_with_modified_existing_anchor_is_drifted(self):
        """BK-0055：新文档 + 修改既有锚点，无法证明复核点覆盖新版本 ⇒ drifted（fail-closed）。"""
        docs = self._setup()
        head = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        time.sleep(1)
        (self.root / "src" / "a.py").write_text("x=2\n", encoding="utf-8")
        (docs / "new.md").write_text(
            make_doc("body", anchors="src/a.py", verified="2026-11-23 / commit " + head), encoding="utf-8"
        )
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drifted", proc.stdout)

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_bd1r_new_doc_with_new_anchor_passes(self):
        """BK-0055：新文档 + 新锚点同提交 ⇒ 属于同一次提交，rc=0/fresh。"""
        docs = self._setup()
        head = self._git("rev-parse", "--short", "HEAD").stdout.strip()
        time.sleep(1)
        (self.root / "src" / "b.py").write_text("y=1\n", encoding="utf-8")
        (docs / "new.md").write_text(
            make_doc("body", anchors="src/b.py", verified="2026-11-23 / commit " + head), encoding="utf-8"
        )
        self._git("add", "-A")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", str(docs),
             "--repo", str(self.root), "--staged", "--fail-on-drift"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("fresh", proc.stdout)


if __name__ == "__main__":
    unittest.main()
