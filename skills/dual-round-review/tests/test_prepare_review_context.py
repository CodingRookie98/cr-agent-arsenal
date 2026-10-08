import re
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'prepare-review-context.sh'


def _git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True)


def _repo(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    _git(tmp_path, 'config', 'user.email', 't@example.com')
    _git(tmp_path, 'config', 'user.name', 't')
    (tmp_path / 'a.txt').write_text('one\n', encoding='utf-8')
    _git(tmp_path, 'add', '.')
    _git(tmp_path, 'commit', '-qm', 'init')
    return tmp_path


def _run(repo, *args):
    return subprocess.run(['bash', str(SCRIPT), *args], cwd=repo, capture_output=True, text=True)


def test_help_exits_zero(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '用法' in r.stdout


def test_working_mode_scaffolds_record(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--working')
    assert r.returncode == 0, r.stderr
    assert (repo / '.review-context' / 'review-working.md').is_file()


def test_record_contains_schema_fields(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _run(repo, '--working')
    text = (repo / '.review-context' / 'review-working.md').read_text(encoding='utf-8')
    for field in ['模式', '基线', '轮次', '迭代计数', 'Previous Blockers', '终审裁决', '阻断项统计']:
        assert f'- **{field}**' in text


def test_no_record_skips_scaffold(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    assert not (repo / '.review-context').exists()


def test_range_mode_writes_record_named_by_base(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _git(repo, 'commit', '-aqm', 'second')
    base = _git(repo, 'rev-parse', '--short', 'HEAD~1').stdout.strip()
    r = _run(repo, 'HEAD~1', 'HEAD')
    assert r.returncode == 0, r.stderr
    assert (repo / '.review-context' / f'review-{base}.md').is_file()


def test_record_is_not_clobbered(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _run(repo, '--working')
    rec = repo / '.review-context' / 'review-working.md'
    rec.write_text('CUSTOM\n', encoding='utf-8')
    _run(repo, '--working')
    assert rec.read_text(encoding='utf-8') == 'CUSTOM\n'


def test_invalid_base_ref_fails(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo, 'no-such-ref', 'HEAD')
    assert r.returncode != 0


# --- RFC-0001 交付凭据归档 scaffold -----------------------------------------

ARCHIVE_FIELDS = ['**交付单元**', '**归档根**', '**终审裁决**', '## 轮次台账']


def _archive_dirs(repo, root='docs/project/reviews'):
    base = repo / root
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir())


def test_help_lists_archive_options(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '--slug' in r.stdout
    assert '--archive-root' in r.stdout


def test_slug_scaffolds_archive_index(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=demo-delivery', '--working')
    assert r.returncode == 0, r.stderr
    dirs = _archive_dirs(repo)
    assert len(dirs) == 1
    assert dirs[0].name.endswith('-demo-delivery')
    index = dirs[0] / 'README.md'
    assert index.is_file()
    text = index.read_text(encoding='utf-8')
    for field in ARCHIVE_FIELDS:
        assert field in text


def test_archive_root_recorded_in_anchor(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _run(repo, '--slug=demo-delivery', '--working')
    anchor = (repo / '.review-context' / 'review-working.md').read_text(encoding='utf-8')
    assert '## 归档索引' in anchor
    assert 'docs/project/reviews/' in anchor


def test_archive_dir_reused_on_rerun(tmp_path):
    """同一 slug 的二次运行（模拟 Delta 再循环）必须复用既有目录，不得按新日期重建。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _run(repo, '--slug=demo-delivery', '--working')
    _run(repo, '--slug=demo-delivery', '--working')
    assert len(_archive_dirs(repo)) == 1


def test_archive_index_section_not_duplicated(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _run(repo, '--slug=demo-delivery', '--working')
    _run(repo, '--slug=demo-delivery', '--working')
    anchor = (repo / '.review-context' / 'review-working.md').read_text(encoding='utf-8')
    assert anchor.count('## 归档索引') == 1


def test_no_slug_creates_no_archive(tmp_path):
    """不传 --slug 时保持既有行为完全不变（向后兼容）。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--working')
    assert r.returncode == 0, r.stderr
    assert not (repo / 'docs').exists()


def test_no_record_with_slug_creates_no_archive(tmp_path):
    """--no-record 语义为「不落盘」，归档 scaffold 必须一并禁用。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=demo-delivery', '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    assert not (repo / 'docs').exists()


def test_archive_root_override(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=demo-delivery', '--archive-root=custom/reviews', '--working')
    assert r.returncode == 0, r.stderr
    assert len(_archive_dirs(repo, root='custom/reviews')) == 1
    assert not (repo / 'docs').exists()


def test_existing_archive_index_not_overwritten(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _run(repo, '--slug=demo-delivery', '--working')
    index = _archive_dirs(repo)[0] / 'README.md'
    index.write_text('CUSTOM-INDEX\n', encoding='utf-8')
    _run(repo, '--slug=demo-delivery', '--working')
    assert index.read_text(encoding='utf-8') == 'CUSTOM-INDEX\n'


def test_invalid_slug_rejected(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=Bad_Slug', '--working')
    assert r.returncode != 0


def test_help_does_not_scaffold(tmp_path):
    repo = _repo(tmp_path)
    _run(repo, '--help')
    assert not (repo / '.review-context').exists()


def test_staged_mode_scaffolds_record(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    _git(repo, 'add', 'a.txt')
    r = _run(repo, '--staged')
    assert r.returncode == 0, r.stderr
    assert (repo / '.review-context' / 'review-staged.md').is_file()


def test_options_order_independent(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--working', '--no-record')
    assert r.returncode == 0, r.stderr
    assert not (repo / '.review-context').exists()


def test_root_mode_scaffolds_record(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo)
    assert r.returncode == 0, r.stderr
    root_sha = _git(repo, 'rev-parse', '--short', 'HEAD').stdout.strip()
    assert (repo / '.review-context' / f'review-{root_sha}.md').is_file()


def test_unknown_option_fails(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo, '--bogus')
    assert r.returncode != 0


# --- RFC-0002 子智能体直写：--round 预授权报告路径 -------------------------------


def _report_path(stdout):
    m = re.search(r'本轮报告目标路径[^:]*:\s*(\S+\.md)', stdout)
    assert m, f'未从输出解析到报告目标路径:\n{stdout}'
    return m.group(1)


def test_help_lists_round_option(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '--round' in r.stdout


def test_round_prints_report_path(tmp_path):
    """--round 必须机械化输出本轮预授权写入面，且不得预创建目标文件。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert r.returncode == 0, r.stderr
    path = _report_path(r.stdout)
    assert '/r1-working..' in path
    assert not (repo / path).exists(), '目标文件不得被预创建（Write-Once 保护）'


def test_round_requires_slug(tmp_path):
    """--round 依赖归档目录，缺少 --slug 时必须显式报错。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--round=r1', '--working')
    assert r.returncode != 0
    assert '必须与 --slug 同时使用' in r.stderr


def test_invalid_round_rejected(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=demo', '--round=r9', '--working')
    assert r.returncode != 0
    assert 'r1' in r.stderr


def test_round_warns_when_target_exists(tmp_path):
    """Write-Once 保护：目标已存在时告警且绝不改写既有文件。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    first = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert first.returncode == 0, first.stderr
    target = repo / _report_path(first.stdout)
    target.write_text('existing\n', encoding='utf-8')

    second = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert second.returncode == 0, second.stderr
    assert 'Write-Once' in second.stdout
    assert target.read_text(encoding='utf-8') == 'existing\n'


def test_round_delta_alias_accepted(tmp_path):
    """Delta 再循环轮次标记必须被接受。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8')
    r = _run(repo, '--slug=demo', '--round=delta-r1', '--working')
    assert r.returncode == 0, r.stderr
    assert '/delta-r1-working..' in _report_path(r.stdout)

