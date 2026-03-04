# 第三章：Python API 详解

## 本章目标

学完本章后，你将能够：
1. 安装 Python 依赖
2. 使用 Python 调用 Ollama API
3. 理解各个参数的作用
4. 实现多轮对话

---

## 3.1 环境准备

### 3.1.1 安装依赖

```bash
pip install ollama openai
```

- **ollama**: Ollama 官方 Python 库
- **openai**: OpenAI 兼容 API（Ollama 也支持）

### 3.1.2 验证安装

```python
import ollama
print(ollama.__version__)
```

### 3.1.3 确保 Ollama 服务运行

```bash
# 启动 Ollama 服务
ollama serve

# 验证服务运行
curl http://localhost:11434
```

---

## 3.2 基础调用

### 3.2.1 最简单的调用

```python
import ollama

# 最简单的调用
response = ollama.chat(
    model='qwen2.5',
    messages=[
        {'role': 'user', 'content': '你好'}
    ]
)

print(response['message']['content'])
```

### 3.2.2 response 结构解析

```python
response = {
    'model': 'qwen2.5',                    # 使用的模型
    'created_at': '2024-01-01T00:00:00.000000000Z',  # 创建时间
    'message': {
        'role': 'assistant',                # 回复角色
        'content': '你好！有什么我可以帮你的吗？'  # 回复内容
    },
    'done': True,                          # 是否完成
    'total_duration': 1234567890,          # 总耗时（纳秒）
    'load_duration': 123456789,            # 模型加载时间
    'prompt_eval_count': 5,                # 输入 token 数
    'eval_count': 20                       # 输出 token 数
}
```

---

## 3.3 完整参数详解

### 3.3.1 chat() 完整参数

```python
import ollama

response = ollama.chat(
    model='qwen2.5',              # 【必填】模型名称

    messages=[                     # 【必填】对话历史
        {'role': 'system', 'content': '你是一个助手'},
        {'role': 'user', 'content': '你好'},
    ],

    stream=False,                 # 【可选】是否流式输出，默认 False

    options={                     # 【可选】生成参数
        'temperature': 0.7,       # 创造性，0-2
        'top_p': 0.9,            # 核采样，0-1
        'top_k': 40,             # 候选词数量
        'num_predict': 256,      # 最大生成 token 数
        'stop': ['用户:', '---'], # 停止词
        'repeat_penalty': 1.1,    # 重复惩罚
    },

    format='json',              # 【可选】输出格式（json）

    templates=None,             # 【可选】提示词模板

    context=None,               # 【可选】上下文 token

    keep_alive=None,            # 【可选】保持模型加载时间
)
```

### 3.3.2 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | 必填 | 模型名称 |
| `messages` | array | 必填 | 对话历史 |
| `stream` | boolean | false | 流式输出 |
| `temperature` | float | 0.8 | 创造性，0=确定性，2=最随机 |
| `top_p` | float | 0.9 | 核采样，控制多样性 |
| `top_k` | int | 40 | 限制候选词数量 |
| `num_predict` | int | 128 | 最大生成长度 |
| `repeat_penalty` | float | 1.1 | 重复惩罚 |
| `stop` | array | - | 停止词列表 |
| `format` | string | - | 输出格式（如 json） |

### 3.3.3 参数使用示例

```python
import ollama

# 精确回答场景
response = ollama.chat(
    model='qwen2.5',
    messages=[{'role': 'user', 'content': '1+1等于多少？'}],
    options={
        'temperature': 0.1,      # 低创造性，保证准确
        'num_predict': 50,       # 简短回答
    }
)

# 创意写作场景
response = ollama.chat(
    model='qwen2.5',
    messages=[{'role': 'user', 'content': '写一个故事开头'}],
    options={
        'temperature': 1.2,      # 高创造性
        'top_p': 0.95,          # 更多样性
        'num_predict': 500,     # 较长输出
    }
)

# 编程场景
response = ollama.chat(
    model='qwen2.5',
    messages=[{'role': 'user', 'content': '写一个快速排序'}],
    options={
        'temperature': 0.2,      # 低创造性，保证代码正确
        'repeat_penalty': 1.2,   # 减少重复
    }
)
```

---

## 3.4 流式输出

### 3.4.1 流式调用

```python
import ollama

# 流式输出：逐字显示回复
for chunk in ollama.chat(
    model='qwen2.5',
    messages=[{'role': 'user', 'content': '讲一个故事'}],
    stream=True
):
    print(chunk['message']['content'], end='', flush=True)
print()  # 换行
```

### 3.4.2 流式响应结构

```python
# 每次迭代返回的内容
chunk = {
    'model': 'qwen2.5',
    'message': {
        'role': 'assistant',
        'content': '你'  # 第一个字
    },
    'done': False  # 还未完成
}

# 最后一次迭代
chunk = {
    ...
    'done': True,  # 完成
    'total_duration': 1234567890,
    'eval_count': 20
}
```

### 3.4.2 实际应用示例

```python
import ollama
import sys

def stream_chat(prompt):
    """流式聊天函数"""
    print("助手: ", end="")

    full_response = ""
    for chunk in ollama.chat(
        model='qwen2.5',
        messages=[{'role': 'user', 'content': prompt}],
        stream=True
    ):
        content = chunk['message']['content']
        print(content, end="", flush=True)
        full_response += content

    print()  # 换行
    return full_response

# 使用
stream_chat("给我讲个笑话")
```

---

## 3.5 多轮对话

### 3.5.1 对话历史管理

```python
import ollama

# 构建对话历史
messages = [
    {'role': 'system', 'content': '你是一个Python专家'},
    {'role': 'user', 'content': 'Python怎么定义函数？'},
    {'role': 'assistant', 'content': '用def关键字定义...'},
    {'role': 'user', 'content': '那JavaScript呢？'},  # 第二轮
]

response = ollama.chat(
    model='qwen2.5',
    messages=messages
)

print(response['message']['content'])
```

### 3.5.2 完整多轮对话示例

```python
import ollama

class ChatBot:
    """简单的聊天机器人"""

    def __init__(self, model='qwen2.5'):
        self.model = model
        self.messages = []

    def reset(self):
        """重置对话"""
        self.messages = []

    def chat(self, user_input):
        """发送消息"""
        # 添加用户消息
        self.messages.append({
            'role': 'user',
            'content': user_input
        })

        # 调用 API
        response = ollama.chat(
            model=self.model,
            messages=self.messages
        )

        # 添加助手回复
        assistant_msg = response['message']['content']
        self.messages.append({
            'role': 'assistant',
            'content': assistant_msg
        })

        return assistant_msg

# 使用
bot = ChatBot()

print(bot.chat("你好"))
print(bot.chat("Python怎么定义函数？"))
print(bot.chat("谢谢"))
```

---

## 3.6 其他 API

### 3.6.1 generate() - 纯生成

```python
import ollama

# 不需要对话历史，直接生成
response = ollama.generate(
    model='qwen2.5',
    prompt='写一首关于春天的诗',
    options={
        'temperature': 0.8,
        'num_predict': 200,
    }
)

print(response['response'])
```

### 3.6.2 embeddings() - 向量嵌入

```python
import ollama

# 获取文本的向量表示
response = ollama.embeddings(
    model='nomic-embed-text',
    prompt='Python是一门编程语言'
)

embedding = response['embedding']
print(f"向量维度: {len(embedding)}")
```

### 3.6.3 list() - 列出模型

```python
import ollama

# 列出所有可用模型
models = ollama.list()

for model in models['models']:
    print(f"{model['name']} - {model['size']} bytes")
```

### 3.6.4 show() - 模型信息

```python
import ollama

# 查看模型详情
info = ollama.show('qwen2.5')

print(f"模型名称: {info['name']}")
print(f"参数大小: {info['parameters']}")
print(f"量化版本: {info['quantization']}")
```

---

## 3.7 错误处理

### 3.7.1 常见错误

```python
import ollama
from ollama import ResponseError

try:
    response = ollama.chat(
        model='qwen2.5',
        messages=[{'role': 'user', 'content': '你好'}]
    )
    print(response['message']['content'])

except ResponseError as e:
    print(f"API 错误: {e}")

except Exception as e:
    print(f"其他错误: {e}")
```

### 3.7.2 超时处理

```python
import ollama
import signal
from functools import wraps
import time

def timeout_handler(signum, frame):
    raise TimeoutError("请求超时")

def with_timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator

@with_timeout(30)  # 30秒超时
def chat_with_timeout():
    return ollama.chat(
        model='qwen2.5',
        messages=[{'role': 'user', 'content': '你好'}]
    )

try:
    response = chat_with_timeout()
    print(response['message']['content'])
except TimeoutError:
    print("请求超时了")
```

---

## 3.8 异步调用

### 3.8.1 基础异步

```python
import asyncio
import ollama

async def async_chat(prompt):
    # 使用 to_thread 在事件循环中运行同步函数
    response = await asyncio.to_thread(
        ollama.chat,
        model='qwen2.5',
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['message']['content']

async def main():
    result = await async_chat("你好")
    print(result)

asyncio.run(main())
```

### 3.8.2 并发多个请求

```python
import asyncio
import ollama

async def chat_once(prompt):
    return await asyncio.to_thread(
        ollama.chat,
        model='qwen2.5',
        messages=[{'role': 'user', 'content': prompt}]
    )

async def main():
    # 并发三个请求
    tasks = [
        chat_once("你好"),
        chat_once("今天天气怎么样"),
        chat_once("Python是什么")
    ]

    results = await asyncio.gather(*tasks)

    for prompt, response in zip(
        ["你好", "今天天气怎么样", "Python是什么"],
        results
    ):
        print(f"Q: {prompt}")
        print(f"A: {response['message']['content']}\n")

asyncio.run(main())
```

---

## 3.9 本章小结

本章我们学习了：

- ✅ Python 环境准备
- ✅ 基础 API 调用
- ✅ 完整参数详解
- ✅ 流式输出
- ✅ 多轮对话
- ✅ 其他 API（generate, embeddings）
- ✅ 错误处理
- ✅ 异步调用

---

## 3.10 练习

1. 用 Python 实现一个简单的聊天程序
2. 尝试流式输出
3. 实现一个带错误处理的聊天机器人

---

## 下章预告

接下来的章节我们将学习技术原理，包括：
- LLM 基础概念
- Transformer 简介

然后是手把手实战：
- 天气 Agent
- 工具 Agent
- RAG Agent
