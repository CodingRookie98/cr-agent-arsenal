# 项目待办与后续演进清单 (Backlog Index)

> **文档控制信息**
> - **文档标识**: BK-INDEX-GOV
> - **当前版本**: V2.0.0 (动态索引)
> - **维护模式**: 机器脚本自动化生成 (请勿手写对账日记，运行 `manage-backlog.py sync-index` 自动刷新)
> - **更新日期**: 2026-10-08

---

## 1. 待办健康度仪表盘 (Metrics Dashboard)

- **现役活跃待办**: **15** 项 (进行中: 0, 计划中: 15)
- **历史已归档项**: **0** 项 (物理归档于 `archive/` 目录)

| 优先级 | P0 (阻断级) | P1 (高优) | P2 (中优) | P3 (低优) |
| :--- | :--- | :--- | :--- | :--- |
| **活跃数量** | 0 | 0 | 4 | 11 |

---

## 2. 🔄 进行中待办 (In Progress)

*(当前暂无进行中的待办)*

---

## 3. 📋 计划中待办 (Planned Backlog)

| 编号 | 优先级 | 类型 | 标题 | 触发条件 | 卡片入口 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BK-0001** | `P2` | `TechDebt` | trim-revision.py 复用 project-reviews 归档豁免常量 | — | [BK-0001](./active/BK-0001-trim-revision-py-archive-exemption.md) |
| **BK-0002** | `P2` | `TechDebt` | generate-llms-txt.py 复用归档豁免常量 | — | [BK-0002](./active/BK-0002-generate-llms-txt-archive-exemption.md) |
| **BK-0003** | `P2` | `Governance` | 稳定 ID 方向二改为按文件名配对 R1-R2 后施加 | — | [BK-0003](./active/BK-0003-stable-id-pair-by-filename.md) |
| **BK-0004** | `P2` | `Security` | 新增终审裁决在索引中唯一校验 | — | [BK-0004](./active/BK-0004-unique-verdict-in-review-index.md) |
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

---

## 4. 🗄️ 历史已结项归档 (Archive Summary)

> 共收录 0 条已关闭历史条目，详情参见 `archive/` 各版本目录。

