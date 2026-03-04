# 从零实现最小 Agent

## 本章目标

手把手实现一个最小的 Agent：
1. 纯 Python 实现
2. 支持工具调用
3. 支持对话记忆
4. 完整代码示例

---

## 1.1 核心架构

```
┌─────────────────────────────────┐
│           Agent                 │
├─────────────────────────────────┤
│  messages: 对话历史             │
│  tools: 工具注册表             │
│  llm: LLM 调用接口            │
├─────────────────────────────────┤
│  chat(): 主入口                │
│  register_tool(): 注册工具      │
│  _execute_tool(): 执行工具     │
└─────────────────────────────────┘
```

---

## 1.2 完整代码

```python
#!/usr/bin/env python3
"""
最小 Agent 实现 - 100 行代码
支持: 工具调用、对话记忆、多轮对话
"""

import json
import requests
from typing import Dict, List, Callable, Any

class Agent:
    """最小 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        self.messages: List[Dict] = []
        self.tools: Dict[str, Callable] = {}
        self.tools_schema: List[Dict] = []

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict = None
    ):
        """注册工具"""
        self.tools[name] = func
        self.tools_schema.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })

    def call_llm(self, messages: List[Dict]) -> Dict:
        """调用 LLM (使用 Ollama)"""
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self.tools_schema if self.tools_schema else None,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=120)
        return response.json()

    def execute_tool(self, name: str, args: Dict) -> str:
        """执行工具"""
        if name not in self.tools:
            return f"错误: 工具 {name} 不存在"

        try:
            if args:
                return str(self.tools[name](**args))
            else:
                return str(self.tools[name]())
        except Exception as e:
            return f"执行错误: {e}"

    def chat(self, user_input: str, max_loops: int = 5) -> str:
        """主对话流程"""
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(max_loops):
            # 调用 LLM
            response = self.call_llm(self.messages)
            message = response.get("message", {})

            # 检查工具调用
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # 无工具调用，返回结果
                assistant_msg = message.get("content", "")
                self.messages.append({"role": "assistant", "content": assistant_msg})
                return assistant_msg

            # 处理工具调用
            for call in tool_calls:
                tool_name = call["function"]["name"]
                tool_args = call["function"].get("arguments", {})

                # 执行工具
                result = self.execute_tool(tool_name, tool_args)

                # 添加结果到消息
                self.messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result
                })

        return "达到最大循环次数"


# ============== 使用示例 ==============

# 工具函数
def get_time():
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculator(expr: str):
    """计算器"""
    try:
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expr):
            return str(eval(expr))
        return "非法表达式"
    except Exception as e:
        return f"错误: {e}"

def get_weather(city: str):
    """查询天气"""
    weather_db = {
        "北京": "晴，20-28°C",
        "上海": "多云，22-30°C",
        "广州": "雨，24-32°C",
    }
    return weather_db.get(city, f"未知{city}天气")


# 运行
if __name__ == "__main__":
    # 创建 Agent
    agent = Agent("qwen2.5")

    # 注册工具
    agent.register_tool("get_time", get_time, "获取当前时间")
    agent.register_tool("calculator", calculator, "进行数学计算", {
        "type": "object",
        "properties": {
            "expr": {"type": "string", "description": "数学表达式"}
        },
        "required": ["expr"]
    })
    agent.register_tool("get_weather", get_weather, "查询城市天气", {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名"}
        },
        "required": ["city"]
    })

    # 测试
    print("=== 测试 1: 时间查询 ===")
    print(agent.chat("现在几点了？"))

    print("\n=== 测试 2: 计算 ===")
    print(agent.chat("123 * 456 等于多少？"))

    print("\n=== 测试 3: 天气 ===")
    print(agent.chat("北京今天天气怎么样？"))

    print("\n=== 测试 4: 多轮 ===")
    agent.messages = []  # 清空
    print(agent.chat("我想查下上海的天气"))
    print(agent.chat("那北京呢？"))
```

---

## 1.3 代码解析

### 1.3.1 核心组件

| 组件 | 作用 |
|------|------|
| messages | 对话历史 |
| tools | 工具注册表 |
| tools_schema | 工具描述 (给 LLM 看) |
| call_llm | LLM API 调用 |
| execute_tool | 工具执行 |

### 1.3.2 工作流程

```
1. 用户输入
2. 添加到 messages
3. 调用 LLM
4. 检查 tool_calls
5. 有工具 → 执行 → 添加结果 → 循环
6. 无工具 → 返回结果
```

---

## 1.4 C 语言版本

```c
// 最小的 C 语言 Agent (伪代码)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 工具结构
typedef struct {
    char* name;
    char* (*func)();
} Tool;

// 执行工具
char* execute_tool(Tool* tools, int n, char* name) {
    for (int i = 0; i < n; i++) {
        if (strcmp(tools[i].name, name) == 0) {
            return tools[i].func();
        }
    }
    return "Tool not found";
}

int main() {
    // 注册工具
    Tool tools[] = {
        {"get_time", get_time},
        {"calculator", calculator},
    };

    // 主循环
    while (1) {
        printf("> ");
        char input[1024];
        fgets(input, 1024, stdin);

        // 调用 LLM API
        char* response = call_llm_api(input);

        // 解析响应
        if (has_tool_call(response)) {
            char* tool = get_tool_name(response);
            char* result = execute_tool(tools, 2, tool);
            printf("Tool: %s\n", result);
        } else {
            printf("%s\n", response);
        }
    }

    return 0;
}
```

---

## 1.5 本章小结

- ✅ 核心架构
- ✅ Python 实现 (100 行)
- ✅ 代码解析
- ✅ C 语言伪代码
