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



class TestFollowupP2P3(unittest.TestCase):
    """计划 9 后续四项回归：R2D56-1 / R2D56-3 / R2D56-4 / R2D56-2"""

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

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r2d56_1_glob_anchor_must_not_mask_real_drift(self):
        docs, sha = self._init({"src/x.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="src/x.py, src/**", verified="2026-11-22 / commit " + sha),
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

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r2d56_3_bold_wrapped_real_anchor_is_not_glob(self):
        docs, sha = self._init({"src/pkg/x.py": "x=1\n"})
        (docs / "a.md").write_text(
            make_doc("body", anchors="**src/pkg/x.py**", verified="2026-11-22 / commit " + sha),
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
            make_doc("body", anchors="see appendix A", verified="2026-11-22"), encoding="utf-8"
        )
        res = self.mod.analyze(self.root / "docs", now_ts=2000)
        self.assertEqual(res["declared"], 1)
        self.assertEqual(len(res["missing_anchor"]), 0)
        self.assertEqual(res["docs"][0]["status"], "unverified")
        self.assertEqual(res["docs"][0]["invalid_anchors"], ["see appendix A"])

    @unittest.skipUnless(shutil.which("git"), "env has no git")
    def test_r2d56_2_allow_unverified_leaves_a_trace(self):
        docs, _ = self._init({"src/x.py": "x=1\n"})
        (docs / "a.md").write_text(make_doc("body", anchors="src/x.py"), encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "doc")
        self.assertEqual(self._run(docs, "--write-baseline").returncode, 0)
        proc = self._run(docs, "--fail-on-drift", "--allow-unverified")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("--allow-unverified", proc.stdout)
        self.assertIn("\u8c41\u514d", proc.stdout)


if __name__ == "__main__":
    unittest.main()
