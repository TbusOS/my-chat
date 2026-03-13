#!/usr/bin/env python3
"""
AI 培训 — 现场演示：用 Python SDK 调用大模型

使用前安装依赖：
    pip install openai anthropic google-generativeai

使用方法：
    python 02-python-api.py              # 运行所有演示
    python 02-python-api.py --test       # 测试 API 连通性
    python 02-python-api.py --openai     # 只演示 OpenAI
    python 02-python-api.py --claude     # 只演示 Claude
    python 02-python-api.py --gemini     # 只演示 Gemini
    python 02-python-api.py --compare    # temperature 对比实验
    python 02-python-api.py --tool-use   # 工具调用演示
"""

import os
import sys
import json
import argparse


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_step(step, desc):
    print(f"\033[34m▶ [{step}] {desc}\033[0m")


# ============================================================
# Demo 1: OpenAI GPT
# ============================================================
def demo_openai():
    print_header("OpenAI GPT-4o 调用演示")

    try:
        from openai import OpenAI
    except ImportError:
        print("  ⚠️  请先安装: pip install openai")
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("  ⚠️  OPENAI_API_KEY 未设置")
        return

    client = OpenAI(api_key=api_key)

    print_step("1", "基本调用")
    print("  模型: gpt-4o")
    print("  temperature: 0.3")
    print()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是资深后端工程师，回答简洁专业。"},
            {"role": "user", "content": "微服务架构中的请求链路追踪流程是什么？"}
        ],
        temperature=0.3,
        max_tokens=300
    )

    print(f"  回答: {response.choices[0].message.content}")
    print(f"\n  Token 用量:")
    print(f"    输入: {response.usage.prompt_tokens} tokens")
    print(f"    输出: {response.usage.completion_tokens} tokens")
    print(f"    总计: {response.usage.total_tokens} tokens")


# ============================================================
# Demo 2: Anthropic Claude
# ============================================================
def demo_claude():
    print_header("Anthropic Claude Sonnet 调用演示")

    try:
        import anthropic
    except ImportError:
        print("  ⚠️  请先安装: pip install anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  ANTHROPIC_API_KEY 未设置")
        return

    client = anthropic.Anthropic(api_key=api_key)

    print_step("1", "基本调用")
    print("  模型: claude-sonnet-4-20250514")
    print("  temperature: 0.3")
    print()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        system="你是资深后端工程师，回答简洁专业。",
        messages=[
            {"role": "user", "content": "微服务架构中的请求链路追踪流程是什么？"}
        ],
        max_tokens=300,
        temperature=0.3
    )

    print(f"  回答: {response.content[0].text}")
    print(f"\n  Token 用量:")
    print(f"    输入: {response.usage.input_tokens} tokens")
    print(f"    输出: {response.usage.output_tokens} tokens")


# ============================================================
# Demo 3: Google Gemini
# ============================================================
def demo_gemini():
    print_header("Google Gemini Pro 调用演示")

    try:
        import google.generativeai as genai
    except ImportError:
        print("  ⚠️  请先安装: pip install google-generativeai")
        return

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  ⚠️  GOOGLE_API_KEY 未设置")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-pro",
        system_instruction="你是资深后端工程师，回答简洁专业。"
    )

    print_step("1", "基本调用")
    print("  模型: gemini-pro")
    print("  temperature: 0.3")
    print()

    response = model.generate_content(
        "微服务架构中的请求链路追踪流程是什么？",
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=300
        )
    )

    print(f"  回答: {response.text}")


# ============================================================
# Demo 4: Temperature 对比实验
# ============================================================
def demo_compare():
    print_header("Temperature 对比实验")

    try:
        import anthropic
    except ImportError:
        print("  ⚠️  请先安装: pip install anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  ANTHROPIC_API_KEY 未设置")
        return

    client = anthropic.Anthropic(api_key=api_key)
    prompt = "用一个比喻来描述微服务架构的作用"

    print(f"  提示词: {prompt}")
    print()

    for temp in [0.0, 0.5, 1.0]:
        print_step(f"temp={temp}", f"temperature = {temp}")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            system="你是一位有创意的科技作家。",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=temp
        )

        print(f"  {response.content[0].text}")
        print()


# ============================================================
# Demo 5: 工具调用 (Tool Use)
# ============================================================
def demo_tool_use():
    print_header("工具调用 (Tool Use) 演示")

    try:
        import anthropic
    except ImportError:
        print("  ⚠️  请先安装: pip install anthropic")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ⚠️  ANTHROPIC_API_KEY 未设置")
        return

    client = anthropic.Anthropic(api_key=api_key)

    # 定义工具
    tools = [
        {
            "name": "query_orders",
            "description": "查询系统订单记录",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单ID"
                    },
                    "date_range": {
                        "type": "string",
                        "description": "日期范围，格式: YYYY-MM-DD~YYYY-MM-DD"
                    }
                },
                "required": ["order_id"]
            }
        }
    ]

    print_step("1", "定义工具")
    print(f"  工具名: query_orders")
    print(f"  描述: 查询系统订单记录")
    print()

    print_step("2", "发送请求，让模型决定是否调用工具")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        system="你是订单查询助手。当用户询问订单信息时，使用 query_orders 工具查询。",
        messages=[
            {"role": "user", "content": "帮我查一下订单号 ORD-20240315-001 的详情"}
        ],
        tools=tools,
        max_tokens=500
    )

    print(f"  停止原因: {response.stop_reason}")
    print()

    for block in response.content:
        if block.type == "tool_use":
            print_step("3", "模型决定调用工具")
            print(f"  工具: {block.name}")
            print(f"  参数: {json.dumps(block.input, ensure_ascii=False, indent=4)}")
            print()
            print("  → 在实际应用中，这里会执行真正的数据库查询")
            print("  → 然后将结果返回给模型，让模型生成最终回答")


# ============================================================
# 连通性测试
# ============================================================
def test_connectivity():
    print_header("API 连通性测试")

    services = {
        "OpenAI": ("OPENAI_API_KEY", "openai"),
        "Anthropic": ("ANTHROPIC_API_KEY", "anthropic"),
        "Google": ("GOOGLE_API_KEY", "google.generativeai"),
    }

    for name, (env_var, package) in services.items():
        key = os.environ.get(env_var)
        has_key = "✅" if key else "❌"

        try:
            __import__(package)
            has_pkg = "✅"
        except ImportError:
            has_pkg = "❌"

        print(f"  {name:12s}  Key: {has_key}  Package: {has_pkg}")

    print()


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="AI 培训 — Python SDK 演示")
    parser.add_argument("--test", action="store_true", help="测试 API 连通性")
    parser.add_argument("--openai", action="store_true", help="OpenAI 演示")
    parser.add_argument("--claude", action="store_true", help="Claude 演示")
    parser.add_argument("--gemini", action="store_true", help="Gemini 演示")
    parser.add_argument("--compare", action="store_true", help="Temperature 对比")
    parser.add_argument("--tool-use", action="store_true", help="工具调用演示")
    args = parser.parse_args()

    if args.test:
        test_connectivity()
        return

    run_all = not any([args.openai, args.claude, args.gemini, args.compare, args.tool_use])

    if run_all or args.openai:
        demo_openai()
    if run_all or args.claude:
        demo_claude()
    if run_all or args.gemini:
        demo_gemini()
    if run_all or args.compare:
        demo_compare()
    if run_all or args.tool_use:
        demo_tool_use()

    print_header("演示完成！")


if __name__ == "__main__":
    main()
