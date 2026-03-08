# nanochat vs nanoGPT

## 为什么需要 nanochat？

nanoGPT 只做了训练 ChatGPT 的**第一步**（预训练），而 nanochat 覆盖了**全部步骤**。

用一个比喻：nanoGPT 教你造了一个引擎，nanochat 教你造了一辆完整的车并开上路。

## 对比

| 维度 | nanoGPT | nanochat |
|------|---------|----------|
| 作者 | Karpathy | Karpathy |
| 状态 | 不再活跃维护 | 活跃开发中 |
| 代码量 | ~300 行 | ~8000 行 |
| 覆盖阶段 | 预训练 | 分词 → 预训练 → SFT → RL → 评估 → 对话 |
| 最终产出 | 能续写文本的模型 | 能在网页上聊天的模型 |
| 训练数据 | Shakespeare / OpenWebText | FineWeb / ClimbMix / SmolTalk |
| 分词器 | 使用 GPT-2 现成分词器 | 从零训练 BPE 分词器 |
| 评估 | 只看 loss | CORE score + 多任务评估 |
| 推理 | 简单采样 | KV Cache 高效推理 |
| 部署 | 无 | FastAPI Web UI |
| 超参管理 | 手动设置 | `--depth` 一个参数自动推导 |
| 优化器 | AdamW | AdamW + Muon |
| 精度 | 手动 autocast | 显式 COMPUTE_DTYPE |

## 能力差异

### nanoGPT 训练出来的模型

```
输入: "The quick brown fox"
输出: "jumps over the lazy dog and then proceeded to run across the field..."
```

只能续写，不能对话。你说"你好"，它不会回"你好"，而是会接着写一段和"你好"相关的文本。

### nanochat 训练出来的模型

```
用户: 你好，请介绍一下你自己
助手: 我是一个由 nanochat 训练的语言模型...

用户: 天空为什么是蓝色的？
助手: 天空呈现蓝色是因为瑞利散射...
```

能够进行多轮对话，理解用户意图并给出回答。

## 关键差异：SFT 是分水岭

从"续写"到"对话"的关键一步是 **SFT（Supervised Fine-Tuning）**：

```
基座模型（只会续写）
    ↓ SFT：用对话数据微调
对话模型（会问答）
    ↓ RL：用奖励信号优化
更好的对话模型
```

nanoGPT 止步于基座模型，nanochat 走完了全程。

## 代码复杂度

虽然 nanochat 有 8000 行，但核心训练逻辑和 nanoGPT 是同源的：

- `gpt.py` 是 nanoGPT 模型定义的进化版
- `base_train.py` 对应 nanoGPT 的 `train.py`
- 新增的代码主要是 SFT、RL、评估和推理

如果你已经读懂了 nanoGPT（本仓库 [6-nanoGPT-train](../../6-nanoGPT-train/)），理解 nanochat 不会有太大障碍。

## 学习路径建议

```
6-nanoGPT-train  理解预训练的核心
       ↓
11-nanochat      理解从预训练到完整 ChatGPT 的全流程
```

---

> **下一步**：动手实操，看 [训练并对话你的迷你 ChatGPT](../hands-on/01-训练并对话你的迷你ChatGPT.md)
