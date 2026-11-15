"""test_optional_skill_contract.py — goal-loop 外部技能依赖处置的条文契约自检。

把「缺失可选技能时的探测与三分支处置」固化为断言，防止条文被后续改动静默简化
（本协议是行为规则，无运行时实现，故只能校验文本契约本身）。

覆盖:
  1. 依赖清单四行（阶段 × 技能 × 来源）在场;
  2. 探测段给出可执行的目录探测命令，并约定「不逐阶段重复」的频次;
  3. 三分支 A/B/C 在场，且「交互不可用不得提问」为显式条款（子代理提问会被宿主拒绝）;
  4. 安装命令为可复制的 npx 形态，并绑定已验证的 superpowers / mattpocock 来源;
  5. 内联最小规程覆盖全部四项依赖，替身模板真实可达（单装后不断链）;
  6. 路由层 SKILL.md 指向本文，且与细则层口径一致（不漂移）。
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
PROTOCOL = SKILL_DIR / "references" / "optional-skill-dependencies.md"
SKILL_MD = SKILL_DIR / "SKILL.md"


def _protocol():
    return PROTOCOL.read_text(encoding="utf-8")


def test_dependency_table_covers_four_phases():
    body = _protocol()
    for phase in ("P-1", "P0", "P0.5", "P1"):
        assert f"**{phase}**" in body, f"依赖清单缺少阶段: {phase}"
    for skill in ("brainstorming", "grilling", "research", "writing-plans"):
        assert f"`{skill}`" in body, f"依赖清单缺少技能: {skill}"
    for repo in ("obra/superpowers", "mattpocock/skills"):
        assert repo in body, f"依赖清单缺少来源仓库: {repo}"


def test_probe_is_executable_and_one_shot():
    body = _protocol()
    assert 'test -d "$d/$s"' in body, "缺少可执行的目录探测命令"
    assert ".agents/skills" in body, "缺少宿主默认技能目录"
    assert "不逐阶段重复" in body, "必须约定探测频次，避免每阶段反复探测"


def test_three_branches_and_no_blocking_branch():
    body = _protocol()
    for branch in ("**A 交互可用**", "**B 交互不可用**", "**C 安装失败**"):
        assert branch in body, f"缺少处置分支: {branch}"
    assert "不提问" in body, "分支 B 必须显式禁止提问，否则无头派发场景停摆"
    assert "ask_user_question" in body, "分支 A 须点名宿主提问原语"


def test_install_commands_are_copyable():
    body = _protocol()
    assert body.count("npx --yes skills@latest add -y") >= 2, "两份来源各需一条可复制命令"
    assert "skills_manager.py install -f superpowers" in body, "缺少本仓库整组安装入口"


def test_inline_fallbacks_cover_all_dependencies():
    body = _protocol()
    section = body.split("## 4.")[1].split("## 5.")[0]
    for skill in ("brainstorming", "grilling", "research", "writing-plans"):
        assert f"替代 `{skill}`" in section, f"内联规程缺少替代项: {skill}"
    assert (SKILL_DIR / "templates" / "goal-plan-template.md").is_file(), \
        "writing-plans 的替身模板不存在（单装后会断链）"


def test_iron_rules_and_no_false_claim():
    body = _protocol()
    assert "不得伪称已激活" in body, "缺少反伪造条款"
    assert "Active Checkpoint" in body, "降级必须落到计划检查点"
    assert "缺失不是跳过门禁的理由" in body, "缺失不得成为跳过门禁的借口"


def test_routing_layer_points_to_protocol():
    skill = SKILL_MD.read_text(encoding="utf-8")
    assert "references/optional-skill-dependencies.md" in skill, "SKILL.md 未指向依赖处置细则"
    assert "不得阻塞" in skill and "不得伪称已激活" in skill, "路由层与细则层口径不一致"
