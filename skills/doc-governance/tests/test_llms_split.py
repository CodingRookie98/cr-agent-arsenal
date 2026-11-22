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

    def test_ac1_default_mode_matches_independent_oracle(self):
        """AC-1：默认模式产物与**独立 oracle**（硬编码期望全文）逐字节一致。

        SD-2：原用例比较「新 build_llms_map」与「已改为调用新函数的 generate_llms_txt」，
        属同义反复——渲染层回归时两边同时变，用例仍绿。此处改为对照固定夹具的期望全文。
        """
        expected = (
            "# Demo Machine-Readable Knowledge Base Map\n"
            "\n"
            "> 本文件遵循 llmstxt.org 规范，为 AI 智能体提供全景知识拓扑与物理文件导航地图。\n"
            "> 严禁凭空猜测路径，查阅具体模块前请通过下述相对链接精准索引对应文件。\n"
            "\n"
            "## Proposals & RFCs (需求与设计孵化层)\n"
            "\n"
            "- [RFC-0001 A](proposals/RFC-0001-a.md): 提案一\n"
            "\n"
            "## Reference (技术参考 / 机器事实唯一真相源)\n"
            "\n"
            "- [规则 X](reference/rules/x.md): 规则说明\n"
        )
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=False)
        self.assertEqual(list(built.keys()), ["llms.txt"])
        self.assertEqual(built["llms.txt"], expected)

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



class TestS1S3S4S5(unittest.TestCase):
    """红队 S-1/S-2/S-3/S-4/S-5 回归"""

    def setUp(self):
        self.mod = load_module("generate_llms_txt", SCRIPTS_DIR / "generate-llms-txt.py")
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="llms_s_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.root), *extra],
            capture_output=True, text=True,
        )

    def test_s1_custom_output_basename_is_honoured(self):
        write_doc(self.root, "proposals/a.md", "A", desc="d")
        out = self.root / "custom-map.txt"
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"),
             "--root", str(self.root), "--output", str(out)],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(out.is_file(), "custom basename must be written")
        self.assertFalse((self.root / "llms.txt").exists(), "must not write default name")

    def test_s3_default_mode_has_no_byte_limit(self):
        for i in range(40):
            write_doc(self.root, f"proposals/doc-{i}.md", f"Doc {i}", desc="x" * 200)
        proc = self._run()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertGreater((self.root / "llms.txt").stat().st_size, 8192)

    def test_s3_split_mode_still_enforces_limit(self):
        for i in range(40):
            write_doc(self.root, f"proposals/doc-{i}.md", f"Doc {i}", desc="x" * 200)
        proc = self._run("--split", "--max-root-bytes", "200")
        self.assertEqual(proc.returncode, 1)
        self.assertFalse((self.root / "llms.txt").exists())

    def test_s4_non_http_schemes_are_not_rebased(self):
        write_doc(self.root, "proposals/a.md", "A", desc="[tel](tel:123) [cdn](//cdn.example/x.md) [ok](./b.md)")
        built = self.mod.build_llms_map(self.root, project_name="Demo", split=True)
        section = built["_llms/proposals.md"]
        self.assertIn("](tel:123)", section)
        self.assertIn("](//cdn.example/x.md)", section)
        self.assertIn("](../proposals/b.md)", section)

    def test_s5_nested_stray_under_section_dir_is_detected(self):
        write_doc(self.root, "proposals/a.md", "A", desc="d")
        write_doc(self.root, "index.md", "Index")
        built = self.mod.build_llms_map(self.root, project_name="System", split=True)
        for rel, content in built.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self.assertEqual(self.audit.check_llms_map_consistency(self.root), "")
        nested = self.root / "_llms" / "sub"
        nested.mkdir()
        (nested / "sneaky.md").write_text("# 私藏\n", encoding="utf-8")
        self.assertIn("不一致", self.audit.check_llms_map_consistency(self.root))

    def test_s2_regen_hint_mentions_split(self):
        write_doc(self.root, "proposals/a.md", "A", desc="d")
        write_doc(self.root, "index.md", "Index")
        built = self.mod.build_llms_map(self.root, project_name="System", split=True)
        for rel, content in built.items():
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (self.root / "_llms" / "proposals.md").write_text("# 手改\n", encoding="utf-8")
        issue = self.audit.check_llms_map_consistency(self.root)
        self.assertIn("--split", issue)



class TestSD1SD3SD5SD6(unittest.TestCase):
    """Delta 复核 SD-1/3/5/6 回归：检测面与清理面同口径"""

    def setUp(self):
        self.mod = load_module("generate_llms_txt", SCRIPTS_DIR / "generate-llms-txt.py")
        self.audit = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="llms_sd_"))
        write_doc(self.root, "proposals/a.md", "A", desc="d")
        write_doc(self.root, "index.md", "Index")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.root), *extra],
            capture_output=True, text=True,
        )

    def _split(self):
        self.assertEqual(self._run("--split").returncode, 0)

    def test_sd1_nested_stray_makes_check_red_and_regen_converges(self):
        self._split()
        nested = self.root / "_llms" / "sub"
        nested.mkdir()
        (nested / "sneaky.md").write_text("# 私藏\n", encoding="utf-8")
        # 检测面（--check）必须与 audit 同口径判红
        self.assertEqual(self._run("--split", "--check").returncode, 1)
        self.assertIn("不一致", self.audit.check_llms_map_consistency(self.root))
        # 清理面必须收敛：重生成后 check 绿、audit 绿
        self.assertEqual(self._run("--split").returncode, 0)
        self.assertEqual(self._run("--split", "--check").returncode, 0)
        self.assertEqual(self.audit.check_llms_map_consistency(self.root), "")
        self.assertFalse((nested / "sneaky.md").exists())

    def test_sd3_check_reports_actual_basename(self):
        self.assertEqual(self._run("--split").returncode, 0)
        custom = self.root / "map.txt"
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"),
             "--root", str(self.root), "--output", str(custom), "--split", "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("map.txt", proc.stderr)
        self.assertNotIn("不一致: llms.txt", proc.stderr)

    def test_sd6_root_byte_budget_is_enforced_by_audit(self):
        self._split()
        big = self.root / "llms.txt"
        big.write_text(big.read_text(encoding="utf-8") + "\n" + "x" * 9000, encoding="utf-8")
        self.assertIn("根体量", self.audit.check_llms_map_consistency(self.root))

    def test_sd5_symlinked_section_subdir_is_detected(self):
        self._split()
        target = self.root / "elsewhere"
        target.mkdir()
        link = self.root / "_llms" / "linked"
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("平台不支持目录符号链接")
        self.assertIn("符号链接", self.audit.check_llms_map_consistency(self.root))


if __name__ == "__main__":
    unittest.main()
