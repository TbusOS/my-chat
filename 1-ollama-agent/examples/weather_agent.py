#!/usr/bin/env python3
"""
天气预报 Agent
功能：理解用户意图 → 提取城市 → 查询天气 → 返回格式化信息

使用方法:
    python examples/weather_agent.py
"""

import ollama
import re
from typing import Optional, Dict


class WeatherAgent:
    """天气预报 Agent"""

    def __init__(self, model: str = "qwen2.5"):
        self.model = model
        self.messages = [
            {
                'role': 'system',
                'content': '你是一个天气预报助手。理解用户的天气查询意图，提取城市名称，以友好的方式返回天气信息。'
            }
        ]

    def _extract_city(self, user_input: str) -> Optional[str]:
        """从用户输入中提取城市名称"""
        cities = [
            '北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '重庆',
            '武汉', '西安', '苏州', '天津', '长沙', '郑州', '济南', '青岛',
        ]

        for city in cities:
            if city in user_input:
                return city

        prompt = f'从以下输入中提取城市名称，如果没有返回"未知"。\n输入：{user_input}\n只返回城市名称。'
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )
        city = response['message']['content'].strip()
        return city if city != '未知' else None

    def _get_weather(self, city: str) -> Dict:
        """获取天气信息（模拟数据）"""
        weather_data = {
            '北京': {'weather': '晴', 'temp': '15-25°C', 'wind': '北风3-4级', 'aqi': '良'},
            '上海': {'weather': '多云', 'temp': '18-27°C', 'wind': '东风2-3级', 'aqi': '优'},
            '广州': {'weather': '雷阵雨', 'temp': '22-30°C', 'wind': '南风3-4级', 'aqi': '良'},
            '深圳': {'weather': '晴', 'temp': '23-29°C', 'wind': '南风2-3级', 'aqi': '优'},
            '杭州': {'weather': '阴', 'temp': '17-24°C', 'wind': '东北风2级', 'aqi': '良'},
            '成都': {'weather': '小雨', 'temp': '16-22°C', 'wind': '北风1-2级', 'aqi': '良'},
        }
        return weather_data.get(city, {'weather': '未知', 'temp': '未知', 'wind': '未知', 'aqi': '未知'})

    def chat(self, user_input: str) -> str:
        """对话"""
        self.messages.append({'role': 'user', 'content': user_input})

        city = self._extract_city(user_input)
        if not city:
            return "请问您想查询哪个城市的天气呢？"

        weather = self._get_weather(city)
        weather_info = f"{city}天气：{weather['weather']}，温度{weather['temp']}，{weather['wind']}，空气质量{weather['aqi']}"

        prompt = f'基于以下天气信息，用友好的语气回复用户。\n天气信息：{weather_info}\n用户问题：{user_input}'
        response = ollama.chat(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}]
        )

        assistant_msg = response['message']['content']
        self.messages.append({'role': 'assistant', 'content': assistant_msg})
        return assistant_msg


if __name__ == "__main__":
    agent = WeatherAgent("qwen2.5")

    print("=" * 50)
    print("天气预报 Agent")
    print("=" * 50)

    for q in ["北京今天天气怎么样？", "上海的天气", "杭州天气"]:
        print(f"\n用户: {q}")
        print(f"助手: {agent.chat(q)}")

    print("\n交互模式（输入 quit 退出）")
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        if user_input:
            print(f"助手: {agent.chat(user_input)}")
