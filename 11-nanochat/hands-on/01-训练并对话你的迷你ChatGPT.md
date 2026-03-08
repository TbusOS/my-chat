# 训练并对话你的迷你 ChatGPT

## 目标

从零完成 nanochat 的完整训练 pipeline，最终在 Web 界面上和你的模型对话。

## 前置准备

- 一台有 GPU 的机器（推荐 8×H100，单卡也能跑）
- 已完成 [快速入门](../tutorial/01-快速入门.md) 中的环境搭建

## 完整流程

### 第一步：训练分词器

```bash
python -m scripts.tok_train
```

这会训练一个 GPT-4 风格的 BPE 分词器。完成后你会得到分词器文件。

**验证**：

```bash
# 评估分词器的压缩率
python -m scripts.tok_eval
```

### 第二步：预训练基座模型

这是最耗时的一步。

```bash
# 8 卡（推荐）
OMP_NUM_THREADS=1 torchrun --standalone --nproc_per_node=8 -m scripts.base_train -- \
    --depth=26 \
    --run="my-gpt2"
```

```bash
# 单卡（需要更久，建议用更小的 depth）
python -m scripts.base_train -- --depth=12 --run="my-small-gpt"
```

**预期时间**：

| 配置 | depth=12 | depth=26 |
|------|----------|----------|
| 8×H100 | ~5 分钟 | ~2 小时 |
| 单卡 H100 | ~40 分钟 | ~16 小时 |
| 单卡 3090 | ~2 小时 | 不推荐 |

**如何判断训练在正常进行**：
- `val_bpb` 应该持续下降
- `train/tok_per_sec` 稳定
- 无 OOM 错误

### 第三步：评估基座模型

```bash
python -m scripts.base_eval
```

这会输出：
- DCLM CORE score（GPT-2 基准为 0.2565，超过这个就是 GPT-2 级别）
- Bits per byte
- 生成的文本样本

此时模型只能续写文本，还不能对话。

### 第四步：SFT 监督微调

```bash
python -m scripts.chat_sft
```

这一步用对话数据（SmolTalk）教模型"如何聊天"。完成后，模型从"续写机器"变成"对话助手"。

### 第五步：强化学习（可选）

```bash
python -m scripts.chat_rl
```

通过奖励信号进一步提升对话质量。这一步是可选的，跳过也能聊天。

### 第六步：评估对话能力

```bash
python -m scripts.chat_eval
```

会在 GSM8K（数学）、MMLU（知识）、HumanEval（编程）等任务上评估。

### 第七步：启动聊天！

```bash
# Web 界面（推荐）
python -m scripts.chat_web

# 或 CLI
python -m scripts.chat_cli -p "你好"
```

打开浏览器，访问显示的 URL，开始和你的模型对话！

## 你会看到什么

训练完 depth=26 的模型后：

- **能做的事**：写故事、回答常识问题、简单推理、写诗
- **做不好的事**：复杂数学、长逻辑链、最新知识（它只知道训练数据里的内容）
- **有趣的事**：问它"你是谁"，它会自信地编造一个身份（幻觉）

> Karpathy 的描述：和它聊天就像和一个幼儿园小朋友聊天 :)

## 如果一切顺利

恭喜！你刚刚走完了和 OpenAI 训练 ChatGPT 本质上相同的全部流程：

```
分词器 → 预训练 → 评估 → SFT → RL → 部署
```

不同的只是规模 —— OpenAI 用了上万张卡和数百万美元，你用了不到 $100。

## 常见问题

### Q: 我的模型回答很差怎么办？

- depth 越小，能力越弱。depth=12 只是 GPT-1 水平
- SFT 数据的质量决定对话质量
- 确保每个阶段都正常完成（看 loss 曲线）

### Q: 可以用中文聊天吗？

默认训练数据以英文为主。如果想要中文能力，需要在 SFT 阶段混入中文对话数据。

### Q: 怎么保存和分享我的模型？

训练过程会自动保存 checkpoint。你可以把 checkpoint 文件拷贝到其他机器，用 `chat_web.py` 加载并对话。

---

> **下一步**：想给模型定制个性？看 [定制你的 nanochat 人格](02-定制你的nanochat人格.md)
