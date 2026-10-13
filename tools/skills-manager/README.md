# Skills Manager

针对各智能体环境（OpenCode、Claude Code、Cursor 等）的技能批量包管理工具。基于 `npx skills` 底层能力，通过预设集合实现一键批量安装、卸载与查看。

## 目录结构

```text
skills-manager/
├── skills_manager.py            # 核心管理 CLI 脚本
├── collections/                 # 技能预设清单配置 (JSON)
│   ├── common.json              # 基础通用技能集 (默认)
│   ├── cr-agent-arsenal.json      # 本仓库原创工业级核心技能集
│   ├── frontend.json            # 前端研发与设计增强
│   ├── architecture.json        # 架构与深层模块设计
│   ├── superpowers.json         # 超能力核心基线
│   ├── video_creation.json      # 视频与媒体创作
│   ├── frontend-slides.json     # HTML 网页演示文稿与 PPT 转换
│   └── document-illustrator.json # 文档智能配图与风格插画生成
└── skills_collection.md         # 候选优质技能库参考
```

## 来源组收录判据 (Source-Group Inclusion Criteria)

预设（`collections/*.json`）中的每个来源组都是一条长期承诺：`common` 是**缺省预设**（`-f` / `--file` 缺省即为 `common`），其内容会被默认安装，并占用使用者的技能目录与上下文预算。因此来源组进 `common` 需**同时**满足：

1. **即装即用**：不要求使用者先安装某个外部产品／商业工具链才能生效；缺少该工具时不得成为惰性条目；
2. **增量能力**：提供缺省基线尚不具备的能力，而非重做已有能力（含本仓库 `skills/` 自有技能与 `common` 既有来源组）；触发场景、交付物与所需工具链三者相同即视为重做；
3. **厂商中立命名**：技能名（`names` 条目，含前、中、后缀）不带厂商／产品品牌；`source` 是仓库地址、必然含组织名，不适用本条；
4. **粒度克制**：不得把「以操作某个厂商／产品为唯一目的」的成套技能搬进基线；面向多主题的通用技能合集可整源收录（`mode: "all"` 走整源安装，`names` 不参与安装）。

> **唯一例外**：当某项技能是该第三方 CLI／API 的**第一方唯一入口**、技能自带安装与调用说明、且不绑定特定智能体宿主时，可突破第 1、3 条。示例：`firecrawl-search`（firecrawl/cli）、`context7-cli` 与 `find-docs`（upstash/context7，同一来源组）、`agent-browser`（vercel-labs/agent-browser）。

**厂商／产品专用成套技能不进 `common`**：面向单一厂商或产品的成套工作流／记录／任务技能，应独立成一个预设（既有独立预设：`superpowers.json` 为第三方通用方法论合集，`frontend-slides.json`、`document-illustrator.json` 为第三方单技能），按需 `-f <preset>` 安装；独立预设仅豁免第 1、3 条，仍须满足第 2、4 条。

**适用范围**：本判据约束此后新增或变更的来源组（登记基准 2026-10-13）；既有 `common` 条目维持现状，不因本判据追溯失效。

**登记同步**：来源组或 `names` 条目数发生变化时，必须同步 `README.md` §3 的计数注释（口径为 `names` 条目数；`mode: "all"` 组按整源安装，实际安装数另计）。

## 使用方法

### 1. 查看已配置技能
```bash
# 查看默认通用技能配置 (collections/common.json)
python3 skills_manager.py list

# 查看指定预设 (可直接使用名称无需路径或后缀)
python3 skills_manager.py list -f cr-agent-arsenal
python3 skills_manager.py list -f frontend
python3 skills_manager.py list -f frontend-slides
python3 skills_manager.py list -f document-illustrator
```

### 2. 为目标智能体批量安装技能
```bash
# 为 opencode 安装通用技能 (干跑测试)
python3 skills_manager.py install -a opencode --dry-run

# 真正执行安装
python3 skills_manager.py install -a opencode

# 安装特定预设
python3 skills_manager.py install -a opencode -f cr-agent-arsenal
python3 skills_manager.py install -a opencode -f frontend
python3 skills_manager.py install -a opencode -f frontend-slides

# 安装特定单个技能
python3 skills_manager.py install -a opencode -s agent-browser
```

### 3. 批量卸载技能
```bash
# 卸载指定配置中定义的所有技能
python3 skills_manager.py uninstall -a opencode

# 卸载单个技能
python3 skills_manager.py uninstall -a opencode -s agent-browser
```
