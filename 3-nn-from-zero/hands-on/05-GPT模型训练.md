# GPT 模型训练

## 本章目标

手把手训练一个 GPT 模型：
1. 数据准备
2. 模型构建
3. 训练循环
4. 文本生成

---

## 1.1 数据准备

```python
import torch
from torch.utils.data import Dataset, DataLoader

class TextDataset(Dataset):
    """文本数据集"""

    def __init__(self, text, tokenizer, block_size):
        self.data = tokenizer(text)
        self.block_size = block_size

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return torch.tensor(x), torch.tensor(y)


# 简单分词器
class SimpleTokenizer:
    def __init__(self, text):
        chars = sorted(set(text))
        self.stoi = {c: i for i, c in enumerate(chars)}
        self.itos = {i: c for c, i in self.stoi.items()}

    def __call__(self, text):
        return [self.stoi[c] for c in text]

    def decode(self, ids):
        return ''.join([self.itos[i] for i in ids])


# 使用示例
text = "hello world this is a test of the gpt model " * 100
tokenizer = SimpleTokenizer(text)
dataset = TextDataset(text, tokenizer, block_size=32)
dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
```

---

## 1.2 GPT 模型

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class GPT(nn.Module):
    """简化版 GPT"""

    def __init__(self, vocab_size, d_model, num_heads, num_layers, block_size):
        super().__init__()
        self.block_size = block_size

        # 词嵌入和位置嵌入
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(block_size, d_model)

        # Transformer Encoder
        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_model * 4)
            for _ in range(num_layers)
        ])

        # 输出层
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)

        # 权重绑定
        self.lm_head.weight = self.token_embedding.weight

    def forward(self, idx, targets=None):
        B, T = idx.shape

        # 嵌入
        token_emb = self.token_embedding(idx)
        pos_emb = self.position_embedding(torch.arange(T, device=idx.device))
        x = token_emb + pos_emb

        # Transformer
        for block in self.blocks:
            x = block(x)

        # 输出
        logits = self.lm_head(x)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                targets.view(-1)
            )

        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0):
        """自回归生成"""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature

            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)

        return idx


class TransformerBlock(nn.Module):
    """Transformer 块"""
    def __init__(self, d_model, num_heads, d_ff):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        attn_output, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_output)
        x = self.norm2(x + self.ffn(x))
        return x
```

---

## 1.3 训练代码

```python
import torch.optim as optim

def train_gpt():
    # 配置
    vocab_size = 100  # 简化的词表大小
    d_model = 128
    num_heads = 4
    num_layers = 4
    block_size = 32
    batch_size = 8
    learning_rate = 3e-4
    max_iters = 1000

    # 创建模型
    model = GPT(vocab_size, d_model, num_heads, num_layers, block_size)
    model = model.to('cuda' if torch.cuda.is_available() else 'cpu')

    # 优化器
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # 训练数据
    text = "hello world this is a test of the gpt model " * 1000
    tokenizer = SimpleTokenizer(text)
    dataset = TextDataset(text, tokenizer, block_size)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 训练循环
    model.train()
    for iter, (x, y) in enumerate(dataloader):
        x, y = x.to(model.lm_head.weight.device), y.to(model.lm_head.weight.device)

        # 前向
        logits, loss = model(x, y)

        # 反向
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if iter % 100 == 0:
            print(f"Iter {iter}, Loss: {loss.item():.4f}")

        if iter >= max_iters:
            break

    return model, tokenizer


# 训练
model, tokenizer = train_gpt()
```

---

## 1.4 文本生成

```python
# 生成文本
model.eval()

# 初始 token
idx = torch.tensor([[tokenizer.stoi['h']]]).to(model.lm_head.weight.device)

# 生成
generated = model.generate(idx, max_new_tokens=100, temperature=0.8)

# 解码
output = tokenizer.decode(generated[0].tolist())
print(output)
```

---

## 1.5 完整代码

```python
#!/usr/bin/env python3
"""
GPT 训练完整示例
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader


# ========== 数据 ==========
class SimpleTokenizer:
    def __init__(self, text):
        chars = sorted(set(text))
        self.stoi = {c: i for i, c in enumerate(chars)}
        self.itos = {i: c for c, i in self.stoi.items()}
        self.vocab_size = len(chars)

    def __call__(self, text):
        return [self.stoi[c] for c in text]

    def decode(self, ids):
        return ''.join([self.itos[i] for i in ids])


class TextDataset(Dataset):
    def __init__(self, text, tokenizer, block_size):
        self.data = tokenizer(text)
        self.block_size = block_size

    def __len__(self):
        return len(self.data) - self.block_size

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.block_size]
        y = self.data[idx + 1:idx + self.block_size + 1]
        return torch.tensor(x), torch.tensor(y)


# ========== 模型 ==========
class GPT(nn.Module):
    def __init__(self, vocab_size, d_model, num_heads, num_layers, block_size):
        super().__init__()
        self.block_size = block_size

        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(block_size, d_model)

        self.blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_model * 4)
            for _ in range(num_layers)
        ])

        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight

    def forward(self, idx, targets=None):
        B, T = idx.shape
        token_emb = self.token_embedding(idx)
        pos_emb = self.position_embedding(torch.arange(T, device=idx.device))
        x = token_emb + pos_emb

        for block in self.blocks:
            x = block(x)

        logits = self.lm_head(x)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))

        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx


class TransformerBlock(nn.Module):
    def __init__(self, d_model, num_heads, d_ff):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x):
        attn_output, _ = self.attn(x, x, x)
        x = self.norm1(x + attn_output)
        x = self.norm2(x + self.ffn(x))
        return x


# ========== 训练 ==========
def main():
    # 训练数据
    text = "hello world this is a test of the gpt model " * 500
    tokenizer = SimpleTokenizer(text)

    # 超参数
    d_model = 128
    num_heads = 4
    num_layers = 4
    block_size = 32
    batch_size = 8
    learning_rate = 3e-4
    max_iters = 500

    # 创建模型
    model = GPT(tokenizer.vocab_size, d_model, num_heads, num_layers, block_size)

    # 数据
    dataset = TextDataset(text, tokenizer, block_size)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 优化器
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # 训练
    model.train()
    for iter, (x, y) in enumerate(dataloader):
        logits, loss = model(x, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if iter % 50 == 0:
            print(f"Iter {iter}, Loss: {loss.item():.4f}")

        if iter >= max_iters:
            break

    # 生成
    model.eval()
    idx = torch.tensor([[tokenizer.stoi['h']]])
    generated = model.generate(idx, max_new_tokens=200, temperature=0.8)
    print("\n生成的文本:")
    print(tokenizer.decode(generated[0].tolist()))


if __name__ == "__main__":
    main()
```

---

## 1.6 本章小结

- ✅ 数据准备
- ✅ 模型构建
- ✅ 训练循环
- ✅ 文本生成
- ✅ 完整代码
