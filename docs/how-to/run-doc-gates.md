# 执行文档门禁并解读失败 (How-To)

> **文档控制信息**
> - **文档标识**: HOW-RUN-DOC-GATES-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：六道门禁的用途、命令与失败处置对照表 |

---

**适用场景**：提交前、交付前、或 CI 里跑门禁；以及门禁红了不知道该改什么。

## 一条命令跑全部

```bash
python3 skills/doc-governance/scripts/check-all.py          # 六道门禁（实测约 1.5 s）
python3 skills/doc-governance/scripts/check-all.py --full   # 追加 pytest 全量（约 30 s）
python3 skills/doc-governance/scripts/check-all.py --quiet  # 成功时静默，只报失败
```

退出码：0 全绿；1 有门禁失败；2 用法/环境错误。

## 装成 pre-commit（推荐）

```bash
git config core.hooksPath .githooks
```

之后每次 git commit 都会先跑门禁。临时跳过用 git commit --no-verify，**须在提交信息登记原因**。

> hook 会拒绝「工作树有未暂存改动」的提交——因为门禁校验的是工作树，而你提交的是索引，二者不一致时结果不可信。先 git add 再提交。

## 六道门禁与失败处置

| 门禁 | 查什么 | 失败时改什么 |
| :--- | :--- | :--- |
| **机器地图** | docs/llms.txt 与 docs/_llms/*.md 是否等于生成器产物（逐字节） | 重跑 generate-llms-txt.py --split（见下） |
| **断链** | 相对链接目标是否存在、.md 后缀、#锚点 | 按输出的「文件:行号」逐条修；目录链接要求该目录有 index.md |
| **版本一致** | 控制头版本号 == 修订历史最新行版本号 | trim-revision.py --fix --keep 5，或手工同步 |
| **真值轴** | 声明了「代码锚点」的文档是否在锚点变更后复核过 | 复核断言并刷新「复核于」；**禁止删除锚点**（会被墓碑判违规） |
| **健康体检** | 元数据、孤儿文档、体量、状态机、backlog 编号 | 按报告逐项修；体量超限见下 |
| **可回答性** | 20 条「知识库能否答出这类问题」断言 | FAIL 立即修；GAP 是真实缺口，登记 backlog 而非当场补写 |

## 分场景处置

### 机器地图不一致

说明有人手改了 llms.txt 或 _llms/*.md，或改了文档没重生成。直接重生成（不要手改）：

```bash
python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --split
```

### 真值轴 drifted

```text
- [drifted] explanation/architecture/x-design.md  ←  skills/doc-governance/SKILL.md
```

含义：SKILL.md 在该文档的「复核于」之后又被改过。处置：

1. 打开文档，确认里面的断言是否仍然成立；
2. 若成立：只把控制头的「复核于」改成当前提交（`2026-11-22 / commit <sha>`）；
3. 若不成立：改文档内容，再刷新「复核于」；
4. **不要**为了变绿而删掉「代码锚点」——基线墓碑会判违规。

### 体量超限

```text
⛔ 文档体量超限: project/plans/x.md: 127747 字节 > 65536（新增超限，无基线记录）
```

- **新增超限**：拆分文档（总纲 + 子册），或改掉超长单行（> 1000 字符）；
- **存量超限**：若确实暂时无法拆，用 --write-size-baseline 登记为棘轮基线，**并在提交信息说明原因**；基线只降不升。

```bash
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --write-size-baseline
```

### 版本漂移

控制头写 V1.2.0，修订表最新行却是 V1.1.0。把两者改成一致，或跑：

```bash
python3 skills/doc-governance/scripts/trim-revision.py --root docs --fix --keep 5
```

### 可回答性 GAP

```text
🕳️ G-12 某个操作的具体步骤是什么？ —— how-to 象限为空（操作类知识缺位）
```

GAP **不是门禁故障**，是知识库真的缺这块内容。正确动作：登记 backlog 卡片，按优先级排期——不要为了消 GAP 当场写一篇空壳文档。

## CI 用法

```bash
python3 skills/doc-governance/scripts/check-all.py --full
```

无需另写脚本：CI 与 pre-commit 共用同一入口。注意 actions/checkout 默认浅克隆会让真值轴 fail-closed（rc=2），需设 fetch-depth: 0。
