# 第一章：最小GPT实现 - 100行代码

## 经典项目推荐

在开始之前，推荐几个 GitHub 上经典的最小实现：

| 项目 | 语言 | 行数 | 特点 |
|------|------|------|------|
| [llama.c](https://github.com/karpathy/llama.c) | C | ~1000 | 最小的羊驼实现 |
| [minGPT](https://github.com/karpathy/minGPT) | Python | ~600 | 最小 PyTorch GPT |
| [tinygrad](https://github.com/tinygrad/tinygrad) | Python | ~1000 | 最小深度学习框架 |
| [ggml](https://github.com/ggerganov/ggml) | C | ~5000 | 张量库 + LLM |

---

## karpathy/llama.c 分析

这是 Andrej Karpathy 写的最小羊驼实现，仅用 C 语言就能跑。

### 核心特点

```c
// 核心推理循环 - 简化版
void inference(struct Model* model, int* tokens, int n_tokens) {
    for (int i = 0; i < n_tokens; i++) {
        // 1. 前向传播
        forward(model, tokens[i]);

        // 2. 采样下一个 token
        int next_token = sample(model->logits);

        // 3. 输出
        printf("%s", model->vocab[next_token]);
    }
}
```

### 为什么这么短？

1. **不用框架**：纯 C 实现
2. **量化**：使用 Q4 量化压缩模型
3. **简化**：去掉复杂优化

---

## 本教程目标

用 Python 实现一个可运行的最小 GPT：
- 100-200 行代码
- 使用 PyTorch
- 能训练和推理

---

## 1.1 最小 GPT 代码

```python
import torch
import torch.nn as nn
from torch.nn import functional as F

# ========== 配置 ==========
batch_size = 4
block_size = 32
max_iters = 5000
eval_interval = 500
learning_rate = 1e-3
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# ========== 数据 ==========
# 简单文本
text = "hello world this is a test of the gpt model"
chars = sorted(set(text))
vocab_size = len(chars)

# 编码/解码
stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for c, i in stoi.items()}

encode = lambda s: [stoi[c] for c in s]
decode = lambda l: ''.join([itos[i] for i in l])

# 训练数据
data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data = data[:n]
val_data = data[n:]

def get_batch(split):
    data = train_data if split == 'train' else val_data
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    return x, y

# ========== 模型 ==========
class GPT(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, 64)
        self.position_embedding = nn.Embedding(block_size, 64)
        self.blocks = nn.Sequential(
            nn.TransformerEncoderLayer(d_model=64, nhead=4, dim_feedforward=128, batch_first=True),
            nn.TransformerEncoderLayer(d_model=64, nhead=4, dim_feedforward=128, batch_first=True),
        )
        self.lm_head = nn.Linear(64, vocab_size)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        token_emb = self.token_embedding(idx)
        pos_emb = self.position_embedding(torch.arange(T, device=idx.device))
        x = token_emb + pos_emb
        x = self.blocks(x)
        logits = self.lm_head(x)

        if targets is None:
            loss = None
        else:
            B, T, C = logits.shape
            logits = logits.view(B * T, C)
            targets = targets.view(B * T)
            loss = F.cross_entropy(logits, targets)

        return logits, loss

    def generate(self, idx, max_new_tokens):
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -block_size:]
            logits, loss = self(idx_cond)
            logits = logits[:, -1, :]
            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
        return idx

# ========== 训练 ==========
model = GPT(vocab_size).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

for iter in range(max_iters):
    xb, yb = get_batch('train')
    xb, yb = xb.to(device), yb.to(device)

    logits, loss = model(xb, yb)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if iter % eval_interval == 0:
        print(f"iter {iter}: loss {loss.item():.4f}")

# ========== 生成 ==========
context = torch.zeros((1, 1), dtype=torch.long, device=device)
print(decode(model.generate(context, max_new_tokens=100)[0].tolist()))
```

---

## 1.2 代码解析

### 核心组件

| 组件 | 作用 |
|------|------|
| Embedding | 词嵌入 |
| Position Embedding | 位置编码 |
| TransformerEncoder | 核心处理层 |
| Linear | 输出层 |

### 训练流程

```
数据 → 嵌入 → Transformer → 输出 → Loss → 反向传播
```

---

## 1.3 扩展阅读

- [llama.c](https://github.com/karpathy/llama.c) - C 语言最小实现
- [minGPT](https://github.com/karpathy/minGPT) - PyTorch 版本
- [nanoGPT](https://github.com/karpathy/nanoGPT) - 更简洁的版本

---

## 1.4 本章小结

- ✅ 了解了经典最小实现项目
- ✅ 理解最小 GPT 架构
- ✅ 运行了完整代码示例
