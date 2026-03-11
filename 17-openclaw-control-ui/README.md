# OpenClaw Control UI — 网页管理面板

> 通过浏览器管理你的 OpenClaw Gateway：查看状态、管理对话、监控日志

## 这是什么？

OpenClaw 内置了一个 **Control UI** 网页管理面板，可以通过浏览器：

- 查看 Gateway 运行状态
- 查看和管理对话历史
- 监控连接的 Bot 和设备
- 管理模型配置
- 查看实时日志

## 架构

```
浏览器 (macOS / 任意设备)
    │
    │  http://localhost:18789/
    │
    ▼
┌─────────────────────────────┐
│  SSH Tunnel / 直连           │
│  (端口转发到 Gateway)        │
└──────────────┬──────────────┘
               │
     ┌─────────▼──────────┐
     │  OpenClaw Gateway  │
     │  虚拟机 :18789      │
     │                    │
     │  Control UI (内置)  │
     │  WebSocket API     │
     └────────────────────┘
```

**重要**：Control UI 使用 device identity 校验，**必须通过 localhost 访问**。直接用 IP 地址访问会被拦截。

---

## 前置条件

- OpenClaw Gateway 已在虚拟机中运行
- 能够 SSH 到虚拟机
- 知道 Gateway 的 token（查看方法见下文）

---

## 第一步：确认 Gateway 配置

### 1.1 查看 Gateway 状态

```bash
# SSH 进入虚拟机
ssh <your-vm-user>@<your-vm-ip>

# 检查 Gateway 是否运行
ps aux | grep openclaw

# 或使用状态脚本（如果已配置）
~/services-status.sh
```

### 1.2 确认 Control UI 已启用

编辑 `~/.openclaw/openclaw.json`，确保 gateway 配置中包含 controlUi：

```json
{
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789"
      ]
    },
    "auth": {
      "mode": "token",
      "token": "<your-gateway-token>"
    }
  }
}
```

### 1.3 获取 Gateway Token

```bash
# 方法一：运行命令
openclaw token

# 方法二：查看配置文件
cat ~/.openclaw/openclaw.json | grep -A2 '"auth"'
```

---

## 第二步：访问 Control UI

### 方法 A：SSH 端口转发（推荐）

适用于 Gateway 运行在虚拟机或远程服务器上。

```bash
# 在本地（macOS）终端运行：
ssh -N -L 18789:127.0.0.1:18789 <your-vm-user>@<your-vm-ip>

# -N: 不执行远程命令，只做端口转发
# -L: 将本地 18789 端口转发到虚拟机的 127.0.0.1:18789
```

然后浏览器打开：

```
http://localhost:18789/
```

输入 Gateway token 即可登录。

> **提示**：命令会阻塞终端。可以加 `-f` 参数让它在后台运行：
> ```bash
> ssh -fN -L 18789:127.0.0.1:18789 <your-vm-user>@<your-vm-ip>
> ```

### 方法 B：虚拟机内浏览器

如果虚拟机有桌面环境，可以直接在虚拟机里打开浏览器访问：

```
http://localhost:18789/
```

### 方法 C：禁用设备认证（不推荐）

如果你在安全的内网环境中，可以禁用设备认证以直接用 IP 访问：

```json
{
  "gateway": {
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "http://<your-vm-ip>:18789",
        "http://<your-mac-ip>:18789"
      ],
      "dangerouslyDisableDeviceAuth": true
    }
  }
}
```

修改后重启 Gateway：

```bash
~/services-stop.sh && ~/services-start.sh
```

> **警告**：`dangerouslyDisableDeviceAuth: true` 会跳过设备身份校验。只在你信任网络中的所有设备时使用。

---

## 第三步：使用 Control UI

### 3.1 登录

打开 `http://localhost:18789/` 后，输入 Gateway token 登录。

### 3.2 主要功能

| 功能 | 说明 |
|------|------|
| **Dashboard** | Gateway 概览：运行时间、连接数、消息统计 |
| **Conversations** | 查看和管理对话历史 |
| **Devices** | 已连接的设备和 Bot 列表 |
| **Models** | 当前可用的模型和 Provider |
| **Logs** | 实时查看 Gateway 日志 |

### 3.3 管理对话

在 Conversations 面板中可以：
- 查看所有对话的历史记录
- 按时间、模型、渠道（飞书/Office/API）筛选
- 查看每条消息的 token 用量和耗时
- 删除不需要的对话

### 3.4 监控模型状态

在 Models 面板中可以看到：
- 已配置的所有 Provider 和模型
- 每个模型的调用次数和平均延迟
- 模型是否在线可用

---

## SSH 端口转发进阶

### 自动重连

使用 `autossh` 保持连接稳定（断线自动重连）：

```bash
# 安装
brew install autossh  # macOS
sudo apt install autossh  # Ubuntu

# 启动（自动重连）
autossh -M 0 -fN -L 18789:127.0.0.1:18789 <your-vm-user>@<your-vm-ip>
```

### SSH Config 简化命令

在 `~/.ssh/config` 中添加：

```
Host openclaw-vm
    HostName <your-vm-ip>
    User <your-vm-user>
    LocalForward 18789 127.0.0.1:18789
```

之后只需：

```bash
ssh -fN openclaw-vm
```

### 同时转发多个端口

如果你还需要访问 OpenClaw Office 或其他服务：

```bash
ssh -fN \
  -L 18789:127.0.0.1:18789 \
  -L 5180:127.0.0.1:5180 \
  <your-vm-user>@<your-vm-ip>
```

---

## 通过 Cloudflare Tunnel 远程访问（可选）

如果你想从外网访问 Control UI，可以结合 Cloudflare Tunnel：

```yaml
# ~/.cloudflared/config.yml
ingress:
  - hostname: control.your-domain.com
    service: http://localhost:18789
  - service: http_status:404
```

**务必配合 Cloudflare Access 做认证**，否则任何人都能访问你的管理面板。

---

## 常见问题

### Q: 打开页面显示"离线"或空白

- 确认你是通过 `localhost` 而不是 IP 地址访问的
- 确认 SSH 端口转发正在运行
- 确认 Gateway 正在运行：`ps aux | grep openclaw`

### Q: Token 在哪里找？

```bash
# 在虚拟机上运行
openclaw token

# 或查看配置文件
grep -A2 '"token"' ~/.openclaw/openclaw.json
```

### Q: SSH 转发经常断开

使用 `autossh` 自动重连（见上文），或在 `~/.ssh/config` 中配置 keepalive：

```
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### Q: 可以不用 SSH 转发直接访问吗？

可以，但需要设置 `dangerouslyDisableDeviceAuth: true` 并把你的 IP 加入 `allowedOrigins`。这在安全的局域网内可以接受，**不建议在公网环境使用**。

### Q: Control UI 支持手机访问吗？

支持，Control UI 是响应式网页。但手机需要通过某种方式连到 localhost:18789（如 VPN 或 Cloudflare Tunnel + Access）。

---

## 安全建议

1. **不要把 Gateway 端口暴露到公网** — 始终通过 SSH 转发或 Cloudflare Tunnel 访问
2. **使用强 token** — `openssl rand -hex 24` 生成
3. **定期轮换 token** — 修改 openclaw.json 中的 token 并重启 Gateway
4. **限制 allowedOrigins** — 只添加你实际使用的地址
5. **公网访问必须配 Cloudflare Access** — 绝不裸露 Control UI 到互联网

---

## License

MIT
