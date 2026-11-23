#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_doc_size.py - 文档体量门禁 (RFC-0008) 契约测试

AC-1 全库达标；AC-2 新增超限阻断；AC-3 存量未恶化仅警告；
AC-4 存量恶化阻断；AC-5 基线缺失/损坏视为无基线；AC-6 行数只警告；AC-7 达标文档提示清理。
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def load_module(name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_doc(root: Path, rel: str, lines: int = 5, line_len: int = 20):
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    body = ["# T"] + ["x" * line_len] * (lines - 1)
    target.write_text("\n".join(body) + "\n", encoding="utf-8")
    return target


class TestDocSize(unittest.TestCase):
    def setUp(self):
        self.mod = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_size_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _check(self, **kw):
        return self.mod.check_doc_size(self.root, **kw)

    def _baseline(self, payload):
        path = self.root / self.mod.SIZE_BASELINE_NAME
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_ac1_all_within_limits(self):
        write_doc(self.root, "reference/a.md", lines=10, line_len=50)
        res = self._check()
        self.assertEqual(res["issues"], [])

    def test_ac2_new_oversized_doc_blocks(self):
        write_doc(self.root, "reference/big.md", lines=40, line_len=2000)
        res = self._check(max_bytes=1000, max_line=100)
        self.assertTrue(res["issues"], res)

    def test_ac3_baseline_unchanged_is_warning_only(self):
        write_doc(self.root, "reference/big.md", lines=40, line_len=2000)
        first = self._check(max_bytes=1000, max_line=100)
        baseline = self._baseline({"version": 1, "docs": {"reference/big.md": first["docs"]["reference/big.md"]}})
        res = self._check(max_bytes=1000, max_line=100, baseline_path=baseline)
        self.assertEqual(res["issues"], [], res)
        self.assertTrue(res["warnings"], res)

    def test_ac4_baseline_growth_blocks(self):
        write_doc(self.root, "reference/big.md", lines=40, line_len=2000)
        first = self._check(max_bytes=1000, max_line=100)
        baseline = self._baseline({"version": 1, "docs": {"reference/big.md": first["docs"]["reference/big.md"]}})
        write_doc(self.root, "reference/big.md", lines=80, line_len=2000)
        res = self._check(max_bytes=1000, max_line=100, baseline_path=baseline)
        self.assertTrue(res["issues"], res)

    def test_ac5_missing_or_corrupt_baseline_means_no_baseline(self):
        write_doc(self.root, "reference/big.md", lines=40, line_len=2000)
        missing = self._check(max_bytes=1000, max_line=100, baseline_path=self.root / "nope.json")
        self.assertTrue(missing["issues"], missing)
        corrupt = self.root / self.mod.SIZE_BASELINE_NAME
        corrupt.write_text("{not json", encoding="utf-8")
        res = self._check(max_bytes=1000, max_line=100, baseline_path=corrupt)
        self.assertTrue(res["issues"], res)

    def test_ac6_line_count_only_warns(self):
        write_doc(self.root, "reference/long.md", lines=900, line_len=10)
        res = self._check(max_bytes=10_000_000, max_line=10_000, max_lines=800)
        self.assertEqual(res["issues"], [], res)
        self.assertTrue(any("行" in w for w in res["warnings"]), res)

    def test_ac7_compliant_doc_in_baseline_is_flagged_for_cleanup(self):
        write_doc(self.root, "reference/small.md", lines=5, line_len=10)
        baseline = self._baseline({"version": 1, "docs": {"reference/small.md": {"bytes": 999999, "longest_line": 9999}}})
        res = self._check(baseline_path=baseline)
        self.assertEqual(res["issues"], [])
        self.assertTrue(any("清理" in w for w in res["warnings"]), res)

    def test_write_baseline_roundtrip(self):
        write_doc(self.root, "reference/big.md", lines=40, line_len=2000)
        path = self.mod.write_size_baseline(self.root, max_bytes=1000, max_line=100)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertIn("reference/big.md", data["docs"])

    def test_reference_articles_are_exempt_from_size_gate(self):
        """RFC-0008 / GOVERNANCE §4.1：reference/articles/** 外部转载文献不参与体量门禁，普通文档仍阻断。"""
        # 构造 >64 KB 且单行 >1000 字符的文档
        write_doc(self.root, "reference/articles/ext.md", lines=60, line_len=1200)
        write_doc(self.root, "reference/articles/nested/ext2.md", lines=60, line_len=1200)
        res_exempt = self._check()
        self.assertEqual(res_exempt["issues"], [], res_exempt)
        self.assertEqual(res_exempt["warnings"], [], res_exempt)
        self.assertNotIn("reference/articles/ext.md", res_exempt["docs"])
        self.assertNotIn("reference/articles/nested/ext2.md", res_exempt["docs"])

        # 同大小普通文档与前缀相似目录（reference/articles-extra/）必须被阻断
        write_doc(self.root, "explanation/a.md", lines=60, line_len=1200)
        write_doc(self.root, "reference/articles-extra/other.md", lines=60, line_len=1200)
        res_block = self._check()
        self.assertEqual(len(res_block["issues"]), 2, res_block)
        self.assertTrue(any("explanation/a.md" in i for i in res_block["issues"]), res_block)
        self.assertTrue(any("reference/articles-extra/other.md" in i for i in res_block["issues"]), res_block)
        self.assertFalse(any("reference/articles/ext.md" in i for i in res_block["issues"]), res_block)

    def test_audit_health_and_cli_respect_max_doc_bytes_and_line(self):
        """回归：audit_health 与 CLI 体检必须将 --max-doc-bytes / --max-doc-line 透传至 check_doc_size。"""
        ctrl = (
            "> **文档控制信息**\n"
            "> - **文档标识**: {doc_id}\n"
            "> - **当前版本**: V1.0.0\n\n"
            "### 修订历史记录 (Revision History)\n\n"
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **V1.0.0** | 2026-11-23 | AI Agent | 架构师 | 初版 |\n"
        )
        (self.root / "explanation").mkdir(parents=True, exist_ok=True)
        (self.root / "explanation" / "sample.md").write_text(
            "# Sample\n\n" + ctrl.format(doc_id="EXP-1") + "\n" + ("a" * 80) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (self.root / "index.md").write_text(
            "# Index\n\n" + ctrl.format(doc_id="IDX-1") + "\n- [Sample](./explanation/sample.md)\n",
            encoding="utf-8",
            newline="\n",
        )

        # 函数级：默认阈值不阻断，收紧阈值必须产出 doc_size issues
        default_res = self.mod.audit_health(self.root)
        self.assertEqual(default_res["doc_size"]["issues"], [], default_res["doc_size"])

        tight_bytes = self.mod.audit_health(self.root, max_doc_bytes=100)
        self.assertTrue(tight_bytes["doc_size"]["issues"], tight_bytes["doc_size"])

        tight_line = self.mod.audit_health(self.root, max_doc_line=50)
        self.assertTrue(tight_line["doc_size"]["issues"], tight_line["doc_size"])

        # CLI 级：默认 PASS；传入 --max-doc-bytes / --max-doc-line 必须触发体量阻断（rc != 0）
        script = str(SCRIPTS_DIR / "audit-doc-health.py")
        cli_ok = subprocess.run(
            [sys.executable, script, "--root", str(self.root)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(cli_ok.returncode, 0, cli_ok.stdout + cli_ok.stderr)

        cli_bytes = subprocess.run(
            [sys.executable, script, "--root", str(self.root), "--max-doc-bytes", "100"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertNotEqual(cli_bytes.returncode, 0, cli_bytes.stdout + cli_bytes.stderr)
        self.assertIn("文档体量超限", cli_bytes.stdout + cli_bytes.stderr)

        cli_line = subprocess.run(
            [sys.executable, script, "--root", str(self.root), "--max-doc-line", "50"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertNotEqual(cli_line.returncode, 0, cli_line.stdout + cli_line.stderr)
        self.assertIn("文档体量超限", cli_line.stdout + cli_line.stderr)



class TestSizeRobustness(unittest.TestCase):
    """B-03~B-06：体量门禁的健壮性"""

    def setUp(self):
        self.mod = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_size_rb_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _check(self, **kw):
        return self.mod.check_doc_size(self.root, **kw)

    def test_b03_uppercase_and_markdown_suffix_are_scanned(self):
        """.MD / .markdown 不得逃逸扫描。"""
        (self.root / "reference").mkdir()
        (self.root / "reference" / "BIG.MD").write_text("x" * 5000, encoding="utf-8")
        (self.root / "reference" / "big.markdown").write_text("y" * 5000, encoding="utf-8")
        res = self._check(max_bytes=1000, max_line=10_000)
        self.assertEqual(len(res["issues"]), 2, res)

    def test_b04_u2028_does_not_break_longest_line(self):
        """U+2028 不是换行符：不得用它绕过最长单行上限。"""
        (self.root / "reference").mkdir()
        (self.root / "reference" / "a.md").write_text("x" * 600 + "\u2028" + "y" * 600, encoding="utf-8")
        res = self._check(max_bytes=10_000_000, max_line=1000)
        self.assertTrue(res["issues"], res)

    def test_b05_non_numeric_baseline_values_do_not_crash(self):
        (self.root / "reference").mkdir()
        (self.root / "reference" / "a.md").write_text("x" * 5000, encoding="utf-8")
        baseline = self.root / self.mod.SIZE_BASELINE_NAME
        baseline.write_text('{"version":1,"docs":{"reference/a.md":{"bytes":"abc","longest_line":null}}}', encoding="utf-8")
        res = self._check(max_bytes=1000, max_line=10_000, baseline_path=baseline)
        self.assertTrue(res["issues"], res)

    def test_b06_unreadable_file_is_fail_closed(self):
        """不可读文件不得按 0 字节放行。"""
        import os
        (self.root / "reference").mkdir()
        target = self.root / "reference" / "secret.md"
        target.write_text("x" * 5000, encoding="utf-8")
        os.chmod(target, 0)
        try:
            res = self._check(max_bytes=1000, max_line=10_000)
            self.assertTrue(res["issues"], res)
        finally:
            os.chmod(target, 0o644)




class TestAssertionFixes(unittest.TestCase):
    """B-10 / B-14：断言层修正"""

    def setUp(self):
        self.mod = load_module("check_golden_tasks", SCRIPTS_DIR / "check-golden-tasks.py")
        self.root = Path(tempfile.mkdtemp(prefix="golden_fix_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_b10_g02_accepts_shixian_jihua(self):
        (self.root / "proposals").mkdir()
        (self.root / "proposals" / "RFC-1.md").write_text(
            "# RFC-1\n\n> - **当前状态**: In Review\n\n实施计划：[x](../project/plans/x.md)\n",
            encoding="utf-8",
        )
        status, detail = self.mod.g02_rfc_has_plan(self.root)
        self.assertEqual(status, "pass", detail)

    def test_b14_g14_empty_active_dir_is_reported(self):
        (self.root / "project" / "backlog" / "active").mkdir(parents=True)
        status, detail = self.mod.g14_backlog_acceptance(self.root)
        self.assertEqual(status, "gap", detail)


if __name__ == "__main__":
    unittest.main()
