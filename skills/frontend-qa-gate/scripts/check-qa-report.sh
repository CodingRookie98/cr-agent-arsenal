#!/usr/bin/env bash
# check-qa-report.sh — 《前端验收报告》结构校验器。
#
# 定位：qa-gate 的机械门禁。只校验「报告是否具备可审查的结构与完整性」，
# 不判断验收结论是否正确（结论正确性由人工签收与 dual-round-review 终审负责）。
# 契约：① 必需区块齐备；② 证据三态标注齐备；③ 明细断言数与结论表「五维合计」
#       声明值一致；④ 围栏代码块内的示例文本不计入证据统计。
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
  if ! grep -qF "$section" "$REPORT"; then
    echo "错误: 缺少必需区块: $section"
    FAIL=1
  fi
done

# 围栏代码块内的示例文本不参与统计（awk 状态机剥离后送入 stdin）
strip_fences() {
  awk 'BEGIN{f=0} /^```/{f=!f; next} f==0{print}'
}

BODY="$(strip_fences < "$REPORT")"

for state in "${TRI_STATES[@]}"; do
  if ! grep -qF "$state" <<<"$BODY"; then
    echo "错误: 证据三态标注缺少状态: ${state%：}"
    FAIL=1
  fi
done

assert_count="$(grep -cE '^[[:space:]]*-[[:space:]]*\[[ xX]\]' <<<"$BODY" || true)"
declared="$(grep -oE '断言[[:space:]]*[0-9]+' <<<"$BODY" | grep -oE '[0-9]+' | head -1 || true)"

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

echo "结构校验通过: 断言 $assert_count 条 · 三态齐备 · 必需区块齐备"
exit 0
