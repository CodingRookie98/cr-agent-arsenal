# 第一轮对抗审查报告 (Round 1 Red-Team Review Report)

审查基线：`git diff 2360b32...3a922c2`（三点式，HEAD `3a922c2`，分支 `feat/doc-truth-axis`，工作区仅存在未跟踪的归档目录）。Review Mode：FULL_REVIEW。取证方式：不仅读 Diff，还在 `/tmp` 下构造隔离 git 仓库对每条指控做**可复现实验**，并在真实 `docs/` 树上实跑门禁；凡未经运行验证者一律标注「未验证」。

## 1. 第一性原理与本质溯源分析

- **改动性质定性：架构演进为主，但「门禁」部分存在浅层修补与自证失真。**
  问题域是真实的：结构分（链接/元数据/修订/孤儿/架构）确实测不出「文档还对不对」，用「锚点文件在复核点之后是否被提交」作为漂移的机械代理信号，并在 RFC §2 明说「漂移是怀疑信号而非结论」——这一步是诚实的。双轴并置（不合并 `total_score`）也确实规避了 RFC §3 表格 A 指出的破坏性改分。这部分成立。

  不成立的是**被当作门禁交付的那一半**。同一份 diff 里同时交付了「报告」（`--truth=warn`，只报告）与「闸门」（`--fail-on-drift` / `--truth=require`），而闸门在本基线 HEAD 上**对自身交付物就是红的**（见 R1-1），且有三个互不相同的洗绿通道（删声明 R1-2、选惰性锚点 R1-10、浅历史 R1-3 的反向误杀）。一个「可机械测定」的真值轴，其判定结果却取决于被测方是否愿意保留声明——这仍是 Goodhart 定律下的 KPI，不是独立信号。

- **物理与业务一致性：代理信号与用户语义之间存在两处未经证伪的断层。**
  ① 「复核于」的语义是**日**（`YYYY-MM-DD`，RFC §4.1 与模板规则 6 的写法），判定却按**秒**严格比较（`check-doc-drift.py:128` 的 `ts > verified_ts`），并把日期钉在 UTC 零点（`:183`）。于是「今天复核、今天提交」在物理上不可能被判为 fresh——这不是边界瑕疵，而是主路径语义错误（R1-1）。
  ② 「漂移」被定义为锚点文件被改过，但实现只认**当前分支可达历史里的最后一次提交时间**。历史被截断（浅克隆/浅拉取/squash）时，该时间不再代表「文件何时被改」，而是代表「克隆边界何时生成」——语义在这里悄悄换掉了，且没有任何运行时自检（R1-3）。

- **过度设计审计：四处「声明了但没有消费者」的装饰面，一处可删的重复实现。**
  1. `stale` + `--max-age-days`：除把文档从 fresh 踢出分母外不产生任何差异化动作，且 `unverified` 完全不受该参数影响（RFC §5 AC-4 括注的「可配 `--max-age-days` 视为过期」未实现）；
  2. `来源` 字段：解析后只存进 `fields["sources"]`，全库零消费者、零断言（除一条解析用例）；
  3. 行区间 `line_start`/`line_end`：解析、落盘、随 JSON 输出，但判定完全不使用；`classify_doc` 的 `anchor_paths` 形参是死参数（`check-doc-drift.py:116` 声明、`:124-132` 从不引用）；
  4. `--truth=off`：只抑制打印，`audit-doc-health.py:631` 无条件调用 `analyze()`，仍会跑全部 git 子进程（实测 off=0.56s / warn=0.49s）。
  另有一处不必要的重复：RFC §1（`:34`）把 `check-doc-control-sync.parse_frontmatter` 点名为「可复用资产、新增字段无需改解析器」，实现却在 `check-doc-drift.py:77-112` 另写了一套控制头解析器，且两者窗口与清洗规则已分叉（60 行 vs 50 行、`**`+反引号 vs `[*_`]`、无表格模式），见 R1-11。

- **对「零声明语义」的裁决（不是缺陷，但需要写进口径）。**
  `enabled=False + freshness_score=0` 确实没有污染既有 PASS：实测 `--truth=warn` 时 `total_score` 仍为 100.0、退出码 0，`tests/test_doc_drift.py:268-280` 的 A/B 对照断言也站得住（AC-1 成立）。`require` 模式下「未启用即阻断」是 RFC §4.3 的显式决策（D-06 登记在案），我不判为过度设计；但它的真实代价必须写明：**任何新仓库/新目录在第一条锚点声明出现前都无法启用 require**，且启用后门槛 12/15 意味着「已声明的文档里至少 80% 必须 fresh」——这条前置在 GOVERNANCE/SKILL/矩阵里都没有写，只在脚本 help 里出现，属于文档缺失而非设计错误。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

未激活（非客户端/SSR 改动）。本 diff 为 Python 标准库脚本 + Markdown，无 `*.tsx/*.jsx/*.vue/*.svelte`、无 `"use client"`、无 `react`/`next/*` 导入。

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

### 攻击路径 1：同日复核 → 全库假漂移，交付自证反转（已在真实树上复现）

- **触发条件**：文档按模板只用日期形式 `复核于: YYYY-MM-DD`（本 diff 自身三处自证登记全部如此：`docs/GOVERNANCE.md`、`docs/explanation/architecture/doc-governance-design.md:7`、`docs/project/plans/2026-11-22-doc-truth-axis.md:9`），且锚点文件在同一 UTC 日被提交——这是「写完文档顺带提交代码」的默认姿势。
- **复现推演**：`_verified_ts` 把 `2026-11-22` 解释为 `2026-11-22T00:00:00Z` = epoch `1795305600`（`check-doc-drift.py:183`）；锚点最后一次提交的 committer time 为 `1795315766`（`git log -1 --format=%ct -- skills/doc-governance/scripts/check-doc-drift.py`，即 2026-11-22 02:49:26Z）；`classify_doc` 用严格大于（`:128`）⇒ 判定 `drifted`。同一日历日、相差 2h49m，被判为「复核之后又被改过」。
- **实测结果（真实仓库，非构造成本）**：
  - `check-doc-drift.py --root docs --repo . --json` → `declared 3 / drifted 3 / fresh 0 / freshness_score 0.0`
  - `... --fail-on-drift` → **rc=1**
  - `audit-doc-health.py --root docs --truth=require` → **REJECTED（真值分 0.0 < 门槛 12.0）**
  而 `docs/project/plans/2026-11-22-doc-truth-axis.md:33` 记录「fresh 3、drifted 0、真值分 15.0/15」，`:86` 记录「预期：漂移脚本 rc=0」。**同一基线，记录与实测相反。**
- **影响结果**：该特性一旦按 `change-impact-matrix.md:30` 的 DoD（`--fail-on-drift` 严格 Exit Code 0）接入，红灯是本 diff 自己造成的、且无法通过「不改动锚点代码」消除；作恶成本最低的解法恰好是红线 7 禁止的那一个（删声明）。同时「复核于=今天」这一最常见写法永久不可达 fresh，指标退化为「你必须在提交锚点代码之前先写文档」的时序纪律。
- **涉及代码**：`skills/doc-governance/scripts/check-doc-drift.py:128`、`:183`；`docs/project/plans/2026-11-22-doc-truth-axis.md:33`、`:86`

### 攻击路径 2：一行删除把 REJECT 洗成 PASS（机械复现）

- **触发条件**：`--truth=require` 生效（`evaluate_verdict` 是唯一出口，`audit-doc-health.py:121-126`）；已声明文档中出现漂移。
- **复现推演**：隔离仓库 2 篇声明文档（一篇锚 `src/stable.py`，一篇锚 `src/a.py`）→ 初次 `fresh 2 / 15.0`；改动 `src/a.py` 并提交后 → `declared 2 / drifted 1 / score 7.5` → `audit-doc-health --truth=require` 输出 `REJECTED（真值分 7.5 < 门槛 12.0）`；随后**只删掉失败文档里的 `代码锚点` 一行**（正文一字不动）→ `declared 1 / drifted 0 / score 15.0`，真值轴的 REJECT 理由整条消失。`coverage` 由 1.0 掉到 0.5，但**覆盖率不参与任何判定**（`:121-126` 只看 `enabled` 与 `freshness_score`）。
- **影响结果**：`docs/GOVERNANCE.md:108` 的红线 7「严禁『删锚点清零』自我豁免」被证明是**纯文字约束**：实现层没有任何墓碑（tombstone）、基线快照、覆盖率下限或 git 历史比对来发现「昨天声明过、今天不声明了」。`skills/doc-governance/references/change-impact-matrix.md:32` 更把它写成「锚点漂移进入机械门禁，禁用『删锚点清零』的自我豁免」——这句是**宣称与取证不同宽**：机械层只覆盖「全库零声明」这一种自我豁免形态，逐文档删除完全不被发现。
- **涉及代码**：`skills/doc-governance/scripts/audit-doc-health.py:121-126`；`skills/doc-governance/scripts/check-doc-drift.py:271`（`fresh/declared` 公式，分母随声明消失）；`docs/GOVERNANCE.md:108`；`skills/doc-governance/references/change-impact-matrix.md:32`

### 攻击路径 3：CI 浅拉取 → 全量假漂移（已复现，且与文档承诺相反）

- **触发条件**：`actions/checkout` 默认 `fetch-depth: 1`，或任何 `git clone --depth N` 的巡检环境。
- **复现推演**：隔离仓库中「锚点文件最后一次提交 2026-10-01T10:00Z、复核于 `2026-10-01 / commit <sha>`」→ 完整克隆下判定 `fresh`（score 15.0）；同一仓库 `git clone --depth 1` 后判定 `drifted`（score 0.0），`--fail-on-drift` **rc=1**。机理：浅边界提交在 `git log -- <path>` 眼里等价于「一次性新增了全部文件」，于是 `git_last_commit_ts`（`:163-168`）返回的是**克隆 tip 的时间**而不是文件被改的时间；同时 `git show -s` 对不在浅窗口内的复核 commit 失败（`:155-160`）→ 静默退回日期比较。
- **影响结果**：`is_git_repo`（`:151-152`）在浅克隆里返回 true，**没有任何一处检测「历史被截断」**，因此 RFC §7 承诺的「git 不可用（CI 浅克隆）→ `--repo` 探测失败返回 2（fail-closed），不静默通过」（`RFC-0005:119`）不成立：实际行为是静默产出**假漂移**（方向甚至相反，fail-open 变成了 fail-loud-and-wrong）。`skills/doc-governance/SKILL.md:142` 同样复述了「退出码 2 属 fail-closed」。这是本轮最容易被 CI 直接放大的缺陷：一旦接线，默认配置下每个声明文档都会红。
- **涉及代码**：`skills/doc-governance/scripts/check-doc-drift.py:151-168`；`docs/proposals/RFC-0005-doc-truth-axis.md:119`；`skills/doc-governance/SKILL.md:142`

### 攻击路径 4：报告自相矛盾——「完美」与「REJECTED」同屏（BK-0028 复现）

- **触发条件**：`--truth=require` 且真值轴是唯一失败维度。
- **复现推演**：在真实仓库实跑 `audit-doc-health.py --root docs --truth=require`，stdout 同时出现第 37 行「🌟 完美！未检测到任何健康缺陷，知识库处于极佳健康状态！」与第 40 行「🚫 诊断结论: REJECTED（真值分 0.0 < 门槛 12.0）」。原因：真值维度只加进了 `evaluate_verdict`（`:121-126`），没有加进 `has_issues` 聚合链（`:775-823`）。
- **影响结果**：`evaluate_verdict` 的 docstring（`:102-106`）逐字写着这条不变量存在的理由——「两处漂移即出现『同一份体检结果既满足 PASS 又给出 REJECT 理由』的自相矛盾」。本次改动以新增维度的方式**把该缺陷原样复现**，且是用户可见的 stdout 文案，不是内部状态。
- **涉及代码**：`skills/doc-governance/scripts/audit-doc-health.py:121-126`、`:775-823`

### 攻击路径 5：未跟踪锚点 = 永久 fresh（fail-open），并可能就是 15.0/15 的来路

- **触发条件**：锚点文件存在但未被 git 跟踪（刚生成的脚本、被 .gitignore 忽略的产物、`.git/info/exclude` 命中的路径）。
- **复现推演**：隔离仓库中新建 `src/untracked.py`（`git add` 之前）→ 锚点指向它、复核于写 `2026-11-01` → 判定 `fresh`。机理：`git log -1 -- <path>` 对未跟踪路径返回空串 → `git_last_commit_ts` 返回 `None` → `classify_doc` 的 `any(ts is not None and ts > verified_ts)` 短路为 False → 「没有历史」被当成「没有变化」。
- **影响结果**：这是一个方向为 fail-open 的静默通道，且**恰好能解释**计划 `:33` 的 `fresh 3 / 15.0/15`：若该实测取自 `08baa79` 落盘之前的工作区，三个锚点文件尚未被跟踪，检测器就会读成 fresh。（该历史重建为**推断，未验证**；但通道本身已复现。）同一通道也覆盖 squash/重写历史后的路径。
- **涉及代码**：`skills/doc-governance/scripts/check-doc-drift.py:163-168`、`:128`

### 攻击路径 6：锚点失效（文件被移动/删除）不影响任何退出码——而矩阵恰恰只认退出码

- **触发条件**：被锚定的文件被重命名或删除（`git mv` 后锚点悬空）。
- **复现推演**：复核后 `git mv src/A.py src/B.py` → 判定 `missing_anchor`（`:124-125`），`drifted` 为 0 → `--fail-on-drift` **rc=0**。即：`change-impact-matrix.md:30` 那一行的标题正是「文档代码锚点失效（被锚定路径变动/移动/删除）」，DoD 却只写了 `check-doc-drift.py --root docs --fail-on-drift` 严格 Exit Code 0——**该命令对这一行描述的全部场景都不会变红**。唯一能发现它的是 `--truth=require` 模式或自行解析 JSON。
- **影响结果**：按规程执行 = 通过，但文档的依赖已经死了。这是「门禁覆盖不到自己声明的场景」，属于契约层缺口（RFC §5 AC-3 明确要求 missing_anchor 不误报为 drift，本身没错；错在 DoD 只挑了 drift 作为寄存器）。
- **涉及代码**：`skills/doc-governance/scripts/check-doc-drift.py:339-341`；`skills/doc-governance/references/change-impact-matrix.md:30`

### 攻击路径 7：惰性锚点——零成本把真值分钉在 15/15

- **触发条件**：声明一个几乎永不改动的仓库路径（`LICENSE`、`.gitattributes`、`docs/project/archive/**` 里的死文件）。
- **复现推演**：文档正文完全不写任何真实断言，控制头写 `代码锚点: LICENSE`、`复核于: 2026-11-01` → 判定 `fresh`、score 15.0（已复现）。红线 7 只禁止「删除锚点声明」，未禁止「选择惰性锚点」；RFC §2 用词是「文档断言所依赖的仓库内路径」，但没有任何机制校验锚点与正文断言的相关性。
- **影响结果**：在 require 模式下，「选一个永不动的锚点」比「真的去复核」更省力且更稳定，指标对被测方单向不利——这正是 RFC §3 用来否决方案 A 的理由（「等于用门禁逼出一批伪锚点」）在声明层被重新引入。
- **涉及代码**：`skills/doc-governance/scripts/check-doc-drift.py:128`、`:271`；`docs/GOVERNANCE.md:108`

### 攻击路径 8：散文与合法路径被切碎成幽灵锚点

- **触发条件**：锚点值里出现逗号/顿号（含路径内逗号，或人在控制头里写了一句解释）。
- **复现推演**：`代码锚点: src/a,b.py` → `_ANCHOR_SPLIT`（`:37`，按 `[,，、;；]` 切）产出 `src/a` 与 `b.py` 两个锚点，均不存在 → `missing_anchor`（已复现）；`代码锚点: 见附录 A` → 被归一为路径 `见附录 A` → 同样是 `missing_anchor`，且该文档被计入分母，压低真值分直至 require 模式 REJECT。`代码锚点` 写两遍时后者静默覆盖前者（`:106`，已复现）。
- **影响结果**：合法输入被判缺失（误报），自由文本被判路径（把散文当代码），且两者都无告警。
- **涉及代码**：`skills/doc-governance/scripts/check-doc-drift.py:37`、`:56-74`、`:100-106`

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | P1 (Blocker) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:128`, `:183`；`docs/project/plans/2026-11-22-doc-truth-axis.md:33`, `:86` | 日期型「复核于」按 UTC 零点起算，同日提交必判 drifted；HEAD 实测 drifted 3 / 真值分 0.0，与计划记录（fresh 3 / 15.0/15 / rc=0）相反 | `_verified_ts` 把 YYYY-MM-DD 钉在 00:00Z，`classify_doc` 用秒级严格大于 ⇒ 「今天复核、今天提交」物理不可达 fresh；`--fail-on-drift` rc=1、`--truth=require` REJECTED，交付自证被自己的门禁否决 |
| R1-2 | P1 (Blocker) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:121-126`；`skills/doc-governance/scripts/check-doc-drift.py:271`；`skills/doc-governance/references/change-impact-matrix.md:32`；`docs/GOVERNANCE.md:108` | require 门禁可被「删除失败文档的锚点声明」洗绿（实测 7.5 → 15.0，REJECT 理由消失），覆盖率下降不参与判定 | `freshness_score = 15 × fresh/declared`，分母随声明消失；`evaluate_verdict` 只看 enabled 与分数；无墓碑/快照/git 历史比对。红线 7 与矩阵「禁用删锚点清零」属纯文字约束，宣称与取证不同宽 |
| R1-3 | P1 (Blocker) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:151-168`；`docs/proposals/RFC-0005-doc-truth-axis.md:119`；`skills/doc-governance/SKILL.md:142` | 浅克隆下 100% 假漂移：同一仓库完整克隆 fresh/15.0，`--depth 1` 克隆 drifted/0.0 且 rc=1；文档承诺的「浅克隆 → 退出 2 fail-closed」不存在 | 浅边界提交在 `git log -- path` 下等价于「新增全部文件」→ 锚点时间被替换为克隆 tip 时间；`git show -s` 对窗口外 SHA 失败后静默退回日期比较；`is_git_repo` 不检测历史截断 |
| R1-4 | P1 (Blocker) | 是 | `skills/doc-governance/scripts/audit-doc-health.py:121-126`, `:775-823` | `--truth=require` 下 stdout 同时输出「🌟 完美！未检测到任何健康缺陷」与「🚫 REJECTED」，复现 BK-0028 明令禁止的 PASS/REJECT 理由并存 | 真值维度只进 `evaluate_verdict`，未进 `has_issues` 聚合链；人读文案与机器裁决分叉 |
| R1-5 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:163-168`, `:128` | 未跟踪锚点文件被判 fresh（fail-open）；可能就是计划 `:33` 得到 15.0/15 的机理（历史重建为推断，未验证） | `git log` 对未跟踪路径返回空 → `ts=None` → 漂移比较短路为 False；「无历史」被当成「无变化」 |
| R1-6 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:339-341`；`skills/doc-governance/references/change-impact-matrix.md:30` | `--fail-on-drift` 对 `missing_anchor` 无退出码；矩阵该行（行名即「变动/移动/删除」）指定的 DoD 命令对锚点失效恒为 rc=0（已复现） | 退出码契约 1 只覆盖 drifted；锚点被 `git mv` 后判定 missing_anchor，门禁静默放行 |
| R1-7 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:123`, `:124-132`；`docs/proposals/RFC-0005-doc-truth-axis.md:81`, `:99`；`skills/doc-governance/tests/test_doc_drift.py:8` | 五态优先级三处口径互不一致（RFC：drifted 优先；脚本 docstring 与测试 docstring：missing_anchor 优先且 drifted 高于 unverified；代码：missing_anchor→unverified→drifted→stale）；RFC §4.2 的排序与自家 AC-3 冲突 | 规范不可机械执行：同一「一锚缺失 + 一锚漂移」文档按 RFC 排序应报 drifted，按 AC-3 与代码报 missing_anchor；文档之间亦互相矛盾 |
| R1-8 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:37`, `:56-74`, `:100-106` | 逗号/顿号切分会把 `src/a,b.py` 切碎为两个幽灵锚点（已复现）；散文值（`见附录 A`）被当成路径并计入分母；重复 `代码锚点` 行后者覆盖前者（已复现） | 合法路径误报 missing_anchor；自由文本被当作代码依赖；声明被静默丢弃 |
| R1-9 | P2 (Suggestion) | 是 | `skills/doc-governance/tests/test_doc_drift.py:249-252`, `:268-309` | 4 条关键用例（AC-1/AC-5/require 未启用阻断/missing_anchor 上报）定义在 `if __name__ == "__main__": unittest.main()` 之后：`python3 test_doc_drift.py` 实测 `Ran 13 tests`，pytest 才 17 条；计划宣称「17 条」只在 pytest 路径成立 | 直接执行/部分 CI 包装方式会静默跳过全部 audit 集成用例（含 require 门禁的唯一回归保护） |
| R1-10 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:128`, `:271`；`docs/GOVERNANCE.md:108` | 惰性锚点洗分：锚 `LICENSE` 之类永不改动文件即恒 fresh / 15.0（已复现）；红线 7 只禁「删锚点」，未禁「选惰性锚点」 | 指标不校验锚点与正文断言的相关性；require 模式下「选死文件」比「真复核」更省力，重演 RFC §3 否决方案 A 时点名的「伪锚点」激励 |
| R1-11 | P2 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:77-112`；`skills/doc-governance/scripts/check-doc-control-sync.py:32-60`；`docs/proposals/RFC-0005-doc-truth-axis.md:34` | 两套控制头解析器并存且已分叉：扫描窗口 60 行 vs 50 行、清洗字符集不同、后者有表格模式前者没有；RFC 却宣称「新增字段无需改解析器、可直接复用」 | 同一文档可能被版本一致性门禁忽略而被真值轴采信（或反之），形成静默覆盖黑洞；这是本次改动新引入的重复实现 |
| R1-12 | P3 (Suggestion) | 是 | `skills/doc-governance/references/change-impact-matrix.md:34` | 用法说明写「矩阵第 7 行」，实际新增行是第 8 行（第 7 行是「文档拓扑变动」）；矩阵共 8 个数据行 | 读者按指引会落到错误的矩阵行，取到错误的联动要求 |
| R1-13 | P3 (Suggestion) | 是 | `docs/proposals/RFC-0005-doc-truth-axis.md:89`, `:52`；`skills/doc-governance/scripts/audit-doc-health.py:631`；`skills/doc-governance/references/change-impact-matrix.md:30` | RFC 承诺「`已声明 = 0` 时置 0 并报 `not_enabled`」，实现无此字面量；`--truth=off` 仍执行全量 analyze（实测 0.56s vs 0.49s）；矩阵 DoD 用 `--truth=warn` 却要求「真值分不低于 12/15」（warn 不强制）；RFC §3 表格 B 仍残留旧开关名 `--require-truth` | 契约字面量与实现不对齐；off 语义只到打印层；DoD 用不可强制的模式声明门槛 |
| R1-14 | P3 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:163-168`; `:130`; `:85`; `:39` | 大小写不匹配的锚点在大小写不敏感文件系统上会 fail-open（Linux 实测 `git log -- src/a.py` 无输出、`src/A.py` 有值；macOS/Windows 上 `is_file()` 为真 ⇒ 永久 fresh，**平台行为未验证**）；`unverified` 不受 `--max-age-days` 影响（RFC §5 AC-4 括注未实现）；控制头扫描仅前 60 行；`\d` 接受全角/阿拉伯数字（`src/a.py:١٢٣` 解析为 123） | 平台差异导致的静默漏判；参数语义不完整；魔数窗口；Unicode 数字被误收 |
| R1-15 | P3 (Suggestion) | 是 | `skills/doc-governance/scripts/check-doc-drift.py:250` | 每个锚点一次 `git` 子进程（实测约 13ms/锚点）；`audit-doc-health` 每次体检都全量重跑（基线 0.49s，当前 7 锚点 +0.09s） | 线性放大：154 篇文档若各声明 1 个锚点约 2s，500 锚点约 6.5s；建议 `git log --stdin` 或一次 `--name-only` 取表 |
| R1-16 | P3 (Suggestion) | 是 | `docs/index.md:97`；`skills/doc-governance/scripts/check-doc-drift.py:43-49`；`skills/doc-governance/scripts/audit-doc-health.py:631` | 文档影响面收尾问题：`docs/index.md` §4 表按时间升序排列，新行（2026-11-22）被插在 2026-10-19 与 2026-10-20 之间而非表尾；`in_evidence_archive` 仅当 `--root` 是 docs 根时成立（`--root docs/project` 会把审查报告纳入统计）；audit 以 `root_dir.parent` 硬编码 repo 根 | 索引时序破坏人工索引可读性；豁免域依赖入参形态；非标准 `--root` 下锚点相对解析错位 |

## 5. 第一轮结论概要

1. **总体判断：阻断交付（4 项 P1）。**「真值轴报告」这一半是诚实且可用的（结构分零污染、AC-1 成立、`llms.txt` 逐字节一致、全量 178 测试绿、`check-doc-links` / `check-doc-control-sync` rc=0）；「真值轴门禁」这一半在本基线 HEAD 上是红的、可绕的、且在 CI 默认配置下会误杀。

2. **最致命的一条不是「有没有 bug」，而是「自证不成立」**：计划 `:33`/`:86` 记录的 `fresh 3 / 15.0/15 / rc=0`，在提交后的 HEAD 上实测为 `drifted 3 / 0.0 / rc=1`，`--truth=require` 直接 REJECTED。根因是「复核于」按日记录、判定按秒比较（UTC 零点）——这不是极端边界，而是本 diff 三处自证登记**全部命中**的主路径。

3. **红线 7 是文字约束，不是机械约束**：删一行声明即可把 7.5 → 15.0 并把 REJECT 理由整条抹掉，覆盖率下降无人过问；选一个永不改动的锚点同样恒得满分。`change-impact-matrix.md:32` 的「禁用『删锚点清零』的自我豁免」因此属于宣称与取证不同宽，必须降级措辞或补机械手段（覆盖率下限、声明墓碑、与 `git log` 的历史比对三者取其一）。

4. **fail-closed 承诺未兑现**：RFC `:119` 与 `SKILL.md:142` 都写「浅克隆 → 退出 2」，实现只在「不是 git 仓库」时返回 2；浅历史下产出的是假漂移而非环境错误，方向与承诺相反。

5. **测试保真度不足**：17 条用例里 4 条关键用例位于 `__main__` 守卫之后，直接执行只跑 13 条；且全部 git 集成用例都走「commit 固定」分支，**恰好绕开**了唯一在生产中会用的日期分支——这正是 R1-1 未被自家测试抓住的原因。没有任何用例覆盖浅克隆、未跟踪锚点、逗号路径、missing_anchor 的退出码、以及「删声明洗绿」。

6. **移交第二轮**：请元架构师重点裁定三项——① R1-1 的修复方向（日期粒度对齐 vs 强制 commit 形式 vs 改默认 (	ext{fresh}) 判据）是否值得在本轮内做；② R1-2/R1-10 是否构成「必须补机械手段」的阻断，还是应把 require 模式整体降级为不交付（YAGNI），只保留 warn 报告；③ R1-3 的 CI 适配（`fetch-depth: 0` 契约化 vs 显式检测浅历史并 fail-closed）应写进 RFC 还是推迟。另请复核 P2 中 R1-6/R1-7 是否应升格 P1——两者都属「规范化文档与实现不自洽」，但影响面限于锚点失效与文档口径，未直接导致错误裁决。
