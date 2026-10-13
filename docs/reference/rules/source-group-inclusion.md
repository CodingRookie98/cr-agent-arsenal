# 来源组收录判据 (Source-Group Inclusion Criteria)

> **文档控制信息**
> - **文档标识**: REF-SOURCE-GROUP-INCLUSION-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-10-13
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.0.0** | 2026-10-13 | AI Agent | 核心架构组 | 由 `tools/skills-manager/README.md` 迁入，确立为本判据唯一事实来源 |

---

> ⚠️ **机器真理源声明**: 本文档为预设来源组收录判据的唯一事实来源，供维护者与 AI 智能体判定来源组能否进入缺省预设 `common` 使用。

## 1. 适用对象与登记基准 (Scope & Baseline)

| 项 | 内容 |
| :--- | :--- |
| 约束对象 | `tools/skills-manager/collections/*.json` 中**新增或变更**的来源组（source group） |
| 登记基准 | `2026-10-13`；基准日之前既有 `common` 来源组维持现状，不因本判据追溯失效 |
| 缺省预设事实 | `-f` / `--file` 缺省即指向 [`collections/common.json`](../../../tools/skills-manager/collections/common.json)（见 [`skills_manager.py`](../../../tools/skills-manager/skills_manager.py) 的 `SKILLS_JSON_PATH` 与 argparse 缺省值）；该预设内容被默认安装，并占用使用者的技能目录与上下文预算 |

## 2. 收录判据 (Inclusion Criteria)

来源组进入 `common` 需**同时**满足下列四条：

| 编号 | 判据 | 判定口径 |
| :--- | :--- | :--- |
| **C-1** | 即装即用 | 不要求使用者先安装某个外部产品／商业工具链才能生效；缺少该工具时不得成为惰性条目 |
| **C-2** | 增量能力 | 提供缺省基线尚不具备的能力，而非重做已有能力（含本仓库 `skills/` 自有技能与 `common` 既有来源组）；触发场景、交付物与所需工具链三者相同即视为重做 |
| **C-3** | 厂商中立命名 | 技能名（`names` 条目，含前、中、后缀）不带厂商／产品品牌；`source` 是仓库地址、必然含组织名，不适用本条 |
| **C-4** | 粒度克制 | 不得把「以操作某个厂商／产品为唯一目的」的成套技能搬进基线；面向多主题的通用技能合集可整源收录 |

安装语义：`mode: "all"` 的来源组按整源安装（`names` 不参与安装，实际安装条目在安装时确定）；其余来源组按 `names` 逐条安装。

## 3. 唯一例外 (Sole Exception)

某项技能**同时**满足下列三条时，可突破 C-1 与 C-3：

1. 是该第三方 CLI／API 的第一方唯一入口；
2. 技能自带安装与调用说明；
3. 不绑定特定智能体宿主。

`common` 既有适用项：`firecrawl-search`（[firecrawl/cli](https://github.com/firecrawl/cli)）、`context7-cli` 与 `find-docs`（[upstash/context7](https://github.com/upstash/context7)，同一来源组）、`agent-browser`（[vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)）。

## 4. 厂商／产品专用成套技能的去向 (Vendored Suite Placement)

面向单一厂商或产品的成套工作流／记录／任务技能不进 `common`，应独立成一个预设文件，按需 `-f <preset>` 安装。独立预设**仅豁免 C-1 与 C-3**，仍须满足 C-2 与 C-4。

既有独立预设：`superpowers.json`（第三方通用方法论合集）、`frontend-slides.json`、`document-illustrator.json`（第三方单技能）。

## 5. 登记同步 (Registration Sync)

来源组或 `names` 条目数发生变化时，必须同步 [`README.md`](../../../README.md) §3 的计数注释。计数口径为 `names` 条目数；`mode: "all"` 组按整源安装，实际安装数另计。
