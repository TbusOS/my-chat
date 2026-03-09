"""
内核专家交互式命令行

支持：
- 提问并获取回答
- 对回答进行反馈（👍/👎/修正）
- 查看统计信息
- 触发自我改进

用法:
    python serve/api/chat.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from serve.api.engine import KernelExpertEngine, Confidence


def print_answer(answer):
    """格式化打印回答"""
    # 置信度标记
    confidence_icons = {
        Confidence.CERTAIN: "[CERTAIN]   来自知识库精确匹配",
        Confidence.HIGH: "[HIGH]      模型有较高把握",
        Confidence.POSSIBLE: "[POSSIBLE]  模型不太确定",
        Confidence.UNSURE: "[UNSURE]    建议验证",
    }

    source_icons = {
        "knowledge_base": "知识库",
        "local_model": "本地模型",
        "local_model+rag": "本地模型 + RAG 源码检索",
        "opus_api": "Opus API",
    }

    print(f"\n{'─' * 60}")
    print(f"  置信度: {confidence_icons.get(answer.confidence, answer.confidence.value)}")
    print(f"  来源:   {source_icons.get(answer.source, answer.source)}")

    if answer.knowledge_refs:
        print(f"  参考:   {', '.join(answer.knowledge_refs)}")
    if answer.exec_context:
        print(f"  上下文: {answer.exec_context}")
    if answer.can_sleep is not None:
        print(f"  可睡眠: {'是' if answer.can_sleep else '否'}")

    print(f"  延迟:   {answer.latency_ms:.0f}ms")
    print(f"{'─' * 60}")
    print(f"\n{answer.text}\n")


def main():
    engine = KernelExpertEngine()

    print("=" * 60)
    print("  Linux Kernel Expert (ARM32/ARM64)")
    print("  输入问题开始提问，输入 /help 查看命令")
    print("=" * 60)

    last_question = ""
    last_answer = None

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        # 命令处理
        if user_input.startswith("/"):
            cmd = user_input.lower()

            if cmd == "/help":
                print("""
命令:
  /help          显示帮助
  /stats         显示统计信息
  /good          标记上一个回答为正确
  /bad           标记上一个回答为错误
  /fix <text>    提交正确答案修正
  /improve       触发自我改进分析
  /quit          退出
                """)

            elif cmd == "/stats":
                stats = engine.get_stats()
                print(f"\n总反馈: {stats['total_feedback']}")
                print(f"准确率: {stats['accuracy']:.1%}")
                print(f"待审核更新: {stats['pending_updates']}")
                print(f"按来源准确率:")
                for source, acc in stats.get("by_source_accuracy", {}).items():
                    print(f"  {source}: {acc:.1%}")

            elif cmd == "/good":
                if last_answer:
                    engine.submit_feedback(last_question, last_answer, "correct")
                    print("  Feedback recorded: correct")
                else:
                    print("  No previous answer to rate")

            elif cmd == "/bad":
                if last_answer:
                    engine.submit_feedback(last_question, last_answer, "incorrect")
                    print("  Feedback recorded: incorrect")
                    print("  Use /fix <correct answer> to provide the right answer")
                else:
                    print("  No previous answer to rate")

            elif cmd.startswith("/fix "):
                correction = user_input[5:].strip()
                if last_answer and correction:
                    engine.submit_feedback(last_question, last_answer, "incorrect", correction)
                    print("  Correction recorded. Will be used for knowledge base update.")
                else:
                    print("  Usage: /fix <correct answer text>")

            elif cmd == "/improve":
                print("  Running self-improvement analysis...")
                import subprocess
                subprocess.run([
                    sys.executable,
                    str(Path(__file__).parent.parent / "feedback/self_improve.py"),
                    "--analyze",
                ])

            elif cmd == "/quit" or cmd == "/exit":
                print("Bye!")
                break

            else:
                print(f"  Unknown command: {cmd}. Type /help for help.")

            continue

        # 正常提问
        last_question = user_input
        last_answer = engine.ask(user_input)
        print_answer(last_answer)

        # 提示反馈
        if last_answer.confidence in (Confidence.POSSIBLE, Confidence.UNSURE):
            print("  (回答不太确定，建议用 /good 或 /bad 反馈，帮助系统改进)")


if __name__ == "__main__":
    main()
