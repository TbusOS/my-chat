# 模型评估方法论

> 如何科学地衡量 LLM 的能力？"感觉还行"远远不够。

> **类型**: 可直接运行 | **前置**: Python 基础 | **硬件**: CPU / GPU | **额外依赖**: `pip install lm-eval`

## 为什么评估重要？

模型评估是 LLM 开发中最容易被忽略、却最关键的环节：

- **选型决策**：在众多开源模型中选出最适合你场景的那个
- **微调验证**：确认微调后的模型确实比基座更好
- **回归检测**：升级模型版本时，确保核心能力没有退化
- **成本优化**：找到性能与推理成本的最优平衡点

## 本章目录

### 教程 (Tutorial)
- [评估方法入门](tutorial/01-评估方法入门.md) - 自动评估 vs 人工评估，常见指标一览

### 理论 (Theory)
- [评估指标详解](theory/01-评估指标详解.md) - Perplexity、BLEU、ROUGE、Pass@k 深度解析

### 实战 (Hands-on)
- [评估你的模型](hands-on/01-评估你的模型.md) - 用 lm-evaluation-harness 评估本地模型

### 代码示例 (Examples)
- [eval_perplexity.py](examples/eval_perplexity.py) - Python 计算 Perplexity 的完整实现

## 学习路径

```
评估方法入门 → 评估指标详解 → 动手评估你的模型
     ↑               ↑              ↑
   了解全貌      理解数学原理    实际跑通评估流程
```

## 前置知识

- 已完成 [1-ollama-agent](../1-ollama-agent/) 或有基本的 LLM 使用经验
- Python 基础
- 了解基本的概率与统计概念（有帮助但非必需）

## 参考资源

- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) - 最权威的 LLM 评估框架
- [Open LLM Leaderboard](https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard_2) - Hugging Face 开放排行榜
- [C-Eval](https://cevalbenchmark.com/) - 中文大模型评估基准
- [HumanEval](https://github.com/openai/human-eval) - OpenAI 代码生成评估
- [MMLU](https://github.com/hendrycks/test) - 大规模多任务语言理解基准
