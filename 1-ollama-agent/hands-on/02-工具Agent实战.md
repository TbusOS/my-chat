# 第二章：工具 Agent 实战

## 本章目标

手把手实现一个工具调用 Agent，让 LLM 能够：
1. 注册和使用自定义工具
2. 理解何时需要调用工具
3. 处理工具返回的结果

---

## 2.1 什么是工具调用 Agent？

### 2.1.1 普通 Agent vs 工具 Agent

**普通 Agent**：只能根据训练知识回答，可能过时或出错。

```
用户: "现在几点了？"
普通 Agent: "现在是下午3点左右"  ← 可能不准确
```

**工具 Agent**：可以调用外部工具获取实时信息。

```
用户: "现在几点了？"
工具 Agent: → 调用 get_time() → 返回 "14:30" → "现在是下午2点30分"
```

### 2.1.2 工具调用流程

```
用户输入 → LLM判断需要工具 → 执行工具 → 返回结果 → LLM生成回复
```

### 2.1.3 常见工具类型

| 工具类型 | 示例 |
|----------|------|
| 获取时间 | get_time() |
| 计算器 | calculator() |
| 天气查询 | get_weather() |
| 搜索 | web_search() |
| 数据库 | query_db() |
| API调用 | call_api() |

---

## 2.2 工具 Agent 架构

### 2.2.1 核心组件

```
ToolAgent
├── register_tool()    # 注册工具
├── tools{}           # 工具注册表
├── _execute_tool()   # 执行工具
└── chat()           # 对话主流程
```

### 2.2.2 工具定义格式

```python
# 工具定义示例
{
    "name": "get_weather",
    "description": "获取指定城市的天气信息",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称"
            }
        },
        "required": ["city"]
    }
}
```

---

## 2.3 完整代码实现

### 2.3.1 工具 Agent 主程序

```python
#!/usr/bin/env python3
"""
工具调用 Agent
功能：让 LLM 能够调用外部工具（函数）
"""

import ollama
import json
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional


class ToolAgent:
    """支持工具调用的 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        """
        初始化 Tool Agent

        Args:
            model: 使用的模型
        """
        self.model = model
        self.messages: List[Dict] = []
        self.tools: Dict[str, Callable] = {}
        self.tools_schema: List[Dict] = []

    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict = None
    ):
        """
        注册工具

        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述（让模型知道何时调用）
            parameters: 参数定义
        """
        self.tools[name] = func

        # 构建工具 schema
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters or {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        self.tools_schema.append(schema)

    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            return f"错误：工具 {tool_name} 不存在"

        try:
            func = self.tools[tool_name]

            # 调用函数
            if arguments:
                result = func(**arguments)
            else:
                result = func()

            return str(result)

        except Exception as e:
            return f"工具执行错误: {str(e)}"

    def chat(self, user_input: str, max_tool_calls: int = 3) -> str:
        """
        带工具调用的对话

        Args:
            user_input: 用户输入
            max_tool_calls: 最大工具调用次数

        Returns:
            最终回复
        """
        # 1. 添加用户消息
        self.messages.append({'role': 'user', 'content': user_input})

        # 2. 第一次调用：让模型决定是否调用工具
        response = ollama.chat(
            model=self.model,
            messages=self.messages,
            tools=self.tools_schema
        )

        # 3. 检查是否有工具调用
        tool_calls = response['message'].get('tool_calls', [])

        if not tool_calls:
            # 没有工具调用，直接返回回复
            final_msg = response['message']['content']
            self.messages.append({'role': 'assistant', 'content': final_msg})
            return final_msg

        # 4. 处理工具调用
        for _ in range(max_tool_calls):
            if not tool_calls:
                break

            # 执行所有工具调用
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function'].get('arguments', {})

                # 执行工具
                result = self._execute_tool(tool_name, tool_args)

                # 将工具结果返回给模型
                self.messages.append({
                    'role': 'tool',
                    'name': tool_name,
                    'content': result
                })

            # 5. 第二次调用：基于工具结果生成回复
            response = ollama.chat(
                model=self.model,
                messages=self.messages
            )

            # 检查是否还有工具调用
            tool_calls = response['message'].get('tool_calls', [])

        # 6. 返回最终回复
        final_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': final_msg})
        return final_msg


# ============== 内置工具 ==============

def get_time() -> str:
    """获取当前时间"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


def get_date() -> str:
    """获取当前日期"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日")


def calculator(expression: str) -> str:
    """数学计算器

    Args:
        expression: 数学表达式，如 "2+3*4"
    """
    try:
        # 安全检查：只允许数字和运算符
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含非法字符"

        result = eval(expression)
        return str(result)

    except Exception as e:
        return f"计算错误: {str(e)}"


def get_weather(city: str) -> str:
    """获取城市天气

    Args:
        city: 城市名称
    """
    weather_data = {
        "北京": "晴，15-25°C，良",
        "上海": "多云，18-27°C，优",
        "广州": "雷阵雨，22-30°C，良",
        "深圳": "晴，23-29°C，优",
        "杭州": "阴，17-24°C，良",
        "成都": "小雨，16-22°C，良",
        "重庆": "阴，19-26°C，中",
        "武汉": "多云，18-27°C，良",
    }

    if city in weather_data:
        return f"{city}：{weather_data[city]}"
    return f"未知{city}的天气情况"


def search_web(query: str) -> str:
    """模拟网页搜索

    Args:
        query: 搜索关键词
    """
    # 实际项目中应该调用真实搜索 API
    results = [
        f"关于「{query}」的第一条搜索结果...",
        f"关于「{query}」的第二条搜索结果...",
        f"关于「{query}」的第三条搜索结果...",
    ]
    return "\n".join(results)


def send_email(to: str, subject: str, content: str) -> str:
    """发送邮件（模拟）

    Args:
        to: 收件人
        subject: 主题
        content: 内容
    """
    # 实际项目中应该调用邮件 API
    return f"邮件已发送！\n收件人：{to}\n主题：{subject}"


# ============== 使用示例 ==============

def main():
    # 创建 Agent
    agent = ToolAgent("qwen2.5")

    # 注册工具
    agent.register_tool(
        name="get_time",
        func=get_time,
        description="获取当前时间",
    )

    agent.register_tool(
        name="get_date",
        func=get_date,
        description="获取当前日期",
    )

    agent.register_tool(
        name="calculator",
        func=calculator,
        description="进行数学计算",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2+3*4'"
                }
            },
            "required": ["expression"]
        }
    )

    agent.register_tool(
        name="get_weather",
        func=get_weather,
        description="获取指定城市的天气信息",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如'北京'"
                }
            },
            "required": ["city"]
        }
    )

    agent.register_tool(
        name="search_web",
        func=search_web,
        description="搜索网页信息",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    )

    print("=" * 50)
    print("工具调用 Agent 测试")
    print("=" * 50)

    # 测试用例
    test_cases = [
        "现在几点了？",
        "今天是几号？",
        "123 * 456 等于多少？",
        "北京今天天气怎么样？",
        "帮我搜索 Python 教程",
    ]

    for question in test_cases:
        print(f"\n用户: {question}")
        response = agent.chat(question)
        print(f"助手: {response}")

    # 交互模式
    print("\n" + "=" * 50)
    print("交互模式（输入 quit 退出）")
    print("=" * 50 + "\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break
        if not user_input:
            continue

        response = agent.chat(user_input)
        print(f"助手: {response}\n")


if __name__ == "__main__":
    main()
```

---

## 2.4 代码解析

### 2.4.1 工具注册

```python
# 注册工具需要提供：
# 1. name: 工具名称
# 2. func: 工具函数
# 3. description: 工具描述（供 LLM 理解）
# 4. parameters: 参数定义（JSON Schema 格式）

agent.register_tool(
    name="calculator",
    func=calculator,
    description="进行数学计算",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式"
            }
        },
        "required": ["expression"]
    }
)
```

### 2.4.2 工具调用流程

```
1. 用户输入
   ↓
2. LLM 判断需要调用工具（通过 tools schema 理解可用工具）
   ↓
3. 返回 tool_calls（包含工具名和参数）
   ↓
4. 执行工具，获取结果
   ↓
5. 将工具结果作为 tool 消息发给 LLM
   ↓
6. LLM 根据工具结果生成最终回复
```

### 2.4.3 消息格式

```python
# 用户消息
{'role': 'user', 'content': '123*456等于多少？'}

# 助手消息（包含工具调用）
{
    'role': 'assistant',
    'tool_calls': [
        {
            'function': {
                'name': 'calculator',
                'arguments': {'expression': '123*456'}
            }
        }
    ]
}

# 工具结果消息
{
    'role': 'tool',
    'name': 'calculator',
    'content': '56088'
}
```

---

## 2.5 扩展练习

### 2.5.1 添加更多工具

1. **翻译工具**
```python
def translate(text: str, to_lang: str = "en") -> str:
    """翻译文本

    Args:
        text: 待翻译文本
        to_lang: 目标语言，如 'en', 'ja', 'ko'
    """
    # 调用翻译 API
    ...
```

2. **提醒工具**
```python
def set_reminder(time: str, message: str) -> str:
    """设置提醒

    Args:
        time: 提醒时间
        message: 提醒内容
    """
    ...
```

3. **文件操作**
```python
def read_file(path: str) -> str:
    """读取文件"""
    ...
```

### 2.5.2 高级功能

1. **工具链**
```python
# 连续调用多个工具
def web_search_and_summarize(query: str) -> str:
    # 1. 搜索
    results = search_web(query)
    # 2. 总结
    summary = llm_summarize(results)
    return summary
```

2. **工具选择策略**
```python
# 当前：让 LLM 决定调用哪个
# 高级：基于关键词提前判断
if "天气" in user_input:
    return get_weather(extract_city(user_input))
```

---

## 2.6 本章小结

本章我们实现了一个完整的工具调用 Agent：

- ✅ **工具注册**：动态注册工具
- ✅ **工具描述**：JSON Schema 格式
- ✅ **工具执行**：参数传递和错误处理
- ✅ **多轮工具调用**：支持连续调用多个工具
- ✅ **结果整合**：将工具结果融入回复

---

## 下章预告

下一章我们将实现：
- **RAG Agent（检索增强）**
- 知识库构建
- 向量检索
- 上下文增强
