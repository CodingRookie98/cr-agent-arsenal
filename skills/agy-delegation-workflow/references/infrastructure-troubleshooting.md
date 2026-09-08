# agy 基础设施排错与假失败诊断指南 (Infrastructure Troubleshooting)

本指南汇总了在 Linux / WSL 环境下驱动 `agy`（Antigravity CLI）后台执行智能体时的高频基础设施故障（网络、代理、认证超时、假失败）与诊断对策。

---

## 1. WSL 代理污染与区域限制 (Proxy Pollution & Region Blocks)

### 现象
`agy -p` 执行失败并报错：
* `Error: Agent execution terminated due to error.`
* 日志（`~/.gemini/antigravity-cli/log/cli-*.log`）包含：
  * `proxyconnect tcp: dial tcp ...: connect: connection refused`
  * `User location is not supported for the API use`

### 根因剖析
* `agy` 基于 Go 编写，其 HTTP 客户端会自动读取环境变量 `HTTPS_PROXY`、`HTTP_PROXY` 等。
* 在 WSL 环境中，Windows 宿主机即使开启了 TUN 模式代理，旧终端会话遗留的代理环境变量仍会导致 Go 客户端尝试连接死端口而报 `connection refused`。
* 此外，Google CloudCode API（`daily-cloudcode-pa.googleapis.com`）对请求 IP 的地理位置有合规限制。

### 标准修复命令
在分发任何 `agy` 任务前，**必须显式清理所有代理环境变量**：
```bash
unset HTTPS_PROXY HTTP_PROXY http_proxy https_proxy ALL_PROXY all_proxy; \
agy -p "$(cat .agy-tasks/task.md)" \
  --model 'Gemini 3.8 Flash (High)' \
  --dangerously-skip-permissions \
  --print-timeout 20m
```

---

## 2. OAuth EOF 报错但代码已写入 (Silent Landing 假失败)

### 现象
`agy` 进程退出并返回非 0 退出码，报错信息显示：
* `Eligibility check failed: Get "https://www.googleapis.com/oauth2/v2/userinfo": EOF`
* `Get "https://lh3.googleusercontent.com/...": EOF`

### 根因剖析
`agy` 在执行任务时是**流式增量写入文件**的。如果代码和单测已经编写完毕，但在最后的汇报或会话清理阶段，Google OAuth Token 刷新发生网络波动，`agy` 会抛出退出错误。此时**核心代码工作实际上已经圆满完成**，属于“汇报阶段假失败”。

### 强制排查 SOP（严禁立即重跑或直接判定失败！）
1. **核对文件是否存在**：
   ```bash
   git status -s
   ls -la <任务指定的目标代码与测试文件>
   ```
2. **直接运行验收测试**：
   ```bash
   # 前端
   npx vitest run <目标测试文件>
   # 后端
   go test ./... -run "TestFeature" -v
   ```
3. **裁决原则**：
   * 若目标文件已存在且测试通过 ➔ **判定任务实质成功**，直接进入前台审查阶段，无需任何重试或降级！
   * 若目标文件缺失或不完整 ➔ 判定为真实故障，进入重试或 3-Tries 降级链。

---

## 3. 进程退出后文件延迟落盘 (Delayed File Landing)

### 现象
后台 `agy` 进程刚退出的 1~2 秒内，`git status` 显示工作区依然为 clean（没有任何文件改动），但数分钟后重新检查，所有期望的代码文件完整呈现。

### 根因剖析
WSL2 跨文件系统（如从 Windows 挂载盘或高 I/O 缓冲区）在多进程异步刷新时存在落盘时延。

### 防御对策
* 监控到 `agy` 进程退出后，若首发 `git status` 为空，**不要急于判定失败或立即发起重复委派**；
* 等待 5~10 秒后二次运行 `git status` 并检查文件的 `mtime`（修改时间）；
* 检查是否伴随产生了 `IMPLEMENTATION_PLAN.md` 或 `task.md`（若有，前台必须立即删除，捍卫职责边界）。

---

## 4. 20 分钟超时处理：代码已完成但单测未写完 (Mid-Batch Timeout)

### 现象
`agy` 执行耗尽 `--print-timeout 20m`，报错 `Error: timeout waiting for response`。通常由于 `agy` 在探索阶段执行了全库大范围 `grep` 陷入超时卡顿。

### 处置原则
1. **检查落地资产**：`git status --short` 查看业务代码是否已编写完成；
2. **验证业务代码能否编译**：`npx tsc --noEmit` 或 `go build ./...`；
3. **前台补写测试（更快更稳）**：
   * 如果生产代码已编译通过且逻辑清晰，前台智能体直接自行补齐单元测试；
   * **严禁完整重新发起 agy 重跑**，避免其再次掉入全库扫描超时的泥潭。
