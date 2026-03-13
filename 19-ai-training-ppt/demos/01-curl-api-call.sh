#!/bin/bash
# ============================================================
# AI 培训 — 现场演示：用 curl 调用大模型 API
# ============================================================
# 使用前请设置环境变量：
#   export OPENAI_API_KEY="your-key"
#   export ANTHROPIC_API_KEY="your-key"
#   export GOOGLE_API_KEY="your-key"
# ============================================================

set -e

# Color output helpers
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROMPT="用一句话解释微服务架构中的服务发现机制"

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}  大模型 API 调用演示${NC}"
echo -e "${YELLOW}============================================================${NC}"
echo ""
echo -e "提示词: ${GREEN}${PROMPT}${NC}"
echo ""

# --- Demo 1: OpenAI GPT ---
demo_openai() {
  echo -e "${BLUE}▶ [1/3] 调用 OpenAI GPT-4o${NC}"
  echo -e "   端点: https://api.openai.com/v1/chat/completions"
  echo -e "   认证方式: Authorization: Bearer \$OPENAI_API_KEY"
  echo ""

  if [ -z "$OPENAI_API_KEY" ]; then
    echo "   ⚠️  OPENAI_API_KEY 未设置，跳过"
    return
  fi

  curl -s https://api.openai.com/v1/chat/completions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"gpt-4o\",
      \"messages\": [
        {\"role\": \"system\", \"content\": \"你是资深后端工程师，回答简洁专业。\"},
        {\"role\": \"user\", \"content\": \"${PROMPT}\"}
      ],
      \"temperature\": 0.3,
      \"max_tokens\": 200
    }" | python3 -m json.tool

  echo ""
}

# --- Demo 2: Anthropic Claude ---
demo_claude() {
  echo -e "${BLUE}▶ [2/3] 调用 Anthropic Claude Sonnet${NC}"
  echo -e "   端点: https://api.anthropic.com/v1/messages"
  echo -e "   认证方式: x-api-key: \$ANTHROPIC_API_KEY"
  echo ""

  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "   ⚠️  ANTHROPIC_API_KEY 未设置，跳过"
    return
  fi

  curl -s https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"claude-sonnet-4-20250514\",
      \"system\": \"你是资深后端工程师，回答简洁专业。\",
      \"messages\": [
        {\"role\": \"user\", \"content\": \"${PROMPT}\"}
      ],
      \"max_tokens\": 200,
      \"temperature\": 0.3
    }" | python3 -m json.tool

  echo ""
}

# --- Demo 3: Google Gemini ---
demo_gemini() {
  echo -e "${BLUE}▶ [3/3] 调用 Google Gemini Pro${NC}"
  echo -e "   端点: https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
  echo -e "   认证方式: URL 参数 ?key=\$GOOGLE_API_KEY"
  echo ""

  if [ -z "$GOOGLE_API_KEY" ]; then
    echo "   ⚠️  GOOGLE_API_KEY 未设置，跳过"
    return
  fi

  curl -s "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${GOOGLE_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
      \"system_instruction\": {
        \"parts\": [{\"text\": \"你是资深后端工程师，回答简洁专业。\"}]
      },
      \"contents\": [{
        \"parts\": [{\"text\": \"${PROMPT}\"}]
      }],
      \"generationConfig\": {
        \"temperature\": 0.3,
        \"maxOutputTokens\": 200
      }
    }" | python3 -m json.tool

  echo ""
}

# --- Temperature comparison demo ---
demo_temperature() {
  echo -e "${YELLOW}============================================================${NC}"
  echo -e "${YELLOW}  Temperature 对比演示${NC}"
  echo -e "${YELLOW}============================================================${NC}"
  echo ""

  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "   ⚠️  ANTHROPIC_API_KEY 未设置，跳过 temperature 演示"
    return
  fi

  for temp in 0.0 0.5 1.0; do
    echo -e "${BLUE}▶ temperature = ${temp}${NC}"
    curl -s https://api.anthropic.com/v1/messages \
      -H "x-api-key: $ANTHROPIC_API_KEY" \
      -H "anthropic-version: 2023-06-01" \
      -H "Content-Type: application/json" \
      -d "{
        \"model\": \"claude-sonnet-4-20250514\",
        \"system\": \"你是一位有创意的科技作家。\",
        \"messages\": [
          {\"role\": \"user\", \"content\": \"用一个比喻来描述微服务架构\"}
        ],
        \"max_tokens\": 150,
        \"temperature\": ${temp}
      }" | python3 -c "import sys,json; print(json.load(sys.stdin)['content'][0]['text'])"
    echo ""
  done
}

# --- Main ---
case "${1:-all}" in
  openai)   demo_openai ;;
  claude)   demo_claude ;;
  gemini)   demo_gemini ;;
  temp)     demo_temperature ;;
  all)
    demo_openai
    demo_claude
    demo_gemini
    demo_temperature
    ;;
  *)
    echo "用法: $0 [openai|claude|gemini|temp|all]"
    exit 1
    ;;
esac

echo -e "${YELLOW}============================================================${NC}"
echo -e "${YELLOW}  演示完成！${NC}"
echo -e "${YELLOW}============================================================${NC}"
