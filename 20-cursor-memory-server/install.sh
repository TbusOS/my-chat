#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_CONFIG="$HOME/.cursor/mcp.json"
MEMORY_DIR="$HOME/.cursor/memory"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[!]${NC} $1"; }
fail() { echo -e "  ${RED}[ERROR]${NC} $1"; exit 1; }

show_help() {
  echo ""
  echo -e "${BOLD}Cursor Memory Server - 一键安装脚本${NC}"
  echo ""
  echo -e "${BOLD}用法:${NC}"
  echo "  bash install.sh <command> [options]"
  echo ""
  echo -e "${BOLD}命令:${NC}"
  echo -e "  ${CYAN}global${NC}              只安装 MCP Server（全局生效，所有项目可用）"
  echo -e "  ${CYAN}project <dir>${NC}       为指定项目安装 Cursor Rule（需先完成 global 安装）"
  echo -e "  ${CYAN}all <dir>${NC}           全部安装：MCP Server + 指定项目的 Cursor Rule"
  echo -e "  ${CYAN}help${NC}                显示此帮助信息"
  echo ""
  echo -e "${BOLD}示例:${NC}"
  echo "  bash install.sh global                          # 安装 MCP Server（全局）"
  echo "  bash install.sh project /path/to/my-app         # 为 my-app 项目添加记忆规则"
  echo "  bash install.sh all /path/to/my-app             # 全部搞定"
  echo "  bash install.sh project .                       # 为当前目录项目添加记忆规则"
  echo ""
  echo -e "${BOLD}安装的内容:${NC}"
  echo "  global  -> 检查 Bun 环境、安装依赖、验证 Server、写入 ~/.cursor/mcp.json"
  echo "  project -> 在目标项目下创建 .cursor/rules/memory-auto.md（AI 自动记忆行为指令）"
  echo ""
  echo -e "${BOLD}安装完成后重启 Cursor 即可使用。${NC}"
  echo ""
}

install_global() {
  echo ""
  echo "======================================"
  echo " Cursor Memory Server - 全局安装"
  echo "======================================"

  # --- 1. 检查 Bun ---
  echo ""
  echo "[1/4] 检查 Bun 环境..."
  if ! command -v bun &>/dev/null; then
    warn "未检测到 Bun，正在安装..."
    curl -fsSL https://bun.sh/install | bash
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
    if ! command -v bun &>/dev/null; then
      fail "Bun 安装失败，请手动安装: https://bun.sh"
    fi
  fi
  ok "Bun $(bun --version)"

  # --- 2. 安装依赖 ---
  echo ""
  echo "[2/4] 安装项目依赖..."
  cd "$SCRIPT_DIR"
  bun install --silent 2>/dev/null || bun install
  ok "依赖安装完成"

  # --- 3. 验证服务器 ---
  echo ""
  echo "[3/4] 验证服务器启动..."
  STARTUP_OUTPUT=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
    | MEMORY_DIR=/tmp/.cursor-memory-test bun run src/index.ts 2>/dev/null | head -1)

  if echo "$STARTUP_OUTPUT" | grep -q '"protocolVersion"'; then
    ok "服务器启动验证通过"
    rm -rf /tmp/.cursor-memory-test
  else
    fail "服务器启动失败，请检查错误信息"
  fi

  # --- 4. 配置 MCP ---
  echo ""
  echo "[4/4] 配置 MCP Server..."
  mkdir -p "$(dirname "$MCP_CONFIG")"

  if [ -f "$MCP_CONFIG" ]; then
    if grep -q '"memory"' "$MCP_CONFIG"; then
      warn "MCP 配置中已存在 memory server，跳过"
    else
      bun -e "
        const fs = require('fs');
        const cfg = JSON.parse(fs.readFileSync('$MCP_CONFIG', 'utf8'));
        cfg.mcpServers = cfg.mcpServers || {};
        cfg.mcpServers.memory = {
          command: 'bun',
          args: ['run', '$SCRIPT_DIR/src/index.ts'],
          env: { MEMORY_DIR: '$MEMORY_DIR' }
        };
        fs.writeFileSync('$MCP_CONFIG', JSON.stringify(cfg, null, 2) + '\n');
      "
      ok "已添加到现有 MCP 配置"
    fi
  else
    cat > "$MCP_CONFIG" << MCPEOF
{
  "mcpServers": {
    "memory": {
      "command": "bun",
      "args": ["run", "$SCRIPT_DIR/src/index.ts"],
      "env": {
        "MEMORY_DIR": "$MEMORY_DIR"
      }
    }
  }
}
MCPEOF
    ok "已创建 MCP 配置"
  fi

  echo ""
  echo -e "  ${GREEN}全局安装完成${NC}"
  echo "  MCP 配置: $MCP_CONFIG"
  echo "  数据存储: $MEMORY_DIR"
}

install_project() {
  local target_dir="$1"

  # 支持 "." 作为当前目录
  target_dir="$(cd "$target_dir" && pwd)"

  echo ""
  echo "======================================"
  echo " Cursor Memory Server - 项目配置"
  echo "======================================"
  echo ""
  echo "目标项目: $target_dir"

  local rdir="$target_dir/.cursor/rules"
  local rfile="$rdir/memory-auto.md"

  mkdir -p "$rdir"

  if [ -f "$rfile" ]; then
    warn "Cursor Rule 已存在: $rfile"
    echo ""
    read -r -p "  是否覆盖? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
      cp "$SCRIPT_DIR/cursor-rule-template.md" "$rfile"
      ok "Cursor Rule 已更新: $rfile"
    else
      warn "跳过"
    fi
  else
    cp "$SCRIPT_DIR/cursor-rule-template.md" "$rfile"
    ok "Cursor Rule 已创建: $rfile"
  fi

  echo ""
  echo -e "  ${GREEN}项目配置完成${NC}"
}

# --- 主入口 ---
COMMAND="${1:-}"

case "$COMMAND" in
  global)
    install_global
    echo ""
    echo -e "${BOLD}下一步:${NC}"
    echo "  1. 为需要记忆功能的项目运行: bash install.sh project /path/to/project"
    echo "  2. 重启 Cursor IDE"
    echo ""
    ;;

  project)
    PROJECT_DIR="${2:-}"
    if [ -z "$PROJECT_DIR" ]; then
      echo ""
      fail "请指定项目目录，例如: bash install.sh project /path/to/my-app"
    fi
    if [ ! -d "$PROJECT_DIR" ]; then
      echo ""
      fail "目录不存在: $PROJECT_DIR"
    fi
    install_project "$PROJECT_DIR"
    echo ""
    echo -e "${BOLD}下一步:${NC}"
    echo "  1. 确保已运行过: bash install.sh global"
    echo "  2. 重启 Cursor IDE"
    echo ""
    ;;

  all)
    PROJECT_DIR="${2:-}"
    if [ -z "$PROJECT_DIR" ]; then
      echo ""
      fail "请指定项目目录，例如: bash install.sh all /path/to/my-app"
    fi
    if [ ! -d "$PROJECT_DIR" ]; then
      echo ""
      fail "目录不存在: $PROJECT_DIR"
    fi
    install_global
    install_project "$PROJECT_DIR"
    echo ""
    echo "======================================"
    echo -e " ${GREEN}全部安装完成!${NC}"
    echo "======================================"
    echo ""
    echo "  重启 Cursor IDE 即可使用"
    echo ""
    ;;

  help|-h|--help)
    show_help
    ;;

  *)
    show_help
    exit 1
    ;;
esac
