"""check-review-report.sh 契约测试：校验《审查归档》结构门禁的判定语义。

覆盖 RFC-0001 §3.5 的 7 项校验规则，每项各配失败与通过用例。
"""
import hashlib
import re
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check-review-report.sh'

R1_BODY = """# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析
- **改动性质定性**: 本质根因修复

## 2. 运行时与 SSR/沙盒安全推演（条件维度）
未激活（非客户端/SSR 改动）

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)
- **攻击路径 1: 状态覆写**: 触发条件 -> 复现推演 -> 影响结果 -> 涉及代码 `src/a.ts:1`

## 4. 潜在缺陷清单 (Identified Defect Candidates)
| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | P1 (Blocker) | 是 | `src/a.ts:1` | 未处理的竞态覆盖 | 快速二次请求覆写进行中状态 |
| R1-2 | P2 (Suggestion) | 历史既有 | `src/b.ts:9` | 重复校验未提取 | 历史遗留，本次未改动 |

## 5. 第一轮结论概要
存在 1 项阻断候选，移交第二轮架构师元审判。
"""

R2_BODY = """# 第二轮元对抗审查与终审裁决书 (Round 2 Meta-Architect Verdict)

## 1. 元审查辩证质询 (Meta-Challenges on Round 1)
- **R1 攻击可信度整体评估**: 高度中肯
- **Diff 边界合规性核查**: 无历史越界

## 2. 最终裁决明细表 (Final Verdict Synthesis Table)
| 稳定 ID (沿用 R1) | 检查点 / 文件位置 | 原始 R1 评级 | 变更归属 (本次引入/历史既有) | 终审裁决 | 最终定性分析与裁决理由 | 处置要求 |
|:---|:---|:---:|:---:|:---:|:---|:---|
| R1-1 | `src/a.ts:1` | P1 | 本次引入 | 🔴 **P1 阻断项** | 坐实竞态风险，必须修复 | 必须修复，打回重测 |
| R1-2 | `src/b.ts:9` | P2 | 历史既有 | 🟡 **P2 优化建议** | 历史技术债，非本次引入 | 记入待办，准予放行 |

## 3. 终审放行结论
- **阻断项统计**: 🔴 1 个
- **优化建议统计**: 🟡 1 个
- **驳回误报统计**: ⚪ 0 个
- **交付判定**: 🔴 阻断交付
"""

INDEX_TMPL = """# 审查归档 · 示例交付

- **交付单元**: sample-delivery
- **归档根**: docs/project/reviews/2026-10-04-sample-delivery/
- **审查模式**: {mode}
- **当前迭代计数**: 1/3
- **终审裁决**: {verdict}

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 |
| :--- | :--- | :--- | :--- | :--- | :--- |
{rows}

## 待办与后续轮次
- [ ] 无
"""


def _sha12(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def _build(tmp_path, *, mode='full', verdict='✅ 准予交付', with_r2=True,
           r1_body=R1_BODY, r2_body=R2_BODY, r1_sha=None, r2_sha=None,
           tamper_after_index=False, index_override=None, drop_file=False):
    """构造一个归档目录；返回 (目录, r1 文件, r2 文件或 None)。"""
    d = tmp_path / 'archive'
    d.mkdir()
    r1_name = 'r1-940e0f3..a1b2c3d.md'
    r2_name = 'r2-940e0f3..a1b2c3d.md'
    (d / r1_name).write_text(r1_body, encoding='utf-8')
    rows = ['| R1 | `940e0f3..a1b2c3d` | sub-1 | `%s` | `%s` | 🔴 1 / 🟡 1 / ⚪ 0 |'
            % (r1_name, r1_sha if r1_sha is not None else _sha12(r1_body))]
    r2_file = None
    if with_r2:
        r2_file = d / r2_name
        r2_file.write_text(r2_body, encoding='utf-8')
        rows.append('| R2 | `940e0f3..a1b2c3d` | sub-2 | `%s` | `%s` | %s |'
                    % (r2_name, r2_sha if r2_sha is not None else _sha12(r2_body), verdict))
    index = index_override if index_override is not None else INDEX_TMPL.format(
        mode=mode, verdict=verdict, rows='\n'.join(rows))
    (d / 'README.md').write_text(index, encoding='utf-8')
    if drop_file:
        (d / r1_name).unlink()
    if tamper_after_index:
        # 索引登记后篡改报告内容，制造指纹漂移
        (d / r1_name).write_text(r1_body + '\n追加篡改行\n', encoding='utf-8')
    return d, d / r1_name, r2_file


def _run(target, *args):
    return subprocess.run(['bash', str(SCRIPT), str(target), *args],
                          capture_output=True, text=True)


def test_help_exits_zero(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '用法' in r.stdout


def test_usage_error_when_no_args():
    r = subprocess.run(['bash', str(SCRIPT)], capture_output=True, text=True)
    assert r.returncode == 2
    assert 'usage' in r.stderr.lower() or '用法' in r.stderr


def test_usage_error_when_dir_missing(tmp_path):
    r = subprocess.run(['bash', str(SCRIPT), str(tmp_path / 'nope')],
                       capture_output=True, text=True)
    assert r.returncode == 2


def test_usage_error_when_arg_is_file(tmp_path):
    f = tmp_path / 'a.md'
    f.write_text('x', encoding='utf-8')
    assert _run(f).returncode == 2


def test_invalid_require_verdict_value(tmp_path):
    d, _, _ = _build(tmp_path)
    assert _run(d, '--require-verdict=FAIL').returncode == 2


def test_valid_full_archive_passes(tmp_path):
    d, _, _ = _build(tmp_path)
    r = _run(d)
    assert r.returncode == 0, r.stdout + r.stderr
    assert '通过' in r.stdout


def test_missing_index_fails(tmp_path):
    d, _, _ = _build(tmp_path)
    (d / 'README.md').unlink()
    r = _run(d)
    assert r.returncode == 1
    assert 'README' in r.stdout


def test_missing_index_field_fails(tmp_path):
    d, _, _ = _build(tmp_path, index_override='# 审查归档\n\n- **交付单元**: x\n')
    r = _run(d)
    assert r.returncode == 1
    assert '归档根' in r.stdout or '终审裁决' in r.stdout


def test_missing_report_file_fails(tmp_path):
    d, _, _ = _build(tmp_path, drop_file=True)
    r = _run(d)
    assert r.returncode == 1
    assert '不存在' in r.stdout


def test_empty_report_file_fails(tmp_path):
    d, r1, _ = _build(tmp_path)
    r1.write_text('', encoding='utf-8')
    r = _run(d)
    assert r.returncode == 1


def test_hash_mismatch_fails(tmp_path):
    d, _, _ = _build(tmp_path, tamper_after_index=True)
    r = _run(d)
    assert r.returncode == 1
    assert 'SHA256' in r.stdout or '指纹' in r.stdout


def test_wrong_declared_hash_fails(tmp_path):
    d, _, _ = _build(tmp_path, r1_sha='deadbeef0000')
    assert _run(d).returncode == 1


def test_r1_missing_section_fails(tmp_path):
    body = R1_BODY.replace('## 5. 第一轮结论概要', '## 五、结论')
    d, _, _ = _build(tmp_path, r1_body=body)
    r = _run(d)
    assert r.returncode == 1
    assert '第一轮结论概要' in r.stdout


def test_r1_section_only_inside_fence_fails(tmp_path):
    body = R1_BODY.replace(
        '## 4. 潜在缺陷清单 (Identified Defect Candidates)',
        '```text\n## 4. 潜在缺陷清单 (Identified Defect Candidates)\n| R1-1 | P1 | 是 | a.ts:1 | x | y |\n```')
    d, _, _ = _build(tmp_path, r1_body=body)
    r = _run(d)
    assert r.returncode == 1
    assert '围栏' in r.stdout


def test_unclosed_fence_fails(tmp_path):
    body = R1_BODY + '\n```text\n未闭合\n'
    d, _, _ = _build(tmp_path, r1_body=body)
    r = _run(d)
    assert r.returncode == 1
    assert '围栏' in r.stdout


def test_r2_missing_section_fails(tmp_path):
    body = R2_BODY.replace('## 3. 终审放行结论', '## 三、结论')
    d, _, _ = _build(tmp_path, r2_body=body)
    r = _run(d)
    assert r.returncode == 1
    assert '终审放行结论' in r.stdout


def test_stable_id_mismatch_fails(tmp_path):
    body = R2_BODY.replace('| R1-2 | `src/b.ts:9`', '| R1-99 | `src/b.ts:9`')
    d, _, _ = _build(tmp_path, r2_body=body)
    r = _run(d)
    assert r.returncode == 1
    assert 'R1-99' in r.stdout


def test_light_mode_without_r2_passes(tmp_path):
    d, _, _ = _build(tmp_path, mode='light', with_r2=False, verdict='未定')
    assert _run(d).returncode == 0


def test_require_verdict_pass_ok(tmp_path):
    d, _, _ = _build(tmp_path)
    r = _run(d, '--require-verdict=PASS')
    assert r.returncode == 0, r.stdout + r.stderr


def test_require_verdict_pass_fails_when_blocked(tmp_path):
    d, _, _ = _build(tmp_path, verdict='🔴 阻断交付')
    r = _run(d, '--require-verdict=PASS')
    assert r.returncode == 1


def test_require_verdict_pass_fails_when_undecided(tmp_path):
    d, _, _ = _build(tmp_path, verdict='未定')
    r = _run(d, '--require-verdict=PASS')
    assert r.returncode == 1


SKILL_DIR = Path(__file__).resolve().parents[1]
_TEMPLATES = {
    'r1': SKILL_DIR / 'references' / 'round-1-red-team.md',
    'r2': SKILL_DIR / 'references' / 'round-2-meta-architect.md',
}


def _checker_sections():
    text = SCRIPT.read_text(encoding='utf-8')
    r1 = text.split('R1_SECTIONS=(')[1].split(')')[0]
    r2 = text.split('R2_SECTIONS=(')[1].split(')')[0]
    return (re.findall(r'"(## \d+\.[^"]*)"', r1),
            re.findall(r'"(## \d+\.[^"]*)"', r2))


def _template_headings(path):
    body = path.read_text(encoding='utf-8').split('## Output Format')[-1]
    return re.findall(r'^## \d+\. .+$', body, re.M)


def test_template_headings_match_checker_constants():
    """提示词模板的输出区块标题必须以门禁必需常量为前缀——防止两处独立漂移。

    门禁用 grep -F（前缀子串）匹配，故模板标题允许携带英文副标题，但不得改名。
    """
    r1_secs, r2_secs = _checker_sections()
    assert r1_secs and r2_secs, '未能从门禁脚本解析出必需区块常量'
    for h in _template_headings(_TEMPLATES['r1']):
        assert any(h.startswith(s) for s in r1_secs), 'R1 模板标题与门禁常量不匹配: ' + h
    for h in _template_headings(_TEMPLATES['r2']):
        assert any(h.startswith(s) for s in r2_secs), 'R2 模板标题与门禁常量不匹配: ' + h


def test_ledger_rows_outside_section_ignored(tmp_path):
    """台账区块外的同名表格行不得被当作登记项（防误解析）。"""
    d, _, _ = _build(tmp_path)
    index = (d / 'README.md').read_text(encoding='utf-8')
    index += ('\n## 其他表格\n| R1 | `x..y` | sub-9 | `ghost.md` | `deadbeef0000` | 🔴 0 |\n')
    (d / 'README.md').write_text(index, encoding='utf-8')
    r = _run(d)
    # 台账区块内的登记项合法；区块外的 ghost.md 不得触发「文件不存在」
    assert r.returncode == 0, r.stdout
