# ADR-0003: 退役 `spec-evolution` 技能并将核心哨兵下沉至共享测试

> **ADR 控制元数据**
> - **决策编号**: 0003
> - **当前版本**: V1.0.0
> - **当前状态**: Accepted
> - **决策所有者**: 核心架构组
> - **决议日期**: 2026-11-23
> - **取代历史文档**: [RFC-0004 spec-evolution 演进回路](../../proposals/RFC-0004-spec-evolution.md) · [spec-evolution 架构设计书](../architecture/spec-evolution-design.md)
> - **关联实施计划**: [2026-11-23-retire-spec-evolution.md](../../project/plans/2026-11-23-retire-spec-evolution.md)

---

## 1. 背景与上下文 (Context and Problem Statement)

`spec-evolution` 于 2026-10-12 依据 RFC-0004 立项交付，原定位是补齐提示词与技能演进回路的「选择端」。但运行一个多月后，实证暴露出四项结构性失配：

1. **不可外部复用，却占用公开技能发行面**：采集器与判定器硬编码绑定本仓库的 `contexts/AGENTS.md`、`cr-agent-arsenal.json`、`test_cross_skill_links.py` 与 `doc-governance` 脚本路径。外部用户通过 `npx skills` 或 `skills-manager` 安装后，只增加了 379 字符元数据上下文开销，在外部项目中无法运行。
2. **零真实使用**：RFC-0004 V0.6.0（2026-11-12）撤回未实现的 `goal-loop` P5 挂载时已记录「自 2026-10-14 起 30 天内真实执行 0 次、影响交付决策 0 次」。
3. **输出全为已知噪声**：2026-11-23 实跑 `collect-facts.py --no-gates` + `judge.py`，共产出 5 条 MID findings（`C-04` 2 条、`C-06` 3 条），全部已在 BK-0041 裁定 `wontfix`（接受偏离），且 `RFC-0008` 已废止文档行数阻断指标。
4. **维护成本与体量倒挂**：`skills/spec-evolution/` 占 12 个文件、2,851 行代码与 84 条用例（单测耗时约 16.73s），历史归档中累积了大量围绕其自身边界缺陷与跨平台超时/编码问题的修复卡片（BK-0033~BK-0038、BK-0040、BK-0043、BK-0046、BK-0047、BK-0050）。

与此同时，逐条审计其 C-01~C-10 判据发现：
- **已被替代（3 项）**：`C-02`（设计书存在性）已被 `check-golden-tasks.py` `G-08` 覆盖；`C-08`（跨技能相对链接）已被 `test_cross_skill_links.py` 覆盖；`C-09`（门禁聚合）已被 `check-all.py` 与 `.githooks/pre-commit` 覆盖。
- **噪声/误报/弱约束（4 项）**：`C-03` 对纯规程技能易误报、`C-04` 与 `C-06` 已裁定 `wontfix`、`C-10` 对 `contexts/AGENTS.md` 仅依赖静态 `baseline.json` 人工对账。
- **真实盲区（3 项）**：`C-01`（技能具备 `tests/test_*.py`）、`C-05`（`description < 1024` 与 YAML 合法性）、`C-07`（四处注册面同步）目前无其他门禁覆盖。

---

## 2. 考虑的备选方案 (Considered Options)

* **方案 A（选定）：退技能、留哨兵** —— 删除 `skills/spec-evolution/` 及其公开注册，将 `C-01`/`C-05`+YAML/`C-07` 浓缩为 `skills/_shared/tests/test_skill_surface_sentinels.py` 并纳入常规 `pytest` 运行。
* **方案 B（未采纳）：裸删且不迁移任何校验** —— 直接移除技能，放弃对新增技能缺测试、超长/非法 YAML、漏注册面的机械检查。
* **方案 C（未采纳）：降级为内部脚本保留** —— 保留 `skills/spec-evolution/` 目录但不分发，仍需长期维护两千余行脚手架与重复判据。

---

## 3. 最终决策与裁决 (Decision Outcome)

选定 **方案 A**：

1. 物理移除 `skills/spec-evolution/` 与本地悬空软链接 `.agents/skills/spec-evolution`，并将公开技能集合由 8 个收敛为 7 个（`cr-agent-arsenal.json`、`README.md`、`docs/index.md`、`install-skills.md`、`quick-start.md`、`cross-skill-link-policy.json`、`test_cross_skill_links.py`）。
2. 新增 `skills/_shared/tests/test_skill_surface_sentinels.py`（约 250 行含负向自检），在每次 `pytest skills/` 时以毫秒级成本机械守卫：
   - **C-01**：每个技能存在 `tests/test_*.py`（含非 `_shared` 目录必含 `SKILL.md` 校验）；
   - **C-05 + YAML**：`SKILL.md` frontmatter 为合法 YAML（覆盖未引号 `": "` 陷阱）、`name` 与目录一致、`license == MIT`、`description` 非空且 `< 1024` 字符；
   - **C-07**：实际技能目录集合与 `test_cross_skill_links.py::SKILL_NAMES`、`cross-skill-link-policy.json`、`cr-agent-arsenal.json`、`README.md`、`docs/index.md` 五处注册位点双向严格一致（同时防漏登记与残留幻影条目）。
3. 放弃 `C-02`/`C-03`/`C-04`/`C-06`/`C-08`/`C-09`/`C-10` 及其独立采集-判定-报告基础设施；`RFC-0004` 与 `spec-evolution-design.md` 按文档状态机流转为 `Superseded`，保留历史溯源，并保留 `docs/project/reviews/` 下的 Write-Once 审查凭据原貌。

### 3.1 积极后果 (Positive Consequences)

* 消除了 2,851 行高维护成本的非复用代码与 16.73s 的重复子进程测试开销；
* 外部用户安装包不再注入无法在外部生效的技能元数据；
* 保留了全部 3 条真正不可替代的技能交付面与注册面硬防线，且 `C-07` 从单向查漏升级为双向严格集合对齐。

### 3.2 消极后果与已知代价 (Negative Consequences / Trade-offs)

* 不再自动比对 `contexts/AGENTS.md` 与 `baseline.json` 的行数/字节数增长（`C-10`）；该文件准入判据回归人工评审把关（`contexts/AGENTS.md` 第 3 行明文约束）。
* 哨兵测试仅针对本仓库布局生效（`skills/_shared/` 本身不参与外部 `npx skills` 技能分发，故无跨仓可用性问题）。

---

## 4. 修订历史 (Revision History)

| 版本号 | 修订日期 | 修订人 | 修订描述 |
| :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-23 | AI Agent | 正式裁决退役 `spec-evolution` 技能，将 `C-01`/`C-05`+YAML/`C-07` 哨兵下沉至 `skills/_shared/tests/` |
