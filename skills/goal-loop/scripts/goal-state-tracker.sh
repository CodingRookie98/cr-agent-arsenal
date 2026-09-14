#!/usr/bin/env bash
# ==============================================================================
# goal-state-tracker.sh
# goal-loop 派生视图与计划文件编辑器
#
# 真相源：计划文件的复选框与 Active Checkpoint 锚点。
# 本脚本不维护并行状态文件；.goal-loop/plan.path 仅是指向计划文件的指针。
# 可用 GOAL_LOOP_ROOT 环境变量覆盖根目录（默认取 git 根，其次当前目录）。
# ==============================================================================
exec python3 - "$@" <<'PY'
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _git_root():
    try:
        out = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return None


REPO_ROOT = Path(os.environ.get('GOAL_LOOP_ROOT') or _git_root() or os.getcwd())
STATE_DIR = REPO_ROOT / '.goal-loop'
POINTER = STATE_DIR / 'plan.path'
SCRATCH = STATE_DIR / 'scratchpad.md'

PHASES = ['P-1', 'P0', 'P0.5', 'P1', 'P2', 'P3', 'P3.5', 'P4', 'P5', 'DONE']
FIELDS = ['当前执行通道', '当前活跃阶段', '当前活跃子任务', '当前子任务重试计数',
          '外层循环迭代', '最后一次验证状态', '最新有效提交']

TASK_RX = re.compile(
    r'^(\s*-\s*)\[([ xX])\](\s*\*\*(?:Task\s+)?)([A-Za-z][0-9A-Za-z]*(?:[.\-][0-9A-Za-z]+)+)(.*)$'
)


def field_rx(key):
    return re.compile(r'^(\s*(?:>\s*)?-\s*\*\*' + re.escape(key) + r'\*\*:\s*)(.*)$')


def die(msg, code=1):
    sys.stderr.write('❌ ' + msg + '\n')
    sys.exit(code)


def usage(code=0):
    print('''用法: goal-state-tracker.sh <子命令> [参数...]

真相源: 计划文件的复选框与 Active Checkpoint 锚点（本脚本不维护并行状态文件）。

子命令:
  init <目标名称> [计划文件路径]   绑定计划文件作为唯一可读真相源（缺省自动选取 plans 目录最新计划）
  status                          显示派生状态看板
  json                            以 JSON 输出派生状态
  set-phase <阶段代码>            更新检查点当前阶段 (P-1, P0, P0.5, P1, P2, P3, P3.5, P4, P5, DONE)
  set-current-task <任务标识>     更新检查点当前子任务
  complete-task <任务标识>        将计划中匹配的 - [ ] **Task <id>** 勾选为完成
  retry <n|n/max>                 更新当前子任务 3-Tries 重试计数
  block <原因>                    标记为熔断受阻并记录原因
  unblock                         解除阻断状态
  reset                           清除指针与临时文件（不删除计划文件）
  -h, --help                      显示本帮助信息''')
    sys.exit(code)


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def resolve_plan(strict=True):
    if not POINTER.is_file():
        if strict:
            die('未初始化：请先执行 init <目标名称> [计划文件路径]')
        return None
    raw = POINTER.read_text(encoding='utf-8').strip()
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    if strict and not p.is_file():
        die('计划文件不存在: %s' % p)
    return p


def read_lines(p):
    return p.read_text(encoding='utf-8').splitlines()


def write_lines(p, lines):
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    os.replace(tmp, p)


def get_field(lines, key):
    rx = field_rx(key)
    for ln in lines:
        m = rx.match(ln)
        if m:
            return m.group(2).strip()
    return ''


def set_field(lines, key, value):
    rx = field_rx(key)
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if m:
            lines[i] = m.group(1) + value
            return True
    return False


def norm(t):
    return re.sub(r'[^0-9a-z]', '', t.lower())


def task_progress(lines):
    total = done = 0
    for ln in lines:
        m = TASK_RX.match(ln)
        if m:
            total += 1
            if m.group(2).lower() == 'x':
                done += 1
    return done, total


def mutate(fn):
    p = resolve_plan()
    lines = read_lines(p)
    result = fn(lines)
    write_lines(p, lines)
    return result


def cmd_init(rest):
    if not rest:
        die('必须指定目标名称，如: init "订单结算重构" "docs/project/plans/2026-01-01-order.md"')
    plan_arg = rest[1] if len(rest) > 1 else None
    if plan_arg:
        plan = Path(plan_arg)
    else:
        cands = glob.glob(str(REPO_ROOT / 'docs' / 'project' / 'plans' / '*.md'))
        plan = (Path(sorted(cands, key=os.path.getmtime, reverse=True)[0]).relative_to(REPO_ROOT)
                if cands else Path('IMPLEMENTATION_PLAN.md'))
    p = Path(plan)
    if not p.is_absolute():
        p = REPO_ROOT / p
    if not p.is_file():
        die('计划文件不存在: %s\n请先用 templates/goal-plan-template.md 创建计划文件。' % p)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    POINTER.write_text(str(plan) + '\n', encoding='utf-8')
    print('✅ goal-loop 已绑定计划文件（唯一可读真相源）')
    print('📂 指针: %s' % POINTER)
    print('📋 计划: %s' % plan)
    print('🎯 目标: %s' % rest[0])
    print('🚀 当前阶段: %s' % (get_field(read_lines(p), '当前活跃阶段') or '—'))


def cmd_status():
    p = resolve_plan(strict=False)
    if p is None:
        print('⚠️ 未绑定计划文件。请运行 init <目标名称> [计划文件路径] 进行绑定。')
        return
    lines = read_lines(p)
    title = next((l.lstrip('#').strip() for l in lines if l.startswith('# ')), p.name)
    done, total = task_progress(lines)
    print('=' * 70)
    print('📊 goal-loop 状态看板（派生视图 · 真相源为计划文件）')
    print('=' * 70)
    print('📋 计划文件: %s' % (p.relative_to(REPO_ROOT) if str(p).startswith(str(REPO_ROOT)) else p))
    print('🎯 当前目标: %s' % title)
    for k in FIELDS:
        print('   %s: %s' % (k, get_field(lines, k) or '—'))
    print('✅ 任务进度: %d/%d' % (done, total))
    print('=' * 70)


def cmd_json():
    p = resolve_plan(strict=False)
    if p is None:
        print('{}')
        return
    lines = read_lines(p)
    done, total = task_progress(lines)
    print(json.dumps({
        'plan_file': str(p),
        'goal': next((l.lstrip('#').strip() for l in lines if l.startswith('# ')), p.name),
        'status': get_field(lines, '状态'),
        'phase': get_field(lines, '当前活跃阶段'),
        'current_task': get_field(lines, '当前活跃子任务'),
        'retry': get_field(lines, '当前子任务重试计数'),
        'iterations': get_field(lines, '外层循环迭代'),
        'last_verification': get_field(lines, '最后一次验证状态'),
        'last_commit': get_field(lines, '最新有效提交'),
        'task_done': done,
        'task_total': total,
        'updated_at': now(),
    }, ensure_ascii=False, indent=2))


def cmd_set_phase(rest):
    if not rest:
        die('必须指定阶段代码，如: set-phase P3')
    phase = rest[0]
    if phase not in PHASES:
        die('非法阶段代码: %s（可选: %s）' % (phase, ', '.join(PHASES)))
    mutate(lambda lines: set_field(lines, '当前活跃阶段', phase)
           or die('计划检查点缺少"当前活跃阶段"字段'))
    print('✅ 阶段已更新为: %s' % phase)


def cmd_set_current_task(rest):
    if not rest:
        die('必须指定任务标识，如: set-current-task P3.1')
    mutate(lambda lines: set_field(lines, '当前活跃子任务', rest[0])
           or die('计划检查点缺少"当前活跃子任务"字段'))
    print('✅ 当前子任务已更新为: %s' % rest[0])


def cmd_complete_task(rest):
    if not rest:
        die('必须指定任务标识，如: complete-task P3.1')
    target = norm(rest[0])
    found = {'hit': False, 'already': False}

    def apply(lines):
        for i, ln in enumerate(lines):
            m = TASK_RX.match(ln)
            if m and norm(m.group(4)) == target:
                found['hit'] = True
                if m.group(2).lower() == 'x':
                    found['already'] = True
                    return
                lines[i] = m.group(1) + '[x]' + m.group(3) + m.group(4) + m.group(5)
                set_field(lines, '当前活跃子任务', '无')
                return

    mutate(apply)
    if not found['hit']:
        die('未在计划中找到任务: %s' % rest[0])
    if found['already']:
        print('ℹ️ 任务 [%s] 早已完成。' % rest[0])
    else:
        print('✅ 子任务 [%s] 已勾选完成。' % rest[0])


def cmd_retry(rest):
    if not rest:
        die('必须指定重试计数，如: retry 1/3')
    mutate(lambda lines: set_field(lines, '当前子任务重试计数', rest[0])
           or die('计划检查点缺少"当前子任务重试计数"字段'))
    print('🔁 重试计数已更新为: %s' % rest[0])


def cmd_block(rest):
    reason = rest[0] if rest else '未知阻断'
    mutate(lambda lines: set_field(lines, '状态', '熔断受阻')
           or die('计划元数据缺少"状态"字段'))
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with SCRATCH.open('a', encoding='utf-8') as f:
        f.write('\n## [%s] 熔断受阻\n%s\n' % (now(), reason))
    print('⚠️ 状态机已标记为熔断受阻')
    print('📝 阻断原因: %s' % reason)
    print('🗒️ 已写入 Scratchpad: %s' % SCRATCH)


def cmd_unblock():
    mutate(lambda lines: set_field(lines, '状态', '进行中')
           or die('计划元数据缺少"状态"字段'))
    print('✅ 阻断已解除，状态恢复为进行中。')


def cmd_reset():
    removed = []
    for f in [POINTER, SCRATCH, STATE_DIR / 'state.json', STATE_DIR / '.tracker.lock']:
        if f.exists():
            f.unlink()
            removed.append(f.name)
    for f in glob.glob(str(STATE_DIR / 'state.json.*')):
        os.unlink(f)
        removed.append(os.path.basename(f))
    try:
        STATE_DIR.rmdir()
    except OSError:
        pass
    print('🧹 已清除指针与临时文件: %s' % (', '.join(removed) if removed else '无'))
    print('ℹ️ 计划文件未被删除（它才是真相源）。')


def main():
    argv = sys.argv[1:]
    if not argv:
        cmd_status()
        return
    cmd, rest = argv[0], argv[1:]
    table = {
        'init': cmd_init,
        'status': lambda _r: cmd_status(),
        'json': lambda _r: cmd_json(),
        'set-phase': cmd_set_phase,
        'set-current-task': cmd_set_current_task,
        'complete-task': cmd_complete_task,
        'retry': cmd_retry,
        'block': cmd_block,
        'unblock': lambda _r: cmd_unblock(),
        'reset': lambda _r: cmd_reset(),
        '-h': lambda _r: usage(0),
        '--help': lambda _r: usage(0),
    }
    if cmd not in table:
        sys.stderr.write("❌ 未知子命令 '%s'\n" % cmd)
        usage(1)
    table[cmd](rest)


main()
PY
