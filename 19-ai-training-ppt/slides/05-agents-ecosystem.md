---
marp: true
theme: ai-training
paginate: true
header: 'AI 全栈培训'
footer: '第五部分：Agent 生态'
---

<!-- _class: divider -->

# 第五部分：AI Agent 与 OpenClaw 生态

> **核心类比：大模型 = 进程，OpenClaw = 操作系统**

---

# 什么是 Agent？

**大模型本身 = 有脑子但没有手脚的顾问**

- 能思考、能分析、能给建议……但**不能动手干活**
- 不能读文件、不能跑代码、不能调接口、不能上网

**Agent = LLM + Tools + Memory + Planning**

- 不仅能想，还能**做**
- 能读写文件、执行代码、浏览网页、调用 API、自主决策

> **类比：** 咨询顾问 vs 全职员工
> 顾问给你一份报告，你自己去执行；员工直接帮你把活干了。

---

# Agent 的四大组件

```
┌─────────────────────────────────────────┐
│              🧠 LLM（大脑）              │
│     推理、理解、生成、判断、规划          │
├──────────┬──────────┬───────────────────┤
│ 🔧 Tools │ 📒 Memory│ 📋 Planning       │
│  （手脚） │ （笔记本）│ （思考链）         │
├──────────┼──────────┼───────────────────┤
│ 文件读写  │ 对话历史  │ 将复杂任务拆解     │
│ API 调用  │ 长期记忆  │ 为多个小步骤       │
│ 代码执行  │ 上下文窗口│ 逐步推进           │
│ 数据库查询│ 向量存储  │ 动态调整策略       │
└──────────┴──────────┴───────────────────┘
```

**每个组件缺一不可** — 缺 Tools 就是纸上谈兵，缺 Memory 就是金鱼脑袋，缺 Planning 就是无头苍蝇。

---

# Agent 怎么调用工具？

**核心机制：Function Calling / Tool Use**

```
用户提问 → LLM 判断需要工具 → 输出结构化 JSON → 系统执行工具
    ↑                                                    │
    └──── LLM 继续推理 ←── 工具结果返回给 LLM ──────────┘
```

**实际的 JSON 长这样：**

```json
{
  "type": "tool_use",
  "name": "read_file",
  "input": { "path": "/src/main.go" }
}
```

```json
{
  "type": "tool_result",
  "content": "package main\nimport \"fmt\"\nfunc main() { ... }"
}
```

> LLM **不直接执行**工具，它只输出"我想调用什么"，由外部系统代为执行。

---

# Agent 之间怎么通信？

**不是纯 Markdown！而是结构化 JSON + 自然语言的混合体**

| 通信类型 | 格式 | 用途 |
|---------|------|------|
| 工具调用 | JSON | `{"name": "search", "input": {...}}` |
| 推理过程 | 自然语言 | "我需要先查找相关文件……" |
| 行为约束 | System Prompt | 定义 Agent 的角色和边界 |
| 数据传递 | JSON / 文本 | Agent A 的输出 → Agent B 的输入 |

**多 Agent 协作示例：**

```
[Orchestrator Agent]
  "请 Code Agent 修复 bug #123"
      ↓
[Code Agent]
  调用 read_file → 分析代码 → 调用 write_file → 修复
  "修复完成，请 Test Agent 验证"
      ↓
[Test Agent]
  调用 run_tests → 收集结果 → "全部通过"
```

---

# Agent 工作流全过程

| 步骤 | Agent 行为 | 类比 |
|------|-----------|------|
| **1. 接收任务** | 用户说"帮我重构订单模块" | 领导分配任务 |
| **2. 分析理解** | 读取相关文件，理解现有代码 | 先看现状 |
| **3. 制定计划** | 拆解为 5 个子任务 | 写实施方案 |
| **4. 执行步骤 1** | 调用工具：读文件、改代码 | 动手干活 |
| **5. 观察结果** | 检查修改是否正确 | 自查 |
| **6. 调整计划** | 发现新问题，更新后续步骤 | 灵活应变 |
| **7. 继续执行** | 完成剩余步骤 | 持续推进 |
| **8. 返回结果** | 汇报完成情况 | 交付成果 |

> **关键洞察：** Agent 不是一次性回答，而是**循环执行**——思考→行动→观察→再思考

---

# MCP 是什么？

<!-- _class: highlight -->

## Model Context Protocol = AI 世界的 USB 接口

**Before MCP（旧世界）：**

每个工具都需要定制集成——就像早年的串口、并口、PS/2 接口，每种设备一个口。

**After MCP（新世界）：**

一个标准协议接入所有工具——就像 USB，一个接口通吃键盘、鼠标、U 盘、打印机。

| 特性 | 说明 |
|------|------|
| **发起者** | Anthropic（Claude 的公司） |
| **目标** | 统一 AI 工具接入标准 |
| **状态** | 正在成为行业标准，OpenAI 也已支持 |
| **本质** | JSON-RPC 2.0 协议 |

---

# MCP 解决什么问题？

<!-- _class: columns -->

<div class="col">

### 没有 MCP

**N 个模型 × M 个工具 = N×M 次集成**

```
Claude ──→ GitHub（定制）
Claude ──→ Slack（定制）
Claude ──→ DB（定制）
GPT   ──→ GitHub（再定制）
GPT   ──→ Slack（再定制）
GPT   ──→ DB（再定制）
```

3 个模型 × 3 个工具 = **9 次集成**

</div>

<div class="col">

### 有了 MCP

**N 个模型 + M 个工具 = N+M 次集成**

```
Claude ──┐
GPT   ──┤──→ MCP ──→ GitHub Server
Gemini──┘         ──→ Slack Server
                  ──→ DB Server
```

3 个模型 + 3 个工具 = **6 次集成**

规模越大，优势越明显！

</div>

---

# MCP 架构

```
┌──────────────────────────────────────────────────┐
│                   Host（宿主）                     │
│         Claude Desktop / Cursor / CLI             │
│  ┌────────────────────────────────────────────┐  │
│  │              Client（客户端）                │  │
│  │          协议处理、连接管理                   │  │
│  └──────────────┬─────────────────────────────┘  │
└─────────────────┼────────────────────────────────┘
                  │ JSON-RPC 2.0
┌─────────────────┼────────────────────────────────┐
│           Server（服务端 / 工具提供方）             │
│  ┌──────────┬──────────┬───────────────────────┐ │
│  │ Resources│  Tools   │       Prompts          │ │
│  │ 资源暴露  │ 工具注册  │    提示词模板           │ │
│  │ 文件/数据 │ 函数调用  │    可复用指令           │ │
│  └──────────┴──────────┴───────────────────────┘ │
└──────────────────────────────────────────────────┘
```

> **类比 Web 服务：** Host = 应用服务器，Client = HTTP 客户端，Server = 后端 API，Resources/Tools = 各种微服务

---

# Skills 是什么？

**Skills = 可复用的能力模块**

就像 Linux 的软件包/命令——安装一次，到处使用。

| 概念 | 说明 | 例子 |
|------|------|------|
| **注册** | 声明能力和参数 | `skill: "code-review"` |
| **发现** | 其他 Agent 可以搜索可用 Skills | "有没有代码审查的 Skill？" |
| **调用** | 传参执行，返回结构化结果 | `invoke("code-review", {files: [...]})` |

**Skill 的结构：**

```yaml
name: code-review
description: 审查代码质量和安全性
parameters:
  - files: string[]    # 要审查的文件
  - level: enum        # 审查级别：quick / thorough
returns:
  - issues: Issue[]    # 发现的问题列表
  - score: number      # 质量评分
```

> 任何 Agent 都可以调用任何 Skill，实现**能力的解耦和复用**。

---

<!-- _class: highlight -->

# OpenClaw：AI 的"操作系统"

**核心类比：大模型 = 进程，OpenClaw = 操作系统**

OpenClaw **不是**一个 shell 或简单的 CLI 工具——它更接近一个**完整的操作系统**，拥有自己的 init 系统、进程调度器、文件系统、包管理器和 cron。

**五大核心组件：**

| 组件 | 职责 | OS 类比 |
|------|------|---------|
| **Gateway（网关）** | 消息路由 + 会话管理 | init/systemd |
| **Brain（大脑）** | Agent 循环执行引擎 | CPU 调度器 |
| **Memory（记忆）** | 本地 SQLite 混合搜索 | 文件系统 + page cache |
| **Skills/Tools（技能）** | 工具调用 + 高级工作流 | 系统调用 + 软件包 |
| **Heartbeat（心跳）** | 定时任务 / 主动行为 | cron daemon |

> **Linux 内核不会帮你算 Excel，但它管理着算 Excel 的进程。**
> **OpenClaw 不会帮你写代码，但它管理着写代码的 Agent。**

---

# OpenClaw 五大组件详解（上）

**1. Gateway（网关）— init/systemd**

- 单进程 Node.js 长驻服务，轻量级：1 CPU、<1GB RAM
- 路由来自 **20+ 渠道**的消息：WhatsApp、Slack、Telegram、Discord、iMessage、Web UI、CLI
- **Lane Queue 系统**：每会话串行执行，防止竞态条件
- 绑定 localhost WebSocket，所有通信走本地

**2. Brain（Agent Runtime / 大脑）— CPU 调度器**

- 核心 Agent 循环：**组装上下文 → 调用 LLM → 执行工具 → 流式回复 → 持久化状态**
- 支持多模型：Claude、GPT-4、Gemini、DeepSeek、本地 Ollama 模型
- **Context Window Guard**：监控 token 数量，溢出前自动触发摘要压缩

**3. Memory（记忆系统）— 文件系统 + page cache**

- 本地优先，数据存储在 `~/.openclaw/memory/`，使用 SQLite
- **混合搜索**：BM25 关键词搜索 + 向量语义搜索（SQLite FTS5）
- **时间衰减评分**：近期记忆权重更高
- 启动文件（AGENTS.md、SOUL.md、TOOLS.md、IDENTITY.md、USER.md、MEMORY.md）每轮注入上下文

---

# OpenClaw 五大组件详解（下）

**4. Skills/Tools（技能/工具）— 系统调用 + 软件包**

- **两层架构**：
  - **Tools**（低级）：~25 个内置能力——文件读写、Shell 执行、浏览器自动化等
  - **Skills**（高级）：组合工作流——代码审查、会议摘要、自动部署等
- **ClawHub 市场**：800+ 已发布 Skills，类似 npm / apt
- **Semantic Snapshots**：将浏览器视觉页面转为结构化文本树，5MB 截图压缩至 <50KB

**5. Heartbeat（心跳）— cron daemon**

- 定时任务系统，让 Agent **主动**执行而非被动等待
- 可定时检查邮件、监控服务状态、运行周期性任务
- 用户离开时 Agent 仍在后台工作

---

# OpenClaw 架构对照表

| Linux 组件 | 职责 | OpenClaw 组件 | 职责 |
|-----------|------|-------------|------|
| **init/systemd** | 进程管理 + 消息总线 | **Gateway** | 消息路由 + 会话管理（Lane Queue） |
| **CPU 调度器** | 执行进程调度循环 | **Brain** | 执行 Agent 循环（上下文→LLM→工具→回复） |
| **文件系统 + page cache** | 数据存储 + 缓存 | **Memory** | SQLite 本地存储 + 混合搜索（BM25 + 向量） |
| **系统调用 + 软件包** | 内核接口 + 用户态程序 | **Skills/Tools** | 内置工具 + ClawHub 市场（800+ Skills） |
| **cron** | 定时任务调度 | **Heartbeat** | 主动行为 + 后台监控 |

> **关键区别：** OpenClaw 不只是一个 shell——它是一个完整的操作系统，
> 有自己的 init（Gateway）、调度器（Brain）、文件系统（Memory）、包管理器（ClawHub）和 cron（Heartbeat）。

---

# OpenClaw 为什么不安全？

**已被确认的安全事件（工程师必须了解）**

**1. ClawJacked CVE — WebSocket 劫持**
> 任何网站可静默劫持本地 OpenClaw 的 localhost WebSocket。**零用户交互**即可远程控制你的 Agent。

**2. 7 个已公开 CVE（CVE-2026-25593、CVE-2026-24763 等）**
> SSRF、认证绕过、路径遍历、远程代码执行——覆盖 OWASP Top 10 多个类别。

**3. 提示词注入（Prompt Injection）**
> LLM 的根本性问题。攻击者在邮件/消息中嵌入恶意指令，可劫持 Agent 行为。
> 类似 SQL 注入，但目前**无根治方案**。

**4. ClawHub 供应链攻击**
> Snyk 发现 **1,467 个恶意载荷**，分布在 1,000+ Skills 中。
> Trend Micro 发现有 Skills 分发 **Atomic Stealer**（macOS 信息窃取木马）。
> 无代码签名、无安全审查、默认无沙箱。

**5. 行业评估**
> **Cisco** 明确称个人 AI Agent 如 OpenClaw 是"安全噩梦"。
> **Microsoft** 建议仅在完全隔离的环境中运行（专用虚拟机）。

---

# Agent 安全最佳实践

| 原则 | 说明 | 软件系统类比 |
|------|------|---------|
| **最小权限** | Agent 只授予完成任务所需的最小权限 | 普通用户不需要 root 权限 |
| **沙箱隔离** | Agent 在受限环境中运行，不影响主系统 | 测试环境和生产环境隔离 |
| **输入校验** | 所有用户输入经过过滤和验证 | API 参数必须校验合法性 |
| **审计日志** | 记录 Agent 的每一步操作 | 系统操作日志必须可追溯 |
| **人工兜底** | 关键操作必须人工确认 | 生产环境变更需要审批 |

<div class="callout">

**核心原则：** 像对待生产环境安全一样对待 AI Agent 安全。
不信任任何输入，记录所有操作，关键动作需人工审批。

</div>
