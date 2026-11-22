# Delta 复核报告（Light 模式）— 文档状态机 T-1~T-11 收口

> **审查基线**: `4fe9801`（修复提交）→ `HEAD = 7354819`（其后仅文档重钉 + 归档索引，代码面零改动）
> **上一轮**: [round-1-light.md](./round-1-light.md)（22,367 B，sha256 `c3dd9aa003dc58f64e141fdb665f3cc4c25f6e839eb8cefed58b9c4194edcd78`，Blockers=1：T-1）
> **契约**: [RFC-0007 V0.1.1](../../../proposals/RFC-0007-doc-status-contested.md)（新增 C-6）、[计划 D-01~D-09](../../plans/2026-11-22-doc-status-machine.md)、[控制头模板](../../../../skills/doc-governance/templates/doc-control-header.md)
> **口径**: 仅 P0/P1 计入 Blockers；只读复核，夹具全部落在 `/tmp`，工作树除本报告外零改动
> **审查日期**: 2026-11-22

---

## 1. 命令与输出

### 1.1 基线与工作树

```bash
$ git log --oneline -4
7354819 docs(review): 归档文档状态机红队报告（Blockers=1：T-1）
773f8ce docs(doc-governance): 复核点跟随 4fe9801 重钉（状态机 T 项收口后）
4fe9801 fix(doc-governance): 收口状态机红队 T-1~T-11
a53a0db docs(doc-governance): 复核点跟随 10359e7 重钉（状态机落地后）

$ git diff --stat 4fe9801..HEAD -- skills/ docs/proposals docs/project/plans
 docs/project/plans/2026-11-22-doc-truth-axis.md | 2 +-   # 仅复核点重钉，代码面冻结

$ git status --porcelain      # （空）
$ sha256sum docs/project/reviews/2026-11-22-doc-status-machine/round-1-light.md
c3dd9aa003dc58f64e141fdb665f3cc4c25f6e839eb8cefed58b9c4194edcd78  round-1-light.md   # 22,367 B，与上轮登记一致
```

### 1.2 T-1 端到端（模板 → 填槽 → 临时 docs → 真门禁）

方法：`cp -a` 整仓到 `/tmp/delta_e2e/repo`；用正则从 `templates/doc-control-header.md` 抽取 markdown 围栏内的骨架，按模板第 3 行「不得保留槽位文本」填槽（`REF-<NAME>-<YYYY>`→`REF-DEMO-2026`、`YYYY-MM-DD`→`2026-11-22`、`<所有者>/<修订人>/<审核人>/<一句话说明>` 全填，三个「（可选）」字段行按模板语义删除），写入 `docs/reference/rules/demo-from-template.md`；补 index 入链并重生成机器地图（消除与状态机无关的孤儿/地图噪声）后跑真 CLI。

```text
$ python3 skills/doc-governance/scripts/audit-doc-health.py --root docs --repo .
   * 孤儿文档引用度:     10.0 / 10 分 (孤立文档: 0/99)
📌 [文档状态机 · 未决冲突清单]:
   * 状态分布: Active 51｜Contested 0｜Superseded 0
🏁 诊断结论: PASS (健康度达标，准予交付) ✅
rc=0
```

生成物（逐字，去掉可选行后）：

```text
> **文档控制信息**
> - **文档标识**: REF-DEMO-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-22
> - **文档所有者**: 核心架构组
```

同一份文档追加 `> - **取代于**: ./new-doc.md`（仍是 Active）复跑：

```text
   ⛔ 文档状态违规: reference/rules/demo-from-template.md: 状态为 Active 却出现「取代于」（仅 Superseded 允许）
   * 状态分布: Active 51｜Contested 0｜Superseded 0
🚫 诊断结论: REJECTED（1 处文档状态违规），请修复后重测
rc=1
```

> 两点同时成立：① 模板骨架照抄+填槽**不再**被自家门禁阻断；② 手工给 Active 加指针**仍**被 C-3 阻断，且同屏不再出现「全库 Active」（T-11 生效）。

### 1.3 夹具矩阵（`/tmp/probe_delta*.py`，直调 `check_doc_status(root, now="2026-11-22")`）

**T-2 / T-3 / T-4（形态与污染）**

| 夹具 | 期望 | 实测 |
| :--- | :--- | :--- |
| YAML frontmatter + 引用块 `文档状态: Superseded` + 有效指针 | Superseded、零 issue | Superseded 1，issues=[] ✅ |
| YAML + 引用块 `Contested` + `争议点` | Contested | Contested 1，issues=[] ✅ |
| YAML 仅 `status: Superseded`（无引用块） | 观察 | 计为 Active、零 issue（契约键是 `文档状态`；与 backlog 卡片 `status` 生命周期字段刻意隔离） |
| 表格 `\| **文档状态** \| Superseded \|` + `\| **取代于** \| ./new.md \|` | Superseded、零 issue | Superseded 1，issues=[] ✅ |
| 表格 `\| 文档状态 \| Bogus \|` | C-1 阻断 | `取值非法（Bogus）` ✅ |
| 围栏（反引号）内示例 `文档状态: Superseded` + `取代于: ./x.md` | 保持 Active | Active、issues=[] ✅ |
| 围栏（`~~~`）示例位于控制头**之前** | 保持 Active | **被翻成 Superseded** 并触发 C-2 ❌（TD-6） |
| 围栏内**表格**示例 `\| **取代于** \| ./x.md \|` | 保持 Active | **C-3 假阳性**（`Active 却出现取代于`）❌（TD-2） |
| 无状态声明 + 表格 `\| 文档状态 \| Active / Contested / Superseded \|`（字段说明表） | 应 Active、零 issue | **C-1 假阳性** ❌（TD-2） |
| 未闭合反引号围栏吞掉控制头 | Superseded | 静默 Active ❌（TD-6） |

**T-5 / T-6（指针路径）**

| 指针 | 期望 | 实测 |
| :--- | :--- | :--- |
| `./new.md#sec` | 通过 | 通过 ✅ |
| `/etc/passwd` | 阻断 | `必须是仓库内相对路径` ✅ |
| `../../../etc/passwd` | 阻断 | 同上 ✅ |
| `./sub/../../x.md` | 阻断 | 同上 ✅ |
| `/tmp/.../outside.md`（**真实存在**的根外 .md） | 阻断 | 阻断（理由=路径，不是「不存在」）✅ |
| `../../outside.md`（**真实存在**的根外 .md） | 阻断 | 阻断 ✅ |
| `../new.md`（从 `reference/sub/` 指向根内 `reference/new.md`） | 应通过（RFC：仓库内相对路径） | **阻断** ❌（TD-1） |
| `./sub/../new.md`（归一化后仍在根内） | 应通过 | **阻断** ❌（TD-1） |
| 重复两行 `取代于`（先好后坏） | 至少报其一 | 零 issue（first-wins 静默）⚠️ |

**T-7（C-5 年龄）**

| 修订表形态 | 期望 | 实测 |
| :--- | :--- | :--- |
| 升序（2026-01-01 → 2026-11-20），now=2026-11-22 | age=2 | **age=2** ✅ |
| 降序（2026-11-20 → 2026-01-01） | age=2 | age=2 ✅ |
| 标题与表格之间夹一段说明 | age=2 | age=2 ✅ |
| 单行表：日期列「待补」、描述列含 `2026-01-01` | 应 null 或 2 | **age=325**（取到描述列）❌（TD-7） |
| 未来日期 `2026-12-31` | age 为负、不超期 | age=-39 ⚠️ |

**T-10（backlog 排除面）**

| 场景 | 期望 | 实测 |
| :--- | :--- | :--- |
| `project/backlog/BK-1.md`（BadStatus） | 跳过 | 跳过 ✅ |
| `reference/backlog/real.md`（BadStatus） | 生效 | 1 issue ✅ |
| `project/backlog/deep/BK-2.md` | 跳过 | 跳过 ✅ |
| 检出根为 `/tmp/.../backlog/t10c/docs` | 门禁不得归零 | 1 issue ✅ |

**C-4（上轮 T-7，本轮重编号后未出现在修复清单）**

| 引用形态 | 期望 | 实测 |
| :--- | :--- | :--- |
| `[旧版](./old.md)` | 警告 | 警告 ✅ |
| `[旧版][r]` + `[r]: ./old.md` | 警告 | **无警告** ❌ |
| `[旧版](./old.md "标题")` | 警告 | **无警告** ❌ |
| `[旧版](./OLD.MD)` / `./old` | 警告 | **无警告** ❌ |

### 1.4 回归面（真实树，本树复跑）

```bash
$ python3 -m pytest skills/doc-governance/tests -q
264 passed in 18.56s          # 上轮 255 → +9；提交信息称 263，实测 264（TD-9）

$ generate-llms-txt.py --root docs --output docs/llms.txt --split --check
✅ 机器地图校验通过（6 个文件，根 883 字节）                        rc=0
$ check-doc-links.py --root docs
📊 共扫描 105 个 Markdown 文件 / 未发现 404 断链                    rc=0
$ check-doc-control-sync.py --root docs
📊 共检查 57 个 Markdown 文件 / 100% 保持一致                       rc=0
$ check-doc-drift.py --root docs --repo . --fail-on-drift
📊 声明 3/56 篇（覆盖度 5.4%）｜fresh 3｜真值分 15.0 / 15           rc=0
$ audit-doc-health.py --root docs --repo .
🌟 完美！未检测到任何健康缺陷
📌 [文档状态机 · 未决冲突清单]:
   * 状态分布: Active 50｜Contested 0｜Superseded 0
   （无争议、无取代：全库 Active）
🏁 诊断结论: PASS (健康度达标，准予交付) ✅                          rc=0
```

覆盖面对账：`合规文档: 98/98`，状态机实扫 **50** 篇，差值 **48** = `docs/project/backlog/*.md` 卡片数（`find … | wc -l = 48`），即排除面已精确等于设计意图，不再有「49% 静默出界」。

### 1.5 未决冲突清单渲染（含真实非 Active 分支）

```text
📌 [文档状态机 · 未决冲突清单]:
   * 状态分布: Active 1｜Contested 1｜Superseded 1
   - [Contested] reference/c.md（325 天，⚠️ 超期）：选型未定
   - [Superseded] reference/s.md → ./new.md
🏁 诊断结论: PASS (健康度达标，准予交付) ✅   rc=0
```

（C-4/C-5 只进报告不阻断，与 RFC §4.4 一致；真实树 0 篇非 Active，该两条分支仍只在夹具中跑通。）

---

## 2. 六项结论

### 2.1 T-1 真解（端到端）— ✅ 收口

- 骨架不再携带行内 HTML 注释与 `取代于`/`争议点` 预置行；条件字段的用法整体移到围栏外的说明区（模板 `:7-12`）。按说明填槽的文档在**真门禁**上 `rc=0 / PASS / Active 51`，零状态违规——上轮「照模板产出必然过不了门禁」不成立。
- 豁免没有过头：同一份 Active 文档手工加 `取代于` 仍被 C-3 阻断（`rc=1`），且同屏不再打印「全库 Active」。
- 唯一保留意见：模板规则 7（`:44`）仍只写「仓库内相对路径」，与实现「任何 `..` 一律阻断」不一致（见 TD-1）。

### 2.2 T-2 / T-3 / T-4 — 🟡 三种规范形态收口，两类污染面仍在

- **T-2 收口**：`parse_frontmatter` 不再 YAML 命中即 `return`，引用块改用 `setdefault` 合并，YAML+引用块并存时状态被正确识别（Superseded/Contested 均实测通过）。YAML 单独写 `status:` 仍不计入（契约键是 `文档状态`，与 backlog 卡片的 `status` 生命周期字段刻意隔离），属**有意留白**而非缺陷。
- **T-3 收口但引入越界捕获**：表格形态可识别、非法取值可阻断；代价是模式 C 变成「全文任意表格行 + 白名单」——字段**说明表**（`\| 文档状态 \| Active / Contested / Superseded \|`）会被当作声明，C-1 假阳性；`\| 取代于 \| ./x.md \|` 会被当作指针，C-3 假阳性，且**围栏不设防**（TD-2）。
- **T-4 部分收口**：反引号围栏内的引用块示例不再污染（实测 Active 保持）；但 `~~~` 围栏、未闭合围栏、以及模式 C 的表格示例均不设防（TD-6）。另：窗口由 50 行放宽到 80 行，控制头在第 82 行仍静默退化为 Active（fail-open）。

### 2.3 T-5 / T-6 — ✅ 四个必测点达标，但「越界」判据过宽

- `./new.md#sec` 通过；`/etc/passwd`、`../../../etc/passwd`、`./sub/../../x.md` 全部阻断；用**真实存在**的根外 `.md` 复测，阻断理由落在「必须是仓库内相对路径」而不是「目标不存在」——T-5/T-6 的原始逃逸面确实关上了。
- 但判据是 `".." in Path(pointer_path).parts`（`:329`），把**不越界**的仓库内父级路径一并杀掉：`../new.md`、`./sub/../new.md` 均被阻断，而 RFC C-6 与模板的措辞都是「`..` **越界**」（TD-1）。后果是跨目录取代链在当前实现下**无法表达**。

### 2.4 T-7 — ✅ 升序表按最新行计算

- 2026-01-01 + 2026-11-20 两行、now=2026-11-22 ⇒ `age_days=2`（上轮为 325）；降序表同为 2；标题与表格之间夹段落不再退化为 `null`。`max(dates)` 对 ISO 日期字符串排序正确。
- 残留：行内取「第一个 `YYYY-MM-DD`」的旧逻辑未动，日期列写「待补」时仍会取到描述列日期（单行表实测 325 天假超期，TD-7）。

### 2.5 T-10 — ✅ 排除面精确化且不再环境相关

- `project/backlog/**` 跳过、`reference/backlog/**` 照常受检、`project/backlog/deep/**` 跳过、扁平文件 `project/backlog.md` 不受影响；检出根为 `/tmp/.../backlog/.../docs` 时门禁**不再归零**（实测仍报 1 issue）。
- 真实树对账：98 篇审计文档 − 50 篇状态机覆盖 = 48 = backlog 卡片数，收窄后的语义与注释一致；`f.relative_to(root_dir).parts[:2]` 不再受绝对路径分量污染。
- 残留：该豁免仍未登记进 GOVERNANCE §4.1 豁免表（上轮 T-9 第三点，TD-8）。

### 2.6 回归面 — ✅ 全绿，且状态机不再是「单测专属」

- `pytest 264 passed`；五道门禁 rc=0；真实分布 `Active 50 / Contested 0 / Superseded 0`，输出与缺陷面自洽（T-11 的互斥条件已生效）。
- 与上轮相比：测试 +9（`TestStatusRedTeamFixes`），覆盖 T-1/T-2/T-3/T-4/T-5/T-6/T-7/T-10/T-9；但 T-9 的用例是**空断言**（见 TD-5），C-4 形态、`~~~` 围栏、说明表假阳性仍无契约用例。
- 真实树仍 0 篇 `Contested`/`Superseded`，年龄/取代链/C-4 三条分支依旧只在夹具里跑通（上轮残留风险 1 未消除）。

---

## 3. 新缺陷（TD-n）

| 稳定 ID | 级别 | 归属 | 位置 | 缺陷与证据 | 处置 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TD-1** | **P2** | 本次引入（D-06） | `audit-doc-health.py:329` | `取代于` 对 `..` 一刀切：`../new.md`（根内）、`./sub/../new.md`（归一化在根内）均被阻断，与 C-6「`..` **越界**」及模板规则 7「仓库内相对路径」冲突；跨目录取代链无法表达（同目录之外无合法写法）。夹具 t6e/t6f 实测 | 改为 `target.resolve().is_relative_to(root_dir.resolve())` 判越界，保留绝对路径拦截；或把 C-6/模板措辞收窄为「禁止任何 `..`」——二者必居其一 |
| **TD-2** | **P2** | 本次引入（D-03） | `:506-519` | 模式 C 白名单扩容后变成「全文任意表格行」：① 字段说明表 `\| 文档状态 \| Active / Contested / Superseded \|` ⇒ C-1 假阳性；② `\| 取代于 \| ./x.md \|`（含**围栏内**示例）⇒ C-3 假阳性；③ 真实树证据：给 RFC-0007 加一行 `文档状态: Active` 即被它自己的字段表（`RFC-0007:46`）判 C-3；RFC-0004 加 `Contested` 时 `争议点` 取到 `RFC-0004:296` 的「分歧」 | 模式 C 同样跳过围栏；表格形态限定在「控制头块内」（如首个表格且键值同段），或仅接受两列加粗键形态 |
| **TD-3** | **P2** | 历史既有 + 宣称偏差 | `:359` | 上轮 T-7（C-4 漏报引用式 `[r]: ./old.md`、带 title、`.MD`、无扩展名）**既未修也未登记**：修复提交重编号后 T-7 变成 C-5 年龄项，该 P2 从 D-01~D-09 与提交信息中消失，而提交信息宣称「T-1~T-11 全部收口」 | 补 D-10 登记并复用 `check-doc-links.py` 的链接解析；或在 RFC 显式声明 C-4 只覆盖行内链接 |
| **TD-4** | **P2** | 历史既有（未收口） | `:307-311` | 隐式 Active 携带 `取代于` 静默通过：`if not raw: … continue` 在读 `pointer` 之前早退，无状态声明 + 指针（引用块或表格）⇒ Active、零 issue、指针不进清单（C-3 的语义空洞） | 把 `pointer` 读取移到早退之前；无状态 + 指针 ⇒ C-3 或至少 warning |
| **TD-5** | **P3** | 本次引入（D-09） | `:262-266`、`tests/test_doc_status.py:239-244` | `max_age_days` 参数从未被函数体引用（`max_age_days=1` 与 `99999` 返回完全一致），死常量只是换成了死参数；`test_t9` 只断言 `age_days>5` / `<90`，与参数无关，属空断言；RFC C-5「可配」无 CLI 落地 | 要么让阈值参与判定（并暴露 `--contested-max-age`），要么删参数、把「可配」从 RFC 删除；测试改为断言超期标志翻转 |
| **TD-6** | **P3** | 本次引入（D-04） | `:467-477`、`:496` | 围栏感知只认反引号三连且只作用于模式 B：`~~~` 围栏示例在控制头之前会把 Active 翻成 Superseded 并触发 C-2；未闭合围栏会吞掉控制头（静默 Active）；80 行窗口外的控制头仍 fail-open | 围栏正则同时识别 `~{3,}`；未闭合围栏视为解析失败并告警；窗口改为「到首个 H2 为止」 |
| **TD-7** | **P3** | 历史既有（未收口） | `:253-256` | `_DATE_IN_ROW.search(line)` 取行内首个日期，日期列写「待补」时会取到描述列日期：单行表实测 `age=325` 假超期（上轮 T-8 次生缺陷未修） | 只取修订日期列（按表头定位列序），或对「待补」显式返回 `None` 并在清单标注「不可判定」 |
| **TD-8** | **P3** | 本次引入（D-08） | `docs/GOVERNANCE.md:119-131` | `project/backlog` 豁免已收窄但**未登记**进 §4.1 豁免表（该表是 BK-0007 的机械契约面），上轮 T-9 第三点未收口 | §4.1 增一行：工具 `check_doc_status` / 豁免项 `project/backlog/**` / 理由「YAML `status` 为生命周期字段」 |
| **TD-9** | **P3** | 本次引入 | 提交信息 `4fe9801` | 取证口径偏差：称 `263 passed（新增 9 条）`，实测 264（255+9）；称「T-1~T-11 收口」但 C-4 形态项未修（TD-3）。违反「宣称与取证同宽」 | 修正后续登记口径；把未修项显式列入 D 表 |

> 边界观察（不计级，不在本次 diff 内）：`check-review-report.py docs/project/reviews/2026-11-22-doc-status-machine` 现为 `rc=1`（台账「报告文件」列写成 markdown 链接被拼成 `round-1-light.md.round-1-light.md`，且轮次列 `R1（Light）` 不是 `r1/delta-r1` 前缀）。归档索引的可机械校验性需主智能体在登记 delta 轮次时一并修正。

---

## 4. 裁决

### 4.1 阻断项计数

| 级别 | 数量 | 条目 |
| :--- | :--- | :--- |
| P0 | 0 | — |
| **P1** | **0** | —（上轮唯一 P1「T-1 模板自伤」已端到端收口） |
| P2 | 4 | TD-1（`..` 一刀切）、TD-2（表格越界捕获）、TD-3（C-4 形态未收口）、TD-4（隐式 Active 指针空洞） |
| P3 | 5 | TD-5 ~ TD-9 |

**Blockers = 0**（口径：仅 P0/P1 计入）。

### 4.2 裁决

**✅ 准予交付（Blockers = 0）。**

理由：上轮唯一阻断项 T-1 的判据是「模板与门禁由同一次提交引入却互不自洽，照模板产出必然过不了门禁」。本轮以**真门禁 + 真 CLI** 复现：骨架填槽产物 `rc=0 / PASS / Active 51`、零状态违规；同时 C-3 对 Active 携带指针仍然阻断，豁免没有反向放松。T-2/T-3/T-4/T-5/T-6/T-7/T-10 的规范形态全部可复现，T-10 的排除面已与设计意图精确对齐（98−48=50）。回归面 264 passed、五道门禁 rc=0。

新增缺陷集中在**过严/过宽捕获**而非「放行错误文档」：TD-1、TD-2 都是 fail-closed 的假阳性（误杀合法声明），TD-4 是历史既有的语义空洞，均无真实文档受影响（真实树 0 篇非 Active、0 篇显式指针），故不构成 P1；但 TD-1 与 TD-2 必须在下一次迭代优先收口——它们会在「首篇真实 Superseded 文档」和「首份字段说明表」落地时立刻显形。

### 4.3 放行后的最小跟进集（按优先级）

1. **TD-1 + TD-2**：`取代于` 改判「解析后是否越界」；模式 C 加围栏跳过 + 限定控制头块。两条都是 1~2 行级改动，但直接决定跨目录取代链与治理文档能否落地。
2. **TD-3 + TD-4**：把 C-4 形态项重新登记为 D-10；把 `pointer` 读取提到隐式 Active 早退之前。
3. **TD-5 ~ TD-9**：随下一批次（可并入 backlog）处理，不阻断。

### 4.4 残留风险（3 条）

1. **真实分支仍零覆盖**：全库 `Contested 0 / Superseded 0`，年龄、取代链、C-4 告警三条链路只在夹具中跑通；首篇非 Active 文档落地时，TD-1/TD-2/TD-4 会同时暴露。
2. **共享解析器的放大面**：T-2/T-3/T-4 的根因都在 `parse_frontmatter`，它同时被 `check-doc-control-sync.py` 等门禁复用；本轮把白名单与窗口都放宽，任何「用表格/引用块描述控制头字段」的文档都可能被误读（RFC-0007/RFC-0004 已具备该形态）。
3. **报告面口径**：「全库 Active」在 48 篇 backlog 卡片被排除的前提下仍写「全库」，且 80 行窗口外的控制头静默退化——两者都不会报错，读者无法从输出判断覆盖边界。
