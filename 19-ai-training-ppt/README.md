# AI 培训 PPT — 从零到实战

技术团队 AI 全栈培训材料，84 页 / 3 小时。

## 快速开始

### 安装 Marp CLI

```bash
npm install -g @marp-team/marp-cli
```

### 导出为 HTML（推荐演示用）

```bash
# 导出单个模块
marp slides/01-mindset-shift.md --theme theme/ai-training.css --html -o output/01-mindset-shift.html

# 导出全部模块
for f in slides/*.md; do
  name=$(basename "$f" .md)
  marp "$f" --theme theme/ai-training.css --html -o "output/${name}.html"
done
```

### 导出为 PPTX

```bash
marp slides/01-mindset-shift.md --theme theme/ai-training.css --pptx -o output/01-mindset-shift.pptx
```

### 导出为 PDF

```bash
marp slides/01-mindset-shift.md --theme theme/ai-training.css --pdf -o output/01-mindset-shift.pdf
```

### 本地预览（实时刷新）

```bash
marp slides/01-mindset-shift.md --theme theme/ai-training.css --html --preview
```

## 项目结构

```
19-ai-training-ppt/
├── docs/requirements.md          # 需求文档
├── slides/                       # Marp 幻灯片（7 个模块）
│   ├── 01-mindset-shift.md       # 认知颠覆（15 页）
│   ├── 02-llm-landscape.md       # 主流大模型（12 页）
│   ├── 03-api-and-params.md      # API 与参数（15 页）
│   ├── 04-fine-tuning.md         # 微调（10 页）
│   ├── 05-agents-ecosystem.md    # Agent 生态（15 页）
│   ├── 06-tools-practice.md      # 实战工具链（10 页）
│   └── 07-reflection.md          # 冷思考（6 页）
├── interactive/                   # HTML 交互演示（5 个）
│   ├── temperature-playground.html
│   ├── agent-flow.html
│   ├── mcp-architecture.html
│   ├── llm-api-compare.html
│   └── openclaw-os-analogy.html
├── demos/                         # 现场演示脚本
│   ├── 01-curl-api-call.sh
│   ├── 02-python-api.py
│   ├── 03-cursor-advanced.md
│   └── 04-claude-cli-demo.sh
├── theme/
│   └── ai-training.css        # Marp 自定义主题
└── README.md
```

## 培训流程

| 顺序 | 模块 | 时长 | 形式 |
|------|------|------|------|
| 1 | 认知颠覆 | 30 min | 讲解 + 互动 |
| 2 | 主流大模型 | 20 min | 讲解 |
| 3 | API 与参数 | 40 min | 讲解 + 动手 |
| 4 | 微调 | 20 min | 讲解 |
| 5 | Agent 生态 | 30 min | 讲解 + 互动 |
| 6 | 实战工具链 | 30 min | 全程动手 |
| 7 | 冷思考 | 10 min | 讲解 + Q&A |

## 现场演示准备

```bash
# 设置 API Key（演示前配置）
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"

# 安装 Python 依赖
pip install openai anthropic google-generativeai

# 测试 API 连通性
python demos/02-python-api.py --test
```

## HTML 交互页使用

交互页为独立 HTML 文件，直接用浏览器打开即可，无需服务器：

```bash
open interactive/temperature-playground.html
```

演示时建议用全屏浏览器展示（F11 或 Cmd+Shift+F）。
