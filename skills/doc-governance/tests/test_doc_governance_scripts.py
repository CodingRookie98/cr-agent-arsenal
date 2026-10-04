#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_doc_governance_scripts.py - 文档治理自动化脚本全量回归单元测试套件
覆盖:
  1. check-doc-links.py: 物理链接检测、锚点 slugify、404 断链识别、.md 后缀严格检查;
  2. trim-revision.py: 修订历史滑动窗口检测、超额裁剪自愈、表头完整性保持;
  3. audit-doc-health.py: Frontmatter 解析、各象限拓扑识别、孤儿文档探测、综合评分;
  4. generate-llms-txt.py: 标题与摘要提取、llms.txt 规范生成;
  5. scaffold-doc.sh: 各类 Diátaxis 与 RFC 脚手架自动化生成。
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# 引入被测脚本
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# 将短横线文件名做动态模块导入兼容
import importlib.util

def load_module(name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

check_doc_links = load_module("check_doc_links", SCRIPTS_DIR / "check-doc-links.py")
trim_revision = load_module("trim_revision", SCRIPTS_DIR / "trim-revision.py")
audit_doc_health = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
generate_llms_txt = load_module("generate_llms_txt", SCRIPTS_DIR / "generate-llms-txt.py")


class TestCheckDocLinks(unittest.TestCase):
    """测试链接与锚点检测器"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_links_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_slugify_heading(self):
        """测试标题转换为 GitHub 锚点 Slug"""
        self.assertEqual(check_doc_links.slugify_heading("# Simple Title"), "simple-title")
        self.assertEqual(check_doc_links.slugify_heading("## 1. 核心理论与实践 (Core Theory)"), "1-核心理论与实践-core-theory")
        self.assertEqual(check_doc_links.slugify_heading("### Feature: [Auth](./auth.md) & Security"), "feature-auth-security")

    def test_valid_relative_links_and_anchors(self):
        """测试合法的相对链接和存在的锚点"""
        target_file = self.test_dir / "target.md"
        target_file.write_text(
            "# Target Document\n\n## Section One\nContent\n\n## 中文章节\nMore content\n",
            encoding="utf-8",
        )

        source_file = self.test_dir / "source.md"
        source_file.write_text(
            "# Source\n\n"
            "- [Go to Target](./target.md)\n"
            "- [Go to Section](./target.md#section-one)\n"
            "- [Go to Chinese](./target.md#中文章节)\n"
            "- [External](https://google.com)\n",
            encoding="utf-8",
        )

        cache = {}
        errs = check_doc_links.check_file_links(source_file, self.test_dir, cache, strict_md_extension=True)
        self.assertEqual(errs, [], f"期望无断链，但出现错误: {errs}")

    def test_detect_404_broken_link(self):
        """测试探测 404 不存在的链接"""
        source_file = self.test_dir / "source.md"
        source_file.write_text("- [Broken Link](./non-existent.md)\n", encoding="utf-8")

        cache = {}
        errs = check_doc_links.check_file_links(source_file, self.test_dir, cache, strict_md_extension=True)
        self.assertEqual(len(errs), 1)
        self.assertIn("404 Not Found", errs[0][3])

    def test_detect_missing_md_extension(self):
        """测试严格模式下检测缺少 .md 后缀的 Markdown 链接"""
        target_file = self.test_dir / "target.md"
        target_file.write_text("# Target\n", encoding="utf-8")

        source_file = self.test_dir / "source.md"
        # 故意省略 .md
        source_file.write_text("- [Link without ext](./target)\n", encoding="utf-8")

        cache = {}
        # 目标 ./target 实际不存在因此会报 404
        errs = check_doc_links.check_file_links(source_file, self.test_dir, cache, strict_md_extension=True)
        self.assertEqual(len(errs), 1)
        self.assertIn("404 Not Found", errs[0][3])

    def test_detect_missing_anchor(self):
        """测试目标文件存在但锚点不存在的错误"""
        target_file = self.test_dir / "target.md"
        target_file.write_text("# Target Doc\n\n## Existing Section\n", encoding="utf-8")

        source_file = self.test_dir / "source.md"
        source_file.write_text("- [Bad Anchor](./target.md#ghost-section)\n", encoding="utf-8")

        cache = {}
        errs = check_doc_links.check_file_links(source_file, self.test_dir, cache, strict_md_extension=True)
        self.assertEqual(len(errs), 1)
        self.assertIn("未找到对应锚点 '#ghost-section'", errs[0][3])


class TestTrimRevision(unittest.TestCase):
    """测试修订历史裁剪器"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_rev_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_no_overflow_when_under_limit(self):
        """当修订历史 <= 5 时不触发裁剪"""
        doc = self.test_dir / "test.md"
        doc.write_text(
            "# Title\n\n"
            "### 修订历史记录 (Revision History)\n\n"
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| V1.0.0 | 2026-09-01 | Alice | Bob | 首次创建 |\n"
            "| V1.1.0 | 2026-09-02 | Alice | Bob | 新增功能 |\n\n"
            "## 1. 正文内容\n",
            encoding="utf-8",
        )

        overflow, count, new_content = trim_revision.process_markdown_file(doc, max_keep=5, fix=True)
        self.assertFalse(overflow)
        self.assertEqual(count, 2)
        self.assertIsNone(new_content)

    def test_overflow_and_trim_to_five(self):
        """当修订历史超过 5 条时，在 fix 模式下正确截断为 5 条"""
        doc = self.test_dir / "overflow.md"
        doc.write_text(
            "# Title\n\n"
            "### 修订历史记录 (Revision History)\n\n"
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| V1.0.0 | 2026-09-01 | Alice | Bob | 历史 1 |\n"
            "| V1.1.0 | 2026-09-02 | Alice | Bob | 历史 2 |\n"
            "| V1.2.0 | 2026-09-03 | Alice | Bob | 历史 3 |\n"
            "| V1.3.0 | 2026-09-04 | Alice | Bob | 历史 4 |\n"
            "| V1.4.0 | 2026-09-05 | Alice | Bob | 历史 5 |\n"
            "| V1.5.0 | 2026-09-06 | Alice | Bob | 历史 6 |\n"
            "| V1.6.0 | 2026-09-07 | Alice | Bob | 历史 7 |\n\n"
            "## 1. 正文内容\n",
            encoding="utf-8",
        )

        # 1. 检查模式 (fix=False)
        overflow, count, new_content = trim_revision.process_markdown_file(doc, max_keep=5, fix=False)
        self.assertTrue(overflow)
        self.assertEqual(count, 7)
        self.assertIsNone(new_content)

        # 2. 修复模式 (fix=True)
        overflow, count, new_content = trim_revision.process_markdown_file(doc, max_keep=5, fix=True)
        self.assertTrue(overflow)
        self.assertIsNotNone(new_content)
        # 验证修复后保留的是最近的 5 条 (V1.2.0 ~ V1.6.0)
        self.assertIn("V1.6.0", new_content)
        self.assertIn("V1.2.0", new_content)
        self.assertNotIn("V1.0.0", new_content)
        self.assertNotIn("V1.1.0", new_content)


class TestAuditDocHealth(unittest.TestCase):
    """测试知识库健康度体检引擎"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_health_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_frontmatter(self):
        """测试不同形式的控制元数据解析"""
        content_yaml = "---\nversion: V1.2.0\nid: DOC-001\nowner: Alice\n---\n# Title\n"
        meta_yaml = audit_doc_health.parse_frontmatter(content_yaml)
        self.assertEqual(meta_yaml.get("version"), "V1.2.0")
        self.assertEqual(meta_yaml.get("id"), "DOC-001")

        content_block = (
            "# Title\n\n"
            "> **文档控制信息**\n"
            "> - **文档标识**: DOC-002\n"
            "> - **当前版本**: V2.0.0\n"
            "> - **文档所有者**: Bob\n\n---\n"
        )
        meta_block = audit_doc_health.parse_frontmatter(content_block)
        self.assertEqual(meta_block.get("当前版本"), "V2.0.0")
        self.assertEqual(meta_block.get("文档标识"), "DOC-002")

    def test_audit_health_report(self):
        """测试全流程健康度审计与评分计算"""
        # 创建标准目录结构
        (self.test_dir / "tutorials").mkdir(parents=True)
        (self.test_dir / "how-to").mkdir(parents=True)

        t1 = self.test_dir / "tutorials" / "quick-start.md"
        t1.write_text(
            "---\nversion: V1.0.0\nid: TUT-001\n---\n"
            "# Quick Start\n\n- [Check HowTo](../how-to/deploy.md)\n",
            encoding="utf-8",
        )

        h1 = self.test_dir / "how-to" / "deploy.md"
        h1.write_text(
            "---\nversion: V1.0.0\nid: HOW-001\n---\n"
            "# Deploy Guide\n\nContent\n",
            encoding="utf-8",
        )

        # 根目录 index.md 引用 t1
        idx = self.test_dir / "index.md"
        idx.write_text(
            "# Index\n\n- [Tutorial](./tutorials/quick-start.md)\n",
            encoding="utf-8",
        )

        report = audit_doc_health.audit_health(self.test_dir, compat_mode=False)
        self.assertNotIn("error", report)
        self.assertEqual(report["total_files"], 3)
        self.assertEqual(report["total_link_errors"], 0)
        self.assertGreaterEqual(report["total_score"], 80.0)


class TestGenerateLlmsTxt(unittest.TestCase):
    """测试机器地图生成器"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_llms_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_llms_txt_structure(self):
        """测试生成 llms.txt 结构与分类完整性"""
        (self.test_dir / "proposals").mkdir()
        (self.test_dir / "reference").mkdir()

        rfc = self.test_dir / "proposals" / "RFC-0001-test.md"
        rfc.write_text(
            "# RFC-0001: 协同画布设计\n\n> 描述: 这是一个协同画布提案\n\n正文内容\n",
            encoding="utf-8",
        )

        ref = self.test_dir / "reference" / "api.md"
        ref.write_text(
            "# API Specifications\n\n权威 API 接口规格说明\n",
            encoding="utf-8",
        )

        out_file = self.test_dir / "llms.txt"
        generate_llms_txt.generate_llms_txt(self.test_dir, out_file, project_name="MockProject")

        self.assertTrue(out_file.exists())
        content = out_file.read_text(encoding="utf-8")
        self.assertIn("# MockProject Machine-Readable Knowledge Base Map", content)
        self.assertIn("## Proposals & RFCs", content)
        self.assertIn("## Reference", content)
        self.assertIn("API Specifications", content)


class TestScaffoldDocSh(unittest.TestCase):
    """测试脚手架生成脚本"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_scaffold_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scaffold_all_types(self):
        """测试生成 tutorial, how-to, reference, explanation, adr, rfc 各类脚手架"""
        scaffold_script = SCRIPTS_DIR / "scaffold-doc.sh"
        self.assertTrue(scaffold_script.exists())

        types = ["tutorial", "how-to", "reference", "explanation", "adr", "rfc"]
        for t in types:
            res = subprocess.run(
                [str(scaffold_script), t, f"test-{t}", "--root", str(self.test_dir)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"scaffold-doc.sh {t} 失败: {res.stderr}")

        # 检查生成的文件
        self.assertTrue((self.test_dir / "tutorials" / "test-tutorial.md").exists())
        self.assertTrue((self.test_dir / "how-to" / "test-how-to.md").exists())
        self.assertTrue((self.test_dir / "reference" / "test-reference.md").exists())
        self.assertTrue((self.test_dir / "explanation" / "test-explanation.md").exists())
        self.assertTrue((self.test_dir / "explanation" / "decisions" / "0001-test-adr.md").exists())
        self.assertTrue((self.test_dir / "proposals" / "RFC-0001-test-rfc.md").exists())


class TestEvidenceArchiveExemption(unittest.TestCase):
    """交付凭据归档 docs/project/reviews/** 豁免文档治理扫描（RFC-0001 R1-2 回归）。

    归档文件是**逐字原文**（G1 红线：添加控制头会改变内容并污染 SHA256 指纹），
    报告之间亦无 markdown 入链；因此必须排除在元数据/孤儿/断链计分之外，
    否则每次真实审查交付都会单调侵蚀知识库健康度。
    """

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_reviews_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_archive(self, files=("r1-x.md", "r2-x.md")):
        arch = self.test_dir / "project" / "reviews" / "2026-01-01-demo"
        arch.mkdir(parents=True, exist_ok=True)
        for name in files:
            (arch / name).write_text("# 审查报告\n\n无控制头的逐字原文\n", encoding="utf-8")
        return arch

    def test_health_exempts_evidence_archive(self):
        self._make_archive()
        (self.test_dir / "index.md").write_text(
            "> **文档控制信息**\n"
            "> - **文档标识**: T-2026\n"
            "> - **当前版本**: V1.0.0\n"
            "> - **维护负责人**: t\n"
            "> - **生效日期**: 2026-01-01\n",
            encoding="utf-8",
        )
        res = audit_doc_health.audit_health(self.test_dir)
        self.assertNotIn("error", res)
        self.assertEqual(res["total_files"], 1, "归档目录下的报告不得计入文档总数")
        self.assertEqual(len(res["missing_meta_files"]), 0, "归档报告不得计入缺失控制头")
        self.assertEqual(len(res["orphan_docs"]), 0, "归档报告不得计入孤儿文档")

    def test_link_check_exempts_evidence_archive(self):
        self._make_archive(files=("r1-x.md",))
        (self.test_dir / "project" / "reviews" / "2026-01-01-demo" / "r1-x.md").write_text(
            "[broken](./nope.md)\n", encoding="utf-8")
        total, errors, _ = check_doc_links.scan_directory(self.test_dir, [], strict_md=True)
        self.assertEqual(total, 0, "归档报告不得计入断链扫描文件数")
        self.assertEqual(errors, 0, "归档报告内的相对链接不得被判为断链")


class TestBacklogAudit(unittest.TestCase):
    """测试 Backlog V2.0.0 冷热分离、编号合规与自动化指标体检"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_backlog_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_backlog_hot_and_cold_valid(self):
        """测试合规的热区待办与冷区归档：无断链、无编号重复、指标正确计算"""
        (self.test_dir / "index.md").write_text(
            "> **文档控制信息**\n> - **文档标识**: DOC-001\n> - **当前版本**: V1.0.0\n\n"
            "# Index\n\n- [Backlog](./project/backlog.md)\n- [Archive](./project/archive/backlog-v0.9.md)\n",
            encoding="utf-8",
        )
        proj_dir = self.test_dir / "project"
        arch_dir = proj_dir / "archive"
        arch_dir.mkdir(parents=True)

        (proj_dir / "backlog.md").write_text(
            "> **文档控制信息**\n> - **文档标识**: BK-HOT\n> - **当前版本**: V2.0.0\n\n"
            "# 待办与后续方向 (Backlog)\n\n"
            "## 进行中\n"
            "- [ ] **BK-0003** `[Type:Feature]` `[Pri:P1]` 画布协同通信接线\n"
            "  - **来源**: RFC-0006\n"
            "  - **验收**: WS 连接鉴权通过\n\n"
            "## 计划中\n"
            "- [ ] **BK-0004** `[Type:TechDebt]` `[Pri:P2]` `[Trigger:多实例部署时]` 状态外置 Redis\n"
            "  - **来源**: ADR-0001\n"
            "  - **验收**: 阶段轮询支持多实例\n"
            "- [ ] **BK-0005** `[Type:Security]` `[Pri:P0]` 凭据泄露防护拦截\n"
            "  - **来源**: R1 审查建议\n"
            "  - **验收**: 403 严格 Fail-Closed\n",
            encoding="utf-8",
        )

        (arch_dir / "backlog-v0.9.md").write_text(
            "> **文档控制信息**\n> - **文档标识**: BK-COLD-09\n> - **当前版本**: V1.0.0\n\n"
            "# v0.9.0 已结项归档\n\n"
            "- [x] **BK-0001** `[Type:Feature]` `[Pri:P1]` 多租户行级隔离 (2026-09-11 交付)\n"
            "- [x] **BK-0002** `[Type:Bug]` `[Pri:P0]` 修复登录空指针异常 (2026-09-12 交付)\n",
            encoding="utf-8",
        )

        res = audit_doc_health.audit_health(self.test_dir)
        self.assertNotIn("error", res)
        self.assertEqual(res["backlog_issues"], [], f"合规用例不应报错: {res['backlog_issues']}")
        self.assertEqual(res["backlog_warnings"], [], f"合规用例不应告警: {res['backlog_warnings']}")

        bm = res["backlog_metrics"]
        self.assertTrue(bm["has_backlog"])
        self.assertEqual(bm["active_total"], 3)
        self.assertEqual(bm["in_progress"], 1)
        self.assertEqual(bm["planned"], 2)
        self.assertEqual(bm["cold_archived_total"], 2)
        self.assertEqual(bm["hot_completed_count"], 0)
        self.assertEqual(bm["priority_counts"]["P0"], 1)
        self.assertEqual(bm["priority_counts"]["P1"], 1)
        self.assertEqual(bm["priority_counts"]["P2"], 1)
        self.assertEqual(bm["type_counts"]["Feature"], 1)
        self.assertEqual(bm["type_counts"]["Techdebt"], 1)
        self.assertEqual(bm["type_counts"]["Security"], 1)

    def test_backlog_detect_duplicate_and_missing_bk(self):
        """测试探测热区与冷区之间的跨文件重号以及缺号条目"""
        proj_dir = self.test_dir / "project"
        arch_dir = proj_dir / "archive"
        arch_dir.mkdir(parents=True)

        hot_file = proj_dir / "backlog.md"
        hot_file.write_text(
            "- [ ] **BK-0001** 有编号条目\n"
            "- [ ] 没有编号的条目\n",
            encoding="utf-8",
        )
        cold_file = arch_dir / "backlog-v0.1.md"
        cold_file.write_text(
            "- [x] **BK-0001** 冷区重号条目\n",
            encoding="utf-8",
        )

        issues, warnings, metrics = audit_doc_health.audit_backlog(self.test_dir, [hot_file, cold_file])
        self.assertTrue(any("缺 BK-XXXX 编号前缀" in i for i in issues))
        self.assertTrue(any("编号重复" in i for i in issues))

    def test_backlog_hot_hygiene_warnings(self):
        """测试热区堆积已完成项 [x]、存在「已关闭」分区与体积超标触发告警"""
        proj_dir = self.test_dir / "project"
        proj_dir.mkdir(parents=True)

        hot_file = proj_dir / "backlog.md"
        content = (
            "# 待办清单\n\n"
            "## 进行中\n- [ ] **BK-0001** 进行中项\n\n"
            "## 已关闭\n- [x] **BK-0002** 已完成项滞留在热区\n"
        )
        hot_file.write_text(content, encoding="utf-8")

        issues, warnings, metrics = audit_doc_health.audit_backlog(self.test_dir, [hot_file])
        self.assertEqual(issues, [])
        self.assertTrue(any("发现「已关闭」分区" in w for w in warnings))
        self.assertTrue(any("为已完成状态 `[x]`，滞留在热区文档中" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()

