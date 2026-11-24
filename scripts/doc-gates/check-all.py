#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-all.py - 本仓文档治理门禁聚合器

按固定顺序运行三道门禁（断链 / 健康体检 / 可回答性），任一失败即以非零退出码阻断，
并给出可直接复制的修复命令。pre-commit hook 与 CI 共用同一入口。

用法:
    python3 scripts/doc-gates/check-all.py            # 三道门禁
    python3 scripts/doc-gates/check-all.py --full     # 追加 pytest 全量测试
    python3 scripts/doc-gates/check-all.py --quiet    # 仅输出失败项

退出码: 0 = 全绿；1 = 有门禁失败；2 = 用法/环境错误。
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[1]


def _run(name: str, cmd: List[str], fix: str) -> Tuple[str, bool, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return name, False, f"执行失败: {exc}"
    return name, proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def _build_checks(py: str, root: str, full: bool) -> List[Tuple[str, List[str], str]]:
    checks: List[Tuple[str, List[str], str]] = [
        (
            "断链",
            [py, str(REPO_ROOT / "skills/doc-governance/scripts/check-doc-links.py"),
             "--root", root, "--exclude", "project/reviews"],
            "按输出逐条修复断链（相对路径必须保留 .md 后缀）",
        ),
        (
            "健康体检",
            [py, str(SCRIPTS_DIR / "check-doc-health.py"), "--root", root, "--quiet"],
            f"{py} scripts/doc-gates/check-doc-health.py --root {root}",
        ),
        (
            "可回答性",
            [py, str(SCRIPTS_DIR / "check-golden-tasks.py"), "--root", root, "--quiet"],
            "FAIL 项按输出修复；GAP 项为真实知识缺口，登记 backlog 而非当场补写",
        ),
    ]
    if full:
        checks.append(
            ("测试套件", [py, "-m", "pytest", "skills/", "scripts/", "-q"], "按失败用例输出修复")
        )
    return checks


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    parser = argparse.ArgumentParser(description="本仓文档治理门禁聚合器（三道门禁：断链 / 健康体检 / 可回答性）")
    parser.add_argument("--root", default="docs", help="文档根目录（默认 docs）")
    parser.add_argument("--full", action="store_true", help="追加 pytest 全量测试（skills/ 与 scripts/）")
    parser.add_argument("--quiet", action="store_true", help="只输出失败项，全绿零输出")
    args = parser.parse_args()

    checks = _build_checks(sys.executable, args.root, args.full)
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
            print("\n".join(output.splitlines()[-12:]))
            print(f"→ 修复: {fix}")
        print("\n" + "=" * 60)
        print(f"🚫 门禁未通过：{len(failures)}/{len(checks)} 项失败")
        return 1

    if not args.quiet:
        print(f"\n🏁 全部门禁通过（{len(checks)} 项）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
