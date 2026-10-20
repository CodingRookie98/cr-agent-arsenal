"""check-review-report.py 契约测试：校验《审查归档》结构门禁的判定语义。

覆盖 RFC-0001 §3.5 的 7 项校验规则，每项各配失败与通过用例。

跨平台口径：默认调用 Python 实现（`sys.executable`）；POSIX 下旧 `.sh` 兼容壳仍可用，
其行为等价性由 `test_compat_shim_forwards_to_python` 守护。
"""
import ast
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check-review-report.py'
SHIM = SCRIPT.with_suffix('.sh')

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
    (d / r1_name).write_text(r1_body, encoding='utf-8', newline='\n')
    rows = [_row('R1', r1_name, r1_sha if r1_sha is not None else _sha12(r1_body),
                 '🔴 1 / 🟡 1 / ⚪ 0', r1_mode)]
    r2_file = None
    if with_r2:
        r2_file = d / r2_name
        r2_file.write_text(r2_body, encoding='utf-8', newline='\n')
        rows.append(_row('R2', r2_name, r2_sha if r2_sha is not None else _sha12(r2_body),
                         verdict, r2_mode))
    index = index_override if index_override is not None else INDEX_TMPL.format(
        mode=mode, verdict=verdict, rows='\n'.join(rows))
    (d / 'README.md').write_text(index, encoding='utf-8', newline='\n')
    if drop_file:
        (d / r1_name).unlink()
    if tamper_after_index:
        # 索引登记后篡改报告内容，制造指纹漂移
        (d / r1_name).write_text(r1_body + '\n追加篡改行\n', encoding='utf-8', newline='\n')
    return d, d / r1_name, r2_file


def _run(target, *args):
    return subprocess.run([sys.executable, str(SCRIPT), str(target), *args],
                          capture_output=True, text=True, encoding='utf-8')


def test_help_exits_zero(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '用法' in r.stdout


def test_usage_error_when_no_args():
    r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 2
    assert 'usage' in r.stderr.lower() or '用法' in r.stderr


def test_usage_error_when_dir_missing(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / 'nope')],
                       capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 2


def test_usage_error_when_arg_is_file(tmp_path):
    f = tmp_path / 'a.md'
    f.write_text('x', encoding='utf-8', newline='\n')
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
    r1.write_text('', encoding='utf-8', newline='\n')
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


def test_unclosed_fence_message_identifies_report_and_parity(tmp_path):
    """BK-0008：围栏奇偶判定失败须给出可定位诊断（报告标识 + 标记数 + 应为偶数）。"""
    body = R1_BODY + '\n```text\n未闭合\n'
    d, r1_file, _ = _build(tmp_path, r1_body=body)
    r = _run(d)
    assert r.returncode == 1
    line = next((ln for ln in r.stdout.splitlines() if '围栏代码块未闭合' in ln), None)
    assert line is not None, r.stdout
    assert r1_file.name in line, '诊断须指出具体报告文件'
    assert '围栏标记' in line and '应为偶数' in line
    # R1-4 变异可杀：BK-0008 新增的排障提示必须出现，否则本用例对 BASE 实现同样通过（空转）。
    assert '嵌套围栏演示请避免行首标记' in line, line


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
    """从门禁 Python 实现中解析必需区块常量。

    契约迁移：原实现从 `.sh` 的 `R1_SECTIONS=(` 文本切分解析；`.sh` 退役为转发壳后
    改为从 `.py` 读取同名模块级常量。改用 AST 取字面量元组，断言强度不降反升——
    常量必须仍是字面量序列才可解析，字符串拼接/动态构造会直接失败。
    """
    tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ('R1_SECTIONS', 'R2_SECTIONS'):
                found[target.id] = list(ast.literal_eval(node.value))
    return found.get('R1_SECTIONS', []), found.get('R2_SECTIONS', [])


def _template_headings(path):
    body = path.read_text(encoding='utf-8').split('## Output Format')[-1]
    return re.findall(r'^## \d+\. .+$', body, re.M)


def test_template_headings_match_checker_constants():
    """提示词模板的输出区块标题必须以门禁必需常量为前缀——防止两处独立漂移。

    门禁按行首**前缀**匹配（Python 实现为 `line.startswith(section)`，等价于原
    `grep -F` 前缀语义），故模板标题允许携带英文副标题，但不得改名。
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
    (d / 'README.md').write_text(index, encoding='utf-8', newline='\n')
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
    (d / 'README.md').write_text(LEGACY_INDEX_TMPL.format(rows=legacy_rows), encoding='utf-8', newline='\n')
    r = _run(d)
    assert r.returncode != 0
    assert '写入形态' in r.stdout + r.stderr


# --- BK-0003 回归：稳定 ID 方向二必须按文件名基线配对施加 ------------------------

R1_TABLE_HEAD = (
    '| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | '
    '缺陷描述 | 攻击或破坏机理 |\n'
    '|:---|:---|:---:|:---|:---|:---|'
)

R2_TABLE_HEAD = (
    '| 稳定 ID (沿用 R1) | 检查点 / 文件位置 | 原始 R1 评级 | 变更归属 (本次引入/历史既有) | '
    '终审裁决 | 最终定性分析与裁决理由 | 处置要求 |\n'
    '|:---|:---|:---:|:---:|:---:|:---|:---|'
)

# 官方模板（`templates/r2-report.md`）的表头形态；历史归档清一色写成上面那种自拟表头。
OFFICIAL_R2_TABLE_HEAD = (
    '| R1 稳定 ID | 最终定性 | 复核依据与反证据 | 残余风险 |\n'
    '| :--- | :--- | :--- | :--- |'
)


def _body_with_ids(template, table_head, ids, tail):
    """用给定稳定 ID 列表重建报告表格；``ids=[]`` 表示「表头在位、明细为空」。"""
    head, sep, _ = template.partition(table_head)
    assert sep, '夹具表头漂移，须同步更新本测试'
    rows = ''.join(
        '| %s | P2 (Suggestion) | 历史既有 | `src/a.ts:1` | 缺陷 | 机理 |\n' % i
        for i in ids)
    return head + sep + '\n' + rows + tail


def _build_two_round(tmp_path, *, round2_ids=('R1-1', 'R1-2'), with_round2_r2=True,
                     r2_table_head=R2_TABLE_HEAD, round2_r2_ids=()):
    """共享归档：第 1 轮已闭环；第 2 轮（delta）的 R1 清单与 R2 明细表按参数给出。

    两轮的稳定 ID **故意重名**（都从 ``R1-1`` 起编）——这正是跨轮次并集碰撞的现场：
    第 1 轮的 R2 行足以让第 2 轮的空明细表「看起来对齐」。
    ``r2_table_head`` 用于切换 R2 表头形态（历史自拟表头 / 官方模板表头）。
    """
    d = tmp_path / 'archive'
    d.mkdir()
    r2_body = (R2_BODY if r2_table_head == R2_TABLE_HEAD
               else R2_BODY.replace(R2_TABLE_HEAD, r2_table_head))
    names = {
        'r1-aaa1111..bbb2222.md': R1_BODY,
        'r2-aaa1111..bbb2222.md': r2_body,
        'delta-r1-bbb2222..ccc3333.md': _body_with_ids(
            R1_BODY, R1_TABLE_HEAD, round2_ids, '\n## 5. 第一轮结论概要\n移交第二轮。\n'),
    }
    if with_round2_r2:
        names['delta-r2-bbb2222..ccc3333.md'] = _body_with_ids(
            r2_body, r2_table_head, round2_r2_ids,
            '\n## 3. 终审放行结论\n- **交付判定**: ✅ 准予交付\n')
    for fname, body in names.items():
        (d / fname).write_text(body, encoding='utf-8', newline='\n')
    rows = [_row(rank, fname, _sha12(names[fname]), '🔴 1 / 🟡 1 / ⚪ 0')
            for rank, fname in (('R1', 'r1-aaa1111..bbb2222.md'),
                                ('R2', 'r2-aaa1111..bbb2222.md'),
                                ('delta-r1', 'delta-r1-bbb2222..ccc3333.md'),
                                ('delta-r2', 'delta-r2-bbb2222..ccc3333.md'))
            if fname in names]
    (d / 'README.md').write_text(
        INDEX_TMPL.format(mode='full', verdict='✅ 准予交付', rows='\n'.join(rows)),
        encoding='utf-8', newline='\n')
    return d


def test_cross_round_id_union_collision_fails(tmp_path):
    """BK-0003：旧轮 R2 行不得替新一轮顶包——空明细表仍须判失败。

    全局并集下 ``R2_IDS`` 含第 1 轮的 R1-1/R1-2，新一轮（delta-r1 有清单、
    delta-r2 明细为空）因此被判「稳定 ID 对齐」并 rc=0，门禁静默放行。
    """
    d = _build_two_round(tmp_path)
    r = _run(d)
    assert r.returncode == 1, r.stdout
    assert 'delta-r1' in r.stdout or '明细表' in r.stdout


def test_paired_r1_without_r2_fails(tmp_path):
    """BK-0003：登记了 R1 却无同基线 R2 的轮次属未闭环，不得靠他轮 R2 顶包放行。"""
    d = _build_two_round(tmp_path, with_round2_r2=False)
    r = _run(d)
    assert r.returncode == 1, r.stdout
    assert 'R2' in r.stdout


def test_two_round_archive_with_paired_ids_passes(tmp_path):
    """BK-0003 反向保护：两轮各自闭环时必须放行（配对不得误伤多轮归档）。"""
    d = _build_two_round(tmp_path)
    r2_round2 = _body_with_ids(
        R2_BODY, R2_TABLE_HEAD, ['R1-1', 'R1-2'],
        '\n## 3. 终审放行结论\n- **交付判定**: ✅ 准予交付\n')
    (d / 'delta-r2-bbb2222..ccc3333.md').write_text(r2_round2, encoding='utf-8', newline='\n')
    index = (d / 'README.md').read_text(encoding='utf-8')
    # 台账指纹随内容同步（门禁按登记的 SHA256 前 12 位比对）
    index = re.sub(
        r'(\| `delta-r2-bbb2222\.\.ccc3333\.md` \| `)[0-9a-f]{12}(`)',
        lambda m: m.group(1) + _sha12(r2_round2) + m.group(2), index)
    (d / 'README.md').write_text(index, encoding='utf-8', newline='\n')
    r = _run(d)
    assert r.returncode == 0, r.stdout + r.stderr


def test_official_template_r2_header_is_aligned(tmp_path):
    """R1-1（R1 轮发现）：R2 表头以官方模板 `| R1 稳定 ID |` 为准，抽取器须兼容。

    `templates/r2-report.md` 的表头首列写作 `R1 稳定 ID`，而历史归档自拟为
    `稳定 ID (沿用 R1)`。首列抽取若只认 `稳定 ID` 字面前缀，模板产出的合规 R2
    报告会被判成「明细表为空」——合法交付被确定性误阻断（且 R1 清单为空时防捏造的
    方向一也会静默失效）。
    """
    d = _build_two_round(tmp_path, r2_table_head=OFFICIAL_R2_TABLE_HEAD,
                         round2_r2_ids=('R1-1', 'R1-2'))
    r = _run(d)
    assert r.returncode == 0, r.stdout + r.stderr


def test_official_template_r2_empty_detail_table_still_fails(tmp_path):
    """R1-1 反向保护：换表头形态不得把「空明细表放行」一起放掉。"""
    d = _build_two_round(tmp_path, r2_table_head=OFFICIAL_R2_TABLE_HEAD)
    r = _run(d)
    assert r.returncode == 1, r.stdout
    assert '明细表' in r.stdout


# --- BK-0004 回归：`**终审裁决**` 在索引中必须唯一 -------------------------------


def test_fenced_example_verdict_cannot_preempt_real_field(tmp_path):
    """BK-0004：围栏示例行位于真实字段之前时不得抢答——首匹配制会产生**假 PASS**。

    真实字段为「阻断交付」，但索引顶部围栏示例里的「准予交付」被 ``head -n 1``
    先命中，``--require-verdict=PASS`` 于是放行了一份被阻断的归档。
    """
    d, _, _ = _build(tmp_path, verdict='🔴 阻断交付')
    index = (d / 'README.md').read_text(encoding='utf-8')
    example = '```markdown\n- **终审裁决**: ✅ 准予交付\n```\n\n'
    (d / 'README.md').write_text(
        index.replace('# 审查归档 · 示例交付\n', '# 审查归档 · 示例交付\n\n' + example, 1),
        encoding='utf-8', newline='\n')
    r = _run(d, '--require-verdict=PASS')
    assert r.returncode == 1, '围栏示例行不得抢答真实裁决字段'
    assert '终审裁决' in r.stdout


def test_duplicate_verdict_field_fails_without_require_verdict(tmp_path):
    """BK-0004：命中数 ≠ 1 属结构缺陷，与 ``--require-verdict`` 是否传入无关。"""
    d, _, _ = _build(tmp_path)
    index = (d / 'README.md').read_text(encoding='utf-8')
    (d / 'README.md').write_text(
        index + '\n> 备注：上文 **终审裁决** 字段亦见于派发提示词模板。\n', encoding='utf-8', newline='\n')
    r = _run(d)
    assert r.returncode == 1
    assert '终审裁决' in r.stdout


# --- 兼容壳（契约迁移：`.sh` 退役为 §2.2 转发壳）--------------------------------


@pytest.mark.skipif(sys.platform == 'win32' or shutil.which('bash') is None,
                    reason='POSIX 兼容壳仅在 POSIX + bash 环境可执行')
def test_compat_shim_forwards_to_python(tmp_path):
    """L4 壳等价性：`bash check-review-report.sh` 与 `.py` 退出码/stdout 必须一致。

    壳只做转发（§2.2），不得做参数解析或输出加工，故对同一归档的裁决输出必须逐字相同。
    """
    d, _, _ = _build(tmp_path)
    via_py = subprocess.run([sys.executable, str(SCRIPT), str(d)],
                            capture_output=True, text=True, encoding='utf-8')
    via_sh = subprocess.run(['bash', str(SHIM), str(d)],
                            capture_output=True, text=True, encoding='utf-8')
    assert via_sh.returncode == via_py.returncode == 0, via_sh.stdout + via_sh.stderr
    assert via_sh.stdout == via_py.stdout

    via_py_err = subprocess.run([sys.executable, str(SCRIPT), str(d), '--bogus'],
                                capture_output=True, text=True, encoding='utf-8')
    via_sh_err = subprocess.run(['bash', str(SHIM), str(d), '--bogus'],
                                capture_output=True, text=True, encoding='utf-8')
    assert via_sh_err.returncode == via_py_err.returncode == 2
    assert via_sh_err.stdout == via_py_err.stdout
    assert via_sh_err.stderr == via_py_err.stderr


# --- R1-01 / R1-02 回归（fail-open 与 Unicode 空白填充）---------------------------


def _without_table_rows(body):
    """删除「稳定 ID」契约表格的数据行，仅保留表头与列分隔行。"""
    return '\n'.join(line for line in body.split('\n') if not line.startswith('| R1-'))


def _with_malformed_id_cells(body):
    """把 ID 单元格改成「含 ID 记号但不符合契约列结构」（→ 解析失败信号，触发 fail-closed）。"""
    return body.replace('| R1-1 |', '| R1-1（P1） |', 1).replace('| R1-2 |', '| R1-2（P2） |', 1)


def test_u3000_padded_id_header_cannot_bypass_empty_r2_table(tmp_path):
    """R1-01 回归：U+3000 缩进的「稳定 ID」表头不得让「R2 空裁决表」保护整体失效（fail-open）。

    原实现以 gawk `[[:space:]]` 识别表头（UTF-8 locale 下匹配 U+3000）；若移植时退化为 ASCII
    字符类，则表头匹配失败 → ID 集为空 → 两向对齐与空表保护被静默跳过，非法归档被放行。
    """
    r1_body = R1_BODY.replace('| 稳定 ID |', '|\u3000稳定 ID |', 1)
    d, _, _ = _build(tmp_path, r1_body=r1_body, r2_body=_without_table_rows(R2_BODY))
    r = _run(d)
    assert r.returncode == 1, r.stdout + r.stderr
    assert '禁止空表放行' in r.stdout


def test_id_header_without_ids_fails_closed(tmp_path):
    """R1-01 回归：表头出现且表格含 ID 记号行、却抽不到任何契约 ID 时必须 fail-closed。"""
    d, _, _ = _build(tmp_path, r1_body=_with_malformed_id_cells(R1_BODY))
    r = _run(d)
    assert r.returncode == 1, r.stdout + r.stderr
    assert '未抽取到任何稳定 ID' in r.stdout


def test_zero_defect_clean_report_is_accepted(tmp_path):
    """R1-01 回归边界：真正零缺陷的空明细表（表头后无 ID 记号行）不得被误判为解析失败。"""
    d, _, _ = _build(tmp_path,
                     r1_body=_without_table_rows(R1_BODY),
                     r2_body=_without_table_rows(R2_BODY))
    r = _run(d)
    assert r.returncode == 0, r.stdout + r.stderr
    assert '未抽取到任何稳定 ID' not in r.stdout


def test_unicode_padded_write_mode_cell_is_accepted(tmp_path):
    """R1-02 回归：写入形态单元格的 Unicode 空白填充不应把合法归档误判为非法。"""
    d, _, _ = _build(tmp_path)
    index = (d / 'README.md').read_text(encoding='utf-8')
    (d / 'README.md').write_text(
        index.replace('| direct |', '|\u3000direct\u3000|', 1), encoding='utf-8', newline='\n')
    r = _run(d)
    assert r.returncode == 0, r.stdout + r.stderr
    assert '通过' in r.stdout

