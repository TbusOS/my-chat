#!/bin/bash
# 查看 OpenClaw + Nanobot 运行状态

# ========== 配置（根据你的环境修改）==========
OLLAMA_URL="http://YOUR_MAC_IP:11434"
# =============================================

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "=== 飞书 Bot 服务状态 ==="
echo ""

# OpenClaw
echo -n "OpenClaw Gateway:  "
if pgrep -f "openclaw-gateway" > /dev/null 2>&1; then
    PID=$(pgrep -f "openclaw-gateway" | head -1)
    echo -e "${GREEN}运行中${NC} (PID: $PID)"
else
    echo -e "${RED}未运行${NC}"
fi

# Nanobot
echo -n "Nanobot (Docker):  "
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q nanobot-bot; then
    echo -e "${GREEN}运行中${NC}"
else
    echo -e "${RED}未运行${NC}"
fi

# Ollama
echo -n "Ollama (macOS):    "
if curl -s --max-time 2 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}可达${NC}"
else
    echo -e "${RED}不可达${NC}"
fi

echo ""
