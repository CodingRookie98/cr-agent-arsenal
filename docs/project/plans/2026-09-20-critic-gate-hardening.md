# Critic 门禁加固（taste-driven-designer） 维护修复计划 (Maintenance-Patch Plan)

> **文档控制信息**
> - **文档标识**: PLAN-FIX-CRITIC-GATE-2026
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-09-20

> **目标元数据**
> - **所属项目**: CR Agent Arsenal
> - **执行通道**: Maintenance-Patch（存量维护通道；保留 3-Tries 熔断、修复前先复现、回归测试、定向单轮红队审查）
> - **目标简述**: 修复 `taste-driven-designer` 的收敛门禁设计缺陷 —— 实跑证据（另一会话 10 轮 Critic 评审）证明「Critic 绝对评分 ≥9/10 才算完成」不可作验收判据。门禁换代：结构清单（客观核验）+ 盲比 A/B 改进（强制选择、不给分）+ 人类签收；分数降为遥测；补版本回执、鉴别力自检、冲突仲裁与评审账本。
> - **创建日期**: 2026-09-20
> - **计划负责人**: DSH AI Agent
> - **需求方**: 王辉
> - **批准人 (User Nod)**: 王辉 | **批准时间**: 2026-09-20（"那就做A"）
> - **批准基线**: A 方案六项修补方向（证据固化 / 门禁换代 / 意图与回执 / 鉴别力与仲裁 / 排序法强制化 / 账本）
> - **状态**: 进行中
> - **隔离分支**: `fix/critic-gate-hardening`
> - **技术调研备忘录**: 豁免（无第三方依赖；根因分析见回归证据 fixture 第 3 节）
> - **临时 Scratchpad**: `.goal-loop/scratchpad.md`

---

## 🚀 活跃执行状态与持久化检查点 (Active Checkpoint)
- **当前执行通道**: Maintenance-Patch
- **当前活跃阶段**: P4.2 Delta Re-Loop（R1 裁定 1 阻断 + 7🟡 + 2⚪ 已全部修复，待以修复提交为新基线复核）
- **当前活跃子任务**: Task P4.2
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 1/5（Delta 第 1 轮）
- **最后一次验证状态**: L1 全量 pytest 22 passed（seed 13 + 契约 9，规避实验拦截验证通过）；L0 bash -n / diff --check OK；L-Doc 断链 0 / 健康度 PASS / 修订历史窗口合规
- **最新有效提交**: `cbfa86b`（P3 门禁加固原子单元；Delta 修复提交见下）
- **阻断原因**: 无（R1 唯一阻断项已修复）

---

## 1. 现象与复现 (Symptom & Reproduction)

- **现象**: 真实 UI 打磨任务中，绝对评分轨迹 `6.2 → 5.8 → 6.0 → 3.8 → 4.2 → 5.8 → 5.8 → 5.2` 与每轮改动无相关性；输入 md5 变化后评审输出逐字相同；降级排序法同样退化为数值分数；R5/R7 跨轮自相矛盾且与已决原则「线胜于面」冲突；10 轮越界超出 5 轮上限；最终如实报 blocked。
- **复现证据**: [critic-gate-counter-evidence.md](../../../skills/taste-driven-designer/tests/fixtures/critic-gate-counter-evidence.md)（E1~E7 逐条固化）
- **根因假设**: 绝对审美分数信噪比不足 + 隔离规则剥夺基线 + Critic 无设计意图输入 + 无产物回执校验 + 把文章的「9/10」口号当作工程契约、却把文章真正的相对排序判据降级为可选。

## 2. 修复范围 (Fix Scope — Diff 锁定)

- `skills/taste-driven-designer/SKILL.md` — 铁律 3 / 阶段纪律 / 快速清单 / 阶段路由 D2 行 / 降级与预算表
- `skills/taste-driven-designer/references/critic-loop-protocol.md` — 全面改写（三信号门禁、版本回执、鉴别力自检、冲突仲裁、遥测规则、排序法主路径、评审账本）
- `skills/taste-driven-designer/templates/critic-prompt-template.md` — 双模式模板（盲比 A/B、参考排序），版本回执 + 已决原则注入 + 硬禁数值输出
- `skills/taste-driven-designer/templates/design-brief-template.md` — 已决原则台账 + 评审账本
- `skills/taste-driven-designer/tests/test_gate_contract.py` + `tests/fixtures/critic-gate-counter-evidence.md` — 回归契约测试与证据
- `docs/explanation/architecture/taste-driven-designer-design.md` — §4/§7/§8 与版本号 V1.1.0
- 注册文档：`docs/index.md`（V1.9.0 + 计划行）、`docs/llms.txt`、`README.md`（技能行描述去 9/10）
- **严禁越界**: 不改动 `scripts/generate-seed.sh` 与既有单测（门禁修复不涉脚本）；不修改其它技能本体；不引入新依赖。

## 3. 回归测试 (Regression Tests)

- [x] **Task P3.1**: 证据 fixture 固化 + 契约测试先红 —— `tests/test_gate_contract.py` 7 用例（旧门禁字样必须消失、三信号锚点必须存在、模板必须要求回执并硬禁分数、协议必须含鉴别力自检/仲裁/账本、简报必须含台账）
  - **验收命令**: `python3 -m pytest skills/taste-driven-designer/tests/test_gate_contract.py -q`（改前 6 failed / 1 passed = 红灯基线）
- [x] **Task P3.2**: 文档改写转绿（4 个技能文件）
  - **验收命令**: 同上（7 passed）
- [x] **Task P3.3**: 全量回归 —— `python3 -m pytest skills/taste-driven-designer/tests/ -q`（seed 13 用例 + 契约 7 用例全绿）
- [x] **Task P3.4**: L0 + L-Doc 门禁（`bash -n` / `git diff --check` / 断链 / 健康度）

## 4. 终审与归档 (Review & Closure)

- [x] **Task P4.1**: 定向单轮红队审查（Light，子智能体 426bbf2f）—— 裁定 **存在阻断项 🔴×1**（SKILL.md 铁律 2「只收当前产物」与盲比门禁自相矛盾）+ 🟡×7 + ⚪×2；证据保真、Diff 范围与安全两项全过
- [x] **Task P4.2**: R1 裁定修复（Delta 第 1 轮）—— ①🔴 铁律 2 增补「盲比模式另附去标识、随机左右的上一版」；②作废二级上限（连续 2 轮作废即停并升级）；③"无法区分"计入无改进的终止语义；④轮次 nonce 与版本标识分离（盲比匿名性）；⑤§8.1 补登第三项偏离 D3（Critic 输入含意图与已决原则）；⑥契约测试升级为句子级扫描（22 passed，规避实验拦截成功）+ 修复恒真空断言；⑦三处残留旧口径清剿（设计书 §2/§3、ai-tells 执行时机）；⑧两处因重编号失效的 §4→§8 交叉引用
- [ ] **Task P4.3**: Zero Blockers 结项登记；合并回 master

---

## 5. 修订历史 (Revision History)
- **[2026-09-20]**: 计划创建（V1.0.0，Maintenance-Patch 通道，A 方案）。
