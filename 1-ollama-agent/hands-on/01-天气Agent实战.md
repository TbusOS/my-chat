# 第一章：天气 Agent 实战

## 本章目标

手把手实现一个天气预报 Agent，功能包括：
1. 理解用户查询天气的意图
2. 提取城市名称
3. 获取天气信息
4. 生成自然回复

---

## 1.1 项目概述

### 1.1.1 功能需求

用户可能用各种方式询问天气：

```
"北京今天天气怎么样？"
"上海明天会下雨吗？"
"广州天气如何？"
"帮我查下深圳的天气"
```

我们的 Agent 需要：
1. 识别用户想要查询天气
2. 提取城市名称
3. 调用天气 API
4. 生成友好的回复

### 1.1.2 系统架构

```
用户输入 → 意图识别 → 实体提取 → 天气查询 → 回复生成 → 用户
```

### 1.1.3 项目结构

```
weather_agent/
├── weather_agent.py    # 主程序
├── weather_data.py     # 模拟天气数据
└── requirements.txt    # 依赖
```

---

## 1.2 准备工作

### 1.2.1 安装依赖

```bash
pip install ollama
```

### 1.2.2 准备天气数据

```python
# weather_data.py
"""模拟天气数据"""

WEATHER_DATA = {
    "北京": {
        "today": {"weather": "晴", "temp": "15-25°C", "wind": "北风3-4级", "aqi": "良"},
        "tomorrow": {"weather": "多云", "temp": "14-24°C", "wind": "北风2-3级", "aqi": "良"}
    },
    "上海": {
        "today": {"weather": "多云", "temp": "18-27°C", "wind": "东风2-3级", "aqi": "优"},
        "tomorrow": {"weather": "阴", "temp": "17-26°C", "wind": "东南风2级", "aqi": "优"}
    },
    "广州": {
        "today": {"weather": "雷阵雨", "temp": "22-30°C", "wind": "南风3-4级", "aqi": "良"},
        "tomorrow": {"weather": "大雨", "temp": "21-28°C", "wind": "南风4级", "aqi": "中"}
    },
    "深圳": {
        "today": {"weather": "晴", "temp": "23-29°C", "wind": "南风2-3级", "aqi": "优"},
        "tomorrow": {"weather": "晴", "temp": "24-30°C", "wind": "南风2级", "aqi": "优"}
    },
    "杭州": {
        "today": {"weather": "阴", "temp": "17-24°C", "wind": "东北风2级", "aqi": "良"},
        "tomorrow": {"weather": "小雨", "temp": "16-23°C", "wind": "东北风1-2级", "aqi": "良"}
    },
    "成都": {
        "today": {"weather": "小雨", "temp": "16-22°C", "wind": "北风1-2级", "aqi": "良"},
        "tomorrow": {"weather": "多云", "temp": "17-23°C", "wind": "北风1级", "aqi": "良"}
    },
    "重庆": {
        "today": {"weather": "阴", "temp": "19-26°C", "wind": "西北风1级", "aqi": "中"},
        "tomorrow": {"weather": "晴", "temp": "20-27°C", "wind": "西风1级", "aqi": "良"}
    },
    "武汉": {
        "today": {"weather": "多云", "temp": "18-27°C", "wind": "东南风2级", "aqi": "良"},
        "tomorrow": {"weather": "晴", "temp": "19-28°C", "wind": "东南风2-3级", "aqi": "优"}
    },
    "西安": {
        "today": {"weather": "晴", "temp": "14-28°C", "wind": "东北风2-3级", "aqi": "良"},
        "tomorrow": {"weather": "晴", "temp": "15-29°C", "wind": "东北风2级", "aqi": "良"}
    },
    "南京": {
        "today": {"weather": "多云", "temp": "16-25°C", "wind": "东风2级", "aqi": "优"},
        "tomorrow": {"weather": "阴", "temp": "15-24°C", "wind": "东风1-2级", "aqi": "优"}
    }
}

def get_weather(city: str, day: str = "today") -> dict:
    """获取天气信息

    Args:
        city: 城市名称
        day: today 或 tomorrow

    Returns:
        天气信息字典
    """
    if city in WEATHER_DATA:
        return WEATHER_DATA[city].get(day, WEATHER_DATA[city]["today"])
    return None


def get_supported_cities() -> list:
    """获取支持的城市列表"""
    return list(WEATHER_DATA.keys())
```

---

## 1.3 完整代码实现

### 1.3.1 主程序

```python
#!/usr/bin/env python3
"""
天气 Agent
功能：理解用户查询天气的意图，提取城市，获取天气，生成回复
"""

import ollama
from weather_data import get_weather, get_supported_cities


class WeatherAgent:
    """天气预报 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        """
        初始化 Agent

        Args:
            model: 使用的模型
        """
        self.model = model
        self.system_prompt = """你是一个天气预报助手。用户会询问某个城市的天气情况。

你的职责：
1. 理解用户想要查询天气的意图
2. 从用户输入中提取城市名称
3. 以友好的方式返回天气信息

重要规则：
- 只回答天气相关的问题
- 如果用户没有提到具体城市，请礼貌地询问
- 如果不确定城市，可以建议用户说明城市名
- 保持回答简洁友好，不要过于冗长"""

    def extract_city(self, user_input: str) -> str:
        """
        从用户输入中提取城市名称

        Args:
            user_input: 用户输入

        Returns:
            城市名称，如果没找到返回 None
        """
        # 1. 精确匹配
        cities = get_supported_cities()
        for city in cities:
            if city in user_input:
                return city

        # 2. 使用 LLM 提取
        prompt = f"""从以下用户输入中提取城市名称。

用户输入：{user_input}

可选城市：{', '.join(cities)}

如果找到城市，返回城市名称。
如果没有找到城市，返回"未找到"。
只需要返回城市名称或"未找到"，不要其他内容。"""

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        result = response['message']['content'].strip()
        if result != "未找到" and result in cities:
            return result
        return None

    def format_weather_reply(self, city: str, weather: dict) -> str:
        """
        格式化天气回复

        Args:
            city: 城市名称
            weather: 天气信息

        Returns:
            格式化的回复
        """
        return f"""🌤️ {city}今日天气

天气状况：{weather['weather']}
温度：{weather['temp']}
风力：{weather['wind']}
空气质量：{weather['aqi']}"""

    def chat(self, user_input: str) -> str:
        """
        处理用户对话

        Args:
            user_input: 用户输入

        Returns:
            Agent 回复
        """
        # 1. 检查是否是天气相关问题
        is_weather_query = self._check_weather_intent(user_input)
        if not is_weather_query:
            return "我是���个天气预报助手，请问您想查询哪个城市的天气呢？"

        # 2. 提取城市
        city = self.extract_city(user_input)

        if not city:
            # 没有找到城市，询问用户
            cities = ", ".join(get_supported_cities()[:5]) + "等"
            return f"请问您想查询哪个城市的天气呢？目前支持：{cities}"

        # 3. 获取天气信息
        weather = get_weather(city)

        if not weather:
            return f"抱歉，暂时不支持查询 {city} 的天气。"

        # 4. 格式化回复
        weather_info = self.format_weather_reply(city, weather)

        # 5. 让模型生成更自然的回复
        prompt = f"""基于以下天气信息，用友好的语气回复用户。

天气信息：
{weather_info}

用户原始问题：{user_input}

只需要返回回复内容（1-2句话），不需要重复天气详细信息。"""

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        return response['message']['content']

    def _check_weather_intent(self, user_input: str) -> bool:
        """
        检查用户是否在查询天气

        Args:
            user_input: 用户输入

        Returns:
            是否是天气查询
        """
        weather_keywords = ["天气", "气温", "温度", "下雨", "晴天", "阴天",
                          "多云", "刮风", "空气质量", "AQI", "冷", "热"]

        # 简单关键词匹配
        for keyword in weather_keywords:
            if keyword in user_input:
                return True

        # 使用 LLM 判断
        prompt = f"""判断用户是否在查询天气。

用户输入：{user_input}

只需要回答"是"或"否"。"""

        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        result = response['message']['content'].strip()
        return "是" in result


def main():
    """主函数"""
    # 创建 Agent
    agent = WeatherAgent("qwen2.5")

    print("=" * 50)
    print("天气预报 Agent")
    print("=" * 50)
    print("\n输入 quit 退出\n")

    # 测试用例
    test_cases = [
        "北京今天天气怎么样？",
        "上海明天会下雨吗？",
        "广州天气如何？",
        "深圳明天会下雨吗？",
        "杭州天气",
        "今天天气怎么样？",  # 没有城市
        "给我讲个笑话",      # 非天气问题
    ]

    print("\n--- 测试用例 ---\n")
    for question in test_cases:
        print(f"用户: {question}")
        response = agent.chat(question)
        print(f"助手: {response}\n")

    # 交互模式
    print("\n--- 交互模式 ---\n")
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

## 1.4 代码解析

### 1.4.1 核心流程

```
用户输入
   ↓
意图检查 (_check_weather_intent)
   ↓
城市提取 (extract_city)
   ↓
获取天气数据 (get_weather)
   ↓
格式化回复 (format_weather_reply)
   ↓
自然语言生成 (LLM)
   ↓
返回回复
```

### 1.4.2 关键函数

| 函数 | 功能 |
|------|------|
| `_check_weather_intent` | 判断用户是否在查天气 |
| `extract_city` | 提取城市名称 |
| `get_weather` | 获取天气数据 |
| `format_weather_reply` | 格式化天气信息 |
| `chat` | 主对话流程 |

### 1.4.3 设计思路

1. **双重城市提取**
   - 先用关键词精确匹配
   - 匹配失败再用 LLM 提取

2. **模板 + LLM**
   - 天气信息用模板格式化
   - 回复用 LLM 生成，更自然

3. **意图识别**
   - 关键词 + LLM 双重确认

---

## 1.5 扩展练习

### 1.5.1 扩展功能

1. **支持明天天气**
   ```python
   # 添加参数
   def get_weather(self, city, day="today"):
       # 支持 today/tomorrow
   ```

2. **支持多天预报**
   ```python
   # 返回 7 天天气预报
   ```

3. **穿衣建议**
   ```python
   # 根据温度给出穿衣建议
   ```

4. **预警信息**
   ```python
   # 大风、暴雨、高温等预警
   ```

### 1.5.2 接入真实 API

当前使用模拟数据，可以接入真实天气 API：

```python
# 和风天气 API 示例
import requests

def get_weather_from_api(city: str) -> dict:
    """接入和风天气 API"""
    key = "YOUR_API_KEY"
    url = f"https://devapi.qweather.com/v7/weather/now"

    params = {
        "location": city,
        "key": key
    }

    response = requests.get(url, params=params)
    data = response.json()

    return {
        "weather": data["now"]["text"],
        "temp": f"{data['now']['temp']}°C",
        "wind": f"{data['now']['windDir']}{data['now']['windScale']}级",
    }
```

---

## 1.6 本章小结

本章我们实现了一个完整的天气 Agent：

- ✅ **意图识别**：判断用户是否在查天气
- ✅ **实体提取**：从文本中提取城市名称
- ✅ **数据获取**：查询天气信息
- ✅ **回复生成**：用 LLM 生成自然回复
- ✅ **交互体验**：友好的对话流程

---

## 下章预告

下一章我们将实现：
- **工具调用 Agent**
- 注册自定义工具
- 让 LLM 决定调用哪个工具
- 处理工具返回结果
