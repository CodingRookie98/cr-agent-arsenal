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
#   7) 可选 --require-verdict=PASS：终审裁决必须为「准予交付」；
#   8) 写入形态合法性：台账每行的「写入形态」列必须存在且取值 ∈ {direct, transcribed}
#      （RFC-0002 §3.5——该列是唯一能区分「子智能体直写原文」与「主智能体转录产物」的可审计属性）。
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

校验项 8：台账「写入形态」列必须存在且取值 ∈ {direct, transcribed}
  （RFC-0002 §3.5；缺失或第三值均判失败）

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

# 围栏剥离状态机：反引号与波浪号围栏**均**需识别（R1-4 回归——仅识别反引号时，
# 单个 ~~~ 即可把全部区块藏进代码块并绕过结构校验）。
strip_fences() {
  awk 'BEGIN{f=0} /^[[:space:]]*(```|~~~)/{f=!f; next} f==0{print}' "$1"
}

# 区块判定：必须为**行首标题**，行内散文提及不算（R1-4 回归）。
heading_present() {
  awk -v s="$2" 'index($0, s)==1 {found=1; exit} END{exit !found}' "$1"
}
heading_present_stdin() {
  awk -v s="$1" 'index($0, s)==1 {found=1; exit} END{exit !found}'
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
    # 末列为「写入形态」（R1-12 回归）：台账行以 | 结尾时存在空的尾随字段，故取 NF-1；
    # 未以 | 结尾时退回固定第 8 字段。这样结论单元格含裸竖线时也不会错位读取。
    m=(NF>=9) ? $(NF-1) : $8
    gsub(/^[[:space:]]+/, "", r); gsub(/[[:space:]]+$/, "", r)
    gsub(/^[[:space:]]+/, "", m); gsub(/[[:space:]]+$/, "", m)
    gsub(/[^A-Za-z0-9._-]/, "", f)
    gsub(/[^0-9a-fA-F]/, "", h)
    if (r !~ /[A-Za-z0-9]/) next
    if (f == "") next
    print r "\t" f "\t" h "\t" m
  }' <<<"$LEDGER" || true)"

R1_FILES=()
R2_FILES=()
REPORT_COUNT=0

while IFS=$'\t' read -r round fname declared write_mode; do
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

  # --- 8) 写入形态合法性（RFC-0002 §3.5） -------------------------------------
  if [[ -z "${write_mode}" ]]; then
    echo "错误: 台账缺少「写入形态」登记: ${fname}（轮次 ${round}；取值须为 direct 或 transcribed）"
    FAIL=1
  elif [[ "${write_mode}" != "direct" && "${write_mode}" != "transcribed" ]]; then
    echo "错误: 写入形态取值非法: ${fname} 登记 '${write_mode}'（合法值仅 direct / transcribed）"
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
  fence_count="$(grep -cE -- '^[[:space:]]*(```|~~~)' "$file" || true)"
  fence_count="${fence_count:-0}"
  if [[ $((fence_count % 2)) -ne 0 ]]; then
    echo "错误: 围栏代码块未闭合（$label 围栏标记 $fence_count 个，应为偶数）"
    FAIL=1
  fi
  body="$(strip_fences "$file")"
  for s in "${sections[@]}"; do
    if ! heading_present "$file" "$s"; then
      echo "错误: $label 缺少必需区块（须为行首标题）: $s"
      FAIL=1
    elif ! heading_present_stdin "$s" <<<"$body"; then
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
  strip_fences "$file" \
    | awk -v hdr="$header" 'index($0, hdr)==1 {f=1; next} /^## /{f=0} f' \
    | grep -oE 'R1-[0-9]+' | sort -u || true
}

R1_IDS=""
for f in "${R1_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  R1_IDS+="$(section_ids "$f" "## 4. 潜在缺陷清单")"$'\n'
done
R1_IDS="$(sort -u <<<"$R1_IDS" || true)"

R2_IDS=""
for f in "${R2_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  R2_IDS+="$(section_ids "$f" "## 2. 最终裁决明细表")"$'\n'
done
R2_IDS="$(sort -u <<<"$R2_IDS" || true)"

# 方向一：R2 裁决表出现的 ID 必须在 R1 缺陷清单中定义（防凭空引入）
while read -r id; do
  [[ -z "$id" ]] && continue
  if ! grep -qxF -- "$id" <<<"$R1_IDS"; then
    echo "错误: 稳定 ID 未在 R1 缺陷清单中定义: $id（出现在 R2 裁决明细表）"
    FAIL=1
  fi
done <<<"$R2_IDS"

# 方向二：R1 的每一条缺陷都必须被 R2 定性（防元审判静默吞并阻断项）
# 仅当台账登记了 R2 报告时适用——Light 模式为单轮红队，无 R2，不做此校验。
if [[ "${#R2_FILES[@]}" -gt 0 && -n "$R1_IDS" ]]; then
  while read -r id; do
    [[ -z "$id" ]] && continue
    if ! grep -qxF -- "$id" <<<"$R2_IDS"; then
      echo "错误: R1 缺陷 $id 未出现在 R2 裁决明细表中（禁止静默吞并；误报须显式登记为驳回项）"
      FAIL=1
    fi
  done <<<"$R1_IDS"
fi

# --- 7) 可选：终审裁决必须为「准予交付」 --------------------------------------
VERDICT_NOTE=""
if [[ "$REQUIRE_VERDICT" == "PASS" ]]; then
  # 精确字段值判定：剥离 "- **终审裁决**:" 前缀、首尾空白与可选 ✅ 后，值必须**恰好等于**「准予交付」。
  # 严禁子串包含判定——RFC §3.4 的占位符串与否定式串自身即含 PASS 词元（R1-1 回归）。
  VERDICT_LINE="$(grep -F -- '**终审裁决**' "$INDEX" | head -n 1 || true)"
  VERDICT_VAL="$(printf '%s' "$VERDICT_LINE" | sed -e 's/^.*\*\*终审裁决\*\*:[[:space:]]*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  VERDICT_VAL="${VERDICT_VAL#✅}"
  VERDICT_VAL="$(printf '%s' "$VERDICT_VAL" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  if [[ "$VERDICT_VAL" != "准予交付" ]]; then
    echo "错误: 终审裁决字段值必须精确等于「准予交付」（实际: '${VERDICT_VAL:-未登记}'；含该词元的占位符/否定式串不成立）"
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
