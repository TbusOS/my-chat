# 13-kernel-expert: Linux 内核专家系统

> 基于 FlowSight 知识库 + Opus 4.6 蒸馏训练，构建本地 ARM32/ARM64 内核专家模型

## 项目背景

### 问题

任何 LLM（包括最强闭源模型）都无法 100% 精准理解 Linux 内核，原因：
- 内核源码约 2800 万行，ARM 子系统极其复杂
- LLM 本质是概率模型，会产生幻觉（hallucination）
- 内核版本持续演进，训练数据永远滞后

### 解决方案：混合架构

不依赖单一技术，而是结合**确定性规则**、**概率模型**和**源码检索**：

```
第一层：确定性知识引擎（借鉴 FlowSight）
  - YAML 知识库：ARM32/ARM64 架构规则
  - 调用链数据库：所有子系统的完整调用路径
  - 模式匹配器：正则精确识别内核 API
  - 约束规则：执行上下文（是否可睡眠、中断安全）
  - 精度：100%（人类精确编码的规则）

第二层：蒸馏模型 + RAG 辅助
  - 蒸馏模型（Opus 4.6 → Qwen2.5-Coder-32B）
    - 知识"内化"到模型权重，离线可用
    - 比纯 RAG 更连贯、更快
  - RAG 源码检索（模型不确定时自动触发）
    - 内核源码向量索引，检索相关代码片段
    - 为模型回答提供源码佐证，减少幻觉
    - 支持 "show me 实现" 类问题

第三层：Opus 4.6 API 兜底（可选）
  - 用户对本地回答不满意时调用
  - 需要网络，不适合频繁使用
```

### 为什么不用纯 RAG？

| 对比项 | 纯 RAG | 蒸馏 + 知识库 + RAG 辅助 |
|--------|--------|--------------------------|
| 离线可用 | 需要向量数据库 | 模型自带知识，RAG 可选 |
| 回答连贯性 | 拼接感强 | 模型先回答，RAG 提供佐证 |
| 推理延迟 | 高（每次检索 + 生成） | 知识库命中时极快，仅需要时检索 |
| 知识深度 | 取决于检索质量 | 内化到权重 + 源码检索兜底 |
| 更新成本 | 重建索引 | 重新微调 + 重建索引 |

### RAG 在本系统中的定位

RAG **不是核心，是补充层**。本系统引入 RAG 但与纯 RAG 方案有本质区别：

- **纯 RAG**：每次都检索 → 拼接 → 生成，回答碎片化、延迟高
- **本系统**：知识库优先 → 模型用内化知识回答 → RAG 仅在模型不确定时提供内核源码佐证

RAG 索引的对象是**内核源码**（不是知识库，知识库已有精确查询）：

| 场景 | 没有 RAG | 有 RAG |
|------|---------|--------|
| 查询知识库没覆盖的冷门函数 | 模型凭记忆猜测 | 检索实际代码后有据回答 |
| 不同内核版本的差异 | 训练数据可能过时 | 索引最新源码，版本准确 |
| 调用链验证 | 模型可能编造中间函数 | 检索实际调用关系交叉验证 |
| "show me 实现" 类问题 | 无法给出代码 | 直接返回源码片段 |

### 为什么不用纯微调？

纯微调没有"锚点"，模型可能在细节上产生幻觉。知识库提供确定性的规则兜底：
- 调用链、执行上下文、API 语义 → 规则（100% 精准）
- "为什么这样设计"、"和其他方案对比" → 蒸馏模型（辅助理解）
- 具体代码实现细节 → RAG 从源码检索（有据可查）

## 核心灵感来源：FlowSight

FlowSight（`/Users/sky/linux-kernel/usb-learn/flowsight`）是一个跨平台执行流可视化 IDE，
它用**知识库驱动的静态分析**替代 LLM 猜测，提供了三个关键设计：

### 1. 结构化 YAML 知识库

FlowSight 包含 110+ 个 YAML 文件，精确编码内核知识：

```yaml
# 示例：USB probe 回调
usb_driver:
  callbacks:
    probe:
      pattern: '\.probe\s*=\s*(?P<handler>\w+)'
      trigger: "USB 设备插入且 ID 匹配"
      context: "process"        # 进程上下文
      can_sleep: true           # 可以睡眠
      signature: "int (*)(struct usb_interface *, const struct usb_device_id *)"
```

### 2. 完整调用链

把内核隐式调用路径显式化，LLM 做不到这种精度：

```
USB 设备插入 →
  usb_hub_port_connect() →
    usb_new_device() →
      device_add() →
        bus_probe_device() →
          __device_attach() →
            driver_probe_device() →
              really_probe() →
                usb_probe_interface() →
                  drv->probe()  ← 你的代码在这里
```

### 3. Bind-Trigger 关联

通过正则模式精确匹配异步机制的绑定和触发：

```yaml
work_struct:
  bind_patterns:
    - 'INIT_WORK(&dev->work, my_handler)'    # 绑定
  trigger_patterns:
    - 'schedule_work(&dev->work)'             # 触发 → my_handler
```

## 基座模型选择

**不用通用 Qwen2.5，用代码专用变体 Qwen2.5-Coder-32B-Instruct。**

通用模型对内核代码的理解能力不足，蒸馏效果会受限于学生模型的能力上限：

| 模型 | HumanEval | 适合场景 |
|------|-----------|---------|
| Qwen2.5-32B（通用） | ~75% | 通用对话 |
| **Qwen2.5-Coder-32B** | ~92% | 代码理解（推荐） |
| DeepSeek-Coder-V2 | ~90% | 备选 |

但即使用代码模型，**模型也不是系统的核心**——知识库才是。
模型的角色是"翻译者"：把知识库的结构化数据翻译成自然语言。
翻译错了，知识库兜底。知识库没有的，靠用户反馈补充。

## 自学习闭环（核心设计）

系统不是训练一次就用的"死"模型，而是越用越准的"活"系统：

```
用户提问
    |
    v
[第一层] 知识库精确查询 ── 命中 → 直接返回（100% 准确）
    |
    v 没命中
[第二层] 本地模型回答（标注置信度）
    |
    v
用户反馈（正确/错误/修正）
    |
    v
反馈积累到 50+ 条时触发自我改进：
    |
    +── 错误模式分析 → 找出薄弱子系统
    +── 知识库更新 → 从用户修正中提取新 YAML 规则
    +── 补充数据生成 → 针对薄弱环节调 Opus 4.6 生成数据
    +── LoRA 增量微调 → 用新数据微调
    +── 回归评估 → 确保没退步
    |
    v
  越用越准
```

关键：**模型答错不可怕，用户的每一次修正都在永久改进系统。**
修正内容会写入知识库 YAML，下次同类问题直接从知识库返回，不再经过模型。

## 目录结构

```
13-kernel-expert/
├── README.md                    # 本文件
├── PLAN.md                      # 执行计划
│
├── knowledge/                   # 第一层：确定性知识库
│   ├── arm32/                   # ARM32 架构知识
│   ├── arm64/                   # ARM64 架构知识
│   ├── core/                    # 内核核心（workqueue, timer, irq, rcu...）
│   ├── drivers/                 # 驱动框架（usb, pci, i2c, platform...）
│   ├── mm/                      # 内存管理（page_alloc, slub, vmalloc...）
│   ├── net/                     # 网络子系统（tcp, udp, skb...）
│   ├── fs/                      # 文件系统（vfs, ext4, procfs...）
│   └── sync/                    # 同步原语（locking, completion...）
│
├── distill/                     # 第二层：Opus 4.6 蒸馏流水线
│   ├── prompts/                 # 蒸馏 prompt 模板
│   ├── scripts/                 # 数据生成脚本
│   └── data/                    # 训练数据（全部本地存储）
│       ├── raw/                 # API 返回的原始数据
│       ├── cleaned/             # 清洗后的数据
│       └── splits/              # train/val/test 划分
│
├── train/                       # LoRA 微调
│   ├── configs/                 # 训练配置（MLX 格式）
│   └── scripts/                 # 训练脚本
│
├── eval/                        # 模型评估
│   ├── benchmarks/              # 评估数据集（200+ 内核问答对）
│   ├── scripts/                 # 评估脚本
│   └── results/                 # 评估结果
│
├── rag/                         # RAG 源码检索层
│   ├── scripts/
│   │   └── build_index.py       # 内核源码向量索引构建
│   ├── index/                   # 向量索引文件（自动生成）
│   └── retriever.py             # 检索器（语义搜索 + 关键词搜索）
│
├── serve/                       # 推理 + 自学习
│   ├── configs/                 # Ollama modelfile
│   ├── api/
│   │   ├── engine.py            # 三层推理引擎（知识库→模型+RAG→Opus兜底）
│   │   └── chat.py              # 交互式命令行（支持反馈）
│   └── feedback/
│       ├── self_improve.py      # 自学习改进模块（分析→更新→微调→评估）
│       ├── feedback_log.jsonl   # 用户反馈日志（自动生成）
│       └── pending_updates/     # 待审核的知识库更新（自动生成）
│
└── tools/                       # 辅助工具
    └── sync_knowledge.py        # 从 FlowSight 同步知识库
```

## 硬件要求

推荐：**Mac Studio M4 Max 128GB 统一内存**

| 环节 | 内存需求 | 说明 |
|------|---------|------|
| 蒸馏数据生成 | 任意 | 调 Opus 4.6 API，不吃本地资源 |
| RAG 索引构建 | ~8GB | 内核源码向量化，一次性构建 |
| LoRA 微调 14B | ~32GB | Mac Mini 64GB 可用 |
| LoRA 微调 32B | ~80GB | 需要 Mac Studio 128GB |
| 推理 32B Q4 + RAG | ~24GB | Mac Mini 64GB 可用 |
| 推理 70B Q4 + RAG | ~44GB | Mac Studio 128GB 可用 |

## 数据流全景

```
FlowSight YAML (110+ 文件)          Linux 内核源码 (2800万行)
        │                                    │
        ├─ 同步到 knowledge/ 目录            ├─ 向量化索引
        │                                    │
        ▼                                    ▼
组装 Prompt（知识库 + 内核源码片段）    rag/index/ (向量数据库)
        │                                    │
        ▼                                    │
调 Opus 4.6 API → Q&A 数据                  │
        │                                    │
        ▼                                    │
数据清洗 → 划分 train/val/test               │
        │                                    │
        ▼                                    │
MLX LoRA 微调 → 本地模型权重                 │
        │                                    │
        ▼                                    │
评估 → 发现弱点 → 补充数据 → 重训           │
        │                                    │
        ▼                                    ▼
导出 Ollama 模型 ─────────────────── serve/api/engine.py
                                      │
                                      ▼
                              三层推理引擎
                      知识库 → 模型+RAG → Opus兜底
```

## 快速开始

```bash
# 1. 从 FlowSight 同步知识库
python tools/sync_knowledge.py

# 2. 构建内核源码 RAG 索引
python rag/scripts/build_index.py --source /path/to/linux-kernel --arch arm32,arm64

# 3. 生成蒸馏数据（需要 Anthropic API key）
export ANTHROPIC_API_KEY="sk-ant-..."
python distill/scripts/generate.py --topic arm64 --count 500

# 4. 数据清洗
python distill/scripts/clean.py

# 5. LoRA 微调（Mac Studio 上运行，注意用 Coder 变体）
python train/scripts/lora_train.py --model Qwen/Qwen2.5-Coder-32B-Instruct

# 6. 评估
python eval/scripts/evaluate.py --model kernel-expert

# 7. 导出到 Ollama 并使用
ollama create kernel-expert -f serve/configs/Modelfile
python serve/api/chat.py

# 8. 使用过程中提供反馈，积累后触发自我改进
python serve/feedback/self_improve.py --full-cycle
```

## 相关资源

- FlowSight 知识库：`/Users/sky/linux-kernel/usb-learn/flowsight/knowledge/`
- Linux 内核源码：`/Users/sky/linux-kernel/linux/`
- Ollama 部署指南：`../12-ollama-macos-setup/`
- LoRA 微调基础：`../2-litgpt-finetune/`
- 模型评估方法：`../10-model-evaluation/`
