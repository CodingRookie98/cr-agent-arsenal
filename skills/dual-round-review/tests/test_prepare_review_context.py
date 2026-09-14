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
