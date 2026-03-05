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
| smolagents | Python | 轻量 | Hugging Face 官方 Agent 框架 |
| Pocket Flow | 多语言 | 100行 | LLM 框架 |

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

- [smolagents](https://github.com/huggingface/smolagents) - Hugging Face 轻量 Agent 框架
- [Pocket Flow](https://github.com/The-Pocket/PocketFlow) - 极简 LLM 框架
- [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - 纯 C LLM
- [karpathy/llm.c](https://github.com/karpathy/llm.c) - 纯 C 训练 LLM
