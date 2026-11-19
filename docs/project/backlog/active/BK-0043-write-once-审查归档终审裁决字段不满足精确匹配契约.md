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
- [x] 记录处置决策：**方案 (a)**，且以正则在代码中显式定义放宽面（依据见 §4）
- [x] 按方案 (a) 落地：新增 3 条回归（真实归档形态 rc=0 / 无数字后缀 rc=1 / 后缀后带尾巴 rc=1），并复跑**全部 12 个**归档（卡片写作时是 9 个，期间新增 3 个）：12/12 rc=0
- [x] 归档面零改写：本次只改门禁与测试，`docs/project/reviews/**` 未动（`git status` 无该目录变更）

## 4. 实施去向与结项记录
### 实施记录（2026-11-19）· 决策 (a)

**为何选 (a) 而不是 (b)/(c)**：(b) 引入豁免白名单，与 BK-0003/BK-0004 明令禁止的 `.docignore` 类配置机制正面冲突；(c) 零代码但在该归档上永久红，后续每次门禁都失败，等于把一条噪声固化进流程。真实归档的写法不是「不够精确」，而是**比契约更完整**（判词 + 统计），契约本身漏了这一合法形态。

**放宽面被结构化收窄**，不是模糊匹配：

```
^准予交付（[^（）]*[0-9][^（）]*）$
```

- 必须以「准予交付」开头，且括号后缀**必须含阿拉伯数字**（统计），括号后**不得再有内容**（锚定）；
- 加粗 `**` 视为排版而非语义，判定前剔除；
- 仍全败的形态：`未准予交付`、`准予交付?`、`建议准予交付（待人类签收）`、`准予交付（见下）`（无数字）、`准予交付（Blockers = 0）待复核`（有尾巴）、RFC §3.4 占位符串。

**复验**：12 个归档 `--require-verdict=PASS` 全部 rc=0，含此前唯一失败的 `2026-10-12-spec-evolution-v1`。dual-round-review 123 passed / 3 skipped。

**副作用披露**：既有错误文案随之改为「必须为『准予交付』或『准予交付』+ 含数字的括号统计串」，并在其中点名三类被拒形态；`test_require_verdict_fails_on_*` 四条例仍全绿，说明收紧面未被破坏。