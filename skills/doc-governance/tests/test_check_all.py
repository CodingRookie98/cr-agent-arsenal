#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_check_all.py - 门禁聚合器 (BK-0048) 契约测试"""

import shutil
import subprocess
import sys
import tempfile
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

    def test_docstring_describes_six_gates(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("六道门禁", source)
        self.assertNotIn("五道门禁", source)

    def test_version_sync_failure_suggests_control_sync_not_trim_revision(self):
        """版本一致门禁失败时不得误导用户执行 trim-revision.py。"""
        tmp_dir = Path(tempfile.mkdtemp(prefix="check_all_ver_"))
        self.addCleanup(shutil.rmtree, tmp_dir, True)
        (tmp_dir / "explanation").mkdir(parents=True)
        (tmp_dir / "explanation" / "drift.md").write_text(
            "# Drift\n\n"
            "> **文档控制信息**\n"
            "> - **文档标识**: EXP-1\n"
            "> - **当前版本**: V2.0.0\n\n"
            "### 修订历史记录 (Revision History)\n\n"
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **V1.0.0** | 2026-11-23 | AI Agent | 架构师 | 初版 |\n",
            encoding="utf-8",
            newline="\n",
        )
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(tmp_dir), "--quiet"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        output = proc.stdout + proc.stderr
        self.assertIn("【版本一致】", output)
        section = output.split("【版本一致】", 1)[1].split("\n【", 1)[0]
        self.assertNotIn("trim-revision.py", section)
        self.assertIn("check-doc-control-sync.py", section)


if __name__ == "__main__":
    unittest.main()
