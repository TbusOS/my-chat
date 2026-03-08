# 自建 LLM 完整学习指南

> 从使用到原理，由简入难的大模型学习路径 | A Complete Guide for Learning LLM from Scratch

## 目录结构

```
my-chat/
├── 1-ollama-agent/          # Ollama 快速入门
├── 2-litgpt-finetune/       # LitGPT 微调
├── 3-nn-from-zero/          # 从零实现神经网络
├── 4-llama-cpp-native/      # llama.cpp 原生实现
├── 5-minimal-agent/         # 最小 Agent 框架
├── 6-nanoGPT-train/         # nanoGPT 从零训练
├── 7-tokenizer/             # 分词器原理与实现
├── 8-rag-deepdive/          # RAG 检索增强生成
├── 9-rlhf-alignment/        # RLHF 对齐技术
├── 10-model-evaluation/     # 模型评估方法
├── requirements.txt
└── LICENSE
```

## 学习路径

本仓库提供**两条学习路径**，按你的需求选择：

### 路径 A：由简入难（推荐新手）

先用起来，再理解原理。适合想**快速上手**的开发者。

```
1-ollama-agent    用 Ollama 跑起来
       ↓
2-litgpt-finetune 学会微调模型
       ↓
3-nn-from-zero    理解底层原理
       ↓
4-llama-cpp-native C++ 原生推理
       ↓
5-minimal-agent   构建 Agent 应用
       ↓
6-nanoGPT-train   从零训练 GPT
       ↓
7~10 进阶专题      分词器 / RAG / 对齐 / 评估
```

### 路径 B：原理优先

先打基础，再做应用。适合想**深入理解**大模型的学习者。

```
3-nn-from-zero    神经网络基础
       ↓
6-nanoGPT-train   理解训练流程
       ↓
7-tokenizer       分词器原理
       ↓
1-ollama-agent    快速使用模型
       ↓
2-litgpt-finetune 微调定制模型
       ↓
4-llama-cpp-native 推理优化
       ↓
5-minimal-agent   构建应用
       ↓
8~10 进阶专题      RAG / 对齐 / 评估
```

---

## 各模块概览

### 1-ollama-agent | 入门

使用 Ollama 快速运行本地 LLM，构建各类 Agent。

| 类别 | 文档 |
|------|------|
| 教程 | 快速入门 · 模型使用指南 · Python API |
| 理论 | LLM 基础概念 · Transformer 简介 |
| 实战 | 天气 Agent · 工具 Agent · RAG Agent |
| 示例 | `agent.py` · `chat.py` · `examples/*.py` |

### 2-litgpt-finetune | 进阶

使用 LitGPT 框架微调自己的模型。

| 类别 | 文档 |
|------|------|
| 教程 | 微调入门 · 环境配置 · 训练流程 |
| 理论 | 什么是微调 · LoRA 原理 · QLoRA 原理 |
| 实战 | 数据准备 · LoRA 训练 · 模型测试部署 |

### 3-nn-from-zero | 原理

纯 Python + NumPy 从零实现 Transformer。

| 类别 | 文档 |
|------|------|
| 教程 | 神经网络基础 · 反向传播 · PyTorch 入门 |
| 理论 | Attention 机制 · 多头注意力 · 位置编码 · 残差 LayerNorm · Transformer 架构 |
| 实战 | 最小 GPT · 多头注意力 · 位置编码 · 完整 Encoder · GPT 训练 |

### 4-llama-cpp-native | 原生

C++ 原生实现 LLM 推理，深入性能优化。

| 类别 | 文档 |
|------|------|
| 教程 | C++ 基础 · CMake 构建 |
| 理论 | llama.cpp 架构 · GGUF 格式 · 量化技术 · 推理优化 · 采样策略 |
| 实战 | 环境搭建 · 模型加载 · 聊天机器人 · HTTP 服务器 · CUDA 加速 |

### 5-minimal-agent | 极简

用最少代码实现 Agent 框架。

| 类别 | 文档 |
|------|------|
| 教程 | Agent 框架简介 · 主流框架对比 |
| 理论 | Agent 核心原理 · Tool Calling 机制 |
| 实战 | 从零实现 Agent · 多工具 Agent · 生产部署指南 |

### 6-nanoGPT-train | 训练

用 nanoGPT 从零训练一个 GPT 模型。

| 类别 | 文档 |
|------|------|
| 教程 | Mac 训练指南 (MPS) · Ubuntu 训练指南 (CUDA) |
| 理论 | nanoGPT 架构解析 · 训练数据准备 · 训练过程监控 |
| 实战 | 训练你的第一个 GPT · 常见训练问题排查 |

### 7-tokenizer | 分词器

理解文本如何变成模型可处理的 token。

| 类别 | 文档 |
|------|------|
| 教程 | 分词器入门 |
| 理论 | BPE 算法详解 |
| 实战 | 从零实现 BPE 分词器 |

### 8-rag-deepdive | RAG 深入

构建生产级检索增强生成系统。

| 类别 | 文档 |
|------|------|
| 教程 | RAG 基础概念 |
| 理论 | 向量检索原理 |
| 实战 | 构建本地知识库 |

### 9-rlhf-alignment | 对齐

理解 ChatGPT 为什么"听话"。

| 类别 | 文档 |
|------|------|
| 教程 | 对齐技术入门 |
| 理论 | RLHF 原理详解 · DPO 原理详解 |
| 实战 | DPO 微调实战 |

### 10-model-evaluation | 评估

如何科学评估模型质量。

| 类别 | 文档 |
|------|------|
| 教程 | 评估方法入门 |
| 理论 | 评估指标详解 |
| 实战 | 评估你的模型 |

---

## 文档统计

| 目录 | 教程 | 理论 | 实战 | 示例代码 | 总计 |
|------|------|------|------|----------|------|
| 1-ollama-agent | 3 | 2 | 3 | 6 | **14** |
| 2-litgpt-finetune | 3 | 3 | 3 | 2 | **11** |
| 3-nn-from-zero | 3 | 5 | 5 | 1 | **14** |
| 4-llama-cpp-native | 2 | 5 | 5 | 1 | **13** |
| 5-minimal-agent | 2 | 2 | 3 | - | **7** |
| 6-nanoGPT-train | 2 | 3 | 2 | - | **7** |
| 7-tokenizer | 1 | 1 | 1 | 1 | **4** |
| 8-rag-deepdive | 1 | 1 | 1 | 1 | **4** |
| 9-rlhf-alignment | 1 | 2 | 1 | - | **4** |
| 10-model-evaluation | 1 | 1 | 1 | 1 | **4** |
| **总计** | **19** | **25** | **25** | **13** | **82** |

---

## 推荐的 GitHub 项目

| 项目 | 描述 | 链接 |
|------|------|------|
| **llama2.c** | 纯 C 实现 Llama2，约 500 行 | [GitHub](https://github.com/karpathy/llama2.c) |
| **llm.c** | 纯 C 实现 GPT-2 训练 | [GitHub](https://github.com/karpathy/llm.c) |
| **nanoGPT** | 最简洁的 GPT 训练实现 | [GitHub](https://github.com/karpathy/nanoGPT) |
| **minGPT** | PyTorch 最小 GPT 实现 | [GitHub](https://github.com/karpathy/minGPT) |
| **tinygrad** | 最小深度学习框架 | [GitHub](https://github.com/tinygrad/tinygrad) |
| **ggml** | C++ 张量库 | [GitHub](https://github.com/ggerganov/ggml) |
| **smolagents** | Hugging Face 轻量 Agent 框架 | [GitHub](https://github.com/huggingface/smolagents) |
| **Pocket Flow** | 100 行实现 LLM 框架 | [GitHub](https://github.com/The-Pocket/PocketFlow) |

---

## 开始学习

```bash
# 克隆仓库
git clone https://github.com/TbusOS/my-chat.git
cd my-chat

# 安装依赖
pip install -r requirements.txt

# 路径 A：从 Ollama 开始
cd 1-ollama-agent

# 路径 B：从神经网络原理开始
cd 3-nn-from-zero
```

---

## 贡献

欢迎提交 Pull Request！

## 许可证

[MIT License](LICENSE)
