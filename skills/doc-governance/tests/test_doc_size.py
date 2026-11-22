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


if __name__ == "__main__":
    unittest.main()
