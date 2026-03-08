# 自建 LLM 完整学习指南

> 从使用到原理，由简入难的大模型学习路径 | A Complete Guide for Learning LLM from Scratch

## 目录结构

```
my-chat/
├── 1-ollama-agent/          # 入门 · 可直接运行
├── 2-litgpt-finetune/       # 进阶 · 外部项目教程
├── 3-nn-from-zero/          # 原理 · 可直接运行
├── 4-llama-cpp-native/      # 原生推理 · 外部项目教程
├── 5-minimal-agent/         # Agent · 理论专题
├── 6-nanoGPT-train/         # 训练 · 外部项目教程
├── 7-tokenizer/             # 分词器 · 可直接运行
├── 8-rag-deepdive/          # RAG · 可直接运行
├── 9-rlhf-alignment/        # 对齐 · 理论专题
├── 10-model-evaluation/     # 评估 · 可直接运行
├── 11-nanochat/             # 综合实战 · 外部项目教程
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
       ↓
11-nanochat       用 $100 训练你自己的 ChatGPT（毕业项目）
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
       ↓
11-nanochat       用 $100 训练你自己的 ChatGPT（毕业项目）
```

---

## 模块导航

| 模块 | 类型 | 说明 |
|------|------|------|
| [1-ollama-agent](1-ollama-agent/) | 可直接运行 | Ollama 快速入门，构建天气 Agent、工具 Agent、RAG Agent |
| [2-litgpt-finetune](2-litgpt-finetune/) | 外部项目教程 | 基于 LitGPT 学习 LoRA / QLoRA 微调 |
| [3-nn-from-zero](3-nn-from-zero/) | 可直接运行 | 纯 Python + NumPy 从零实现 Transformer |
| [4-llama-cpp-native](4-llama-cpp-native/) | 外部项目教程 | 基于 llama.cpp 学习 C++ 原生推理与量化 |
| [5-minimal-agent](5-minimal-agent/) | 理论专题 | Agent 核心原理、Tool Calling 机制 |
| [6-nanoGPT-train](6-nanoGPT-train/) | 外部项目教程 | 基于 nanoGPT 从零训练一个 GPT 模型 |
| [7-tokenizer](7-tokenizer/) | 可直接运行 | BPE 分词器原理与实现 |
| [8-rag-deepdive](8-rag-deepdive/) | 可直接运行 | 检索增强生成，构建本地知识库 |
| [9-rlhf-alignment](9-rlhf-alignment/) | 理论专题 | RLHF / DPO 对齐技术详解 |
| [10-model-evaluation](10-model-evaluation/) | 可直接运行 | 模型评估方法与指标 |
| [11-nanochat](11-nanochat/) | 外部项目教程 | 用 $100 训练完整 ChatGPT：分词 → 预训练 → SFT → RL → Web 聊天 |

> **类型说明**：「可直接运行」= 仓库内有示例代码可直接执行；「外部项目教程」= 文档引导你使用外部项目（需另行 clone）；「理论专题」= 以概念讲解为主。

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
| **nanochat** | 用 $100 训练完整 ChatGPT | [GitHub](https://github.com/karpathy/nanochat) |
| **Pocket Flow** | 100 行实现 LLM 框架 | [GitHub](https://github.com/The-Pocket/PocketFlow) |

---

## 开始学习

```bash
# 克隆仓库
git clone https://github.com/TbusOS/my-chat.git
cd my-chat

# 安装基础依赖（覆盖大部分模块）
pip install -r requirements.txt

# 路径 A：从 Ollama 开始
cd 1-ollama-agent

# 路径 B：从神经网络原理开始
cd 3-nn-from-zero
```

> **注意**：根目录 `requirements.txt` 只包含基础依赖。部分模块有额外依赖（如 `8-rag-deepdive` 需要 `chromadb`，`10-model-evaluation` 需要 `lm-eval`），请进入模块后查看各自的 README。

---

## 贡献

欢迎提交 Pull Request！

## 许可证

[MIT License](LICENSE)
