"""test_failure_recovery_contract.py — goal-loop 熔断条文契约自检。

把「3-Tries 熔断 + 证据门控重入」的核心不变量固化为断言，防止条文被后续改动静默简化
（本协议是行为规则，无运行时实现，故只能校验文本契约本身）。
覆盖:
  1. 四态状态机与 STOP → RECORD → RESEARCH 升级序列在场;
  2. Re-Entry Gate 四条判据 G1–G4 在场，且「默认不重入」为显式默认（fail-fast）;
  3. 预算数字: 重入 ≤2 轮、每轮 ≤2 次、总上限算式 3 + 2 + 2、成本上限 min(25%, 剩余÷3);
  4. Fast Path / Maintenance-Patch 无重入权（直接升级）;
  5. 升级为非阻塞（报告落盘 + parked + 继续独立工作项）;
  6. 报告模板含闸门判定记录 / 重入历史 / 成本快照;
  7. 路由层 SKILL.md 与细则层口径一致（不漂移）。

设计依据: Huang et al. 2310.01798（无外部反馈的自纠错有害 ⇒ 重入必须由外部证据门控）;
Azure Circuit Breaker（Open 期需外部状态改变方可进入 Half-Open，且只放行有限请求）。
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
PROTOCOL = SKILL_DIR / "references" / "failure-recovery-protocol.md"
SKILL_MD = SKILL_DIR / "SKILL.md"


def _protocol():
    return PROTOCOL.read_text(encoding="utf-8")


def test_state_machine_and_escalation_sequence():
    body = _protocol()
    for state in ("CLOSED", "OPEN", "HALF-OPEN", "ESCALATED"):
        assert state in body, f"缺少状态机状态: {state}"
    for step in ("STOP", "RECORD", "RESEARCH"):
        assert step in body, f"缺少升级序列步骤: {step}"


def test_reentry_gate_criteria_and_failsafe_default():
    body = _protocol()
    for gate in ("G1", "G2", "G3", "G4"):
        assert gate in body, f"缺少门控判据: {gate}"
    for semantic in ("新假设", "新证据", "非措辞改写", "预算未耗尽"):
        assert semantic in body, f"缺少判据语义: {semantic}"
    assert "默认值是不重入" in body, "必须显式声明 fail-fast 默认（举证责任在重入方）"


def test_reentry_budget_numbers():
    body = _protocol()
    assert "重入上限 **2 轮**" in body, "重入轮数上限须为 2"
    assert "**2 次**修复尝试" in body, "每轮尝试上限须为 2"
    assert "3 + 2 + 2 = **7 次**" in body, "总尝试上限须写出算式 3 + 2 + 2 = 7，便于复核"
    assert "25%" in body and "任务剩余预算 ÷ 3" in body, "缺少成本上限口径 min(25%, 剩余÷3)"


def test_light_paths_have_no_reentry():
    body = _protocol()
    assert "Maintenance-Patch → 直接 ESCALATED（无重入权）" in body, \
        "Fast Path / Maintenance-Patch 必须显式无重入权"


def test_escalation_is_non_blocking():
    body = _protocol()
    assert "`parked`" in body, "缺少阻塞点 parked 标记"
    assert "继续推进不依赖该阻塞点的独立工作项" in body, "升级必须非阻塞，不得全流程停摆"


def test_report_template_has_gate_fields():
    body = _protocol()
    for field in ("闸门判定记录", "重入历史", "成本快照"):
        assert field in body, f"报告模板缺少字段: {field}"


def test_reentry_counter_is_persisted_and_shell_safe():
    """G4 的计数与成本判定依赖落盘记录；跨会话恢复不得依赖会话记忆。"""
    body = _protocol()
    token = "0/3+R1-1/2"
    assert token in body, "缺少重入计数落盘记法"
    assert "计数落盘" in body and "报告同步" in body, "缺少计数落盘 / 报告同步条款"
    assert "每轮 HALF-OPEN 结束" in body, "报告必须在每轮重入后更新，否则跨会话 G4 计数失效"
    for doc in (PROTOCOL,
                SKILL_DIR / "templates" / "goal-plan-template.md",
                SKILL_DIR / "references" / "context-engineering.md"):
        assert token in doc.read_text(encoding="utf-8"), \
            f"{doc.name} 的检查点字段未承载重入记法"
    assert not any(c.isspace() for c in token), \
        "记法不得含空白（tracker 按单个 argv 整值写入，含空白会被截断）"


def test_routing_layer_matches_detail_layer():
    skill = SKILL_MD.read_text(encoding="utf-8")
    assert "证据门控" in skill, "SKILL.md 未声明证据门控重入"
    assert "≤2 轮 × 每轮 ≤2 次" in skill, "SKILL.md 与细则层的重入预算口径不一致"
    assert "非阻塞" in skill, "SKILL.md 未声明非阻塞升级"
