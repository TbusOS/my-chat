"""
自学习改进模块

定期分析用户反馈，自动执行：
1. 错误模式分析 - 找出模型的薄弱环节
2. 知识库更新 - 从用户修正中提取新规则写入 YAML
3. 增量训练数据生成 - 针对薄弱环节用 Opus 4.6 补充数据
4. LoRA 增量微调 - 用新数据微调模型
5. 回归评估 - 确保没退步

用法:
    python serve/feedback/self_improve.py --analyze          # 分析错误模式
    python serve/feedback/self_improve.py --update-kb        # 更新知识库
    python serve/feedback/self_improve.py --generate-data    # 生成补充训练数据
    python serve/feedback/self_improve.py --retrain          # 增量微调
    python serve/feedback/self_improve.py --full-cycle       # 执行完整改进周期
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
FEEDBACK_DIR = PROJECT_ROOT / "serve/feedback"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
REPORTS_DIR = FEEDBACK_DIR / "reports"

# 触发改进的最小反馈数量
MIN_FEEDBACK_FOR_IMPROVEMENT = 50


def load_feedback() -> list[dict]:
    """加载所有反馈数据"""
    feedback_file = FEEDBACK_DIR / "feedback_log.jsonl"
    if not feedback_file.exists():
        return []

    data = []
    with open(feedback_file) as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def analyze_errors(feedback: list[dict]) -> dict:
    """
    分析错误模式

    输出:
    - 错误率最高的问题类别
    - 错误率最高的子系统
    - 知识库 vs 模型的错误分布
    - 常见错误类型
    """
    if not feedback:
        print("No feedback data found.")
        return {}

    total = len(feedback)
    incorrect = [f for f in feedback if f["feedback"] == "incorrect"]
    correct = [f for f in feedback if f["feedback"] == "correct"]

    print(f"Total feedback: {total}")
    print(f"Correct: {len(correct)} ({len(correct)/total:.1%})")
    print(f"Incorrect: {len(incorrect)} ({len(incorrect)/total:.1%})")

    # 按来源分析
    source_stats = {}
    for f in feedback:
        source = f.get("answer_source", "unknown")
        source_stats.setdefault(source, {"total": 0, "incorrect": 0})
        source_stats[source]["total"] += 1
        if f["feedback"] == "incorrect":
            source_stats[source]["incorrect"] += 1

    print(f"\nError rate by source:")
    for source, stats in source_stats.items():
        rate = stats["incorrect"] / stats["total"] if stats["total"] > 0 else 0
        print(f"  {source:20s} {rate:.1%} ({stats['incorrect']}/{stats['total']})")

    # 从问题文本中提取关键词，推断子系统
    subsystem_keywords = {
        "arm32": ["arm32", "armv7", "swi", "mach-imx"],
        "arm64": ["arm64", "aarch64", "armv8", "el0", "el1", "gicv3"],
        "usb": ["usb", "urb", "gadget", "endpoint"],
        "irq": ["irq", "interrupt", "中断", "gic"],
        "workqueue": ["workqueue", "work_struct", "init_work", "schedule_work"],
        "timer": ["timer", "hrtimer", "定时器"],
        "mm": ["page", "slab", "kmalloc", "vmalloc", "mmap", "内存"],
        "scheduler": ["sched", "调度", "cfs", "context switch"],
        "driver": ["probe", "driver", "platform", "驱动"],
        "fs": ["vfs", "inode", "dentry", "文件系统", "file_operations"],
        "net": ["socket", "skb", "tcp", "网络", "netdev"],
        "sync": ["mutex", "spinlock", "semaphore", "rcu", "锁"],
    }

    subsystem_errors = Counter()
    subsystem_totals = Counter()

    for f in feedback:
        q = f["question"].lower()
        matched_subsystems = []
        for subsystem, keywords in subsystem_keywords.items():
            if any(kw in q for kw in keywords):
                matched_subsystems.append(subsystem)

        if not matched_subsystems:
            matched_subsystems = ["other"]

        for s in matched_subsystems:
            subsystem_totals[s] += 1
            if f["feedback"] == "incorrect":
                subsystem_errors[s] += 1

    print(f"\nError rate by subsystem:")
    subsystem_error_rates = {}
    for subsystem in sorted(subsystem_totals.keys()):
        total_s = subsystem_totals[subsystem]
        errors = subsystem_errors.get(subsystem, 0)
        rate = errors / total_s if total_s > 0 else 0
        subsystem_error_rates[subsystem] = rate
        bar = "█" * int(rate * 20) + "░" * (20 - int(rate * 20))
        print(f"  {subsystem:15s} {bar} {rate:.1%} ({errors}/{total_s})")

    # 找出最需要改进的子系统
    weak_subsystems = sorted(subsystem_error_rates.items(), key=lambda x: -x[1])
    weak_subsystems = [(s, r) for s, r in weak_subsystems if r > 0.2]

    if weak_subsystems:
        print(f"\nWeakest subsystems (error rate > 20%):")
        for subsystem, rate in weak_subsystems:
            print(f"  {subsystem}: {rate:.1%}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_feedback": total,
        "accuracy": len(correct) / total if total > 0 else 0,
        "source_stats": source_stats,
        "subsystem_error_rates": subsystem_error_rates,
        "weak_subsystems": [s for s, _ in weak_subsystems],
        "incorrect_questions": [f["question"] for f in incorrect[:20]],
    }

    # 保存报告
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nReport saved to: {report_file}")

    return report


def update_knowledge_base():
    """
    从用户修正中更新知识库

    处理 pending_updates 目录中的修正建议
    """
    pending_dir = FEEDBACK_DIR / "pending_updates"
    if not pending_dir.exists():
        print("No pending updates.")
        return

    updates = sorted(pending_dir.glob("*.json"))
    if not updates:
        print("No pending updates.")
        return

    print(f"Found {len(updates)} pending knowledge updates\n")

    applied = 0
    for update_file in updates:
        update = json.loads(update_file.read_text())
        if update.get("status") != "pending":
            continue

        print(f"Update: {update_file.name}")
        print(f"  Question: {update['question'][:80]}...")
        print(f"  Correction: {update['correction'][:100]}...")

        # 自动应用策略：
        # 如果修正中包含明确的调用链或执行上下文信息，
        # 生成 YAML 补丁建议
        correction = update["correction"]
        yaml_patch = _try_extract_yaml_patch(update["question"], correction)

        if yaml_patch:
            print(f"  Generated YAML patch:")
            for line in yaml_patch.split("\n")[:5]:
                print(f"    {line}")

            # 保存补丁（需要人工审核）
            patch_dir = FEEDBACK_DIR / "yaml_patches"
            patch_dir.mkdir(exist_ok=True)
            patch_file = patch_dir / f"patch_{int(time.time())}.yaml"
            patch_file.write_text(yaml_patch)
            print(f"  Patch saved to: {patch_file}")
            print(f"  Status: needs_review (run with --apply-patches to apply)")

        # 标记为已处理
        update["status"] = "processed"
        update_file.write_text(json.dumps(update, ensure_ascii=False, indent=2))
        applied += 1

    print(f"\nProcessed {applied} updates")


def _try_extract_yaml_patch(question: str, correction: str) -> str:
    """
    尝试从修正文本中提取 YAML 补丁

    简单的启发式提取：
    - 如果修正中包含 "→" 或 "->" 箭头，可能是调用链
    - 如果修正中包含 "进程上下文" / "中断上下文"，可能是执行上下文信息
    """
    lines = []
    q_lower = question.lower()

    # 检测是否涉及调用链
    if "->" in correction or "→" in correction or "调用链" in correction:
        lines.append("# Auto-extracted call chain patch")
        lines.append("# Source: user correction")
        lines.append(f"# Question: {question[:100]}")
        lines.append("")
        lines.append("kernel_call_chain:")
        lines.append(f'  trigger: "{question[:50]}"')
        lines.append("  chain:")

        # 提取 → 分隔的函数名
        chain_text = correction
        for sep in ["→", "->", "──>"]:
            if sep in chain_text:
                funcs = [f.strip() for f in chain_text.split(sep)]
                for func in funcs:
                    if func and len(func) < 100:
                        lines.append(f'    - function: "{func}"')
                break

    # 检测执行上下文信息
    ctx_map = {
        "进程上下文": "process",
        "软中断": "softirq",
        "硬中断": "hardirq",
        "process context": "process",
        "softirq context": "softirq",
        "hardirq context": "hardirq",
        "interrupt context": "hardirq",
    }

    for text, ctx in ctx_map.items():
        if text in correction.lower():
            if not lines:
                lines.append("# Auto-extracted context patch")
                lines.append(f"# Question: {question[:100]}")
                lines.append("")
            lines.append(f"context: {ctx}")
            lines.append(f"can_sleep: {'true' if ctx == 'process' else 'false'}")
            break

    return "\n".join(lines) if lines else ""


def generate_targeted_data(weak_subsystems: list[str], count_per_subsystem: int = 100):
    """
    针对薄弱子系统生成补充训练数据

    调用 Opus 4.6 生成针对性 Q&A
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY to generate targeted data")
        print("Alternatively, manually create data in distill/data/raw/")
        return

    print(f"Generating targeted data for weak subsystems: {weak_subsystems}")
    print(f"Count per subsystem: {count_per_subsystem}")
    print()

    # 复用 distill/scripts/generate.py 的逻辑
    sys.path.insert(0, str(PROJECT_ROOT / "distill/scripts"))
    try:
        from generate import generate_topic
        import anthropic as anthropic_lib

        client = anthropic_lib.Anthropic(api_key=api_key)

        for subsystem in weak_subsystems:
            # 映射子系统名到 topic
            topic_map = {
                "arm32": "arm32",
                "arm64": "arm64",
                "usb": "drivers",
                "irq": "core",
                "workqueue": "core",
                "timer": "core",
                "mm": "mm",
                "scheduler": "core",
                "driver": "drivers",
                "fs": "fs",
                "net": "net",
                "sync": "core",
            }
            topic = topic_map.get(subsystem, "core")
            print(f"Generating {count_per_subsystem} entries for {subsystem} (topic: {topic})")
            generate_topic(client, topic, count_per_subsystem, resume=True)

    except ImportError:
        print("Could not import generate module. Run from project root.")


def incremental_retrain():
    """增量 LoRA 微调"""
    print("Starting incremental LoRA retraining...")

    # 先重新清洗数据（包含新生成的数据）
    clean_script = PROJECT_ROOT / "distill/scripts/clean.py"
    train_script = PROJECT_ROOT / "train/scripts/lora_train.py"

    import subprocess

    print("Step 1: Re-cleaning data...")
    subprocess.run([sys.executable, str(clean_script)], check=True)

    print("\nStep 2: LoRA fine-tuning...")
    subprocess.run([
        sys.executable, str(train_script),
        "--model", "Qwen/Qwen2.5-Coder-32B-Instruct",
        "--epochs", "1",  # 增量训练只跑 1 epoch
        "--run-name", f"kernel-expert-incremental-{datetime.now().strftime('%Y%m%d')}",
    ], check=True)

    print("\nStep 3: Running evaluation...")
    eval_script = PROJECT_ROOT / "eval/scripts/evaluate.py"
    subprocess.run([
        sys.executable, str(eval_script),
        "--model", "kernel-expert",
    ], check=True)

    print("\nIncremental retraining complete.")


def full_improvement_cycle():
    """
    执行完整的自我改进周期

    1. 分析错误 → 2. 更新知识库 → 3. 生成数据 → 4. 微调 → 5. 评估
    """
    feedback = load_feedback()

    if len(feedback) < MIN_FEEDBACK_FOR_IMPROVEMENT:
        print(f"Not enough feedback ({len(feedback)}/{MIN_FEEDBACK_FOR_IMPROVEMENT}).")
        print("Continue using the system and providing feedback.")
        return

    print("=" * 60)
    print("SELF-IMPROVEMENT CYCLE")
    print("=" * 60)

    # Step 1: 分析
    print("\n[Step 1/5] Analyzing error patterns...")
    report = analyze_errors(feedback)

    # Step 2: 更新知识库
    print("\n[Step 2/5] Updating knowledge base...")
    update_knowledge_base()

    # Step 3: 生成补充数据
    weak = report.get("weak_subsystems", [])
    if weak:
        print(f"\n[Step 3/5] Generating targeted data for: {weak}")
        generate_targeted_data(weak, count_per_subsystem=50)
    else:
        print("\n[Step 3/5] No weak subsystems found, skipping data generation")

    # Step 4: 增量微调
    print("\n[Step 4/5] Incremental retraining...")
    incremental_retrain()

    # Step 5: 报告
    print("\n[Step 5/5] Improvement cycle complete.")
    print(f"Reports saved to: {REPORTS_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Self-improvement module")
    parser.add_argument("--analyze", action="store_true", help="Analyze error patterns")
    parser.add_argument("--update-kb", action="store_true", help="Update knowledge base from feedback")
    parser.add_argument("--generate-data", action="store_true", help="Generate targeted training data")
    parser.add_argument("--retrain", action="store_true", help="Run incremental LoRA retraining")
    parser.add_argument("--full-cycle", action="store_true", help="Run full improvement cycle")
    parser.add_argument("--stats", action="store_true", help="Show current statistics")
    args = parser.parse_args()

    if args.stats:
        feedback = load_feedback()
        print(f"Total feedback entries: {len(feedback)}")
        correct = sum(1 for f in feedback if f["feedback"] == "correct")
        print(f"Accuracy: {correct}/{len(feedback)} ({correct/len(feedback):.1%})" if feedback else "No data")
        return

    if args.analyze:
        analyze_errors(load_feedback())
    elif args.update_kb:
        update_knowledge_base()
    elif args.generate_data:
        report_files = sorted(REPORTS_DIR.glob("analysis_*.json")) if REPORTS_DIR.exists() else []
        if report_files:
            report = json.loads(report_files[-1].read_text())
            weak = report.get("weak_subsystems", [])
        else:
            weak = []
            print("No analysis report found. Run --analyze first.")
            return
        generate_targeted_data(weak)
    elif args.retrain:
        incremental_retrain()
    elif args.full_cycle:
        full_improvement_cycle()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
