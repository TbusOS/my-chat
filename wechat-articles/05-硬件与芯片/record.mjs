/**
 * 逐帧截图录制脚本
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
const HTML_PATH = join(__dirname, '56-LLM硬件推理全景.html')
const TIMING_PATH = join(__dirname, 'timing.json')

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
}

function startServer(port = 8766) {
  const baseDir = __dirname
  const server = createServer((req, res) => {
    const filePath = join(baseDir, decodeURIComponent(req.url === '/' ? '/56-LLM硬件推理全景.html' : req.url))
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
    deviceScaleFactor: 2,  // 高清截图
  })
  const page = await context.newPage()

  console.log('\nLoading page...')
  await page.goto('http://localhost:8766/')
  await page.waitForTimeout(2000) // 等待字体加载和初始渲染

  // 进入录制模式
  await page.evaluate(() => window.enterRecordingMode())
  console.log('Recording mode enabled.\n')

  // 先预热渲染几帧（让粒子系统初始化）
  for (let i = 0; i < 30; i++) {
    await page.evaluate(() => window.renderOneFrame())
  }

  // 逐帧录制
  let currentStep = -1
  const startTime = Date.now()

  for (let frame = 0; frame < totalFrames; frame++) {
    // 检查是否需要切换步骤
    for (const seg of segments) {
      if (frame === seg.frameStart && seg.step >= 0 && seg.step !== currentStep) {
        currentStep = seg.step
        await page.evaluate((step) => window.goStepSmooth(step), seg.step)
        // 切换步骤后多渲染几帧让粒子系统启动
        for (let w = 0; w < 10; w++) {
          await page.evaluate(() => window.renderOneFrame())
        }
        console.log(`  → Step ${seg.step + 1}: ${seg.id}`)
      }
    }

    // 渲染一帧
    await page.evaluate(() => window.renderOneFrame())

    // 截图
    const frameName = `frame_${String(frame).padStart(6, '0')}.png`
    await page.screenshot({
      path: join(FRAMES_DIR, frameName),
      type: 'png',
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
  const audioPath = join(WORK_DIR, '56-full-narration.mp3')
  const outputPath = join(OUTPUT_DIR, '56-LLM硬件推理全景.mp4')

  execSync([
    'ffmpeg -y',
    `-framerate ${FPS}`,
    `-i "${join(FRAMES_DIR, 'frame_%06d.png')}"`,
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

  console.log(`\n✓ 完成: ${outputPath}`)
  console.log(`  时长: ${dur.toFixed(1)}s, 大小: ${sizeMB}MB`)
  console.log(`  帧率: ${FPS}fps, 分辨率: ${WIDTH * 2}x${HEIGHT * 2} (Retina)`)
}

main().catch(console.error)
