# 5 分钟上手：装好技能，跑通门禁，读懂一份文档 (Tutorial)

> **文档控制信息**
> - **文档标识**: TUT-QUICK-START-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：面向新人/新 agent 的最短上手路径（装技能 → 跑门禁 → 定位一份文档） |

---

本教程是一条**最短路径**：不解释为什么，只让你在 5 分钟内亲手跑通三件事。原理见 [doc-governance 设计书](../explanation/architecture/doc-governance-design.md)。

## 1. 你会得到什么

完成本教程后，你将能：

1. 把仓库里的 8 个技能装进你的 agent（或确认它们已就位）；
2. 用一条命令跑完全部门禁，并看懂失败信息该找谁；
3. 用「象限入口 → 子地图 → 正文」三层索引，在 30 秒内定位任意一份文档。

## 2. 前置准备

- **Python 3.10+**（所有门禁脚本零依赖，只用标准库）
- **git**（真值轴要读提交历史；浅克隆会 fail-closed 并返回退出码 2）
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
# 期望看到 8 个技能目录 + _shared：
# agy-delegation-workflow  clarification-protocol  doc-governance
# dual-round-review  frontend-qa-gate  goal-loop  spec-evolution  taste-driven-designer
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
python3 skills/doc-governance/scripts/check-all.py
```

期望输出（六项绿 + 一行总结）：

```text
✅ 机器地图
✅ 断链
✅ 版本一致
✅ 真值轴
✅ 健康体检
✅ 可回答性

🏁 全部门禁通过（6 项）
```

**现在故意制造一次失败**，看清它怎么报错：

```bash
printf '\n[坏链接](./nope.md)\n' >> docs/AGENTS.md
python3 skills/doc-governance/scripts/check-all.py
```

你会看到失败项、**文件:行号**、以及可直接复制的修复命令。然后撤销：

```bash
git checkout -- docs/AGENTS.md
```

> 想看真实项目的效果与失败分类，读 [门禁执行与失败解读](../how-to/run-doc-gates.md)。

## 5. 第三步：定位一份文档

三层索引，按顺序走：

1. **象限入口** → 打开 [docs/llms.txt](../llms.txt)：只有 6 个象限节，每节一个「全量清单」链接。
2. **子地图** → 点进 [docs/_llms/explanation.md](../_llms/explanation.md)：该象限所有文档的一行摘要。
3. **正文** → 选一篇读，例如 [doc-governance 设计书](../explanation/architecture/doc-governance-design.md)。

练习：用这条路径找到「提交信息该怎么写」的规范。

<details>
<summary>答案</summary>

docs/llms.txt → Reference 节 → [_llms/reference.md](../_llms/reference.md) → [reference/rules/commit-evidence.md](../reference/rules/commit-evidence.md)

</details>

## 6. 下一步

| 你想做什么 | 去哪 |
| :--- | :--- |
| 装技能到别的项目 | [安装技能到宿主](../how-to/install-skills.md) |
| 门禁红了不知道怎么修 | [门禁执行与失败解读](../how-to/run-doc-gates.md) |
| 遇到诡异报错 | [文档治理故障排查](../how-to/troubleshoot-doc-governance.md) |
| 理解这套体系为什么这样设计 | [doc-governance 设计书](../explanation/architecture/doc-governance-design.md) |
| 新增一篇文档 | `python3 skills/doc-governance/scripts/scaffold-doc.py how-to <name>` |

---

**检查点**：如果你跑通了第 4 步的「故意失败」并看到文件行号，说明环境正确、门禁在工作。可以开始干活了。
