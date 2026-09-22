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
6. 独立分发纪律：不得写跨技能相对路径硬链接（正则自检覆盖相对与绝对形态）；
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

SCORE_WORDS = re.compile(r"评分|打分|分数|得分|分值|满分|分级|等级|百分比|通过率|[0-9]+\s*分(?!钟)")
GATE_WORDS = re.compile(r"完成|放行|通过|达标|准入|交付|上线|发版|发布|合并|验收判据")
PROHIBITION_WORDS = re.compile(r"不得|禁止|不输出|不许|不含|不涉及|不参与|不作为|不构成|不以|不设|不采用|不提供|不用于|不计算|仅作|不作|非门禁|非判据|非验收|❌")

# 跨技能相对路径硬链接：覆盖 (../x/)、(./x/)、(x/)、(../../skills/x/) 与绝对路径形态。
# 正则自身由 test_cross_skill_link_scanner_self_check 自检，防止再次出现恒真空断言。
CROSS_SKILL_LINK = re.compile("(?:^|[\\s(=/\"'>、，（])(?:[^)\\s\"'<>]*?[\\\\/])*(?<![\\.])(taste-driven-designer|dual-round-review|goal-loop|frontend-qa-gate|doc-governance|agy-delegation-workflow)[\\\\/]", re.IGNORECASE)
FIVE_DIMENSIONS = ["响应式", "状态", "无障碍", "浏览器", "性能"]


def read(path):
    return path.read_text(encoding="utf-8")


def skill_docs():
    return sorted(p for p in SKILL_DIR.rglob("*.md") if "__pycache__" not in str(p))


COMMAND_EXAMPLE = re.compile(r"^\s*(?:bash|sh|python3?|npx|pnpm|npm|node)\s")


def is_command_example(line):
    """命令行示例（bash/python3/npx ... skills/<name>/...）不是文档链接，豁免跨技能硬链接扫描。"""
    return bool(COMMAND_EXAMPLE.match(line))


def assert_no_score_gate(text, label):
    for sentence in re.split(r"[。！？；\n]", text):
        if SCORE_WORDS.search(sentence) and GATE_WORDS.search(sentence):
            assert PROHIBITION_WORDS.search(sentence), (
                f"{label} 出现把分数/等级当作完成或放行条件的表述: {sentence.strip()[:120]}"
            )


def run_checker(report, *extra):
    return subprocess.run(["bash", str(CHECKER), str(report), *extra], capture_output=True, text=True)


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


def test_matrix_declared_total_matches_rows():
    """声明总数必须等于实际断言行数（防 28 vs 31 类算术漂移）。"""
    text = read(MATRIX)
    rows = [l for l in text.splitlines() if re.match(r"^\|\s*(?:S|V|A|B|P)\d+\s*\|", l)]
    m = re.search(r"五域共 \*\*(\d+) 条断言\*\*", text)
    assert m, "矩阵必须声明五域断言总数"
    assert int(m.group(1)) == len(rows), f"声明 {m.group(1)} 条，实际 {len(rows)} 条"


def test_matrix_rows_are_structured_assertions():
    """每条断言行必须是四列表格行（编号 | 断言 | 操作步骤 | 证据），防止用散文冒充断言。"""
    rows = [l for l in read(MATRIX).splitlines() if re.match(r"^\|\s*(?:S|V|A|B|P)\d+\s*\|", l)]
    assert len(rows) >= 30, f"断言行不足（实际 {len(rows)}）"
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 4, f"断言行不是四列结构: {row[:80]}"
        assert cells[2] and cells[3], f"断言行缺少操作步骤或证据列: {row[:80]}"


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
            if is_command_example(line):
                continue
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
- [x] A1 375x812 无横向溢出 | 操作: 打开首页滚动到底 | 证据: shots/375.png | 状态: 已运行验证
### 3.2 交互状态断言
- [ ] A2 断网提交显示错误并保留输入 | 操作: DevTools offline 后提交 | 证据: shots/error.png | 状态: 已实现未验证
### 3.3 无障碍断言
- [x] A3 键盘可完成登录 | 操作: 仅 Tab/Enter 走完登录 | 证据: logs/keyboard-run.txt | 状态: 已运行验证
### 3.4 浏览器覆盖断言
- [x] A4 Safari 最低版本填充样式正常 | 操作: 真机核对 | 证据: shots/safari.png | 状态: 已运行验证
### 3.5 性能断言
- [ ] A5 关键交互 P95 未回归 | 操作: 前后各测 20 次 | 证据: 待测量 | 状态: 未验证（宿主无性能测量能力）

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

def test_cross_skill_link_scanner_self_check():
    # 防恒真空断言：正则必须对相对/绝对形态命中，且不得误伤技能内路径。
    illegal = [
        '(../taste-driven-designer/SKILL.md)',
        '(./goal-loop/SKILL.md)',
        '(goal-loop/SKILL.md)',
        '(../../skills/dual-round-review/SKILL.md)',
        '(/abs/skills/goal-loop/SKILL.md)',
        '(..\\goal-loop\\SKILL.md)',
        '../Goal-Loop/SKILL.md',
    ]
    for sample in illegal:
        assert CROSS_SKILL_LINK.search(sample), f'跨技能链接正则漏检: {sample}'
    command_examples = [
        'bash skills/frontend-qa-gate/scripts/check-qa-report.sh report.md',
        'python3 skills/doc-governance/scripts/check-doc-links.py --root docs',
    ]
    for sample in command_examples:
        assert is_command_example(sample), f'命令行示例未被识别（会误报）: {sample}'
    legal = ['(references/acceptance-matrix.md)', '(scripts/check-qa-report.sh)', '(templates/qa-report-template.md)', '.goal-loop/dispatch-ledger.md']
    for sample in legal:
        assert not CROSS_SKILL_LINK.search(sample), f'跨技能链接正则误伤技能内路径: {sample}'


def test_score_gate_scanner_covers_variants():
    # 依据实测：旧词表漏检 3/8 变体，扩词后必须全部命中。
    illegal = [
        '仅当 Critic 评分达到 9 分时才放行。',
        '评分到 9 就放上线。',
        '分数达到门槛方可交付。',
        '综合分为 9 分即可发布。',
        '验收满分才准合并。',
        '得分达到 9 分即可交付。',
        '分级为 A 方能上线。',
        '通过率 90% 以上才可交付。',
        '验收评分包括通过率，达到 9 分即可交付。',
        '该门禁包括评分，分数即放行依据。',
        '交付判据包括评分等级，A 级方可上线。',
        '评分包括门禁判定，满分才准合并。',
    ]
    for sample in illegal:
        try:
            assert_no_score_gate(sample, 'variant-probe')
        except AssertionError:
            continue
        raise AssertionError(f'分数门禁变体漏检: {sample}')
    legal = [
        '评分仅作遥测记录，不作为验收判据，禁止用于放行判定。',
        '分数不参与通过判定。',
        '分数不构成交付判据。',
        '不采用绝对分数作为交付判据。',
        '验收通过率不以分数计算。',
        '五域断言需在 30 分钟内完成。',
        '验收报告应在 10 分钟内完成结构校验。',
    ]
    for sample in legal:
        assert_no_score_gate(sample, 'legal-probe')


def test_checker_fails_when_domain_missing(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT.replace("### 3.3 无障碍断言", "### 3.3 其它断言"), encoding="utf-8")
    r = run_checker(report)
    assert r.returncode != 0, "缺少任一域标题时必须非零退出"
    assert "五域覆盖" in r.stdout + r.stderr


def test_checker_fails_when_section_only_inside_fence(tmp_path):
    report = tmp_path / "qa-report.md"
    poisoned = FULL_REPORT.replace("## 8. 签收", "## 8.5 附录")
    poisoned = poisoned + FENCE + "text\n## 8. 签收\n" + FENCE + "\n"
    report.write_text(poisoned, encoding="utf-8")
    r = run_checker(report)
    assert r.returncode != 0, "必需区块仅存在于围栏内时必须非零退出"
    assert "围栏" in r.stdout + r.stderr


def test_checker_fails_when_blocked_without_unverified_items(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT.replace("- 未验证：A5", "- 未验证：无"), encoding="utf-8")
    r = run_checker(report)
    assert r.returncode != 0, "结论 BLOCKED 却声明无未验证项时必须非零退出"
    assert "未验证" in r.stdout + r.stderr


PASS_REPORT = (
    FULL_REPORT
    .replace(
        "- [ ] A2 断网提交显示错误并保留输入 | 操作: DevTools offline 后提交 | 证据: shots/error.png | 状态: 已实现未验证",
        "- [x] A2 断网提交显示错误并保留输入 | 操作: DevTools offline 后提交 | 证据: shots/error.png | 状态: 已运行验证",
    )
    .replace(
        "- [ ] A5 关键交互 P95 未回归 | 操作: 前后各测 20 次 | 证据: 待测量 | 状态: 未验证（宿主无性能测量能力）",
        "- [x] A5 关键交互 P95 未回归 | 操作: 前后各测 20 次 | 证据: perf/p95.txt | 状态: 已运行验证",
    )
    .replace("| 交互状态 | 1 | 0 | 1 | 0 | FAIL |", "| 交互状态 | 1 | 1 | 0 | 0 | PASS |")
    .replace("| 性能 | 1 | 0 | 0 | 1 | BLOCKED |", "| 性能 | 1 | 1 | 0 | 0 | PASS |")
    .replace("五维合计：断言 5 · 通过 3 · 失败 1 · 未验证 1", "五维合计：断言 5 · 通过 5 · 失败 0 · 未验证 0")
    .replace("- A5 未验证：宿主缺少性能测量能力（能力门控，不视为通过）", "- 无")
    .replace("- 未验证：A5", "- 未验证：无")
    .replace("- 结论：BLOCKED（存在未验证项）", "- 结论：PASS")
)


def test_checker_require_verdict_accepts_pass_report(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "结论 PASS" in r.stdout


def test_checker_require_verdict_rejects_blocked_report(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(FULL_REPORT, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "BLOCKED 报告必须被 --require-verdict=PASS 拒绝"


def test_checker_require_verdict_rejects_fail_report(tmp_path):
    report = tmp_path / "qa-report.md"
    fail_report = FULL_REPORT.replace("- 结论：BLOCKED（存在未验证项）", "- 结论：FAIL")
    report.write_text(fail_report, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "FAIL 报告必须被 --require-verdict=PASS 拒绝"


def test_checker_min_assertions_option(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT, encoding="utf-8")
    ok = run_checker(report, "--min-assertions=5")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    strict = run_checker(report, "--min-assertions=15")
    assert strict.returncode != 0, "低于 --min-assertions 的报告必须失败"
    assert "下限 15" in strict.stdout + strict.stderr


def test_checker_verdict_rejects_pass_with_unverified_section(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 无", "- A5 未验证：宿主无性能测量能力", 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "PASS 报告第 4 章列出未验证项时必须拒绝"


def test_checker_verdict_rejects_lowercase_fail(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 结论：PASS", "- 结论：fail"), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "小写 fail 结论必须被拒绝（大小写归一）"


def test_checker_verdict_requires_signoff_section_not_advice_line(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 结论：PASS", "- 智能体建议结论：PASS"), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "建议结论行不得充当签收区结论声明"


def test_checker_verdict_rejects_pass_with_concrete_unverified_items(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 未验证：无", "- 未验证：A5"), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "第 5 章列出具体未验证项时必须拒绝 PASS"


def test_checker_rejects_min_assertions_zero(tmp_path):
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT, encoding="utf-8")
    r = run_checker(report, "--min-assertions=0")
    assert r.returncode == 2, "--min-assertions=0 必须作为用法错误拒绝"


def test_checker_accepts_sec4_none_variants(tmp_path):
    """FU-1a: 第 4 章以「无」开头的声明变体不得被误判为存在未验证项。"""
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 无", "- 无未验证项", 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode == 0, r.stdout + r.stderr


def test_checker_accepts_sec5_parenthesized_none(tmp_path):
    """FU-1b: 第 5 章「（无）」不得被误判为具体未验证项。"""
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 未验证：无", "- 未验证：（无）"), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode == 0, r.stdout + r.stderr


def test_checker_accepts_na_row_with_justification(tmp_path):
    """FU-3: 某域本轮无适用断言时允许 N/A，但报告必须给出「未适用」说明。"""
    report = tmp_path / "qa-report.md"
    text = PASS_REPORT.replace("| 性能 | 1 | 1 | 0 | 0 | PASS |", "| 性能 | 0 | 0 | 0 | 0 | N/A |")
    text = text.replace("- 无", "- 性能域本轮未适用（无性能敏感改动）", 1)
    report.write_text(text, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode == 0, r.stdout + r.stderr


def test_checker_rejects_na_row_without_justification(tmp_path):
    """FU-3 滥用防护: N/A 行缺少说明时必须拒绝（防止用 N/A 逃避验收）。"""
    report = tmp_path / "qa-report.md"
    text = PASS_REPORT.replace("| 性能 | 1 | 1 | 0 | 0 | PASS |", "| 性能 | 1 | 1 | 0 | 0 | N/A |")
    report.write_text(text, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "N/A 行缺少「未适用」说明时必须拒绝"


def test_checker_rejects_sec4_none_with_trailing_unverified(tmp_path):
    """FU-1 滥用防护: 以「无」开头但追加真实未验证项时必须拒绝。"""
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 无", "- 无阻断，但性能未验证", 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "「无阻断，但…未验证」式夹带必须拒绝"


def test_checker_rejects_na_smuggling_unverified(tmp_path):
    """FU-1/FU-3 滥用防护: 借「未适用」夹带未验证项时必须拒绝。"""
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 无", "- 性能未适用，但错误态未验证", 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "借「未适用」夹带未验证项必须拒绝"


def test_checker_rejects_na_row_with_assertions(tmp_path):
    """FU-3 滥用防护: N/A 域的断言数必须为 0。"""
    report = tmp_path / "qa-report.md"
    text = PASS_REPORT.replace("| 性能 | 1 | 1 | 0 | 0 | PASS |", "| 性能 | 1 | 1 | 0 | 0 | N/A |")
    text = text.replace("- 无", "- 性能域本轮未适用", 1)
    report.write_text(text, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "N/A 域仍声明断言时必须拒绝"


def test_checker_accepts_parallel_negation(tmp_path):
    """D1: 第 4 章合法并列否定（顿号/逗号）不得被误拒。"""
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 无", "- 无未验证项、无阻断项", 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode == 0, r.stdout + r.stderr


def test_checker_rejects_table_smuggle_in_sec4(tmp_path):
    """D2: 第 4 章用表格承载未验证项时必须拒绝。"""
    report = tmp_path / "qa-report.md"
    table = "| 项 | 原因 |\n|---|---|\n| A5 | 未验证：宿主无性能测量能力 |"
    report.write_text(PASS_REPORT.replace("- 无", table, 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "表格承载未验证项必须拒绝"


def test_checker_rejects_parenthesized_smuggle(tmp_path):
    """D3: 括号内夹带未验证语义时必须拒绝。"""
    report = tmp_path / "qa-report.md"
    report.write_text(PASS_REPORT.replace("- 无", "- 无未验证项（性能域未测）", 1), encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "括号夹带必须拒绝"


def test_checker_rejects_na_row_with_pass_fail_counts(tmp_path):
    """D4: N/A 行的通过/失败列必须为 0。"""
    report = tmp_path / "qa-report.md"
    text = PASS_REPORT.replace("| 性能 | 1 | 1 | 0 | 0 | PASS |", "| 性能 | 0 | 5 | 5 | 0 | N/A |")
    text = text.replace("- 无", "- 性能域本轮未适用", 1)
    report.write_text(text, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "N/A 行通过/失败列非 0 时必须拒绝"


def test_checker_rejects_na_justification_outside_sec45(tmp_path):
    """D5: N/A 说明必须出现在第 4/5 章，不得在其它章节充数。"""
    report = tmp_path / "qa-report.md"
    text = PASS_REPORT.replace("| 性能 | 1 | 1 | 0 | 0 | PASS |", "| 性能 | 0 | 0 | 0 | 0 | N/A |")
    text = text.replace("### 3.5 性能断言", "### 3.5 性能断言（本轮未适用）", 1)
    report.write_text(text, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "N/A 说明仅出现在第 3 章时必须拒绝"


def test_checker_rejects_unclosed_fence(tmp_path):
    """D6-1: 围栏未闭合必须 fail-closed 报错，而非静默跳过其后内容。"""
    report = tmp_path / "qa-report.md"
    text = PASS_REPORT.replace("- 结论：PASS", "- 结论：PASS\n```text\n未闭合围栏", 1)
    report.write_text(text, encoding="utf-8")
    r = run_checker(report, "--require-verdict=PASS")
    assert r.returncode != 0, "围栏未闭合必须拒绝"
    assert "未闭合" in r.stdout + r.stderr
