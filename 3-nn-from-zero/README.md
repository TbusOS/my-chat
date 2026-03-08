# 从零实现 Transformer 神经网络

> **类型**: 可直接运行 | **前置**: Python 基础 | **硬件**: CPU 即可

## 概述

不依赖 PyTorch/TensorFlow 等深度学习框架，用纯 Python + NumPy 从零实现 Transformer 架构。

## 环境要求

```bash
pip install numpy
```

## 完整代码实现

```python
#!/usr/bin/env python3
"""
从零实现 Transformer
纯 Python + NumPy，无第三方深度学习框架
"""

import math
import numpy as np
from typing import List, Tuple
import json


# ============== 基础组件 ==============

class Embedding:
    """词嵌入层"""
    def __init__(self, vocab_size: int, d_model: int):
        # 简单初始化：使用正态分布
        self.embedding = np.random.randn(vocab_size, d_model) * 0.1
        self.d_model = d_model

    def forward(self, x: np.ndarray) -> np.ndarray:
        """x: (batch, seq_len) -> (batch, seq_len, d_model)"""
        return self.embedding[x]


class PositionalEncoding:
    """位置编码"""
    def __init__(self, d_model: int, max_len: int = 5000):
        self.d_model = d_model

        # 创建位置编码矩阵
        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))

        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        pe = pe[np.newaxis, :, :]  # (1, max_len, d_model)

        self.pe = pe

    def forward(self, x: np.ndarray) -> np.ndarray:
        """x: (batch, seq_len, d_model)"""
        seq_len = x.shape[1]
        return x + self.pe[:, :seq_len, :]


class Linear:
    """线性层"""
    def __init__(self, in_features: int, out_features: int):
        self.weights = np.random.randn(in_features, out_features) * 0.1
        self.bias = np.zeros(out_features)

    def forward(self, x: np.ndarray) -> np.ndarray:
        return x @ self.weights + self.bias


# ============== Attention ==============

def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Softmax 函数"""
    exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class MultiHeadAttention:
    """多头注意力机制"""
    def __init__(self, d_model: int, num_heads: int):
        assert d_model % num_heads == 0

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # Q、K、V 投影矩阵
        self.W_q = Linear(d_model, d_model)
        self.W_k = Linear(d_model, d_model)
        self.W_v = Linear(d_model, d_model)

        # 输出投影
        self.W_o = Linear(d_model, d_model)

    def split_heads(self, x: np.ndarray) -> np.ndarray:
        """分割多头
        x: (batch, seq_len, d_model)
        -> (batch, num_heads, seq_len, d_k)
        """
        batch, seq_len, _ = x.shape
        x = x.reshape(batch, seq_len, self.num_heads, self.d_k)
        return x.transpose(0, 2, 1, 3)

    def forward(
        self,
        q: np.ndarray,
        k: np.ndarray,
        v: np.ndarray,
        mask: np.ndarray = None
    ) -> np.ndarray:
        """
        q, k, v: (batch, seq_len, d_model)
        返回: (batch, seq_len, d_model)
        """
        batch = q.shape[0]

        # 线性投影 + 分割多头
        q = self.split_heads(self.W_q.forward(q))
        k = self.split_heads(self.W_k.forward(k))
        v = self.split_heads(self.W_v.forward(v))

        # 计算 Attention
        # scores: (batch, num_heads, seq_len_q, seq_len_k)
        scores = q @ k.transpose(0, 1, 3, 2) / math.sqrt(self.d_k)

        # 掩码处理
        if mask is not None:
            scores = scores + mask

        # Attention 权重
        attn_weights = softmax(scores, axis=-1)

        # _apply attention to values
        # attn_weights: (batch, num_heads, seq_len_q, seq_len_k)
        # v: (batch, num_heads, seq_len_v, d_k)
        attn_output = attn_weights @ v

        # 合并多头
        # (batch, num_heads, seq_len_q, d_k) -> (batch, seq_len_q, d_model)
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch, -1, self.d_model)

        # 输出投影
        return self.W_o.forward(attn_output)


# ============== Feed Forward ==============

class FeedForward:
    """前馈网络"""
    def __init__(self, d_model: int, d_ff: int):
        self.linear1 = Linear(d_model, d_ff)
        self.linear2 = Linear(d_ff, d_model)

    def forward(self, x: np.ndarray) -> np.ndarray:
        return self.linear2.forward(np.maximum(0, self.linear1.forward(x)))  # ReLU


# ============== Encoder Layer ==============

class EncoderLayer:
    """单个 Encoder 层"""
    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1):
        self.attention = MultiHeadAttention(d_model, num_heads)
        self.feed_forward = FeedForward(d_model, d_ff)

        self.layernorm1 = lambda x: x  # 简化版，不实现 LayerNorm
        self.layernorm2 = lambda x: x

        self.dropout = dropout

    def forward(self, x: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
        # Self-Attention + 残差
        attn_output = self.attention.forward(x, x, x, mask)
        x = self.layernorm1(x + attn_output)

        # Feed Forward + 残差
        ff_output = self.feed_forward.forward(x)
        x = self.layernorm2(x + ff_output)

        return x


class Encoder:
    """完整 Encoder"""
    def __init__(
        self,
        vocab_size: int,
        d_model: int,
        num_heads: int,
        d_ff: int,
        num_layers: int,
        dropout: float = 0.1
    ):
        self.embedding = Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model)

        self.layers = [
            EncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ]

    def forward(self, x: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
        # 嵌入 + 位置编码
        x = self.embedding.forward(x)
        x = self.pos_encoding.forward(x)

        # 堆叠 Encoder 层
        for layer in self.layers:
            x = layer.forward(x, mask)

        return x


# ============== Transformer 主模型 ==============

class Transformer:
    """完整 Transformer 模型（简化版）"""
    def __init__(
        self,
        vocab_size: int,
        d_model: int = 512,
        num_heads: int = 8,
        d_ff: int = 2048,
        num_layers: int = 6,
        dropout: float = 0.1
    ):
        self.encoder = Encoder(
            vocab_size, d_model, num_heads, d_ff, num_layers, dropout
        )
        self.output = Linear(d_model, vocab_size)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """前向传播"""
        encoder_output = self.encoder.forward(x)
        logits = self.output.forward(encoder_output)
        return logits


# ============== 训练相关 ==============

def cross_entropy_loss(logits: np.ndarray, targets: np.ndarray) -> float:
    """交叉熵损失（简化版）"""
    batch_size, seq_len, vocab_size = logits.shape

    # 展平
    logits_flat = logits.reshape(-1, vocab_size)
    targets_flat = targets.reshape(-1)

    # Softmax
    probs = softmax(logits_flat, axis=-1)

    # 交叉熵
    # 简化：使用负对数似然
    loss = 0.0
    for i, target in enumerate(targets_flat):
        loss -= np.log(probs[i, target] + 1e-9)

    return loss / batch_size


def gradient_descent_update(params: List[np.ndarray], grads: List[np.ndarray], lr: float):
    """简单的梯度下降更新"""
    for param, grad in zip(params, grads):
        param -= lr * grad


# ============== 使用示例 ==============

def demo():
    """演示"""
    # 超参数
    vocab_size = 10000
    d_model = 256
    num_heads = 8
    d_ff = 1024
    num_layers = 4
    batch_size = 2
    seq_len = 10

    # 创建模型
    model = Transformer(
        vocab_size=vocab_size,
        d_model=d_model,
        num_heads=num_heads,
        d_ff=d_ff,
        num_layers=num_layers
    )

    # 随机输入
    x = np.random.randint(0, vocab_size, size=(batch_size, seq_len))
    targets = np.random.randint(0, vocab_size, size=(batch_size, seq_len))

    # 前向传播
    logits = model.forward(x)
    print(f"输入形状: {x.shape}")
    print(f"输出形状: {logits.shape}")

    # 计算损失
    loss = cross_entropy_loss(logits, targets)
    print(f"损失: {loss:.4f}")

    # 这是一个完整的 Transformer 实现框架
    # 实际训练需要：
    # 1. 实现完整的 LayerNorm
    # 2. 实现 Adam 优化器
    # 3. 添加数据加载器
    # 4. 添加训练循环


if __name__ == "__main__":
    demo()
    print("\n=== Transformer 从零实现完成 ===")
```

## 代码结构说明

```
从零实现包含以下组件：

1. 基础组件
   - Embedding: 词嵌入
   - PositionalEncoding: 位置编码
   - Linear: 线性层

2. Attention 机制
   - softmax: 归一化指数函数
   - MultiHeadAttention: 多头注意力

3. 前馈网络
   - FeedForward: 两层线性变换 + ReLU

4. Encoder
   - EncoderLayer: 单层 Encoder（Attention + FFN + 残差）
   - Encoder: 多个 Encoder 层堆叠

5. 完整模型
   - Transformer: 编码器 + 输出层
```

## 学习路线

### 第一阶段：理解 Attention

```python
# 理解核心公式
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

### 第二阶段：理解 Multi-Head

```python
# 多头并行计算
head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
MultiHead(Q, K, V) = Concat(head_1, ..., head_h)W^O
```

### 第三阶段：理解残差和归一化

- 残差连接：解决深层网络梯度问题
- LayerNorm：稳定训练

### 第四阶段：完整组装

- 嵌入层 → 位置编码 → N×Encoder层 → 输出

## 参考资源

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - 原始论文
- [The Annotated Transformer](http://nlp.seas.harvard.edu/2018/04/03/attention.html) - 详细注释版
- [Neural Networks from Zero](https://github.com/dair-ai/nn-from-scratch) - 理论基础
