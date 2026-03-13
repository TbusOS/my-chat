#!/bin/bash
# ============================================================
# AI 培训 — 现场演示：Claude CLI 实战
# ============================================================
# 这个脚本引导演示者完成 Claude CLI 的现场演示
# 建议在终端中逐步执行，而不是一键运行
# ============================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step() {
  echo ""
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}  步骤 $1: $2${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

cmd() {
  echo -e "${CYAN}  \$ $1${NC}"
  echo ""
  echo -e "  ${GREEN}(请在终端中手动执行上述命令)${NC}"
  echo ""
  read -p "  按回车继续..."
}

step "0" "前置检查"
echo "  确认 Claude CLI 已安装："
cmd "claude --version"

echo "  确认已登录："
cmd "claude auth status"

step "1" "基本对话模式"
echo "  最简单的使用方式，像聊天一样："
cmd "claude"
echo "  进入后输入: 用 Go 写一个计算两个日期之间天数的函数"
echo ""
echo "  💡 讲解要点:"
echo "  - 这是最基础的用法，大部分人停在这里"
echo "  - 但 Claude CLI 的真正威力在后面..."

step "2" "单次命令模式"
echo "  不进入交互模式，直接执行一次性任务："
cmd "echo '分析这段代码的问题' | claude"
echo ""
echo "  或者结合管道使用："
cmd "cat src/main.go | claude '这段代码有什么安全隐患？'"

step "3" "Agent 模式 — 让 AI 干活"
echo "  这才是核心！Claude CLI 不只能聊天，它能直接操作你的项目："
echo ""
echo "  进入项目目录后启动 claude："
cmd "cd /path/to/your/project && claude"
echo ""
echo "  然后给它一个真实任务，例如："
echo ""
echo -e "  ${CYAN}给这个项目的订单模块添加日志功能：${NC}"
echo -e "  ${CYAN}1. 在每个请求入口和出口添加结构化日志${NC}"
echo -e "  ${CYAN}2. 日志要包含：请求ID、耗时、状态码、结果${NC}"
echo -e "  ${CYAN}3. 敏感信息（用户数据）要脱敏处理${NC}"
echo -e "  ${CYAN}4. 使用 slog 包${NC}"
echo ""
echo "  💡 讲解要点:"
echo "  - Claude 会先阅读项目结构和相关代码"
echo "  - 然后制定计划并逐步执行"
echo "  - 每一步都会请求你的确认（安全！）"
echo "  - 它可以：读文件、写文件、运行命令、搜索代码"

step "4" "工具使用演示"
echo "  在 Claude CLI 会话中，AI 可以使用以下工具："
echo ""
echo "  📁 文件操作: Read, Write, Edit"
echo "  🔍 搜索: Grep (内容搜索), Glob (文件搜索)"
echo "  💻 命令执行: Bash (运行 shell 命令)"
echo "  🌐 网络: WebFetch, WebSearch"
echo ""
echo "  观察 AI 在执行任务时如何自动选择和调用这些工具"

step "5" "Claude CLI vs 普通聊天"
echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │  普通聊天（ChatGPT/网页版）     │"
echo "  │  • 你复制代码给它              │"
echo "  │  • 它给你建议                  │"
echo "  │  • 你手动修改代码              │"
echo "  │  • 你再复制新的问题...          │"
echo "  └─────────────────────────────────┘"
echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │  Claude CLI                     │"
echo "  │  • 它自己读取代码              │"
echo "  │  • 它自己理解项目结构           │"
echo "  │  • 它自己修改文件              │"
echo "  │  • 它自己运行测试验证           │"
echo "  │  • 你只需要审核和确认           │"
echo "  └─────────────────────────────────┘"
echo ""
echo "  这就是 '把 AI 当人用' 的具体体现！"

step "6" "实用技巧"
echo "  1. /help     — 查看所有可用命令"
echo "  2. /compact  — 压缩上下文（对话太长时用）"
echo "  3. /clear    — 清空对话重新开始"
echo "  4. Ctrl+C    — 中断当前操作"
echo "  5. 支持 MCP  — 可以连接外部工具和服务"
echo ""
echo "  CLAUDE.md 文件 = .cursorrules 的 CLI 版本"
echo "  在项目根目录创建 CLAUDE.md，定义 AI 的行为规范"

step "完成" "演示结束"
echo "  核心信息："
echo "  • Claude CLI 不是聊天工具，是终端里的 AI 工程师"
echo "  • Cursor + Claude CLI = 最强组合"
echo "  • 关键是给它足够的上下文和清晰的指令"
echo "  • 从今天起，试着把重复性工作交给它"
