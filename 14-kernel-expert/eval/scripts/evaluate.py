"""
内核专家模型评估脚本

评估模型在内核知识问答上的表现，支持多维度打分。

用法:
    python eval/scripts/evaluate.py --model kernel-expert
    python eval/scripts/evaluate.py --model kernel-expert --baseline qwen2.5:32b
    python eval/scripts/evaluate.py --benchmark eval/benchmarks/arm64.jsonl
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
BENCHMARKS_DIR = PROJECT_ROOT / "eval/benchmarks"
RESULTS_DIR = PROJECT_ROOT / "eval/results"

# 评估维度及权重
EVAL_DIMENSIONS = {
    "call_chain_accuracy": {
        "weight": 0.30,
        "description": "调用链中函数名和顺序是否正确",
    },
    "context_correctness": {
        "weight": 0.25,
        "description": "执行上下文（进程/软中断/硬中断）判断是否正确",
    },
    "sleep_correctness": {
        "weight": 0.15,
        "description": "可睡眠性判断是否正确",
    },
    "source_accuracy": {
        "weight": 0.10,
        "description": "引用的源文件路径是否正确",
    },
    "explanation_clarity": {
        "weight": 0.10,
        "description": "解释是否清晰准确",
    },
    "no_hallucination": {
        "weight": 0.10,
        "description": "是否没有编造不存在的函数或 API",
    },
}

# 执行上下文关键词
CONTEXT_KEYWORDS = {
    "process": ["进程上下文", "process context", "can sleep", "可睡眠", "可以睡眠"],
    "softirq": ["软中断", "softirq", "soft irq", "bottom half", "不可睡眠"],
    "hardirq": ["硬中断", "hardirq", "hard irq", "interrupt context", "中断上下文"],
}


def query_ollama(model: str, question: str) -> str:
    """通过 Ollama 查询模型"""
    try:
        result = subprocess.run(
            ["ollama", "run", model, question],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except FileNotFoundError:
        print("Error: ollama not found")
        sys.exit(1)


def score_call_chain(answer: str, expected: dict) -> float:
    """评估调用链准确性"""
    expected_functions = expected.get("call_chain_functions", [])
    if not expected_functions:
        return 1.0  # 无调用链要求时满分

    found = 0
    for func in expected_functions:
        if func.lower() in answer.lower():
            found += 1

    return found / len(expected_functions) if expected_functions else 0


def score_context(answer: str, expected: dict) -> float:
    """评估执行上下文判断"""
    expected_context = expected.get("expected_context")
    if not expected_context:
        return 1.0

    context_keywords = CONTEXT_KEYWORDS.get(expected_context, [])
    return 1.0 if any(kw in answer.lower() for kw in context_keywords) else 0.0


def score_sleep(answer: str, expected: dict) -> float:
    """评估可睡眠性判断"""
    expected_sleep = expected.get("can_sleep")
    if expected_sleep is None:
        return 1.0

    if expected_sleep:
        return 1.0 if any(kw in answer for kw in ["可睡眠", "可以睡眠", "can sleep"]) else 0.0
    else:
        return 1.0 if any(kw in answer for kw in ["不可睡眠", "不能睡眠", "cannot sleep"]) else 0.0


def score_source_files(answer: str, expected: dict) -> float:
    """评估源文件引用"""
    expected_files = expected.get("source_files", [])
    if not expected_files:
        return 1.0

    found = 0
    for f in expected_files:
        if f in answer:
            found += 1

    return found / len(expected_files) if expected_files else 0


def score_hallucination(answer: str, expected: dict) -> float:
    """检查幻觉（简单启发式）"""
    # 检查是否包含明显的虚构函数
    fake_patterns = expected.get("known_fake_patterns", [])
    for pattern in fake_patterns:
        if pattern in answer:
            return 0.0
    return 1.0


def evaluate_single(answer: str, expected: dict) -> dict:
    """评估单条回答"""
    scores = {
        "call_chain_accuracy": score_call_chain(answer, expected),
        "context_correctness": score_context(answer, expected),
        "sleep_correctness": score_sleep(answer, expected),
        "source_accuracy": score_source_files(answer, expected),
        "no_hallucination": score_hallucination(answer, expected),
        "explanation_clarity": 1.0,  # 需要人工评估，默认满分
    }

    weighted_score = sum(
        scores[dim] * info["weight"]
        for dim, info in EVAL_DIMENSIONS.items()
    )

    return {
        "scores": scores,
        "weighted_score": weighted_score,
    }


def load_benchmark(path: Path) -> list[dict]:
    """加载评估数据集"""
    data = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def run_evaluation(model: str, benchmark_path: Path) -> dict:
    """运行完整评估"""
    benchmark = load_benchmark(benchmark_path)
    print(f"Loaded {len(benchmark)} benchmark questions from {benchmark_path.name}")

    results = []
    total_score = 0

    for i, item in enumerate(benchmark):
        question = item["question"]
        expected = item.get("expected", {})

        print(f"  [{i+1}/{len(benchmark)}] {question[:60]}...", end=" ", flush=True)

        answer = query_ollama(model, question)
        eval_result = evaluate_single(answer, expected)

        result = {
            "question": question,
            "answer": answer,
            "expected": expected,
            "category": item.get("category", "unknown"),
            "arch": item.get("arch", "both"),
            **eval_result,
        }

        results.append(result)
        total_score += eval_result["weighted_score"]
        print(f"score={eval_result['weighted_score']:.2f}")

        time.sleep(0.5)

    avg_score = total_score / len(benchmark) if benchmark else 0

    # 按维度汇总
    dimension_scores = {}
    for dim in EVAL_DIMENSIONS:
        dim_scores = [r["scores"][dim] for r in results]
        dimension_scores[dim] = sum(dim_scores) / len(dim_scores) if dim_scores else 0

    # 按类别汇总
    category_scores = {}
    for result in results:
        cat = result["category"]
        category_scores.setdefault(cat, []).append(result["weighted_score"])

    category_avg = {
        cat: sum(scores) / len(scores)
        for cat, scores in category_scores.items()
    }

    return {
        "model": model,
        "benchmark": benchmark_path.name,
        "total_questions": len(benchmark),
        "average_score": avg_score,
        "dimension_scores": dimension_scores,
        "category_scores": category_avg,
        "results": results,
    }


def print_report(report: dict):
    """打印评估报告"""
    print(f"\n{'='*60}")
    print(f"Evaluation Report: {report['model']}")
    print(f"Benchmark: {report['benchmark']}")
    print(f"{'='*60}")
    print(f"\nOverall Score: {report['average_score']:.1%}")

    print(f"\nDimension Scores:")
    for dim, score in report["dimension_scores"].items():
        weight = EVAL_DIMENSIONS[dim]["weight"]
        desc = EVAL_DIMENSIONS[dim]["description"]
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"  {dim:25s} {bar} {score:.1%} (weight={weight:.0%}) {desc}")

    print(f"\nCategory Scores:")
    for cat, score in sorted(report["category_scores"].items()):
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"  {cat:25s} {bar} {score:.1%}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate kernel expert model")
    parser.add_argument("--model", required=True, help="Ollama model name")
    parser.add_argument("--benchmark", type=Path, help="Benchmark JSONL file")
    parser.add_argument("--baseline", help="Baseline model for comparison")
    parser.add_argument("--output", type=Path, help="Output report path")
    args = parser.parse_args()

    # 默认评估所有基准
    if args.benchmark:
        benchmarks = [args.benchmark]
    else:
        benchmarks = sorted(BENCHMARKS_DIR.glob("*.jsonl"))
        if not benchmarks:
            print(f"No benchmarks found in {BENCHMARKS_DIR}/")
            print("Create benchmark files first (see eval/benchmarks/example.jsonl)")
            sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for benchmark_path in benchmarks:
        print(f"\nEvaluating {args.model} on {benchmark_path.name}...")
        report = run_evaluation(args.model, benchmark_path)
        print_report(report)

        # 保存报告
        output_path = args.output or (RESULTS_DIR / f"{args.model}_{benchmark_path.stem}.json")
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\nReport saved to: {output_path}")

    # 基线对比
    if args.baseline:
        print(f"\n{'='*60}")
        print(f"Running baseline: {args.baseline}")
        for benchmark_path in benchmarks:
            baseline_report = run_evaluation(args.baseline, benchmark_path)
            print_report(baseline_report)

            baseline_output = RESULTS_DIR / f"{args.baseline}_{benchmark_path.stem}.json"
            baseline_output.write_text(json.dumps(baseline_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
