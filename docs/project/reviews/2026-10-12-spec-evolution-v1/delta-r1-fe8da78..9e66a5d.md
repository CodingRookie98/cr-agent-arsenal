# Delta 红队审查报告（R1）· `fe8da78...9e66a5d`

> **审查员角色**：Red-Team Security Auditor / Chaos Engineer / First-Principles Architect
> **审查模式**：`DELTA_REVIEW` —— 只审本轮 Delta 修复批次（`fe8da78...9e66a5d`），不把历史既有、未被本次 diff 触碰的条文回炉定级
> **审查基线**：`fe8da78`（上一轮 R1/R2 基线）→ `9e66a5d`（本次复评基线）
> **约束**：只读仓库（唯一写入 = 本报告）；零网络；零 LLM 自证（每条结论附完整命令与原始输出）
> **结论**：**🔴 未取得 Zero Blockers —— 阻断项 P0 = 0，P1 = 1（DR1-1）**
> **迭代计数**：Delta R1 第 1 轮 / 上限 3 轮

---

## §0 取证环境与方法

### 0.1 变更面确认

```
$ cd /home/hui/workspace/projects/cr-agent-arsenal
$ git status --porcelain
（空）
$ git log --oneline fe8da78..9e66a5d
9e66a5d docs(plan): Active Checkpoint 推进至 Delta 待复评 + 修订历史 V1.3.0
97aefeb docs(spec-evolution): RFC-0004 补登 [REPO:*] 锚点契约 + 七项非阻断项落为 Backlog 卡片
b2ba764 docs(plan): Active Checkpoint 推进至 P3.5 Delta 待复评 + 修订历史 V1.2.0
d8aa611 fix(spec-evolution): P3.5 首轮阻断修复（GI-6 只读不变式 / 退出码口径 / --no-gates 报告三态）
ac13058 docs(review): spec-evolution-v1 P3.5 首轮 R1/R2 审查归档
$ git diff --stat fe8da78...9e66a5d | tail -2
 skills/spec-evolution/tests/test_judge_contract.py |  17 ++-
 21 files changed, 653 insertions(+), 60 deletions(-)
$ git log --oneline -S'errors="replace"' fe8da78..9e66a5d -- skills/spec-evolution/scripts/collect-facts.py
d8aa611 fix(spec-evolution): P3.5 首轮阻断修复（GI-6 只读不变式 / 退出码口径 / --no-gates 报告三态）
$ git log --oneline --diff-filter=A -- 'docs/project/backlog/active/BK-0033*'
97aefeb docs(spec-evolution): RFC-0004 补登 [REPO:*] 锚点契约 + 七项非阻断项落为 Backlog 卡片
```

三点式 diff 的 merge-base 已独立确认（防止上游逆向污染）：

```
$ git merge-base fe8da78 9e66a5d
fe8da78471c727e6bdaef2f8ed64bbe978ac94b5
```

即 `fe8da78` 是 `9e66a5d` 的真祖先，三点式等价于两点式，diff 面可信。

### 0.2 实验副本（全部在 `/tmp`，仓库零写入）

| 副本 | 来源 | 用途 |
| :--- | :--- | :--- |
| `/tmp/oldrepo` | `git archive fe8da78` | 旧基线对照（该副本已失效重建，最终结论均以全新 `git archive` 副本为准） |
| `/tmp/r1delta`、`/tmp/gate-a`、`/tmp/gate-b`、`/tmp/e2e`、`/tmp/ctrl1`、`/tmp/pin1`、`/tmp/pin2`、`/tmp/bisect3`、`/tmp/bisect4`、`/tmp/prefix-fix`、`/tmp/final-e2e` | `git archive 9e66a5d` | 新基线端到端/门禁/夹具实验 |
| `/tmp/mut-r12`、`/tmp/mut-r13`、`/tmp/mut-envnull`、`/tmp/mut-readme` | `git archive 9e66a5d` + 定向变异 | 反向复现（Mutation Testing） |
| `/tmp/real-a`、`/tmp/real-b`、`/tmp/real-c`、`/tmp/real-d` | `git archive 9e66a5d` | 真实门禁树字节码残留实验 |
| `/tmp/probe/sitecustomize.py` | 自建 | `sys.addaudithook` 审计钩子（`PYTHONPATH=/tmp/probe`） |

**仓库内临时文件登记**：无。本会话在仓库内 **未创建/修改/删除任何文件**（除本报告）；收尾核对见 §5.4。

---

## §1 第一性原理与本质溯源

### 1.1 GI-6 的不变式对象是「文件系统副作用」，而仓库的 VCS 视图对它天然失明

GI-6 断言的是「采集器与门禁除显式 `--out` 外不得在仓库内创建/修改/删除任何文件」。这是**文件系统层**的不变式，而开发者/评审者习惯使用的检查手段 `git status` 是**版本控制视图**：本仓库 `.gitignore:19` 忽略 `__pycache__/`，因此**字节码残留对 `git status` 完全不可见**。

这解释了本轮最危险的认知偏差：R1-1 声称已修，而所有「工作区干净」的核对（包括本报告 §0.1 的 `git status --porcelain` 为空）都**结构上无法**发现残留。唯一有效检测器只有**独立于 VCS 的文件系统快照差分**——正是 `test_gate_invariants.py` 里 `snapshot()` 的形态（`conftest.py:94-97` 已刻意不过滤 `__pycache__`）。因此：**GI-6 的取证必须用快照，而不是 `git status`**；本轮全部实验据此设计。

### 1.2 字节码写入有三条本质不同的机制，修复只覆盖了其中两条

| # | 机制 | 是否受 `sys.dont_write_bytecode`（即 `-B` / `PYTHONDONTWRITEBYTECODE=1`）约束 | 本轮证据 |
| :--- | :--- | :--- | :--- |
| (a) | 常规 `import` 机制 | **受约束** | 实验 A/B（§3.1）|
| (b) | `importlib.util.spec_from_file_location` + `module_from_spec` + `exec_module` | **仍受约束**（走 `SourceFileLoader._cache_bytecode` → 检查 `sys.dont_write_bytecode`） | 实验 A（§3.1）：`python3 -B audit-doc-health.py` 零残留 |
| (c) | **显式 `py_compile.compile()`** | **不受约束**（`py_compile` 走显式写字节码语义，`-B` 与 `PYTHONDONTWRITEBYTECODE` 均被忽略） | 变异/端到端实验（§3.2）：修复后采集器仍落字节码 |

修复方把 (b) 误判为「不受 `-B` 约束」，据此把 `PYTHONDONTWRITEBYTECODE=1` 定为「唯一覆盖整棵进程树的机制」；而实测中真正不受抑制的是 (c)，且 (c) 恰好存在于 GI-6 门禁本身所跑的那条链上。

### 1.3 夹具是「握手协议」，生产漂移只能由端到端真实运行暴露

夹具仓库由 `conftest.py:build_repo()` 合成：它只包含夹具自己写进去的文件（含两个桩门禁脚本）。因此**夹具内可达的写字节码路径 = 夹具作者的建模范围**。当生产侧存在夹具未建模的写入者（(c) `py_compile`）时，必然出现「夹具全绿 + 生产失败」——这是本轮 R1-1 未根除的**结构性原因**，不是运气问题。

### 1.4 退出码语义的 SSOT 是「可执行实现」，文档必须向实现收敛

R1-2 的裁决方向（以实现为准，把「`0 = 无 finding`」收敛为「`0 = 无 BLOCKER/HIGH（可含 MID advisory）」）符合单一真相源原则：`judge.py:367-371` 是唯一可执行语义，23 条契约测试把它钉死。反向收敛（改实现迎合文档）会破坏 RFC §3.2 的严重度分层。**该方向已独立验证为真（§3.4）。**

### 1.5 「未取证」与「取证为空」是两种状态，三态是最小完备集

`gates is None`（未采集）与 `gates == {}`（已采集、零失败）在语义上正交，不可折叠。R1-3 的三态实现方向正确；残留缺口仅在于**判据用 `is None` 而非「非空字典」**——`[]` / `{}` 会回落到「已采集、无失败」的肯定陈述（DR1-5）。

---

## §2 运行时与沙盒安全推演

**未激活（非客户端/SSR 改动）。**

本 Delta 的全部变更面为：Python 采集器/判定器脚本、pytest 夹具与断言、Markdown 契约与计划/卡片文档。无浏览器渲染、无 SSR、无客户端注入面，故客户端沙盒推演（CSP/同源/序列化边界）不适用。

仍适用的运行时推演（服务端/CLI 语义）：

1. **子进程环境继承**：`subprocess_env()`（`collect-facts.py:253-260`）返回 `{**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}`，不裁剪父环境，因此 `PYTHONPYCACHEPREFIX`、`LC_ALL`、`PYTHONUTF8` 等父变量照旧透传——无新增环境投毒面，但也意味着**新增变量是唯一可用的加挂点**（见 DR1-1 最小修法）。
2. **进程树覆盖面**：环境变量随 `fork/exec` 继承，覆盖整棵进程树；`-B` 作为 argv 开关只作用于直接子进程——这一点修复方的判断（`conftest.py:73-75`）**方向正确**，只是它要防的向量在本仓库并不存在（§3.1 实验 C/D）。
3. **`cwd` 与写入落点**：门禁子进程 `cwd=repo`（`collect-facts.py:267`），因此任何相对路径写入都落在被测仓库内；这是 GI-6 的威胁模型基础，也是 DR1-1 反例的落点。
4. **超时与失败耦合**：`GATE_TIMEOUT` 超时记为 124、`OSError` 记为 125（`collect-facts.py:270-274`），两者都会成为 C-09 BLOCKER——fail-closed 方向正确，不构成新缺陷。
5. **沙盒逃逸面**：本 Delta 未引入任何新的网络、文件写入目标或权限提升路径；`git rev-parse` 调用（`collect-facts.py:285-289`）只读。

---

## §3 红队攻击路径推演

### 3.1 攻击路径 A（**攻破**）：GI-6 在生产态仍被违反，且修复自称的机制无一处能拦住它

**A-1 先纠正根因叙述：真实门禁树里没有级联子进程**

```
$ grep -rn 'subprocess\|Popen\|os.system' skills/doc-governance/scripts/
（零命中）
$ grep -n 'importlib\|spec_from_file_location' skills/doc-governance/scripts/audit-doc-health.py
49:    spec = importlib.util.spec_from_file_location(module_name, path)
...
137:    _llms_mod.generate_llms_txt(...)   # 同进程调用，非子进程
```

**A-2 三条真实门禁命令的残留矩阵**（全新 `git archive 9e66a5d` 副本）

| 副本 | 命令 | exit | 仓库内字节码条目 |
| :--- | :--- | :--- | :--- |
| `/tmp/real-c` | `python3 skills/doc-governance/scripts/audit-doc-health.py`（= fe8da78 原状：无 `-B`、无 env） | 0 | **5**（1 目录 + 4 `.pyc`） |
| `/tmp/real-a` | `python3 -B skills/doc-governance/scripts/audit-doc-health.py` | 0 | **0** |
| `/tmp/real-b` | `PYTHONDONTWRITEBYTECODE=1 python3 -B …audit-doc-health.py` | 0 | **0** |
| `/tmp/real-d` | `python3 skills/doc-governance/scripts/check-doc-links.py --root docs` | 0 | **0** |

`/tmp/real-c` 原始输出：

```
$ find . -name '__pycache__' -o -name '*.pyc' | sort
./skills/doc-governance/scripts/__pycache__
./skills/doc-governance/scripts/__pycache__/check-doc-control-sync.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/check-doc-links.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/generate-llms-txt.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/trim-revision.cpython-312.pyc
```

→ **结论 1**：`-B` 完全压制 `audit-doc-health.py` 的 importlib 动态加载路径。所以本次修改的两处 `-B`（`collect-facts.py:59-60`、`collect-facts.py:62`）是本轮**真正承重**的修复。
→ **结论 2**：`collect-facts.py:256-257`、`test_gate_invariants.py:206-207`、`docs/explanation/architecture/spec-evolution-design.md:87`、`conftest.py:71-72` 四处「`importlib` 动态加载不受 `-B` 约束、会写出 `__pycache__`／真实仓库靠 subprocess + importlib 留下字节码」的叙述，**与实测相反**（DR1-2）。

**A-3 GI-6 门禁本身（`pytest` 那条）仍会写仓库**

```
$ cd /tmp/gate-a   # git archive 9e66a5d | tar -x
$ python3 -B -m pytest skills/ -q -p no:cacheprovider     # 仅 -B，无 env
376 passed in ...
$ find . -name '__pycache__' -o -name '*.pyc' | wc -l
6
$ find . -name '*.pyc' | sort
./skills/doc-governance/scripts/__pycache__/check-doc-control-sync.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/check-doc-links.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/generate-llms-txt.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc
./skills/doc-governance/scripts/__pycache__/trim-revision.cpython-312.pyc
```

```
$ cd /tmp/gate-b   # 同样的全新副本，但带修复方声称的「唯一覆盖整棵进程树」的机制
$ PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest skills/ -q -p no:cacheprovider
376 passed in ...
$ find . -name '__pycache__' -o -name '*.pyc' | sort
./skills/doc-governance/scripts/__pycache__
./skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc
```

→ **`PYTHONDONTWRITEBYTECODE=1` 只能把残留从 6 条压到 2 条，压不到 0。** 修复自称的「唯一覆盖整棵进程树的机制」被直接证伪。

**A-4 端到端复现：修复后的采集器在真实仓库上破坏自己声明的不变式**

```
$ rm -rf /tmp/final-e2e && mkdir -p /tmp/final-e2e
$ git archive 9e66a5d | tar -x -C /tmp/final-e2e
$ cd /tmp/final-e2e
### 采集前产物计数: 0
$ python3 skills/spec-evolution/scripts/collect-facts.py --repo-root . --out /tmp/final-facts.json
✅ 事实已导出: /tmp/final-facts.json（技能 8 个，门禁 已采集）
采集器 exit=0
$ find . -name '__pycache__' -o -name '*.pyc' | sort
./skills/doc-governance/scripts/__pycache__
./skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc
count=2
```

**GI-6 明文的「不得创建目录」也被违反**（新增的 `__pycache__/` 正是目录）。而同一棵树上 `python3 -m pytest skills/spec-evolution/tests` 的 52 条测试（含两条 GI-6 断言 + 新增的结构性断言）**全绿**——夹具与生产之间的可达性缺口被完整复现。

**A-5 元凶定位（三重独立取证）**

```
$ grep -rn "py_compile\|compileall\|dont_write_bytecode\|write_bytecode" --include='*.py' --include='*.sh' skills/ tools/
skills/doc-governance/tests/test_doc_index_convention.py:420:
             "import py_compile, sys; py_compile.compile(sys.argv[1], doraise=True)",
```

调用点原文（`skills/doc-governance/tests/test_doc_index_convention.py:415-421`）：

```python
    def test_script_compiles_under_strict_syntax_warnings(self):
        """DR1-1：脚本须在 -W error::SyntaxWarning 下零告警编译（未来 Python 的硬错误前哨）"""
        res = subprocess.run(
            [sys.executable, "-W", "error::SyntaxWarning", "-c",
             "import py_compile, sys; py_compile.compile(sys.argv[1], doraise=True)",
             str(SCRIPTS_DIR / "manage-doc-index.py")],
            capture_output=True, text=True,
        )
```

- 取证 1（单独可复现）：
  ```
  $ cd /tmp/pin1 && PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest \
      skills/doc-governance/tests/test_doc_index_convention.py -q -p no:cacheprovider
  31 passed in 2.39s
  $ find . -name '*.pyc'
  ./skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc
  ```
- 取证 2（对照：换掉该文件即消失）：
  ```
  $ cd /tmp/ctrl1 && PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest \
      skills/doc-governance/tests/test_doc_governance_scripts.py -q -p no:cacheprovider
  74 passed in 8.16s
  产物: （空）  count=0
  ```
- 取证 3（重定向验证：`PYTHONPYCACHEPREFIX` 是唯一能覆盖 `py_compile` 的开关）
  ```
  $ PYTHONPYCACHEPREFIX=/tmp/pc PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
      "import py_compile; py_compile.compile('/tmp/p3/x.py', doraise=True)"
  $ find /tmp/p3 -name '__pycache__'      → （空）
  $ find /tmp/pc -name '*.pyc'
  /tmp/pc/tmp/p3/x.cpython-312.pyc        ← 被重定向出仓库
  ```
  ```
  $ cd /tmp/prefix-fix && PYTHONPYCACHEPREFIX=/tmp/pycache-redirect \
      PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest skills/ -q -p no:cacheprovider
  376 passed in 75.70s
  仓库内新增产物: count=0
  被重定向的目标: /tmp/pycache-redirect/tmp/prefix-fix/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
  redirected=1
  ```

→ 修复方选择的变量（`PYTHONDONTWRITEBYTECODE`）漏掉 `py_compile`；正确的「覆盖整棵进程树」变量是 `PYTHONPYCACHEPREFIX`（把整棵树的字节码写到仓库外），且已实测能一次把残留降到 **0**。

**A-6 自述变异证据不成立（Zero-Trust 复核）**

修复方自述：「移除 `env=subprocess_env()` 后两条 GI-6 测试同时失败」。独立复现（`/tmp/mut-envnull`，把两处 `env=subprocess_env()` 改为 `env=None`，保留两条 `-B`）：

```
$ python3 - <<'PY'
import pathlib
p = pathlib.Path("skills/spec-evolution/scripts/collect-facts.py")
s = p.read_text(encoding="utf-8"); n = s.count("env=subprocess_env()"); assert n == 2, n
p.write_text(s.replace("env=subprocess_env()", "env=None"), encoding="utf-8")
print(f"replaced {n} 处 env=subprocess_env() -> env=None（docstring 保留原样）")
PY
replaced 2 处 env=subprocess_env() -> env=None（docstring 保留原样）
$ PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest skills/spec-evolution/tests -q -p no:cacheprovider
52 passed in 5.59s
$ … -k "structural"
1 passed, 12 deselected in 0.03s
```

→ **移除 env 注入后两条 GI-6 测试全绿**，自述的变异结论不可复现。真正能转红的只有「同时移除 env 与两条 `-B`」的组合变异（`/tmp/mut-r13` 之外的 β 实验：8 failed + 2 failed 量级）。这既是自述证据的失真，也是本修复承重机制被误判的直接后果。

**A-7 新增「结构性断言」可被合法重构绕过**

`test_gate_invariants.py:202-218` 的两条断言在 `env=None` 变异下**全部通过**（见 A-6）。原因是：

- `assert "PYTHONDONTWRITEBYTECODE" in src` —— 被测源码的 **docstring**（`collect-facts.py:254`）里就写着 `PYTHONDONTWRITEBYTECODE=1`，因此该断言可被**注释满足**；
- `assert "env" in {k.arg for k in call.keywords}` —— `env=None` 同样含 `env` 关键字。

即：新断言钉住的是「有没有写 `env=` 这个字」，不是「抑制是否真的生效」。

### 3.2 攻击路径 B（**攻破**，文档面）：错误根因叙述会诱导后续维护者删掉真正承重的 `-B`

四处叙述（见 DR1-2）统一宣称「`-B` 管不住 importlib，唯一生效的是环境变量」。若后续维护者据此在新增门禁或重构时省略 `-B`（认为「反正有 env 兜底」），本仓库当前无碍（env 确实覆盖 (a)(b)），但一旦引入 (c) 类显式编译或外部脚本调用，便无任何纵深——而文档已提前宣布「结构性免疫」。**这是把未验证的机制写成了不变式，属取证范围外向结论外推。**

### 3.3 攻击路径 C（**攻破**，语义面）：`gates: []` 回落为肯定陈述（fail-open 残留）

```
$ cd /tmp/e2e
$ python3 skills/spec-evolution/scripts/judge.py --repo-root . --facts /tmp/facts-emptygates.json --report /tmp/rep-empty.md
✅ 演进报告已写出: /tmp/rep-empty.md
📊 findings=11 blocker/high=3
judge exit=1
$ grep -n -A3 "## BLOCKER" /tmp/rep-empty.md
7:## BLOCKER
8:
9:（已采集门禁事实，无失败）
```

`facts["gates"] = []`（C-09 未执行）时，报告输出**肯定陈述**「（已采集门禁事实，无失败）」——正是 R1-3 要根除的「未取证而宣称取证」。对照：`None` 已正确（见 §3.4）。可达性说明：`collect_gates()`（`collect-facts.py:263-281`）对 `GATES` 四个键恒定填值，本仓库内**自然不可达**；但 `judge.py` 以 `--facts` 接受外部 JSON，且未见对 `gates` 类型的强校验，故仍是一个真实的 fail-open 缺口（P3）。

### 3.4 攻击路径 D（**已封堵**，验证通过）：`--no-gates` 三态与 R1-2/R1-3 的反向复现

**三态端到端（真实仓库，修复后）**

| 状态 | 输入 | `## BLOCKER` 段原文 |
| :--- | :--- | :--- |
| 未采集 | `--no-gates` 采集的 facts（`/tmp/facts-nogates.json`，`gates = None`） | 「（未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论）」 |
| 已采集无失败 | 正常 facts，门禁全 0 | 「（已采集门禁事实，无失败）」 |
| 有失败 | 门禁 `exit_code != 0` | 逐条列出 C-09 BLOCKER |

```
$ cd /tmp/e2e && python3 skills/spec-evolution/scripts/collect-facts.py --repo-root . --no-gates --out /tmp/facts-nogates.json
$ python3 -c "import json;print(repr(json.load(open('/tmp/facts-nogates.json'))['gates']))"
None
$ python3 skills/spec-evolution/scripts/judge.py --repo-root . --facts /tmp/facts-nogates.json --report /tmp/rep-nogates.md
📊 findings=11 blocker/high=3
$ grep -n -A3 "## BLOCKER" /tmp/rep-nogates.md
7:## BLOCKER
8:
9:（未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论）
```

**变异 R1-3（回退三态）→ 断言转红**

```
$ cd /tmp/mut-r13   # 三态分支判据 elif raw_gates is None:  →  elif False:
1 failed, 51 passed in 5.71s
FAILED skills/spec-evolution/tests/test_judge_contract.py::test_report_head_contains_verdict_and_metadata
E  assert '未采集门禁事实' in '# spec-evolution 演进报告 …（已采集门...'
skills/spec-evolution/tests/test_judge_contract.py:250: AssertionError
```

**变异 R1-2（把 MID 升格为阻断，即回退为「0 = 无 finding」语义）→ 8 条测试转红**

```
$ cd /tmp/mut-r12   # blocking = [f for f in findings if f["severity"] in ("BLOCKER","HIGH")]
                    #   →  blocking = list(findings)
mutation anchor replaced
8 failed, 44 passed in 9.21s
FAILED test_gate_invariants.py::test_gi1_no_unreplaced_placeholders_in_report
FAILED test_gate_invariants.py::test_gi1_report_and_json_are_byte_identical_across_runs
FAILED test_judge_contract.py::test_c02_missing_design_doc_is_mid
FAILED test_judge_contract.py::test_c03_missing_surface_is_mid
FAILED test_judge_contract.py::test_c04_description_over_soft_limit_is_mid
FAILED test_judge_contract.py::test_c06_oversized_file_is_mid
FAILED test_judge_contract.py::test_c10_root_prompt_growth_is_mid
FAILED test_judge_contract.py::test_report_head_contains_verdict_and_metadata
E  AssertionError: assert 1 == 0
E   +  where 1 = CompletedProcess(... '📊 findings=1 blocker/high=1\n  ⛔ F-01 MID C-04 demo [SKILL:demo/SKILL.md]\n').returncode
skills/spec-evolution/tests/test_judge_contract.py:242
```

→ R1-2 的收敛方向被 8 条测试真实钉住；「MID 为 advisory、退出码 0」不是没有守卫的口头约定。

### 3.5 已尝试且未攻破的项

| 攻击 | 手法 | 结果 |
| :--- | :--- | :--- |
| `[REPO:*]` 绝对路径逃逸 | `[REPO:../../etc/passwd]`（在 `/tmp/r1delta` 内解析为真实存在的 `/etc/passwd`） | **被拒**：`validate_anchor` 返回「越出仓库」类否定 |
| `[REPO:*]` 符号链接逃逸 | 在仓库内建 `escape_link -> /tmp/outside.md` 后 `[REPO:escape_link]` | **被拒**（resolve 后落在仓库外） |
| 目录锚点带行号 | `[REPO:docs:0]`、`[SKILL:spec-evolution:12]`（目录 + `:line`） | **被拒**，证实「`:line` 只对文件有意义」成立 |
| `../` 正常穿越（仍落在仓库内） | `[REPO:docs/../README.md]` | **通过**（符合契约：允许裸路径为文件或目录，containment 以 resolve 后为准） |
| `[SKILL:*]` 越界 | `[SKILL:spec-evolution/../../../README.md]` | **被拒** |
| `--no-gates` 三态语义 | 见 §3.4 | **未攻破**（三态各自正确，`None` 不再误报） |
| 判定确定性 / 幂等 | 同 facts 重跑 `judge.py` 产物比对 | **未攻破**：`test_gi1_report_and_json_are_byte_identical_across_runs` 全绿，且在 R1-2 变异下会转红（证明其非恒真） |
| 全仓判定数字（与计划声称对齐） | `collect-facts.py`（全仓）+ `judge.py` | **未攻破**：`📊 findings=11 blocker/high=3`，与计划 `2026-10-12-spec-evolution.md:34` 声称的「11 findings / HIGH+BLOCKER 3 条」一致 |
| `spec-evolution` 自证零 finding | `--skills spec-evolution` | **未攻破**：`📊 findings=0 blocker/high=0`、`判定结论: **CLEAN**`、exit 0 |
| 审计钩子定位写入者 | `sys.addaudithook` 捕获 `open` 事件 | **工具未攻破（能力边界）**：钩子只捕获到读事件（flags=524288），未捕获到 `py_compile` 的写事件（`py_compile` 走 `_write_atomic` + `os.replace`，且该子进程为 `python3 -c` 且未继承 `PYTHONPATH`）——`import` 钩子在本场景不可靠，元凶由 A-5 的三重取证锁定 |

锚点边界的**直调原始输出**（`/tmp/anchor` 全新副本；先 `ln -sfn /etc/passwd escape_link`，再直调 `judge.py:validate_anchor`）：

```
[REPO:../../etc/passwd]                              -> 仓库锚点路径不存在或越出仓库: ../../etc/passwd
[REPO:escape_link]                                   -> 仓库锚点路径不存在或越出仓库: escape_link
[REPO:docs:0]                                        -> 锚点行号只能指向文件，但目标是目录: docs:0
[REPO:README.md:0]                                   -> 锚点行号越界: README.md:0（共 141 行，行号从 1 起）
[REPO:docs/../README.md]                             -> OK(可行)
[REPO:.]                                             -> OK(可行)
[SKILL:spec-evolution/../../../README.md]            -> 技能锚点不存在或越出仓库: skills/spec-evolution/../../../README.md
[SKILL:spec-evolution/SKILL.md:12]                   -> OK(可行)
[SKILL:spec-evolution:12]                            -> 锚点格式非法: [SKILL:spec-evolution:12]
```

→ containment（resolve 后必须落在仓库内）、符号链接不跟随逃逸、`:line` 只对文件有意义、目录锚点禁行号、`[SKILL:*]` 越界拒绝——**五项全部成立**；`[REPO:docs/../README.md]` 与 `[REPO:.]` 的放行也与契约「裸路径允许指向文件或目录、以 resolve 后 containment 为准」一致。

### 3.6 次生缺陷面（本轮新增代码是否引入新问题）

1. **新耦合**：`subprocess_env()` 同时被门禁与 `git rev-parse` 复用（`collect-facts.py:267`、`:287`）——语义上无害（`git` 不受该变量影响），但把「门禁只读保障」与「git 元数据读取」绑在同一个环境工厂上，属轻微耦合扩张（P3 级观察，不单独立项）。
2. **新恒真断言**：见 A-7（`env=None` + docstring 双重可满足）——**成立**，计入 DR1-1 的证据集。
3. **新 fail-open 路径**：`gates: []` 分支（DR1-5）。
4. **未申报的行为变更**：`collect-facts.py:227` 把 README 注册面判据从 `skills/{name}` 收紧为 `skills/{name}/SKILL.md`（带行内注释说明动机），但**未出现在 D-10~D-16 修复清单中**。实测影响为零：
   ```
   # 把判据回退为旧形式后重跑，与修复版逐行比对 findings
   $ diff <(grep '^| F-' /tmp/rep-new.md) <(grep '^| F-' /tmp/rep-readmeold.md)
   （无差异；两者均 📊 findings=11 blocker/high=3）
   ```
   → 记为 DR1-6（P3，登记缺失而非行为缺陷）。
5. **重排/顺手改**：本次 diff 未见无关重排；`readme` 判据变更是唯一未登记的语义改动。

---

## §4 潜在缺陷清单

| ID | 位置（文件:行） | 严重度 | 是否由当前 Diff 引入 | 一句话 |
| :--- | :--- | :--- | :--- | :--- |
| **DR1-1** | `skills/spec-evolution/scripts/collect-facts.py:253-260`、`skills/spec-evolution/tests/test_gate_invariants.py:202-218`（泄漏源：`skills/doc-governance/tests/test_doc_index_convention.py:420`） | **P1** | **是**（本次 Diff 声称根除 R1-1 并新增结构性断言，实际未闭合） | GI-6 在生产态仍被违反：修复后的采集器端到端新增 `__pycache__/` 目录 + `manage-doc-index.cpython-312.pyc`；`PYTHONDONTWRITEBYTECODE` 拦不住 `py_compile`；新结构断言可被 `env=None` + docstring 满足；自述变异不可复现 |
| **DR1-2** | `skills/spec-evolution/scripts/collect-facts.py:256-257`、`skills/spec-evolution/tests/test_gate_invariants.py:206-207`、`skills/spec-evolution/tests/conftest.py:71-72`、`docs/explanation/architecture/spec-evolution-design.md:87` | **P2** | **是** | 四处把根因写成「`importlib` 动态加载不受 `-B` 约束／真实门禁靠 subprocess + importlib 留下字节码」，与实测相反（`-B` 完全压制该路径；真实门禁树零 `subprocess`） |
| **DR1-3** | `skills/spec-evolution/SKILL.md:81`（被引文件：`skills/spec-evolution/references/checks-spec.md`，共 53 行） | **P2** | **是**（R1-2 修复新增该行） | SKILL.md 宣称「退出码权威定义在 `scripts/judge.py` 与 `references/checks-spec.md`；本表与之一致」，但该文件**没有任何退出码章节**（全部命中仅 C-09 的 `exit_code != 0` 与一句无关表述）→ 权威断链，读者无法据此复核 |
| **DR1-4** | `docs/project/backlog/active/BK-0033-门禁子进程非-utf-8-输出导致裸-traceback.md` | **P3** | **是**（卡片由本次 Diff 新增） | 卡片 `status: active` 且「实施去向」写 `*(未开工)*`、DoD 未勾选，但其第一条验收准则（两处 `subprocess.run` 加 `encoding=utf-8/errors=replace`）已由同一 Delta 的 `d8aa611` 落地（`collect-facts.py:268`、`:288`）→ 卡片状态与实现不同步（第二条 print 硬化确实未做，故卡片本身仍有效，仅状态失真） |
| **DR1-5** | `skills/spec-evolution/scripts/judge.py:246-247`、`:256-260` | **P3** | **是**（三态由本次 Diff 引入） | 三态判据用 `raw_gates is None`，`gates: []`／`{}` 等 falsy-but-not-None 会回落为肯定陈述「（已采集门禁事实，无失败）」（实测），即 R1-3 想根除的 fail-open 仍有残留分支；本仓库内自然不可达（`collect_gates` 恒定填 4 键），但 `--facts` 接受外部输入 |
| **DR1-6** | `skills/spec-evolution/scripts/collect-facts.py:227` | **P3** | **是** | README 注册面判据收紧为 `skills/{name}/SKILL.md`，未登记在 D-10~D-16 修复清单、无对应测试；实测对本仓库 findings 零影响（11/3 不变） |

### DR1-1（P1）：GI-6 未根除 —— 完整证据链与最小修法

**位置**：`skills/spec-evolution/scripts/collect-facts.py:253-260`（被宣称的机制）、`skills/spec-evolution/tests/test_gate_invariants.py:202-218`（守卫）、`skills/doc-governance/tests/test_doc_index_convention.py:415-421`（真实泄漏源，本次未改）

**复现命令与原始输出**（全新副本，逐字）：

```
$ rm -rf /tmp/final-e2e && mkdir -p /tmp/final-e2e
$ git archive 9e66a5d | tar -x -C /tmp/final-e2e && cd /tmp/final-e2e
$ find . -name '__pycache__' -o -name '*.pyc' | wc -l
0
$ python3 skills/spec-evolution/scripts/collect-facts.py --repo-root . --out /tmp/final-facts.json
✅ 事实已导出: /tmp/final-facts.json（技能 8 个，门禁 已采集）
$ echo $?
0
$ find . -name '__pycache__' -o -name '*.pyc' | sort
./skills/doc-governance/scripts/__pycache__
./skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc
```

```
$ cd /tmp/mut-envnull   # env=subprocess_env() → env=None（两条 -B 保留）
$ PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest skills/spec-evolution/tests -q -p no:cacheprovider
52 passed in 5.59s          ← 含两条 GI-6 测试与新增结构断言，全绿
```

**判定**：R1-1 **未根除**。本轮修复真实闭合的是「两条门禁命令缺 `-B`」这一个向量（`collect-facts.py:59-60`、`:62`，由实验 A/C/D 独立证实），但 GI-6 在生产态仍被同一门禁链上的 `py_compile.compile()` 破坏；且修复方用以宣告「结构性免疫」的两项机制（env 注入、AST 断言）在实测中既拦不住该向量，也可被合法重构绕过。

**最小修法（三步，均已独立验证可行）**：

1. **改夹具/测试外的真实写入源**（根治）：把 `skills/doc-governance/tests/test_doc_index_convention.py:418-421` 的 `py_compile.compile(sys.argv[1], doraise=True)` 改为不落盘的语法检查，例如 `compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")`（保留 `-W error::SyntaxWarning` 的前哨作用），或显式指定 `cfile` 到临时目录。
2. **采集器侧加装真正覆盖整棵进程树的开关**（纵深防御，建议一并做）：在 `subprocess_env()`（`collect-facts.py:253-260`）中追加 `PYTHONPYCACHEPREFIX` 指向 `tempfile.mkdtemp()`（仓库外），实测可把完整门禁运行的仓库内残留降到 **0**：

   ```
   $ cd /tmp/prefix-fix && PYTHONPYCACHEPREFIX=/tmp/pycache-redirect \
       PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest skills/ -q -p no:cacheprovider
   376 passed in 75.70s
   仓库内新增产物: count=0
   被重定向的目标: /tmp/pycache-redirect/tmp/prefix-fix/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
   ```

   注意该变量按 `sys.pycache_prefix` 语义**保留源文件绝对路径结构**，因此只是把写入搬出仓库，不改变仓库内容。
3. **让守卫真正生效**：`test_gi6_bytecode_suppression_is_structural`（`test_gate_invariants.py:202-218`）应断言 `env` 的取值表达式**不是** `None`（例如断言 `env=subprocess_env()` 或断言源码中存在 `PYTHONDONTWRITEBYTECODE` 的**赋值**而非任意出现），并增设一条「夹具内无法覆盖、但生产可复现」的回归测试：在合成仓库里放一个 `py_compile.compile()` 型写入者，断言采集器仍不产生残留（该测试在修复前应转红）。

**同时纠正文档叙述**：见 DR1-2。

### DR1-2（P2）：四处根因叙述与实测相反

**位置与原文**：

- `skills/spec-evolution/scripts/collect-facts.py:254-258`
  > 仅靠命令行 `-B` 不足以覆盖全部门禁：`audit-doc-health.py` 内部用 `importlib` 动态加载兄弟脚本，该路径不受 `-B` 影响，会写出 `__pycache__`。
- `skills/spec-evolution/tests/test_gate_invariants.py:205-207`
  > 只给命令加 `-B` 不够——`audit-doc-health.py` 经 `importlib` 动态加载兄弟脚本，该路径不受 `-B` 约束。
- `skills/spec-evolution/tests/conftest.py:71-72`
  > 真实仓库里 `audit-doc-health.py` 正是靠 subprocess + importlib 加载兄弟脚本留下字节码的。
- `docs/explanation/architecture/spec-evolution-design.md:87`
  > 仅靠命令行 `-B` 不足以覆盖全部路径，`audit-doc-health.py` 内部的 `importlib` 动态加载不受 `-B` 约束、会写出 `__pycache__`。

**反证**（命令与原始输出）：

```
$ cd /tmp/real-a && python3 -B skills/doc-governance/scripts/audit-doc-health.py; echo "exit=$?"
exit=0
$ find . -name '__pycache__' -o -name '*.pyc'
（空）                      ← -B 完全压制 importlib 路径

$ grep -rn 'subprocess\|Popen\|os.system' skills/doc-governance/scripts/
（零命中）                  ← 真实门禁树不存在级联子进程
```

**最小修法**：把四处措辞改为可复现的事实陈述，例如：「门禁命令一律带 `-B`（压制 importlib 动态加载在内的 import 写入）；同时为整棵进程树注入 `PYTHONDONTWRITEBYTECODE=1` 并（建议）`PYTHONPYCACHEPREFIX`，以覆盖未来新增门禁的子进程与显式编译（如 `py_compile`）。注意：本仓库当前唯一实测的字节码写入源是 `skills/doc-governance/tests/test_doc_index_convention.py:420` 的 `py_compile.compile()`，它不受 `-B`/`PYTHONDONTWRITEBYTECODE` 约束。」

### DR1-3（P2）：退出码「权威出处」指向不存在的章节

**位置**：`skills/spec-evolution/SKILL.md:81`

```
> 权威定义在 `scripts/judge.py` 与 [references/checks-spec.md](references/checks-spec.md)；本表与之一致。
```

**实测**：`skills/spec-evolution/references/checks-spec.md` 共 53 行，全文中与退出码相关的命中仅有：

```
$ grep -n "退出码\|exit" skills/spec-evolution/references/checks-spec.md
19:| **C-09** | 既有门禁失败 | S1 | **BLOCKER** | 4 条门禁任一 `exit_code != 0` |
47:4. **本技能不做设计质量评价**：…此类问题无退出码可复现，纳入即等于给谄媚开门。
```

即**没有** 0/1/2 的退出码定义表。`doc-governance` 的断链门禁只能发现「链接指向不存在的文件」，无法发现「链接指向的文件没有该内容」——这类**语义断链**是本仓库门禁的已知盲区。

**最小修法**：二选一 —— (a) 在 `references/checks-spec.md` 增设「退出码」小节（0/1/2 三值表 + 「无第四种取值」），使被引权威真实存在；或 (b) 把 `SKILL.md:81` 的权威收敛为 `scripts/judge.py`（并说明「判据清单见 checks-spec.md」），不给读者一个不存在的复核入口。

### DR1-4（P3）：BK-0033 卡片状态与同一 Delta 的实现不同步

**位置**：`docs/project/backlog/active/BK-0033-门禁子进程非-utf-8-输出导致裸-traceback.md`

卡片头部：`status: active`、`resolution: null`；DoD：

```
- [ ] collect-facts.py 两处 subprocess.run 加 encoding=utf-8/errors=replace；judge.py 与 collect-facts.py
  的 print 输出对非 UTF-8 环境不再抛 UnicodeEncodeError；异常路径退出码仍为 2 而非 1

## 4. 实施去向与结项记录
*(未开工)*
```

实现侧（同一 Delta 的 `d8aa611`，由 `git log -S'errors="replace"'` 归因）：

```
$ grep -n "errors=\|reconfigure\|encoding=" skills/spec-evolution/scripts/collect-facts.py skills/spec-evolution/scripts/judge.py
skills/spec-evolution/scripts/collect-facts.py:71:        return path.read_text(encoding="utf-8")
skills/spec-evolution/scripts/collect-facts.py:268:                                  text=True, encoding="utf-8", errors="replace",
skills/spec-evolution/scripts/collect-facts.py:288:                              text=True, encoding="utf-8", errors="replace", timeout=30)
skills/spec-evolution/scripts/collect-facts.py:340:        out.write_text(payload + "\n", encoding="utf-8")
skills/spec-evolution/scripts/judge.py:60:    with path.open("r", encoding="utf-8", errors="replace") as fh:
skills/spec-evolution/scripts/judge.py:292:    template = TEMPLATE_PATH.read_text(encoding="utf-8")
skills/spec-evolution/scripts/judge.py:310:        data = json.loads(path.read_text(encoding="utf-8"))
skills/spec-evolution/scripts/judge.py:358:        path.write_text(render_report(facts, findings), encoding="utf-8")
skills/spec-evolution/scripts/judge.py:364:                        encoding="utf-8")
```

（`reconfigure` 零命中 → print 侧未硬化。）

**判定**：DoD 是合取式，第一条（subprocess 编码）**已落地**，第二条（print 对非 UTF-8 环境不抛 `UnicodeEncodeError`）确未落地（`grep -n "reconfigure" skills/spec-evolution/scripts/*.py` 零命中）。因此卡片作为待办仍有效，但 `status`/「未开工」的记录与实现不同步。

**最小修法**：拆分 DoD 勾选状态（第一条打勾并注明实施提交 `d8aa611`），实施去向写「部分落地：subprocess 编码已修，print 硬化待办」。

### DR1-5（P3）：三态判据未覆盖 falsy-but-not-None

**位置**：`skills/spec-evolution/scripts/judge.py:246-247`、`:256-260`

```python
raw_gates = facts.get("gates")
gates = raw_gates or {}
...
elif raw_gates is None:
    blocker_section = "## BLOCKER\n\n（未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论）"
else:
    blocker_section = "## BLOCKER\n\n（已采集门禁事实，无失败）"
```

**复现**：`/tmp/e2e` 中把真实 facts 的 `gates` 置为 `[]` 后送判定器：

```
$ python3 -c "import json;d=json.load(open('/tmp/facts-e2e.json'));d['gates']=[];json.dump(d,open('/tmp/facts-emptygates.json','w'),ensure_ascii=False)"
$ python3 skills/spec-evolution/scripts/judge.py --repo-root . --facts /tmp/facts-emptygates.json --report /tmp/rep-empty.md
📊 findings=11 blocker/high=3
$ grep -n -A3 "## BLOCKER" /tmp/rep-empty.md
7:## BLOCKER
8:
9:（已采集门禁事实，无失败）
```

**可达性**：本仓库内 `collect_gates()`（`collect-facts.py:263-281`）对四个门禁键恒定填值，`[]`/`{}` 自然不可达；但 `judge.py --facts` 接受外部产物，且 `REQUIRED_TOP_KEYS`（`judge.py:23`）只校键存在、未校 `gates` 类型。

**最小修法**：把三态判据从「`is None`」改为基于「是否为非空映射」：`if not isinstance(raw_gates, dict) or not raw_gates: → 未采集/无有效门禁事实`。注意这会**新增第四态语义**，而 R2 已否决「为 C-09 增设第四态」——因此推荐**不新增分支**，而是让 `gates` 的形状校验（`[]`/`{}` → 退出码 2 输入错误）承担，既不扩张状态机也不留 fail-open。

### DR1-6（P3）：README 注册面判据收紧未登记、无测试

**位置**：`skills/spec-evolution/scripts/collect-facts.py:227`

```python
            # 与 docs_index 同一严格形式：裸子串 `skills/{name}` 会被
            # `skills/{name}-suffix` 之类的前缀命中，造成 C-07 假阴性。
            "readme": f"skills/{name}/SKILL.md" in readme_text,
```

**实测**：把该判据回退为 `skills/{name}` 后在同一棵树上重跑采集与判定，findings 逐行无差异（11 findings / 3 blocking 不变，见 §3.6 第 4 条）——**对本仓库零影响**。但该语义改动未列入计划 D-10~D-16 修复清单，也无对应测试钉住（当前无任何测试覆盖 `readme` 判据的前缀假阴性场景）。

**最小修法**：在计划的 Delta 清单补记该项一行，并加一条正/负例测试（构造 README 含 `skills/demo-extra` 但无 `skills/demo/SKILL.md`，断言 C-07 命中）。

---

## §5 第一轮结论概要

### 5.1 上一轮阻断项逐条裁决

| ID | 指控 | 本轮裁决 | 依据 |
| :--- | :--- | :--- | :--- |
| **R1-1** | GI-6「采集与判定只读」不变式实质失效 | **🔴 未根除（部分修复）** | 修复后采集器端到端仍在仓库内新增 `__pycache__/` 目录 + `manage-doc-index.cpython-312.pyc`（§3.1 A-4）；`PYTHONDONTWRITEBYTECODE=1` 只能把残留从 6 条压到 2 条（A-3）；元凶为 `skills/doc-governance/tests/test_doc_index_convention.py:420` 的 `py_compile.compile()`（A-5）；新增结构断言可被 `env=None` + docstring 满足（A-6/A-7）；自述的变异证据不可复现（A-6） |
| **R1-2** | 退出码语义与实现矛盾（文档写「0 = 无 finding」） | **✅ 已根除** | 四份文档（RFC-0004 §3.3/DK-4、`SKILL.md:73-81`、设计书、计划 §5/§D-10）均已收敛为「0 = 无 BLOCKER/HIGH（可含 MID advisory）；1 = 存在 BLOCKER/HIGH；2 = 用法/输入错误」，无残留「无 finding」表述；实现被 8 条测试真实钉住（§3.4 变异 R1-2 → 8 failed）。残留问题只有 DR1-3（权威指针断链），不构成语义矛盾 |
| **R1-3** | `--no-gates` 下对既有门禁作肯定陈述（fail-open） | **✅ 已根除** | 三态端到端在真实仓库输出正确：`None` → 「未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论」（§3.4）；`SKILL.md:50` 已加「放行前的最终复查必须不带 `--no-gates`」；回退三态使 `test_judge_contract.py:250` 转红。残留 DR1-5（`gates: []`）为**外部输入形状**缺口，本仓库内不可达，定级 P3 不计入阻断 |
| **R1-4**（R2 定级 P2，以 BK-0033 登记） | 门禁子进程非 UTF-8 输出导致裸 traceback | **✅ 主体已修（subprocess 侧）** | `collect-facts.py:268`、`:288` 已加 `encoding="utf-8", errors="replace"`；print 侧硬化仍未做（卡片仍开）。登记状态失真 → DR1-4（P3） |

### 5.2 阻断项计数与 Zero Blockers 判定

- **P0 = 0**
- **P1 = 1**（DR1-1：GI-6 生产态仍被违反，且本次 Diff 以此为由宣告「结构性免疫」）
- **P2 = 2**（DR1-2 根因叙述错误；DR1-3 退出码权威断链）
- **P3 = 3**（DR1-4 卡片状态；DR1-5 `gates: []` fail-open 残留；DR1-6 未登记判据收紧）

> **是否 Zero Blockers：否。** 交付门禁裁决：**🔴 阻断交付**（1 项 P1）。DR1-1 必须以「实测仓库内残留 = 0」的端到端证据闭合，而不是以夹具内断言全绿作为放行依据。
> **迭代计数**：Delta R1 第 1 轮 / 上限 3 轮（余 2 轮）。

### 5.3 通过项（本轮验证为真，供 R2 复核）

1. 全新副本 `python3 -B -m pytest skills/ -q -p no:cacheprovider` → **376 passed**，与计划 §Active Checkpoint 声称一致。
2. 全仓判定 `📊 findings=11 blocker/high=3`，`--skills spec-evolution` → `findings=0`、`CLEAN`、exit 0，与计划 `:34` 声称一致。
3. 两条 `-B` 的补加（`collect-facts.py:59-60`、`:62`）是真实有效的：真实门禁树残留 5 → 0（§3.1 A-2）。
4. 三态报告、退出码语义、`[REPO:*]` 锚点 containment/行号语义、判定确定性、`--no-gates` 不写仓库（`test_gi6_collector_is_read_only_without_gates`）均未攻破。
5. 夹具桩的三级链改造（`conftest.py:75-84`）确实消除了「三无桩」恒真问题（对 env/`-B` 机制而言，组合变异可转红），但**不能覆盖本次生产泄漏向量**——这是夹具能力的边界，不是夹具的缺陷。
6. 本轮未发现本次 Diff 重新引入 R2 已否决的三项扩大化改法（未把夹具桩替换为真实门禁、未为 C-09 增设第四态、未把 MID 升格为阻断）。
7. 文档与实现一致性（除 DR1-3/DR1-4）：`docs/llms.txt` 重跑零差异（73 篇收录）、`docs/index.md` 索引与 7 张 BK 卡同步、backlog `index.md` 仪表盘与 `active/` 卡片数一致、RFC-0004 `[REPO:*]` 契约（V0.5.0）与实现解析一致。

### 5.4 只读合规自证

```
$ cd /home/hui/workspace/projects/cr-agent-arsenal
$ git status --porcelain
（除本报告写入前为空；本报告为唯一写入面，路径已预授权）
```

- 零网络：本会话未发起任何网络请求。
- 仓库内临时文件：**无**（全部实验在 `/tmp` 副本内进行，副本清单见 §0.2）。
- 未执行任何破坏性 git 命令；未修改、删除仓库内任何既有文件。
