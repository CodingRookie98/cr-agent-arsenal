# 文档控制头模板 (Document Control Header Template)

> **用途**：为**不经** `scripts/scaffold-doc.sh` 生成的手写／迁移文档补齐控制头与修订历史，使其通过 `scripts/check-doc-control-sync.py`。骨架中的 `<...>` 为必填槽位，落地时不得保留槽位文本。

## 1. 骨架（复制到文档 H1 之后）

```markdown
> **文档控制信息**
> - **文档标识**: REF-<NAME>-<YYYY>
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: YYYY-MM-DD
> - **文档所有者**: <所有者>

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

## 3. 验证

```bash
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
```

退出码 `0` 表示全库控制头与修订历史零版本漂移。
