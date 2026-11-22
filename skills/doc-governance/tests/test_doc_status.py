#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_doc_status.py - 文档状态机 (RFC-0007) 契约测试

覆盖:
  AC-1 无状态字段 ⇒ 视为 Active、零缺陷；
  AC-2 非法取值 ⇒ C-1 阻断；
  AC-3 Superseded 缺「取代于」⇒ C-2 阻断；
  AC-4 「取代于」指向不存在 ⇒ C-2 阻断；
  AC-5 「取代于」指向自身 ⇒ C-2 阻断；
  AC-6 Active 带「取代于」⇒ C-3 阻断；
  AC-7 Contested 缺「争议点」⇒ 不阻断、清单显示未填写；
  AC-8 Contested 超 90 天 ⇒ C-5 警告。
"""

import importlib.util
import re
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


def write_doc(root: Path, rel: str, status: str = None, superseded_by: str = None,
              contested: str = None, revised: str = "2026-11-20", title: str = "文档"):
    lines = [f"# {title}", "", "> **文档控制信息**", f"> - **文档标识**: T-{rel.replace('/', '-')}",
             "> - **当前版本**: V1.0.0"]
    if status is not None:
        lines.append(f"> - **文档状态**: {status}")
    if superseded_by is not None:
        lines.append(f"> - **取代于**: {superseded_by}")
    if contested is not None:
        lines.append(f"> - **争议点**: {contested}")
    lines.append("> - **生效日期**: 2026-01-01")
    lines += ["", "### 修订历史记录 (Revision History)", "",
              "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |",
              "| :--- | :--- | :--- | :--- | :--- |",
              f"| **V1.0.0** | {revised} | t | t | 初版 |", "", "正文", ""]
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


class TestDocStatus(unittest.TestCase):
    def setUp(self):
        self.mod = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_status_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _check(self):
        return self.mod.check_doc_status(self.root)

    def test_ac1_missing_status_is_active_without_issues(self):
        write_doc(self.root, "reference/a.md")
        res = self._check()
        self.assertEqual(res["counts"]["Active"], 1)
        self.assertEqual(res["issues"], [])

    def test_ac2_invalid_status_is_blocking(self):
        write_doc(self.root, "reference/a.md", status="Deprecated")
        res = self._check()
        self.assertTrue(res["issues"])
        self.assertIn("Deprecated", " ".join(res["issues"]))

    def test_ac3_superseded_without_pointer_is_blocking(self):
        write_doc(self.root, "reference/a.md", status="Superseded")
        res = self._check()
        self.assertTrue(any("取代于" in i for i in res["issues"]), res)

    def test_ac4_pointer_to_missing_file_is_blocking(self):
        write_doc(self.root, "reference/a.md", status="Superseded", superseded_by="./gone.md")
        res = self._check()
        self.assertTrue(any("不存在" in i for i in res["issues"]), res)

    def test_ac5_pointer_to_self_is_blocking(self):
        write_doc(self.root, "reference/a.md", status="Superseded", superseded_by="./a.md")
        res = self._check()
        self.assertTrue(any("自身" in i for i in res["issues"]), res)

    def test_ac6_active_with_pointer_is_blocking(self):
        write_doc(self.root, "reference/b.md", status="Active")
        write_doc(self.root, "reference/a.md", status="Active", superseded_by="./b.md")
        res = self._check()
        self.assertTrue(any("Active" in i and "取代于" in i for i in res["issues"]), res)

    def test_ac7_contested_without_reason_is_not_blocking(self):
        write_doc(self.root, "reference/a.md", status="Contested", revised="2026-11-20")
        res = self._check()
        self.assertEqual(res["issues"], [])
        self.assertEqual(len(res["contested"]), 1)
        self.assertEqual(res["contested"][0]["reason"], "未填写")

    def test_ac8_contested_over_90_days_is_listed_with_age(self):
        write_doc(self.root, "reference/a.md", status="Contested", contested="选型未定",
                  revised="2026-01-01")
        res = self._check()
        self.assertEqual(res["issues"], [])
        self.assertGreater(res["contested"][0]["age_days"], 90)

    def test_c4_active_referencing_superseded_is_warning_not_blocking(self):
        """C-4：Active 文档引用 Superseded ⇒ 警告，不阻断。"""
        write_doc(self.root, "reference/new.md", status="Active")
        write_doc(self.root, "reference/old.md", status="Superseded", superseded_by="./new.md")
        user = write_doc(self.root, "reference/user.md", status="Active")
        user.write_text(
            user.read_text(encoding="utf-8") + "\n参见 [旧版](./old.md)\n", encoding="utf-8"
        )
        res = self._check()
        self.assertEqual(res["issues"], [])
        self.assertTrue(res["warnings"], res)
        self.assertIn("old.md", res["warnings"][0])

    def test_valid_superseded_chain_is_clean(self):
        write_doc(self.root, "reference/new.md", status="Active")
        write_doc(self.root, "reference/old.md", status="Superseded", superseded_by="./new.md")
        res = self._check()
        self.assertEqual(res["issues"], [])
        self.assertEqual(res["counts"]["Superseded"], 1)
        self.assertEqual(res["superseded"][0]["by"], "./new.md")



class TestStatusRedTeamFixes(unittest.TestCase):
    """红队 T-1~T-11 回归"""

    def setUp(self):
        self.mod = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
        self.root = Path(tempfile.mkdtemp(prefix="doc_status_rt_"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _check(self):
        return self.mod.check_doc_status(self.root)

    def test_t1_template_skeleton_passes_gate(self):
        """T-1：模板骨架（复制到 H1 之后）产出的文档必须过门禁。"""
        tpl = (SCRIPTS_DIR.parent / "templates" / "doc-control-header.md").read_text(encoding="utf-8")
        block = re.search(r"```markdown\n(.*?)```", tpl, re.DOTALL)
        self.assertIsNotNone(block, "模板缺少 markdown 骨架")
        skeleton = block.group(1)
        # 按模板说明填槽位（模拟使用者照做）
        filled = (
            skeleton.replace("REF-<NAME>-<YYYY>", "REF-DEMO-2026")
            .replace("V1.0.0", "V1.0.0")
            .replace("YYYY-MM-DD", "2026-11-20")
            .replace("<所有者>", "核心架构组")
            .replace("<修订人>", "t")
            .replace("<审核人>", "t")
            .replace("<一句话说明>", "初版")
        )
        (self.root / "reference").mkdir()
        (self.root / "reference" / "demo.md").write_text("# Demo\n\n" + filled + "\n正文\n", encoding="utf-8")
        res = self._check()
        self.assertEqual(res["issues"], [], res["issues"])
        self.assertEqual(res["counts"]["Active"], 1)

    def test_t2_yaml_and_quote_block_are_both_parsed(self):
        """T-2：YAML frontmatter 与引用块并存时，引用块不得被整体遮蔽。"""
        (self.root / "reference").mkdir()
        (self.root / "reference" / "a.md").write_text(
            "---\nversion: V1.0.0\n---\n# A\n\n> **文档控制信息**\n"
            "> - **文档状态**: Contested\n> - **争议点**: 并存形态\n",
            encoding="utf-8",
        )
        res = self._check()
        self.assertEqual(res["counts"]["Contested"], 1, res["counts"])

    def test_t3_table_form_status_is_recognised(self):
        (self.root / "reference").mkdir()
        (self.root / "reference" / "a.md").write_text(
            "# A\n\n> **文档控制信息**\n\n| 文档状态 | Contested |\n| 争议点 | 表格形态 |\n",
            encoding="utf-8",
        )
        res = self._check()
        self.assertEqual(res["counts"]["Contested"], 1, res["counts"])

    def test_t4_fenced_example_is_not_a_status_declaration(self):
        """T-4：围栏内的示例不得被当成真声明。"""
        (self.root / "reference").mkdir()
        body = (
            "# A\n\n> **文档控制信息**\n> - **文档状态**: Active\n\n"
            "```markdown\n> - **文档状态**: Superseded\n```\n"
        )
        (self.root / "reference" / "a.md").write_text(body, encoding="utf-8")
        res = self._check()
        self.assertEqual(res["counts"]["Active"], 1, res["counts"])
        self.assertEqual(res["counts"]["Superseded"], 0)

    def test_t5_pointer_with_anchor_is_accepted(self):
        write_doc(self.root, "reference/new.md", status="Active")
        write_doc(self.root, "reference/old.md", status="Superseded", superseded_by="./new.md#sec")
        res = self._check()
        self.assertEqual(res["issues"], [], res["issues"])

    def test_t6_escaping_pointer_is_blocked(self):
        write_doc(self.root, "reference/new.md", status="Active")
        for bad in ("/etc/passwd", "../../../etc/passwd"):
            write_doc(self.root, "reference/old.md", status="Superseded", superseded_by=bad)
            res = self._check()
            self.assertTrue(any("取代于" in i for i in res["issues"]), (bad, res["issues"]))

    def test_t7_latest_revision_date_is_used(self):
        """T-7：修订表为升序时，年龄须按最新一行计算。"""
        (self.root / "reference").mkdir()
        (self.root / "reference" / "a.md").write_text(
            "# A\n\n> **文档控制信息**\n> - **文档状态**: Contested\n> - **争议点**: x\n\n"
            "### 修订历史记录 (Revision History)\n\n"
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n| :--- | :--- | :--- | :--- | :--- |\n"
            "| **V1.0.0** | 2026-01-01 | t | t | 初版 |\n"
            "| **V1.1.0** | 2026-11-20 | t | t | 更新 |\n",
            encoding="utf-8",
        )
        res = self._check()
        self.assertLess(res["contested"][0]["age_days"], 90, res["contested"])

    def test_t10_backlog_exclusion_is_scoped_to_project_backlog(self):
        """T-10：只排除 project/backlog，不得连带跳过其它目录。"""
        write_doc(self.root, "project/backlog/BK-1.md", status="BadStatus")
        write_doc(self.root, "reference/backlog/real.md", status="BadStatus")
        res = self._check()
        self.assertEqual(len(res["issues"]), 1, res["issues"])
        self.assertIn("reference/backlog/real.md", res["issues"][0])


    def test_t9_threshold_is_configurable(self):
        write_doc(self.root, "reference/a.md", status="Contested", contested="x", revised="2026-11-01")
        strict = self.mod.check_doc_status(self.root, now="2026-11-22", max_age_days=5)
        loose = self.mod.check_doc_status(self.root, now="2026-11-22", max_age_days=90)
        self.assertGreater(strict["contested"][0]["age_days"], 5)
        self.assertLess(loose["contested"][0]["age_days"], 90)


if __name__ == "__main__":
    unittest.main()
