#!/usr/bin/env python3
"""
SimpleBPE - 从零实现的 BPE (Byte Pair Encoding) 分词器

用法:
    python simple_bpe.py

原理:
    1. 训练: 将文本转为字节序列，反复合并最高频相邻对
    2. 编码: 按训练顺序应用合并规则，将文本转为 token id
    3. 解码: 将 token id 映射回字节，还原文本
"""


class SimpleBPE:
    """最小 BPE 分词器实现"""

    def __init__(self):
        self.merges = {}   # (int, int) -> int 合并规则
        self.vocab = {}    # int -> bytes 词表

    def train(self, text, vocab_size):
        """训练 BPE 分词器

        Args:
            text: 训练语料
            vocab_size: 目标词表大小 (必须 > 256)
        """
        if vocab_size <= 256:
            raise ValueError("vocab_size 必须大于 256（基础字节词表）")

        token_ids = list(text.encode("utf-8"))
        num_merges = vocab_size - 256
        merges = {}

        for i in range(num_merges):
            counts = self._get_pair_counts(token_ids)
            if not counts:
                break

            best_pair = max(counts, key=counts.get)
            new_id = 256 + i

            token_ids = self._merge(token_ids, best_pair, new_id)
            merges[best_pair] = new_id

        self.merges = merges
        self.vocab = self._build_vocab(merges)
        return merges

    def encode(self, text):
        """将文本编码为 token id 序列

        Args:
            text: 输入文本

        Returns:
            token id 列表
        """
        token_ids = list(text.encode("utf-8"))

        while len(token_ids) >= 2:
            counts = self._get_pair_counts(token_ids)
            best_pair = min(
                counts,
                key=lambda p: self.merges.get(p, float("inf")),
            )

            if best_pair not in self.merges:
                break

            new_id = self.merges[best_pair]
            token_ids = self._merge(token_ids, best_pair, new_id)

        return token_ids

    def decode(self, token_ids):
        """将 token id 序列解码为文本

        Args:
            token_ids: token id 列表

        Returns:
            解码后的文本
        """
        byte_sequence = b"".join(
            self.vocab[tid] for tid in token_ids
        )
        return byte_sequence.decode("utf-8", errors="replace")

    @staticmethod
    def _get_pair_counts(token_ids):
        """统计相邻 token 对的出现频率"""
        counts = {}
        for i in range(len(token_ids) - 1):
            pair = (token_ids[i], token_ids[i + 1])
            counts[pair] = counts.get(pair, 0) + 1
        return counts

    @staticmethod
    def _merge(token_ids, pair, new_id):
        """将序列中所有匹配的 pair 替换为 new_id"""
        result = []
        i = 0
        while i < len(token_ids):
            if (
                i < len(token_ids) - 1
                and (token_ids[i], token_ids[i + 1]) == pair
            ):
                result.append(new_id)
                i += 2
            else:
                result.append(token_ids[i])
                i += 1
        return result

    @staticmethod
    def _build_vocab(merges):
        """根据合并规则构建词表"""
        vocab = {i: bytes([i]) for i in range(256)}
        for (p0, p1), new_id in merges.items():
            vocab[new_id] = vocab[p0] + vocab[p1]
        return vocab


def main():
    """演示 SimpleBPE 的完整用法"""

    corpus = (
        "自然语言处理是人工智能的重要分支。"
        "自然语言理解和自然语言生成是两个核心任务。"
        "分词是自然语言处理的第一步。"
        "好的分词器对模型性能有重要影响。"
        "分词器将文本转换为模型可以理解的数字序列。"
    )

    print("=" * 50)
    print("SimpleBPE 分词器演示")
    print("=" * 50)

    # 训练
    bpe = SimpleBPE()
    target_vocab_size = 300
    print(f"\n[训练] 目标词表大小: {target_vocab_size}")
    print(f"[训练] 语料长度: {len(corpus)} 字符\n")

    merges = bpe.train(corpus, vocab_size=target_vocab_size)
    print(f"\n学到 {len(merges)} 条合并规则")
    print(f"词表大小: {256 + len(merges)}")

    # 编码
    test_texts = [
        "自然语言处理",
        "分词器",
        "人工智能",
        "Hello World",
    ]

    print("\n" + "-" * 50)
    print("[编码/解码测试]")
    print("-" * 50)

    for text in test_texts:
        token_ids = bpe.encode(text)
        decoded = bpe.decode(token_ids)
        utf8_len = len(text.encode("utf-8"))

        print(f"\n原文: '{text}'")
        print(f"  UTF-8 字节数: {utf8_len}")
        print(f"  Token 数量:   {len(token_ids)}")
        print(f"  Token IDs:    {token_ids}")
        print(f"  解码还原:     '{decoded}'")
        print(f"  往返一致:     {'Yes' if decoded == text else 'No'}")


if __name__ == "__main__":
    main()
