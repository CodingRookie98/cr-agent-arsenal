#!/usr/bin/env bash
# ==============================================================================
# check-review-report.sh — 《审查归档》结构与证据校验器（dual-round-review 机械门禁）
#
# 定位：校验「归档索引完整 / 报告全文在位 / 指纹一致 / 两轮区块齐备 / 稳定 ID 对齐」。
#       不判断审查结论本身是否正确——结论正确性由两轮对抗与人类裁决负责。
#
# 契约（RFC-0001 §3.5）：
#   1) README.md 存在且含「交付单元 / 归档根 / 终审裁决」三个必需字段，
#      且 `**终审裁决**` 字段名在索引中**唯一**（BK-0004：命中数 ≠ 1 即缺陷）；
#   2) 轮次台账登记的每个报告文件实际存在且非空；
#   3) 台账登记的 SHA256 前 12 位与文件实际值一致（防篡改与转录漂移）；
#   4) R1 报告 5 个必需区块齐备，且不得仅出现在围栏代码块内；
#   5) R2 报告 3 个必需区块齐备（仅当台账含 R2 / delta-r2 行）；
#   6) 稳定 ID 对齐：R2 裁决明细表出现的 R1-<n> 必须全部存在于 R1 缺陷清单；
#      且该方向**按文件名基线逐轮配对**施加，并断言「R1 清单非空 ⇒ 同基线 R2 明细表非空」
#      （BK-0003：全局 ID 并集会让早轮 R2 行替新一轮顶包，空明细表静默放行）；
#   7) 可选 --require-verdict=PASS：终审裁决必须为「准予交付」；
#   8) 写入形态合法性：台账每行的「写入形态」列必须存在且取值 ∈ {direct, transcribed}
#      （RFC-0002 §3.5——该列是唯一能区分「子智能体直写原文」与「主智能体转录产物」的可审计属性）。
#   9) schema 自描述（2026-10-11 产物审查能力）：报告首部含 `> **Review Schema**: artifact` 时，
#      R1 按产物 schema 校验五区块与稳定 ID 区块；未声明则缺省 code —— 既有归档零迁移。
#  10) 轮次列容错（2026-10-11）：台账「轮次」列允许带人类描述（如 `delta-r1 · 第6轮`），
#      门禁按**前导标记值**解析；标记值之外的写法（如 `round-1`）仍判为未登记 R1。
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
# 产物 schema（Review Schema: artifact）——R2 三区块与稳定 ID 命名空间（R1-<n>）与 code 完全共用，
# 故仅 R1 五区块与 R1 稳定 ID 区块需要按 schema 切换。
R1_ARTIFACT_SECTIONS=(
  "## 1. 产物契约核验与意图溯源"
  "## 2. 事实与证据核验"
  "## 3. 失败预演与误用路径推演"
  "## 4. 指控清单"
  "## 5. 第一轮结论概要"
)
ARTIFACT_MARKER='> **Review Schema**: artifact'
CODE_R1_ID_SECTION='## 4. 潜在缺陷清单'
ARTIFACT_R1_ID_SECTION='## 4. 指控清单'
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

校验项 10：台账「轮次」列按前导标记值解析——允许带人类描述（如 `delta-r1 · 第6轮`），
  但标记值须为 r1 / r2 / delta-r1 / delta-r2 之一（如 `round-1` 判为未登记 R1）。

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

# schema 判定（第 9 项）：报告自描述，缺省 code。标记须为**行首整行**且不在围栏内，
# 否则视为未声明（防把标记写进示例代码块来切换校验口径）。
report_schema() {
  local file="$1"
  if strip_fences "$file" | grep -qxF -- "$ARTIFACT_MARKER"; then
    echo "artifact"
  else
    echo "code"
  fi
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

# BK-0004：`**终审裁决**` 必须**唯一**（命中数 ≠ 1 即缺陷）。第 7 项按首匹配取值，
# 索引顶部/围栏示例里的同名行会抢答真实字段——曾使标注「🔴 阻断交付」的归档在
# `--require-verdict=PASS` 下被误判为放行。此处只数命中数，不引入任何语义解析。
VERDICT_HITS="$(grep -cF -- '**终审裁决**' "$INDEX" || true)"
if [[ "$VERDICT_HITS" -ne 1 ]]; then
  echo "错误: 索引中 **终审裁决** 必须唯一（实测命中 $VERDICT_HITS 处；示例行/重复行不得抢答真实字段）"
  FAIL=1
fi

# --- 2)+3) 轮次台账：报告文件在位非空、指纹一致 -------------------------------
LEDGER="$(awk -v hdr="$LEDGER_HEADER" 'index($0, hdr)==1 {f=1; next} /^## /{f=0} f' "$INDEX" || true)"

ROWS="$(awk -F'|' '
  /^\|/ {
    r=$2; f=$5; h=$6
    # 末列为「写入形态」（R1-12 回归）：台账行以 | 结尾时存在空的尾随字段，故取 NF-1；
    # 未以 | 结尾时退回固定第 8 字段。这样结论单元格含裸竖线时也不会错位读取。
    m=(NF>=9) ? $(NF-1) : $8
    gsub(/^[[:space:]]+/, "", r); gsub(/[[:space:]]+$/, "", r)
    # 轮次列容错（第 10 项）：允许人类记述带描述（如 `delta-r1 · 第6轮`），只取前导标记值。
    # 该写法曾使 2026-10-10 归档自生成起即无法通过校验（先在数据侧规范、随后在此处容忍）；
    # `r1` / `r2` / `delta-r1` / `delta-r2` 之外的轮次仍判为未登记。
    if (match(r, /^(delta-r1|delta-r2|r1|r2)/)) r = substr(r, RSTART, RLENGTH)
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
  if [[ "$(report_schema "$f")" == "artifact" ]]; then
    check_sections "$f" "R1 报告（$(basename "$f")）" "${R1_ARTIFACT_SECTIONS[@]}"
  else
    fail_before="$FAIL"
    check_sections "$f" "R1 报告（$(basename "$f")）" "${R1_SECTIONS[@]}"
    if [[ "$FAIL" -ne "$fail_before" ]]; then
      echo "提示: 未发现 Review Schema 标记，按 code schema 校验；若本报告为产物审查，请在报告首部加入 '$ARTIFACT_MARKER' 后重跑。"
    fi
  fi
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
# 稳定 ID 抽取（BK-0003）：只认**该区块内「稳定 ID」契约表格的首列**。
# 旧实现把区块内任意文本里的 `R1-<n>` 都算作一条缺陷，于是「另一行说明列里的交叉引用」
# 会被当成缺陷清单——跨轮次污染（`DR1-7` 内含 `R1-7`、正文引用上一轮 ID）因此从并集
# 搬进配对里，配对后会报出并不存在的「未定性缺陷」。首列表述与模板契约一致，且
# `DR-<n>` / `DR1-<n>` 等 Delta 轮 ID 按字面保留，不参与任何跨命名空间解释。
section_ids() {
  local file="$1" header="$2"
  strip_fences "$file" | awk -v hdr="$header" '
    index($0, hdr) == 1 { sec = 1; next }
    /^## / { sec = 0 }
    !sec { next }
    !tbl {
      if ($0 ~ /^\|[[:space:]]*稳定 ID/) tbl = 1
      next
    }
    !/^\|/ { tbl = 0; next }
    {
      cell = $0
      sub(/^\|[[:space:]]*/, "", cell)
      sub(/[[:space:]]*\|.*$/, "", cell)
      if (cell ~ /^D?R1?-[0-9]+$/) print cell
    }' | sort -u || true
}

# 轮次配对键 = 报告文件名的**基线**段（`<前缀>-<base7>..<head7>.md` 的 <base7>）。
# R2 的 base 等于它所裁决的那一轮的 base（该轮的起点），故按 base 配对才能保证
# 「本轮 R1 由本轮 R2 定性」；全局 ID 并集会让早轮的 R2 行替新一轮顶包（BK-0003）。
base_key() {
  local b="${1##*/}"
  b="${b%.md}"
  b="${b#delta-}"
  b="${b#r1-}"; b="${b#r2-}"
  printf '%s' "${b%%..*}"
}

R1_IDS=""
R2_IDS=""
declare -A R1_BY_BASE=()
declare -A R2_BY_BASE=()
BASES=()

for f in "${R1_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  if [[ "$(report_schema "$f")" == "artifact" ]]; then
    ids="$(section_ids "$f" "$ARTIFACT_R1_ID_SECTION")"
  else
    ids="$(section_ids "$f" "$CODE_R1_ID_SECTION")"
  fi
  R1_IDS+="$ids"$'\n'
  key="$(base_key "$f")"
  [[ -n "${R1_BY_BASE[$key]:-}" ]] || BASES+=("$key")
  R1_BY_BASE[$key]+="$ids"$'\n'
done
R1_IDS="$(sort -u <<<"$R1_IDS" || true)"

for f in "${R2_FILES[@]:-}"; do
  [[ -z "$f" ]] && continue
  ids="$(section_ids "$f" "## 2. 最终裁决明细表")"
  R2_IDS+="$ids"$'\n'
  R2_BY_BASE["$(base_key "$f")"]+="$ids"$'\n'
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

# 方向二：**按基线逐轮配对**施加——R1 的每一条缺陷都必须被**同一轮**的 R2 定性
# （防元审判静默吞并阻断项，亦防跨轮顶包）。仅当台账登记了 R2 报告时适用——
# Light 模式为单轮红队，无 R2，不做此校验。
if [[ "${#R2_FILES[@]}" -gt 0 ]]; then
  for key in "${BASES[@]:-}"; do
    [[ -z "$key" ]] && continue
    round_r1="$(sort -u <<<"${R1_BY_BASE[$key]}" || true)"
    [[ -n "$round_r1" ]] || continue
    if [[ -z "${R2_BY_BASE[$key]:-}" ]]; then
      echo "错误: 基线 $key 的 R1 报告未配同基线 R2 报告（轮次未闭环，禁止靠他轮 R2 顶包放行）"
      FAIL=1
      continue
    fi
    round_r2="$(sort -u <<<"${R2_BY_BASE[$key]}" || true)"
    if [[ -z "$round_r2" ]]; then
      echo "错误: 基线 $key 的 R1 缺陷清单非空，但同基线 R2 裁决明细表为空（禁止空表放行）"
      FAIL=1
      continue
    fi
    while read -r id; do
      [[ -z "$id" ]] && continue
      if ! grep -qxF -- "$id" <<<"$round_r2"; then
        echo "错误: R1 缺陷 $id 未出现在**同基线** R2 裁决明细表中（禁止静默吞并；误报须显式登记为驳回项）"
        FAIL=1
      fi
    done <<<"$round_r1"
  done
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
