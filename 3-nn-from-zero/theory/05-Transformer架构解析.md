# Transformer 架构解析

## 本章目标

完整理解 Transformer 架构：
1. 整体架构
2. Encoder
3. Decoder
4. 编码器-解码器交互

---

## 1.1 整体架构

### 1.1.1 架构图

```
                    Transformer
┌─────────────────────────────────────────┐
│  输入序列 (Token IDs)                    │
│  ↓                                       │
│  嵌入层 (Embedding)                     │
│  ↓                                       │
│  位置编码 (Positional Encoding)         │
│  ↓                                       │
│  ┌─────────────┐   ┌─────────────┐      │
│  │  Encoder    │   │  Decoder    │      │
│  │  × N 层     │   │  × N 层     │      │
│  └─────────────┘   └─────────────┘      │
│  ↓                      ↑               │
│  输出表示              输入             │
└─────────────────────────────────────────┘
```

### 1.1.2 主要组件

| 组件 | 作用 |
|------|------|
| Embedding | 词嵌入 |
| Positional Encoding | 位置编码 |
| Encoder | 编码输入 |
| Decoder | 生成输出 |

---

## 1.2 Encoder (编码器)

### 1.2.1 结构

```
Encoder Layer:
├── Multi-Head Self-Attention
├── Add & LayerNorm
├── Feed Forward Network
└── Add & LayerNorm
```

### 1.2.2 自注意力

```
每个位置可以关注所有其他位置
```

---

## 1.3 Decoder (解码器)

### 1.3.1 结构

```
Decoder Layer:
├── Masked Multi-Head Self-Attention
├── Add & LayerNorm
├── Encoder-Decoder Attention
├── Add & LayerNorm
├── Feed Forward Network
└── Add & LayerNorm
```

### 1.3.2 掩码注意力

```
训练时: 使用掩码防止看到未来位置
推理时: 自回归生成
```

### 1.3.3 编码器-解码器注意力

```
Q: 来自 Decoder
K, V: 来自 Encoder 输出
```

---

## 1.4 完整代码

```python
import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class Transformer(nn.Module):
    def __init__(self, vocab_size, d_model=512, nhead=8, num_layers=6, dim_feedforward=2048):
        super().__init__()
        self.d_model = d_model

        # 嵌入和位置编码
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model)

        # Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, nhead, dim_feedforward, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers)

        # Decoder
        decoder_layer = nn.TransformerDecoderLayer(
            d_model, nhead, dim_feedforward, batch_first=True
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers)

        # 输出
        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, src, tgt):
        # 编码
        src = self.embedding(src) * math.sqrt(self.d_model)
        src = self.pos_encoder(src)
        memory = self.encoder(src)

        # 解码
        tgt = self.embedding(tgt) * math.sqrt(self.d_model)
        tgt = self.pos_encoder(tgt)
        output = self.decoder(tgt, memory)

        return self.fc_out(output)
```

---

## 1.5 本章小结

- ✅ 整体架构
- ✅ Encoder 详解
- ✅ Decoder 详解
- ✅ 编码器-解码器交互
