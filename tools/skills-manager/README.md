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
