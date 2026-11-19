---
id: BK-0019
title: README 入口象限的索引自愈与健康评分语义对齐
type: Governance
status: active
priority: P3
trigger: null
created_at: '2026-10-09'
updated_at: '2026-10-09'
closed_at: null
resolution: null
destination: null
source:
- RFC-0003 Delta 审查 DR1-3（Delta R2 由 P2 降 P3：DA-4 已明令，缺披露非缺陷）
acceptance_criteria:
- 二选一并落地：(a) audit-doc-health 对 README 入口象限内文档豁免孤儿判定；或 (b) RFC/规范显式披露该评分代价与人工登记义务
---

## 1. 背景与问题陈述
DA-4 明令 README 入口象限不生成托管索引，但该象限内 scaffold 生成的文档因此永不登记，被 audit-doc-health.py 判为孤儿并扣分（隔离根实测 88.3/100、孤儿 1/3）。DA-4 原文只披露『链接需人工处理』，未披露评分后果，需在设计上决定：或补齐健康门禁语义（README 入口象限的文档视作已索引），或在规范中显式披露该代价。

## 2. 影响面与技术考量
- 涉及模块: skills/doc-governance/scripts/audit-doc-health.py（orphan_docs 判定）+ docs/GOVERNANCE.md
- 风险点: 豁免范围若写成「根级文件名白名单」会随象限结构演化而失效；若写成「任意层级都不判孤儿」则整项指标失能。取中间：**根级（\(<root>\) 直属）文档不参与**，深层叶子照旧判定

## 3. 验收准则与验证设计 (DoD)
- [x] (a)+(b) 同时落地：(a) 入口象限（根级文档）不参与孤儿判定；(b) GOVERNANCE 显式登记该边界与代价（根级真孤儿不再由该指标发现）

## 4. 实施去向与结项记录
### 实施记录（2026-11-19）

**为什么不是二选一，而是 (a)+(b)**：(a) 修掉「规范强制的结构被计为缺陷」这一评分错误；(b) 把由此产生的**新盲区**（根级真孤儿不再被发现）显式登记。只做 (a) 等于把一次扣分错误换成一次静默遗漏；只做 (b) 则让每个入口文档都顶着一条无法消除的扣分。

**实现**：`orphan_docs` 判定新增一条排除——`f.parent == root_dir` 的根级文档不参与；原有「导航入口文件名」与「归档区」两条排除保留。判定依据写在注释里（三条排除各有理由），避免后来者把它当冗余删掉。

**回归**：`test_entry_quadrant_docs_are_not_orphans` —— 根级 `QUICKSTART.md` + 深层 `how-to/orphan-leaf.md`，实测「孤立文档: 1/2」，即入口文档不计、深层叶子照计。删掉 `f.parent == root_dir` 一行，该断言即转红。

**规范同步**：GOVERNANCE §3 补「孤儿文档计分的边界」：说明豁免理由 + **已知代价**（根级真孤儿不再由该指标发现，改由链接完整率与人工评审覆盖）。

**复验**：doc-governance 151 passed / 7 skipped；真实仓库 audit PASS。
