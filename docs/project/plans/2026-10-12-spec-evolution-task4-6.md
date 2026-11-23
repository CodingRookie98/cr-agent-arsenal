# spec-evolution 实施计划 · 子册 Task 4-6（门禁不变式 / 设计书 / 注册面）

> **文档控制信息**
> - **文档标识**: PLAN-SPEC-EVOLUTION-2026-T46
> - **当前版本**: V1.0.0
> - **文档所有者**: 核心架构组
> - **生效日期**: 2026-10-12
> - **状态**: 母计划子册（历史原文归档，不再增量维护）

> **母计划**: [2026-10-12-spec-evolution.md](./2026-10-12-spec-evolution.md)（本文件为原文逐字迁移，仅作历史实施细节，**不再增量维护**）

---

#### Task 4: 门禁不变式测试 `test_gate_invariants.py`

**Files**
- Create: `skills/spec-evolution/tests/test_gate_invariants.py`

**Goal**：把 RFC-0004 §3.7 的 GI-1~GI-6 变成可回归断言。**这些断言的对象是 spec-evolution 自身**（判定器确定性、模板留白、锚点一致、退出码语义、采集只读），不是被测技能 —— 这是本技能「有真实选择端」的落点。

> **D-6（2026-10-12 P3 执行期修正）**：`test_gi5_exit_code_semantics` 原以 `description_chars = 600` 构造「存在 HIGH」用例，但 600 落在 `DESC_SOFT_LIMIT < n < DESC_HARD_LIMIT` 区间，判定为 **C-04 MID**，`main()` 按 MID 不计阻断 → 退出码为 `0`，断言必失败。已改为 `description_chars = 1100`（触发 **C-05 HIGH**，`>= DESC_HARD_LIMIT`），断言本身保持不变。

- [ ] **Step 1: 写 `test_gate_invariants.py`（第一部分：GI-1 确定性 / GI-2 排列稳定）**

```python
"""test_gate_invariants.py — RFC-0004 §3.7 的 GI-1~GI-6 回归门禁。

对象是 spec-evolution 自身：确定性、留白、锚点一致、退出码语义、只读。
"""

import hashlib
import importlib.util
import json
import re
from pathlib import Path

from conftest import build_repo, run_collect, run_judge

SPEC_DIR = Path(__file__).resolve().parents[1]
ANCHOR_RX = re.compile(r"\[(?:SKILL|REPO|RULE):[^\]]+\]")
PLACEHOLDER_RX = re.compile(r"\{\{(\w+)\}\}")
EXPECTED_PLACEHOLDERS = {
    "DATE", "REPO_HEAD", "SKILL_COUNT", "CRITERIA_COUNT",
    "VERDICT", "BLOCKER_SECTION", "FINDINGS_TABLE", "VERDICT_TABLE",
}


def _judge_module():
    spec = importlib.util.spec_from_file_location(
        "spec_evo_judge", SPEC_DIR / "scripts" / "judge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _facts(root: Path, *extra: str) -> dict:
    out = root / "_facts.json"
    proc = run_collect(root, "--no-gates", "--out", str(out), *extra)
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def _run(root: Path, facts: dict, tmp_path: Path, *extra: str):
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    js = tmp_path / "f.json"
    proc = run_judge(src, "--repo-root", str(root), "--json", str(js), *extra)
    data = json.loads(js.read_text(encoding="utf-8")) if js.exists() else None
    return proc, data


def _files(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_gi1_template_placeholders_are_exactly_the_rendered_set():
    tpl = (SPEC_DIR / "templates" / "evolution-report.md").read_text(encoding="utf-8")
    assert set(PLACEHOLDER_RX.findall(tpl)) == EXPECTED_PLACEHOLDERS


def test_gi1_no_unreplaced_placeholders_in_report(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    report = tmp_path / "report.md"
    proc, _ = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 0, proc.stderr
    assert "{{" not in report.read_text(encoding="utf-8")


def test_gi1_report_and_json_are_byte_identical_across_runs(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    src = root / "_in.json"
    src.write_text(json.dumps(facts, ensure_ascii=False), encoding="utf-8")
    outs = []
    for i in (1, 2):
        rep, js = tmp_path / f"r{i}.md", tmp_path / f"j{i}.json"
        proc = run_judge(src, "--repo-root", str(root),
                         "--report", str(rep), "--json", str(js))
        assert proc.returncode == 0, proc.stderr
        outs.append((rep.read_bytes(), js.read_bytes()))
    assert outs[0] == outs[1], "GI-1：同一 facts 必须产出逐字节相同的报告与 JSON"


def test_gi2_findings_are_stable_under_gate_input_permutation(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    facts["skills"][0]["paths"]["has_tests"] = False
    facts["gates"] = {
        "pytest": {"cmd": "c", "exit_code": 1, "summary": "s"},
        "audit_doc_health": {"cmd": "d", "exit_code": 1, "summary": "t"},
    }
    _, first = _run(root, facts, tmp_path)

    shuffled = json.loads(json.dumps(facts))
    shuffled["gates"] = dict(reversed(list(shuffled["gates"].items())))
    _, second = _run(root, shuffled, tmp_path)
    assert first == second, "GI-2：findings 排列不得依赖输入字典顺序"
```

- [ ] **Step 2: 追加第二部分（GI-3 锚点一致 / GI-4 留白）**

```python
def test_gi3_report_anchors_are_a_subset_of_findings_json(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    facts["skills"][0]["missing_surfaces"] = ["templates"]
    facts["gates"] = {"pytest": {"cmd": "python3 -m pytest skills/ -q",
                                 "exit_code": 1, "summary": "1 failed"}}
    report = tmp_path / "report.md"
    proc, data = _run(root, facts, tmp_path, "--report", str(report))
    assert proc.returncode == 1
    anchors = set(ANCHOR_RX.findall(report.read_text(encoding="utf-8")))
    assert anchors, "报告必须携带可核验锚点"
    assert anchors <= {f["anchor"] for f in data}, "GI-3：报告出现 finding 之外的锚点"


def test_gi3_anchor_validator_rejects_phantom_and_malformed(tmp_path):
    mod = _judge_module()
    root = build_repo(tmp_path / "repo")
    headings = ["# SYSTEM RULES", "## 3. 基础工程规范与防御底线",
                "### 质量门槛 (Definition of Done)"]
    accepted = ["[SKILL:demo/SKILL.md]", "[REPO:docs/index.md]", "[RULE:§3-质量门槛]"]
    rejected = ["[SKILL:nope/SKILL.md]", "[SKILL:demo/ghost.md]",
                "[SKILL:demo/SKILL.md:9999]", "[REPO:docs/ghost.md]",
                "[RULE:§3-不存在的条款]", "[RULE:§9-质量门槛]",
                "SKILL:demo/SKILL.md", "[SKILL:demo/]", ""]
    for anchor in accepted:
        assert mod.validate_anchor(anchor, root, headings) is None, anchor
    for anchor in rejected:
        assert mod.validate_anchor(anchor, root, headings) is not None, anchor


def test_gi4_template_verdict_section_is_blank():
    tpl = (SPEC_DIR / "templates" / "evolution-report.md").read_text(encoding="utf-8")
    _, sep, tail = tpl.partition("## 人类裁决 (Human Verdict)")
    assert sep, "模板必须含人类裁决区"
    assert "[x]" not in tail
    for token in ("BLOCKER", "HIGH", "MID"):
        assert token not in tail, f"GI-4：模板裁决区混入 {token}"


def test_gi4_rendered_verdict_rows_are_empty(tmp_path):
    root = build_repo(tmp_path / "repo")
    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 600
    facts["gates"] = {"pytest": {"cmd": "c", "exit_code": 1, "summary": "s"}}
    report = tmp_path / "report.md"
    _run(root, facts, tmp_path, "--report", str(report))
    _, sep, tail = report.read_text(encoding="utf-8").partition("## 人类裁决 (Human Verdict)")
    assert sep
    rows = [ln for ln in tail.splitlines() if ln.startswith("| F-")]
    assert len(rows) == 2, rows
    for ln in rows:
        assert ln.count("[ ] 采纳 / [ ] 驳回") == 1
        assert ln.endswith("| | | |"), ln
```

- [ ] **Step 3: 追加第三部分（GI-5 退出码 / GI-6 只读）**

```python
def test_gi5_exit_code_semantics(tmp_path):
    root = build_repo(tmp_path / "repo")
    clean, _ = _run(root, _facts(root), tmp_path)
    assert clean.returncode == 0, "无 HIGH/BLOCKER 必须退出 0"

    facts = _facts(root)
    facts["skills"][0]["description_chars"] = 1100  # C-05 HIGH
    blocking, _ = _run(root, facts, tmp_path)
    assert blocking.returncode == 1, "存在 HIGH 必须退出 1"

    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert run_judge(bad).returncode == 2, "输入非法必须退出 2"


def test_gi6_collector_is_read_only_without_gates(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = run_collect(root, "--no-gates", "--out", str(tmp_path / "facts.json"))
    assert proc.returncode == 0, proc.stderr
    assert _files(root) == before, "GI-6：采集改动了仓库"


def test_gi6_gates_run_without_leaving_artifacts(tmp_path):
    root = build_repo(tmp_path / "repo")
    before = _files(root)
    proc = run_collect(root, "--out", str(tmp_path / "facts.json"))
    assert proc.returncode == 0, proc.stderr
    after = _files(root)
    assert after == before, f"GI-6：门禁留下产物 {sorted(set(after) - set(before))}"
    assert not (root / ".pytest_cache").exists(), "GI-6：-p no:cacheprovider 未生效"


def test_gates_recorded_when_enabled(tmp_path):
    root = build_repo(tmp_path / "repo")
    out = tmp_path / "facts.json"
    proc = run_collect(root, "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    gates = json.loads(out.read_text(encoding="utf-8"))["gates"]
    assert set(gates) == {"pytest", "check_doc_links", "audit_doc_health", "cross_skill_links"}
    assert all(g["exit_code"] == 0 for g in gates.values()), gates
```

- [ ] **Step 4: 运行不变式测试**

```bash
python3 -m pytest skills/spec-evolution/tests/test_gate_invariants.py -q
```

期望：全绿。若 `test_gi6_gates_run_without_leaving_artifacts` 失败，**修正采集器的门禁调用**（补 `-B` / `-p no:cacheprovider`）而不是放宽断言。

- [ ] **Step 5: 运行技能全套测试**

```bash
python3 -m pytest skills/spec-evolution/ -q
```

期望：三个测试文件全绿（`test_demo.py` 为技能自证夹具，Task 1 已建）。

- [ ] **Step 6: 提交**

```bash
git add skills/spec-evolution/tests/test_gate_invariants.py
git commit -m "test(spec-evolution): GI-1~GI-6 门禁不变式回归

Task 4/7：确定性（逐字节可复现）、排列与输入顺序无关、报告锚点必为
findings 子集、裁决区永久留白、退出码三态语义、采集只读（含 pytest 无残留）。"
```

**Acceptance（Task 4）**：⑭ `python3 -m pytest skills/spec-evolution/ -q` 全绿；⑮ `test_gi6_gates_run_without_leaving_artifacts` 在真实执行四道门禁后仍断言无新文件。

---

#### Task 5: 架构设计书

**Files**
- Create: `docs/explanation/architecture/spec-evolution-design.md`

**Goal**：补上 C-02 要求的架构设计书，并对外解释「为什么是判定器而不是 LLM 评审」。

> **D-7（2026-10-12 P3 执行期修正）**：本 Task 的 Step 3「门禁复验」在**本 Task 内无法通过** —— 新增的设计书会成为索引孤儿，且 `docs/llms.txt` 与生成物不一致，`audit-doc-health.py` 必然 `REJECTED`。二者都要等 Task 6 完成注册与重生成才转 PASS。故 Step 3 的 ⑱ 实际验收点**顺延到 Task 6 之后**（Task 5 只保证 ⑯ 文件存在 与 ⑰ 断链 0）。

- [ ] **Step 1: 侦察既有设计书结构**

```bash
ls docs/explanation/architecture/
head -40 docs/explanation/architecture/goal-loop-design.md
```

- [ ] **Step 2: 写 `spec-evolution-design.md`**

**必须**模仿 `docs/explanation/architecture/goal-loop-design.md` 的章节骨架（标题层级、元信息块、后续阅读链接风格）。内容至少覆盖：

1. **问题域**：为什么「提示词/技能自身的演进」需要独立机制 —— 三门禁只判「产物正确性」，「存在性缺陷」是盲区。
2. **架构分层**：采集器（只回答是什么）/ 判据表（十条）/ 判定器（确定性映射）/ 报告模板（人类裁决留白）。
3. **关键决策与理由**：
   - 为什么**不做 LLM judge** —— 自评对上下文敏感、有讨好倾向、无对照基线，产出的是假设而非结论；锚点硬门禁把「幻觉」变成进程退出码。
   - 为什么**默认 fail-closed**（锚点不可解析即退出 2、拒绝写产物）。
   - 为什么**人类裁决区永久留白**（Reviewer ≠ Author）。
4. **与 `doc-governance` / `dual-round-review` / `goal-loop` 的边界**（RFC-0004 §3.8 职责边界表）。
5. **已知表达上限**（与 `references/checks-spec.md` §5 一致，不得夸大）。
6. **演进方向**：v1 覆盖 `skills/`；v2 才考虑根提示词与 `docs/` 制品。

- [ ] **Step 3: 门禁复验**

```bash
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py
```

期望：0 断链；PASS。

- [ ] **Step 4: 提交**

```bash
git add docs/explanation/architecture/spec-evolution-design.md
git commit -m "docs(spec-evolution): 架构设计书

Task 5/7：补 C-02 要求的架构设计书，说明分层、锚点硬门禁与
「不做 LLM judge」的决策理由。"
```

**Acceptance（Task 5）**：⑯ `test -f docs/explanation/architecture/spec-evolution-design.md` 成立；⑰ 断链扫描 0；⑱ `audit-doc-health.py` PASS。

---

#### Task 6: 全套注册面接入

**Files**
- Modify: `skills/_shared/tests/test_cross_skill_links.py`（`SKILL_NAMES` 追加 `"spec-evolution"`）
- Modify: `docs/index.md`（技能表新增行 + 版本号 + 修订历史）
- Modify: `README.md`（技能表新增行）
- Modify: `tools/skills-manager/collections/cr-agent-arsenal.json`（**补 F-9**：`clarification-protocol` 缺登记）
- Regenerate: `docs/llms.txt`

**Goal**：让 C-01~C-10 全部对本技能自身返回「已合格」——即用判定器给 spec-evolution 自己打分，结果必须是 CLEAN。

> **D-8（2026-10-12 P3 执行期修正）**：Step 4 写的版本号迁移 `V1.28.0` → `V1.29.0` 已过期 —— RFC-0004 受理流转时 `docs/index.md` 已升至 **V1.29.0**，故本次须 `V1.29.0` → **`V1.30.0`**（`trim-revision.py` 维持修订历史 ≤5 行）。同 Step 2 中「覆盖全部 8 个技能」按实际追加后的 `names` 长度为准。

- [ ] **Step 1: 追加 `SKILL_NAMES`**

在 `skills/_shared/tests/test_cross_skill_links.py:20-28` 的列表中追加 `"spec-evolution"`（保持既有排序风格）。

- [ ] **Step 2: 修 F-9 —— `clarification-protocol` 补登记**

读取 `tools/skills-manager/collections/cr-agent-arsenal.json`，在 `skills[].names` 中补入 `"clarification-protocol"`，使 `names` 覆盖全部 8 个技能（原 7 个 + `spec-evolution`）。**保持既有 JSON 缩进风格**，不改其它字段。

- [ ] **Step 3: `README.md` 技能表新增行**

在技能表中按既有格式新增 `spec-evolution` 行（沿用相邻行的列结构与链接风格）。

- [ ] **Step 4: `docs/index.md` 登记**

1. 技能表新增 `spec-evolution` 行；
2. 版本号 `V1.28.0` → `V1.29.0`；
3. 修订历史新增 V1.29.0 行；
4. 若 RFC-0004 行需反映状态变化，一并更新为 `Implemented`。

- [ ] **Step 5: 裁剪修订历史并重生成机器地图**

```bash
python3 skills/doc-governance/scripts/trim-revision.py --root docs/index.md --fix
python3 skills/doc-governance/scripts/generate-llms-txt.py --root docs --output docs/llms.txt --name=System
```

> **陷阱（身份写保护）**：`generate-llms-txt.py` 必须沿用既有身份 `--name=System`。以其它名字调用会被拒绝（`❌ 拒绝改写机器地图身份`），**不得**为绕过而删除 `docs/llms.txt`。

- [ ] **Step 6: 让本技能暴露给宿主**

```bash
python3 contexts/install.py
```

期望：`skills/spec-evolution` 经相对软链出现在 `.agents/skills/` 下。

- [ ] **Step 7: 用判定器自证 —— 这是本任务的核心验收**

```bash
python3 skills/spec-evolution/scripts/collect-facts.py --out /tmp/facts-self.json
python3 skills/spec-evolution/scripts/judge.py --facts /tmp/facts-self.json \
    --report docs/project/reviews/spec-evolution-selfcheck.md --json /tmp/findings-self.json
echo "exit=$?"
python3 - <<'PY'
import json
f = [x for x in json.load(open('/tmp/findings-self.json')) if x['skill'] in ('spec-evolution', 'clarification-protocol')]
print('spec-evolution 自身 + F-9 相关 findings =', len(f), f)
PY
```

期望：`spec-evolution` **零 finding**；`clarification-protocol` 仅剩既有已知项（本计划不修 F-3/F-6 等），且不再含 `C-07`（F-9 已修）。

> 报告落 `docs/project/reviews/` 供人类裁决 —— 该目录已存在且被文档门禁纳管。**裁决区必须留空**，由人类填写。

- [ ] **Step 8: 全门禁复验**

```bash
python3 -m pytest skills/ -q
python3 skills/doc-governance/scripts/check-doc-links.py --root docs
python3 skills/doc-governance/scripts/audit-doc-health.py
```

期望：`pytest` 全绿（基线 324 + 新增）；断链 0；健康度 PASS。

- [ ] **Step 9: 提交**

```bash
git add skills/_shared/tests/test_cross_skill_links.py docs/index.md README.md \
        tools/skills-manager/collections/cr-agent-arsenal.json docs/llms.txt \
        docs/project/reviews/spec-evolution-selfcheck.md skills/spec-evolution/tests/test_demo.py
git commit -m "feat(spec-evolution): 全套注册面接入 + F-9 收口

Task 6/7：SKILL_NAMES / README / docs/index.md / collections 四处登记，
重生成 llms.txt；修 F-9（clarification-protocol 集合缺登记）。
判定器自证 spec-evolution 零 finding。"
```

**Acceptance（Task 6）**：⑲ `python3 -m pytest skills/_shared/tests/test_cross_skill_links.py -q` 4 passed；⑳ `audit-doc-health.py` PASS 且断链 0；㉑ 判定器对 `spec-evolution` 返回零 finding。

---

