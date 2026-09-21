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
GATE_WORDS = re.compile(r"完成|放行|通过|达标|准入|交付|上线|发版|发布|合并")
PROHIBITION_WORDS = re.compile(r"不得|禁止|不输出|不许|不含|不涉及|不参与|不作为|不构成|仅作|不作|遥测|非门禁|❌")

# 边界声明：本扫描是**启发式护栏**（句子级词表共现），不是语义证明。
# 它拦截"把分数写成完成/放行条件"的常见表述与措辞变体；无法穷尽自然语言。
# 因此配套：① 三信号锚点断言（正向契约）；② 扫描器自检用例（误报/漏报边界）。


def read(path):
    return path.read_text(encoding="utf-8")


COMMAND_EXAMPLE = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")


def is_command_example(line):
    """命令行示例（bash/python3/npx ... skills/<name>/...）不是文档链接，豁免跨技能硬链接扫描。"""
    return bool(COMMAND_EXAMPLE.match(line))


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
    assert "任何模式下都不得携带实现代码" in text, "铁律 2 必须保留隔离纪律（精确锚点）"


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


def test_scanner_boundary_self_check():
    import pytest as _pytest
    # 合法否定表述不得误报（Delta R2 🟡N1）
    for legal in (
        "通过条件不含分数，也不涉及评分。",
        "分数不参与通过判定。",
        "分数不构成交付判据。",
    ):
        assert_no_score_gate(legal, "selftest-legal")
    # 违规表述（含措辞变体）必须拦截（Delta R2 ⚪N3）
    for illegal in (
        "仅当 Critic 评分达到 9 分时才放行。",
        "评分到 9 就放上线。",
        "分数达到门槛方可交付。",
    ):
        with _pytest.raises(AssertionError):
            assert_no_score_gate(illegal, "selftest-illegal")


def test_blind_anonymity_pinned():
    # Delta R2 🟡N2：匿名性必须被钉死，不能只断言 round-nonce 存在
    assert "盲比匿名性" in read(PROTOCOL), "协议必须声明盲比匿名性"
    tmpl = read(CRITIC_TMPL)
    assert "identities stripped" in tmpl or "去除一切版本标识" in tmpl, (
        "模板必须声明候选版本标识已剥离"
    )


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


CROSS_SKILL_LINK = re.compile("(?:^|[\\s(=/\"'>、，（])(?:[^)\\s\"'<>]*?[\\\\/])*(taste-driven-designer|dual-round-review|goal-loop|frontend-qa-gate|doc-governance|agy-delegation-workflow)[\\\\/]", re.IGNORECASE)


def test_no_cross_skill_relative_links_in_taste_docs():
    """独立分发纪律: taste 文档不得出现指向其它技能的相对路径硬链接 (R1-1)."""
    offenders = []
    root = Path(__file__).resolve().parents[1]
    for path in sorted(root.rglob("*.md")):
        if "__pycache__" in str(path):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if is_command_example(line):
                continue
            if CROSS_SKILL_LINK.search(line):
                offenders.append(f"{path.name}: {line.strip()[:80]}")
    assert not offenders, "跨技能相对路径硬链接(单技能安装会断链): " + "; ".join(offenders)


def test_cross_skill_scanner_self_check():
    illegal = [
        "[frontend-qa-gate](../frontend-qa-gate/SKILL.md)",
        "(../../skills/dual-round-review/SKILL.md)",
        "<a href=\"./goal-loop/SKILL.md\">x</a>",
        "[ref]: ../goal-loop/SKILL.md",
        "<a href=\"./doc-governance/SKILL.md\">x</a>",
        "裸路径 ../dual-round-review/SKILL.md 文本",
        '(..\\goal-loop\\SKILL.md)',
        '../Goal-Loop/SKILL.md',
    ]
    for sample in illegal:
        assert CROSS_SKILL_LINK.search(sample), f"漏检: {sample}"
    command_examples = [
        "bash skills/taste-driven-designer/scripts/generate-seed.sh -l 64",
        "python3 skills/doc-governance/scripts/check-doc-links.py --root docs",
    ]
    for sample in command_examples:
        assert is_command_example(sample), f"命令行示例未被识别（会误报）: {sample}"
    legal = [
        "[critic-loop-protocol.md](references/critic-loop-protocol.md)",
        "`frontend-qa-gate` 技能",
        "[discover-phase.md](references/discover-phase.md)",
    ]
    for sample in legal:
        assert not CROSS_SKILL_LINK.search(sample), f"误伤: {sample}"
