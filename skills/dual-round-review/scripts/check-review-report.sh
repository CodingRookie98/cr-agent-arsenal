#!/usr/bin/env bash
# ==============================================================================
# check-review-report.sh — 《审查归档》结构与证据校验器（dual-round-review 机械门禁）
#
# 定位：校验「归档索引完整 / 报告全文在位 / 指纹一致 / 两轮区块齐备 / 稳定 ID 对齐」。
#       不判断审查结论本身是否正确——结论正确性由两轮对抗与人类裁决负责。
#
# 契约（RFC-0001 §3.5）：
#   1) README.md 存在且含「交付单元 / 归档根 / 终审裁决」三个必需字段；
#   2) 轮次台账登记的每个报告文件实际存在且非空；
#   3) 台账登记的 SHA256 前 12 位与文件实际值一致（防篡改与转录漂移）；
#   4) R1 报告 5 个必需区块齐备，且不得仅出现在围栏代码块内；
#   5) R2 报告 3 个必需区块齐备（仅当台账含 R2 / delta-r2 行）；
#   6) 稳定 ID 对齐：R2 裁决明细表出现的 R1-<n> 必须全部存在于 R1 缺陷清单；
#   7) 可选 --require-verdict=PASS：终审裁决必须为「准予交付」。
#
# 用法: bash check-review-report.sh <归档目录> [--require-verdict=PASS]
# 退出码: 0 = 通过；1 = 结构/证据缺陷；2 = 用法错误
# ==============================================================================

set -euo pipefail

R1_SECTIONS=(
  "## 1. 第一性原理与本质溯源分析"
  "## 2. 运行时与 SSR/沙盒安全推演"
  "## 3. 红队攻击路径推演"
  "## 4. 潜在缺陷清单"
  "## 5. 第一轮结论概要"
)
R2_SECTIONS=(
  "## 1. 元审查辩证质询"
  "## 2. 最终裁决明细表"
  "## 3. 终审放行结论"
)
INDEX_FIELDS=("**交付单元**" "**归档根**" "**终审裁决**")
LEDGER_HEADER='## 轮次台账'

usage() {
  cat <<'EOF'
用法: check-review-report.sh <归档目录> [--require-verdict=PASS]

校验双轮审查《交付凭据归档》的结构与证据完整性。

选项:
      --require-verdict=PASS  要求索引「终审裁决」为「准予交付」（交付门禁用法）
  -h, --help                  显示本帮助

退出码:
  0 = 通过；1 = 结构/证据缺陷；2 = 用法错误

归档目录结构（推荐默认根 docs/project/reviews/）:
  README.md                   归档索引（交付单元 / 归档根 / 终审裁决 + 轮次台账）
  r1-<base>..<head>.md        R1 报告全文
  r2-<base>..<head>.md        R2 终审裁决书全文
EOF
}

if [[ "$#" -ge 1 && ( "$1" == "-h" || "$1" == "--help" ) ]]; then
  usage
  exit 0
fi

REQUIRE_VERDICT=""
ARGS=()
for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --require-verdict=*) REQUIRE_VERDICT="${arg#--require-verdict=}" ;;
    -*) echo "错误: 未知选项 '$arg'" >&2; usage >&2; exit 2 ;;
    *) ARGS+=("$arg") ;;
  esac
done

if [[ "${#ARGS[@]}" -ne 1 ]]; then
  echo "错误: 需要且仅需要一个归档目录参数" >&2
  usage >&2
  exit 2
fi

ARCHIVE="${ARGS[0]}"
if [[ ! -d "$ARCHIVE" ]]; then
  echo "错误: 归档目录不存在: $ARCHIVE" >&2
  exit 2
fi
if [[ -n "$REQUIRE_VERDICT" && "$REQUIRE_VERDICT" != "PASS" ]]; then
  echo "错误: --require-verdict 目前仅支持 PASS" >&2
  exit 2
fi

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -- "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 -- "$1" | awk '{print $1}'
  else
    echo "错误: 系统缺少 sha256sum / shasum，无法校验报告指纹" >&2
    exit 2
  fi
}

strip_fences() {
  awk 'BEGIN{f=0} /^[[:space:]]*```/{f=!f; next} f==0{print}' "$1"
}

FAIL=0
INDEX="$ARCHIVE/README.md"

# --- 1) 索引齐备 --------------------------------------------------------------
if [[ ! -f "$INDEX" ]]; then
  echo "错误: 归档缺少索引文件 README.md: $ARCHIVE"
  echo "结构校验未通过: $ARCHIVE"
  exit 1
fi
for field in "${INDEX_FIELDS[@]}"; do
  if ! grep -qF -- "$field" "$INDEX"; then
    echo "错误: 索引缺少必需字段: $field"
    FAIL=1
  fi
done

# --- 2)+3) 轮次台账：报告文件在位非空、指纹一致 -------------------------------
LEDGER="$(awk -v hdr="$LEDGER_HEADER" 'index($0, hdr)==1 {f=1; next} /^## /{f=0} f' "$INDEX" || true)"

ROWS="$(awk -F'|' '
  /^\|/ {
    r=$2; f=$5; h=$6
    gsub(/^[[:space:]]+/, "", r); gsub(/[[:space:]]+$/, "", r)
    gsub(/[^A-Za-z0-9._-]/, "", f)
    gsub(/[^0-9a-fA-F]/, "", h)
    if (r !~ /[A-Za-z0-9]/) next
    if (f == "") next
    print r "\t" f "\t" h
  }' <<<"$LEDGER" || true)"

R1_FILES=()
R2_FILES=()
REPORT_COUNT=0

while IFS=$'\t' read -r round fname declared; do
  [[ -z "$round" ]] && continue
  rfile="$ARCHIVE/$fname"
  if [[ ! -f "$rfile" ]]; then
    echo "错误: 台账登记的报告文件不存在: $fname（轮次 $round）"
    FAIL=1
    continue
  fi
  if [[ ! -s "$rfile" ]]; then
    echo "错误: 报告文件为空: $fname（轮次 $round）"
    FAIL=1
    continue
  fi
  actual="$(sha256_of "$rfile")"
  actual12="${actual:0:12}"
  if [[ -z "$declared" ]]; then
    echo "错误: 台账缺少 SHA256 登记: $fname（实际前 12 位 $actual12）"
    FAIL=1
  elif [[ "${declared,,}" != "${actual12,,}" ]]; then
    echo "错误: SHA256 指纹不一致: $fname 登记 $declared，实际 $actual12"
    FAIL=1
  fi

  REPORT_COUNT=$((REPORT_COUNT + 1))
  case "${round,,}" in
    r1|delta-r1) R1_FILES+=("$rfile") ;;
    r2|delta-r2) R2_FILES+=("$rfile") ;;
  esac
done <<<"$ROWS"

if [[ "$REPORT_COUNT" -eq 0 ]]; then
  echo "错误: 轮次台账为空或未按 schema 登记任何报告文件"
  FAIL=1
fi

# --- 4)+5) 报告必需区块齐备（围栏剥离后仍齐备） -------------------------------
check_sections() {
  local file="$1" label="$2"
  shift 2
  local sections=("$@")
  local fence_count body s
  fence_count="$(grep -cE -- '^[[:space:]]*```' "$file" || true)"
  fence_count="${fence_count:-0}"
  if [[ $((fence_count % 2)) -ne 0 ]]; then
    echo "错误: 围栏代码块未闭合（$label 围栏标记 $fence_count 个，应为偶数）"
    FAIL=1
  fi
  body="$(strip_fences "$file")"
  for s in "${sections[@]}"; do
    if ! grep -qF -- "$s" "$file"; then
      echo "错误: $label 缺少必需区块: $s"
      FAIL=1
    elif ! grep -qF -- "$s" <<<"$body"; then
      echo "错误: $label 必需区块仅出现在围栏代码块内（无效）: $s"
      FAIL=1
    fi
  done
}

for f in "${R1_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  check_sections "$f" "R1 报告（$(basename "$f")）" "${R1_SECTIONS[@]}"
done
for f in "${R2_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  check_sections "$f" "R2 报告（$(basename "$f")）" "${R2_SECTIONS[@]}"
done

if [[ "${#R1_FILES[@]}" -eq 0 ]]; then
  echo "错误: 台账未登记任何 R1 报告（r1 / delta-r1）"
  FAIL=1
fi

# --- 6) 稳定 ID 对齐：R2 裁决表的 R1-<n> 必须存在于 R1 缺陷清单 ---------------
section_ids() {
  local file="$1" header="$2"
  awk -v hdr="$header" 'index($0, hdr)==1 {f=1; next} /^## /{f=0} f' "$file" \
    | grep -oE 'R1-[0-9]+' | sort -u || true
}

R1_IDS=""
for f in "${R1_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  R1_IDS+="$(section_ids "$f" "## 4. 潜在缺陷清单")"$'\n'
done
R1_IDS="$(sort -u <<<"$R1_IDS" || true)"

for f in "${R2_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  while read -r id; do
    [[ -z "$id" ]] && continue
    if ! grep -qxF -- "$id" <<<"$R1_IDS"; then
      echo "错误: 稳定 ID 未在 R1 缺陷清单中定义: $id（出现在 $(basename "$f") 的裁决明细表）"
      FAIL=1
    fi
  done < <(section_ids "$f" "## 2. 最终裁决明细表")
done

# --- 7) 可选：终审裁决必须为「准予交付」 --------------------------------------
VERDICT_NOTE=""
if [[ "$REQUIRE_VERDICT" == "PASS" ]]; then
  VERDICT_LINE="$(grep -F -- '**终审裁决**' "$INDEX" | head -n 1 || true)"
  if [[ "$VERDICT_LINE" != *"准予交付"* ]]; then
    echo "错误: 终审裁决非「准予交付」，不满足 --require-verdict=PASS（登记: ${VERDICT_LINE:-未登记}）"
    FAIL=1
  else
    VERDICT_NOTE=" · 终审裁决 准予交付"
  fi
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "结构校验未通过: $ARCHIVE"
  exit 1
fi

echo "结构校验通过: 索引齐备 · 报告 $REPORT_COUNT 份 · 指纹一致 · 区块齐备 · 稳定 ID 对齐$VERDICT_NOTE"
exit 0
