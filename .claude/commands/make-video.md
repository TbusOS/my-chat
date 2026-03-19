# /make-video — 为交互动画制作配音讲解视频

为 `docs/` 目录下的交互动画制作带女声配音的高质量讲解视频，用于微信公众号发布。

## 参数

$ARGUMENTS — 动画文件名或编号，如 `56-LLM硬件推理全景` 或 `56`

## 工作流程

### Step 1: 确定动画和目标目录

1. 根据参数找到 `docs/` 下对应的 HTML 文件
2. 确定该动画属于哪一期（按主题分类到对应目录）
3. 将 HTML 复制到 `wechat-articles/{期号}-{主题}/` 目录（不修改 docs 原文件）

### Step 2: 分析动画结构

阅读 HTML 源码，理解：
- 有几个步骤/Tab/场景
- 交互方式（按钮、滑块、Tab 切换等）
- 动画类型（Canvas 3D、CSS animation、SVG 等）
- 关键的 JS 函数（切换步骤、渲染循环等）

### Step 3: 编写配音文稿

在目标目录创建 `gen-narration.py`，包含：
- 每个步骤的详细中文解说文稿（要讲解清楚原理，不要太简短）
- 开场引入 + 结尾引导（提及阅读原文可体验交互版）
- 技术数据要准确，不确定的要搜索确认
- **不要提及具体产品名做广告**（如不要特指 ChatGPT，用"AI助手"或"大模型"代替）

使用 edge-tts（微软晓晓女声 `zh-CN-XiaoxiaoNeural`）生成音频，输出 `timing.json`。

### Step 4: 修改 HTML 支持逐帧渲染

在复制的 HTML 中添加：

```javascript
// 录制模式：逐帧渲染，由外部脚本调用
window.__RECORDING_MODE = false;

window.renderOneFrame = function() {
  // 推进一帧动画（tick++, 渲染场景等）
};

window.enterRecordingMode = function() {
  window.__RECORDING_MODE = true;
  // 隐藏不需要的 UI（导航按钮、术语表按钮等）
  // 保持自动旋转（如果有 3D 场景）
  // 禁用鼠标交互
};

// 切换步骤的函数（如已有 goStep，暴露为 window.goStepSmooth）
```

关键：**不要停止动画自动旋转**（如有），视频中 3D 旋转效果更好看。

### Step 5: 逐帧录制

创建 `record.mjs`，核心逻辑：

```
1. 读取 timing.json 获取每段配音时长
2. 计算总帧数 = 总时长 × 30fps
3. Playwright 打开页面，进入录制模式
4. 循环：
   - 根据当前帧号判断是否需要切换步骤
   - 调用 renderOneFrame() 推进动画
   - page.screenshot() 截图保存
5. ffmpeg 将帧序列 + 完整配音 → MP4
```

参数：
- 帧率: 30fps
- 分辨率: 1280×800，deviceScaleFactor: 2（输出 2560×1600）
- 编码: H.264 -preset slow -crf 20 + AAC 192k

### Step 6: 生成文章截图

创建 `take-screenshots.mjs`，对每个步骤截一张高清图，保存到 `images/` 目录。

### Step 7: 编写公众号文章

创建 `article.html`，要求：
- 每个步骤配详细文字解说 + 对应截图
- 使用准确的技术数据（硬件规格要搜索确认）
- 包含数据对比表格、关键概念高亮
- 底部 CTA 引导到 GitHub Pages 交互版
- 动画数量写"57 个交互动画，持续更新"

### 输出清单

确保最终目录包含：
```
wechat-articles/{期号}-{主题}/
├── output/{动画名}.mp4          ← 成品视频（带配音）
├── article.html                 ← 公众号文章
├── images/                      ← 文章配图（每步骤一张）
├── {动画名}.html                ← 修改后的 HTML（录制用）
├── gen-narration.py             ← 配音生成脚本
├── record.mjs                   ← 逐帧录制脚本
├── take-screenshots.mjs         ← 截图脚本
├── timing.json                  ← 配音时长数据
└── work/                        ← 音频等中间文件
```

## 依赖

- Node.js + playwright（`npm install playwright`）
- Python venv + edge-tts（`wechat-articles/.venv/`）
- ffmpeg

## 技术要点

- **同步原理**：配音时长 → timing.json → HTML 按此时长切换步骤 → 视频帧数与音频帧数一致 → 天然同步
- **逐帧渲染**：不用 Playwright 实时录制（只有~25fps），而是手动调 renderOneFrame+screenshot（精确30fps零丢帧）
- **不动原文件**：docs/ 目录的动画不能修改，复制到 wechat-articles/ 后再改
