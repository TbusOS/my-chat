#!/usr/bin/env python3
"""
RAG 检索增强 Agent
功能：让 Agent 能够从自己的知识库中检索信息

使用方法:
    python examples/rag_agent.py
"""

import ollama
import re
from typing import List, Dict, Tuple


class RAGAgent:
    """检索增强生成 Agent"""

    def __init__(self, model: str = "qwen2.5", top_k: int = 3):
        self.model = model
        self.top_k = top_k
        self.knowledge_base: List[Dict] = []

    def add_knowledge(self, text: str, metadata: Dict = None):
        """添加知识到知识库"""
        self.knowledge_base.append({
            'text': text,
            'metadata': metadata or {}
        })

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()

    def retrieve(self, query: str) -> List[Tuple[float, str]]:
        """基于关键词匹配的简单检索"""
        if not self.knowledge_base:
            return []

        similarities = []
        for item in self.knowledge_base:
            query_words = set(self._tokenize(query))
            text_words = set(self._tokenize(item['text']))
            overlap = query_words & text_words

            if overlap:
                score = len(overlap) / max(len(query_words), len(text_words))
            else:
                score = 0.0

            similarities.append((score, item['text']))

        similarities.sort(reverse=True)
        return similarities[:self.top_k]

    def chat(self, user_input: str) -> str:
        """RAG 对话"""
        results = self.retrieve(user_input)

        if results:
            context_text = "\n\n".join(
                [f"[{i+1}] {text}" for i, (_, text) in enumerate(results)]
            )
            context_prompt = f"""基于以下知识库内容回答用户问题。如果知识库没有相关信息，请如实说明。

知识库：
{context_text}

用户问题：{user_input}

回答："""
        else:
            context_prompt = f"用户问题：{user_input}\n\n回答："

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': context_prompt}]
        )

        return response['message']['content']


if __name__ == "__main__":
    rag = RAGAgent("qwen2.5")

    print("添加知识到知识库...")
    rag.add_knowledge("Python是一种高级编程语言，由Guido van Rossum于1991年创建。")
    rag.add_knowledge("Python的函数用def关键字定义，如：def hello(): print('Hello')")
    rag.add_knowledge("Go是Google开发的编程语言，以高性能和并发支持著称。")
    rag.add_knowledge("Go的goroutine是轻量级线程，用go关键字启动：go func() {}")
    print(f"知识库大小: {len(rag.knowledge_base)}")

    print("\n" + "=" * 50)
    print("RAG Agent 测试")
    print("=" * 50)

    questions = [
        "Python是谁创建的？",
        "Go语言的goroutine是什么？",
        "今天天气怎么样？",
    ]

    for q in questions:
        print(f"\n用户: {q}")
        response = rag.chat(q)
        print(f"助手: {response}")
