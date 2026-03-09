"""
内核专家推理引擎

三层回答架构：
1. 知识库精确查询（100% 准确）
2. 本地模型 + RAG 源码检索（标注置信度，有代码佐证）
3. 可选 Opus 4.6 兜底（用户不满意时）

用法:
    from serve.api.engine import KernelExpertEngine
    engine = KernelExpertEngine()
    result = engine.ask("ARM64 的系统调用入口是什么？")
"""

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class Confidence(Enum):
    CERTAIN = "certain"      # 来自知识库精确匹配
    HIGH = "high"            # 模型有把握
    POSSIBLE = "possible"    # 模型不太确定
    UNSURE = "unsure"        # 模型明确不确定


@dataclass
class Answer:
    text: str
    confidence: Confidence
    source: str                          # "knowledge_base" | "local_model" | "opus_api"
    knowledge_refs: list[str] = field(default_factory=list)  # 引用的 YAML 文件
    call_chain: Optional[list[str]] = None
    exec_context: Optional[str] = None   # "process" | "softirq" | "hardirq"
    can_sleep: Optional[bool] = None
    latency_ms: float = 0


class KnowledgeIndex:
    """知识库索引，支持快速查询"""

    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.entries: dict[str, dict] = {}        # keyword -> yaml data
        self.call_chains: dict[str, list] = {}    # function_name -> call chain
        self.callbacks: dict[str, dict] = {}      # pattern -> callback info
        self._build_index()

    def _build_index(self):
        """构建知识库索引"""
        for yaml_file in self.knowledge_dir.rglob("*.yaml"):
            try:
                content = yaml.safe_load(yaml_file.read_text())
                if not isinstance(content, dict):
                    continue

                rel_path = str(yaml_file.relative_to(self.knowledge_dir))
                self._index_yaml(content, rel_path)
            except Exception:
                continue

    def _index_yaml(self, data: dict, source_file: str):
        """递归索引 YAML 内容"""
        for key, value in data.items():
            if not isinstance(value, dict):
                continue

            # 索引回调信息
            if "callbacks" in value and isinstance(value["callbacks"], dict):
                for cb_name, cb_info in value["callbacks"].items():
                    if isinstance(cb_info, dict):
                        cb_info["_source"] = source_file
                        cb_info["_framework"] = key
                        # 用 pattern 作为索引键
                        if "pattern" in cb_info:
                            self.callbacks[cb_info["pattern"]] = cb_info
                        # 用回调名作为索引键
                        self.callbacks[f"{key}.{cb_name}"] = cb_info

            # 索引调用链
            if "kernel_call_chain" in value:
                chain_data = value["kernel_call_chain"]
                if isinstance(chain_data, dict) and "chain" in chain_data:
                    chain = chain_data["chain"]
                    trigger = chain_data.get("trigger", "unknown")
                    self.call_chains[key] = {
                        "trigger": trigger,
                        "chain": chain,
                        "source": source_file,
                    }

            # 通用关键词索引
            desc = value.get("description", "")
            if desc:
                self.entries[key] = {
                    "description": desc,
                    "data": value,
                    "source": source_file,
                }

    def query(self, question: str) -> Optional[Answer]:
        """在知识库中查找精确答案"""
        q_lower = question.lower()

        # 1. 查找调用链相关问题
        for key, chain_info in self.call_chains.items():
            if key.replace("_", " ") in q_lower or key in q_lower:
                chain = chain_info["chain"]
                chain_text = self._format_call_chain(chain_info)
                return Answer(
                    text=chain_text,
                    confidence=Confidence.CERTAIN,
                    source="knowledge_base",
                    knowledge_refs=[chain_info["source"]],
                    call_chain=[step.get("function", "") for step in chain],
                )

        # 2. 查找回调相关问题
        for pattern_key, cb_info in self.callbacks.items():
            cb_name = pattern_key.split(".")[-1] if "." in pattern_key else pattern_key
            if cb_name in q_lower:
                cb_text = self._format_callback(cb_info)
                exec_ctx = cb_info.get("context")
                return Answer(
                    text=cb_text,
                    confidence=Confidence.CERTAIN,
                    source="knowledge_base",
                    knowledge_refs=[cb_info.get("_source", "")],
                    exec_context=exec_ctx,
                    can_sleep=cb_info.get("can_sleep"),
                )

        # 3. 通用关键词匹配
        best_match = None
        best_score = 0
        for key, entry in self.entries.items():
            score = sum(1 for word in key.split("_") if word in q_lower)
            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score >= 2:
            return Answer(
                text=f"{best_match['description']}\n\n{json.dumps(best_match['data'], indent=2, ensure_ascii=False)}",
                confidence=Confidence.HIGH,
                source="knowledge_base",
                knowledge_refs=[best_match["source"]],
            )

        return None

    def _format_call_chain(self, chain_info: dict) -> str:
        """格式化调用链为可读文本"""
        lines = [f"触发: {chain_info['trigger']}\n"]
        lines.append("调用链:")
        for i, step in enumerate(chain_info["chain"]):
            func = step.get("function", "?")
            file = step.get("file", "")
            desc = step.get("description", "")
            is_user = step.get("is_user_entry", False)
            indent = "  " * (i + 1)
            marker = " <-- 用户代码入口" if is_user else ""
            file_info = f"  [{file}]" if file else ""
            desc_info = f"  // {desc}" if desc else ""
            lines.append(f"{indent}{func}{file_info}{desc_info}{marker}")
        return "\n".join(lines)

    def _format_callback(self, cb_info: dict) -> str:
        """格式化回调信息"""
        lines = []
        if "description" in cb_info:
            lines.append(cb_info["description"])
        if "trigger" in cb_info:
            lines.append(f"触发条件: {cb_info['trigger']}")
        if "context" in cb_info:
            lines.append(f"执行上下文: {cb_info['context']}")
        if "can_sleep" in cb_info:
            lines.append(f"可睡眠: {'是' if cb_info['can_sleep'] else '否'}")
        if "signature" in cb_info:
            lines.append(f"函数签名: {cb_info['signature']}")
        return "\n".join(lines)


class KernelExpertEngine:
    """内核专家推理引擎"""

    def __init__(
        self,
        knowledge_dir: Optional[Path] = None,
        model_name: str = "kernel-expert",
        feedback_dir: Optional[Path] = None,
        rag_index_dir: Optional[Path] = None,
        enable_rag: bool = True,
    ):
        project_root = Path(__file__).parent.parent.parent
        self.knowledge_dir = knowledge_dir or (project_root / "knowledge")
        self.feedback_dir = feedback_dir or (project_root / "serve/feedback")
        self.model_name = model_name
        self.enable_rag = enable_rag

        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_index = KnowledgeIndex(self.knowledge_dir)

        # 初始化 RAG 检索器
        self.retriever = None
        if enable_rag:
            try:
                from rag.retriever import KernelRetriever
                rag_dir = rag_index_dir or (project_root / "rag/index")
                self.retriever = KernelRetriever(index_dir=rag_dir)
                if not self.retriever.available:
                    self.retriever = None
            except (ImportError, Exception):
                self.retriever = None

        # 交互日志
        self.session_log: list[dict] = []

    def ask(self, question: str) -> Answer:
        """主入口：回答用户问题"""
        start = time.time()

        # 第一层：知识库精确查询
        kb_answer = self.knowledge_index.query(question)
        if kb_answer and kb_answer.confidence == Confidence.CERTAIN:
            kb_answer.latency_ms = (time.time() - start) * 1000
            self._log_interaction(question, kb_answer)
            return kb_answer

        # 第二层：本地模型 + RAG 增强回答
        rag_context = self._retrieve_source_code(question)
        model_answer = self._query_local_model(question, rag_context=rag_context)
        model_answer.latency_ms = (time.time() - start) * 1000

        # 如果知识库有部分匹配，合并信息
        if kb_answer:
            model_answer.text = (
                f"[知识库参考]\n{kb_answer.text}\n\n"
                f"[模型补充]\n{model_answer.text}"
            )
            model_answer.knowledge_refs = kb_answer.knowledge_refs
            model_answer.confidence = Confidence.HIGH

        self._log_interaction(question, model_answer)
        return model_answer

    def _retrieve_source_code(self, question: str) -> str:
        """从内核源码中检索相关代码片段"""
        if not self.retriever:
            return ""

        try:
            from rag.retriever import KernelRetriever
            results = self.retriever.search(question, top_k=3)
            if results:
                return self.retriever.format_context(results, max_chars=3000)
        except Exception:
            pass
        return ""

    def _query_local_model(self, question: str, rag_context: str = "") -> Answer:
        """查询本地 Ollama 模型，可选附带 RAG 检索到的源码上下文"""
        try:
            # 如果有 RAG 上下文，构建增强 prompt
            if rag_context:
                prompt = (
                    f"基于以下内核源码片段回答问题。如果源码片段与问题无关，忽略它们。\n\n"
                    f"{rag_context}\n\n"
                    f"问题: {question}"
                )
                source = "local_model+rag"
            else:
                prompt = question
                source = "local_model"

            result = subprocess.run(
                ["ollama", "run", self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            text = result.stdout.strip()

            # 简单的置信度判断
            confidence = Confidence.HIGH
            unsure_markers = ["不确定", "不太确定", "可能", "I'm not sure", "不太清楚"]
            if any(m in text for m in unsure_markers):
                confidence = Confidence.UNSURE

            return Answer(
                text=text,
                confidence=confidence,
                source=source,
            )
        except subprocess.TimeoutExpired:
            return Answer(
                text="[模型推理超时]",
                confidence=Confidence.UNSURE,
                source="local_model",
            )
        except FileNotFoundError:
            return Answer(
                text="[Ollama 未安装或模型未加载]",
                confidence=Confidence.UNSURE,
                source="local_model",
            )

    def submit_feedback(self, question: str, answer: Answer, feedback: str, correction: str = ""):
        """
        提交用户反馈

        feedback: "correct" | "incorrect" | "partial"
        correction: 用户提供的正确答案（可选）
        """
        entry = {
            "timestamp": time.time(),
            "question": question,
            "answer": answer.text,
            "answer_source": answer.source,
            "answer_confidence": answer.confidence.value,
            "feedback": feedback,
            "correction": correction,
        }

        # 追加到反馈日志
        feedback_file = self.feedback_dir / "feedback_log.jsonl"
        with open(feedback_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # 如果有修正，尝试提取知识更新到 pending 目录
        if correction and feedback == "incorrect":
            self._extract_knowledge_update(question, correction)

    def _extract_knowledge_update(self, question: str, correction: str):
        """从用户修正中提取知识库更新建议"""
        pending_dir = self.feedback_dir / "pending_updates"
        pending_dir.mkdir(exist_ok=True)

        update = {
            "timestamp": time.time(),
            "question": question,
            "correction": correction,
            "status": "pending",  # pending -> reviewed -> applied | rejected
        }

        update_file = pending_dir / f"update_{int(time.time())}.json"
        update_file.write_text(json.dumps(update, ensure_ascii=False, indent=2))

    def _log_interaction(self, question: str, answer: Answer):
        """记录交互日志"""
        self.session_log.append({
            "timestamp": time.time(),
            "question": question,
            "answer_confidence": answer.confidence.value,
            "answer_source": answer.source,
            "latency_ms": answer.latency_ms,
        })

    def get_stats(self) -> dict:
        """获取使用统计"""
        feedback_file = self.feedback_dir / "feedback_log.jsonl"
        if not feedback_file.exists():
            return {"total_feedback": 0}

        total = 0
        correct = 0
        incorrect = 0
        by_source = {"knowledge_base": 0, "local_model": 0, "local_model+rag": 0}
        by_source_correct = {"knowledge_base": 0, "local_model": 0, "local_model+rag": 0}

        with open(feedback_file) as f:
            for line in f:
                entry = json.loads(line)
                total += 1
                source = entry.get("answer_source", "unknown")
                by_source[source] = by_source.get(source, 0) + 1

                if entry["feedback"] == "correct":
                    correct += 1
                    by_source_correct[source] = by_source_correct.get(source, 0) + 1
                elif entry["feedback"] == "incorrect":
                    incorrect += 1

        return {
            "total_feedback": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": correct / total if total > 0 else 0,
            "by_source": by_source,
            "by_source_accuracy": {
                s: by_source_correct.get(s, 0) / by_source[s] if by_source[s] > 0 else 0
                for s in by_source
            },
            "pending_updates": len(list((self.feedback_dir / "pending_updates").glob("*.json")))
            if (self.feedback_dir / "pending_updates").exists()
            else 0,
        }
