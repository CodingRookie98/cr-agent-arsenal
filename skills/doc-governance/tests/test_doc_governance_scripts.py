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

import json
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
check_doc_control_sync = load_module("check_doc_control_sync", SCRIPTS_DIR / "check-doc-control-sync.py")
audit_doc_health = load_module("audit_doc_health", SCRIPTS_DIR / "audit-doc-health.py")
generate_llms_txt = load_module("generate_llms_txt", SCRIPTS_DIR / "generate-llms-txt.py")
manage_backlog = load_module("manage_backlog", SCRIPTS_DIR / "manage-backlog.py")


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

    def test_inline_code_and_image_syntax_exempted(self):
        """测试含图片语法与多反引号的行内代码示例被正确剥离，不误报断链"""
        source_file = self.test_dir / "source.md"
        source_file.write_text(
            "# Source\n\n"
            "行内图片代码: `![alt](url \"title\")` 以及 `[link](fake.md)`\n"
            "双反引号代码: `` `[xxx.md](./path/xxx.md)` ``\n"
            "合规自引用: [Self](./source.md)\n",
            encoding="utf-8",
        )
        cache = {}
        errs = check_doc_links.check_file_links(source_file, self.test_dir, cache, strict_md_extension=True)
        self.assertEqual(errs, [], f"期望行内代码中的图片/链接语法被剥离且无断链，但报错: {errs}")


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

    def test_audit_health_detects_version_drift(self):
        """测试健康体检能够检测到控制头与修订表版本漂移"""
        (self.test_dir / "tutorials").mkdir(parents=True, exist_ok=True)
        t_drift = self.test_dir / "tutorials" / "drift.md"
        t_drift.write_text(
            "---\nversion: V2.4.1\nid: TUT-DRIFT\n---\n"
            "# Drift Tutorial\n\n"
            "### 修订历史记录\n\n"
            "| 版本号 | 修订日期 | 修订人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **V2.4.0** | 2026-10-03 | Agent | 漏登 2.4.1 |\n",
            encoding="utf-8",
        )
        report = audit_doc_health.audit_health(self.test_dir, compat_mode=False)
        self.assertIn("version_drift_files", report)
        drift_files = [f[0].name for f in report["version_drift_files"]]
        self.assertIn("drift.md", drift_files)


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


class TestManageBacklogAndFormB(unittest.TestCase):
    """测试 Backlog 形态 B (Issue-as-File) 自动化管理、脚本化提取与健康门禁"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_form_b_"))
        self.manage_script = SCRIPTS_DIR / "manage-backlog.py"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_cli(self, *args) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(self.manage_script), "--root", str(self.test_dir)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_create_and_sync_index(self):
        """测试 create 命令自动分配递增 BK 编号、生成标准卡片文件并自动同步 index.md"""
        # 1. 创建第一条待办
        res1 = self.run_cli(
            "create", "多租户行级隔离",
            "--priority", "P1",
            "--type", "Feature",
            "--trigger", "多租户上线时",
            "--source", "RFC-0001",
            "--acceptance", "各租户数据物理隔离",
        )
        self.assertEqual(res1.returncode, 0, f"创建失败: {res1.stderr}")
        self.assertIn("BK-0001", res1.stdout)

        active_dir = self.test_dir / "docs" / "project" / "backlog" / "active"
        self.assertTrue(active_dir.exists())
        cards_1 = list(active_dir.glob("BK-0001*.md"))
        self.assertEqual(len(cards_1), 1)

        card_path = cards_1[0]
        meta, body = manage_backlog.parse_item_file(card_path)
        self.assertEqual(meta.get("id"), "BK-0001")
        self.assertEqual(meta.get("title"), "多租户行级隔离")
        self.assertEqual(meta.get("priority"), "P1")
        self.assertEqual(meta.get("type"), "Feature")
        self.assertEqual(meta.get("status"), "active")
        self.assertEqual(meta.get("trigger"), "多租户上线时")
        self.assertIn("RFC-0001", meta.get("source", []))

        # 2. 创建第二条待办，验证自增为 BK-0002
        res2 = self.run_cli(
            "create", "优化搜索性能",
            "--priority", "P0",
            "--type", "Performance",
        )
        self.assertEqual(res2.returncode, 0)
        self.assertIn("BK-0002", res2.stdout)

        # 3. 验证 index.md 已自动生成并包含两项及仪表盘
        index_file = self.test_dir / "docs" / "project" / "backlog" / "index.md"
        self.assertTrue(index_file.exists())
        index_content = index_file.read_text(encoding="utf-8")
        self.assertIn("BK-0001", index_content)
        self.assertIn("BK-0002", index_content)
        self.assertIn("待办健康度仪表盘", index_content)

    def test_list_and_json_parsing(self):
        """测试 list 命令的脚本化过滤与可编程 JSON 输出"""
        # 创建测试条目
        self.run_cli("create", "Bug 修复", "--priority", "P0", "--type", "Bug")
        self.run_cli("create", "技术债偿还", "--priority", "P2", "--type", "TechDebt")

        # 1. 验证纯 JSON 数组输出
        res_json = self.run_cli("list", "--json")
        self.assertEqual(res_json.returncode, 0)
        items = json.loads(res_json.stdout)
        self.assertEqual(len(items), 2)
        ids = {it["id"] for it in items}
        self.assertEqual(ids, {"BK-0001", "BK-0002"})

        # 2. 验证按优先级过滤
        res_p0 = self.run_cli("list", "--priority", "P0", "--json")
        items_p0 = json.loads(res_p0.stdout)
        self.assertEqual(len(items_p0), 1)
        self.assertEqual(items_p0[0]["id"], "BK-0001")

        # 3. 验证按类型过滤
        res_tech = self.run_cli("list", "--type", "TechDebt", "--json")
        items_tech = json.loads(res_tech.stdout)
        self.assertEqual(len(items_tech), 1)
        self.assertEqual(items_tech[0]["id"], "BK-0002")

        # 4. 验证 id-only 格式
        res_id = self.run_cli("list", "--format", "id-only")
        self.assertEqual(res_id.returncode, 0)
        self.assertEqual(res_id.stdout.strip().splitlines(), ["BK-0001", "BK-0002"])

    def test_close_and_reopen_lifecycle(self):
        """测试待办关闭归档与重新激活的生命周期流转"""
        self.run_cli("create", "生命周期测试项", "--priority", "P1")
        active_dir = self.test_dir / "docs" / "project" / "backlog" / "active"
        archive_dir = self.test_dir / "docs" / "project" / "backlog" / "archive"
        self.assertEqual(len(list(active_dir.glob("BK-0001*.md"))), 1)

        # 1. 关闭归档
        res_close = self.run_cli(
            "close", "BK-0001",
            "--resolution", "delivered",
            "--destination", "docs/project/changelog.md (Commit 940e0f3)",
        )
        self.assertEqual(res_close.returncode, 0)
        self.assertEqual(len(list(active_dir.glob("BK-0001*.md"))), 0)
        archived_files = list(archive_dir.rglob("BK-0001*.md"))
        self.assertEqual(len(archived_files), 1)

        meta, _ = manage_backlog.parse_item_file(archived_files[0])
        self.assertEqual(meta.get("status"), "completed")
        self.assertTrue(meta.get("closed_at"))
        self.assertEqual(meta.get("resolution"), "delivered")
        self.assertEqual(meta.get("destination"), "docs/project/changelog.md (Commit 940e0f3)")

        # 2. 重新激活 reopen
        res_reopen = self.run_cli("reopen", "BK-0001")
        self.assertEqual(res_reopen.returncode, 0)
        self.assertEqual(len(list(active_dir.glob("BK-0001*.md"))), 1)
        self.assertEqual(len(list(archive_dir.rglob("BK-0001*.md"))), 0)
        reopened_meta, _ = manage_backlog.parse_item_file(list(active_dir.glob("BK-0001*.md"))[0])
        self.assertEqual(reopened_meta.get("status"), "active")
        self.assertIsNone(reopened_meta.get("closed_at"))

    def test_audit_health_form_b_compliance_and_warnings(self):
        """测试 audit-doc-health 对形态 B 拓扑的深度门禁与滞留项告警"""
        backlog_dir = self.test_dir / "docs" / "project" / "backlog"
        active_dir = backlog_dir / "active"
        archive_dir = backlog_dir / "archive" / "2026-Q3"
        active_dir.mkdir(parents=True)
        archive_dir.mkdir(parents=True)

        # 合规形态 B 索引与条目
        (backlog_dir / "index.md").write_text(
            "> **文档控制信息**\n> - **文档标识**: BK-INDEX\n> - **当前版本**: V2.0.0\n\n# Backlog Index\n",
            encoding="utf-8",
        )
        manage_backlog.dump_item_file(
            active_dir / "BK-0001-active.md",
            {"id": "BK-0001", "title": "活跃待办", "status": "active", "priority": "P1", "type": "Feature"},
            "正文描述",
        )
        manage_backlog.dump_item_file(
            active_dir / "BK-0002-in-prog.md",
            {"id": "BK-0002", "title": "进行中待办", "status": "in-progress", "priority": "P0", "type": "Security"},
            "正文描述",
        )
        manage_backlog.dump_item_file(
            archive_dir / "BK-0003-closed.md",
            {"id": "BK-0003", "title": "已关闭冷待办", "status": "completed", "priority": "P2", "type": "Bug", "closed_at": "2026-09-01"},
            "正文描述",
        )

        all_files = [
            backlog_dir / "index.md",
            active_dir / "BK-0001-active.md",
            active_dir / "BK-0002-in-prog.md",
            archive_dir / "BK-0003-closed.md",
        ]

        issues, warnings, metrics = audit_doc_health.audit_backlog(self.test_dir, all_files)
        self.assertEqual(issues, [], f"合规形态 B 不得产生阻断错误: {issues}")
        self.assertEqual(warnings, [], f"合规形态 B 不得产生告警: {warnings}")
        self.assertTrue(metrics["has_backlog"])
        self.assertEqual(metrics["topology"], "form_b")
        self.assertEqual(metrics["active_total"], 2)
        self.assertEqual(metrics["in_progress"], 1)
        self.assertEqual(metrics["planned"], 1)
        self.assertEqual(metrics["cold_archived_total"], 1)

        # 滞留项测试：在 active 放置 status: completed 的待办
        manage_backlog.dump_item_file(
            active_dir / "BK-0004-stale.md",
            {"id": "BK-0004", "title": "滞留已完成项", "status": "completed", "priority": "P1", "type": "TechDebt"},
            "滞留正文",
        )
        all_files.append(active_dir / "BK-0004-stale.md")
        issues2, warnings2, metrics2 = audit_doc_health.audit_backlog(self.test_dir, all_files)
        self.assertEqual(issues2, [])
        self.assertTrue(any("滞留在 active/ 目录中" in w and "BK-0004" in w for w in warnings2))

    def test_audit_health_form_b_duplicate_id(self):
        """测试形态 B 检测跨文件编号重复"""
        backlog_dir = self.test_dir / "docs" / "project" / "backlog"
        active_dir = backlog_dir / "active"
        archive_dir = backlog_dir / "archive" / "2026-Q3"
        active_dir.mkdir(parents=True)
        archive_dir.mkdir(parents=True)

        # 在 active 与 archive 各放置一个 BK-0001
        manage_backlog.dump_item_file(
            active_dir / "BK-0001-dup1.md",
            {"id": "BK-0001", "title": "重复条目 1", "status": "active"},
            "正文 1",
        )
        manage_backlog.dump_item_file(
            archive_dir / "BK-0001-dup2.md",
            {"id": "BK-0001", "title": "重复条目 2", "status": "completed"},
            "正文 2",
        )
        all_files = [active_dir / "BK-0001-dup1.md", archive_dir / "BK-0001-dup2.md"]
        issues, warnings, metrics = audit_doc_health.audit_backlog(self.test_dir, all_files)
        self.assertTrue(any("重复" in i and "BK-0001" in i for i in issues))


class TestCheckDocControlSync(unittest.TestCase):
    """测试文档控制头与修订历史版本联动一致性扫描器"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_sync_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_synced_version(self):
        """测试控制头版本与修订历史最新行版本一致"""
        doc = self.test_dir / "doc.md"
        doc.write_text(
            "# 某核心设计文档\n\n"
            "> **文档控制信息**\n"
            "> - **文档标识**: DOC-001\n"
            "> - **当前版本**: V1.4.0\n\n"
            "### 修订历史记录\n\n"
            "| 版本号 | 修订日期 | 修订人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **V1.4.0** | 2026-10-04 | Agent | 最新特性升级 |\n"
            "| **V1.3.0** | 2026-09-16 | Agent | 初始版本 |\n",
            encoding="utf-8",
        )
        is_synced, h_ver, r_ver, err = check_doc_control_sync.check_file_version_sync(doc)
        self.assertTrue(is_synced)
        self.assertIsNone(err)

    def test_detect_version_drift(self):
        """测试控制头版本与修订历史发生漂移（模拟 f994dd0 漏洞场景）"""
        doc = self.test_dir / "doc.md"
        doc.write_text(
            "# 智能体功能设计\n\n"
            "> **文档控制信息**\n"
            "> - **文档标识**: DOC-002\n"
            "> - **当前版本**: V2.4.1\n\n"
            "### 修订历史记录\n\n"
            "| 版本号 | 修订日期 | 修订人 | 修订描述 |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| **V2.4.0** | 2026-10-03 | Agent | 历史发布版本（漏记 V2.4.1） |\n",
            encoding="utf-8",
        )
        is_synced, h_ver, r_ver, err = check_doc_control_sync.check_file_version_sync(doc)
        self.assertFalse(is_synced)
        self.assertIn("不一致", err)
        self.assertIn("2.4.1", err)
        self.assertIn("2.4.0", err)

    def test_scan_version_sync_batch(self):
        """测试批量扫描与漂移文件收集"""
        doc_ok = self.test_dir / "ok.md"
        doc_ok.write_text(
            "# OK\n\n> - **当前版本**: V1.0.0\n\n### 修订历史\n\n| 版本号 | 描述 |\n| :--- | :--- |\n| V1.0.0 | 初始 |\n",
            encoding="utf-8",
        )
        doc_bad = self.test_dir / "bad.md"
        doc_bad.write_text(
            "# BAD\n\n> - **当前版本**: V2.0.0\n\n### 修订历史\n\n| 版本号 | 描述 |\n| :--- | :--- |\n| V1.9.0 | 漏升 |\n",
            encoding="utf-8",
        )
        total, drifts = check_doc_control_sync.scan_version_sync(self.test_dir)
        self.assertEqual(total, 2)
        self.assertEqual(len(drifts), 1)
        self.assertEqual(drifts[0]["file"], "bad.md")


class TestArchiveExemptionBatchA(unittest.TestCase):
    """批次 A 回归（BK-0001 / BK-0002 / BK-0021）：归档豁免与 --output 落点解耦"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_batch_a_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_revision_doc(self, rel_path, rows=7):
        path = self.test_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        body = [
            "# 文档",
            "",
            "### 修订历史记录 (Revision History)",
            "",
            "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for i in range(rows):
            body.append(f"| **V1.0.{i}** | 2026-01-0{i + 1} | AI Agent | 架构师 | r{i} |")
        path.write_text("\n".join(body) + "\n", encoding="utf-8")
        return path

    def test_trim_revision_exempts_archive_reports(self):
        """BK-0001：--fix 不得改写 project/reviews 归档报告（G1 逐字归档红线）"""
        archived = self._write_revision_doc("project/reviews/report.md")
        normal = self._write_revision_doc("project/plans/plan.md")
        before = archived.read_bytes()

        total, overflow, overflow_list = trim_revision.scan_and_trim(self.test_dir, max_keep=5, fix=True)

        self.assertEqual(archived.read_bytes(), before, "BK-0001: 归档报告必须逐字节不变")
        self.assertNotIn("report.md", " ".join(str(p) for p, _ in overflow_list),
                         "BK-0001: 归档报告不得计入超额清单")
        self.assertLess(normal.read_text(encoding="utf-8").count("| **V1.0."), 7,
                        "非归档文档仍应被正常裁剪")

    def test_generate_llms_txt_excludes_archive_reports(self):
        """BK-0002：机器地图不得收录归档条目（与 links/audit 三消费者一致）"""
        self._write_revision_doc("project/reviews/report.md", rows=1)
        self._write_revision_doc("project/plans/plan.md", rows=1)
        out = self.test_dir / "llms.txt"

        generate_llms_txt.generate_llms_txt(self.test_dir, out, project_name="T")
        content = out.read_text(encoding="utf-8")
        self.assertNotIn("project/reviews/", content, "BK-0002: 归档条目必须被排除")
        self.assertIn("project/plans/plan.md", content, "BK-0002: 非归档文档必须保留")

    def test_generate_llms_txt_output_defaults_to_root(self):
        """BK-0021：--output 缺省时落点随 --root 派生，隔离复算成立"""
        docs = self.test_dir / "docs"
        (docs / "explanation").mkdir(parents=True)
        (docs / "explanation" / "a.md").write_text("# A\n\n正文段落\n", encoding="utf-8")
        cwd = self.test_dir / "cwd"
        cwd.mkdir()

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(docs), "--name", "T"],
            capture_output=True, text=True, cwd=str(cwd),
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue((docs / "llms.txt").exists(), "BK-0021: 默认落点应随 --root 派生")
        self.assertFalse((cwd / "docs" / "llms.txt").exists(), "BK-0021: 不得写回 CWD 相对路径")


    def test_trim_revision_rejects_archive_under_narrow_root(self):
        """R1-2：--root 收窄到归档子树内时仍不得改写交付凭据"""
        archived = self._write_revision_doc("docs/project/reviews/report.md")
        before = archived.read_bytes()
        narrow_root = self.test_dir / "docs" / "project" / "reviews"

        trim_revision.scan_and_trim(narrow_root, max_keep=5, fix=True)

        self.assertEqual(archived.read_bytes(), before, "R1-2: 任意 --root 下归档都必须只读")

    def test_trim_revision_rejects_archive_under_wide_root(self):
        """R1-2：--root 放宽到仓库上层时仍不得改写交付凭据"""
        archived = self._write_revision_doc("docs/project/reviews/report.md")
        before = archived.read_bytes()

        trim_revision.scan_and_trim(self.test_dir, max_keep=5, fix=True)

        self.assertEqual(archived.read_bytes(), before, "R1-2: 宽 root 下归档也必须只读")

    def test_trim_revision_single_file_archive_reports_skip(self):
        """R1-3：单文件模式与目录模式判定同构，且必须显式提示跳过（不得静默假绿）"""
        archived = self._write_revision_doc("docs/project/reviews/report.md")
        before = archived.read_bytes()

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "trim-revision.py"), "--root", str(archived), "--fix"],
            capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(archived.read_bytes(), before, "R1-3: 单文件模式不得改写归档")
        self.assertIn("归档", res.stdout + res.stderr, "R1-3: 必须显式说明跳过，而非静默假绿")

    def test_generate_llms_txt_excludes_archive_under_narrow_root(self):
        """R1-7 兜底：--root 收窄时机器地图同样不得收录归档条目"""
        self._write_revision_doc("docs/project/reviews/report.md", rows=1)
        self._write_revision_doc("docs/project/plans/plan.md", rows=1)
        narrow = self.test_dir / "docs" / "project"
        out = self.test_dir / "out.txt"

        generate_llms_txt.generate_llms_txt(narrow, out, project_name="T")

        content = out.read_text(encoding="utf-8")
        self.assertNotIn("report.md", content, "R1-7: 收窄 root 下归档条目仍须被排除")
        self.assertIn("plan.md", content, "非归档文档必须保留")


    def test_trim_revision_empty_scope_does_not_claim_compliance(self):
        """R1-3：目标全部被豁免（或为空）时不得输出「完美/符合规范」的结论性文案"""
        archived = self._write_revision_doc("docs/project/reviews/report.md")

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "trim-revision.py"), "--root", str(archived), "--fix"],
            capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("完美", res.stdout, "R1-3: 无可检查文档时不得宣称符合规范")
        self.assertIn("归档", res.stdout + res.stderr, "R1-3: 必须说明跳过原因")

    def test_trim_revision_library_call_resolves_root(self):
        """DR1-2：库调用 + cwd 位于归档内时同样不得改写归档"""
        archived = self._write_revision_doc("docs/project/reviews/report.md")
        before = archived.read_bytes()
        cwd = self.test_dir / "docs" / "project" / "reviews"
        old_cwd = os.getcwd()
        try:
            os.chdir(cwd)
            trim_revision.scan_and_trim(Path("."), max_keep=5, fix=True)
        finally:
            os.chdir(old_cwd)
        self.assertEqual(archived.read_bytes(), before, "DR1-2: 库调用形态也必须只读归档")

    def test_generate_llms_txt_refuses_output_inside_archive(self):
        """DR1-3：--output 落在交付凭据归档内时必须拒绝写入"""
        archived_dir = self.test_dir / "docs" / "project" / "reviews"
        archived_dir.mkdir(parents=True)
        (self.test_dir / "docs" / "explanation").mkdir(parents=True, exist_ok=True)
        (self.test_dir / "docs" / "explanation" / "a.md").write_text("# A\n\n正文\n", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"),
             "--root", str(archived_dir), "--name", "T"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(res.returncode, 0, "DR1-3: 不得向交付凭据归档内写机器地图")
        self.assertFalse((archived_dir / "llms.txt").exists(), "DR1-3: 归档内不得出现 llms.txt")


class TestBatchBLlmsIntegrity(unittest.TestCase):
    """批次 B 回归（BK-0023 / BK-0025）：机器地图写入侧安全与一致性门禁"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_batch_b_"))
        self.docs = self.test_dir / "docs"
        (self.docs / "explanation").mkdir(parents=True)
        (self.docs / "explanation" / "a.md").write_text("# A 文档\n\n正文段落。\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_llms(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.docs), *extra],
            capture_output=True, text=True,
        )

    def test_llms_output_symlinked_into_archive_is_refused(self):
        """BK-0023：缺省落点经符号链接指向归档文件时必须拒绝（不得穿透写入）"""
        archived_dir = self.docs / "project" / "reviews"
        archived_dir.mkdir(parents=True)
        victim = archived_dir / "victim.md"
        victim.write_text("# 归档受害者\n\n逐字凭据\n", encoding="utf-8")
        before = victim.read_bytes()
        try:
            (self.docs / "llms.txt").symlink_to(Path("project") / "reviews" / "victim.md")
        except OSError:
            self.skipTest("平台不支持符号链接")

        res = self._run_llms()

        self.assertNotEqual(res.returncode, 0, "BK-0023: 符号链接穿透必须被拒绝")
        self.assertEqual(victim.read_bytes(), before, "BK-0023: 归档文件不得被改写")

    def test_llms_zero_coverage_is_refused(self):
        """BK-0023：收录 0 篇时拒绝落盘（避免用空壳覆盖既有 SSOT 地图）"""
        shutil.rmtree(self.docs / "explanation")
        archived_dir = self.docs / "project" / "reviews"
        archived_dir.mkdir(parents=True)
        (archived_dir / "only.md").write_text("# 仅归档\n\n正文\n", encoding="utf-8")

        res = self._run_llms()

        self.assertNotEqual(res.returncode, 0, "BK-0023: 零覆盖必须拒绝落盘")
        self.assertFalse((self.docs / "llms.txt").exists(), "BK-0023: 不得生成空壳机器地图")

    def test_audit_detects_llms_map_drift(self):
        """BK-0025：机器地图与注册命令生成物不一致时，健康门禁必须报出"""
        (self.docs / "llms.txt").write_text("# Stale Map\n\n- 过期的条目\n", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )

        combined = res.stdout + res.stderr
        self.assertIn("机器地图一致性缺陷", combined, "BK-0025: 漂移必须被机械检出")
        reject_lines = [ln for ln in combined.splitlines() if "REJECTED" in ln]
        self.assertTrue(
            any("机器地图不一致" in ln for ln in reject_lines),
            "BK-0025: PASS 接线必须承重——REJECTED 原因行须显式列出机器地图不一致（防接线空转）",
        )
        self.assertNotEqual(res.returncode, 0, "BK-0025: 漂移必须导致门禁失败")

    def test_audit_accepts_consistent_llms_map(self):
        """BK-0025：以注册命令生成的机器地图不得被误报"""
        gen = self._run_llms("--output", str(self.docs / "llms.txt"))
        self.assertEqual(gen.returncode, 0, gen.stderr)

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )
        self.assertNotIn("机器地图", res.stdout + res.stderr,
                         "BK-0025: 一致的机器地图不得被误报（精确断言，防通用假阳性）")


    def test_audit_accepts_map_generated_with_custom_name(self):
        """R1-2：以合法 --name 参数生成的地图不得被判漂移（判定参数须与生成参数同源）"""
        gen = self._run_llms("--name", "Custom Project", "--output", str(self.docs / "llms.txt"))
        self.assertEqual(gen.returncode, 0, gen.stderr)

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )
        self.assertNotIn("机器地图", res.stdout + res.stderr,
                         "R1-2: 自定义 --name 的地图不得被误报为漂移")

    def test_audit_skips_when_nothing_indexable(self):
        """R1-1：无可收录文档时不得形成不可修复的硬阻断死胡同"""
        shutil.rmtree(self.docs / "explanation")
        # 根文件不入机器地图但计入 total_files，用于绕过 audit 的 total_files==0 早退（否则本用例空转）
        (self.docs / "index.md").write_text("# 索引\n\n根文件不进入机器地图。\n", encoding="utf-8")
        archived_dir = self.docs / "project" / "reviews"
        archived_dir.mkdir(parents=True)
        (archived_dir / "only.md").write_text("# 仅归档\n\n正文\n", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )
        self.assertNotIn("机器地图", res.stdout + res.stderr,
                         "R1-1: 零覆盖场景不适用本项，不得硬阻断")

    def test_llms_zero_coverage_leaves_no_empty_dirs(self):
        """R1-7：零覆盖拒绝落盘时不得留下空目录副作用"""
        shutil.rmtree(self.docs / "explanation")
        out = self.test_dir / "newdir" / "llms.txt"

        res = self._run_llms("--output", str(out))

        self.assertNotEqual(res.returncode, 0, "R1-7: 零覆盖必须拒绝落盘")
        self.assertFalse((self.test_dir / "newdir").exists(), "R1-7: 拒绝落盘不得留下空目录")


    def test_audit_skips_when_map_exists_but_nothing_indexable(self):
        """R1-1：地图存在但已无文档可收录时，不得形成不可修复的硬阻断死胡同

        注意：本用例锁定的是 **BK-0027 显式登记的豁免**（零覆盖时一致性检查不适用），
        而非「该状态下地图条目已被校验」这一正确性契约——见 GOVERNANCE §4.1 零覆盖态边界。
        """
        shutil.rmtree(self.docs / "explanation")
        (self.docs / "index.md").write_text("# 索引\n\n根文件不进入机器地图。\n", encoding="utf-8")
        archived_dir = self.docs / "project" / "reviews"
        archived_dir.mkdir(parents=True)
        (archived_dir / "only.md").write_text("# 仅归档\n\n正文\n", encoding="utf-8")
        (self.docs / "llms.txt").write_text("# 陈旧地图\n\n- 旧条目\n", encoding="utf-8")

        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )
        self.assertNotIn("机器地图", res.stdout + res.stderr,
                         "R1-1: 零覆盖场景本项不适用，不得硬阻断（修复命令必然 rc=1）")


    _CTRL = (
        "> **文档控制信息**\n"
        "> - **文档标识**: {doc_id}\n"
        "> - **当前版本**: V1.0.0\n"
        "\n### 修订历史记录 (Revision History)\n\n"
        "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 初版 |\n"
    )

    def _prepare_compliant_tree(self):
        """构造分数达标的合规树：用于锁定 PASS 接线，使漂移成为唯一阻断原因。"""
        shutil.rmtree(self.docs / "explanation", ignore_errors=True)
        (self.docs / "explanation").mkdir(parents=True, exist_ok=True)
        (self.docs / "explanation" / "a.md").write_text(
            "# A 文档\n\n" + self._CTRL.format(doc_id="DOC-A"), encoding="utf-8")
        (self.docs / "index.md").write_text(
            "# 索引\n\n" + self._CTRL.format(doc_id="DOC-IDX") + "\n- [A 文档](./explanation/a.md)\n",
            encoding="utf-8")

    def test_audit_blocks_drift_on_a_perfect_tree(self):
        """BK-0025：合规树上的漂移必须阻断——锁定 PASS 接线承重（防 MUT-E1 空转）"""
        self._prepare_compliant_tree()
        gen = self._run_llms("--output", str(self.docs / "llms.txt"))
        self.assertEqual(gen.returncode, 0, gen.stderr)

        audit_cmd = [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)]
        baseline = subprocess.run(audit_cmd, capture_output=True, text=True)
        self.assertEqual(baseline.returncode, 0,
                         f"夹具本身必须是 PASS 的合规树：{baseline.stdout}{baseline.stderr}")

        (self.docs / "llms.txt").write_text("# Stale Map\n\n- 过期条目\n", encoding="utf-8")
        drifted = subprocess.run(audit_cmd, capture_output=True, text=True)

        self.assertNotEqual(drifted.returncode, 0,
                            "漂移必须阻断：若 PASS 接线被移除，本断言即打红（接线承重）")
        self.assertIn("机器地图不一致", drifted.stdout + drifted.stderr)


class TestBatchCLlmsHintHardening(unittest.TestCase):
    """批次 C 回归（BK-0026 / BK-0027）：提示文案的终端净化与零覆盖口径登记"""

    _CTRL = (
        "> **文档控制信息**\n"
        "> - **文档标识**: {doc_id}\n"
        "> - **当前版本**: V1.0.0\n"
        "\n### 修订历史记录 (Revision History)\n\n"
        "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 初版 |\n"
    )

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_batch_c_"))
        self.docs = self.test_dir / "docs"
        (self.docs / "explanation").mkdir(parents=True)
        (self.docs / "explanation" / "a.md").write_text(
            "# A 文档\n\n" + self._CTRL.format(doc_id="DOC-A"), encoding="utf-8")
        (self.docs / "index.md").write_text(
            "# 索引\n\n" + self._CTRL.format(doc_id="DOC-IDX") + "\n- [A 文档](./explanation/a.md)\n",
            encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_drifted_map(self, project_name):
        """写入首行为指定项目名的漂移地图（触发一致性缺陷并带上该项目名）。"""
        (self.docs / "llms.txt").write_text(
            f"# {project_name} Machine-Readable Knowledge Base Map\n\n- 过期条目\n", encoding="utf-8")

    def _audit(self):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )

    def test_hint_strips_terminal_control_sequences(self):
        """BK-0026 / D2-3：项目名含 OSC/ESC/BEL 时不得把裸控制序列写入门禁输出"""
        self._write_drifted_map("A\x1b]0;PWNED\x07")

        res = self._audit()
        combined = res.stdout + res.stderr

        self.assertIn("机器地图", combined, "前置：漂移必须被检出（否则断言无意义）")
        self.assertNotIn("\x1b", combined, "D2-3: 不得把裸 ESC 写入输出（可篡改终端标题/剪贴板）")
        self.assertNotIn("\x07", combined, "D2-3: 不得把裸 BEL 写入输出")

    def test_hint_rejects_nul_name(self):
        """BK-0026 / D2-5：真含 NUL 的项目名不得把 NUL 写入输出（此前该断言因夹具不含 NUL 而恒真）"""
        self._write_drifted_map("A\x00B")

        res = self._audit()
        combined = res.stdout + res.stderr

        self.assertIn("机器地图", combined, "前置：漂移必须被检出")
        self.assertNotIn("\x00", combined, "D2-5: 不得把 NUL 写入输出")

    def test_hint_rejects_overlong_name(self):
        """BK-0026 / D2-5：超长项目名不得把缺陷行膨胀"""
        self._write_drifted_map("X" * 100000)

        res = self._audit()
        combined = res.stdout + res.stderr

        self.assertIn("机器地图", combined, "前置：漂移必须被检出")
        self.assertLess(len(combined), 20000, "D2-5: 超长项目名不得把缺陷行膨胀 10 万字节")

    def test_legit_edge_names_are_not_misjudged_as_drift(self):
        """R1-1：合法但边缘的项目名不得因显示净化而被误判漂移（判定必须用未净化原名）"""
        for name in ("L" * 65, "中" * 65, " Foo ", "A\u00a0B"):
            with self.subTest(name=repr(name[:10])):
                (self.docs / "llms.txt").unlink(missing_ok=True)  # 显式改名须先移除既有地图（身份写保护）
                gen = subprocess.run(
                    [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.docs),
                     "--output", str(self.docs / "llms.txt"), "--name=" + name],
                    capture_output=True, text=True,
                )
                self.assertEqual(gen.returncode, 0, gen.stderr)

                res = self._audit()
                self.assertNotIn("机器地图", res.stdout + res.stderr,
                                 f"R1-1: 合法边缘名 {name[:10]!r} 不得被误判漂移")

    def test_hint_command_is_executable_for_dash_prefixed_name(self):
        """BK-0026 / D2-4：以 - 开头的项目名不得让修复建议变成 rc=2 死巷"""
        self._write_drifted_map("--root")

        res = self._audit()
        combined = res.stdout + res.stderr

        self.assertIn("--name=--root", combined, "D2-4: 提示须用 --name=<value> 赋值形式")
        gen = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.docs),
             "--output", str(self.docs / "llms.txt"), "--name=--root"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(gen.returncode, 2, "D2-4: --name= 形式必须被 argparse 正常接受")
        self.assertNotIn("expected one argument", gen.stderr)


    def test_malformed_names_never_emit_a_name_option(self):
        """R1-1 / R1-9：反解不可信或名字不可安全回显时，提示不得下发改名命令

        （否则用户照做会把地图 H1 静默改写为占位名或截断名，项目身份在 SSOT 中丢失）
        """
        for name in ("", "A\nB", "A\u2028B", "A\x1b]0;X\x07", "X" * 100000):
            with self.subTest(name=repr(name[:8])):
                self._write_drifted_map(name)

                res = self._audit()
                out = res.stdout + res.stderr
                self.assertIn("机器地图", out, "前置：漂移必须被检出")
                self.assertNotIn("--name=", out, f"R1-1: 畸形名 {name[:8]!r} 不得下发改名命令")

    def test_hint_name_matches_map_identity(self):
        """R1-3 / R1-9：提示中的 --name 值必须与地图 H1 项目名逐字相同（身份保真）"""
        for name in ("CR 公共技能库", " Foo ", "--root"):
            with self.subTest(name=repr(name)):
                self._write_drifted_map(name)

                res = self._audit()
                out = res.stdout + res.stderr
                line = next((ln for ln in out.splitlines() if "--name=" in ln), None)
                self.assertIsNotNone(line, f"可安全回显的名字应下发可执行命令：{name!r}")
                segment = line.split("--name=", 1)[1]
                end = segment.find(" 运行")
                token = (segment[:end] if end > 0 else segment).strip()
                if token.startswith("'") and token.endswith("'"):
                    token = token[1:-1]
                self.assertEqual(token, name, "提示 --name 值必须逐字等于地图身份")


    def test_failclosed_hints_contain_no_executable_command(self):
        """R1-1：fail-closed 分支不得内嵌可执行命令（其缺省 --name=System 即会改写身份）"""
        for name in ("", "A\nB", "A\u2028B", "A\x1b]0;X\x07", "A\u00a0B", "X" * 100000):
            with self.subTest(name=repr(name[:8])):
                self._write_drifted_map(name)

                res = self._audit()
                out = res.stdout + res.stderr
                self.assertIn("机器地图", out, "前置：漂移必须被检出")
                self.assertNotIn("generate-llms-txt.py", out,
                                 "R1-1: fail-closed 分支不得给出可执行命令")

    def test_bare_regeneration_never_rewrites_identity(self):
        """R1-1 + BK-0030：缺省重生成要么拒绝、要么逐字沿用既有身份（H1 永不被改写）"""
        for name in ("", "A\nB", "A\u2028B", "CR 公共技能库", "A\u00a0B"):
            with self.subTest(name=repr(name[:8])):
                self._write_drifted_map(name)
                before_h1 = (self.docs / "llms.txt").read_text(encoding="utf-8").splitlines()[0]

                subprocess.run(
                    [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.docs),
                     "--output", str(self.docs / "llms.txt")],
                    capture_output=True, text=True,
                )

                after_h1 = (self.docs / "llms.txt").read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(after_h1, before_h1,
                                 "缺省重生成不得改写地图身份（要么拒绝，要么沿用）")

    def test_contract_phrase_name_round_trips(self):
        """R1-3：名含契约短语时提示 --name 值必须逐字等于地图身份（fullmatch 关闭截断）"""
        name = "X Machine-Readable Knowledge Base Map Y"
        self._write_drifted_map(name)

        res = self._audit()
        out = res.stdout + res.stderr

        self.assertIn("机器地图", out, "前置：漂移必须被检出")
        segment = out.split("--name=", 1)[1]
        end = segment.find(" 运行")
        token = (segment[:end] if end > 0 else segment).strip()
        if token.startswith("'") and token.endswith("'"):
            token = token[1:-1]
        self.assertEqual(token, name, "R1-3: 契约短语名不得被截断")


class TestBatchDIdentityContract(unittest.TestCase):
    """批次 D 回归（BK-0030 / BK-0031）：身份写保护闸门的完备性与契约登记"""

    _CTRL = (
        "> **文档控制信息**\n"
        "> - **文档标识**: {doc_id}\n"
        "> - **当前版本**: V1.0.0\n"
        "\n### 修订历史记录 (Revision History)\n\n"
        "| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| **V1.0.0** | 2026-10-09 | DSH AI Agent | 王辉 | 初版 |\n"
    )

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_batch_d_"))
        self.docs = self.test_dir / "docs"
        (self.docs / "explanation").mkdir(parents=True)
        (self.docs / "explanation" / "a.md").write_text(
            "# A 文档\n\n" + self._CTRL.format(doc_id="DOC-A"), encoding="utf-8")
        (self.docs / "index.md").write_text(
            "# 索引\n\n" + self._CTRL.format(doc_id="DOC-IDX") + "\n- [A 文档](./explanation/a.md)\n",
            encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _run_llms(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", str(self.docs), *extra],
            capture_output=True, text=True,
        )

    def _audit(self):
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", str(self.docs)],
            capture_output=True, text=True,
        )

    def _write_map(self, head: str) -> Path:
        path = self.docs / "llms.txt"
        path.write_text(head, encoding="utf-8")
        return path

    def test_regeneration_keeps_identity_and_passes(self):
        """BK-0030 ①④：合法重生成（未显式 --name / 显式同名）必须放行且 H1 逐字节不变"""
        first = self._run_llms("--output", str(self.docs / "llms.txt"))
        self.assertEqual(first.returncode, 0, first.stderr)
        baseline = (self.docs / "llms.txt").read_bytes()

        again = self._run_llms("--output", str(self.docs / "llms.txt"))
        self.assertEqual(again.returncode, 0,
                         f"缺省 --name 必须沿用既有身份并放行：{again.stderr}")
        self.assertEqual((self.docs / "llms.txt").read_bytes(), baseline,
                         "重生成不得改变既有地图身份或内容")

        same = self._run_llms("--output", str(self.docs / "llms.txt"), "--name=System")
        self.assertEqual(same.returncode, 0, "显式同名必须放行")

        res = self._audit()
        self.assertNotIn("机器地图", res.stdout + res.stderr, "一致地图不得被报缺陷")

    def test_custom_identity_survives_bare_regeneration(self):
        """BK-0030 ①：自定义身份地图在未显式 --name 的重生成下必须保持不变（不再被拒或改名）"""
        created = self._run_llms("--output", str(self.docs / "llms.txt"), "--name=CR 公共技能库")
        self.assertEqual(created.returncode, 0, created.stderr)
        baseline = (self.docs / "llms.txt").read_bytes()

        again = self._run_llms("--output", str(self.docs / "llms.txt"))
        self.assertEqual(again.returncode, 0,
                         f"自定义身份的合法重生成必须放行（沿用既有身份）：{again.stderr}")
        self.assertEqual((self.docs / "llms.txt").read_bytes(), baseline, "身份必须逐字节保持")

    def test_gate_fails_closed_on_non_utf8_map(self):
        """BK-0031：非合法 UTF-8 既有地图必须拒绝（独立成例，不受执行权限影响）"""
        path = self._write_map("# placeholder Machine-Readable Knowledge Base Map\n")
        path.write_bytes(b"# A" + bytes([0xFF]) + b"B Machine-Readable Knowledge Base Map\n\n- item\n")
        before = path.read_bytes()

        res = self._run_llms("--output", str(path))

        self.assertNotEqual(res.returncode, 0, "非 UTF-8 既有地图必须拒绝")
        self.assertEqual(path.read_bytes(), before, "字节必须逐字节不变（不得归一化为 U+FFFD）")

    def test_gate_fails_closed_on_unreadable_map(self):
        """BK-0030 ③：既有地图不可读时必须拒绝（仅在特权环境下跳过本用例）"""
        path = self._write_map("# Secret Project Machine-Readable Knowledge Base Map\n\n- item\n")
        path.chmod(0o200)
        try:
            if os.access(path, os.R_OK):
                self.skipTest("当前环境以特权运行，无法构造不可读文件")
            res = self._run_llms("--output", str(path))
            self.assertNotEqual(res.returncode, 0, "不可读既有地图必须拒绝")
        finally:
            path.chmod(0o600)

    def test_explicit_foreign_name_is_refused(self):
        """BK-0031 契约：显式异名重生成必须拒绝且既有地图逐字节不变"""
        created = self._run_llms("--output", str(self.docs / "llms.txt"), "--name=Origin Identity")
        self.assertEqual(created.returncode, 0, created.stderr)
        before = (self.docs / "llms.txt").read_bytes()

        res = self._run_llms("--output", str(self.docs / "llms.txt"), "--name=Other Identity")

        self.assertNotEqual(res.returncode, 0, "显式异名必须拒绝（改名须先移除既有地图）")
        self.assertEqual((self.docs / "llms.txt").read_bytes(), before, "字节必须逐字节不变")

    def test_audit_reports_non_utf8_map(self):
        """BK-0031 / R1-13：audit 对非合法 UTF-8 地图必须报缺陷（严格解码不得归一化放行）"""
        (self.docs / "llms.txt").write_bytes(
            b"# A" + bytes([0xFF]) + b"B Machine-Readable Knowledge Base Map\n\n- item\n")

        res = self._audit()
        out = res.stdout + res.stderr

        self.assertIn("机器地图", out, "非 UTF-8 既有地图必须被报为缺陷")
        # 有损解码（errors="replace"）会把身份归一化为 U+FFFD 并当作可安全回显的名字下发 → 必须禁止
        self.assertNotIn("--name=", out, "非法 UTF-8 身份不得被归一化后作为 --name 下发")
        self.assertNotEqual(res.returncode, 0, "非 UTF-8 地图不得通过一致性判定")

    def test_split_line_names_are_refused_at_generation(self):
        """BK-0030 ②：含行分隔符的项目名必须在生成前被拒（不得铸出永久不可修复的地图）"""
        for name in ("A\nB", "A\rB", "A\u2028B", "A\u000bB", "A\u0085B"):
            with self.subTest(name=repr(name[:6])):
                res = self._run_llms("--output", str(self.docs / "llms.txt"), "--name=" + name)
                self.assertNotEqual(res.returncode, 0, "含行分隔符的项目名必须被拒绝")
                self.assertFalse((self.docs / "llms.txt").exists(), "不得留下不可修复的地图")

    def test_empty_explicit_name_is_not_silently_replaced(self):
        """BK-0030：显式 --name="" 不得被静默替换为 System"""
        res = self._run_llms("--output", str(self.docs / "llms.txt"), "--name=")
        if res.returncode == 0:
            head = (self.docs / "llms.txt").read_text(encoding="utf-8").splitlines()[0]
            self.assertTrue(head.startswith("#  Machine-Readable"),
                            f"空名不得被替换为 System：{head!r}")
        else:
            self.assertIn("--name", res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
