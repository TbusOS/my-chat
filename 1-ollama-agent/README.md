# Ollama + Python 实现本地 Agent

> 使用 Ollama 在本地运行大模型，快速构建各类 Agent

> **类型**: 可直接运行 | **前置**: 无 | **硬件**: CPU 即可

## 本章目录

### 教程 (Tutorial)
- [快速入门](tutorial/01-快速入门.md) - 安装 Ollama、下载模型、运行对话
- [模型使用指南](tutorial/02-模型使用指南.md) - 常用模型对比、参数说明
- [Python API 详解](tutorial/03-Python-API详解.md) - 同步/异步调用、流式输出

### 理论 (Theory)
- [LLM 基础概念](theory/01-LLM基础概念.md) - 什么是大模型、为什么本地运行
- [Transformer 简介](theory/02-Transformer简介.md) - Transformer 架构入门

### 实战 (Hands-on)
- [天气 Agent 实战](hands-on/01-天气Agent实战.md) - 意图识别 + 实体提取 + API 调用
- [工具 Agent 实战](hands-on/02-工具Agent实战.md) - 让 Agent 调用外部工具
- [RAG Agent 实战](hands-on/03-RAG-Agent实战.md) - 检索增强生成

### 可运行示例 (Examples)
- [`agent.py`](agent.py) - SimpleAgent：多轮对话 + 上下文记忆
- [`chat.py`](chat.py) - 交互式聊天界面
- [`examples/tool_agent.py`](examples/tool_agent.py) - 工具调用 Agent
- [`examples/rag_agent.py`](examples/rag_agent.py) - RAG 检索增强 Agent
- [`examples/weather_agent.py`](examples/weather_agent.py) - 天气预报 Agent
- [`examples/manager_agent.py`](examples/manager_agent.py) - 多角色 Manager Agent

---

## 快速开始

```bash
# 1. 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. 下载模型
ollama pull qwen2.5

# 3. 安装 Python 依赖
pip install ollama

# 4. 运行示例
python agent.py
python examples/tool_agent.py
```

## 硬件要求

| 显存 | 能跑的模型 |
|------|-----------|
| 无 GPU | 3B 以下模型 |
| 8GB | 7B 模型 (量化版) |
| 16GB | 7B/8B 模型 |
| 24GB | 13B 模型 |

**初学者推荐**：`qwen2.5:7b`，中文能力强，资源占用适中。

---

## 参考链接

- [Ollama 官网](https://ollama.com)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Ollama Python 库](https://github.com/ollama/ollama-python)
- [Model Library](https://ollama.com/library)
