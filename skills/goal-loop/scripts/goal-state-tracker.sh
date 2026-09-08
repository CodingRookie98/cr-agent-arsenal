#!/usr/bin/env bash
# ==============================================================================
# goal-state-tracker.sh
# goal-loop 目标实现循环技能轻量级状态追踪与断点恢复辅助 CLI
# 维护工作区 .goal-loop/state.json 状态机，保证跨会话、跨中断可恢复性
# ==============================================================================

set -euo pipefail

# 自动锚定工作区 Git 根目录，消除子目录调用陷阱
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
STATE_DIR="${REPO_ROOT}/.goal-loop"
STATE_FILE="${STATE_DIR}/state.json"
LOCK_FILE="${STATE_DIR}/.tracker.lock"

usage() {
  local exit_code="${1:-1}"
  cat <<EOF
用法: $(basename "$0") <子命令> [参数...]

子命令:
  init <目标名称> [计划文件路径]   初始化 goal-loop 状态机
  status                          显示当前状态（格式化看板）
  json                            以原生 JSON 格式输出当前状态
  set-phase <阶段代码>            切换当前阶段 (P-1, P0, P0.5, P1, P2, P3, P3.5, P4, P5, DONE)
  complete-task <任务标识>        将指定子任务标记为已完成
  block <受阻原因>                标记状态机处于熔断阻断状态并记录原因
  unblock                         解除当前阻断状态，恢复执行
  reset                           重置/清除当前工作区下的状态机
  -h, --help                      显示本帮助信息

阶段代码说明:
  P-1   阶段 -1:  意图探明与方案对齐 (brainstorming)
  P0    阶段 0:   方案压力测试与评估 (grilling)
  P0.5  阶段 0.5: 技术调研与开源选型 (research / find-docs)
  P1    阶段 1:   计划制定与测试定级 (writing-plans)
  P2    阶段 2:   原子子任务拆解
  P3    阶段 3:   TDD 循环实现 (agy-delegation-workflow)
  P3.5  阶段 3.5: 集成验证与回归
  P4    阶段 4:   E2E 验收与双轮终审 (dual-round-review)
  P5    阶段 5:   文档全向归档
  DONE  目标圆满达成

示例:
  $(basename "$0") init "订单结算系统重构" "docs/superpowers/plans/order.md"
  $(basename "$0") status
  $(basename "$0") set-phase P3
  $(basename "$0") complete-task "task-2.1"
  $(basename "$0") block "支付网关超时，连续 3 次单测失败"
EOF
  exit "$exit_code"
}

# 并发临界区排他锁保障
run_with_lock() {
  mkdir -p "$STATE_DIR"
  (
    flock -x 200
    "$@"
  ) 200>"$LOCK_FILE"
}

# 安全读取单个 JSON 字段（拒绝 eval()）
read_json_field() {
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -r "$field" "$STATE_FILE"
  else
    python3 -c '
import sys, json
field_name = sys.argv[1].lstrip(".").strip("[]").strip("\x27").strip("\"")
with open(sys.argv[2]) as f:
    d = json.load(f)
val = d.get(field_name, "")
print("" if val is None else val)
' "$field" "$STATE_FILE"
  fi
}

cmd_init_impl() {
  local goal_name="$1"
  local plan_file="$2"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local tmp_file
  tmp_file=$(mktemp -p "$STATE_DIR" state.json.XXXXXX)

  if command -v jq >/dev/null 2>&1; then
    jq -n \
      --arg goal "$goal_name" \
      --arg plan "$plan_file" \
      --arg now "$now" \
      '{
        goal: $goal,
        plan_file: $plan,
        phase: "P-1",
        status: "in_progress",
        blocked_reason: null,
        completed_tasks: [],
        current_task: null,
        created_at: $now,
        updated_at: $now
      }' > "$tmp_file"
  else
    python3 -c '
import sys, json
data = {
  "goal": sys.argv[1],
  "plan_file": sys.argv[2],
  "phase": "P-1",
  "status": "in_progress",
  "blocked_reason": None,
  "completed_tasks": [],
  "current_task": None,
  "created_at": sys.argv[3],
  "updated_at": sys.argv[3]
}
with open(sys.argv[4], "w") as f:
  json.dump(data, f, indent=2)
' "$goal_name" "$plan_file" "$now" "$tmp_file"
  fi

  mv -f "$tmp_file" "$STATE_FILE"

  echo "✅ goal-loop 状态机初始化完成！"
  echo "📂 状态文件: ${STATE_FILE}"
  echo "🎯 目标名称: ${goal_name}"
  echo "📋 关联计划: ${plan_file}"
  echo "🚀 当前阶段: P-1 (意图探明与方案对齐)"
}

cmd_init() {
  local goal_name="${1:-}"
  local plan_file="${2:-IMPLEMENTATION_PLAN.md}"
  if [[ -z "$goal_name" ]]; then
    echo "❌ 错误: 必须指定目标名称，如: $(basename "$0") init <目标名称>" >&2
    exit 1
  fi
  run_with_lock cmd_init_impl "$goal_name" "$plan_file"
}

cmd_status() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "⚠️ 未检测到当前工作区的 goal-loop 状态机文件 (${STATE_FILE})。"
    echo "💡 您可以运行 '$(basename "$0") init <目标名称>' 进行初始化。"
    return 0
  fi

  local goal phase status updated_at blocked_reason completed_count
  if command -v jq >/dev/null 2>&1; then
    goal=$(jq -r '.goal' "$STATE_FILE")
    phase=$(jq -r '.phase' "$STATE_FILE")
    status=$(jq -r '.status' "$STATE_FILE")
    updated_at=$(jq -r '.updated_at' "$STATE_FILE")
    blocked_reason=$(jq -r '.blocked_reason // empty' "$STATE_FILE")
    completed_count=$(jq '.completed_tasks | length' "$STATE_FILE")
  else
    goal=$(read_json_field ".goal")
    phase=$(read_json_field ".phase")
    status=$(read_json_field ".status")
    updated_at=$(read_json_field ".updated_at")
    blocked_reason=$(read_json_field ".blocked_reason")
    completed_count=$(python3 -c '
import sys, json
with open(sys.argv[1]) as f:
    d = json.load(f)
print(len(d.get("completed_tasks", [])))
' "$STATE_FILE")
  fi

  echo "======================================================================"
  echo "📊 goal-loop 目标执行状态看板"
  echo "======================================================================"
  echo "🎯 当前目标: ${goal}"
  echo "📍 执行阶段: ${phase}"
  echo "🚦 运行状态: ${status}"
  echo "✅ 已完任务: ${completed_count} 个"
  echo "🕒 最后更新: ${updated_at}"
  if [[ -n "$blocked_reason" && "$blocked_reason" != "null" ]]; then
    echo "⚠️ 阻断原因: ${blocked_reason}"
  fi
  echo "======================================================================"
}

cmd_json() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "{}"
    return 0
  fi
  cat "$STATE_FILE"
}

# 安全事务更新 JSON
apply_json_mutation() {
  local action="$1"
  local val="$2"
  local now
  now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local tmp_file
  tmp_file=$(mktemp -p "$STATE_DIR" state.json.XXXXXX)

  if command -v jq >/dev/null 2>&1; then
    case "$action" in
      set-phase)
        jq --arg p "$val" --arg t "$now" '.phase = $p | .updated_at = $t' "$STATE_FILE" > "$tmp_file"
        ;;
      complete-task)
        jq --arg tid "$val" --arg t "$now" '
          if (.completed_tasks | index($tid)) then . else .completed_tasks += [$tid] end
          | .current_task = null
          | .updated_at = $t
        ' "$STATE_FILE" > "$tmp_file"
        ;;
      block)
        jq --arg r "$val" --arg t "$now" '.status = "blocked" | .blocked_reason = $r | .updated_at = $t' "$STATE_FILE" > "$tmp_file"
        ;;
      unblock)
        jq --arg t "$now" '.status = "in_progress" | .blocked_reason = null | .updated_at = $t' "$STATE_FILE" > "$tmp_file"
        ;;
    esac
  else
    python3 -c '
import sys, json
state_file, action, val, now, tmp_file = sys.argv[1:6]
with open(state_file) as f:
    d = json.load(f)

if action == "set-phase":
    d["phase"] = val
elif action == "complete-task":
    if val not in d.get("completed_tasks", []):
        d.setdefault("completed_tasks", []).append(val)
    d["current_task"] = None
elif action == "block":
    d["status"] = "blocked"
    d["blocked_reason"] = val
elif action == "unblock":
    d["status"] = "in_progress"
    d["blocked_reason"] = None

d["updated_at"] = now
with open(tmp_file, "w") as f:
    json.dump(d, f, indent=2)
' "$STATE_FILE" "$action" "$val" "$now" "$tmp_file"
  fi

  mv -f "$tmp_file" "$STATE_FILE"
}

cmd_set_phase_impl() {
  local new_phase="$1"
  apply_json_mutation "set-phase" "$new_phase"
  echo "✅ 阶段已成功切换至: ${new_phase}"
}

cmd_set_phase() {
  local new_phase="${1:-}"
  if [[ -z "$new_phase" ]]; then
    echo "❌ 错误: 必须指定新的阶段代码，如: set-phase P3" >&2
    exit 1
  fi
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "❌ 错误: 状态机未初始化，请先执行 init。" >&2
    exit 1
  fi
  run_with_lock cmd_set_phase_impl "$new_phase"
}

cmd_complete_task_impl() {
  local task_id="$1"
  apply_json_mutation "complete-task" "$task_id"
  echo "✅ 子任务 [${task_id}] 已标记为完成！"
}

cmd_complete_task() {
  local task_id="${1:-}"
  if [[ -z "$task_id" ]]; then
    echo "❌ 错误: 必须指定完成的任务标识，如: complete-task task-2.1" >&2
    exit 1
  fi
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "❌ 错误: 状态机未初始化，请先执行 init。" >&2
    exit 1
  fi
  run_with_lock cmd_complete_task_impl "$task_id"
}

cmd_block_impl() {
  local reason="$1"
  apply_json_mutation "block" "$reason"
  echo "⚠️ 状态机已标记为阻断状态！"
  echo "📝 阻断原因: ${reason}"
}

cmd_block() {
  local reason="${1:-未知阻断}"
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "❌ 错误: 状态机未初始化，请先执行 init。" >&2
    exit 1
  fi
  run_with_lock cmd_block_impl "$reason"
}

cmd_unblock_impl() {
  apply_json_mutation "unblock" ""
  echo "✅ 阻断已解除，恢复为 in_progress 状态。"
}

cmd_unblock() {
  if [[ ! -f "$STATE_FILE" ]]; then
    echo "❌ 错误: 状态机未初始化，请先执行 init。" >&2
    exit 1
  fi
  run_with_lock cmd_unblock_impl
}

cmd_reset() {
  if [[ -d "$STATE_DIR" && "$STATE_DIR" == *".goal-loop"* ]]; then
    rm -f "${STATE_DIR}/state.json"* "${STATE_DIR}/.tracker.lock"
    rmdir "$STATE_DIR" 2>/dev/null || true
    echo "🧹 已安全重置并清除 ${STATE_DIR} 状态机。"
  fi
}

# 命令分发
if [[ $# -eq 0 ]]; then
  cmd_status
  exit 0
fi

case "$1" in
  init)
    shift
    cmd_init "$@"
    ;;
  status)
    cmd_status
    ;;
  json)
    cmd_json
    ;;
  set-phase)
    shift
    cmd_set_phase "$@"
    ;;
  complete-task)
    shift
    cmd_complete_task "$@"
    ;;
  block)
    shift
    cmd_block "$@"
    ;;
  unblock)
    cmd_unblock
    ;;
  reset)
    cmd_reset
    ;;
  -h|--help)
    usage 0
    ;;
  *)
    echo "❌ 错误: 未知子命令 '$1'" >&2
    usage 1
    ;;
esac
