# 项目待办与后续演进清单 (Backlog Index)

> **文档控制信息**
> - **文档标识**: BK-INDEX-GOV
> - **当前版本**: V2.0.0 (动态索引)
> - **维护模式**: 机器脚本自动化生成 (请勿手写对账日记，运行 `manage-backlog.py sync-index` 自动刷新)
> - **更新日期**: 2026-10-09

---

## 1. 待办健康度仪表盘 (Metrics Dashboard)

- **现役活跃待办**: **22** 项 (进行中: 0, 计划中: 22)
- **历史已归档项**: **3** 项 (物理归档于 `archive/` 目录)

| 优先级 | P0 (阻断级) | P1 (高优) | P2 (中优) | P3 (低优) |
| :--- | :--- | :--- | :--- | :--- |
| **活跃数量** | 0 | 0 | 4 | 18 |

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
| **BK-0023** | `P2` | `Security` | 机器地图写入侧安全加固（符号链接穿透与零覆盖守卫） | — | [BK-0023](./active/BK-0023-机器地图写入侧安全加固-符号链接穿透与零覆盖守卫.md) |
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
| **BK-0025** | `P3` | `Governance` | 机器地图与生成物一致性需要门禁固化 | — | [BK-0025](./active/BK-0025-机器地图与生成物一致性需要门禁固化.md) |

---

## 4. 🗄️ 历史已结项归档 (Archive Summary)

> 共收录 3 条已关闭历史条目，详情参见 `archive/` 各版本目录。

| 编号 | 类型 | 标题 | 结项日期 | 结论 | 交付去向 | 归档卡片 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0001** | `TechDebt` | trim-revision.py 复用 project-reviews 归档豁免常量 | 2026-10-09 | delivered | trim-revision.py 追加交付凭据归档豁免（root 无关段扫描兜底 + 库调用 resolve + 空范围不报合规）；提交 45089b9/9108fbe | [BK-0001](./archive/2026-Q4/BK-0001-trim-revision-py-archive-exemption.md) |
| **BK-0002** | `TechDebt` | generate-llms-txt.py 复用归档豁免常量 | 2026-10-09 | delivered | generate-llms-txt.py 追加同构归档豁免 + 机器地图纯净重生成（归档条目 17→0）；提交 45089b9/9108fbe | [BK-0002](./archive/2026-Q4/BK-0002-generate-llms-txt-archive-exemption.md) |
| **BK-0021** | `Bug` | generate-llms-txt.py 的 --root 与 --output 落点解耦缺陷 | 2026-10-09 | delivered | --output 缺省落点随 --root 派生（并拒绝写入归档）；提交 45089b9/9108fbe | [BK-0021](./archive/2026-Q4/BK-0021-generate-llms-txt-py-的-root-与-output-落点解.md) |
