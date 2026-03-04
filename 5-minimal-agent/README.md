# 最小 Agent 框架

## 本章目录

### 教程 (Tutorial)
- [最小 Agent 框架简介](tutorial/01-最小Agent框架简介.md)

### 理论 (Theory)
- [Agent 核心原理](theory/01-Agent核心原理.md)

### 实战 (Hands-on)
- [从零实现最小 Agent](hands-on/01-从零实现最小Agent.md)

---

## 核心内容

### 1. 最小的 Agent 框架

| 框架 | 语言 | 大小 | 特点 |
|------|------|------|------|
| agent-c | C | 4KB | 超轻量，调用 OpenRouter |
| tinyagents | Python | 50行 | MCP 工具支持 |

### 2. 核心原理

- Agent = LLM + 工具 + 记忆 + 循环
- ReAct 模式：思考 → 行动 → 观察
- 工具调用机制 (Function Calling)
- 思维链 (Chain of Thought)

### 3. 实现

- 100 行 Python 实现
- C 语言伪代码
- 支持工具注册、对话记忆、多轮对话

---

## 参考资源

- [agent-c](https://github.com/senx/agent-c)
- [tinyagents](https://github.com/tinyagents/tinyagents)
- [karpathy/llama2.c](https://github.com/karpathy/llama2.c)
- [karpathy/llm.c](https://github.com/karpathy/llm.c)
