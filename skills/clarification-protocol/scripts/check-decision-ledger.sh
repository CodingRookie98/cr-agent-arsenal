#!/usr/bin/env bash
# check-decision-ledger.sh — 决策台账结构校验器（离线 / 只读 / 无写入）。
#
# 定位：把 SKILL.md §3「决策台账」的三类登记纪律变成机械门禁，供 §4 收敛自检前使用。
# 不判断结论是否正确、依据是否成立（那是人的裁决），只校验**类别与必填字段是否登记**。
#
# 契约（与 references/decision-ledger.md、templates/decision-ledger-template.md 同源）：
#   1) 三类小节齐备：二级及以下标题恰为「已决项」「已排除边界」「默认假设」（允许形如 "## 3.1 已决项" 的编号前缀）；
#   2) 每个类别至少 1 条数据行；数据行 = 表格行且首个单元格是编号（形如 D-01 / E-02 / A-03）；
#   3) 已决项数据行必须含「出处」，已排除边界数据行必须含「排除依据」，默认假设数据行必须含「影响级别」；
#   4) 围栏代码块内的示例不计入（防止模板示例冒充真实登记）。
#
# 用法: bash check-decision-ledger.sh <决策台账 markdown 文件>
# 退出码: 0 = 合规；1 = 不合规（❌ 指明缺什么）；2 = 用法错误（缺参数 / 参数多于 1 个 / 文件不存在）

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: bash check-decision-ledger.sh <决策台账 markdown 文件>" >&2
  echo "错误: 需要且仅需要一个台账文件参数（实收 $# 个）" >&2
  exit 2
fi

LEDGER="$1"
if [[ ! -f "$LEDGER" ]]; then
  echo "错误: 台账文件不存在: $LEDGER" >&2
  exit 2
fi

AWK_RC=0
MESSAGES="$(
  awk '
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    BEGIN {
      cats[1] = "已决项"
      cats[2] = "已排除边界"
      cats[3] = "默认假设"
      req["已决项"] = "出处"
      req["已排除边界"] = "排除依据"
      req["默认假设"] = "影响级别"
      fence_mark = sprintf("%c%c%c", 96, 96, 96)
      in_fence = 0
      fail = 0
      cat = ""
    }
    index($0, fence_mark) > 0 { in_fence = !in_fence; next }
    in_fence { next }
    /^[#][#][#]*[[:space:]]/ {
      h = $0
      sub(/^[#]+[[:space:]]*/, "", h)
      sub(/^[0-9]+(\.[0-9]+)*[.]?[[:space:]]*/, "", h)
      h = trim(h)
      if (h in req) { cat = h; seen[h] = 1 } else { cat = "" }
      next
    }
    cat == "" { next }
    /^[[:space:]]*[|]/ {
      split($0, cells, /[|]/)
      id = trim(cells[2])
      if (id ~ /^[A-Za-z][A-Za-z0-9]*-[0-9]+$/) {
        count[cat]++
        if (index($0, req[cat]) == 0) {
          printf "❌ %s 行缺少「%s」: %s\n", cat, req[cat], trim($0)
          fail = 1
        }
      }
    }
    END {
      for (i = 1; i <= 3; i++) {
        c = cats[i]
        if (!(c in seen)) {
          printf "❌ 缺少「%s」小节（三类登记必须齐备）\n", c
          fail = 1
        } else if (count[c] + 0 == 0) {
          printf "❌ 「%s」小节没有数据行（编号形如 D-01）\n", c
          fail = 1
        }
      }
      exit (fail ? 1 : 0)
    }
  ' "$LEDGER"
)" || AWK_RC=$?

if [[ -n "$MESSAGES" ]]; then
  printf '%s\n' "$MESSAGES"
fi

if [[ "$AWK_RC" -eq 0 ]]; then
  echo "✅ 决策台账结构合规: $LEDGER"
  exit 0
fi

echo "❌ 决策台账结构不合规: $LEDGER（详见上方缺失项）" >&2
exit 1
