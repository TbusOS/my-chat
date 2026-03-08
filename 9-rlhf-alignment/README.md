# RLHF 与对齐技术

## 概述

大语言模型（LLM）经过预训练后，虽然具备了强大的语言能力，但并不天然"有用且安全"。对齐（Alignment）技术的目标是让模型的输出符合人类意图——既有帮助、又诚实、还无害。

本模块覆盖从经典 RLHF 到最新 DPO 的完整对齐技术栈，帮助你理解并实践模型对齐。

## 为什么对齐很重要

- 预训练模型只学会了"预测下一个 token"，而不是"回答用户问题"
- 没有对齐的模型可能生成有害、虚假或无用的内容
- 对齐是从 GPT-3 到 ChatGPT 的关键跨越

## 文档结构

### 教程 (Tutorial)

| 文档 | 内容 |
|------|------|
| [对齐技术入门](tutorial/01-对齐技术入门.md) | 对齐的动机、三阶段流程、主流方法对比 |

### 理论 (Theory)

| 文档 | 内容 |
|------|------|
| [RLHF 原理详解](theory/01-RLHF原理详解.md) | SFT、奖励模型、PPO 完整流程 |
| [DPO 原理详解](theory/02-DPO原理详解.md) | Direct Preference Optimization 原理与对比 |

### 实战 (Hands-on)

| 文档 | 内容 |
|------|------|
| [DPO 微调实战](hands-on/01-DPO微调实战.md) | 使用 TRL 库进行 DPO 训练的完整代码 |

## 环境要求

- Python 3.10+
- PyTorch 2.0+
- transformers >= 4.36
- trl >= 0.7
- 推荐 GPU: A100 / RTX 4090 (16GB+ 显存)

## 参考链接

- [InstructGPT 论文](https://arxiv.org/abs/2203.02155)
- [DPO 论文](https://arxiv.org/abs/2305.18290)
- [TRL 库文档](https://huggingface.co/docs/trl)
- [Anthropic RLHF 论文](https://arxiv.org/abs/2204.05862)
- [ORPO 论文](https://arxiv.org/abs/2403.07691)
- [Hugging Face 对齐手册](https://github.com/huggingface/alignment-handbook)
