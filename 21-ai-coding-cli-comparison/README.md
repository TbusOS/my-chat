# AI Coding CLI 全景对比 (2026.03)

> 8 款主流 AI 编程 CLI 工具的功能、模型、定价、生态全方位对比。
> 所有数据经搜索验证，非猜测。

---

## 一、总览对比表

| 工具 | 开发商 | 开源 | 语言 | GitHub Stars | 首次发布 | 状态 |
|------|--------|------|------|-------------|---------|------|
| **Claude Code** | Anthropic | ❌ | TypeScript | N/A (闭源) | 2025 Q1 | GA |
| **Codex CLI** | OpenAI | ✅ Apache 2.0 | Rust | ~50K+ | 2025.04 | GA |
| **Gemini CLI** | Google | ✅ Apache 2.0 | TypeScript | ~96K+ | 2025.06 | Preview |
| **Copilot CLI** | GitHub/Microsoft | ❌ | - | N/A | 2026.02 GA | GA |
| **Aider** | Aider-AI (社区) | ✅ Apache 2.0 | Python | ~39K+ | 2023 | GA |
| **Kiro CLI** | AWS/Cognition | ❌ (原 Q Dev 开源) | - | N/A | 2025 | GA |
| **Cursor CLI** | Anysphere | ❌ | - | N/A | 2026.01 | Active |
| **OpenCode** | SST/AnomalyCo | ✅ | Go | ~120K+ | 2025 Q4 | Active |

---

## 二、内置工具/能力对比

### 2.1 文件操作

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| 读取文件 | ✅ Read | ✅ | ✅ ReadFile | ✅ | ✅ | ✅ | ✅ | ✅ |
| 写入文件 | ✅ Write | ✅ | ✅ WriteFile | ✅ | ✅ | ✅ | ✅ | ✅ |
| 编辑文件(精确替换) | ✅ Edit/MultiEdit | ✅ | ✅ Edit | ✅ | ✅ | ✅ | ✅ | ✅ |
| 批量读取多文件 | ⚠️ 需并行调用 | ❌ | ✅ ReadMany | ✅ | ✅ 自动 | ❌ | ❌ | ✅ |
| 文件搜索(Glob) | ✅ Glob | ✅ | ✅ FindFiles | ✅ | ✅ | ✅ | ✅ | ✅ |
| 内容搜索(Grep) | ✅ Grep (ripgrep) | ✅ | ✅ SearchText | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2.2 执行与系统

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| Shell 命令执行 | ✅ Bash | ✅ (沙箱) | ✅ Shell | ✅ | ✅ | ✅ | ✅ | ✅ |
| 沙箱隔离执行 | ⚠️ 可选 | ✅ 默认 | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 非交互/CI 模式 | ✅ `--print` | ✅ `exec` | ✅ `-p` | ✅ | ✅ `--message` | ✅ | ✅ | ✅ |

### 2.3 多媒体支持

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| **PDF 读取** | ✅ 原生支持 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **图片识别** | ✅ 原生多模态 | ✅ 截图输入 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Jupyter Notebook** | ✅ 读取+编辑 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **语音输入** | ✅ `/voice` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

### 2.4 网络与搜索

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| Web 搜索 | ✅ WebSearch | ✅ | ✅ GoogleSearch | ✅ | ❌ | ❌ | ❌ | ❌ |
| URL 抓取 | ✅ WebFetch | ❌ | ✅ WebFetch | ✅ | ✅ | ❌ | ❌ | ❌ |

### 2.5 Computer Use (计算机控制)

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| Computer Use (API级) | ✅ API 工具 (beta) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| CLI 内置桌面控制 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 浏览器控制 | ⚠️ 需 MCP | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 内置 browser | ❌ |
| 通过 MCP 扩展 | ✅ MCPControl | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

> **说明**: Claude 的 Computer Use 是 **API 级工具** (鼠标/键盘/截屏控制)，非 CLI 内置功能，可通过 MCP 接入。Cursor 有内置浏览器控制但不控制桌面。

### 2.6 Tool Use / Function Calling (工具调用架构)

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| 内置工具数 | **15 个** | ~8+ | **13 个** | ~10+ | ~5+ | ~5+ | ~10+ | ~8+ |
| MCP Client | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ (最多40工具) | ✅ |
| MCP Server | ✅ (双角色) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Deferred Tool Loading | ✅ 按需加载 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 工具权限控制 | ✅ Deny>Ask>Allow | ✅ 3级模式 | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| 自定义 Slash 命令 | ✅ Skills 系统 | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ Rules | ❌ |
| Plugin 市场 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 30+合作伙伴 | ❌ |

### 2.7 开发辅助

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| LSP 集成 | ✅ 原生 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 原生 |
| Git 自动提交 | ⚠️ 需指令 | ❌ | ❌ | ✅ | ✅ 自动 | ❌ | ❌ | ❌ |
| 代码自动 lint/fix | ⚠️ 通过 Hooks | ✅ Code Review | ❌ | ✅ | ✅ 自动 | ❌ | ❌ | ❌ |
| Mermaid 图渲染 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ ASCII 渲染 | ❌ |

---

## 三、智能体与编排能力

| 能力 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI | Aider | Kiro CLI | Cursor CLI | OpenCode |
|------|:-----------:|:---------:|:----------:|:-----------:|:-----:|:--------:|:----------:|:--------:|
| **子智能体(Sub-agents)** | ✅ 最多10并发 | ⚠️ 实验性 | ✅ Codebase Investigator | ✅ Explore/Task/Review/Plan | ❌ | ❌ | ✅ Subagents | ✅ 多会话 |
| **Agent Teams** | ✅ 多agent协作 | ❌ | ❌ | ✅ 后台委派 | ❌ | ❌ | ❌ | ❌ |
| **Plan Mode** | ✅ Shift+Tab | ❌ | ❌ | ✅ `/plan` | ❌ | ❌ | ✅ `/plan` | ❌ |
| **自主模式层级** | ✅ 权限系统 | ✅ 3级(Suggest/Auto Edit/Full Auto) | ✅ | ✅ Autopilot | ❌ | ✅ | ✅ 3种模式 | ✅ |
| **Hooks 系统** | ✅ 21种生命周期事件 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ 6种事件 (v1.7起) | ❌ |
| **Checkpoint/回滚** | ✅ Esc+Esc | ❌ | ❌ | ❌ | ✅ Git undo | ❌ | ❌ | ❌ |

---

## 四、MCP (Model Context Protocol) 支持

| 工具 | MCP Client | MCP Server | 说明 |
|------|:----------:|:----------:|------|
| **Claude Code** | ✅ | ✅ | 双角色：既是 Client 也是 Server |
| **Codex CLI** | ✅ | ❌ | 可连接第三方 MCP 服务器 |
| **Gemini CLI** | ✅ | ❌ | 支持本地和远程 MCP 服务器 |
| **Copilot CLI** | ✅ | ✅ | 内置 GitHub MCP Server |
| **Aider** | ❌ | ❌ | 不支持 MCP |
| **Kiro CLI** | ✅ | ❌ | 支持 MCP |
| **Cursor CLI** | ✅ | ❌ | `/mcp enable` 管理 |
| **OpenCode** | ✅ | ❌ | 支持 MCP |

---

## 五、持久化记忆系统

| 工具 | 项目配置文件 | 自动记忆 | 跨会话持久 | 说明 |
|------|:-----------:|:-------:|:---------:|------|
| **Claude Code** | ✅ `CLAUDE.md` | ✅ Auto-memory | ✅ | 项目级/用户级/组织级层级配置 |
| **Codex CLI** | ✅ `codex.md` | ❌ | ⚠️ | 项目级指令文件 |
| **Gemini CLI** | ✅ `GEMINI.md` | ✅ SaveMemory | ✅ | 层级配置 + save_memory 工具 |
| **Copilot CLI** | ✅ `.github/copilot-instructions.md` | ✅ Repo Memory | ✅ | 仓库记忆跨会话 |
| **Aider** | ✅ `.aider.conf.yml` | ❌ | ❌ | 配置文件但无自动记忆 |
| **Kiro CLI** | ✅ | ❌ | ❌ | - |
| **Cursor CLI** | ✅ `.cursor/rules` | ✅ | ✅ | 规则系统 |
| **OpenCode** | ✅ | ❌ | ❌ | - |

---

## 六、支持模型对比

| 工具 | 主力模型 | 多模型支持 | 本地模型 | 说明 |
|------|---------|:---------:|:-------:|------|
| **Claude Code** | Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 | ❌ 仅 Claude | ❌ | 1M 上下文(Opus 4.6) |
| **Codex CLI** | GPT-5.4, codex-mini-latest | ❌ 仅 OpenAI | ❌ | 不支持 GPT-4o |
| **Gemini CLI** | Gemini 3.1 Pro, 2.5 Pro | ❌ 仅 Gemini | ❌ | 1M 上下文(2.5 Pro) |
| **Copilot CLI** | Claude Opus 4.6, GPT-5.3, Gemini 3 Pro | ✅ 三家模型 | ❌ | 唯一跨厂商 CLI |
| **Aider** | 任意 LLM | ✅ 100+ 模型 | ✅ Ollama等 | 最灵活的模型支持 |
| **Kiro CLI** | Claude Sonnet 4.5, Haiku 4.5, DeepSeek | ✅ 多模型 | ❌ | AWS 基础设施 |
| **Cursor CLI** | Claude/GPT/Gemini/Composer 1.5 | ✅ 多模型 | ❌ | 有自研模型 Composer |
| **OpenCode** | 75+ 模型 | ✅ 全平台 | ✅ | 可用 Copilot 认证 |

---

## 七、定价对比

| 工具 | 免费层 | 入门价 | 专业价 | 计费方式 |
|------|:------:|-------|-------|---------|
| **Claude Code** | ❌ 需 Pro 订阅 | $20/月 (Pro) | $100-200/月 (Max) | 订阅制，含 token 额度 |
| **Codex CLI** | ✅ 工具免费 | $20/月 (ChatGPT Plus) | $200/月 (Pro) | 订阅制 or API 按量 |
| **Gemini CLI** | ✅ 1000次/天免费 | $0 | 按量付费 | 最慷慨免费层 |
| **Copilot CLI** | ✅ 有限额度 | $10/月 (Pro) | $39/月 (Pro+) | 订阅制 |
| **Aider** | ✅ 工具完全免费 | BYO API Key | BYO API Key | 纯 API 费用，无加价 |
| **Kiro CLI** | ✅ 50 credits | $20/月 | $200/月 (Power) | Credit 制 |
| **Cursor CLI** | ❌ 需订阅 | $20/月 (Pro) | $40/月 (Business) | 订阅制+超量按量 |
| **OpenCode** | ✅ 工具完全免费 | BYO API Key | BYO API Key | 纯 API 费用 |

---

## 八、独家特性 (各工具的杀手锏)

### Claude Code
- **Hooks 系统**: 21 种生命周期事件 (PreToolUse, PostToolUse, Stop 等)，支持命令/提示/智能体三种 handler
- **PDF 原生读取**: 唯一支持直接读取 PDF 的 CLI
- **Jupyter Notebook 读取+编辑**: 唯一完整支持 .ipynb 的 CLI
- **MCP 双角色**: 同时作为 MCP Client 和 Server
- **Agent Teams**: 多智能体协作，agent 间可互相通信
- **Checkpoint 回滚**: 每次编辑自动快照，Esc+Esc 秒级回滚
- **语音模式**: `/voice` push-to-talk

### Codex CLI
- **Rust 构建**: 性能优异
- **沙箱默认开启**: 安全性最高，命令执行默认隔离
- **三级自主模式**: Suggest → Auto Edit → Full Auto，渐进式信任
- **Apache 2.0 开源**: 完全开放

### Gemini CLI
- **1M token 上下文免费**: 最大的免费上下文窗口
- **Google Search 内置**: 原生 Google 搜索 grounding
- **免费层最慷慨**: 每天 1000 次免费请求，用 Gemini 2.5 Pro
- **Codebase Investigator**: 自主代码库分析子智能体
- **Apache 2.0 开源**: 完全开放

### Copilot CLI
- **GitHub 深度集成**: Issue、PR、Repo 对话式操作
- **跨厂商模型**: 唯一同时支持 Claude + GPT + Gemini 的 CLI
- **后台云委派**: `&` 前缀将任务交给云端 agent
- **仓库记忆**: 跨会话持久化项目约定

### Aider
- **模型自由**: 100+ 模型，包括本地模型，零厂商锁定
- **Git 原生**: 自动创建有意义的 commit message
- **自动 lint/test**: 编辑后自动跑 linter 和测试
- **语音编程**: voice-to-code
- **最成熟**: 这个品类的先驱，最大开源用户群

### Kiro CLI (原 Amazon Q Developer)
- **AWS 深度集成**: 资源查询、错误诊断、服务管理
- **代码转换**: 自动化语言升级 (如 Java 版本迁移)
- **企业合规**: SOC 2，企业分析仪表板

### Cursor CLI
- **自研模型 Composer 1.5**: 专为代码优化，成本低 50%
- **IDE 联动**: CLI ↔ Cursor IDE 无缝切换
- **Plan-to-Cloud**: CLI 制定计划后交给云端执行
- **Mermaid 图**: 终端内 ASCII 渲染 Mermaid 图

### OpenCode
- **LSP 原生集成**: 自动配置语言服务器 (Rust, Swift, TS, Python 等)
- **多会话并行**: 同一项目跑多个并行 agent
- **隐私优先**: 不存储任何代码或上下文数据
- **跨平台形态**: CLI + 桌面 App + IDE 扩展

---

## 九、各工具优缺点对比

### Claude Code (Anthropic)

| 优点 | 缺点 |
|------|------|
| SWE-bench 最高分 (72.7%)，复杂任务推理能力最强 | 闭源，不可审计代码 |
| 唯一原生支持 PDF 读取 + Jupyter Notebook 编辑 | 无免费层，最低 $20/月 |
| Hooks 系统 (21 种生命周期事件) 可深度定制工作流 | 仅支持 Claude 模型，厂商锁定 |
| Agent Teams 多智能体协作，子智能体最多 10 并发 | 不支持本地模型 |
| MCP 双角色 (同时作 Client 和 Server) | 高级功能 (1M 上下文) 需 Max 订阅 $100-200/月 |
| Checkpoint 回滚 + Plan Mode + 语音模式 | 上下文窗口超限时自动压缩可能丢失信息 |

### Codex CLI (OpenAI)

| 优点 | 缺点 |
|------|------|
| 开源 Apache 2.0，Rust 构建性能好 | 使用限制激进，Plus 用户 1-2 次就可能触发限流 |
| 沙箱默认开启，安全性最高 | 不支持 GPT-4o，模型选择受限 |
| 三级自主模式 (Suggest/Auto Edit/Full Auto) 渐进信任 | 无 PDF/Notebook 支持 |
| 有 CI/CD 模式 (`codex exec`) 和 GitHub Actions 集成 | 无 Hooks/生命周期扩展系统 |
| 可通过 ChatGPT 订阅或 API 两种方式计费 | 无 LSP 集成 |
| Cloud + Local 混合模式 | Token 消耗量大，新模型尤其明显 |

### Gemini CLI (Google)

| 优点 | 缺点 |
|------|------|
| **免费层最慷慨**: 1000 次/天，Gemini 2.5 Pro 1M 上下文 | 仍在 Preview 阶段，未正式 GA |
| 开源 Apache 2.0，96K+ GitHub Stars | 仅支持 Gemini 模型，无法用 Claude/GPT |
| Google Search 原生内置，搜索能力最强 | 无 PDF 原生读取 |
| Codebase Investigator 自主分析子智能体 | 无 Hooks/生命周期事件系统 |
| GEMINI.md + SaveMemory 跨会话记忆 | 无 Jupyter Notebook 支持 |
| 支持本地和远程 MCP 服务器 | 无 Checkpoint/回滚机制 |

### Copilot CLI (GitHub/Microsoft)

| 优点 | 缺点 |
|------|------|
| **唯一跨厂商模型**: Claude + GPT + Gemini 同时可用 | 闭源 |
| GitHub 深度集成 (Issue/PR/Repo 对话式操作) | 重度依赖 GitHub 生态 |
| 后台云委派 (`&` 前缀) 异步执行任务 | 免费层额度有限 |
| 仓库记忆跨会话持久化 | 无 Hooks 扩展系统 |
| 内置 Explore/Task/Review/Plan 专用智能体 | 无 PDF/Notebook 支持 |
| 入门价最低 ($10/月 Pro) | 无本地模型支持 |

### Aider

| 优点 | 缺点 |
|------|------|
| **100+ 模型零厂商锁定**，包括本地模型 (Ollama) | 无子智能体/多 agent 编排能力 |
| 完全免费工具，只付 API 费用无加价 | 无 MCP 支持 |
| Git 原生集成，自动创建有意义的 commit | 无 Web 搜索能力 |
| 自动 lint + 自动测试，编辑后立即验证 | 无 Plan Mode |
| 语音编程 (voice-to-code) | 无沙箱隔离 |
| 最成熟稳定，最大开源用户群 (39K+ stars) | 无跨会话自动记忆 |

### Kiro CLI (原 Amazon Q Developer)

| 优点 | 缺点 |
|------|------|
| AWS 生态深度集成 (资源查询、错误诊断) | 原开源版已停止维护，新版闭源 |
| 代码转换 (如 Java 版本自动升级) | 免费层仅 50 credits |
| 企业级合规 (SOC 2) | 不支持本地模型 |
| 支持多模型 (Claude + DeepSeek) | 无 PDF/Notebook/语音支持 |
| 25+ 编程语言支持 | 无 Hooks/Agent Teams |
| Credit 计费灵活 | Power 层 $200/月，成本较高 |

### Cursor CLI (Anysphere)

| 优点 | 缺点 |
|------|------|
| 与 Cursor IDE 无缝联动 | 闭源，强绑定 Cursor 生态 |
| 自研 Composer 1.5 模型，成本低 50% | 超量使用费用高 ($200-500/月常见) |
| Plan-to-Cloud 交接执行 | 无 PDF/Notebook 支持 |
| Mermaid 图终端 ASCII 渲染 | 无本地模型支持 |
| 多模型支持 (Claude/GPT/Gemini) | CLI 无 Auto 模式，每次请求消耗配额 |
| ✅ Hooks 系统 (6 种事件, v1.7 起) | Hooks 事件数少于 Claude Code (6 vs 21) |

### OpenCode (SST/AnomalyCo)

| 优点 | 缺点 |
|------|------|
| **LSP 原生集成** (自动配置 Rust/Swift/TS/Python 等) | 较新，生态还在成长 |
| 75+ 模型支持 + 本地模型 | 无 Web 搜索能力 |
| 隐私优先 (不存储代码或上下文) | 无 Hooks/生命周期系统 |
| 多会话并行 (同一项目多个 agent) | 无 PDF/Notebook 支持 |
| 跨形态 (CLI + 桌面 App + IDE 扩展) | 无语音模式 |
| 开源，120K+ GitHub Stars，增长最快 | 无自动记忆系统 |

---

## 十、SWE-bench 性能 (已知数据)

| 工具 | SWE-bench Verified | 说明 |
|------|:-----------------:|------|
| Claude Code | **72.7%** | 最高分 |
| Codex CLI (Cloud) | 69.1% | 略低 |
| Copilot CLI | - | 未公开 |
| Gemini CLI | - | 未公开 |
| Aider | ~50-60% | 取决于所用模型 |

---

## 十一、选型建议

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| 复杂多文件重构 | **Claude Code** | 最强推理 + Agent Teams + Hooks |
| 成本敏感/学生 | **Gemini CLI** | 1M 上下文免费，每天 1000 次 |
| 开源/隐私优先 | **Aider** 或 **OpenCode** | 完全开源，BYO API Key |
| GitHub 重度用户 | **Copilot CLI** | 深度 GitHub 集成 |
| AWS 生态 | **Kiro CLI** | AWS 服务原生集成 |
| 安全敏感 | **Codex CLI** | 沙箱默认开启 |
| 多模型灵活切换 | **Aider** | 100+ 模型零锁定 |
| IDE + CLI 联动 | **Cursor CLI** | 与 Cursor IDE 无缝衔接 |

---

## 十二、数据来源

所有信息均通过搜索引擎验证，主要来源：

- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [OpenAI Codex CLI 官方](https://developers.openai.com/codex/cli) | [GitHub](https://github.com/openai/codex)
- [Gemini CLI 官方](https://developers.google.com/gemini-code-assist/docs/gemini-cli) | [GitHub](https://github.com/google-gemini/gemini-cli)
- [GitHub Copilot CLI](https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/)
- [Aider 官网](https://aider.chat/) | [GitHub](https://github.com/Aider-AI/aider)
- [Kiro CLI](https://kiro.dev/cli/) | [原 Q Developer GitHub](https://github.com/aws/amazon-q-developer-cli)
- [Cursor CLI 文档](https://cursor.com/docs/cli/overview)
- [OpenCode 官网](https://opencode.ai/) | [GitHub](https://github.com/opencode-ai/opencode)
- [Composio 对比文章](https://composio.dev/content/claude-code-vs-openai-codex)
- [DataCamp 对比文章](https://www.datacamp.com/blog/codex-vs-claude-code)
- [Tembo: 15 Agents Compared](https://www.tembo.io/blog/coding-cli-tools-comparison)

---

*最后更新: 2026-03-17*
