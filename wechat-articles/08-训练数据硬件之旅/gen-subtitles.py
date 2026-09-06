"""
从 gen-narration.py 的配音文稿 + timing.json 生成 SRT 字幕文件
按中文标点拆分短句，按字符数比例分配时间
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

# ── 配音文稿（与 gen-narration.py 一致）──
SEGMENTS_TEXT = {
    "intro": (
        "你好，欢迎来到大模型训练·数据硬件之旅。"
        "今天我们要追踪一个训练数据，"
        "看它从硬盘出发，穿越CPU、PCIe通道，"
        "进入GPU的显存，深入Tensor Core完成矩阵运算，"
        "最后在多张GPU之间同步梯度。"
        "这是一次从宏观到微观的完整旅程，"
        "让我们开始吧。"
    ),
    "scene1": (
        "首先来到训练系统的全景。"
        "这是一台典型的AI训练服务器。"
        "顶部是NVMe固态硬盘阵列，存放着海量训练数据。"
        "中间是CPU主板，搭配DDR5内存，"
        "负责数据的读取和预处理。"
        "右边排列着8块GPU——"
        "它们才是训练的主角。"
        "GPU之间通过NVLink高速互联，"
        "和CPU之间通过PCIe总线连接。"
        "一次训练迭代，数据将穿越所有这些硬件组件。"
    ),
    "scene2": (
        "数据的旅程从NVMe固态硬盘内部开始。"
        "我们放大看它的内部结构——"
        "现代NVMe使用3D NAND Flash技术，"
        "数十层硅片像楼房一样垂直堆叠。"
        "每一层都密布着存储单元，"
        "保存着训练用的token序列。"
        "SSD控制器从这些存储层中读出数据，"
        "经由NVMe协议封装后发出。"
        "读取带宽大约是每秒7GB——"
        "听起来很快，但和GPU内部带宽比，"
        "这只是一个起点。"
    ),
    "scene3": (
        "数据到达CPU后，进入预处理工厂。"
        "我们看到CPU die的俯视图——"
        "多个核心同时工作。"
        "每个核心运行一个DataLoader Worker进程，"
        "并行执行四个步骤："
        "读取原始文本，分词，"
        "把不等长的句子填充到统一长度，"
        "最后组成训练用的Batch批次。"
        "核心周围环绕着三级缓存——"
        "L1、L2、L3——"
        "像同心圆一样，越外层容量越大。"
        "DDR5内存提供约90GB每秒的带宽，"
        "源源不断地供给数据。"
    ),
    "scene4": (
        "批次数据准备好了，"
        "现在要通过PCIe通道从CPU传到GPU。"
        "这是一条由16条并行通道组成的高速隧道。"
        "数据粒子在每条通道中飞速穿行。"
        "PCIe Gen5的带宽是每秒64GB——"
        "相比上一代Gen4翻了一倍。"
        "但是，和GPU内部动辄上千GB每秒的带宽相比，"
        "PCIe仍然是整个系统最窄的瓶颈之一。"
        "这就是为什么我们需要尽可能减少"
        "CPU和GPU之间的数据搬运。"
    ),
    "scene5": (
        "数据终于抵达了GPU芯片。"
        "我们从高空俯瞰H100的芯片版图。"
        "中央密布着80个SM——流多处理器——"
        "这是GPU的基本计算单元，"
        "总共包含528个Tensor Core。"
        "四周矗立着6组HBM3存储塔，"
        "提供总计80GB的高带宽显存。"
        "中间环绕着一圈50MB的L2 Cache。"
        "从HBM读数据到L2，再到SM内部——"
        "数据就是沿着这条路径流动的。"
    ),
    "scene6": (
        "让我们放大一组HBM3存储塔，"
        "看看高带宽内存的奥秘。"
        "HBM用的是3D堆叠技术——"
        "8到12层DRAM die像三明治一样垂直叠放。"
        "层与层之间通过数千根TSV硅通孔连接——"
        "这些微小的垂直通道直径只有5微米，"
        "却能让数据在层间高速穿行。"
        "1024位超宽总线，"
        "是普通DDR5的64位总线的16倍。"
        "这就是HBM能达到3.35 TB每秒带宽的秘密——"
        "用空间换带宽，用堆叠换速度。"
    ),
    "scene7": (
        "现在我们来到GPU存储层次的全景——"
        "一座四层金字塔。"
        "最底层是HBM显存，容量最大，80GB，"
        "但访问需要约600个时钟周期。"
        "往上一层是L2 Cache，50MB，"
        "带宽约6TB每秒。"
        "再往上是Shared Memory，"
        "每个SM有228KB，带宽高达19TB每秒。"
        "最顶层是Register File寄存器，"
        "每个SM有256KB，访问几乎零延迟。"
        "数据从底部向顶部攀升，"
        "每上一层，速度就翻几倍。"
        "大模型训练的核心优化思路，"
        "就是让数据尽量留在金字塔的上层。"
    ),
    "scene8": (
        "我们深入到一个SM的内部。"
        "顶部是4个Warp Scheduler——指挥官，"
        "负责把任务分配给下面的计算单元。"
        "中间是128个CUDA Core——通用计算核心，"
        "排列成整齐的蓝色阵列。"
        "中央最醒目的是4个Tensor Core——"
        "金色的大方块。"
        "它们是AI训练的主力引擎，"
        "专门用来做矩阵乘加运算。"
        "底部是Shared Memory和Register File——"
        "这些是离计算单元最近的高速存储。"
        "数据从Shared Memory流入Register，"
        "再分发到各个Core执行计算。"
    ),
    "scene9": (
        "现在我们把镜头对准一个Tensor Core，"
        "看它最核心的操作——"
        "矩阵乘加运算，D等于A乘B加C。"
        "矩阵A从左侧滑入，矩阵B从上方滑入，"
        "两个4乘4矩阵在一个时钟周期内"
        "完成全部64次乘加运算。"
        "输入用FP16半精度——只占16位——"
        "累加器用FP32全精度——32位——"
        "这就是混合精度计算的硬件基础。"
        "一整块H100芯片有528个这样的Tensor Core，"
        "理论算力接近1000万亿次浮点运算每秒。"
    ),
    "scene10": (
        "硬件准备就绪，训练正式开始。"
        "第一步是Embedding——"
        "把每个Token ID变成一个向量。"
        "看左边的Token ID序列——"
        "每个数字就是一个词的编号。"
        "它们射出光线，索引到右边的权重矩阵中，"
        "取出对应的行向量。"
        "这个矩阵有128K行、4096列，"
        "大小约1GB，整个存在HBM中。"
        "数据从HBM搬到L2 Cache，"
        "再进入SM的Shared Memory——"
        "就是我们之前看到的那座存储金字塔。"
    ),
    "scene11": (
        "接下来是Transformer最核心的计算——"
        "自注意力机制。"
        "输入向量通过三组权重矩阵，"
        "分别投影为Query、Key和Value。"
        "红色的Query代表我在找什么，"
        "蓝色的Key代表我是什么，"
        "绿色的Value代表我的内容。"
        "Query和Key做点积，"
        "生成注意力分数矩阵——"
        "颜色越深表示两个词越相关。"
        "经过Softmax归一化后，"
        "用注意力权重对Value加权求和。"
        "所有这些矩阵乘法，"
        "都是由Tensor Core在底层执行的。"
    ),
    "scene12": (
        "标准的注意力计算有一个严重问题——"
        "数据在HBM和SM之间反复搬运。"
        "看左边——Q、K、V从HBM读出，"
        "计算中间结果，写回HBM，"
        "再读出来继续算。"
        "红色箭头来来回回，HBM不堪重负。"
        "FlashAttention彻底改变了这一点。"
        "它把数据分成小块，"
        "在SRAM中一次性完成全部注意力计算，"
        "只把最终结果写回HBM一次。"
        "内存访问减少了10到20倍，"
        "训练速度提升了2到4倍。"
        "这是算法和硬件深度协作的经典案例。"
    ),
    "scene13": (
        "注意力之后是前馈网络——FFN。"
        "数据维度先从4096扩展到16384——"
        "你看粒子数量爆增。"
        "然后经过GELU激活函数的波浪形变换，"
        "再压缩回原来的4096维。"
        "FFN占了Transformer总计算量的三分之二。"
        "重要的是——"
        "每一层的激活值都要写回HBM保存，"
        "因为反向传播时还需要用到它们。"
        "这就是为什么训练比推理消耗更多显存——"
        "所有中间结果都不能丢。"
    ),
    "scene14": (
        "前向传播完成后，Loss函数计算出预测误差。"
        "现在，梯度从Loss端开始逆流——"
        "这就是反向传播。"
        "粉色的梯度粒子从顶部向底部流过每一层。"
        "每经过一层，之前保存的激活值被从HBM读出，"
        "用来计算该层的梯度，"
        "然后梯度又写回HBM。"
        "一个70B参数的模型，仅梯度就占140GB。"
        "加上权重、激活值和优化器状态，"
        "整个HBM被塞得满满当当。"
        "梯度检查点技术可以缓解这个问题——"
        "只保存部分层的激活值，"
        "反向时重新计算其他层——"
        "用33%的额外计算换取60%的内存节省。"
    ),
    "scene15": (
        "在实际训练中，我们不会全用FP32精度。"
        "混合精度训练是关键优化。"
        "主权重用FP32保存——32位，精度最高。"
        "但送入Tensor Core前，先转换成FP16——"
        "只有16位，Tensor Core原生支持。"
        "梯度也用FP16计算，"
        "但为了防止数值下溢，"
        "会先乘以一个很大的缩放因子。"
        "最终梯度转回FP32，"
        "用来更新FP32的主权重。"
        "这样做能节省大约一半的显存，"
        "训练速度提升两到三倍——"
        "代价几乎为零。"
    ),
    "scene16": (
        "单卡的梯度算完了，"
        "但大模型训练使用的是多卡并行。"
        "8张GPU通过NVLink组成环形拓扑。"
        "NVLink的带宽高达每秒900GB，"
        "是PCIe的14倍。"
        "梯度同步使用AllReduce操作，分两步完成。"
        "第一步ReduceScatter——"
        "每张GPU把梯度分成8份，"
        "沿着环发送碎片，同时累加收到的碎片。"
        "经过7轮传递，每张卡持有八分之一梯度的完整累加。"
        "第二步AllGather——"
        "累加好的碎片再沿环传播，"
        "每张卡收集到完整的平均梯度。"
        "整个过程高度流水线化，"
        "通信和计算可以重叠进行。"
    ),
    "scene17": (
        "所有GPU拿到了同步后的梯度，"
        "最后一步——Adam优化器更新权重。"
        "优化器维护着三组数据：梯度g、动量m和方差v。"
        "每次更新，先用指数移动平均更新动量和方差，"
        "然后用它们计算自适应学习率，更新权重。"
        "一个70B参数的模型，"
        "优化器状态本身就占560GB——"
        "超过权重的两倍！"
        "所以必须用多卡分摊。"
        "权重更新完毕，新的Batch从NVMe出发——"
        "整个训练循环，永不停歇。"
    ),
    "outro": (
        "现在你知道了，"
        "一次大模型训练迭代中，"
        "数据从NVMe出发，经CPU预处理，"
        "穿过PCIe进入GPU的HBM，"
        "沿着存储金字塔攀升到Tensor Core，"
        "完成前向传播，反向计算梯度，"
        "通过NVLink在多卡间同步，"
        "最后由优化器更新权重。"
        "每一跳都有巨大的带宽落差——"
        "从7GB每秒到3.35 TB每秒，差了500倍。"
        "如何减少数据搬运、让数据留在高速存储中——"
        "这就是大模型训练优化的核心思想。"
        "点击阅读原文，"
        "可以体验交互版本，亲手旋转3D模型。"
    ),
}


def split_sentences(text, max_len=25):
    """按中文标点拆分为短句"""
    # 先按 。！？ 切分
    parts = re.split(r'([。！？])', text)
    sentences = []
    buf = ''
    for p in parts:
        buf += p
        if p in '。！？':
            sentences.append(buf.strip())
            buf = ''
    if buf.strip():
        sentences.append(buf.strip())

    # 超过 max_len 的在 ，、：；处再切
    result = []
    for s in sentences:
        if len(s) <= max_len:
            result.append(s)
        else:
            sub = re.split(r'([，、：；])', s)
            buf2 = ''
            for sp in sub:
                if len(buf2) + len(sp) > max_len and buf2:
                    result.append(buf2.strip())
                    buf2 = sp
                else:
                    buf2 += sp
            if buf2.strip():
                result.append(buf2.strip())

    # 合并过短片段
    merged = []
    for s in result:
        if merged and len(s) < 6:
            merged[-1] += s
        else:
            merged.append(s)

    return merged


def format_time(seconds):
    """SRT 时间格式 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    timing_path = os.path.join(BASE, "timing.json")
    with open(timing_path, "r", encoding="utf-8") as f:
        timing = json.load(f)

    srt_lines = []
    idx = 1
    cumulative_time = 0.0

    for t in timing:
        seg_id = t["id"]
        duration = t["duration"]
        text = SEGMENTS_TEXT.get(seg_id, "")
        if not text:
            cumulative_time += duration
            continue

        sentences = split_sentences(text)
        total_chars = sum(len(s) for s in sentences)
        if total_chars == 0:
            cumulative_time += duration
            continue

        seg_start = cumulative_time
        for s in sentences:
            char_ratio = len(s) / total_chars
            sent_dur = duration * char_ratio
            start_t = seg_start
            end_t = seg_start + sent_dur

            srt_lines.append(f"{idx}")
            srt_lines.append(f"{format_time(start_t)} --> {format_time(end_t)}")
            srt_lines.append(s)
            srt_lines.append("")

            idx += 1
            seg_start = end_t

        cumulative_time += duration

    srt_path = os.path.join(BASE, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"Generated {idx - 1} subtitle entries -> {srt_path}")


if __name__ == "__main__":
    main()
