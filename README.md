# 自建 LLM Agent 完整开源指南

> 面向全球开发者的从入门到精通教程 | A Complete Guide for Building Your Own LLM Agents

## 目录结构

```
my-chat/
├── 1-ollama-agent/           # Ollama 快速入门 (8 篇)
├── 2-litgpt-finetune/       # LitGPT 微调 (9 篇)
├── 3-nn-from-zero/          # 从零实现神经网络 (13 篇)
├── 4-llama-cpp-native/      # llama.cpp 原生实现 (12 篇)
└── README.md
```

## 学习路径 | Learning Path

### 入门 (适合零基础) | Beginner

**1-ollama-agent** - 使用 Ollama 快速运行本地 LLM

| 类别 | 文档 |
|------|------|
| 教程 | 快速入门 · 模型使用指南 · Python API |
| 理论 | LLM 基础概念 · Transformer 简介 |
| 实战 | 天气 Agent · 工具 Agent · RAG Agent |

### 进阶 | Intermediate

**2-litgpt-finetune** - 微调自己的模型

| 类别 | 文档 |
|------|------|
| 教程 | 微调入门 · 环境配置 · 训练流程 |
| 理论 | 什么是微调 · LoRA 原理 · QLoRA 原理 |
| 实战 | 数据准备 · LoRA 训练 · 模型测试部署 |

### 原理 | Advanced

**3-nn-from-zero** - 从零实现神经网络

| 类别 | 文档 |
|------|------|
| 教程 | 神经网络基础 · 反向传播 · PyTorch 入门 |
| 理论 | Attention 机制 · 多头注意力 · 位置编码 · 残差 LayerNorm · Transformer 架构 |
| 实战 | 最小 GPT · 多头注意力 · 位置编码 · 完整 Encoder · GPT 训练 |

### 原生 | Expert

**4-llama-cpp-native** - C++ 原生实现

| 类别 | 文档 |
|------|------|
| 教程 | C++ 基础 · CMake 构建 |
| 理论 | llama.cpp 架构 · GGUF 格式 · 量化技术 · 推理优化 · 采样策略 |
| 实战 | 环境搭建 · 模型加载 · 聊天机器人 · HTTP 服务器 · CUDA 加速 |

---

## 文档统计 | Statistics

| 目录 | 教程 | 理论 | 实战 | 总计 |
|------|------|------|------|------|
| 1-ollama-agent | 3 | 2 | 3 | **8** |
| 2-litgpt-finetune | 3 | 3 | 3 | **9** |
| 3-nn-from-zero | 3 | 5 | 5 | **13** |
| 4-llama-cpp-native | 3 | 5 | 4 | **12** |
| **总计** | **12** | **15** | **15** | **42** |

---

## 推荐的 GitHub 项目 | Recommended Projects

### 经典最小实现 | Classic Minimal Implementations

| 项目 | 描述 | 链接 |
|------|------|------|
| **llama.c** | 1000行C语言实现羊驼模型 | [GitHub](https://github.com/karpathy/llama.c) |
| **minGPT** | PyTorch 最小 GPT 实现 | [GitHub](https://github.com/karpathy/minGPT) |
| **nanoGPT** | 最简洁的 GPT 实现 | [GitHub](https://github.com/karpathy/nanoGPT) |
| **tinygrad** | 最小深度学习框架 | [GitHub](https://github.com/tinygrad/tinygrad) |
| **ggml** | C++ 张量库 | [GitHub](https://github.com/ggerganov/ggml) |

---

## 开始学习 | Getting Started

```bash
# 克隆仓库
git clone https://github.com/your-repo/my-chat.git
cd my-chat

# 从第一阶段开始
cd 1-ollama-agent
```

---

## 语言 | Language

本教程支持多语言。可以在各目录的文档中添加翻译版本。

---

## 贡献 | Contributing

欢迎提交 Pull Request！

---

## 许可证 | License

MIT License
