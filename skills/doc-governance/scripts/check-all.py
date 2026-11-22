#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-all.py - 文档治理门禁聚合器（BK-0048）

按固定顺序运行五道门禁，任一失败即以非零退出码阻断，并给出可直接复制的修复命令。
设计目标：让「忘记跑门禁」不再是失败模式——pre-commit hook 与 CI 共用同一入口。

用法:
    python3 skills/doc-governance/scripts/check-all.py            # 五道门禁（快，<10s）
    python3 skills/doc-governance/scripts/check-all.py --full     # 追加 pytest 全量
    python3 skills/doc-governance/scripts/check-all.py --quiet    # 只输出失败项

退出码: 0 = 全绿；1 = 有门禁失败；2 = 用法/环境错误。
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[2]


def _run(name: str, cmd: List[str], fix: str) -> Tuple[str, bool, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return name, False, f"执行失败: {exc}"
    return name, proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="文档治理门禁聚合器")
    parser.add_argument("--root", default="docs", help="文档根目录（默认 docs）")
    parser.add_argument("--full", action="store_true", help="追加 pytest 全量测试")
    parser.add_argument("--quiet", action="store_true", help="只输出失败项")
    args = parser.parse_args()

    py = sys.executable
    root = args.root
    checks: List[Tuple[str, List[str], str]] = [
        (
            "机器地图",
            [py, str(SCRIPTS_DIR / "generate-llms-txt.py"), "--root", root,
             "--output", str(Path(root) / "llms.txt"), "--split", "--check"],
            f"{py} skills/doc-governance/scripts/generate-llms-txt.py --root {root} --output {root}/llms.txt --split",
        ),
        (
            "断链",
            [py, str(SCRIPTS_DIR / "check-doc-links.py"), "--root", root],
            "按输出逐条修复断链（相对路径必须保留 .md 后缀）",
        ),
        (
            "版本一致",
            [py, str(SCRIPTS_DIR / "check-doc-control-sync.py"), "--root", root],
            f"{py} skills/doc-governance/scripts/trim-revision.py --root {root} --fix --keep 5",
        ),
        (
            "真值轴",
            [py, str(SCRIPTS_DIR / "check-doc-drift.py"), "--root", root, "--repo", ".", "--fail-on-drift"],
            "复核锚点断言并刷新「复核于」；禁止删除锚点声明",
        ),
        (
            "健康体检",
            [py, str(SCRIPTS_DIR / "audit-doc-health.py"), "--root", root, "--repo", "."],
            "按体检报告逐项修复",
        ),
    ]
    if args.full:
        checks.append(
            ("测试套件", [py, "-m", "pytest", "skills/doc-governance/tests", "-q"], "修复失败用例")
        )

    failures = []
    for name, cmd, fix in checks:
        label, ok, output = _run(name, cmd, fix)
        if ok:
            if not args.quiet:
                print(f"✅ {label}")
        else:
            failures.append((label, output, fix))
            print(f"❌ {label}")

    if failures:
        print("\n" + "=" * 60)
        for label, output, fix in failures:
            print(f"\n【{label}】失败输出（尾部）:")
            tail = "\n".join(output.splitlines()[-12:])
            print(tail)
            print(f"→ 修复: {fix}")
        print("\n" + "=" * 60)
        print(f"🚫 门禁未通过：{len(failures)}/{len(checks)} 项失败")
        return 1

    if not args.quiet:
        print(f"\n🏁 全部门禁通过（{len(checks)} 项）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
