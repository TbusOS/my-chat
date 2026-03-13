# AI 培训 PPT — 需求文档

## 项目背景

### 团队情况
- 软件技术团队，涵盖前后端、基础设施等方向
- 团队目前没有 AI 基础，无模型平台部署
- 大部分人仅使用 Cursor 基础功能，把 AI 当聊天工具
- Claude CLI、高阶 AI 工具链基本无人掌握

### 培训目标
1. 让团队理解 AI 的完整技术体系（从概念到实践）
2. **核心认知转变：把 AI 从"聊天工具"变成"当人来用"**
3. 掌握大模型 API 调用、参数调优的实操能力
4. 理解 Agent 生态（MCP、Skills、OpenClaw）的架构与原理
5. 学会 Cursor 高阶用法和 Claude CLI 实战

### 培训对象
- 软件/硬件/系统工程师为主
- 小白视角通俗易懂，但核心技术点必须精准

---

## 技术方案

### 制作工具
- **主体内容**：Marp CLI（Markdown → PPTX / PDF / HTML）
- **关键交互页**：原生 HTML + CSS + JavaScript 动画
- **现场演示**：可直接运行的 Shell / Python 脚本

### 项目结构

```
19-ai-training-ppt/
├── docs/
│   └── requirements.md          # 本文档
├── slides/                      # Marp 幻灯片源文件
│   ├── 01-mindset-shift.md      # 第一部分：认知颠覆
│   ├── 02-llm-landscape.md      # 第二部分：主流大模型
│   ├── 03-api-and-params.md     # 第三部分：API 与参数
│   ├── 04-fine-tuning.md        # 第四部分：微调
│   ├── 05-agents-ecosystem.md   # 第五部分：Agent 生态
│   ├── 06-tools-practice.md     # 第六部分：实战工具链
│   └── 07-reflection.md         # 第七部分：冷思考
├── interactive/                  # HTML 交互演示页
│   ├── temperature-playground.html
│   ├── agent-flow.html
│   ├── mcp-architecture.html
│   ├── llm-api-compare.html
│   └── openclaw-os-analogy.html
├── demos/                        # 现场动手演示脚本
│   ├── 01-curl-api-call.sh
│   ├── 02-python-api.py
│   ├── 03-cursor-advanced.md
│   └── 04-claude-cli-demo.sh
├── theme/                        # Marp 自定义主题
│   └── ai-training.css
└── README.md                     # 构建、导出、演示说明
```

---

## 内容大纲

### 第一部分：认知颠覆（15 页 / 30 分钟）

> 主线："别把 AI 当工具，把 AI 当人"

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 1 | 你真的会用 AI 吗？ | 开场：大部分人只把 AI 当搜索引擎或聊天机器人 | Marp |
| 2 | AI 不是工具，是"人" | 对比：问搜索引擎 vs 给 AI 下工作指令 | Marp |
| 3 | "聊天式"vs"当人用" | 同一需求两种提问方式的输出差异（截图对比） | Marp |
| 4 | 什么是 AI？ | 规则系统 → 机器学习 → 深度学习 → LLM 的演进时间线 | Marp |
| 5 | 什么是 AGI？ | 通用人工智能：能做任何人类智力任务，目前还没到 | Marp |
| 6 | 什么是 ASI？ | 超级人工智能：超越人类，纯理论阶段 | Marp |
| 7 | AI 的"大脑"：Transformer | 用快递分拣中心类比注意力机制，不讲公式，讲直觉 | Marp 图解 |
| 8 | 预训练：读遍互联网 | 大模型怎么"学习"的，训练数据规模感知 | Marp |
| 9 | 为什么 AI 能"理解"你说的话？ | Token 化 → 向量 → 注意力 → 生成，通俗流程图 | Marp 图解 |
| 10 | 多模态：不只会读字 | 文本 / 图像 / 音频 / 视频，各模型支持情况 | Marp |
| 11 | 多模态实际能干嘛？ | 看图写代码、语音转文字、视频理解 — 真实案例 | Marp |
| 12 | 提示词 ≠ 问问题 | 提示词是"工作指令"：角色设定 + 上下文 + 约束 + 输出格式 | Marp |
| 13 | System / User / Assistant | 三种角色的职责和关系，就像公司的制度、员工、执行 | Marp |
| 14-15 | 🔴 互动演示 | 同一问题，调整提示词策略，实时对比输出效果 | HTML 交互 |

### 第二部分：主流大模型横向对比（12 页 / 20 分钟）

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 16 | 大模型全景图 | 市面主流模型一览：厂商、发布时间、定位 | Marp |
| 17 | GPT 系列 (OpenAI) | GPT-4o / o1 / o3，特点：生态最大、插件最多 | Marp |
| 18 | Claude 系列 (Anthropic) | Opus / Sonnet / Haiku，特点：长上下文、代码能力、安全对齐 | Marp |
| 19 | Gemini 系列 (Google) | 多模态原生、200 万 token 上下文、Google 生态 | Marp |
| 20 | 国产模型 | Qwen（通义）、DeepSeek、GLM（智谱）、文心一言 | Marp |
| 21 | 能力雷达图 | 代码 / 推理 / 创意 / 多模态 / 长文本 五维对比 | Marp 图表 |
| 22 | 架构差异：Dense vs MoE | Dense（全参数激活）vs MoE（专家混合），配图解释 | Marp 图解 |
| 23 | 训练策略差异 | 数据规模、对齐方式（RLHF / Constitutional AI / DPO） | Marp |
| 24 | 上下文窗口对比 | 各模型支持的 token 数量，对实际使用的影响 | Marp |
| 25 | 垂直领域：代码模型 | Codex、StarCoder、DeepSeek-Coder、Qwen-Coder | Marp |
| 26 | 垂直领域：行业模型 | 医疗 / 金融 / 法律 / 教育 各领域代表 | Marp |
| 27 | 端侧小模型 | Phi、Gemma、Qwen-tiny — 边缘设备场景的可能性 | Marp |

### 第三部分：调用大模型 — API 与参数（15 页 / 40 分钟）

> 全程动手

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 28 | API 是什么？ | 用餐厅点菜流程类比 API 请求/响应 | Marp 类比 |
| 29 | 大模型 API 的基本结构 | endpoint / headers / body，通用请求格式 | Marp 代码 |
| 30 | 认证与密钥 | API Key 管理，安全注意事项 | Marp |
| 31 | temperature — 创造力旋钮 | 0.0 = 确定性输出，1.0 = 创意发散，什么场景用什么值 | Marp |
| 32 | top_p — 词汇筛选器 | 核采样原理，和 temperature 的配合关系 | Marp |
| 33 | top_k — 候选词数量 | 只从前 K 个最可能的词里选，简化版筛选 | Marp |
| 34 | max_tokens — 回答长度上限 | 输入 + 输出不能超窗口，成本与长度的权衡 | Marp |
| 35 | 其他参数 | frequency_penalty / presence_penalty / stop / seed | Marp |
| 36-37 | 🔴 参数实验室 | 拖动滑块实时调 temperature / top_p，看输出变化 | HTML 交互 |
| 38 | GPT API 格式 | 请求示例 + 响应示例 + 工具调用（function calling） | Marp 代码 |
| 39 | Claude API 格式 | 请求示例 + 响应示例 + 工具调用（tool_use） | Marp 代码 |
| 40 | Gemini API 格式 | 请求示例 + 响应示例 + 工具调用 | Marp 代码 |
| 41 | 🔴 三大 API 对比 | 格式 / 工具调用 / 流式输出 / 多模态 并排对比 | HTML 交互 |
| 42 | 🔴 现场 Demo：curl 调用 | 终端演示 curl 调用 OpenAI / Claude / Gemini | 终端实操 |
| 43 | 🔴 现场 Demo：Python 调用 | SDK 方式调用，展示参数对输出的影响 | 终端实操 |

### 第四部分：微调 — 教大模型学你的业务（10 页 / 20 分钟）

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 44 | 为什么需要微调？ | 通用模型 = 应届毕业生，微调 = 岗前培训 | Marp 类比 |
| 45 | 微调 vs 提示词工程 vs RAG | 三种方案对比：成本、效果、适用场景 | Marp 表格 |
| 46 | 全量微调 | 改整个大脑，效果好但成本极高 | Marp |
| 47 | LoRA：记忆补丁 | 不改原始权重，加一层低秩适配器，配图解释 | Marp 图解 |
| 48 | QLoRA：量化 + LoRA | 4-bit 量化 + LoRA，消费级显卡也能跑 | Marp |
| 49 | 微调关键参数 | learning_rate / epochs / batch_size / rank / alpha | Marp 表格 |
| 50 | 数据集怎么准备？ | 格式要求、数据清洗、标注规范 | Marp |
| 51 | 案例：日志异常检测 | 用系统日志微调模型识别异常请求模式 | Marp |
| 52 | 案例：技术文档问答 | 用内部文档微调专属客服 / 运维助手 | Marp |
| 53 | 微调的坑 | 过拟合、灾难性遗忘、数据泄露风险 | Marp |

### 第五部分：AI Agent 与 OpenClaw 生态（15 页 / 30 分钟）

> 核心类比：**大模型 = 进程，OpenClaw = 操作系统**

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 54 | 什么是 Agent？ | LLM 单独 = 只会想不会做，Agent = 想 + 做 + 规划 | Marp |
| 55 | Agent 的组成 | LLM（大脑）+ 工具（手脚）+ 记忆（笔记）+ 规划（思考链） | Marp 图解 |
| 56 | Agent 怎么调用工具？ | Function Calling / Tool Use 的机制 | Marp 代码 |
| 57 | Agent 之间怎么通信？ | 不是纯 Markdown，是 JSON + 自然语言的混合协议 | Marp 代码 |
| 58 | 🔴 Agent 工作流动画 | 点击步骤，看 思考 → 规划 → 调工具 → 反馈 全过程 | HTML 动画 |
| 59 | MCP 是什么？ | Model Context Protocol = AI 世界的 USB 接口标准 | Marp 类比 |
| 60 | MCP 解决什么问题？ | 没有 MCP：每个工具单独对接；有 MCP：统一协议 | Marp 对比 |
| 61 | 🔴 MCP 架构动画 | Host → Client → Server → Tools/Resources 数据流可视化 | HTML 动画 |
| 62 | Skills 是什么？ | 可复用的能力插件，注册 → 发现 → 调用的流程 | Marp |
| 63 | OpenClaw：AI 的操作系统 | 它本身不是大模型，是调度和约束大模型的"壳" | Marp |
| 64 | OpenClaw 架构 | 进程管理 / 资源分配 / 权限控制 — 对照 Linux 内核概念 | Marp 图解 |
| 65-66 | 🔴 OpenClaw 操作系统类比动画 | 左边 Linux 进程调度，右边 OpenClaw Agent 调度，动态对照 | HTML 动画 |
| 67 | OpenClaw 为什么不安全？ | 提示词注入 / 权限逃逸 / 工具链供应链攻击 / 数据泄露 | Marp |
| 68 | Agent 安全最佳实践 | 最小权限、沙箱隔离、输入校验、审计日志 | Marp |

### 第六部分：实战工具链（10 页 / 30 分钟）

> 全程动手演示

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 69 | 工具全景：你有哪些选择？ | Cursor / Claude CLI / Copilot / Windsurf / 其他 | Marp |
| 70 | Cursor 基础 vs 高阶 | Tab 补全（基础）vs Agent 模式 / 多文件编辑 / @ 引用（高阶） | Marp |
| 71-72 | 🔴 Cursor 高阶 Demo | 演示：Agent 模式重构代码、@ 引用文档、Rules 配置 | 现场演示 |
| 73 | Claude CLI 是什么？ | 终端里的 AI 工程师，不只是对话 | Marp |
| 74 | Claude CLI 核心功能 | Agent 模式 / 工具调用 / MCP / Hooks / 并行任务 | Marp |
| 75-76 | 🔴 Claude CLI Demo | 演示：用 CLI 完成一个完整功能开发流程 | 现场演示 |
| 77 | 怎么选工具？ | 决策树：简单补全 → Cursor，复杂任务 → Claude CLI，架构设计 → 对话 | Marp |
| 78 | 从"问 AI"到"让 AI 干活" | 工作流搭建思路：拆任务 → 写提示词 → 配工具 → 验收 | Marp |

### 第七部分：冷思考与行动计划（6 页 / 10 分钟）

| 序号 | 页面标题 | 内容要点 | 形式 |
|------|---------|---------|------|
| 79 | AI 的真实缺陷 | 幻觉 / 成本 / 隐私 / 不可解释 / 过度依赖风险 | Marp |
| 80 | 这些设计好吗？ | Transformer 的局限、自回归生成的天然缺陷、上下文窗口瓶颈 | Marp |
| 81 | AI + 业务系统机会 | 智能客服、异常检测、运维预测、代码辅助 | Marp |
| 82 | 团队 AI 能力路线图 | 第一月：工具上手 → 第二月：API 实践 → 第三月：业务场景落地 | Marp |
| 83 | 推荐资源 | 学习路径、文档链接、社区推荐 | Marp |
| 84 | Q&A | 开放提问环节 | Marp |

---

## HTML 交互页面清单

共 5 个独立 HTML 页面，嵌入幻灯片对应位置。

| 文件名 | 对应页码 | 交互效果 |
|--------|---------|---------|
| `temperature-playground.html` | 36-37 | 左侧：滑块控制 temperature / top_p / top_k；右侧：同一提示词的输出结果实时变化。用预设数据模拟，不需要真实 API |
| `agent-flow.html` | 58 | 步骤式动画：用户输入 → Agent 思考（思考链气泡）→ 选择工具 → 执行 → 返回结果。每步可点击展开细节 |
| `mcp-architecture.html` | 61 | MCP 四层架构图：Host / Client / Server / Tools。悬停显示数据流方向，点击组件展开协议细节 |
| `llm-api-compare.html` | 41 | 三栏并排：GPT / Claude / Gemini。可切换查看：请求格式 / 响应格式 / 工具调用 / 流式输出。代码高亮 |
| `openclaw-os-analogy.html` | 65-66 | 分屏动画。左侧：Linux 内核（进程调度、内存管理、系统调用）。右侧：OpenClaw（Agent 调度、上下文管理、工具调用）。同步动画展示对应关系 |

---

## 现场演示脚本清单

| 文件名 | 对应页码 | 演示内容 |
|--------|---------|---------|
| `01-curl-api-call.sh` | 42 | 用 curl 分别调用 OpenAI / Claude / Gemini API，展示请求格式差异 |
| `02-python-api.py` | 43 | 用 Python SDK 调用三大模型，演示 temperature 等参数对输出的影响 |
| `03-cursor-advanced.md` | 71-72 | Cursor 高阶操作步骤清单：Agent 模式、@ 引用、Rules、多文件编辑 |
| `04-claude-cli-demo.sh` | 75-76 | Claude CLI 实战：从 `claude` 启动到完成一个功能的全流程 |

---

## 培训整体规划

| 项目 | 内容 |
|------|------|
| 总页数 | 84 页 |
| 总时长 | 约 3 小时（含动手实操） |
| Marp 页面 | 74 页 |
| HTML 交互页 | 5 个 |
| 现场演示 | 4 个脚本 |
| 目标受众 | 软件 / 硬件 / 系统工程师（AI 小白） |
| 风格要求 | 通俗类比 + 精准技术点，不讲公式讲直觉 |

---

## 设计原则

1. **类比优先**：每个抽象概念都用团队熟悉的软件开发 / 操作系统概念类比
   - Transformer 注意力 → 快递分拣中心
   - API 调用 → 餐厅点菜请求/响应
   - temperature → 创造力旋钮
   - MCP → USB 接口标准
   - OpenClaw → 操作系统
   - 微调 → 岗前培训
   - Agent → 能想能做的员工

2. **代码真实**：所有 API 调用示例用真实 curl / Python，不用伪代码

3. **交互关键页**：最难理解或最重要的概念用 HTML 交互，让观众"玩"着学

4. **贯穿主线**："别把 AI 当工具，把 AI 当人" — 每个模块都回扣这条主线

---

## 待确认事项

- [ ] 84 页 / 3 小时的规模是否合适？
- [ ] 5 个 HTML 交互页的选择是否覆盖了最重要的点？
- [ ] 现场 Demo 网络环境：能调外部 API（OpenAI / Anthropic）还是只用本地 Ollama？
- [ ] Marp 主题风格偏好：深色科技风 / 简洁白底 / 公司品牌色？
- [ ] 内容顺序和侧重有无需要调整的地方？
