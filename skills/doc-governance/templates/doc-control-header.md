# 文档控制头模板 (Document Control Header Template)

> **用途**：为**不经** `scripts/scaffold-doc.py` 生成的手写／迁移文档补齐控制头与修订历史，使其通过 `scripts/check-doc-control-sync.py`。骨架中的 `<...>` 为必填槽位，落地时不得保留槽位文本。

## 1. 骨架（复制到文档 H1 之后）

> **状态字段的用法（骨架里只留 `文档状态: Active`，其余按需自行添加）**：
> - `文档状态` ∈ `Active` / `Contested` / `Superseded`（缺省 Active）；
> - 声明 `Superseded` 时**必须**同时加一行 `> - **取代于**: ./new-doc.md`——仓库内相对路径、可带 `#锚点`、禁止绝对路径与 `..` 越界；
> - 声明 `Contested` 时建议加 `> - **争议点**: <一句话>`；
> - **不要在骨架里预置这两行**：`Active` 携带 `取代于` 会被门禁判为矛盾（C-3）；
> - 不要在控制头里写行内 HTML 注释——注释文本会被解析器并入取值。

```markdown
> **文档控制信息**
> - **文档标识**: REF-<NAME>-<YYYY>
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: YYYY-MM-DD
> - **文档所有者**: <所有者>
> - **来源**: <raw/… 或上游提案路径>（可选）
> - **代码锚点**: <src/a.py:120-168>, <src/b.py>（可选）
> - **复核于**: YYYY-MM-DD / commit <sha>（可选）

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | YYYY-MM-DD | <修订人> | <审核人> | 初版发布：<一句话说明> |
```

## 2. 填写规则（机械门禁相关）

1. **控制头版本号必须逐字等于修订历史最新行的版本号**——`check-doc-control-sync.py` 只做这一条断言，漂移即 Exit 1 阻断。
2. **修订历史最多保留最近 5 行**（GOVERNANCE 红线）；超额用 `python3 skills/doc-governance/scripts/trim-revision.py --root docs --fix --keep 5` 裁剪最早一行。
3. **版本号语义**：破坏性变更升 Major，新增内容升 Minor，文字修正升 Patch。
4. **文档标识**按象限前缀命名（如 `REF-` 参考、`REVIEW-ARCHIVE-` 归档索引），全库唯一。
5. 控制头是**文档自身**的元数据；象限索引与 `docs/index.md` 各自独立演进——跨文档版本跟随**无机械门禁**，必须人工同步（象限索引未跟随成员文档升版时不会被拦截）。
6. **真值三字段（可选，声明即受检）**：`来源` / `代码锚点` / `复核于` 由 `check-doc-drift.py` 消费（RFC-0005）。
   - 锚点按**仓库根**解析，禁止绝对路径与 `..`；多个锚点用 `,`/`、`/`;` 分隔，可带行区间 `:120-168`；
   - `复核于` 记 `YYYY-MM-DD / commit <sha>`，commit 存在时以提交时间判定漂移（而非文件 mtime）；
   - **未声明 ≠ 通过**：未声明锚点的文档不参与真值分，`audit-doc-health.py` 会显式报「未启用」。
7. **文档状态三态（RFC-0007）**：`Active`（缺省）/ `Contested` / `Superseded`。
   - `Superseded` 必须填 `取代于`（仓库内相对路径、非自身、目标存在），否则**阻断**；
   - `取代于` 只能出现在 `Superseded` 文档上，否则**阻断**；
   - `Contested` 建议填 `争议点`，超 90 天未更新会在「未决冲突清单」标超期（不阻断）；
   - 取值不在这三态内即阻断（防手误写 `Deprecated`）。

## 3. 验证

```bash
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
```

退出码 `0` 表示全库控制头与修订历史零版本漂移。
