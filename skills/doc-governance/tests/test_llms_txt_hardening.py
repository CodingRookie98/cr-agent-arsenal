#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_llms_txt_hardening.py - llms.txt 生成器与断链检查器加固回归测试（D1/D2/D3）
覆盖:
  1. D1 HTML 注释剥离: 描述派生不再泄漏 HTML 注释（单行/跨行/未闭合/内联多余空白），
     且不改变无注释文档的既有描述语义;
  2. D2 跨文档相对链接重写: 描述内相对 href 按源文档目录解析后重置为 docs 根相对（可达），
     逃出 docs 根时退化为纯文本（保留链接文字、去掉链接语法），http(s) 绝对链接逐字保留;
  3. D3 扫描盲区: check-doc-links.py 根扫描纳入 docs/llms.txt，其断链可检出、修复后通过，
     且 --dir 选择性扫描契约不被破坏。

说明: 全部用例使用临时夹具，不依赖仓库 on-disk docs/llms.txt 的内容（该文件当前含已知旧缺陷）。
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
GENERATOR = SCRIPTS_DIR / "generate-llms-txt.py"
CHECKER = SCRIPTS_DIR / "check-doc-links.py"


def load_module(name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


generate_llms_txt = load_module("generate_llms_txt_hardening", GENERATOR)
check_doc_links = load_module("check_doc_links_hardening", CHECKER)


class LlmsHardeningTestBase(unittest.TestCase):
    """临时夹具基类: <test_dir>/docs 作为文档根，test_dir 可放置根外文件构造逃逸链接。"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_llms_hardening_"))
        self.root = self.test_dir / "docs"
        self.root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ---- 夹具与执行辅助 ----
    def write_doc(self, rel_path: str, content: str) -> Path:
        path = self.root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def llms_path(self) -> Path:
        return self.root / "llms.txt"

    def llms_text(self) -> str:
        return self.llms_path().read_text(encoding="utf-8")

    def run_generate(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.root), "--output", str(self.llms_path())],
            capture_output=True,
            text=True,
        )

    def run_check(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CHECKER), "--root", str(self.root), *extra],
            capture_output=True,
            text=True,
        )

    def find_lines(self, needle: str):
        return [line for line in self.llms_text().splitlines() if needle in line]


class TestHtmlCommentStripping(LlmsHardeningTestBase):
    """D1: HTML 注释不得进入 llms.txt 描述。"""

    def test_strip_single_line_comment_leaves_no_residue(self):
        self.assertEqual("A B", generate_llms_txt.strip_html_comments("A<!-- doc-index:managed -->B"))

    def test_strip_multiline_comment_collapses_to_single_space(self):
        text = "前文<!-- 托管标记\n  doc-index:managed\n-->后文"
        self.assertEqual("前文 后文", generate_llms_txt.strip_html_comments(text))

    def test_strip_unclosed_comment_truncates_to_eof(self):
        cleaned = generate_llms_txt.strip_html_comments("# 标题\n有用段落\n<!-- 未闭合\nleaked: 是")
        self.assertNotIn("<!--", cleaned)
        self.assertNotIn("leaked", cleaned)
        self.assertIn("有用段落", cleaned)

    def test_extract_description_ignores_comment_only_body(self):
        doc = self.write_doc(
            "reference/managed.md",
            "# Managed\n<!-- doc-index:managed -->\n> 托管声明\n- 条目\n",
        )
        title, desc = generate_llms_txt.extract_doc_info(doc, self.root)
        self.assertEqual("Managed", title)
        self.assertEqual("", desc)

    def test_extract_description_strips_multiline_comment_and_normalizes_whitespace(self):
        doc = self.write_doc(
            "reference/inline.md",
            "# Inline\n<!-- 托管\n标记 -->  Real   description   here.\n",
        )
        _, desc = generate_llms_txt.extract_doc_info(doc, self.root)
        self.assertEqual("Real description here.", desc)

    def test_frontmatter_description_inside_comment_is_not_leaked(self):
        doc = self.write_doc(
            "reference/frontmatter.md",
            "# FM\n<!-- description: LEAKED VALUE -->\n真实段落文本。\n",
        )
        _, desc = generate_llms_txt.extract_doc_info(doc, self.root)
        self.assertEqual("真实段落文本。", desc)

    def test_plain_description_is_unchanged_by_hardening(self):
        self.write_doc("reference/plain.md", "# Plain\nA plain sentence with single spaces.\n")
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("- [Plain](reference/plain.md): A plain sentence with single spaces.", self.llms_text())

    def test_generated_map_never_contains_comment_marker(self):
        self.write_doc(
            "reference/managed.md",
            "# Managed\n<!-- doc-index:managed -->\n> 托管声明\n- 条目\n",
        )
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        text = self.llms_text()
        self.assertNotIn("doc-index:managed", text)
        # 描述为空时条目不得残留空的 ": " 尾巴
        self.assertEqual(["- [Managed](reference/managed.md)"], self.find_lines("reference/managed.md"))
        check = self.run_check()
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)


class TestRelativeLinkRewriting(LlmsHardeningTestBase):
    """D2: 描述内相对链接按源文档目录解析并重写为 docs 根相对。"""

    def test_cross_document_link_rewritten_to_root_relative_and_reachable(self):
        # docs/proposals/source.md 中 ../../docs/reference/target.md 在其源位置合法，
        # 但原样搬入 docs/llms.txt 会解析到 docs 根之外（仓库外），必须重置为根相对。
        self.write_doc("reference/target.md", "# Target\n\n目标正文。\n")
        self.write_doc(
            "proposals/source.md",
            "# Source\nSee [RFC-0001 §3.7](../../docs/reference/target.md) for details.\n",
        )
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        text = self.llms_text()
        self.assertNotIn("../../docs/", text)
        self.assertNotIn("../", text)
        self.assertIn(
            "- [Source](proposals/source.md): See [RFC-0001 §3.7](reference/target.md) for details.",
            text,
        )
        check = self.run_check()
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_fragment_only_link_rewritten_to_source_document(self):
        self.write_doc(
            "reference/guide.md",
            "# Guide\n1. [Section One](#section-one) 导读文本。\n\n## Section One\n\n正文。\n",
        )
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1. [Section One](reference/guide.md#section-one) 导读文本。", self.llms_text())
        check = self.run_check()
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_escaping_link_degrades_to_plain_text(self):
        # 源文档在 docs/notes/，../../outside.md 解析到 docs 根之外；该文件真实存在，
        # 链接在源文档位置合法，但搬入 docs 根下的 llms.txt 后不可达，只能退化为纯文本。
        (self.test_dir / "outside.md").write_text("# Outside\n", encoding="utf-8")
        self.write_doc("notes/source.md", "# Source\n参见 [Outside Link](../../outside.md) 全文。\n")
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        text = self.llms_text()
        self.assertNotIn("../", text)
        self.assertNotIn("../../outside.md", text)
        self.assertIn("参见 Outside Link 全文。", text)
        check = self.run_check()
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_absolute_http_link_preserved_verbatim(self):
        self.write_doc("reference/target.md", "# Target\n\n目标正文。\n")
        self.write_doc(
            "reference/abs.md",
            "# Abs\nSee [spec](https://example.com/spec.md) and [local](./target.md).\n",
        )
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        text = self.llms_text()
        self.assertIn("[spec](https://example.com/spec.md)", text)
        self.assertIn("[local](reference/target.md)", text)
        check = self.run_check()
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_link_title_preserved_when_rewriting(self):
        self.write_doc("reference/target.md", "# Target\n\n目标正文。\n")
        self.write_doc(
            "proposals/titled.md",
            '# Titled\n参见 [标题](../reference/target.md "Title X") 章节。\n',
        )
        result = self.run_generate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('[标题](reference/target.md "Title X")', self.llms_text())

    def test_image_link_rewritten_to_root_relative(self):
        description = "![diagram](../reference/pic.png)"
        rewritten = generate_llms_txt.rewrite_description_links(
            description, self.root / "proposals" / "source.md", self.root
        )
        self.assertEqual("![diagram](reference/pic.png)", rewritten)

    def test_resolve_rejects_targets_outside_root(self):
        source = self.root / "proposals" / "source.md"
        self.assertIsNone(
            generate_llms_txt._resolve_link_within_root(source, self.root, "../../outside.md")
        )
        self.assertEqual(
            "reference/target.md",
            generate_llms_txt._resolve_link_within_root(source, self.root, "../../docs/reference/target.md"),
        )


class TestLlmsTxtLinkScanning(LlmsHardeningTestBase):
    """D3: docs/llms.txt 纳入断链扫描，且不破坏 --dir 选择性契约。"""

    def test_broken_link_in_llms_txt_is_detected_and_fix_passes(self):
        self.write_doc("reference/target.md", "# Target\n\n目标正文。\n")
        self.llms_path().write_text("- [Broken](reference/missing.md)\n", encoding="utf-8")

        broken = self.run_check()
        self.assertEqual(1, broken.returncode)
        self.assertIn("【llms.txt】", broken.stdout)
        self.assertIn("reference/missing.md", broken.stdout)
        self.assertIn("404 Not Found", broken.stdout)

        self.llms_path().write_text("- [Ok](reference/target.md)\n", encoding="utf-8")
        fixed = self.run_check()
        self.assertEqual(0, fixed.returncode, fixed.stdout + fixed.stderr)
        self.assertIn("共扫描 2 个 Markdown 文件", fixed.stdout)

    def test_escaping_relative_link_in_llms_txt_is_detected(self):
        self.write_doc("reference/target.md", "# Target\n\n目标正文。\n")
        self.llms_path().write_text("- [Esc](../reference/target.md)\n", encoding="utf-8")
        result = self.run_check()
        self.assertEqual(1, result.returncode)
        self.assertIn("【llms.txt】", result.stdout)
        self.assertIn("../reference/target.md", result.stdout)

    def test_dir_scope_keeps_root_llms_txt_out(self):
        self.write_doc("reference/target.md", "# Target\n\n目标正文。\n")
        self.llms_path().write_text("- [Broken](reference/missing.md)\n", encoding="utf-8")
        result = self.run_check("--dir", "reference")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("共扫描 1 个 Markdown 文件", result.stdout)

    def test_generated_map_round_trip_is_clean(self):
        self.write_doc("proposals/source.md", "# Source\n普通段落。\n")
        generated = self.run_generate()
        self.assertEqual(0, generated.returncode, generated.stderr)
        check = self.run_check()
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)
        self.assertIn("共扫描 2 个 Markdown 文件", check.stdout)
        self.assertIn("- [Source](proposals/source.md)", self.llms_text())


if __name__ == "__main__":
    unittest.main()
