# 训练你的第一个 GPT

## 本章目标

动手训练一个字符级 GPT 模型，完整走一遍流程：
1. 下载代码
2. 准备数据
3. 训练模型
4. 生成文本
5. 保存和加载模型

---

## 1. 一键跑通

```bash
# 5 分钟跑通全流程

# 1. 克隆
git clone https://github.com/karpathy/nanoGPT.git
cd nanoGPT

# 2. 安装依赖
pip install torch numpy tiktoken

# 3. 准备数据
python data/shakespeare_char/prepare.py

# 4. 训练（Mac 用 mps，Linux 用 cuda，无 GPU 用 cpu）
python train.py \
    --dataset=shakespeare_char \
    --n_layer=6 --n_head=6 --n_embd=384 \
    --block_size=256 --batch_size=64 \
    --max_iters=5000 \
    --device=mps \
    --compile=False \
    --out_dir=out-shakespeare

# 5. 生成
python sample.py --out_dir=out-shakespeare --device=mps
```

---

## 2. 理解训练输出

```
step 0: train loss 4.2241, val loss 4.2306
```

| 指标 | 含义 | 理想趋势 |
|------|------|----------|
| step | 当前训练步数 | 递增 |
| train loss | 训练集损失 | 持续下降 |
| val loss | 验证集损失 | 下降后趋于平稳 |

- **train loss 下降，val loss 也下降** → 正常训练
- **train loss 下降，val loss 上升** → 过拟合，需早停或增加 dropout
- **两个 loss 都不动** → 学习率太小或数据有问题

---

## 3. 观察模型从无到有学习

### Step 0（随机输出）
```
xK&^jY2!pQm@...
```

### Step 1000（开始学到空格和换行）
```
the and is for to of
he what not you
```

### Step 3000（学到基本句型）
```
ROMEO: I am not so
What is the matter with thee?
```

### Step 5000（接近 Shakespeare 风格）
```
ROMEO:
What say'st thou, gentle cousin? is the day
So full of shapes is fancy's images...
```

---

## 4. 实验：改变模型大小

### 实验 1：超小模型

```bash
python train.py \
    --dataset=shakespeare_char \
    --n_layer=2 --n_head=2 --n_embd=64 \
    --block_size=64 --batch_size=32 \
    --max_iters=3000 \
    --device=mps --compile=False \
    --out_dir=out-tiny
```

**结果**：模型太小，只能学到简单的字符模式。

### 实验 2：中型模型

```bash
python train.py \
    --dataset=shakespeare_char \
    --n_layer=8 --n_head=8 --n_embd=512 \
    --block_size=512 --batch_size=32 \
    --max_iters=10000 \
    --device=mps --compile=False \
    --out_dir=out-medium
```

**结果**：生成质量明显提升，更连贯的段落。

### 实验 3：对比总结

| 配置 | 参数量 | val loss | 生成质量 |
|------|--------|----------|---------|
| tiny (2L/2H/64E) | ~0.1M | ~2.0 | 模糊的单词 |
| small (6L/6H/384E) | ~10M | ~1.4 | 基本句型正确 |
| medium (8L/8H/512E) | ~30M | ~1.2 | 连贯段落 |

---

## 5. 实验：改变温度

```bash
# 低温度 = 更保守、更重复
python sample.py --out_dir=out-shakespeare --temperature=0.5

# 中温度 = 平衡
python sample.py --out_dir=out-shakespeare --temperature=0.8

# 高温度 = 更创意、更随机
python sample.py --out_dir=out-shakespeare --temperature=1.2
```

| 温度 | 效果 |
|------|------|
| 0.1 - 0.5 | 保守，重复高频词 |
| 0.7 - 0.9 | 平衡，推荐 |
| 1.0 - 1.5 | 创意，偶有语法错误 |
| > 1.5 | 混乱，不可读 |

---

## 6. 保存和加载模型

### 训练自动保存

训练完成后模型保存在 `out_dir/ckpt.pt`，包含：
- 模型权重
- 优化器状态
- 训练配置
- 当前步数

### 手动加载推理

```python
import torch
from model import GPT, GPTConfig

# 加载 checkpoint
ckpt = torch.load('out-shakespeare/ckpt.pt', map_location='cpu')

# 重建模型
config = GPTConfig(**ckpt['model_args'])
model = GPT(config)
model.load_state_dict(ckpt['model'])
model.eval()

print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")
```

---

## 7. 本章小结

- [x] 5 分钟跑通 nanoGPT 全流程
- [x] 理解训练指标（loss 曲线）
- [x] 观察模型学习过程
- [x] 实验不同模型大小和温度
- [x] 保存和加载模型
