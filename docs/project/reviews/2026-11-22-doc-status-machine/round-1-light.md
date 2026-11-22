# 第一轮红队审查报告（Light 模式）— 文档状态机（RFC-0007）

> **审查基线**: `79d031c..HEAD`（HEAD = `a53a0db`）
> **审查面**: `git diff 79d031c..HEAD -- skills/`（3 文件，+297/−1）
> **契约**: [RFC-0007](../../../proposals/RFC-0007-doc-status-contested.md) §4、[实施计划](../../plans/2026-11-22-doc-status-machine.md)、[GOVERNANCE](../../../GOVERNANCE.md) §4 红线 8
> **口径**: 仅 P0/P1 计入 Blockers；只读审查，工作树除本报告外零改动
> **审查日期**: 2026-11-22

---

## 1. 命令与输出

### 1.1 基线核对

```bash
$ git log --oneline -3
a53a0db docs(doc-governance): 复核点跟随 10359e7 重钉（状态机落地后）
10359e7 feat(doc-governance): 文档状态机（RFC-0007）—— 把「有争议」与「已被取代」升为一等公民
79d031c docs(doc-governance): 分层机器地图交付收尾（RFC-0006 → Implemented）

$ git diff --stat 79d031c..HEAD -- skills/
 skills/doc-governance/scripts/audit-doc-health.py  | 154 +++++++++++++++++++++
 skills/doc-governance/templates/doc-control-header.md |   9 +-
 skills/doc-governance/tests/test_doc_status.py     | 135 ++++++++++++++++++
 3 files changed, 297 insertions(+), 1 deletion(-)
```

### 1.2 回归面：单测与五道门禁

```bash
$ python3 -m pytest skills/doc-governance/tests -q
255 passed in 22.17s
```

| 门禁 | 命令 | 实测 |
| :--- | :--- | :--- |
| G1 机器地图 | `generate-llms-txt.py --root docs --output docs/llms.txt --split --check` | `✅ 机器地图校验通过（6 个文件，根 883 字节）` rc=0 |
| G2 断链 | `check-doc-links.py --root docs` | `共扫描 105 个 Markdown 文件 / 未发现任何 404 断链` rc=0 |
| G3 控制头版本 | `check-doc-control-sync.py --root docs` | `共检查 57 个 Markdown 文件 / 100% 保持一致` rc=0 |
| G4 真值轴 | `check-doc-drift.py --root docs --repo . --fail-on-drift` | `声明 3/56 篇（覆盖度 5.4%）｜fresh 3｜真值分 15.0 / 15` rc=0 |
| G5 健康体检 | `audit-doc-health.py --root docs --repo .` | `总得分: 100.0 / 100`，`PASS` rc=0 |

### 1.3 真实状态分布（`audit-doc-health.py --root docs --repo .`）

```text
📌 [文档状态机 · 未决冲突清单]:
   * 状态分布: Active 50｜Contested 0｜Superseded 0
   （无争议、无取代：全库 Active）
```

补充实测（同一棵树）：

- `audit_health` 的扫描面是 **98 篇**（`合规文档: 98/98`），而 `check_doc_status` 实际只覆盖 **50 篇**——48 篇被 `backlog` 过滤掉，占 49%。
- 全库显式写 `文档状态` 的只有 5 篇，取值全为 `Active`；真实 `Contested`/`Superseded` **0 篇**。
- 因此计划 A-5「把本 RFC 计划文档与至少一份文档标注为真实状态（制造非空清单）」**未执行**；「未决冲突清单」的两条真实分支（Contested 年龄、Superseded 指针）只在单测里跑过，从未在真实文档上产生过输出。

### 1.4 攻击探针矩阵（隔离 fixture，`check_doc_status(root, now="2026-11-22")` 直调）

探针脚本落在 `/tmp/probe_doc_status.py`、`/tmp/probe2.py`，未写入仓库；每组 fixture 独立临时根。

**A 组：取值与形态（C-1/C-2/C-3 能否被绕过）**

| 输入 | 期望 | 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| `文档状态: superseded`（小写）+ 有效指针 | 阻断 | `取值非法（superseded）` → 阻断 | ✅ 拦得住（fail-closed） |
| `文档状态: SUPERSEDED` | 阻断 | `取值非法` → 阻断 | ✅ |
| `文档状态: （Superseded）`（全角括号） | 阻断 | `取值非法（（Superseded））` → 阻断 | ✅ |
| `文档状态: Superseded `（尾空格）/ Tab / 全角空格 | 正常按 Superseded 判定 | strip 后 `Superseded`，零 issue | ✅ 归一化正确 |
| `文档状态: **Superseded**` | 阻断 | `取值非法（**Superseded**）` | ✅ |
| YAML `status: Superseded`，无引用块控制头 | 按契约应阻断/至少可见 | 计为 **Active**，零 issue | ❌ 静默逃逸 |
| YAML frontmatter + 下方引用块 `文档状态: Superseded` + 有效指针 | 按 Superseded 判定 | 计为 **Active**，零 issue | ❌ 引用块被 YAML 整体遮蔽 |
| 表格控制头 `\| **文档状态** \| Superseded \|` + `\| **取代于** \| ./gone.md \|` | C-2 阻断 | 计为 **Active**，零 issue | ❌ 完全失明 |
| 控制头位于第 55 行（前 50 行填充） | 按 Superseded 判定 | 计为 **Active**，零 issue | ❌ 50 行窗口外静默丢弃 |
| 真实 `Active` 头 + 第 20 行围栏代码块内示例 `文档状态: Superseded` | 保持 Active | 被翻成 **Superseded**，并因示例里的 `./x.md` 触发 C-2 阻断 | ❌ 假阳性（阻断合法文档） |
| 模板骨架逐字复制（`templates/doc-control-header.md`） | 应可交付 | `取值非法（Active <!-- Active \| Contested \| Superseded -->）` → **REJECTED rc=1** | ❌ 模板自伤（见 T-1） |

**B 组：`取代于` 解析**

| 指针 | 期望 | 实测 | 判定 |
| :--- | :--- | :--- | :--- |
| `./a.md` / `a.md`（自指两种写法） | 阻断 | 均 `「取代于」指向自身` | ✅ |
| `./dir`（目录）/ `./x.txt` / `./gone.md` | 阻断 | 均 `目标不存在或不是 .md` | ✅ |
| `/etc/passwd` | 阻断 | 阻断（后缀非 .md） | ✅ |
| `../reference/new.md`（根内父级） | 通过 | 通过 | ✅ |
| `./new.md#sec`（带锚点） | 契约未禁止 | **阻断**（后缀 `.md#sec`） | ⚠️ 过严，与 C-4 的锚点支持口径冲突 |
| `/tmp/outside/x.md`（绝对路径、仓库外） | 应阻断（模板 :39「仓库内相对路径」） | **通过** | ❌ 越界（T-5） |
| `../../../../../tmp/outside/x.md`（相对逃逸） | 应阻断 | **通过** | ❌ 越界（T-5） |
| 重复两行 `取代于`（先断后通） | 至少报告其一 | 静默 last-wins，零 issue | ⚠️ 静默 |

**C 组：C-4（Active 引用 Superseded）**

| 引用形态 | 实测 | 判定 |
| :--- | :--- | :--- |
| `[旧版](./old.md)` | 警告 | ✅ |
| `![图](./old.md)`（图片） | **警告**（正则 `\]\(` 同样匹配图片语法） | ✅ 题设假设不成立 |
| `[旧版](./old.md#sec)` / `[旧版](old.md)` | 警告 | ✅ |
| `[ref]: ./old.md`（引用式定义，含 `[x][ref]` 用法） | **无警告** | ❌ 漏报 |
| `[旧版](./old.md "标题")` | **无警告** | ❌ 漏报 |
| `[旧版](./OLD.MD)` / `[旧版](./old)` | **无警告** | ❌ 漏报 |
| Contested 文档引用 Superseded | 无警告 | 符合 RFC（只约束 Active） |

**D 组：C-5（Contested 年龄）**

| 修订表形态 | age_days | 判定 |
| :--- | :--- | :--- |
| 降序（最新在首行，2026-11-20 / 2026-01-01） | 2 天 | ✅ |
| **升序**（最旧在首行，2026-01-01 / 2026-11-20） | **325 天** | ❌ 取到最旧行（T-8） |
| 无修订历史章节 | `null`（显示「未知」，永不超期） | ❌ 静默失效 |
| 日期写 `2026/01/01` | `null` | ❌ |
| 章节与表格之间夹一段说明 | `null`（`elif line.strip(): break`） | ❌ |
| 修订日期列写「待补」、描述列含 `2026-01-01` | **325 天**（取了描述列的日期） | ❌ 假阳性 |
| 章节后有两张表 | 只读第一张表 | ⚠️ 新增表不生效 |

**E/G 组：排除面与降级**

| 场景 | 实测 | 判定 |
| :--- | :--- | :--- |
| `docs/x/backlog/real-doc.md`（真实文档，`文档状态: Bogus` + 断指针） | 零 issue、counts 全 0 | ❌ 整体跳过（T-9） |
| 根路径含名为 `backlog` 的目录分量（`/tmp/x/backlog/docs`） | 扫描 0 篇、零 issue（门禁整体归零） | ❌ 环境相关全量失效（T-9） |
| `evaluate_verdict` 的 `res` 无 `doc_status` 键 | `(True, [])` | ✅ 安全降级 |
| `doc_status: {}` | `(True, [])` | ✅ |
| `doc_status.issues` 非空 | `(False, ["1 处文档状态违规"])` | ✅ |

### 1.5 两个端到端复现

**(a) 模板复制件 → 硬阻断（rc=1）**

```text
⛔ 文档状态违规: reference/filled.md: 文档状态取值非法（Active            <!-- Active | Contested | Superseded -->），只允许 Active/Contested/Superseded
📌 [文档状态机 · 未决冲突清单]:
   * 状态分布: Active 0｜Contested 0｜Superseded 0｜非法 1
   （无争议、无取代：全库 Active）
🚫 诊断结论: REJECTED（1 处文档状态违规），请修复后重测
rc=1
```

同一屏既报「文档状态违规」又断言「全库 Active」（T-10）。若用户把注释删干净但保留骨架第 12 行 `取代于: ./new-doc.md`，则改为 C-3 阻断（`状态为 Active 却出现「取代于」`）——两条路都过不去。

**(b) 只含 backlog 文档的根 → 全量静默 PASS（rc=0）**

```text
📌 [文档状态机 · 未决冲突清单]:
   * 状态分布: Active 0｜Contested 0｜Superseded 0
   （无争议、无取代：全库 Active）
🏁 诊断结论: PASS (健康度达标，准予交付) ✅
rc=0
```

该文档带有 `文档状态: Bogus` 与指向不存在文件的 `取代于`，状态机零告警。

---

## 2. 六项结论

### 2.1 判据可绕过：取值层拦得住，形态层三处静默失明

- **C-1 对「同一个键」是可靠的**：小写、大写、全角括号、加粗、非法词全部阻断；尾随空白/Tab/全角空格被 `strip()` 归一化后按合法值处理。这一层没有绕过。
- **绕过不在取值，而在「哪些行会被当成状态」**：`check_doc_status` 把解析完全委托给共享的 `parse_frontmatter`（`audit-doc-health.py:292`），而该函数有三条早退/窗口规则（`:456-462` YAML 优先、`:465` 只扫前 50 行、`:480` 表格白名单不含 `文档状态`/`取代于`）。三者都不报错、不告警，直接让文档退化为 `Active`。
- **反向假阳性同样存在**：解析器不感知围栏代码块，前 50 行内的**示例**会覆盖真实状态（实测把 Active 翻成 Superseded 并触发阻断）。本仓库正是「大量展示控制头示例」的文档工程仓库：RFC-0007 自己的示例在第 64 行，距离 50 行窗口只剩 14 行余量。
- 结论：**契约写在引用块上时判据成立；一旦文档采用 YAML、表格或「示例先于正文」的形态，C-1/C-2/C-3 全部失效，且没有任何提示。**

### 2.2 `取代于` 解析：自指/目录/非 md/缺失都正确，边界两端各漏一个

- 正确：`a.md` 与 `./a.md` 两种自指均判「指向自身」；目录、`.txt`、缺失路径、`/etc/passwd` 均阻断；根内 `../reference/new.md` 正常解析。
- 过严：`./new.md#sec` 被阻断。C-4 的链接正则（`:344`）明确支持 `#anchor`，两条判据对同一份文档的「带锚点引用」口径相反；模板与 RFC 也没有说锚点非法。
- 过松：绝对路径 `/tmp/x.md` 与 `../../..` 逃逸均通过 C-2。RFC §2/D-4 与模板 `:39` 都写「**仓库内**相对路径」，但 C-2 的机械条件（`:314-318`）只校验「存在 + 后缀 .md + 非自身」——实现精确落在 RFC §4.2 的枚举上，却与 §2/D-4 的语义冲突。**这是契约内部的措辞不一致，不是纯实现 bug**，但后果是「取代链」可以指向仓库外，C-4 永远看不到那个接替者。
- 附带：重复 `取代于` 键静默 last-wins，先写的坏指针不会进入报告。

### 2.3 C-4/C-5 准确性：图片链接不漏，但引用式/带 title/大写扩展名全漏；C-5 的「最新行」假设与仓库既有实现相反

- **C-4**：题设怀疑的 `![x](./old.md)` **会被捕获**（`\]\(` 同样匹配图片语法），带 `#anchor`、不带 `./` 也都捕获。真正的漏报是引用式 `[ref]: ./old.md`、带 title `(./old.md "t")`、`.MD` 大写、无扩展名。C-4 按 RFC 只是警告，故不阻断，但「未决冲突清单」的完整性依赖它。
- **C-5 主缺陷**：`_latest_revision_date`（`:243-258`）取「章节后第一行含 `YYYY-MM-DD` 的表格行」，隐含**降序**假设。仓库内已有反例：[RFC-0004](../../../proposals/RFC-0004-spec-evolution.md) 的修订表是升序（`:21-25`，V0.2.0 `2026-10-12` → V0.6.0 `2026-11-12`），而姊妹门禁 `check-doc-control-sync.py:171-181` **已经显式实现了升序判定**（`if v_last > v_first`）。新函数没有复用该判定，同一仓库两套「最新行」语义。
- **C-5 次生缺陷**：34/50 篇被扫文档没有可识别的修订历史日期（无该章节、`2026/01/01` 格式、章节与表格之间夹段落、修订日期列写「待补」），`age_days=None` 显示「未知」且**永不超期**；日期还可能取到描述列里的日期（实测 325 天假阳性）。阈值常量 `CONTESTED_MAX_AGE_DAYS`（`:239`）定义后从未使用，`main:1173` 硬编码 90。

### 2.4 误伤风险：`backlog` 排除过宽、理由不成立、且是唯一未登记的豁免

- 覆盖面：`docs` 下 98 篇被审计文档，状态机只覆盖 50 篇（**49% 不在门禁内**），而输出仍写「全库 Active」。
- 排除判据用**绝对路径分量**（`:284` `"backlog" not in f.parts`）：`docs/x/backlog/` 下的真实文档被整体跳过（实测非法状态 + 断指针零告警）；仓库若检出在名为 `backlog` 的目录下，整道门禁扫描 0 篇（实测）。
- **排除理由与事实相反**：代码注释 `:293-294` 称「否则 47 张卡片会被误判为非法状态」。实测 48 篇 YAML 卡片**没有任何一篇**含 `文档状态` 键——`parse_frontmatter` 返回的是 `status`，而 `check_doc_status` 只读 `文档状态`。即使完全不排除 backlog，也不会产生一条误判。该行是建立在错误前提上的排除。
- `_llms/`、`AGENTS.md` 的排除与既有 `in_generated_map`/`is_router_file` 同源且已在 GOVERNANCE §4.1 登记；`project/reviews/**` 亦已登记。**唯独新的 `backlog` 豁免没有登记进 §4.1 豁免表**——该表正是 BK-0007 的机械契约面。

### 2.5 与既有门禁耦合：`--json` 前提不成立；字典只增键、缺失安全降级；但文本输出会自相矛盾

- `audit-doc-health.py` **没有 `--json` 参数，也没有任何 JSON 输出**（全文 grep 无 `json`），题设的「`--json` 向后兼容」在本 CLI 上无适用面。真正对外的是 `audit_health()` 返回字典：`doc_status` 是新增键，测试中没有精确键集合断言（唯一一处 `list(built.keys())` 在 `test_llms_split.py:75`，与本改动无关），只增键安全。
- `evaluate_verdict` 用 `(res.get("doc_status") or {})` 读取（`:173`），块缺失/为空均安全降级（实测 `(True, [])`）；新理由追加在 `reasons` 末尾，全仓没有按理由字符串解析的消费方（无 CI workflow / Makefile 调用 audit 并解析文案）。
- **但文本输出违反 BK-0028 的同屏互斥口径**：`main:1177-1178` 只判断 `contested`/`superseded`，不看 `issues`，于是「有非法状态文档」与「（无争议、无取代：全库 Active）」可以同屏出现（1.5a 实测）。
- `has_issues` 只影响「完美」文案，退出码由 `evaluate_verdict` 决定——C-4/C-5 确实不阻断，与 RFC §4.4 一致。

### 2.6 回归面：全绿，但状态机的真实分支从未被真实文档跑过

- `pytest 255 passed`；五道门禁 rc=0；audit 100/100。就「不破坏既有门禁」而言，本次改动干净。
- 真实分布 `Active 50 / Contested 0 / Superseded 0`；全库 0 篇非 Active。计划 A-5 未执行，清单的两条核心分支（年龄、取代链）只在单测 fixture 里存在。
- 计划文档自身仍写「状态: 进行中」「A-1..A-6 全 ☐」，RFC-0007 仍为 `In Review`；设计书 [doc-governance-design.md](../../../explanation/architecture/doc-governance-design.md) `:192` 仍把控制头写成四态 `[Draft | Active | Deprecated | Superseded]`，与 C-1「`Deprecated` 一律阻断」直接冲突（该行是历史行，但本次提交恰好重钉了该文件）。这些属边界外，记 P3。

---

## 3. 新缺陷清单

| 稳定 ID | 级别 | 归属 | 位置 | 缺陷 | 机理 / 证据 | 处置 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T-1** | **P1** | 本次引入 | `skills/doc-governance/templates/doc-control-header.md:11-13` | 模板骨架复制即被自家门禁阻断 | 行内 `<!-- ... -->` 注释被 `parse_frontmatter` 并入取值 → C-1 `取值非法（Active <!-- ... -->）`；删掉注释但保留第 12 行占位指针 → C-3 `Active 却出现「取代于」`。模板第 5 行标题明写「骨架（复制到文档 H1 之后）」，第 3 行只要求替换 `<...>` 槽位，未要求删注释 | 必改：把两处提示移出骨架围栏，或把 `取代于` 行改为 `> - **取代于**: <!-- 仅 Superseded 填 -->`（空值即不触发 C-3）；改后用复制件跑 audit 验证 PASS |
| T-2 | P2 | 本次引入 | `audit-doc-health.py:292` + `:456-462` | YAML frontmatter 早退使引用块控制头整体失效 | `parse_frontmatter` 命中 `---` 即 `return`，`status: Superseded` 不在 `文档状态` 键上；YAML + 引用块并存时后者被遮蔽（实测 Active、零 issue） | 解析器合并两种来源，或对「YAML 存在且无 `文档状态`」显式告警 |
| T-3 | P2 | 本次引入 | `:480` | 表格形态控制头完全失明 | 模式 C 白名单不含 `文档状态`/`取代于`，`\| **文档状态** \| Superseded \|` 计为 Active（实测） | 白名单补两键，或声明表格形态不支持并在文档中登记 |
| T-4 | P2 | 本次引入 | `:465` | 50 行窗口 + 无围栏感知 | 控制头在第 51 行起视同无字段；前 50 行内的代码块示例会覆盖真实状态并触发假阳性阻断（实测） | 解析时跳过围栏代码块；窗口改为「到首个 H1/正文为止」或全文件只认首个控制块 |
| T-5 | P2 | 本次引入 | `:314-318` | `取代于` 未约束仓库内 | 绝对路径与 `../../..` 逃逸均通过 C-2；模板 `:39` 与 RFC §2/D-4 要求仓库内 | 校验 `target.is_relative_to(root_dir.resolve())`，并统一 RFC §4.2 的措辞 |
| T-6 | P2 | 本次引入 | `:317` | 带锚点的合法指针被阻断 | `Path("./new.md#sec").suffix == ".md#sec"`；C-4 却支持 `#anchor` | 先剥 `#fragment` 再判后缀（与 C-4 同口径） |
| T-7 | P2 | 本次引入 | `:344` | C-4 漏报引用式 / 带 title / 大写扩展名 | 只匹配 `\]\(path.md[#...]\)`；`[ref]: ./old.md`、`(./old.md "t")`、`.MD` 全部漏（实测） | 复用 `check-doc-links.py` 的链接解析器，或补引用式定义正则 |
| T-8 | P2 | 本次引入 | `:243-258`、`:326-333` | C-5 年龄取「首行」而非「最新行」 | 升序表取到最旧日期（RFC-0004 为真实升序表，偏差 31 天）；无修订表/斜杠日期/夹段落 → `null` 永不超期；描述列日期会被误取 | 复用 `check-doc-control-sync.py:171-181` 的升降序判定；`null` 显式标注「不可判定」 |
| T-9 | P2 | 本次引入 | `:284`、`:293-294` | `backlog` 排除过宽、理由不成立、豁免未登记 | 98→50 篇；嵌套 `backlog/` 真实文档被跳过；绝对路径分量含 `backlog` 时门禁归零；48 篇卡片实测无一含 `文档状态`，注释所称误判不成立；GOVERNANCE §4.1 无此豁免 | 改为根相对 `project/backlog` 精确前缀，删除错误注释，并在 §4.1 登记（或直接移除该排除） |
| T-10 | P2 | 本次引入 | `main:1177-1178` | 「全库 Active」与非法状态同屏 | 只判断 `contested`/`superseded`，不看 `issues`；1.5a 实测同屏矛盾（BK-0028 禁止形态） | 条件加 `and not doc_status.get("issues")`，或改为「已扫 N 篇：…」 |
| T-11 | P3 | 本次引入 | `:239`、`main:1173` | 阈值常量死代码 + 两处复制 | `CONTESTED_MAX_AGE_DAYS` 定义未用，main 硬编码 `90`；RFC D-5 称「可配」 | 单一来源，参数化 |
| T-12 | P3 | 本次引入 | `tests/test_doc_status.py:65-135` | 测试缺口 | 10 条全为 `check_doc_status` 单函数用例；无 `evaluate_verdict` 集成、无 CLI 文案、无 YAML/表格/围栏/锚点/升序表用例 | 按本报告 A~E 组补契约用例（至少 T-1、T-2、T-8、T-10） |
| T-13 | P3 | 边界外 | 计划 / RFC / 设计书 | 交付态与文档态不一致 | 计划仍「进行中」且 A-1..A-6 全 ☐；RFC 仍 In Review；A-5 未执行；设计书仍写四态 | 状态流转 + A-5 补做（边界外，不阻断本次代码） |

---

## 4. 裁决

### 4.1 阻断项计数

| 级别 | 数量 | 条目 |
| :--- | :--- | :--- |
| P0 | 0 | — |
| **P1** | **1** | **T-1（模板自伤）** |
| P2 | 9 | T-2 ~ T-10 |
| P3 | 3 | T-11 ~ T-13 |

**Blockers = 1**（口径：仅 P0/P1 计入）。

### 4.2 裁决

**🔴 阻断交付（Blockers = 1）。**

阻断理由（一句话）：本次改动新增的**手写/迁移文档唯一推荐模板**（`templates/doc-control-header.md:5` 标题明写「骨架（复制到文档 H1 之后）」，`:3` 只要求替换 `<...>` 槽位）产出的文档**必然被本次新增的 C-1/C-3 阻断**——模板与门禁由同一次提交引入却互不自洽，属契约破损（P1），且修复面极小（模板 2 行），没有放行理由。

放行条件（最小修复集）：

1. 修 T-1：提示移出骨架，或把 `取代于` 骨架行改为空值 + 注释；用「复制骨架 → 只替换 `<...>` 槽位」的文档跑 `audit-doc-health.py` 必须 PASS。
2. 复跑 `pytest skills/doc-governance/tests -q` 与五道门禁，保持 rc=0。

非阻断跟进（登记后放行即可）：T-2/T-3/T-4 建议合并为「状态解析器形态收敛」一个批次；T-5/T-6 合并为「`取代于` 路径口径统一」；T-8 复用 control-sync 的升降序判定；T-9 与 T-10 是「报告面真实性」两项，建议同批修复。

### 4.3 残留风险（3 条）

1. **真实分支零覆盖**：全库 0 篇 `Contested`/`Superseded`，年龄、取代链、C-4 告警三条链路从未在真实文档上跑过；首篇非 Active 文档落地时，T-2/T-8 的失明面才会真正暴露。
2. **共享解析器**：T-2/T-4 的根因在 `parse_frontmatter`，它同时被 `check-doc-control-sync.py` 等门禁复用；若只修模板不动解析器，未来采用 YAML/表格形态的文档仍会静默逃逸。
3. **环境相关归零**：`backlog` 排除按绝对路径分量判断，换一个检出路径（或 CI 工作目录名恰为 `backlog`）即可让整道状态机门禁扫描 0 篇且零告警；该风险不随 T-1 修复消失。
