# nanoGPT 从零训练教程

> 使用 Karpathy 的 nanoGPT 在本地从零训练一个小型 GPT 模型

> **类型**: 外部项目教程 | **前置**: Python 基础 | **硬件**: Apple Silicon (MPS) / NVIDIA GPU

## 本章目录

### 教程 (Tutorial)
- [Mac 训练指南](tutorial/01-Mac训练指南.md) - 在 macOS 上用 MPS 加速训练
- [Ubuntu 训练指南](tutorial/02-Ubuntu训练指南.md) - 在 Ubuntu 上用 CUDA 加速训练

### 理论 (Theory)
- [nanoGPT 架构解析](theory/01-nanoGPT架构解析.md) - 300 行代码的 GPT-2 实现
- [训练数据准备](theory/02-训练数据准备.md) - 数据清洗、Tokenization、数据格式
- [训练过程监控](theory/03-训练过程监控.md) - Loss 曲线、学习率调度、过拟合判断

### 实战 (Hands-on)
- [训练你的第一个 GPT](hands-on/01-训练你的第一个GPT.md) - 完整训练流程
- [常见训练问题排查](hands-on/02-常见训练问题排查.md) - Loss 不降、OOM、梯度爆炸等

---

## 什么是 nanoGPT？

[nanoGPT](https://github.com/karpathy/nanoGPT) 是 Andrej Karpathy 开发的最简洁 GPT 训练代码，约 300 行 PyTorch 实现完整的 GPT-2 训练流程。

| 特性 | 说明 |
|------|------|
| 代码量 | ~300 行核心代码 |
| 依赖 | 仅 PyTorch + NumPy |
| 训练数据 | Shakespeare、OpenWebText 等 |
| 硬件 | CPU / MPS (Mac) / CUDA (GPU) |

### 与其他项目的关系

```
minGPT (教学用，不再维护)
   ↓
nanoGPT (生产级，当前推荐)
   ↓
llm.c (纯 C 实现，更底层)
```

---

## 参考资源

- [nanoGPT GitHub](https://github.com/karpathy/nanoGPT)
- [Karpathy 视频教程](https://www.youtube.com/watch?v=kCc8FmEb1nY) - "Let's build GPT"
- [minGPT](https://github.com/karpathy/minGPT)
- [llm.c](https://github.com/karpathy/llm.c)
