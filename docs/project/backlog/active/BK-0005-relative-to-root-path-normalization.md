---
id: BK-0005
title: 豁免判定前执行路径根相对语义归一化
type: Governance
status: active
priority: P3
trigger: null
created_at: '2026-10-04'
closed_at: null
resolution: null
destination: null
source:
- Delta R2 R1-7
acceptance_criteria:
- 豁免判定前执行 path.resolve().relative_to(root_dir.resolve())（2 行/脚本；保持元组全等比较，禁止改前缀语义）
- 在 docs/GOVERNANCE.md 补「根相对语义，收窄根即不豁免」提示
---

## 1. 背景与问题描述

`--dir project/reviews/../../plans` 实测扫描 0 文件 rc=0，根外文档被静默豁免。

- **来源追溯**: Delta R2 R1-7
- **重要度依据**: 源自 `dual-round-review` V2.1.0 Delta R2 终审裁决「最小修法」批次。

## 2. 影响面与设计考量

影响 `skills/doc-governance/scripts/` 下全部审计脚本的路径归一化。

严格遵循 R2 YAGNI 审计指令：**严禁在同批引入裁决语义解析器、`.docignore` 配置机制或过度工程化的重构**。

## 3. 验收条件 (Definition of Done)

- [x] 路径作用域守卫：`--dir` 与 `--root` 求值后必须落在根内且真实存在，否则 exit 2（保持 resolved 全等语义，不做字符串前缀比较）
- [x] 在 docs/GOVERNANCE.md 补「根相对语义，收窄根即不豁免」提示

## 4. 结项与闭环记录

### 实施记录（2026-11-19）

**AC 的一处重新定位（须记录）**：原 AC 要求「豁免判定前执行 `path.resolve().relative_to(root_dir.resolve())`」。复核发现豁免判定 `_is_root_scan()` 本身**已经**是 resolved 全等比较（`check-doc-links.py:196-199`），真正的缺口在更前一跳：`--dir` 与 `--root` **字符串拼接**后直接喂给 `rglob`，既不验根内也不验存在性。于是：

- `--dir ../../x` 把扫描带到根外（越界面）；
- `--dir a/../nope` 静默退化为「扫描 0 个文件 + rc=0」（假绿面）。

守卫因此前移到入参处，而不是在豁免判定里再补一次归一化——后者对上述两种形态都不生效。

**实现**：`check-doc-links.py` 与 `check-doc-control-sync.py`（本仓库仅这两个脚本接受 `--dir`）各加 `_validate_target_dirs()`：对每个 `--dir` 求 `(root / raw).resolve()`，`relative_to(root.resolve())` 失败即报「越出根目录」，`exists()` 失败即报「指向不存在的路径」，任一命中 **exit 2**（与「发现断链」的 exit 1 区分：一个是用法错，一个是被测对象不合格）。

**复验**：卡片原命令 `--root docs --dir project/reviews/../../plans` → `rc=2` + 「指向不存在的路径 … → plans」（此前 rc=0 / 0 文件）。回归 4 条：越界 exit 2、不存在 exit 2、根内子目录仍只扫该子树（「共扫描 1 个」）、control-sync 同契约。doc-governance 全量 73 passed / 6 skipped。

**GOVERNANCE.md** 已补「`--dir` 作用域契约」提示：判据是 resolve 后的根相对语义，收窄根会改变豁免基线。
