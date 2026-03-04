#!/usr/bin/env python3
"""
LitGPT LoRA 微调训练脚本
使用配置文件的示例
"""

import os
import sys
import yaml
from pathlib import Path

# 添加 litgpt 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "litgpt"))

import torch
from litgpt import LLM
from litgpt.args import TrainArgs
from litgpt.data import get_data
from litgpt import pretrain


def load_config(config_path: str) -> dict:
    """加载 YAML 配置"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    # 解析命令行参数
    args = TrainArgs.parse_args()

    # 如果提供了配置文件，加载配置
    if hasattr(args, 'config') and args.config:
        config = load_config(args.config)

        # 应用配置到 args
        for key, value in config.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    setattr(args, sub_key, sub_value)
            else:
                setattr(args, key, value)

    print(f"模型: {args.model.name if hasattr(args.model, 'name') else args.model}")
    print(f"数据: {args.data}")
    print(f"LoRA r: {args.lora.r}")
    print(f"训练轮数: {args.train.epochs}")

    # 获取数据
    data = get_data(args)

    # 开始训练
    pretrain.main(args, data)


if __name__ == "__main__":
    main()
