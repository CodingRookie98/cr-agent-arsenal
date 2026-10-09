#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_doc_index_convention.py - RFC-0003 目录级索引约定与 scaffold 索引自愈验收测试
覆盖:
  1. manage-doc-index.py: ensure 托管索引骨架创建、人工索引零改写、register 幂等与版本联动;
  2. scaffold-doc.sh: 产物零断链 (AS-1)、象限索引自愈与登记 (AS-2)、幂等 (AS-3)、
     人工索引只读与链接降级 (AS-4);
  3. 技能规范补登记断言 (G1): SKILL.md / 设计书 / GOVERNANCE.md 的象限索引契约。
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
SKILL_DIR = SCRIPTS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent

MANAGED_MARKER = "<!-- doc-index:managed -->"


class IndexConventionTestBase(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_index_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ---- 辅助断言 ----
    def run_manage(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "manage-doc-index.py"), *args],
            capture_output=True,
            text=True,
        )

    def run_scaffold(self, *args):
        return subprocess.run(
            [str(SCRIPTS_DIR / "scaffold-doc.sh"), *args, "--root", str(self.test_dir)],
            capture_output=True,
            text=True,
        )

    def run_link_check(self):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-links.py"), "--root", str(self.test_dir)],
            capture_output=True,
            text=True,
        )

    def run_control_sync(self):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-control-sync.py"), "--root", str(self.test_dir)],
            capture_output=True,
            text=True,
        )

    def read(self, rel):
        return (self.test_dir / rel).read_text(encoding="utf-8")

    def prepare_doc(self, dir_rel, filename, content="# 占位文档\n"):
        """按 R1-6 契约：register 前目标文档必须真实存在。"""
        path = self.test_dir / dir_rel / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path


class TestManageDocIndexEnsure(IndexConventionTestBase):
    """ensure 子命令：托管骨架创建与人工索引零改写"""

    def test_ensure_creates_managed_index_with_control_header(self):
        res = self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        self.assertEqual(res.returncode, 0, res.stderr)

        index_file = self.test_dir / "how-to" / "index.md"
        self.assertTrue(index_file.exists(), "ensure 应创建象限索引 index.md")

        content = index_file.read_text(encoding="utf-8")
        self.assertIn(MANAGED_MARKER, content, "托管索引必须携带托管标记")
        self.assertIn("**当前版本**: V1.0.0", content)
        self.assertIn("修订历史记录", content)
        self.assertIn("## 文档清单", content)

        # 与既有版本联动门禁兼容
        sync_ok = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "check-doc-control-sync.py"), "--root", str(self.test_dir)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(sync_ok.returncode, 0, sync_ok.stdout + sync_ok.stderr)

    def test_ensure_is_idempotent(self):
        self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        first = self.read("how-to/index.md")
        res = self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(first, self.read("how-to/index.md"), "重复 ensure 不得改写既有索引")

    def test_ensure_is_noop_on_manual_index(self):
        manual_dir = self.test_dir / "how-to"
        manual_dir.mkdir(parents=True)
        manual_body = "# 人工维护的操作指南索引\n\n> 由人手工撰写，脚本不得改写。\n"
        (manual_dir / "index.md").write_text(manual_body, encoding="utf-8")

        res = self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(manual_body, self.read("how-to/index.md"), "人工索引必须逐字节不变")


class TestManageDocIndexRegister(IndexConventionTestBase):
    """register 子命令：幂等登记与版本联动"""

    def test_register_appends_row_and_bumps_patch_version(self):
        self.prepare_doc("how-to", "deployment.md")
        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "生产部署 SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)

        content = self.read("how-to/index.md")
        self.assertIn("](./deployment.md)", content, "清单必须登记相对链接")
        self.assertIn("HowTo", content)
        self.assertIn("**当前版本**: V1.0.1", content, "登记须升补丁版本")

        sync = self.run_control_sync()
        self.assertEqual(sync.returncode, 0, sync.stdout + sync.stderr)

    def test_register_is_idempotent(self):
        self.prepare_doc("how-to", "deployment.md")
        args = (
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "生产部署 SOP", "--kind", "HowTo",
        )
        self.run_manage(*args)
        first = self.read("how-to/index.md")
        res = self.run_manage(*args)
        self.assertEqual(res.returncode, 0, res.stderr)

        content = self.read("how-to/index.md")
        self.assertEqual(first, content, "重复登记不得改写索引")
        self.assertEqual(content.count("](./deployment.md)"), 1, "清单不得出现重复行")
        self.assertIn("**当前版本**: V1.0.1", content, "重复登记不得重复升版本")

    def test_register_skips_manual_index(self):
        self.prepare_doc("how-to", "deployment.md")
        manual_dir = self.test_dir / "how-to"
        manual_dir.mkdir(parents=True, exist_ok=True)
        manual_body = "# 人工索引\n\n- 手工条目\n"
        (manual_dir / "index.md").write_text(manual_body, encoding="utf-8")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(manual_body, self.read("how-to/index.md"), "人工索引必须逐字节不变")

    def test_revision_window_capped_at_five(self):
        for i in range(7):
            self.prepare_doc("how-to", f"doc-{i}.md")
            res = self.run_manage(
                "register", "--root", str(self.test_dir), "--dir", "how-to",
                "--file", f"doc-{i}.md", "--title", f"文档 {i}", "--kind", "HowTo",
            )
            self.assertEqual(res.returncode, 0, res.stderr)

        content = self.read("how-to/index.md")
        self.assertIn("**当前版本**: V1.0.7", content)
        # 修订历史数据行（以 | **V 开头的行）不得超过 5 条
        rev_rows = [ln for ln in content.splitlines() if ln.strip().startswith("| **V")]
        self.assertLessEqual(len(rev_rows), 5, f"修订历史窗口超限: {len(rev_rows)}")


class TestScaffoldIndexSelfHealing(IndexConventionTestBase):
    """scaffold-doc.sh 索引自愈与零断链闭环 (AS-1 ~ AS-4)"""

    def test_how_to_scaffold_creates_and_registers_index(self):
        res = self.run_scaffold("how-to", "deployment")
        self.assertEqual(res.returncode, 0, res.stderr)

        index_file = self.test_dir / "how-to" / "index.md"
        self.assertTrue(index_file.exists(), "AS-2: scaffold 应自动创建象限索引")
        content = index_file.read_text(encoding="utf-8")
        self.assertIn(MANAGED_MARKER, content)
        self.assertIn("](./deployment.md)", content, "AS-2: 新文档应被自动登记")

        sync = self.run_control_sync()
        self.assertEqual(sync.returncode, 0, sync.stdout + sync.stderr)
        links = self.run_link_check()
        self.assertEqual(links.returncode, 0, links.stdout + links.stderr)

    def test_tutorial_scaffold_has_zero_broken_links(self):
        res = self.run_scaffold("tutorial", "quick-start")
        self.assertEqual(res.returncode, 0, res.stderr)

        links = self.run_link_check()
        self.assertEqual(links.returncode, 0, "AS-1: 脚手架产物不得含任何断链\n" + links.stdout)

    def test_tutorial_link_degrades_when_howto_index_absent(self):
        res = self.run_scaffold("tutorial", "quick-start")
        self.assertEqual(res.returncode, 0, res.stderr)

        body = self.read("tutorials/quick-start.md")
        self.assertNotIn("](../how-to/index.md)", body, "AS-4: 目标索引缺失时必须降级为纯文本")
        self.assertIn("how-to", body)
        self.assertNotIn("当前尚无该象限索引", body, "R1-8: 降级文案不得包含事实断言")

    def test_tutorial_link_kept_when_howto_index_exists(self):
        ensure = self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        self.assertEqual(ensure.returncode, 0, ensure.stderr)

        res = self.run_scaffold("tutorial", "quick-start")
        self.assertEqual(res.returncode, 0, res.stderr)
        body = self.read("tutorials/quick-start.md")
        self.assertIn("](../how-to/index.md)", body, "目标索引存在时应保留真实链接")
        links = self.run_link_check()
        self.assertEqual(links.returncode, 0, links.stdout + links.stderr)

    def test_scaffold_all_types_end_to_end_zero_broken_links(self):
        for t in ["tutorial", "how-to", "reference", "explanation", "adr", "rfc"]:
            res = self.run_scaffold(t, f"e2e-{t}")
            self.assertEqual(res.returncode, 0, f"scaffold {t} 失败: {res.stderr}")

        links = self.run_link_check()
        self.assertEqual(links.returncode, 0, "AS-1: 全类型产物必须零断链\n" + links.stdout)
        sync = self.run_control_sync()
        self.assertEqual(sync.returncode, 0, "AS-2: 全部索引必须版本联动一致\n" + sync.stdout)

    def test_repeated_scaffold_registers_each_document_once(self):
        for name in ["deployment", "local-setup"]:
            res = self.run_scaffold("how-to", name)
            self.assertEqual(res.returncode, 0, res.stderr)
        # 幂等复跑（同名文件覆盖生成）
        res = self.run_scaffold("how-to", "local-setup")
        self.assertEqual(res.returncode, 0, res.stderr)

        content = self.read("how-to/index.md")
        self.assertEqual(content.count("](./deployment.md)"), 1)
        self.assertEqual(content.count("](./local-setup.md)"), 1)
        self.assertIn("**当前版本**: V1.0.2", content, "AS-3: 幂等复跑不得重复升版本")

    def test_manual_index_survives_scaffold(self):
        manual_dir = self.test_dir / "how-to"
        manual_dir.mkdir(parents=True)
        manual_body = "# 人工维护索引\n\n> 禁止脚本改写。\n"
        (manual_dir / "index.md").write_text(manual_body, encoding="utf-8")

        res = self.run_scaffold("how-to", "deployment")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(manual_body, self.read("how-to/index.md"), "AS-4: 人工索引必须逐字节不变")


class TestSkillSpecQuadrantIndexConvention(unittest.TestCase):
    """G1 规范补登记断言：三处规范必须成文登记象限索引契约"""

    def test_skill_md_documents_managed_index(self):
        body = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("象限索引", body, "SKILL.md 必须成文定义象限索引")
        self.assertIn(MANAGED_MARKER, body, "SKILL.md 必须登记托管标记契约")
        self.assertIn("manage-doc-index.py", body)

    def test_design_doc_documents_managed_index(self):
        body = (REPO_ROOT / "docs" / "explanation" / "architecture" / "doc-governance-design.md").read_text(encoding="utf-8")
        self.assertIn("象限索引", body)
        self.assertIn(MANAGED_MARKER, body)

    def test_governance_documents_quadrant_index(self):
        body = (REPO_ROOT / "docs" / "GOVERNANCE.md").read_text(encoding="utf-8")
        self.assertIn("象限索引", body)

    def test_change_impact_matrix_requires_index_sync(self):
        body = (SKILL_DIR / "references" / "change-impact-matrix.md").read_text(encoding="utf-8")
        self.assertIn("象限索引", body)


class TestDeltaHardening(IndexConventionTestBase):
    """Delta Re-Loop 回归（R2 终审：2 阻断 + 同轮 P2/P3 修复项成对交付）"""

    def test_manual_index_referencing_marker_is_not_managed(self):
        """R1-1：人工索引仅在正文引用标记字符串时，不得被判为托管（位置契约）"""
        manual_dir = self.test_dir / "how-to"
        manual_dir.mkdir(parents=True)
        body = "# 人工索引\n\n本文件不含 <!-- doc-index:managed --> 标记，请勿改写。\n"
        (manual_dir / "index.md").write_text(body, encoding="utf-8")
        self.prepare_doc("how-to", "deployment.md")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(body, self.read("how-to/index.md"), "R1-1: 仅引用标记的人工索引必须逐字节不变")

    def test_ensure_skips_when_readme_entry_exists(self):
        """R1-3：README 入口象限按 DA-4 跳过生成"""
        entry_dir = self.test_dir / "how-to"
        entry_dir.mkdir(parents=True)
        readme = "# 人工 README 入口\n"
        (entry_dir / "README.md").write_text(readme, encoding="utf-8")

        res = self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse((entry_dir / "index.md").exists(), "R1-3: README 入口存在时不得生成第二份索引")
        self.assertEqual(readme, (entry_dir / "README.md").read_text(encoding="utf-8"))

    def test_register_skips_when_readme_entry_exists(self):
        """R1-3：README 入口象限不登记、不生成"""
        entry_dir = self.test_dir / "how-to"
        entry_dir.mkdir(parents=True)
        (entry_dir / "README.md").write_text("# 人工入口\n", encoding="utf-8")
        self.prepare_doc("how-to", "deployment.md")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertFalse((entry_dir / "index.md").exists(), "R1-3: 不得凭空生成托管索引")

    def test_register_rejects_missing_file(self):
        """R1-6：目标文档不存在时必须拒绝（杜绝 ghost 登记制造 404）"""
        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "ghost.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertNotEqual(res.returncode, 0, "R1-6: 不存在的文档必须报错非 0")
        self.assertFalse((self.test_dir / "how-to" / "index.md").exists())

    def test_register_rejects_file_with_path_separator(self):
        """R1-6 / SH-1：--file 必须是纯 basename"""
        self.prepare_doc("how-to/sub", "x.md")
        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "sub/x.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertNotEqual(res.returncode, 0, "SH-1: 含路径分隔符的 --file 必须报错非 0")

    def test_register_rejects_dir_escape(self):
        """R1-7 / R1-10：--dir 不得逃逸 root，也不得为 root 本身"""
        escape = self.run_manage(
            "register", "--root", str(self.test_dir / "docs"), "--dir", "../escape",
            "--file", "e.md", "--title", "E", "--kind", "K",
        )
        self.assertNotEqual(escape.returncode, 0, "R1-7: 含 .. 的 --dir 必须报错非 0")
        self.assertFalse((self.test_dir / "escape").exists(), "R1-7: 不得创建越界目录")

        root_dir = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", ".",
            "--file", "e.md", "--title", "E", "--kind", "K",
        )
        self.assertNotEqual(root_dir.returncode, 0, "R1-10: --dir 为 root 本身必须拒绝（N3）")

    def test_register_tolerates_annotated_version_header(self):
        """R1-4：控制头版本带注记时仍应升补丁版并写修订行"""
        index_dir = self.test_dir / "how-to"
        index_dir.mkdir(parents=True)
        (index_dir / "index.md").write_text(
            "# How To 象限索引\n\n<!-- doc-index:managed -->\n\n"
            "> **文档控制信息**\n> - **当前版本**: V1.0.0 (Draft)\n\n"
            "---\n\n### 修订历史记录 (Revision History)\n\n"
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **V1.0.0** | 2026-01-01 | AI Agent | 架构师 | 初始化 |\n\n"
            "---\n\n## 文档清单 (Document Inventory)\n",
            encoding="utf-8",
        )
        self.prepare_doc("how-to", "deployment.md")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        content = self.read("how-to/index.md")
        self.assertIn("**当前版本**: V1.0.1", content, "R1-4: 带注记的版本行也必须升版")
        sync = self.run_control_sync()
        self.assertEqual(sync.returncode, 0, "R1-4: 升版后不得出现版本漂移\n" + sync.stdout)

    def test_register_aborts_when_revision_table_unrecognized(self):
        """R1-5：修订表结构无法识别时必须整体放弃（要么都不动、要么都动）"""
        index_dir = self.test_dir / "how-to"
        index_dir.mkdir(parents=True)
        original = (
            "# How To 象限索引\n\n<!-- doc-index:managed -->\n\n"
            "> **文档控制信息**\n> - **当前版本**: V1.0.0\n\n"
            "---\n\n### 修订历史记录 (Revision History)\n\n"
            "| 版本 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **V1.0.0** | 2026-01-01 | AI Agent | 架构师 | 初始化 |\n"
        )
        (index_dir / "index.md").write_text(original, encoding="utf-8")
        self.prepare_doc("how-to", "deployment.md")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertNotEqual(res.returncode, 0, "R1-5: 修订表不可识别时必须报错非 0")
        self.assertEqual(original, self.read("how-to/index.md"), "R1-5: 失败时不得留下半成品改写")


    def test_generated_skeleton_has_no_stray_backslash_before_backtick(self):
        """DR1-1：ensure 生成物不得含「反斜杠+反引号」无效转义残留"""
        res = self.run_manage("ensure", "--root", str(self.test_dir), "--dir", "how-to")
        self.assertEqual(res.returncode, 0, res.stderr)
        content = self.read("how-to/index.md")
        stray = chr(92) + chr(96)
        self.assertNotIn(stray, content, "DR1-1: 生成物含反斜杠转义残留")

    def test_script_compiles_under_strict_syntax_warnings(self):
        """DR1-1：脚本须在 -W error::SyntaxWarning 下零告警编译（未来 Python 的硬错误前哨）"""
        res = subprocess.run(
            [sys.executable, "-W", "error::SyntaxWarning", "-c",
             "import py_compile, sys; py_compile.compile(sys.argv[1], doraise=True)",
             str(SCRIPTS_DIR / "manage-doc-index.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, "DR1-1: 严格告警下编译失败\n" + res.stderr)

    def test_is_managed_tolerates_bom_prefix(self):
        """DR1-2：托管索引被加 BOM 后仍应识别为托管并正常登记"""
        index_dir = self.test_dir / "how-to"
        index_dir.mkdir(parents=True)
        body = ("\ufeff" + "# How To 象限索引\n\n<!-- doc-index:managed -->\n\n"
                "> **文档控制信息**\n> - **当前版本**: V1.0.0\n\n"
                "---\n\n### 修订历史记录 (Revision History)\n\n"
                "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
                "| :--- | :--- | :--- | :--- | :--- |\n"
                "| **V1.0.0** | 2026-01-01 | AI Agent | 架构师 | 初始化 |\n\n"
                "---\n\n## 文档清单 (Document Inventory)\n")
        (index_dir / "index.md").write_text(body, encoding="utf-8")
        self.prepare_doc("how-to", "deployment.md")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("](./deployment.md)", self.read("how-to/index.md"), "DR1-2: BOM 前导时仍应登记")

    def test_is_managed_tolerates_frontmatter_comment(self):
        """DR1-2：frontmatter 围栏内含 # 注释时不得抢占 H1 锚点"""
        index_dir = self.test_dir / "how-to"
        index_dir.mkdir(parents=True)
        body = ("---\ntitle: how-to index\n# note comment\n---\n\n"
                "# How To 象限索引\n\n<!-- doc-index:managed -->\n\n"
                "> **文档控制信息**\n> - **当前版本**: V1.0.0\n\n"
                "---\n\n### 修订历史记录 (Revision History)\n\n"
                "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
                "| :--- | :--- | :--- | :--- | :--- |\n"
                "| **V1.0.0** | 2026-01-01 | AI Agent | 架构师 | 初始化 |\n\n"
                "---\n\n## 文档清单 (Document Inventory)\n")
        (index_dir / "index.md").write_text(body, encoding="utf-8")
        self.prepare_doc("how-to", "deployment.md")

        res = self.run_manage(
            "register", "--root", str(self.test_dir), "--dir", "how-to",
            "--file", "deployment.md", "--title", "SOP", "--kind", "HowTo",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("](./deployment.md)", self.read("how-to/index.md"), "DR1-2: frontmatter 注释不得抢占锚点")

    def test_register_rejects_dir_resolving_to_root(self):
        """DR1-4：--dir 经符号链接解析为 root 本身时必须拒绝（N3）"""
        docs = self.test_dir / "docs"
        docs.mkdir(parents=True)
        (docs / "index.md").write_text("# 人工根索引\n", encoding="utf-8")
        try:
            (docs / "self").symlink_to(docs)
        except OSError:
            self.skipTest("平台不支持符号链接")

        res = self.run_manage("ensure", "--root", str(docs), "--dir", "self")
        self.assertNotEqual(res.returncode, 0, "DR1-4: 解析为 root 本身的 --dir 必须拒绝")


if __name__ == "__main__":
    unittest.main()
