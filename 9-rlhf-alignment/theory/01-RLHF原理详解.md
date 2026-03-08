# RLHF 原理详解

## 概述

RLHF（Reinforcement Learning from Human Feedback，基于人类反馈的强化学习）是将预训练语言模型对齐到人类偏好的核心技术。本文详细讲解三个阶段的原理。

## 全景图

```
预训练模型 (Base Model)
    │
    ▼
┌─────────────────────┐
│  阶段 1: SFT         │  用标注数据微调，教模型"回答问题"
│  输入: 指令-回答对    │
│  输出: SFT 模型       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  阶段 2: 奖励模型     │  学习人类偏好，给回答打分
│  输入: 偏好排序数据   │
│  输出: Reward Model   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  阶段 3: PPO 优化     │  用 RL 优化模型，生成高分回答
│  输入: SFT模型 + RM   │
│  输出: 对齐后的模型    │
└─────────────────────┘
```

## 阶段 1：SFT（Supervised Fine-Tuning）

### 目标

将预训练模型从"文本补全器"变成"指令跟随者"。

### 数据格式

```python
# 典型的 SFT 训练数据
sft_examples = [
    {
        "messages": [
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "什么是梯度下降？"},
            {"role": "assistant", "content": "梯度下降是一种优化算法..."}
        ]
    }
]
```

### 训练过程

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")

trainer = SFTTrainer(
    model=model,
    train_dataset=sft_dataset,
    args=TrainingArguments(
        output_dir="./sft-output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-5,
    ),
)
trainer.train()
```

### 关键点

- SFT 数据质量比数量更重要（LIMA 论文用 1000 条数据达到很好的效果）
- SFT 模型已经能回答问题，但回答质量参差不齐
- SFT 是后续 RM 和 PPO 的基础

## 阶段 2：奖励模型（Reward Model）训练

### 目标

训练一个模型，对回答质量打分，模拟人类的偏好判断。

### 偏好数据格式

```python
# 人类标注的偏好数据
preference_data = {
    "prompt": "如何提高代码质量？",
    "chosen": "提高代码质量可以从以下几个方面入手：\n1. 代码审查...\n2. 单元测试...\n3. 重构...",
    "rejected": "写好代码就行。"
}
# 标注员认为 chosen 比 rejected 更好
```

### 奖励模型架构

奖励模型基于 SFT 模型改造：去掉语言模型头，加上一个标量输出头。

```python
from transformers import AutoModelForSequenceClassification

# 奖励模型 = 预训练模型 + 标量输出头
reward_model = AutoModelForSequenceClassification.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    num_labels=1  # 输出一个标量分数
)
```

### 损失函数

奖励模型使用 **Bradley-Terry 排序损失**：

```
Loss = -log(sigmoid(r(chosen) - r(rejected)))
```

直觉解释：
- 当 r(chosen) >> r(rejected) 时，loss 接近 0（模型判断正确）
- 当 r(chosen) << r(rejected) 时，loss 很大（模型判断错误）
- 目标：让好回答的分数始终高于差回答

### 训练代码

```python
from trl import RewardTrainer, RewardConfig

reward_trainer = RewardTrainer(
    model=reward_model,
    tokenizer=tokenizer,
    train_dataset=preference_dataset,
    args=RewardConfig(
        output_dir="./reward-model",
        num_train_epochs=1,
        per_device_train_batch_size=8,
        learning_rate=1e-5,
    ),
)
reward_trainer.train()
```

## 阶段 3：PPO（Proximal Policy Optimization）

### 目标

用强化学习优化 SFT 模型，使其生成的回答获得更高的奖励分数。

### PPO 在 RLHF 中的角色

```
               ┌──────────────┐
  prompt ────→ │  策略模型      │ ────→ 生成回答
               │  (SFT 模型)   │
               └──────┬───────┘
                      │ 回答
                      ▼
               ┌──────────────┐
               │  奖励模型      │ ────→ 奖励分数 r
               └──────────────┘
                      │
                      ▼
               ┌──────────────┐
               │  PPO 更新      │ ────→ 更新策略模型参数
               │  目标: 最大化   │
               │  r - β·KL     │
               └──────────────┘
```

### PPO 优化目标

```
目标函数 = E[reward(response)] - β * KL(π_new || π_sft)

其中：
- reward(response): 奖励模型对生成回答的打分
- KL(π_new || π_sft): 新策略与 SFT 模型的 KL 散度
- β: KL 惩罚系数（控制偏离程度）
```

**为什么需要 KL 惩罚？**

| 没有 KL 惩罚 | 有 KL 惩罚 |
|:---:|:---:|
| 模型学会"讨好"奖励模型 | 模型在有用和自然之间平衡 |
| 生成重复、夸张的回答 | 保持语言的流畅性 |
| 奖励 hacking | 稳定训练 |

### PPO 训练代码

```python
from trl import PPOTrainer, PPOConfig, AutoModelForCausalLMWithValueHead

# PPO 需要 4 个模型（内存需求大）
# 1. 策略模型（要优化的）
# 2. 参考模型（SFT 模型副本，计算 KL 用）
# 3. 奖励模型
# 4. 价值头（Value Head，辅助 PPO 训练）

model = AutoModelForCausalLMWithValueHead.from_pretrained("./sft-output")

ppo_config = PPOConfig(
    batch_size=16,
    learning_rate=1e-5,
    ppo_epochs=4,
    kl_penalty="kl",
    init_kl_coef=0.2,
)

ppo_trainer = PPOTrainer(
    config=ppo_config,
    model=model,
    ref_model=ref_model,
    tokenizer=tokenizer,
)

# 训练循环
for batch in dataloader:
    query_tensors = batch["input_ids"]

    # 1. 生成回答
    response_tensors = ppo_trainer.generate(query_tensors)

    # 2. 计算奖励
    rewards = reward_model(query_tensors, response_tensors)

    # 3. PPO 更新
    stats = ppo_trainer.step(query_tensors, response_tensors, rewards)
```

## RLHF 的问题和挑战

### 1. 训练不稳定

PPO 是强化学习算法，本身就比监督学习更难训练：
- 超参数敏感（KL 系数、学习率、batch size）
- 奖励 hacking（模型找到奖励模型的漏洞）
- 训练过程中性能可能突然崩溃

### 2. 资源需求高

RLHF 训练需要同时加载 4 个模型：

| 模型 | 用途 | 是否需要梯度 |
|------|------|:---:|
| 策略模型 | 生成回答 | 是 |
| 参考模型 | 计算 KL 散度 | 否 |
| 奖励模型 | 打分 | 否 |
| 价值模型 | PPO 辅助 | 是 |

对于 7B 参数模型，RLHF 训练至少需要 4x A100 (80GB)。

### 3. 奖励模型质量瓶颈

- 奖励模型的天花板决定了对齐效果的天花板
- 人类标注存在噪声和不一致性
- 分布外泛化能力有限

### 4. 人类标注成本

- 需要大量高质量的人类标注数据
- 标注员之间的偏好不一致
- 持续更新标注数据成本高

## 替代方案

正因为 RLHF 有以上挑战，研究者提出了更简洁的替代方案：

- **DPO**：去掉奖励模型，直接从偏好数据优化 -> [DPO 原理详解](02-DPO原理详解.md)
- **ORPO**：将对齐融入 SFT，一步到位
- **KTO**：只需要"好/坏"标签，不需要配对数据

## 下一步

- 了解更简洁的 DPO 方法：[DPO 原理详解](02-DPO原理详解.md)
- 动手实践 DPO 训练：[DPO 微调实战](../hands-on/01-DPO微调实战.md)
