# RAG 基础概念

## 什么是 RAG？

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将**信息检索**与**文本生成**结合的技术架构。

核心思想：不依赖 LLM 的参数记忆，而是在生成回答前，先从外部知识库检索相关信息，将检索到的内容作为上下文提供给 LLM，从而生成更准确、更有依据的回答。

```
传统 LLM：用户提问 → LLM（依赖训练数据） → 回答（可能过时或幻觉）

RAG 方式：用户提问 → 检索知识库 → 将相关文档 + 问题一起给 LLM → 回答（有据可依）
```

### 为什么需要 RAG？

LLM 存在以下局限：

| 问题 | 说明 | RAG 如何解决 |
|------|------|-------------|
| 知识过时 | 训练数据有截止日期 | 实时检索最新文档 |
| 幻觉问题 | 可能编造不存在的信息 | 基于真实文档生成 |
| 领域知识缺乏 | 对特定企业/行业了解不足 | 接入企业内部知识库 |
| 上下文窗口有限 | 无法一次性输入所有文档 | 只检索最相关的片段 |

---

## RAG vs 微调 vs 提示工程

| 特性 | RAG | 微调 (Fine-tuning) | 提示工程 (Prompt Engineering) |
|------|-----|---------------------|-------------------------------|
| **实现难度** | 中等 | 高 | 低 |
| **成本** | 中（需要向量数据库） | 高（需要 GPU 训练） | 低（仅需设计 Prompt） |
| **知识更新** | 实时（更新文档即可） | 需要重新训练 | 手动更新 Prompt |
| **适用数据量** | 大量文档 | 中等规模标注数据 | 少量示例 |
| **准确性** | 高（有文档支撑） | 高（模型内化知识） | 中（依赖模型能力） |
| **可解释性** | 高（可追溯来源） | 低 | 低 |
| **最佳场景** | 知识库问答、文档搜索 | 风格/格式定制 | 简单任务、快速原型 |

### 如何选择？

```
需要实时更新知识？          → RAG
需要改变模型输出风格/格式？  → 微调
任务简单、预算有限？        → 提示工程
需要最高准确度？            → RAG + 微调（组合使用）
```

---

## RAG 的核心流程

RAG 分为两个阶段：**离线索引** 和 **在线检索生成**。

### 阶段一：离线索引（Indexing）

将文档预处理并存入向量数据库：

```
原始文档（PDF/TXT/HTML）
    ↓
文档加载（Document Loading）
    ↓
文本分块（Chunking）
    ↓
向量化（Embedding）
    ↓
存入向量数据库（Vector Store）
```

### 阶段二：在线检索生成（Retrieval & Generation）

用户提问时实时检索并生成：

```
用户提问
    ↓
问题向量化（Query Embedding）
    ↓
相似度检索（Similarity Search）
    ↓
获取 Top-K 相关文档片段
    ↓
构建 Prompt（问题 + 相关文档）
    ↓
LLM 生成回答
```

---

## 适用场景

### 1. 知识库问答

企业内部文档、产品手册、FAQ 系统。用户用自然语言提问，系统从知识库中检索并生成回答。

### 2. 文档搜索

从海量文档中精准检索信息，支持语义搜索（不仅仅是关键词匹配）。

### 3. 客服系统

基于产品文档自动回答客户问题，减少人工客服压力。

### 4. 学术研究

从论文库中检索相关研究，自动总结研究进展。

---

## 简单 RAG 代码示例

以下是一个最简化的 RAG 流程，帮助你理解核心原理：

```python
import ollama
import chromadb

# 1. 初始化向量数据库
client = chromadb.Client()
collection = client.create_collection("demo")

# 2. 准备知识文档
docs = [
    "Python 是一种解释型高级编程语言，由 Guido van Rossum 创建。",
    "RAG 是检索增强生成的缩写，结合了信息检索和文本生成。",
    "向量数据库使用高维向量来存储和检索数据。",
]

# 3. 文档向量化并存入数据库
for i, doc in enumerate(docs):
    embedding = ollama.embed(model="nomic-embed-text", input=doc)
    collection.add(
        ids=[f"doc_{i}"],
        documents=[doc],
        embeddings=[embedding["embeddings"][0]],
    )

# 4. 用户提问 → 检索 → 生成
question = "什么是 RAG？"
q_embedding = ollama.embed(model="nomic-embed-text", input=question)
results = collection.query(
    query_embeddings=[q_embedding["embeddings"][0]],
    n_results=2,
)

# 5. 构建 Prompt 并生成回答
context = "\n".join(results["documents"][0])
prompt = f"根据以下参考资料回答问题。\n\n参考资料：\n{context}\n\n问题：{question}"
response = ollama.chat(
    model="qwen2.5",
    messages=[{"role": "user", "content": prompt}],
)
print(response["message"]["content"])
```

运行前确保：
1. 已安装 `ollama` 和 `chromadb`（`pip install ollama chromadb`）
2. Ollama 服务已启动
3. 已拉取模型（`ollama pull qwen2.5 && ollama pull nomic-embed-text`）

---

## 下一步

- 深入了解向量检索原理 → [向量检索原理](../theory/01-向量检索原理.md)
- 动手构建完整 RAG 系统 → [构建本地知识库](../hands-on/01-构建本地知识库.md)
