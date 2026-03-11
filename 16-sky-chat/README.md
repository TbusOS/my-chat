# LobeChat 定制化 + Cloudflare 公网安全部署

> 基于 LobeHub/lobe-chat 打造个人 AI 聊天平台，通过 Cloudflare 安全暴露到公网

## 这是什么？

我们要做三件事：

1. **定制 LobeChat** — 基于开源 LobeChat 进行个性化改造（品牌、默认配置、插件等）
2. **Docker 部署** — 用 Docker Compose 一键启动完整服务栈（前端 + 数据库 + 缓存）
3. **Cloudflare 安全发布** — 用 Cloudflare Tunnel + Access 把服务安全暴露到公网，无需公网 IP

## 为什么用 Cloudflare？

| 传统方案 | Cloudflare 方案 |
|----------|----------------|
| 需要公网 IP 或端口映射 | 不需要，Tunnel 主动连接 Cloudflare |
| 源站 IP 暴露，容易被攻击 | 源站 IP 完全隐藏 |
| 自己配 HTTPS 证书 | Cloudflare 自动管理证书 |
| 自己做 DDoS 防护 | Cloudflare 免费 DDoS 防护 |
| 无访问控制 | Cloudflare Access 提供认证 |
| 自己配 WAF 规则 | Cloudflare WAF 自动防护 |

**总结**：家庭网络部署 AI 服务的最佳方案。零暴露、零成本（免费计划足够）。

## 整体架构

```
                    ┌──────────────────────────────┐
                    │       Cloudflare Edge        │
                    │                              │
用户（手机/电脑）     │  ┌────────┐  ┌───────────┐  │
──── HTTPS ────────►│  │  WAF   │→ │  Access   │  │
                    │  │ DDoS防护│  │ 身份认证   │  │
                    │  └────────┘  └─────┬─────┘  │
                    └────────────────────┼────────┘
                                         │ Cloudflare Tunnel
                                         │ (加密隧道，出站连接)
                    ┌────────────────────┼────────┐
                    │   你的 Mac / 服务器  │        │
                    │                    ▼        │
                    │  ┌──────────────────────┐   │
                    │  │  cloudflared (守护进程) │   │
                    │  └──────────┬───────────┘   │
                    │             │               │
                    │  ┌──────────▼───────────┐   │
                    │  │     Docker Compose    │   │
                    │  │                      │   │
                    │  │  LobeChat  (:3210)   │   │
                    │  │  PostgreSQL (:5432)  │   │
                    │  │  Redis     (:6379)   │   │
                    │  └──────────┬───────────┘   │
                    │             │               │
                    │  ┌──────────▼───────────┐   │
                    │  │  Ollama (macOS 原生)   │   │
                    │  │  :11434              │   │
                    │  └──────────────────────┘   │
                    └─────────────────────────────┘

关键：所有流量都是 cloudflared 主动连出去的，
     不需要开放任何入站端口。
```

## 安全层级

本方案提供 **四层安全防护**：

```
第 1 层：Cloudflare Tunnel — 源站 IP 隐藏，无入站端口
第 2 层：Cloudflare WAF   — SQL 注入、XSS 等自动拦截
第 3 层：Cloudflare Access — 登录才能访问（邮箱验证码 / GitHub OAuth / etc）
第 4 层：LobeChat 自身    — 应用层认证（可选）
```

---

## 前置条件

- Docker + Docker Compose（或 Colima）
- 一个域名（可以是便宜的 .xyz / .top 域名，几块钱一年）
- [Cloudflare 账号](https://dash.cloudflare.com/sign-up)（免费计划即可）
- Ollama 已安装并运行

---

## 第一步：部署 LobeChat 服务栈

### 1.1 创建项目目录

```bash
mkdir -p ~/ai-chat && cd ~/ai-chat
```

### 1.2 创建环境变量文件

```bash
cat > .env << 'EOF'
# === 数据库 ===
POSTGRES_USER=lobechat
POSTGRES_PASSWORD=<生成一个强密码>
POSTGRES_DB=lobechat

# === Redis ===
REDIS_PASSWORD=<生成另一个强密码>

# === Ollama ===
# Docker Desktop 用户：
OLLAMA_HOST=host.docker.internal
# Colima 用户：改为你的宿主机 IP
# OLLAMA_HOST=192.168.x.x

# === LobeChat ===
# 访问密码（可选，Cloudflare Access 已提供认证）
# ACCESS_CODE=your-access-code
EOF
```

> **生成强密码**：`openssl rand -base64 24`

### 1.3 创建 docker-compose.yml

```yaml
services:
  lobechat:
    image: lobehub/lobe-chat-database
    container_name: lobechat
    ports:
      - "127.0.0.1:3210:3210"  # 只监听 localhost，不对外暴露
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - OPENAI_PROXY_URL=http://${OLLAMA_HOST:-host.docker.internal}:11434/v1
      - OPENAI_API_KEY=ollama-local
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: lobechat-postgres
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: lobechat-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
```

> **注意**：`127.0.0.1:3210:3210` 只绑定 localhost。外部访问全部走 Cloudflare Tunnel。

### 1.4 启动服务

```bash
docker compose up -d
docker compose ps          # 确认全部 healthy
curl http://localhost:3210  # 本地测试
```

---

## 第二步：域名接入 Cloudflare

### 2.1 添加域名

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 点击 **Add a site** → 输入你的域名
3. 选择 **Free** 计划
4. Cloudflare 会给你两个 nameserver 地址
5. 去你的域名注册商（如 Namesilo、Cloudflare Registrar）把 DNS 服务器改为 Cloudflare 的

等待 DNS 生效（通常几分钟，最长 24 小时）。

### 2.2 确认域名状态

Dashboard 中域名状态变为 **Active** 即可继续。

---

## 第三步：设置 Cloudflare Tunnel

Tunnel 让你无需公网 IP，也不用开放任何端口，就能把本地服务暴露到互联网。

### 3.1 安装 cloudflared

```bash
# macOS
brew install cloudflared

# Linux (Debian/Ubuntu)
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared
```

### 3.2 登录认证

```bash
cloudflared tunnel login
```

浏览器会打开授权页面。选择你的域名，授权后会在 `~/.cloudflared/` 生成证书。

### 3.3 创建 Tunnel

```bash
# 创建 tunnel（名字随意）
cloudflared tunnel create ai-chat

# 记住输出的 Tunnel ID，类似: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 3.4 配置 Tunnel

```bash
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <你的 Tunnel ID>
credentials-file: ~/.cloudflared/<你的 Tunnel ID>.json

ingress:
  # AI 聊天 — 主服务
  - hostname: chat.your-domain.com
    service: http://localhost:3210
  # 兜底规则（必须有）
  - service: http_status:404
EOF
```

### 3.5 添加 DNS 记录

```bash
cloudflared tunnel route dns ai-chat chat.your-domain.com
```

这会自动在 Cloudflare DNS 中添加一条 CNAME 记录，指向你的 Tunnel。

### 3.6 启动 Tunnel

```bash
# 前台运行（调试用）
cloudflared tunnel run ai-chat

# 安装为系统服务（推荐，开机自启）
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# macOS 用 launchd：
sudo cloudflared service install
```

### 3.7 验证

浏览器打开 `https://chat.your-domain.com`，应该能看到 LobeChat 界面。

此时：
- 自动 HTTPS（Cloudflare 管理证书）
- 源站 IP 完全隐藏
- 但**任何人**都能访问 — 下一步加认证

---

## 第四步：Cloudflare Access 访问控制

让只有你（和你授权的人）能访问。

### 4.1 进入 Zero Trust

Cloudflare Dashboard → **Zero Trust** → **Access** → **Applications**

### 4.2 创建 Application

1. 点击 **Add an application** → 选择 **Self-hosted**
2. 配置：
   - **Application name**: AI Chat
   - **Session Duration**: 24 hours（或更长）
   - **Application domain**: `chat.your-domain.com`

### 4.3 添加 Policy

1. **Policy name**: Allowed Users
2. **Action**: Allow
3. **Include** 规则（任选一种或多种）：

| 方式 | 配置 | 说明 |
|------|------|------|
| 邮箱 | Emails: `you@example.com` | 输入邮箱收验证码登录 |
| GitHub | GitHub Organization | 用 GitHub 账号登录 |
| Google | Google Workspace | 用 Google 账号登录 |
| IP 白名单 | IP Ranges: `x.x.x.x/32` | 指定 IP 免认证 |

**推荐**：邮箱验证码，最简单，不依赖第三方。

### 4.4 效果

配置完成后，访问 `https://chat.your-domain.com` 会先跳转到 Cloudflare 认证页面：

```
用户访问 → Cloudflare Access 认证页 → 输入邮箱 → 收到验证码 → 验证通过 → 进入 LobeChat
```

未授权用户无法看到任何 LobeChat 内容。

---

## 第五步：Cloudflare WAF 防护

免费计划已包含基础 WAF，可选加强：

### 5.1 开启安全设置

Cloudflare Dashboard → 你的域名 → **Security** → **WAF**

### 5.2 推荐规则

| 设置 | 推荐值 | 说明 |
|------|--------|------|
| Security Level | Medium | 对可疑 IP 展示验证码 |
| Bot Fight Mode | On | 自动拦截恶意爬虫 |
| Browser Integrity Check | On | 拦截伪造浏览器请求 |
| Hotlink Protection | On | 防盗链 |

### 5.3 自定义规则（可选）

```
# 只允许特定国家访问
Rule: Block non-CN traffic
Expression: (ip.geoip.country ne "CN")
Action: Block
```

---

## 第六步：LobeChat 定制（可选）

### 6.1 自定义模型列表

在 `.env` 中配置 LobeChat 显示的模型：

```bash
# 只显示你安装的模型
OPENAI_MODEL_LIST=qwen2.5:7b,llama3.1:8b

# 或接入多个 provider
# OPENAI_API_KEY=your-api-key
# ANTHROPIC_API_KEY=your-api-key
```

### 6.2 自定义品牌

LobeChat 支持通过环境变量定制：

```bash
# docker-compose.yml 中的 lobechat 服务添加：
environment:
  - CUSTOM_TITLE=My AI Chat
  - CUSTOM_DESCRIPTION=Personal AI Assistant
```

### 6.3 接入多模型 Provider

LobeChat 原生支持多种 AI 服务商，在界面设置中配置即可：

- OpenAI / Azure OpenAI
- Anthropic Claude
- Google Gemini
- 本地 Ollama
- 兼容 OpenAI API 的第三方中转

---

## 运维管理

### 更新 LobeChat

```bash
cd ~/ai-chat
docker compose pull lobechat
docker compose up -d lobechat
```

### 查看日志

```bash
docker compose logs -f lobechat      # 应用日志
sudo journalctl -u cloudflared -f    # Tunnel 日志
```

### 备份数据

```bash
# 备份数据库
docker compose exec postgres pg_dump -U lobechat lobechat > backup-$(date +%Y%m%d).sql

# 备份配置
cp .env .env.backup
cp ~/.cloudflared/config.yml ~/.cloudflared/config.yml.backup
```

### 监控 Tunnel 状态

```bash
cloudflared tunnel info ai-chat
```

或在 Cloudflare Dashboard → Zero Trust → Tunnels 中查看。

---

## 安全检查清单

部署完成后，逐项检查：

- [ ] LobeChat 端口只绑定 `127.0.0.1`，不对外暴露
- [ ] Cloudflare Tunnel 运行正常
- [ ] Cloudflare Access 已配置，未授权用户无法访问
- [ ] WAF 和 Bot 防护已开启
- [ ] `.env` 文件不在 git 仓库中（已在 `.gitignore`）
- [ ] 数据库密码使用随机强密码
- [ ] SSL/TLS 模式设为 Full（Cloudflare Dashboard → SSL/TLS）
- [ ] 定期备份数据库

---

## 常见问题

### Q: 免费 Cloudflare 计划够用吗？

完全够用。免费计划包含：Tunnel（无限流量）、Access（最多 50 用户）、基础 WAF、DDoS 防护、SSL 证书。个人使用绰绰有余。

### Q: Tunnel 断了怎么办？

cloudflared 会自动重连。如果安装为系统服务，机器重启后也会自动启动。检查状态：

```bash
# Linux
sudo systemctl status cloudflared

# macOS
sudo launchctl list | grep cloudflared
```

### Q: 可以同时暴露多个服务吗？

可以。在 `config.yml` 的 ingress 中添加多个 hostname：

```yaml
ingress:
  - hostname: chat.your-domain.com
    service: http://localhost:3210
  - hostname: api.your-domain.com
    service: http://localhost:8811
  - service: http_status:404
```

### Q: 手机上怎么用？

LobeChat 自带响应式设计，手机浏览器直接访问 `https://chat.your-domain.com` 即可。也可以在 iPhone/Android 上"添加到主屏幕"当 PWA 使用。

### Q: 访问速度慢怎么办？

- Cloudflare 在全球有 CDN 节点，静态资源自动缓存加速
- 如果 AI 回复慢，瓶颈在模型推理，不在网络
- 开启 Cloudflare 的 **Rocket Loader** 和 **Auto Minify** 可加速前端加载

---

## 成本

| 项目 | 费用 |
|------|------|
| Cloudflare 账号 | 免费 |
| Cloudflare Tunnel | 免费 |
| Cloudflare Access | 免费（≤50 用户） |
| 域名 | ~10 元/年（.xyz / .top） |
| 服务器 | 你的 Mac（已有） |
| AI 模型 | Ollama 本地模型免费 |

**总成本：约 10 元/年**（仅域名费用）

---

## License

MIT
