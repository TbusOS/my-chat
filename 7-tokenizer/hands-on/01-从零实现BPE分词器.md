# 从零实现 BPE 分词器

本文将用纯 Python 从零实现一个 BPE（Byte Pair Encoding）分词器，包含训练、编码、解码三个阶段。

> 完整代码见 [examples/simple_bpe.py](../examples/simple_bpe.py)

---

## 整体架构

```
BPE 分词器
├── 训练 (train)
│   ├── 将文本转为 UTF-8 字节序列
│   ├── 统计相邻字节对频率
│   ├── 合并最高频对，生成新 token
│   └── 重复直到达到目标词表大小
├── 编码 (encode)
│   ├── 将文本转为字节序列
│   └── 按训练顺序依次应用合并规则
└── 解码 (decode)
    └── 将 token id 映射回字节，再转为文本
```

---

## 第一步：训练阶段

训练的目标是从语料中学习合并规则。

### 1.1 统计相邻对频率

```python
def get_pair_counts(token_ids):
    """统计相邻 token 对的出现频率"""
    counts = {}
    for i in range(len(token_ids) - 1):
        pair = (token_ids[i], token_ids[i + 1])
        counts[pair] = counts.get(pair, 0) + 1
    return counts
```

### 1.2 执行合并

```python
def merge(token_ids, pair, new_id):
    """将序列中所有匹配的 pair 替换为 new_id"""
    result = []
    i = 0
    while i < len(token_ids):
        if i < len(token_ids) - 1 and (token_ids[i], token_ids[i + 1]) == pair:
            result.append(new_id)
            i += 2
        else:
            result.append(token_ids[i])
            i += 1
    return result
```

### 1.3 训练主循环

```python
def train(text, vocab_size):
    """训练 BPE 分词器"""
    # 初始词表：256 个字节值
    token_ids = list(text.encode("utf-8"))
    merges = {}  # (pair) -> new_id

    num_merges = vocab_size - 256

    for i in range(num_merges):
        counts = get_pair_counts(token_ids)
        if not counts:
            break

        # 找到频率最高的对
        best_pair = max(counts, key=counts.get)
        new_id = 256 + i

        # 执行合并
        token_ids = merge(token_ids, best_pair, new_id)
        merges[best_pair] = new_id

        print(f"合并 #{i+1}: {best_pair} → {new_id}"
              f" (出现 {counts[best_pair]} 次)")

    return merges
```

训练结束后，`merges` 字典记录了所有合并规则及其顺序。

---

## 第二步：编码阶段

编码是将新文本转为 token id 序列的过程。

```python
def encode(text, merges):
    """将文本编码为 token id 序列"""
    token_ids = list(text.encode("utf-8"))

    while len(token_ids) >= 2:
        # 统计当前序列中的所有相邻对
        counts = get_pair_counts(token_ids)

        # 找到在 merges 中优先级最高（最先学到）的对
        # 不在 merges 中的对赋予无穷大，确保不会被选中
        best_pair = min(counts, key=lambda p: merges.get(p, float("inf")))

        if best_pair not in merges:
            break  # 没有可合并的对了

        new_id = merges[best_pair]
        token_ids = merge(token_ids, best_pair, new_id)

    return token_ids
```

关键点：编码时按照 **训练时学到的顺序**（merges 的 value 越小越优先）来应用合并规则。

---

## 第三步：解码阶段

解码是将 token id 序列还原为文本。

```python
def build_vocab(merges):
    """根据合并规则构建词表"""
    vocab = {i: bytes([i]) for i in range(256)}
    for (p0, p1), new_id in merges.items():
        vocab[new_id] = vocab[p0] + vocab[p1]
    return vocab

def decode(token_ids, merges):
    """将 token id 序列解码为文本"""
    vocab = build_vocab(merges)
    byte_sequence = b"".join(vocab[tid] for tid in token_ids)
    return byte_sequence.decode("utf-8", errors="replace")
```

---

## 完整示例

将以上代码组合起来，实际运行一下：

```python
# 训练语料
corpus = """
自然语言处理是人工智能的重要分支。
自然语言理解和自然语言生成是两个核心任务。
分词是自然语言处理的第一步。
好的分词器对模型性能有重要影响。
"""

# 训练：目标词表大小 280（256 基础 + 24 次合并）
merges = train(corpus, vocab_size=280)

# 编码
test_text = "自然语言处理"
token_ids = encode(test_text, merges)
print(f"\n编码: '{test_text}' → {token_ids}")
print(f"Token 数量: {len(token_ids)}")

# 解码
decoded = decode(token_ids, merges)
print(f"解码: {token_ids} → '{decoded}'")

# 验证往返一致性
assert decoded == test_text, "编码→解码不一致！"
print("往返验证通过！")
```

---

## 与 tiktoken 对比

让我们对比一下手写的 BPE 和 OpenAI tiktoken 的结果：

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")
test_text = "自然语言处理是人工智能的重要分支。"

# tiktoken 编码
tk_ids = enc.encode(test_text)
print(f"tiktoken Token 数: {len(tk_ids)}")
print(f"tiktoken Token IDs: {tk_ids}")
for tid in tk_ids:
    print(f"  {tid} → {repr(enc.decode([tid]))}")

# 自己的 BPE 编码（使用上面训练好的 merges）
my_ids = encode(test_text, merges)
print(f"\n自制 BPE Token 数: {len(my_ids)}")
```

你会发现差异很大，原因在于：

| 差异点 | 自制 BPE | tiktoken |
|--------|----------|----------|
| 训练语料 | 几行中文 | 互联网级别的海量文本 |
| 词表大小 | ~280 | ~100,000 |
| 合并次数 | ~24 次 | ~100,000 次 |
| 特殊处理 | 无 | 正则预分割、特殊 token |

核心算法完全一致，差别只在规模。

---

## 进阶思考

### 1. 正则预分割

GPT-2/GPT-4 在 BPE 之前会先用正则表达式将文本切分为粗粒度的块：

```python
import re

# GPT-2 使用的正则（简化版）
pattern = r"""'s|'t|'re|'ve|'m|'ll|'d| ?\w+| ?\d+| ?[^\s\w\d]+|\s+"""
chunks = re.findall(pattern, "Hello, I'm learning BPE!")
# ['Hello', ',', ' I', "'m", ' learning', ' BPE', '!']
```

这样做的好处：防止跨词边界合并（比如不希望 "dog." 中的 "g" 和 "." 被合并）。

### 2. 特殊 Token

实际的分词器还需要处理特殊 token：

```
<|endoftext|>   文本结束标记
<|im_start|>    消息开始（ChatML 格式）
<|im_end|>      消息结束
```

这些特殊 token 不参与 BPE 合并，而是直接映射到固定的 ID。

### 3. 训练效率

实际训练时的优化：
- 使用优先队列（堆）维护频率，而非每轮全量统计
- 用 Rust/C++ 实现核心循环（tiktoken 就是用 Rust 写的）
- 在大规模语料上并行统计频率

---

## 小结

| 阶段 | 核心操作 | 输出 |
|------|----------|------|
| 训练 | 反复合并最高频对 | 合并规则列表 |
| 编码 | 按顺序应用合并规则 | Token ID 序列 |
| 解码 | 查词表拼接字节 | 还原文本 |

通过这个实现，你应该对 BPE 有了深入的理解。核心算法不到 50 行 Python，但正是这个简单的思想支撑着 GPT-4 等最强大模型的分词需求。

## 参考

- [minbpe](https://github.com/karpathy/minbpe) - Karpathy 的最小 BPE 实现
- [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) - Karpathy 视频教程
