#!/usr/bin/env bash
# check-qa-report.sh — 《前端验收报告》结构校验器。
#
# 定位：qa-gate 的机械门禁。校验「报告结构完整性」与（可选）「结论为 PASS」，
# 不判断验收证据本身是否真实（证据真实性由独立复核与人类签收负责）。
#
# 契约：
#   1) 八个必需区块齐备，且不得仅出现在围栏代码块内（防围栏伪造）；
#   2) 五域标题各出现恰好一次（五域覆盖）；
#   3) 证据三态齐备（仅统计第 5 章）；
#   4) 明细断言数与结论表「五维合计」声明值一致，且不低于下限（默认 5，可用 --min-assertions 提高，最小 1）；
#   5) 未验证项一致性：结论表「未验证」列合计与「五维合计」声明必须相等；声明 > 0 时第 5 章必须列出具体项；
#      结论为 BLOCKED 时未验证数不得为 0；
#   6) 可选 --require-verdict=PASS：第 8 章必须声明「结论：PASS」（大小写归一，排除「建议结论」行），
#      结论表所有结论列必须为 PASS，第 4 章不得列出未验证项，第 5 章不得列出具体未验证项。
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
if ! [[ "$MIN_ASSERTIONS" =~ ^[0-9]+$ ]] || [[ "$MIN_ASSERTIONS" -lt 1 ]]; then
  echo "错误: --min-assertions 必须是 >=1 的整数: $MIN_ASSERTIONS" >&2
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

# 围栏必须成对闭合（未闭合 → 其后内容会被静默跳过，fail-closed 报错）
FENCE_COUNT="$(grep -cE -- '^[[:space:]]*```' "$REPORT" || true)"
if [[ $((FENCE_COUNT % 2)) -ne 0 ]]; then
  echo "错误: 围栏代码块未闭合（围栏标记 $FENCE_COUNT 个，应为偶数）"
  FAIL=1
fi

# 围栏代码块内的示例文本不参与结构判定（awk 状态机剥离后送入 stdin）
strip_fences() {
  awk 'BEGIN{f=0} /^[[:space:]]*```/{f=!f; next} f==0{print}'
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

# 章节区块提取（避免其它章节同名字样干扰）
TRI_SECTION="$(awk '/^## 5\. 证据三态标注/{f=1;next} /^## 6\./{f=0} f' <<<"$BODY")"
SEC4="$(awk '/^## 4\. 未验证项与阻断原因/{f=1;next} /^## 5\./{f=0} f' <<<"$BODY")"
SEC8="$(awk '/^## 8\. 签收/{f=1;next} f' <<<"$BODY")"

for state in "${TRI_STATES[@]}"; do
  if ! grep -qF -- "$state" <<<"$TRI_SECTION"; then
    echo "错误: 证据三态标注缺少状态: ${state%：}"
    FAIL=1
  fi
done

UNVERIFIED_LINES="$(grep -F -- "未验证：" <<<"$TRI_SECTION" | grep -vE -- '未验证：[[:space:]]*[（(]?无[）)]?[[:space:]]*$' || true)"

# 结论表「未验证」列合计（第 2 章区块，第 6 字段）与「五维合计」声明一致性
UNV_TOTAL="$(awk -F'|' '/^## 2\./{f=1;next} /^## 3\./{f=0} f && /^\|/ {v=$6; gsub(/[^0-9]/,"",v); if (v!="") s+=v} END{print s+0}' <<<"$BODY")"
DECLARED_UNV="$(grep -oE -- '未验证[[:space:]]*[0-9]+' <<<"$BODY" | grep -oE -- '[0-9]+' | head -1 || true)"
if [[ -n "$DECLARED_UNV" && "$DECLARED_UNV" -ne "$UNV_TOTAL" ]]; then
  echo "错误: 结论表未验证列合计 $UNV_TOTAL 与「五维合计」声明 $DECLARED_UNV 不一致"
  FAIL=1
fi
TOTAL_UNV="$UNV_TOTAL"
if [[ -n "$DECLARED_UNV" && "$DECLARED_UNV" -gt "$TOTAL_UNV" ]]; then TOTAL_UNV="$DECLARED_UNV"; fi
if [[ "${TOTAL_UNV:-0}" -gt 0 && -z "$UNVERIFIED_LINES" ]]; then
  echo "错误: 声明存在未验证项（$TOTAL_UNV）但第 5 章未列出具体未验证项"
  FAIL=1
fi
if grep -qiE -- '^[[:space:]]*-[[:space:]]*结论[：:][[:space:]]*BLOCKED' <<<"$SEC8" && [[ "${TOTAL_UNV:-0}" -eq 0 ]]; then
  echo "错误: 第 8 章结论为 BLOCKED 但结论表声明未验证 0 项（自相矛盾）"
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

# N/A 可追溯性：结论表出现 N/A 时，报告必须说明「未适用/不适用」理由（防滥用）
# N/A 域不得同时声明断言（防用 N/A 规避已存在的断言）
NA_BAD="$(awk -F'|' '/^## 2\./{f=1;next} /^## 3\./{f=0} f && /^\|/ {c=$7; gsub(/[[:space:]]/,"",c); if (toupper(c)=="N/A") {n=$3;p=$4;fl=$5; gsub(/[^0-9]/,"",n);gsub(/[^0-9]/,"",p);gsub(/[^0-9]/,"",fl); if ((n!=""&&n+0>0)||(p!=""&&p+0>0)||(fl!=""&&fl+0>0)) print c"("n"/"p"/"fl")"}}' <<<"$BODY" || true)"
if [[ -n "$NA_BAD" ]]; then
  echo "错误: 结论为 N/A 的域其断言数/通过数/失败数必须均为 0（实际: $(echo "$NA_BAD" | tr '\n' ' ')）"
  FAIL=1
fi

if grep -qiE -- '\|[[:space:]]*N/A[[:space:]]*\|' <<<"$BODY"; then
  if ! grep -qE -- '未适用|不适用' <<<"$SEC4$TRI_SECTION"; then
    echo "错误: 结论表存在 N/A 行但报告未说明「未适用/不适用」理由"
    FAIL=1
  fi
fi

# 可选结论校验：机械证明「结论为 PASS」（锚定第 8 章、大小写归一、排除建议结论行）
if [[ "$REQUIRE_VERDICT" == "PASS" ]]; then
  if ! grep -qiE -- '^[[:space:]]*-[[:space:]]*结论[：:][[:space:]]*PASS' <<<"$SEC8"; then
    echo "错误: 第 8 章未声明「结论：PASS」（--require-verdict=PASS 校验；建议结论行不计数）"
    FAIL=1
  fi
  if grep -qiE -- '^[[:space:]]*-[[:space:]]*结论[：:][[:space:]]*(FAIL|BLOCKED)' <<<"$SEC8"; then
    echo "错误: 第 8 章声明结论为 FAIL/BLOCKED，与 --require-verdict=PASS 冲突"
    FAIL=1
  fi
  BAD_ROWS="$(awk -F'|' '/^## 2\./{f=1;next} /^## 3\./{f=0} f && /^\|/ {c=$7; gsub(/[[:space:]]/,"",c); if (c!="" && c!="结论" && c!="---") print c}' <<<"$BODY" | grep -viE -- '^(PASS|N/A)$' || true)"
  if [[ -n "$BAD_ROWS" ]]; then
    echo "错误: 结论表存在非 PASS 结论: $(echo "$BAD_ROWS" | tr "\n" " ")"
    FAIL=1
  fi
  # 第 4 章内容判定：列表行宽松（含「未验证/阻断」实词且非「无…」否定式）；
  # 表格/引用行需带冒号实词（避免表头误判）；转折词与括号夹带一律视为有内容。
  # 第 4 章内容判定（统一 awk 判定，覆盖列表/表格/引用行）：
  #   1) 「- <实词>…：无」标准否定式白名单；
  #   2) 表头白名单（含 原因/说明/描述 且无冒号）；
  #   3) 循环抹除「否定词 + 实词（可连接重复）」配对后，残留实词即视为有内容。
  # 第 4 章内容判定（统一 awk 判定）：
  #   1) 表头白名单：含分隔符、无冒号、无数字，且所有单元格均为表头词；
  #   2) 循环抹除：① 「实词：无 + 终止符」短语（不整行跳过，防括号/标点夹带）；
  #                ② 「否定词（可带 任何/其它/其他/额外）+ 实词（可连接重复）」配对；
  #   3) 抹除至稳定后残留实词即视为有内容。
  OTHER4="$(awk '
    /^[[:space:]]*(-|\||>)/ {
      line=$0
      if (line ~ /[|｜]/ && line !~ /[：:]/ && line !~ /[0-9]/) {
        m=split(line, cells, /[|｜]/)
        allhdr=1
        for (j=1;j<=m;j++) {
          cc=cells[j]
          gsub(/^[[:space:]]+/, "", cc)
          gsub(/[[:space:]]+$/, "", cc)
          if (cc == "") continue
          if (cc !~ /(原因|说明|描述|项|编号|ID|Id|id)/) { allhdr=0; break }
        }
        if (allhdr) next
      }
      work=line
      for (k=0;k<10;k++) {
        before=work
        gsub(/(未验证项|未验证|阻断项|阻断|未测|未完成)[[:space:]]*[：:][[:space:]]*无([[:space:]]|（|\(|[，。；、]|$)/, "", work)
        gsub(/(无|没有|不存在|未出现)[[:space:]]*(任何|其它|其他|额外)?[[:space:]]*((未验证项|未验证|阻断项|阻断|未测|未完成|未跑|待测|待验证|尚未|未执行|未确认|未经测试|未覆盖|未审计|未回归|pending|TODO)[[:space:]]*([与和及、,，]?[[:space:]]*)?)+/, "", work)
        if (work==before) break
      }
      if (work ~ /未验证项|未验证|阻断项|阻断|未测|未完成|未跑|待测|待验证|尚未|未执行|未确认|未经测试|未覆盖|未审计|未回归|pending|TODO/) print $0
    }' <<<"$SEC4" || true)"
  if [[ -n "$OTHER4" ]]; then
    echo "错误: 结论为 PASS 但第 4 章列出了未验证项或阻断"
    FAIL=1
  fi
  if [[ -n "$UNVERIFIED_LINES" ]]; then
    echo "错误: 结论为 PASS 但第 5 章列出了具体未验证项"
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
