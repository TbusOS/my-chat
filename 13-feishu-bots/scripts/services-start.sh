#!/bin/bash
# 一键启动 OpenClaw + Nanobot
# 使用前请修改下面的配置变量

set -e

# ========== 配置（根据你的环境修改）==========
OLLAMA_URL="http://YOUR_MAC_IP:11434"     # macOS 主机的 Ollama 地址
NANOBOT_DIR="$HOME/feishu-nanobot"         # Nanobot 项目目录
OPENCLAW_LOGDIR="$HOME/.openclaw/logs"     # OpenClaw 日志目录
# =============================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== 启动飞书 Bot 服务 ===${NC}"
echo ""

# 1. 检查 Ollama 是否可达
echo -n "检查 Ollama 连接... "
if curl -s --max-time 3 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}无法连接 $OLLAMA_URL${NC}"
    echo "请确认 macOS 上的 Ollama 已启动，且设置了 OLLAMA_HOST=0.0.0.0"
    exit 1
fi

# 2. 启动 Docker（如果未运行）
echo -n "检查 Docker... "
if ! systemctl is-active --quiet docker; then
    echo -e "${YELLOW}启动 Docker...${NC}"
    sudo systemctl start docker
    sleep 2
fi
echo -e "${GREEN}OK${NC}"

# 3. 启动 Nanobot（Docker）
echo ""
echo -e "${YELLOW}[1/2] 启动 Nanobot${NC}"
cd "$NANOBOT_DIR"
docker compose up -d --build
echo -e "${GREEN}Nanobot 已启动${NC}"

# 4. 启动 OpenClaw（Gateway 模式）
echo ""
echo -e "${YELLOW}[2/2] 启动 OpenClaw${NC}"

if pgrep -f "openclaw-gateway" > /dev/null 2>&1; then
    echo -e "${YELLOW}OpenClaw Gateway 已在运行${NC}"
else
    mkdir -p "$OPENCLAW_LOGDIR"
    LOGFILE="$OPENCLAW_LOGDIR/gateway.log"
    nohup openclaw gateway run > "$LOGFILE" 2>&1 &
    echo "OpenClaw PID: $!"

    # 等待 gateway 进程出现
    sleep 8
    if pgrep -f "openclaw-gateway" > /dev/null 2>&1 || pgrep -f "openclaw" > /dev/null 2>&1; then
        echo -e "${GREEN}OpenClaw Gateway 已启动${NC}"
    else
        echo -e "${RED}OpenClaw 启动失败，查看日志: $LOGFILE${NC}"
        tail -5 "$LOGFILE" 2>/dev/null
        exit 1
    fi
fi

# 5. 状态汇总
echo ""
echo -e "${GREEN}=== 全部启动完成 ===${NC}"
echo ""
echo "  Nanobot:   docker compose (nanobot-bot 容器)"
echo "  OpenClaw:  openclaw gateway (PID: $(pgrep -f 'openclaw-gateway' | head -1 || echo '?'))"
echo "  Ollama:    $OLLAMA_URL"
echo ""
echo "查看日志:"
echo "  Nanobot:   cd $NANOBOT_DIR && docker compose logs -f bot"
echo "  OpenClaw:  tail -f $OPENCLAW_LOGDIR/gateway.log"
echo ""
echo "停止服务:    ~/services-stop.sh"
