# 实战案例 1: 浅层修补（打布丁）识别与阻断

## 1. 场景背景与代码 Diff
在用户登出流程中，前端偶尔报错 `Uncaught TypeError: Cannot read properties of undefined (reading 'token')`。
开发者提交的候选修复：

```diff
--- a/src/auth/session.ts
+++ b/src/auth/session.ts
@@ -25,5 +25,9 @@ export function clearUserSession() {
-  const token = getSession().token;
-  apiClient.revokeToken(token);
-  localStorage.removeItem("session");
+  try {
+    const session = getSession();
+    if (session?.token) {
+      apiClient.revokeToken(session.token);
+    }
+  } catch (e) {
+    // 忽略异常，静默跳过
+  }
+  localStorage.removeItem("session");
```

---

## 2. 第一轮红队审查 (Round 1 Output)
* **本质溯源**：
  * 该改动属于典型的**浅层打布丁 (Palliative Patching)**。
  * `getSession()` 为什么会返回 `undefined` 或抛出异常？排查发现是由于前端状态机存在并发登出竞态，上游已经提前将内存状态置为 null，但未取消挂起的路由监听器。
  * 外层强加 `try/catch` 并吞掉错误，导致 `revokeToken` 在异常时没有真正告知后端销毁服务端会话，导致后端会话残留，产生未授权安全漏洞。
* **判定候选**：🔴 P1 阻断项（契约破坏与会话残留）。

---

## 3. 第二轮元审判裁决 (Round 2 Output)
* **元质询 (Meta-Challenges)**：
  * R1 攻击有效。经查证代码库上下文，`clearUserSession` 必须确保后端会话注销成功，否则 Token 仍处于有效生命周期内。
  * `try/catch` 吞异常确实掩盖了并发重复调用的状态机时序问题。
* **最终裁决**：
  * 🔴 **P1 阻断项**：静默吞异常导致会话撤销静默失败。打回重构，必须重构为原子状态转换，并在底层处理防重入。
