# 项目待办与后续演进清单 (Backlog Index)

> **文档控制信息**
> - **文档标识**: BK-INDEX-GOV
> - **当前版本**: V2.0.0 (动态索引)
> - **维护模式**: 机器脚本自动化生成 (请勿手写对账日记，运行 `manage-backlog.py sync-index` 自动刷新)
> - **更新日期**: 2026-11-15

---

## 1. 待办健康度仪表盘 (Metrics Dashboard)

- **现役活跃待办**: **12** 项 (进行中: 0, 计划中: 12)
- **历史已归档项**: **35** 项 (物理归档于 `archive/` 目录)

| 优先级 | P0 (阻断级) | P1 (高优) | P2 (中优) | P3 (低优) |
| :--- | :--- | :--- | :--- | :--- |
| **活跃数量** | 0 | 0 | 1 | 11 |

---

## 2. 🔄 进行中待办 (In Progress)

*(当前暂无进行中的待办)*

---

## 3. 📋 计划中待办 (Planned Backlog)

| 编号 | 优先级 | 类型 | 标题 | 触发条件 | 卡片入口 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0036** | `P2` | `Security` | collect-facts/judge 的输入范围与输出落点双守卫（未知技能名静默 CLEAN + 静默覆盖被跟踪文件） | ① 调用 collect-facts.py --skills <拼错的技能名>；② 把 --out / --json / --report 指向仓库内已存在的被跟踪文件 | [BK-0036](./active\BK-0036-collect-facts-judge-输入范围与输出落点双守卫.md) |
| **BK-0005** | `P3` | `Governance` | 豁免判定前执行路径根相对语义归一化 | null | [BK-0005](./active\BK-0005-relative-to-root-path-normalization.md) |
| **BK-0006** | `P3` | `TechDebt` | 四条审查护栏各补 1 条反证测试用例 | null | [BK-0006](./active\BK-0006-review-gates-negative-test-cases.md) |
| **BK-0009** | `P3` | `Bug` | resolve_archive_dir 增加交付单元与请求 slug 一致性校验 | null | [BK-0009](./active\BK-0009-resolve-archive-dir-slug-consistency.md) |
| **BK-0012** | `P3` | `TechDebt` | 门禁枚举未登记报告文件或收紧 --round 命名输入 | null | [BK-0012](./active\BK-0012-enumerate-unregistered-reports.md) |
| **BK-0017** | `P3` | `TechDebt` | scaffold ADR 模板补控制头版本字段 | null | [BK-0017](./active\BK-0017-scaffold-adr-模板补控制头版本字段.md) |
| **BK-0019** | `P3` | `Governance` | README 入口象限的索引自愈与健康评分语义对齐 | null | [BK-0019](./active\BK-0019-readme-入口象限的索引自愈与健康评分语义对齐.md) |
| **BK-0022** | `P3` | `TechDebt` | strip_leading_noise 对未闭合 frontmatter 围栏兜底 | null | [BK-0022](./active\BK-0022-strip_leading_noise-对未闭合-frontmatter-围栏兜.md) |
| **BK-0024** | `P3` | `TechDebt` | 治理脚本契约细节四项（空范围返回契约/判定越界/归因顺序/表格渲染） | null | [BK-0024](./active\BK-0024-治理脚本契约细节四项-空范围返回契约-判定越界-归因顺序-表格渲染.md) |
| **BK-0028** | `P3` | `TechDebt` | 机器地图判定侧剩余缺口（用例承重与反解契约） | null | [BK-0028](./active\BK-0028-机器地图判定侧剩余缺口-用例承重与反解契约.md) |
| **BK-0043** | `P3` | `Governance` | Write-Once 审查归档 2026-10-12-spec-evolution-v1 的终审裁决字段不满足 check-review-report.sh 精确匹配契约 | dual-round-review 门禁维护窗口；无前置依赖 | [BK-0043](./active\BK-0043-write-once-审查归档终审裁决字段不满足精确匹配契约.md) |
| **BK-0044** | `P3` | `Governance` | 提交信息取证据口径：易失数字与工作区属性反复触发独立复核阻断 | 独立复核循环 V8/V9/V11/V12 反复因提交信息的凭据表述判阻断或提更正：V8 阻断项（8facf12 提交信息的 judge findings | [BK-0044](./active\BK-0044-提交信息取证据口径-易失数字与工作区属性反复触发独立复核阻断.md) |

---

## 4. 🗄️ 历史已结项归档 (Archive Summary)

> 共收录 35 条已关闭历史条目，详情参见 `archive/` 各版本目录。

| 编号 | 类型 | 标题 | 结项日期 | 结论 | 交付去向 | 归档卡片 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0011** | `TechDebt` | 审查归档契约测试的弱断言改为行为断言 | 2026-11-15 | superseded | 前提已被 test_write_channel_contract.py:203-211（R1-12 回归）推翻；残余形态偏好并入 BK-0006 判定 | [BK-0011](./archive\2026-Q4\BK-0011-review-contract-weak-assertions.md) |
| **BK-0037** | `Security` | 输出路径可静默覆盖仓库内被跟踪文件 | 2026-11-15 | superseded | 并入 BK-0036（输入范围与输出落点双守卫，已提 P2） | [BK-0037](./archive\2026-Q4\BK-0037-输出路径可静默覆盖仓库内被跟踪文件.md) |
| **BK-0047** | `Bug` | Windows 全量 pytest 95 例失败：控制台编码与夹具断言漂移两类归因 | 2026-11-15 | delivered | 四批修复：a11ea14(A) / 1c982e4(B+C) / b9f37f1(D)；Windows 498 passed、WSL 518 passed、采集器四门禁 blocker/high=0 | [BK-0047](./archive\2026-Q4\BK-0047-windows-全量-pytest-95-例失败-控制台编码与夹具断言漂移两类归.md) |
| **BK-0041** | `TechDebt` | 存量技能交付面残余债务：agy 设计书缺失 / 两条 description 超建议值 / doc-governance 测试文件超行限 | 2026-11-12 | wontfix | C-02 交付：新增 docs/explanation/architecture/agy-delegation-workflow-design.md；C-04 | [BK-0041](./archive\2026-Q4\BK-0041-存量技能交付面残余债务-agy-设计书缺失-两条-description-超建议.md) |
| **BK-0046** | `Bug` | spec-evolution 门禁 pytest 超时阈值（GATE_TIMEOUT=300s）与实际套件时长临界导致 C-09 假 BLOCKER | 2026-11-12 | delivered | docs/project/backlog/archive/2026-Q4/BK-0046-spec-evolution-门禁-pytest-超时阈值-gate_timeo.md | [BK-0046](./archive\2026-Q4\BK-0046-spec-evolution-门禁-pytest-超时阈值-gate_timeo.md) |
| **BK-0007** | `Governance` | GOVERNANCE.md 豁免表文本精确化 | 2026-10-20 | delivered | docs/project/plans/2026-10-20-p3-six-backlog-batch.md | [BK-0007](./archive\2026-Q4\BK-0007-governance-doc-exemption-table-accuracy.md) |
| **BK-0008** | `Governance` | 围栏奇偶告警文案补充嵌套演示规避提示 | 2026-10-20 | delivered | docs/project/plans/2026-10-20-p3-six-backlog-batch.md | [BK-0008](./archive\2026-Q4\BK-0008-fence-parity-nested-block-guidance.md) |
| **BK-0010** | `Security` | archive-root 空值与非法形态防御校验 | 2026-10-20 | delivered | docs/project/plans/2026-10-20-p3-six-backlog-batch.md | [BK-0010](./archive\2026-Q4\BK-0010-archive-root-empty-or-illegal-guard.md) |
| **BK-0014** | `Governance` | 作废轮次的版本库留痕缺失 | 2026-10-20 | delivered | docs/project/plans/2026-10-20-p3-six-backlog-batch.md | [BK-0014](./archive\2026-Q4\BK-0014-voided-round-repo-trace.md) |
| **BK-0016** | `TechDebt` | 象限索引幂等判据精确匹配（剥离锚点与查询串） | 2026-10-20 | delivered | docs/project/plans/2026-10-20-p3-six-backlog-batch.md | [BK-0016](./archive\2026-Q4\BK-0016-象限索引幂等判据精确匹配-剥离锚点与查询串.md) |
| **BK-0045** | `Bug` | prepare-review-context 未跟踪文件过滤正则失效（GNU BRE `\?` 为重复算子） | 2026-10-20 | delivered | docs/project/plans/2026-10-20-p3-six-backlog-batch.md | [BK-0045](./archive\2026-Q4\BK-0045-prepare-review-context-未跟踪文件过滤正则失效.md) |
| **BK-0003** | `Governance` | 稳定 ID 方向二改为按文件名配对 R1-R2 后施加 | 2026-10-14 | delivered | fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/） | [BK-0003](./archive\2026-Q4\BK-0003-stable-id-pair-by-filename.md) |
| **BK-0004** | `Security` | 新增终审裁决在索引中唯一校验 | 2026-10-14 | delivered | fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/） | [BK-0004](./archive\2026-Q4\BK-0004-unique-verdict-in-review-index.md) |
| **BK-0013** | `TechDebt` | 台账末列定位对无尾随竖线且结论含裸竖线的行误判 | 2026-10-14 | wontfix | 有意保留 fail-closed：目标输入无尾随竖线且结论含裸竖线，本身已破坏 Markdown 表格渲染；BK-0011 行为用例已把「无尾随竖线行 | [BK-0013](./archive\2026-Q4\BK-0013-trailing-pipe-column-misparse.md) |
| **BK-0015** | `TechDebt` | working/staged 模式的报告命名与 base7..head7 模板字面不符 | 2026-10-14 | wontfix | 不接受：纯命名措辞澄清，零运行时与门禁影响；卡片维护成本高于一句文案收益，可在后续文档润色时顺带修正 | [BK-0015](./archive\2026-Q4\BK-0015-working-staged-naming-literal.md) |
| **BK-0018** | `Governance` | 明确 skills-lock.json computedHash 权威定义并评估全量重算 | 2026-10-14 | wontfix | 治理对象不在本仓所有权：skills-lock.json 已 gitignore 且未跟踪，由外部 npx skills 生成，82/86 | [BK-0018](./archive\2026-Q4\BK-0018-明确-skills-lock-json-computedhash-权威定义并评估.md) |
| **BK-0020** | `TechDebt` | 修订表头定位限定在修订历史章节作用域内 | 2026-10-14 | delivered | fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/） | [BK-0020](./archive\2026-Q4\BK-0020-修订表头定位限定在修订历史章节作用域内.md) |
| **BK-0029** | `Security` | 交付凭据写入侧历史残留（硬链接穿透与删除逃逸） | 2026-10-14 | superseded | 目标已达成：硬链接篡改路径由 8f3d1e4 原子替换消除；R1-4 已由 GOVERNANCE.md §4.1 登记豁免；.pyc 按 | [BK-0029](./archive\2026-Q4\BK-0029-交付凭据写入侧历史残留-硬链接穿透与删除逃逸.md) |
| **BK-0032** | `Security` | 身份写保护闸门的权限与语义细节残余 | 2026-10-14 | wontfix | 不接受：残余项多为不可达理论边界（行尾 U+000B 分隔符、自指软链、非法 surrogate 文件名、FIFO 目录半边），M 级成本收益不足 | [BK-0032](./archive\2026-Q4\BK-0032-身份写保护闸门的权限与语义细节残余.md) |
| **BK-0033** | `TechDebt` | 门禁输出非 UTF-8 环境下的 print 硬化与异常退出码收敛 | 2026-10-14 | delivered | fix/p2-six-backlog-items @ deb691e（R2 终审 ✅ 准予交付；审查归档 docs/project/reviews/2026-10-14-p2-six-backlog-items/） | [BK-0033](./archive\2026-Q4\BK-0033-门禁子进程非-utf-8-输出导致裸-traceback.md) |

*(其余 15 条历史记录已隐藏，可查看 archive/ 目录)*
