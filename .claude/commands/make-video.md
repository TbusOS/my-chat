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

### Step 6: 生成字幕版视频

创建 `gen-subtitles.py`，从配音文稿和 timing.json 生成 SRT 字幕文件：

```python
# 核心逻辑：
# 1. 读取 timing.json 获取每段时间
# 2. 提取 gen-narration.py 中的配音文稿
# 3. 按中文标点拆分为短句（每句 ≤25 字）
#    - 先按 。！？ 切分
#    - 超过 25 字的在 ，、： 处再切
#    - 合并过短片段（<6 字）到前一句
# 4. 按字符数比例分配时间
# 5. 输出 subtitles.srt
```

然后用 ffmpeg 烧录字幕到视频（需要 libass 支持）：

```bash
ffmpeg -i output/原版.mp4 \
  -vf "subtitles=subtitles.srt:force_style='FontName=PingFang SC,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Outline=1,Shadow=0,MarginV=35,Alignment=2'" \
  -c:v libx264 -crf 20 -preset medium -c:a copy \
  output/字幕版.mp4
```

**ffmpeg 字幕依赖：** 需要 `homebrew-ffmpeg/ffmpeg` 版本（自带 libass + freetype）。
如果 `ffmpeg -filters | grep subtitle` 无输出，需要：
```bash
brew tap homebrew-ffmpeg/ffmpeg
brew install homebrew-ffmpeg/ffmpeg/ffmpeg
```

### Step 7: 生成文章截图

创建 `take-screenshots.mjs`，对每个步骤截一张高清图，保存到 `images/` 目录。

截图经验：
- **不要截全屏**，要裁剪/放大到关键视觉元素
- 文字说明在文章里写就行，截图里不需要
- 3D 动画用小视口(800×600) + 高 camZoom 放大粒子
- DOM 页面用 `element.screenshot()` 直接截具体元素（条形图、饼图等）
- 一个步骤内容放不下可以截多张图

### Step 8: 编写公众号文章

创建 `article.html`，**必须使用全 inline style**。

#### 微信公众号 inline style 规则（关键！）

微信公众号编辑器粘贴 HTML 时**只认 inline style**，`<style>` 标签和 CSS class 会被全部丢弃。必须遵守：

1. **禁止 `<style>` 块** — 所有样式写在每个元素的 `style=""` 属性中
2. **禁止 CSS class** — `class="xxx"` 在微信中无效
3. **禁止 `linear-gradient`** — 微信不支持渐变，用 `background-color` 纯色替代
4. **禁止 `::before` / `::after` 伪元素** — 用文字字符替代（如播放按钮用 `&#9654;`）
5. **禁止 `flex` 布局** — 用 `display:inline-block` + `text-align:center` 替代
6. **表格每个 `<th>` `<td>` 都要完整 inline style** — 包括 padding、background-color、border、font 等

#### 常用 inline style 模板

```html
<!-- 深色引言卡片 -->
<div style="background-color:#0f172a;color:#e2e8f0;padding:24px;border-radius:12px;margin-bottom:32px;font-size:15px;line-height:1.9;border-left:4px solid #22d3ee;">
  内容...<strong style="color:#22d3ee;">高亮</strong>
</div>

<!-- 深色截图区 -->
<div style="background-color:#0a0e1a;border-radius:10px;padding:20px;margin:16px 0;text-align:center;border:1px dashed #334155;">
  <img src="images/xxx.png" style="max-width:100%;border-radius:8px;">
  <p style="color:#64748b;font-size:12px;margin-top:8px;">▲ 说明文字</p>
</div>

<!-- 视频播放占位 -->
<div style="background-color:#0a0e1a;border-radius:12px;padding:28px 20px;text-align:center;margin-bottom:20px;">
  <div style="display:inline-block;width:56px;height:56px;background-color:rgba(34,211,238,0.85);border-radius:50%;line-height:56px;font-size:22px;color:#fff;margin-bottom:10px;">&#9654;</div>
  <div style="color:#e8ecf4;font-size:15px;font-weight:600;">视频标题</div>
  <div style="color:#64748b;font-size:12px;margin-top:6px;">（视频需在公众号编辑器中插入 xxx.mp4）</div>
</div>

<!-- 彩色术语标签 -->
<span style="display:inline;font-weight:700;padding:1px 4px;border-radius:3px;color:#dc2626;background-color:#fef2f2;">Query (Q)</span>

<!-- 数值标签 -->
<span style="display:inline-block;background-color:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:2px 8px;font-size:14px;font-weight:600;color:#166534;font-family:'Menlo','Consolas',monospace;">3.2</span>

<!-- 表格表头 -->
<th style="padding:10px 14px;background-color:#0f172a;color:#e2e8f0;font-weight:600;text-align:left;">列名</th>

<!-- 表格单元格（奇数行） -->
<td style="padding:10px 14px;border-bottom:1px solid #f1f5f9;">内容</td>

<!-- 表格单元格（偶数行） -->
<td style="padding:10px 14px;border-bottom:1px solid #f1f5f9;background-color:#f8fafc;">内容</td>

<!-- 分隔线（替代渐变） -->
<div style="height:1px;background-color:#ddd;margin:28px 0;"></div>

<!-- 底部 CTA -->
<div style="background-color:#0f172a;color:#fff;border-radius:12px;padding:24px;text-align:center;margin-top:32px;">
  <h3 style="font-size:18px;margin-bottom:10px;color:#22d3ee;">标题</h3>
  <p style="font-size:14px;color:#94a3b8;line-height:1.8;">描述</p>
  <a style="display:inline-block;margin-top:14px;background-color:#22d3ee;color:#fff;padding:10px 28px;border-radius:24px;font-size:15px;font-weight:600;text-decoration:none;" href="https://tbusos.github.io/my-chat/">点击「阅读原文」立即体验</a>
</div>

<!-- 标签 -->
<span style="display:inline-block;font-size:12px;color:#6b7280;background-color:#f3f4f6;padding:4px 12px;border-radius:12px;margin:4px;">标签</span>
```

#### 文章内容要求

- 每个步骤配详细文字解说 + 对应截图
- 使用准确的技术数据（硬件规格要搜索确认）
- 包含数据对比表格、关键概念高亮
- 底部 CTA 引导到 GitHub Pages 交互版

### 输出清单

确保最终目录包含：
```
wechat-articles/{期号}-{主题}/
├── output/{动画名}.mp4              ← 原版视频（带配音）
├── output/{动画名}-字幕版.mp4       ← 字幕版视频
├── article.html                     ← 公众号文章（全 inline style）
├── images/                          ← 文章配图（每步骤一张）
├── {动画名}.html                    ← 修改后的 HTML（录制用）
├── gen-narration.py                 ← 配音生成脚本
├── gen-subtitles.py                 ← 字幕生成脚本
├── subtitles.srt                    ← SRT 字幕文件
├── record.mjs                       ← 逐帧录制脚本
├── take-screenshots.mjs             ← 截图脚本
├── timing.json                      ← 配音时长数据
└── work/                            ← 音频等中间文件
```

## 依赖

- Node.js + playwright（`npm install playwright`）
- Python venv + edge-tts（`wechat-articles/.venv/`）
- ffmpeg（需要 `homebrew-ffmpeg/ffmpeg` 版本，带 libass + freetype）

## 技术要点

- **同步原理**：配音时长 → timing.json → HTML 按此时长切换步骤 → 视频帧数与音频帧数一致 → 天然同步
- **逐帧渲染**：不用 Playwright 实时录制（只有~25fps），而是手动调 renderOneFrame+screenshot（精确30fps零丢帧）
- **字幕方案**：从 timing.json + 文稿生成 SRT → ffmpeg subtitles 滤镜烧录（PingFang SC 白字+半透明黑底）
- **文章必须全 inline style**：微信公众号编辑器会丢弃 `<style>` 块和 CSS class
- **不动原文件**：docs/ 目录的动画不能修改，复制到 wechat-articles/ 后再改
