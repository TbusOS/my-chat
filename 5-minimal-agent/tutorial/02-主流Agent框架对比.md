# 主流 Agent 框架对比

## 本章目标

对比主流 Agent 框架，帮助你选择合适的工具：
1. 框架概览
2. 核心差异
3. 选型建议

---

## 1. 框架概览

### 1.1 LangChain

```bash
pip install langchain langchain-community
```

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain_community.llms import Ollama

llm = Ollama(model="qwen2.5")

tools = [
    Tool(name="Calculator", func=lambda x: str(eval(x)),
         description="计算数学表达式")
]

agent = create_react_agent(llm, tools, prompt_template)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "123 * 456 = ?"})
```

**优点**：生态最大，文档最全，支持几乎所有 LLM
**缺点**：抽象层多，调试困难，包体积大

### 1.2 smolagents

```bash
pip install smolagents
```

```python
from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel

agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=HfApiModel()
)
result = agent.run("搜索最新的 AI 新闻")
```

**优点**：代码简洁，Hugging Face 官方维护
**缺点**：功能相对简单，社区较小

### 1.3 Pocket Flow

```bash
pip install pocketflow
```

```python
from pocketflow import Node, Flow

class ThinkNode(Node):
    def run(self, shared):
        # 调用 LLM 思考
        return "action"

class ActNode(Node):
    def run(self, shared):
        # 执行工具
        return "done"

flow = Flow(start=ThinkNode())
flow.run()
```

**优点**：极简（~100 行核心代码），易于理解和修改
**缺点**：需要自己实现很多功能

### 1.4 CrewAI

```bash
pip install crewai
```

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="研究员",
    goal="调查最新 AI 进展",
    backstory="你是一位资深 AI 研究员"
)

task = Task(description="调查 2024 年最重要的 AI 论文", agent=researcher)
crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

**优点**：多 Agent 协作，角色扮演
**缺点**：对简单任务过于复杂

---

## 2. 核心差异对比

| 特性 | LangChain | smolagents | Pocket Flow | CrewAI |
|------|-----------|------------|-------------|--------|
| 代码量 | 重量级 | 轻量 | 极简 | 中等 |
| 学习曲线 | 陡峭 | 平缓 | 最低 | 中等 |
| 工具生态 | 丰富 | 中等 | 需自建 | 中等 |
| 多 Agent | 支持 | 有限 | 需自建 | 原生 |
| 本地 LLM | 支持 | 支持 | 支持 | 支持 |
| 生产就绪 | 是 | 部分 | 否 | 部分 |
| 调试难度 | 高 | 低 | 低 | 中 |

---

## 3. 选型建议

| 场景 | 推荐 | 原因 |
|------|------|------|
| 学习 Agent 原理 | Pocket Flow / 自己写 | 代码透明，理解原理 |
| 快速原型 | smolagents | 简单直接 |
| 生产应用 | LangChain | 生态完善，社区大 |
| 多 Agent 协作 | CrewAI | 原生支持角色分工 |
| 完全掌控 | 自己写 | 0 依赖，100% 可控 |

---

## 4. 何时不需要框架？

如果你的需求只是：
- 调用 LLM API + 解析 JSON → 直接用 `requests`
- 单工具调用 → 50 行代码足够
- 简单对话机器人 → 直接用 Ollama Python 库

**框架带来的价值在于**：多工具编排、记忆管理、错误处理、可观测性。
如果不需要这些，不要引入框架。

---

## 5. 本章小结

- [x] 4 大主流框架对比
- [x] 核心差异分析
- [x] 选型建议
- [x] 何时不需要框架
