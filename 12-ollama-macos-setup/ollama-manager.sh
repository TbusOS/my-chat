#!/bin/bash

# Ollama 一键管理脚本
# 用法: ./ollama-manager.sh [start|stop|restart|status|test]

OLLAMA_SERVICE="ollama"
MODELS=("qwen2.5:7b" "gemma2:9b")

case "${1:-status}" in
  start)
    echo "启动 Ollama 服务..."
    launchctl setenv OLLAMA_HOST "${OLLAMA_BIND_ADDR:-127.0.0.1}"
    brew services start "$OLLAMA_SERVICE"
    echo "等待服务就绪..."
    sleep 2
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
      echo "Ollama 已启动，监听 ${OLLAMA_BIND_ADDR:-127.0.0.1}:11434"
    else
      echo "启动失败，请检查日志"
      exit 1
    fi
    ;;

  stop)
    echo "停止 Ollama 服务..."
    brew services stop "$OLLAMA_SERVICE"
    echo "已停止"
    ;;

  restart)
    echo "重启 Ollama 服务..."
    launchctl setenv OLLAMA_HOST "${OLLAMA_BIND_ADDR:-127.0.0.1}"
    brew services restart "$OLLAMA_SERVICE"
    sleep 2
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
      echo "Ollama 已重启，监听 ${OLLAMA_BIND_ADDR:-127.0.0.1}:11434"
    else
      echo "重启失败，请检查日志"
      exit 1
    fi
    ;;

  status)
    echo "=== Ollama 服务状态 ==="
    brew services info "$OLLAMA_SERVICE"
    echo ""
    echo "=== 已安装模型 ==="
    ollama list
    echo ""
    echo "=== 当前运行中的模型 ==="
    ollama ps
    echo ""
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
      echo "API 状态: 正常 (http://${OLLAMA_BIND_ADDR:-127.0.0.1}:11434)"
    else
      echo "API 状态: 不可用"
    fi
    ;;

  test)
    echo "=== 测试 qwen2.5:7b (中文模型) ==="
    echo "发送: 你好，请用一句话介绍自己"
    echo "---"
    START=$(python3 -c 'import time; print(int(time.time()*1000))')
    ollama run qwen2.5:7b "你好，请用一句话介绍自己" 2>/dev/null
    END=$(python3 -c 'import time; print(int(time.time()*1000))')
    ELAPSED=$(( END - START ))
    echo ""
    echo "--- 耗时: $((ELAPSED / 1000)).$((ELAPSED % 1000 / 100))s ---"
    echo ""

    echo "=== 测试 gemma2:9b (英文模型) ==="
    echo "发送: Hello, introduce yourself in one sentence"
    echo "---"
    START=$(python3 -c 'import time; print(int(time.time()*1000))')
    ollama run gemma2:9b "Hello, introduce yourself in one sentence" 2>/dev/null
    END=$(python3 -c 'import time; print(int(time.time()*1000))')
    ELAPSED=$(( END - START ))
    echo ""
    echo "--- 耗时: $((ELAPSED / 1000)).$((ELAPSED % 1000 / 100))s ---"
    ;;

  *)
    echo "用法: $0 [start|stop|restart|status|test]"
    echo ""
    echo "  start   - 启动 Ollama 服务"
    echo "  stop    - 停止 Ollama 服务"
    echo "  restart - 重启 Ollama 服务"
    echo "  status  - 查看服务和模型状态"
    echo "  test    - 测试两个模型是否正常"
    ;;
esac
