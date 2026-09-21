"""test_qa_gate_contract.py — frontend-qa-gate 边界契约的静态回归测试。

背景：本技能的存在价值是补齐「产物级验收」空白，因此它的**边界**比它的**清单**更重要。
一旦边界被侵蚀（引入绝对分数判据、替代人类签收、侵入代码级审查），技能就会退化为
dual-round-review 的重复品或第二个不可靠的评分门禁（taste V1.1 反证 E1/E2/E3 已证伪）。

契约要点：
1. 不得把任何绝对分数/等级/百分比当作验收判据（句子级扫描，防措辞规避）；
2. 放行权必须归人类（Gate C 语义），技能不得自签；
3. 不得进行代码级审查：代码级判据必须显式路由到 dual-round-review；
4. 五大断言维度（响应式视口/交互状态/无障碍/浏览器覆盖/性能）必须在位；
5. 回流路由四类齐备，命令顺序固定为 taste -> qa-gate -> dual-round-review；
6. 独立分发纪律：不得写跨技能相对路径硬链接；
7. 报告结构校验脚本行为正确。
"""

import re
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
MATRIX = SKILL_DIR / "references" / "acceptance-matrix.md"
ROUTING = SKILL_DIR / "references" / "regression-routing.md"
TEMPLATE = SKILL_DIR / "templates" / "qa-report-template.md"
CHECKER = SKILL_DIR / "scripts" / "check-qa-report.sh"

FENCE = "```"

SCORE_WORDS = re.compile(r"评分|分数|得分|分值|等级|百分比|通过率")
GATE_WORDS = re.compile(r"完成|放行|通过|达标|准入|交付|上线|发版|发布|合并|验收判据")
PROHIBITION_WORDS = re.compile(r"不得|禁止|不输出|不许|不含|不涉及|不参与|不作为|不构成|仅作|不作|非门禁|❌")

# 边界声明：本扫描是启发式护栏（句子级词表共现），不是语义证明；配套正向锚点与自检用例。
CROSS_SKILL_LINK = re.compile(
    r"\]\((?:\\.\\./)*\\.{0,2}/?(?:taste-driven-designer|dual-round-review|goal-loop)/"
)
FIVE_DIMENSIONS = ["响应式", "状态", "无障碍", "浏览器", "性能"]


def read(path):
    return path.read_text(encoding="utf-8")


def skill_docs():
    return sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in str(p))


def assert_no_score_gate(text, label):
    for sentence in re.split(r"[。！？；\n]", text):
        if SCORE_WORDS.search(sentence) and GATE_WORDS.search(sentence):
            assert PROHIBITION_WORDS.search(sentence), (
                f"{label} 出现把分数/等级当作完成或放行条件的表述: {sentence.strip()[:120]}"
            )


def run_checker(report):
    return subprocess.run(["bash", str(CHECKER), str(report)], capture_output=True, text=True)


def test_no_score_gate_in_any_skill_doc():
    docs = skill_docs()
    assert docs, "技能目录下必须存在技能文档"
    for path in docs:
        assert_no_score_gate(read(path), path.name)


def test_score_gate_scanner_self_check():
    legal = "评分仅作遥测记录，不作为验收判据，禁止用于放行判定。"
    illegal = "当验收评分为 9 分以上时，方可放行交付。"
    assert_no_score_gate(legal, "self-check-legal")
    try:
        assert_no_score_gate(illegal, "self-check-illegal")
    except AssertionError:
        pass
    else:
        raise AssertionError("扫描器未能拦截违规的分数门禁表述")


def test_human_signoff_authority_is_pinned():
    text = read(SKILL_MD)
    assert "人类" in text and "签收" in text, "SKILL.md 必须声明人工签收权"
    assert re.search(r"(放行|签收)[^。]{0,20}(人类|用户)|(人类|用户)[^。]{0,20}(签收|放行)", text), (
        "SKILL.md 必须显式声明放行权归人类/用户"
    )


def test_gate_c_semantics_referenced_not_redefined():
    assert "Gate C" in read(MATRIX), "验收基线必须声明与 taste Gate C（人类签收）的边界"


def test_code_level_review_is_routed_out():
    assert "dual-round-review" in read(SKILL_MD), "SKILL.md 必须把代码级审查路由到 dual-round-review"
    boundaries = read(MATRIX)
    assert "不在本技能" in boundaries or "不重复" in boundaries, "验收基线必须声明代码级判据不在本技能范围"
    assert "模式" in read(ROUTING), "回流路由必须按失败模式编号引用 dual-round-review 的模式库"


def test_skill_does_not_claim_code_static_analysis():
    forbidden = re.compile(r"本技能(?:负责|执行|包含)[^。]{0,12}(?:代码审查|静态分析|lint|类型检查)")
    assert not forbidden.search(read(SKILL_MD)), "SKILL.md 不得声称本技能执行代码级静态审查"


def test_five_assertion_dimensions_present():
    text = read(MATRIX)
    for dim in FIVE_DIMENSIONS:
        assert dim in text, f"acceptance-matrix.md 缺少断言维度: {dim}"


def test_matrix_has_observable_assertions_not_adjectives():
    text = read(MATRIX)
    assert text.count("断言") >= 10, "验收矩阵必须以可判定断言为主体"
    assert "证据" in text, "验收矩阵必须要求证据"


def test_regression_routing_covers_four_classes():
    text = read(ROUTING)
    for marker in ["行为修复", "结构", "根因", "方向"]:
        assert marker in text, f"回流路由表缺少缺陷类别: {marker}"
    assert "D2" in text, "回流路由必须写明结构类缺陷回到 taste D2"
    assert "人类" in text, "回流路由必须写明方向级争议升级人类裁决"


def test_pipeline_order_is_taste_then_gate_then_review():
    text = read(TEMPLATE)
    order = [text.find("taste-driven-designer"), text.find("frontend-qa-gate"), text.find("dual-round-review")]
    assert all(i >= 0 for i in order), "报告模板必须包含全流程命令顺序三元组"
    assert order == sorted(order), "顺序必须是 taste-driven-designer -> frontend-qa-gate -> dual-round-review"


def test_no_cross_skill_relative_links():
    offenders = []
    for path in skill_docs():
        for line in read(path).splitlines():
            if CROSS_SKILL_LINK.search(line):
                offenders.append(path.name + ": " + line.strip()[:80])
    assert not offenders, "禁止跨技能相对路径硬链接（独立分发会断链）: " + "; ".join(offenders)


FULL_REPORT = """# 前端验收报告 · Example

## 1. 验收范围
| 项 | 内容 |
|---|---|
| 产物 | http://localhost:3000 |
| 基线 | taste D3 出口 |

## 2. 断言结论表
| 维度 | 断言数 | 通过 | 失败 | 未验证 | 结论 |
|---|---|---|---|---|---|
| 响应式视口 | 1 | 1 | 0 | 0 | PASS |
| 交互状态 | 1 | 0 | 1 | 0 | FAIL |
| 无障碍 | 1 | 1 | 0 | 0 | PASS |
| 浏览器覆盖 | 1 | 1 | 0 | 0 | PASS |
| 性能 | 1 | 0 | 0 | 1 | BLOCKED |

五维合计：断言 5 · 通过 3 · 失败 1 · 未验证 1

## 3. 五维断言明细
### 3.1 响应式视口断言
- [x] A1 375x812 无横向溢出 | 操作: 打开首页滚动到底 | 证据: shots/375.png
### 3.2 交互状态断言
- [ ] A2 断网提交显示错误并保留输入 | 操作: DevTools offline 后提交 | 证据: shots/error.png
### 3.3 无障碍断言
- [x] A3 键盘可完成登录 | 操作: 仅 Tab/Enter 走完登录 | 证据: logs/keyboard-run.txt
### 3.4 浏览器覆盖断言
- [x] A4 Safari 最低版本填充样式正常 | 操作: 真机核对 | 证据: shots/safari.png
### 3.5 性能断言
- [ ] A5 关键交互 P95 未回归 | 操作: 前后各测 20 次 | 证据: 待测量

## 4. 未验证项与阻断原因
- A5 未验证：宿主缺少性能测量能力（能力门控，不视为通过）

## 5. 证据三态标注
- 已实现：A1 A3 A4
- 已运行验证：A1 A2(失败复现) A3 A4
- 未验证：A5

## 6. 回流路由
| 缺陷 | 类型 | 修复位置 | 回流目标 |
|---|---|---|---|
| A2 错误态未实现 | 行为修复 | 就地修正 | 重跑断言 |

## 7. 全流程命令顺序
```text
taste-driven-designer D1-D3 -> frontend-qa-gate -> dual-round-review
```

## 8. 签收
- 结论：BLOCKED（存在未验证项）
- 放行权：人类（用户）
"""


def test_checker_passes_on_well_formed_report(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT, encoding="utf-8")
    r = run_checker(report)
    assert r.returncode == 0, r.stdout + r.stderr


def test_checker_fails_when_required_section_missing(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT.replace("## 4. 未验证项与阻断原因", "## 4. 其它"), encoding="utf-8")
    r = run_checker(report)
    assert r.returncode != 0, "缺少必需区块时必须非零退出"
    assert "未验证项" in r.stdout + r.stderr


def test_checker_fails_when_tri_state_incomplete(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT.replace("## 5. 证据三态标注", "## 5. 备注"), encoding="utf-8")
    r = run_checker(report)
    assert r.returncode != 0, "缺少证据三态标注时必须非零退出"


def test_checker_fails_on_missing_file():
    r = subprocess.run(["bash", str(CHECKER), "/nonexistent/qa-report.md"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "不存在" in r.stdout + r.stderr or "usage" in (r.stdout + r.stderr).lower()


def test_checker_fails_when_counts_mismatch(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT.replace("断言 5", "断言 99"), encoding="utf-8")
    r = run_checker(report)
    assert r.returncode != 0, "断言行数与五维合计不一致时必须非零退出"
    assert "合计" in r.stdout + r.stderr


def test_checker_ignores_tri_states_inside_code_fence(tmp_path):
    report = tmp_path / "qa-report.md"
    appendix = "## 7.5 附录\n" + FENCE + "text\n已实现：仅示例文本\n已运行验证：仅示例文本\n未验证：仅示例文本\n" + FENCE
    report.write_text(FULL_REPORT.replace("## 8. 签收", appendix + "\n\n## 8. 签收"), encoding="utf-8")
    r = run_checker(report)
    assert r.returncode == 0, "围栏代码块内的示例文本不得被当作真实三态记录"