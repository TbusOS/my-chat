"""
从 FlowSight 同步知识库到本项目

用法:
    python tools/sync_knowledge.py
    python tools/sync_knowledge.py --source /path/to/flowsight/knowledge
    python tools/sync_knowledge.py --dry-run  # 只显示会复制哪些文件
"""

import argparse
import shutil
from pathlib import Path

# FlowSight 知识库路径
DEFAULT_FLOWSIGHT_KNOWLEDGE = Path.home() / "linux-kernel/usb-learn/flowsight/knowledge/platforms/linux-kernel"

# 本项目知识库路径
PROJECT_KNOWLEDGE = Path(__file__).parent.parent / "knowledge"

# FlowSight 目录 → 本项目目录的映射
DIR_MAPPING = {
    "arch/arm32": "arm32",
    "arch/arm64": "arm64",
    "arch": "arm32",  # arm.yaml 归入 arm32
    "core": "core",
    "drivers": "drivers",
    "mm": "mm",
    "net": "net",
    "fs": "fs",
    "sync": "sync",
    "block": "core",     # block 归入 core
    "init": "core",      # init 归入 core
    "lib": "core",       # lib 归入 core
    "sound": "drivers",  # sound 归入 drivers
}


def sync_knowledge(source: Path, dest: Path, dry_run: bool = False):
    """同步知识库文件"""
    if not source.exists():
        print(f"Error: FlowSight knowledge directory not found: {source}")
        print("Please specify --source /path/to/flowsight/knowledge/platforms/linux-kernel")
        return

    yaml_files = sorted(source.rglob("*.yaml"))
    print(f"Found {len(yaml_files)} YAML files in FlowSight knowledge base\n")

    copied = 0
    skipped = 0

    for yaml_file in yaml_files:
        rel_path = yaml_file.relative_to(source)
        parts = list(rel_path.parts)

        # 确定目标目录
        target_dir = None
        for prefix, mapped_dir in DIR_MAPPING.items():
            prefix_parts = prefix.split("/")
            if parts[:len(prefix_parts)] == prefix_parts:
                target_dir = mapped_dir
                break

        if target_dir is None:
            print(f"  SKIP (no mapping): {rel_path}")
            skipped += 1
            continue

        target_file = dest / target_dir / yaml_file.name
        target_file.parent.mkdir(parents=True, exist_ok=True)

        if dry_run:
            print(f"  WOULD COPY: {rel_path} -> {target_dir}/{yaml_file.name}")
        else:
            shutil.copy2(yaml_file, target_file)
            print(f"  COPIED: {rel_path} -> {target_dir}/{yaml_file.name}")

        copied += 1

    print(f"\nTotal: {copied} copied, {skipped} skipped")
    if dry_run:
        print("(dry-run mode, no files were actually copied)")


def show_stats(dest: Path):
    """显示知识库统计"""
    print("\nKnowledge base statistics:")
    print("-" * 40)

    total = 0
    for subdir in sorted(dest.iterdir()):
        if subdir.is_dir():
            count = len(list(subdir.glob("*.yaml")))
            total += count
            print(f"  {subdir.name:15s} {count:3d} files")

    print("-" * 40)
    print(f"  {'TOTAL':15s} {total:3d} files")


def main():
    parser = argparse.ArgumentParser(description="Sync knowledge from FlowSight")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_FLOWSIGHT_KNOWLEDGE,
        help="FlowSight linux-kernel knowledge directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without copying",
    )
    args = parser.parse_args()

    print(f"Source: {args.source}")
    print(f"Target: {PROJECT_KNOWLEDGE}\n")

    sync_knowledge(args.source, PROJECT_KNOWLEDGE, args.dry_run)
    if not args.dry_run:
        show_stats(PROJECT_KNOWLEDGE)


if __name__ == "__main__":
    main()
