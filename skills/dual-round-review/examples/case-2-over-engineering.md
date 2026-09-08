# 实战案例 2: 过度工程与纸上谈兵甄别（驳回项）

## 1. 场景背景与代码 Diff
开发者为格式化金额添加了一个简单、完备的纯函数：

```diff
--- a/src/utils/format.ts
+++ b/src/utils/format.ts
@@ -0,0 +1,7 @@
+export function formatCurrency(amountInCents: number, currency: string = "CNY"): string {
+  if (!Number.isFinite(amountInCents)) {
+    throw new TypeError("amountInCents must be a finite number");
+  }
+  return new Intl.NumberFormat("zh-CN", { style: "currency", currency }).format(amountInCents / 100);
+}
```

---

## 2. 第一轮红队审查 (Round 1 Output)
* **红队攻击意见**：
  * 该实现缺乏灵活性。目前仅硬编码了 `"zh-CN"` locale，无法支持跨国国际化。
  * 建议引入抽象工厂模式与插件式汇率转换策略类：`CurrencyFormatterFactory`、`LocaleProvider` 和 `ExchangeRateProvider`。
* **判定候选**：🔴 P1 阻断项（缺乏多币种扩展性）。

---

## 3. 第二轮元审判裁决 (Round 2 Output)
* **元质询 (Meta-Challenges)**：
  * **过度工程 (Anti-Overengineering & YAGNI 校验)**：
    * 查阅当前系统需求规格书（Spec），系统仅在中国大陆区域为科研人员提供国内报销计费服务，完全没有多语言与动态汇率需求。
    * 引入 `CurrencyFormatterFactory` 和插件体系将使一个 7 行的纯函数膨胀为 100+ 行的代码，增加了不必要的间接层与维护成本。
  * **原代码健壮性核查**：
    * 原函数有明确的参数校验，使用了成熟的 ECMAScript 标准 `Intl.NumberFormat`，单元测试 100% 覆盖。
* **最终裁决**：
  * ⚪ **驳回项 (Dismissed)**：R1 属于典型的投机性泛化（Speculative Generality）与过度工程。驳回 R1 意见，代码无需改动，直接准予交付放行。
