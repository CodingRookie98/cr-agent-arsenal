# 来源组收录判据 (Source-Group Inclusion Criteria)

> **文档控制信息**
> - **文档标识**: REF-SOURCE-GROUP-INCLUSION-2026
> - **当前版本**: V1.2.0
> - **文档状态**: Active
> - **生效日期**: 2026-10-13
> - **文档所有者**: 核心架构组

---

### 修订历史记录 (Revision History)

| 版本号 | 修订日期 | 修订人 | 审核人 | 修订描述 |
| :--- | :--- | :--- | :--- | :--- |
| **V1.2.0** | 2026-10-13 | AI Agent | 核心架构组 | 订正 C-3 与安装语义的事实错误（`mode: "all"` 的 `names` 实为点名白名单 + 整组卸载清单，而非「不参与安装」），并显式登记 C-3 实际约束面；§1 补取证边界；§4 收敛独立预设豁免范围并补齐非 `common` 预设实况；§5 C-4 基准补「个人／组织维护的通用合集」 |
| **V1.1.0** | 2026-10-13 | AI Agent | 核心架构组 | 闭合 C-3 作用域（`mode: "all"` 组不适用）与「变更」语义；品牌口径扩至个人／组织；补例外条件判定式、`mode: "all"` 组 C-4 审计基准与预设 opt-in 边界 |
| **V1.0.0** | 2026-10-13 | AI Agent | 核心架构组 | 由 `tools/skills-manager/README.md` 迁入，确立为本判据唯一事实来源 |

---

> ⚠️ **机器真理源声明**: 本文档为预设来源组收录判据的唯一事实来源，供维护者与 AI 智能体判定来源组能否进入缺省预设 `common` 使用。

## 1. 适用对象与登记基准 (Scope & Baseline)

| 项 | 内容 |
| :--- | :--- |
| 约束对象 | `tools/skills-manager/collections/*.json` 中**新增或变更**的来源组（source group）。「变更」指对既有来源组的条目增删改；组内**未变更**的既有条目维持现状，不因该次变更受审 |
| 登记基准 | `2026-10-13`；基准日之前既有 `common` 来源组维持现状，不因本判据追溯失效 |
| 缺省预设事实 | `-f` / `--file` 缺省即指向 [`collections/common.json`](../../../tools/skills-manager/collections/common.json)（见 [`skills_manager.py`](../../../tools/skills-manager/skills_manager.py) 的 `SKILLS_JSON_PATH` 与 argparse 缺省值）；该预设内容被默认安装，并占用使用者的技能目录与上下文预算 |
| 取证边界 | C-1／C-2／C-4 与第 3 节三条件的判定依据（技能正文、来源仓库整体性质、维护方归属）均在本仓库之外，须以来源仓库的公开内容取证；证据不可得时记「未取证」，不得默认通过 |

## 2. 收录判据 (Inclusion Criteria)

来源组进入 `common` 需**同时**满足下列四条：

| 编号 | 判据 | 判定口径 |
| :--- | :--- | :--- |
| **C-1** | 即装即用 | 不要求使用者先安装某个外部产品／商业工具链才能生效；缺少该工具时不得成为惰性条目 |
| **C-2** | 增量能力 | 提供缺省基线尚不具备的能力，而非重做已有能力（含本仓库 `skills/` 自有技能与 `common` 既有来源组）；触发场景、交付物与所需工具链三者相同即视为重做 |
| **C-3** | 厂商中立命名 | 技能名（`names` 条目，含前、中、后缀）不带厂商／产品／个人或组织品牌；`source` 是仓库地址、必然含组织名，不适用本条。本条按**本次变更涉及的技能名**判定，且只约束「按 `names` 逐条安装」的路径（见下） |
| **C-4** | 粒度克制 | 不得把「以操作某个厂商／产品为唯一目的」的成套技能搬进基线；面向多主题的通用技能合集可整源收录 |

安装语义（据 [`skills_manager.py`](../../../tools/skills-manager/skills_manager.py) 的 `install` / `uninstall` 分支实测）：`install` 不带 `-s` 时，`mode: "all"` 组按整源安装（`add -y <source> --full-depth`，`names` 不参与），`mode: "names"` 组按 `names` 逐条安装；`install -s <skill>` 以 `names` 为白名单反查来源后按名安装；`uninstall` 不带 `-s` 时以**全部 `names`** 作为卸载清单。故 `mode: "all"` 组的 `names` 是「点名安装白名单 + 整组卸载清单」，**不决定缺省安装面**——缺省路径下的实际装入集合由上游仓库当下内容决定。C-3 的实际约束面因此限于按 `names` 逐条安装的来源组与新增来源组的命名选择：`mode: "all"` 组随缺省预设整源装入的技能名（现有 45 条）不受 C-3 审，其品牌耦合风险由 C-4 按来源组整体性质判定（见第 5 节）。

## 3. 唯一例外 (Sole Exception)

某项技能**同时**满足下列三条时，可突破 C-1 与 C-3：

1. 是该第三方 CLI／API 的第一方唯一入口：技能由该产品的维护方在其官方仓库内发布，且同一来源组内的多项技能（如 `context7-cli` 与 `find-docs`）按同一入口合并判定；
2. 技能自带安装与调用说明：技能正文含可直接执行的安装与调用命令，使用者无需查阅仓库外文档即可生效；
3. 不绑定特定智能体宿主：不依赖特定宿主的 hook、私有配置目录或专有安装路径，仅使用通用技能目录与标准 CLI。

`common` 既有适用项：`firecrawl-search`（[firecrawl/cli](https://github.com/firecrawl/cli)）、`context7-cli` 与 `find-docs`（[upstash/context7](https://github.com/upstash/context7)，同一来源组）、`agent-browser`（[vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser)）。

新增适用项须在本节登记其满足上述三条的书面依据（登记基准 2026-10-13）。

## 4. 厂商／产品专用成套技能的去向 (Vendored Suite Placement)

面向单一厂商或产品的成套工作流／记录／任务技能不进 `common`，应独立成一个预设文件，按需 `-f <preset>` 安装。独立预设**仅豁免 C-1 与 C-3**（opt-in 安装，其内容可绑定特定宿主或产品工具链，不受第 3 节例外条件的约束）；C-2（相对缺省基线的增量）仍是其存在理由；C-4 只约束基线收录面，不对独立预设成立。

既有非 `common` 预设 7 个：`architecture.json`、`frontend.json`、`cr-agent-arsenal.json`（用途细分）、`superpowers.json`（第三方通用方法论合集）、`frontend-slides.json`、`document-illustrator.json`（第三方单技能）、`video_creation.json`（`remotion-dev/skills` 等产品工具链套件 —— 厂商套件走独立预设的既有先例）。

## 5. 登记同步 (Registration Sync)

来源组或 `names` 条目数发生变化时，必须同步 [`README.md`](../../../README.md) §3 的计数注释。计数口径为 `names` 条目数；`mode: "all"` 组按整源安装，实际安装数另计。

`mode: "all"` 组的 C-4 审计以其来源仓库的整体性质为基准：**多主题通用合集**（含个人／组织维护者发布的通用工程合集）归入可整源收录，**单一厂商或产品套件**归入第 4 节；实际安装集随上游演进，不构成对既有收录的回溯违规。
