# 最小 Agent 框架

> **类型**: 理论专题 | **前置**: 建议先读 [1-ollama-agent](../1-ollama-agent/) | **硬件**: 无要求

## 本章目录

### 教程 (Tutorial)
- [最小 Agent 框架简介](tutorial/01-最小Agent框架简介.md)
- [主流 Agent 框架对比](tutorial/02-主流Agent框架对比.md)

### 理论 (Theory)
- [Agent 核心原理](theory/01-Agent核心原理.md)
- [Tool Calling 机制详解](theory/02-ToolCalling机制详解.md)

### 实战 (Hands-on)
- [从零实现最小 Agent](hands-on/01-从零实现最小Agent.md)
- [实战：带记忆的多工具 Agent](hands-on/02-带记忆的多工具Agent.md)
- [生产部署指南](hands-on/03-生产部署指南.md)

---

## 核心内容

### 1. 什么是 Agent？

```
Agent = LLM + 工具 + 记忆 + 循环
```

一个 Agent 的完整工作流：

```
用户输入 → LLM 理解意图 → 是否需要工具？
                              ↓ 是
                         选择工具 → 执行 → 将结果返回 LLM
                              ↓ 否
                         直接回复用户
```

### 2. 最小的 Agent 框架

| 框架 | 语言 | 大小 | 特点 | 适用场景 |
|------|------|------|------|----------|
| smolagents | Python | 轻量 | Hugging Face 官方 | 快速原型 |
| Pocket Flow | 多语言 | 100行 | 极简流式处理 | 学习理解 |
| LangChain | Python | 重量级 | 功能最全 | 生产应用 |
| CrewAI | Python | 中等 | 多 Agent 协作 | 复杂任务 |

### 3. 核心原理

| 概念 | 说明 |
|------|------|
| ReAct 模式 | 思考 → 行动 → 观察，循环直到完成 |
| Function Calling | LLM 输出结构化的工具调用请求 |
| Chain of Thought | 让 LLM 先推理再行动，提升准确率 |
| Memory | 短期（对话历史）+ 长期（向量数据库） |
| Planning | 将复杂任务分解为子步骤 |

### 4. 实现方式

| 方式 | 代码量 | 适用场景 |
|------|--------|----------|
| 50 行 Python | 最小 | 学习原理 |
| 100 行 Python | 带工具注册 | 快速原型 |
| 完整框架 | 500+ 行 | 生产使用 |

### 5. 生产部署

本章新增了生产部署指南，涵盖：
- 错误处理和重试机制
- API 限流和超时控制
- 日志和监控
- Docker 容器化部署
- 安全最佳实践

---

## 快速上手

```python
#!/usr/bin/env python3
"""最小 Agent - 30 行代码"""

import requests

def agent(question, model="qwen2.5"):
    messages = [{"role": "user", "content": question}]
    tools = [{
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {"expr": {"type": "string"}},
                "required": ["expr"]
            }
        }
    }]

    for _ in range(5):
        resp = requests.post("http://localhost:11434/api/chat",
            json={"model": model, "messages": messages, "tools": tools, "stream": False}
        ).json()

        msg = resp["message"]
        if not msg.get("tool_calls"):
            return msg["content"]

        for call in msg["tool_calls"]:
            result = str(eval(call["function"]["arguments"]["expr"]))
            messages.append(msg)
            messages.append({"role": "tool", "content": result})

    return "达到最大轮次"

print(agent("123 * 456 等于多少？"))
```

---

## 参考资源

- [smolagents](https://github.com/huggingface/smolagents) - Hugging Face 轻量 Agent 框架
- [Pocket Flow](https://github.com/The-Pocket/PocketFlow) - 极简 LLM 框架
- [LangChain](https://github.com/langchain-ai/langchain) - 全功能 LLM 应用框架
- [CrewAI](https://github.com/crewAIInc/crewAI) - 多 Agent 协作框架
- [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - 纯 C LLM
- [karpathy/llm.c](https://github.com/karpathy/llm.c) - 纯 C 训练 LLM
