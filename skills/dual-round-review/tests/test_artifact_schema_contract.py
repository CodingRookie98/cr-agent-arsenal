"""产物审查 schema 契约测试：验证 `Review Schema = artifact` 的识别、区块校验与零迁移。

覆盖:
  1. 零迁移回归：既有归档的门禁结果不得因 schema 支持而改变（含 1 例已登记的既有失败）;
  2. schema 判定：报告声明 `> **Review Schema**: artifact` 时按产物五区块校验；未声明缺省 code;
  3. 防绕过：标记写在围栏代码块内视为未声明（不得凭此切换校验口径）;
  4. 稳定 ID 对齐在 artifact schema 下仍生效（R2 不得凭空引入 ID、不得静默吞并 R1 指控）;
  5. 未声明标记却缺 code 区块时，门禁给出可操作提示（防漏标记被误判为「缺区块」）;
  6. 模板契约：产物 R1 模板含三条硬约束与五区块标题；分级表含四级与 ⚖️ 出口。

背景：产物没有可执行真值源，故判据由「冻结的产物契约 + Toulmin 四元组」提供；终止条件由
「阻断项清零」替换为「信息增量收敛 + ⚖️ 不可判定出口」。
"""
import hashlib
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / 'scripts' / 'check-review-report.sh'
REPO = SKILL_DIR.parents[1]
REVIEWS = REPO / 'docs' / 'project' / 'reviews'

ARTIFACT_MARKER = '> **Review Schema**: artifact'

R1_ARTIFACT_BODY = """# 第一轮产物审查报告 (Round 1 Artifact Review Report)

> **Review Schema**: artifact

## 1. 产物契约核验与意图溯源
- **契约逐字复述**: Intent=冻结规则语义；Audience=5 宿主读者；Out of Scope=文风
- **契约可判定性评估**: 六项齐备

## 2. 事实与证据核验
| # | 事实性主张 | 核验方式 | 结论 | 出处 |
|---|---|---|---|---|
| F1 | 规则文件 129 行 | 机器统计 | 已核实 | §3 |

## 3. 失败预演与误用路径推演
- **Steelman（必填、必在最前）**: 该产物最强的论证是……；我接受其中 A、B。
- **失败归因（过去时）**:
  1. 它失败的原因是读者把条件性条款当成了普遍约束。

## 4. 指控清单
| 稳定 ID | 级别推断 | Claim | Grounds | Warrant | Impact | Top-3 |
|---|---|---|---|---|---|---|
| R1-1 | P1 | 契约违背 | `docs/x.md:12` | 若读者据此行行动则越权 | 误导执行 | ① |

## 5. 第一轮结论概要
- 1 项 P1 候选，交裁决。
"""

R2_BODY = """# 第二轮元对抗审查与终审裁决书 (Round 2 Meta-Architect Verdict)

## 1. 元审查辩证质询 (Meta-Challenges on Round 1)
- **R1 指控可信度整体评估**: 中肯

## 2. 最终裁决明细表 (Final Verdict Synthesis Table)
| 稳定 ID (沿用 R1) | 检查点 / 位置 | 原始 R1 评级 | 归属 | 终审裁决 | 最终定性分析与裁决理由 | 处置要求 |
|:---|:---|:---:|:---:|:---:|:---|:---|
| R1-1 | `docs/x.md:12` | P1 | 契约内 | 🔴 **P1 阻断项** | Warrant 成立，须修复 | 必须修复 |

## 3. 终审放行结论
- **交付判定**: 🔴 阻断交付
"""

CODE_R1_BODY = """# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析
- **改动性质定性**: 本质根因修复

## 2. 运行时与 SSR/沙盒安全推演
未激活（非客户端/SSR 改动）

## 3. 红队攻击路径推演
- **攻击路径 1**: 触发条件 -> 复现推演 -> 影响结果

## 4. 潜在缺陷清单
| 稳定 ID | 严重级别推断 | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | P1 | 是 | `src/a.ts:1` | 竞态覆盖 | 二次请求覆写 |

## 5. 第一轮结论概要
存在 1 项阻断候选。
"""

INDEX_TMPL = """# 审查归档 · {unit}

- **交付单元**: {unit}
- **归档根**: {root}
- **审查模式**: {mode}
- **当前迭代计数**: 1/3
- **终审裁决**: {verdict}

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 | 写入形态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{rows}
"""


def _sha12(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def _row(round_token, fname, body, conclusion='🔴 阻断交付'):
    return '| %s | `base..head` | handle | `%s` | `%s` | %s | direct |' % (
        round_token, fname, _sha12(body), conclusion)


def _build(tmp_path, name, reports, *, schema='artifact', verdict='🔴 阻断交付'):
    """reports: [(round_token, fname, body)]；schema 仅用于构造索引的模式字段。"""
    d = tmp_path / name
    d.mkdir(parents=True)
    rows = '\n'.join(_row(t, f, b) for t, f, b in reports)
    (d / 'README.md').write_text(
        INDEX_TMPL.format(unit=name, root=str(d), mode=schema, verdict=verdict, rows=rows),
        encoding='utf-8')
    for _, fname, body in reports:
        (d / fname).write_text(body, encoding='utf-8')
    return d


def _run_gate(archive):
    return subprocess.run(['bash', str(SCRIPT), str(archive)],
                          capture_output=True, text=True)


# --- 1. 零迁移回归 ------------------------------------------------------------

def test_existing_archives_all_pass_gate():
    """既有归档必须全部通过门禁（schema 支持与台账修正后的统一基线）。

    历史：2026-10-10-global-agent-delegation-redlines 的台账「轮次」列曾写作 `delta-r1 · 第6轮`
    （带描述，非 schema 值），自归档生成起门禁即无法识别轮次标记。该缺陷于 2026-10-11 经用户批准
    修正——只规范轮次列、原描述移入「结论」列开头，六份报告文件与 SHA256 指纹一字未动。
    本断言即修正确认，同时守护其它归档不再漂移。
    """
    archives = sorted(p for p in REVIEWS.glob('*') if (p / 'README.md').is_file())
    assert archives, '未找到任何归档目录（回归测试失去意义）'
    failures = []
    for a in archives:
        r = _run_gate(a)
        if r.returncode != 0:
            failures.append('%s: %s' % (a.name, r.stdout.strip().splitlines()[:3]))
    assert not failures, '既有归档门禁失败: %s' % failures


def test_ledger_round_column_tolerates_human_description(tmp_path):
    """轮次列容忍人类记述：`delta-r1 · 第1轮` 按前导标记值解析后应通过。

    历史：2026-10-10 归档因该写法自生成起即无法通过校验。处置分两步——先在数据侧规范台账
    （e166725），再在门禁侧容忍记述习惯（本次），使同类台账无需规范即可通过。
    """
    for i, token in enumerate(('delta-r1 · 第1轮', 'r1 · 第1轮', 'delta-r1')):
        d = _build(tmp_path, 'decorated-%d' % i,
                   [(token, 'r1-aaa..bbb.md', R1_ARTIFACT_BODY)])
        r = _run_gate(d)
        assert r.returncode == 0, '%r 未被容忍: %s%s' % (token, r.stdout, r.stderr)


def test_ledger_round_column_rejects_unknown_token(tmp_path):
    """容忍不等于放宽：非标记值轮次（如 `round-1`）仍须判为未登记 R1。"""
    d = _build(tmp_path, 'unknown-round',
               [('round-1', 'r1-aaa..bbb.md', R1_ARTIFACT_BODY)])
    r = _run_gate(d)
    assert r.returncode != 0
    assert '台账未登记任何 R1 报告' in r.stdout


# --- 2. schema 判定 ----------------------------------------------------------

def test_artifact_schema_archive_passes(tmp_path):
    d = _build(tmp_path, 'artifact-ok',
               [('r1', 'r1-aaa..bbb.md', R1_ARTIFACT_BODY), ('r2', 'r2-aaa..bbb.md', R2_BODY)])
    r = _run_gate(d)
    assert r.returncode == 0, r.stdout + r.stderr


def test_code_schema_archive_still_passes(tmp_path):
    d = _build(tmp_path, 'code-ok',
               [('r1', 'r1-aaa..bbb.md', CODE_R1_BODY), ('r2', 'r2-aaa..bbb.md', R2_BODY)])
    r = _run_gate(d)
    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_report_missing_section_fails_with_section_name(tmp_path):
    broken = R1_ARTIFACT_BODY.replace('## 3. 失败预演与误用路径推演', '## 3. 未命名区块')
    d = _build(tmp_path, 'artifact-broken', [('r1', 'r1-aaa..bbb.md', broken)])
    r = _run_gate(d)
    assert r.returncode != 0
    assert '## 3. 失败预演与误用路径推演' in r.stdout


def test_marker_inside_fence_is_not_recognized(tmp_path):
    """防绕过：把 schema 标记藏进围栏代码块不得切换校验口径。"""
    fenced = R1_ARTIFACT_BODY.replace(
        ARTIFACT_MARKER, '```markdown\n%s\n```' % ARTIFACT_MARKER)
    d = _build(tmp_path, 'artifact-fenced', [('r1', 'r1-aaa..bbb.md', fenced)])
    r = _run_gate(d)
    assert r.returncode != 0
    # 退回 code schema：应报缺 code 区块，并给出可操作提示
    assert '## 1. 第一性原理与本质溯源分析' in r.stdout
    assert '未发现 Review Schema 标记' in r.stdout


# --- 3. 稳定 ID 对齐在 artifact schema 下仍生效 ---------------------------------

def test_id_alignment_still_enforced_for_artifact(tmp_path):
    r2 = R2_BODY.replace('| R1-1 | `docs/x.md:12`', '| R1-9 | `docs/x.md:12`')
    r2 = r2.replace('| R1-1 | P1 | 契约内', '| R1-9 | P1 | 契约内', 1)
    d = _build(tmp_path, 'artifact-id-drift', [
        ('r1', 'r1-aaa..bbb.md', R1_ARTIFACT_BODY),
        ('r2', 'r2-aaa..bbb.md', r2)])
    r = _run_gate(d)
    assert r.returncode != 0
    assert 'R1-9' in r.stdout


# --- 4. 模板契约 --------------------------------------------------------------

def test_artifact_templates_carry_hard_constraints():
    tpl = (SKILL_DIR / 'references' / 'round-1-artifact-red-team.md').read_text(encoding='utf-8')
    for token in ('Steelman 义务', '过去时', 'Toulmin 四元组', 'Pre-mortem Facilitator and Hostile Reader'):
        assert token in tpl, '产物 R1 模板缺少: %s' % token
    for section in ('## 1. 产物契约核验与意图溯源', '## 2. 事实与证据核验',
                    '## 3. 失败预演与误用路径推演', '## 4. 指控清单', '## 5. 第一轮结论概要'):
        assert section in tpl, '产物 R1 模板缺少区块标题: %s' % section
    assert ARTIFACT_MARKER in tpl, '产物 R1 模板未声明 Review Schema 标记'


def test_artifact_rubric_has_four_levels_and_undecidable_exit():
    rubric = (SKILL_DIR / 'references' / 'verdict-rubric-artifact.md').read_text(encoding='utf-8')
    for token in ('P1 契约违背', 'P2 削弱', 'Dismissed', 'Undecidable', '信息增量收敛', '400 行', '200 行'):
        assert token in rubric, '产物分级表缺少: %s' % token


def test_skill_md_wires_artifact_schema():
    skill = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
    for token in ('审查对象 (Review Schema)', 'artifact-contract.md',
                  'round-1-artifact-red-team.md', 'verdict-rubric-artifact.md',
                  '无契约不得开审', '有外部读者 或 有不可逆后果'):
        assert token in skill, 'SKILL.md 未接通产物模式: %s' % token
    assert 'artifact' in (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8').split('---')[1], \
        'frontmatter description 未声明 artifact 触发面'
