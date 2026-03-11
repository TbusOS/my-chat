#!/bin/bash
# ============================================
# Mac Mini AI Stack - 一键启动脚本
# ============================================
# 用法：chmod +x start-all.sh && ./start-all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STACK_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Starting Mac Mini AI Stack ==="
echo ""

# 1. 启动 Ollama（后台）
echo "[1/3] Starting Ollama..."
if pgrep -x "ollama" > /dev/null; then
    echo "  Ollama already running."
else
    OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2
    if pgrep -x "ollama" > /dev/null; then
        echo "  Ollama started (PID: $(pgrep -x ollama))"
    else
        echo "  [!] Failed to start Ollama. Check /tmp/ollama.log"
        exit 1
    fi
fi

# 2. 启动 Docker 服务
echo "[2/3] Starting Docker services..."
cd "$STACK_DIR"
docker compose up -d
echo "  Docker services started."

# 3. 启动 MCP Server（后台）
echo "[3/3] Starting MCP Server..."
if lsof -i :8811 > /dev/null 2>&1; then
    echo "  MCP Server already running on :8811"
else
    cd "$STACK_DIR/mcp-server"
    nohup uvicorn mcp_server:app --host 0.0.0.0 --port 8811 > /tmp/mcp-server.log 2>&1 &
    sleep 2
    if lsof -i :8811 > /dev/null 2>&1; then
        echo "  MCP Server started on :8811"
    else
        echo "  [!] Failed to start MCP Server. Check /tmp/mcp-server.log"
    fi
fi

echo ""
echo "=== All Services Running ==="
echo ""
echo "  LobeChat:    http://localhost:3210"
echo "  Ollama API:  http://localhost:11434"
echo "  MCP Server:  http://localhost:8811"
echo "  MCP Health:  http://localhost:8811/health"
echo ""
echo "Stop all: docker compose down && pkill ollama && pkill -f mcp_server"
