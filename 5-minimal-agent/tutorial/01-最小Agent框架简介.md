# 第五章：最小 Agent 框架

## 本章目标

了解最轻量的 Agent 框架：
1. agent-c 超轻量实现
2. tinyagents 最小实现
3. Pocket Flow 极简框架
4. 从零写一个最小 Agent
5. 实战：50 行代码实现 Agent

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

## 5.2 agent-c 超轻量框架

### 5.2.1 简介

**agent-c** 是目前最小的 C 语言 Agent 框架：

- 二进制大小：~4KB (macOS), ~16KB (Linux)
- 调用 OpenRouter API
- 支持工具调用
- 支持对话记忆

### 5.2.2 项目地址

[GitHub - senx/agent-c](https://github.com/senx/agent-c)

### 5.2.3 安装

```bash
# 克隆
git clone https://github.com/senx/agent-c.git
cd agent-c

# 编译
make

# 运行
./agent-c --api-key YOUR_KEY "你的问题"
```

### 5.2.4 使用示例

```bash
# 简单对话
./agent-c --api-key $OPENROUTER_KEY "你好"

# 执行命令
./agent-c --api-key $OPENROUTER_KEY "帮我执行 ls -la"

# 多轮对话
./agent-c --api-key $OPENROUTER_KEY
```

### 5.2.5 核心代码解析

```c
// agent-c 核心逻辑简化版
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 工具结构
typedef struct {
    char* name;
    char* description;
    char* (*execute)(char* args);
} Tool;

// 执行工具
char* execute_tool(Tool* tools, int n_tools, char* tool_name, char* args) {
    for (int i = 0; i < n_tools; i++) {
        if (strcmp(tools[i].name, tool_name) == 0) {
            return tools[i].execute(args);
        }
    }
    return "Tool not found";
}

// 主循环
void agent_loop(Tool* tools, int n_tools) {
    char input[4096];

    while (1) {
        printf("> ");
        fgets(input, sizeof(input), stdin);

        // 移除换行
        input[strlen(input)-1] = 0;

        if (strcmp(input, "exit") == 0) break;

        // 调用 LLM (实际使用 curl)
        char* response = call_llm_api(input);

        // 解析响应
        if (has_tool_call(response)) {
            char* tool = get_tool_name(response);
            char* args = get_tool_args(response);

            // 执行工具
            char* result = execute_tool(tools, n_tools, tool, args);

            // 循环
            printf("Tool result: %s\n", result);
        } else {
            printf("%s\n", response);
        }
    }
}

int main() {
    // 初始化工具
    Tool tools[] = {
        {"shell", "Execute shell command", shell_execute},
        {"read", "Read file", read_file},
    };

    agent_loop(tools, 2);
    return 0;
}
```

---

## 5.3 tinyagents 最小实现

### 5.3.1 简介

**tinyagents** 是最小的 Python Agent 框架之一，专注于 MCP (Model Context Protocol)。

### 5.3.2 项目地址

[GitHub - tinyagents/tinyagents](https://github.com/tinyagents/tinyagents)

### 5.3.3 核心代码

```python
# 最小的 Agent 实现 (约 50 行)

import json
import requests

class TinyAgent:
    def __init__(self, api_key, model="openai/gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.messages = []
        self.tools = {}

    def tool(self, name, description):
        """装饰器：注册工具"""
        def decorator(func):
            self.tools[name] = {"func": func, "description": description}
            return func
        return decorator

    def chat(self, message):
        # 添加用户消息
        self.messages.append({"role": "user", "content": message})

        # 构建请求
        payload = {
            "model": self.model,
            "messages": self.messages,
            "tools": self._build_tools_schema()
        }

        # 调用 API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )

        result = response.json()["choices"][0]["message"]

        # 检查工具调用
        if "tool_calls" in result:
            self.messages.append(result)

            for call in result["tool_calls"]:
                tool_name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])

                # 执行工具
                tool_result = self.tools[tool_name]["func"](**args)

                # 添加结果
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": str(tool_result)
                })

            # 再次调用获取最终回复
            return self.chat("")  # 继续循环

        self.messages.append(result)
        return result["content"]

    def _build_tools_schema(self):
        schema = []
        for name, info in self.tools.items():
            schema.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info["description"],
                    "parameters": {"type": "object", "properties": {}}
                }
            })
        return schema


# 使用示例
agent = TinyAgent("your-api-key")

@agent.tool("shell", "Execute shell command")
def run_shell(cmd):
    import subprocess
    return subprocess.check_output(cmd, shell=True).decode()

# 对话
print(agent.chat("执行 ls -la"))
```

---

## 5.4 Pocket Flow 极简框架

### 5.4.1 简介

**Pocket Flow** 是一个极简的 LLM 框架，仅用约 100 行代码实现。支持多种语言，专注于构建基于流式处理的 Agent。

### 5.4.2 项目地址

[GitHub - pocket-flow/pocket-flow](https://github.com/pocket-flow/pocket-flow)

### 5.4.3 核心特性

- 极简代码：约 100 行
- 流式处理支持
- 多语言实现
- 易于扩展

### 5.4.4 安装与使用

```bash
# 安装
pip install pocket-flow

# 基本使用
from pocket import Pocket

agent = Pocket()
response = agent.chat("你好")
print(response)
```

### 5.4.5 核心代码结构

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

## 5.5 从零实现最小 Agent

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
- ✅ agent-c 超轻量框架
- ✅ tinyagents 最小实现
- ✅ Pocket Flow 极简框架
- ✅ 50 行代码实现 Agent

---

## 5.6 参考资源

- [agent-c](https://github.com/senx/agent-c) - 超轻量 C Agent
- [tinyagents](https://github.com/tinyagents/tinyagents) - 最小 Python Agent
- [Pocket Flow](https://github.com/pocket-flow/pocket-flow) - 极简 LLM 框架
- [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - 纯 C LLM
- [karpathy/llm.c](https://github.com/karpathy/llm.c) - 纯 C 训练 LLM
