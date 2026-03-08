# LitGPT 微调实战教程

> **类型**: 外部项目教程 | **前置**: Python 基础 | **硬件**: NVIDIA GPU（推荐）

## 概述

LitGPT 是一个轻量级、高性能的 LLM 训练框架，支持 LoRA、QLoRA、全参数微调等多种训练方式。

## 环境要求

- Python 3.9+
- CUDA 11.8+ (GPU训练)
- 16GB+ RAM (CPU训练较慢)
- 推荐 A100/H100 或消费级 RTX 4090

## 安装

```bash
# 克隆仓库
git clone https://github.com/Lightning-AI/litgpt.git
cd litgpt

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[all]"
```

## 下载预训练模型

```bash
# 方法1：使用 litgpt CLI 下载（推荐，当前版本）
litgpt download --repo_id microsoft/phi-2

# 方法2：使用 Python API
# python -c "from litgpt import download; download('microsoft/phi-2')"

# 方法3：手动从 HuggingFace 下载
# huggingface-cli download microsoft/phi-2 --local-dir models/phi-2/

# 注意：旧版本使用 python scripts/download.py，新版已迁移到 litgpt CLI
```

## 训练方式

### 1. LoRA 微调（推荐入门）

LoRA (Low-Rank Adaptation) 只训练少量参数，适合消费级 GPU。

```bash
# 单卡训练
python finetune/lora.py \
    --model.size 7b \
    --model.quantization bnb.nf4 \
    --data.alpaca \
    --lora.r 8 \
    --lora.alpha 16 \
    --lora.dropout 0.05 \
    --train.epochs 3 \
    --train.batch_size 8 \
    --train.gradient_accumulation_steps 4 \
    --train.lr 3e-4
```

### 2. QLoRA 微调（更省显存）

```bash
# 4bit 量化 + LoRA
python finetune/lora.py \
    --model.size 7b \
    --model.quantization 4bit \
    --model.quantization_config bnb \
    --data.alpaca \
    --lora.r 64 \
    --train.epochs 3
```

### 3. 全参数微调（需要多卡）

```bash
python finetune/full.py \
    --model.size 7b \
    --data.alpaca \
    --train.epochs 1 \
    --train.batch_size 1 \
    --train.micro_batch_size 1
```

## 数据准备

### Alpaca 格式

```json
[
  {
    "instruction": "生成一个Python函数",
    "input": "计算斐波那契数列",
    "output": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
  },
  {
    "instruction": "解释什么是机器学习",
    "input": "",
    "output": "机器学习是人工智能的一个分支..."
  }
]
```

### 自定义数据

```python
from litgpt.data import CustomData

# 在配置中指定
--data.custom "path/to/your/data.json" \
--data.formats alpaca
```

## 训练脚本示例

```bash
#!/bin/bash
# lora_train.sh

# 设置环境
export CUDA_VISIBLE_DEVICES=0

python finetune/lora.py \
    --model.name Llama-3.2-1B \
    --model.tokenizer_dir Llama-3.2-1B \
    --data.alpaca \
    --data.max_seq_length 512 \
    --lora.r 16 \
    --lora.alpha 32 \
    --lora.dropout 0.05 \
    --lora.query_key \
    --lora.value \
    --lora.projection \
    --lora.mlp \
    --train.epochs 3 \
    --train.batch_size 4 \
    --train.gradient_accumulation_steps 2 \
    --train.lr 3e-4 \
    --train.warmup_steps 100 \
    --train.save_interval 500 \
    --train.log_interval 10 \
    --out_dir out/lora-llama
```

## 推理测试

```python
from litgpt import LLM

# 加载微调后的模型
llm = LLM.load(
    name="Llama-3.2-1B",
    finetune_path="out/lora-llama"
)

# 对话
response = llm.chat(
    messages=[{"role": "user", "content": "写一个快速排序函数"}]
)
print(response)
```

## 配置详解

### LoRA 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--lora.r` | 8 | LoRA 秩，越大越强但越慢 |
| `--lora.alpha` | 16 | 缩放因子 |
| `--lora.dropout` | 0.05 | Dropout 概率 |
| `--lora.query_key` | true | 是否在 Q、K 上应用 LoRA |

### 训练参数

| 参数 | 说明 |
|------|------|
| `--train.epochs` | 训练轮数 |
| `--train.batch_size` | 全局批次大小 |
| `--train.gradient_accumulation_steps` | 梯度累积步数 |
| `--train.lr` | 学习率 |
| `--train.warmup_steps` | 预热步数 |

## 常见问题

### 显存不够？

- 使用 `--model.quantization bnb.nf4`
- 减小 `--train.batch_size`
- 使用 `--train.gradient_accumulation_steps`

### 训练崩溃？

- 降低学习率 `--train.lr`
- 增加 warmup_steps

### 效果不好？

- 增加训练数据量
- 调整 LoRA r 和 alpha
- 增加训练 epochs

## 参考链接

- [LitGPT 官网](https://lightning.ai/litgpt)
- [LitGPT GitHub](https://github.com/Lightning-AI/litgpt)
- [LoRA 论文](https://arxiv.org/abs/2106.09685)
