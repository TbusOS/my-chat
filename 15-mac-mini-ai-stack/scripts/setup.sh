#!/bin/bash
# ============================================
# Mac Mini AI Stack - 一键安装脚本
# ============================================
# 用法：chmod +x setup.sh && ./setup.sh

set -e

echo "=== Mac Mini AI Stack Setup ==="
echo ""

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "[!] Homebrew not found. Install from https://brew.sh/"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[!] Docker not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# 安装 Ollama
echo "[1/4] Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "  Ollama already installed: $(ollama --version)"
else
    brew install ollama
    echo "  Ollama installed."
fi

# 安装 Python 依赖（MCP Server）
echo "[2/4] Installing MCP Server dependencies..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
pip install -r "$SCRIPT_DIR/../mcp-server/requirements.txt"

# 安装 MLX（可选）
echo "[3/4] Installing MLX (for model training)..."
if pip show mlx-lm &> /dev/null; then
    echo "  mlx-lm already installed."
else
    pip install mlx-lm
    echo "  mlx-lm installed."
fi

# 准备 Docker 环境
echo "[4/4] Preparing Docker environment..."
COMPOSE_DIR="$SCRIPT_DIR/.."
if [ ! -f "$COMPOSE_DIR/.env" ]; then
    cp "$COMPOSE_DIR/.env.example" "$COMPOSE_DIR/.env"
    echo "  .env created from template. Please edit it before starting:"
    echo "  vim $COMPOSE_DIR/.env"
else
    echo "  .env already exists."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your passwords"
echo "  2. Pull a model:     ollama pull qwen2.5:7b"
echo "  3. Start Ollama:     OLLAMA_HOST=0.0.0.0:11434 ollama serve"
echo "  4. Start Docker:     cd $(dirname "$SCRIPT_DIR") && docker compose up -d"
echo "  5. Start MCP Server: uvicorn mcp-server.mcp_server:app --host 0.0.0.0 --port 8811"
echo ""
echo "Access LobeChat at: http://localhost:3210"
