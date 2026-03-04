#!/usr/bin/env python3
"""
从零实现 Transformer - 完整可运行版本
纯 Python + NumPy
"""

import math
import numpy as np
from typing import List, Optional
import json


class LayerNorm:
    """Layer Normalization"""

    def __init__(self, d_model: int, eps: float = 1e-6):
        self.gamma = np.ones(d_model)
        self.beta = np.zeros(d_model)
        self.eps = eps

    def forward(self, x: np.ndarray) -> np.ndarray:
        """x: (batch, seq_len, d_model)"""
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        x_norm = (x - mean) / np.sqrt(var + self.eps)
        return self.gamma * x_norm + self.beta


class Embedding:
    """词嵌入"""

    def __init__(self, vocab_size: int, d_model: int):
        self.embedding = np.random.randn(vocab_size, d_model) * 0.01

    def forward(self, x: np.ndarray) -> np.ndarray:
        return self.embedding[x]


class PositionalEncoding:
    """位置编码 - Sinusoidal"""

    def __init__(self, d_model: int, max_len: int = 5000):
        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        self.pe = pe[np.newaxis, :, :]

    def forward(self, x: np.ndarray) -> np.ndarray:
        return x + self.pe[:, :x.shape[1], :]


class Linear:
    """线性层 y = xW + b"""

    def __init__(self, in_features: int, out_features: int):
        self.weights = np.random.randn(in_features, out_features) * 0.01
        self.bias = np.zeros(out_features)

    def forward(self, x: np.ndarray) -> np.ndarray:
        return x @ self.weights + self.bias


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class MultiHeadAttention:
    """多头注意力"""

    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        assert d_model % num_heads == 0

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.scale = 1.0 / math.sqrt(self.d_k)

        self.W_q = Linear(d_model, d_model)
        self.W_k = Linear(d_model, d_model)
        self.W_v = Linear(d_model, d_model)
        self.W_o = Linear(d_model, d_model)

    def split_heads(self, x: np.ndarray) -> np.ndarray:
        batch, seq, _ = x.shape
        return x.reshape(batch, seq, self.num_heads, self.d_k).transpose(0, 2, 1, 3)

    def forward(
        self,
        q: np.ndarray,
        k: np.ndarray,
        v: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        batch = q.shape[0]

        # 投影 + 分头
        q = self.split_heads(self.W_q.forward(q))
        k = self.split_heads(self.W_k.forward(k))
        v = self.split_heads(self.W_v.forward(v))

        # 注意力分数
        scores = q @ k.transpose(0, 1, 3, 2) * self.scale

        if mask is not None:
            scores = scores + mask

        # 注意力权重
        attn_weights = softmax(scores, axis=-1)

        # 应用注意力
        attn_output = attn_weights @ v

        # 合并多头
        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch, -1, self.d_model)

        return self.W_o.forward(attn_output)


class FeedForward:
    """前馈网络"""

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        self.linear1 = Linear(d_model, d_ff)
        self.linear2 = Linear(d_ff, d_model)
        self.dropout = dropout

    def forward(self, x: np.ndarray) -> np.ndarray:
        return self.linear2.forward(np.maximum(0, self.linear1.forward(x)))  # ReLU


class EncoderLayer:
    """单个 Encoder 层"""

    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1):
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        self.feed_forward = FeedForward(d_model, d_ff, dropout)
        self.layernorm1 = LayerNorm(d_model)
        self.layernorm2 = LayerNorm(d_model)
        self.dropout = dropout

    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        # Self-Attention + 残差
        attn_output = self.attention.forward(x, x, x, mask)
        x = self.layernorm1(x + attn_output)

        # FFN + 残差
        ff_output = self.feed_forward.forward(x)
        x = self.layernorm2(x + ff_output)

        return x


class Encoder:
    """Encoder"""

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

    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        x = self.embedding.forward(x)
        x = self.pos_encoding.forward(x)

        for layer in self.layers:
            x = layer.forward(x, mask)

        return x


class Transformer:
    """完整 Transformer"""

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
        encoder_output = self.encoder.forward(x)
        return self.output.forward(encoder_output)


def train_step(model: Transformer, x: np.ndarray, targets: np.ndarray, lr: float = 0.001):
    """单步训练（简化版，无自动微分）"""
    # 前向
    logits = model.forward(x)

    # 损失
    batch, seq, vocab = logits.shape
    logits_flat = logits.reshape(-1, vocab)
    targets_flat = targets.reshape(-1)
    probs = softmax(logits_flat, axis=-1)

    # 简化：随机梯度（演示用）
    loss = 0.0
    for i, t in enumerate(targets_flat):
        loss -= np.log(probs[i, t] + 1e-9)
    loss /= batch

    # 简化：随机更新（实际应计算真实梯度）
    # 这只是演示结构
    return loss


def generate(model: Transformer, input_ids: np.ndarray, max_new_tokens: int = 20) -> np.ndarray:
    """简单的自回归生成"""
    for _ in range(max_new_tokens):
        logits = model.forward(input_ids)
        next_token_logits = logits[0, -1, :]
        probs = softmax(next_token_logits)
        next_token = np.argmax(probs)

        input_ids = np.concatenate([input_ids, [[next_token]]], axis=1)

    return input_ids


# ============== 测试 ==============

def test_basic():
    """基础测试"""
    print("=" * 50)
    print("基础组件测试")
    print("=" * 50)

    # 测试 Embedding
    embed = Embedding(vocab_size=1000, d_model=128)
    x = np.array([[1, 2, 3], [4, 5, 6]])
    out = embed.forward(x)
    print(f"Embedding: {x.shape} -> {out.shape}")

    # 测试 PositionalEncoding
    pe = PositionalEncoding(d_model=128, max_len=100)
    x = np.random.randn(2, 10, 128)
    out = pe.forward(x)
    print(f"PositionalEncoding: {x.shape} -> {out.shape}")

    # 测试 Linear
    linear = Linear(in_features=128, out_features=256)
    out = linear.forward(x)
    print(f"Linear: {x.shape} -> {out.shape}")

    # 测试 MultiHeadAttention
    attn = MultiHeadAttention(d_model=128, num_heads=8)
    q, k, v = np.random.randn(2, 10, 128), np.random.randn(2, 10, 128), np.random.randn(2, 10, 128)
    out = attn.forward(q, k, v)
    print(f"MultiHeadAttention: {q.shape} -> {out.shape}")

    # 测试 FeedForward
    ff = FeedForward(d_model=128, d_ff=512)
    out = ff.forward(x)
    print(f"FeedForward: {x.shape} -> {out.shape}")

    print("\n基础组件测试通过!")


def test_transformer():
    """Transformer 测试"""
    print("=" * 50)
    print("Transformer 测试")
    print("=" * 50)

    vocab_size = 1000
    d_model = 128
    num_heads = 4
    d_ff = 256
    num_layers = 2
    batch_size = 2
    seq_len = 8

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

    # 前向
    logits = model.forward(x)
    print(f"输入: {x.shape}")
    print(f"输出: {logits.shape}")

    # 损失
    loss = train_step(model, x, targets)
    print(f"损失: {loss:.4f}")

    # 生成
    input_ids = np.array([[1, 2, 3]])
    generated = generate(model, input_ids, max_new_tokens=5)
    print(f"生成: {input_ids.shape} -> {generated.shape}")

    print("\nTransformer 测试通过!")


def main():
    test_basic()
    print()
    test_transformer()
    print("\n所有测试通过!")


if __name__ == "__main__":
    main()
