# 实战：带记忆的多工具 Agent

## 本章目标

实现一个功能完整的 Agent，支持：
1. 多工具注册和调用
2. 对话记忆（多轮上下文）
3. 工具结果处理
4. 错误处理

---

## 1. 完整实现

```python
#!/usr/bin/env python3
"""
带记忆的多工具 Agent - 完整实现
依赖: pip install requests
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Callable, Any


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict] = []

    def register(self, name: str, func: Callable, description: str,
                 parameters: Dict = None):
        """注册一个工具"""
        self._tools[name] = func
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters or {
                    "type": "object", "properties": {}, "required": []
                }
            }
        })

    def execute(self, name: str, args: Dict) -> str:
        """执行工具"""
        if name not in self._tools:
            return json.dumps({"error": f"工具 '{name}' 不存在"})
        try:
            result = self._tools[name](**args) if args else self._tools[name]()
            return str(result)
        except Exception as e:
            return json.dumps({"error": f"执行失败: {e}"})

    @property
    def schemas(self) -> List[Dict]:
        return self._schemas


class Agent:
    """带记忆的多工具 Agent"""

    def __init__(self, model: str = "qwen2.5",
                 base_url: str = "http://localhost:11434",
                 system_prompt: str = "你是一个有用的助手，可以使用工具来帮助用户。"):
        self.model = model
        self.base_url = base_url
        self.tools = ToolRegistry()
        self.messages: List[Dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def chat(self, user_input: str, max_tool_rounds: int = 5) -> str:
        """主对话方法"""
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(max_tool_rounds):
            response = self._call_llm()
            message = response.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                content = message.get("content", "")
                self.messages.append({"role": "assistant", "content": content})
                return content

            # 处理工具调用
            self.messages.append(message)
            for call in tool_calls:
                name = call["function"]["name"]
                args = call["function"].get("arguments", {})
                result = self.tools.execute(name, args)
                self.messages.append({
                    "role": "tool",
                    "name": name,
                    "content": result
                })

        return "达到最大工具调用轮次"

    def reset(self):
        """重置对话历史（保留系统提示）"""
        self.messages = [self.messages[0]]

    def _call_llm(self) -> Dict:
        """调用 LLM API"""
        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": False
        }
        if self.tools.schemas:
            payload["tools"] = self.tools.schemas

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()


# ============== 工具定义 ==============

def get_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculator(expression: str) -> str:
    """安全计算器"""
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "错误: 包含非法字符"
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

def get_weather(city: str) -> str:
    """模拟天气查询"""
    weather_db = {
        "北京": "晴，20-28°C，湿度 35%",
        "上海": "多云，22-30°C，湿度 65%",
        "广州": "雷阵雨，24-32°C，湿度 80%",
        "深圳": "晴，23-29°C，湿度 60%",
        "杭州": "阴，19-26°C，湿度 55%",
    }
    return weather_db.get(city, f"暂无 {city} 的天气数据")

def search_knowledge(query: str) -> str:
    """模拟知识搜索"""
    knowledge = {
        "python": "Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年发布。",
        "transformer": "Transformer 是 2017 年提出的注意力机制架构，是现代 LLM 的基础。",
        "agent": "AI Agent 是能够自主感知环境、做出决策并执行行动的智能系统。",
    }
    for key, value in knowledge.items():
        if key in query.lower():
            return value
    return f"未找到关于 '{query}' 的信息"


# ============== 主程序 ==============

if __name__ == "__main__":
    agent = Agent(model="qwen2.5")

    # 注册工具
    agent.tools.register("get_time", get_time, "获取当前日期和时间")

    agent.tools.register("calculator", calculator, "计算数学表达式", {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 '2+3*4'"}
        },
        "required": ["expression"]
    })

    agent.tools.register("get_weather", get_weather, "查询城市天气", {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"}
        },
        "required": ["city"]
    })

    agent.tools.register("search_knowledge", search_knowledge, "搜索知识库", {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        },
        "required": ["query"]
    })

    # 交互式对话
    print("Agent 已启动（输入 'quit' 退出，'reset' 重置对话）")
    print("-" * 50)

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("对话已重置")
            continue
        if not user_input:
            continue

        response = agent.chat(user_input)
        print(f"\nAgent: {response}")
```

---

## 2. 使用示例

```
你: 现在几点了？
Agent: 现在是 2024-12-15 14:30:22。

你: 帮我算一下 (123 + 456) * 789
Agent: (123 + 456) * 789 = 456,111。

你: 北京和上海的天气分别怎么样？
Agent: 北京今天晴天，气温 20-28°C，湿度 35%。
       上海今天多云，气温 22-30°C，湿度 65%。

你: 什么是 Transformer？
Agent: Transformer 是 2017 年提出的注意力机制架构，是现代 LLM 的基础。
```

---

## 3. 代码结构解析

```
Agent
├── ToolRegistry          # 工具管理
│   ├── register()        # 注册工具
│   ├── execute()         # 执行工具（带错误处理）
│   └── schemas           # 工具描述（给 LLM 看）
├── messages              # 对话历史（记忆）
├── chat()                # 主入口（循环调用 LLM + 工具）
├── reset()               # 清除记忆
└── _call_llm()           # HTTP 调用 Ollama API
```

---

## 4. 关键设计点

### 4.1 为什么需要循环？

一次工具调用可能不够。比如用户问"北京和上海天气对比"，LLM 可能需要：
1. 第一轮：调用 get_weather("北京") 和 get_weather("上海")
2. 第二轮：基于两个结果生成对比总结

### 4.2 为什么需要 max_tool_rounds？

防止 LLM 陷入无限工具调用循环。常见设置 3-10 轮。

### 4.3 错误处理策略

```python
# 工具不存在 → 返回错误信息给 LLM，让它调整
# 工具执行异常 → 捕获异常，返回错误信息
# LLM API 超时 → requests timeout=120
```

---

## 5. 本章小结

- [x] 完整的多工具 Agent 实现
- [x] 工具注册表模式
- [x] 对话记忆管理
- [x] 错误处理
- [x] 交互式使用
