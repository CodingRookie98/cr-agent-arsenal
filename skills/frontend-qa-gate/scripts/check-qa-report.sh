#!/usr/bin/env bash
# check-qa-report.sh — 《前端验收报告》结构校验器。
#
# 定位：qa-gate 的机械门禁。只校验「报告是否具备可审查的结构与完整性」，
# 不判断验收结论是否正确（结论正确性由人工签收与 dual-round-review 终审负责）。
#
# 契约：
#   1) 八个必需区块齐备，且不得仅出现在围栏代码块内（防围栏伪造）；
#   2) 五域标题各出现恰好一次（五域覆盖，防止只验单一域即通过）；
#   3) 证据三态齐备；结论表声明存在未验证项时第 5 章必须逐条列出；
#   4) 明细断言数与结论表「五维合计」声明值一致（≥5）。
#
# 用法: bash check-qa-report.sh <报告文件路径>
# 退出码: 0 = 结构完整；1 = 结构缺陷；2 = 用法错误

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

if [[ $# -ne 1 ]]; then
  echo "usage: bash check-qa-report.sh <报告文件路径>" >&2
  exit 2
fi

REPORT="$1"
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

if [[ -z "$assert_count" || "$assert_count" -lt 5 ]]; then
  echo "错误: 五维断言明细不足（至少需要 5 条可判定断言，实际 $assert_count）"
  FAIL=1
fi

if [[ -z "$declared" ]]; then
  echo "错误: 结论表缺少「五维合计」断言行数声明"
  FAIL=1
elif [[ "$declared" -ne "$assert_count" ]]; then
  echo "错误: 结论表声明断言 $declared 条，明细实际 $assert_count 条，合计不一致"
  FAIL=1
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "结构校验未通过: $REPORT"
  exit 1
fi

echo "结构校验通过: 断言 $assert_count 条 · 五域覆盖 · 三态齐备 · 必需区块齐备"
exit 0
