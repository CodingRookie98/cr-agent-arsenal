"""RFC-0002 子智能体直写通道契约测试。

校验「路径预授权 + 直写通道 + 转录降级登记」在五个载体间保持一致：
技能规程（SKILL.md）、提示词模板（R1/R2）、机械门禁与上下文脚本。
"""
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
R1 = SKILL_DIR / 'references' / 'round-1-red-team.md'
R2 = SKILL_DIR / 'references' / 'round-2-meta-architect.md'
SKILL = SKILL_DIR / 'SKILL.md'
CHECKER = SKILL_DIR / 'scripts' / 'check-review-report.sh'
PREPARE = SKILL_DIR / 'scripts' / 'prepare-review-context.sh'

LEGACY_READONLY = ('Read-Only constraint: You must not modify the working tree, '
                   'branch, or index.')


def _text(path):
    return path.read_text(encoding='utf-8')


# --- 提示词模板：Write-Scope 例外与写盘契约 ------------------------------------


def test_r1_declares_write_scope_exception():
    t = _text(R1)
    assert 'Write-scope constraint' in t
    assert '[REPORT_PATH]' in t
    assert 'REPORT_SHA256' in t
    assert 'REPORT_BYTES' in t


def test_r2_declares_write_scope_exception():
    t = _text(R2)
    assert 'Write-scope constraint' in t
    assert '[REPORT_PATH]' in t
    assert 'REPORT_SHA256' in t
    assert 'REPORT_BYTES' in t


def test_templates_drop_legacy_readonly_clause():
    """旧的全禁 Read-Only 条款必须被**替换**——留一份残骸会与例外条款自相矛盾。"""
    assert LEGACY_READONLY not in _text(R1)
    assert LEGACY_READONLY not in _text(R2)


def test_templates_forbid_self_rescue():
    """失败时不得自救：不得换路径、不得建目录、不得覆盖既有文件。"""
    for path in (R1, R2):
        t = _text(path)
        assert '不得自救' in t, path.name
        assert '改用其他路径' in t, path.name
        assert '覆盖既有文件' in t, path.name


def test_templates_require_verbatim_write():
    for path in (R1, R2):
        assert '逐字' in _text(path), path.name


def test_templates_report_write_once_protection():
    for path in (R1, R2):
        assert 'Write-Once' in _text(path), path.name


def test_r2_requires_write_mode_verification():
    """R2 必须在元审判中核验 R1 报告的产出通道（direct / transcribed）。"""
    t = _text(R2)
    assert '产出通道核验' in t
    assert 'transcribed' in t


def test_templates_preserve_mandatory_sections():
    """直写契约不得改动报告结构（R1 五区块 / R2 三区块）。"""
    r1 = _text(R1)
    for s in ['## 1. 第一性原理与本质溯源分析',
              '## 2. 运行时与 SSR/沙盒安全推演',
              '## 3. 红队攻击路径推演',
              '## 4. 潜在缺陷清单',
              '## 5. 第一轮结论概要']:
        assert s in r1, s
    r2 = _text(R2)
    for s in ['## 1. 元审查辩证质询',
              '## 2. 最终裁决明细表',
              '## 3. 终审放行结论']:
        assert s in r2, s


# --- 技能规程：契约与诚实边界 --------------------------------------------------


def test_skill_documents_direct_write_channel():
    t = _text(SKILL)
    for token in ('直写通道', '转录降级', '写入形态', '路径预授权', '--round'):
        assert token in t, f'SKILL.md 缺少契约关键词: {token}'


def test_skill_documents_honest_boundary():
    """不得把提示词约束表述为隔离（RFC-0002 §3.7 诚实边界）。"""
    t = _text(SKILL)
    assert '提示词契约' in t
    assert '诚实边界' in t


def test_skill_documents_legacy_migration():
    """既有归档须一次性补列迁移，且报告文件与指纹不得变动。"""
    t = _text(SKILL)
    assert 'V2.1.0 → V2.2.0 迁移' in t
    assert '指纹不得变动' in t


# --- 脚本：门禁与预授权路径 ----------------------------------------------------


def test_checker_enforces_write_mode():
    t = _text(CHECKER)
    assert 'direct' in t and 'transcribed' in t
    assert '写入形态' in t


def test_prepare_supports_round_argument():
    t = _text(PREPARE)
    assert '--round' in t
    for r in ('r1', 'r2', 'delta-r1', 'delta-r2'):
        assert r in t, r
    assert 'Write-Once' in t


# --- Delta 回归（R1-8 / R1-11）------------------------------------------------


def test_templates_guard_unreplaced_placeholder():
    """R1-8 回归：模板须有「占位符未替换即中止」兜底。

    `[REPORT_PATH]` 是合法文件名——无兜底时合规执行的子智能体会在当前目录
    真实创建该文件，落在唯一授权写入面之外。
    """
    for path in (R1, R2):
        t = _text(path)
        assert '占位符兜底' in t, path.name
        assert '未注入' in t, path.name


def test_skill_forbids_isolation_claim():
    """R1-11 回归：SKILL.md 中每次出现「已隔离」都必须处于**禁止**语境。

    朴素的 `'已隔离' not in t` 会假红——SKILL.md 本身含该词（写在禁令内）。
    """
    t = _text(SKILL)
    hits = [m.start() for m in re.finditer('已隔离', t)]
    assert hits, 'SKILL.md 应含「严禁表述为已隔离」的诚实边界声明'
    for pos in hits:
        window = t[max(0, pos - 40):pos + 12]
        assert any(k in window for k in ('严禁', '不得', '禁止')), (
            '出现非禁止语境的「已隔离」表述: …' + window + '…')


def test_skill_documents_path_determinism():
    """R1-1 回归：SKILL.md 必须写明预授权路径是基线的确定函数。"""
    t = _text(SKILL)
    assert '路径必须是基线的确定函数' in t
    assert 'R1-1 回归' in t


def test_skill_documents_replay_branch():
    """R1-1 回归：异常降级表必须覆盖「同轮同基线需重派」。"""
    assert '同轮同基线需重派' in _text(SKILL)


def test_skill_fingerprint_comparison_is_full_value():
    """R1-4 回归：核验口径必须为 64 位全值比对（12 位仅用于台账登记）。

    修复前 SKILL.md 的核验动作为 `sha256sum <报告文件> | cut -c1-12`，
    与模板回报的 64 位全值字面永不相等 → 会误判写入异常并作废整轮。
    """
    t = _text(SKILL)
    assert 'R1-4 回归' in t
    assert 'sha256sum <报告文件> | cut -c1-12' not in t, '核验不得使用截断到 12 位的复算命令'
    assert 'sha256sum <报告文件>`）并与子智能体回报的**全值**逐字比对' in t


def test_checker_uses_last_column_not_fixed_index():
    """R1-12 回归：写入形态须按末列定位，避免结论含裸竖线时错位。"""
    assert 'NF>=9' in _text(CHECKER)

