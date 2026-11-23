# Wave 0 止血修复计划：全仓现红测试与已实证源码级真 Bug 清零

> **文档控制信息**
> - **文档标识**: PLAN-WAVE0-STABILIZATION-2026
> - **当前版本**: V1.0.0
> - **文档状态**: Active
> - **生效日期**: 2026-11-23
> - **执行通道**: **Maintenance-Patch（存量维护通道）** —— 公共契约不变，定向修复已实证的真 Bug、现红测试与敏感路径/失实文档，不扩展接口语义
> - **分支**: `fix/wave0-skill-bugs-and-red-tests`（基于 `master` `7a91c22`）
> - **依据总纲**: [2026-11-23-arsenal-skills-portfolio-overview.md](../../explanation/analysis/2026-11-23-arsenal-skills-portfolio-overview.md)

---

### Active Checkpoint

- **当前阶段**: `DONE`（已完成交付并取得独立红队 Zero Blockers 终审）
- **状态**: 已完成
- **已完成**: 基线复现 → 三路子智能体 W0-A/B/C 并行修复 → 主智能体 Zero-Trust Diff 复核与全仓 `pytest skills/ -q`（631 passed / 0 failed） → 独立红队 Light 定向单轮审查（Blockers=0，P2=2 / P3=4；审查归档见 [README.md](../reviews/2026-11-23-wave0-skill-bugs-stabilization/README.md)） → 归档门禁与全量文档门禁验证通过
- **遗留非阻断项**: R1-1 / R1-2（P2）及 R1-3~R1-6（P3）不阻塞交付，记入 Wave 2 对应技能 V3.0 重构顺手收口

---

## 1. 修复现象与根因清单（三路无冲突执行包）

### W0-A：`dual-round-review` 现红测试 + 隐藏脚本 Bug + 跨技能缺参
1. `prepare-review-context.py:358` `_UNIT_RX` 强求行首 `>`，但自身 `:500` 及 17/17 真实归档均无 `>`，导致 `_read_unit()` 全返回 `None` → 兼容 `(?:>\s*)?` 并补真实无 `>` 回归单测。
2. `check-review-report.py:216` `_NON_FILE_CHARS_RE.sub("", raw_file)` 把台账内 Markdown 链接 `[f](./f)` 拼坏为 `f.f` → 正确提取链接目标 basename 并补回归单测。
3. `test_artifact_schema_contract.py::test_existing_archives_all_pass_gate` 因 2026-11-22 4 个 Write-Once 历史归档（正文不可篡改且缺五区块标题）导致仓库 `pytest` 现红 → 不篡改历史报告正文、不弱化未来门禁；在测试中显式冻结登记 4 个历史遗留项（只降不升），强断言其余全部 13+ 既有及新增归档 100% `rc=0`。
4. `skills/dual-round-review/SKILL.md:123` 调用 `check-qa-report.py` 漏写必选位置参数 `<报告文件>` → 补齐 `<报告文件>`。

### W0-B：`doc-governance` 7 处已实证源码 Bug 与漂移
1. `audit-doc-health.py:1207-1233` `--max-doc-bytes` / `--max-doc-line` 未透传进 `audit_health()` → 透传并补单测。
2. `audit-doc-health.py:333-343` `_size_docs()` 未按 `docs/GOVERNANCE.md:142` 豁免 `reference/articles/**` → 补齐豁免并补单测。
3. `scaffold-doc.py` L503 仍推荐已废弃 `scaffold-doc.sh` → 改为 `.py`；修复 `--help` 行为与 `--lang` 死参数（不破坏既有 L4 兼容壳测试）。
4. `check-all.py` docstring「五道门禁」→「六道门禁」；L60 版本一致失败修复建议从错误的 `trim-revision.py --fix` 改为同步控制头与修订表首行版本。
5. `references/change-impact-matrix.md:4,34` 版本号漂移（`V1.3.1` → `V1.4.0`）与「第 7 行」→「第 8 行」；`references/backlog-specification.md:77` 清理 `file:///` 示例；`docs/explanation/architecture/doc-governance-design.md` 清理 `/home/hui/workspace/projects/cr-public-skills` 旧仓绝对路径。

### W0-C：`taste-driven-designer` + `frontend-qa-gate` + `goal-loop` 缺陷与敏感信息止血
1. `skills/taste-driven-designer/scripts/generate-seed.py:128-138` Park-Miller LCG 初态 `0` 导致 `-s A` / `-s AAAA` 全输出 `A`（零熵死锁）→ 哈希后若 `state == 0` 钳位为非零（如 `1`），补 `-s A` / `-s AAAA` 非全 `A` 回归单测。
2. `skills/taste-driven-designer/references/ai-tells-audit.md:83` 清除已废止的「Critic 终分」旧口径；`templates/design-brief-template.md:30-31` 清除硬编码个人真名 `王辉`。
3. `docs/explanation/architecture/taste-driven-designer-design.md` 恢复 `ef7e325~1` 被误覆写的真实 V1.1.0 内容并升版为 V1.2.0（纠正「本技能没有自动化测试」失实断言，更新 `.py` 与 `frontend-qa-gate` 对接）。
4. `docs/explanation/architecture/goal-loop-design.md:10` 清除个人绝对路径 `/home/hui/workspace/projects/faceFusionCpp/...`。
5. `skills/taste-driven-designer/tests/test_gate_contract.py:168` 与 `skills/frontend-qa-gate/tests/test_qa_gate_contract.py:44` 内联跨技能白名单补齐 `clarification-protocol`（对齐 `skills/_shared/cross-skill-link-policy.json`）。

---

## 2. 测试策略与级别裁定

- **改动风险定级**: MEDIUM（跨 5 个技能目录的定向存量 Bug 修复，契约不变）
- **强制执行级别**: L0 语法检查 + L1 全仓技能单测（`python3 -m pytest skills/ -q`）+ L-Doc 全套治理门禁（`python3 skills/doc-governance/scripts/check-all.py --full`）
- **独立审查门禁**: 定向单轮红队对抗审查（Diff 边界锁，Zero Blockers 方可收口）
