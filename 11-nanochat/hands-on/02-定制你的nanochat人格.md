# 定制你的 nanochat 人格

## 目标

通过合成数据生成，给你的 nanochat 注入自定义身份和个性。

## 原理

nanochat 的 SFT 阶段决定了模型"怎么说话"。如果在 SFT 数据中混入自定义的对话数据，模型就会学到你定义的身份和风格。

Karpathy 提供了一个完整的指南：[Guide: infusing identity to your nanochat](https://github.com/karpathy/nanochat/discussions/139)

## 步骤

### 1. 生成合成数据

nanochat 提供了合成数据生成脚本：

```bash
python dev/gen_synthetic_data.py
```

你可以修改这个脚本来定义你的模型身份。例如：

- 它叫什么名字
- 它的性格特征
- 它擅长什么领域
- 它的说话风格

### 2. 准备对话数据

对话数据格式是标准的 JSONL，每行一个对话：

```json
{"messages": [{"role": "user", "content": "你是谁？"}, {"role": "assistant", "content": "我是小明，一个热爱编程的 AI 助手。"}]}
{"messages": [{"role": "user", "content": "你擅长什么？"}, {"role": "assistant", "content": "我特别擅长 Python 编程和数据分析。"}]}
```

### 3. 混入 SFT 训练

将自定义数据与默认的 SmolTalk 数据混合，在 SFT 阶段一起训练。

nanochat 的 `tasks/customjson.py` 支持从任意 JSONL 文件加载对话数据。

### 4. 验证效果

```bash
python -m scripts.chat_cli -p "你是谁？"
```

如果一切正常，模型会按照你定义的身份回答。

## 可以定制的方向

| 方向 | 做法 |
|------|------|
| 身份 | "我叫 XX，是一个 XX 领域的专家" |
| 风格 | 幽默 / 严肃 / 简洁 / 详细 |
| 能力 | 混入特定领域的对话数据 |
| 语言 | 混入中文/日文/其他语言的对话 |

## 进阶：教模型新能力

Karpathy 还提供了一个教模型"数草莓里有几个 r"的指南：[Guide: counting r in strawberry](https://github.com/karpathy/nanochat/discussions/164)

核心思路：
1. 生成包含目标能力的训练数据
2. 混入 SFT 阶段
3. 评估模型是否学会

这个方法可以推广到教模型任何特定能力。

## 注意事项

- 自定义数据量不宜过大，否则会"淹没"通用对话能力
- 建议自定义数据占 SFT 数据总量的 5-15%
- 多测试几轮，观察模型是否同时保留了通用能力和自定义身份

---

> **恭喜**！你已经完成了 nanochat 模块的全部内容。回到 [模块首页](../README.md) 查看参考资源。
