# 5 分钟上手：装好技能，跑通门禁，读懂一份文档 (Tutorial)

> **文档控制信息**
> - **文档标识**: TUT-QUICK-START-2026
> - **当前版本**: V1.0.3
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.3** | 2026-11-24 | AI Agent | 王辉 | 随 Wave 2C（ADR-0005）将门禁入口更新为 `scripts/doc-gates/check-all.py`（3 项），将文档定位改用 `docs/AGENTS.md` → `docs/index.md` → 象限索引，移除已退役命令 |
| **V1.0.2** | 2026-11-23 | AI Agent | 王辉 | 随 `ADR-0004` 退役 `agy-delegation-workflow`，技能清单与期望输出由 7 个同步为 6 个 |
| **V1.0.1** | 2026-11-23 | AI Agent | 王辉 | 随 `ADR-0003` 退役 `spec-evolution`，技能清单与期望输出由 8 个同步为 7 个 |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：面向新人/新 agent 的最短上手路径（装技能 → 跑门禁 → 定位一份文档） |

---

本教程是一条**最短路径**：不解释为什么，只让你在 5 分钟内亲手跑通三件事。原理见 [doc-governance 设计书](../explanation/architecture/doc-governance-design.md)。

## 1. 你会得到什么

完成本教程后，你将能：

1. 把仓库里的 6 个技能装进你的 agent（或确认它们已就位）；
2. 用一条命令跑完本仓三道文档门禁，并看懂失败信息该找谁；
3. 用「路由文件 → 全局总索引 → 象限索引 → 正文」顺序，在 30 秒内定位任意一份文档。

## 2. 前置准备

- **Python 3.10+**（门禁脚本零依赖，只用标准库）
- **git**（版本库与 pre-commit hook 环境）
- 一个支持 `AGENTS.md` 的 agent（Claude Code / Codex / Cursor / Gemini / DSH 均可）

确认环境：

```bash
python3 --version   # 期望 3.10+
git --version
```

## 3. 第一步：确认技能就位

在仓库根执行：

```bash
ls skills/
# 期望看到 6 个技能目录 + _shared：
# clarification-protocol  doc-governance  dual-round-review
# frontend-qa-gate  goal-loop  taste-driven-designer
```

若你的 agent 还看不到这些技能，二选一：

```bash
# A. 本仓库内开发（软连接，改源码即时生效）
python3 contexts/install.py

# B. 装到别的项目（从 GitHub master 拉取，落到目标项目 .agents/skills/）
python3 tools/skills-manager/skills_manager.py install -f cr-agent-arsenal -a <agent> -y
```

> 两种形态**不要混用**：A 用软连接保证单一真相源；B 是给外部仓库的独立副本。详见 [README](../../README.md)。

## 4. 第二步：跑一次门禁

```bash
python3 scripts/doc-gates/check-all.py
```

期望输出（三项绿 + 一行总结）：

```text
✅ 断链
✅ 健康体检
✅ 可回答性

🏁 全部门禁通过（3 项）
```

**现在故意制造一次失败**，看清它怎么报错：

```bash
printf '\n[坏链接](./nope.md)\n' >> docs/AGENTS.md
python3 scripts/doc-gates/check-all.py
```

你会看到失败项、**文件:行号**、以及可直接复制的修复提示。随后请把刚才追加在 `docs/AGENTS.md` 末尾的测试行删除复原（或用你顺手的编辑器撤销该行，再重新跑一次 `check-all.py` 确认变绿）。

> 想看详细处置方式与失败分类，读 [执行文档门禁并解读失败](../how-to/run-doc-gates.md)。

## 5. 第三步：定位一份文档

按路由顺序走：

1. **路由入口** → 打开 [docs/AGENTS.md](../AGENTS.md)：确认读取顺序与硬约束。
2. **全局总索引** → 点进 [docs/index.md](../index.md)：按技能/Diátaxis 板块浏览全景条目。
3. **象限索引与正文** → 进入对应象限 `index.md`（存在时）或直接打开目标文档，例如 [doc-governance 设计书](../explanation/architecture/doc-governance-design.md)。

练习：用这条路径找到「提交信息该怎么写」的规范。

<details>
<summary>答案</summary>

[docs/index.md](../index.md) → §6 平台规则与不可变约束 → [reference/rules/index.md](../reference/rules/index.md) → [reference/rules/commit-evidence.md](../reference/rules/commit-evidence.md)

</details>

## 6. 下一步

| 你想做什么 | 去哪 |
| :--- | :--- |
| 装技能到别的项目 | [安装技能到宿主](../how-to/install-skills.md) |
| 门禁红了不知道怎么修 | [执行文档门禁并解读失败](../how-to/run-doc-gates.md) |
| 遇到诡异报错 | [文档治理故障排查](../how-to/troubleshoot-doc-governance.md) |
| 理解这套体系为什么这样设计 | [doc-governance 设计书](../explanation/architecture/doc-governance-design.md) |
| 新增一篇文档 | 遵循 [GOVERNANCE.md](../GOVERNANCE.md) 在对应 Diátaxis 象限创建，并同步更新 [docs/index.md](../index.md) 与象限 `index.md` |

---

**检查点**：如果你跑通了第 4 步的「故意失败」并看到文件行号、还原后重跑变绿，说明环境正确、门禁在工作。可以开始干活了。
