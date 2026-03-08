# RAG 深度解析

> 检索增强生成（Retrieval-Augmented Generation）从原理到实战

> **类型**: 可直接运行 | **前置**: Python 基础 | **硬件**: CPU 即可 | **额外依赖**: `pip install chromadb`

## 本章目录

### 教程 (Tutorial)
- [RAG 基础概念](tutorial/01-RAG基础概念.md)

### 理论 (Theory)
- [向量检索原理](theory/01-向量检索原理.md)

### 实战 (Hands-on)
- [构建本地知识库](hands-on/01-构建本地知识库.md)

### 代码示例 (Examples)
- [local_rag.py](examples/local_rag.py) - 基于 Ollama + ChromaDB 的本地 RAG 系统

---

## 核心内容

### RAG 是什么？

```
RAG = 检索（Retrieval） + 增强（Augmented） + 生成（Generation）
```

让 LLM 在回答问题前，先从外部知识库中检索相关信息，再基于检索结果生成答案。

### 核心流程

```
文档 → 分块 → 向量化 → 存入向量数据库
                                ↓
用户提问 → 向量化 → 相似度检索 → 取出相关文档
                                ↓
            相关文档 + 用户问题 → LLM 生成回答
```

### 适用场景

| 场景 | 说明 |
|------|------|
| 知识库问答 | 基于企业内部文档回答问题 |
| 文档搜索 | 从大量文档中精准检索信息 |
| 客服系统 | 基于产品手册自动回答客户问题 |
| 学术研究 | 从论文库中检索并总结研究进展 |

---

## 快速上手

```bash
# 安装依赖
pip install chromadb ollama

# 启动 Ollama
ollama pull qwen2.5
ollama pull nomic-embed-text

# 运行示例
python examples/local_rag.py
```

---

## 参考资源

- [ChromaDB](https://github.com/chroma-core/chroma) - 开源向量数据库
- [Ollama](https://github.com/ollama/ollama) - 本地运行 LLM
- [LangChain RAG](https://python.langchain.com/docs/tutorials/rag/) - LangChain RAG 教程
- [FAISS](https://github.com/facebookresearch/faiss) - Meta 向量检索库
- [Milvus](https://github.com/milvus-io/milvus) - 分布式向量数据库
