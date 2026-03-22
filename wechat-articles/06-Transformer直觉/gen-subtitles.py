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
        "欢迎来到Transformer原理3D直觉之旅。"
        "我们将用3D动画，一步步展示，"
        "Transformer注意力机制是怎么被推导出来的。"
    ),
    "step1": (
        "在机器眼中，文字只是冰冷的编号。"
        "看这些字——我、爱、吃、苹果——"
        "它们在黑暗中孤零零地漂浮。"
        "机器只知道「我」是编号1024，"
        "「苹果」是编号1975，"
        "但完全不知道它们之间有什么关系。"
        "我们需要找到一种方法，"
        "让机器真正理解文字的含义。"
    ),
    "step2": (
        "第一步的突破是词向量。"
        "我们把每个编号映射到高维空间中的一个点。"
        "看，当3D网格出现，"
        "每个字都亮起了自己的颜色，"
        "飞到了空间中属于自己的位置。"
        "相似的词会靠得很近——"
        "「吃」和「苹果」在空间中是邻居，"
        "因为它们在大量文本中经常一起出现。"
        "但这还不够。"
    ),
    "step3": (
        "问题来了。"
        "「苹果」在「我爱吃苹果」里是水果，"
        "在「苹果手机真好用」里是科技公司。"
        "但它在向量空间中只有一个固定位置！"
        "看这个闪烁的粒子——"
        "它在水果和科技之间犹豫不决。"
        "没有上下文信息，"
        "同一个词向量无法表达不同的含义。"
        "我们必须让每个词能看到周围的词。"
    ),
    "step4": (
        "最直接的想法："
        "让「吃」去看句子里的所有词，"
        "把所有信息等权混合。"
        "但你看这些连线——"
        "每条一样粗，一样亮。"
        "25%的「我」、25%的「爱」、"
        "25%的「吃」、25%的「苹果」。"
        "结果就像把所有颜料等量混合，"
        "只能得到一团灰色。"
        "这不对——"
        "「吃」应该更关注「苹果」，"
        "因为那是它要吃的东西。"
    ),
    "step5": (
        "现在释放注意力——看！"
        "连线发生了变化。"
        "「吃」到「苹果」的连线变得又粗又亮，"
        "而「吃」到「我」的连线变得很细很暗。"
        "这就是注意力机制的核心思想："
        "不同的词应该得到不同的权重。"
        "相关性越高，权重越大。"
        "那问题来了——"
        "这些权重是怎么计算出来的？"
    ),
    "step6": (
        "我们发现，"
        "用词本身的向量来计算相似度有个问题："
        "一个词同时要表达「我在找什么」和「我是什么」两个角色。"
        "所以每个词分裂出两个影子——"
        "红色的Q代表「我在找什么」，"
        "绿色的K代表「我是什么」。"
        "看这些Q和K之间的匹配线——"
        "「吃」的Q在问「谁是我的搭配对象」，"
        "而「苹果」的K在回答「我是一个可以被吃的东西」。"
    ),
    "step7": (
        "Q找到了K，但我们还需要传递实际的内容。"
        "这就是金色的V——Value值向量。"
        "看这些金色粒子沿着注意力通道流动，"
        "从权重高的词流向「吃」。"
        "苹果贡献了最多的信息内容，"
        "因为它的注意力权重最高。"
        "Q负责提问，K负责匹配，V负责交付内容——"
        "这三个角色缺一不可。"
    ),
    "step8": (
        "一组QKV只能捕捉一种关系模式。"
        "看现在——"
        "场景分裂成了四个平行层，"
        "每一层的连线模式完全不同。"
        "第一层关注语法关系，"
        "第二层关注语义关系，"
        "第三层关注位置关系，"
        "第四层关注情感关系。"
        "就像多个侦探从不同角度调查同一个案件，"
        "最后把线索合并，"
        "就能看到完整的真相。"
    ),
    "step9": (
        "最终，所有平行层合并回来。"
        "看每个粒子——"
        "它们现在比刚开始时亮了很多，"
        "而且有了多彩的光晕。"
        "这代表每个词都吸收了丰富的上下文信息。"
        "「苹果」终于知道自己在这句话里是水果，"
        "「吃」知道自己要吃的是苹果。"
        "这就是Transformer自注意力机制的全部——"
        "从一个简单的问题出发，"
        "一步步推导出来的优雅解决方案。"
    ),
    "outro": (
        "以上就是Transformer注意力机制的直觉推导。"
        "如果你想亲手体验这个3D动画，"
        "可以在阅读原文中找到交互版。"
        "下一个视频，"
        "我们将用真实数字，"
        "一步步手算Self-Attention的每一个数学操作。"
    ),
}


def split_into_phrases(text):
    """按中文标点拆分成短句，保留标点在句尾"""
    # 在主要断句标点后切分
    parts = re.split(r'(?<=[。！？；])', text)
    phrases = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 如果太长（>25字），在逗号处再切一刀
        if len(part) > 25:
            sub_parts = re.split(r'(?<=[，、：])', part)
            # 合并过短的片段（<8字）到前一句
            merged = []
            for sp in sub_parts:
                sp = sp.strip()
                if not sp:
                    continue
                if merged and len(merged[-1]) < 8:
                    merged[-1] += sp
                else:
                    merged.append(sp)
            phrases.extend(merged)
        else:
            # 合并过短的片段到前一句
            if phrases and len(part) < 6:
                phrases[-1] += part
            else:
                phrases.append(part)
    return phrases


def format_time(seconds):
    """格式化为 SRT 时间戳 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    # 读取 timing
    with open(os.path.join(BASE, "timing.json")) as f:
        timing = json.load(f)

    srt_lines = []
    sub_index = 1
    seg_start = 0.0

    for seg in timing:
        seg_id = seg["id"]
        seg_duration = seg["duration"]
        text = SEGMENTS_TEXT[seg_id]

        phrases = split_into_phrases(text)
        total_chars = sum(len(p) for p in phrases)

        # 按字符数比例分配时间
        cursor = seg_start
        for phrase in phrases:
            char_ratio = len(phrase) / total_chars
            phrase_duration = seg_duration * char_ratio
            start = cursor
            end = cursor + phrase_duration

            srt_lines.append(f"{sub_index}")
            srt_lines.append(f"{format_time(start)} --> {format_time(end)}")
            srt_lines.append(phrase)
            srt_lines.append("")

            sub_index += 1
            cursor = end

        seg_start += seg_duration

    # 写入 SRT 文件
    srt_path = os.path.join(BASE, "subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"Generated {sub_index - 1} subtitle entries")
    print(f"Saved to: {srt_path}")
    print(f"Total duration: {format_time(seg_start)}")


if __name__ == "__main__":
    main()
