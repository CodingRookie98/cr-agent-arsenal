#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_check_all.py - 门禁聚合器 (BK-0048) 契约测试"""

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
REPO_ROOT = SCRIPTS_DIR.parents[2]
SCRIPT = SCRIPTS_DIR / "check-all.py"


class TestCheckAll(unittest.TestCase):
    def test_help_exits_zero(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--full", proc.stdout)

    def test_all_gates_pass_on_current_tree(self):
        """当前树应全绿；失败时输出足以定位（这正是 hook 的判据）。"""
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--quiet"], cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_quiet_mode_is_silent_on_success(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--quiet"], cwd=str(REPO_ROOT), capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
