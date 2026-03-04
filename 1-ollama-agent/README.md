# Ollama + Python 实现本地 Agent - 详细教程

## 目录

1. [什么是 LLM？为什么要本地运行？](#1-什么是-llm为什么要本地运行)
2. [硬件要求](#2-硬件要求)
3. [Ollama 安装](#3-ollama-安装)
4. [模型下载和使用](#4-模型下载和使用)
5. [Python API 详解](#5-python-api-详解)
6. [手把手实现各类 Agent](#6-手把手实现各类-agent)
7. [实战项目：天气预报 Agent](#7-实战项目天气预报-agent)
8. [常见问题](#8-常见问题)

---

## 1. 什么是 LLM？为什么要本地运行？

### 1.1 LLM 是什么？

LLM (Large Language Model) 即大语言模型，是一种基于深度学习的 AI 模型，能够：

- 理解和生成自然语言
- 回答问题、撰写文章、编写代码
- 进行翻译、总结、推理

你可以把 LLM 想象成一个超级知识库，它读过了互联网上的海量文本，学会了如何与人对话。

### 1.2 为什么要本地运行？

| 对比项 | 云端 API (如 ChatGPT) | 本地运行 (Ollama) |
|--------|----------------------|-------------------|
| 隐私 | 数据发送到第三方 | 数据完全本地 |
| 网络 | 需要联网 | 无需联网 |
| 费用 | 按调用付费 | 一次性投入 |
| 定制 | 无法微调 | 可自由微调 |
| 速度 | 依赖网络 | 本地更快 |
| 离线 | 不可用 | 完全离线可用 |

**本地运行的好处：**
1. **隐私安全**：敏感数据不离开你的电脑
2. **无网络依赖**：飞机上、地下室都能用
3. **无限使用**：不按 token 计费
4. **可定制**：可以微调成专属模型

### 1.3 Ollama 是什么？

Ollama 是一个让你在本地轻松运行大模型的工具：

- 一键安装
- 模型管理简单
- 支持多种开源模型
- 有 Python/JS API

---

## 2. 硬件要求

### 2.1 最低配置（能运行但慢）

| 配置项 | 要求 |
|--------|------|
| 内存 | 8GB RAM |
| 存储 | 20GB 硬盘 |
| 显卡 | 无（纯 CPU 运行） |
| 速度 | 慢，每秒几个字 |

### 2.2 推荐配置

| 配置项 | 推荐 |
|--------|------|
| 内存 | 16GB+ RAM |
| 存储 | 50GB+ SSD |
| 显卡 | NVIDIA 8GB+ 或 Apple Silicon |
| 速度 | 流畅，每秒几十个字 |

### 2.3 显存与模型对应

| 显存 | 能跑的模型 |
|------|-----------|
| 无 GPU | 3B 以下模型 |
| 8GB | 7B 模型 (量化版) |
| 16GB | 7B/8B 模型 |
| 24GB | 13B 模型 |
| 40GB+ | 70B 模型 |

**提示**：初学者推荐 7B 模型，资源要求低，效果也不错。

### 2.4 如何查看自己的配置？

```bash
# macOS
# 查看内存
top -l 1 | head -5

# 查看 CPU
sysctl -n machdep.cpu.brand_string

# Linux
free -h           # 内存
nvidia-smi        # NVIDIA 显卡

# Windows
# 右键"此电脑" -> 属性
```

---

## 3. Ollama 安装

### 3.1 macOS 安装（最简单）

**方法一：官网安装包**

1. 打开 https://ollama.com
2. 点击 Download
3. 下载 macOS 版本
4. 打开安装包，按提示安装

**方法二：命令行安装**

```bash
# 打开终端，运行：
curl -fsSL https://ollama.com/install.sh | sh
```

安装过程中可能需要输入密码（管理员权限）。

### 3.2 Linux 安装

```bash
# 安装
curl -fsSL https://ollama.com/install.sh | sh

# 验证安装
ollama --version

# 启动服务（通常自动启动）
ollama serve
```

**如果安装失败**：

```bash
# 1. 安装依赖
sudo apt update
sudo apt install curl build-essential

# 2. 手动下载
wget https://ollama.com/install.sh
chmod +x install.sh
./install.sh
```

### 3.3 Windows 安装

**方法一：官网下载**

1. 打开 https://ollama.com/download/windows
2. 下载安装包
3. 双击安装

**方法二：WSL2 (推荐，性能更好)**

```bash
# 1. 启用 WSL2（以管理员身份运行 PowerShell）
wsl --install

# 2. 进入 WSL
wsl

# 3. 安装 Ollama（同 Linux）
curl -fsSL https://ollama.com/install.sh | sh
```

### 3.4 验证安装

```bash
# 查看版本
ollama --version

# 启动服务（一般自动启动）
ollama serve

# 测试运行
ollama run qwen2.5 "你好"
```

---

## 4. 模型下载和使用

### 4.1 常用模型介绍

| 模型 | 大小 | 特点 | 推荐场景 |
|------|------|------|----------|
| **qwen2.5** | 3B/7B/14B | 中文能力最强 | 中文项目首选 |
| **llama3** | 8B | 英文能力强 | 英文对话 |
| **mistral** | 7B | 欧洲模型，推理快 | 通用场景 |
| **phi3** | 3.8B | 轻量快速 | 低配电脑 |
| **deepseek-coder** | 6.7B | 编程能力强 | 代码助手 |
| **gemma** | 2B/7B | Google 出品 | 轻量场景 |

**初学者推荐**：先试 `qwen2.5:7b`，中文好，效果也不错。

### 4.2 下载模型

```bash
# 查看已下载的模型
ollama list

# 下载模型（推荐先试这个）
ollama pull qwen2.5

# 指定版本
ollama pull qwen2.5:7b
ollama pull qwen2.5:3b

# 下载其他模型
ollama pull llama3
ollama pull mistral
ollama pull phi3
```

**下载时间**：
- 7B 模型：约 4GB，首次下载可能需要 10-30 分钟（视网速）
- 3B 模型：约 2GB，下载更快

### 4.3 运行模型（交互式）

```bash
# 启动对话
ollama run qwen2.5

# 退出输入 /bye 或 Ctrl+D
```

交互界面示例：
```
>>> 你好
你好！有什么我可以帮你的吗？

>>> 给我讲个笑话
当然可以！...

>>> /bye
```

### 4.4 非交互式运行

```bash
# 直接提问（不进入交互模式）
ollama run qwen2.5 "什么是 Python？"

# 带参数运行
ollama run qwen2.5 --temp 0.5 --num 100 "解释一下机器学习"
```

---

## 5. Python API 详解

### 5.1 安装依赖

```bash
pip install ollama openai
```

### 5.2 基础调用

```python
import ollama

# 最简单的调用
response = ollama.chat(
    model='qwen2.5',
    messages=[
        {'role': 'user', 'content': '你好'}
    ]
)

# 打印回复
print(response['message']['content'])
```

**response 结构解析**：
```python
{
    'model': 'qwen2.5',
    'created_at': '2024-01-01T00:00:00.000000000Z',
    'message': {
        'role': 'assistant',
        'content': '你好！有什么我可以帮你的吗？'
    },
    'done': True,
    'total_duration': 1234567890,
    'load_duration': 123456789,
    'prompt_eval_count': 5,
    'eval_count': 20
}
```

### 5.3 完整参数说明

```python
import ollama

response = ollama.chat(
    model='qwen2.5',           # 模型名称（必填）
    messages=[                 # 对话历史（必填）
        {'role': 'system', 'content': '你是一个助手'},  # 系统提示
        {'role': 'user', 'content': '你好'},            # 用户问题
    ],
    stream=False,             # 是否流式输出
    options={                 # 生成参数（可选）
        'temperature': 0.7,    # 创造性：0-2，越高越随机
        'top_p': 0.9,         # 核采样：控制输出多样性
        'top_k': 40,          # 限制采样词汇量
        'num_predict': 256,   # 最大生成 token 数
        'stop': ['用户:', '---'],  # 停止词
        'repeat_penalty': 1.1, # 重复惩罚
    }
)
```

**参数详解**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| temperature | float | 0.8 | 创造性控制，0=确定性，2=最随机 |
| top_p | float | 0.9 | 核采样，值越小越保守 |
| top_k | int | 40 | 限制候选词数量 |
| num_predict | int | 128 | 最大生成长度 |
| repeat_penalty | float | 1.1 | 重复惩罚，>1 减少重复 |

### 5.4 流式输出

```python
import ollama

# 流式输出：逐字显示回复
print("助手: ", end="")
for chunk in ollama.chat(
    model='qwen2.5',
    messages=[{'role': 'user', 'content': '写一首诗'}],
    stream=True
):
    print(chunk['message']['content'], end='', flush=True)
print()  # 换行
```

### 5.5 多轮对话

```python
import ollama

# 构建对话历史
messages = [
    {'role': 'system', 'content': '你是一个Python专家'},
    {'role': 'user', 'content': 'Python怎么定义函数？'},
    {'role': 'assistant', 'content': '用 def 关键字...'},
    {'role': 'user', 'content': '那JavaScript呢？'},  # 第二轮
]

response = ollama.chat(
    model='qwen2.5',
    messages=messages
)

print(response['message']['content'])
```

### 5.6 同步/异步调用

```python
import ollama
import asyncio

# 同步调用
def chat_sync():
    response = ollama.chat(
        model='qwen2.5',
        messages=[{'role': 'user', 'content': '你好'}]
    )
    return response['message']['content']

# 异步调用
async def chat_async():
    response = await asyncio.to_thread(
        ollama.chat,
        model='qwen2.5',
        messages=[{'role': 'user', 'content': '你好'}]
    )
    return response['message']['content']

# 使用
result = chat_sync()
print(result)

# 异步使用
result = asyncio.run(chat_async())
print(result)
```

---

## 6. 手把手实现各类 Agent

### 6.1 简单对话 Agent

最基础的 Agent：记住对话历史，可以多轮对话。

```python
#!/usr/bin/env python3
"""
简单对话 Agent
功能：支持多轮对话、上下文记忆、系统提示词
"""

import ollama
from typing import List, Dict, Optional


class SimpleAgent:
    """简单的对话 Agent"""

    def __init__(
        self,
        model: str = "qwen2.5",
        system_prompt: str = "你是一个有帮助的AI助手。",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        初始化 Agent

        参数:
            model: 使用的模型名称
            system_prompt: 系统提示词，定义 Agent 的角色
            temperature: 创造性参数，0-2
            max_tokens: 最大生成 token 数
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.messages: List[Dict] = []

        # 初始化系统提示词
        if system_prompt:
            self.messages.append({
                'role': 'system',
                'content': system_prompt
            })

    def reset(self):
        """清空对话历史，保留系统提示词"""
        if self.system_prompt:
            self.messages = [{'role': 'system', 'content': self.system_prompt}]
        else:
            self.messages = []

    def chat(self, user_input: str) -> str:
        """
        发送对话，返回助手回复

        参数:
            user_input: 用户输入

        返回:
            助手的回复内容
        """
        # 1. 添加用户消息
        self.messages.append({'role': 'user', 'content': user_input})

        # 2. 调用模型
        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            options={
                'temperature': self.temperature,
                'num_predict': self.max_tokens,
            }
        )

        # 3. 提取回复
        assistant_msg = response['message']['content']

        # 4. 添加助手消息到历史
        self.messages.append({'role': 'assistant', 'content': assistant_msg})

        return assistant_msg

    def stream_chat(self, user_input: str):
        """流式对话"""
        self.messages.append({'role': 'user', 'content': user_input})

        for chunk in ollama.chat(
            model=self.model,
            messages=self.messages,
            stream=True,
            options={
                'temperature': self.temperature,
                'num_predict': self.max_tokens,
            }
        ):
            yield chunk['message']['content']

        # 更新消息历史（简化版）
        self.messages.append({'role': 'user', 'content': user_input})


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 创建 Agent
    agent = SimpleAgent(
        model="qwen2.5",
        system_prompt="你是一个Python编程专家，用中文回答问题。回答时喜欢给出代码示例。"
    )

    print("=" * 50)
    print("简单对话 Agent 测试")
    print("=" * 50)

    # 第一轮对话
    print("\n用户: Python怎么定义函数？")
    response = agent.chat("Python怎么定义函数？")
    print(f"助手: {response}\n")

    # 第二轮对话（会自动记住上一轮上下文）
    print("用户: 那JavaScript呢？")
    response = agent.chat("那JavaScript呢？")
    print(f"助手: {response}\n")

    # 流式输出示例
    print("流式输出示例:")
    print("助手: ", end="")
    for chunk in agent.stream_chat("给我讲个笑话"):
        print(chunk, end='', flush=True)
    print("\n")

    # 清空对话
    agent.reset()
    print("对话已清空，重新开始...")
    print(f"消息历史: {agent.messages}")
```

### 6.2 工具调用 Agent

让 Agent 能够调用外部工具，如计算器、天气API等。

```python
#!/usr/bin/env python3
"""
工具调用 Agent
功能：让 Agent 能够调用外部工具（函数）
"""

import ollama
import json
from datetime import datetime
from typing import Dict, List, Any, Callable


class ToolAgent:
    """支持工具调用的 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        """
        初始化 Tool Agent

        参数:
            model: 使用的模型名称
        """
        self.model = model
        self.messages: List[Dict] = []
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable, description: str):
        """
        注册工具

        参数:
            name: 工具名称
            func: 工具函数
            description: 工具描述（让模型知道何时调用）
        """
        self.tools[name] = func

    def _build_tools_description(self) -> List[Dict]:
        """构建工具描述（供模型理解）"""
        tools_description = []
        for name, func in self.tools.items():
            tools_description.append({
                'type': 'function',
                'function': {
                    'name': name,
                    'description': func.__doc__ or '',
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            })
        return tools_description

    def get_time(self) -> str:
        """获取当前时间"""
        return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    def calculator(self, expression: str) -> str:
        """简单计算器"""
        try:
            # 注意：实际使用要用安全的计算方式，不要用 eval
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return str(result)
            else, "非法字符"
        except Exception as e:
            return f"计算错误: {e}"

    def weather(self, city: str) -> str:
        """模拟天气查询"""
        # 实际项目中这里调用真实天气 API
        weather_data = {
            "北京": "晴，15-25°C",
            "上海": "多云，18-27°C",
            "广州": "雨，22-30°C",
            "深圳": "晴，23-29°C",
        }
        return weather_data.get(city, f"未知{city}的天气情况")

    def chat(self, user_input: str, max_tool_calls: int = 3) -> str:
        """
        带工具调用的对话

        参数:
            user_input: 用户输入
            max_tool_calls: 最大工具调用次数

        返回:
            最终回复
        """
        # 1. 添加用户消息
        self.messages.append({'role': 'user', 'content': user_input})

        # 2. 构建工具描述
        tools_desc = self._build_tools_description()

        # 3. 第一次调用：让模型决定是否调用工具
        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            tools=tools_desc
        )

        # 4. 检查是否有工具调用
        tool_calls = response['message'].get('tool_calls', [])

        if not tool_calls:
            # 没有工具调用，直接返回回复
            final_msg = response['message']['content']
            self.messages.append({'role': 'assistant', 'content': final_msg})
            return final_msg

        # 5. 处理工具调用
        for _ in range(max_tool_calls):
            if not tool_calls:
                break

            # 执行工具调用
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function'].get('arguments', {})

                if tool_name in self.tools:
                    try:
                        # 调用工具函数
                        if tool_args:
                            result = self.tools[tool_name](**tool_args)
                        else:
                            result = self.tools[tool_name]()

                        # 将工具结果返回给模型
                        self.messages.append({
                            'role': 'tool',
                            'name': tool_name,
                            'content': str(result)
                        })
                    except Exception as e:
                        self.messages.append({
                            'role': 'tool',
                            'name': tool_name,
                            'content': f"工具执行错误: {e}"
                        })

            # 6. 第二次调用：基于工具结果生成回复
            response = ollama.chat(
                model=self.model,
                messages=self.messages
            )

            # 检查是否还有工具调用
            tool_calls = response['message'].get('tool_calls', [])

        # 7. 返回最终回复
        final_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': final_msg})
        return final_msg


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 创建 Agent
    agent = ToolAgent("qwen2.5")

    # 注册工具
    agent.register_tool("get_time", agent.get_time, "获取当前时间")
    agent.register_tool("calculator", agent.calculator, "进行数学计算")
    agent.register_tool("weather", agent.weather, "查询天气")

    print("=" * 50)
    print("工具调用 Agent 测试")
    print("=" * 50)

    # 测试工具调用
    print("\n--- 测试时间查询 ---")
    response = agent.chat("现在几点了？")
    print(f"用户: 现在几点了？")
    print(f"助手: {response}")

    print("\n--- 测试计算 ---")
    response = agent.chat("123 * 456 等于多少？")
    print(f"用户: 123 * 456 等于多少？")
    print(f"助手: {response}")

    print("\n--- 测试天气 ---")
    response = agent.chat("北京今天天气怎么样？")
    print(f"用户: 北京今天天气怎么样？")
    print(f"助手: {response}")

    print("\n--- 测试普通对话 ---")
    response = agent.chat("你觉得人工智能会取代人类工作吗？")
    print(f"用户: 你觉得人工智能会取代人类工作吗？")
    print(f"助手: {response}")
```

### 6.3 RAG 检索增强 Agent

让 Agent 能在自己的知识库中检索答案。

```python
#!/usr/bin/env python3
"""
RAG 检索增强 Agent
功能：让 Agent 能够从自己的知识库中检索信息
"""

import ollama
from typing import List, Dict, Tuple
import re


class RAGAgent:
    """检索增强生成 Agent"""

    def __init__(self, model: str = "qwen2.5", top_k: int = 3):
        """
        初始化 RAG Agent

        参数:
            model: 使用的模型名称
            top_k: 检索返回的结果数量
        """
        self.model = model
        self.top_k = top_k
        self.knowledge_base: List[Dict] = []
        self.embeddings: List[List[float]] = []

    def add_knowledge(self, text: str, metadata: Dict = None):
        """
        添加知识到知识库

        参数:
            text: 知识文本
            metadata: 元数据（如标题、来源等）
        """
        self.knowledge_base.append({
            'text': text,
            'metadata': metadata or {}
        })

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 转小写，去除标点，分词
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()

    def _compute_embedding(self, text: str) -> List[float]:
        """
        简单的 embedding 计算
        实际项目中应该使用专门的 embedding 模型

        这里用一个简化版：基于词频的向量
        """
        words = self._tokenize(text)
        # 创建词袋模型
        word_set = set(words)

        # 简单编码
        embedding = []
        for i in range(256):  # 固定维度
            if i < len(word_set):
                embedding.append(hash(list(word_set)[i % len(word_set)]) % 100 / 100.0)
            else:
                embedding.append(0.0)

        return embedding

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def retrieve(self, query: str) -> List[Tuple[float, str]]:
        """
        检索相关知识

        参数:
            query: 查询文本

        返回:
            [(相似度, 文本), ...] 按相似度排序
        """
        if not self.knowledge_base:
            return []

        # 计算查询的 embedding
        query_embedding = self._compute_embedding(query)

        # 计算与每个知识点的相似度
        similarities = []
        for item in self.knowledge_base:
            # 实际应该用预训练 embedding 模型
            # 这里用简化的关键词匹配
            query_words = set(self._tokenize(query))
            text_words = set(self._tokenize(item['text']))

            # 计算交集
            overlap = query_words & text_words
            if overlap:
                score = len(overlap) / max(len(query_words), len(text_words))
            else:
                score = 0.0

            similarities.append((score, item['text']))

        # 排序并返回 top_k
        similarities.sort(reverse=True)
        return similarities[:self.top_k]

    def chat(self, user_input: str) -> str:
        """
        RAG 对话

        参数:
            user_input: 用户输入

        返回:
            助手的回复
        """
        # 1. 检索相关知识
        results = self.retrieve(user_input)

        # 2. 构建上下文
        if results:
            context_text = "\n\n".join([f"[{i+1}] {text}" for i, (_, text) in enumerate(results)])
            context_prompt = f"""基于以下知识库内容回答用户问题。如果知识库没有相关信息，请如实说明。

知识库：
{context_text}

用户问题：{user_input}

回答："""
        else:
            context_prompt = f"""用户问题：{user_input}

回答："""

        # 3. 调用模型
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': context_prompt}]
        )

        return response['message']['content']


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 创建 RAG Agent
    rag = RAGAgent("qwen2.5")

    # 添加知识
    print("添加知识到知识库...")

    # Python 相关知识
    rag.add_knowledge("Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python以其简洁的语法和强大的库支持著称。")
    rag.add_knowledge("Python的函数用def关键字定义，如：def hello(): print('Hello')")
    rag.add_knowledge("Python的列表推导式：[x**2 for x in range(10)] 可以快速生成列表。")
    rag.add_knowledge("Python的虚拟环境用python -m venv env创建，用source env/bin/activate激活。")

    # JavaScript 相关知识
    rag.add_knowledge("JavaScript是一种运行在浏览器中的脚本语言，也可以用于服务端开发(Node.js)。")
    rag.add_knowledge("JavaScript用function关键字或箭头函数定义：const add = (a, b) => a + b")
    rag.add_knowledge("JavaScript的Promise用于处理异步操作，如：fetch(url).then(r => r.json())")

    # Go 相关知识
    rag.add_knowledge("Go是Google开发的编程语言，以高性能和并发支持著称。")
    rag.add_knowledge("Go的函数用func关键字定义，如：func add(a, b int) int { return a + b }")
    rag.add_knowledge("Go的goroutine是轻量级线程，用go关键字启动：go func() {}")

    print("知识库大小:", len(rag.knowledge_base))

    print("\n" + "=" * 50)
    print("RAG Agent 测试")
    print("=" * 50)

    # 测试问答
    questions = [
        "Python是谁创建的？",
        "Python怎么定义函数？",
        "JavaScript的箭头函数怎么写？",
        "Go语言的goroutine是什么？",
        "今天天气怎么样？",  # 知识库没有的信息
    ]

    for q in questions:
        print(f"\n用户: {q}")
        response = rag.chat(q)
        print(f"助手: {response}")
```

### 6.4 多角色 Manager Agent

一个管理多个子 Agent 的主 Agent。

```python
#!/usr/bin/env python3
"""
多角色 Manager Agent
功能：一个主 Agent 管理多个专业子 Agent
"""

import ollama
from typing import List, Dict, Optional
from enum import Enum


class AgentRole(Enum):
    """Agent 角色"""
    GENERAL = "general"      # 通用助手
    CODER = "coder"         # 编程专家
    WRITER = "writer"       # 写作专家
    RESEARCHER = "researcher"  # 研究助手


class SubAgent:
    """子 Agent"""

    def __init__(self, role: str, system_prompt: str, model: str = "qwen2.5"):
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.messages: List[Dict] = [
            {'role': 'system', 'content': system_prompt}
        ]

    def chat(self, user_input: str) -> str:
        """子 Agent 对话"""
        self.messages.append({'role': 'user', 'content': user_input})

        response = ollama.chat(
            model=self.model,
            messages=self.messages
        )

        assistant_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': assistant_msg})

        return assistant_msg


class ManagerAgent:
    """管理多个子 Agent 的主 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        self.sub_agents: Dict[str, SubAgent] = {}
        self._init_sub_agents()

    def _init_sub_agents(self):
        """初始化子 Agents"""
        # 通用助手
        self.sub_agents['general'] = SubAgent(
            role='general',
            system_prompt='你是一个乐于助人的通用AI助手，用简洁清晰的语言回答各种问题。'
        )

        # 编程专家
        self.sub_agents['coder'] = SubAgent(
            role='coder',
            system_prompt="""你是一个专业的编程助手，擅长Python、JavaScript、Go、Java等语言。
回答要求：
1. 给出完整可运行的代码示例
2. 解释代码逻辑
3. 指出常见的坑和最佳实践
4. 用中文回答"""
        )

        # 写作专家
        self.sub_agents['writer'] = SubAgent(
            role='writer',
            system_prompt="""你是一个专业的写作助手，擅长各种文体的写作。
包括但不限于：
- 技术文档
- 商业文案
- 故事创作
- 邮件回复
回答要求：
1. 语言流畅、专业
2. 结构清晰
3. 用中文回答"""
        )

        # 研究助手
        self.sub_agents['researcher'] = SubAgent(
            role='researcher',
            system_prompt="""你是一个研究助手，擅长信息检索和分析。
可以帮你：
- 总结文章要点
- 整理信息
- 分析对比选项
- 制定计划
回答要求：
1. 信息准确
2. 结构化呈现
3. 用中文回答"""
        )

    def _determine_role(self, user_input: str) -> str:
        """根据用户输入确定应该使用哪个子 Agent"""
        # 构建角色选择提示
        prompt = f"""根据用户的问题，确定最适合的助手类型。

可选类型：
- general: 通用问题，不需要专业知识
- coder: 编程、代码相关问题
- writer: 写作、文案相关问题
- researcher: 研究、信息整理相关问题

用户问题：{user_input}

只需要返回类型名称，不要其他内容。"""

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        role = response['message']['content'].strip().lower()

        # 验证角色是否有效
        if role not in self.sub_agents:
            role = 'general'

        return role

    def chat(self, user_input: str) -> str:
        """主 Agent 对话"""
        # 1. 确定使用哪个子 Agent
        role = self._determine_role(user_input)

        # 2. 调用对应的子 Agent
        sub_agent = self.sub_agents[role]
        response = sub_agent.chat(user_input)

        return response


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 创建 Manager Agent
    manager = ManagerAgent("qwen2.5")

    print("=" * 50)
    print("Manager Agent 测试")
    print("=" * 50)

    # 测试不同类型的请求
    test_questions = [
        ("general", "今天天气怎么样？"),
        ("coder", "Python怎么实现快速排序？"),
        ("writer", "帮我写一封辞职信"),
        ("researcher", "对比一下 Python 和 JavaScript 的优缺点"),
    ]

    for expected_role, question in test_questions:
        print(f"\n[{expected_role}] 用户: {question}")
        response = manager.chat(question)
        print(f"助手: {response[:200]}..." if len(response) > 200 else f"助手: {response}")
```

---

## 7. 实战项目：天气预报 Agent

综合运用所学知识，实现一个完整的天气预报 Agent。

```python
#!/usr/bin/env python3
"""
实战项目：天气预报 Agent
功能：
1. 理解用户想查询天气
2. 提取城市名称
3. 调用天气 API（或模拟）
4. 返回格式化的天气信息
"""

import ollama
import re
from datetime import datetime
from typing import Optional, Dict


class WeatherAgent:
    """天气预报 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        self.messages = [
            {
                'role': 'system',
                'content': '''你是一个天气预报助手。用户会询问某个城市的天气情况。

你的职责：
1. 理解用户想要查询天气的意图
2. 提取城市名称
3. 以友好的方式返回天气信息

注意：
- 如果用户没有指定城市，可以反问
- 如果不确定具体城市，可以建议常见城市
- 保持回答简洁友好'''
            }
        ]

    def _extract_city(self, user_input: str) -> Optional[str]:
        """从用户输入中提取城市名称"""
        # 常见城市列表
        cities = [
            '北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '重庆',
            '武汉', '西安', '苏州', '天津', '长沙', '郑州', '济南', '青岛',
            '大连', '沈阳', '哈尔滨', '长春', '福州', '厦门', '南昌', '合肥',
            '昆明', '贵阳', '兰州', '银川', '西宁', '乌鲁木齐', '拉萨',
            '香港', '澳门', '台北', '东京', '首尔', '纽约', '伦敦', '巴黎'
        ]

        # 尝试匹配城市
        for city in cities:
            if city in user_input:
                return city

        # 用模型提取
        prompt = f'''从以下用户输入中提取城市名称。如果用户没有提到具体城市，返回"未知"。

用户输入：{user_input}

只需要返回城市名称，不需要其他内容。'''

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        city = response['message']['content'].strip()
        return city if city != '未知' else None

    def _get_weather(self, city: str) -> Dict:
        """获取天气信息（模拟）"""
        # 模拟天气数据
        weather_data = {
            '北京': {'weather': '晴', 'temp': '15-25°C', 'wind': '北风3-4级', 'aqi': '良'},
            '上海': {'weather': '多云', 'temp': '18-27°C', 'wind': '东风2-3级', 'aqi': '优'},
            '广州': {'weather': '雷阵雨', 'temp': '22-30°C', 'wind': '南风3-4级', 'aqi': '良'},
            '深圳': {'weather': '晴', 'temp': '23-29°C', 'wind': '南风2-3级', 'aqi': '优'},
            '杭州': {'weather': '阴', 'temp': '17-24°C', 'wind': '东北风2级', 'aqi': '良'},
            '成都': {'weather': '小雨', 'temp': '16-22°C', 'wind': '北风1-2级', 'aqi': '良'},
            '重庆': {'weather': '阴', 'temp': '19-26°C', 'wind': '西北风1级', 'aqi': '中'},
            '武汉': {'weather': '多云', 'temp': '18-27°C', 'wind': '东南风2级', 'aqi': '良'},
            '西安': {'weather': '晴', 'temp': '14-28°C', 'wind': '东北风2-3级', 'aqi': '良'},
            '南京': {'weather': '多云', 'temp': '16-25°C', 'wind': '东风2级', 'aqi': '优'},
        }

        # 尝试精确匹配
        if city in weather_data:
            return weather_data[city]

        # 模糊匹配
        for key in weather_data:
            if key[0] in city or city[0] in key:
                return weather_data[key]

        # 默认返回
        return {'weather': '未知', 'temp': '未知', 'wind': '未知', 'aqi': '未知'}

    def chat(self, user_input: str) -> str:
        """对话"""
        # 1. 添加用户消息
        self.messages.append({'role': 'user', 'content': user_input})

        # 2. 提取城市
        city = self._extract_city(user_input)

        if not city:
            # 无法提取城市，询问用户
            response = ollama.chat(
                model=self.model,
                messages=self.messages + [
                    {'role': 'assistant', 'content': '请问您想查询哪个城市的天气呢？'}
                ]
            )
            return response['message']['content']

        # 3. 获取天气信息
        weather = self._get_weather(city)

        # 4. 格式化天气回复
        weather_info = f"""
🌤️ {city}今日天气

天气状况：{weather['weather']}
温度：{weather['temp']}
风力：{weather['wind']}
空气质量：{weather['aqi']}

温馨提示：出行记得带伞哦！
"""

        # 5. 让模型生成自然回复
        prompt = f'''基于以下天气信息，用友好的语气回复用户。

天气信息：{weather_info}
用户问题：{user_input}

只需要返回回复内容，不需要重复天气信息。'''

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        assistant_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': assistant_msg})

        return assistant_msg


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 创建 Agent
    agent = WeatherAgent("qwen2.5")

    print("=" * 50)
    print("天气预报 Agent")
    print("=" * 50)

    # 测试各种问法
    test_questions = [
        "北京今天天气怎么样？",
        "我想查一下上海的天气",
        "广州天气如何？",
        "深圳明天会下雨吗？",
        "杭州天气",
    ]

    for q in test_questions:
        print(f"\n用户: {q}")
        response = agent.chat(q)
        print(f"助手: {response}")

    print("\n" + "=" * 50)
    print("交互模式（输入 quit 退出）")
    print("=" * 50)

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break
        if not user_input:
            continue

        response = agent.chat(user_input)
        print(f"助手: {response}")
```

---

## 8. 常见问题

### 8.1 安装问题

**Q: Ollama 安装失败**
```
A:
1. 检查网络
2. 尝试手动安装：wget https://ollama.com/install.sh
3. 检查权限：sudo ./install.sh
```

**Q: 模型下载太慢**
```
A:
1. 使用镜像源
2. 尝试更小的模型（如 phi3:3.8b）
3. 夜间下载（网络较空）
```

### 8.2 运行问题

**Q: 显存不足**
```
A:
1. 使用量化模型：ollama pull qwen2.5:7b-q4_K_M
2. 使用更小的模型：ollama pull phi3
3. 使用 CPU 模式
```

**Q: 速度太慢**
```
A:
1. 使用更快的模型
2. 减少 max_tokens 参数
3. 考虑升级硬件
```

### 8.3 API 问题

**Q: 连接错误**
```
A:
1. 确保 Ollama 服务正在运行：ollama serve
2. 检查端口：默认 11434
3. 重启服务
```

**Q: 模型回复太长**
```
A:
1. 减少 num_predict 参数
2. 添加 stop 参数
3. 降低 temperature
```

---

## 参考链接

- [Ollama 官网](https://ollama.com)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Ollama Python 库](https://github.com/ollama/ollama-python)
- [Model Library](https://ollama.com/library)
- [Ollama API 文档](https://github.com/ollama/ollama/blob/main/docs/api.md)
