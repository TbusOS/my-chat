# 执行计划：Linux 内核专家系统

## 总览

```
Phase 1         Phase 1.5        Phase 2           Phase 3          Phase 4          Phase 5
知识库搭建  →   RAG 索引构建  →  蒸馏数据生成  →   LoRA 微调   →   评估迭代    →   部署上线
(1-2 周)        (2-3 天)          (1-2 周)          (3-5 天)         (持续)           (1-2 天)
```

---

## Phase 1：知识库搭建（1-2 周）

### 目标
从 FlowSight 同步并扩展 ARM32/ARM64 内核知识库

### 任务清单

#### 1.1 同步 FlowSight 知识库
- [ ] 编写 `tools/sync_knowledge.py`，从 FlowSight 复制 YAML 文件
- [ ] 验证 110+ YAML 文件完整复制
- [ ] 建立文件映射关系表

FlowSight 已有的知识库分布：

| 子系统 | 文件数 | 覆盖情况 |
|--------|--------|---------|
| arch/arm32 | 3 | imx, irq, pm |
| arch/arm64 | 2 | core, patterns |
| core/ | 22 | workqueue, timer, irq, rcu, sched... |
| drivers/ | 40+ | usb, pci, i2c, spi, platform, gpio... |
| mm/ | 7 | page_alloc, slub, vmalloc, dma... |
| net/ | 9 | tcp, udp, skb, netfilter, socket... |
| fs/ | 7 | vfs, ext4, procfs, sysfs, debugfs... |
| sync/ | 4 | locking, completion, rwlock, semaphore |

#### 1.2 扩展 ARM32 知识库
- [ ] 补充 ARM32 异常处理（SWI, Data Abort, IRQ 入口）
- [ ] 补充 ARM32 页表结构（两级/三级页表）
- [ ] 补充 ARM32 中断控制器（GIC-400, VIC）
- [ ] 补充 ARM32 启动流程（head.S → start_kernel）
- [ ] 补充 ARM32 上下文切换（__switch_to）

以 ARM32 异常向量表为例，需要新增的知识：

```yaml
# knowledge/arm32/exception.yaml
arm32_exception:
  vector_table:
    - offset: "0x00"
      type: "Reset"
    - offset: "0x04"
      type: "Undefined Instruction"
    - offset: "0x08"
      type: "SWI (System Call)"
    - offset: "0x0C"
      type: "Prefetch Abort"
    - offset: "0x10"
      type: "Data Abort"
    - offset: "0x18"
      type: "IRQ"
    - offset: "0x1C"
      type: "FIQ"
  kernel_call_chain:
    trigger: "IRQ 中断"
    chain:
      - function: "vector_irq"
        file: "arch/arm/kernel/entry-armv.S"
      - function: "__irq_svc / __irq_usr"
        file: "arch/arm/kernel/entry-armv.S"
      - function: "irq_handler"
        file: "arch/arm/kernel/entry-armv.S"
      - function: "handle_arch_irq"
        file: "arch/arm/kernel/irq.c"
      - function: "generic_handle_irq"
        file: "kernel/irq/irqdesc.c"
      - function: "my_irq_handler()"
        is_user_entry: true
```

#### 1.3 扩展 ARM64 知识库
- [ ] 补充 ARM64 内存屏障指令（DMB, DSB, ISB 详细语义）
- [ ] 补充 ARM64 原子操作（LDXR/STXR, CAS, LSE）
- [ ] 补充 ARM64 虚拟化（EL2, VHE, KVM 入口）
- [ ] 补充 ARM64 安全扩展（TrustZone, EL3, SMC 调用）
- [ ] 补充 ARM64 特性检测（cpufeature, alternatives）

#### 1.4 补充调用链
- [ ] 为每个驱动框架补充 probe/remove 完整调用链
- [ ] 为每个异步机制补充 handler 执行调用链
- [ ] 为系统调用补充 ARM32/ARM64 入口路径
- [ ] 为中断处理补充 ARM32/ARM64 的 GIC 路径

#### 1.5 质量验证
- [ ] 每个 YAML 对照内核源码验证准确性
- [ ] 内核版本标注（以 6.1 LTS 为基准）
- [ ] 编写知识库完整性检查脚本

### 交付物
- `knowledge/` 目录下 130+ 个 YAML 文件
- `tools/sync_knowledge.py` 同步脚本
- `tools/validate_knowledge.py` 验证脚本

---

## Phase 1.5：RAG 源码索引构建（2-3 天）

### 目标
将 Linux 内核源码构建为可检索索引，为模型回答提供源码佐证

### 设计理念

RAG 在本系统中**不是核心，是补充层**：

| 层 | 职责 | 精度 |
|----|------|------|
| 知识库 | 已编码的结构化规则 | 100% |
| 蒸馏模型 | 内化的知识，自然语言回答 | 高（可能有幻觉） |
| **RAG** | **源码佐证，减少幻觉** | **取决于检索质量** |

关键区别：不是纯 RAG（每次都检索拼接），而是模型先回答，RAG 仅在需要时提供源码片段。

### 任务清单

#### 1.5.1 代码切分策略
- [ ] 实现函数级别切分（每个 C 函数一个 chunk）
- [ ] 实现结构体/枚举/联合体切分
- [ ] 实现宏定义块切分
- [ ] 实现汇编文件按标签切分
- [ ] 验证切分质量（抽查 50 个 chunk）

切分规则（按语义，不是按固定行数）：

```
Linux 源码文件
    │
    ├─ .c 文件 → 按函数定义切分
    ├─ .h 文件 → 按结构体/宏定义切分
    └─ .S 文件 → 按汇编标签切分
```

#### 1.5.2 构建 BM25 关键词索引
- [ ] 实现内核代码分词（拆分 snake_case、CamelCase）
- [ ] 实现 BM25 打分和搜索
- [ ] 索引保存/加载
- [ ] 测试常见函数名检索准确率

BM25 索引完全离线可用，不需要任何 embedding 模型。

#### 1.5.3 可选：构建语义向量索引
- [ ] 选择 embedding 模型（推荐 BAAI/bge-base-zh-v1.5）
- [ ] 实现 FAISS 向量索引
- [ ] 实现混合检索（BM25 + 语义，Reciprocal Rank Fusion）
- [ ] 对比纯 BM25 和混合检索的效果

语义索引需要安装额外依赖（sentence-transformers + faiss-cpu），不是必需的。

#### 1.5.4 集成到推理引擎
- [ ] engine.py 加载 RAG 检索器
- [ ] 模型回答时自动检索相关源码
- [ ] 格式化源码上下文（控制长度，不超出模型窗口）
- [ ] 测试 RAG 增强前后的回答质量对比

#### 1.5.5 索引构建执行

```bash
# 基础索引（仅 BM25，快速）
python rag/scripts/build_index.py \
  --source /Users/sky/linux-kernel/linux \
  --arch arm32,arm64

# 完整索引（BM25 + 语义向量）
python rag/scripts/build_index.py \
  --source /Users/sky/linux-kernel/linux \
  --arch arm32,arm64 \
  --semantic
```

预估索引大小：

| 类型 | 大小 | 构建时间 |
|------|------|---------|
| BM25 关键词索引 | ~500MB | ~5 分钟 |
| 语义向量索引 | ~2GB | ~30 分钟 |

### 交付物
- `rag/retriever.py` 混合检索器
- `rag/scripts/build_index.py` 索引构建脚本
- `rag/index/` 索引文件

---

## Phase 2：蒸馏数据生成（1-2 周）

### 目标
用 Opus 4.6 生成 5000-10000 条高质量内核 Q&A 训练数据

### 任务清单

#### 2.1 设计 Prompt 模板

需要覆盖的题型分布：

| 题型 | 占比 | 示例 |
|------|------|------|
| 原理解释 | 30% | "ARM64 的四级页表是如何将虚拟地址转换为物理地址的？" |
| 调用链分析 | 20% | "当用户空间调用 write() 时，内核中经过哪些函数到达驱动的 write 回调？" |
| 代码阅读 | 20% | 给出一段内核代码，要求解释其功能和执行上下文 |
| 对比分析 | 10% | "ARM32 和 ARM64 的中断处理入口有什么区别？" |
| 调试场景 | 10% | "在 softirq 上下文中调用了 mutex_lock 会发生什么？如何排查？" |
| API 用法 | 10% | "devm_request_irq 和 request_irq 有什么区别？何时用哪个？" |

- [ ] 编写原理解释类 prompt 模板
- [ ] 编写调用链分析类 prompt 模板
- [ ] 编写代码阅读类 prompt 模板
- [ ] 编写对比分析类 prompt 模板
- [ ] 编写调试场景类 prompt 模板
- [ ] 编写 API 用法类 prompt 模板

Prompt 模板示例：

```python
# distill/prompts/call_chain.py
TEMPLATE = """
你是 Linux 内核专家。基于以下知识库信息，生成高质量的问答对。

## 知识库上下文
{yaml_content}

## 内核源码参考
{source_code}

## 要求
1. 问题要具体，涉及 ARM32 或 ARM64 架构
2. 回答要包含完整的内核调用链（从触发源到用户代码）
3. 回答要标注每个函数的执行上下文（进程/软中断/硬中断）
4. 回答要标注每个函数所在的源文件
5. 如果涉及可睡眠性，必须明确说明

生成 {count} 个问答对，JSON 格式：
[{{"question": "...", "answer": "...", "category": "call_chain", "arch": "arm64"}}]
"""
```

#### 2.2 编写数据生成脚本
- [ ] `distill/scripts/generate.py` - 主生成脚本
- [ ] 实现分批调 API（每批 10-20 条，控制成本）
- [ ] 实现断点续传（中断后可继续）
- [ ] 实现数据去重
- [ ] 添加进度条和成本估算

#### 2.3 数据生成执行

按子系统分批生成：

| 批次 | 子系统 | 条数 | 预估 API 费用 |
|------|--------|------|--------------|
| 1 | ARM64 核心（异常/页表/系统调用） | 800 | ~$15 |
| 2 | ARM32 核心（异常/页表/中断） | 800 | ~$15 |
| 3 | 驱动框架（USB/PCI/Platform/I2C） | 1500 | ~$25 |
| 4 | 内核核心（调度/中断/WorkQueue/RCU） | 1500 | ~$25 |
| 5 | 内存管理 | 800 | ~$15 |
| 6 | 网络/文件系统/同步 | 1000 | ~$18 |
| 7 | 对比分析（ARM32 vs ARM64） | 600 | ~$12 |
| **合计** | | **7000** | **~$125** |

- [ ] 批次 1：ARM64 核心
- [ ] 批次 2：ARM32 核心
- [ ] 批次 3：驱动框架
- [ ] 批次 4：内核核心
- [ ] 批次 5：内存管理
- [ ] 批次 6：网络/文件系统/同步
- [ ] 批次 7：对比分析

#### 2.4 数据清洗
- [ ] `distill/scripts/clean.py` - 清洗脚本
- [ ] 去除格式错误的条目
- [ ] 验证 JSON 结构完整性
- [ ] 检查答案中的调用链是否与知识库一致
- [ ] 过滤过短/过长的回答
- [ ] 去除重复或高度相似的条目

#### 2.5 数据集划分
- [ ] 按 90/5/5 比例划分 train/val/test
- [ ] 确保每个类别在各集合中分布均匀
- [ ] 保存到 `distill/data/splits/`

### 交付物
- `distill/data/splits/train.jsonl` (~6300 条)
- `distill/data/splits/val.jsonl` (~350 条)
- `distill/data/splits/test.jsonl` (~350 条)
- 各类 prompt 模板文件
- 数据生成和清洗脚本

---

## Phase 3：LoRA 微调（3-5 天）

### 目标
在 Mac Studio M4 Max 128GB 上用 MLX 微调 Qwen2.5-32B

### 任务清单

#### 3.1 环境准备
- [ ] 安装 MLX 和 mlx-lm
- [ ] 下载 Qwen2.5-32B 基座模型（约 64GB）
- [ ] 验证 Mac Studio 内存和性能

```bash
pip install mlx mlx-lm
huggingface-cli download Qwen/Qwen2.5-32B-Instruct --local-dir models/qwen2.5-32b
```

#### 3.2 训练配置

```yaml
# train/configs/qwen2.5-32b.yaml
model: "models/qwen2.5-32b"
train_data: "distill/data/splits/train.jsonl"
val_data: "distill/data/splits/val.jsonl"

# LoRA 参数
lora:
  rank: 16              # LoRA 秩（16 对内核知识足够）
  alpha: 32             # LoRA alpha（通常 2 * rank）
  dropout: 0.05
  target_modules:        # 微调的目标层
    - "q_proj"
    - "k_proj"
    - "v_proj"
    - "o_proj"

# 训练参数
training:
  learning_rate: 2e-4
  batch_size: 2          # 128GB 内存，32B 模型，batch_size=2 安全
  epochs: 3
  warmup_ratio: 0.1
  max_seq_length: 4096   # 内核调用链回答可能较长
  gradient_checkpointing: true
```

- [ ] 编写训练配置文件
- [ ] 编写数据格式转换脚本（适配 MLX chat 模板）

#### 3.3 执行训练
- [ ] 首轮训练（~6300 条，预估 8-12 小时）
- [ ] 监控 loss 曲线
- [ ] 验证集 loss 是否收敛
- [ ] 保存 LoRA 权重到 `train/output/`

```bash
python -m mlx_lm.lora \
  --model models/qwen2.5-32b \
  --data distill/data/splits/ \
  --train \
  --lora-layers 16 \
  --batch-size 2 \
  --num-epochs 3 \
  --learning-rate 2e-4 \
  --adapter-path train/output/kernel-expert-v1
```

#### 3.4 快速验证
- [ ] 合并 LoRA 权重
- [ ] 用几个典型问题手动测试
- [ ] 对比基座模型和微调模型的回答质量

### 交付物
- LoRA 权重文件：`train/output/kernel-expert-v1/`
- 训练日志和 loss 曲线
- 手动测试报告

---

## Phase 4：评估与迭代（持续）

### 目标
构建评估体系，量化模型精度，针对性改进

### 任务清单

#### 4.1 构建评估数据集

200+ 题的评估集，手动编写标准答案：

| 类别 | 题数 | 评估重点 |
|------|------|---------|
| ARM64 架构 | 40 | 异常处理、页表、GICv3、系统调用 |
| ARM32 架构 | 40 | 异常向量、中断控制器、启动流程 |
| 驱动框架 | 40 | USB/PCI/Platform probe 调用链 |
| 内核核心 | 30 | WorkQueue/Timer/RCU 执行上下文 |
| 执行上下文判断 | 30 | "这个函数在什么上下文执行？能否睡眠？" |
| ARM32 vs ARM64 对比 | 20 | 架构差异分析 |

- [ ] 编写 ARM64 架构评估题 (40 题)
- [ ] 编写 ARM32 架构评估题 (40 题)
- [ ] 编写驱动框架评估题 (40 题)
- [ ] 编写内核核心评估题 (30 题)
- [ ] 编写执行上下文判断题 (30 题)
- [ ] 编写对比分析题 (20 题)
- [ ] 为每道题编写标准答案（包含源码引用）

#### 4.2 评估指标

| 指标 | 权重 | 说明 |
|------|------|------|
| 调用链准确率 | 30% | 函数名、顺序是否正确 |
| 执行上下文正确率 | 25% | 进程/软中断/硬中断 判断 |
| 可睡眠性判断 | 15% | 是否正确判断函数能否睡眠 |
| 源文件准确率 | 10% | 引用的文件路径是否正确 |
| 解释清晰度 | 10% | 人工评分 1-5 |
| 无幻觉率 | 10% | 是否编造了不存在的函数/API |

- [ ] 编写自动评估脚本（调用链对比、关键词匹配）
- [ ] 编写人工评估表格模板

#### 4.3 基线对比

测试以下模型作为基线：

| 模型 | 说明 |
|------|------|
| Qwen2.5-Coder-32B（无微调） | 基座模型基线 |
| Qwen2.5-Coder-32B + RAG | 纯 RAG 基线 |
| Qwen2.5-Coder-32B + LoRA | 纯蒸馏方案 |
| Qwen2.5-Coder-32B + LoRA + RAG | 蒸馏 + RAG 混合方案 |
| **知识库 + LoRA + RAG（完整系统）** | **三层混合方案** |

- [ ] 跑基座模型基线
- [ ] 跑纯 RAG 基线
- [ ] 跑纯蒸馏模型
- [ ] 跑蒸馏 + RAG 混合方案
- [ ] 跑完整三层系统
- [ ] 汇总对比报告（重点看：RAG 是否减少了幻觉率）

#### 4.4 迭代改进

根据评估结果，循环执行：

```
评估发现弱点（如 ARM32 启动流程回答差）
    ↓
针对性补充知识库 YAML
    ↓
用 Opus 4.6 生成该领域的额外训练数据（500 条）
    ↓
增量 LoRA 微调
    ↓
重新评估 → 确认改进
```

- [ ] 第一轮评估 → 发现弱点
- [ ] 补充训练数据 → 增量微调
- [ ] 第二轮评估 → 确认改进
- [ ] 重复直到各项指标达标

### 交付物
- `eval/benchmarks/kernel-expert-bench.jsonl` (200+ 题)
- `eval/results/` 各模型评估报告
- 迭代改进记录

---

## Phase 5：部署上线（1-2 天）

### 目标
导出为 Ollama 模型，本地一键使用

### 任务清单

#### 5.1 模型导出
- [ ] 合并 LoRA 权重到基座模型
- [ ] 转换为 GGUF 格式
- [ ] 选择量化级别（Q4_K_M 推荐，平衡精度和速度）

```bash
# 合并 LoRA
python -m mlx_lm.fuse \
  --model models/qwen2.5-32b \
  --adapter-path train/output/kernel-expert-v1 \
  --save-path train/output/kernel-expert-merged

# 转换 GGUF（需要 llama.cpp）
python llama.cpp/convert_hf_to_gguf.py \
  train/output/kernel-expert-merged \
  --outtype q4_k_m \
  --outfile serve/models/kernel-expert-q4.gguf
```

#### 5.2 Ollama 配置
- [ ] 编写 Modelfile

```dockerfile
# serve/configs/Modelfile
FROM ./kernel-expert-q4.gguf

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

SYSTEM """你是 Linux 内核专家，专注于 ARM32 和 ARM64 架构。

你的知识来源：
1. Linux 内核源码（基于 6.1 LTS）
2. ARM Architecture Reference Manual
3. 内核子系统的完整调用链

回答规则：
- 涉及调用链时，列出完整的函数调用路径，标注源文件
- 涉及执行上下文时，明确标注（进程/软中断/硬中断）
- 涉及可睡眠性时，明确说明能否睡眠及原因
- 如果不确定，明确说"我不确定"，不要编造
"""
```

- [ ] 创建 Ollama 模型

```bash
ollama create kernel-expert -f serve/configs/Modelfile
ollama run kernel-expert
```

#### 5.3 功能验证
- [ ] 测试常见问题回答质量
- [ ] 测试推理速度（tokens/sec）
- [ ] 测试长对话的上下文保持

### 交付物
- GGUF 模型文件
- Ollama Modelfile
- 使用说明

---

## Phase 6: 自学习闭环（持续运行）

### 目标
系统在日常使用中自动收集反馈、分析弱点、更新知识库、增量微调

### 核心原则

**模型不是核心，知识库才是核心。**

- 知识库查到的答案 = 100% 准确（人类编码的规则）
- 模型回答的 = 需要验证（可能有幻觉）
- 用户每一次修正 = 永久改进系统（写入知识库 YAML）
- 下次同类问题 = 直接从知识库返回，不再经过模型

### 基座模型变更

原方案用 Qwen2.5-32B（通用），改为 **Qwen2.5-Coder-32B-Instruct**（代码专用）：
- 代码理解能力从 ~75% 提升到 ~92%（HumanEval）
- 对 C 代码、内联汇编、内核 API 的理解更准确
- 相同参数量，不增加硬件需求

### 自学习模块文件

| 文件 | 功能 |
|------|------|
| `serve/api/engine.py` | 三层推理引擎：知识库查询 → 本地模型 → Opus 兜底 |
| `serve/api/chat.py` | 交互式命令行，支持 /good /bad /fix 反馈 |
| `serve/feedback/self_improve.py` | 自学习改进：分析 → 更新 → 生成 → 微调 → 评估 |

### 日常使用流程

```bash
# 启动交互式命令行
python serve/api/chat.py

# 提问
> ARM64 上 timer 回调在什么上下文执行？

# 系统回答（标注置信度和来源）
  [CERTAIN] 来自知识库精确匹配
  来源: 知识库
  上下文: softirq
  可睡眠: 否

# 如果回答正确
> /good

# 如果回答错误
> /bad
> /fix 正确答案是...timer 回调在 softirq 上下文执行，
  调用链是 run_timer_softirq → __run_timers → call_timer_fn → timer->function()

# 查看统计
> /stats

# 积累足够反馈后触发改进
> /improve
```

### 自动改进周期

积累 50+ 条反馈后自动触发：

```bash
python serve/feedback/self_improve.py --full-cycle
```

执行步骤：

| 步骤 | 自动化程度 | 说明 |
|------|-----------|------|
| 1. 错误模式分析 | 全自动 | 按子系统统计错误率，找出薄弱环节 |
| 2. 知识库更新建议 | 半自动 | 从用户修正提取 YAML 补丁，需人工审核 |
| 3. 补充数据生成 | 全自动 | 针对薄弱子系统调 Opus 4.6 API |
| 4. LoRA 增量微调 | 全自动 | MLX LoRA，只跑 1 epoch |
| 5. 回归评估 | 全自动 | 跑评估集确认没退步 |

### 知识库更新安全机制

用户修正不会直接写入知识库，而是经过审核：

```
用户修正 → pending_updates/ 目录（待审核）
    ↓
self_improve.py --update-kb
    ↓
生成 YAML 补丁 → yaml_patches/ 目录
    ↓
人工审核（或高置信度自动合并）
    ↓
合并到 knowledge/ 目录
```

低风险条目可以设置自动合并（如仅补充执行上下文信息），
高风险条目（如修改调用链）必须人工审核。

### 任务清单

- [ ] 测试 engine.py 三层推理引擎
- [ ] 测试 chat.py 交互式反馈流程
- [ ] 测试 self_improve.py 错误分析
- [ ] 测试知识库补丁生成和审核流程
- [ ] 设置定期改进的 cron job（可选）
- [ ] 记录知识库版本变更日志

### 交付物
- 可用的交互式命令行（`python serve/api/chat.py`）
- 反馈收集和分析系统
- 知识库增量更新机制
- 模型增量微调流程

---

## 时间线总览

```
第 1 周  ████████░░░░░░░░░░░░  Phase 1: 知识库同步 + ARM32 扩展
第 2 周  ░░░░████████░░░░░░░░  Phase 1: ARM64 扩展 + Phase 1.5: RAG 索引构建
第 3 周  ░░░░░░░░████████░░░░  Phase 2: Prompt 设计 + 数据生成
第 4 周  ░░░░░░░░░░░░████████  Phase 2: 数据清洗 + Phase 3: LoRA 微调
第 5 周  ░░░░░░░░░░░░░░░░████  Phase 4: 评估对比 + Phase 5: 部署
第 6 周+ ░░░░░░░░░░░░░░░░░░██  Phase 6: 自学习持续迭代
```

## 成本估算

| 项目 | 费用 |
|------|------|
| Mac Studio M4 Max 128GB | ~¥32,000（一次性） |
| Opus 4.6 API 蒸馏数据生成 | ~$125（约 ¥900） |
| 电费（微调 + 推理） | 可忽略 |
| **总计** | **~¥33,000** |

## 风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 蒸馏数据质量不够 | 中 | 增加人工审核环节，抽检 10% 数据 |
| 32B 模型微调内存溢出 | 低 | 降低 batch_size 到 1 或换 14B 模型先验证 |
| 评估分数低 | 中 | 迭代补充数据，先从单个子系统做到满分 |
| Opus 4.6 API 限流 | 低 | 分批生成，设置合理的 rate limit |
| 知识库与新版内核不符 | 中 | 以 6.1 LTS 为基准，后续按需更新 |
