#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_llms_split.py - 分层机器地图 (RFC-0006) 契约测试

覆盖:
  1. 默认模式零破坏（AC-1）；
  2. split 生成：根体量、子地图齐全、条目格式（AC-2）；
  3. 幂等（AC-3）；空象限删子文件（AC-4）；
  4. 根体量超限不落盘 + exit 1（AC-5）；
  5. audit 多文件比对：手改/缺失/多余子地图均判漂移（AC-6/7）；
  6. 路由文件 docs/AGENTS.md 行数与必需小节断言（AC-8）。
"""

import importlib.util
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


def write_doc(root: Path, rel: str, title: str, body: str = "正文", desc: str = ""):
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    head = f"# {title}\n\n"
    if desc:
        head += f"> 描述: {desc}\n\n"
    target.write_text(head + body + "\n", encoding="utf-8")
    return target


class TestBuildMap(unittest.TestCase):
    def setUp(self):
        self.mod = load_module("generate_llms_txt", SCRIPTS_DIR / "generate-llms-txt.py")
        self.root = Path(tempfile.mkdtemp(prefix="llms_split_"))
        write_doc(self.root, "proposals/RFC-0001-a.md", "RFC-0001 A", desc="提案一")
        write_doc(self.root, "reference/rules/x.md", "规则 X", desc="规则说明")
        write_doc(self.root, "index.md", "Index")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_ac1_default_mode_is_single_file_and_matches_legacy(self):
        """AC-1：默认模式产物必须与既有 generate_llms_txt 逐字节一致。"""
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=False)
        self.assertEqual(list(built.keys()), ["llms.txt"])

        out = Path(tempfile.mkdtemp(prefix="llms_legacy_")) / "llms.txt"
        try:
            self.mod.generate_llms_txt(self.root, out, project_name="Demo")
            self.assertEqual(built["llms.txt"], out.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(out.parent, ignore_errors=True)

    def test_ac2_split_creates_root_and_section_maps(self):
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        self.assertIn("llms.txt", built)
        self.assertIn("_llms/proposals.md", built)
        self.assertIn("_llms/reference.md", built)
        root = built["llms.txt"]
        self.assertLessEqual(len(root.encode("utf-8")), 8192)
        # 根只放象限入口，不得罗列具体条目
        self.assertNotIn("RFC-0001 A", root)
        self.assertIn("_llms/proposals.md", root)
        self.assertIn("_llms/reference.md", root)
        # 子地图保留全量条目与原格式；链接相对 _llms/ 目录 ⇒ 需 ../ 前缀（否则断链）
        self.assertIn("[RFC-0001 A](../proposals/RFC-0001-a.md)", built["_llms/proposals.md"])

    def test_ac2_root_reports_counts(self):
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        self.assertIn("1 篇", built["llms.txt"])

    def test_ac3_split_is_idempotent(self):
        first = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        second = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        self.assertEqual(first, second)

    def test_ac4_empty_section_produces_no_section_map(self):
        (self.root / "reference" / "rules" / "x.md").unlink()
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        self.assertNotIn("_llms/reference.md", built)
        self.assertNotIn("Reference", built["llms.txt"])

    def test_excludes_agents_md_and_section_maps(self):
        (self.root / "AGENTS.md").write_text("# Router\n\n正文\n", encoding="utf-8")
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        for content in built.values():
            self.assertNotIn("Router", content)


class TestSplitCli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="llms_cli_"))
        write_doc(self.root, "proposals/RFC-0001-a.md", "RFC-0001 A", desc="提案一")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"),
             "--root", str(self.root), "--output", str(self.root / "llms.txt"), *extra],
            capture_output=True, text=True,
        )

    def test_ac5_root_byte_limit_blocks_write(self):
        proc = self._run("--split", "--max-root-bytes", "10")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertFalse((self.root / "llms.txt").exists())

    def test_check_mode_does_not_write(self):
        """--check 只校验：未生成时 rc=1；生成后 rc=0 且不修改文件。"""
        missing = self._run("--split", "--check")
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertFalse((self.root / "llms.txt").exists())

        self.assertEqual(self._run("--split").returncode, 0)
        before = (self.root / "llms.txt").read_bytes()
        ok = self._run("--split", "--check")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertEqual((self.root / "llms.txt").read_bytes(), before)

    def test_split_writes_root_and_sections(self):
        proc = self._run("--split")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((self.root / "llms.txt").is_file())
        self.assertTrue((self.root / "_llms" / "proposals.md").is_file())


class TestAuditMultiFile(unittest.TestCase):
    def setUp(self):
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.mod = load_module("generate_llms_txt", SCRIPTS_DIR / "generate-llms-txt.py")
        self.root = Path(tempfile.mkdtemp(prefix="llms_audit_"))
        write_doc(self.root, "proposals/RFC-0001-a.md", "RFC-0001 A", desc="提案一")
        write_doc(self.root, "reference/rules/x.md", "规则 X", desc="规则说明")
        write_doc(self.root, "index.md", "Index")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_split(self):
        built = self.mod.build_llms_map(self.root, project_name="System", split=True)
        for rel, content in built.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def test_ac6_hand_edited_section_map_is_detected(self):
        self._write_split()
        self.assertEqual(self.audit.check_llms_map_consistency(self.root), "")
        section = self.root / "_llms" / "proposals.md"
        section.write_text(section.read_text(encoding="utf-8") + "\n- 手改\n", encoding="utf-8")
        self.assertIn("不一致", self.audit.check_llms_map_consistency(self.root))

    def test_ac7_missing_and_extra_section_maps_are_detected(self):
        self._write_split()
        (self.root / "_llms" / "reference.md").unlink()
        self.assertIn("不一致", self.audit.check_llms_map_consistency(self.root))

        self._write_split()
        (self.root / "_llms" / "stray.md").write_text("# 多余\n", encoding="utf-8")
        self.assertIn("不一致", self.audit.check_llms_map_consistency(self.root))

    def test_ac8_agents_md_line_limit(self):
        self._write_split()
        (self.root / "AGENTS.md").write_text(
            "# Router\n\n## 读取顺序\n\n1. llms.txt\n\n## 硬约束\n\n- 禁猜路径\n",
            encoding="utf-8",
        )
        self.assertEqual(self.audit.check_agents_md(self.root), "")
        (self.root / "AGENTS.md").write_text("# Router\n" + "\n".join(f"- 行{i}" for i in range(40)) + "\n", encoding="utf-8")
        self.assertIn("行", self.audit.check_agents_md(self.root))


if __name__ == "__main__":
    unittest.main()
