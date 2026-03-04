# 残差连接与 LayerNorm

## 本章目标

理解残差连接和归一化的作用：
1. 残差连接
2. 梯度问题
3. LayerNorm
4. 整体作用

---

## 1.1 残差连接 (Residual Connection)

### 1.1.1 什么是残差？

```
输出 = F(x) + x

其中 F(x) 是残差函数
```

### 1.1.2 直观理解

```
普通网络: x → F(x) → 输出
残差网络: x → F(x) → + → 输出
                 ↑
                 x ( shortcuts / skip connection )
```

---

## 1.2 解决梯度问题

### 1.2.1 深层网络问题

深层网络训练困难的原因：
- 梯度消失
- 梯度爆炸

### 1.2.2 残差如何解决

```
反向传播时：
∂(F(x)+x)/∂x = ∂F/∂x + 1

即使 ∂F/∂x 很小，加 1 也能保证梯度有效传递
```

---

## 1.3 Layer Normalization

### 1.3.1 公式

```
LayerNorm(x) = γ * (x - μ) / σ + β

其中:
μ = mean(x)    # 均值
σ = std(x)     # 标准差
γ, β: 可学习参数
```

### 1.3.2 对比

| 方法 | 维度 | 适用场景 |
|------|------|----------|
| BatchNorm | 批次维度 | 批次大且稳定 |
| LayerNorm | 特征维度 | 序列模型、变长输入 |

---

## 1.4 在 Transformer 中的作用

### 1.4.1 典型结构

```
x → MultiHeadAttention → Add & Norm → FeedForward → Add & Norm
  ↑                              ↑
  └─────── shortcuts ───────────┘
```

### 1.4.2 完整代码

```python
import torch
import torch.nn as nn

class TransformerBlock(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()

        # 多头注意力
        self.attention = nn.MultiheadAttention(d_model, num_heads, dropout=dropout)
        self.norm1 = nn.LayerNorm(d_model)

        # 前馈网络
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        self.norm2 = nn.LayerNorm(d_model)

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # 多头注意力 + 残差
        attn_output, _ = self.attention(x, x, x, mask=mask)
        x = self.norm1(x + self.dropout(attn_output))

        # 前馈网络 + 残差
        ffn_output = self.ffn(x)
        x = self.norm2(x + self.dropout(ffn_output))

        return x
```

---

## 1.5 本章小结

- ✅ 残差连接原理
- ✅ 解决梯度问题
- ✅ LayerNorm
- ✅ Transformer 中的应用
