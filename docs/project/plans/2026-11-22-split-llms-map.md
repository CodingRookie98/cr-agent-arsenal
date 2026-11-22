# 分层机器地图（RFC-0006）实施计划

> **文档控制信息**
> - **文档标识**: PLAN-SPLIT-LLMS-MAP-2026
> - **当前版本**: V1.2.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-11-22

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: **Heavy Track**（新增生成器模式 + 改写一致性门禁 + 新增路由文件 + 规程同步）
> - **需求源**: [RFC-0006](../../proposals/RFC-0006-split-llms-map.md)（In Review）+ [调研报告](../../explanation/analysis/llm-wiki-implementation-research.md) §7 P1-5
> - **执行后端**: 当前会话内联
> - **批准基线**: `feat/doc-truth-axis` @ `9ca589f`
> - **状态**: 已完成（2026-11-22，Delta 复核 **Blockers=0 / 准予交付**）

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)

- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P5 完成（Light 红队 3×P1 → Delta 复核 0 Blockers）
- **当前活跃子任务**: 无（交付完成）
- **当前子任务重试计数**: 0/3（无触发）
- **门禁基线（改动前实测）**: drift rc=0（3/46、15.0/15）｜audit PASS 100/100｜links rc=0｜sync rc=0｜pytest 217 passed｜`docs/llms.txt` 21,810 B / 92 条
- **批次进度**: A-1 ✅ / A-2 ✅ / A-3 ✅ / A-4 ✅ / A-5 ✅ / A-6 ✅ / A-7 ✅
- **实测（交付时）**: 根 21,810 → **883 字节**；6 个子地图（explanation 4,618 / other 538 / project 15,060 / proposals 1,880 / reference 1,462）；pytest **229 passed**；四道门禁 rc=0 / PASS

---

## 1. 目标与非目标

**目标**：根 `llms.txt` 从「全集清单」降为「象限入口」，体量恒定在 8 KB 以内；全量条目下沉 `_llms/`，并由门禁保证根与子地图逐字节同步。

**非目标**：检索层、MCP、`llms-full.txt`、多语言、按角色分层。

## 2. 方案要点

```text
docs/llms.txt（根，≈1-2 KB）       docs/_llms/<section>.md（全量条目）
  6 个象限节 + 篇数 + 子地图链接  ←→  与现行单文件条目格式逐字一致
                  ↑
          docs/AGENTS.md（≤30 行，只写读取顺序与硬约束）
```

关键设计（对应 RFC §4）：① 默认模式零破坏；② 根/子/路由三层职责单一；③ 多文件集合比对门禁；④ 体量超限不落盘。

## 3. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: **HIGH**（改写机器地图生成器与一致性门禁；下游：CI、doc-governance 技能、GOVERNANCE 规程）
- **强制执行级别**: **L0 + L1 + L2 + L3 + L-Doc**
- **豁免测试级别**: 无
- **精确验证命令清单**:
  1. L0: `python3 -m py_compile skills/doc-governance/scripts/*.py`
  2. L1: `python3 -m pytest skills/doc-governance/tests/test_llms_split.py -q`
  3. L2: `python3 -m pytest skills/doc-governance/tests -q`（含既有 llms 契约测试回归）
  4. L3: 真实 `docs/` 上跑 `--split` → 根 ≤8192 B、6 个子地图、`--check` rc=0；再手改子地图验证门禁报错
  5. L-Doc: links / control-sync / drift / audit 四道门禁

## 4. 原子任务清单

- [x] **A-1** 生成器重构为纯函数 `build_llms_map(root, project_name, split) -> Dict[rel_path, content]`；`generate_llms_txt` 改为调用它后写盘（默认模式产物必须逐字节不变）
- [x] **A-2** 实现 split 渲染：根（象限节 + 篇数 + 子地图链接 + 可选象限索引）、子地图（H1 + 上级链接 + 全量条目）；空象限删子文件
- [x] **A-3** CLI：`--split`、`--max-root-bytes`（默认 8192）、`--check`（只校验不写盘）；体量超限不落盘 + exit 1
- [x] **A-4** `audit-doc-health.py` 一致性门禁改多文件比对（根 + 全部子地图；多余/缺失均判漂移）+ 根体量缺陷
- [x] **A-5** 新增 `docs/AGENTS.md`（≤30 行，只写读取顺序与硬约束）；audit 断言行数与必需小节
- [x] **A-6** 迁移：对真实 `docs/` 执行 `--split` 生成；`docs/index.md` 与 `llms.txt` 互链同步
- [x] **A-7** 规程同步（GOVERNANCE / SKILL / 变更矩阵 / 模板）+ P3.5/P4/P5 门禁与审查

## 5. 验收命令

```bash
python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --split
python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --split --check
wc -c docs/llms.txt docs/_llms/*.md
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
python3 -m pytest skills/doc-governance/tests -q
```

预期：根 ≤8192 B；6 个子地图；`--check` rc=0；audit PASS；全量测试绿。

## 6. 执行偏差记录 (Deviation Log)

| 编号 | 偏差 | 原因 | 处理 |
| :--- | :--- | :--- | :--- |
| D-01 | 体量门限改为仅 split 下默认生效 | 红队 S-3：默认模式被 8192 接管，RFC §7 的回滚命令（无 `--split` 重生成）直接 rc=1 | 已修 + 回归用例 |
| D-02 | 根文件落 `--output` 完整路径 | 红队 S-1：此前恒写 `<dir>/llms.txt`，基名被丢弃且身份闸门读 A 写 B | 已修 + 回归用例 |
| D-03 | 删除 `audit-doc-health.py` 中重复定义的三个函数 | 红队 S-2：`check_llms_map_consistency` 定义两次，后者覆盖前者导致提示缺 `--split`、split 地图不可收敛 | 已修 + 回归用例 |
| D-04 | 描述链接排除任意 scheme 与 `//host` | 红队 S-4：`tel:`/`ftp:`/协议相对 URL 被改写为静默断链 | 已修 + 回归用例 |
| D-05 | `_llms/` 递归检测嵌套多余文件 | 红队 S-5：嵌套子目录成为免检静默区 | 已修 + 回归用例 |
| D-06 | `--check`/清理改 `rglob`，与 audit 同口径 | Delta SD-1：检测面递归而清理面单层 ⇒ audit 常红、`--check` 常绿，提示不收敛 | 已修 + 回归用例 |
| D-07 | AC-1 改用独立 oracle（硬编码期望全文） | Delta SD-2：原用例比较「新函数」与「已改为调用新函数的旧入口」，同义反复 | 已修，变异测试可打红 |
| D-08 | `--check` 回显实际基名 | Delta SD-3：自定义 `--output` 时提示错位 | 已修 |
| D-09 | audit 补根体量判据 + 符号链接目录检测 | Delta SD-5/SD-6：契约 §4.5 未实现；symlink 子目录绕过 rglob | 已修 + 回归用例 |
| D-10 | RFC 登记 S-4 对默认模式产物的有意偏差 | Delta SD-4：`//host` 描述下默认模式产物差 2 字节，「逐字节同产物」需限定 | 已登记 |

## 7. 回滚方案

删除 `docs/_llms/`，以默认模式重生成根文件（一条命令）即可回到单文件形态；生成器默认行为未变，故无数据迁移回滚。
