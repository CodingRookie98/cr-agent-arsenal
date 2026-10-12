# 第二轮元对抗审查与终审裁决书 (Round 2 Meta-Architect Verdict)

> 审查范围（三点式）：`git diff fe8da78471c727e6bdaef2f8ed64bbe978ac94b5...2100136ed682c7ee8cee3250508f77bc392adf8d`
> 模式：DELTA_RE_LOOP（修复后再循环，覆盖 `d8aa611` 首轮 R2 修法批次 → `7449aae` 首个 Delta 轮修法批次 → `2100973` 重派 Delta 轮四条建议）
> 前驱 R1 报告：`docs/project/reviews/2026-10-12-spec-evolution-v1/delta-r1-fe8da78..9db83c7.md`（direct 通道，38749 字节，SHA256 前 12 位 `313ee5f7ccc3` —— 已实测复算一致，与台账登记同值）
> ID 命名空间：首轮 `R1-1`…`R1-15`（并集取自 `r1-0306f37..fe8da78.md`）+ 本轮 `DeltaR1-1`…`DeltaR1-4`

## 1. 元审查辩证质询 (Meta-Challenges on Round 1)

- **R1 攻击可信度整体评估**: **存在过度挑刺倾向**（首轮 15 条），但**本轮前驱（重派 Delta R1）的 4 条攻击高度中肯**。

  分轮定性：
  - **首轮 R1（`r1-0306f37..fe8da78.md`，15 条）**：3 条 P1 阻断（R1-1/R1-2/R1-3）经两轮推演**全部坐实**，且直指同一结构性病灶（「把机械可证当作自身属性来宣称」），攻击质量高。但非阻断面存在明确的**过度挑刺与失实**：R1-7 的恒真断言**无法复现**（见下），R1-13 属过度表述，R1-6 被首轮 R2 由 P2 下调 P3，R1-4/R1-5/R1-6 实为同一根因的三个分支却被拆成三条并列指控（虚增缺陷计数）。故整体评为「存在过度挑刺倾向」，而非「较多误报」——其阻断面是准的。
  - **本轮前驱 Delta R1（`delta-r1-fe8da78..9db83c7.md`，4 条）**：`DeltaR1-1`…`DeltaR1-4` **四条全部经我独立复现坐实**，零幻觉、零越界，且每条都给出了可机械复现的机理与取证命令。这是本仓历轮红队中质量最高的一份报告。其对前轮 `DR1-1`~`DR1-3` 的「全部已根治」复核结论，我也独立复验为真。

- **Diff 边界合规性核查**:
  - **未发现首轮 R1 把未被本次改动触及的历史技术债定级为 P0/P1 的行为**。唯一的历史既有项 R1-15 已由 R1 **自行标注**「是否由当前 Diff 引入 = 否 —— 历史既有」，评级 P3，未构成越界阻断。这一点首轮 R1 做得正确，应予确认而非纠正。
  - **但存在一处「半越界」需纠正**：R1-13（`collect-facts.py:130-145` 的 C-08 正则与 `skills/_shared/tests/test_cross_skill_links.py` 近似重复）被标为「本次引入」，理由是「后者在本次 diff 中被修改」。核实：`test_cross_skill_links.py` 在本次 range 中确有改动，但**正则重复这一技术债本身在 `fe8da78` 之前即已存在**；本次改动只是让它多了一处同源副本。归属应精确表述为「**历史既有债，本次变更扩大其表面积**」。首轮 R2 已将其登记为待办（BK-0038）而非阻断，处置正确，故**终审维持 🟡 P3，仅纠正归属表述**，不改变评级。
  - **R1-15 的历史既有定级无须纠正**：其指控对象（`agy-delegation-workflow` / `clarification-protocol` / `doc-governance` / `dual-round-review` 的交付面缺口）与本次 diff 无因果关系，且 RFC-0004 已确立「检测与修复分离」原则，`F-1`~`F-9` 不随本次交付修复（RFC-0004:350 裁定）。我实测在真实仓库上运行判定器得到 11 条 findings（F-01~F-03 HIGH、F-04~F-11 MID），其中 `spec-evolution` 自身 **0 条**——全部 findings 均可归因于既有技能存量债务，与本次交付无涉。
  - **对 DeltaR1 四条做边界复核**：`DeltaR1-1`（`judge.py` `load_facts` 类型校验缺失）、`DeltaR1-2`（`collect-facts.py` 固定缓存根）、`DeltaR1-3`（模块级 `gettempdir()` 推导 + 无越界校验）三条均直接指向 `fe8da78..9db83c7` 区间内**新增/修改的代码行**，归属「本次引入」成立；`DeltaR1-4`（章节重编号引入的 `§4` 指针断裂）指向 D-19 在本次交付内新增 `checks-spec.md` §4 所引发的连带断裂，亦属本次引入。**四条边界全部合规，无越界挑刺。**

- **幻觉与误报甄别**:
  - **R1-7 部分失实（已由首轮 R2 纠正，我复核确认）**：R1 称计划文档中 `grep -c "CI\|pytest"` 恒真。复核：该串在 1787 行中命中 **0 次**，R1 所报数字仅覆盖单段。该子指控**不成立**。但其主干（RFC §3.4 锚点契约漏登 `[REPO:*]`）经首轮 R2 认定「比 R1 所述更严重」并已补登（RFC-0004 V0.5.0，见 `docs/proposals/RFC-0004-spec-evolution.md` 的 `[REPO:<repo-relative-path>[:<line>]]` 形态登记）。故 **R1-7 定性为「主干成立、子指控失实」，终审维持 🟡 P2 并已闭环**。
  - **R1-8 属追溯链混淆（表述不实，实质成立）**：R1 把 RFC §3.7 的 `GI-1`/`GI-3` 与设计书 §门禁不变式的定义**当作同一组**，据此指控「不变式无对应断言」。核实：二者确非同一定义（RFC:250 的 GI-3 被 `design.md:106` 重定义为「报告锚点是 findings.json 锚点子集」，与实现的锚点存在性校验 `judge.py` `validate_anchor()` 语义不同）。指控的**实质**（追溯表/不变式清单未对齐）成立，但**机理叙述失实**。已由首轮 R2 维持 P2 并登记为 BK-0035，终审维持 🟡 P2。
  - **R1-13 属过度表述**：首轮 R2 已纠正为「同一 `len()` 计数的两处调用」，非「两处 `description` 计数不同源」。终审维持 🟡 P3（真实存在的正则双实现债，BK-0038），但纠正其机理叙述。
  - **R1-4/R1-5/R1-6 的拆分属虚增**：三条实为「判定器对『输入不可信』维度整体缺位」这一根因的三个分支（首轮 R1 自己在 §5 移交请求第 4 点也承认了这一点，却仍在 §4 拆成三条并列）。这不是幻觉，但**夸大了缺陷数量**，元审查须指出。
  - **DeltaR1 四条零幻觉**：我逐条独立复现，全部为真（证据见 §1 末「再循环次生破坏复核」）。未发现任何一条基于不存在的代码上下文。

- **过度工程拦截 (YAGNI 审计)**:
  - **首轮 R2 已正确否决三项扩大化改法（YAGNI）**，我复核后**维持否决**：不把夹具桩替换为真实门禁、不为 C-09 增设 `INCOMPLETE` 第四态、不把 MID 升格为阻断。三项均属「为 0.001% 场景破坏既有架构一致性」，且第三项会直接推翻 `checks-spec.md` §4 已定案的「MID 不阻断」契约。
  - **本轮为关闭 `DeltaR1-1`~`DeltaR1-4` 付出的复杂度，逐项审计如下**（这是本轮 YAGNI 审计的重点）：
    1. **`mkdtemp` + `atexit` 清理（`DeltaR1-2` 修法）—— 必要成本，予以支持**。固定名 `/tmp/spec-evolution-pycache` 是**可预测、共享、跨运行持久**的路径，`/tmp` 为 `drwxrwxrwt`，本地用户可抢先创建并植入畸形字节码被门禁进程读取执行——这是**真实的进程内任意代码执行**，不是理论风险。`mkdtemp` 是标准库对该问题的**最小正解**：它以 `O_EXCL` 语义保证独占创建、权限 0700、随机名不可预测，一行调用即同时关闭「可预测」「共享」「不独占」三个属性。任何更简单的形态（如自行拼 uid + 进程号）都要重新实现 `O_EXCL` 竞态防护，反而更复杂。`atexit` 清理同样是必要的（否则 `/tmp` 无限累积）。**结论：奥卡姆剃刀下的正确选择，非过度工程。**
    2. **越界 fail-closed（`DeltaR1-3` 修法）—— 必要成本，予以支持**。校验逻辑是 `if base == repo or repo in base.parents: raise CollectError(...)`，**一行判定、零新增抽象**，且**在创建任何目录之前**执行（避免「校验失败却已落盘」）。这是把一个静默失守（GI-6 被环境变量重新击穿）转为响亮失败的最小形态，符合「fail-closed 优于 fail-open」的既有架构一致性。**结论：非过度工程。**
    3. **键类型校验（`DeltaR1-1` 修法）—— 方向正确但形态次优，属**建议级**的 YAGNI 观察**。`load_facts` 的 `expected = {...}` 白名单是**枚举式**防御：它逐键列举合法类型，天然不完备（我实测确认嵌套类型仍未被覆盖，见 §1 末）。更简单的形态本可一次关闭整个类：在 `main()` 外层兜底 `except Exception` → 退出码 2，即可让**任何**未预期的输入形态都不再伪装成「存在 BLOCKER/HIGH」。当前修法只关闭了 5 个已知键，剩余面（`skills[].path`、`skills[].files`、`root_prompt.baseline` 等）仍走裸 traceback + 退出码 1。**这不构成过度工程（白名单本身很便宜），但构成「修法未与宣称同宽」**——`DeltaR1-1` 的原指控是「输入错误伪装成阻断裁决」，该属性在嵌套字段上依然成立。终审据此把 `DeltaR1-1` 维持为 🟡 P2 建议并给出更简形态，不作为阻断项。

- **再循环次生破坏复核 (仅再循环模式)**:
  - **上一轮 Blocker 根治情况（全部实测，不采信测试断言的字面绿）**：
    - **`R1-1`（GI-6 只读不变式）→ 已根治**。实测：在 `/tmp/r2audit/real` 的 `git archive HEAD` 干净副本上，先预热使既有 `.pyc` 全部落地，快照 `find -type f`，再以 `TMPDIR=/tmp/r2audit/pyroot`（仓库外）执行 `collect-facts.py --repo-root /tmp/r2audit/real`（**门禁启用**，四条门禁 `pytest`/`check_doc_links`/`audit_doc_health`/`cross_skill_links` 全部 `exit_code=0`），前后文件清单 `diff` **完全为空**。仓库内零字节码镜像落盘。GI-6 在真实仓库、真实门禁、真实子进程下成立。
    - **`R1-2`（退出码语义自相矛盾）→ 已根治**。`checks-spec.md` §4 已给出严格三态表（`0` = 无 BLOCKER/HIGH；`1` = 存在 BLOCKER/HIGH；`2` = 用法或输入错误且拒绝写出任何产物），`SKILL.md` 的退出码表与之逐字一致，且权威指针已补登（`SKILL.md:84`「权威定义在 `scripts/judge.py` 与 `references/checks-spec.md`」）。实测：合法输入 rc=1 且写出报告；四类非法输入 rc=2 且**报告文件不存在**。
    - **`R1-3`（`--no-gates` 渲染肯定句）→ 已根治**。实测：`--no-gates` 采集的 facts 送判定器，报告 `## BLOCKER` 段渲染为「（未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论）」，全报告 `grep -c "无既有门禁失败"` = **0**。肯定句已消除，改为中性三态。且 `collected_gates()` 已把 `[]`/`{}`/`0`/`{"pytest": "junk"}` 等 falsy-but-not-None 形态一并归入「未采集」，关闭了 DR1-5 指出的残余 fail-open。
  - **本轮前驱 4 条建议的关闭质量（变异对照实测）**：
    - **变异 A（把 `pycache_prefix` 改回固定名 `/tmp/spec-evolution-pycache`）**：`test_gi6_pycache_prefix_is_per_run_and_private` 与 `test_gi6_rejects_pycache_prefix_inside_repo` **双双转红**（`FileNotFoundError: '/tmp/spec-evolution-pycache'`）。→ 新测试**确实钉住**了「每次运行独占、随机名、私有」这一属性，而非仅钉住实现细节。
    - **变异 B（仅删除 containment 校验、保留 `mkdtemp`）**：`test_gi6_rejects_pycache_prefix_inside_repo` **转红**、`test_gi6_pycache_prefix_is_per_run_and_private` **保持绿**。→ 两条测试的**判别力互相独立**，不存在「一条测试覆盖两处断言」的虚绿。
    - **越界 fail-closed 端到端**：以 `TMPDIR=<仓库自身>` 运行采集器，得到 `❌ 字节码重定向根落在仓库内: /tmp/r2audit/tmpin（repo=/tmp/r2audit/tmpin）——请修正 TMPDIR / 临时目录配置后重试`，退出码 **2**；仓库内文件数不变（230 → 230），**零镜像文件**。fail-closed 真实生效，未退化为「悄悄写进仓库」。
    - **`baseline.json` 与根提示词一致性**：实测 `contexts/AGENTS.md` = **97 行 / 10746 字节**，`references/baseline.json` 登记 `lines: 97, bytes: 10746`，**逐值一致**；`baseline.json` 全文件 10 行 357 字节，本次 range 内**无改动**（`git diff` 空）。
    - **判定器在真实仓库上的自证**：`spec-evolution` 自身 **0 条 finding**（C-01~C-10 全绿）；其余 11 条（3 HIGH + 8 MID）分布于 `clarification-protocol`(5) / `agy-delegation-workflow`(2) / `doc-governance`(2) / `dual-round-review`(2)，**全部为既有技术债**，与本次交付无因果关系，已由 RFC-0004:350 裁定与 BK-0033~BK-0039 承接。
  - **精准修复补丁是否引入新的状态死锁 / 条件调用 / 测试隔离破裂 —— 未发现**：
    - 无状态死锁：`pycache_prefix()` 的模块级缓存 `_pycache_dir` 仅在首次调用时求值，`CollectError` 抛出后不写缓存，重试语义正确。
    - 无条件调用破坏：`collected_gates()` 对 `gates` 键缺失、`None`、`[]`、`{}`、畸形值一律返回 `{}`，调用方 `build_findings` / `render_report` 的 `sorted(...)` 迭代安全。
    - 测试隔离未破裂：`conftest.py` 全程使用 `tmp_path`（`build_repo(tmp_path / "repo")`），无固定共享路径；干净副本全量 **56 passed**（11 秒）。
    - 无破坏性级联重构：`git diff --stat` 显示本次 range 共 25 文件、2032 insertions / 71 deletions，改动集中在 `collect-facts.py`(+92/-)、`judge.py`(+82/-)、三个测试文件与文档，**无无关文件被顺手重构**。
  - **我独立发现的两处残余（均非阻断）**：
    1. **`DeltaR1-1` 的修法未与宣称同宽（嵌套类型仍可伪装退出码）**。实测 5 例（均在 `/tmp` 副本内）：`{"skills":[{"name":...,"path":123}]}` → **rc=1 且写出报告**；`{"skills":[{"name":...,"files":"x"}]}` → **rc=1 且写出报告**；`{"root_prompt":{...,"baseline":5}}` → **rc=1，裸 `TypeError: argument of type 'int' is not iterable`，报告未写出**。三者均与「存在 BLOCKER/HIGH」同码。对比：`skills=5`、`root_prompt="junk"`、`repo_root=123`、`skills=[{}]`、`gates=0`、`gates="junk"` 六例已正确收口为 rc=2 且不写产物。→ 修法**部分有效**，`DeltaR1-1` 维持 🟡 P2，建议改以 `main()` 顶层兜底 `except Exception` → 2 的**更简形态**一次关闭全类（该形态比白名单更短且完备）。
    2. **`atexit` 清理在信号终止下不执行**。`atexit.register(shutil.rmtree, ...)` 只在解释器正常退出时触发；`SIGTERM`/`SIGKILL`/崩溃路径下 `/tmp/spec-evolution-pycache-*` 会残留累积。影响面极小（每次仅一个空目录、随机名、0700），且**严格优于**修复前的固定名持久目录，不构成回归。→ 记为 🟡 观察项，不阻断。
  - **是否全盘采纳 R1 意见导致非必要破坏性级联 —— 否**。本轮对 `DeltaR1-4`（章节指针）的处置尤为克制：**只改指针、不重构章节体系**（`checks-spec.md` 保持 §1~§6 现状，仅四处指针 `§4`→`§5`）。我全仓复核确认四处指针全部到位且**零残留错误指针**：`SKILL.md:24`、`spec-evolution-design.md:161`、计划 `:194`、计划 `:2115` 均指向 §5「已知表达上限」，与 `checks-spec.md` 实际标题（`:55 ## 5. 已知表达上限`）语义一致；剩余 `§4` 引用（计划 `:31`、`:2300`）语义正确（指 D-19 记述本身）。无一处误改。
  - **归档与转录保真核验**：
    - R1 报告经**归档文件通道**传入，指纹实测复算 `313ee5f7ccc3`（38749 字节），与索引台账登记**逐字一致**。
    - R1 报告结构完整：§4 潜在缺陷清单含「稳定 ID」列，15 行齐备，schema 合规。**不降低采信度**。
    - 产出通道：查阅 `docs/project/reviews/2026-10-12-spec-evolution-v1/README.md` 轮次台账，R1 行（`delta-r1-fe8da78..9db83c7.md`）「写入形态」列为 **`direct`**；首轮 R1 行同为 **`direct`**。故**转录改写残差不存在**。但须明确：`direct` 仅表示落盘方式为子智能体直写，**不得**据此声称其内容已获密码学证明——指纹只能证明「文件自归档后未被篡改」，不能证明「文件内容为真」。退役行 `delta-r1-fe8da78..9e66a5d.md`（`retired`）区块标题不符门禁 schema，不计入 ID 并集，本次仅作背景参考。
    - **本节未激活（非客户端/SSR 改动）**：`git diff` 覆盖 25 个文件，全部为 Python 脚本、测试、Markdown 文档与 JSON 基线常量，**零客户端/SSR/浏览器代码**。SSR/沙盒安全维度与产物 Schema 维度均不激活（R1 报告首部未声明 `> **Review Schema**: artifact`）。

## 2. 最终裁决明细表 (Final Verdict Synthesis Table)

### 2.1 首轮 ID 命名空间（`R1-1`…`R1-15`）最终定性

| 稳定 ID (沿用 R1) | 检查点 / 文件位置 | 原始 R1 评级 | 变更归属 (本次引入/历史既有) | 终审裁决 | 最终定性分析与裁决理由 | 处置要求 |
|:---|:---|:---:|:---:|:---:|:---|:---|
| R1-1 | `skills/spec-evolution/scripts/collect-facts.py`（`subprocess_env()` / `pycache_prefix()`）；`tests/conftest.py` | P1 | 本次引入 | 🟡 **P2 优化建议**（阻断已解除） | 首轮 P1 成立且经三轮治理：`d8aa611` 加 `-B` → `7449aae` 发现真实泄漏路径是显式 `py_compile.compile()`（同时无视 `-B` 与 `PYTHONDONTWRITEBYTECODE`），改用 `PYTHONPYCACHEPREFIX` 整体改道 → `2100973` 再以 `mkdtemp` + containment 收口。**我实测根治**：干净副本上以门禁启用运行，仓库内文件清单前后 `diff` 为空。该轮次已关闭，**当前无阻断项**。 | 无需进一步改动；保持 `test_gi6_*` 三条回归测试常绿 |
| R1-2 | `judge.py` 退出码 vs `SKILL.md` / `checks-spec.md` / 设计书 | P1 | 本次引入 | 🟡 **P2 优化建议**（阻断已解除） | 首轮 P1 成立。现已建立单一权威：`checks-spec.md` §4 严格三态表 + `SKILL.md:84` 权威指针，且 `SKILL.md` 退出码表与 §4 逐字一致。实测 rc=2 时不写任何产物、rc=1 时写报告，语义与文档同宽。**阻断解除**。 | 无需改动；后续若新增退出码取值，须同批次更新 §4 与 `SKILL.md` 表 |
| R1-3 | `judge.py` `collected_gates()` / `render_report()` 的 `--no-gates` 分支 | P1 | 本次引入 | 🟡 **P2 优化建议**（阻断已解除） | 首轮 P1 成立。现渲染为中性三态「（未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论）」，肯定句 `grep -c` = 0；且 `collected_gates()` 已把 `[]`/`{}`/`0`/畸形 dict 全部归入「未采集」，关闭 DR1-5 残余 fail-open。**阻断解除**。 | 无需改动 |
| R1-4 | `collect-facts.py` 门禁子进程输出编码 / `print` 前缀；`judge.py` 同类 | P2 | 本次引入 | 🟡 **P2 优化建议**（部分修复，保持开放） | 两处 `subprocess.run` 已加 `encoding="utf-8", errors="replace"`，但 **`print()` 侧未修**。我实测：`LC_ALL=C PYTHONIOENCODING=ascii` 下采集器在 `collect-facts.py:403` 抛未捕获 `UnicodeEncodeError: 'ascii' codec can't encode character '\u2705'`，**rc=1**。真实残留，已登记 BK-0033。 | 保留 BK-0033；建议把 `print` 前缀改 ASCII 或对 stdout 设 `errors="replace"` |
| R1-5 | `collect-facts.py` baseline 静默降级；`judge.py` `load_facts` 校验面 | P2 | 本次引入 | 🟡 **P2 优化建议**（部分修复，保持开放） | `load_facts` 已补顶层键类型校验（6 类非法输入实测收口 rc=2）；但**嵌套字段类型仍未校验**，且 baseline 解析失败仍为静默降级。我实测 `root_prompt.baseline=5` → 裸 `TypeError`、**rc=1**，与「存在 BLOCKER/HIGH」同码——R1-5 与 DeltaR1-1 的原始机理在此点**仍然成立**。已登记 BK-0034。 | 保留 BK-0034；建议改以 `main()` 顶层 `except Exception` → 2 的完备形态收口 |
| R1-6 | `judge.py` `validate_anchor()` 的 `[REPO:*]` 分支 | P2 | 本次引入 | 🟡 **P3 优化建议**（已闭环；维持首轮 R2 的 P2→P3 下调） | 首轮 R2 已由 P2 下调 P3（理由：真实攻击面需攻击者先控制仓库内文件，届时已无「只读不变式」可守）。现已修复：`_resolve_within(repo_root / rel, repo_root)` 对 `[REPO:*]` 与 `[SKILL:*]` 同源做 containment，越界即返回失败原因 → rc=2。**降级维持正确，且已闭环**。 | 无需改动 |
| R1-7 | `docs/proposals/RFC-0004-spec-evolution.md` §3.4 锚点契约 | P2 | 本次引入 | 🟡 **P2 优化建议**（已闭环；子指控失实已纠正） | 主干成立且**比 R1 所述更严重**：实现已用 `[REPO:*]` 表达 C-07 四注册面与 C-09 门禁证据，RFC 原文只登记 `[SKILL:*]`/`[RULE:*]`。已补登 `[REPO:<repo-relative-path>[:<line>]]` 形态与行号语义（RFC-0004 V0.5.0）。**子指控「`grep -c "CI\|pytest"` 恒真」实测不成立**（该串在 1787 行中命中 0 次）。 | 已闭环；纠正后的机理叙述以 D-15 为准 |
| R1-8 | RFC-0004 §3.5 门禁不变式 vs `design.md` vs `tests/` | P2 | 本次引入 | 🟡 **P2 优化建议**（保持开放） | 实质成立、机理叙述失实：R1 把 RFC 的 `GI-1`/`GI-3` 与设计书定义当作同一组。核实二者确非同一定义（RFC:250 的 GI-3 被 `design.md:106` 重定义为「报告锚点是 findings.json 锚点子集」，与 `validate_anchor()` 的存在性校验语义不同）。属追溯表未对齐的文档契约债，已登记 BK-0035。 | 保留 BK-0035；登记时须先择一定义并同步 RFC:412 追溯表 |
| R1-9 | `tests/conftest.py` 夹具为两条设计决策让路（`__pycache__` 过滤、共享路径） | P2 | 本次引入 | 🟡 **P2 优化建议**（已闭环） | 已随 R1-1 同批修复：夹具全程使用 `tmp_path`（`build_repo(tmp_path / "repo")`），无固定共享路径；`test_gate_invariants.py` 以 `-B` 派生子进程。干净副本全量 56 passed，无隔离破裂。 | 无需改动 |
| R1-10 | `collect-facts.py` `--skills` 未知技能名静默丢弃 | P3 | 本次引入 | 🟡 **P3 优化建议**（保持开放） | 未修复：`selected = [n for n in all_names if only is None or n in only]` 仍静默过滤拼错的技能名 → 0 技能、CLEAN、rc=0。已登记 BK-0036。属诊断友好性缺口，不影响当前正确性。 | 保留 BK-0036 |
| R1-11 | `collect-facts.py` `--out` / `judge.py` `--report` 路径可覆盖仓库内被跟踪文件 | P3 | 本次引入 | 🟡 **P3 优化建议**（部分修复，保持开放） | 采集器侧已收紧（`if not out.parent.is_dir(): return 2`，不再 `mkdir`）；但 `judge.py:381,386` 仍 `path.parent.mkdir(parents=True, exist_ok=True)`，仍可静默覆盖仓库内被跟踪文件。已登记 BK-0037。 | 保留 BK-0037 |
| R1-12 | `collect-facts.py` `readme` 注册面匹配形式 | P3 | 本次引入 | 🟡 **P3 优化建议**（已闭环） | 已修复：`readme` 改用与 `docs_index` 同一严格形式 `f"skills/{name}/SKILL.md" in readme_text`（`:240`，含说明注释），消除了前缀兄弟技能（`skills/{name}-suffix`）造成的 C-07 **HIGH 假阴性**。新增 `test_readme_registration_requires_exact_skill_path` 钉住该行为。 | 无需改动 |
| R1-13 | `collect-facts.py` C-08 正则 vs `skills/_shared/tests/test_cross_skill_links.py` | P3 | **历史既有**（本次变更扩大其表面积） | 🟡 **P3 优化建议**（归属表述纠正） | 正则双实现的技术债在 `fe8da78` 前即已存在；本次改动使 `test_cross_skill_links.py` 新增一处同源副本，扩大了漂移面。首轮 R1 标为「本次引入」**归属不精确**，但首轮 R2 已登记 BK-0038 而非阻断，处置正确。`checks-spec.md` §5 第 3 条已显式登记该漂移风险，并以 C-09 运行该测试本身作为缓解。 | 保留 BK-0038；归属表述以本行为准 |
| R1-14 | `judge.py` `_check_line()` 锚点行号下限 | P3 | 本次引入 | 🟡 **P3 优化建议**（已闭环） | 已修复：`if n < 1 or n > total: return f"锚点行号越界: {label}:{line}（共 {total} 行，行号从 1 起）"`，`[REPO:docs/index.md:0]` 现被拒 → rc=2。另补 `if not target.is_file()` 拒绝目录锚点带行号。 | 无需改动 |
| R1-15 | `agy-delegation-workflow` / `clarification-protocol` / `doc-governance` / `dual-round-review` 存量交付面缺口 | P3 | **历史既有** | 🟡 **P3 优化建议**（准予放行） | R1 **自行标注**「非本次 Diff 引入」，无越界挑刺。RFC-0004:350 已裁定「检测与修复分离」，`F-1`~`F-9` 不随本次交付修复（唯一例外 F-9 因与「登记新技能」同处编辑而随附）。我实测真实仓库 11 条 findings 全部可归因于既有技能债务，`spec-evolution` 自身 0 条。已登记 BK-0039。 | 保留 BK-0039，由后续专门的存量修复轮次承接；**不得阻断本次交付** |

### 2.2 本轮 Delta 轮 4 条发现复核（`DeltaR1-1`…`DeltaR1-4`）

| 稳定 ID (本轮) | 检查点 / 文件位置 | 原始 R1 评级 | 变更归属 (本次引入/历史既有) | 终审裁决 | 最终定性分析与裁决理由 | 处置要求 |
|:---|:---|:---:|:---:|:---:|:---|:---|
| DeltaR1-1 | `skills/spec-evolution/scripts/judge.py` `load_facts()`（原 `:59-61,75-83`） | P2 | 本次引入 | 🟡 **P2 优化建议**（部分修复，保持开放） | 指控成立：`load_facts` 原只校验顶层键**在场**，`skills=5` 等触发 `TypeError` → 解释器 **rc=1**，与「存在 BLOCKER/HIGH」同码，编排方只读退出码即把「输入坏了」采信为「存在高危结论」。已修：6 类非法顶层输入实测收口 rc=2 且不写产物。**但修法未与宣称同宽**——嵌套字段仍未校验，我实测 `skills[].path=123`、`skills[].files="x"` 仍 rc=1 且**写出报告**，`root_prompt.baseline=5` 仍 rc=1 裸 traceback。原指控属性在嵌套面依然成立。 | 保留 BK-0034；建议改以 `main()` 顶层 `except Exception` → 2 的**更简且完备**形态收口，替换逐键白名单 |
| DeltaR1-2 | `skills/spec-evolution/scripts/collect-facts.py` `pycache_prefix()` | P2 | 本次引入 | 🟡 **P2 优化建议**（已闭环） | 指控成立且机理实测可复现：固定名 `/tmp/spec-evolution-pycache` 可预测、共享、跨运行持久，`/tmp` 为 `drwxrwxrwt`，本地用户可抢先植入畸形字节码被门禁进程读取执行——**真实进程内任意代码执行**。已修：`tempfile.mkdtemp(prefix=..., dir=base)` 独占随机名 + 0700 + `atexit` 清理。**变异对照实测**：改回固定名 → `test_gi6_pycache_prefix_is_per_run_and_private` 转红；仅删 containment → 该测试保持绿而另一条转红（判别力独立，无虚绿）。 | 已闭环；`atexit` 在 SIGTERM/SIGKILL 下不执行致 `/tmp` 可能残留空目录（随机名 0700，影响极小，**严格优于**修复前），记为观察项即可 |
| DeltaR1-3 | `skills/spec-evolution/scripts/collect-facts.py` `pycache_prefix()` 越界校验 | P3 | 本次引入 | 🟡 **P3 优化建议**（已闭环） | 指控成立：重定向根原在模块级由 `gettempdir()` 推导且不校验越界，`TMPDIR` 指向仓库内或临时目录全不可写回落 `os.getcwd()` 时，镜像整体落入仓库，GI-6 静默失守。已修：求值移入 `pycache_prefix(repo)`，**在创建任何目录之前**校验 `base == repo or repo in base.parents`，不成立即 `CollectError` → rc=2。**端到端实测**：`TMPDIR=<仓库自身>` → 报错文案 + rc=2，仓库内文件数不变（230→230），零镜像文件。 | 已闭环，无需改动 |
| DeltaR1-4 | `skills/spec-evolution/SKILL.md:24`、`docs/explanation/architecture/spec-evolution-design.md:161`、计划 `:194` / `:2115` | P2 | 本次引入 | 🟡 **P2 优化建议**（已闭环） | 指控成立：D-19 新增 `checks-spec.md` §4 并把原 §4/§5 顺延为 §5/§6，三处 `§4` 指针未同步而实际内容已顺延，D-19 自述的「章节编号全文件复核」**宣称宽于取证**。已修：四处指针改为 `§5`。**我全仓复核确认零残留错误指针**：四处均指向 §5「已知表达上限」，与 `checks-spec.md:55` 实际标题一致；剩余 `§4` 引用（计划 `:31`、`:2300`）语义正确。 | 已闭环；「宣称与取证同宽」纪律已在 D-27 行如实登记，无需追加 |

## 3. 终审放行结论

- **阻断项统计**: 🔴 **0** 个
- **优化建议统计**: 🟡 **19** 个（首轮命名空间 15 条全部为建议级：其中 7 条已闭环、2 条部分修复保持开放、6 条保持开放；本轮 `DeltaR1-1`~`DeltaR1-4` 4 条全部为建议级，其中 3 条已闭环、1 条部分修复保持开放。19 条中无一构成阻断）
- **驳回误报统计**: ⚪ **0** 个（首轮 R1-7 的「恒真」子指控与 R1-13 的「不同源」表述确属失实，但二者主干均成立且已按 🟡 建议登记，不整体驳回；本轮 Delta R1 四条零误报）
- **交付判定**: ✅ **准予交付 (Blockers == 0，允许提交并进入下一环节)**

**放行理由综述**：首轮三个 P1 阻断项（`R1-1` GI-6 只读不变式、`R1-2` 退出码语义、`R1-3` `--no-gates` 三态）经三轮修复后，**我逐条实际执行命令独立复验，全部根治**，且未采信测试断言的字面绿——`R1-1` 以真实仓库 + 真实门禁 + 前后文件清单 `diff` 为空取证；`R1-2`/`R1-3` 以端到端渲染与退出码实测取证。本轮精准修复补丁（`2100973`）的纯度经**变异对照**确认：新测试具备独立判别力，非虚绿。`baseline.json` 与 `contexts/AGENTS.md` 的行数/字节数逐值一致（97 行 / 10746 字节）。判定器在真实仓库上对 `spec-evolution` 自身零 finding，其余 11 条全部可归因于既有技术债，符合 RFC-0004「检测与修复分离」的既定边界。全部 19 条建议中，7 条已闭环、6 条与既有技术债均已在 `BK-0033`~`BK-0039` 登记为可追踪待办，具备明确触发条件与验收准则，**不构成本次交付的阻断理由**。

**遗留观察项（不影响放行，供后续轮次承接）**：① `judge.py` `load_facts` 的逐键白名单未覆盖嵌套字段类型，建议改以 `main()` 顶层兜底收口（`DeltaR1-1` / `R1-5`）；② `collect-facts.py:403` 的 `print` 在 ASCII stdout 下抛 `UnicodeEncodeError` 且 rc=1（`R1-4` / BK-0033）；③ `atexit` 在信号终止路径下不执行，`/tmp` 可能残留随机名空目录（`DeltaR1-2` 残留，影响极小）。
