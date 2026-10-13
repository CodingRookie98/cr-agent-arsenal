# 项目待办与后续演进清单 (Backlog Index)

> **文档控制信息**
> - **文档标识**: BK-INDEX-GOV
> - **当前版本**: V2.0.0 (动态索引)
> - **维护模式**: 机器脚本自动化生成 (请勿手写对账日记，运行 `manage-backlog.py sync-index` 自动刷新)
> - **更新日期**: 2026-10-13

---

## 1. 待办健康度仪表盘 (Metrics Dashboard)

- **现役活跃待办**: **32** 项 (进行中: 0, 计划中: 32)
- **历史已归档项**: **11** 项 (物理归档于 `archive/` 目录)

| 优先级 | P0 (阻断级) | P1 (高优) | P2 (中优) | P3 (低优) |
| :--- | :--- | :--- | :--- | :--- |
| **活跃数量** | 0 | 0 | 7 | 25 |

---

## 2. 🔄 进行中待办 (In Progress)

*(当前暂无进行中的待办)*

---

## 3. 📋 计划中待办 (Planned Backlog)

| 编号 | 优先级 | 类型 | 标题 | 触发条件 | 卡片入口 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0003** | `P2` | `Governance` | 稳定 ID 方向二改为按文件名配对 R1-R2 后施加 | — | [BK-0003](./active/BK-0003-stable-id-pair-by-filename.md) |
| **BK-0004** | `P2` | `Security` | 新增终审裁决在索引中唯一校验 | — | [BK-0004](./active/BK-0004-unique-verdict-in-review-index.md) |
| **BK-0020** | `P2` | `TechDebt` | 修订表头定位限定在修订历史章节作用域内 | — | [BK-0020](./active/BK-0020-修订表头定位限定在修订历史章节作用域内.md) |
| **BK-0033** | `P2` | `TechDebt` | 门禁输出非 UTF-8 环境下的 print 硬化与异常退出码收敛 | 采集器或判定器在 LC_ALL=C / PYTHONUTF8=0 等非 UTF-8 环境下运行 | [BK-0033](./active/BK-0033-门禁子进程非-utf-8-输出导致裸-traceback.md) |
| **BK-0034** | `P2` | `Bug` | baseline.json 损坏静默降级导致 C-10 假阳性与假阴性 | skills/spec-evolution/references/baseline.json 被人工写坏或键被删除 | [BK-0034](./active/BK-0034-baseline-json-损坏静默降级导致-c-10-假阳性与假阴性.md) |
| **BK-0035** | `P2` | `Governance` | RFC-0004 的 GI-1/GI-3 不变式清单与实现未对齐 | 审阅 RFC-0004 §3.5 门禁不变式表时 | [BK-0035](./active/BK-0035-rfc-0004-的-gi-1-gi-3-不变式清单与实现未对齐.md) |
| **BK-0040** | `P2` | `Bug` | spec-evolution judge.py 嵌套类型逃逸使退出码 1 与「存在 BLOCKER/HIGH」同码 | `--facts` 输入被截断、被手工修改，或上游 `collect-facts.py` schema 漂移时可达（`--facts` 接受任意外部输入）。 | [BK-0040](./active/BK-0040-spec-evolution-judge-py-嵌套类型逃逸使退出码-1-与-存.md) |
| **BK-0005** | `P3` | `Governance` | 豁免判定前执行路径根相对语义归一化 | — | [BK-0005](./active/BK-0005-relative-to-root-path-normalization.md) |
| **BK-0006** | `P3` | `TechDebt` | 四条审查护栏各补 1 条反证测试用例 | — | [BK-0006](./active/BK-0006-review-gates-negative-test-cases.md) |
| **BK-0007** | `P3` | `Governance` | GOVERNANCE.md 豁免表文本精确化 | — | [BK-0007](./active/BK-0007-governance-doc-exemption-table-accuracy.md) |
| **BK-0008** | `P3` | `Governance` | 围栏奇偶告警文案补充嵌套演示规避提示 | — | [BK-0008](./active/BK-0008-fence-parity-nested-block-guidance.md) |
| **BK-0009** | `P3` | `Bug` | resolve_archive_dir 增加交付单元与请求 slug 一致性校验 | — | [BK-0009](./active/BK-0009-resolve-archive-dir-slug-consistency.md) |
| **BK-0010** | `P3` | `Security` | archive-root 空值与非法形态防御校验 | — | [BK-0010](./active/BK-0010-archive-root-empty-or-illegal-guard.md) |
| **BK-0011** | `P3` | `TechDebt` | 审查归档契约测试的弱断言改为行为断言 | — | [BK-0011](./active/BK-0011-review-contract-weak-assertions.md) |
| **BK-0012** | `P3` | `TechDebt` | 门禁枚举未登记报告文件或收紧 --round 命名输入 | — | [BK-0012](./active/BK-0012-enumerate-unregistered-reports.md) |
| **BK-0013** | `P3` | `TechDebt` | 台账末列定位对无尾随竖线且结论含裸竖线的行误判 | — | [BK-0013](./active/BK-0013-trailing-pipe-column-misparse.md) |
| **BK-0014** | `P3` | `Governance` | 作废轮次的版本库留痕缺失 | — | [BK-0014](./active/BK-0014-voided-round-repo-trace.md) |
| **BK-0015** | `P3` | `TechDebt` | working/staged 模式的报告命名与 base7..head7 模板字面不符 | — | [BK-0015](./active/BK-0015-working-staged-naming-literal.md) |
| **BK-0016** | `P3` | `TechDebt` | 象限索引幂等判据精确匹配（剥离锚点与查询串） | — | [BK-0016](./active/BK-0016-象限索引幂等判据精确匹配-剥离锚点与查询串.md) |
| **BK-0017** | `P3` | `TechDebt` | scaffold ADR 模板补控制头版本字段 | — | [BK-0017](./active/BK-0017-scaffold-adr-模板补控制头版本字段.md) |
| **BK-0018** | `P3` | `Governance` | 明确 skills-lock.json computedHash 权威定义并评估全量重算 | — | [BK-0018](./active/BK-0018-明确-skills-lock-json-computedhash-权威定义并评估.md) |
| **BK-0019** | `P3` | `Governance` | README 入口象限的索引自愈与健康评分语义对齐 | — | [BK-0019](./active/BK-0019-readme-入口象限的索引自愈与健康评分语义对齐.md) |
| **BK-0022** | `P3` | `TechDebt` | strip_leading_noise 对未闭合 frontmatter 围栏兜底 | — | [BK-0022](./active/BK-0022-strip_leading_noise-对未闭合-frontmatter-围栏兜.md) |
| **BK-0024** | `P3` | `TechDebt` | 治理脚本契约细节四项（空范围返回契约/判定越界/归因顺序/表格渲染） | — | [BK-0024](./active/BK-0024-治理脚本契约细节四项-空范围返回契约-判定越界-归因顺序-表格渲染.md) |
| **BK-0028** | `P3` | `TechDebt` | 机器地图判定侧剩余缺口（用例承重与反解契约） | — | [BK-0028](./active/BK-0028-机器地图判定侧剩余缺口-用例承重与反解契约.md) |
| **BK-0029** | `P3` | `Security` | 交付凭据写入侧历史残留（硬链接穿透与删除逃逸） | — | [BK-0029](./active/BK-0029-交付凭据写入侧历史残留-硬链接穿透与删除逃逸.md) |
| **BK-0032** | `P3` | `Security` | 身份写保护闸门的权限与语义细节残余 | — | [BK-0032](./active/BK-0032-身份写保护闸门的权限与语义细节残余.md) |
| **BK-0036** | `P3` | `Bug` | --skills 传入未知技能名静默产出 CLEAN | 调用 collect-facts.py --skills <拼错的技能名> | [BK-0036](./active/BK-0036-skills-传入未知技能名静默产出-clean.md) |
| **BK-0037** | `P3` | `Security` | 输出路径可静默覆盖仓库内被跟踪文件 | 操作者把 --out / --json / --report 指向仓库内已存在的被跟踪文件 | [BK-0037](./active/BK-0037-输出路径可静默覆盖仓库内被跟踪文件.md) |
| **BK-0038** | `P3` | `TechDebt` | 跨技能链接正则存在两份近似实现 | 修改 skills/_shared/tests/test_cross_skill_links.py 的 SKILL_NAMES 或正则时 | [BK-0038](./active/BK-0038-跨技能链接正则存在两份近似实现.md) |
| **BK-0041** | `P3` | `TechDebt` | 存量技能交付面残余债务：agy 设计书缺失 / 两条 description 超建议值 / doc-governance 测试文件超行限 | spec-evolution judge 全量复跑出现 C-02 / C-04 / C-06 类 MID 发现且不阻断交付时登记；无前置条件，随时可做 | [BK-0041](./active/BK-0041-存量技能交付面残余债务-agy-设计书缺失-两条-description-超建议.md) |
| **BK-0043** | `P3` | `Governance` | Write-Once 审查归档 2026-10-12-spec-evolution-v1 的终审裁决字段不满足 check-review-report.sh 精确匹配契约 | dual-round-review 门禁维护窗口；无前置依赖 | [BK-0043](./active/BK-0043-write-once-审查归档终审裁决字段不满足精确匹配契约.md) |

---

## 4. 🗄️ 历史已结项归档 (Archive Summary)

> 共收录 11 条已关闭历史条目，详情参见 `archive/` 各版本目录。

| 编号 | 类型 | 标题 | 结项日期 | 结论 | 交付去向 | 归档卡片 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0039** | `TechDebt` | 存量技能交付面债务：agy/clarification 缺测试与 README 登记 | 2026-10-13 | delivered | 技能交付面补齐：agy 与 clarification-protocol 补 tests/、clarification 交付面与设计书入册、doc-governance 与 dual-round-review 补 templates/，C-01/C-02/C-03 转绿；提交 8facf12/cdedd38 | [BK-0039](./archive/2026-Q4/BK-0039-存量技能交付面债务-agy-clarification-缺测试与-readme-.md) |
| **BK-0042** | `TechDebt` | manage-backlog.py close 未收敛卡片 §3 DoD 勾选与 §4「(未开工)」占位 | 2026-10-13 | delivered | close/create/reopen 收口一致性：close 机械收敛 *(未开工)* 占位语并按项数提示未勾选 DoD、reopen 写明历史留痕口径、create 声明人工勾选职责；新增 8 用例契约测试；提交 afdb4e5 | [BK-0042](./archive/2026-Q4/BK-0042-manage-backlog-py-close-未收敛卡片-3-dod-勾选与-.md) |
| **BK-0001** | `TechDebt` | trim-revision.py 复用 project-reviews 归档豁免常量 | 2026-10-09 | delivered | trim-revision.py 追加交付凭据归档豁免（root 无关段扫描兜底 + 库调用 resolve + 空范围不报合规）；提交 45089b9/9108fbe | [BK-0001](./archive/2026-Q4/BK-0001-trim-revision-py-archive-exemption.md) |
| **BK-0002** | `TechDebt` | generate-llms-txt.py 复用归档豁免常量 | 2026-10-09 | delivered | generate-llms-txt.py 追加同构归档豁免 + 机器地图纯净重生成（归档条目 17→0）；提交 45089b9/9108fbe | [BK-0002](./archive/2026-Q4/BK-0002-generate-llms-txt-archive-exemption.md) |
| **BK-0021** | `Bug` | generate-llms-txt.py 的 --root 与 --output 落点解耦缺陷 | 2026-10-09 | delivered | --output 缺省落点随 --root 派生（并拒绝写入归档）；提交 45089b9/9108fbe | [BK-0021](./archive/2026-Q4/BK-0021-generate-llms-txt-py-的-root-与-output-落点解.md) |
| **BK-0023** | `Security` | 机器地图写入侧安全加固（符号链接穿透与零覆盖守卫） | 2026-10-09 | delivered | 机器地图写入侧安全加固：缺省落点统一 resolve()、零覆盖拒绝落盘、提示命令 shlex.quote；提交 141cf99 | [BK-0023](./archive/2026-Q4/BK-0023-机器地图写入侧安全加固-符号链接穿透与零覆盖守卫.md) |
| **BK-0025** | `Governance` | 机器地图与生成物一致性需要门禁固化 | 2026-10-09 | delivered | 机器地图一致性门禁固化：audit-doc-health 新增硬阻断（判定与生成参数同源 + 合规树接线用例）；提交 141cf99 | [BK-0025](./archive/2026-Q4/BK-0025-机器地图与生成物一致性需要门禁固化.md) |
| **BK-0026** | `Security` | 机器地图提示文案的终端注入面与畸形项目名 | 2026-10-09 | delivered | 生成器身份写保护闸门 + 提示文案净化（re.fullmatch / 安全回显谓词 / --name= 赋值）；提交 4dfc3ad | [BK-0026](./archive/2026-Q4/BK-0026-机器地图提示文案的终端注入面与畸形项目名.md) |
| **BK-0027** | `Governance` | 零覆盖态机器地图无门禁兜底需显式登记或补校验 | 2026-10-09 | delivered | GOVERNANCE §4.1 显式登记零覆盖态无门禁兜底的口径与代价；提交 d9f2514/4dfc3ad | [BK-0027](./archive/2026-Q4/BK-0027-零覆盖态机器地图无门禁兜底需显式登记或补校验.md) |
| **BK-0030** | `Security` | 机器地图身份写保护闸门的完备性残余 | 2026-10-09 | delivered | 身份沿用语义 + round-trip 断言 + 全面 fail-closed + 放行级用例 + 文案修正；提交 9efdbbd | [BK-0030](./archive/2026-Q4/BK-0030-机器地图身份写保护闸门的完备性残余.md) |
| **BK-0031** | `Governance` | 身份写保护契约登记与历史防护面残留 | 2026-10-09 | delivered | GOVERNANCE §4.1 身份写保护契约登记（沿用/改名/fail-closed/地图缺失口径）+ 严格解码；提交 9efdbbd | [BK-0031](./archive/2026-Q4/BK-0031-身份写保护契约登记与历史防护面残留.md) |
