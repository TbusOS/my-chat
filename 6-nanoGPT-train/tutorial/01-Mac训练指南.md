# Mac 上用 nanoGPT 从零训练 GPT 模型

## 本章目标

在 macOS 上从零训练一个小型 GPT 模型：
1. 环境搭建（Python + PyTorch MPS）
2. 数据准备（Shakespeare 数据集）
3. 训练模型（MPS 加速 / CPU 回退）
4. 生成文本

---

## 1. 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 芯片 | Intel Mac / M1 | M1 Pro / M2 / M3 以上 |
| 内存 | 8GB | 16GB+ |
| 存储 | 2GB 可用 | 5GB+ |
| macOS | 12.3+ (MPS 需要) | 14.0+ |

> Apple Silicon (M1/M2/M3/M4) 支持 MPS (Metal Performance Shaders) 加速，训练速度比 CPU 快 5-10 倍。

---

## 2. 环境搭建

### 2.1 安装 Python

```bash
# 方法1：Homebrew 安装（推荐）
brew install python@3.11

# 方法2：从官网下载
# https://www.python.org/downloads/macos/

# 验证
python3 --version
# Python 3.11.x
```

### 2.2 创建虚拟环境

```bash
# 创建项目目录
mkdir ~/nanoGPT-train
cd ~/nanoGPT-train

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 确认 pip
pip install --upgrade pip
```

### 2.3 安装 PyTorch（MPS 支持）

```bash
# Apple Silicon Mac（M1/M2/M3/M4）- MPS 加速
pip install torch torchvision torchaudio

# 验证 MPS 是否可用
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'MPS available: {torch.backends.mps.is_available()}')
print(f'MPS built: {torch.backends.mps.is_built()}')
"
# 预期输出:
# PyTorch: 2.x.x
# MPS available: True
# MPS built: True
```

> Intel Mac 无 MPS 支持，会自动回退到 CPU 训练（速度较慢但可用）。

### 2.4 克隆 nanoGPT

```bash
cd ~/nanoGPT-train
git clone https://github.com/karpathy/nanoGPT.git
cd nanoGPT

# 安装依赖
pip install numpy tiktoken datasets transformers
```

---

## 3. 数据准备

### 3.1 Shakespeare 数据集（推荐入门）

```bash
# 下载并预处理 Shakespeare 数据集
cd ~/nanoGPT-train/nanoGPT
python data/shakespeare_char/prepare.py
```

这会生成：
- `data/shakespeare_char/train.bin` - 训练集（~1MB）
- `data/shakespeare_char/val.bin` - 验证集

### 3.2 检查数据

```python
#!/usr/bin/env python3
"""检查准备好的数据"""

import numpy as np

# 加载训练数据
train_data = np.memmap('data/shakespeare_char/train.bin', dtype=np.uint16, mode='r')
val_data = np.memmap('data/shakespeare_char/val.bin', dtype=np.uint16, mode='r')

print(f"训练集 tokens: {len(train_data):,}")
print(f"验证集 tokens: {len(val_data):,}")
print(f"词表大小: {int(max(train_data)) + 1}")
print(f"前 100 个 token: {train_data[:100]}")
```

---

## 4. 配置训练参数

### 4.1 Mac 专用配置

创建训练配置文件：

```bash
cat > ~/nanoGPT-train/nanoGPT/config/train_shakespeare_mac.py << 'EOF'
# Mac 上训练 Shakespeare 的配置
# 针对 Apple Silicon MPS 优化

# 数据
dataset = 'shakespeare_char'
gradient_accumulation_steps = 1
batch_size = 64
block_size = 256  # 上下文长度

# 小型模型（适合 Mac）
n_layer = 6
n_head = 6
n_embd = 384
dropout = 0.2

# 训练参数
learning_rate = 1e-3
max_iters = 5000
lr_decay_iters = 5000
min_lr = 1e-4
beta2 = 0.99

# 评估
eval_interval = 500
eval_iters = 200
log_interval = 100

# 设备
# MPS 自动检测：Apple Silicon 用 mps，Intel Mac 用 cpu
device = 'mps'  # 改为 'cpu' 如果 MPS 有问题
compile = False  # Mac 上不支持 torch.compile

# 保存
out_dir = 'out-shakespeare-mac'
always_save_checkpoint = True

# 其他
wandb_log = False
EOF
```

### 4.2 参数说明

| 参数 | 值 | 说明 |
|------|------|------|
| `n_layer` | 6 | Transformer 层数 |
| `n_head` | 6 | 注意力头数 |
| `n_embd` | 384 | 嵌入维度 |
| `block_size` | 256 | 上下文窗口长度 |
| `batch_size` | 64 | 批次大小 |
| `max_iters` | 5000 | 训练步数 |
| `device` | mps | Apple Silicon 加速 |
| `compile` | False | Mac 不支持 torch.compile |

> 模型参数量约 **10M**（1000万），训练约 10-30 分钟（取决于芯片）。

---

## 5. 开始训练

### 5.1 启动训练

```bash
cd ~/nanoGPT-train/nanoGPT

# Apple Silicon Mac（MPS 加速）
python train.py config/train_shakespeare_mac.py

# 如果 MPS 出现问题，回退到 CPU
python train.py config/train_shakespeare_mac.py --device=cpu
```

### 5.2 训练输出示例

```
step 0: train loss 4.2241, val loss 4.2306
step 500: train loss 1.8215, val loss 1.9842
step 1000: train loss 1.5632, val loss 1.7421
step 1500: train loss 1.4218, val loss 1.6335
step 2000: train loss 1.3245, val loss 1.5618
...
step 5000: train loss 0.9876, val loss 1.4532
```

### 5.3 训练时间参考

| 芯片 | 5000 步耗时 | 备注 |
|------|------------|------|
| M1 | ~20 分钟 | MPS 加速 |
| M1 Pro/Max | ~12 分钟 | MPS 加速 |
| M2/M3 | ~10 分钟 | MPS 加速 |
| M3 Pro/Max | ~6 分钟 | MPS 加速 |
| Intel Mac | ~60 分钟 | 仅 CPU |

---

## 6. 生成文本

### 6.1 使用训练好的模型生成

```bash
# 生成 Shakespeare 风格文本
python sample.py --out_dir=out-shakespeare-mac --device=mps
```

### 6.2 自定义生成

```bash
# 指定起始文本
python sample.py \
    --out_dir=out-shakespeare-mac \
    --device=mps \
    --start="ROMEO:" \
    --num_samples=3 \
    --max_new_tokens=500 \
    --temperature=0.8
```

### 6.3 生成效果示例

训练 5000 步后的典型输出：

```
ROMEO:
What say'st thou, gentle cousin? is the day
So full of shapes is fancy's images,
And in my heart I do purpose to wed
The fairest lady in the world...
```

> 虽然不完美，但已能生成符合 Shakespeare 风格的文本。

---

## 7. 进阶：调整模型大小

### 7.1 更小的模型（快速实验）

```python
# config/train_shakespeare_tiny.py
n_layer = 4
n_head = 4
n_embd = 128
block_size = 128
batch_size = 32
max_iters = 2000
device = 'mps'
compile = False
dataset = 'shakespeare_char'
out_dir = 'out-shakespeare-tiny'
```

### 7.2 更大的模型（更好效果）

```python
# config/train_shakespeare_large.py
# 需要 16GB+ 内存
n_layer = 8
n_head = 8
n_embd = 512
block_size = 512
batch_size = 32
max_iters = 10000
device = 'mps'
compile = False
dataset = 'shakespeare_char'
out_dir = 'out-shakespeare-large'
```

---

## 8. 使用自定义数据训练

### 8.1 准备自己的文本

```bash
# 创建数据目录
mkdir -p data/my_data

# 将你的文本放入 input.txt
# 比如：中文小说、代码、聊天记录等
cp your_text.txt data/my_data/input.txt
```

### 8.2 创建数据准备脚本

```python
#!/usr/bin/env python3
"""
data/my_data/prepare.py
准备自定义文本数据
"""

import os
import numpy as np

# 读取文本
input_file = os.path.join(os.path.dirname(__file__), 'input.txt')
with open(input_file, 'r', encoding='utf-8') as f:
    data = f.read()

print(f"总字符数: {len(data):,}")

# 字符级分词
chars = sorted(list(set(data)))
vocab_size = len(chars)
print(f"词表大小: {vocab_size}")

stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for i, ch in enumerate(chars)}

def encode(s):
    return [stoi[c] for c in s]

def decode(l):
    return ''.join([itos[i] for i in l])

# 分割训练集和验证集
n = len(data)
train_data = data[:int(n * 0.9)]
val_data = data[int(n * 0.9):]

# 编码并保存
train_ids = encode(train_data)
val_ids = encode(val_data)

print(f"训练集 tokens: {len(train_ids):,}")
print(f"验证集 tokens: {len(val_ids):,}")

train_ids = np.array(train_ids, dtype=np.uint16)
val_ids = np.array(val_ids, dtype=np.uint16)

train_ids.tofile(os.path.join(os.path.dirname(__file__), 'train.bin'))
val_ids.tofile(os.path.join(os.path.dirname(__file__), 'val.bin'))

# 保存词表信息
meta = {
    'vocab_size': vocab_size,
    'itos': itos,
    'stoi': stoi,
}

import pickle
with open(os.path.join(os.path.dirname(__file__), 'meta.pkl'), 'wb') as f:
    pickle.dump(meta, f)

print("数据准备完成")
```

### 8.3 训练自定义数据

```bash
# 准备数据
python data/my_data/prepare.py

# 训练
python train.py \
    --dataset=my_data \
    --device=mps \
    --compile=False \
    --n_layer=6 \
    --n_head=6 \
    --n_embd=384 \
    --block_size=256 \
    --batch_size=64 \
    --max_iters=5000 \
    --out_dir=out-my-data
```

---

## 9. 常见问题

### MPS 报错？

```bash
# 回退到 CPU
python train.py config/train_shakespeare_mac.py --device=cpu

# 或设置环境变量禁用 MPS
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
```

### 内存不足？

- 减小 `batch_size`（如 32 → 16）
- 减小 `block_size`（如 256 → 128）
- 减小模型（`n_layer`, `n_head`, `n_embd`）

### 训练 loss 不下降？

- 检查数据是否正确准备（`train.bin` 非空）
- 尝试增大 `learning_rate`（如 1e-3 → 3e-3）
- 检查数据量是否太少（建议 > 100KB）

### torch.compile 报错？

Mac 上不支持 `torch.compile`，确保配置中 `compile = False`。

---

## 10. 本章小结

- [x] 在 Mac 上搭建 nanoGPT 环境
- [x] 使用 MPS 加速训练
- [x] 训练 Shakespeare 字符级 GPT
- [x] 生成文本
- [x] 使用自定义数据训练
