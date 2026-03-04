#!/usr/bin/env python3
"""
llama.cpp 服务器包装器
通过 Python 调用 llama.cpp 的 HTTP API
"""

import requests
import json
import time
from typing import List, Dict, Optional


class LlamaCppClient:
    """llama.cpp 服务器客户端"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama-2-7b-chat",
        temperature: float = 0.7,
        max_tokens: int = 256
    ) -> str:
        """发送聊天请求"""
        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def completion(
        self,
        prompt: str,
        model: str = "llama-2-7b-chat",
        temperature: float = 0.7,
        max_tokens: int = 256
    ) -> str:
        """补全请求"""
        url = f"{self.base_url}/v1/completions"

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["text"]

    def embeddings(self, text: str) -> List[float]:
        """获取文本嵌入"""
        url = f"{self.base_url}/v1/embeddings"

        payload = {
            "model": "llama-2-7b-chat",
            "input": text
        }

        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["data"][0]["embedding"]


class LlamaCppAgent:
    """基于 llama.cpp 的 Agent"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.client = LlamaCppClient(base_url)
        self.messages = []
        self.system_prompt = ""

    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt

    def reset(self):
        """重置对话"""
        self.messages = []

    def chat(self, user_input: str) -> str:
        """发送对话"""
        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        messages.extend(self.messages)
        messages.append({"role": "user", "content": user_input})

        response = self.client.chat(messages)

        self.messages.append({"role": "user", "content": user_input})
        self.messages.append({"role": "assistant", "content": response})

        return response


# ============== 使用示例 ==============

def demo_basic():
    """基础使用示例"""
    print("=" * 50)
    print("基础使用示例")
    print("=" * 50)

    # 确保 llama.cpp 服务器正在运行
    # ./build/bin/llama-server -m models/llama-2-7b-chat.Q4_K_M.gguf

    client = LlamaCppClient("http://localhost:8080")

    # 简单补全
    prompt = "Write a hello world program in Python:"
    print(f"Prompt: {prompt}")
    response = client.completion(prompt, max_tokens=128)
    print(f"Response: {response}\n")


def demo_chat():
    """聊天示例"""
    print("=" * 50)
    print("聊天示例")
    print("=" * 50)

    client = LlamaCppClient("http://localhost:8080")

    messages = [
        {"role": "user", "content": "What is Python?"}
    ]

    response = client.chat(messages, temperature=0.7, max_tokens=256)
    print(f"User: What is Python?")
    print(f"Assistant: {response}\n")


def demo_agent():
    """Agent 示例"""
    print("=" * 50)
    print("Agent 示例")
    print("=" * 50)

    agent = LlamaCppAgent("http://localhost:8080")
    agent.set_system_prompt("You are a helpful programming assistant.")

    # 第一轮对话
    response = agent.chat("How do I define a function in Python?")
    print(f"User: How do I define a function in Python?")
    print(f"Assistant: {response}\n")

    # 第二轮对话（保持上下文）
    response = agent.chat("What about JavaScript?")
    print(f"User: What about JavaScript?")
    print(f"Assistant: {response}\n")


def demo_streaming():
    """流式输出示例（需要服务器支持）"""
    print("=" * 50)
    print("流式输出示例")
    print("=" * 50)

    import sseclient
    import urllib.request

    url = "http://localhost:8080/v1/completions"
    payload = {
        "model": "llama-2-7b-chat",
        "prompt": "Count from 1 to 5:",
        "stream": True,
        "max_tokens": 50
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')

    with urllib.request.urlopen(req) as response:
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data and event.data != "[DONE]":
                chunk = json.loads(event.data)
                if chunk["choices"]:
                    text = chunk["choices"][0]["text"]
                    print(text, end='', flush=True)
    print()


def main():
    """主函数"""
    print("llama.cpp Python Client Demo")
    print("请确保 llama.cpp 服务器正在运行:")
    print("  ./build/bin/llama-server -m models/llama-2-7b-chat.Q4_K_M.gguf")
    print()

    try:
        demo_basic()
    except Exception as e:
        print(f"基础示例错误: {e}")

    try:
        demo_chat()
    except Exception as e:
        print(f"聊天示例错误: {e}")

    try:
        demo_agent()
    except Exception as e:
        print(f"Agent 示例错误: {e}")


if __name__ == "__main__":
    main()
