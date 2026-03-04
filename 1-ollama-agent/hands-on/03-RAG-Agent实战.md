# 第三章：RAG Agent 实战

## 本章目标

手把手实现一个 RAG（检索增强生成）Agent：
1. 理解 RAG 的原理
2. 构建知识库
3. 实现向量检索
4. 将检索结果融入 LLM 生成

---

## 3.1 什么是 RAG？

### 3.1.1 RAG 的定义

**RAG (Retrieval-Augmented Generation)** = 检索 + 增强 + 生成

**核心思想**：不让 LLM 仅依赖训练知识，而是先从外部知识库检索相关信息，再让 LLM 基于检索结果生成回答。

### 3.1.2 为什么需要 RAG？

| 问题 | RAG 解决方案 |
|------|-------------|
| 知识过时 | 检索最新信息 |
| 幻觉（胡说八道） | 基于事实检索 |
| 知识有限 | 可接入任意知识库 |
| 无法引用来源 | 可以标注来源 |

### 3.1.3 RAG 流程

```
用户输入
    ↓
检索 query 编码
    ↓
向量数据库检索
    ↓
获取 Top-K 相关文档
    ↓
构建 Prompt（含检索结果）
    ↓
LLM 生成回复
    ↓
返回结果（可附带来源）
```

---

## 3.2 RAG 核心概念

### 3.2.1 向量嵌入（Embedding）

把文本转换成向量表示：

```
文本: "Python是一门编程语言"
    ↓ Embedding
向量: [0.1, -0.3, 0.5, 0.8, ...]  (假设 768 维)
```

### 3.2.2 向量检索

通过向量相似度找到相关内容：

```
Query: "Python怎么定义函数？"
    ↓
Query 向量: [0.2, -0.1, 0.7, ...]
    ↓
与知识库向量计算相似度
    ↓
返回 Top-K 最相似的文档
```

### 3.2.3 相似度计算

常用方法：**余弦相似度**

```
cosine(A, B) = (A · B) / (||A|| × ||B||)

值范围: -1 到 1
1 = 完全相同
0 = 无关
-1 = 完全相反
```

---

## 3.3 完整代码实现

### 3.3.1 项目结构

```
rag_agent/
├── rag_agent.py      # 主程序
├── knowledge_base/   # 知识库
└── requirements.txt # 依赖
```

### 3.3.2 简单向量检索实现

为了不依赖外部向量库，这里实现一个简化版本：

```python
#!/usr/bin/env python3
"""
RAG Agent
功能：检索增强生成，让 LLM 基于知识库回答问题
"""

import ollama
import json
import re
from typing import List, Dict, Tuple


class SimpleChunker:
    """简单文本分块器"""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Args:
            chunk_size: 每个块的最大字符数
            overlap: 块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[str]:
        """将文本分割成块"""
        # 按句子分割
        sentences = re.split(r'([。！？.!?])', text)

        chunks = []
        current_chunk = ""

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""

            # 如果当前块加上句子超过限制，开始新块
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # 新块从上一个块末尾取 overlap 字符
                current_chunk = current_chunk[-self.overlap:] + sentence + punctuation
            else:
                current_chunk += sentence + punctuation

        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


class SimpleEmbedding:
    """简化版 embedding（基于词频）"""

    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def encode(self, text: str) -> List[float]:
        """将文本转换为向量"""
        # 简单分词
        words = re.findall(r'\w+', text.lower())

        # 创建词袋
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 生成固定维度向量（简单哈希）
        embedding = []
        for i in range(self.dimension):
            # 基于词频和位置生成
            value = 0.0
            for word, freq in word_freq.items():
                # 简单哈希
                hash_val = hash(word + str(i))
                value += freq * (hash_val % 1000) / 1000.0
            embedding.append(value / max(len(word_freq), 1))

        # 归一化
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(x * y for x, y in zip(a, b))
        return dot_product


class RAGAgent:
    """检索增强生成 Agent"""

    def __init__(self, model: str = "qwen2.5", top_k: int = 3):
        """
        Args:
            model: 使用的 LLM 模型
            top_k: 检索返回的相关文档数量
        """
        self.model = model
        self.top_k = top_k

        # 知识库
        self.documents: List[Dict] = []

        # 工具
        self.chunker = SimpleChunker(chunk_size=500, overlap=50)
        self.embedding = SimpleEmbedding(dimension=256)

    def add_document(self, text: str, metadata: Dict = None):
        """
        添加文档到知识库

        Args:
            text: 文档内容
            metadata: 元数据（如标题、来源）
        """
        # 分块
        chunks = self.chunker.chunk_text(text)

        # 为每个块创建向量
        for chunk in chunks:
            chunk_embedding = self.embedding.encode(chunk)

            self.documents.append({
                'content': chunk,
                'embedding': chunk_embedding,
                'metadata': metadata or {}
            })

    def add_documents_batch(self, documents: List[Tuple[str, Dict]]):
        """
        批量添加文档

        Args:
            documents: [(文本, 元数据), ...]
        """
        for text, metadata in documents:
            self.add_document(text, metadata)

    def retrieve(self, query: str) -> List[Dict]:
        """
        检索相关文档

        Args:
            query: 查询文本

        Returns:
            相关文档列表
        """
        if not self.documents:
            return []

        # 查询向量
        query_embedding = self.embedding.encode(query)

        # 计算相似度
        results = []
        for doc in self.documents:
            similarity = self.embedding.cosine_similarity(
                query_embedding,
                doc['embedding']
            )
            results.append({
                'content': doc['content'],
                'metadata': doc['metadata'],
                'score': similarity
            })

        # 排序并返回 top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:self.top_k]

    def build_prompt(self, query: str, retrieved_docs: List[Dict]) -> str:
        """
        构建增强 Prompt

        Args:
            query: 用户问题
            retrieved_docs: 检索到的文档

        Returns:
            完整的 Prompt
        """
        # 构建上下文
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc['metadata'].get('source', '未知来源')
            context_parts.append(f"[来源{i} - {source}]\n{doc['content']}")

        context = "\n\n".join(context_parts)

        # 构建完整 Prompt
        prompt = f"""基于以下知识库内容回答用户问题。

重要规则：
1. 只基于提供的知识库内容回答，不要编造信息
2. 如果知识库没有相关信息，请如实说明"知识库中没有相关信息"
3. 在回答中注明参考来源

知识库：
{context}

用户问题：{query}

回答："""

        return prompt

    def chat(self, user_input: str) -> str:
        """
        RAG 对话

        Args:
            user_input: 用户输入

        Returns:
            LLM 回复
        """
        # 1. 检索相关文档
        retrieved_docs = self.retrieve(user_input)

        if not retrieved_docs:
            # 没有检索到内容
            prompt = f"""用户问题：{user_input}

回答："""
        else:
            # 2. 构建增强 Prompt
            prompt = self.build_prompt(user_input, retrieved_docs)

        # 3. 调用 LLM
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        return response['message']['content']


# ============== 使用示例 ==============

def create_knowledge_base():
    """创建示例知识库"""
    documents = [
        # Python 相关
        ("Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python的设计哲学强调代码的可读性和简洁的语法。", {"source": "Python百科"}),
        ("Python的函数用def关键字定义。例如：def greet(name): return f'Hello, {name}!'", {"source": "Python教程"}),
        ("Python的列表推导式是一种简洁的创建列表的方式。例如：[x**2 for x in range(10)]可以快速生成0到9的平方列表。", {"source": "Python教程"}),
        ("Python的虚拟环境用于隔离项目依赖。可以使用python -m venv env创建虚拟环境，使用source env/bin/activate激活。", {"source": "Python最佳实践"}),

        # JavaScript 相关
        ("JavaScript是一种运行在浏览器中的脚本语言，也可以用于服务端开发（Node.js）。由Brendan Eich于1995年创建。", {"source": "JavaScript百科"}),
        ("JavaScript用function关键字或箭头函数定义。箭头函数语法：const add = (a, b) => a + b", {"source": "JavaScript教程"}),
        ("JavaScript的Promise用于处理异步操作。例如：fetch(url).then(r => r.json()).then(data => console.log(data))", {"source": "JavaScript教程"}),
        ("Node.js是运行在服务端的JavaScript环境，基于Chrome V8引擎。", {"source": "Node.js百科"}),

        # Go 相关
        ("Go是Google开发的编程语言，于2009年发布。Go以其高性能和出色的并发支持著称。", {"source": "Go百科"}),
        ("Go的函数用func关键字定义。例如：func add(a, b int) int {{ return a + b }}", {"source": "Go教程"}),
        ("Go的goroutine是轻量级线程，比传统线程更轻量。用go关键字启动：go func() {{ }}()", {"source": "Go教程"}),
        ("Go的channel用于goroutine之间的通信。例如：ch := make(chan int)", {"source": "Go教程"}),
    ]
    return documents


def main():
    # 创建 RAG Agent
    rag = RAGAgent("qwen2.5", top_k=3)

    # 添加知识库
    print("正在构建知识库...")
    documents = create_knowledge_base()
    rag.add_documents_batch(documents)
    print(f"知识库大小：{len(rag.documents)} 个文本块\n")

    print("=" * 50)
    print("RAG Agent 测试")
    print("=" * 50)

    # 测试用例
    test_cases = [
        "Python是谁创建的？",
        "Python怎么定义函数？",
        "JavaScript的箭头函数怎么写？",
        "Go语言的goroutine是什么？",
        "什么是Node.js？",
        "今天天气怎么样？",  # 知识库没有的信息
    ]

    for question in test_cases:
        print(f"\n用户: {question}")

        # 先展示检索结果
        retrieved = rag.retrieve(question)
        print(f"检索到 {len(retrieved)} 个相关文档：")
        for i, doc in enumerate(retrieved, 1):
            print(f"  [{i}] (相似度: {doc['score']:.3f}) {doc['content'][:80]}...")

        # 获取回复
        response = rag.chat(question)
        print(f"\n助手: {response}")

    # 交互模式
    print("\n" + "=" * 50)
    print("交互模式（输入 quit 退出）")
    print("=" * 50 + "\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break
        if not user_input:
            continue

        response = rag.chat(user_input)
        print(f"助手: {response}\n")


if __name__ == "__main__":
    main()
```

---

## 3.4 代码解析

### 3.4.1 知识库构建

```python
# 1. 添加文档
rag.add_document(
    "Python是一种高级编程语言...",
    {"source": "Python百科"}
)

# 2. 文档会被自动分块
# 3. 每个块会被转换成向量
# 4. 向量和原始内容一起存储
```

### 3.4.2 检索流程

```python
# 1. 用户输入
query = "Python怎么定义函数？"

# 2. 计算查询向量
query_embedding = embedding.encode(query)

# 3. 与知识库向量计算相似度
for doc in documents:
    similarity = cosine(query_embedding, doc.embedding)

# 4. 返回 top-k
return sorted(results, key=lambda x: x.score)[:3]
```

### 3.4.3 Prompt 构建

```python
prompt = f"""基于以下知识库内容回答用户问题。

知识库：
[来源1 - Python教程]
Python的函数用def关键字定义...

用户问题：Python怎么定义函数？

回答："""
```

---

## 3.5 进阶功能

### 3.5.1 真实向量库

实际项目中应使用专门的向量库：

```python
# 使用 Chroma
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_knowledge")

# 添加文档
collection.add(
    documents=["Python是...", "JavaScript是..."],
    ids=["doc1", "doc2"]
)

# 检索
results = collection.query(
    query_texts=["Python怎么定义函数？"],
    n_results=3
)
```

```python
# 使用 FAISS
import faiss
import numpy as np

# 创建索引
dimension = 768
index = faiss.IndexFlatL2(dimension)

# 添加向量
index.add(embeddings)

# 检索
D, I = index.search(query_embedding, k=3)
```

### 3.5.2 真实 Embedding 模型

```python
# 使用 sentence-transformers
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# 编码
embeddings = model.encode(["文本1", "文本2"])
```

### 3.5.3 高级检索策略

1. **混合检索**
```python
# 向量检索 + 关键词检索
vector_results = vector_search(query)
keyword_results = keyword_search(query)
results = merge_and_rerank(vector_results, keyword_results)
```

2. **重排序**
```python
# 使用 LLM 对检索结果重排序
reranked = llm_rerank(query, retrieved_docs)
```

---

## 3.6 本章小结

本章我们实现了一个完整的 RAG Agent：

- ✅ **知识库构建**：文档添加、分块、向量化
- ✅ **向量检索**：相似度计算、Top-K 检索
- ✅ **Prompt 增强**：将检索结果融入 Prompt
- ✅ **完整流程**：检索 → 增强 → 生成

---

## 3.7 扩展练习

1. **接入真实向量库**
   - 使用 Chroma 或 FAISS
   - 使用 sentence-transformers 做 embedding

2. **构建更大知识库**
   - 加载 PDF、Word 文档
   - 加载网页内容

3. **实现高级检索**
   - 混合检索
   - 重排序

---

## 下章预告

到这里 1-ollama-agent 部分就完成了！

接下来我们将学习：
- **LitGPT 微调** - 如何微调自己的模型
- **从零实现神经网络** - 深入理解 Transformer
- **llama.cpp 原生实现** - C++ 高性能推理
