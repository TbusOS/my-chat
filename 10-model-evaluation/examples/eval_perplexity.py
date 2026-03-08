#!/usr/bin/env python3
"""
eval_perplexity.py - 计算语言模型的困惑度 (Perplexity)

困惑度是衡量语言模型质量的基础指标。
值越低，模型对文本的建模能力越强。

用法:
    python eval_perplexity.py

依赖:
    pip install torch transformers
"""

import math
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def compute_perplexity(model, tokenizer, text, max_length=2048):
    """
    计算模型在给定文本上的困惑度。

    Args:
        model: 语言模型
        tokenizer: 对应的分词器
        text: 待评估的文本
        max_length: 最大 token 长度

    Returns:
        困惑度值 (float)
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    ).to(model.device)

    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])

    return math.exp(outputs.loss.item())


def compare_models(model_names, eval_texts):
    """
    对比多个模型在相同文本上的困惑度。

    Args:
        model_names: 模型名称列表 (Hugging Face Hub ID)
        eval_texts: 评估文本列表

    Returns:
        对比结果字典
    """
    results = {}

    for model_name in model_names:
        print(f"\n{'='*50}")
        print(f"Loading: {model_name}")

        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
            )
            model.eval()
        except Exception as e:
            print(f"  Failed to load model: {e}")
            continue

        perplexities = []

        for i, text in enumerate(eval_texts):
            ppl = compute_perplexity(model, tokenizer, text)
            perplexities.append(ppl)
            print(f"  Text {i+1}: PPL = {ppl:.2f}")

        avg_ppl = sum(perplexities) / len(perplexities)
        results[model_name] = {
            "per_text": perplexities,
            "average": avg_ppl,
        }
        print(f"  Average PPL: {avg_ppl:.2f}")

        # 释放显存
        del model
        del tokenizer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

    return results


def main():
    # ---- 评估文本 ----
    eval_texts = [
        "大语言模型通过在大规模文本语料上进行预训练，"
        "学习到了丰富的语言知识和世界知识。",

        "Python 是一种解释型、面向对象的高级编程语言，"
        "广泛应用于数据科学、人工智能和 Web 开发。",

        "Transformer 架构的核心是自注意力机制，"
        "它允许模型在处理每个位置时关注输入序列的所有位置。",

        "梯度下降是深度学习中最基本的优化算法，"
        "通过计算损失函数相对于参数的梯度来更新模型权重。",
    ]

    # ---- 要对比的模型 ----
    # 根据你的硬件条件选择合适大小的模型
    model_names = [
        "Qwen/Qwen2.5-0.5B",
        # "Qwen/Qwen2.5-1.5B",  # 需要更多显存
    ]

    print("Perplexity Evaluation")
    print("=" * 50)
    print(f"Number of eval texts: {len(eval_texts)}")
    print(f"Models to compare: {len(model_names)}")

    results = compare_models(model_names, eval_texts)

    # ---- 输出对比结果 ----
    print("\n" + "=" * 50)
    print("COMPARISON SUMMARY")
    print("=" * 50)
    print(f"{'Model':<30} {'Avg PPL':>10}")
    print("-" * 42)

    sorted_results = sorted(results.items(), key=lambda x: x[1]["average"])
    for model_name, data in sorted_results:
        short_name = model_name.split("/")[-1]
        print(f"{short_name:<30} {data['average']:>10.2f}")

    if len(sorted_results) > 1:
        best_model = sorted_results[0][0].split("/")[-1]
        print(f"\nBest model (lowest PPL): {best_model}")


if __name__ == "__main__":
    main()
