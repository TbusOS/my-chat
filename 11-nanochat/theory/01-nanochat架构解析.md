# nanochat 架构解析

## 设计哲学

nanochat 不是一个 LLM "框架"，没有巨大的配置对象、模型工厂或 if-else 怪兽。它是一个单一的、内聚的、最小的、可读可改的代码库。

核心设计原则：

- **一个旋钮**：`--depth`（Transformer 层数）决定一切，其他超参自动计算
- **全栈覆盖**：从分词到聊天 UI，一个仓库搞定
- **可 fork**：设计为"最大可 fork 性"的强基线

## 目录结构

```
nanochat/
├── nanochat/                # 核心库
│   ├── gpt.py               # GPT Transformer 模型定义
│   ├── tokenizer.py          # BPE 分词器（GPT-4 风格）
│   ├── dataloader.py         # 分布式数据加载器
│   ├── dataset.py            # 预训练数据下载与读取
│   ├── optim.py              # AdamW + Muon 优化器
│   ├── engine.py             # KV Cache 推理引擎
│   ├── checkpoint_manager.py # Checkpoint 管理
│   ├── core_eval.py          # DCLM CORE 评估
│   ├── loss_eval.py          # Bits Per Byte 评估
│   ├── execution.py          # Python 代码执行（Tool Use）
│   ├── common.py             # 公共工具函数
│   └── ui.html               # Web 聊天前端
├── scripts/                 # 可执行脚本
│   ├── tok_train.py          # 1. 训练分词器
│   ├── base_train.py         # 2. 预训练基座
│   ├── base_eval.py          # 3. 评估基座
│   ├── chat_sft.py           # 4. SFT 微调
│   ├── chat_rl.py            # 5. 强化学习
│   ├── chat_eval.py          # 6. 评估对话
│   ├── chat_cli.py           # 7a. CLI 聊天
│   └── chat_web.py           # 7b. Web 聊天
├── tasks/                   # 评估任务
│   ├── gsm8k.py              # 数学题
│   ├── mmlu.py               # 多领域选择题
│   ├── humaneval.py          # 简单编程题
│   ├── arc.py                # 科学选择题
│   ├── spellingbee.py        # 拼写/数字母
│   └── smoltalk.py           # HuggingFace SmolTalk 数据
└── runs/                    # 运行脚本
    ├── speedrun.sh            # 一键训练 GPT-2 级别模型
    ├── runcpu.sh              # CPU/MPS 运行
    ├── miniseries.sh          # 多规模模型系列训练
    └── scaling_laws.sh        # Scaling Laws 实验
```

## 核心模块解析

### gpt.py — Transformer 模型

和 nanoGPT 一样是标准的 GPT 架构，但增加了：

- `--depth` 自动推导 width、head 数、学习率等
- 自定义 Linear 层，前向传播时自动转换到 `COMPUTE_DTYPE`
- Embedding 直接存储为 `COMPUTE_DTYPE` 节省显存

### optim.py — 优化器

同时实现了 AdamW 和 Muon 优化器，支持单卡和分布式。

### engine.py — KV Cache 推理

支持 KV Cache 的高效推理引擎，用于训练后的聊天和评估。

### dataloader.py — 分布式数据加载

在训练时自动处理数据分片和跨 GPU 分发。

## --depth：唯一的超参

这是 nanochat 最精妙的设计。你只需要指定 Transformer 的层数，其他一切自动确定：

| depth | 大约等价 | 训练时间（8×H100） |
|-------|---------|-------------------|
| 4 | 极小模型 | ~5 分钟 |
| 12 | GPT-1 规模 | ~5 分钟 |
| 20-26 | GPT-2 规模 | ~2-3 小时 |

```bash
# 快速实验用 depth=12
torchrun --nproc_per_node=8 -m scripts.base_train -- --depth=12

# 完整训练用 depth=20-26
torchrun --nproc_per_node=8 -m scripts.base_train -- --depth=26
```

## 不使用 autocast

nanochat 拒绝 `torch.amp.autocast`，用 `COMPUTE_DTYPE` 全局变量显式管理精度。模型权重以 fp32 存储（保证优化器精度），前向传播时转为低精度。

---

> **下一步**：了解完整训练流程的每个阶段，看 [从预训练到对话的完整流程](02-从预训练到对话的完整流程.md)
