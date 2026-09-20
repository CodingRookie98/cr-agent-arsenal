#!/usr/bin/env bash
# generate-seed.sh — 为 taste-driven-designer 生成设计灵感种子字符串
#
# 原理: String Seed of Thought (SSoT, Sakana AI) —— 随机性必须来自模型外部。
# 本脚本从 /dev/urandom 抽取真随机 base62 串, 供技能 Discover 阶段作为
# 创意方向的灵感来源; 提供确定性模式 (-s) 供团队共享同一设计方向。
set -euo pipefail

CHARSET="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
LENGTH=64
COUNT=1
SEED=""

usage() {
  cat <<'EOF'
用法: generate-seed.sh [-l LENGTH] [-c COUNT] [-s SEED]

生成 base62 字母数字字符串, 作为设计灵感的外部随机性种子 (String Seed of Thought)。

选项:
  -l LENGTH  种子字符串长度 (默认 64, 有效范围 8..1024)
  -c COUNT   生成条数 (默认 1, 有效范围 1..64)
  -s SEED    确定性模式: 以给定字符串为种子经 Park-Miller LCG 生成可复现输出;
             不传则从 /dev/urandom 取真随机 (每次运行结果不同)
  -h         显示本帮助

示例:
  bash generate-seed.sh                  # 64 位真随机种子
  bash generate-seed.sh -l 128 -c 3      # 3 条 128 位种子, 供多方向并行探索
  bash generate-seed.sh -s team-2026 -l 48   # 团队可复现同一设计方向
EOF
}

while getopts "l:c:s:h" opt; do
  case "$opt" in
    l) LENGTH="$OPTARG" ;;
    c) COUNT="$OPTARG" ;;
    s) SEED="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

# 参数边界校验
if ! [[ "$LENGTH" =~ ^[0-9]+$ ]] || [ "$LENGTH" -lt 8 ] || [ "$LENGTH" -gt 1024 ]; then
  echo "错误: -l 必须为 8..1024 的整数 (收到: $LENGTH)" >&2
  exit 2
fi
if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [ "$COUNT" -lt 1 ] || [ "$COUNT" -gt 64 ]; then
  echo "错误: -c 必须为 1..64 的整数 (收到: $COUNT)" >&2
  exit 2
fi

if [ -n "$SEED" ]; then
  # 确定性模式: 先把种子字符串按 CHARSET 索引哈希为初始状态,
  # 再用 Park-Miller LCG (a=48271, m=2^31-1) 生成可复现输出。
  # 乘积上限 ~1.04e14 < 2^53, awk 双精度运算精确无溢出。
  awk -v seed="$SEED" -v len="$LENGTH" -v count="$COUNT" -v cs="$CHARSET" 'BEGIN {
    m = 2147483647
    a = 48271
    h = 0
    n = length(seed)
    for (i = 1; i <= n; i++) {
      ch = substr(seed, i, 1)
      idx = index(cs, ch)
      if (idx == 0) v = 97; else v = idx - 1
      h = (h * 31 + v) % m
    }
    x = h
    for (k = 1; k <= count; k++) {
      s = ""
      for (j = 0; j < len; j++) {
        x = (a * x) % m
        p = (x % 62) + 1
        s = s substr(cs, p, 1)
      }
      print s
    }
  }'
else
  # 真随机模式: /dev/urandom -> base64 -> 过滤出 base62 字符, 不足则续取
  for ((k = 0; k < COUNT; k++)); do
    out=""
    while [ "${#out}" -lt "$LENGTH" ]; do
      chunk=$(head -c "$((LENGTH * 3))" /dev/urandom | base64 | tr -dc "$CHARSET")
      out="${out}${chunk}"
    done
    echo "${out:0:LENGTH}"
  done
fi
