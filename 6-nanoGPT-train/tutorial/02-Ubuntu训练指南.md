# Ubuntu 上用 nanoGPT 从零训练 GPT 模型

## 本章目标

在 Ubuntu 上从零训练一个小型 GPT 模型：
1. 环境搭建（Python + PyTorch CUDA）
2. 数据准备（Shakespeare + OpenWebText）
3. 训练模型（CUDA 加速）
4. 生成文本
5. 进阶：训练更大的模型

---

## 1. 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|----------|----------|
| GPU | GTX 1060 6GB | RTX 3090 / 4090 |
| 内存 | 8GB | 32GB+ |
| 存储 | 5GB | 50GB+（OpenWebText 需要） |
| Ubuntu | 20.04+ | 22.04 / 24.04 |
| CUDA | 11.8+ | 12.x |

> 无 NVIDIA GPU 也可用 CPU 训练，但速度慢 10-50 倍。

---

## 2. 环境搭建

### 2.1 安装 NVIDIA 驱动和 CUDA

```bash
# 检查 GPU
nvidia-smi

# 如果未安装驱动
sudo apt update
sudo apt install -y nvidia-driver-535

# 重启
sudo reboot

# 验证
nvidia-smi
# 应显示 GPU 型号、驱动版本、CUDA 版本
```

### 2.2 安装 CUDA Toolkit（可选，PyTorch 自带）

```bash
# PyTorch 自带 CUDA runtime，通常不需要单独安装
# 如果需要 nvcc 编译器：
sudo apt install -y nvidia-cuda-toolkit

# 验证
nvcc --version
```

### 2.3 安装 Python 和虚拟环境

```bash
# 安装 Python
sudo apt install -y python3.11 python3.11-venv python3-pip

# 创建项目目录
mkdir ~/nanoGPT-train
cd ~/nanoGPT-train

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
```

### 2.4 安装 PyTorch（CUDA 版本）

```bash
# CUDA 12.x（推荐）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证 CUDA
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')
"
```

### 2.5 克隆 nanoGPT

```bash
cd ~/nanoGPT-train
git clone https://github.com/karpathy/nanoGPT.git
cd nanoGPT

# 安装依赖
pip install numpy tiktoken datasets transformers
```

---

## 3. 数据准备

### 3.1 Shakespeare 数据集（快速入门）

```bash
python data/shakespeare_char/prepare.py
```

### 3.2 OpenWebText 数据集（更大规模训练）

```bash
# 下载并预处理 OpenWebText（约 12GB，需要较长时间）
python data/openwebtext/prepare.py

# 这会下载完整的 OpenWebText 数据集
# 生成 train.bin (~17GB) 和 val.bin (~8MB)
```

> OpenWebText 下载和处理需要 1-3 小时，取决于网络速度。

---

## 4. 训练配置

### 4.1 Shakespeare 训练（入门）

```bash
cat > ~/nanoGPT-train/nanoGPT/config/train_shakespeare_ubuntu.py << 'EOF'
# Ubuntu GPU 训练 Shakespeare 配置

# 数据
dataset = 'shakespeare_char'
gradient_accumulation_steps = 1
batch_size = 64
block_size = 256

# 模型（小型）
n_layer = 6
n_head = 6
n_embd = 384
dropout = 0.2

# 训练
learning_rate = 1e-3
max_iters = 5000
lr_decay_iters = 5000
min_lr = 1e-4
beta2 = 0.99

# 评估
eval_interval = 500
eval_iters = 200
log_interval = 100

# GPU 设置
device = 'cuda'
compile = True  # Linux 支持 torch.compile，加速约 2x
dtype = 'bfloat16'  # Ampere+ GPU 用 bfloat16

# 保存
out_dir = 'out-shakespeare-ubuntu'
always_save_checkpoint = True

wandb_log = False
EOF
```

### 4.2 OpenWebText 训练（进阶）

```bash
cat > ~/nanoGPT-train/nanoGPT/config/train_gpt2_ubuntu.py << 'EOF'
# Ubuntu GPU 训练 GPT-2 级别模型
# 需要 RTX 3090+ (24GB VRAM)

# 数据
dataset = 'openwebtext'
gradient_accumulation_steps = 40  # 模拟大 batch
batch_size = 12
block_size = 1024

# GPT-2 Small 架构（124M 参数）
n_layer = 12
n_head = 12
n_embd = 768
dropout = 0.0

# 训练
learning_rate = 6e-4
max_iters = 600000
lr_decay_iters = 600000
min_lr = 6e-5
warmup_iters = 2000
beta2 = 0.95

# 评估
eval_interval = 2000
eval_iters = 200
log_interval = 100

# GPU 设置
device = 'cuda'
compile = True
dtype = 'bfloat16'

# 保存
out_dir = 'out-gpt2-ubuntu'
always_save_checkpoint = True

wandb_log = False
EOF
```

### 4.3 参数对比

| 参数 | Shakespeare (入门) | GPT-2 (进阶) |
|------|-------------------|---------------|
| 参数量 | ~10M | ~124M |
| 数据集 | 1MB | 17GB |
| GPU 显存 | 4GB+ | 24GB+ |
| 训练时间 | ~5 分钟 | ~3-4 天 |
| `compile` | True | True |
| `dtype` | bfloat16 | bfloat16 |

---

## 5. 开始训练

### 5.1 单 GPU 训练

```bash
cd ~/nanoGPT-train/nanoGPT

# Shakespeare（入门）
python train.py config/train_shakespeare_ubuntu.py

# OpenWebText（进阶，需要大显存 GPU）
python train.py config/train_gpt2_ubuntu.py
```

### 5.2 多 GPU 训练（DDP）

```bash
# 2 GPU 训练
torchrun --standalone --nproc_per_node=2 train.py config/train_gpt2_ubuntu.py

# 4 GPU 训练
torchrun --standalone --nproc_per_node=4 train.py config/train_gpt2_ubuntu.py

# 8 GPU 训练
torchrun --standalone --nproc_per_node=8 train.py config/train_gpt2_ubuntu.py
```

### 5.3 后台训练（推荐）

```bash
# 使用 tmux 在后台训练
tmux new -s train

# 在 tmux 中运行
python train.py config/train_gpt2_ubuntu.py

# Ctrl+B, D 退出 tmux（训练继续）
# tmux attach -t train  回到训练窗口
```

### 5.4 训练输出示例

```
number of parameters: 10.65M
num decayed parameter tensors: 26, with 10,740,096 total parameters
num non-decayed parameter tensors: 13, with 4,992 total parameters
using fused AdamW: True
compiling the model... (takes a ~minute)
step 0: train loss 4.2241, val loss 4.2306
step 500: train loss 1.8215, val loss 1.9842
step 1000: train loss 1.5632, val loss 1.7421
step 2000: train loss 1.3245, val loss 1.5618
step 5000: train loss 0.9876, val loss 1.4532
```

### 5.5 训练时间参考（Shakespeare 5000 步）

| GPU | 耗时 | 备注 |
|-----|------|------|
| RTX 4090 | ~2 分钟 | compile=True |
| RTX 3090 | ~3 分钟 | compile=True |
| RTX 3060 | ~8 分钟 | compile=True |
| GTX 1080 Ti | ~12 分钟 | compile=False |
| CPU (i7) | ~90 分钟 | 无 GPU 回退 |

---

## 6. 生成文本

```bash
# 生成文本
python sample.py --out_dir=out-shakespeare-ubuntu --device=cuda

# 自定义生成
python sample.py \
    --out_dir=out-shakespeare-ubuntu \
    --device=cuda \
    --start="KING HENRY:" \
    --num_samples=5 \
    --max_new_tokens=500 \
    --temperature=0.8 \
    --top_k=200
```

---

## 7. 进阶：从 checkpoint 继续训练

```bash
# 从上次中断的地方继续
python train.py config/train_gpt2_ubuntu.py \
    --init_from=resume \
    --out_dir=out-gpt2-ubuntu
```

---

## 8. 进阶：微调 GPT-2 预训练模型

```bash
# 下载 GPT-2 权重并在 Shakespeare 上微调
python train.py \
    --init_from=gpt2 \
    --dataset=shakespeare_char \
    --device=cuda \
    --compile=True \
    --dtype=bfloat16 \
    --n_layer=12 \
    --n_head=12 \
    --n_embd=768 \
    --max_iters=2000 \
    --learning_rate=3e-5 \
    --out_dir=out-shakespeare-finetune
```

---

## 9. 使用自定义数据训练

### 9.1 字符级（适合中文）

```python
#!/usr/bin/env python3
"""
data/my_data/prepare.py
准备自定义文本数据（字符级分词）
"""

import os
import numpy as np

input_file = os.path.join(os.path.dirname(__file__), 'input.txt')
with open(input_file, 'r', encoding='utf-8') as f:
    data = f.read()

print(f"总字符数: {len(data):,}")

chars = sorted(list(set(data)))
vocab_size = len(chars)
print(f"词表大小: {vocab_size}")

stoi = {ch: i for i, ch in enumerate(chars)}

def encode(s):
    return [stoi[c] for c in s]

n = len(data)
train_data = data[:int(n * 0.9)]
val_data = data[int(n * 0.9):]

train_ids = np.array(encode(train_data), dtype=np.uint16)
val_ids = np.array(encode(val_data), dtype=np.uint16)

train_ids.tofile(os.path.join(os.path.dirname(__file__), 'train.bin'))
val_ids.tofile(os.path.join(os.path.dirname(__file__), 'val.bin'))

import pickle
meta = {'vocab_size': vocab_size, 'stoi': stoi, 'itos': {i: ch for ch, i in stoi.items()}}
with open(os.path.join(os.path.dirname(__file__), 'meta.pkl'), 'wb') as f:
    pickle.dump(meta, f)

print(f"训练集: {len(train_ids):,} tokens")
print(f"验证集: {len(val_ids):,} tokens")
```

### 9.2 BPE 分词（适合英文）

```python
#!/usr/bin/env python3
"""
data/my_data_bpe/prepare.py
使用 GPT-2 的 BPE 分词器
"""

import os
import numpy as np
import tiktoken

input_file = os.path.join(os.path.dirname(__file__), 'input.txt')
with open(input_file, 'r', encoding='utf-8') as f:
    data = f.read()

enc = tiktoken.get_encoding("gpt2")

n = len(data)
train_data = data[:int(n * 0.9)]
val_data = data[int(n * 0.9):]

train_ids = enc.encode_ordinary(train_data)
val_ids = enc.encode_ordinary(val_data)

print(f"训练集: {len(train_ids):,} tokens")
print(f"验证集: {len(val_ids):,} tokens")

train_ids = np.array(train_ids, dtype=np.uint16)
val_ids = np.array(val_ids, dtype=np.uint16)

train_ids.tofile(os.path.join(os.path.dirname(__file__), 'train.bin'))
val_ids.tofile(os.path.join(os.path.dirname(__file__), 'val.bin'))
```

### 9.3 训练自定义数据

```bash
# 准备数据
mkdir -p data/my_data
cp your_text.txt data/my_data/input.txt
python data/my_data/prepare.py

# 训练
python train.py \
    --dataset=my_data \
    --device=cuda \
    --compile=True \
    --dtype=bfloat16 \
    --n_layer=6 --n_head=6 --n_embd=384 \
    --block_size=256 --batch_size=64 \
    --max_iters=5000 \
    --out_dir=out-my-data
```

---

## 10. 监控与调试

### 10.1 GPU 监控

```bash
# 实时监控 GPU 使用
watch -n 1 nvidia-smi

# 或使用 gpustat（更美观）
pip install gpustat
gpustat -i 1
```

### 10.2 启用 Weights & Biases 日志

```bash
pip install wandb
wandb login

# 训练时启用
python train.py config/train_shakespeare_ubuntu.py --wandb_log=True --wandb_project=nanoGPT
```

### 10.3 常见问题

**CUDA Out of Memory？**
- 减小 `batch_size`
- 减小 `block_size`
- 使用 `gradient_accumulation_steps` 补偿小 batch
- 使用 `dtype='float16'` 替代 `bfloat16`（老 GPU）

**torch.compile 报错？**
- 需要 PyTorch 2.0+
- 老 GPU (Volta 以前) 可设 `compile=False`

**训练 loss 震荡？**
- 降低 `learning_rate`
- 增加 `warmup_iters`
- 检查数据质量

**多 GPU 训练卡住？**
- 检查 NCCL 版本：`python -c "import torch; print(torch.cuda.nccl.version())"`
- 设置 `export NCCL_DEBUG=INFO` 查看通信日志

---

## 11. 本章小结

- [x] Ubuntu 环境搭建（CUDA + PyTorch）
- [x] Shakespeare 快速训练入门
- [x] OpenWebText GPT-2 级别训练
- [x] 多 GPU 分布式训练（DDP）
- [x] 自定义数据训练
- [x] 微调预训练 GPT-2
- [x] 监控与调试
