#!/bin/bash
# 一键停止 OpenClaw + Nanobot

# ========== 配置（根据你的环境修改）==========
NANOBOT_DIR="$HOME/feishu-nanobot"
# =============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}=== 停止飞书 Bot 服务 ===${NC}"
echo ""

# 1. 停止 OpenClaw Gateway
echo -n "[1/2] 停止 OpenClaw... "
if pgrep -f "openclaw-gateway" > /dev/null 2>&1 || pgrep -x "openclaw" > /dev/null 2>&1; then
    openclaw gateway stop 2>/dev/null || true
    sleep 2
    pkill -f "openclaw-gateway" 2>/dev/null || true
    pkill -x "openclaw" 2>/dev/null || true
    echo -e "${GREEN}已停止${NC}"
else
    echo "未运行"
fi

# 2. 停止 Nanobot（Docker）
echo -n "[2/2] 停止 Nanobot... "
cd "$NANOBOT_DIR"
docker compose down 2>/dev/null
echo -e "${GREEN}已停止${NC}"

echo ""
echo -e "${GREEN}=== 全部已停止 ===${NC}"
