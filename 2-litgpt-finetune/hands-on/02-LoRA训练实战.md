# LoRA 训练实战

## 本章目标

手把手完成 LoRA 训练：
1. 配置参数
2. 开始训练
3. 监控过程
4. 常见问题解决

---

## 1.1 训练配置

### 1.1.1 配置文件

```yaml
# config.yaml
model:
  name: microsoft/phi-2
  tokenizer_dir: microsoft/phi-2

data:
  alpaca:
    path: data/train.json
  max_seq_length: 512

lora:
  r: 16           # LoRA 秩
  alpha: 32       # 缩放因子
  dropout: 0.05   # Dropout
  query_key: true # 在 Q、K 上应用
  value: true     # 在 V 上应用
  projection: true
  mlp: true

train:
  epochs: 3
  batch_size: 4
  gradient_accumulation_steps: 4
  lr: 3e-4
  warmup_steps: 100
  save_interval: 500
  log_interval: 10

out_dir: out/lora-phi2
```

---

## 1.2 开始训练

### 1.2.1 单 GPU 训练

```bash
# 激活环境
source venv/bin/activate

# 开始训练
litgpt finetune lora \
  --config config.yaml
```

### 1.2.2 多 GPU 训练

```bash
# 4 GPU 并行
torchrun --nproc_per_node=4 litgpt/finetune/lora.py \
  --config config.yaml
```

### 1.2.3 Apple Silicon 训练

```bash
# 使用 MLX 后端
litgpt finetune lora \
  --model microsoft/phi-2 \
  --data alpaca \
  --backend mlx
```

---

## 1.3 训练过程

### 1.3.1 预期输出

```
Training...
epoch: 1/3 | step: 100/1500 | loss: 1.234 | lr: 2.5e-4 | time: 45s
epoch: 1/3 | step: 200/1500 | loss: 0.876 | lr: 2.3e-4 | time: 44s
epoch: 1/3 | step: 300/1500 | loss: 0.654 | lr: 2.1e-4 | time: 46s
...
Saving checkpoint to out/lora-phi2/checkpoint-1000
...
Done!
```

### 1.3.2 监控指标

| 指标 | 说明 |
|------|------|
| loss | 训练损失，越低越好 |
| lr | 学习率 |
| time | 每步耗时 |

---

## 1.4 常见问题

### 1.4.1 显存不足

```bash
# 方案 1: 减少批次
--train.batch_size 1

# 方案 2: 增加梯度累积
--train.gradient_accumulation_steps 16

# 方案 3: 使用 QLoRA
--quantize qlora
```

### 1.4.2 训练不稳定

```bash
# 降低学习率
--train.lr 1e-5

# 增加 warmup
--train.warmup_steps 500
```

### 1.4.3 效果不好

```bash
# 增加训练数据
# 增加训练轮数
--train.num_epochs 5

# 调整 LoRA 参数
--lora.r 32
--lora.alpha 64
```

---

## 1.5 训练后模型

### 1.5.1 输出目录

```
out/lora-phi2/
├── checkpoint-1000/
│   ├── lit_model.pth
│   ├── model_config.json
│   └── lora_weights.pt
├── checkpoint-2000/
├── final/
│   ├── lit_model.pth
│   ├── model_config.json
│   └── lora_weights.pt
└── logs/
```

### 1.5.2 使用微调后模型

```python
from litgpt import LLM

llm = LLM.load(
    name="microsoft/phi-2",
    finetune_path="out/lora-phi2/final"
)

response = llm.chat(
    messages=[{"role": "user", "content": "你的问题"}]
)
print(response)
```

---

## 1.6 本章小结

- ✅ 配置文件编写
- ✅ 开始训练
- ✅ 监控过程
- ✅ 常见问题解决
- ✅ 使用微调后模型
