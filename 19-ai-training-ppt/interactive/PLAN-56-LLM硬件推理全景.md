# 56-LLM硬件推理全景.html — 开发计划

## 概述

一个 3D 交互动画，展示大语言模型推理时数据在硬件之间的完整流动过程。
用户可以逐步了解：模型加载、Prefill、Decode、KV Cache、带宽瓶颈、多GPU并行。

## 文件位置

- 源文件: `19-ai-training-ppt/interactive/56-LLM硬件推理全景.html`
- 同步: `docs/56-LLM硬件推理全景.html`
- 更新: 两个目录的 `index.html`（数量 55→56，新增卡片到"硬件深度与未来"章节，footer 同步）

## 设计规格

### 3D 可视化

- **等轴测 3D**：Canvas 渲染，透视投影，拖拽旋转 + 滚轮缩放
- **硬件组件**：CPU、DDR 内存条、PCIe 总线、GPU 芯片、HBM/VRAM、Tensor Core 阵列
- **数据粒子**：彩色粒子沿硬件间路径流动，表示数据搬运
- **实时数值**：VRAM 占用、带宽利用率、计算利用率等指标面板

### 6 个步骤

| Step | 标题 | 核心内容 | 3D 重点 |
|------|------|---------|--------|
| 1 | 模型加载 | 权重从磁盘→DDR→PCIe→GPU HBM | 粒子沿 SSD→DDR→PCIe→HBM 路径流动，显示传输速率 |
| 2 | Prefill（预填充） | 所有 prompt token 并行送入 GPU，矩阵乘法，compute-bound | GPU 内 Tensor Core 全亮，计算利用率高 |
| 3 | Decode（逐token生成） | 每生成1个 token 需读取全部权重，memory-bound | HBM→Tensor Core 反复搬运，带宽条拉满，计算条很低 |
| 4 | KV Cache 增长 | 每个新 token 的 K/V 向量缓存在 VRAM 中，随序列变长不断增长 | HBM 中 KV Cache 区域动态增长，颜色加深 |
| 5 | 带宽瓶颈可视化 | GPU 算力利用仅 ~5-10%，但 HBM 带宽已 100%，瓶颈在数据搬运 | 对比柱状图：算力 vs 带宽，"高速公路堵车"比喻 |
| 6 | 多GPU并行（Tensor Parallelism） | 模型切分到多卡，NVLink 互联通信 | 多个 GPU 模块，NVLink 粒子通道，All-Reduce 动画 |

### 视觉风格

- 深色背景 `#050a18`，星空点缀
- 硬件组件用等轴测 3D 方块绘制，各有主题色：
  - CPU: `#4a9eff` (蓝)
  - DDR: `#4ade80` (绿)
  - PCIe Bus: `#ffd666` (金)
  - GPU: `#a78bfa` (紫)
  - HBM/VRAM: `#22d3ee` (青)
  - Tensor Core: `#fb923c` (橙)
  - KV Cache: `#f472b6` (粉)
- 数据粒子：小圆点沿路径运动，带拖尾效果
- 指标面板：右侧浮动，实时显示各项利用率

### 交互元素

- 上/下一步导航按钮
- 圆形进度指示器（步骤 1-6）
- 拖拽旋转 3D 视角
- 滚轮缩放
- 术语表（❓按钮）
- 每步可点击硬件组件查看详细说明

### 术语表内容

- **HBM** (High Bandwidth Memory) — GPU 专用高带宽显存
- **Prefill** — 一次性处理所有输入 token 的阶段
- **Decode** — 逐个生成输出 token 的阶段
- **KV Cache** — 缓存注意力机制的 Key/Value 向量，避免重复计算
- **Tensor Core** — GPU 中专门做矩阵乘法的硬件单元
- **PCIe** — CPU 与 GPU 之间的数据通道
- **NVLink** — GPU 之间的高速互联通道
- **Memory-bound** — 性能瓶颈在内存带宽，而非算力
- **Compute-bound** — 性能瓶颈在算力，而非内存带宽
- **Tensor Parallelism** — 将模型层内的矩阵切分到多个 GPU 并行计算

## 技术要点

- 纯前端单文件 HTML，无外部依赖
- Canvas 2D 绘制等轴测 3D（投影变换）
- requestAnimationFrame 驱动粒子动画
- 所有事件监听和 onclick 使用 `window.fn = function(){}` 模式（兼容 innerHTML）
- 中文字符串用单引号包裹，内部引号用 `「」`

## 进度

- [x] 规划文档
- [x] HTML 骨架 + CSS 样式
- [x] 3D 渲染引擎（等轴测投影、旋转、缩放）
- [x] Step 1: 模型加载动画
- [x] Step 2: Prefill 动画
- [x] Step 3: Decode 动画
- [x] Step 4: KV Cache 动画
- [x] Step 5: 带宽瓶颈动画
- [x] Step 6: 多GPU并行动画
- [x] 术语表
- [x] 同步到 docs/
- [x] 更新 index.html（两个目录）
