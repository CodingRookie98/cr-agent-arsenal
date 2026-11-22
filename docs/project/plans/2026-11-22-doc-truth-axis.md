# 文档真值轴（来源/代码锚点/漂移检测）实施计划

> **文档控制信息**
> - **文档标识**: PLAN-DOC-TRUTH-AXIS-2026
> - **当前版本**: V1.9.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-11-22
> - **代码锚点**: skills/doc-governance/scripts/check-doc-drift.py, skills/doc-governance/scripts/audit-doc-health.py
> - **复核于**: 2026-11-22 / commit 8b48bdb

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: **Heavy Track**（跨模块：新增脚本 + 改写既有评分引擎 + 技能/规程/模板同步）
> - **需求源**: [RFC-0005](../../proposals/RFC-0005-doc-truth-axis.md)（In Review）+ [LLM-WIKI 调研报告](../../explanation/analysis/llm-wiki-implementation-research.md) §7
> - **范围裁定**: 调研报告 **P0 三项**（P-1 提问超时未获答复，按「P0 三项」默认假设执行并登记，见 §6 D-01）
> - **执行后端**: 当前会话内联（P3 后端提问同批超时，按默认假设登记，见 §6 D-02）
> - **创建日期**: 2026-11-22
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准基线**: `feat/doc-truth-axis` @ `2360b32`
> - **状态**: 已完成（2026-11-22，终审 **Blockers=0 / 准予交付**）

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)

- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P5 完成（六轮审查闭环：R1 → R2 → Delta → 放行确认 → 收口确认 2）
- **当前活跃子任务**: 无（交付完成；后续非阻断项见 §9）
- **当前子任务重试计数**: 0/3（无触发；R1 阻断项一轮修复，未触发 3-Tries）
- **门禁基线（改动前实测）**: `check-doc-links` rc=0（93 文件）｜`check-doc-control-sync` rc=0｜`audit-doc-health` PASS 100/100｜`pytest skills/doc-governance/tests` 161 passed
- **批次进度**: A-1 ✅ / A-2 ✅ / A-3 ✅ / A-4 ✅ / A-5 ✅ / A-6 ✅ / A-7 ⏳
- **实测（R1 收口后）**: `check-doc-drift.py --fail-on-drift` → 声明 3/46、fresh 3、drifted 0、真值分 15.0/15、rc=0；`audit-doc-health.py`（warn）→ PASS；`--truth=require` → REJECTED（覆盖率 6.5% < 50%，符合设计）；`pytest skills/doc-governance/tests` → **182 passed**

---

## 1. 目标与非目标

**目标**：让知识库第一次具备**可机械测定的真值轴**——文档能声明自己依赖哪些代码、何时被复核过；工具能回答「哪些文档的依赖已经变了」，并在需要时阻断。

**非目标**（明确不做，防止范围蔓延）：分层 `llms.txt`、`docs/AGENTS.md`、检索层/MCP、矛盾状态扩展、并发软锁、golden task 评测。

## 2. 方案要点

```text
控制头（三可选字段）            check-doc-drift.py                audit-doc-health.py
来源 / 代码锚点 / 复核于   ──▶   声明 → 锚点存在性 → git 提交时间   ──▶  truth 块（独立双轴）
                                 → drifted / missing / unverified        --truth=warn|require
```

关键设计（对应 RFC §3–§4）：① 结构分 `total_score` 语义**不变**；② 真值分独立报告、默认 warn；③ 零声明 ⇒ `enabled=false` 且分数 0（不颁发满分）；④ 豁免域与既有 `project/reviews/**` 一致。

## 3. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: **HIGH**（改写公共评分引擎的输出契约 + 新增门禁脚本；下游消费者：CI 脚本、`doc-governance` 技能、GOVERNANCE 规程）
- **强制执行级别**: **L0 + L1 + L2 + L3 + L-Doc**
- **豁免测试级别**: 无
- **精确验证命令清单**:
  1. L0: `python3 -m py_compile skills/doc-governance/scripts/*.py`
  2. L1: `python3 -m pytest skills/doc-governance/tests/test_doc_drift.py -q`
  3. L2: `python3 -m pytest skills/doc-governance/tests -q`（含临时 git 仓库集成用例）
  4. L3: 在真实 `docs/` 上跑 `check-doc-drift.py --json` + `audit-doc-health.py --truth=warn`，核对退出码与真值块
  5. L-Doc: `check-doc-links.py` / `check-doc-control-sync.py` / `generate-llms-txt.py` / `audit-doc-health.py`
- **豁免充分理由**: 不适用（本改动触及公共输出契约，按矩阵「修改公共接口/核心领域契约」行强制 L2，并因 CLI 面向用户追加 L3）

## 4. 原子任务清单

- [x] **A-1** 新增 `check-doc-drift.py` 纯函数层：`parse_truth_fields` / `normalize_anchor` / `classify_doc`；先写 13 条失败测试（RED 实测 13 failed）
- [x] **A-2** 补齐 CLI 与 git 适配层：`--root/--repo/--json/--fail-on-drift/--max-age-days`；退出码 `0/1/2`；L2 用临时 git 仓库验证「复核后新增提交 ⇒ drifted」
- [x] **A-3** `audit-doc-health.py` 接入真值块：`truth` 字典 + `--truth=warn|require|off` + `--truth-threshold`；`evaluate_verdict` 单一出口扩展；L1 断言 AC-1/AC-5（+ require 模式未启用即阻断）
- [x] **A-4** 模板与规程：`templates/doc-control-header.md` 增三字段与规则 6；`references/change-impact-matrix.md` 新增矩阵行 V1.3.0
- [x] **A-5** 技能与治理文档同步：`SKILL.md`（模式 1/2 + 漂移步）、`GOVERNANCE.md` V1.7.0（§3 工具表 + §4 红线 7）
- [x] **A-6** 自证：`GOVERNANCE.md`、`doc-governance-design.md` V1.4.0、本计划三处登记锚点，真值轴非空（3/46、15.0/15）
- [x] **A-7** P3.5/P4/P5：全量门禁 + 六轮对抗审查（最终 **Zero Blockers**）+ 索引/llms.txt 归档

## 5. 验收命令

```bash
python3 skills/doc-governance/scripts/check-doc-drift.py --root docs --repo . --json
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --truth=warn
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/check-doc-control-sync.py --root docs
```

预期：漂移脚本 rc=0（当前无「已声明且漂移」文档）；健康 PASS；测试全绿；断链 0；零版本漂移。

## 6. 执行偏差记录 (Deviation Log)

| 编号 | 偏差 | 原因 | 处理 |
| :--- | :--- | :--- | :--- |
| **D-01** | P-1 范围提问超时未获答复，按「P0 三项」执行 | 交互不可用；用户指令已明确「按调研报告 + goal-loop 开工」 | 记录为显式默认假设；若需扩至 P1/P2，另立 RFC |
| **D-02** | P3 执行后端未获答复，按「当前会话内联」执行 | 同上 | 记录为显式默认假设 |
| **D-03** | 真值分**不合并**进 `total_score`（偏离调研报告 P0-3 权重表） | 零锚点基线下合并会把健康分打到 ~75 并触发阈值阻断，逼出伪锚点 | RFC §3 已论证；合并留待覆盖率 ≥50%（D-4） |
| **D-04** | 不建「可回答性」维度 | 依赖 golden task 集（调研 P2-8），空维度会稀释真值轴 | RFC D-5 |
| **D-05** | 根级入口文档改为「仅未声明锚点时豁免」 | `GOVERNANCE.md` 声明了锚点却因文件名被排除，会让真值轴出现静默覆盖黑洞 | 已回写 RFC §4.2（V0.1.1） |
| **D-06** | 门禁开关实现为 `--truth=require`，而非 RFC 初稿的 `--require-truth` | 与 `--truth` 三态（off/warn/require）合并为一个参数，避免两个开关互相矛盾 | 已回写 RFC §4.3（V0.1.1） |
| **D-07** | 测试断言从「硬编码 ≥80 分」改为「开/关真值轴的 total_score 相等」 | 固件文档缺控制头时结构分本就 <80，硬编码阈值测的是夹具而非契约 | 已落 `test_ac1_zero_declared_scores_zero_without_touching_structure_score` |
| **D-08** | 日期型 `复核于` 改按**当日末刻**起算 | R1-1：按 UTC 零点起算会让「同日复核 + 同日提交」必判漂移，本仓三处自证文档当场反转为 drifted | 已修 + 回归用例 |
| **D-09** | require 模式新增 `--min-coverage`（默认 0.5） | R1-2：删掉失败文档的锚点声明可把真值分从 7.5 洗成 15.0，文字红线无法机械拦截 | 已修 + 回归用例 |
| **D-10** | 浅克隆显式 fail-closed（rc=2） | R1-3：`--depth 1` 下 `git log -1 -- path` 返回克隆 tip，100% 假漂移；RFC 承诺的 rc=2 此前未实现 | 已修 + 回归用例 |
| **D-11** | 真值阻断理由并入 `has_issues` 链 | R1-4：require 下会同时打印「完美」与 REJECTED（BK-0028 禁止的并存） | 已修，输出互斥 |
| **D-12** | 锚点分隔符改为「逗号仅后接空白」才切分 | 加固：`src/a,b.py` 这类合法路径会被切碎（R1 未列，代码自检发现） | 已修 + 回归用例 |
| **D-13** | 新增锚点基线（墓碑）`<root>/.doc-truth-baseline.json` | R2-1：覆盖率下限只挡住「跌破阈值」，12 篇夹具删 2 条锚点后覆盖率恰为 0.5000 即可放行；墓碑改为「登记过就不许消失」 | 已修 + 2 条回归用例 |
| **D-14** | 未跟踪锚点落 `unverified`，不再算 fresh | R2-2：`git log` 对未跟踪文件返回空 → 旧实现判 fresh，提交同一内容后立刻 drifted | 已修 + 回归用例 |
| **D-15** | `--fail-on-drift` 同时覆盖 `missing_anchor` 与墓碑违规 | R2-3：锚点被删除/移动（矩阵第 7 行标题场景）在旧实现里 rc=0 | 已修 + 回归用例 |
| **D-16** | 判定梯收敛为 `truth_blockers()` 单点 | R2：`main()` 复制了 `evaluate_verdict` 的判定链，违背 BK-0028「单一判定出口」 | 已修，两处共用 |
| **D-17** | 围栏内示例不再被解析为声明 | R2-3（文档即输入）：教程/模板里的控制头骨架会被当成真登记 | 已修 + 回归用例 |

## 8. 争议焦点与升级裁决（铁律 6）

**现状**：四轮独立审查全部返回真实阻断项，且每轮抓到的都是不同层的问题：

| 轮次 | 阻断项 | 性质 | 状态 |
| :--- | :--- | :--- | :--- |
| R1 红队 | 4×P1 | 语义/环境（同日复核、覆盖率、浅克隆、文案互斥） | 已修 + 回归 |
| R2 元审判 | 3 Blockers | 判定结构（墓碑缺失、未跟踪锚点、硬断裂） | 已修 + 回归 |
| Delta 终审 | 1 P1 | 信任锚可缺席（账本 missing/corrupt 与无违规同形） | 已修 + 回归 |
| 放行确认 | 1 P1 | 信任锚可被清空（空账本绕过墓碑） | 已修 + 回归 |

**升级理由**：按 goal-loop 铁律 6，同一模块连续 3 轮未清零阻断项即须升级人类裁决；本单元已是第 4 轮，**主智能体不自行宣布放行**。

**争议焦点（需人类裁决）**：

1. **墓碑的信任锚仍是单一可编辑文件**。空账本已堵，但「账本滞后」（新增声明未登记）无法由账本自身发现——这是设计固有上限，不是实现缺陷。是否接受？
2. **--write-baseline 是唯一一键刷新口**，也是唯一能洗掉真实删除的命令。当前靠「提交信息登记原因 + 代码评审」约束，属流程约束而非机械约束。是否接受？
3. **剩余 P2 未修**：--fail-on-drift 不覆盖 unverified（R2D-5）、glob/目录锚点会硬红（R2D-6）、墓碑归属计数失真（R2D2-2）。建议登记 Backlog，不在本次交付内。
4. **是否合并计分**：当前真值轴与结构分并置（warn 默认），require 下本仓会因覆盖率 6.5% 被拒。是否在锚点覆盖率达到阈值后合并为单一分数？

**人类裁决（2026-11-22）**：选择 **B 继续收口**。已执行：R2D-5（门禁非 fresh 即阻断，`--allow-unverified` 显式豁免）、R2D-6（glob/占位符锚点落 unverified、目录锚点受支持、修正 `src/**` 被当加粗抹掉）、R2D2-2（墓碑归属精确化）、R2D-4 残留（audit 增 `--repo`），提交 `3120d5a`；待放行确认 2。

**可选裁决**：

- **A 准予交付**：接受上述 4 条为已知边界，P2 项登记 Backlog；本次交付测试全绿、四轮审查凭据齐全。
- **B 继续收口**：先修 R2D-5/R2D-6 再交付（预计再一轮审查，可能牵出新 P2 链）。
- **C 降级交付**：只保留 --truth=warn 报告能力，删 require 门禁（减少承诺面，真值轴失去强制力）。

---

## 7. 回滚方案

功能以「新增文件 + 新增可选开关」为主，回滚路径为：删除 `check-doc-drift.py` 与对应测试 + 撤销 `audit-doc-health.py` 中的 `truth` 块（`--truth=off` 亦可等价关闭）。**不动** `total_score` 与既有退出码语义，因此不存在数据迁移回滚。

## 9. 后续待办（非阻断，交付后登记）

以下缺陷由放行确认 2 判为 P2/P3（默认门禁下不构成阻断），未在本次交付内处理：

| 编号 | 定级 | 现象 | 触发条件 | 建议动作 |
| :--- | :--- | :--- | :--- | :--- |
| R2D56-1 | P2 | classify_doc 的 unverifiable 短路在 missing/drifted 之前，glob 锚点可盖住同文档的真实漂移 | 仅当 --allow-unverified 进入常规门禁时升级 P1 | **已修**：不可核验锚点只退出判定集，不短路整篇；同文档真实锚点照常判 drifted |
| R2D56-3 | P2 | 加粗真实锚点（两端加星号）被任意 * 判为 glob → unverified 假红 | 手写控制头时使用加粗 | **已修**：两端 `**` 且内部无 `*` 先剥离加粗，再判 glob |
| R2D56-4 | P2 | 散文锚点（如「见附录 A」）仍 missing_anchor 硬红 | 文档把锚点写成描述而非路径 | **已修**：非路径形态归 `invalid` 并落 unverified，不计 missing |
| R2D56-2 | P3 | --allow-unverified 生效时零痕迹（stdout 逐字节相同） | 任何使用该参数的门禁 | **已修**：强制打印豁免行（JSON 走 stderr） |

**状态（2026-11-22 追加）**：四项均已修复并带回归测试（`TestFollowupP2P3` 4 条）。**随后定向红队（Light）判定 1 个 P1**：R2D56-4 的 invalid 判据过度矫正（含空格/中文的合法路径被静默丢弃，删文件后仍 rc=0）——已改为「不像路径」判据并补 6 条回归（`TestR3Fixes`），全量 209 passed。R3-2/3/5 同批收口；`TestFollowupP2P3` 重复定义（4 条从未被收集）已删。**R3 Delta 复核再判 1 个 P1（R3D-1，本次修复引入的回归）**：`Makefile:2` 这类「根级无扩展名文件 + 行区间」被新判据误判 invalid 而漏检——已改为「先剥行区间再判形态」，并同批收 R3D-3/4 与明细可定位性，全量 214 passed。R3D-2（`A/B 测试` 类散文含 `/` 被判路径 → 硬红）按有意假红接受并登记。**R3D 确认判 0 Blockers / 准予交付**，但其残留风险 1 指同一族事故已三次（R3-1 → R3D-1 → R3DC-1），故追加 **R3DC-1 根治**：锚点判据顺序改为「存在性 → 基线登记 → 形态」，字符类白名单降为最后兜底，全量 217 passed。剩余已知边界见 §8 争议焦点第 1、2 条（账本滞后不可自检、`--write-baseline` 属流程约束），属设计固有上限，不再单独立项。
