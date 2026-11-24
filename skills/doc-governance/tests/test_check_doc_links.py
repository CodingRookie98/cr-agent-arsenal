"""行为回归与边界测试：skills/doc-governance/scripts/check-doc-links.py。"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-doc-links.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_doc_links_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


cdl = _load_module()


def _run_cli(root: Path | None, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPT)]
    if root is not None:
        cmd.extend(["--root", str(root)])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_help_exits_zero():
    res = _run_cli(None, "--help")
    assert res.returncode == 0, res.stderr
    assert "--exclude" in res.stdout
    assert "--no-strict-ext" in res.stdout


def test_valid_links_anchors_and_duplicate_slug(tmp_path: Path):
    _write(
        tmp_path / "target.md",
        "# Target\n\n## Overview\nA\n\n## Overview\nB\n\n## 中文章节\nC\n",
    )
    _write(
        tmp_path / "source.md",
        "# Source\n\n## Local Sec\n\n"
        "- [Target](./target.md)\n"
        "- [First](./target.md#overview)\n"
        "- [Second](./target.md#overview-1)\n"
        "- [ZH](./target.md#中文章节)\n"
        "- [Self](#local-sec)\n"
        "- [Web](https://example.com/docs)\n",
    )
    res = _run_cli(tmp_path, "--verbose")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "共扫描 2 个 Markdown 文件" in res.stdout


def test_detects_404_and_missing_anchors(tmp_path: Path):
    _write(tmp_path / "target.md", "# Target\n\n## Real Heading\n")
    _write(
        tmp_path / "source.md",
        "# Source\n\n"
        "- [Missing](./ghost.md)\n"
        "- [Bad Remote Anchor](./target.md#absent)\n"
        "- [Bad Self Anchor](#missing-local)\n",
    )
    res = _run_cli(tmp_path)
    assert res.returncode == 1
    assert "404 Not Found" in res.stdout
    assert "未找到对应锚点 '#absent'" in res.stdout
    assert "当前文件内未找到锚点 '#missing-local'" in res.stdout


def test_missing_md_extension_strict_vs_relaxed(tmp_path: Path):
    target = _write(tmp_path / "target.md", "# Target\n")
    _write(tmp_path / "no_file.md", "- [Missing](./target)\n")
    r_missing = _run_cli(tmp_path)
    assert r_missing.returncode == 1
    assert "404 Not Found" in r_missing.stdout

    if not hasattr(os, "symlink"):
        pytest.skip("当前平台不支持 os.symlink")
    alias = tmp_path / "alias"
    try:
        os.symlink(target, alias)
    except OSError:
        pytest.skip("当前环境无创建符号链接权限")

    _write(tmp_path / "no_file.md", "- [Alias](./alias)\n")
    r_strict = _run_cli(tmp_path)
    assert r_strict.returncode == 1
    assert "缺失 '.md' 后缀" in r_strict.stdout

    r_relaxed = _run_cli(tmp_path, "--no-strict-ext")
    assert r_relaxed.returncode == 0, r_relaxed.stdout + r_relaxed.stderr


def test_inline_code_and_nested_fences_ignore_fake_links_and_headings(tmp_path: Path):
    _write(
        tmp_path / "doc.md",
        "# Title\n\n"
        "Inline `[a](./fake1.md)` and `` `[b](./fake2.md)` `` ignored.\n\n"
        "````markdown\n"
        "```\n"
        "# Fake Heading Inside Fence\n"
        "[fake3](./fake3.md)\n"
        "```\n"
        "````\n\n"
        "~~~~markdown\n"
        "~~~\n"
        "[fake4](./fake4.md)\n"
        "~~~\n"
        "~~~~\n\n"
        "- [Valid Self](./doc.md#title)\n",
    )
    res = _run_cli(tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr

    # 确认围栏内伪标题未污染锚点表，且围栏闭合后的真实断链仍被检出
    _write(
        tmp_path / "broken_after_fence.md",
        "# Top\n\n"
        "````md\n# Hidden\n```\n[ignore](./nope.md)\n````\n\n"
        "~~~md\n[ignore2](./nope2.md)\n~~~\n\n"
        "- [Hidden Anchor](#hidden)\n"
        "- [Real Broken](./real-missing.md)\n",
    )
    res2 = _run_cli(tmp_path)
    assert res2.returncode == 1
    assert "real-missing.md" in res2.stdout
    assert "当前文件内未找到锚点 '#hidden'" in res2.stdout
    assert "nope.md" not in res2.stdout and "nope2.md" not in res2.stdout


def test_directory_links_require_index_or_readme(tmp_path: Path):
    (tmp_path / "guide").mkdir()
    _write(tmp_path / "notes" / "README.md", "# Notes\n")
    _write(tmp_path / "root.md", "- [Guide](./guide/)\n- [Notes](./notes/)\n")

    r_fail = _run_cli(tmp_path)
    assert r_fail.returncode == 1
    assert "缺失 index.md/README.md" in r_fail.stdout

    _write(tmp_path / "guide" / "index.md", "# Guide\n")
    r_ok = _run_cli(tmp_path)
    assert r_ok.returncode == 0, r_ok.stdout + r_ok.stderr


def test_dir_scope_and_fail_closed_validation(tmp_path: Path):
    docs = tmp_path / "docs"
    _write(docs / "sub" / "ok.md", "# OK\n\n[Self](ok.md)\n")
    _write(docs / "other" / "bad.md", "[Bad](./missing.md)\n")
    _write(tmp_path / "outside" / "x.md", "# Outside\n")

    r_sub = _run_cli(docs, "--dir", "sub")
    assert r_sub.returncode == 0, r_sub.stdout + r_sub.stderr
    assert "共扫描 1 个 Markdown 文件" in r_sub.stdout

    r_escape = _run_cli(docs, "--dir", "../outside")
    assert r_escape.returncode == 2
    assert "越出根目录" in r_escape.stderr

    r_missing = _run_cli(docs, "--dir", "sub/nonexistent")
    assert r_missing.returncode == 2
    assert "不存在" in r_missing.stderr


def test_exclude_single_multiple_exact_segment_and_nonexistent(tmp_path: Path):
    _write(tmp_path / "index.md", "# Root\n")
    _write(tmp_path / "project" / "reviews" / "r1.md", "[Broken](./nope.md)\n")
    _write(tmp_path / "vendor" / "draft.md", "[Broken](./nope.md)\n")
    extra = _write(tmp_path / "project" / "reviews-extra" / "b.md", "[Broken](./gone.md)\n")

    # 精确路径段豁免：project/reviews 不得误豁免 project/reviews-extra
    r_boundary = _run_cli(tmp_path, "--exclude", "project/reviews", "--exclude", "vendor")
    assert r_boundary.returncode == 1
    assert "gone.md" in r_boundary.stdout
    assert "r1.md" not in r_boundary.stdout
    assert "draft.md" not in r_boundary.stdout

    extra.unlink()
    # 允许 --exclude 指向尚不存在但合法落在根内的相对前缀
    r_ok = _run_cli(
        tmp_path,
        "--exclude", "project/reviews",
        "--exclude", "vendor",
        "--exclude", "future/archive",
    )
    assert r_ok.returncode == 0, r_ok.stdout + r_ok.stderr
    assert "共扫描 1 个 Markdown 文件" in r_ok.stdout

    # 支持排除单文件且模块函数与 CLI 行为一致
    total, errs, _ = cdl.scan_directory(
        tmp_path, exclude_prefixes=["project/reviews", "vendor", "index.md"]
    )
    assert (total, errs) == (0, 0)


@pytest.mark.parametrize(
    "bad_prefix",
    ["", "   ", "/etc", "\\abs", "C:\\Windows", "../outside", "project/../../outside"],
)
def test_exclude_invalid_paths_fail_closed(tmp_path: Path, bad_prefix: str):
    _write(tmp_path / "index.md", "# Root\n")
    res = _run_cli(tmp_path, "--exclude", bad_prefix)
    assert res.returncode == 2, f"非法 --exclude={bad_prefix!r} 未 fail-closed: rc={res.returncode}"
    assert res.stderr.strip()


@pytest.mark.parametrize("root_alias", [".", "./", "sub/..", "dir/../."])
def test_exclude_root_self_rejected_fail_closed(tmp_path: Path, root_alias: str):
    _write(tmp_path / "index.md", "# Root\n\n[broken](./missing.md)\n")
    res = _run_cli(tmp_path, "--exclude", root_alias)
    assert res.returncode == 2, f"--exclude={root_alias!r} 应拦截禁止静默全跳: rc={res.returncode}"
    assert "根目录自身" in res.stderr
    with pytest.raises(ValueError, match="根目录自身"):
        cdl.scan_directory(tmp_path, exclude_prefixes=[root_alias])


def test_optional_llms_txt_root_scan(tmp_path: Path):
    _write(tmp_path / "sub" / "doc.md", "# Doc\n")
    assert _run_cli(tmp_path).returncode == 0

    llms = _write(tmp_path / "llms.txt", "- [Broken](sub/missing.md)\n")
    r_bad = _run_cli(tmp_path)
    assert r_bad.returncode == 1
    assert "llms.txt" in r_bad.stdout

    # --dir 收窄时不扫描根级 llms.txt
    assert _run_cli(tmp_path, "--dir", "sub").returncode == 0

    _write(llms, "- [Doc](sub/doc.md)\n")
    r_ok = _run_cli(tmp_path)
    assert r_ok.returncode == 0, r_ok.stdout + r_ok.stderr
    assert "共扫描 2 个 Markdown 文件" in r_ok.stdout
