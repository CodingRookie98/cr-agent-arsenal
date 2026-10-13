---
id: BK-0043
title: Write-Once 审查归档 2026-10-12-spec-evolution-v1 的终审裁决字段不满足 check-review-report.sh 精确匹配契约
type: Governance
status: active
priority: P3
trigger: dual-round-review 门禁维护窗口；无前置依赖
created_at: '2026-10-13'
updated_at: '2026-10-13'
closed_at: null
resolution: null
destination: null
source:
- 模板自验（2026-10-13）发现：真实归档 docs/project/reviews/2026-10-12-spec-evolution-v1 结构校验 rc=0，但 --require-verdict=PASS rc=1
- 全量归档普查（2026-10-13）：9 个归档中 8 个 rc=0，仅该归档失败
acceptance_criteria:
- 在卡片中记录处置决策（三选一并写明依据）：(a) 门禁允许「判决值 + 单个括号统计后缀」并以正则显式定义；(b) 门禁新增显式归档豁免白名单（登记 slug 与理由）；(c) 维持严格契约，仅在 check-review-report.sh 与技能文档中登记该归档为历史例外
- 按所选方案落地：若是 (a)/(b)，须在 skills/dual-round-review/tests 增加回归测试（正例 rc=0、反例 rc=1），并复跑 scripts/check-review-report.sh 对全部 9 个归档；若是 (c)，须在文档中给出一行可执行豁免命令或说明
- 归档面 docs/project/reviews/** 保持 Write-Once，不改写既有证据文件
---

## 1. 背景与问题陈述
`skills/dual-round-review/scripts/check-review-report.sh` 的 `--require-verdict=PASS` 判定为：取首个含 `**终审裁决**` 的行 → 剥前缀与空白 → 剥一个前导 ✅ → 剥空白 → 必须精确等于「准予交付」。真实归档 docs/project/reviews/2026-10-12-spec-evolution-v1/README.md:13 写作 `- **终审裁决**: ✅ **准予交付**（delta-r2：Blockers = 0；🔴 0 / 🟡 19 / ⚪ 0）`，带加粗与括号统计后缀，实测 rc=1。该归档属 Write-Once 证据面（docs/project/reviews/** 在 docs 门禁中豁免），不得就地修改，故该门禁对该归档永久失效。

普查实测（2026-10-13）：docs/project/reviews/ 下 9 个归档目录，含 README.md 者 9 个；结构校验全部 rc=0；`--require-verdict=PASS` 仅 2026-10-12-spec-evolution-v1 rc=1，其余 8 个 rc=0。

## 2. 影响面与技术考量
- 涉及模块: skills/dual-round-review/scripts/check-review-report.sh、skills/dual-round-review/SKILL.md、skills/dual-round-review/tests/
- 风险点: 方案 (a) 放宽判决匹配会削弱门禁对「带后缀统计」的拦截强度（原设计正是要拒绝含该词元的占位/否定式串）；方案 (b) 引入豁免名单属配置机制，与既有 YAGNI 约束（BK-0003/BK-0004 明示禁止引入 .docignore 类配置机制）张力较大；方案 (c) 零代码风险但门禁对后续同形态归档仍失效。

## 3. 验收准则与验证设计 (DoD)
- [ ] 在卡片中记录处置决策（三选一并写明依据）
- [ ] 按所选方案落地：若是 (a)/(b) 增加回归测试（正例 rc=0、反例 rc=1）并复跑全部 9 个归档；若是 (c) 给出一行可执行豁免说明
- [ ] 归档面 docs/project/reviews/** 保持 Write-Once，不改写既有证据文件

## 4. 实施去向与结项记录
*(未开工)*