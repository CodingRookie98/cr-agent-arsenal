# 文档联动复核矩阵 (Documentation Synchronization Matrix)

## 概述 (Overview)

代码演进必须伴随文档同步，避免下游维护者与智能体产生认知漂移。本矩阵用于 `goal-loop` 的 **`Close`（原 P5）** 阶段，默认按 **Diátaxis 四象限**布局组织；若目标项目采用其他文档目录结构，按职责映射到项目既有对应目录即可。若项目已启用 `doc-governance` 技能，文档同步完成后直接交由其执行断链、版本一致性与机器地图门禁审计。

---

## 1. Diátaxis 文档联动检查清单 (Sync Checklist)

| 象限 / 归档域 | 触发检查条件 | 标准目录示例（Diátaxis） | 核心核验与同步动作 |
|---|---|---|---|
| **Tutorials（教程）** | 影响新用户的初始安装、快速上手流程或首个示例命令 | `docs/tutorials/` | 验证并更新端到端上手步骤与示例命令 |
| **How-To（操作指南）** | 新增或变更安装、配置、排障、门禁运行等任务型 SOP | `docs/how-to/` | 更新操作步骤与故障排查条目（现象 → 根因 → 方案） |
| **Reference（技术参考）** | 修改公共接口、CLI 参数/子命令、数据契约、行为规范或核心术语 | `docs/reference/` | 同步冷峻事实（参数表、字段约束、规则红线与术语一致性） |
| **Explanation（深度剖析）** | 新增/重构模块拓扑（架构设计）、做出重大技术选型（ADR）或产出调研评估 | `docs/explanation/architecture/`<br/>`docs/explanation/decisions/`<br/>`docs/explanation/analysis/` | 升级对应架构设计书版本与修订表；沉淀 MADR 决策记录；归档技术调研与评估结论 |
| **Proposals（需求提案）** | `Align` 阶段产出的需求确认文档进入已落地状态 | `docs/proposals/RFC-*.md` | 核验 RFC 状态流转与通用 4 列决策台账（对齐 `clarification-protocol`：已决 / 已排除 / 默认假设无遗漏且无矛盾） |
| **Project Governance（工程演进）** | 目标交付完成、终审凭据归档或待办项闭环 | `docs/project/plans/`<br/>`docs/project/reviews/`<br/>`docs/project/backlog/`<br/>`docs/project/changelog.md` | 计划标记 `[已完成]` 并写收口摘要；核验终审凭据归档；关闭关联待办卡片；补齐发布日志条目 |
| **根级入口（按需）** | 对外暴露的新能力、安装入口或全局协作约束发生变化 | `README.md`、`AGENTS.md`、`docs/index.md` | 仅同步受影响的入口表格与导航指针，严禁顺手改写无关段落 |

---

## 2. 同步纪律 (Sync Standards)

1. **以真实 Diff 为准**：更新文档前先执行 `git diff --stat` 核对实际变动范围；文档内全部示例命令必须在本地真实可执行，严禁凭记忆编造。
2. **术语一词一义**：同一概念在代码、RFC、参考与架构文档中保持唯一命名，不引入并行别名；新增核心术语须在项目术语规范处同步登记。
3. **物理链接与生成物一致**：跨文档相对引用显式保留 `.md` 物理后缀、杜绝 404 断链；若项目维护自动生成的机器地图（如 `docs/llms.txt` 与分层子地图），务必重新生成并严禁手工篡改。
4. **干净提交与多语同步**：文档联动建议采用清晰的 Conventional Commits（如 `docs: sync <scope> for <reason>`）；若项目维护多语言文档，须同步更新对应语种版本。
