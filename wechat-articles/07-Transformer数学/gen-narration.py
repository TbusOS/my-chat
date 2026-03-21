"""
生成 59-Transformer数学工坊 的分段配音，输出 timing.json
"""
import asyncio
import json
import os
import subprocess
import edge_tts

VOICE = "zh-CN-XiaoxiaoNeural"
BASE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(BASE, "work")
os.makedirs(WORK, exist_ok=True)

SEGMENTS = [
    {
        "id": "intro",
        "step": -1,
        "text": (
            "接下来，我们用真实的数字，"
            "一步一步手算一遍Self-Attention。"
            "别担心，我们只用4维向量——"
            "比实际模型的几千维简单得多，"
            "但原理完全一样。"
            "我们的例句是：我爱吃苹果。"
        ),
    },
    {
        "id": "step1",
        "step": 0,
        "text": (
            "第一步，把文字变成数字。"
            "模型不认识汉字，只认识数字。"
            "通过嵌入矩阵，每个词被映射成一个4维向量。"
            "比如「我」变成了1.0、0.5、负0.3、0.8这四个数字。"
            "看右边的条形图——"
            "蓝色的条越长代表正值越大，"
            "粉色的条代表负值。"
            "每个词的条形图都不一样，"
            "这就是它在模型眼中的「数字指纹」。"
        ),
    },
    {
        "id": "step2",
        "step": 1,
        "text": (
            "第二步，位置编码。"
            "Transformer同时看所有词，不知道谁在前谁在后。"
            "所以我们用正弦和余弦函数——"
            "就是你看到的这些动态波形——"
            "给每个位置生成一个独特的信号。"
            "把这个信号加到词向量上，"
            "模型就知道「我」在第一位，"
            "「苹果」在第四位了。"
        ),
    },
    {
        "id": "step3",
        "step": 2,
        "text": (
            "第三步，生成Query向量。"
            "每个词向量乘以一个权重矩阵W_Q，得到Query向量。"
            "以「吃」为例：它的词向量[0.7, 0.3, 0.5, -0.4]，"
            "乘以W_Q矩阵的每一列，得到Q的每个分量。"
            "看这个逐步计算——每个乘法和加法都一目了然。"
            "最终「吃」的Query是[0.4, 0.6, 0.2, -0.2]。"
            "Query代表的是：我在找什么信息？"
        ),
    },
    {
        "id": "step4",
        "step": 3,
        "text": (
            "第四步，同样的方式生成Key和Value。"
            "Key代表我是什么，Value代表我的内容。"
            "注意看条形图——"
            "同一个词的Q、K、V形状完全不同！"
            "因为它们是通过不同的权重矩阵投影出来的。"
            "就像同一个人在不同场合展现不同的面貌。"
        ),
    },
    {
        "id": "step5",
        "step": 4,
        "text": (
            "第五步，计算相似度。"
            "用「吃」的Query和每个词的Key做点积——"
            "就是把对应位置的数字相乘再加起来。"
            "看这个2D向量角度图："
            "Q_吃和K_苹果的箭头方向最接近，"
            "所以它们的点积最大，高达3.2！"
            "而Q_吃和K_我的角度最大，点积只有0.5。"
            "角度越小、点积越大，就代表两个词越相关。"
        ),
    },
    {
        "id": "step6",
        "step": 5,
        "text": (
            "第六步，缩放。"
            "为什么要除以根号d？"
            "因为维度越高，点积就越大。"
            "如果维度是512，点积可能达到几十甚至上百，"
            "送进Softmax就会变成非0即1的极端值，"
            "梯度消失，模型就学不动了。"
            "除以根号4等于2，把数字拉回合理范围。"
            "看这些柱状图是如何缩短的。"
        ),
    },
    {
        "id": "step7",
        "step": 6,
        "text": (
            "第七步，Softmax归一化。"
            "先对每个分数取e的指数，然后除以总和，变成概率。"
            "看这个饼图——苹果独占了71%！"
            "这意味着「吃」把绝大部分注意力都放在了「苹果」上。"
            "Softmax的魔力在于它会放大差距——"
            "原本分数最高的「苹果」，"
            "在归一化之后优势更加明显。"
        ),
    },
    {
        "id": "step8",
        "step": 7,
        "text": (
            "第八步，加权求和。"
            "用这些概率对每个词的Value向量做加权求和。"
            "看色彩混合圆圈——"
            "绿色的「苹果」最大，因为它贡献了71%。"
            "金色的「吃」也有12%的自身贡献。"
            "最终这些加权的Value向量相加，"
            "得到「吃」的新向量。"
            "这个新向量融合了上下文信息——"
            "「吃」现在「知道」自己吃的是苹果了。"
            "这就是一次完整的Self-Attention计算！"
        ),
    },
    {
        "id": "step9",
        "step": 8,
        "text": (
            "第九步，多头注意力。"
            "一组Q、K、V只能学到一种关系模式。"
            "怎么办？"
            "把4维向量切成两份，每份2维，各自独立做注意力。"
            "一个头可能学到了语法关系——"
            "「吃」关注「苹果」，因为苹果是宾语。"
            "另一个头学到了语义关系——"
            "「吃」关注「爱」，因为有人「爱」吃。"
            "最后把两个头的结果拼接起来。"
            "GPT-3用了96个头，每个头128维，总共12288维！"
        ),
    },
    {
        "id": "step10",
        "step": 9,
        "text": (
            "最后一步，残差连接和前馈网络。"
            "注意力的输出加上原始输入——"
            "这就是残差连接，一条保险通道，"
            "确保原始信息不会丢失。"
            "然后经过前馈网络：先升维4倍、"
            "用ReLU激活引入非线性、再降回原来的维度。"
            "看这个完整的流水线——"
            "从输入到Attention、到Add和Norm、"
            "到FFN、再到Add和Norm——"
            "这就是一个完整的Transformer Block。"
            "实际模型会堆叠几十甚至上百个这样的Block，"
            "每一层都让词对上下文的理解更深一层。"
        ),
    },
    {
        "id": "outro",
        "step": -1,
        "text": (
            "恭喜！你已经跟着我们手算了一遍"
            "Transformer Self-Attention的完整流程。"
            "从词向量到QKV投影，从点积到Softmax，"
            "从加权求和到多头注意力。"
            "如果想亲手体验，点击阅读原文，"
            "59个交互动画等你探索。"
        ),
    },
]


async def main():
    timing = []

    for seg in SEGMENTS:
        audio_path = os.path.join(WORK, f"{seg['id']}.mp3")
        communicate = edge_tts.Communicate(seg["text"], VOICE, rate="+0%")
        await communicate.save(audio_path)

        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", audio_path],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())

        timing.append({
            "id": seg["id"],
            "step": seg["step"],
            "duration": round(duration, 2),
        })
        print(f"  {seg['id']}: {duration:.2f}s")

    # Concatenate all audio
    concat_list = os.path.join(WORK, "concat.txt")
    with open(concat_list, "w") as f:
        for t in timing:
            f.write(f"file '{os.path.join(WORK, t['id'] + '.mp3')}'\n")

    full_audio = os.path.join(WORK, "59-full-narration.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c:a", "libmp3lame", "-q:a", "2", full_audio
    ], capture_output=True)

    total = sum(t["duration"] for t in timing)
    print(f"\n  Total: {total:.1f}s")

    # Save timing JSON
    timing_path = os.path.join(BASE, "timing.json")
    with open(timing_path, "w") as f:
        json.dump(timing, f, indent=2, ensure_ascii=False)
    print(f"  Timing saved: {timing_path}")


asyncio.run(main())
