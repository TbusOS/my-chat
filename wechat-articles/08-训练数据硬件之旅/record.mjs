/**
 * 逐帧截图录制脚本 — 60-大模型训练数据硬件之旅
 *
 * 原理：
 *   1. 读取 timing.json 获取每段配音时长
 *   2. 计算每段对应的帧数（30fps）
 *   3. 在 Playwright 中逐帧调用 renderOneFrame() + screenshot
 *   4. 用 ffmpeg 把帧序列 + 完整配音合成最终视频
 *
 * 用法: node record.mjs
 */
import { chromium } from 'playwright'
import { createServer } from 'http'
import { readFileSync, existsSync, mkdirSync, rmSync } from 'fs'
import { join, extname } from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import { execSync } from 'child_process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const FPS = 30
const WIDTH = 1280
const HEIGHT = 800
const FRAMES_DIR = join(__dirname, 'frames')
const OUTPUT_DIR = join(__dirname, 'output')
const WORK_DIR = join(__dirname, 'work')
const HTML_PATH = join(__dirname, '60-大模型训练数据硬件之旅.html')
const TIMING_PATH = join(__dirname, 'timing.json')

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
}

function startServer(port = 8769) {
  const baseDir = __dirname
  const server = createServer((req, res) => {
    const filePath = join(baseDir, decodeURIComponent(req.url === '/' ? '/60-大模型训练数据硬件之旅.html' : req.url))
    if (!existsSync(filePath)) { res.writeHead(404); res.end('Not Found'); return }
    res.writeHead(200, { 'Content-Type': MIME[extname(filePath)] || 'application/octet-stream' })
    res.end(readFileSync(filePath))
  })
  return new Promise(resolve => server.listen(port, () => {
    console.log(`Server: http://localhost:${port}`)
    resolve(server)
  }))
}

async function main() {
  // 读取 timing
  const timing = JSON.parse(readFileSync(TIMING_PATH, 'utf8'))
  const totalDuration = timing.reduce((sum, t) => sum + t.duration, 0)
  const totalFrames = Math.ceil(totalDuration * FPS)
  console.log(`\nTiming: ${timing.length} segments, ${totalDuration.toFixed(1)}s total, ${totalFrames} frames @ ${FPS}fps\n`)

  // 计算每段的帧范围
  const segments = []
  let frameStart = 0
  for (const t of timing) {
    const frameCount = Math.round(t.duration * FPS)
    segments.push({
      id: t.id,
      step: t.step,
      duration: t.duration,
      frameStart,
      frameEnd: frameStart + frameCount,
      frameCount,
    })
    console.log(`  ${t.id}: step=${t.step}, ${t.duration}s, frames ${frameStart}-${frameStart + frameCount - 1}`)
    frameStart += frameCount
  }

  // 准备目录
  if (existsSync(FRAMES_DIR)) rmSync(FRAMES_DIR, { recursive: true })
  mkdirSync(FRAMES_DIR, { recursive: true })
  mkdirSync(OUTPUT_DIR, { recursive: true })

  // 启动服务和浏览器
  const server = await startServer()
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    locale: 'zh-CN',
    deviceScaleFactor: 1,  // 1x for speed, still 1280x800
  })
  const page = await context.newPage()

  console.log('\nLoading page...')
  await page.goto('http://localhost:8769/')
  await page.waitForTimeout(2000)

  // 进入录制模式
  await page.evaluate(() => window.enterRecordingMode())
  console.log('Recording mode enabled.\n')

  // 预热渲染
  for (let i = 0; i < 30; i++) {
    await page.evaluate(() => window.renderOneFrame())
  }

  // ── 每个场景的交互动作时间表 ──
  // 格式: { framePercent: 触发时刻(0-1), action: 动作名 }
  // 在该场景播放到指定百分比时触发对应交互按钮
  const SCENE_ACTIONS = {
    0: [], // 全景 — 纯展示
    1: [   // NVMe
      { at: 0.15, action: 'read' },  // 触发读取动画
    ],
    2: [   // CPU
      { at: 0.15, action: 'dataloader' },  // 启动多核处理
    ],
    3: [   // PCIe
      { at: 0.55, action: 'compare' },  // 中途切到Gen4对比
      { at: 0.80, action: 'compare' },  // 切回Gen5
    ],
    4: [   // GPU鸟瞰
      { at: 0.20, action: 'highlight' },  // 高亮SM
      { at: 0.45, action: 'highlight' },  // 高亮L2
      { at: 0.70, action: 'highlight' },  // 高亮HBM
    ],
    5: [   // HBM塔
      { at: 0.20, action: 'write' },  // 数据写入动画
    ],
    6: [   // 金字塔
      { at: 0.15, action: 'climb' },  // 第1层
      { at: 0.35, action: 'climb' },  // 第2层
      { at: 0.55, action: 'climb' },  // 第3层
      { at: 0.75, action: 'climb' },  // 第4层
    ],
    7: [   // SM内部
      { at: 0.30, action: 'warp' },   // Warp调度动画
    ],
    8: [   // Tensor Core
      { at: 0.10, action: 'multiply' },  // step 1: 矩阵滑入
      { at: 0.40, action: 'multiply' },  // step 2: 乘法连线
      { at: 0.65, action: 'multiply' },  // step 3: 结果生成
    ],
    9: [   // Embedding
      { at: 0.20, action: 'lookup' },  // Token查找动画
    ],
    10: [  // 自注意力
      { at: 0.60, action: 'multihead' },  // 展开多头
    ],
    11: [  // FlashAttention — 先展示标准，再切Flash
      { at: 0.45, action: 'flash' },  // 切换到Flash模式
    ],
    12: [  // FFN
      { at: 0.50, action: 'showact' },  // 显示激活值存储
    ],
    13: [  // 反向传播
      { at: 0.60, action: 'checkpoint' },  // 梯度检查点
    ],
    14: [  // 混合精度
      { at: 0.50, action: 'precision' },  // 精度对比
    ],
    15: [  // AllReduce
      { at: 0.15, action: 'allreduce' },  // 启动AllReduce动画
    ],
    16: [  // 优化器
      { at: 0.40, action: 'loop' },  // 训练循环动画
    ],
  }

  // 逐帧录制
  let currentStep = -1
  const startTime = Date.now()
  const triggeredActions = new Set()  // 已触发的动作（防重复）

  for (let frame = 0; frame < totalFrames; frame++) {
    // 检查是否需要切换步骤
    for (const seg of segments) {
      if (frame === seg.frameStart && seg.step >= 0 && seg.step !== currentStep) {
        currentStep = seg.step
        triggeredActions.clear()
        await page.evaluate((fc) => window.setSceneFrameTotal(fc), seg.frameCount)
        await page.evaluate((step) => window.goStepSmooth(step), seg.step)
        for (let w = 0; w < 15; w++) {
          await page.evaluate(() => window.renderOneFrame())
        }
        console.log(`  -> Step ${seg.step + 1}: ${seg.id}`)
      }

      // 检查是否需要触发交互动作
      if (frame >= seg.frameStart && frame < seg.frameEnd && seg.step >= 0) {
        const localFrame = frame - seg.frameStart
        const pct = localFrame / seg.frameCount
        const actions = SCENE_ACTIONS[seg.step] || []
        for (const act of actions) {
          const key = `${seg.step}_${act.action}_${act.at}`
          if (pct >= act.at && !triggeredActions.has(key)) {
            triggeredActions.add(key)
            await page.evaluate((a) => window.sceneAction(a), act.action)
            // 触发后多渲染几帧让效果展现
            for (let w = 0; w < 10; w++) {
              await page.evaluate(() => window.renderOneFrame())
            }
            console.log(`     [${(act.at*100).toFixed(0)}%] action: ${act.action}`)
          }
        }
      }
    }

    // 渲染一帧
    await page.evaluate(() => window.renderOneFrame())

    // 截图
    const frameName = `frame_${String(frame).padStart(6, '0')}.jpg`
    await page.screenshot({
      path: join(FRAMES_DIR, frameName),
      type: 'jpeg',
      quality: 90,
    })

    // 进度
    if (frame % 100 === 0 || frame === totalFrames - 1) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(0)
      const pct = ((frame / totalFrames) * 100).toFixed(1)
      const eta = frame > 0 ? (((Date.now() - startTime) / frame * (totalFrames - frame)) / 1000).toFixed(0) : '?'
      process.stdout.write(`\r  Capturing: ${frame}/${totalFrames} (${pct}%) elapsed=${elapsed}s eta=${eta}s`)
    }
  }

  console.log('\n\nCapture complete!')
  await context.close()
  await browser.close()
  server.close()

  // ffmpeg 合成
  console.log('\nAssembling video with ffmpeg...')
  const audioPath = join(WORK_DIR, '60-full-narration.mp3')
  const outputPath = join(OUTPUT_DIR, '60-大模型训练数据硬件之旅.mp4')

  execSync([
    'ffmpeg -y',
    `-framerate ${FPS}`,
    `-i "${join(FRAMES_DIR, 'frame_%06d.jpg')}"`,
    `-i "${audioPath}"`,
    '-c:v libx264 -preset slow -crf 20',
    '-c:a aac -b:a 192k',
    '-pix_fmt yuv420p',
    '-shortest',
    `"${outputPath}"`
  ].join(' '), { stdio: 'inherit' })

  // 输出信息
  const dur = parseFloat(execSync(
    `ffprobe -v error -show_entries format=duration -of csv=p=0 "${outputPath}"`,
    { encoding: 'utf8' }
  ).trim())
  const sizeMB = (readFileSync(outputPath).length / 1024 / 1024).toFixed(1)

  console.log(`\nDone: ${outputPath}`)
  console.log(`  Duration: ${dur.toFixed(1)}s, Size: ${sizeMB}MB`)
  console.log(`  FPS: ${FPS}, Resolution: ${WIDTH}x${HEIGHT}`)
}

main().catch(console.error)
