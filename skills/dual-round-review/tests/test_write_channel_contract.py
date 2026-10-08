"""RFC-0002 子智能体直写通道契约测试。

校验「路径预授权 + 直写通道 + 转录降级登记」在五个载体间保持一致：
技能规程（SKILL.md）、提示词模板（R1/R2）、机械门禁与上下文脚本。
"""
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
