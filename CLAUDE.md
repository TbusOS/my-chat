# Project Rules

## 目录同步规则 (Critical)

`docs/` 和 `19-ai-training-ppt/interactive/` 两个目录的内容必须保持完全一致。

- `19-ai-training-ppt/interactive/` — 动画源文件目录
- `docs/` — GitHub Pages 部署目录（线上访问版本）

**任何时候**对其中一个目录下的文件进行新增、修改或删除，都必须对另一个目录执行相同操作，确保两边完全同步。

---

## 交互动画设计规范 (Animation Design Skill)

本项目包含 48+ 个 AI 培训交互动画。以下规范确保新增动画风格统一、质量一致。

### 技术栈

- **纯前端单文件**: HTML + CSS + vanilla JS，不使用任何框架或构建工具
- **字体**: Google Fonts — `Noto Sans SC`(中文) + `JetBrains Mono`(代码/数据)
- **不依赖外部库**: 所有动画、图表、交互用原生 CSS animation + requestAnimationFrame + Canvas 实现

### 视觉风格

- **深色科技风**为主 — 背景色 `#050a18` 到 `#0a0e1a` 范围
- **星空背景**: 大部分动画使用随机闪烁星点作为背景装饰
- **渐变标题**: 标题使用 `linear-gradient` + `background-clip: text` 实现彩色渐变
- **发光效果**: 关键元素使用 `box-shadow` 和 `text-shadow` 发光
- **卡片式 UI**: 圆角(10-16px)、半透明背景(`rgba`)、`backdrop-filter: blur`
- **颜色系统**:
  - 蓝色 `#4a9eff` — AI/技术
  - 绿色 `#4ade80` — 成功/开源
  - 紫色 `#a78bfa` — 高级/闭源
  - 金色 `#ffd666` — 重要/特色
  - 青色 `#22d3ee` — 数据/硬件
  - 粉色 `#f472b6` — 安全/警告
  - 橙色 `#fb923c` — 训练/工业

### 动画类型参考

根据内容选择最合适的动画形式（不要拘泥于一种）:

| 类型 | 适用场景 | 参考动画 |
|------|---------|---------|
| 2D小人叙事 | 概念讲解、工作流程 | 05-Agent工作故事 |
| 交互实验室 | 参数调节、实时演示 | 03-参数实验室、31-分词实验室 |
| 擂台对战 | 优缺点对比 | 30-Transformer优缺点擂台 |
| 流水线/工厂 | 多步骤过程 | 32-大模型训练全过程 |
| 时间线 | 历史演进 | 42-神经网络进化史 |
| 多Tab切换 | 多视角/多维度 | 38-GPU并行计算、40-存算一体 |
| 族谱/图谱 | 生态全景、模型关系 | 35-大模型家族图谱 |
| 分层地图 | 技术栈、生态 | 37-AI应用生态全景图 |
| 蓝图构建 | 架构设计、思想实验 | 44-理想神经网络架构 |
| VS对比 | 两种技术路线对比 | 33-Fine-tuning vs RAG、47-Apple vs NVIDIA |

### 必备元素

每个动画**必须包含**:

1. **标题区**: 渐变色大标题 + 灰色副标题
2. **交互控制**: Tab切换 / 按钮 / 滑块等，不能是纯静态页面
3. **术语表(❓按钮)**: 右下角固定位置，点击弹出术语解释面板
   - `position: fixed; bottom: 24px; right: 24px; z-index: 9999`
   - 面板从右侧滑入，半透明深色背景
   - 每个术语: 英文缩写(粗体) + 中文名 + 一句话解释
4. **响应式**: 支持 PC 端为主，移动端基本可用
5. **中文为主**: 所有文字中文，技术术语附英文原名

### 命名规则

- 文件名: `{序号}-{中文主题}.html`，如 `48-数字精度与量化原理.html`
- 序号从现有最大值+1开始
- 新增后必须更新 `index.html`（两个目录都要）

### 新增动画流程

1. 确定主题和最适合的动画类型
2. 创建 HTML 文件到 `19-ai-training-ppt/interactive/`
3. 复制到 `docs/`
4. 更新两个目录的 `index.html`（数量 + 卡片 + footer）
5. 确保术语表(❓)按钮可正常工作（JS 需在 DOM 之后执行或用 DOMContentLoaded）

### 质量检查

- [ ] 动画流畅，无卡顿
- [ ] 术语表按钮可点击、面板可打开/关闭
- [ ] 所有文字可读，无截断
- [ ] 深色背景下对比度足够
- [ ] 两个目录文件完全同步
- [ ] index.html 数量和卡片已更新

---

## 微信公众号视频制作 (Video Production Skill)

本项目支持将交互动画制作成带配音的讲解视频，用于微信公众号发布。使用 `/make-video` 命令即可启动。

### 核心方案：逐帧截图渲染 + 配音时长驱动

```
配音文稿 → edge-tts 生成音频 → 获取每段精确时长(timing.json)
    ↓
修改 HTML 添加 renderOneFrame() → 按 timing.json 的时长切换步骤
    ↓
Playwright 逐帧调用 renderOneFrame() + screenshot (30fps, 2x Retina)
    ↓
ffmpeg 合成帧序列 + 完整配音 → MP4 (天然同步，零偏移)
```

### 为什么这样做

- **完美同步**：视频帧数和音频时长基于同一组 timing 数据，不存在漂移
- **高画质**：逐帧截图 30fps 零丢帧，2560×1600 Retina 分辨率
- **3D 旋转**：Canvas 动画保持自动旋转，视频有立体感
- **全免费**：edge-tts(微软晓晓) + Playwright + ffmpeg，零成本

### 目录结构

```
wechat-articles/
├── .venv/                      ← Python venv (edge-tts)
├── 01-AI基础入门/              ← 第1期
├── 05-硬件与芯片/              ← 第5期
│   ├── output/*.mp4            ← 成品视频
│   ├── article.html            ← 公众号文章
│   ├── images/                 ← 文章配图
│   ├── gen-narration.py        ← 配音生成
│   ├── record.mjs              ← 逐帧录制
│   └── take-screenshots.mjs    ← 步骤截图
└── ...
```

### 发布流程

1. 运行 `/make-video {动画编号}` 生成视频 + 文章 + 截图
2. 在微信公众号后台「素材管理」上传视频和图片
3. 新建图文 → 复制粘贴 article.html 内容 → 插入视频和图片
4. 设置「阅读原文」链接为 `https://tbusos.github.io/my-chat/`
5. 发布

### 依赖安装

```bash
# Python venv + edge-tts（如 .venv 不存在）
python3 -m venv wechat-articles/.venv
wechat-articles/.venv/bin/pip install edge-tts

# Node.js + Playwright
npm install playwright  # 在 wechat-articles 目录下

# ffmpeg（macOS）
brew install ffmpeg
```

### 注意事项

- **不修改 docs/ 原文件**：复制到 wechat-articles/ 后再修改 HTML
- **技术数据要准确**：硬件规格等数据必须搜索确认后再写入
- **不打广告**：不要在配音/文章中特指某个产品（如用"AI助手"代替"ChatGPT"）
- **配音语速**：edge-tts rate="+0%" 正常语速，内容要详细充实
