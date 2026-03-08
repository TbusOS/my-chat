# DPO 微调实战

## 概述

本教程使用 Hugging Face 的 TRL（Transformer Reinforcement Learning）库，对一个小型语言模型进行 DPO 训练。整个流程可以在单张 GPU（16GB+）上完成。

## 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install torch transformers trl datasets peft accelerate bitsandbytes
```

### 依赖版本

| 库 | 最低版本 | 用途 |
|----|---------|------|
| transformers | >= 4.36 | 模型加载和推理 |
| trl | >= 0.7 | DPO 训练器 |
| datasets | >= 2.14 | 数据加载 |
| peft | >= 0.6 | LoRA 支持 |
| accelerate | >= 0.24 | 分布式训练 |
| bitsandbytes | >= 0.41 | 量化支持 |

## 步骤 1：准备偏好数据集

### 使用现有数据集

```python
from datasets import load_dataset

# 加载 Anthropic 的人类偏好数据集
dataset = load_dataset("Anthropic/hh-rlhf", split="train[:5000]")

# 查看数据结构
print(dataset[0])
# {
#     "chosen": "Human: ...\nAssistant: (高质量回答)",
#     "rejected": "Human: ...\nAssistant: (低质量回答)"
# }
```

### 构造自定义偏好数据

```python
from datasets import Dataset

# 自定义偏好数据格式
raw_data = [
    {
        "prompt": "请用一句话解释什么是机器学习。",
        "chosen": "机器学习是一种让计算机通过数据和经验自动改进性能的技术，"
                  "而无需被显式编程告知每一步该怎么做。",
        "rejected": "机器学习就是机器在学习。"
    },
    {
        "prompt": "Python 中 list 和 tuple 的区别是什么？",
        "chosen": "list 是可变的（mutable），可以增删改元素；"
                  "tuple 是不可变的（immutable），创建后不能修改。"
                  "tuple 因为不可变所以可以作为字典的 key，且性能略优于 list。",
        "rejected": "一个用方括号一个用圆括号。"
    },
    {
        "prompt": "如何写出高质量的代码？",
        "chosen": "高质量代码应该具备以下特征：\n"
                  "1. 可读性强：命名清晰，结构规范\n"
                  "2. 可测试：函数职责单一，便于编写单元测试\n"
                  "3. 可维护：低耦合，高内聚\n"
                  "4. 有错误处理：预期并处理异常情况\n"
                  "5. 有文档：关键逻辑有注释和文档说明",
        "rejected": "多写就好了。"
    },
]

dataset = Dataset.from_list(raw_data)
dataset = dataset.train_test_split(test_size=0.1)
```

### 数据预处理

```python
def format_prompt(example):
    """将数据格式化为对话模板"""
    return {
        "prompt": f"<|user|>\n{example['prompt']}\n<|assistant|>\n",
        "chosen": example["chosen"],
        "rejected": example["rejected"],
    }

formatted_dataset = dataset.map(format_prompt)
```

## 步骤 2：加载基座模型

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig

# 选择基座模型（这里用小模型便于演示）
model_name = "Qwen/Qwen2.5-1.5B-Instruct"

# 加载 tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 加载模型
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# LoRA 配置（减少显存需求）
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    task_type="CAUSAL_LM",
)
```

## 步骤 3：配置 DPO 训练

```python
from trl import DPOConfig, DPOTrainer

# DPO 训练配置
training_args = DPOConfig(
    output_dir="./dpo-output",

    # 训练参数
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=5e-6,
    warmup_steps=100,

    # DPO 专属参数
    beta=0.1,                  # KL 惩罚系数（核心参数）
    loss_type="sigmoid",       # 损失类型：sigmoid / hinge / ipo

    # 序列长度
    max_length=1024,
    max_prompt_length=512,

    # 优化器
    optim="adamw_torch",
    lr_scheduler_type="cosine",

    # 日志
    logging_steps=10,
    save_steps=500,
    eval_strategy="steps",
    eval_steps=100,

    # 精度
    bf16=True,

    # 梯度检查点（节省显存）
    gradient_checkpointing=True,
)
```

### beta 参数调优指南

| 场景 | 推荐 beta | 原因 |
|------|----------|------|
| 偏好数据质量高、差异明确 | 0.05 - 0.1 | 可以更激进地对齐 |
| 偏好数据有噪声 | 0.2 - 0.5 | 保守一些，减少噪声影响 |
| 基座模型质量已经很好 | 0.1 - 0.3 | 避免过度修改 |
| 首次尝试 | 0.1 | 社区常用默认值 |

## 步骤 4：启动训练

```python
# 创建 DPO 训练器
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,       # 设为 None 时自动创建参考模型
    args=training_args,
    train_dataset=formatted_dataset["train"],
    eval_dataset=formatted_dataset["test"],
    tokenizer=tokenizer,
    peft_config=peft_config,
)

# 开始训练
dpo_trainer.train()

# 保存模型
dpo_trainer.save_model("./dpo-final")
tokenizer.save_pretrained("./dpo-final")
```

### 训练日志解读

```
Step 10:  loss=0.693  rewards/chosen=0.01  rewards/rejected=-0.02  rewards/margins=0.03
Step 100: loss=0.520  rewards/chosen=0.45  rewards/rejected=-0.38  rewards/margins=0.83
Step 500: loss=0.410  rewards/chosen=0.72  rewards/rejected=-0.65  rewards/margins=1.37
```

关注指标：

| 指标 | 含义 | 健康范围 |
|------|------|---------|
| loss | DPO 损失 | 持续下降，收敛于 0.3-0.5 |
| rewards/chosen | 好回答的隐式奖励 | 正值且逐渐增大 |
| rewards/rejected | 差回答的隐式奖励 | 负值且逐渐减小 |
| rewards/margins | 好与差的奖励差距 | 正值且逐渐增大 |

## 步骤 5：评估对齐效果

### 定性评估

```python
from transformers import pipeline

# 加载对齐后的模型
aligned_pipe = pipeline(
    "text-generation",
    model="./dpo-final",
    tokenizer=tokenizer,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# 测试问题
test_prompts = [
    "请解释什么是深度学习？",
    "如何提高代码质量？",
    "Python 有哪些常用的数据结构？",
]

for prompt in test_prompts:
    messages = [{"role": "user", "content": prompt}]
    result = aligned_pipe(messages, max_new_tokens=256, do_sample=True, temperature=0.7)
    print(f"问题: {prompt}")
    print(f"回答: {result[0]['generated_text'][-1]['content']}")
    print("-" * 50)
```

### 定量评估：胜率对比

```python
def compare_models(base_model, aligned_model, tokenizer, test_data, judge_model):
    """对比基座模型和对齐模型的回答质量"""
    results = {"aligned_wins": 0, "base_wins": 0, "ties": 0}

    for item in test_data:
        prompt = item["prompt"]

        base_response = base_model.generate(prompt)
        aligned_response = aligned_model.generate(prompt)

        # 用更强的模型（如 GPT-4）做裁判
        judgment = judge_model.compare(prompt, base_response, aligned_response)

        if judgment == "aligned":
            results["aligned_wins"] += 1
        elif judgment == "base":
            results["base_wins"] += 1
        else:
            results["ties"] += 1

    total = len(test_data)
    print(f"对齐模型胜率: {results['aligned_wins'] / total:.1%}")
    print(f"基座模型胜率: {results['base_wins'] / total:.1%}")
    print(f"平局: {results['ties'] / total:.1%}")

    return results
```

### 使用 MT-Bench 评估

```bash
# 克隆 FastChat 评估工具
git clone https://github.com/lm-sys/FastChat.git
cd FastChat

# 生成回答
python gen_model_answer.py --model-path ./dpo-final --model-id dpo-model

# 用 GPT-4 评分（需要 API key）
python gen_judgment.py --model-list dpo-model --judge-model gpt-4
```

## 常见问题

### 训练 loss 不下降

- 检查数据格式是否正确（prompt / chosen / rejected）
- 降低学习率（尝试 1e-6）
- 检查 chosen 和 rejected 是否有明确的质量差异

### 显存不足

```python
# 方案 1：使用 4-bit 量化
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=bnb_config)

# 方案 2：减小 batch size + 增大梯度累积
# per_device_train_batch_size=1, gradient_accumulation_steps=8

# 方案 3：减小 max_length
# max_length=512, max_prompt_length=256
```

### 对齐过度（模型变得过于保守）

- 增大 beta 值（如 0.2 -> 0.5）
- 减少训练轮数
- 检查偏好数据是否过于偏向拒绝

## 参考资料

- [TRL 官方文档 - DPO](https://huggingface.co/docs/trl/dpo_trainer)
- [DPO 论文](https://arxiv.org/abs/2305.18290)
- [Hugging Face 对齐手册](https://github.com/huggingface/alignment-handbook)
- [RLHF 原理详解](../theory/01-RLHF原理详解.md)
- [DPO 原理详解](../theory/02-DPO原理详解.md)
