# Proposals & RFCs (需求与设计孵化层)

> 本文件由 `generate-llms-txt.py --split` 生成，请勿手改。
> 上级入口：[../llms.txt](../llms.txt)

- [RFC-0001: dual-round-review 审查报告持久化归档契约](../proposals/RFC-0001-review-report-archive.md): `dual-round-review` 的两轮提示词模板已定义完整的报告输出契约——R1 需产出「第一性原理分析 / 红队攻击路径推演 / 潜在缺陷清单」，R2 需产出「元审查质询 / 终审裁决明细表 / 放行结论」。但**技能全流程没有任...
- [RFC-0002: dual-round-review 审查报告子智能体直写契约](../proposals/RFC-0002-subagent-direct-write.md): RFC-0001 解决了「报告全文从未落盘」，但其选定方案把写盘动作判给了**主智能体**（[RFC-0001 §3.7](../proposals/RFC-0001-review-report-archive.md)）：
- [RFC-0003: 目录级索引约定与 scaffold 索引自愈](../proposals/RFC-0003-quadrant-index-convention.md): `doc-governance` 的脚手架生成器 `scaffold-doc.sh` 在 `tutorial` 分支的产物模板中硬编码了一条跨象限链接：
- [RFC-0004: spec-evolution 技能 —— 面向提示词与技能的机械化演进回路](../proposals/RFC-0004-spec-evolution.md): 2026-10-12 在 `master`（HEAD `10359c2`）实测既有三道机械门禁，**全部 PASS**：
- [RFC-0005: 文档真值轴 —— 来源/代码锚点、漂移检测与真值分维度](../proposals/RFC-0005-doc-truth-axis.md): 调研报告给出三条硬证据，指向同一个缺口——**我们测得到「文档写得规不规范」，测不到「文档还对不对」**：
- [RFC-0006: 分层机器地图 —— 根 llms.txt 降为象限入口，全量条目下沉 llms/](../proposals/RFC-0006-split-llms-map.md): `docs/llms.txt` 当前 **21,810 字节 / 92 条**（实测），已从「精炼入口」退化为「全集清单」：
