"""
MLX LoRA 微调脚本

在 Mac Studio M4 Max 128GB 上用 MLX 微调 Qwen2.5-32B

用法:
    python train/scripts/lora_train.py
    python train/scripts/lora_train.py --model Qwen/Qwen2.5-14B-Instruct  # 先用小模型验证
    python train/scripts/lora_train.py --config train/configs/qwen2.5-32b.yaml
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SPLITS_DIR = PROJECT_ROOT / "distill/data/splits"
OUTPUT_DIR = PROJECT_ROOT / "train/output"

DEFAULT_MODEL = "Qwen/Qwen2.5-32B-Instruct"

# 针对不同模型大小的推荐参数
MODEL_CONFIGS = {
    "7b": {
        "batch_size": 4,
        "lora_layers": 16,
        "learning_rate": 2e-4,
        "epochs": 3,
        "estimated_memory_gb": 16,
    },
    "14b": {
        "batch_size": 2,
        "lora_layers": 16,
        "learning_rate": 2e-4,
        "epochs": 3,
        "estimated_memory_gb": 32,
    },
    "32b": {
        "batch_size": 2,
        "lora_layers": 16,
        "learning_rate": 1e-4,
        "epochs": 3,
        "estimated_memory_gb": 80,
    },
    "70b": {
        "batch_size": 1,
        "lora_layers": 8,
        "learning_rate": 5e-5,
        "epochs": 2,
        "estimated_memory_gb": 140,
    },
}


def detect_model_size(model_name: str) -> str:
    """从模型名推断大小"""
    name_lower = model_name.lower()
    for size in ["70b", "32b", "14b", "7b"]:
        if size in name_lower:
            return size
    return "14b"  # 默认


def check_data():
    """检查训练数据是否存在"""
    train_file = SPLITS_DIR / "train.jsonl"
    valid_file = SPLITS_DIR / "valid.jsonl"

    if not train_file.exists():
        print(f"Error: Training data not found: {train_file}")
        print("Run distill/scripts/generate.py and distill/scripts/clean.py first.")
        sys.exit(1)

    train_count = sum(1 for _ in open(train_file))
    valid_count = sum(1 for _ in open(valid_file)) if valid_file.exists() else 0

    print(f"Training data: {train_count} samples")
    print(f"Validation data: {valid_count} samples")

    return train_count, valid_count


def run_training(model: str, config: dict, run_name: str):
    """执行 MLX LoRA 训练"""
    output_path = OUTPUT_DIR / run_name
    output_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mlx_lm.lora",
        "--model", model,
        "--data", str(SPLITS_DIR),
        "--train",
        "--batch-size", str(config["batch_size"]),
        "--lora-layers", str(config["lora_layers"]),
        "--num-epochs", str(config["epochs"]),
        "--learning-rate", str(config["learning_rate"]),
        "--adapter-path", str(output_path),
        "--iters", "0",  # 使用 epochs 而不是 iters
    ]

    print(f"\nCommand: {' '.join(cmd)}")
    print(f"Output: {output_path}")
    print(f"Estimated memory: ~{config['estimated_memory_gb']}GB")
    print()

    try:
        subprocess.run(cmd, check=True)
        print(f"\nTraining complete. Adapter saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"\nTraining failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: mlx-lm not found. Install with: pip install mlx-lm")
        sys.exit(1)


def fuse_model(model: str, adapter_path: str, output_path: str):
    """合并 LoRA 权重到基座模型"""
    cmd = [
        sys.executable, "-m", "mlx_lm.fuse",
        "--model", model,
        "--adapter-path", adapter_path,
        "--save-path", output_path,
    ]

    print(f"\nFusing model...")
    print(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print(f"Fused model saved to: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Fuse failed with exit code {e.returncode}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="LoRA fine-tuning with MLX")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Base model name or path")
    parser.add_argument("--epochs", type=int, help="Override number of epochs")
    parser.add_argument("--batch-size", type=int, help="Override batch size")
    parser.add_argument("--learning-rate", type=float, help="Override learning rate")
    parser.add_argument("--run-name", default=None, help="Name for this training run")
    parser.add_argument("--fuse", action="store_true", help="Fuse LoRA weights after training")
    parser.add_argument("--dry-run", action="store_true", help="Show config without training")
    args = parser.parse_args()

    # 检查数据
    train_count, valid_count = check_data()

    # 确定模型配置
    size = detect_model_size(args.model)
    config = MODEL_CONFIGS[size].copy()

    # 应用覆盖参数
    if args.epochs:
        config["epochs"] = args.epochs
    if args.batch_size:
        config["batch_size"] = args.batch_size
    if args.learning_rate:
        config["learning_rate"] = args.learning_rate

    run_name = args.run_name or f"kernel-expert-{size}-v1"

    # 显示配置
    print(f"\nTraining configuration:")
    print(f"  Model:         {args.model}")
    print(f"  Model size:    {size}")
    print(f"  LoRA layers:   {config['lora_layers']}")
    print(f"  Batch size:    {config['batch_size']}")
    print(f"  Epochs:        {config['epochs']}")
    print(f"  Learning rate: {config['learning_rate']}")
    print(f"  Run name:      {run_name}")
    print(f"  Est. memory:   ~{config['estimated_memory_gb']}GB")

    if args.dry_run:
        print("\n(dry-run mode, no training executed)")
        return

    # 执行训练
    run_training(args.model, config, run_name)

    # 可选：合并权重
    if args.fuse:
        adapter_path = str(OUTPUT_DIR / run_name)
        fuse_path = str(OUTPUT_DIR / f"{run_name}-fused")
        fuse_model(args.model, adapter_path, fuse_path)


if __name__ == "__main__":
    main()
