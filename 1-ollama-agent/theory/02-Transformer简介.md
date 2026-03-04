# 第二章：Transformer 简介

## 本章目标

理解 Transformer 架构的核心概念，包括：
1. 为什么需要注意力机制
2. 多头注意力的原理
3. Transformer 的整体结构

---

## 2.1 注意力机制的诞生

### 2.1.1 RNN 的问题

在 Transformer 出现之前，主流的序列处理模型是 **RNN（循环神经网络）**：

```
RNN 处理序列：
h0 → [今天] → h1 → [天气] → h2 → [很好] → h3
```

**RNN 的问题**：

1. **长距离依赖困难**
   ```
   "那个在巴黎工作的设计师，他的家乡在..." ← 需要记住开头的信息
   ```
   信息在传递过程中会逐渐稀释

2. **并行计算困难**
   - 必须按顺序计算，无法充分利用 GPU

3. **梯度消失/爆炸**
   - 深层网络训练不稳定

### 2.1.2 注意力机制的突破

2017 年，Google 提出了 **Transformer** 论文《Attention Is All You Need》，完全摒弃了 RNN，只用注意力机制。

**核心思想**：让每个位置的词直接"注意"到所有其他位置的词。

---

## 2.2 什么是注意力？

### 2.2.1 直观理解

想象你在阅读这段文字：

```
"小明把球踢给了小红，她接住球后传给了他。"
```

当你读到"她"时，你知道指的是"小红"；
当你读到"他"时，你知道指的是"小明"。

**注意力机制**就是让模型学会这种"关联"能力。

### 2.2.2 核心公式

```
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

**三个输入**：
- **Q (Query)**：我要找什么
- **K (Key)**：我有什么
- **V (Value)**：我的具体内容

**计算过程**：
1. Q 和 K 计算相似度（QK^T）
2. 除以 √d_k（缩放，防止数值过大）
3. softmax 转成概率
4. 加权求和得到输出

---

## 2.3 自注意力（Self-Attention）

### 2.3.1 什么是自注意力？

**自注意力**：输入序列"关注"自己。

```
句子: "今天天气很好"

每个词都要和其他词计算注意力：
- "今天" 关注 "天气", "很好"
- "天气" 关注 "今天", "很好"
- "很好" 关注 "今天", "天气"
```

### 2.3.2 计算过程

```python
# 简化计算过程

# 1. 输入嵌入
x = [embedding(今天), embedding(天气), embedding(很好)]

# 2. 转换为 Q, K, V（通过线性变换）
Q = x @ W_Q
K = x @ W_K
V = x @ W_V

# 3. 计算注意力分数
scores = Q @ K.T  # (seq_len, seq_len)

# 4. 缩放
scores = scores / sqrt(d_k)

# 5. softmax
attention_weights = softmax(scores, axis=-1)

# 6. 加权求和
output = attention_weights @ V
```

### 2.3.3 注意力权重可视化

```
句子: "The cat sat on the mat"

注意力权重（"sat" 关注其他词）:

        The  cat  sat  on  the  mat
sat    0.1  0.4  0.1  0.1  0.1  0.2

解释："sat" 最关注 "cat"（0.4）
```

---

## 2.4 多头注意力（Multi-Head Attention）

### 2.4.1 为什么需要多头？

**单头注意力的局限**：只能学习一种类型的关联。

**多头注意力的优势**：并行学习多种关联模式。

```
不同头学习不同关系：

Head 1（主语-谓语）:
"猫" → "跑"  （猫在跑）

Head 2（修饰关系）:
"可爱" → "猫"  （可爱的猫）

Head 3（位置关系）:
"桌子上" → "猫"  （桌子上有猫）
```

### 2.4.2 多头计算

```python
# 多头注意力
num_heads = 8  # 8 个头
d_k = 64       # 每个头的维度

# 1. 分割成多个头
Q = reshape(Q, (batch, num_heads, seq_len, d_k))
K = reshape(K, (batch, num_heads, seq_len, d_k))
V = reshape(V, (batch, num_heads, seq_len, d_k))

# 2. 每个头独立计算注意力
for i in range(num_heads):
    head_i = Attention(Q[:,i], K[:,i], V[:,i])

# 3. 拼接所有头
output = concat([head_1, ..., head_8])

# 4. 线性投影
output = output @ W_O
```

### 2.4.3 多头注意力可视化

```
多头注意力示意:

Input: "The bank refused to lend money"

Head 1 (语义相关):
"The" ↔ "bank" (低)
"bank" ↔ "lend" (高)  ← 学习"银行拒绝贷款"

Head 2 (位置相邻):
"The" ↔ "bank" (高)
"bank" ↔ "refused" (高)  ← 学习相邻关系
```

---

## 2.5 Transformer 架构

### 2.5.1 整体结构

```
输入:
  Token Embedding + Positional Encoding
      ↓
编码器 Encoder (×6 层):
  ├── Multi-Head Attention
  ├── Add & LayerNorm
  ├── Feed Forward
  └── Add & LayerNorm
      ↓
输出:
  预测的 Token 概率
```

### 2.5.2 核心组件

1. **位置编码（Positional Encoding）**
   - 注意力机制不区分位置顺序
   - 需要显式添加位置信息

2. **残差连接（Residual Connection）**
   ```
   Output = LayerNorm(x + SubLayer(x))
   ```
   - 缓解深层网络训练困难

3. **前馈网络（Feed Forward）**
   - 两层线性变换 + ReLU
   - 增强模型表达能力

4. **LayerNorm**
   - 稳定训练，加速收敛

---

## 2.6 位置编码

### 2.6.1 为什么需要位置编码？

注意力机制是**无序**的：

```
"狗咬人" vs "人咬狗"
用自注意力计算，两句话的表示相同！
```

**解决**：添加位置编码。

### 2.6.2 Sinusoidal 位置编码

Transformer 使用正弦/余弦函数编码位置：

```python
import numpy as np

def positional_encoding(seq_len, d_model):
    # PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
    # PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    pe = np.zeros((seq_len, d_model))
    position = np.arange(seq_len).reshape(-1, 1)
    div_term = np.exp(np.arange(0, d_model, 2) * -np.log(10000.0) / d_model)

    pe[:, 0::2] = np.sin(position * div_term)
    pe[:, 1::2] = np.cos(position * div_term)

    return pe
```

### 2.6.3 位置编码特点

1. **唯一性**：每个位置有唯一编码
2. **可扩展性**：可以推广到任意长度
3. **相对位置**：可以学习相对位置关系

---

## 2.7 GPT vs BERT

### 2.7.1 两种架构

| 架构 | 特点 | 预训练任务 | 适用场景 |
|------|------|------------|----------|
| **BERT** | Encoder 双向 | Masked LM | 理解任务（分类、NER） |
| **GPT** | Decoder 单向 | 语言建模 | 生成任务（��话、写作） |

### 2.7.2 BERT（理解为主）

```
输入: "今天天气很好" → [MASK] 了

预测: "今天天气很好" → [MASK] 了 → "出门"
```

### 2.7.3 GPT（生成为主）

```
输入: "今天天气很好，"

自回归生成:
今天 → 天气 → 很好 → ， → 适合 → 出门 → ...
```

---

## 2.8 本章小结

本章我们学习了：

- ✅ **注意力机制**：让词"关注"相关词
- ✅ **自注意力**：输入关注输入自己
- ✅ **多头注意力**：并行学习多种关联
- ✅ **Transformer 架构**：Encoder/Decoder
- ✅ **位置编码**：添加位置信息
- ✅ **GPT vs BERT**：理解 vs 生成

---

## 2.9 扩展阅读

- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
- [Attention Is All You Need 论文](https://arxiv.org/abs/1706.03762)
- [Annotated Transformer](http://nlp.seas.harvard.edu/2018/04/03/attention.html)
