---
marp: true
theme: ai-training
paginate: true
header: 'AI 全栈培训'
footer: '第六部分：实战工具链'
---

<!-- _class: divider -->

# 第六部分：实战工具链

> **从今天起，让 AI 帮你干活**

---

# 工具全景（2026.03）

| 工具 | 定位 | 核心差异 | 费用 |
|------|------|---------|------|
| **Cursor** | AI IDE（最成熟） | 云端 Agent + Automations + 自有模型 | $20-200/月 |
| **Trae** | AI IDE（性价比） | 字节出品，免费 Claude/DeepSeek 算力 | 免费/$10 |
| **Kiro** | AI IDE（Spec-Driven） | Amazon 出品，先写规格再生成代码 | $0-200/月 |
| **Claude Code** | 终端 Agent | 纯 CLI，子 Agent + Hooks + Memory | 按 Token |
| **Windsurf** | AI IDE（Cognition AI） | Cascade + Memories + SWE-1.5 自有模型 | $15/月 |
| **Copilot** | 插件 + CLI + Agent | GitHub 生态，Copilot CLI GA | $0-39/月 |

> **它们不是竞争关系，而是互补的。**
> 不同场景用不同工具 — 详细对比见 `interactive/coding-tools-compare.html`。

---

# AI IDE vs 终端 Agent：两条路线

<div class="columns">
<div class="col">

### IDE 路线（Cursor / Trae / Kiro）

- 图形界面，所见即所得
- Tab 补全 + 行内编辑 + 侧栏聊天
- @引用系统精准给上下文
- 适合：**日常编码、代码浏览、快速修改**

</div>
<div class="col">

### 终端路线（Claude Code）

- 纯命令行，SSH / CI/CD 可用
- 完整文件系统 + Shell 访问
- 并行子 Agent + Hooks + Memory
- 适合：**复杂工程、自动化、无 GUI 环境**

</div>
</div>

<div class="callout-blue">

**最佳实践：两条路线组合使用。** IDE 处理日常编码和代码浏览，终端 Agent 处理跨项目重构、CI/CD 集成和服务器端任务。

</div>

---

# Cursor：基础 vs 高阶

<!-- _class: columns -->

<div class="col">

### 基础用法（大多数人停在这里）

- **Tab 补全** — 写一半自动补全
- **行内聊天** — 选中代码问 AI
- **简单问答** — "这个函数干嘛的？"
- **单文件修改** — 改改当前文件

> 这些功能 **Copilot 也能做**，
> 你还没发挥 Cursor 的真正实力。

</div>

<div class="col">

### 高阶用法（今天要学的）

- **Agent Mode** — `Cmd+I` 全项目级操作
- **@引用** — `@file` `@folder` `@web` 精准给上下文
- **.cursorrules** — 让 AI 遵循你的代码规范
- **多文件编辑** — 一次指令改 10 个文件
- **上下文钉选** — 固定重要文件作为参考

> 这才是 **$20/月的价值所在**。

</div>

---

# Cursor 高阶技巧

**1. Agent Mode（`Cmd+I`）**
```
指令："重构整个订单模块，将回调改为 async/await"
Cursor：读取所有相关文件 → 制定修改计划 → 批量修改 → 保持一致性
```

**2. @引用系统**

| 引用 | 作用 | 例子 |
|------|------|------|
| `@file` | 指定文件作为上下文 | `@order.go 帮我加错误处理` |
| `@folder` | 整个目录作为上下文 | `@src/services 这些服务有什么共同问题？` |
| `@web` | 实时搜索网页 | `@web MCP 最新规范是什么？` |
| `@codebase` | 全项目搜索 | `@codebase 哪里调用了这个 API？` |

**3. `.cursorrules` 文件**
```
放在项目根目录，告诉 AI：错误必须返回统一格式、
函数不超过 50 行、必须写单元测试……
AI 会自动遵守这些约定。
```

---

<!-- _class: demo -->

# Cursor Demo 预告

### 稍后我们将现场演示：

**场景：** 使用 Cursor Agent 模式重构一个真实代码模块

| 步骤 | 演示内容 |
|------|---------|
| **1** | 打开项目，进入 Agent Mode |
| **2** | 用 `@folder` 引用整个模块目录 |
| **3** | 下达重构指令，观察 AI 的修改计划 |
| **4** | 查看多文件协同修改的效果 |
| **5** | 配置 `.cursorrules` 并验证 AI 遵守规范 |

<div class="callout-blue">

**动手环节：** 请确保你的电脑已安装 Cursor，
稍后跟着一起操作。

</div>

---

# Claude CLI 是什么？

**不只是终端里的聊天工具——它是一个 AI 软件工程师**

```bash
$ claude   # 启动一个 AI 工程师会话

> 帮我分析这个项目的架构，找出性能瓶颈
```

**Claude CLI 能做什么：**

| 能力 | 说明 | 对应的工具 |
|------|------|-----------|
| **读写文件** | 直接操作你的项目文件 | `Read` / `Edit` / `Write` |
| **执行命令** | 跑 shell 命令、编译、测试 | `Bash` |
| **搜索代码** | 在整个代码库中搜索 | `Grep` / `Glob` |
| **管理 Git** | 提交、分支、PR 全流程 | `Bash` (git/gh) |
| **调用 MCP** | 连接任何 MCP 工具服务器 | MCP 协议 |

> **关键区别：** ChatGPT 在云端对话，Claude CLI 在**你的项目目录里**工作，
> 拥有**完整的文件和终端访问权限**。

---

# Claude CLI 核心能力

**1. Agent Mode — 自主多步骤执行**
> 给一个任务，它自己拆解、执行、验证，全程自主。

**2. Tool Use — 文件操作、Bash 命令、搜索**
> 不是"告诉你怎么做"，而是**直接帮你做**。

**3. MCP 集成 — 连接任意 MCP 服务器**
> GitHub、数据库、内部工具……通过 MCP 全部打通。

**4. Hooks — 工具执行前后的钩子**
> 比如：每次编辑 `.ts` 文件后自动跑类型检查。

**5. 并行任务 — 多个 Agent 同时工作**
> 一个 Agent 改代码，另一个跑测试，并行不等待。

**6. /commands — 可扩展的技能系统**
> 自定义命令，比如 `/commit`、`/review-pr`，一键触发复杂流程。

---

# 四大工具核心差异

| 维度 | Cursor | Trae | Kiro | Claude Code |
|------|--------|------|------|------------|
| **界面** | GUI IDE | GUI IDE | GUI IDE | 终端 CLI |
| **模型** | 多家 + 自有 Composer | Claude + DeepSeek | 仅 Claude（Bedrock） | 仅 Claude 系列 |
| **Agent 模式** | Agent + 云端 Agent | Builder + SOLO | Spec-Driven | 子 Agent 并行 |
| **MCP** | MCP Apps（含 UI） | MCP 市场 | MCP + Kiro Powers | MCP Connector |
| **SSH / CI** | 不支持 | 不支持 | 不支持 | 原生支持 |
| **费用** | $20-200/月 | 免费/$10 | $0-200/月 | 按 API Token |
| **特色** | Automations + Bugbot | 免费算力 | 先规格后代码 | Hooks + Memory |

<div class="callout">

**一句话选型：** 功能全面选 Cursor，零成本入门选 Trae，需求驱动选 Kiro，终端/CI 选 Claude Code。最佳实践是 **IDE + CLI 组合**。详细对比动画见 `interactive/coding-tools-compare.html`。

</div>

---

<!-- _class: demo -->

# Claude CLI Demo 预告

### 稍后我们将现场演示：

**场景：** 从零完成一个功能开发的完整流程

```
$ claude
> 在项目中新增一个健康检查 API：
>   - 路径 /api/health
>   - 返回服务状态、数据库连接状态、版本号
>   - 写单元测试
>   - 提交到 Git
```

**你将看到 Claude CLI 自主完成：**

| 阶段 | AI 的行为 |
|------|----------|
| **分析** | 读取项目结构，理解技术栈 |
| **计划** | 列出实施步骤 |
| **编码** | 创建路由、处理函数、测试文件 |
| **测试** | 运行测试，确认通过 |
| **提交** | `git add` → `git commit`，附带规范的提交信息 |

---

# 从"问 AI"到"让 AI 干活"

**思维模式的转变：**

```
旧模式：你问 → AI 答 → 你自己做
新模式：你分任务 → AI 规划 → AI 执行 → 你验收
```

**高效使用 AI 的四步法：**

| 步骤 | 要点 | 反面教材 |
|------|------|---------|
| **1. 拆任务** | 把大需求拆成明确的小任务 | "帮我写个系统"（太模糊） |
| **2. 写提示词** | 给清晰指令 + 充足上下文 | "改一下那个 bug"（没上下文） |
| **3. 配工具** | 给 AI 正确的工具和权限 | 让 AI 写代码但不让它跑测试 |
| **4. 验收** | 审查结果，而非盲目信任 | AI 写啥就用啥，不检查 |

<div class="callout-blue">

**核心思路：** 不是"聊天聊得更快"让你提效 10 倍，
而是"**把活委派给 AI，你只做决策和验收**"。

</div>
