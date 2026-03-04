#!/usr/bin/env python3
"""
简单 Agent 类
支持多轮对话、上下文记忆
"""

import ollama
from typing import List, Dict, Optional


class SimpleAgent:
    """简单的对话 Agent"""

    def __init__(
        self,
        model: str = "qwen2.5",
        system_prompt: str = "你是一个有帮助的AI助手。",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.messages: List[Dict] = []

        # 初始化系统提示词
        if system_prompt:
            self.messages.append({
                'role': 'system',
                'content': system_prompt
            })

    def reset(self):
        """清空对话历史，保留系统提示词"""
        if self.system_prompt:
            self.messages = [{'role': 'system', 'content': self.system_prompt}]
        else:
            self.messages = []

    def chat(self, user_input: str) -> str:
        """发送对话，返回助手回复"""
        self.messages.append({'role': 'user', 'content': user_input})

        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            options={
                'temperature': self.temperature,
                'num_predict': self.max_tokens,
            }
        )

        assistant_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': assistant_msg})

        return assistant_msg

    def stream_chat(self, user_input: str):
        """流式对话"""
        self.messages.append({'role': 'user', 'content': user_input})

        for chunk in ollama.chat(
            model=self.model,
            messages=self.messages,
            stream=True,
            options={
                'temperature': self.temperature,
                'num_predict': self.max_tokens,
            }
        ):
            yield chunk['message']['content']

        # 更新消息历史
        full_response = ""
        self.messages.append({'role': 'user', 'content': user_input})


# 使用示例
if __name__ == "__main__":
    # 创建 Agent
    agent = SimpleAgent(
        model="qwen2.5",
        system_prompt="你是一个Python编程专家，用中文回答问题。"
    )

    # 单轮对话
    response = agent.chat("Python怎么定义函数？")
    print(f"助手: {response}\n")

    # 多轮对话（会自动保留上下文）
    response = agent.chat("那JavaScript呢？")
    print(f"助手: {response}\n")

    # 流式输出
    print("流式输出示例:")
    for chunk in agent.stream_chat("给我讲个笑话"):
        print(chunk, end='', flush=True)
    print("\n")

    # 清空对话
    agent.reset()
    print("对话已清空，重新开始...")
