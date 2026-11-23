# 可选技能依赖与缺失处置 (Optional Skill Dependencies)

> `Align` / `Plan`（原 P-1 / P0 / P0.5 / P1）会联动外部技能。它们是**增强件，不是安装前提**：缺失时按本文探测与处置，
> 不得假定其存在，也不得因缺失跳过门禁或伪称已激活。

## 1. 依赖清单

| 阶段 | 外部技能 | 来源仓库 | 缺失时的后果 |
|:---:|---|---|---|
| **Align（原 P-1）** | `brainstorming` | obra/superpowers | 方案对比门禁无执行体 |
| **Align（原 P0）** | `grilling`（`/grill-me`） | mattpocock/skills | 方案压力测试退化为自查 |
| **Align（原 P0.5）** | `research`（可替代 `deep-research`） | mattpocock/skills | 调研须改为会话内只读探查 |
| **Plan（原 P1）** | `writing-plans` | obra/superpowers | 计划改按本技能模板生成 |

> 清单只登记**有阶段门禁职责**的四项；其余联动技能（如 `find-docs`、`clarification-protocol`、`doc-governance`）按其自身装配状态按需使用，不纳入强制探测。

## 2. 探测（进入首个相关阶段前执行一次，不逐阶段重复）

命中任一条件即视为「已具备」：

1. 宿主技能清单中出现该技能名（宿主可见的技能索引）；
2. 技能目录下存在同名目录。

```bash
for s in brainstorming grilling research writing-plans; do
  for d in .agents/skills .claude/skills "$HOME/.claude/skills"; do
    test -d "$d/$s" && echo "present: $s ($d)"
  done
done
```

探测结果是**事实**：写入计划头部的 `Active Checkpoint` 备注，不改变阶段顺序，也不构成跳过门禁的理由。

## 3. 缺失处置（按交互能力三分支）

| 分支 | 触发条件 | 动作 |
|:---:|---|---|
| **A 交互可用** | 主会话且宿主提供提问工具（如 `ask_user_question`） | 一次性列出缺失项与安装命令，询问是否安装。**用户同意** → 等待安装完成后再进入该阶段；**用户拒绝** → 转分支 B 并登记 |
| **B 交互不可用** | 子智能体、外部无头 CLI 派发、批处理，或宿主无提问原语 | **不提问**，直接按第 4 节内联规程执行（子代理下调提问原语会被宿主拒绝，硬问即流程停摆） |
| **C 安装失败** | 命令报错、无网络、无 `npx` | 记录失败原因，转分支 B，并在报告中标注「依赖缺失 + 已降级」 |

安装命令（在目标项目根目录执行，`<agent>` 取当前宿主标识）：

```bash
npx --yes skills@latest add -y https://github.com/obra/superpowers --skill brainstorming --agent <agent> --full-depth
npx --yes skills@latest add -y https://github.com/mattpocock/skills --skill grilling --agent <agent> --full-depth
```

> 本仓库工作区内可整组安装：`python3 tools/skills-manager/skills_manager.py install -f superpowers -a <agent>`。

## 4. 内联最小规程（B / C 分支的替代物）

缺失不改变门禁，只替换执行体；逐项对应：

- **替代 `brainstorming`**：给出 2~3 个方案对比（权衡 / 成本 / 回滚），取得 User Nod 后方可继续；
- **替代 `grilling`**：自列 ≥5 条隐式假设逐条证伪，未决项登记为显式默认假设；
- **替代 `research`**：本地检索 → `gh search repos|code` → 官方文档，产出分析文档落盘至 `docs/explanation/analysis/`；
- **替代 `writing-plans`**：按 [goal-plan-template.md](../templates/goal-plan-template.md) 生成计划。

## 5. 铁律

1. **缺什么问什么，但只问一次**：同一会话内不重复追问；用户给出拒绝即视为已决策，不再回问。
2. **缺失不是跳过门禁的理由**：门禁照常执行，只替换执行体。
3. **降级必须留痕**：写入计划头部 `Active Checkpoint`，注明「依赖缺失 → 分支 B/C」。
4. **不得伪称已激活**：未真实调用该技能时，计划与报告中禁止出现「已按 `writing-plans` 生成」类表述。
