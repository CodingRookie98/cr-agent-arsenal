#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manage-backlog.py 结项收口契约测试 (BK-0042)

覆盖三个动作对卡片自身状态的一致性保证：
  - create: §3 DoD 复选框 + 人工核验职责说明；§4「*(未开工)*」建卡占位语
  - close : 机械收敛占位语；DoD 未勾选时在结项记录中给出项数提示；不代勾复选框
  - reopen: 保留历史结项记录并追加「重启记录」，当前状态以元数据 status: active 为准

全部用例通过 CLI 子进程驱动（与用户实际调用路径一致），互不共享临时目录。
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
MANAGE_SCRIPT = SCRIPTS_DIR / "manage-backlog.py"
BACKLOG_REL = Path("docs") / "project" / "backlog"


class ManageBacklogCloseContractTest(unittest.TestCase):
    """drive manage-backlog.py CLI against an isolated temp docs root"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="doc_gov_test_close_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_cli(self, *args) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(MANAGE_SCRIPT), "--root", str(self.test_dir)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    # ---------- helpers ----------

    def active_cards(self) -> list:
        return sorted((self.test_dir / BACKLOG_REL / "active").glob("BK-*.md"))

    def create_card(self, acs=("各租户数据物理隔离", "边界用例双向成立")) -> Path:
        args = ["create", "多租户行级隔离", "--type", "Feature", "--priority", "P1"]
        for ac in acs:
            args += ["--acceptance", ac]
        res = self.run_cli(*args)
        self.assertEqual(res.returncode, 0, f"create 失败: {res.stderr}")
        cards = self.active_cards()
        self.assertEqual(len(cards), 1, f"应恰好创建 1 张卡片: {cards}")
        return cards[0]

    def close_card(self, card_id="BK-0001", resolution="delivered") -> None:
        res = self.run_cli("close", card_id, "--resolution", resolution, "--destination", "演示交付")
        self.assertEqual(res.returncode, 0, f"close 失败: {res.stderr}")

    def archived_card(self, card_id="BK-0001") -> Path:
        cards = sorted((self.test_dir / BACKLOG_REL / "archive").rglob(f"{card_id}-*.md"))
        self.assertEqual(len(cards), 1, f"应恰好归档 1 张卡片: {cards}")
        return cards[0]

    # ---------- create ----------

    def test_create_writes_dod_checklist_and_manual_tick_duty(self):
        """建卡模板必须写明 DoD 由作者人工勾选，且保留 *(未开工)* 占位语"""
        text = self.create_card().read_text(encoding="utf-8")
        self.assertIn("- [ ] 各租户数据物理隔离", text)
        self.assertIn("- [ ] 边界用例双向成立", text)
        self.assertIn("由作者在结项前人工核验并逐项勾选", text)
        self.assertIn("不代勾验收准则", text)
        self.assertIn("*(未开工)*", text)

    # ---------- close ----------

    def test_close_removes_placeholder_and_hints_unchecked_dod(self):
        """close 归档后：占位语消失、结项记录存在、未勾选 DoD 有项数提示"""
        self.create_card()
        self.close_card()
        text = self.archived_card().read_text(encoding="utf-8")
        self.assertNotIn("未开工", text)
        self.assertIn("### 结项记录", text)
        self.assertIn("§3 DoD 仍有 2 项未勾选", text)
        self.assertIn("不代勾验收准则", text)

    def test_close_after_manual_tick_has_no_hint_and_keeps_ticks(self):
        """作者已手工勾选 DoD 时，close 不得改写复选框、也不得输出未勾选提示"""
        card = self.create_card()
        card.write_text(card.read_text(encoding="utf-8").replace("- [ ] ", "- [x] "), encoding="utf-8")
        self.close_card()
        text = self.archived_card().read_text(encoding="utf-8")
        self.assertIn("- [x] 各租户数据物理隔离", text)
        self.assertIn("- [x] 边界用例双向成立", text)
        self.assertNotIn("§3 DoD 仍有", text)
        self.assertNotIn("请作者核验后更新卡片", text)

    def test_close_converges_legacy_placeholder_wording(self):
        """历史卡片写作 *(未开工；结项时由 close 指令自动追加)* 时同样必须被收敛"""
        card = self.create_card()
        legacy = card.read_text(encoding="utf-8").replace("*(未开工)*", "*(未开工；结项时由 close 指令自动追加)*")
        card.write_text(legacy, encoding="utf-8")
        self.close_card()
        text = self.archived_card().read_text(encoding="utf-8")
        self.assertNotIn("未开工", text)
        self.assertIn("### 结项记录", text)

    def test_close_wontfix_sets_rejected_and_still_converges(self):
        """wontfix 结项走 rejected 状态分支，占位语仍需收敛"""
        self.create_card()
        self.close_card(resolution="wontfix")
        text = self.archived_card().read_text(encoding="utf-8")
        self.assertIn("status: rejected", text)
        self.assertNotIn("未开工", text)

    def test_close_unknown_id_is_error(self):
        """未知编号必须非零退出且给出可读错误，不得静默成功"""
        res = self.run_cli("close", "BK-9999", "--resolution", "delivered")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("未找到", res.stderr)

    # ---------- reopen ----------

    def test_reopen_appends_reopen_log_preserving_close_record(self):
        """reopen 后：状态回 active、历史结项记录保留、重启记录写明以元数据为准"""
        self.create_card()
        self.close_card()
        res = self.run_cli("reopen", "BK-0001")
        self.assertEqual(res.returncode, 0, f"reopen 失败: {res.stderr}")
        cards = self.active_cards()
        self.assertEqual(len(cards), 1, f"应恰好 1 张活跃卡片: {cards}")
        text = cards[0].read_text(encoding="utf-8")
        self.assertIn("status: active", text)
        self.assertIn("### 结项记录", text)
        self.assertIn("### 重启记录", text)
        self.assertIn("历史结项记录仅作留痕", text)
        self.assertIn("status: active` 为准", text)

    # ---------- index 刷新 ----------

    def test_close_and_reopen_refresh_index(self):
        """close/reopen 均须刷新 index.md 并保持条目可检索"""
        self.create_card()
        self.close_card()
        idx = (self.test_dir / BACKLOG_REL / "index.md").read_text(encoding="utf-8")
        self.assertIn("BK-0001", idx)
        self.assertIn("历史已归档项", idx)
        self.assertEqual(self.run_cli("reopen", "BK-0001").returncode, 0)
        idx_after = (self.test_dir / BACKLOG_REL / "index.md").read_text(encoding="utf-8")
        self.assertIn("BK-0001", idx_after)
        self.assertIn("现役活跃待办", idx_after)


if __name__ == "__main__":
    unittest.main()
