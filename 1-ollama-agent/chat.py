#!/usr/bin/env python3
"""
Ollama Agent 完整示例
功能：支持多轮对话、上下文记忆、系统提示词
"""

import ollama
import json

def main():
    print("=" * 50)
    print("Ollama Agent Demo")
    print("=" * 50)

    # 初始化 Agent
    model = "qwen2.5"

    # 系统提示词
    system_prompt = """你是一个专业的编程助手，擅长Python、JavaScript、Go等语言。
请用简洁清晰的语言回答问题，适当给出代码示例。"""

    messages = [{'role': 'system', 'content': system_prompt}]

    print(f"\n使用模型: {model}")
    print("输入 'quit' 或 'exit' 退出\n")

    while True:
        user_input = input("你: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见!")
            break

        if not user_input:
            continue

        messages.append({'role': 'user', 'content': user_input})

        try:
            response = ollama.chat(model=model, messages=messages)
            assistant_msg = response['message']['content']

            print(f"\n助手: {assistant_msg}\n")
            messages.append({'role': 'assistant', 'content': assistant_msg})

        except Exception as e:
            print(f"错误: {e}")
            break


if __name__ == "__main__":
    main()
