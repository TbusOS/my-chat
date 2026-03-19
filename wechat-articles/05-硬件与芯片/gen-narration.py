"""
生成 56-LLM硬件推理全景 的分段配音，输出 timing.json
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
            "你有没有想过，当你向AI助手提一个问题的时候，"
            "背后的大模型到底在硬件层面经历了什么？"
            "CPU和GPU各自扮演什么角色？"
            "今天我们就来拆解这个过程。"
            "从磁盘到显存，从CPU到GPU，"
            "看看数据在硬件之间的完整旅程。"
        ),
    },
    {
        "id": "step1",
        "step": 0,
        "text": (
            "第一步，模型加载。"
            "整个加载过程由CPU发起和协调。"
            "CPU的内存控制器首先将模型文件从SSD读入DDR内存，速度大约7GB每秒。"
            "然后CPU通过DMA传输，将数据经PCIe总线送入GPU。"
            "PCIe 4.0的带宽可以达到32GB每秒。"
            "最终数据落入GPU的HBM高带宽显存。"
            "以一个70B参数的模型为例，FP16半精度下需要140GB的空间。"
            "一张80GB显存的A100根本装不下，"
            "所以要么做量化压缩，要么用多张卡分担。"
        ),
    },
    {
        "id": "step2",
        "step": 1,
        "text": (
            "第二步，Prefill预填充。"
            "这一步CPU和GPU有明确的分工。"
            "CPU先负责Tokenization，把你输入的文本切分成一个个Token ID。"
            "这些Token ID通过PCIe发送给GPU。"
            "GPU的Tensor Core接收后，一次性并行处理所有Prompt Token，执行大规模矩阵乘法。"
            "这个阶段CPU基本处于空闲等待状态，瓶颈完全在GPU的计算能力上。"
            "算力利用率高达80%，但内存带宽只用了30%，是典型的计算密集型。"
            "一个很反直觉的事实是：处理1000个Token和处理10个Token，耗时几乎没什么区别。"
            "因为Tensor Core是高度并行的，它可以同时处理大量数据。"
        ),
    },
    {
        "id": "step3",
        "step": 2,
        "text": (
            "第三步，Decode逐Token生成。"
            "到了生成阶段，情况彻底反转，CPU和GPU的协作也变得更加紧密。"
            "GPU每一步只产出一个Token的概率分布，也就是logits。"
            "这些logits通过PCIe传回CPU，由CPU执行采样策略，选出最终的Token。"
            "CPU还负责请求调度，比如在vLLM框架中管理多个并发请求的优先级。"
            "然后CPU把选出的Token ID送回GPU，继续下一轮生成。"
            "在GPU侧，为了算出每一步的logits，必须把全部140GB的模型权重从显存读一遍。"
            "此时HBM的带宽利用率高达95%，而Tensor Core的算力只用了可怜的5%。"
            "这就是典型的内存瓶颈。"
            "大模型为什么是一个字一个字蹦出来的？不是计算不够快，而是数据搬运太慢了。"
        ),
    },
    {
        "id": "step4",
        "step": 3,
        "text": (
            "第四步，KV Cache增长。"
            "为了避免重复计算已经生成的Token，"
            "大模型会把每个Token对应的Key和Value向量缓存在GPU显存中。"
            "这就是KV Cache。"
            "问题在于，KV Cache的大小随序列长度线性增长。"
            "以70B模型为例，不使用GQA优化时，4K上下文的KV Cache大约占10GB。"
            "128K上下文则高达320GB，远超单卡容量。"
            "现代模型使用GQA分组查询注意力来优化，可以将KV Cache压缩到原来的八分之一。"
            "在推理框架中，CPU负责KV Cache的内存调度。"
            "比如vLLM的PagedAttention就是由CPU来管理显存中Cache块的分配和淘汰。"
        ),
    },
    {
        "id": "step5",
        "step": 4,
        "text": (
            "第五步，带宽瓶颈可视化。"
            "我们用一个高速公路的比喻来理解这个问题。"
            "GPU的算力就像一条8车道的高速公路，非常宽敞。"
            "但在Decode阶段，只有一辆车在上面跑，7条车道都空着。"
            "而HBM的带宽就像一条只有2车道的乡间小路，已经堵得水泄不通。"
            "这个矛盾的本质是：每个Token的计算量太少，数据搬运量太大。"
            "优化方向有两个。"
            "一是量化，用INT8或INT4来减少每次搬运的数据量。"
            "二是推测解码，一次猜多个Token，增加每步的计算量。"
        ),
    },
    {
        "id": "step6",
        "step": 5,
        "text": (
            "第六步，多GPU张量并行。"
            "当一张卡装不下整个模型时，"
            "可以用Tensor Parallelism把权重矩阵切分到多张GPU上。"
            "每张GPU只负责计算自己的那一部分，"
            "然后通过NVLink高速互联执行AllReduce操作来汇总结果。"
            "以H100为例，NVLink第四代的双向带宽高达900GB每秒，是PCIe 4.0的28倍。"
            "即使是A100的NVLink 3.0，也有600GB每秒。"
            "4张卡并行时，每张卡只需要读取四分之一的权重，"
            "Decode的延迟可以降低接近4倍。"
            "这就是为什么高端推理服务器都会配备NVLink互联的多卡方案。"
        ),
    },
    {
        "id": "outro",
        "step": -1,
        "text": (
            "以上就是大模型推理时，数据在硬件间流动的完整旅程。"
            "从SSD到显存的加载，到Prefill的并行计算，"
            "再到Decode阶段的带宽瓶颈，KV Cache的显存博弈，"
            "最后用多卡并行来突破单卡的物理限制。"
            "每一步都是计算和带宽的精密配合。"
            "想自己操作探索每个步骤？"
            "点击文末阅读原文，体验完整的交互版本。"
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

    full_audio = os.path.join(WORK, "56-full-narration.mp3")
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
