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
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{rows}

## 待办与后续轮次
- [ ] 无
"""


def _sha12(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def _row(rank, fname, sha, conclusion, write_mode='direct'):
    """构造台账数据行；write_mode=None 表示该行**不登记**「写入形态」列（RFC-0002 缺列场景）。"""
    cells = [rank, '`940e0f3..a1b2c3d`', 'sub-%s' % rank, '`%s`' % fname,
             '`%s`' % sha, conclusion]
    if write_mode is not None:
        cells.append(write_mode)
    return '| ' + ' | '.join(cells) + ' |'


def _build(tmp_path, *, mode='full', verdict='✅ 准予交付', with_r2=True,
           r1_body=R1_BODY, r2_body=R2_BODY, r1_sha=None, r2_sha=None,
           tamper_after_index=False, index_override=None, drop_file=False,
           r1_mode='direct', r2_mode='direct'):
    """构造一个归档目录；返回 (目录, r1 文件, r2 文件或 None)。"""
    d = tmp_path / 'archive'
    d.mkdir()
    r1_name = 'r1-940e0f3..a1b2c3d.md'
    r2_name = 'r2-940e0f3..a1b2c3d.md'
    (d / r1_name).write_text(r1_body, encoding='utf-8')
    rows = [_row('R1', r1_name, r1_sha if r1_sha is not None else _sha12(r1_body),
                 '🔴 1 / 🟡 1 / ⚪ 0', r1_mode)]
    r2_file = None
    if with_r2:
        r2_file = d / r2_name
        r2_file.write_text(r2_body, encoding='utf-8')
        rows.append(_row('R2', r2_name, r2_sha if r2_sha is not None else _sha12(r2_body),
                         verdict, r2_mode))
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


# --- R1-1 回归：终审裁决必须为精确字段值（禁止子串包含判定） -------------------

def test_sections_mentioned_inline_do_not_count(tmp_path):
    """区块标题必须位于行首；散文内提及不构成结构齐备（R1-4 回归）。"""
    body = ('本报告覆盖 ## 1. 第一性原理与本质溯源分析、## 2. 运行时与 SSR/沙盒安全推演、'
            '## 3. 红队攻击路径推演、## 4. 潜在缺陷清单 与 ## 5. 第一轮结论概要 五大区块（内容从略）。\n')
    d, _, _ = _build(tmp_path, r1_body=body)
    assert _run(d).returncode == 1


def test_r2_sections_mentioned_inline_do_not_count(tmp_path):
    """R2 区块标题必须位于行首；散文内提及不构成结构齐备（R1-4 回归）。"""
    r2 = '本报告覆盖 ## 1. 元审查辩证质询、## 2. 最终裁决明细表 与 ## 3. 终审放行结论（内容从略）。\n'
    d, _, _ = _build(tmp_path, r2_body=r2)
    r = _run(d)
    assert r.returncode == 1, r.stdout
    assert '元审查辩证质询' in r.stdout


def test_tilde_fence_is_stripped(tmp_path):
    """波浪号围栏同样应被剥离，置于其中的区块不算齐备（R1-4 回归）。"""
    body = R1_BODY.replace(
        '## 4. 潜在缺陷清单 (Identified Defect Candidates)',
        '~~~text\n## 4. 潜在缺陷清单 (Identified Defect Candidates)\n~~~')
    d, _, _ = _build(tmp_path, r1_body=body)
    r = _run(d)
    assert r.returncode == 1
    assert '围栏' in r.stdout


def test_ids_inside_fence_do_not_legitimize(tmp_path):
    """R1 中仅存在于围栏内的 ID 不得合法化 R2 裁决表中的同 ID（R1-4 回归）。"""
    r1 = R1_BODY.replace(
        '| R1-2 | P2 (Suggestion) | 历史既有 | `src/b.ts:9` | 重复校验未提取 | 历史遗留，本次未改动 |',
        '~~~text\n| R1-9 | P1 | 是 | src/c.ts:1 | 伪造 | 伪造 |\n~~~')
    r2 = R2_BODY.replace('| R1-2 | `src/b.ts:9`', '| R1-9 | `src/c.ts:1`')
    d, _, _ = _build(tmp_path, r1_body=r1, r2_body=r2)
    r = _run(d)
    assert r.returncode == 1
    assert 'R1-9' in r.stdout


def test_require_verdict_fails_on_placeholder_string(tmp_path):
    """RFC §3.4 官方占位符串（含 PASS 词元）不得被判为放行。"""
    d, _, _ = _build(tmp_path, verdict='[🔴 阻断交付 | ✅ 准予交付 | 未定]')
    r = _run(d, '--require-verdict=PASS')
    assert r.returncode == 1, r.stdout
    assert '准予交付' in r.stdout


def test_require_verdict_fails_on_negated_string(tmp_path):
    """否定式裁决串（含 PASS 词元但语义为阻断）不得被判为放行。"""
    d, _, _ = _build(tmp_path, verdict='🔴 阻断交付（未达「准予交付」标准）')
    assert _run(d, '--require-verdict=PASS').returncode == 1


def test_require_verdict_fails_on_substring_value(tmp_path):
    """字段值必须精确，含 PASS 词元的子串不成立。"""
    d, _, _ = _build(tmp_path, verdict='建议准予交付（待人类签收）')
    assert _run(d, '--require-verdict=PASS').returncode == 1


def test_require_verdict_ok_on_bare_value(tmp_path):
    """裸值「准予交付」应被接受。"""
    d, _, _ = _build(tmp_path, verdict='准予交付')
    r = _run(d, '--require-verdict=PASS')
    assert r.returncode == 0, r.stdout


# --- RFC-0002 第 8 项：写入形态合法性 ------------------------------------------


def test_direct_write_mode_passes(tmp_path):
    """子智能体直写通道登记 direct，必须通过。"""
    d, _, _ = _build(tmp_path, r1_mode='direct', r2_mode='direct')
    assert _run(d).returncode == 0


def test_transcribed_write_mode_passes(tmp_path):
    """转录降级通道登记 transcribed，必须通过（合法通道之一）。"""
    d, _, _ = _build(tmp_path, r1_mode='transcribed', r2_mode='transcribed')
    assert _run(d).returncode == 0


def test_missing_write_mode_fails(tmp_path):
    """台账缺「写入形态」列即失败（RFC-0002 §3.5 第 8 项）。"""
    d, _, _ = _build(tmp_path, r1_mode=None)
    r = _run(d)
    assert r.returncode != 0
    assert '写入形态' in r.stdout + r.stderr


def test_invalid_write_mode_fails(tmp_path):
    """写入形态取值非法（第三值）即失败。"""
    d, _, _ = _build(tmp_path, r1_mode='auto')
    r = _run(d)
    assert r.returncode != 0
    assert '写入形态' in r.stdout + r.stderr


def test_usage_documents_write_mode_check(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '写入形态' in r.stdout



LEGACY_INDEX_TMPL = """# 审查归档 · 示例交付

- **交付单元**: sample-delivery
- **归档根**: docs/project/reviews/2026-10-04-sample-delivery/
- **审查模式**: full
- **当前迭代计数**: 1/3
- **终审裁决**: ✅ 准予交付

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 |
| :--- | :--- | :--- | :--- | :--- | :--- |
{rows}

## 待办与后续轮次
- [ ] 无
"""


def test_legacy_six_column_ledger_fails(tmp_path):
    """V2.1.0 六列表头（删掉「写入形态」列）必须判失败。

    门禁不得留「删表头即绕过第 8 项」的后门——历史归档须一次性补列迁移
    （取值 transcribed，因 V2.1.0 只有转录通道），而非让门禁宽容跳过。
    """
    d, r1, r2 = _build(tmp_path)
    legacy_rows = '\n'.join([
        _row('R1', r1.name, _sha12(R1_BODY), '🔴 1 / 🟡 1 / ⚪ 0', None),
        _row('R2', r2.name, _sha12(R2_BODY), '✅ 准予交付', None),
    ])
    (d / 'README.md').write_text(LEGACY_INDEX_TMPL.format(rows=legacy_rows), encoding='utf-8')
    r = _run(d)
    assert r.returncode != 0
    assert '写入形态' in r.stdout + r.stderr

