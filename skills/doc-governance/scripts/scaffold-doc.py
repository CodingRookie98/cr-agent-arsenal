#!/usr/bin/env python3
"""scaffold-doc.py - Diátaxis & RFC 标准文档脚手架自动化生成器（跨平台 Python 实现）。

移植自 skills/doc-governance/scripts/scaffold-doc.sh，行为逐字节对齐（stdout/stderr/
退出码/产物文件内容）。用法：
    python3 scaffold-doc.py <type> <name> [--root docs] [--lang zh|en]
类型 (<type>)：
    tutorial    - 新手上门教程 (docs/tutorials/)
    how-to      - 任务操作指南 (docs/how-to/)
    reference   - 权威技术参考 (docs/reference/)
    explanation - 深度架构剖析 (docs/explanation/)
    adr         - 架构决策记录 (docs/explanation/decisions/000X-name.md)
    rfc         - 需求与设计提案 (docs/proposals/RFC-000X-name.md)
    backlog     - 技术债/任务卡片 (docs/project/backlog/active/BK-000X-name.md)

兼容性说明：POSIX 下旧 .sh 调用仍可用（skills/doc-governance/scripts/scaffold-doc.sh
为兼容壳，转发到本实现）。
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from datetime import date

USAGE_TYPES = "<tutorial|how-to|reference|explanation|adr|rfc|backlog> <doc-name> [--root docs] [--lang zh|en]"

# 原实现 heredoc 中 `${NAME}` / `${SEQ_PADDED}` 等占位符，Python 侧用同名 token 渲染。
TUTORIAL_TEMPLATE = """# ${NAME} 新手上路指南 (Tutorial)

> **文档控制信息**
> - **文档标识**: TUT-${NAME_UPPER}-${YEAR}
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: ${TODAY}
> - **文档所有者**: AI Agent / 工程师

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | ${TODAY} | AI Agent | 架构师 | 初始化新手上路教程脚手架 |

---

## 1. 学习目标 (What You'll Learn)
完成本教程后，你将能够：
1. 搭建最小运行环境；
2. 运行首个核心业务链路；
3. 验证端到端交付结果。

## 2. 前置准备 (Prerequisites)
- 环境依赖说明（如 Node.js >= 20, Python >= 3.10）

## 3. 循序渐进操作步骤 (Step-by-Step)
### 步骤 1: 准备环境
```bash
# 示例命令
```

### 步骤 2: 启动最小示例
```bash
# 示例命令
```

## 4. 下一步探索 (Next Steps)
${NEXT_STEP_LINE}
"""

HOWTO_TEMPLATE = """# ${NAME} 操作指南 (How-To Guide)

> **文档控制信息**
> - **文档标识**: HOWTO-${NAME_UPPER}-${YEAR}
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: ${TODAY}
> - **文档所有者**: AI Agent / 工程师

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | ${TODAY} | AI Agent | 架构师 | 初始化任务操作指南脚手架 |

---

## 1. 目标与场景 (Objective)
说明本指南解决的具体生产任务或故障排查目标。

## 2. 前置条件 (Prerequisites)
- 执行前必须就绪的凭证、权限或环境变量

## 3. 标准操作规程 (SOP / Execution Steps)
### 3.1 步骤一
```bash
# 可直接执行的命令
```

### 3.2 步骤二
```bash
# 可直接执行的命令
```

## 4. 验证与排错 (Verification & Troubleshooting)
- 如何验证操作成功（预期状态码与输出日志）
- 常见偶发问题与对策
"""

REFERENCE_TEMPLATE = """# ${NAME} 权威技术参考 (Technical Reference)

> **文档控制信息**
> - **文档标识**: REF-${NAME_UPPER}-${YEAR}
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: ${TODAY}
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | ${TODAY} | AI Agent | 架构师 | 初始化权威技术参考脚手架 |

---

> ⚠️ **机器真理源声明**: 本文档为全系统权威机械规格唯一事实来源，供 AI 智能体生成代码与人机对齐使用。

## 1. 接口与数据模型契约 (Schema & API Contracts)

### 1.1 数据结构定义
| 字段名 | 类型 | 必填 | 默认值 | 约束说明 |
| :--- | :--- | :--- | :--- | :--- |
| `id` | string | 是 | 无 | 唯一实体 UUID |
| `status` | string | 是 | "pending" | 枚举: pending, running, completed |

### 1.2 异常与错误信封 (Error Envelope)
```json
{
  "code": "ERR_INVALID_PAYLOAD",
  "message": "请求载荷字段校验失败",
  "details": {}
}
```

## 2. 状态机与不可变约束 (Invariants)
- 状态转换规则与守卫条件
"""

EXPLANATION_TEMPLATE = """# ${NAME} 深度剖析与架构设计 (Explanation & Architecture)

> **文档控制信息**
> - **文档标识**: EXP-${NAME_UPPER}-${YEAR}
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: ${TODAY}
> - **文档所有者**: 架构设计委员会

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | ${TODAY} | AI Agent | 架构师 | 初始化系统深度剖析脚手架 |

---

## 1. 设计哲学与宏观背景 (Philosophy & Context)
阐述系统为什么如此设计，以及核心第一性原理。

## 2. 总体架构拓扑 (Architecture Topology)
```mermaid
graph TD
    Client["表现层 / Client"] --> Core["核心领域业务 / Core"]
    Core --> Store["不可变状态与存储 / Store"]
```

## 3. 核心机制推演 (Mechanism & Trade-offs)
- 核心算法推导
- 边界并发竞争与防护机理
"""

ADR_TEMPLATE = """# ADR-${SEQ_PADDED}: ${NAME}

> **ADR 控制元数据**
> - **决策编号**: ${SEQ_PADDED}
> - **当前状态**: Proposed
> - **决策所有者**: 架构组
> - **决议日期**: ${TODAY}

---

## 1. 背景与上下文 (Context and Problem Statement)
- 面临的现实技术或业务问题是什么？
- 有哪些硬性约束？

## 2. 考虑的备选方案 (Considered Options)
* **方案 1**: 备选方案 A
* **方案 2 (选定)**: 备选方案 B
* **方案 3**: 备选方案 C

## 3. 最终决策与裁决 (Decision Outcome)
选定 **方案 2**，原因是：核心优势明显且契合项目技术栈。

### 3.1 积极后果 (Positive Consequences)
* ✅ 优势 1: ...

### 3.2 消极后果与已知代价 (Negative Consequences / Trade-offs)
* ⚠️ 代价 1: ...

---

## 4. 备选方案详细对比 (Pros and Cons)
### 4.1 方案 1
* 赞同理由 (+): ...
* 反对理由 (-): ...

### 4.2 方案 2 (选定)
* 赞同理由 (+): ...
"""

RFC_TEMPLATE = """# RFC-${SEQ_PADDED}: ${NAME}

> **提案元数据**
> - **标识**: RFC-${YEAR}-${NAME_UPPER_ASCII}
> - **当前状态**: Draft
> - **发起人**: 工程师 / AI Agent
> - **当前版本**: V0.1.0
> - **初次发起日期**: ${TODAY}
> - **目标里程碑**: [如 v0.7.0]

---

## 1. 背景与业务痛点 (Why)
- 为什么需要引入此特性？当前痛点是什么？

## 2. 目标与非目标 (Goals & Non-Goals)
### 2.1 核心目标 (Goals)
- [ ] 目标 1: ...
### 2.2 明确非目标 (Non-Goals)
- 明确本期坚决不做的边界

## 3. 核心设计与契约草案 (How - Draft Spec)
> ⚠️ 本节内容为初期探索草案，定案前严禁作为生产基线直接引用。
### 3.1 交互流程与用户故事
### 3.2 领域数据模型草案 (Draft Models)
### 3.3 外部接口与事件草案 (Draft APIs)

## 4. 备选方案权衡与争议焦点 (Alternatives & Trade-offs)
- **方案 A (选定草案)**:
- **方案 B (备选方案)**:

## 5. 未决问题与对齐清单 (Open Questions)
- [ ] 焦点 1: ...
- [ ] 焦点 2: ...
"""

BACKLOG_TEMPLATE = """---
id: BK-${SEQ_PADDED}
title: ${NAME}
type: TechDebt
status: active
priority: P2
trigger: null
created_at: ${TODAY}
updated_at: ${TODAY}
closed_at: null
resolution: null
destination: null
source: []
acceptance_criteria:
  - 核心功能通过自动化单元测试验证
  - 无架构契约回归与漂移
---

## 1. 背景与问题陈述
待补充具体问题描述与上下文分析。

## 2. 影响面与技术考量
- 涉及模块: 待对齐
- 风险点: 待评估

## 3. 验收准则与验证设计 (DoD)
- [ ] 核心功能通过自动化测试 (Exit Code 0)
- [ ] 门禁检查无告警

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录
*(未开工)*
"""

# 各象限骨架：目标子目录、索引登记 kind、模板、以及原实现 heredoc 重定向行号
# （行号仅用于逐字复刻 bash 的重定向失败诊断，见 _write_text）。
QUADRANTS = {
    "tutorial": ("tutorials", "Tutorial", TUTORIAL_TEMPLATE, 76),
    "how-to": ("how-to", "HowTo", HOWTO_TEMPLATE, 126),
    "reference": ("reference", "Reference", REFERENCE_TEMPLATE, 174),
    "explanation": ("explanation", "Explanation", EXPLANATION_TEMPLATE, 223),
}

# bash 算术在非数值序号前缀上的内部诊断（保持 rc/stderr 形态一致）
_ARITH_LINES = {"adr": (270, 272), "rfc": (326, 328), "proposal": (326, 328)}


def _self_path() -> str:
    """原实现用法/错误诊断中的自指路径：bash 的 `$0`（调用时传入形态，非 basename）。"""
    return sys.argv[0]


def _out(text: str) -> None:
    print(text, flush=True)


def _err(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def _upper_locale(value: str) -> str:
    """复刻 bash `${{VAR^^}}`（locale 感知大写：单字符展开才替换）。"""
    chars = []
    for ch in value:
        upper = ch.upper()
        chars.append(upper if len(upper) == 1 else ch)
    return "".join(chars)


def _upper_ascii(value: str) -> str:
    """复刻 `echo "$NAME" | tr '[:lower:]' '[:upper:]'`（ASCII-only）。"""
    return "".join(chr(ord(ch) - 32) if "a" <= ch <= "z" else ch for ch in value)


def _mkdir_p(path: str) -> bool:
    """复刻 `mkdir -p`：逐级建目录，失败时按 coreutils 文案打到 stderr。返回是否成功。"""
    if path == "":
        _err("mkdir: cannot create directory '': No such file or directory")
        return False
    parts = [part for part in path.split("/") if part != ""]
    current = "/" if path.startswith("/") else ""
    for index, part in enumerate(parts):
        if current == "/":
            current = "/" + part
        elif current == "":
            current = part
        else:
            current = current + "/" + part
        last = index == len(parts) - 1
        if os.path.isdir(current):
            continue
        if os.path.exists(current) or os.path.islink(current):
            _err(f"mkdir: cannot create directory '{current}': "
                 + ("File exists" if last else "Not a directory"))
            return False
        try:
            os.mkdir(current)
        except FileExistsError:
            if os.path.isdir(current):
                continue
            _err(f"mkdir: cannot create directory '{current}': "
                 + ("File exists" if last else "Not a directory"))
            return False
        except OSError as exc:
            _err(f"mkdir: cannot create directory '{current}': {exc.strerror}")
            return False
    return True


def _write_text(path: str, content: str, redirect_line: int) -> bool:
    """写产物（UTF-8/LF 固化）；失败时复刻 bash 重定向失败的诊断形态。"""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except OSError as exc:
        _err(f"{_self_path()}: line {redirect_line}: {path}: {exc.strerror}")
        return False
    return True


def _render(template: str, **tokens: str) -> str:
    """按 bash heredoc 同名变量占位符渲染模板。"""
    rendered = template
    for key, value in tokens.items():
        rendered = rendered.replace("${" + key + "}", value)
    return rendered


def _fence(code: str) -> str:
    """把模板里的围栏裸 ``` 还原为原 heredoc 转义后的形态（占位保持逐字节一致）。"""
    return code


def _scripts_dir() -> str:
    """复刻 `SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`。"""
    return os.path.dirname(os.path.abspath(__file__))


def _run_python_helper(helper_name: str, args: list[str], suppress_stderr: bool) -> int | None:
    """调用同目录兄弟 Python 脚本；helper 不存在时返回 None（原实现静默跳过）。"""
    helper = os.path.join(_scripts_dir(), helper_name)
    if not os.path.isfile(helper):
        return None
    interpreter = sys.executable or "python3"
    sys.stdout.flush()
    sys.stderr.flush()
    stderr = subprocess.DEVNULL if suppress_stderr else None
    try:
        return subprocess.run([interpreter, helper, *args], stderr=stderr).returncode
    except OSError:
        return 1


def _heal_doc_index(root_dir: str, dir_rel: str, file_name: str, title: str, kind: str) -> None:
    """象限索引自愈（RFC-0003）：登记失败不阻断主产物，仅在 stdout 打告警。"""
    code = _run_python_helper(
        "manage-doc-index.py",
        ["register", "--root", root_dir, "--dir", dir_rel,
         "--file", file_name, "--title", title, "--kind", kind],
        suppress_stderr=False,
    )
    if code is None:
        return
    if code != 0:
        _out(f"⚠️  象限索引自愈失败（主产物已生成，索引需人工补登记）: {dir_rel}/{file_name}")


def _sync_backlog_index(root_dir: str) -> None:
    """backlog 索引同步：原实现 `2>/dev/null || true`，失败静默。"""
    _run_python_helper(
        "manage-backlog.py",
        ["sync-index", "--root", root_dir],
        suppress_stderr=True,
    )


def _matching_names(target_dir: str, pattern: str) -> list[str]:
    """复刻 `find <dir> -maxdepth 1 -name "<pattern>" | sort`（字节序）。"""
    try:
        names = os.listdir(target_dir)
    except OSError:
        return []
    matched = [name for name in names if fnmatch.fnmatchcase(name, pattern)]
    matched.sort(key=lambda item: item.encode("utf-8", "surrogateescape"))
    return matched


def _cut_field(value: str, index: int) -> str:
    """复刻 `cut -d'-' -f<index>`（1 基；字段不足时返回空串）。"""
    fields = value.split("-")
    return fields[index - 1] if len(fields) >= index else ""


def _next_seq(raw_value: str, lines: tuple[int, int]) -> int | None:
    """复刻 `NEXT_SEQ=$((LAST_NUM + 1))`；非十进制时按 bash 内部诊断处理并返回 None。"""
    digits = raw_value
    if digits == "":
        return 1
    if re.fullmatch(r"[0-9]+", digits):
        return int(digits) + 1
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", digits):
        _err(f"{_self_path()}: line {lines[0]}: {digits}: unbound variable")
        return None
    _err(f'{_self_path()}: line {lines[0]}: {digits}: value too great for base '
         f'(error token is "{digits}")')
    _err(f"{_self_path()}: line {lines[1]}: FILE_PATH: unbound variable")
    return None


def _quadrant_file(root_dir: str, doc_type: str, name: str, today: str, year: str) -> str | None:
    """tutorial / how-to / reference / explanation 四象限骨架。"""
    sub_dir, kind, template, redirect_line = QUADRANTS[doc_type]
    target_dir = f"{root_dir}/{sub_dir}"
    if not _mkdir_p(target_dir):
        return None
    file_path = f"{target_dir}/{name}.md"
    tokens = {
        "NAME": name,
        "NAME_UPPER": _upper_locale(name),
        "YEAR": year,
        "TODAY": today,
    }
    if doc_type == "tutorial":
        if os.path.isfile(f"{root_dir}/how-to/index.md"):
            next_step = "- 探索更多实战操作: [how-to 指南](../how-to/index.md)"
        else:
            next_step = ("- 探索更多实战操作: 运行 `scaffold-doc.sh how-to <name>` "
                         "创建 `how-to/` 象限指南")
        tokens["NEXT_STEP_LINE"] = next_step
    if not _write_text(file_path, _render(template, **tokens), redirect_line):
        return None
    _heal_doc_index(root_dir, sub_dir, f"{name}.md", name, kind)
    return file_path


def _adr_file(root_dir: str, name: str, today: str) -> str | None:
    """ADR：`docs/explanation/decisions/<000X>-<name>.md`，序号自动递增。"""
    target_dir = f"{root_dir}/explanation/decisions"
    if not _mkdir_p(target_dir):
        return None
    next_seq = 1
    existing = _matching_names(target_dir, "????-*.md")
    if existing:
        last_num = _cut_field(existing[-1], 1).lstrip("0")
        if last_num != "":
            seq = _next_seq(last_num, _ARITH_LINES["adr"])
            if seq is None:
                return None
            next_seq = seq
    padded = f"{next_seq:04d}"
    file_path = f"{target_dir}/{padded}-{name}.md"
    if not _write_text(file_path, _render(ADR_TEMPLATE, SEQ_PADDED=padded,
                                          NAME=name, TODAY=today), 275):
        return None
    _heal_doc_index(root_dir, "explanation/decisions", f"{padded}-{name}.md", name, "ADR")
    return file_path


def _rfc_file(root_dir: str, doc_type: str, name: str, today: str, year: str) -> str | None:
    """RFC/提案：`docs/proposals/RFC-<000X>-<name>.md`，序号自动递增。"""
    target_dir = f"{root_dir}/proposals"
    if not _mkdir_p(target_dir):
        return None
    next_seq = 1
    existing = _matching_names(target_dir, "RFC-????-*.md")
    if existing:
        last_num = _cut_field(existing[-1], 2).lstrip("0")
        if last_num != "":
            seq = _next_seq(last_num, _ARITH_LINES[doc_type])
            if seq is None:
                return None
            next_seq = seq
    padded = f"{next_seq:04d}"
    file_path = f"{target_dir}/RFC-{padded}-{name}.md"
    content = _render(RFC_TEMPLATE, SEQ_PADDED=padded, NAME=name, TODAY=today,
                      YEAR=year, NAME_UPPER_ASCII=_upper_ascii(name))
    if not _write_text(file_path, content, 331):
        return None
    _heal_doc_index(root_dir, "proposals", f"RFC-{padded}-{name}.md", name, "RFC")
    return file_path


def _backlog_file(root_dir: str, name: str, today: str) -> str | None:
    """技术债/任务卡：`docs/project/backlog/active/BK-<000X>-<name>.md`。"""
    target_dir = f"{root_dir}/project/backlog/active"
    if not _mkdir_p(target_dir):
        return None
    next_seq = 1
    if os.path.isdir(f"{root_dir}/project/backlog"):
        max_num = 0
        for found in _walk_backlog(root_dir):
            base = os.path.basename(found)
            matched = re.match(r"^BK-([0-9]{4})", base)
            if matched is None:
                continue
            number = matched.group(1).lstrip("0")
            if number != "" and int(number) > max_num:
                max_num = int(number)
        next_seq = max_num + 1
    padded = f"{next_seq:04d}"
    file_path = f"{target_dir}/BK-{padded}-{name}.md"
    if not _write_text(file_path, _render(BACKLOG_TEMPLATE, SEQ_PADDED=padded,
                                          NAME=name, TODAY=today), 390):
        return None
    _sync_backlog_index(root_dir)
    return file_path


def _walk_backlog(root_dir: str) -> list[str]:
    """复刻 `find "$ROOT_DIR/project/backlog" -name "BK-*.md"`（递归、不排序）。"""
    found: list[str] = []
    for current, _dirs, files in os.walk(f"{root_dir}/project/backlog"):
        for file_name in files:
            if fnmatch.fnmatchcase(file_name, "BK-*.md"):
                found.append(os.path.join(current, file_name))
    return found


def _parse_options(argv: list[str]) -> tuple[str, str, bool]:
    """解析 `--root` / `--lang`；返回 (root_dir, lang, ok)。未知参数按原实现打到 stdout。"""
    root_dir = "docs"
    lang = "zh"
    index = 2
    while index < len(argv):
        arg = argv[index]
        if arg == "--root":
            if index + 1 >= len(argv):
                _err(f"{_self_path()}: line 33: $2: unbound variable")
                return root_dir, lang, False
            root_dir = argv[index + 1]
            index += 2
        elif arg == "--lang":
            if index + 1 >= len(argv):
                _err(f"{_self_path()}: line 37: $2: unbound variable")
                return root_dir, lang, False
            lang = argv[index + 1]
            index += 2
        else:
            _out(f"未知参数: {arg}")
            return root_dir, lang, False
    return root_dir, lang, True


def main(argv: list[str] | None = None) -> int:
    """入口：返回进程退出码（与原 Bash 实现一致）。"""
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", newline="\n")
    args = list(argv) if argv is not None else list(sys.argv[1:])

    doc_type = args[0] if len(args) > 0 else ""
    name = args[1] if len(args) > 1 else ""

    if doc_type == "" or name == "":
        _out("❌ 错误: 必须指定文档类型和文档名称。")
        _out(f"用法: {_self_path()} {USAGE_TYPES}")
        return 1

    root_dir, _lang, ok = _parse_options(args)
    if not ok:
        return 1

    today = date.today().strftime("%Y-%m-%d")
    year = date.today().strftime("%Y")

    if not _mkdir_p(root_dir):
        return 1

    if doc_type in QUADRANTS:
        file_path = _quadrant_file(root_dir, doc_type, name, today, year)
    elif doc_type == "adr":
        file_path = _adr_file(root_dir, name, today)
    elif doc_type in ("rfc", "proposal"):
        file_path = _rfc_file(root_dir, doc_type, name, today, year)
    elif doc_type == "backlog":
        file_path = _backlog_file(root_dir, name, today)
    else:
        _out(f"❌ 错误: 未知类型 '{doc_type}'。可用类型: "
             "tutorial, how-to, reference, explanation, adr, rfc, backlog")
        return 1

    if file_path is None:
        return 1
    _out(f"✅ 成功生成 {doc_type} 模板脚手架: {file_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
