# 变更联动登记模板 (Change Registration Template)

> **用途**：按 `references/change-impact-matrix.md` §3 的 Sync SOP，把一次变更的**影响面 → 同步动作 → 门禁证据**登记成可审计的一块记录（通常落在计划文件或检查点中）。`<...>` 为必填槽位。

## 1. 登记骨架

```markdown
### 变更联动登记 · <变更标识> · YYYY-MM-DD

- **变更范围**：<一句话；含受影响模块>
- **影响面扫描**：<`git diff --name-only HEAD~1` 的关键路径输出>
- **矩阵命中**：<命中的矩阵行，如「核心架构、框架与基础设施」>

| 同步类别 | 目标文件 | 动作 | 完成 |
| :--- | :--- | :--- | :--- |
| 契约镜像（reference/api、models、rules） | <路径｜不适用> | <更新的行/新增的段> | ☐ |
| 待办闭环（BK 编号移入冷区归档） | <BK 编号 + docs/project/backlog/archive/ 目标文件> | <移动 + 去向/日期> | ☐ |
| 日志追加（changelog 未发布段） | docs/project/changelog.md | <追加一句变更陈述> | ☐ |
| 版本与修订（控制头 + 修订历史 ≤5 行） | <受影响文档> | <Major/Minor/Patch> | ☐ |

- **门禁证据**：`check-doc-links.py --root docs` → Exit <0/1>；`audit-doc-health.py --root docs` → <PASS/REJECTED>（原始输出片段：<粘贴>）
- **未同步项与理由**：<无｜逐条列出并说明为何不适用>
```

## 2. 使用纪律

1. **不得只写结论**：门禁证据必须附退出码或原始输出片段，缺失即视为未验证。
2. **不适用也要写**：矩阵未命中的行写「不适用」，留空或省略会被读成遗漏。
3. **未同步项必须显式登记**：不写等于宣称已同步，属「宣称与取证同宽」违规。
4. 登记完成后才可 `git commit`；`check-doc-links.py` 返回非 0 时禁止提交。
