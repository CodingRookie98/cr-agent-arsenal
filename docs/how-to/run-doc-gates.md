# 执行文档门禁并解读失败 (How-To)

> **文档控制信息**
> - **文档标识**: HOW-RUN-DOC-GATES-2026
> - **当前版本**: V2.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-24
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V2.0.0** | 2026-11-24 | AI Agent | 王辉 | 随 Wave 2C（ADR-0005）切换至本仓 `scripts/doc-gates/check-all.py` 三道门禁，移除 `llms.txt`/版本一致/真值轴/体量棘轮过时说明 |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：门禁的用途、命令与失败处置对照表 |

---

**适用场景**：提交前、交付前、或 CI 里跑门禁；以及门禁红了不知道该改什么。

## 一条命令跑全部

```bash
python3 scripts/doc-gates/check-all.py          # 三道本仓门禁（断链 / 健康体检 / 可回答性）
python3 scripts/doc-gates/check-all.py --full   # 追加 pytest skills/ scripts/ -q 全量单测
python3 scripts/doc-gates/check-all.py --quiet  # 成功时静默，只报失败
```

退出码：0 全绿；1 有门禁失败；2 用法/环境错误。

也可单独运行公共技能里的跨仓通用断链扫描器：

```bash
python3 skills/doc-governance/scripts/check-doc-links.py --root docs --exclude project/reviews
```

## 装成 pre-commit（推荐）

```bash
git config core.hooksPath .githooks
```

之后每次 `git commit` 都会先跑门禁。临时跳过用 `git commit --no-verify`，**须在提交信息登记原因**。

> hook 会拒绝「工作树有未暂存改动」的提交——因为门禁校验的是工作树，而你提交的是索引，二者不一致时结果不可信。先 `git add` 再提交。

## 三道门禁与失败处置

| 门禁 | 载体脚本 | 查什么 | 失败时改什么 |
| :--- | :--- | :--- | :--- |
| **断链** | `skills/doc-governance/scripts/check-doc-links.py` | 相对链接目标是否存在、`.md` 后缀、`#锚点`、目录入口 | 按输出的「文件:行号」逐条修；目录链接要求该目录含 `index.md` 或 `README.md` |
| **健康体检** | `scripts/doc-gates/check-doc-health.py` | RFC-0007 三态状态机、RFC-0008 体量上限（≤64 KB / ≤1,000 字符）、`docs/AGENTS.md` ≤30 行守卫 | 按报错逐项修正状态字段、拆分超限文档或修剪 `docs/AGENTS.md` |
| **可回答性** | `scripts/doc-gates/check-golden-tasks.py` | 20 条「知识库能否答出这类问题」机械断言 | `FAIL` 立即修；`GAP` 是真实缺口，登记 backlog 而非当场补写 |

## 分场景处置

### 物理断链与目录链接失败

```text
📄 【how-to/example.md】:
   第 12 行 | 链接文本: '指南' ➔ 目标: './missing.md'
   ↳ 错误原因: 目标路径不存在 (404 Not Found)
```

1. 确保所有相对链接保留 `.md` 后缀且从当前文件所在目录正确解析；
2. 若链接指向目录（如 `../reference/rules/`），确保该目录下存在 `index.md` 或 `README.md`；
3. 若带 `#anchor`，确认目标文件存在对应标题。

### 体量超限（RFC-0008）

```text
❌ 体量超限 [project/plans/x.md]: 72100 字节 > 65536
```

* **单文档 > 64 KB（65,536 字节）**：按「总纲 + 子册」拆分为多篇文档并互相链接；
* **最长单行 > 1,000 字符**：按语义或标点边界折行；
* 行数 `> 800` 仅作警告，不阻断；`docs/reference/articles/**` 与 `docs/project/reviews/**` 已豁免。

### 文档状态机违规（RFC-0007）

* `文档状态` 只允许 `Active` / `Contested` / `Superseded`（缺省视同 `Active`）；
* `Superseded` 必须填写文档根（`--root`，如 `docs/`）内真实有效的 `.md` 相对路径 `取代于`（不能指向自身或越出文档根目录）；
* `Active`（含缺省）不得携带 `取代于`。

### 路由文件守卫失败

`docs/AGENTS.md` 超过 30 行或缺少 `读取顺序` / `硬约束` 二级小节时会直接失败。保持其仅存路由顺序、硬约束与门禁命令，领域知识请移入对应象限。

### 可回答性 GAP

```text
🕳️ G-12 某个操作的具体步骤是什么？ —— how-to 象限为空（操作类知识缺位）
```

GAP **不是门禁故障**，是知识库真的缺这块内容。正确动作：通过 `python3 scripts/backlog/manage-backlog.py create ...` 登记 backlog 卡片，按优先级排期——不要为了消 GAP 当场写一篇空壳文档。

## CI 用法

```bash
python3 scripts/doc-gates/check-all.py --full
```

CI 与 pre-commit 共用同一入口；`--full` 会顺序执行 3 道文档门禁并追加 `python3 -m pytest skills/ scripts/ -q`。
