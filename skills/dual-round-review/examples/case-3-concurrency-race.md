# 实战案例 3: 隐蔽异步竞态与资源泄漏识别（坐实阻断项）

## 1. 场景背景与代码 Diff
开发者在 React/TS 组件中新增了搜索输入联想功能：

```diff
--- a/src/components/SearchBox.tsx
+++ b/src/components/SearchBox.tsx
@@ -10,6 +10,12 @@ export function SearchBox() {
   const [query, setQuery] = useState("");
   const [results, setResults] = useState<string[]>([]);
 
+  useEffect(() => {
+    if (query.trim()) {
+      searchApi(query).then((data) => setResults(data));
+    }
+  }, [query]);
+
   return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
 }
```

---

## 2. 第一轮红队审查 (Round 1 Output)
* **红队攻击推演**：
  * **竞态覆盖 (Race Condition)**：若用户快速输入 `cat` 紧接着输入 `dog`，`searchApi('cat')` 的网络响应延迟可能大于 `searchApi('dog')`。结果导致用户输入框显示 `dog`，但列表最终被延迟到达的 `cat` 搜索结果覆盖！
  * **卸载后异步状态更新 (Memory/State Leak)**：若组件在请求未完成时被卸载，触发对已卸载组件的 `setState`。
* **判定候选**：🔴 P1 阻断项（竞态失序与悬挂）。

---

## 3. 第二轮元审判裁决 (Round 2 Output)
* **元质询 (Meta-Challenges)**：
  * **去伪存真**：经查 `searchApi` 为直接 Axios 网络调用，未在底层做任何取消机制。时序推演完全成立，在线上弱网或高延迟环境下极其容易复现脏数据覆盖。
  * **修复方案评估**：无需引入复杂的外部 RxJS 流库（避免过度工程），使用 React 原生 `useEffect` 清理函数 + `AbortController` 或布尔标志位即可 5 行代码优雅精准解决。
* **最终裁决**：
  * 🔴 **P1 阻断项**：竞态缺陷坐实。打回实施精准修复（增加 AbortController 取消处理），修复后重新进入双轮审查。
