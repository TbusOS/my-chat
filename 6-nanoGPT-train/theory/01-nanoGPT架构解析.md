# nanoGPT 架构解析

## 本章目标

深入理解 nanoGPT 的代码架构：
1. 项目文件结构
2. 模型架构（GPT 类）
3. 训练流程
4. 关键设计决策

---

## 1. 项目结构

```
nanoGPT/
├── model.py          # GPT 模型定义（核心，~300行）
├── train.py          # 训练脚本
├── sample.py         # 文本生成
├── config/           # 训练配置
│   ├── train_shakespeare_char.py
│   ├── train_gpt2.py
│   └── ...
└── data/             # 数据集
    ├── shakespeare_char/
    │   └── prepare.py
    └── openwebtext/
        └── prepare.py
```

---

## 2. 模型架构

### 2.1 整体结构

```
Input tokens
    ↓
Token Embedding + Position Embedding
    ↓
Transformer Block × N
    ├── LayerNorm
    ├── Causal Self-Attention
    ├── Residual Connection
    ├── LayerNorm
    ├── MLP (Feed-Forward)
    └── Residual Connection
    ↓
LayerNorm
    ↓
Linear (lm_head) → logits
```

### 2.2 核心类

```python
class GPT(nn.Module):
    """GPT 模型"""

    def __init__(self, config):
        self.transformer = nn.ModuleDict(dict(
            wte = nn.Embedding(config.vocab_size, config.n_embd),   # token embedding
            wpe = nn.Embedding(config.block_size, config.n_embd),   # position embedding
            drop = nn.Dropout(config.dropout),
            h = nn.ModuleList([Block(config) for _ in range(config.n_layer)]),  # N 个 Transformer Block
            ln_f = nn.LayerNorm(config.n_embd),                     # 最终 LayerNorm
        ))
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # 权重绑定：lm_head 和 wte 共享权重
        self.transformer.wte.weight = self.lm_head.weight
```

### 2.3 Causal Self-Attention

```python
class CausalSelfAttention(nn.Module):
    """因果自注意力"""

    def __init__(self, config):
        # Q, K, V 投影合并为一个线性层
        self.c_attn = nn.Linear(config.n_embd, 3 * config.n_embd)
        # 输出投影
        self.c_proj = nn.Linear(config.n_embd, config.n_embd)

    def forward(self, x):
        B, T, C = x.size()

        # 计算 Q, K, V
        q, k, v = self.c_attn(x).split(self.n_embd, dim=2)

        # 重塑为多头
        q = q.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        k = k.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)
        v = v.view(B, T, self.n_head, C // self.n_head).transpose(1, 2)

        # Flash Attention（PyTorch 2.0+）
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)

        # 合并多头
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.c_proj(y)
```

### 2.4 MLP (Feed-Forward)

```python
class MLP(nn.Module):
    def __init__(self, config):
        self.c_fc   = nn.Linear(config.n_embd, 4 * config.n_embd)
        self.gelu   = nn.GELU()
        self.c_proj = nn.Linear(4 * config.n_embd, config.n_embd)

    def forward(self, x):
        x = self.c_fc(x)
        x = self.gelu(x)
        x = self.c_proj(x)
        return x
```

---

## 3. 关键设计决策

### 3.1 权重绑定

输入 embedding (`wte`) 和输出投影 (`lm_head`) 共享权重，减少 30% 参数。

### 3.2 Flash Attention

使用 PyTorch 2.0 的 `scaled_dot_product_attention`，自动启用 Flash Attention，减少显存、提升速度。

### 3.3 Pre-norm vs Post-norm

nanoGPT 使用 **Pre-LayerNorm**（先 Norm 再 Attention），训练更稳定：

```
x → LayerNorm → Attention → + x → LayerNorm → MLP → + x
```

### 3.4 torch.compile

Linux + CUDA 上可启用 `torch.compile`，将 Python 代码编译为优化内核，加速约 2 倍。

---

## 4. GPT-2 模型配置对比

| 模型 | n_layer | n_head | n_embd | 参数量 |
|------|---------|--------|--------|--------|
| GPT-2 Small | 12 | 12 | 768 | 124M |
| GPT-2 Medium | 24 | 16 | 1024 | 350M |
| GPT-2 Large | 36 | 20 | 1280 | 774M |
| GPT-2 XL | 48 | 25 | 1600 | 1558M |
| nanoGPT 教程 | 6 | 6 | 384 | ~10M |

---

## 5. 本章小结

- [x] 项目文件结构
- [x] GPT 模型各组件（Embedding, Attention, MLP, LayerNorm）
- [x] 因果自注意力机制
- [x] 权重绑定、Flash Attention、Pre-norm 等关键设计
- [x] GPT-2 各规模配置对比
