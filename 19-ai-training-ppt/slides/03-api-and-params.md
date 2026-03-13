---
marp: true
theme: ai-training
paginate: true
header: 'AI 全栈培训'
footer: '第三部分：API 与参数'
---

<!-- _class: divider -->

# 第三部分：手把手调用大模型

## 调用大模型 — API 与参数

15 页 / 40 分钟（全程动手）

---

# API 是什么？

<div class="columns">
<div class="col">

### 餐厅点餐流程

1. **顾客** 看菜单、告诉服务员要什么菜
2. **厨房** 收到订单、开始做菜
3. **服务员** 把做好的菜端上桌

你每天都在用 API —— 前端和后端之间的通信，就是 API 调用。

</div>
<div class="col">

### 大模型 API 流程

1. **你的代码** 发送提示词（prompt）
2. **大模型服务器** 处理请求
3. **大模型** 返回生成的文本

</div>
</div>

<div class="callout-blue">

**核心类比：** 餐厅点餐 = API 请求/响应。顾客（客户端）下单、厨房（服务器）处理、上菜（返回结果），流程完全一致。区别只是：一个传菜单，一个传自然语言。

</div>

---

# 大模型 API 的基本结构

所有大模型 API 都遵循相同的三层结构：

### 1. Endpoint（地址）—— 你要敲哪扇门

```
POST https://api.openai.com/v1/chat/completions
```

### 2. Headers（请求头）—— 你的身份证明

```
Authorization: Bearer sk-xxxxx      # API 密钥
Content-Type: application/json       # 数据格式
```

### 3. Body（请求体）—— 你要说的话 + 参数

```json
{
  "model": "gpt-4o",                          // 选哪个模型
  "messages": [{"role": "user", "content": "你好"}],  // 对话内容
  "temperature": 0.7                           // 参数调节
}
```

> 记住这三层结构，所有大模型 API 都是这个套路，区别只在细节。

---

# 认证与密钥

### API Key = 你的身份证 + 钱包

- 它证明你是谁（认证）
- 它决定你能花多少钱（计费）
- 它泄露了别人就能花你的钱

### 正确做法：使用环境变量

```bash
# 在终端设置（不写进代码）
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxx"
export GOOGLE_API_KEY="AIzaXXXXXXXXXXXXXXXX"
```

```python
# 在代码中读取
import os
api_key = os.environ["OPENAI_API_KEY"]
```

<div class="callout">

**安全铁律：** 永远不要把 API Key 写进代码、提交到 Git、发到群聊里。一旦泄露，立即到官网轮换密钥。

</div>

---

<!-- _class: highlight -->

# temperature — 创造力旋钮

**temperature** 控制模型输出的随机性，范围 **0.0 ~ 2.0**

<div class="columns">
<div class="col">

### 不同温度的效果

| temperature | 表现 | 类比 |
|:-----------:|------|------|
| **0.0** | 确定性输出，每次一样 | 计算器：1+1 永远等于 2 |
| **0.3** | 略有变化，整体稳定 | 老师傅做菜：味道稳定 |
| **0.7** | 适度创意，常用默认值 | 即兴演讲：有框架有发挥 |
| **1.0** | 高度创意，变化较大 | 头脑风暴：天马行空 |
| **>1.5** | 混乱，可能胡言乱语 | 喝多了说胡话 |

</div>
<div class="col">

### 场景推荐

- **代码生成** → `0.0 ~ 0.2`
  确定性最重要，不要"创意"代码
- **数据提取 / 分类** → `0.0`
  要准确，不要变化
- **客服回复** → `0.3 ~ 0.5`
  稳定但不死板
- **创意写作** → `0.7 ~ 1.0`
  需要多样性和新意
- **头脑风暴** → `1.0 ~ 1.5`
  越发散越好

</div>
</div>

> **同一个 prompt，temperature=0 和 temperature=1.5 的输出可能完全不同。**

---

# top_p — 核采样

### 什么是核采样（Nucleus Sampling）？

模型预测下一个词时，会给所有候选词打分（概率）。**top_p** 决定从概率排名前多少的词里选。

### 类比：点菜策略

| top_p | 做法 | 类比 |
|:-----:|------|------|
| **0.1** | 只从概率前 10% 的词里选 | 只看菜单前 3 道招牌菜 |
| **0.5** | 从概率前 50% 的词里选 | 看半页菜单，选熟悉的 |
| **0.9** | 从概率前 90% 的词里选 | 几乎整个菜单都考虑 |
| **1.0** | 所有词都有机会被选 | 连隐藏菜单都看，什么都可能点 |

<div class="callout-blue">

**重要原则：temperature 和 top_p 一般只调一个，不要同时调。**
- 想要更确定的输出 → 降低 temperature（保持 top_p=1.0）
- 想要更聚焦的输出 → 降低 top_p（保持 temperature=1.0）

</div>

---

# top_k — 候选词数量

### 比 top_p 更简单粗暴的筛选

**top_k** 直接限定：只从概率最高的前 K 个词里选。

| top_k | 效果 | 类比 |
|:-----:|------|------|
| **1** | 永远选概率最高的词（贪心） | 永远点最畅销的菜 |
| **10** | 从前 10 个候选词里随机选 | 从 Top 10 热门菜里选 |
| **50** | 从前 50 个候选词里随机选 | 有足够多的选择空间 |
| **100+** | 候选词很多，接近不筛选 | 几乎随便点 |

### 注意：不是所有 API 都支持

| 模型 | 是否支持 top_k |
|------|:--------------:|
| GPT 系列（OpenAI） | 不支持 |
| Claude 系列（Anthropic） | 支持 |
| Gemini 系列（Google） | 支持 |

> **top_k vs top_p：** top_k 按数量截断，top_p 按概率截断。top_p 更灵活，是目前主流做法。

---

# max_tokens — 回答长度上限

### Token 是什么？

Token 是大模型处理文本的最小单位，不是字也不是词，而是介于两者之间的"片段"。

| 内容 | 大约 Token 数 | 说明 |
|------|:------------:|------|
| 1 个中文字 | **1 ~ 2** tokens | "你好" ≈ 2 tokens |
| 1 个英文单词 | **≈ 1** token | "hello" = 1 token |
| 一段代码（100 行） | **300 ~ 800** tokens | 视代码复杂度而定 |
| 一篇文章（1000 字） | **1000 ~ 2000** tokens | 中文消耗更多 token |

### 关键约束

```
输入 tokens + 输出 tokens ≤ 模型上下文窗口
```

- GPT-4o：128K 上下文，最大输出 16K tokens
- Claude Sonnet：200K 上下文，最大输出 8K tokens
- 设置 `max_tokens` = 你愿意为一次回复付费的上限

<div class="callout">

**成本公式：** 费用 = (输入 tokens x 输入单价) + (输出 tokens x 输出单价)。输出通常比输入贵 2~4 倍，所以 max_tokens 直接影响你的账单。

</div>

---

# 其他重要参数

| 参数 | 作用 | 值域 | 什么时候用 |
|------|------|------|-----------|
| **frequency_penalty** | 降低已出现词的重复概率 | -2.0 ~ 2.0 | 模型一直重复同样的话时，调到 0.5~1.0 |
| **presence_penalty** | 鼓励模型提到新话题 | -2.0 ~ 2.0 | 希望回答更丰富多样时，调到 0.5~1.0 |
| **stop** | 遇到指定字符串就停止生成 | 字符串数组 | 需要精确控制输出结尾时，如 `["\n\n", "END"]` |
| **seed** | 固定随机种子（尽量可复现） | 整数 | 调试时想复现同样的输出 |

### 实际使用建议

- **大部分场景**：默认值就好，不用动
- **模型输出太啰嗦**：提高 `frequency_penalty` 到 0.5
- **模型总是重复**：提高 `presence_penalty` 到 0.6
- **需要可复现的结果**：设 `seed` + `temperature=0`

> 这些参数是"微调旋钮"，先用好 temperature 和 top_p，再考虑这些。

---

<!-- _class: highlight -->

# 参数组合秘方

不同场景的推荐参数搭配（直接抄作业）：

| 场景 | temperature | top_p | max_tokens | 其他 |
|------|:-----------:|:-----:|:----------:|------|
| **代码生成** | 0 | 0.95 | 4096 | `seed` 固定以复现 |
| **代码审查** | 0 | 0.95 | 2048 | — |
| **创意写作** | 0.8 | 0.95 | 4096 | `presence_penalty=0.6` |
| **数据提取 / 分类** | 0 | 1.0 | 1024 | `stop` 控制输出格式 |
| **客服回复** | 0.3 | 0.9 | 1024 | `frequency_penalty=0.3` |
| **翻译** | 0.1 | 0.95 | 4096 | — |
| **头脑风暴** | 1.2 | 0.95 | 4096 | `presence_penalty=1.0` |
| **摘要总结** | 0.2 | 0.9 | 2048 | — |

<div class="callout-blue">

**新手建议：** 先从默认参数开始（temperature=1.0, top_p=1.0），然后根据结果微调。代码任务直接 temperature=0，创意任务调到 0.7~1.0。

</div>

---

# GPT API 格式（OpenAI）

### 请求示例

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "system", "content": "你是资深后端工程师"},
      {"role": "user", "content": "解释RESTful API设计原则"}
    ],
    "temperature": 0.3
  }'
```

### OpenAI 特点

- **认证方式：** `Authorization: Bearer <key>` 标准 OAuth 风格
- **消息格式：** `messages` 数组，包含 `system` / `user` / `assistant` 三种角色
- **工具调用：** `tools` + `function calling`，生态最成熟
- **模型选择：** `gpt-4o`（主力）、`gpt-4o-mini`（便宜快速）、`o3`（强推理）

> OpenAI 是最早开放 API 的厂商，文档最全，社区最大，遇到问题最容易找到答案。

---

# Claude API 格式（Anthropic）

### 请求示例

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "system": "你是资深后端工程师",
    "messages": [
      {"role": "user", "content": "解释RESTful API设计原则"}
    ]
  }'
```

### Claude 特点

- **认证方式：** `x-api-key` 自定义头 + `anthropic-version` 版本号（必填）
- **消息格式：** `system` 是顶层字段（不在 messages 里），`messages` 只有 `user` / `assistant`
- **工具调用：** `tool_use` blocks，与 OpenAI 的 `function calling` 语法不同
- **强项：** 200K 超长上下文、代码能力强、安全对齐好

> **关键差异：** Claude 的 `system` 提示词不在 messages 数组里，是单独的顶层字段。`max_tokens` 是必填参数。

---

# Gemini API 格式（Google）

### 请求示例

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GOOGLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "system_instruction": {
      "parts": [{"text": "你是资深后端工程师"}]
    },
    "contents": [
      {
        "role": "user",
        "parts": [{"text": "解释RESTful API设计原则"}]
      }
    ],
    "generationConfig": {
      "temperature": 0.3,
      "maxOutputTokens": 1024,
      "topP": 0.95,
      "topK": 40
    }
  }'
```

### Gemini 特点

- **认证方式：** API Key 直接放在 URL 参数里（`?key=`）
- **消息格式：** `contents` 数组，每条消息用 `parts` 包裹，支持多模态混排
- **参数命名：** `maxOutputTokens`（驼峰）、`topP`、`topK` —— 命名风格不同
- **强项：** 原生多模态、200 万 token 超长上下文、免费额度最多

---

<!-- _class: highlight -->

# 三大 API 关键差异总结

| 对比项 | OpenAI (GPT) | Anthropic (Claude) | Google (Gemini) |
|--------|:------------:|:------------------:|:---------------:|
| **认证方式** | `Authorization: Bearer` | `x-api-key` 头 | URL 参数 `?key=` |
| **System 提示词** | `messages` 里的 `system` 角色 | 顶层 `system` 字段 | `system_instruction.parts` |
| **消息格式** | `messages[].content` | `messages[].content` | `contents[].parts[].text` |
| **工具调用** | `function calling` | `tool_use` blocks | `functionDeclarations` |
| **流式输出** | `stream: true` + SSE | `stream: true` + SSE | `streamGenerateContent` |
| **多模态输入** | `image_url` 在 content 里 | `image` media type | `parts` 里混排 |
| **max_tokens** | 可选（有默认值） | **必填** | `maxOutputTokens`（可选） |
| **支持 top_k** | 不支持 | 支持 | 支持 |

<div class="callout-blue">

**实战建议：** 三家 API 核心逻辑一样（发 prompt，收回答），差异在认证方式和字段命名。建议用 Python SDK 封装差异，代码更干净。

</div>

---

<!-- _class: demo -->

# 动手时间

### 接下来我们要做什么？

<div class="columns">
<div class="col">

### 实验 1：curl 调用

- 打开终端
- 分别用 curl 调用 GPT / Claude / Gemini
- 感受三家 API 的格式差异
- 调整 temperature，观察输出变化

</div>
<div class="col">

### 实验 2：Python SDK

- 用 Python SDK 调用三大模型
- 同一个 prompt，不同参数
- 对比 temperature=0 vs temperature=1.0 的输出
- 测试 max_tokens 对回复长度的影响

</div>
</div>

<div class="callout">

**准备工作：**
1. 确认环境变量已设置：`echo $OPENAI_API_KEY`
2. 确认 Python 依赖已安装：`pip install openai anthropic google-generativeai`
3. 打开终端，准备好了吗？

**现在请打开你的终端...**

</div>
