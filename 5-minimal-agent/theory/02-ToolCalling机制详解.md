# Tool Calling 机制详解

## 本章目标

深入理解 LLM 工具调用的底层机制：
1. Function Calling 原理
2. 工具描述格式
3. 调用流程
4. 常见模式

---

## 1. 什么是 Tool Calling？

Tool Calling（工具调用）让 LLM 能"使用工具"：

```
传统 LLM:
  用户: "北京天气如何？"
  LLM: "我无法获取实时天气信息" ← 只能生成文本

Tool Calling:
  用户: "北京天气如何？"
  LLM: { "tool": "get_weather", "args": {"city": "北京"} } ← 输出工具调用
  系统: 执行 get_weather("北京") → "晴，25°C"
  LLM: "北京今天天气晴朗，气温25°C" ← 基于工具结果回答
```

---

## 2. 工具描述格式

### 2.1 OpenAI 格式（通用标准）

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "获取指定城市的天气信息",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名称，如'北京'"
        },
        "unit": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "description": "温度单位"
        }
      },
      "required": ["city"]
    }
  }
}
```

### 2.2 Ollama 格式

Ollama 兼容 OpenAI 格式，通过 `/api/chat` 接口传递：

```python
requests.post("http://localhost:11434/api/chat", json={
    "model": "qwen2.5",
    "messages": messages,
    "tools": [tool_definition],  # 工具列表
    "stream": False
})
```

---

## 3. 完整调用流程

```
第 1 轮:
  用户 → [messages + tools 定义] → LLM
  LLM → { tool_calls: [{name: "get_weather", args: {city: "北京"}}] }

第 2 轮:
  系统执行工具 → 结果: "晴，25°C"
  [messages + tool结果] → LLM
  LLM → "北京今天天气晴朗，气温25°C"
```

### 消息流

```python
messages = [
    # 1. 用户消息
    {"role": "user", "content": "北京天气怎么样？"},

    # 2. LLM 返回工具调用（系统自动添加）
    {"role": "assistant", "tool_calls": [
        {"function": {"name": "get_weather", "arguments": '{"city": "北京"}'}}
    ]},

    # 3. 工具执行结果
    {"role": "tool", "name": "get_weather", "content": "晴，25°C"},

    # 4. LLM 最终回复
    {"role": "assistant", "content": "北京今天天气晴朗，气温25°C"}
]
```

---

## 4. 并行工具调用

LLM 可以一次返回多个工具调用：

```json
{
  "tool_calls": [
    {"function": {"name": "get_weather", "arguments": "{\"city\": \"北京\"}"}},
    {"function": {"name": "get_weather", "arguments": "{\"city\": \"上海\"}"}}
  ]
}
```

系统应并行执行所有工具，然后将结果一起返回给 LLM。

---

## 5. 工具调用 vs 提示词工程

| 方式 | 可靠性 | 结构化 | 适用场景 |
|------|--------|--------|----------|
| Tool Calling API | 高 | JSON 格式 | 生产环境 |
| 提示词（手动解析） | 中 | 需要正则/解析 | 不支持 tools 的模型 |

### 提示词方式（备选）

```python
system_prompt = """你可以使用以下工具：
- get_weather(city): 获取天气
- calculator(expr): 计算表达式

当需要使用工具时，请用以下格式回复：
<tool>get_weather</tool>
<args>{"city": "北京"}</args>

不需要工具时直接回答。"""
```

---

## 6. 支持 Tool Calling 的模型

| 模型 | Tool Calling | 备注 |
|------|-------------|------|
| GPT-4 / GPT-4o | 原生支持 | 最稳定 |
| Claude 3.5+ | 原生支持 | 高质量 |
| Qwen2.5 | 原生支持 | 开源推荐 |
| Llama 3.1+ | 原生支持 | Meta 开源 |
| Mistral | 原生支持 | 欧洲开源 |
| Gemma 2 | 有限支持 | Google 开源 |

---

## 7. 本章小结

- [x] Tool Calling 原理
- [x] 工具描述 JSON 格式
- [x] 完整调用流程和消息流
- [x] 并行工具调用
- [x] Tool Calling vs 提示词方式
- [x] 支持模型列表
