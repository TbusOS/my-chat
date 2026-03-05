# 第五章：最小 Agent 框架

## 本章目标

了解最轻量的 Agent 框架：
1. smolagents 轻量实现
2. Pocket Flow 极简框架
3. 从零写一个最小 Agent
4. 实战：50 行代码实现 Agent

---

## 5.1 最小的 Agent 是什么？

### 5.1.1 Agent 核心逻辑

```
Agent = LLM + 循环 + 工具调用
```

一个最简单的 Agent 只需要：

1. 调用 LLM API
2. 解析响应
3. 如果需要工具，执行工具
4. 循环直到完成

### 5.1.2 代码核心

```c
// 最简单的 Agent (伪代码)
while (true) {
    // 1. 获取用户输入
    char* input = get_input();

    // 2. 调用 LLM
    char* response = call_llm(input);

    // 3. 解析响应
    if (need_tool(response)) {
        // 4. 执行工具
        char* result = execute_tool(response);
        // 5. 把结果发给 LLM
        input = result;
    } else {
        // 6. 输出结果
        print(response);
        break;
    }
}
```

---

## 5.2 smolagents 轻量框架

### 5.2.1 简介

**smolagents** 是 Hugging Face 官方推出的轻量级 Agent 框架：

- 简洁的 Python 实现
- 支持多种 LLM (OpenAI, Anthropic, 本地模型等)
- 内置工具调用支持
- 支持 Code Agent 模式

### 5.2.2 项目地址

[GitHub - huggingface/smolagents](https://github.com/huggingface/smolagents)

### 5.2.3 安装

```bash
pip install smolagents
```

### 5.2.4 使用示例

```python
from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel

# 创建 Agent
agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=HfApiModel()
)

# 执行任务
result = agent.run("搜索最新的 AI 新闻")
print(result)
```

### 5.2.5 核心代码结构

```python
from smolagents import Agent

# 简单 Agent
agent = Agent()

# 添加自定义工具
@agent.tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    return str(eval(expression))

# 对话
response = agent.chat("计算 123 * 456")
print(response)
```

---

## 5.3 Pocket Flow 极简框架

### 5.3.1 简介

**Pocket Flow** 是一个极简的 LLM 框架，仅用约 100 行代码实现。支持多种语言，专注于构建基于流式处理的 Agent。

### 5.3.2 项目地址

[GitHub - The-Pocket/PocketFlow](https://github.com/The-Pocket/PocketFlow)

### 5.3.3 核心特性

- 极简代码：约 100 行
- 流式处理支持
- 多语言实现
- 易于扩展

### 5.3.4 安装与使用

```bash
# 安装
pip install pocket-flow

# 基本使用
from pocket import Pocket

agent = Pocket()
response = agent.chat("你好")
print(response)
```

### 5.3.5 核心代码结构

```python
# Pocket Flow 核心概念
class Pocket:
    def __init__(self):
        self.messages = []
        self.tools = {}

    def tool(self, name, description):
        """装饰器注册工具"""
        def decorator(func):
            self.tools[name] = {"func": func, "description": description}
            return func
        return decorator

    def chat(self, message):
        """主对话方法"""
        # 实现流式处理逻辑
        pass
```

---

## 5.4 从零实现最小 Agent

### 5.4.1 50 行代码实现

```python
#!/usr/bin/env python3
"""
最小的 Agent 实现 - 50 行代码
"""

import json
import os

# 模拟 LLM API (用 curl 调用)
def call_llm(messages, tools=None):
    import subprocess
    import json

    data = {
        "model": "qwen/qwen2.5-7b-instruct",
        "messages": messages,
        "temperature": 0.7
    }
    if tools:
        data["tools"] = tools

    # 这里用 curl 调用本地 Ollama
    cmd = 'curl -s http://localhost:11434/api/chat -d @- <<EOF\n' + json.dumps(data) + '\nEOF'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

# 简单 Agent
class Agent:
    def __init__(self):
        self.messages = []

    def run(self, user_input, max_turns=5):
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(max_turns):
            response = call_llm(self.messages)
            msg = response["message"]

            if "tool_calls" in msg:
                self.messages.append(msg)

                for call in msg["tool_calls"]:
                    # 执行工具 (这里模拟)
                    result = f"执行了: {call['function']['name']}"
                    self.messages.append({
                        "role": "tool",
                        "content": result
                    })
            else:
                self.messages.append(msg)
                return msg["content"]

        return "达到最大轮次"


# 使用
if __name__ == "__main__":
    agent = Agent()
    print(agent.run("你好"))
```

---

## 5.5 本章小结

- ✅ 理解最小 Agent 核心逻辑
- ✅ smolagents 轻量框架
- ✅ Pocket Flow 极简框架
- ✅ 50 行代码实现 Agent

---

## 5.6 参考资源

- [smolagents](https://github.com/huggingface/smolagents) - Hugging Face 轻量 Agent 框架
- [Pocket Flow](https://github.com/The-Pocket/PocketFlow) - 极简 LLM 框架
- [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - 纯 C LLM
- [karpathy/llm.c](https://github.com/karpathy/llm.c) - 纯 C 训练 LLM
