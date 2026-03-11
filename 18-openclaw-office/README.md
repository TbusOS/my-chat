# OpenClaw Office — 3D 可视化 AI 前端

> 在浏览器中与 AI 进行 3D 可视化交互，连接 OpenClaw Gateway 获得完整 AI 能力

## 这是什么？

[OpenClaw Office](https://github.com/WW-AI-Lab/openclaw-office) 是 OpenClaw 的 3D 可视化前端界面。不同于传统聊天窗口，它提供沉浸式的 3D 交互体验，同时保留完整的 AI 对话能力。

它通过 WebSocket 连接 OpenClaw Gateway，获得：
- AI 对话（支持多模型切换）
- 工具调用（Tool Calling）
- 文件操作
- 网络搜索
- 所有 OpenClaw 支持的功能

## 架构

```
浏览器 (macOS)
┌──────────────────────────────┐
│  OpenClaw Office (:5180)     │
│  3D 渲染 + AI 对话界面        │
│                              │
│         WebSocket            │
└──────────────┬───────────────┘
               │ ws://<gateway-host>:18789
               ▼
┌──────────────────────────────┐
│  OpenClaw Gateway (:18789)   │
│  虚拟机 / 远程服务器           │
│                              │
│  ├── Ollama (本地模型)        │
│  ├── 云端 API (GPT/Claude/…) │
│  ├── 飞书 Bot                │
│  └── 工具 & 插件              │
└──────────────────────────────┘
```

**重要**：OpenClaw Office 是纯前端，运行在你的浏览器里（需要 GPU 渲染 3D）。Gateway 可以在本地、虚拟机或远程服务器上。

---

## 前置条件

- macOS（需要 GPU 渲染 3D 场景）或任何有 GPU 的电脑
- Node.js 18+（用于运行 Office Server）
- OpenClaw Gateway 已在运行（本地或远程）
- 知道 Gateway 的地址和 token

---

## 第一步：安装 OpenClaw Office

### 方法 A：npx 直接运行（推荐）

```bash
npx @ww-ai-lab/openclaw-office \
  --gateway ws://<gateway-host>:18789 \
  --token <your-gateway-token>
```

### 方法 B：全局安装

```bash
npm install -g @ww-ai-lab/openclaw-office

openclaw-office \
  --gateway ws://<gateway-host>:18789 \
  --token <your-gateway-token>
```

启动成功后访问：

```
http://127.0.0.1:5180
```

---

## 第二步：Gateway 配置

### 2.1 允许 Office 连接

Office 通过 WebSocket 连接 Gateway，需要在 Gateway 配置中添加 Office 的 origin。

编辑虚拟机上的 `~/.openclaw/openclaw.json`：

```json
{
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "http://127.0.0.1:5180",
        "http://<your-mac-ip>:5180"
      ],
      "dangerouslyDisableDeviceAuth": true
    },
    "auth": {
      "mode": "token",
      "token": "<your-gateway-token>"
    }
  }
}
```

**关键配置**：

| 字段 | 说明 |
|------|------|
| `allowedOrigins` | 添加 Office 的地址（`http://127.0.0.1:5180` 和 `http://<mac-ip>:5180`） |
| `dangerouslyDisableDeviceAuth` | 设为 `true`，否则 Office 无法通过 WebSocket 认证 |

修改后重启 Gateway：

```bash
~/services-stop.sh && ~/services-start.sh
```

### 2.2 网络连通性

Office 运行在 macOS 上，需要能访问 Gateway（虚拟机）。确认网络互通：

```bash
# 在 macOS 上测试
curl http://<gateway-host>:18789
# 应返回 OpenClaw Gateway 的响应
```

如果 Gateway 在虚拟机内只绑定了 localhost，需要确保 `bind: "lan"` 以便局域网访问。

---

## 第三步：已知问题和解决方案

### 3.1 浏览器直连问题（重要）

OpenClaw Office 的 Server 端和浏览器端连接 Gateway 的方式不同：

```
Office Server (Node.js)  ──ws──►  Gateway  ✅ 直接连接
浏览器 (Browser)          ──ws──►  Gateway  ❌ 可能被代理拦截
```

**问题**：某些版本的 Office Server 会给浏览器配置一个代理地址（`browserGatewayUrl`），而不是让浏览器直连 Gateway。如果代理不工作，浏览器会连接失败。

**解决方案**：修改 Office Server 源码，让浏览器直连 Gateway。

找到 Office Server 的入口文件：

```bash
# npx 方式安装的路径（哈希可能不同，用 find 查找）
find ~/.npm/_npx -name "openclaw-office-server.js" 2>/dev/null

# 全局安装的路径
find $(npm root -g) -name "openclaw-office-server.js" 2>/dev/null
```

编辑该文件，找到 `createRuntimeConfigScript` 函数中设置 `gatewayUrl` 的地方：

```javascript
// 修改前（浏览器走代理）：
gatewayUrl: config.browserGatewayUrl

// 修改后（浏览器直连 Gateway）：
gatewayUrl: config.gatewayUrl
```

> **注意**：这是对 node_modules 的直接修改。每次 `npx` 更新或重新安装后，需要重新修改。

### 3.2 验证连接

修改后重启 Office：

```bash
npx @ww-ai-lab/openclaw-office \
  --gateway ws://<gateway-host>:18789 \
  --token <your-gateway-token>
```

浏览器打开 `http://127.0.0.1:5180`，检查：

1. 3D 场景正常加载
2. 能发送消息并收到 AI 回复
3. 浏览器开发者工具 → Network → WS 标签中，能看到 WebSocket 连接到 Gateway

---

## 第四步：日常使用

### 4.1 启动流程

```bash
# 1. 确认 Gateway 在运行（虚拟机/远程服务器上）
ssh <your-vm-user>@<your-vm-ip> "~/services-status.sh"

# 2. 启动 Office（macOS 上）
npx @ww-ai-lab/openclaw-office \
  --gateway ws://<gateway-host>:18789 \
  --token <your-gateway-token>

# 3. 打开浏览器
open http://127.0.0.1:5180
```

### 4.2 创建启动脚本（可选）

创建一个快捷脚本简化启动：

```bash
cat > ~/start-office.sh << 'SCRIPT'
#!/bin/bash
# OpenClaw Office 启动脚本

GATEWAY_HOST="${OPENCLAW_GATEWAY:-<gateway-host>}"
GATEWAY_PORT="${OPENCLAW_PORT:-18789}"
GATEWAY_TOKEN="${OPENCLAW_TOKEN:-<your-token>}"

echo "Connecting to Gateway: ws://${GATEWAY_HOST}:${GATEWAY_PORT}"

npx @ww-ai-lab/openclaw-office \
  --gateway "ws://${GATEWAY_HOST}:${GATEWAY_PORT}" \
  --token "${GATEWAY_TOKEN}"
SCRIPT

chmod +x ~/start-office.sh
```

使用时：

```bash
# 默认配置
~/start-office.sh

# 或通过环境变量覆盖
OPENCLAW_GATEWAY=192.168.1.100 OPENCLAW_TOKEN=abc123 ~/start-office.sh
```

### 4.3 使用环境变量管理配置

创建 `~/.openclaw-office.env`（不要提交到 git）：

```bash
OPENCLAW_GATEWAY=<gateway-host>
OPENCLAW_PORT=18789
OPENCLAW_TOKEN=<your-token>
```

在启动脚本中加载：

```bash
source ~/.openclaw-office.env
~/start-office.sh
```

---

## 与 Control UI 对比

| | Control UI | OpenClaw Office |
|---|---|---|
| 类型 | 管理面板 | AI 交互前端 |
| 主要用途 | 运维监控 | 与 AI 对话 |
| 渲染 | 普通网页 | 3D 场景（需要 GPU） |
| 访问方式 | `http://localhost:18789` | `http://127.0.0.1:5180` |
| 运行位置 | Gateway 内置 | 独立 Node.js 服务 |
| 适合场景 | 查看状态、管理配置 | 日常 AI 交互 |

两者可以同时使用，互不影响。

---

## 常见问题

### Q: 3D 场景加载很慢或卡顿

- 确认 GPU 可用（macOS 上 Metal 通常自动启用）
- 关闭浏览器的其他 GPU 密集标签页
- 降低浏览器窗口大小可以减轻 GPU 负担

### Q: 能发消息但 AI 不回复

1. 检查 Gateway 日志：`tail -f ~/.openclaw/logs/gateway.log`（在虚拟机上）
2. 确认模型服务正常（Ollama 或云端 API）
3. 如果用 Ollama，检查是否正常运行：`curl http://<ollama-host>:11434/api/tags`

### Q: WebSocket 连接失败

1. 检查 `allowedOrigins` 是否包含 Office 的地址
2. 检查 `dangerouslyDisableDeviceAuth` 是否为 `true`
3. 确认 Gateway 端口可达：`curl http://<gateway-host>:18789`
4. 如果改过源码，确认修改正确（`gatewayUrl` 而非 `browserGatewayUrl`）

### Q: npx 更新后 patch 丢失

npx 缓存机制可能在更新时重建 node_modules，导致之前的修改丢失。解决方案：

1. **每次启动前检查**：在启动脚本中加入自动 patch 逻辑
2. **使用全局安装**：`npm install -g` 更新频率更低
3. **关注官方修复**：在 [GitHub Issues](https://github.com/WW-AI-Lab/openclaw-office/issues) 中跟进，未来版本可能原生支持直连

自动 patch 脚本示例：

```bash
#!/bin/bash
# auto-patch-office.sh — 自动修复 Office 直连问题

OFFICE_SERVER=$(find ~/.npm/_npx -name "openclaw-office-server.js" 2>/dev/null | head -1)

if [ -z "$OFFICE_SERVER" ]; then
  echo "Office server not found, will be downloaded on first run"
  exit 0
fi

if grep -q "browserGatewayUrl" "$OFFICE_SERVER"; then
  echo "Patching Office server for direct gateway connection..."
  sed -i.bak 's/config\.browserGatewayUrl/config.gatewayUrl/g' "$OFFICE_SERVER"
  echo "Patched: $OFFICE_SERVER"
else
  echo "Already patched or no patch needed"
fi
```

### Q: 用浏览器地址栏要输 127.0.0.1 还是 localhost？

建议用 `127.0.0.1`。某些浏览器对 `localhost` 有特殊处理（如 Chrome 强制 HTTPS），可能导致连接问题。

---

## 安全建议

1. **Office 只绑定 localhost** — 默认行为，不需要改
2. **Gateway token 不要硬编码** — 用环境变量或配置文件管理
3. **不要把 `.openclaw-office.env` 提交到 git**
4. **公网访问走 Cloudflare Tunnel + Access** — 参考 [16-sky-chat](../16-sky-chat/) 的 Cloudflare 方案
5. **定期更新 Office** — `npm update -g @ww-ai-lab/openclaw-office`

---

## License

MIT
