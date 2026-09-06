# Pretext 文本布局引擎集成技术方案

> 将 [chenglou/pretext](https://github.com/chenglou/pretext) 的文本测量与布局能力引入 my-chat 动画项目，解决当前固定宽度气泡、文字截断、布局跳变等问题。

---

## 0. 前置背景

### Pretext 核心能力

Pretext 是一个纯 JS 文本布局引擎，核心思路：**用 Canvas `measureText()` 替代 DOM 测量，避免 layout reflow**。

两阶段架构：
- `prepare(text, font)` — 分词 + 测量 + 缓存（~19ms / 500段文本，一次性）
- `layout(prepared, maxWidth, lineHeight)` — 纯算术计算行数和高度（~0.0002ms / 次，无 DOM）

关键 API：
```
prepare(text, font)                    → PreparedText（不透明句柄）
prepareWithSegments(text, font)        → PreparedTextWithSegments（含分段数据）
layout(prepared, maxWidth, lineHeight) → { lineCount, height }
layoutWithLines(prepared, maxWidth, lineHeight) → { lines: [{ text, width }] }
walkLineRanges(prepared, maxWidth, cb) → 逐行回调宽度，不生成字符串
layoutNextLine(prepared, cursor, maxWidth) → 逐行流式布局，每行可不同宽度
```

### my-chat 动画现状

- 纯 HTML 单文件，无构建工具，无外部依赖
- 气泡用固定 `maxWidth`（140px-300px），不根据文字内容适配
- 无文字测量，依赖 CSS `word-wrap: break-word` 自动换行
- 架构图中文字位置硬编码，resize 后可能错位
- 质量检查项中已标注「所有文字可读，无截断」为已知风险

---

## 1. 集成方式

### 问题

my-chat 项目规范要求「不依赖外部库」，所有代码在单个 HTML 文件内。Pretext 是 ESM npm 包（`@chenglou/pretext`），无法直接 `<script src>` 引入。

### 方案：提取精简版内联工具函数

**不引入 Pretext 整包**，而是从 Pretext 的实现中提取核心算法，封装为一个自包含的工具函数集（约 150-200 行），直接内联在需要的 HTML 文件中。

理由：
1. 符合「无外部依赖」的项目规范
2. 我们只需要 Pretext 的子集功能（测量 + 简单换行），不需要 bidi、soft hyphen、pre-wrap 等
3. 中文分词比英文简单（每个字符都是断行点），不需要 `Intl.Segmenter` 的完整能力
4. 避免 CDN 依赖导致的离线不可用

### 提取范围

```javascript
// pretext-lite.js — 内联在 <script> 标签中
// 约 150-200 行，覆盖以下能力：

/**
 * 1. measureTextWidth(text, font) 
 *    - 用 OffscreenCanvas/Canvas 测量文本宽度
 *    - 带缓存，相同 (font, text) 只测量一次
 *
 * 2. countLines(text, font, maxWidth, lineHeight)
 *    - 分词 → 测量 → 贪心换行 → 返回 { lineCount, height }
 *    - 中文逐字符断行，英文按空格断行
 *    - 支持 overflow-wrap: break-word 语义
 *
 * 3. findTightWidth(text, font, maxWidth, lineHeight)
 *    - 二分搜索找最紧容器宽度（不增加行数的前提下最窄）
 *    - 用于气泡 shrinkwrap
 *
 * 4. getLineWidths(text, font, maxWidth)
 *    - 返回每行实际宽度数组
 *    - 用于找最宽行（shrinkwrap）或逐行渲染
 *
 * 5. fitFontSize(text, font, maxWidth, maxLines, minSize, maxSize)
 *    - 二分搜索找最大字号使文字在 maxWidth 内不超过 maxLines 行
 *    - 用于标题自适应
 */
```

### 实现方式

每个需要文本测量的 HTML 文件，在 `<script>` 开头加入工具函数。为避免重复，将工具函数写成可直接复制的代码块，各文件独立包含（符合单文件自包含原则）。

```html
<script>
// ═══ Pretext-Lite: 文本测量工具 ═══
const _measureCache = new Map();
const _canvasCtx = (() => {
  const c = typeof OffscreenCanvas !== 'undefined'
    ? new OffscreenCanvas(1, 1)
    : document.createElement('canvas');
  return c.getContext('2d');
})();

function measureTextWidth(text, font) {
  const key = font + '\0' + text;
  if (_measureCache.has(key)) return _measureCache.get(key);
  _canvasCtx.font = font;
  const w = _canvasCtx.measureText(text).width;
  _measureCache.set(key, w);
  return w;
}

// ... 其余工具函数
// ═══ End Pretext-Lite ═══
</script>
```

---

## 2. 方案一：聊天气泡收缩包裹（Bubble Shrinkwrap）

### 当前问题

05-Agent工作故事.html 等动画中，气泡使用固定 `maxWidth`：

```javascript
// 当前代码
createElement('div', {
  className: 'bubble tail-right',
  style: { left: '90px', bottom: '100px', maxWidth: '200px' },
  textContent: '帮我看看这个项目，最近响应速度变慢了'
});
```

问题：
- 200px 对于短文字（如「收到！」）太宽，气泡右侧大量空白
- 对于长文字可能换行后最后一行很短，气泡底部视觉不紧凑
- 不同文字需要手动调不同的 `maxWidth` 值（140px / 200px / 260px / 300px）

### Pretext 方案

借鉴 Pretext bubbles demo 的二分搜索算法：

```
原始宽度 200px → 文字排3行 → 二分搜索 → 发现 162px 也排3行 → 用 162px
```

### 具体实现

```javascript
/**
 * 找到不增加行数的最紧容器宽度
 * @param {string} text - 气泡文本
 * @param {string} font - CSS font 声明，如 '14px Noto Sans SC'  
 * @param {number} maxWidth - 最大可用宽度（px）
 * @param {number} lineHeight - 行高（px）
 * @returns {{ tightWidth: number, lineCount: number, height: number }}
 */
function shrinkwrapBubble(text, font, maxWidth, lineHeight) {
  // Step 1: 在 maxWidth 下计算基准行数
  const baseLines = countLines(text, font, maxWidth, lineHeight);
  
  // Step 2: 二分搜索最紧宽度
  let lo = 1, hi = Math.ceil(maxWidth);
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    const midLines = countLines(text, font, mid, lineHeight);
    if (midLines.lineCount <= baseLines.lineCount) {
      hi = mid;  // 可以更窄
    } else {
      lo = mid + 1;  // 会多换一行，太窄了
    }
  }
  
  // Step 3: 找最宽行宽度作为最终宽度
  const lineWidths = getLineWidths(text, font, lo);
  const tightWidth = Math.ceil(Math.max(...lineWidths));
  
  return {
    tightWidth,
    lineCount: baseLines.lineCount,
    height: baseLines.lineCount * lineHeight
  };
}
```

### 应用到现有代码

```javascript
// 改造后
function createBubble(text, position, tailDir, cssMaxWidth) {
  const font = '14px "Noto Sans SC", sans-serif';
  const lineHeight = 22;  // 14px * 1.6
  const padding = 36;     // 18px * 2 (左右 padding)
  const contentMax = (cssMaxWidth || 240) - padding;
  
  const { tightWidth } = shrinkwrapBubble(text, font, contentMax, lineHeight);
  const bubbleWidth = tightWidth + padding;
  
  return createElement('div', {
    className: `bubble tail-${tailDir}`,
    style: { 
      ...position,
      width: bubbleWidth + 'px',   // 精确宽度
      maxWidth: (cssMaxWidth || 240) + 'px'  // 保留上限兜底
    },
    textContent: text
  });
}

// 使用
createBubble(
  '帮我看看这个项目，最近响应速度变慢了',
  { left: '90px', bottom: '100px' },
  'right',
  240
);
```

### 适用动画

| 动画 | 气泡数量 | 改造难度 |
|------|---------|---------|
| 05-Agent工作故事 | ~8个 | 低 — 替换 createElement 调用 |
| 17-Skills技能命令 | ~6个 | 低 |
| 01-AI进化之路 | ~4个 | 低 |
| 规划中的对话类动画 | 待定 | 从一开始就用新方案 |

### 效果预期

- 短文字气泡（「收到！」「明白了」）宽度从 140px 缩至 ~70px，视觉更紧凑
- 长文字气泡最后一行不再有大量空白
- 无需手动为每个气泡调 maxWidth

---

## 3. 方案二：文字环绕障碍物布局（Text Around Obstacles）

### 当前问题

28-Transformer架构全景.html 中，模块描述文字使用固定 `detail-body` 面板，弹出覆盖：

```javascript
function showDetail(key) {
  document.getElementById('detailBody').innerHTML = data.body;
  document.getElementById('detailOverlay').classList.add('active');
}
```

规划中的 35-大模型家族图谱、37-AI应用生态全景图、44-理想神经网络架构 等动画需要：
- 文字说明环绕图形节点
- 连线标签在连线旁精确定位
- 多列文字从左列流到右列

### Pretext 方案

借鉴 Pretext dynamic-layout demo 的 `layoutNextLine()` 流式布局：

```
对于每一行：
  1. 计算该行 y 坐标处有哪些障碍物
  2. 从可用区域中去掉障碍物占据的区间
  3. 在剩余最宽区间中排一行文字
  4. 移动光标到下一行
```

### 具体实现

```javascript
/**
 * 在矩形区域中排布文字，绕过障碍物
 * @param {string} text - 要排布的文字
 * @param {string} font - CSS font
 * @param {{ x, y, width, height }} region - 可用区域
 * @param {number} lineHeight - 行高
 * @param {{ x, y, width, height }[]} obstacles - 障碍物矩形数组
 * @returns {{ lines: { text, x, y, width }[] }}
 */
function layoutAroundObstacles(text, font, region, lineHeight, obstacles) {
  const words = segmentText(text);  // 分词
  const widths = words.map(w => measureTextWidth(w, font));
  
  const lines = [];
  let wordIndex = 0;
  let lineTop = region.y;
  
  while (wordIndex < words.length && lineTop + lineHeight <= region.y + region.height) {
    // 计算该行被障碍物遮挡的区间
    const blocked = [];
    for (const obs of obstacles) {
      if (lineTop < obs.y + obs.height && lineTop + lineHeight > obs.y) {
        blocked.push({ left: obs.x, right: obs.x + obs.width });
      }
    }
    
    // 从区域中挖去被遮挡的部分，得到可用的文字槽
    const slots = carveSlots(
      { left: region.x, right: region.x + region.width },
      blocked
    );
    
    if (slots.length === 0) {
      lineTop += lineHeight;
      continue;  // 整行被遮挡，跳过
    }
    
    // 选最宽的槽
    const slot = slots.reduce((a, b) => 
      (b.right - b.left) > (a.right - a.left) ? b : a
    );
    const slotWidth = slot.right - slot.left;
    
    // 贪心排文字
    let lineText = '';
    let lineWidth = 0;
    while (wordIndex < words.length) {
      const needed = lineWidth === 0 ? widths[wordIndex] : widths[wordIndex];
      if (lineWidth + needed > slotWidth && lineWidth > 0) break;
      lineText += words[wordIndex];
      lineWidth += widths[wordIndex];
      wordIndex++;
    }
    
    if (lineText) {
      lines.push({
        text: lineText,
        x: slot.left,
        y: lineTop,
        width: lineWidth
      });
    }
    
    lineTop += lineHeight;
  }
  
  return { lines };
}

/**
 * 从区间中挖去被遮挡的部分
 */
function carveSlots(full, blocked) {
  let slots = [full];
  for (const b of blocked) {
    const next = [];
    for (const s of slots) {
      if (b.right <= s.left || b.left >= s.right) {
        next.push(s);  // 不重叠
      } else {
        if (s.left < b.left) next.push({ left: s.left, right: b.left });
        if (s.right > b.right) next.push({ left: b.right, right: s.right });
      }
    }
    slots = next;
  }
  return slots.filter(s => s.right - s.left > 10);  // 过滤太窄的槽
}
```

### 应用场景

#### 场景 A：模型家族图谱（35号动画）

```javascript
// 文字说明环绕节点卡片
const nodes = [
  { x: 200, y: 100, width: 120, height: 60 },  // GPT-4 节点
  { x: 400, y: 200, width: 120, height: 60 },  // Claude 节点
];

const result = layoutAroundObstacles(
  '大模型的发展经历了从统计模型到深度学习再到大规模预训练的演变过程...',
  '14px "Noto Sans SC"',
  { x: 50, y: 80, width: 600, height: 400 },
  22,
  nodes
);

// 渲染每行文字
result.lines.forEach(line => {
  const span = document.createElement('span');
  span.textContent = line.text;
  span.style.cssText = `
    position: absolute;
    left: ${line.x}px;
    top: ${line.y}px;
    font: 14px "Noto Sans SC";
    color: rgba(148,163,184,0.8);
  `;
  container.appendChild(span);
});
```

#### 场景 B：数据流描述文字（28号、39号动画）

在 Canvas 粒子动画旁用 DOM 文字环绕：

```javascript
// 粒子流区域作为障碍物
const particleRegion = { x: 280, y: 100, width: 80, height: 300 };

const leftText = layoutAroundObstacles(
  '输入嵌入层将每个 Token 转换为高维向量表示...',
  '13px "Noto Sans SC"',
  { x: 40, y: 100, width: 260, height: 300 },
  20,
  [particleRegion]
);
```

### 适用动画

| 动画 | 场景 | 复杂度 |
|------|------|--------|
| 35-大模型家族图谱 | 文字环绕节点卡片 | 中 |
| 37-AI应用生态全景图 | 层级描述文字 | 中 |
| 39-AI训练集群架构 | 拓扑图中的标注 | 中 |
| 44-理想神经网络架构 | 蓝图中的组件说明 | 高 |

---

## 4. 方案三：无 Reflow 高度预计算（Smooth Transitions）

### 当前问题

步骤切换动画中，新内容出现时高度是 CSS 自动计算的，导致：
1. 面板展开时有跳变（从 0 突然到最终高度）
2. `setTimeout(drawConnectionLine, 300)` 这种延时 hack 等 DOM 渲染完再测量
3. 无法做从当前高度到目标高度的平滑过渡

```javascript
// 当前方式：等 DOM 渲染完才能知道高度
function showDetail(key) {
  detailBody.innerHTML = data.body;
  overlay.classList.add('active');
  // 高度由 CSS auto 决定，无法预知
}
```

### Pretext 方案

用 Canvas 测量预计算文字高度，在 DOM 更新前就知道目标高度：

```javascript
/**
 * 预计算文本在给定容器中的布局高度
 * @param {string} text - 文本内容
 * @param {string} font - CSS font
 * @param {number} containerWidth - 容器内部宽度（减去 padding）
 * @param {number} lineHeight - 行高
 * @returns {{ height: number, lineCount: number }}
 */
function predictHeight(text, font, containerWidth, lineHeight) {
  return countLines(text, font, containerWidth, lineHeight);
}
```

### 应用场景

#### 场景 A：Detail Panel 平滑展开（28号动画）

```javascript
function showDetail(key) {
  const data = moduleData[key];
  const panelWidth = 360;   // detail-panel 宽度
  const padding = 48;       // 24px * 2
  const contentWidth = panelWidth - padding;
  const font = '14px "Noto Sans SC"';
  const lineHeight = 25.2;  // 14px * 1.8
  
  // 预计算目标高度
  const plainText = data.body.replace(/<[^>]*>/g, '');  // 去掉 HTML 标签
  const { height } = predictHeight(plainText, font, contentWidth, lineHeight);
  const totalHeight = height + 80;  // 加上标题区高度
  
  // 设置初始高度 → 动画到目标高度
  const panel = document.getElementById('detailPanel');
  panel.style.height = '0px';
  panel.style.overflow = 'hidden';
  panel.style.transition = 'height 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
  
  // 下一帧设置目标高度，触发动画
  requestAnimationFrame(() => {
    panel.style.height = totalHeight + 'px';
  });
  
  // 内容照常填充
  document.getElementById('detailBody').innerHTML = data.body;
}
```

#### 场景 B：手风琴展开（步骤切换）

```javascript
async function goToStep(step) {
  const content = STEPS[step].content;
  const font = '14px "Noto Sans SC"';
  
  // 提前知道新步骤的内容高度
  const { height: newHeight } = predictHeight(content, font, stageWidth, 22);
  
  // 当前高度 → 0（收起旧内容）
  stage.style.height = stage.offsetHeight + 'px';
  stage.style.transition = 'height 0.3s ease-out';
  
  await nextFrame();
  stage.style.height = '0px';
  
  // 等收起动画完成
  await delay(300);
  
  // 替换内容 → 展开到新高度
  clearDynamic();
  stage.style.height = '0px';
  await nextFrame();
  stage.style.height = newHeight + 'px';
  
  // 播放新步骤
  await stepFunctions[step]();
}
```

### 适用动画

| 动画 | 场景 | 改造难度 |
|------|------|---------|
| 28-Transformer架构全景 | Detail Panel 展开 | 低 |
| 05-Agent工作故事 | 步骤间内容切换 | 中 |
| 所有 Tab 切换类动画 | Tab 内容高度变化 | 低 |
| 31-Tokenization分词实验室 | 结果面板动态高度 | 低 |

---

## 5. 方案四：标签/标题字号自适应（Auto Font Sizing）

### 当前问题

- 所有动画标题字号固定（32px），窄屏下可能溢出
- 架构图中模块标签字号固定，节点大小变化时文字不适配
- 时间线节点名称长度不一，短名称浪费空间，长名称被截断

### Pretext 方案

借鉴 dynamic-layout demo 的标题字号二分搜索：

```javascript
/**
 * 二分搜索最大字号，使文字在容器内不超过指定行数
 * @param {string} text - 文本
 * @param {string fontFamily - 字体族，如 '"Noto Sans SC", sans-serif'
 * @param {number} maxWidth - 容器宽度
 * @param {number} maxLines - 最大行数
 * @param {number} minSize - 最小字号
 * @param {number} maxSize - 最大字号
 * @param {object} options
 * @param {boolean} options.noWordBreak - 是否禁止断词（标题模式）
 * @returns {{ fontSize: number, lineCount: number }}
 */
function fitFontSize(text, fontFamily, maxWidth, maxLines, minSize, maxSize, options) {
  let best = minSize;
  let lo = minSize, hi = maxSize;
  
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    const font = `${mid}px ${fontFamily}`;
    const lineHeight = Math.round(mid * 1.3);
    const result = countLines(text, font, maxWidth, lineHeight);
    
    let fits = result.lineCount <= maxLines;
    
    // 标题模式：不允许断词（中文除外）
    if (fits && options?.noWordBreak) {
      const lineWidths = getLineWidths(text, font, maxWidth);
      // 检查是否有行在词中间断开（简化检查）
      fits = lineWidths.every(w => w <= maxWidth);
    }
    
    if (fits) {
      best = mid;
      lo = mid + 1;  // 试更大
    } else {
      hi = mid - 1;  // 试更小
    }
  }
  
  return { fontSize: best, lineCount: countLines(text, `${best}px ${fontFamily}`, maxWidth, Math.round(best * 1.3)).lineCount };
}
```

### 应用场景

#### 场景 A：动画主标题自适应

```javascript
function renderTitle(titleText, containerWidth) {
  const { fontSize } = fitFontSize(
    titleText,
    '"Noto Sans SC", sans-serif',
    containerWidth - 40,  // 两侧 padding
    2,    // 最多2行
    20,   // 最小 20px
    36    // 最大 36px
  );
  
  const titleEl = document.querySelector('.header h1');
  titleEl.style.fontSize = fontSize + 'px';
}

// 响应式
window.addEventListener('resize', () => {
  renderTitle('Transformer 架构全景解析', document.body.clientWidth);
});
```

#### 场景 B：模块标签自适应（架构图）

```javascript
function renderModuleLabel(text, nodeWidth) {
  const { fontSize } = fitFontSize(
    text,
    '"Noto Sans SC"',
    nodeWidth - 16,  // 内边距
    2,    // 最多2行
    10,   // 最小 10px
    14    // 最大 14px
  );
  return `<div style="font-size:${fontSize}px">${text}</div>`;
}
```

#### 场景 C：时间线节点名称（42号动画）

```javascript
// 在固定宽度的时间线节点中自适应字号
const architectures = ['Perceptron', 'Transformer', '循环神经网络 (RNN)', '长短期记忆网络 (LSTM)'];
architectures.forEach(name => {
  const { fontSize } = fitFontSize(name, '"Noto Sans SC"', 100, 1, 10, 14);
  // ...
});
```

### 适用动画

| 动画 | 场景 | 改造难度 |
|------|------|---------|
| 所有动画 | 主标题响应式 | 低 — 统一改 |
| 28-Transformer架构全景 | 模块标签 | 低 |
| 42-神经网络进化史 | 时间线节点名 | 低 |
| 35-大模型家族图谱 | 模型名称标签 | 中 |
| 37-AI应用生态全景图 | 层级标签 | 低 |

---

## 6. 方案五：Canvas 文字精确定位（Typed Text + Cursor）

### 当前问题

03-参数实验室中的打字机效果使用 `innerHTML` 逐字追加 + CSS 光标：

```javascript
el.innerHTML = chunk.replace(/\n/g, '<br>') + '<span class="cursor"></span>';
```

问题：
- 每次追加都触发 innerHTML 解析 + DOM 重建
- 光标位置由 DOM 自动计算（inline-block），有时跳动
- 无法实现光标在文字中间精确定位（如修改/删除效果）

### Pretext 方案

用 Canvas `measureText()` 精确定位光标 x 坐标：

```javascript
/**
 * 计算文本中指定位置的 x 坐标（光标位置）
 * @param {string} text - 完整文本
 * @param {number} charIndex - 光标在第几个字符后
 * @param {string} font - CSS font
 * @returns {number} x 坐标（px）
 */
function getCursorX(text, charIndex, font) {
  const prefix = text.slice(0, charIndex);
  return measureTextWidth(prefix, font);
}

/**
 * 打字机效果 - 逐字追加并精确定位光标
 */
function typeWriter(container, text, font, charDelay) {
  let index = 0;
  const textSpan = container.querySelector('.typed-text');
  const cursor = container.querySelector('.cursor');
  
  function tick() {
    if (index > text.length) return;
    textSpan.textContent = text.slice(0, index);
    
    // 精确光标位置
    const x = getCursorX(text, index, font);
    cursor.style.transform = `translateX(${x}px)`;
    
    index++;
    setTimeout(tick, charDelay);
  }
  
  tick();
}
```

### 适用动画

| 动画 | 场景 | 改造难度 |
|------|------|---------|
| 03-参数实验室 | 输出打字效果 | 中 |
| 31-Tokenization分词实验室 | 分词结果逐字显示 | 中 |
| 规划中的代码演示动画 | 代码逐行输入效果 | 高 |

---

## 7. 方案六：resize 零 Reflow 性能优化

### 当前问题

28-Transformer架构全景.html 中 SVG 连线需要在 resize 时重新计算：

```javascript
// 当前：每次 resize 都读 DOM 位置
function drawConnectionLine() {
  const containerRect = container.getBoundingClientRect();  // 触发 reflow
  const encRect = encOutput.getBoundingClientRect();        // 触发 reflow
  const crossRect = crossMod.getBoundingClientRect();       // 触发 reflow
  // ...
}
window.addEventListener('resize', drawConnectionLine);
```

对于 Canvas 粒子动画 + DOM 标签的复合页面，resize 时大量 `getBoundingClientRect()` 调用导致卡顿。

### Pretext 方案

将文字测量从 resize 路径中移除。把 `prepare` 阶段（一次性测量）和 `layout` 阶段（纯算术）分离：

```javascript
// 页面加载时一次性准备
const prepared = {};
function initTextMeasurements() {
  const labels = getAllLabels();  // 收集所有标签文字
  labels.forEach(({ id, text, font }) => {
    prepared[id] = {
      text,
      font,
      // 预测量各种可能宽度下的行数（或者 resize 时再算，因为 countLines 很快）
    };
  });
}

// resize 时只做纯算术
function onResize() {
  const viewWidth = window.innerWidth;
  
  Object.entries(prepared).forEach(([id, data]) => {
    const maxWidth = viewWidth * 0.3;  // 相对宽度
    const { lineCount, height } = countLines(data.text, data.font, maxWidth, 20);
    
    // 纯数值更新，不读 DOM
    const el = document.getElementById(id);
    el.style.width = maxWidth + 'px';
    el.style.height = height + 'px';
  });
  
  // 连线位置用布局数据计算，不读 getBoundingClientRect
  updateConnectionLines(viewWidth);
}
```

### 性能预期

| 场景 | 当前耗时 | 优化后 |
|------|---------|--------|
| 500 文字块 resize | ~30ms（reflow） | ~0.1ms（纯算术） |
| 连线重绘 | ~5ms（3次 getBoundingClientRect） | ~0.01ms（缓存坐标计算） |
| Canvas + DOM 混合 resize | ~40ms | ~5ms |

---

## 8. 实施路线图

### Phase 1：基础工具 + 气泡改造（1-2天）

**目标**：完成 pretext-lite 工具函数 + 气泡 shrinkwrap

1. 编写 pretext-lite 核心函数（`measureTextWidth`, `countLines`, `getLineWidths`, `shrinkwrapBubble`）
2. 在 05-Agent工作故事.html 中集成并验证
3. 对比改造前后的气泡视觉效果
4. 推广到 01、17 号动画

**验收标准**：
- 气泡宽度自适应文字内容，无明显空白
- 不增加新的外部依赖
- 动画流畅度不受影响

### Phase 2：标题自适应 + 高度预计算（1天）

**目标**：标题字号响应式 + Detail Panel 平滑展开

1. 编写 `fitFontSize` 和 `predictHeight` 函数
2. 在 28-Transformer架构全景.html 的 Detail Panel 中集成
3. 为所有动画的 `.header h1` 添加自适应逻辑

**验收标准**：
- 窄屏下标题不溢出
- Detail Panel 展开有平滑高度过渡动画

### Phase 3：文字环绕障碍物（2-3天）

**目标**：为规划中的复杂布局动画提供文字环绕能力

1. 编写 `layoutAroundObstacles` 和 `carveSlots` 函数
2. 在 35-大模型家族图谱（新动画）中首次使用
3. 验证文字能正确绕过节点卡片流动

**验收标准**：
- 文字在障碍物区域自动避让
- resize 时重新计算布局，文字不重叠
- 支持多个障碍物

### Phase 4：性能优化 + 打字机效果（1-2天）

**目标**：Canvas 文字精确定位 + resize 性能优化

1. 在 03-参数实验室中用 Canvas 测量替代 innerHTML 打字效果
2. 在 28 号等复合动画中优化 resize 路径
3. 性能对比测试

**验收标准**：
- 打字机光标无跳动
- resize 无明显卡顿

---

## 9. 风险与注意事项

### 字体加载时序

Canvas `measureText()` 要求字体已加载。必须在 `document.fonts.ready` 之后才能调用测量函数：

```javascript
document.fonts.ready.then(() => {
  // 字体已加载，可以安全测量
  initTextMeasurements();
});
```

如果字体未加载就测量，Canvas 会用 fallback 字体（如 serif），宽度会不准确。

### 中文字体测量精度

Noto Sans SC 是等宽 CJK 字体，中文字符宽度 = fontSize。但混排时（中文+英文+数字+标点），各字符宽度不同，必须逐字符或逐词测量。

### Emoji 处理

macOS 上 Canvas 测量 emoji 比 DOM 宽（fontSize < 24px 时）。Pretext 有修正逻辑，但我们的动画中 emoji 使用很少，可以先忽略此问题，必要时再加修正。

### 单文件体积

每个 HTML 文件会增加约 150-200 行工具函数代码（约 5KB），对于已经 1000-1600 行的文件来说增幅可控（~15%）。

### 与 CSS 换行行为的一致性

Canvas 测量 + JS 分词的换行结果可能与浏览器 CSS 换行有微小差异（1-2px）。这在 Pretext 中通过浏览器引擎探测和 epsilon 容差处理，但我们的精简版不做这个。对于动画场景，1-2px 差异不影响视觉效果。

---

## 10. 核心代码清单

最终需要实现的函数清单（pretext-lite）：

| 函数 | 用途 | 依赖 | Phase |
|------|------|------|-------|
| `measureTextWidth(text, font)` | Canvas 文字宽度测量 + 缓存 | 无 | 1 |
| `segmentText(text)` | 中英混排分词 | 无 | 1 |
| `countLines(text, font, maxWidth, lineHeight)` | 计算行数和高度 | measureTextWidth, segmentText | 1 |
| `getLineWidths(text, font, maxWidth)` | 获取每行实际宽度 | measureTextWidth, segmentText | 1 |
| `shrinkwrapBubble(text, font, maxWidth, lineHeight)` | 气泡收缩包裹 | countLines, getLineWidths | 1 |
| `predictHeight(text, font, width, lineHeight)` | 预计算高度 | countLines | 2 |
| `fitFontSize(text, fontFamily, maxWidth, maxLines, min, max)` | 字号自适应 | countLines | 2 |
| `layoutAroundObstacles(text, font, region, lineHeight, obstacles)` | 文字环绕障碍物 | measureTextWidth, segmentText, carveSlots | 3 |
| `carveSlots(full, blocked)` | 区间切割 | 无 | 3 |
| `getCursorX(text, charIndex, font)` | 光标精确定位 | measureTextWidth | 4 |
