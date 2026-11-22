#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_golden_tasks.py - 可回答性评测 (BK-0049) 契约测试"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
REPO_ROOT = SCRIPTS_DIR.parents[2]
SCRIPT = SCRIPTS_DIR / "check-golden-tasks.py"


class TestGoldenTasks(unittest.TestCase):
    def test_twenty_assertions_and_json_shape(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"], cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(len(payload["results"]), 20)
        self.assertEqual(set(payload["counts"]), {"pass", "gap", "fail"})
        for item in payload["results"]:
            self.assertIn(item["status"], ("pass", "gap", "fail"))
            self.assertTrue(item["detail"])

    def test_gap_does_not_block(self):
        """GAP 是知识缺口而非结构缺陷，不得导致非零退出。"""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"], cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        payload = json.loads(proc.stdout)
        if payload["counts"]["fail"] == 0:
            self.assertEqual(proc.returncode, 0)
        else:
            self.assertEqual(proc.returncode, 1)

    def test_quiet_mode_only_shows_non_pass(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--quiet"], cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        for line in proc.stdout.splitlines():
            if line.strip().startswith(("✅", "🕳️", "❌")):
                self.assertNotIn("✅", line)


if __name__ == "__main__":
    unittest.main()
