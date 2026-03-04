# 第三章：Attention 机制详解

## 本章目标

深入理解 Attention 机制：
1. 为什么需要 Attention
2. Q/K/V 是什么
3. 注意力计算过程
4. 多头注意力

---

## 1.1 为什么需要 Attention？

### 1.1.1 传统方法的局限

在 Attention 出现之前，序列处理主要靠 RNN：

```
RNN: h_t = f(x_t, h_{t-1})
```

问题：
- 长距离依赖丢失
- 无法并行计算

### 1.1.2 Attention 的突破

**核心思想**：让每个位置直接"注意"到所有其他位置。

```
Attention: 直接建立任意两个位置的联系
```

---

## 1.2 Q/K/V 是什么？

### 1.2.1 直观理解

想象你在图书馆找书：

- **Query（查询）**：你心里想找什么
- **Key（键）**：每本书的标签
- **Value（值）**：书的实际内容

### 1.2.2 在 Attention 中的含义

```
Q (Query): "我需要找什么信息"
K (Key):   "我有什么信息"
V (Value): "信息的具体内容"
```

---

## 1.3 Attention 计算

### 1.3.1 核心公式

```
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

### 1.3.2 步骤详解

```
1. QK^T: 计算 Query 和 Key 的相似度
         (seq_len, d_k) × (d_k, seq_len) = (seq_len, seq_len)

2. /√d_k: 缩放，防止数值过大

3. softmax: 转成概率分布

4. × V: 加权求和得到输出
        (seq_len, seq_len) × (seq_len, d_v) = (seq_len, d_v)
```

---

## 1.4 代码实现

```python
import numpy as np

def softmax(x, axis=-1):
    exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)

def attention(Q, K, V):
    """简化版 Attention"""
    d_k = Q.shape[-1]

    # 1. 计算相似度
    scores = np.matmul(Q, K.T) / np.sqrt(d_k)

    # 2. softmax
    attn_weights = softmax(scores, axis=-1)

    # 3. 加权求和
    output = np.matmul(attn_weights, V)

    return output, attn_weights
```

---

## 1.5 多头注意力

### 1.5.1 为什么需要多头？

单头只能学习一种关系，多头可以并行学习多种。

```
Head 1: 学习主语-谓语关系
Head 2: 学习修饰关系
Head 3: 学习位置关系
```

### 1.5.2 多头计算

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O

其中 head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
```

---

## 1.6 本章小结

- ✅ Attention 解决的问题
- ✅ Q/K/V 含义
- ✅ Attention 计算过程
- ✅ 多头注意力
