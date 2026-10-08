#!/usr/bin/env bash
# ==============================================================================
# prepare-review-context.sh
# 辅助提取双轮审查所需的 Git Diff 与统计信息
# 支持工作区未提交审查 (--working)、暂存区审查 (--staged) 以及版本范围审查 (BASE...HEAD)
# ==============================================================================

set -euo pipefail

# 交付凭据归档辅助函数（RFC-0001 §3.2 / §3.3）

# 解析归档目录：复用既有同 slug 目录（Delta 再循环跨天不分裂），否则按当天日期新建
resolve_archive_dir() {
  local root="$1" slug="$2" existing
  existing="$(ls -d "${root}"/*-"${slug}" 2>/dev/null | sort | tail -n 1 || true)"
  if [[ -n "${existing}" ]]; then
    echo "${existing}"
  else
    echo "${root}/$(date +%Y-%m-%d)-${slug}"
  fi
}

# 锚点内「归档索引」段：存在则先移除旧段再追加，保证幂等
upsert_archive_index() {
  local file="$1" archive_dir="$2"
  if grep -qF '## 归档索引' "${file}"; then
    awk '/^## 归档索引/{skip=1;next} /^## /{skip=0} !skip' "${file}" > "${file}.tmp"
    mv "${file}.tmp" "${file}"
  fi
  {
    echo ""
    echo "## 归档索引 (Archive Index)"
    echo "- **归档根**: ${archive_dir}"
    echo "- **轮次台账**: ${archive_dir}README.md"
  } >> "${file}"
}

usage() {
  cat <<'EOF'
用法: prepare-review-context.sh [选项] [BASE_SHA [HEAD_SHA]]

提取双轮审查所需上下文，并生成审查记录锚点 .review-context/review-<baseline>.md

选项:
  -w, --working      审查工作区未提交改动（默认有改动时自动选择）
  -s, --staged       审查暂存区改动
      --no-record    只打印上下文，不写审查记录锚点与归档目录
      --slug=<slug>  启用交付凭据归档 scaffold（RFC-0001）；不传则仅生成运行时锚点
      --round=<轮次>  输出本轮「预授权报告目标路径」（RFC-0002 子智能体直写通道）；
                     取值 r1|r2|delta-r1|delta-r2，必须与 --slug 同时使用
      --archive-root=<路径>
                     归档根（默认 docs/project/reviews，仅与 --slug 联动）
  -h, --help         显示本帮助

参数:
  BASE_SHA [HEAD_SHA]  审查指定提交区间（默认 BASE...HEAD）

记录锚点: .review-context/review-<baseline>.md（已 gitignore），供 Delta Re-Loop 读取 Previous Blockers 与迭代计数。
交付凭据归档: 传 --slug 时另在 <archive-root>/<YYYY-MM-DD>-<slug>/ 生成归档索引 README.md（进版本库，
              供人类与子智能体阅读报告全文）；复用既有同 slug 目录，Delta 再循环不新建。
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
SLUG=""
ROUND=""
ARCHIVE_ROOT="docs/project/reviews"
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    -h|--help) usage; exit 0 ;;
    -w|--working) MODE="working" ;;
    -s|--staged) MODE="staged" ;;
    --no-record) NO_RECORD=1 ;;
    --slug=*) SLUG="${arg#--slug=}" ;;
    --round=*) ROUND="${arg#--round=}" ;;
    --archive-root=*) ARCHIVE_ROOT="${arg#--archive-root=}" ;;
    -*) echo "❌ 错误: 未知选项 '${arg}'" >&2; usage >&2; exit 1 ;;
    *) POSITIONAL+=("${arg}") ;;
  esac
done

# 2.1 归档参数校验（RFC-0001 §3.3：slug 采用小写 kebab-case）
if [[ -n "${SLUG}" && ! "${SLUG}" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "❌ 错误: --slug 必须为小写 kebab-case（^[a-z0-9][a-z0-9-]*$）: ${SLUG}" >&2
  exit 1
fi

# 2.2 轮次参数校验（RFC-0002 §3.2 路径预授权：目标路径依赖归档目录，故必须与 --slug 同用）
if [[ -n "${ROUND}" ]]; then
  if [[ -z "${SLUG}" ]]; then
    echo "❌ 错误: --round 必须与 --slug 同时使用（报告目标路径依赖归档目录）" >&2
    exit 1
  fi
  case "${ROUND}" in
    r1|r2|delta-r1|delta-r2) ;;
    *) echo "❌ 错误: --round 取值必须为 r1|r2|delta-r1|delta-r2，实际: ${ROUND}" >&2
       exit 1 ;;
  esac
fi

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

  # 3.1 交付凭据归档 scaffold（RFC-0001 §3.2/§3.3；未传 --slug 时完全不介入）
  if [[ -n "${SLUG}" ]]; then
    ARCHIVE_DIR="$(resolve_archive_dir "${ARCHIVE_ROOT}" "${SLUG}")"
    if ! mkdir -p "${ARCHIVE_DIR}"; then
      echo "❌ 错误: 无法创建归档目录: ${ARCHIVE_DIR}" >&2
      exit 1
    fi
    ARCHIVE_INDEX="${ARCHIVE_DIR}/README.md"
    if [[ ! -f "${ARCHIVE_INDEX}" ]]; then
      cat > "${ARCHIVE_INDEX}" <<EOF
# 审查归档 · ${SLUG}

> **文档控制信息**
> - **文档标识**: REVIEW-ARCHIVE-${SLUG}
> - **当前版本**: V1.0.0
> - **维护负责人**: 主调度智能体
> - **生效日期**: $(date +%Y-%m-%d)

- **交付单元**: ${SLUG}
- **归档根**: ${ARCHIVE_DIR}/
- **审查模式**: [full | light | delta]
- **当前迭代计数**: [0/3]
- **终审裁决**: 未定（取值必须**精确**为 准予交付 / 阻断交付 / 未定 三者之一；禁止保留占位符方括号或附加解释）

## 轮次台账
| 轮次 | 基线 | 派发句柄 | 报告文件 | SHA256(前 12 位) | 结论 |
| :--- | :--- | :--- | :--- | :--- | :--- |

## 报告清单
> 每轮归档后在此追加一行 markdown 链接，供人类与子智能体按路径直达：
> - [<报告文件>](./<报告文件>)

## 待办与后续轮次
- [ ] 待第一次审查派发后登记
EOF
      echo "📦 已生成归档索引: ${ARCHIVE_INDEX}"
    else
      echo "📦 复用既有归档索引: ${ARCHIVE_INDEX}"
    fi
    upsert_archive_index "${RECORD_FILE}" "${ARCHIVE_DIR}/"
    echo "📦 归档根已登记至锚点: ${ARCHIVE_DIR}/"

    # 3.2 预授权报告目标路径（RFC-0002 §3.2）：派发提示词内联该字面值，
    #     子智能体不得自选/推断/改写路径；目标文件一律**不预创建**（Write-Once 保护）。
    if [[ -n "${ROUND}" ]]; then
      REPORT_PATH="${ARCHIVE_DIR}/${ROUND}-${RECORD_BASE:-unknown}..${RECORD_HEAD:-unknown}.md"
      echo "📄 本轮报告目标路径 (预授权写入面): ${REPORT_PATH}"
      if [[ -e "${REPORT_PATH}" ]]; then
        echo "⚠️ 目标文件已存在（Write-Once 保护）: ${REPORT_PATH}"
        echo "   ↳ 视为基线漂移缺陷，严禁覆盖；请排查命名冲突后再派发。"
      fi
    fi
  fi
fi

echo "----------------------------------------------------------------------"
echo "⛔ 边界锁与审查重点见 verdict-rubric.md §3 与 round-1-red-team.md；运行时/SSR 维度仅在 diff 触及客户端代码时激活。"
echo "======================================================================"

