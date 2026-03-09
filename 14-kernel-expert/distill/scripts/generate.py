"""
蒸馏数据生成脚本

从 FlowSight 知识库 + 内核源码生成高质量 Q&A 训练数据。
调用 Opus 4.6 API 生成，所有数据保存在本地。

用法:
    python distill/scripts/generate.py --topic arm64 --count 100
    python distill/scripts/generate.py --topic drivers --category call_chain --count 200
    python distill/scripts/generate.py --all --count 7000
    python distill/scripts/generate.py --resume  # 断点续传
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: pip install anthropic")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))
from prompts.templates import TEMPLATES

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
KERNEL_SOURCE = Path.home() / "linux-kernel/linux"
RAW_DATA_DIR = PROJECT_ROOT / "distill/data/raw"

# 每个 topic 对应的知识库目录和推荐题型
TOPIC_CONFIG = {
    "arm32": {
        "knowledge_dir": "arm32",
        "categories": ["principle", "call_chain", "debug", "api_usage"],
        "arch": "arm32",
        "kernel_paths": ["arch/arm/kernel/", "arch/arm/mm/", "arch/arm/mach-imx/"],
    },
    "arm64": {
        "knowledge_dir": "arm64",
        "categories": ["principle", "call_chain", "debug", "api_usage"],
        "arch": "arm64",
        "kernel_paths": ["arch/arm64/kernel/", "arch/arm64/mm/", "arch/arm64/include/asm/"],
    },
    "core": {
        "knowledge_dir": "core",
        "categories": ["principle", "call_chain", "code_reading", "debug"],
        "arch": "both",
        "kernel_paths": ["kernel/workqueue.c", "kernel/time/timer.c", "kernel/irq/"],
    },
    "drivers": {
        "knowledge_dir": "drivers",
        "categories": ["call_chain", "code_reading", "api_usage", "debug"],
        "arch": "both",
        "kernel_paths": ["drivers/usb/", "drivers/base/", "drivers/i2c/"],
    },
    "mm": {
        "knowledge_dir": "mm",
        "categories": ["principle", "call_chain", "debug"],
        "arch": "both",
        "kernel_paths": ["mm/", "include/linux/mm.h"],
    },
    "net": {
        "knowledge_dir": "net",
        "categories": ["principle", "call_chain", "code_reading"],
        "arch": "both",
        "kernel_paths": ["net/core/", "net/ipv4/", "include/linux/skbuff.h"],
    },
    "fs": {
        "knowledge_dir": "fs",
        "categories": ["principle", "call_chain", "api_usage"],
        "arch": "both",
        "kernel_paths": ["fs/", "include/linux/fs.h"],
    },
    "comparison": {
        "knowledge_dir": None,  # 特殊：同时用 arm32 和 arm64
        "categories": ["comparison"],
        "arch": "both",
        "kernel_paths": [],
    },
}

# 每批生成的条数（控制单次 API 调用的输出量）
BATCH_SIZE = 10

# API 调用间隔（秒），避免限流
API_DELAY = 2.0


def load_knowledge(topic: str) -> str:
    """加载指定 topic 的知识库 YAML 内容"""
    config = TOPIC_CONFIG[topic]

    if topic == "comparison":
        arm32_dir = KNOWLEDGE_DIR / "arm32"
        arm64_dir = KNOWLEDGE_DIR / "arm64"
        content = "## ARM32 Knowledge\n\n"
        for f in sorted(arm32_dir.glob("*.yaml")):
            content += f.read_text() + "\n\n"
        content += "## ARM64 Knowledge\n\n"
        for f in sorted(arm64_dir.glob("*.yaml")):
            content += f.read_text() + "\n\n"
        return content

    knowledge_dir = KNOWLEDGE_DIR / config["knowledge_dir"]
    if not knowledge_dir.exists():
        print(f"Warning: Knowledge directory not found: {knowledge_dir}")
        return ""

    content = ""
    for yaml_file in sorted(knowledge_dir.glob("*.yaml")):
        content += f"# --- {yaml_file.name} ---\n"
        content += yaml_file.read_text() + "\n\n"

    return content


def load_kernel_source(paths: list[str], max_lines: int = 200) -> str:
    """加载内核源码片段"""
    if not KERNEL_SOURCE.exists():
        return "(kernel source not available)"

    content = ""
    for rel_path in paths:
        full_path = KERNEL_SOURCE / rel_path
        if full_path.is_file():
            lines = full_path.read_text().splitlines()[:max_lines]
            content += f"// --- {rel_path} ---\n"
            content += "\n".join(lines) + "\n\n"
        elif full_path.is_dir():
            for c_file in sorted(full_path.glob("*.c"))[:3]:
                lines = c_file.read_text().splitlines()[:100]
                rel = c_file.relative_to(KERNEL_SOURCE)
                content += f"// --- {rel} ---\n"
                content += "\n".join(lines) + "\n\n"

    return content[:8000]  # 限制长度


def generate_batch(
    client: anthropic.Anthropic,
    template: str,
    yaml_content: str,
    source_code: str,
    topic: str,
    category: str,
    count: int,
    arch: str,
) -> list[dict]:
    """调用 Opus 4.6 生成一批 Q&A 数据"""
    if category == "comparison":
        prompt = template.format(
            arm32_yaml=yaml_content.split("## ARM64 Knowledge")[0],
            arm64_yaml=yaml_content.split("## ARM64 Knowledge")[-1],
            count=count,
            subsystem=topic,
        )
    elif category == "code_reading":
        prompt = template.format(
            yaml_content=yaml_content[:4000],
            source_code=source_code[:4000],
            count=count,
            subsystem=topic,
            arch=arch,
        )
    else:
        prompt = template.format(
            yaml_content=yaml_content[:6000],
            source_code=source_code[:2000],
            count=count,
            subsystem=topic,
            arch=arch,
            topic=topic,
        )

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text

    # 提取 JSON 数组
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        print(f"  Warning: No JSON array found in response")
        return []

    try:
        data = json.loads(text[start:end])
        return data
    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse error: {e}")
        return []


def get_progress_file(topic: str) -> Path:
    """获取进度文件路径"""
    return RAW_DATA_DIR / f".progress_{topic}.json"


def save_progress(topic: str, generated: int, total: int):
    """保存进度"""
    progress_file = get_progress_file(topic)
    progress_file.write_text(json.dumps({"generated": generated, "total": total}))


def load_progress(topic: str) -> int:
    """加载已生成的条数"""
    progress_file = get_progress_file(topic)
    if progress_file.exists():
        data = json.loads(progress_file.read_text())
        return data.get("generated", 0)
    return 0


def generate_topic(client: anthropic.Anthropic, topic: str, total_count: int, resume: bool = False):
    """为指定 topic 生成训练数据"""
    config = TOPIC_CONFIG[topic]
    categories = config["categories"]
    arch = config["arch"]

    # 每个类别均分
    per_category = total_count // len(categories)

    # 加载知识库
    yaml_content = load_knowledge(topic)
    source_code = load_kernel_source(config["kernel_paths"])

    # 输出文件
    output_file = RAW_DATA_DIR / f"{topic}.jsonl"
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 断点续传
    existing_count = 0
    if resume and output_file.exists():
        existing_count = sum(1 for _ in open(output_file))
        print(f"  Resuming from {existing_count} existing entries")

    all_data = []
    generated = existing_count

    for category in categories:
        template = TEMPLATES.get(category)
        if not template:
            print(f"  Warning: No template for category '{category}'")
            continue

        remaining = per_category - (generated // len(categories))
        if remaining <= 0:
            continue

        print(f"  Category: {category} ({remaining} to generate)")

        while remaining > 0:
            batch_count = min(BATCH_SIZE, remaining)
            print(f"    Generating batch of {batch_count}...", end=" ", flush=True)

            try:
                batch = generate_batch(
                    client, template, yaml_content, source_code,
                    topic, category, batch_count, arch,
                )
                print(f"got {len(batch)} entries")

                # 追加写入
                with open(output_file, "a") as f:
                    for item in batch:
                        item["_generated_at"] = datetime.now().isoformat()
                        item["_topic"] = topic
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")

                all_data.extend(batch)
                generated += len(batch)
                remaining -= len(batch)

                save_progress(topic, generated, total_count)
                time.sleep(API_DELAY)

            except anthropic.RateLimitError:
                print("Rate limited, waiting 60s...")
                time.sleep(60)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    print(f"  Topic '{topic}' complete: {generated} total entries in {output_file}")
    return all_data


def main():
    parser = argparse.ArgumentParser(description="Generate distillation training data")
    parser.add_argument("--topic", choices=list(TOPIC_CONFIG.keys()), help="Topic to generate")
    parser.add_argument("--count", type=int, default=100, help="Number of Q&A pairs to generate")
    parser.add_argument("--all", action="store_true", help="Generate for all topics")
    parser.add_argument("--resume", action="store_true", help="Resume from previous progress")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        print("Error: Set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)

    if args.all:
        # 按比例分配
        distribution = {
            "arm64": 0.12,
            "arm32": 0.12,
            "drivers": 0.22,
            "core": 0.22,
            "mm": 0.12,
            "net": 0.06,
            "fs": 0.06,
            "comparison": 0.08,
        }
        topics = {t: int(args.count * r) for t, r in distribution.items()}
    elif args.topic:
        topics = {args.topic: args.count}
    else:
        parser.print_help()
        sys.exit(1)

    # 显示计划
    print("Generation plan:")
    print("-" * 50)
    total = 0
    for topic, count in topics.items():
        config = TOPIC_CONFIG[topic]
        print(f"  {topic:12s}  {count:5d} entries  categories: {', '.join(config['categories'])}")
        total += count
    print("-" * 50)
    print(f"  {'TOTAL':12s}  {total:5d} entries")
    print(f"  Estimated API cost: ~${total * 0.018:.0f}")
    print()

    if args.dry_run:
        print("(dry-run mode, no API calls made)")
        return

    client = anthropic.Anthropic(api_key=api_key)

    for topic, count in topics.items():
        print(f"\n{'='*60}")
        print(f"Generating: {topic} ({count} entries)")
        print(f"{'='*60}")
        generate_topic(client, topic, count, resume=args.resume)

    print(f"\nAll done. Data saved to {RAW_DATA_DIR}/")


if __name__ == "__main__":
    main()
