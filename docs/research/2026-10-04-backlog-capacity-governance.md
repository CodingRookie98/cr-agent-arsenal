# 大规模 issue / 待办 / 变更记录的容量治理：真实实践调研

> **文档控制信息**
> - **文档标识**: RES-BACKLOG-CAPACITY-2026
> - **当前版本**: V1.0.0
> - **维护负责人**: 核心架构组
> - **生效日期**: 2026-10-04

> 证据分级：**【共识】**= 官方文档或标准明文；**【争议】**= 存在对立的一手主张；**【推断】**= 本次调研的推论，非来源结论。

## 1. Issue backlog 规模治理

**【共识】官方推荐是“入口收口 + 定期出清”，而非设定容量上限。** Linear 的 Triage 是独立收件箱，进入的是集成（Slack/Sentry/Zendesk）与跨团队创建的问题，动作只有四个：accept / decline / mark as duplicate / snooze，并可用 Triage Responsibility 做轮值认领（[Linear Docs: Triage](https://linear.app/docs/triage)）。Linear 把 “keep a manageable backlog” 列为 Linear Method 核心原则，用 auto-close + auto-archive 自动出清；且明确**不做手动归档**，理由是多数人把归档当垃圾桶用（[Linear Changelog 2021-04-15](https://linear.app/changelog/2021-04-15-auto-archive-cycles-and-projects-and-deleting-issues)）。auto-close 有保护条件：属活跃 cycle / 未完成 project 的问题不关闭（[Linear Docs: Delete and archive](https://linear.app/docs/delete-archive-issues)）。

**【共识】Jira 一侧的官方口径偏向“持续精炼 + 归档”而非“设上限”。** Atlassian 把 backlog 定义为持续演化、定期 review/refine 的优先级列表（[Atlassian: Product backlog](https://www.atlassian.com/agile/scrum/backlogs)）；Jira Data Center 管理文档直言把 Done/Resolved 的问题归档是 good practice，可避免 “clutter your Jira”（[Archiving an issue (DC)](https://confluence.atlassian.com/adminjiraserver/archiving-an-issue-968669980.html)）。**但两家都没给出可执行的数字容量线**——Atlassian 的 backlog 页通篇没有条目数量建议（**未找到权威来源**给出官方容量阈值）。

**【共识】GitHub 官方不给过期治理，只给状态语义。** 官方只有 Completed / Not planned 两种关闭状态，not planned 覆盖 duplicate、out of scope、invalid、won’t fix（[GitHub Docs: Closing an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/closing-an-issue)）。规模治理完全外挂给 Actions 与检索谓词。

**【争议】Jira backlog 膨胀的“解法”是社区共识而非厂商承诺。** 主因被归结为流程而非工具（把 backlog 当 idea graveyard），主流解法是本轮检索中反复出现的四条：区分 intake 与开发库、Definition of Ready 准入、bulk-archive/close 超期项、定期 grooming——均出自社区讨论（如 [Atlassian Community 相关帖](https://community.atlassian.com/forums/Jira-questions/ARCHIVING-OLD-ISSUES-OF-JIRA/qaq-p/582136)），厂商并未背书具体阈值。

## 2. 自动关闭 / stale 策略

**【共识】默认参数并不“温和”。** actions/stale 默认：**60 天**无活动打 stale 标签 + 评论，**再 7 天**自动关闭；关闭原因默认 not_planned。它提供了大量豁免开关（exempt-issue-labels、exempt-milestones、exempt-assignees、exempt-issue-types，remove-stale-when-updated 默认 true）（[actions/stale README](https://github.com/actions/stale)）。

**【争议】“自动关闭是否伤害社区”存在一手对立。** 反方：Drew DeVault 称其为 “a terrible, horrible, no good, very bad idea”，核心论点是 issue 是**用户互助与贡献者漏斗**的空间，“未回应”是正常状态，问题数量多是受欢迎的信号而非羞耻（[GitHub stale bot considered harmful](https://drewdevault.com/blog/stalebot/)）。GitHub 官方社区至今有请愿帖要求禁止自动关 stale 的 Action，措辞是 “completely dismissive, hurts the community”（[community discussion #176678](https://github.com/orgs/community/discussions/176678)）。正方（维护者视角）此次只检索到二手博客，未取得可比强度的一手文本（**未找到权威一手来源**）。

**【推断】争议焦点不是“自动”，是“无判断地关”。** 可迁移的折中：已被确认的问题必须豁免（label / milestone），关闭理由必须显式，且关闭不得锁贴——这三项恰好对应 actions/stale 的现成配置项。

## 3. 归档（archiving）模式

**【共识】三大平台对“归档”的定义都是 close-as-move：移出主列表 + 只读/可恢复，而非删除。** Jira Cloud 归档后只出现在 Archived work items 且**不可编辑**，restore 后重新出现在 backlog/boards（[Archive a work item](https://support.atlassian.com/jira-software-cloud/docs/archive-an-issue/)）。Linear 的 auto-archive 由系统托管、周期可配（[Delete and archive](https://linear.app/docs/delete-archive-issues)）。GitHub **没有 archive 层**，只能用 is:closed / reason: / updated: 等检索谓词模拟（[Searching issues](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)）。

**【推断】index + shard（索引 + 分片）是文档型 backlog 的等价拓扑。** 平台靠统一检索兜底可检索性，纯文件系统没有这层兜底；因此按年/季度分片时必须另建常驻 index（ID + 标题 + 状态 + 去向），否则“归档”会退化为“找不到”。tombstone（墓碑）的等价物是 Linear/Jira 的归档记录本身：条目仍在、只是不参与主列表渲染。

## 4. 变更日志与待办的职责边界

**【共识】Keep a Changelog 的立场是原文级的硬立场。** “Changelogs are for humans, not machines”；用 commit diff 当 changelog 是 bad idea，因为“commit 的目的是一步步记录源码演进，而 changelog entry 的目的是记录跨多个 commit 的、值得注意的差异”。规范含六分类（Added/Changed/Deprecated/Removed/Fixed/Security）与顶部 Unreleased 段（[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)）。

**【共识】Conventional Commits 与 Changesets 是机器管线，不宣称为人读文本。** Conventional Commits 把 feat / fix / BREAKING CHANGE 显式映射 SemVer 的 MINOR / PATCH / MAJOR（[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)）；Changesets 用 .changeset 的 markdown 片段“声明版本意图”，把**意图与发布步骤解耦**，再生成包 changelog（[changesets.dev](https://changesets.dev/)）。

**【推断】两者的判据是“时态与述说对象”，不是“详略”。** Changelog 写已发生（“已经变了”）且面向使用者；待办写未发生（“可能会做”）且面向维护者。混写的双向损伤是：用户把待办读成承诺，维护者被 Changelog 的完成时措辞绑住。建议物理隔离文件、仅在条目上用 ID 互引。

## 5. 决策记录的生命周期

**【共识】MADR 的 supersede 是“状态字段 + 新记录”，不是编辑旧记录。** 模板 status 取值明列 proposed | rejected | accepted | deprecated | … | superseded by ADR-0123，ADR 编号顺序化、单目录存放（[MADR](https://adr.github.io/madr/)、[MADR 模板](https://github.com/adr/madr/blob/develop/template/adr-template.md)）。

**【共识】PEP / Rust RFC 用状态机承载“过时但须可追溯”。** PEP 1：Deferred 是“无进展”（可被 editor 退回 Draft，偶有复活）；Rejected **仍保留在 PEP 索引中作为决策与理由的档案**；Superseded 通过新旧 PEP 的 Superseded-By: / Replaces: 头部互指；一旦到达 Accepted/Final/Rejected/Superseded 便**不再实质修改**，转为历史文档（[PEP 1](https://peps.python.org/pep-0001/)）。Rust 的等价规则是：“once accepted, RFCs should not be substantially changed”，实质变化必须开新 RFC 并在原 RFC 加注（[rust-lang/rfcs README](https://github.com/rust-lang/rfcs)）。

**【推断】超期退场与取代退场是两条通道。** 前者按**时间**退场（§3 的归档），后者按**被取代**退场（§5 的 supersede + 墓碑指针）。backlog 需要两者都有，不要把被新方案取代的条目当成“过期垃圾”清理掉。

## 6. 代码内 TODO / FIXME 治理

**【共识】主流风格指南要求 TODO 必须带可追溯标识符。** Google C++ Style Guide：TODO 必须全大写并紧跟 bug ID、人名、邮箱或票据，推荐 // TODO: bug 12345678 - ...；若写“将来某时做”，**必须**给出具体日期或具体触发事件（[Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)）。

**【共识】TODO 会腐烂有实证支撑。** ACM 论文测得开源仓库中约 **46.7%** 的 TODO 评论为低质量（含糊、缺信息、对开发者无用），且大量 TODO 长期未解决或长期滞留（[What Makes a Good TODO Comment?](https://dl.acm.org/doi/10.1145/3664811)）；TDCleaner 专门识别“任务已完成但忘记删除”的 obsolete TODO，作者明确指出其会误导团队并可能引入缺陷（[arXiv:2108.05846](https://arxiv.org/abs/2108.05846)）。SATD（自我承认的技术债）概念源自 Potdar & Shihab 的 ICSME 2014 研究，以 TODO/FIXME/HACK/XXX 关键词挖掘（[IEEE 6976075](https://ieeexplore.ieee.org/document/6976075)）。

**【未验证】ripgrep 门禁 / todo bot 没有权威一手规范。** 检索只得到聚合页与个人教程，未找到官方标准（**未找到权威来源**）。可安全复用的规则源是 Google 风格指南那句“必须带票据或具体日期/事件”，它本身就能翻译成一条正则门禁。

---

## 可迁移到 backlog / 待办文档设计的原则

1. **入口先收口**：新条目先进“待分诊区”，只有 accept / decline / duplicate / snooze 四种出口，绝不直接落进主列表。
2. **退场是默认结局**：为每条目预设到期条件（时间或事件），到期未复现即归档或关闭，而不是等人工想起。
3. **关闭 ≠ 删除，但必须有理由**：关闭动作带显式理由（completed / not planned + 一句说明），原文保持可查。
4. **归档自带检索兜底**：分片归档时同步维护常驻 index（ID + 标题 + 状态 + 去向），否则归档等于信息消失。
5. **确认类条目豁免自动清理**：已人工确认或被认领的条目标记豁免，自动策略只处理无人认领的悬置项。
6. **超期退场与取代退场分开**：时间导致的归档与方案被取代的 supersede 不可混用同一动作。
7. **取代只加不改**：旧条目正文冻结，仅追加 “superseded by <ID>”，新条目反向引用，裁决链永不断。
8. **待办与 changelog 物理分文件**：待办写“将要做”面向维护者，changelog 写“已发生”面向使用者，两者仅靠 ID 互引。
9. **代码 TODO 必须带追踪号或具体截止事件**：禁止“以后修”这类无锚点 TODO，并把同一条规则做成扫描门禁。
10. **容量不设硬上限，设“腐烂”上限**：管理无活动滞留比例与时龄分布，而非条目总数——因为没有任何权威来源给出过数字容量线。
