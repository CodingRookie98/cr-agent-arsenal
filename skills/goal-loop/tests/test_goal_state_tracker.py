import json
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'goal-state-tracker.sh'

PLAN = """# 测试目标 实施方案计划

> **目标元数据**
> - **状态**: 进行中

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P1 计划制定
- **当前活跃子任务**: 无
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 0/5
- **最后一次验证状态**: 无
- **最新有效提交**: 无

---

### P3: 核心功能原子实现 (TDD 循环)
- [ ] **Task P3.1**: 实现 A
- [ ] **Task P3.2**: 实现 B
"""

REL = 'docs/project/plans/2026-01-01-x.md'


def _run(tmp_path, *args):
    env = dict(os.environ, GOAL_LOOP_ROOT=str(tmp_path))
    return subprocess.run(['bash', str(SCRIPT), *args],
                          cwd=tmp_path, capture_output=True, text=True, env=env)


def _plan(tmp_path, rel=REL):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(PLAN, encoding='utf-8')
    return p


def test_init_rejects_missing_plan(tmp_path):
    r = _run(tmp_path, 'init', 'X', 'nope.md')
    assert r.returncode != 0
    assert '计划文件不存在' in (r.stdout + r.stderr)


def test_init_creates_pointer_not_statejson(tmp_path):
    _plan(tmp_path)
    r = _run(tmp_path, 'init', 'X', REL)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / '.goal-loop' / 'plan.path').is_file()
    assert not (tmp_path / '.goal-loop' / 'state.json').exists()


def test_status_derives_from_plan(tmp_path):
    _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    r = _run(tmp_path, 'status')
    assert r.returncode == 0, r.stderr
    assert 'P1 计划制定' in r.stdout
    assert '0/2' in r.stdout


def test_set_phase_writes_plan(tmp_path):
    p = _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    r = _run(tmp_path, 'set-phase', 'P3')
    assert r.returncode == 0, r.stderr
    assert '- **当前活跃阶段**: P3' in p.read_text(encoding='utf-8')


def test_set_phase_rejects_unknown(tmp_path):
    _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    assert _run(tmp_path, 'set-phase', 'P99').returncode != 0


def test_complete_task_normalizes_id(tmp_path):
    p = _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    r = _run(tmp_path, 'complete-task', 'p3-1')
    assert r.returncode == 0, r.stderr
    text = p.read_text(encoding='utf-8')
    assert '- [x] **Task P3.1**' in text
    assert '- [ ] **Task P3.2**' in text


def test_complete_task_unknown_fails(tmp_path):
    _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    assert _run(tmp_path, 'complete-task', 'P9.9').returncode != 0


def test_json_is_derived(tmp_path):
    _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    r = _run(tmp_path, 'json')
    data = json.loads(r.stdout)
    assert data['phase'] == 'P1 计划制定'
    assert data['task_total'] == 2
    assert data['task_done'] == 0


def test_block_and_unblock(tmp_path):
    p = _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    assert _run(tmp_path, 'block', '测试阻断').returncode == 0
    assert '熔断受阻' in p.read_text(encoding='utf-8')
    assert _run(tmp_path, 'unblock').returncode == 0


def test_reset_removes_pointer_and_keeps_plan(tmp_path):
    p = _plan(tmp_path)
    _run(tmp_path, 'init', 'X', REL)
    r = _run(tmp_path, 'reset')
    assert r.returncode == 0, r.stderr
    assert not (tmp_path / '.goal-loop' / 'plan.path').exists()
    assert p.is_file()
