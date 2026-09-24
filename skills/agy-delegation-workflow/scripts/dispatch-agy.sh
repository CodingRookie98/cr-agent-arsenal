#!/usr/bin/env bash
# ==============================================================================
# dispatch-agy.sh
# 辅助分发 agy (Antigravity CLI) 后台执行任务的标准调度脚本
# 自动清理 WSL/Linux 代理变量、注入 Gemini 3.8 Flash 模型与安全超时参数
# ==============================================================================

set -euo pipefail

DEFAULT_MODEL="Gemini 3.8 Flash (High)"
MODEL="${AGY_MODEL:-$DEFAULT_MODEL}"
TIMEOUT="20m"
BACKGROUND=false
TASK_FILE=""
PROMPT_TEXT=""

# 帮助信息
usage() {
  local exit_code="${1:-1}"
  cat <<EOF
用法: $(basename "$0") [选项] <任务Prompt文件或提示词>

选项:
  -f, --file <path>     指定任务提示词文件 (.agy-tasks/task.md)
  -p, --prompt <text>   直接指定单行任务描述文本
  -m, --model <name>    指定执行模型 (默认: ${DEFAULT_MODEL})
  -t, --timeout <time>  指定无头超时时间 (默认: ${TIMEOUT})
  -b, --background      后台执行并在完成后输出日志提示
  -h, --help            显示本帮助信息

示例:
  $(basename "$0") -f .agy-tasks/task-a.md -b
  $(basename "$0") -p "为 src/utils/math.ts 补充 100% 单元测试"
EOF
  exit "$exit_code"
}

# 解析参数
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)
      TASK_FILE="$2"
      shift 2
      ;;
    -p|--prompt)
      PROMPT_TEXT="$2"
      shift 2
      ;;
    -m|--model)
      MODEL="$2"
      shift 2
      ;;
    -t|--timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    -b|--background)
      BACKGROUND=true
      shift
      ;;
    -h|--help)
      usage 0
      ;;
    *)
      if [[ -z "$TASK_FILE" && -f "$1" ]]; then
        TASK_FILE="$1"
      elif [[ -z "$PROMPT_TEXT" ]]; then
        PROMPT_TEXT="$1"
      else
        echo "❌ 错误: 未知参数 $1" >&2
        usage
      fi
      shift
      ;;
  esac
done

# 校验 agy CLI 是否存在
if ! command -v agy >/dev/null 2>&1; then
  echo "❌ 错误: 系统中未找到 'agy' (Antigravity CLI) 可执行文件。请确认已安装并加入 PATH。" >&2
  exit 1
fi

# 获取提示词内容
CONTENT=""
if [[ -n "$TASK_FILE" ]]; then
  if [[ ! -f "$TASK_FILE" ]]; then
    echo "❌ 错误: 任务提示词文件不存在: $TASK_FILE" >&2
    exit 1
  fi
  CONTENT=$(cat "$TASK_FILE")
elif [[ -n "$PROMPT_TEXT" ]]; then
  CONTENT="$PROMPT_TEXT"
else
  echo "❌ 错误: 必须通过 -f <文件> 或 -p <文本> 指定任务内容。" >&2
  usage
fi

# ------------------------------------------------------------------------------
# 修正工作目录与 Hindsight 记忆库归属 (bank attribution)
#
# 实测结论（勿删）：agy 无头模式 (`agy -p`) 下没有 active workspace，
#   1) hook 事件里的 workspacePaths 是空数组 []；
#   2) agy 给 hook / MCP server 子进程的 cwd 固定为 ~/.gemini/config，而非 agy 自身 cwd。
# 两者叠加使 bank 模板 `coding-agent::{gitProject}` 回退成目录 basename，
# 整批会话都会被写进 `coding-agent::config`（实测误收 75 个文档 / 3,237 条记忆单元，横跨 6 个仓库）。
# 修复：用 --add-dir 把仓库根注册为会话 workspace（agy 会填进 workspacePaths，
# hook 据此解析 bank），并用 HINDSIGHT_MCP_PROJECT_CWD 让 MCP server 解析到同一目录。
# ------------------------------------------------------------------------------
REPO_ROOT=""
if [[ -n "$TASK_FILE" ]]; then
  REPO_ROOT=$(git -C "$(dirname "$TASK_FILE")" rev-parse --show-toplevel 2>/dev/null || true)
elif git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel)
fi

if [[ -n "$REPO_ROOT" ]]; then
  cd "$REPO_ROOT"
  export HINDSIGHT_MCP_PROJECT_CWD="$REPO_ROOT"
  AGY_WORKSPACE_ARGS=(--add-dir "$REPO_ROOT")
  echo "📂 记忆库归属根目录: ${REPO_ROOT}"
else
  AGY_WORKSPACE_ARGS=()
  echo "⚠️  警告: 未能定位 git 仓库根 —— Hindsight 的 bank 会退化为目录名" >&2
  echo "           (coding-agent::$(basename "$PWD"))。请先 cd 到项目仓库根，或用 -f 指定仓库内的任务文件。" >&2
fi

# 1. 彻底清除代理环境变量，杜绝 WSL/Linux 下的 Go 客户端 proxyconnect connection refused
unset HTTPS_PROXY HTTP_PROXY http_proxy https_proxy ALL_PROXY all_proxy || true

echo "======================================================================"
echo "🚀 启动 agy 后台执行任务"
echo "======================================================================"
echo "📌 执行模型: ${MODEL}"
echo "⏱️  超时时限: ${TIMEOUT}"
echo "📂 工作目录: $(pwd)"
echo "----------------------------------------------------------------------"

if [[ "$BACKGROUND" == true ]]; then
  LOG_DIR=".agy-tasks/logs"
  mkdir -p "$LOG_DIR"
  LOG_FILE="${LOG_DIR}/agy-$(date +%Y%m%d-%H%M%S)-$$.log"
  echo "📡 后台执行模式已激活，日志输出至: ${LOG_FILE}"
  
  nohup agy ${AGY_WORKSPACE_ARGS[@]+"${AGY_WORKSPACE_ARGS[@]}"} -p "$CONTENT" \
    --model "$MODEL" \
    --dangerously-skip-permissions \
    --print-timeout "$TIMEOUT" > "$LOG_FILE" 2>&1 &
  
  PID=$!
  echo "✅ agy 任务已在后台启动 (PID: ${PID})"
  echo "💡 提示: 您可以使用 'tail -f ${LOG_FILE}' 实时跟踪执行进展。"
else
  # 前台同步执行
  exec agy ${AGY_WORKSPACE_ARGS[@]+"${AGY_WORKSPACE_ARGS[@]}"} -p "$CONTENT" \
    --model "$MODEL" \
    --dangerously-skip-permissions \
    --print-timeout "$TIMEOUT"
fi
