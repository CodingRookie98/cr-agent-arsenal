# 第一轮对抗审查报告 · Delta 修复批次再循环 (Delta Re-Loop Round 1 Red-Team Review Report)

## 1. 第一性原理与本质溯源分析

- **审查基线与改动性质定性**: 基线 `fe8da78471c727e6bdaef2f8ed64bbe978ac94b5...9db83c77a4a240ad3e26224633d372de0e6c56a0`（`git diff --stat` = 24 files changed, 1406 insertions(+), 64 deletions(-)）。本次修复的是上一轮 R2 的 3 项阻断（`R1-1/R1-2/R1-3`，落点于 `d8aa611`）与退役 Delta R1 的 `DR1-1`（`7449aae`）。**性质定性：根因修复方向正确，四条修法（GI-6 三重机制 / 三态收紧 / 权威链补登 / 判据收紧登记）全部通过独立变异复现；但其中一条修法以「改道写入」换来了新的环境条件性依赖，另一条修法在自己的文档面制造了 3 处引用断裂。**
- **本次修复的两条设计前提**（第一性原理假设，逐条实测）：
  - **前提 P1**：只读不变式 (GI-6) 的失效根因是「字节码写入路径」，三条路径各需不同机制，`PYTHONPYCACHEPREFIX` 是把三条路径一并改道到仓库外的唯一充分机制。
  - **前提 P2**：`judge.py` 退出码 `0/1/2` 三态是「本技能唯一的对外结论」，其中「输入错误」必须落 `2` 且拒绝写出产物。
- 本次审查的全部实验在 `/tmp/dr1-audit/**` 的仓库副本内进行；写入本报告前 `git status --porcelain` 为空、`skills/**` 字节码清单与基线逐条一致（§5 末附取证）。

### 1.1 前提 P1 实测：成立（机制必要性真值表逐格对齐）

三条路径的最小复现（`/tmp/dr1-audit/vec/proj`，源文件 `_helper.py`，每次运行前清 `__pycache__`，判定「仓库内是否出现 .pyc」）：

| 写入路径 | 仅 `-B`（父进程） | `PYTHONDONTWRITEBYTECODE=1` | `PYTHONPYCACHEPREFIX=<仓库外>` |
| :--- | :--- | :--- | :--- |
| V1 直接子进程导入期写入 | 无写入（`-B` 生效） | 无写入 | 无写入 |
| V2 孙进程导入期写入（父带 `-B`，子经 `subprocess`） | **写入 `__pycache__/_helper.cpython-312.pyc`** | 无写入 | 无写入 |
| V3 孙进程显式 `py_compile.compile()` | **写入** | **仍然写入** | 无写入 |

生产态端到端变异（各在 `real` 的独立副本内跑真实四道门禁，比对运行前后文件清单）：

```bash
B=/tmp/dr1-audit
for m in a b c; do
  d=$B/prodMUT$m; cp -a $B/real $d
  case $m in
    a) sed -i '/"PYTHONPYCACHEPREFIX": PYCACHE_PREFIX,/d' $d/skills/spec-evolution/scripts/collect-facts.py ;;
    b) sed -i '/"PYTHONDONTWRITEBYTECODE": "1",/d' $d/skills/spec-evolution/scripts/collect-facts.py ;;
    c) sed -i 's/"python3", "-B", /"python3", /g' $d/skills/spec-evolution/scripts/collect-facts.py ;;
  esac
  find $d -type f -printf "%T@ %s %p\n" | sort -k3 > $B/${m}_before.txt
  ( cd $d && python3 -B $d/skills/spec-evolution/scripts/collect-facts.py --repo-root $d --out $B/facts_prodMUT$m.json >/dev/null 2>&1; echo "collect rc=$?" )
  find $d -type f -printf "%T@ %s %p\n" | sort -k3 > $B/${m}_after.txt
  diff $B/${m}_before.txt $B/${m}_after.txt && echo "(no change)"
done
```

原始输出（节选决定性行）：

```text
########## PRODUCTION MUTATION a ##########   # 删除 PYTHONPYCACHEPREFIX
--- remaining -B count in GATES: 4
collect rc=0
--- diff before/after (in-repo side effects) ---
205a206
> 1791801998.4071231660 17448 /tmp/dr1-audit/prodMUTa/skills/doc-governance/scripts/__pycache__/manage-doc-index.cpython-312.pyc
########## PRODUCTION MUTATION b ##########   # 删除 PYTHONDONTWRITEBYTECODE
--- remaining -B count in GATES: 4
collect rc=0
--- diff before/after (in-repo side effects) ---
(no change)
########## PRODUCTION MUTATION c ##########   # 删除四条 GATES 的 -B
--- remaining -B count in GATES: 0
collect rc=0
--- diff before/after (in-repo side effects) ---
(no change)
```

夹具级变异（干净环境，`env -u` 清除我自身 shell 可能透传的同名变量，避免 `{**os.environ}` 把污染带进被测代码）：

```bash
cd /tmp/dr1-audit/fixmutN && env -u PYTHONPYCACHEPREFIX -u PYTHONDONTWRITEBYTECODE \
  python3 -B -m pytest skills/spec-evolution/tests -q -p no:cacheprovider
```

```text
fixmut1（删除 PYTHONPYCACHEPREFIX） → 2 failed, 51 passed in 6.63s
    FAILED skills/spec-evolution/tests/test_gate_invariants.py::test_gi6_gates_run_without_leaving_artifacts
    FAILED skills/spec-evolution/tests/test_gate_invariants.py::test_gi6_bytecode_suppression_is_structural
    （后者断言点 test_gate_invariants.py:227：assert 'PYTHONPYCACHEPREFIX' in {'PYTHONDONTWRITEBYTECODE'}）
fixmut2（删除 PYTHONDONTWRITEBYTECODE）→ 1 failed, 52 passed in 11.46s（仅 structural 转红）
fixmut3（删除四条 -B）            → 53 passed（无任何测试守护 -B）
未变异的同一副本（fixmut3 变异前）  → 53 passed
```

**对照作者自述（计划 `:2298` D-17 / `:2299` D-18）逐条核验：**

| 自述 | 我的独立实测 | 判定 |
| :--- | :--- | :--- |
| 移除 `PYTHONPYCACHEPREFIX` → 2 条转红（结构 + 功能） | fixmut1 = `2 failed, 51 passed`（同名两条） | 一致 |
| 单独移除 `PYTHONDONTWRITEBYTECODE` → 仅结构测试转红，其为「冗余纵深」 | fixmut2 = `1 failed, 52 passed`（仅 structural） | 一致 |
| 端到端干净副本差分：修复后 0 残留（修复前残留 `manage-doc-index.cpython-312.pyc`） | production MUT a 复现出该残留（17448 B），未变异副本差分 `(no change)` | 一致 |
| 显式 `py_compile.compile()` 同时无视 `-B` 与 `PYTHONDONTWRITEBYTECODE` | V3 真值表两列均为「写入」；出处 `skills/doc-governance/tests/test_doc_index_convention.py:414-421` 实读确认 | 一致 |
| 泄漏向量在真实运行中确实被触发（而非仅存在于假想） | 采集器运行期镜像内出现 `manage-doc-index.cpython-312.pyc`（18:34:26 / 17444 B，另有作者自验的 `gi6-clean` 18:23:04 一份），而副本差分同时为空 | 一致 |

**结论：前提 P1 成立，且是本次修复中最扎实的一环。** 关键反证（泄漏向量被真实触发且被改道）：

```bash
find /tmp/spec-evolution-pycache -name "manage-doc-index*" -printf "%TY-%Tm-%Td %TH:%TM:%TS %s %p\n" | sort
```

```text
2026-10-12 18:23:04.5302904770 17439 /tmp/spec-evolution-pycache/tmp/gi6-clean/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
2026-10-12 18:34:26.6083600390 17444 /tmp/spec-evolution-pycache/tmp/dr1-audit/real/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
2026-10-12 18:47:11.8305178820 17448 /tmp/spec-evolution-pycache/tmp/dr1-audit/prodMUTb/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
2026-10-12 18:47:48.8254611550 17448 /tmp/spec-evolution-pycache/tmp/dr1-audit/prodMUTc/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
```

### 1.2 前提 P2 实测：主要成立，一处反例（→ R1-1）

`judge.py` 对构造 facts 的退出码实测（`--facts case_X.json --report rep2/X.md`）：

| 用例 | 输入 | rc | 产物 | report 文案 |
| :--- | :--- | :--- | :--- | :--- |
| A | 真实 facts（四门禁 exit 0） | 1 | 写出 | 「已采集门禁事实，无失败」 |
| B | `pytest.exit_code=1` | 1 | 写出 | 门禁失败表 |
| C | `gates = null` | 1 | 写出 | 「未采集门禁事实 —— C-09 未执行」 |
| D | `gates = []` | 1 | 写出 | 「未采集门禁事实 —— C-09 未执行」 |
| E | `{"pytest":{"exit_code":0},"check_doc_links":"junk"}` | 1 | 写出 | 「未采集门禁事实 —— C-09 未执行」 |
| F | `skills = 5` | **1** | **无** | stderr 10 行 Python Traceback |
| G | `root_prompt = "junk"` | **1** | **无** | stderr 11 行 Traceback |
| H | `repo_root = 123` | **1** | **无** | stderr 12 行 Traceback |
| I | `skills = [{}]` | **1** | **无** | stderr 11 行 Traceback |
| J | `root_prompt.path = "../../../../etc/passwd"` + C-10 触发 | 2 | 无 | 「❌ 锚点存在性校验失败（GI-3），拒绝写出任何产物：」 |
| K | `root_prompt.path = "/etc/passwd"` | 2 | 无 | 同上 |
| L | `oversized_files = ["skills/demo/../../.git/config"]` | 2 | 无 | 同上 |
| M | `root_prompt.path = "docs:5"`（目录带行号） | 2 | 无 | 「锚点行号只能指向文件，但目标是目录: docs:5」 |
| N | `root_prompt.path = "README.md:99999"` | 2 | 无 | 「锚点行号越界: README.md:99999（共 141 行，行号从 1 起）」 |
| O | `root_prompt.path = "README.md:1"` | 1 | 写出 | 正常判定（真 facts 含 3×HIGH） |

- **三态收紧（A~E）成立**：`[]`/`{}`/`0`/`""`/混入非 dict 值均被判「未采集」，报告不再对既有门禁作肯定陈述 → 上一轮 `DR1-5`（同类 fail-open）已根治。
- **GI-3 fail-closed 成立**（J~O）：绝对路径逃逸、`../` 穿越、技能锚点穿越、目录带行号、行号越界五种越界形态全部 rc=2 且零产物；行号合法时正常判定。新增的 `_check_line` 并非死代码——它可经 `--facts` 注入的 `root_prompt.path`（携带 `:digits`）在生产路径上被真实触发（M/N 即证据）。
- **反例（F~I）**：顶层键存在但**类型**畸形时，`judge.py` 未被捕获的异常使其以 CPython 的「未捕获异常退出码 1」退出——与「存在 BLOCKER/HIGH」同码，且 stderr 为 traceback 而非 `❌` 诊断。这直接违反本次新写入的 `references/checks-spec.md §4` 契约（`2` = 用法或输入错误；`1` = 至少一条阻断级 finding）。详见 R1-1。

### 1.3 前提的边界（第一性原理穿透）

1. **本轮修法是「改道写入」而非「消除写入」。** 唯一有实质作用的机制 `PYTHONPYCACHEPREFIX` 把字节码落点整体搬到仓库外；写入行为本身仍然发生（镜像内有真实 `.pyc`）。因此 **GI-6 的实际作用域是「采集器信封（collector envelope）」，而非「仓库级只读」**。这与 `docs/explanation/architecture/spec-evolution-design.md:87`「采集器与它跑的门禁除显式 --out 外不得在仓库内创建/修改/删除任何文件」及 `:103`「GI-1~GI-6 的对象是本技能自身」的自述限定自洽，故**不构成缺陷**；但仓库内现存的 4 个 18:25:33 的 `skills/doc-governance/scripts/__pycache__/*.pyc` 只能由**非信封化**的 `pytest` 运行（无 `-B`、无 `PYTHONDONTWRITEBYTECODE`、无 `PYTHONPYCACHEPREFIX`）产生——信封化运行时它们会落进镜像（见 §1.1 反证）。任何把本轮结论升级表述为「仓库已实现全局只读」的说法都会失实；正确表述是「**采集器信封内只读**」。
2. **改道的代价：确定性换成了条件性。** 修法把字节码写/读位置从「仓库内目录（需仓写权）」搬到「`/tmp` 下的共享、可预测路径（`/tmp` 为 `drwxrwxrwt`，任何本地用户可抢先创建）」，并把路径来源交给 `tempfile.gettempdir()` 的环境推导（`TMPDIR` 可在仓库内；候选目录全不可写时回落 `os.getcwd()`）。这两条是本轮**新引入**的信任面与失效面（R1-2 / R1-3）。一句话概括本质：**修法用「依赖环境的路径推导 + 共享命名空间」替换了「确定性的仓内写入」——可审计的确定性被换成了不可审计的条件性。**
3. **「冗余纵深」的声明是诚实的。** `-B` 与 `PYTHONDONTWRITEBYTECODE` 在生产态变异（MUT b/c）与夹具变异（fixmut2/3）中均被证明确实不承担充分性职责，`collect-facts.py:257-281` 的 docstring 亦主动声明「后者是保留的冗余纵深」，**宣称与取证同宽**，这一点值得肯定。
4. **上一轮阻断项复核**：`R1-1`（`d8aa611`）→ **已根治**（本轮 MUT a/fixmut1 证明充分机制在位，端到端 0 残留）；`R1-2`（退出码口径）→ **已根治**（RFC-0004 / `SKILL.md:75-79` / `checks-spec.md §4` / 实现四处一致，A~E 实测与表一致）；`R1-3`（`--no-gates` 肯定陈述）→ **已根治**（C/D/E 三态文案）；`DR1-1`（`7449aae`）→ **已根治**（同一批机制）；`DR1-2`（根因叙述失实）→ **已根治**（§1.1 对照表逐条一致）；`DR1-3`（权威断链）→ **已根治但引入新债**：`checks-spec.md §4` 已存在且与 `SKILL.md:81` 双向自洽，但该章节插入造成的编号顺延使另外 **3 处 `§4` 指针**指向了错误章节（R1-4），且计划 `:2300` D-19 行自述的验证方法「章节编号全文件复核」未落实。

## 2. 运行时与 SSR/沙盒安全推演（条件维度）

未激活（非客户端/SSR 改动）

## 3. 红队攻击路径推演 (Concrete Failure Scenarios)

### 攻击路径 1：畸形 facts 注入 —— 「输入错误伪装成阻断裁决」　【攻破】

```bash
python3 -B - <<'PY'
import json, subprocess, sys, pathlib, os
J="/home/hui/workspace/projects/cr-agent-arsenal/skills/spec-evolution/scripts/judge.py"
base=json.load(open("/tmp/dr1-audit/facts.json"))
cases={
 "F_skills_int":      lambda d: d.__setitem__("skills",5),
 "G_rootprompt_str":  lambda d: d.__setitem__("root_prompt","junk"),
 "H_repo_root_int":   lambda d: d.__setitem__("repo_root",123),
 "I_skills_elem":     lambda d: d.__setitem__("skills",[{}]),
 "D_gates_empty_list":lambda d: d.__setitem__("gates",[]),
}
for name,mut in cases.items():
    d=json.loads(json.dumps(base)); mut(d)
    f=f"/tmp/dr1-audit/case_{name}.json"; json.dump(d,open(f,"w"))
    rp=f"/tmp/dr1-audit/rep2/{name}.md"
    p=subprocess.run([sys.executable,"-B",J,"--facts",f,"--report",rp],capture_output=True,text=True,
                     env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    err=(p.stderr.strip().splitlines() or [""])
    print(f"--- {name}: rc={p.returncode} report_written={os.path.exists(rp)} stderr_lines={len(err)}")
    for l in err[:2]: print("    "+l)
    print("    last:", err[-1] if err else "")
PY
```

原始输出：

```text
--- F_skills_int: rc=1 report_written=False stderr_lines=10
    Traceback (most recent call last):
      File "/home/hui/workspace/projects/cr-agent-arsenal/skills/spec-evolution/scripts/judge.py", line 388, in <module>
        sys.exit(main())
    last: TypeError: 'int' object is not iterable
--- G_rootprompt_str: rc=1 report_written=False stderr_lines=11
    last: AttributeError: 'str' object has no attribute 'get'
--- H_repo_root_int: rc=1 report_written=False stderr_lines=12
    last: TypeError: argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'int'
--- I_skills_elem: rc=1 report_written=False stderr_lines=11
    last: KeyError: 'name'
--- D_gates_empty_list: rc=1 report_written=True stderr_lines=1
```

机理：`load_facts`（`judge.py:321-333`）只做「顶层键存在性」检查，不校验类型；`build_findings` 随后迭代/取字段时崩溃。Python 解释器对未捕获异常固定以状态码 **1** 退出，而本次新写入的 `checks-spec.md §4` 把 `1` 定义为「存在 BLOCKER/HIGH，至少一条阻断级 finding」。于是**一个纯粹的使用错误，被判成了阻断级结论**，且编排方会拿到一份 traceback 而非 `❌` 诊断。破坏机理不需要复杂构造：任何被截断/手工编辑/上游 schema 漂移的 facts 文件都落在这条路径上。

### 攻击路径 2：共享 `PYCACHE_PREFIX` 缓存投毒 —— 门禁进程内任意代码执行　【攻破】

前置事实：`collect-facts.py:44` 把镜像根固定为 `os.path.join(tempfile.gettempdir(), "spec-evolution-pycache")`（固定名，注释自述「避免每次采集都在 /tmp 累积目录」），且 `:279-280` 把它注入每个门禁子进程。CPython 会**优先读取**该路径下与之匹配的字节码缓存。

```bash
P=/tmp/dr1-audit/poison/repo; cp -a /tmp/dr1-audit/real $P
# 步骤 1：基线（无投毒）
cd $P && PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/spec-evolution-pycache \
  python3 -B -m pytest skills/doc-governance/tests/test_doc_governance_scripts.py -q -p no:cacheprovider | tail -3
# 步骤 2：以「同尺寸 + 同 mtime」伪造目标模块的缓存条目（目标 = 真实门禁模块 check-doc-links.py）
python3 -B - <<'PY'
import os, sys, importlib.util, py_compile, pathlib
prefix="/tmp/spec-evolution-pycache"
target="/tmp/dr1-audit/poison/repo/skills/doc-governance/scripts/check-doc-links.py"
st=os.stat(target); size=st.st_size
sys.pycache_prefix=prefix
cfile=importlib.util.cache_from_source(target)
pathlib.Path(cfile).parent.mkdir(parents=True, exist_ok=True)
marker="import pathlib; pathlib.Path('/tmp/dr1-audit/POISON_EXECUTED').write_text('exec')\n"
pad=max(0, size-len(marker.encode()))
open("/tmp/dr1-audit/poison/poison_src.py","w").write(marker+"#"*pad)
os.utime("/tmp/dr1-audit/poison/poison_src.py",(st.st_atime, st.st_mtime))
py_compile.compile("/tmp/dr1-audit/poison/poison_src.py", cfile=cfile, dfile=target, doraise=True)
print("poisoned cache ->", cfile); print("source size/mtime:", size, int(st.st_mtime), "| poison size:", len(marker)+pad)
PY
rm -f /tmp/dr1-audit/POISON_EXECUTED
# 步骤 3：用与采集器完全相同的 env 再跑同一条门禁命令
cd $P && PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/spec-evolution-pycache \
  python3 -B -m pytest skills/doc-governance/tests/test_doc_governance_scripts.py -q -p no:cacheprovider | tail -6
ls -l /tmp/dr1-audit/POISON_EXECUTED
```

原始输出：

```text
74 passed in 5.36s                     # 步骤 1：基线通过
poisoned cache -> /tmp/spec-evolution-pycache/tmp/dr1-audit/poison/repo/skills/doc-governance/scripts/check-doc-links.cpython-312.pyc
source size/mtime: 11582 1791081790 | poison size: 11582
    scan_directory = _links_mod.scan_directory
E   AttributeError: module 'check_doc_links' has no attribute 'scan_directory'
ERROR skills/doc-governance/tests/test_doc_governance_scripts.py - AttributeE...
1 error in 2.90s                       # 步骤 3：模块身份被替换（真实源码未被使用）
-rw-r--r-- 1 hui hui 4 Oct 12 18:41 /tmp/dr1-audit/POISON_EXECUTED   # => 注入代码以门禁进程身份执行
```

权限面（`/tmp` 为 sticky+world-writable，任何本地用户可抢先创建该共享根目录，从而成为其属主并持有写权）：

```bash
stat -c '%A %U:%G %n' /tmp /tmp/spec-evolution-pycache /tmp/spec-evolution-pycache/tmp
```

```text
drwxrwxrwt root:root /tmp
drwxr-xr-x hui:hui /tmp/spec-evolution-pycache
drwxr-xr-x hui:hui /tmp/spec-evolution-pycache/tmp
```

**取证边界（宣称与取证同宽）**：本机无第二账户，「跨用户抢先创建 → 植入」这一步**未实测**，仅由 `/tmp` 权限实测 + CPython 缓存读取语义推导；**同用户植入已端到端实测成功**（上表最后一行）。植入条目已由我删除（`rm -f /tmp/spec-evolution-pycache/tmp/dr1-audit/poison/repo/skills/doc-governance/scripts/__pycache__/check-doc-links.cpython-312.pyc`，验证目录已空）。

### 攻击路径 3：`TMPDIR`/CWD 回落把「仓库外」重新指回仓库内　【攻破】

```bash
d=/tmp/dr1-audit/tmpdir1
TMPDIR=$d python3 -B $d/skills/spec-evolution/scripts/collect-facts.py --repo-root $d --out /tmp/dr1-audit/facts_tmpdir.json
cd $d && find . -type f | wc -l
grep -c "pytest-of-hui" <(find . -type f) ; grep -c "spec-evolution-pycache" <(find . -type f)
find . -path "*spec-evolution-pycache*" -type f -printf "%s %p\n"
```

原始输出（决定性片段）：

```text
collect rc=0
1908                                   # 运行后副本内新增文件总数
1907                                   # 属 pytest basetemp（历史既有行为，与本次 diff 无关）
3                                      # 属本次新增的 PYCACHE_PREFIX 镜像
162 ./spec-evolution-pycache/tmp/dr1-audit/tmpdir1/pytest-of-hui/pytest-0/test_gates_recorded_when_enabl0/repo/skills/doc-governance/scripts/_gate_helper.cpython-312.pyc
162 ./spec-evolution-pycache/tmp/dr1-audit/tmpdir1/pytest-of-hui/pytest-0/test_gi6_gates_run_without_lea0/repo/skills/doc-governance/scripts/_gate_helper.cpython-312.pyc
17447 ./spec-evolution-pycache/tmp/dr1-audit/tmpdir1/skills/doc-governance/scripts/manage-doc-index.cpython-312.pyc
```

同类失效面不止 `TMPDIR`：`tempfile.gettempdir()` 的候选目录全部不可写时会回落到 `os.getcwd()`（CPython 标准库原文，实读确认）：

```bash
python3 -B -c "import tempfile,inspect;print(inspect.getsource(tempfile._candidate_tempdir_list))"
```

```text
        dirlist.extend(['/tmp', '/var/tmp', '/usr/tmp'])
        try:
            dirlist.append(_os.getcwd())
        except (AttributeError, OSError):
            dirlist.append(_os.curdir)
            # As a last resort, the current directory.
```

即：只要采集器以仓库目录为 cwd 启动且候选临时目录不可写，`PYCACHEPREFIX` 自身就落进仓库——**GI-6 的充分机制被环境静默反噬，而代码对此没有任何护栏**（`PYCACHE_PREFIX` 在 `:44` 模块级求值，采集器不校验它是否位于 `repo_root` 之外）。

### 攻击路径 4：章节重编号造成的引用断裂　【攻破】

本次 diff 往 `checks-spec.md` 插入了 `## 4. 退出码语义`（`:42`），原 §4/§5 顺延为 §5/§6；但仓库内其他指向 `§4` 的指针未同步：

```bash
grep -rn "checks-spec.md[^)]*§[0-9]\|checks-spec.md §[0-9]" --include="*.md" . | grep -v "docs/project/reviews/"
grep -n "^## " skills/spec-evolution/references/checks-spec.md
```

原始输出：

```text
skills/spec-evolution/SKILL.md:24:**不适用**（结构性排除，详见 [references/checks-spec.md](references/checks-spec.md) §4）
docs/explanation/architecture/spec-evolution-design.md:161:（…与 references/checks-spec.md §4 保持一致…）
docs/project/plans/2026-10-12-spec-evolution.md:2115:5. **已知表达上限**（与 references/checks-spec.md §4 一致，不得夸大）。
docs/project/plans/2026-10-12-spec-evolution.md:2300:> | D-19 | … | 章节编号全文件复核 |
55:## 5. 已知表达上限（显式登记，不在 v1 掩饰）
42:## 4. 退出码语义
```

三处指针在改动前指向「已知表达上限」（当时确为 §4，**改动前是正确的**），改动后全部指向「退出码语义」——即断裂由本次 diff 引入。同时 `:2300` 的 D-19 行把验证方法自述为「章节编号全文件复核」，而实际只复核了 `SKILL.md:81` 那条权威声明本身：**这是一处「宣称的验证范围 > 实际取证范围」**，与上一轮 `DR1-2`（根因叙述失实）同类。

### 攻击路径 5：GI-6 三重机制的生产态必要性　【已封堵（验证通过）】

见 §1.1：`PYTHONPYCACHEPREFIX` 移除即复现 17448 B 仓内字节码（MUT a），在位时端到端零残留；`-B` / `PYTHONDONTWRITEBYTECODE` 移除均无差异（MUT b/c、fixmut2/3）。**结论：唯一充分机制在位且被变异守护（fixmut1 双测试转红），冗余项被诚实标注。**

### 攻击路径 6：锚点越界与行号幻觉　【已封堵（验证通过）】

```bash
python3 -B - <<'PY'
import json,subprocess,sys,os
J="/home/hui/workspace/projects/cr-agent-arsenal/skills/spec-evolution/scripts/judge.py"
def run(tag, path):
    d=json.load(open("/tmp/dr1-audit/facts.json"))
    d["root_prompt"]["path"]=path
    d["root_prompt"]["lines"]=d["root_prompt"]["baseline"]["lines"]+5   # 触发 C-10，使该锚点进入判定
    f=f"/tmp/dr1-audit/case_{tag}.json"; json.dump(d,open(f,"w"))
    rp=f"/tmp/dr1-audit/rep2/{tag}.md"
    p=subprocess.run([sys.executable,"-B",J,"--facts",f,"--report",rp],capture_output=True,text=True,
                     env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    print(f"--- {tag}: path={path!r} rc={p.returncode} report_written={os.path.exists(rp)}")
    print(p.stderr.rstrip())
run("M_dir_line","docs:5"); run("N_line_oob","README.md:99999"); run("O_line_ok","README.md:1")
run("J3_traverse","../../../../etc/passwd")
PY
```

原始输出：

```text
--- M_dir_line: path='docs:5' rc=2 report_written=False
❌ 锚点存在性校验失败（GI-3），拒绝写出任何产物：
  - F-04 C-10 anchor: 锚点行号只能指向文件，但目标是目录: docs:5
--- N_line_oob: path='README.md:99999' rc=2 report_written=False
  - F-04 C-10 anchor: 锚点行号越界: README.md:99999（共 141 行，行号从 1 起）
--- O_line_ok: path='README.md:1' rc=1 report_written=True
--- J3_traverse: path='../../../../etc/passwd' rc=2 report_written=False
  - F-04 C-10 anchor: 仓库锚点路径不存在或越出仓库: ../../../../etc/passwd
```

**结论：`_resolve_within` + `_check_line` 三面（绝对路径逃逸 / `../` 穿越 / 目录带行号 / 行号越界）全部 fail-closed 且可经 `--facts` 在生产路径触发；锚点合法时正常写出。**

### 攻击路径 7：三态 fail-open 复辟　【已封堵（验证通过）】

见 §1.2 用例 C/D/E：`gates = null`、`[]`、以及「一条 well-formed + 一条 junk」的混合表，均判为「未采集」，报告文案为「未采集门禁事实 —— C-09 未执行；本报告对既有门禁是否失败不作任何结论」，**不再出现「无既有门禁失败」**。`collected_gates` 的判据（`judge.py:144-155`：必须是非空 dict 且每个值都是 dict）在 `build_findings` 与 `render_report` 共用，无第二条判据分叉。

### 攻击路径 8：判据收紧造成假阳性（C-07 / README 精确路径）　【已封堵（验证通过）】

```bash
for s in agy-delegation-workflow clarification-protocol doc-governance dual-round-review \
         frontend-qa-gate goal-loop spec-evolution taste-driven-designer; do
  printf "%-28s %s\n" "$s" "$(grep -c "skills/$s/SKILL.md" README.md)"
done
cd /tmp/dr1-audit && python3 -B .../judge.py --facts facts.json --json findings2.json --report rep2/full.md
```

原始输出：

```text
agy-delegation-workflow      1
clarification-protocol       0        # 8 技能中唯一未登记 → F-03 是真阳性，非收紧误伤
doc-governance               1
dual-round-review            1
frontend-qa-gate             1
goal-loop                    1
spec-evolution               1
taste-driven-designer        1
📊 findings=11 blocker/high=3
  ⛔ F-01 HIGH C-01 agy-delegation-workflow [SKILL:agy-delegation-workflow/SKILL.md]
  ⛔ F-02 HIGH C-01 clarification-protocol [SKILL:clarification-protocol/SKILL.md]
  ⛔ F-03 HIGH C-07 clarification-protocol [REPO:README.md]
judge rc=1
findings: 11 Counter({'MID': 8, 'HIGH': 3})
spec-evolution findings: []
```

（三条 HIGH 全部落在本次 diff 范围之外的技能上，属历史既有，本轮不定级；`spec-evolution` 自身零 finding 与 RFC-0004 `:24` 的自述一致，findings 11 条 / 阻断级 3 条亦与自述数字逐字吻合。）

另：D-21 声称「该测试在收紧前的实现上会转红」，我独立变异复现（把 `:231` 判据还原为裸子串 `f"skills/{name}" in readme_text` 后单跑该测试）：

```bash
d=/tmp/dr1-audit/fixmut3
sed -i 's|f"skills/{name}/SKILL.md" in readme_text|f"skills/{name}" in readme_text|' $d/skills/spec-evolution/scripts/collect-facts.py
cd $d && env -u PYTHONPYCACHEPREFIX -u PYTHONDONTWRITEBYTECODE python3 -B -m pytest \
  skills/spec-evolution/tests/test_collect_facts.py -q -p no:cacheprovider | tail -4
```

```text
E       assert True is False
skills/spec-evolution/tests/test_collect_facts.py:118: AssertionError
FAILED skills/spec-evolution/tests/test_collect_facts.py::test_readme_registration_requires_exact_skill_path
1 failed, 15 passed in 0.95s
```

**宣称成立：该测试确实是新增行为的承重测试，而非装饰。**

### 已尝试且未能攻破（供后续轮次免重复投入）

| # | 尝试 | 命令要点 | 结果 |
| :--- | :--- | :--- | :--- |
| 1 | 移除四条 GATES 的 `-B`，看 GI-6 是否失守 | 生产态 MUT c / 夹具 fixmut3 | 二者均无差异（`(no change)` / `53 passed`）→ `-B` 是纯冗余纵深，不是可攻破面 |
| 2 | 移除 `PYTHONDONTWRITEBYTECODE` | 生产态 MUT b / fixmut2 | 生产态无差异；夹具仅结构测试转红 → 同上，且文档已如实标注「冗余」 |
| 3 | 绝对路径逃逸锚点（`/etc/passwd`） | 用例 K | rc=2，零产物 |
| 4 | `../` 穿越锚点（root_prompt 与技能锚点两条通道） | 用例 J3 / L | 均 rc=2，零产物 |
| 5 | 目录锚点带行号 / 行号越界 | 用例 M / N | 均 rc=2，含中文诊断 |
| 6 | 空表 / 畸形门禁表骗过「已采集」判定 | 用例 C/D/E | 全部判「未采集」，fail-closed |
| 7 | C-07 收紧导致既有技能批量假阳性 | 全仓 `judge --json` | 11 findings / 3 HIGH，与收紧前同数，无假阳性新增 |
| 8 | 门禁树本身是否已红（是否误把绿当红） | 真实四门禁端到端 | `pytest 377 passed in 78.25s`、断链 ✅ 0、健康 PASS、跨技能链接 `4 passed`，四条 exit_code 全 0 |
| 9 | `--no-gates` 是否让 C-09 静默通过 | 三态用例 + `SKILL.md:50` 警示 | 报告显式声明未采集，且 `SKILL.md` 已写明「放行前最终复查必须不带 `--no-gates`」 |
| 10 | 审查自身是否污染仓库 | 运行前后 `find -printf` 清单比对 + `git status --porcelain` | 本报告写入前工作区零改动；`skills/**` 字节码仅基线 4 个（18:25:33） |

## 4. 潜在缺陷清单 (Identified Defect Candidates)

| 稳定 ID | 严重级别推断 (P0/P1/P2/P3) | 是否由当前 Diff 引入 | 涉及文件与行号 | 缺陷描述 | 攻击或破坏机理 |
|:---|:---|:---:|:---|:---|:---|
| R1-1 | P2 (Suggestion) | 契约面本次引入（崩溃点历史既有） | `skills/spec-evolution/scripts/judge.py:321-333`（`load_facts`）、`:23`（`REQUIRED_TOP_KEYS`）、`:144-155`（本次新增的类型容忍只覆盖 `gates`） | 顶层键存在但类型畸形时未被捕获，解释器以状态码 1 退出，与「存在 BLOCKER/HIGH」同码，stderr 为 traceback 而非 `❌` 诊断 | 任何被截断/手改/上游 schema 漂移的 `--facts` 输入都会让「使用错误」被判成「阻断级结论」，编排方若只看 rc 会采信一个不存在的高危裁决 |
| R1-2 | P2 (Suggestion) | 是（`PYCACHE_PREFIX` 为本次新增） | `skills/spec-evolution/scripts/collect-facts.py:44`、`:257-281`（env 注入点） | 镜像根固定为 `/tmp/spec-evolution-pycache`（可预测、共享、跨运行持久），且不校验属主/独占性 | `/tmp` 为 `drwxrwxrwt`：本地用户可抢先创建该目录并植入与门禁模块同尺寸同 mtime 的畸形成员字节码，被门禁进程当作真实模块读取执行（实测已执行注入代码） |
| R1-3 | P3 (Suggestion) | 是（同上） | `skills/spec-evolution/scripts/collect-facts.py:44` | `PYCACHE_PREFIX` 由 `tempfile.gettempdir()` 在模块级推导，采集器不校验它位于 `repo_root` 之外 | `TMPDIR` 指向仓库内、或候选临时目录全不可写导致 `gettempdir()` 回落 `os.getcwd()` 时，镜像整体落入仓库，GI-6 静默失守（实测新增 3 个镜像文件） |
| R1-4 | P2 (Suggestion) | 是（断裂由本次章节重编号引入；断链行本身未被触碰） | `skills/spec-evolution/SKILL.md:24`、`docs/explanation/architecture/spec-evolution-design.md:161`、`docs/project/plans/2026-10-12-spec-evolution.md:2115`（另 `:2300` D-19 行） | 三处 `checks-spec.md §4` 指针在改动后指向「退出码语义」，而实际内容已顺延为 §5「已知表达上限」；D-19 自述的验证方法「章节编号全文件复核」未落实 | 从 `SKILL.md` 入口查阅「结构性排除」依据的读者会落入一个无关表格并可能判定「文档未记载」；同类权威断链正是上一轮 `DR1-3` 的成因，属修复引入的新债 |

### R1-1 畸形 facts 使「输入错误」伪装成阻断裁决（P2）

复现（原始输出见 §3 攻击路径 1）：

```bash
python3 -B -c "
import json;d=json.load(open('/tmp/dr1-audit/facts.json'));d['skills']=5
json.dump(d,open('/tmp/dr1-audit/case_F.json','w'))"
python3 -B skills/spec-evolution/scripts/judge.py --facts /tmp/dr1-audit/case_F.json --report /tmp/dr1-audit/rep2/F.md
echo "rc=$?"
```

```text
Traceback (most recent call last):
  File "/home/hui/workspace/projects/cr-agent-arsenal/skills/spec-evolution/scripts/judge.py", line 388, in <module>
    sys.exit(main())
  ...
TypeError: 'int' object is not iterable
rc=1
```

- **实测输出**：`rc=1`、无产物、stderr 10~12 行 traceback（`skills=5` / `root_prompt="junk"` / `repo_root=123` / `skills=[{}]` 四种均同）。
- **影响**：`references/checks-spec.md §4` 明写「`1` = 存在 BLOCKER/HIGH（至少一条阻断级 finding）」「`2` = 用法或输入错误」。此处输入错误被报成阻断裁决，且诊断从 `❌` 降级为 Python traceback；对只读退出码的下游（本次交付的编排器正是如此消费）构成**误判通道**。
- **最小修法**：在 `load_facts`（`judge.py:321-333`）现有 `missing` 检查之后补一段类型校验，失败即 `raise FactsError`（自然落 `2`）：`skills` 必须 `list` 且每项 `dict` 含 `name`；`root_prompt` 必须 `dict`；`repo_root` 必须 `str`；`gates` 必须 `dict | list | None`。约 4~6 行，与本次已落地的 `collected_gates` 类型容忍策略同源，可顺手为 `:144-155` 的判据补齐兄弟键。

### R1-2 共享、可预测的 `PYCACHE_PREFIX` 打开缓存投毒通道（P2）

复现步骤与原始输出见 §3 攻击路径 2（基线 74 passed → 植入同尺寸同 mtime 缓存 → 同一条门禁命令 `1 error`，`AttributeError: module 'check_doc_links' has no attribute 'scan_directory'`，标记文件 `/tmp/dr1-audit/POISON_EXECUTED` 4 字节被写出）。

- **影响**：门禁进程（以及经它派生的全部孙进程）会**读取并执行**该共享路径下的字节码。修法把读取位置从「仓库内目录（攻击者需仓写权）」搬到「`/tmp` 下的固定名共享路径（任何本地用户可抢先占位）」——**信任边界向下移动了一级**。
- **取证边界**：同用户植入已端到端实测；「跨用户抢先创建」未实测（本机无第二账户），仅由 `/tmp` 权限（`drwxrwxrwt`）与 CPython 缓存语义推导。单用户工作站上该风险为 0，故定级 P2 而非 P1。
- **最小修法**（二选一）：
  1. `PYCACHE_PREFIX = tempfile.mkdtemp(prefix="spec-evolution-pycache-")`（`mkdtemp` 以 0700 创建、名字不可预测），并在 `collect_gates` 收尾 `shutil.rmtree(..., ignore_errors=True)`——代价是放弃「固定名避免 /tmp 累积」的既有取舍；
  2. 保留固定名但在 `subprocess_env()` 内 `os.makedirs(PYCACHE_PREFIX, mode=0o700, exist_ok=True)` + 校验 `os.stat(PYCACHE_PREFIX).st_uid == os.getuid()` 与权限位，不满足即回退方案 1。
- 另建议：把该目录同时纳入 GI-6 的机械断言（例如断言 `PYCACHE_PREFIX` 的解析结果不在 `repo_root` 内，见 R1-3）。

### R1-3 `PYCACHE_PREFIX` 可被环境/回落重新指回仓库内（P3）

复现与原始输出见 §3 攻击路径 3（`TMPDIR=<副本> collect-facts.py` → 副本内新增 1908 个文件，其中 3 个属本次新机制；`_candidate_tempdir_list` 的 `os.getcwd()` 末位回落原文亦已实读确认）。

- **影响**：GI-6 的充分机制被环境静默反噬，`spec-evolution` 的「只读不变式」在一条环境变量下失效；1907 个 `pytest-of-hui` 文件属 pytest 自身对 `TMPDIR` 的既有响应（**历史既有**，不在本轮定级范围），本轮新机制的贡献是 3 个镜像文件。
- **最小修法**：把 `PYCACHE_PREFIX` 的求值从模块级（`:44`）移入 `subprocess_env(repo)`，在其中断言 `not Path(prefix).resolve().is_relative_to(repo.resolve())`，不成立则改用 `tempfile.mkdtemp()`（或直接以退出码 2 拒绝采集并提示 `TMPDIR` 越界）——把「仓库外」从注释承诺升级为机械不变量。

### R1-4 章节重编号造成 3 处引用断裂 + D-19 验证范围宣称过宽（P2）

复现与原始输出见 §3 攻击路径 4。

- **影响**：`SKILL.md:24` 是技能自身入口面，指向的「结构性排除」依据章节已不存在（现为退出码表）；`design.md:161` 与 `plan:2115` 是同一断裂的另两处落点。三处指针在改动前均正确，属本次 diff 引入的引用债；`plan:2300` D-19 行把验证方法写为「章节编号全文件复核」而实际未做全仓复核，构成一处「宣称范围 > 取证范围」。
- **最小修法**：三处 `§4` 改为 `§5`；把 D-19 的「变异对照 / 取证」列改为可机械执行的命令，例如 `grep -rn "checks-spec.md[^)]*§" --include='*.md' .` 并断言输出中所有引用编号与该文件实际标题一致（或在该列注明「仅复核 `SKILL.md:81`，未做全仓扫描」以收缩宣称）。

## 5. 第一轮结论概要

- **P0 数：0**
- **P1 数：0**
- **Zero Blockers：是**（按本轮编号：`R1-1` P2 / `R1-2` P2 / `R1-3` P3 / `R1-4` P2，无 P0 与 P1）
- **阻断项复核结论**：`R1-1`（GI-6 只读不变式）**已根治**；`R1-2`（退出码口径漂移）**已根治**；`R1-3`（`--no-gates` 肯定陈述）**已根治**；退役轮的 `DR1-1` **已根治**，`DR1-2`（根因叙述失实）**已根治**，`DR1-3`（权威断链）**已根治但引入 R1-4**。
- **最关键的三条发现**：
  1. **修法的机制选择被实测证实，但代价是一条新的信任边界。** `PYTHONPYCACHEPREFIX` 确实是封堵 GI-6 的唯一充分机制（MUT a 复现 17448 B 仓内字节码；机制在位时端到端零残留），但它把字节码的读写位置搬到 `/tmp` 的固定名共享目录——`§3 攻击路径 2` 已实测「共享缓存投毒 → 门禁进程内执行注入代码」。这是本轮**唯一具备代码执行后果**的发现（R1-2）。
  2. **「只读」现在是条件性的，且无护栏。** `TMPDIR` 指向仓库内或 `gettempdir()` 回落 `os.getcwd()` 时，充分机制自己会把镜像落回仓库（实测 3 个文件），采集器对此没有任何断言（R1-3）。GI-6 的准确表述是「采集器信封内只读」，而非「仓库级只读」（§1.3）。
  3. **本次修法在自己的契约面留了一处误判通道**：顶层键类型畸形时 `judge.py` 以解释器默认状态码 1 退出，恰好等于本次新写入的「存在 BLOCKER/HIGH」语义，输入错误因此伪装成阻断裁决（R1-1）；同时 `§4` 的插入制造了 3 处引用断裂并让 D-19 的验证宣称过宽（R1-4）。
- **审查自身的只读取证**：全部实验在 `/tmp/dr1-audit/**` 副本内完成；写入本报告前实测 `git status --porcelain` 为空、仓库内 `skills/**` 字节码仅基线 4 个（`2026-10-12 18:25:33`），本次审查除本报告外未在仓库内留下任何写入。
