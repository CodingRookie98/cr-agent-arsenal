#!/usr/bin/env bash
# ==============================================================================
# prepare-review-context.sh
# 辅助提取双轮审查所需的 Git Diff 与统计信息
# 支持工作区未提交审查 (--working)、暂存区审查 (--staged) 以及版本范围审查 (BASE...HEAD)
# ==============================================================================

set -euo pipefail

usage() {
  cat <<'EOF'
用法: prepare-review-context.sh [选项] [BASE_SHA [HEAD_SHA]]

提取双轮审查所需上下文，并生成审查记录锚点 .review-context/review-<baseline>.md

选项:
  -w, --working      审查工作区未提交改动（默认有改动时自动选择）
  -s, --staged       审查暂存区改动
      --no-record    只打印上下文，不写审查记录锚点
  -h, --help         显示本帮助

参数:
  BASE_SHA [HEAD_SHA]  审查指定提交区间（默认 BASE...HEAD）

记录锚点: .review-context/review-<baseline>.md（已 gitignore），供 Delta Re-Loop 读取 Previous Blockers 与迭代计数。
EOF
}

# 0. 帮助优先（无需位于 Git 仓库）
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# 1. 前置环境检查：必须在 Git 仓库工作区内运行
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ 错误: 当前目录并非 Git 工作区。" >&2
  exit 1
fi

MODE="range"
BASE_REF=""
HEAD_REF=""

# 2. 参数解析（选项顺序无关）
NO_RECORD=0
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    -h|--help) usage; exit 0 ;;
    -w|--working) MODE="working" ;;
    -s|--staged) MODE="staged" ;;
    --no-record) NO_RECORD=1 ;;
    -*) echo "❌ 错误: 未知选项 '${arg}'" >&2; usage >&2; exit 1 ;;
    *) POSITIONAL+=("${arg}") ;;
  esac
done

if [[ "${#POSITIONAL[@]}" -ge 2 ]]; then
  BASE_REF="${POSITIONAL[0]}"
  HEAD_REF="${POSITIONAL[1]}"
  MODE="range"
elif [[ "${#POSITIONAL[@]}" -eq 1 ]]; then
  BASE_REF="${POSITIONAL[0]}"
  HEAD_REF="HEAD"
  MODE="range"
elif [[ "${MODE}" != "working" && "${MODE}" != "staged" ]]; then
  # 未指定模式与区间时智能自适应：有改动优先未提交审查，否则检查最近一次提交
  DIRTY_COUNT=$(git status --porcelain | wc -l)
  if [[ "${DIRTY_COUNT}" -gt 0 ]]; then
    MODE="working"
  else
    COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
    if [[ "${COMMIT_COUNT}" -le 1 ]]; then
      MODE="root"
    else
      BASE_REF="HEAD~1"
      HEAD_REF="HEAD"
      MODE="range"
    fi
  fi
fi

echo "======================================================================"
echo "🔍 准备双轮审查上下文 (Dual-Round Review Context)"
echo "======================================================================"

case "${MODE}" in
  "working")
    RECORD_BASE="working"
    RECORD_HEAD="$(git rev-parse --short HEAD 2>/dev/null || echo none)"
    echo "📌 审查模式: 工作区变更审查 (Working Tree & Staged vs HEAD)"
    echo "----------------------------------------------------------------------"
    echo "📊 工作区未提交状态 (Git Status):"
    git status -s
    echo ""

    # 检测未跟踪文件并提供具体清单与建议
    UNTRACKED_FILES=$(git status -s | grep '^\?\?' | awk '{print $2}' || true)
    if [[ -n "${UNTRACKED_FILES}" ]]; then
      echo "⚠️ 发现未跟踪的新增文件 (Untracked Files):"
      echo "${UNTRACKED_FILES}"
      echo ""
      echo "💡 提示: Git 默认不对比未跟踪文件。若要审查新增代码，请先执行:"
      echo "   git add -N .   # 标记为 intent-to-add（不暂存内容，但使其可被 git diff 完整捕获）"
      echo "   然后再运行本脚本以生成完整 Diff。"
      echo ""
    fi

    echo "----------------------------------------------------------------------"
    echo "📊 变更统计 (Diff Stat vs HEAD):"
    git diff HEAD --stat || true
    echo ""
    echo "📋 变动文件清单:"
    git diff HEAD --name-only || true
    echo ""
    echo "💡 审查子智能体 Diff 命令建议:"
    echo "   git diff HEAD"
    ;;

  "staged")
    RECORD_BASE="staged"
    RECORD_HEAD="$(git rev-parse --short HEAD 2>/dev/null || echo none)"
    echo "📌 审查模式: 暂存区审查 (Staged / Cached vs HEAD)"
    echo "----------------------------------------------------------------------"
    echo "📊 暂存区变更统计 (Diff Stat --cached):"
    git diff --cached --stat
    echo ""
    echo "📋 暂存文件清单:"
    git diff --cached --name-only
    echo ""
    echo "💡 审查子智能体 Diff 命令建议:"
    echo "   git diff --cached"
    ;;

  "root")
    echo "📌 审查模式: 仓库初始提交审查 (Root Commit)"
    if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
      echo "⚠️ 当前分支尚无任何提交 (0 commits)。请先完成首次提交或添加工作区修改后再触发审查。"
      exit 0
    fi
    ROOT_COMMIT=$(git rev-list --max-parents=0 HEAD | head -n 1)
    RECORD_BASE="$(git rev-parse --short "${ROOT_COMMIT}")"
    RECORD_HEAD="${RECORD_BASE}"
    echo "Root Commit: ${ROOT_COMMIT}"
    echo ""
    echo "📊 初始提交统计:"
    git show --stat "${ROOT_COMMIT}"
    echo ""
    echo "💡 审查子智能体 Diff 命令建议:"
    echo "   git show ${ROOT_COMMIT}"
    ;;

  "range")
    # 严格校验必须为 Commit 对象（防止 Tree 或非 Commit 对象注入）
    if ! git rev-parse --verify "${BASE_REF}^{commit}" >/dev/null 2>&1; then
      echo "❌ 错误: 无效的 Base Commit Ref: ${BASE_REF}" >&2
      exit 1
    fi
    if ! git rev-parse --verify "${HEAD_REF}^{commit}" >/dev/null 2>&1; then
      echo "❌ 错误: 无效的 Head Commit Ref: ${HEAD_REF}" >&2
      exit 1
    fi

    BASE_SHA=$(git rev-parse "${BASE_REF}^{commit}")
    HEAD_SHA=$(git rev-parse "${HEAD_REF}^{commit}")
    RECORD_BASE="$(git rev-parse --short "${BASE_SHA}")"
    RECORD_HEAD="$(git rev-parse --short "${HEAD_SHA}")"

    echo "📌 审查模式: 提交区间审查 (${BASE_REF}...${HEAD_REF})"
    echo "Base SHA: ${BASE_SHA}"
    echo "Head SHA: ${HEAD_SHA}"
    echo ""

    # 检查工作区是否有未提交污染
    DIRTY_FILES=$(git status --porcelain)
    if [[ -n "${DIRTY_FILES}" ]]; then
      echo "⚠️ 提醒: 检测到工作区存在未提交变更（不包含在本次 commit 区间中）："
      echo "${DIRTY_FILES}"
      echo ""
    fi

    echo "----------------------------------------------------------------------"
    echo "📊 提交区间统计 (基于 Merge-Base 的三点式 Diff Stat):"
    git diff --stat "${BASE_SHA}...${HEAD_SHA}"
    echo ""

    echo "📝 包含的提交列表 (Commits on Head):"
    git log --oneline "${BASE_SHA}..${HEAD_SHA}"
    echo ""

    echo "📋 变动文件清单:"
    git diff --name-only "${BASE_SHA}...${HEAD_SHA}"
    echo ""

    echo "💡 审查子智能体 Diff 命令建议 (推荐三点式防止上游逆向污染):"
    echo "   git diff ${BASE_SHA}...${HEAD_SHA}"
    ;;
esac

# 3. 写入审查记录锚点（供 Delta Re-Loop 读取 Previous Blockers 与迭代计数）
if [[ "${NO_RECORD:-0}" -ne 1 ]]; then
  mkdir -p .review-context
  RECORD_FILE=".review-context/review-${RECORD_BASE:-unknown}.md"
  if [[ ! -f "${RECORD_FILE}" ]]; then
    cat > "${RECORD_FILE}" <<EOF
# 审查记录 · ${RECORD_BASE:-unknown}
- **模式**: [full | light | delta]
- **基线**: ${RECORD_BASE:-unknown}..${RECORD_HEAD:-unknown}
- **轮次**: [1 | 2 | ...]
- **迭代计数**: [0/3]
- **Previous Blockers**: 无
- **Round 1 结论**: [待填写]
- **终审裁决**: 未定
- **阻断项统计**: [🔴 0 / 🟡 0 / ⚪ 0]
EOF
    echo "📝 已生成审查记录锚点: ${RECORD_FILE}"
  else
    echo "📝 复用既有审查记录锚点: ${RECORD_FILE}"
  fi
fi

echo "----------------------------------------------------------------------"
echo "⛔ 边界锁与审查重点见 verdict-rubric.md §3 与 round-1-red-team.md；运行时/SSR 维度仅在 diff 触及客户端代码时激活。"
echo "======================================================================"

