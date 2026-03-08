#!/usr/bin/env python3
"""
多角色 Manager Agent
功能：一个主 Agent 管理多个专业子 Agent，自动路由到合适的角色

使用方法:
    python examples/manager_agent.py
"""

import ollama
from typing import List, Dict


class SubAgent:
    """子 Agent"""

    def __init__(self, role: str, system_prompt: str, model: str = "qwen2.5"):
        self.role = role
        self.model = model
        self.messages: List[Dict] = [
            {'role': 'system', 'content': system_prompt}
        ]

    def chat(self, user_input: str) -> str:
        self.messages.append({'role': 'user', 'content': user_input})
        response = ollama.chat(model=self.model, messages=self.messages)
        assistant_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': assistant_msg})
        return assistant_msg


class ManagerAgent:
    """管理多个子 Agent 的主 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        self.sub_agents: Dict[str, SubAgent] = {
            'general': SubAgent('general', '你是一个乐于助人的通用AI助手。'),
            'coder': SubAgent('coder', '你是编程专家，回答时给出完整代码示例并解释逻辑。'),
            'writer': SubAgent('writer', '你是写作专家，语言流畅、结构清晰。'),
            'researcher': SubAgent('researcher', '你是研究助手，擅长信息检索和结构化分析。'),
        }

    def _determine_role(self, user_input: str) -> str:
        """根据用户输入确定应该使用哪个子 Agent"""
        prompt = f"""根据用户的问题，确定最适合的助手类型。
可选：general, coder, writer, researcher
用户问题：{user_input}
只返回类型名称。"""

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        role = response['message']['content'].strip().lower()
        if role not in self.sub_agents:
            role = 'general'
        return role

    def chat(self, user_input: str) -> str:
        role = self._determine_role(user_input)
        print(f"  [路由到: {role}]")
        return self.sub_agents[role].chat(user_input)


if __name__ == "__main__":
    manager = ManagerAgent("qwen2.5")

    print("=" * 50)
    print("Manager Agent 测试")
    print("=" * 50)

    questions = [
        "今天天气怎么样？",
        "Python怎么实现快速排序？",
        "帮我写一封辞职信",
        "对比 Python 和 JavaScript 的优缺点",
    ]

    for q in questions:
        print(f"\n用户: {q}")
        response = manager.chat(q)
        print(f"助手: {response[:300]}..." if len(response) > 300 else f"助手: {response}")
