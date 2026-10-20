#!/usr/bin/env bash
# 兼容壳：保留既有调用面，转发到跨平台 Python 实现（同目录 scaffold-doc.py）。
set -euo pipefail
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/scaffold-doc.py" "$@"
