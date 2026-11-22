# 文档状态机（RFC-0007）实施计划

> **文档控制信息**
> - **文档标识**: PLAN-DOC-STATUS-MACHINE-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-11-22

> **目标元数据**
> - **所属项目**: CR 公共技能库（cr-agent-arsenal）
> - **执行通道**: **Heavy Track**（控制头契约扩展 + 审计引擎新增判据 + 规程同步）
> - **需求源**: [RFC-0007](../../proposals/RFC-0007-doc-status-contested.md)（In Review）+ [调研报告](../../explanation/analysis/llm-wiki-implementation-research.md) §7 P1-4
> - **执行后端**: 当前会话内联
> - **批准基线**: `feat/doc-truth-axis` @ `79d031c`
> - **状态**: 进行中

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)

- **当前执行通道**: Heavy Track
- **当前活跃阶段**: P3（TDD 实现，A-1 起）
- **当前活跃子任务**: A-1 状态解析与判据纯函数（先红后绿）
- **当前子任务重试计数**: 0/3
- **门禁基线（改动前实测）**: drift rc=0（fresh 3、15.0/15）｜audit PASS 100/100｜links rc=0｜sync rc=0｜`--split --check` rc=0｜pytest 245 passed
- **批次进度**: A-1 ☐ / A-2 ☐ / A-3 ☐ / A-4 ☐ / A-5 ☐ / A-6 ☐

---

## 1. 目标与非目标

**目标**：控制头的 `文档状态` 从装饰性字段变为**有机械后果**的三态状态机；审计能输出「未决冲突清单」，让「哪份该信」从读全文降级为看状态。

**非目标**：自动矛盾检测、状态迁移审批流、`Deprecated` 等扩展状态。

## 2. 方案要点

```text
控制头 文档状态: Active | Contested | Superseded
       取代于: ./new.md      （Superseded 必填）
       争议点: 一句话         （Contested 建议）
              ↓
check_doc_status() → counts / contested / superseded / issues
              ↓
C-1 非法取值(阻断) C-2 取代于缺失或失效(阻断) C-3 Active 带取代于(阻断)
C-4 Active 引用 Superseded(警告)  C-5 Contested 超 90 天(警告)
```

## 3. 测试策略与级别裁定 (Test Scope Determination)

- **改动风险定级**: **MEDIUM**（扩展元数据契约与审计输出；不触碰真值轴与机器地图）
- **强制执行级别**: **L0 + L1 + L2 + L-Doc**
- **豁免测试级别**: **L3 E2E**（无用户交互链路；CLI 行为由 L2 覆盖）
- **豁免充分理由**: 本改动只影响审计报告与门禁判定，不改变任何运行时数据流；审计本身已是 CLI 端到端入口
- **精确验证命令清单**:
  1. L0: `python3 -m py_compile skills/doc-governance/scripts/*.py`
  2. L1: `python3 -m pytest skills/doc-governance/tests/test_doc_status.py -q`
  3. L2: `python3 -m pytest skills/doc-governance/tests -q`
  4. L-Doc: links / control-sync / drift / audit / `--split --check`

## 4. 原子任务清单

- [ ] **A-1** 新增 `check_doc_status(root)`：解析三字段、执行 C-1~C-3、收集 C-4/C-5 素材
- [ ] **A-2** 接入 `audit_health` 的 `doc_status` 块 + `evaluate_verdict` 阻断理由
- [ ] **A-3** 文本输出增「未决冲突清单」小节
- [ ] **A-4** 控制头模板与 GOVERNANCE 同步（三态取值、两新字段、三条红线）
- [ ] **A-5** 自证：把本 RFC 计划文档与至少一份文档标注为真实状态（制造非空清单）
- [ ] **A-6** 门禁 + 审查 + 归档

## 5. 验收命令

```bash
python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
python3 -m pytest skills/doc-governance/tests -q
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
```

预期：`doc_status` 块含真实计数；C-1~C-3 零违规；未决冲突清单可见；全量测试绿。

## 6. 执行偏差记录 (Deviation Log)

| 编号 | 偏差 | 原因 | 处理 |
| :--- | :--- | :--- | :--- |
| D-01 | 模板骨架不预置 `取代于`/`争议点` 与行内注释 | 红队 T-1（P1）：模板明写「复制到 H1 之后」，但注释并入取值、占位行触发 C-3 ⇒ 照模板产出必然过不了门禁 | 已修 + 端到端回归用例 |
| D-02 | `parse_frontmatter` 不再 YAML 早退 | 红队 T-2：YAML+引用块并存时引用块被整体遮蔽 | 已修 + 回归用例 |
| D-03 | 表格白名单补状态机三字段 | 红队 T-3：表格形态的状态声明完全失明 | 已修 + 回归用例 |
| D-04 | 解析器跳过围栏代码块 | 红队 T-4：前 50 行内的示例可把 Active 翻成 Superseded | 已修 + 回归用例 |
| D-05 | `取代于` 支持 `#锚点` | 红队 T-5：与 C-4 的锚点口径冲突，误杀合法写法 | 已修 |
| D-06 | `取代于` 阻断绝对路径与 `..` 越界 | 红队 T-6：`/etc/passwd`、`../../../etc/passwd` 可逃逸 | 已修 + 回归用例 |
| D-07 | C-5 取修订表最新日期 | 红队 T-7：假定降序，升序表（如 RFC-0004）年龄偏差 31 天 | 已修 + 回归用例 |
| D-08 | backlog 排除收窄为 `project/backlog` | 红队 T-10：按绝对路径分量判断，检出路径含 `backlog` 即整道门禁归零；且 48 篇卡片无一含 `文档状态` 键 | 已修 + 回归用例 |
| D-09 | 阈值常量化 + 非法状态时不宣称「全库 Active」 | 红队 T-9/T-11：死代码常量；与非法状态同屏自相矛盾 | 已修 + 回归用例 |

## 7. 回滚方案

删除三字段即回到 Active；门禁对无字段文档零判定，故回滚无数据迁移。
