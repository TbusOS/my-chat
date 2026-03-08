#!/usr/bin/env python3
"""
工具调用 Agent
功能：让 Agent 能够调用外部工具（函数）

使用方法:
    python examples/tool_agent.py
"""

import ollama
import json
from datetime import datetime
from typing import Dict, List, Any, Callable


class ToolAgent:
    """支持工具调用的 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        self.messages: List[Dict] = []
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable, description: str):
        """注册工具"""
        self.tools[name] = func

    def _build_tools_description(self) -> List[Dict]:
        """构建工具描述（供模型理解）"""
        tools_description = []
        for name, func in self.tools.items():
            tools_description.append({
                'type': 'function',
                'function': {
                    'name': name,
                    'description': func.__doc__ or '',
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            })
        return tools_description

    def chat(self, user_input: str, max_tool_calls: int = 3) -> str:
        """带工具调用的对话"""
        self.messages.append({'role': 'user', 'content': user_input})
        tools_desc = self._build_tools_description()

        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            tools=tools_desc
        )

        tool_calls = response['message'].get('tool_calls', [])

        if not tool_calls:
            final_msg = response['message']['content']
            self.messages.append({'role': 'assistant', 'content': final_msg})
            return final_msg

        for _ in range(max_tool_calls):
            if not tool_calls:
                break

            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function'].get('arguments', {})

                if tool_name in self.tools:
                    try:
                        if tool_args:
                            result = self.tools[tool_name](**tool_args)
                        else:
                            result = self.tools[tool_name]()

                        self.messages.append({
                            'role': 'tool',
                            'name': tool_name,
                            'content': str(result)
                        })
                    except Exception as e:
                        self.messages.append({
                            'role': 'tool',
                            'name': tool_name,
                            'content': f"工具执行错误: {e}"
                        })

            response = ollama.chat(
                model=self.model,
                messages=self.messages
            )
            tool_calls = response['message'].get('tool_calls', [])

        final_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': final_msg})
        return final_msg


# ============== 工具函数 ==============

def get_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")


def calculator(expression: str) -> str:
    """简单计算器"""
    allowed_chars = set('0123456789+-*/.() ')
    if all(c in allowed_chars for c in expression):
        result = eval(expression)
        return str(result)
    return "非法字符"


def weather(city: str) -> str:
    """模拟天气查询"""
    weather_data = {
        "北京": "晴，15-25°C",
        "上海": "多云，18-27°C",
        "广州": "雨，22-30°C",
        "深圳": "晴，23-29°C",
    }
    return weather_data.get(city, f"未知{city}的天气情况")


# ============== 使用示例 ==============

if __name__ == "__main__":
    agent = ToolAgent("qwen2.5")

    agent.register_tool("get_time", get_time, "获取当前时间")
    agent.register_tool("calculator", calculator, "进行数学计算")
    agent.register_tool("weather", weather, "查询天气")

    print("=" * 50)
    print("工具调用 Agent 测试")
    print("=" * 50)

    tests = [
        "现在几点了？",
        "123 * 456 等于多少？",
        "北京今天天气怎么样？",
    ]

    for q in tests:
        print(f"\n用户: {q}")
        response = agent.chat(q)
        print(f"助手: {response}")
