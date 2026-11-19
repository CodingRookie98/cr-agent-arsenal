---
id: BK-0012
title: 门禁枚举未登记报告文件或收紧 --round 命名输入
type: TechDebt
status: active
priority: P3
trigger: null
created_at: '2026-10-08'
updated_at: '2026-10-08'
closed_at: null
resolution: null
destination: null
source:
- dual-round-review V2.2.0 Delta R2 DR-3
acceptance_criteria:
- 在「门禁枚举未登记报告文件」与「约束 --round 命名输入使 head 分量确定」之间择一实现，不做双份
- 补回归用例（归档目录含 README.md，天真枚举会假红，须文件名模式 + 台账交叉校验）
---

## 1. 背景与问题陈述
R1-1 残余：单参数形式 --round <BASE_SHA> 下 HEAD 为符号引用，HEAD 漂移即路径漂移且 Write-Once 静默；实测未登记报告放入归档目录后门禁仍 rc=0（孤儿不可枚举）。触发需三步编排者失误叠加，故记待办而非阻断。

## 2. 影响面与技术考量
- 涉及模块: skills/dual-round-review/scripts/check-review-report.py（新增校验项 11）+ 其契约用例
- 风险点: 枚举面必须**双向收窄**——只认轮次前缀 `r1-` / `r2-` / `delta-r1-` / `delta-r2-` 的 `.md`（否则 `README.md` 假红），且只在台账交叉校验后判孤儿；放宽成「目录里任何多余文件」会把操作者的临时笔记也判成缺陷

## 3. 验收准则与验证设计 (DoD)
- [x] 择一实现：**门禁枚举未登记报告文件**（不碰 `--round` 命名，符合「不做双份」）
- [x] 补回归用例：未登记报告 rc=1 且指名、`README.md` 不得被判孤儿（假红防护）、已登记 delta 报告不误报

## 4. 实施去向与结项记录
### 实施记录（2026-11-19）

**选「枚举未登记报告」这一半**，理由：它是实测坐实的有害面（孤儿凭据在 Write-Once 面里既不被门禁枚举、也不被任何结论引用）；另一半（收紧 `--round` 命名）经复核**未复现原卡描述的形态**——实测 `--round=r1 <BASE>` 输出 `r1-e9cbce9..e9cbce9.md`，路径两端都是解析后的 SHA，不是符号引用 `HEAD`。按「择一实现、不做双份」的要求，不动命名侧。

**新增校验项 11**（`_check_orphan_reports`）：遍历归档目录，凡匹配 `^(r1|r2|delta-r1|delta-r2)-.+\.md$` 且**未出现在轮次台账**的文件，逐条报缺陷。双条件（文件名模式 + 台账交叉校验）正是卡片要求的假红防护。

**复验**：往真实归档副本里塞 `r1-orphan-unregistered.md` → rc=1 且报错指名该文件（改前 rc=0）；12 个真实归档全量扫 → **12/12 rc=0**（无假红）。dual-round-review 126 passed / 3 skipped。
