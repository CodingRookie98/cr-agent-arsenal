#!/usr/bin/env bash
# check-qa-report.sh — 《前端验收报告》结构校验器。
#
# 定位：qa-gate 的机械门禁。校验「报告结构完整性」与（可选）「结论为 PASS」，
# 不判断验收证据本身是否真实（证据真实性由独立复核与人类签收负责）。
#
# 契约：
#   1) 八个必需区块齐备，且不得仅出现在围栏代码块内（防围栏伪造）；
#   2) 五域标题各出现恰好一次（五域覆盖）；
#   3) 证据三态齐备（仅统计第 5 章）；结论为 BLOCKED 时第 5 章必须列出具体未验证项；
#   4) 明细断言数与结论表「五维合计」声明值一致，且不低于下限（默认 5，可用 --min-assertions 提高）；
#   5) 可选 --require-verdict=PASS：声明结论必须为 PASS，且不得出现 FAIL/BLOCKED。
#
# 用法: bash check-qa-report.sh <报告文件> [--require-verdict=PASS] [--min-assertions=N]
# 退出码: 0 = 通过；1 = 结构/结论缺陷；2 = 用法错误

set -euo pipefail

REQUIRED_SECTIONS=(
  "## 1. 验收范围"
  "## 2. 断言结论表"
  "## 3. 五维断言明细"
  "## 4. 未验证项与阻断原因"
  "## 5. 证据三态标注"
  "## 6. 回流路由"
  "## 7. 全流程命令顺序"
  "## 8. 签收"
)
DOMAIN_TITLES=(
  "### 3.1 响应式视口断言"
  "### 3.2 交互状态断言"
  "### 3.3 无障碍断言"
  "### 3.4 浏览器覆盖断言"
  "### 3.5 性能断言"
)
TRI_STATES=("已实现：" "已运行验证：" "未验证：")

REQUIRE_VERDICT=""
MIN_ASSERTIONS=5
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --require-verdict=*) REQUIRE_VERDICT="${arg#--require-verdict=}" ;;
    --min-assertions=*) MIN_ASSERTIONS="${arg#--min-assertions=}" ;;
    *) ARGS+=("$arg") ;;
  esac
done

if [[ ${#ARGS[@]} -ne 1 ]]; then
  echo "usage: bash check-qa-report.sh <报告文件> [--require-verdict=PASS] [--min-assertions=N]" >&2
  exit 2
fi
if ! [[ "$MIN_ASSERTIONS" =~ ^[0-9]+$ ]]; then
  echo "错误: --min-assertions 必须是非负整数: $MIN_ASSERTIONS" >&2
  exit 2
fi
if [[ -n "$REQUIRE_VERDICT" && "$REQUIRE_VERDICT" != "PASS" ]]; then
  echo "错误: --require-verdict 目前仅支持 PASS" >&2
  exit 2
fi

REPORT="${ARGS[0]}"
if [[ ! -f "$REPORT" ]]; then
  echo "错误: 报告文件不存在: $REPORT" >&2
  exit 2
fi

FAIL=0

for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -qF -- "$section" "$REPORT"; then
    echo "错误: 缺少必需区块: $section"
    FAIL=1
  fi
done

# 围栏代码块内的示例文本不参与结构判定（awk 状态机剥离后送入 stdin）
strip_fences() {
  awk 'BEGIN{f=0} /^```/{f=!f; next} f==0{print}'
}

BODY="$(strip_fences < "$REPORT")"

for section in "${REQUIRED_SECTIONS[@]}"; do
  if ! grep -qF -- "$section" <<<"$BODY"; then
    echo "错误: 必需区块仅出现在围栏代码块内（无效）: $section"
    FAIL=1
  fi
done

for domain in "${DOMAIN_TITLES[@]}"; do
  hits="$(grep -cF -- "$domain" <<<"$BODY" || true)"
  if [[ "$hits" -ne 1 ]]; then
    echo "错误: 五域覆盖不完整: $domain 出现 $hits 次（要求恰好 1 次）"
    FAIL=1
  fi
done

# 仅取第 5 章（证据三态标注）区块，避免其它章节同名字样干扰判定
TRI_SECTION="$(awk '/^## 5\. 证据三态标注/{f=1;next} /^## 6\./{f=0} f' <<<"$BODY")"

for state in "${TRI_STATES[@]}"; do
  if ! grep -qF -- "$state" <<<"$TRI_SECTION"; then
    echo "错误: 证据三态标注缺少状态: ${state%：}"
    FAIL=1
  fi
done

# 结论为 BLOCKED 时，第 5 章必须列出具体未验证项（排除「未验证：无」这类空声明）
UNVERIFIED_LINES="$(grep -F -- "未验证：" <<<"$TRI_SECTION" | grep -vE -- '未验证：[[:space:]]*无[[:space:]]*$' || true)"
if [[ -z "$UNVERIFIED_LINES" ]] && grep -qF -- "BLOCKED" <<<"$BODY"; then
  echo "错误: 结论为 BLOCKED 但第 5 章未列出任何具体未验证项"
  FAIL=1
fi

assert_count="$(grep -cE -- '^[[:space:]]*-[[:space:]]*\[[ xX]\]' <<<"$BODY" || true)"
declared="$(grep -oE -- '断言[[:space:]]*[0-9]+' <<<"$BODY" | grep -oE -- '[0-9]+' | head -1 || true)"

if [[ -z "$assert_count" || "$assert_count" -lt "$MIN_ASSERTIONS" ]]; then
  echo "错误: 五维断言明细不足（下限 $MIN_ASSERTIONS，实际 $assert_count）"
  FAIL=1
fi

if [[ -z "$declared" ]]; then
  echo "错误: 结论表缺少「五维合计」断言行数声明"
  FAIL=1
elif [[ "$declared" -ne "$assert_count" ]]; then
  echo "错误: 结论表声明断言 $declared 条，明细实际 $assert_count 条，合计不一致"
  FAIL=1
fi

# 可选结论校验：机械证明「结论为 PASS」而非仅结构完整
if [[ "$REQUIRE_VERDICT" == "PASS" ]]; then
  if ! grep -qE -- '结论[：:][[:space:]]*PASS' <<<"$BODY"; then
    echo "错误: 报告未声明结论为 PASS（--require-verdict=PASS 校验）"
    FAIL=1
  fi
  if grep -qE -- '结论[：:][[:space:]]*(FAIL|BLOCKED)' <<<"$BODY"; then
    echo "错误: 报告声明结论为 FAIL/BLOCKED，与 --require-verdict=PASS 冲突"
    FAIL=1
  fi
  if grep -qE -- '\|[[:space:]]*(FAIL|BLOCKED)[[:space:]]*\|' <<<"$BODY"; then
    echo "错误: 结论表存在 FAIL/BLOCKED 行，与 --require-verdict=PASS 冲突"
    FAIL=1
  fi
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "结构校验未通过: $REPORT"
  exit 1
fi

VERDICT_NOTE=""
if [[ "$REQUIRE_VERDICT" == "PASS" ]]; then VERDICT_NOTE=" · 结论 PASS"; fi
echo "结构校验通过: 断言 $assert_count 条（下限 $MIN_ASSERTIONS） · 五域覆盖 · 三态齐备 · 必需区块齐备${VERDICT_NOTE}"
exit 0
