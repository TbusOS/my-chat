# 在 Mac 虚拟机（Ubuntu）上部署飞书 AI Bot

> 在 macOS 的 Parallels 虚拟机中运行两个飞书聊天机器人，共用 macOS 上的 Ollama 大模型

## 这是什么？

我们要在 Mac 上搭建两个**飞书 AI 机器人**，在飞书里直接和 AI 聊天：

| Bot | 说明 | 使用模型 |
|-----|------|----------|
| **Nanobot** | 自己写的 Python 飞书 Bot | qwen2.5:7b |
| **OpenClaw** | 开源 AI Gateway，功能丰富 | gemma2:9b |

两个 Bot 都运行在 **Ubuntu 虚拟机** 中，但大模型跑在 **macOS 主机** 的 Ollama 上（利用 Mac 的 GPU 加速）。

## 整体架构

```
┌─────────────────────────────────────────────────────┐
│  飞书服务器（云端）                                    │
│  ← WebSocket 长连接（无需公网 IP）→                    │
└──────────┬──────────────────────┬────────────────────┘
           │                      │
     ┌─────▼──────┐        ┌─────▼──────┐
     │  Nanobot   │        │  OpenClaw  │
     │  (Docker)  │        │  (Node.js) │
     │ Python Bot │        │  Gateway   │
     └─────┬──────┘        └─────┬──────┘
           │                      │
           │   Ubuntu 虚拟机 (VM)  │
           └──────────┬───────────┘
                      │ HTTP API
              ┌───────▼───────┐
              │    Ollama     │
              │  macOS 主机    │
              │  (Apple GPU)  │
              │ qwen2.5 / gemma2
              └───────────────┘
```

**为什么这样设计？**
- Ollama 跑在 macOS 上，可以用 Apple Silicon 的 GPU 加速
- Bot 跑在虚拟机里，与主机隔离更安全
- 使用 WebSocket 长连接，不需要公网 IP 和域名

## 前置条件

- macOS + Parallels Desktop（装好 Ubuntu 24.04 虚拟机）
- 飞书开放平台账号（需要创建两个应用）
- 基本的终端操作能力

---

## 第一步：macOS 主机 — 安装 Ollama

### 1.1 安装 Ollama

去 [ollama.com](https://ollama.com) 下载 macOS 版本，安装后打开。

### 1.2 下载模型

打开 macOS 终端，下载两个模型：

```bash
# 给 Nanobot 用的模型（4.7GB）
ollama pull qwen2.5:7b

# 给 OpenClaw 用的模型（5.4GB）
ollama pull gemma2:9b
```

### 1.3 让虚拟机能访问 Ollama

Ollama 默认只监听 `127.0.0.1`，虚拟机连不上。需要设置环境变量让它监听所有网络接口：

```bash
# 在 macOS 终端执行
launchctl setenv OLLAMA_HOST "0.0.0.0"
```

然后**重启 Ollama**（点击菜单栏的 Ollama 图标 → Quit → 重新打开）。

### 1.4 找到 macOS 的虚拟机网络 IP

```bash
# 在 macOS 终端执行
ifconfig | grep "inet " | grep -v 127.0.0.1
```

找到 Parallels 虚拟网络的 IP 地址（通常是 `10.211.55.x`），记下来，后面要用。

### 1.5 验证

```bash
# 在虚拟机终端测试（把 <你的Mac IP> 换成上一步找到的地址）
curl http://<你的Mac IP>:11434/api/tags
```

能返回 JSON 就说明连通了。

---

## 第二步：飞书开放平台 — 创建应用

需要创建 **两个应用**，一个给 Nanobot，一个给 OpenClaw。

### 2.1 创建应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用名称（如 "Nanobot" 和 "OpenClaw"）
4. 创建完成后，记下 **App ID** 和 **App Secret**

### 2.2 配置权限

进入应用 → 「权限管理」，搜索并开通以下权限：

**Nanobot 需要的权限：**
- `im:message` — 获取与发送单聊、群组消息
- `im:message:send_as_bot` — 以应用的身份发消息

**OpenClaw 需要的权限：**
- `im:message` — 获取与发送单聊、群组消息
- `im:message:send_as_bot` — 以应用的身份发消息
- `im:message.reactions:write_only` — 消息表情回复（可选）
- `contact:contact.base:readonly` — 读取通讯录基本信息（可选）

### 2.3 开启机器人能力

进入应用 → 「应用能力」→ 「机器人」→ 开启。

### 2.4 配置事件订阅（长连接模式）

进入应用 → 「事件与回调」：
1. 订阅方式选择「**使用长连接接收事件**」
2. 添加事件：`im.message.receive_v1`（接收消息）

### 2.5 发布应用

进入「版本管理与发布」→ 创建版本 → 申请发布。

> **注意**：企业管理员需要审批通过后，Bot 才能在飞书中使用。

---

## 第三步：虚拟机 — 安装基础环境

### 3.1 安装 Docker

```bash
# 更新包管理器
sudo apt update

# 安装 Docker
sudo apt install -y docker.io docker-compose-v2

# 把当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER

# 重新登录使生效
newgrp docker
```

### 3.2 安装 Node.js（OpenClaw 需要）

```bash
# 安装 Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 设置 npm 全局目录（避免 sudo）
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# 添加到 PATH（加到 ~/.bashrc 末尾）
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

---

## 第四步：部署 Nanobot（自写 Python Bot）

### 4.1 创建项目目录

```bash
mkdir -p ~/feishu-nanobot
cd ~/feishu-nanobot
```

### 4.2 创建代码文件

复制本目录中的以下文件到 `~/feishu-nanobot/`：

- `nanobot/bot.py` — Bot 主程序
- `nanobot/requirements.txt` — Python 依赖
- `nanobot/Dockerfile` — Docker 构建文件
- `nanobot/docker-compose.yml` — Docker Compose 配置

### 4.3 配置环境变量

```bash
cd ~/feishu-nanobot

# 复制示例配置
cp .env.example .env

# 编辑 .env，填入你自己的信息
nano .env
```

`.env` 文件内容：

```
FEISHU_APP_ID=你的Nanobot应用的AppID
FEISHU_APP_SECRET=你的Nanobot应用的AppSecret
OLLAMA_URL=http://<你的Mac IP>:11434
OLLAMA_MODEL=qwen2.5:7b
```

### 4.4 启动

```bash
docker compose up -d --build
```

### 4.5 查看日志

```bash
docker compose logs -f bot
```

看到 `connected to wss://msg-frontier.feishu.cn` 就说明连接成功了。

---

## 第五步：部署 OpenClaw（AI Gateway）

### 5.1 安装 OpenClaw

```bash
npm i -g openclaw@latest
```

### 5.2 初始化配置

安装后，OpenClaw 的配置文件在 `~/.openclaw/openclaw.json`。

首次运行 `openclaw gateway run`，它会自动创建默认配置。然后按下 `Ctrl+C` 停止。

编辑配置文件：

```bash
nano ~/.openclaw/openclaw.json
```

需要修改的关键配置：

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://<你的Mac IP>:11434",
        "apiKey": "ollama-local",
        "api": "ollama",
        "models": [
          {
            "id": "gemma2:9b",
            "name": "gemma2:9b",
            "compat": {
              "supportsTools": false
            }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/gemma2:9b"
      }
    }
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "domain": "feishu",
      "connectionMode": "websocket",
      "dmPolicy": "open",
      "groupPolicy": "disabled",
      "accounts": {
        "default": {
          "appId": "你的OpenClaw应用的AppID",
          "appSecret": "你的OpenClaw应用的AppSecret",
          "botName": "OpenClaw"
        }
      }
    }
  },
  "gateway": {
    "mode": "local"
  }
}
```

> **关键**：gemma2 不支持 tool calling，必须设置 `"supportsTools": false`，否则会报 400 错误。如果想用 tools 功能，换成 qwen2.5 或 llama3.1 等支持 tool calling 的模型。

### 5.3 启动

```bash
# 前台运行（调试用）
openclaw gateway run

# 或后台运行
nohup openclaw gateway run > ~/.openclaw/logs/gateway.log 2>&1 &
```

### 5.4 停止

```bash
openclaw gateway stop
```

---

## 第六步：一键启停脚本

为了方便日常使用，本目录提供了三个脚本：

| 脚本 | 用途 |
|------|------|
| `scripts/services-start.sh` | 一键启动两个 Bot |
| `scripts/services-stop.sh` | 一键停止两个 Bot |
| `scripts/services-status.sh` | 查看运行状态 |

### 6.1 安装脚本

```bash
# 复制到 home 目录
cp scripts/services-*.sh ~/

# 添加执行权限
chmod +x ~/services-start.sh ~/services-stop.sh ~/services-status.sh
```

### 6.2 使用

```bash
# 启动（会自动检查 Ollama 连接和 Docker 状态）
~/services-start.sh

# 查看状态
~/services-status.sh

# 停止
~/services-stop.sh
```

### 6.3 自定义

脚本中的以下变量需要根据你的环境修改：

- `OLLAMA_URL` — macOS 主机的 Ollama 地址（默认 `http://<你的Mac IP>:11434`）
- Nanobot 目录路径（默认 `~/feishu-nanobot`）
- OpenClaw 日志路径（默认 `~/.openclaw/logs/gateway.log`）

---

## 安全注意事项

> **重要**：以下几点关系到你的账号和电脑安全，请认真阅读。

### 绝对不要做的事

1. **不要把 `.env` 文件提交到 Git**
   - `.env` 里有你的飞书 App Secret，泄露后别人可以冒充你的 Bot
   - 本项目的 `.gitignore` 已经排除了 `.env`，但请再次确认

2. **不要把 `openclaw.json` 提交到 Git**
   - 里面有飞书的 App Secret 和 Gateway Token
   - OpenClaw 的配置在 `~/.openclaw/` 目录下，不在项目里

3. **不要把 Ollama 暴露到公网**
   - Ollama 没有认证机制，任何人连上就能用
   - 只在虚拟机内网（`10.211.55.x`）使用

### 建议做的事

1. **限制 Nanobot 只处理私聊消息**
   - 代码中已设置 `chat_type != "p2p"` 时忽略
   - 这样可以防止有人在群里利用你的 Bot

2. **限制 OpenClaw 的 DM 策略**
   - 配置中 `dmPolicy: "open"` 表示任何人都能私聊你的 Bot
   - 如果只想自己用，改成指定 `allowFrom` 白名单

3. **定期轮换飞书 App Secret**
   - 在飞书开放平台的应用管理中可以重置

4. **虚拟机防火墙**
   - 虚拟机不需要开放任何端口（Bot 用 WebSocket 长连接主动连飞书）
   - OpenClaw Gateway 只监听 `127.0.0.1:18789`，外部访问不到

---

## 常见问题

### Q: Ollama 连不上？

```bash
# 1. 确认 macOS 上 Ollama 在运行
# 2. 确认设置了 OLLAMA_HOST=0.0.0.0 并重启了 Ollama
# 3. 在虚拟机中测试：
curl http://<你的Mac IP>:11434/api/tags
```

### Q: Nanobot 收到消息但不回复？

```bash
# 查看日志
cd ~/feishu-nanobot && docker compose logs -f bot

# 常见原因：
# - Ollama 地址不对
# - 模型没下载
# - 飞书权限没配够
```

### Q: OpenClaw 报 "does not support tools"？

在 `~/.openclaw/openclaw.json` 的模型配置中加上：

```json
"compat": { "supportsTools": false }
```

这会禁用 tool calling，模型只做纯聊天。

### Q: OpenClaw 报 "EACCES: permission denied, mkdir /home/node"？

这是因为之前用 Docker 跑过 OpenClaw，旧 session 残留了 Docker 路径。清除即可：

```bash
rm ~/.openclaw/agents/main/sessions/sessions.json
rm ~/.openclaw/agents/main/sessions/*.jsonl
# 然后重启 OpenClaw
```

### Q: 飞书上找不到 Bot？

1. 确认应用已发布且通过审批
2. 在飞书搜索栏搜 Bot 名称
3. 确认 Bot 的「机器人」能力已开启

---

## 文件说明

```
13-feishu-bots/
├── README.md               ← 你正在看的教程
├── nanobot/
│   ├── bot.py              ← Nanobot 主程序
│   ├── requirements.txt    ← Python 依赖
│   ├── Dockerfile          ← Docker 构建文件
│   ├── docker-compose.yml  ← Docker Compose 配置
│   └── .env.example        ← 环境变量模板（需复制为 .env 并填入）
└── scripts/
    ├── services-start.sh   ← 一键启动
    ├── services-stop.sh    ← 一键停止
    └── services-status.sh  ← 查看状态
```
