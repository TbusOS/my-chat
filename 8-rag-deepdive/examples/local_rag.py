#!/usr/bin/env python3
"""
本地 RAG 系统 - 基于 Ollama + ChromaDB

安装依赖：
    pip install ollama chromadb

前置条件：
    1. 安装并启动 Ollama: https://ollama.com
    2. 拉取模型:
       ollama pull qwen2.5
       ollama pull nomic-embed-text

使用方法：
    python local_rag.py
"""

import ollama
import chromadb

CHAT_MODEL = "qwen2.5"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3


class LocalRAG:
    """本地 RAG 系统"""

    def __init__(self, collection_name="knowledge"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, text):
        """生成文本的 Embedding 向量"""
        result = ollama.embed(model=EMBED_MODEL, input=text)
        return result["embeddings"][0]

    def _chunk(self, text):
        """将文本按固定长度分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunks = [*chunks, text[start:end]]
            start = end - CHUNK_OVERLAP
        return chunks

    def add_documents(self, documents):
        """添加文档到知识库

        Args:
            documents: 文档列表，每项为字符串或 {"content": str, "source": str}
        """
        all_ids = []
        all_docs = []
        all_embeddings = []
        all_metadatas = []

        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                content, source = doc, f"doc_{i}"
            else:
                content, source = doc["content"], doc.get("source", f"doc_{i}")

            chunks = self._chunk(content)
            for j, chunk in enumerate(chunks):
                all_ids = [*all_ids, f"{source}_chunk_{j}"]
                all_docs = [*all_docs, chunk]
                all_embeddings = [*all_embeddings, self._embed(chunk)]
                all_metadatas = [*all_metadatas, {"source": source, "chunk": j}]

        self.collection.add(
            ids=all_ids,
            documents=all_docs,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
        )
        print(f"[RAG] 已索引 {len(all_docs)} 个文本块")

    def query(self, question, n_results=TOP_K):
        """查询知识库并生成回答

        Args:
            question: 用户问题
            n_results: 检索的文档数量

        Returns:
            生成的回答文本
        """
        results = self.collection.query(
            query_embeddings=[self._embed(question)],
            n_results=n_results,
        )

        context = "\n---\n".join(results["documents"][0])
        prompt = (
            "你是一个知识库助手。请根据以下参考资料回答用户的问题。\n"
            "如果参考资料中没有相关信息，请如实告知。\n\n"
            f"参考资料：\n{context}\n\n"
            f"用户问题：{question}\n\n"
            "请用中文回答："
        )

        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]


def main():
    """演示：构建知识库并进行问答"""
    rag = LocalRAG()

    # 示例文档
    documents = [
        "Python 是一种解释型、面向对象的高级编程语言。它由 Guido van Rossum 于 1991 年创建。"
        "Python 以简洁的语法和丰富的库生态系统著称，广泛应用于 Web 开发、数据科学和人工智能领域。",

        "RAG（检索增强生成）是一种结合信息检索和文本生成的技术。"
        "它让大语言模型在回答问题前先从知识库中检索相关信息，从而减少幻觉并提供更准确的回答。",

        "向量数据库是专门用于存储和检索高维向量的数据库系统。"
        "常见的向量数据库包括 ChromaDB、FAISS、Milvus 和 Qdrant。"
        "它们通过近似最近邻算法实现高效的相似度搜索。",
    ]

    rag.add_documents(documents)

    # 交互式问答
    print("\n本地 RAG 知识库已就绪，输入问题开始问答（输入 q 退出）\n")
    while True:
        question = input("问题：").strip()
        if question.lower() == "q":
            break
        if not question:
            continue
        answer = rag.query(question)
        print(f"\n回答：{answer}\n")


if __name__ == "__main__":
    main()
