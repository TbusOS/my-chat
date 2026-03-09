"""
蒸馏数据清洗脚本

清洗 Opus 4.6 生成的原始数据，过滤低质量条目，划分数据集。

用法:
    python distill/scripts/clean.py
    python distill/scripts/clean.py --min-answer-length 200
    python distill/scripts/clean.py --split-ratio 0.9 0.05 0.05
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DIR = PROJECT_ROOT / "distill/data/raw"
CLEANED_DIR = PROJECT_ROOT / "distill/data/cleaned"
SPLITS_DIR = PROJECT_ROOT / "distill/data/splits"

# 必须包含的字段
REQUIRED_FIELDS = ["question", "answer", "category"]

# 答案中应包含的内核相关关键词（至少命中一个）
KERNEL_KEYWORDS = [
    "struct", "void", "int", "linux", "kernel", "driver", "irq",
    "mutex", "spinlock", "work_struct", "timer", "probe", "ARM",
    "arm64", "arm32", "GIC", "page", "mm", "socket", "skb",
    "进程上下文", "中断上下文", "软中断", "硬中断", "可睡眠", "不可睡眠",
    "调用链", "回调", "异步", "work_queue", "workqueue",
]


def load_raw_data() -> list[dict]:
    """加载所有原始数据"""
    data = []
    for jsonl_file in sorted(RAW_DIR.glob("*.jsonl")):
        with open(jsonl_file) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    item["_source_file"] = jsonl_file.name
                    item["_source_line"] = line_num
                    data.append(item)
                except json.JSONDecodeError:
                    print(f"  Warning: Invalid JSON at {jsonl_file.name}:{line_num}")
    return data


def check_required_fields(item: dict) -> bool:
    """检查必要字段"""
    return all(field in item and item[field] for field in REQUIRED_FIELDS)


def check_answer_length(item: dict, min_length: int, max_length: int) -> bool:
    """检查答案长度"""
    length = len(item.get("answer", ""))
    return min_length <= length <= max_length


def check_kernel_relevance(item: dict) -> bool:
    """检查答案是否与内核相关"""
    answer = item.get("answer", "").lower()
    return any(kw.lower() in answer for kw in KERNEL_KEYWORDS)


def check_not_refusal(item: dict) -> bool:
    """检查是否是拒绝回答"""
    answer = item.get("answer", "").lower()
    refusal_patterns = [
        "i cannot", "i can't", "i'm sorry", "as an ai",
        "i don't have", "i am not able",
    ]
    return not any(p in answer for p in refusal_patterns)


def deduplicate(data: list[dict]) -> list[dict]:
    """基于问题内容去重"""
    seen = set()
    unique = []
    for item in data:
        question_hash = hashlib.md5(item["question"].encode()).hexdigest()
        if question_hash not in seen:
            seen.add(question_hash)
            unique.append(item)
    return unique


def format_for_training(item: dict) -> dict:
    """转换为训练格式（chat 格式）"""
    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 Linux 内核专家，专注于 ARM32 和 ARM64 架构。"
                    "回答时引用具体函数名、源文件路径，标注执行上下文。"
                ),
            },
            {"role": "user", "content": item["question"]},
            {"role": "assistant", "content": item["answer"]},
        ],
        "category": item.get("category", "unknown"),
        "subsystem": item.get("subsystem", item.get("_topic", "unknown")),
        "arch": item.get("arch", "both"),
    }


def split_data(
    data: list[dict],
    train_ratio: float = 0.9,
    val_ratio: float = 0.05,
    test_ratio: float = 0.05,
) -> tuple[list, list, list]:
    """划分数据集，确保类别分布均匀"""
    # 按 category 分组
    by_category: dict[str, list] = {}
    for item in data:
        cat = item.get("category", "unknown")
        by_category.setdefault(cat, []).append(item)

    train, val, test = [], [], []

    for cat, items in by_category.items():
        random.shuffle(items)
        n = len(items)
        n_val = max(1, int(n * val_ratio))
        n_test = max(1, int(n * test_ratio))
        n_train = n - n_val - n_test

        train.extend(items[:n_train])
        val.extend(items[n_train : n_train + n_val])
        test.extend(items[n_train + n_val :])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    return train, val, test


def save_jsonl(data: list[dict], path: Path):
    """保存为 JSONL"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Clean and split distillation data")
    parser.add_argument("--min-answer-length", type=int, default=100, help="Minimum answer length")
    parser.add_argument("--max-answer-length", type=int, default=8000, help="Maximum answer length")
    parser.add_argument(
        "--split-ratio",
        type=float,
        nargs=3,
        default=[0.9, 0.05, 0.05],
        help="Train/val/test ratio",
    )
    args = parser.parse_args()

    # 加载原始数据
    print("Loading raw data...")
    raw_data = load_raw_data()
    print(f"  Loaded {len(raw_data)} entries from {RAW_DIR}/")

    if not raw_data:
        print("No data found. Run generate.py first.")
        sys.exit(1)

    # 清洗流水线
    print("\nCleaning pipeline:")
    data = raw_data

    # Step 1: 必要字段检查
    data = [item for item in data if check_required_fields(item)]
    print(f"  After field check:     {len(data)} ({len(raw_data) - len(data)} removed)")

    # Step 2: 答案长度检查
    prev = len(data)
    data = [item for item in data if check_answer_length(item, args.min_answer_length, args.max_answer_length)]
    print(f"  After length check:    {len(data)} ({prev - len(data)} removed)")

    # Step 3: 内核相关性检查
    prev = len(data)
    data = [item for item in data if check_kernel_relevance(item)]
    print(f"  After relevance check: {len(data)} ({prev - len(data)} removed)")

    # Step 4: 拒绝回答检查
    prev = len(data)
    data = [item for item in data if check_not_refusal(item)]
    print(f"  After refusal check:   {len(data)} ({prev - len(data)} removed)")

    # Step 5: 去重
    prev = len(data)
    data = deduplicate(data)
    print(f"  After dedup:           {len(data)} ({prev - len(data)} removed)")

    # 统计
    print(f"\nCleaned data statistics:")
    category_counts = Counter(item.get("category", "unknown") for item in data)
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat:20s} {count:5d}")

    arch_counts = Counter(item.get("arch", "unknown") for item in data)
    print(f"\nArchitecture distribution:")
    for arch, count in sorted(arch_counts.items()):
        print(f"  {arch:20s} {count:5d}")

    # 保存清洗后的数据
    print(f"\nSaving cleaned data...")
    save_jsonl(data, CLEANED_DIR / "all.jsonl")
    print(f"  Saved to {CLEANED_DIR / 'all.jsonl'}")

    # 转换为训练格式并划分
    print(f"\nFormatting for training...")
    formatted = [format_for_training(item) for item in data]

    train_r, val_r, test_r = args.split_ratio
    train, val, test = split_data(formatted, train_r, val_r, test_r)

    save_jsonl(train, SPLITS_DIR / "train.jsonl")
    save_jsonl(val, SPLITS_DIR / "valid.jsonl")
    save_jsonl(test, SPLITS_DIR / "test.jsonl")

    print(f"  train: {len(train):5d} entries -> {SPLITS_DIR / 'train.jsonl'}")
    print(f"  valid: {len(val):5d} entries -> {SPLITS_DIR / 'valid.jsonl'}")
    print(f"  test:  {len(test):5d} entries -> {SPLITS_DIR / 'test.jsonl'}")
    print(f"\nDone.")


if __name__ == "__main__":
    main()
