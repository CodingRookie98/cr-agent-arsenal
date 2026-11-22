# 文档治理故障排查 (How-To)

> **文档控制信息**
> - **文档标识**: HOW-TROUBLESHOOT-DOC-GOV-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-11-22 | DSH AI Agent | 王辉 | 初版：按症状索引的排障手册（12 类真实故障） |

---

**适用场景**：门禁报错看不懂、结果自相矛盾、或行为与文档描述不一致。按**症状**查，不按脚本查。

## 症状索引

| 症状 | 跳到 |
| :--- | :--- |
| 真值轴返回 rc=2 | [浅克隆](#浅克隆导致真值轴-rc2) |
| 真值轴说 drifted，但我刚改过文档 | [同提交语义](#真值轴说-drifted但我刚改过) |
| 删了锚点才变绿 | [墓碑违规](#删锚点后门禁变绿) |
| 机器地图永远不一致 | [生成物含自身](#机器地图永远不一致) |
| 断链指向的目录明明存在 | [目录链接规则](#断链指向目录但目录存在) |
| 修订历史越裁剪越乱 | [滑动窗口](#修订历史裁剪后版本对不上) |
| hook 不生效 | [hooksPath](#pre-commit-hook-不生效) |
| hook 拒绝提交但门禁是绿的 | [工作树与索引不一致](#hook-拒绝提交但门禁是绿的) |
| 体量门禁把老文档判红 | [棘轮基线](#体量门禁把老文档判红) |
| 可回答性 GAP 一堆 | [GAP 不是故障](#可回答性-gap-一堆) |
| 文档状态判我非法 | [状态机取值](#文档状态判非法) |
| Python 报编码错误 | [跨平台编码](#windows-下-python-报编码错误) |

## 浅克隆导致真值轴 rc=2

```text
❌ 错误: 检测到浅克隆（shallow repository），历史提交时间不可得，无法判定漂移。
```

真值轴靠 git 提交时间判断「锚点在复核之后有没有被改」，浅克隆只有 tip，会把一切锚点判成漂移。

**处置**：

```bash
git fetch --unshallow        # 已有仓库
# 或克隆时完整拉取
git clone <url> <dir>        # 不要加 --depth 1
```

CI 里设 `fetch-depth: 0`（GitHub Actions）或等价配置。**不要**为了过门禁而删除锚点。

## 真值轴说 drifted，但我刚改过

两种可能：

1. **你只改了文档，没改锚点** → 正常，锚点没变本来就不该 drift，检查是否别的提交动了锚点文件。
2. **你在同一次提交里改了锚点和文档** → 需要同时刷新「复核于」行。判据是：锚点与文档的最后提交 SHA 相同 **且** 「复核于」行在该提交中被改过。只加一行注释不算。

```bash
# 看某文档的复核点与锚点文件的最后提交
grep '复核于' docs/explanation/architecture/x-design.md
git log -1 --format='%h %cd' -- skills/doc-governance/SKILL.md
```

## 删锚点后门禁变绿

**这是违规**。体量基线墓碑（`.doc-truth-baseline.json`）记录了所有声明过的锚点，删除或缩减会被判「墓碑违规」：

```text
⛔ 基线墓碑违规（声明被删除/缩减）: explanation/architecture/x.md 缺失: skills/xxx/SKILL.md
```

正确动作：复核断言。内容仍成立 → 只刷新「复核于」；不成立 → 改文档。真要彻底移除某锚点，须用 `--write-baseline` 显式重建并在提交信息登记原因。

## 机器地图永远不一致

常见原因：手改了 `docs/llms.txt` 或 `docs/_llms/*.md`；或新增了文档但没重生成。

```bash
python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --split
```

若重生成后仍不一致，检查是否有 `.MD` / `.markdown` 后缀的文件（生成器只扫 `.md`），或 `_llms/` 下有多余的嵌套文件（会被判多余）。

## 断链指向目录但目录存在

本仓库规则：**链接指向目录时，该目录必须有 `index.md` 或 `README.md`**。否则视为断链。

处置：在该目录建一个索引（推荐用脚手架自动生成）：

```bash
python3 skills/doc-governance/scripts/manage-doc-index.py ensure --root docs --dir how-to
```

## 修订历史裁剪后版本对不上

`trim-revision.py --fix` 只裁剪**行数**，不改控制头版本号。裁剪后控制头可能仍写着被删掉的那一版。

处置：确认控制头版本 == 修订表最新行（第一行）版本。不一致就改控制头。

```bash
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
```

## pre-commit hook 不生效

```bash
git config --get core.hooksPath    # 期望输出 .githooks
ls -l .githooks/pre-commit         # 期望有可执行位
```

若为空：`git config core.hooksPath .githooks`。若无执行位：`chmod +x .githooks/pre-commit`。

## hook 拒绝提交但门禁是绿的

hook 会先检查「工作树是否等于索引」：

```text
🚫 工作树存在未暂存改动，pre-commit 校验结果不可信：
```

原因：门禁读工作树，你提交的是索引，二者不一致时门禁结论没有意义。**处置**：`git add` 后再提交。

## 体量门禁把老文档判红

若该文档此前已登记在 `docs/.doc-size-baseline.json`，应只报「存量，基线内未恶化」的警告。判红说明：

- 文档**变大了**（超出基线记录）→ 需要拆分或改掉超长单行；
- 或基线里**没有**这条记录 → 属于新增超限。

确实无法立即拆分时（须在提交信息说明原因）：

```bash
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --write-size-baseline
```

## 可回答性 GAP 一堆

GAP 表示知识库**确实缺**这类内容，不是脚本坏了。正确动作是登记 backlog：

```bash
python3 skills/doc-governance/scripts/manage-backlog.py create "知识库缺口：<主题>" --type Feature --priority P2
```

**不要**为了消 GAP 写空壳文档——那只会把缺口变成噪音。

## 文档状态判非法

```text
⛔ 文档状态违规: x.md: 文档状态取值非法（Deprecated），只允许 Active/Contested/Superseded
```

三态只有 `Active` / `Contested` / `Superseded`。另外：

- `Superseded` 必须带 `取代于`（仓库内相对路径、非自身、目标存在）；
- `Active` 不得带 `取代于`；
- `Contested` 建议带 `争议点`。

## Windows 下 Python 报编码错误

所有脚本入口已显式设 UTF-8，但若你在自己的脚本里调用它们：

```python
import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')
```

另：生成器写盘固定 LF（`newline='\n'`），以保证与版本库 blob 一致——不要在中间环节用文本模式改写。

## 还是不行

1. 跑 `python3 skills/doc-governance/scripts/check-all.py --full`，把完整输出留下；
2. 看 [GOVERNANCE.md](../GOVERNANCE.md) §4.1 的豁免表——有些目录**故意**不参与计分（reviews / _llms / AGENTS.md / backlog / reference/articles）；
3. 仍无解则登记 backlog 并附完整输出与复现命令。
