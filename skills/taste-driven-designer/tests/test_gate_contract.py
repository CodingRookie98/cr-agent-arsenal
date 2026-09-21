"""test_gate_contract.py — 收敛门禁契约的静态回归测试。

背景：实跑证据（tests/fixtures/critic-gate-counter-evidence.md）证明
「Critic 绝对评分 ≥9/10 才算完成」作为硬门禁不可靠（分辨率低、与改动无关、
无鉴别力、单 Critic 权威导致跨轮自相矛盾）。本测试把新门禁契约钉死为
可机械核验的静态断言，防止旧设计被无意识重新引入。

契约要点：
1. 技能文档不得再把绝对分数作为完成判据（无 "9/10" 硬门禁字样）；
2. 完成判据必须是三信号：结构清单 + 盲比改进 + 人类签收；
3. Critic 提示词模板必须要求版本回执、注入已决原则，并禁止输出数值分数；
4. 闭环协议必须包含鉴别力自检、冲突仲裁（原则优先）与评审账本；
5. 设计简报模板必须含已决原则台账与评审账本；
6. 反证 fixture 必须在位且保留原始证据数字。
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
PROTOCOL = SKILL_DIR / "references" / "critic-loop-protocol.md"
CRITIC_TMPL = SKILL_DIR / "templates" / "critic-prompt-template.md"
BRIEF_TMPL = SKILL_DIR / "templates" / "design-brief-template.md"
FIXTURE = SKILL_DIR / "tests" / "fixtures" / "critic-gate-counter-evidence.md"


def read(path):
    return path.read_text(encoding="utf-8")


def test_skill_has_no_hard_numeric_gate():
    text = read(SKILL_MD)
    assert "9/10" not in text, "SKILL.md 不得保留 9/10 硬门禁字样（分数只能作遥测）"
    assert "才算完成" not in text or "签收" in text, "完成判据不得是单一分数"


def test_skill_declares_three_signal_gate():
    text = read(SKILL_MD)
    for anchor in ("结构清单", "盲比", "签收"):
        assert anchor in text, f"SKILL.md 缺少三信号门禁锚点: {anchor}"
    assert "遥测" in text, "SKILL.md 必须明确绝对分数仅作遥测"


def test_critic_template_requires_receipt_and_bans_scores():
    text = read(CRITIC_TMPL)
    assert "Receipt" in text or "版本回执" in text, "Critic 模板必须要求版本回执"
    assert "out of 10" not in text, "Critic 模板不得再要求 10 分制打分"
    assert "禁止输出分数" in text or "不得输出分数" in text, "Critic 模板必须禁止数值评分输出"
    assert "已决原则" in text, "Critic 模板必须注入已决原则（防止凭空发明需求/跨轮反转）"


def test_protocol_documents_discrimination_and_arbitration():
    text = read(PROTOCOL)
    for anchor in ("鉴别力自检", "版本回执", "评审账本", "原则优先", "盲比"):
        assert anchor in text, f"闭环协议缺少锚点: {anchor}"


def test_protocol_drops_old_gate_wording():
    text = read(PROTOCOL)
    assert "≥9/10 → 放行" not in text
    assert "9/10 的收敛线" not in text


def test_brief_has_ledgers():
    text = read(BRIEF_TMPL)
    assert "已决原则台账" in text, "设计简报必须含已决原则台账"
    assert "评审账本" in text, "设计简报必须含评审账本（强制轮次上限）"


def test_counter_evidence_fixture_preserved():
    text = read(FIXTURE)
    for fragment in ("6.2 → 5.8", "70a91fc", "线胜于面", "空白截图"):
        assert fragment in text, f"反证 fixture 丢失原始证据片段: {fragment}"
