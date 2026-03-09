"""
内核源码检索器

提供两种检索模式：
1. 语义搜索 - 基于向量相似度（需要 embedding 模型）
2. 关键词搜索 - 基于 BM25 的精确匹配（离线可用，无需 GPU）

两种模式互补：
- 语义搜索擅长理解问题意图（"怎么处理中断" → 找到 IRQ 相关代码）
- 关键词搜索擅长精确匹配函数名（"generic_handle_irq" → 精确定位）

用法:
    from rag.retriever import KernelRetriever
    retriever = KernelRetriever(index_dir="rag/index")
    results = retriever.search("ARM64 系统调用入口", top_k=5)
"""

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SearchResult:
    file_path: str          # 内核源码相对路径
    content: str            # 代码片段
    score: float            # 相关性分数
    line_start: int = 0     # 起始行号
    line_end: int = 0       # 结束行号
    match_type: str = ""    # "semantic" | "keyword" | "hybrid"
    function_name: str = "" # 匹配到的函数名（如果有）


class BM25Index:
    """
    BM25 关键词索引

    完全离线可用，不需要任何 embedding 模型。
    对内核代码中的函数名、结构体名等精确匹配效果好。
    """

    def __init__(self):
        self.documents: list[dict] = []   # [{path, content, line_start, line_end, tokens}]
        self.doc_count = 0
        self.avg_doc_len = 0
        self.doc_freq: Counter = Counter()  # token -> 出现在多少文档中
        self.k1 = 1.5
        self.b = 0.75

    def add_document(self, path: str, content: str, line_start: int, line_end: int):
        tokens = self._tokenize(content)
        self.documents.append({
            "path": path,
            "content": content,
            "line_start": line_start,
            "line_end": line_end,
            "tokens": tokens,
            "token_freq": Counter(tokens),
        })
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.doc_freq[token] += 1

    def build(self):
        self.doc_count = len(self.documents)
        total_len = sum(len(d["tokens"]) for d in self.documents)
        self.avg_doc_len = total_len / self.doc_count if self.doc_count > 0 else 0

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc in enumerate(self.documents):
            score = self._bm25_score(query_tokens, doc)
            if score > 0:
                scores.append((i, score))

        scores.sort(key=lambda x: -x[1])

        results = []
        for i, score in scores[:top_k]:
            doc = self.documents[i]
            func_name = self._extract_function_name(doc["content"])
            results.append(SearchResult(
                file_path=doc["path"],
                content=doc["content"],
                score=score,
                line_start=doc["line_start"],
                line_end=doc["line_end"],
                match_type="keyword",
                function_name=func_name,
            ))
        return results

    def _bm25_score(self, query_tokens: list[str], doc: dict) -> float:
        score = 0.0
        doc_len = len(doc["tokens"])
        tf_map = doc["token_freq"]

        for token in query_tokens:
            if token not in tf_map:
                continue
            tf = tf_map[token]
            df = self.doc_freq.get(token, 0)
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
            tf_norm = (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
            )
            score += idf * tf_norm
        return score

    def _tokenize(self, text: str) -> list[str]:
        """分词：拆分标识符、小写化"""
        # 先按非字母数字字符分割
        words = re.split(r'[^a-zA-Z0-9_]+', text.lower())
        tokens = []
        for word in words:
            if not word:
                continue
            tokens.append(word)
            # 拆分 camelCase 和 snake_case
            parts = re.split(r'_', word)
            if len(parts) > 1:
                tokens.extend(p for p in parts if p)
            # 拆分 camelCase
            camel_parts = re.findall(r'[a-z]+|[A-Z][a-z]*|[0-9]+', word)
            if len(camel_parts) > 1:
                tokens.extend(p.lower() for p in camel_parts if p)
        return tokens

    def _extract_function_name(self, content: str) -> str:
        """从代码片段中提取函数名"""
        # 匹配 C 函数定义
        match = re.search(
            r'^(?:static\s+)?(?:inline\s+)?(?:__[a-z]+\s+)*'
            r'(?:void|int|long|unsigned|bool|struct\s+\w+\s*\*?|enum\s+\w+|[a-z_]+_t)\s+'
            r'(\w+)\s*\(',
            content,
            re.MULTILINE,
        )
        return match.group(1) if match else ""

    def save(self, path: Path):
        data = {
            "doc_count": self.doc_count,
            "avg_doc_len": self.avg_doc_len,
            "doc_freq": dict(self.doc_freq),
            "documents": [
                {
                    "path": d["path"],
                    "content": d["content"],
                    "line_start": d["line_start"],
                    "line_end": d["line_end"],
                }
                for d in self.documents
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        data = json.loads(path.read_text())
        index = cls()
        for doc in data["documents"]:
            index.add_document(doc["path"], doc["content"], doc["line_start"], doc["line_end"])
        index.build()
        return index


class SemanticIndex:
    """
    语义向量索引

    基于 sentence-transformers 的向量搜索。
    需要安装 sentence-transformers 和 faiss-cpu。
    如果未安装，自动降级到纯 BM25 模式。
    """

    def __init__(self, model_name: str = "BAAI/bge-base-zh-v1.5"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents: list[dict] = []
        self._available = False
        self._try_load_deps()

    def _try_load_deps(self):
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def build(self, documents: list[dict]):
        if not self._available:
            return

        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np

        self.documents = documents
        self.model = SentenceTransformer(self.model_name)

        # 为每个文档生成摘要用于 embedding
        texts = [self._make_summary(d) for d in documents]

        # 批量编码
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=64)
        embeddings = np.array(embeddings, dtype="float32")

        # 归一化用于余弦相似度
        faiss.normalize_L2(embeddings)

        # 构建 FAISS 索引
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # 内积 = 余弦相似度（归一化后）
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not self._available or self.index is None:
            return []

        import numpy as np
        import faiss

        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding, dtype="float32")
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            doc = self.documents[idx]
            results.append(SearchResult(
                file_path=doc["path"],
                content=doc["content"],
                score=float(score),
                line_start=doc["line_start"],
                line_end=doc["line_end"],
                match_type="semantic",
            ))
        return results

    def _make_summary(self, doc: dict) -> str:
        """生成文档摘要用于 embedding"""
        path = doc["path"]
        content = doc["content"][:500]
        return f"File: {path}\n{content}"

    def save(self, path: Path):
        if not self._available or self.index is None:
            return

        import faiss
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "faiss.index"))

        meta = [
            {"path": d["path"], "content": d["content"],
             "line_start": d["line_start"], "line_end": d["line_end"]}
            for d in self.documents
        ]
        (path / "documents.json").write_text(json.dumps(meta, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path, model_name: str = "BAAI/bge-base-zh-v1.5") -> "SemanticIndex":
        instance = cls(model_name=model_name)
        if not instance._available:
            return instance

        import faiss
        index_file = path / "faiss.index"
        docs_file = path / "documents.json"

        if index_file.exists() and docs_file.exists():
            instance.index = faiss.read_index(str(index_file))
            instance.documents = json.loads(docs_file.read_text())
        return instance


class KernelRetriever:
    """
    内核源码混合检索器

    结合 BM25 关键词搜索和语义向量搜索：
    - BM25：精确匹配函数名、结构体名（总是可用）
    - 语义搜索：理解问题意图（需要 sentence-transformers + faiss）

    如果语义搜索依赖未安装，自动降级到纯 BM25 模式。
    """

    def __init__(
        self,
        index_dir: Optional[Path] = None,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ):
        project_root = Path(__file__).parent.parent
        self.index_dir = index_dir or (project_root / "rag/index")
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.bm25: Optional[BM25Index] = None
        self.semantic: Optional[SemanticIndex] = None
        self._load_indices()

    def _load_indices(self):
        bm25_path = self.index_dir / "bm25.json"
        if bm25_path.exists():
            self.bm25 = BM25Index.load(bm25_path)

        semantic_dir = self.index_dir / "semantic"
        if semantic_dir.exists():
            self.semantic = SemanticIndex.load(semantic_dir)

    @property
    def available(self) -> bool:
        return self.bm25 is not None

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        混合搜索：BM25 + 语义搜索，结果融合去重
        """
        if not self.available:
            return []

        # BM25 关键词搜索（总是执行）
        bm25_results = self.bm25.search(query, top_k=top_k * 2) if self.bm25 else []

        # 语义搜索（如果可用）
        semantic_results = []
        if self.semantic and self.semantic.available and self.semantic.index is not None:
            semantic_results = self.semantic.search(query, top_k=top_k * 2)

        # 如果只有 BM25，直接返回
        if not semantic_results:
            return bm25_results[:top_k]

        # 结果融合（Reciprocal Rank Fusion）
        return self._fuse_results(bm25_results, semantic_results, top_k)

    def _fuse_results(
        self,
        bm25_results: list[SearchResult],
        semantic_results: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion 融合两路结果"""
        k = 60  # RRF 常数

        # 用 (file_path, line_start) 作为去重键
        scores: dict[tuple, float] = {}
        result_map: dict[tuple, SearchResult] = {}

        for rank, r in enumerate(bm25_results):
            key = (r.file_path, r.line_start)
            rrf_score = self.keyword_weight / (k + rank + 1)
            scores[key] = scores.get(key, 0) + rrf_score
            if key not in result_map:
                result_map[key] = r

        for rank, r in enumerate(semantic_results):
            key = (r.file_path, r.line_start)
            rrf_score = self.semantic_weight / (k + rank + 1)
            scores[key] = scores.get(key, 0) + rrf_score
            if key not in result_map:
                result_map[key] = r

        sorted_keys = sorted(scores.keys(), key=lambda k_: -scores[k_])

        results = []
        for key in sorted_keys[:top_k]:
            result = result_map[key]
            results.append(SearchResult(
                file_path=result.file_path,
                content=result.content,
                score=scores[key],
                line_start=result.line_start,
                line_end=result.line_end,
                match_type="hybrid",
                function_name=result.function_name,
            ))
        return results

    def format_context(self, results: list[SearchResult], max_chars: int = 4000) -> str:
        """
        将检索结果格式化为模型可用的上下文

        控制总长度不超过 max_chars，避免超出模型上下文窗口
        """
        if not results:
            return ""

        lines = ["[内核源码参考]"]
        total_chars = 0

        for r in results:
            header = f"\n--- {r.file_path}:{r.line_start}-{r.line_end} ---"
            if r.function_name:
                header += f" ({r.function_name})"

            chunk = f"{header}\n{r.content}\n"
            if total_chars + len(chunk) > max_chars:
                # 截断当前片段以适应限制
                remaining = max_chars - total_chars
                if remaining > len(header) + 100:
                    chunk = f"{header}\n{r.content[:remaining - len(header) - 10]}\n... (truncated)\n"
                    lines.append(chunk)
                break

            lines.append(chunk)
            total_chars += len(chunk)

        return "\n".join(lines)
