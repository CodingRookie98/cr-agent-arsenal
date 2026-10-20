---
id: BK-0045
title: prepare-review-context 未跟踪文件过滤正则失效（GNU BRE `\?` 为重复算子）
type: Bug
status: completed
priority: P2
trigger: null
created_at: 2026-10-19
updated_at: 2026-10-20
closed_at: 2026-10-20
resolution: delivered
destination: docs/project/plans/2026-10-20-p3-six-backlog-batch.md
source: [skill-scripts-python-unification]
acceptance_criteria: 
---

## 1. 背景与问题陈述
`skills/dual-round-review/scripts/prepare-review-context.sh`（v1.0.0，行 226 附近）以如下管道判定未跟踪文件：

```bash
UNTRACKED_FILES=$(git status -s | grep '^\?\?' | awk '{print $2}')
```

在 GNU grep 3.11 的 **BRE** 语义下，`\?` 不是字面问号，而是「前一项重复 0 或 1 次」的重复算子；模式 `^\?\?` 因此退化为「行首 + 可选的 `?`」，**恒匹配任意行**（含空行）。实测反证据：

```
$ printf 'M  a.txt\n?? new.txt\n' | grep '^\?\?'
M  a.txt
?? new.txt
```

后果：脚本「未跟踪新增文件」段落实际列出 `git status -s` 的**全部**条目的 `$2` 字段，已修改/已暂存文件被误标为未跟踪；随后基于该清单给出的 `git add -N .` 建议也建立在错误集合上。审查上下文因此可能失真（R1 的改动面边界识别）。

## 2. 影响面与技术考量
- 涉及模块: `skills/dual-round-review/scripts/prepare-review-context.{sh,py}`（提示段落文本，不进任何门禁判定与产物哈希）。
- 风险点: ① 修复会改变既有 stdout（契约变更），需同步更新契约测试与技能文档口径；② POSIX 差异——BSD/macOS grep 的 BRE 语义与 GNU 不同（`\?` 在 BSD 为字面 `?`），故该缺陷实际是「平台相关行为分歧」，修复应改用不依赖方言的写法（如 `awk '$1=="??"{print $2}'` 或 `git ls-files --others --exclude-standard`）。
- 迁移自证: 本次「技能脚本 Python 统一化」交付对既有实现**保真复刻**（byte-parity 为首要验收），故刻意不改；差分证据见 `.goal-loop/cases/prepare-review-context.txt`（两侧一致）。**未新增任何固化该错误语义的断言**。

## 3. 验收准则与验证设计 (DoD)
- [x] 过滤逻辑改为平台无关写法，能在 GNU/BSD grep 与 Windows（无 grep 依赖）下得到同一集合
- [x] 新增三态混排夹具的行为用例（已暂存 / 已修改 / 未跟踪），断言仅未跟踪项进入清单
- [x] 更新 `skills/dual-round-review/SKILL.md` 与相关模板中的输出示例（若受影响）
- [x] `python3 -B -m pytest skills/dual-round-review/tests -q` 全绿，差分矩阵与既有契约测试无回归

*（§3 DoD 复选框由作者在结项前人工核验并逐项勾选；`close` 只收敛本卡占位语并提示未勾选项数，不代勾验收准则。）*

## 4. 实施去向与结项记录

### 结项记录 (2026-10-20)
- **结论**: delivered
- **去向/凭据**: docs/project/plans/2026-10-20-p3-six-backlog-batch.md
- **归档目录**: archive/2026-Q4/
