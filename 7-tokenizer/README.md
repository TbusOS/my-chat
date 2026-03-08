# 分词器 (Tokenizer)

> 理解 LLM 如何将文本转化为数字 —— 一切从分词开始

> **类型**: 可直接运行 | **前置**: Python 基础 | **硬件**: CPU 即可

## 本章目录

### 教程 (Tutorial)
- [分词器入门](tutorial/01-分词器入门.md)

### 理论 (Theory)
- [BPE 算法详解](theory/01-BPE算法详解.md)

### 实战 (Hands-on)
- [从零实现 BPE 分词器](hands-on/01-从零实现BPE分词器.md)

### 代码 (Examples)
- [simple_bpe.py](examples/simple_bpe.py) - 完整可运行的 BPE 分词器

---

## 核心内容

### 为什么要学分词器？

```
文本 → 分词器 → Token IDs → 模型 → Token IDs → 分词器 → 文本
```

分词器是 LLM 的"翻译官"：模型只能处理数字，分词器负责在文本和数字之间来回转换。

### 主流分词方案

| 算法 | 代表模型 | 特点 |
|------|----------|------|
| BPE | GPT 系列 | 基于频率合并，最主流 |
| WordPiece | BERT | 基于似然合并 |
| Unigram | T5, LLaMA | 基于概率剪枝 |
| SentencePiece | 多种模型 | 语言无关，直接处理原始文本 |

---

## 快速上手

```bash
pip install tiktoken
```

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4")
tokens = enc.encode("你好，世界！Hello World!")
print(f"Token IDs: {tokens}")
print(f"Token 数量: {len(tokens)}")
print(f"解码还原: {enc.decode(tokens)}")
```

---

## 参考资源

- [tiktoken](https://github.com/openai/tiktoken) - OpenAI 官方分词器
- [tokenizers](https://github.com/huggingface/tokenizers) - Hugging Face 高性能分词库
- [sentencepiece](https://github.com/google/sentencepiece) - Google 通用分词工具
- [minbpe](https://github.com/karpathy/minbpe) - Karpathy 的最小 BPE 实现
- [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) - Karpathy 分词器教程视频
