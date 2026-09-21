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
- **当前活跃阶段**: 已完成（R1 阻断清零 → Delta R1 复核 Zero Blockers → Delta R2 聚焦复核 Zero Blockers）
- **当前活跃子任务**: 无（P3~P5 全部闭合）
- **当前子任务重试计数**: 0/3
- **外层循环迭代**: 2/5（Delta 第 2 轮闭合）
- **最后一次验证状态**: L1 全量 pytest **24 passed（seed 13 + 契约 11）**；5 组变异实验全部拦截且还原一致；L0 bash -n / diff --check OK；L-Doc 断链 0 / 健康度 PASS / 修订历史窗口合规
- **最新有效提交**: `a1a57ad`（Delta R2 修复提交；结项登记提交随后）
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

- [x] **Task P4.3**: Zero Blockers 结项登记（本节 + 第 6 节）；交付链 `cbfa86b` → `9c92f6b` → `a1a57ad` → 结项提交
- [x] **Task P4.1**: 定向单轮红队审查（Light，子智能体 426bbf2f）—— 裁定 **存在阻断项 🔴×1**（SKILL.md 铁律 2「只收当前产物」与盲比门禁自相矛盾）+ 🟡×7 + ⚪×2；证据保真、Diff 范围与安全两项全过
- [x] **Task P4.2 (Delta R1 复核闭环表)**: 8 项 R1 裁定中 7 项 ✅ 闭环（唯一 ⚠️ 为计划 checkpoint 未记 Delta SHA，本轮已补记）；复核结论 **Zero Blockers ✅（🔴 0 / 🟡 3 / ⚪ 3）**，并新发现 N1 测试误报（Delta 自引入）、N2 匿名性未钉死、N3 残余规避、N4 弱断言、N5 触发粒度冗余
- [x] **Task P4.2 (Delta R2 修复)**: ①N1 禁止词表扩充（不含/不涉及/不参与/不构成）并增设扫描器自检用例（合法否定不误报、违规变体必拦截）；②N2 新增匿名性锚点断言（协议"盲比匿名性" + 模板 identities stripped）；③N3 GATE_WORDS 扩充（交付/上线/发版/发布/合并）+ 边界声明（启发式护栏非语义证明）；④N4 删除 or 回退改精确锚点；⑤N5 协议补 Gate B 优先于 2 轮熔断的触发优先级。**5 组变异实验逐项验证拦截有效**（E2/E5/E6/E7/E8 全 1 failed）
- [x] **Task P4.2 (原始 R1 修复)**: R1 裁定修复（Delta 第 1 轮）—— ①🔴 铁律 2 增补「盲比模式另附去标识、随机左右的上一版」；②作废二级上限（连续 2 轮作废即停并升级）；③"无法区分"计入无改进的终止语义；④轮次 nonce 与版本标识分离（盲比匿名性）；⑤§8.1 补登第三项偏离 D3（Critic 输入含意图与已决原则）；⑥契约测试升级为句子级扫描（22 passed，规避实验拦截成功）+ 修复恒真空断言；⑦三处残留旧口径清剿（设计书 §2/§3、ai-tells 执行时机）；⑧两处因重编号失效的 §4→§8 交叉引用
- [ ] **Task P4.3**: Zero Blockers 结项登记；合并回 master

---

## 5. 结项登记 (Closure Record)

- **终审凭据**（三次独立审查，均针对最新提交）：
  - R1 定向单轮红队（子智能体 426bbf2f；基线 `7eff43c..cbfa86b`）：存在阻断项 🔴×1 + 🟡×7 + ⚪×2
  - Delta R1 复核（子智能体 a65280f7；基线 `cbfa86b..9c92f6b`）：**Zero Blockers ✅**（🔴 0 / 🟡 3 / ⚪ 3；R1 八项 7 ✅ + 1 ⚠️ 记录精度）
  - Delta R2 聚焦复核（子智能体 a347fec5；基线 `9c92f6b..a1a57ad`）：**Zero Blockers ✅**（🔴 0 / 🟡 0 / ⚪ 1 / ⚠️ 1）
- **阻断项闭环**: R1#1「SKILL.md 铁律 2 只收当前产物」与盲比门禁自相矛盾 → 改为「默认只收当前产物 + 盲比模式另附去标识、随机左右的上一版」（变异实验 E2 拦截验证）
- **建议项闭环**: 作废二级上限（连续 2 轮 → 停止并升级；E7 拦截）· "无法区分"终止语义与 Gate B 优先级 · 轮次 nonce 与版本标识分离的盲比匿名性（E4/E6 拦截）· §8.1 补登第三项显式偏离 D3（文章 L219 逐字核对）· 三处残留旧口径清剿 · 契约测试升级为句子级扫描（E1/E5 规避句拦截）· 测试去误报（N1）与匿名性锚点钉死（N2）
- **验证证据**: pytest **24 passed**（seed 13 + 契约 11）；5 组变异实验全部正确拦截且还原一致（sha256 前缀比对，实验后 `git status` 干净）；`bash -n` / `git diff --check`；断链 0 / 健康度 PASS / 修订历史窗口合规；技能内相对链接 18/18 有效
- **交付清单**: 门禁换代（SKILL.md 铁律 3 / 阶段纪律 / 快速清单 / 降级与预算表）· 闭环协议重写（三信号门禁 / 回执与匿名性 / 鉴别力自检 / 冲突仲裁 / 遥测规则 / 排序主路径 / 预算账本）· 双模式 Critic 模板 · 设计简报已决原则台账与评审账本 · 反证 fixture · 契约测试 · 设计书 V1.1.0（含 §8.1 偏离登记 D1/D2/D3）· 注册（index V1.9.0 / llms.txt / README）
- **提交链**: `cbfa86b`（门禁换代）→ `9c92f6b`（Delta R1 修复）→ `a1a57ad`（Delta R2 修复）→ 结项登记提交
- **未覆盖项**: 无（唯一 ⚠️ 为计划记录精度，本节已闭环）

---

## 6. 修订历史 (Revision History)
- **[2026-09-20]**: 计划创建（V1.0.0，Maintenance-Patch 通道，A 方案）。
- **[2026-09-20]**: 结项（三次独立审查闭环，Delta R2 取得 Zero Blockers；追加第 5 节结项登记，修订历史顺延为第 6 节）。
