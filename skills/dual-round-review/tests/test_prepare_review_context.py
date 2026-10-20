import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'prepare-review-context.py'
SHIM = SCRIPT.with_suffix('.sh')


def _git(repo, *args):
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True)


def _mk_repo_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def _repo(tmp_path):
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    _git(tmp_path, 'config', 'user.email', 't@example.com')
    _git(tmp_path, 'config', 'user.name', 't')
    (tmp_path / 'a.txt').write_text('one\n', encoding='utf-8', newline='\n')
    _git(tmp_path, 'add', '.')
    _git(tmp_path, 'commit', '-qm', 'init')
    return tmp_path


def _run(repo, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo,
                          capture_output=True, text=True, encoding='utf-8')


def test_help_exits_zero(tmp_path):
    r = _run(tmp_path, '--help')
    assert r.returncode == 0
    assert '用法' in r.stdout


def test_working_mode_scaffolds_record(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--working')
    assert r.returncode == 0, r.stderr
    assert (repo / '.review-context' / 'review-working.md').is_file()


def test_record_contains_schema_fields(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--working')
    text = (repo / '.review-context' / 'review-working.md').read_text(encoding='utf-8')
    for field in ['模式', '基线', '轮次', '迭代计数', 'Previous Blockers', '终审裁决', '阻断项统计']:
        assert f'- **{field}**' in text


def test_no_record_skips_scaffold(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    assert not (repo / '.review-context').exists()


def test_range_mode_writes_record_named_by_base(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _git(repo, 'commit', '-aqm', 'second')
    base = _git(repo, 'rev-parse', '--short', 'HEAD~1').stdout.strip()
    r = _run(repo, 'HEAD~1', 'HEAD')
    assert r.returncode == 0, r.stderr
    assert (repo / '.review-context' / f'review-{base}.md').is_file()


def test_record_is_not_clobbered(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--working')
    rec = repo / '.review-context' / 'review-working.md'
    rec.write_text('CUSTOM\n', encoding='utf-8', newline='\n')
    _run(repo, '--working')
    assert rec.read_text(encoding='utf-8') == 'CUSTOM\n'


def test_invalid_base_ref_fails(tmp_path):
    repo = _repo(tmp_path)
    r = _run(repo, 'no-such-ref', 'HEAD')
    assert r.returncode != 0


# --- BK-0045 未跟踪清单 / BK-0010 归档根防御 ---------------------------------


def test_untracked_block_lists_only_untracked_paths(tmp_path):
    """BK-0045：未跟踪清单不得混入已修改/已暂存条目（GNU BRE `\\?` 缺陷回归）。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    (repo / 'staged.txt').write_text('s\n', encoding='utf-8', newline='\n')
    _git(repo, 'add', 'staged.txt')
    (repo / 'new.txt').write_text('n\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    assert '未跟踪的新增文件' in r.stdout
    block = r.stdout.split('未跟踪的新增文件', 1)[1].split('💡', 1)[0]
    assert 'new.txt' in block
    assert 'a.txt' not in block
    assert 'staged.txt' not in block


def test_untracked_block_absent_without_untracked_files(tmp_path):
    """BK-0045：无未跟踪文件（仅修改/已暂存）时不出现未跟踪提示块。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    (repo / 'staged.txt').write_text('s\n', encoding='utf-8', newline='\n')
    _git(repo, 'add', 'staged.txt')
    r = _run(repo, '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    assert '未跟踪的新增文件' not in r.stdout


def test_untracked_block_preserves_unicode_and_space_paths(tmp_path):
    """R1-7：未跟踪清单须原样呈现中文/空格路径（-z 输出，无八进制转义与引号）。"""
    repo = _repo(tmp_path)
    tricky = '文档 名.md'
    (repo / tricky).write_text('x\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    block = r.stdout.split('未跟踪的新增文件', 1)[1].split('💡', 1)[0]
    assert tricky in block
    assert '\\346' not in block
    assert '"文档' not in block


def test_empty_archive_root_is_rejected(tmp_path):
    """BK-0010：--archive-root= 空值须在写盘前终结性拒绝（rc≠0 且给出修复提示）。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--working', '--no-record', '--archive-root=')
    assert r.returncode != 0
    assert 'archive-root' in r.stderr and '不能为空' in r.stderr
    assert not (repo / 'docs').exists()


def test_filesystem_root_archive_root_is_rejected(tmp_path):
    """BK-0010：--archive-root 指向文件系统根时拒绝（报告不得散落到任意位置）。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--working', '--no-record', f'--archive-root={os.path.abspath(os.sep)}')
    assert r.returncode != 0
    assert '文件系统根目录' in r.stderr


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
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
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
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--slug=demo-delivery', '--working')
    anchor = (repo / '.review-context' / 'review-working.md').read_text(encoding='utf-8')
    assert '## 归档索引' in anchor
    assert 'docs/project/reviews/' in anchor


def test_archive_dir_reused_on_rerun(tmp_path):
    """同一 slug 的二次运行（模拟 Delta 再循环）必须复用既有目录，不得按新日期重建。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--slug=demo-delivery', '--working')
    _run(repo, '--slug=demo-delivery', '--working')
    assert len(_archive_dirs(repo)) == 1


def test_archive_index_section_not_duplicated(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--slug=demo-delivery', '--working')
    _run(repo, '--slug=demo-delivery', '--working')
    anchor = (repo / '.review-context' / 'review-working.md').read_text(encoding='utf-8')
    assert anchor.count('## 归档索引') == 1


def test_no_slug_creates_no_archive(tmp_path):
    """不传 --slug 时保持既有行为完全不变（向后兼容）。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--working')
    assert r.returncode == 0, r.stderr
    assert not (repo / 'docs').exists()


def test_no_record_with_slug_creates_no_archive(tmp_path):
    """--no-record 语义为「不落盘」，归档 scaffold 必须一并禁用。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo-delivery', '--no-record', '--working')
    assert r.returncode == 0, r.stderr
    assert not (repo / 'docs').exists()


def test_archive_root_override(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo-delivery', '--archive-root=custom/reviews', '--working')
    assert r.returncode == 0, r.stderr
    assert len(_archive_dirs(repo, root='custom/reviews')) == 1
    assert not (repo / 'docs').exists()


def test_existing_archive_index_not_overwritten(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--slug=demo-delivery', '--working')
    index = _archive_dirs(repo)[0] / 'README.md'
    index.write_text('CUSTOM-INDEX\n', encoding='utf-8', newline='\n')
    _run(repo, '--slug=demo-delivery', '--working')
    assert index.read_text(encoding='utf-8') == 'CUSTOM-INDEX\n'


def test_invalid_slug_rejected(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=Bad_Slug', '--working')
    assert r.returncode != 0


def test_help_does_not_scaffold(tmp_path):
    repo = _repo(tmp_path)
    _run(repo, '--help')
    assert not (repo / '.review-context').exists()


def test_staged_mode_scaffolds_record(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _git(repo, 'add', 'a.txt')
    r = _run(repo, '--staged')
    assert r.returncode == 0, r.stderr
    assert (repo / '.review-context' / 'review-staged.md').is_file()


def test_options_order_independent(tmp_path):
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
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
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert r.returncode == 0, r.stderr
    path = _report_path(r.stdout)
    assert '/r1-working..' in path
    assert not (repo / path).exists(), '目标文件不得被预创建（Write-Once 保护）'


def test_round_requires_slug(tmp_path):
    """--round 依赖归档目录，缺少 --slug 时必须显式报错。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--round=r1', '--working')
    assert r.returncode != 0
    assert '必须与 --slug 同时使用' in r.stderr


def test_invalid_round_rejected(tmp_path):
    """R1-11 回归：原断言 `'r1' in stderr` 无鉴别力——usage 与白名单文案自带 r1。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo', '--round=r9', '--working')
    assert r.returncode != 0
    assert '取值必须为' in r.stderr


def test_round_warns_when_target_exists(tmp_path):
    """Write-Once 保护：目标已存在时告警且绝不改写既有文件。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    first = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert first.returncode == 0, first.stderr
    target = repo / _report_path(first.stdout)
    target.write_text('existing\n', encoding='utf-8', newline='\n')

    second = _run(repo, '--slug=demo', '--round=r1', '--working')
    assert second.returncode == 0, second.stderr
    assert 'Write-Once' in second.stdout
    assert target.read_text(encoding='utf-8') == 'existing\n'


def test_round_delta_alias_accepted(tmp_path):
    """Delta 再循环轮次标记必须被接受。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo', '--round=delta-r1', '--working')
    assert r.returncode == 0, r.stderr
    assert '/delta-r1-working..' in _report_path(r.stdout)



# --- RFC-0002 Delta 回归（R1-1 / R1-2 / R1-7）---------------------------------


def test_round_requires_explicit_baseline(tmp_path):
    """R1-1 回归：--round 禁止自适应模式。

    自适应会在两次调用间切换 working/range，使预授权路径漂移、
    Write-Once 保护静默失效（旧报告成为门禁不可枚举的孤儿）。
    """
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo', '--round=r1')
    assert r.returncode != 0
    assert '确定性基线' in r.stderr


def test_round_path_is_stable_on_dirty_tree(tmp_path):
    """R1-1 不变量：显式基线下，工作区被自身产物弄脏**不得**改变预授权路径。

    这是「路径是基线的确定函数」这一不变式的守护测试：R1-1 的漂移正源于
    scaffold 自身把净树弄脏后，第二次调用落入自适应 working 分支。
    鉴别 R1-1 本身的断言是 test_round_requires_explicit_baseline（禁止自适应）。
    """
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _git(repo, 'commit', '-aqm', 'second')
    first = _run(repo, '--slug=demo', '--round=r1', 'HEAD~1', 'HEAD')
    assert first.returncode == 0, first.stderr
    # 前提校验：首次调用必须确实弄脏了工作区，否则本测试是空洞的
    assert _git(repo, 'status', '--porcelain').stdout.strip(), \
        '首次调用应已创建 .review-context/ 与归档目录使工作区变脏'
    second = _run(repo, '--slug=demo', '--round=r1', 'HEAD~1', 'HEAD')
    assert second.returncode == 0, second.stderr
    assert _report_path(first.stdout) == _report_path(second.stdout), (
        '预授权路径必须是基线的确定函数——脏树导致文件名漂移即 Write-Once 失效')


def test_scaffold_index_header_has_write_mode_column(tmp_path):
    """R1-2 回归：scaffold 产出的台账表头必须含「写入形态」列且列数自洽。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    _run(repo, '--slug=demo', '--working')
    text = (_archive_dirs(repo)[0] / 'README.md').read_text(encoding='utf-8')
    assert '| 写入形态 |' in text
    header = next(l for l in text.splitlines() if l.startswith('| 轮次'))
    sep = next(l for l in text.splitlines() if l.startswith('| :---'))
    assert header.count('|') == sep.count('|'), '表头与分隔行列数必须一致'


def test_empty_round_rejected(tmp_path):
    """R1-7 回归：--round= 空值不得被 [[ -n ]] 静默短路。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo', '--round=', '--working')
    assert r.returncode != 0
    assert '不能为空' in r.stderr


def test_round_with_no_record_rejected(tmp_path):
    """R1-7 回归：--round 与 --no-record 互斥须显式拒绝，而非静默零输出。"""
    repo = _repo(tmp_path)
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')
    r = _run(repo, '--slug=demo', '--round=r1', '--no-record', '--working')
    assert r.returncode != 0
    assert '互斥' in r.stderr


# --- 兼容壳（契约迁移：`.sh` 退役为 §2.2 转发壳）--------------------------------


@pytest.mark.skipif(sys.platform == 'win32' or shutil.which('bash') is None,
                    reason='POSIX 兼容壳仅在 POSIX + bash 环境可执行')
def test_compat_shim_forwards_to_python(tmp_path):
    """L4 壳等价性：`bash prepare-review-context.sh` 与 `.py` 退出码/stdout 必须一致。

    分别覆盖成功路径（归档脚手架）与失败路径（`--round` 空值），壳不得加工输出。
    两侧各用一个**全新仓库**：脚本会创建 `.review-context/` 与归档目录使工作区变脏，
    复用同一仓库会让后跑一侧的未跟踪文件清单不同（与被测实现无关）。
    """
    repo_py = _repo(_mk_repo_dir(tmp_path / 'via-py'))
    repo_sh = _repo(_mk_repo_dir(tmp_path / 'via-sh'))
    for repo in (repo_py, repo_sh):
        (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')

    via_py = subprocess.run([sys.executable, str(SCRIPT), '--slug=demo', '--working'],
                            cwd=repo_py, capture_output=True, text=True, encoding='utf-8')
    via_sh = subprocess.run(['bash', str(SHIM), '--slug=demo', '--working'],
                            cwd=repo_sh, capture_output=True, text=True, encoding='utf-8')
    assert via_sh.returncode == via_py.returncode == 0, via_sh.stderr
    assert via_sh.stdout == via_py.stdout

    err_py = subprocess.run([sys.executable, str(SCRIPT), '--slug=demo', '--round=', '--working'],
                            cwd=repo_py, capture_output=True, text=True, encoding='utf-8')
    err_sh = subprocess.run(['bash', str(SHIM), '--slug=demo', '--round=', '--working'],
                            cwd=repo_sh, capture_output=True, text=True, encoding='utf-8')
    assert err_sh.returncode == err_py.returncode == 1
    assert err_sh.stdout == err_py.stdout
    assert err_sh.stderr == err_py.stderr

