"""test_gate_contract.py — 收敛门禁契约的静态回归测试。

背景：实跑证据（tests/fixtures/critic-gate-counter-evidence.md）证明
「Critic 绝对评分 ≥9/10 才算完成」作为硬门禁不可靠（分辨率低、与改动无关、
无鉴别力、单 Critic 权威导致跨轮自相矛盾）。本测试把新门禁契约钉死为
可机械核验的静态断言，防止旧设计被重新引入。

断言强度说明（V1.1.1 加固，依据红队复核 🟡#6）：
- 不做单一字面匹配，改用「句子级语义扫描」：任何句子里同时出现
  「评分/分数」与「完成/放行/通过/达标」时，必须同时带禁止性表述
  （不得/禁止/仅作/不作判据/遥测/非门禁），否则判失败；
- 兼容改写措辞的规避（如"评分达到 9 分时才放行"）；
- 每个 Delta 修复点都有对应锚点断言（盲比上一版 / 轮次 nonce / 作废上限 /
  无法区分终止语义 / 回归维度 / 降级去标识）。

契约要点：
1. 技能文档不得把绝对分数当完成判据（句子级扫描 + 数字形态正则）；
2. 完成判据必须是三信号：结构清单 + 盲比改进 + 人类签收；
3. Critic 模板必须要求回执、注入已决原则、禁止数值评分，并含回归维度字段；
4. 闭环协议必须含鉴别力自检、冲突仲裁（原则优先）、评审账本与作废二级上限；
5. 盲比匿名性：轮次 nonce 与版本标识分离；
6. 设计简报模板必须含已决原则台账与评审账本；
7. 反证 fixture 必须在位且保留原始证据数字。
"""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
PROTOCOL = SKILL_DIR / "references" / "critic-loop-protocol.md"
CRITIC_TMPL = SKILL_DIR / "templates" / "critic-prompt-template.md"
BRIEF_TMPL = SKILL_DIR / "templates" / "design-brief-template.md"
FIXTURE = SKILL_DIR / "tests" / "fixtures" / "critic-gate-counter-evidence.md"

SCORE_WORDS = re.compile(r"评分|分数|得分|分值")
GATE_WORDS = re.compile(r"完成|放行|通过|达标|准入")
PROHIBITION_WORDS = re.compile(r"不得|禁止|不输出|不许|仅作|不作|遥测|非门禁|❌")


def read(path):
    return path.read_text(encoding="utf-8")


def assert_no_score_gate(text, label):
    """句子级扫描：分数与完成/放行同句时必须带禁止性表述。"""
    for sentence in re.split(r"[。！？\n]", text):
        if SCORE_WORDS.search(sentence) and GATE_WORDS.search(sentence):
            assert PROHIBITION_WORDS.search(sentence), (
                f"{label} 出现把分数当作完成/放行条件的表述: {sentence.strip()[:120]}"
            )


def test_skill_has_no_hard_numeric_gate():
    text = read(SKILL_MD)
    # 数字形态：9/10、≥9、达到/满 9 分、9.5 分 等
    assert not re.search(r"9\s*/\s*10", text), "SKILL.md 不得出现 9/10 门禁形态"
    assert not re.search(r"[≥>]\s*9|达(?:到|满)\s*9(?:\.\d+)?\s*分|9(?:\.\d+)?\s*分", text), (
        "SKILL.md 不得出现把 9 分当条件的形态"
    )
    assert_no_score_gate(text, "SKILL.md")


def test_skill_declares_three_signal_gate():
    text = read(SKILL_MD)
    assert re.search(r"三信号", text), "SKILL.md 必须声明三信号门禁"
    for anchor in ("结构清单", "盲比", "签收"):
        assert anchor in text, f"SKILL.md 缺少三信号门禁锚点: {anchor}"
    assert "遥测" in text, "SKILL.md 必须明确绝对分数仅作遥测"


def test_skill_invariant_two_allows_blind_previous_version():
    # 红队复核 🔴#1：铁律 2 必须允许盲比模式附上一版，否则与 Gate B 自相矛盾
    text = read(SKILL_MD)
    assert re.search(r"盲比模式另附去标识", text), "铁律 2 必须允许盲比模式附去标识的上一版"
    # 允许「默认只收当前产物 + 盲比例外」的表述；禁止的是绝对化的排他表述
    assert "任何模式下都不得携带" in text or "不得携带" in text, "铁律 2 必须保留隔离纪律"
    assert not re.search(r"只收当前产物[^。\n]*不(?:得|允许)附(?:上)?一版", text)


def test_critic_template_requires_receipt_and_bans_scores():
    text = read(CRITIC_TMPL)
    assert "Receipt" in text, "Critic 模板必须要求回执"
    assert "round-nonce" in text, "盲比回执必须使用与候选身份无关的轮次 nonce"
    assert "out of 10" not in text, "Critic 模板不得再要求 10 分制打分"
    assert "禁止输出分数" in text or "Do NOT output any numeric score" in text, (
        "Critic 模板必须禁止数值评分输出"
    )
    assert "已决原则" in text, "Critic 模板必须注入已决原则（防止凭空发明需求/跨轮反转）"
    assert "Regressed dimensions" in text, "盲比输出必须含回归维度字段（Gate B 证据来源）"


def test_protocol_documents_discrimination_and_arbitration():
    text = read(PROTOCOL)
    for anchor in ("鉴别力自检", "回执", "评审账本", "原则优先", "盲比"):
        assert anchor in text, f"闭环协议缺少锚点: {anchor}"


def test_protocol_has_void_cap_and_convergence_semantics():
    text = read(PROTOCOL)
    assert re.search(r"连续\s*\*{0,2}2 轮作废", text), "协议必须设作废二级上限（防无限重派）"
    assert re.search(r"轮次 nonce", text), "协议必须区分轮次 nonce 与版本标识"
    assert re.search(r"无法区分.*计入.*无改进|计入\"无改进\"", text), (
        "协议必须定义「无法区分」计入无改进的终止语义"
    )


def test_protocol_drops_old_gate_wording():
    text = read(PROTOCOL)
    assert "≥9/10 → 放行" not in text
    assert "9/10 的收敛线" not in text
    assert not re.search(r"9\s*/\s*10", text)
    assert_no_score_gate(text, "闭环协议")


def test_brief_has_ledgers():
    text = read(BRIEF_TMPL)
    assert "已决原则台账" in text, "设计简报必须含已决原则台账"
    assert "评审账本" in text, "设计简报必须含评审账本（强制轮次上限）"
    assert "作废计数" in text, "评审账本必须单列作废计数"
    assert_no_score_gate(text, "设计简报模板")


def test_counter_evidence_fixture_preserved():
    text = read(FIXTURE)
    for fragment in ("6.2 → 5.8", "70a91fc", "线胜于面", "空白截图"):
        assert fragment in text, f"反证 fixture 丢失原始证据片段: {fragment}"
