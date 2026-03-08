# nanochat：用 $100 训练你自己的 ChatGPT

> nanoGPT 的升级版 —— 完整 pipeline 从分词到 Web 聊天，一个脚本跑通全流程

> **类型**: 外部项目教程 | **前置**: 建议先读 [6-nanoGPT-train](../6-nanoGPT-train/) | **硬件**: 8×H100（推荐）/ 8×A100 / 单卡可跑但更慢

## 本章目录

### 教程 (Tutorial)
- [nanochat 快速入门](tutorial/01-快速入门.md) - 环境搭建、一键训练、启动 Web 聊天
- [单卡与低配运行指南](tutorial/02-单卡与低配运行指南.md) - 没有 8 卡 H100 怎么办

### 理论 (Theory)
- [nanochat 架构解析](theory/01-nanochat架构解析.md) - 8000 行代码如何覆盖完整 ChatGPT pipeline
- [从预训练到对话的完整流程](theory/02-从预训练到对话的完整流程.md) - 分词 → 预训练 → SFT → RL → 评估 → 推理
- [nanochat vs nanoGPT](theory/03-nanochat-vs-nanoGPT.md) - 从"只能续写"到"能够对话"的跨越

### 实战 (Hands-on)
- [训练并对话你的迷你 ChatGPT](hands-on/01-训练并对话你的迷你ChatGPT.md) - 完整实战：从零到网页聊天
- [定制你的 nanochat 人格](hands-on/02-定制你的nanochat人格.md) - 通过合成数据注入个性化身份

---

## 什么是 nanochat？

[nanochat](https://github.com/karpathy/nanochat) 是 Andrej Karpathy 开发的全栈 LLM 训练框架，是 nanoGPT 的正式继任者。

| 特性 | 说明 |
|------|------|
| 代码量 | ~8000 行，可读可改 |
| 覆盖范围 | 分词 → 预训练 → SFT → RL → 评估 → Web 聊天 |
| 成本 | ~$48（8×H100 跑 2 小时），Spot 实例低至 ~$15 |
| 最终成果 | 在网页上和你自己训练的模型聊天 |
| 复杂度控制 | 只需调一个参数 `--depth`（Transformer 层数） |

### 与其他项目的关系

```
nanoGPT (只有预训练)
   ↓
nanochat (完整 pipeline：分词 → 训练 → SFT → RL → 评估 → 对话)
```

### nanochat 的完整 pipeline

```
1. tok_train.py      训练 BPE 分词器
2. base_train.py     预训练基座模型
3. base_eval.py      评估基座（CORE score、bits per byte）
4. chat_sft.py       SFT 监督微调
5. chat_rl.py        强化学习（可选）
6. chat_eval.py      评估对话能力
7. chat_web.py       启动 Web 聊天界面
```

### GPT-2 级别模型的训练纪录

| 耗时 | 成本 | 说明 |
|------|------|------|
| 168 小时 | ~$43,000 | 2019 年 OpenAI 原始训练 |
| ~2 小时 | ~$48 | 2026 年 nanochat（8×H100） |

7 年间，同等能力模型的训练成本下降了约 900 倍。

---

## 参考资源

- [nanochat GitHub](https://github.com/karpathy/nanochat)
- [Beating GPT-2 for <<$100: the nanochat journey](https://github.com/karpathy/nanochat/discussions/481)
- [nanochat 原始发布帖](https://github.com/karpathy/nanochat/discussions/1)
- [Guide: 给 nanochat 注入身份](https://github.com/karpathy/nanochat/discussions/139)
- [Guide: 教模型数草莓里的 r](https://github.com/karpathy/nanochat/discussions/164)
- [nanochat-mlx (Apple Silicon 移植)](https://github.com/scasella/nanochat-mlx)
- [DeepWiki: 向 nanochat 提问](https://deepwiki.com/karpathy/nanochat)
