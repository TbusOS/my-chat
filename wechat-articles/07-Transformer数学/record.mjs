/**
 * 逐帧截图录制脚本 — 59-Transformer数学工坊
 *
 * 原理：
 *   1. 读取 timing.json 获取每段配音时长
 *   2. 计算每段对应的帧数（30fps）
 *   3. 在 Playwright 中逐帧截图，配合步骤切换 + 按钮点击 + 滚动
 *   4. 用 ffmpeg 把帧序列 + 完整配音合成最终视频
 *
 * 关键差异（vs 58）：
 *   - DOM-based 动画，非 Canvas 3D
 *   - 每步需要：goStepSmooth → 展示描述 → triggerAction → 滚动展示结果
 *   - 步骤0（嵌入向量）的 action 是点击词卡而非 action-btn
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
const HTML_FILE = '59-Transformer数学工坊.html'
const HTML_PATH = join(__dirname, HTML_FILE)
const TIMING_PATH = join(__dirname, 'timing.json')

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
}

// How long to wait after action triggers for each step (ms)
// Steps with complex animations need more time
const ACTION_WAIT = {
  0: 1200,   // step1: embedding - click word card, bars animate
  1: 1800,   // step2: position encoding - vectors + bars for 4 words
  2: 3500,   // step3: Q generation - 4 calc-steps with sequential reveal
  3: 1500,   // step4: K and V - auto-animates on render (no action btn)
  4: 3200,   // step5: dot product - 4 calc-steps + bar chart
  5: 1000,   // step6: scaling - auto-animates on render (no action btn)
  6: 2200,   // step7: softmax - calc-steps + pie chart
  7: 2800,   // step8: weighted sum - color mix + math detail
  8: 1500,   // step9: multi-head - auto-animates on render (no action btn)
  9: 2000,   // step10: FFN + residual - pipeline auto-animates
}

// Steps that have an action button to click (vs auto-animate)
const HAS_ACTION_BUTTON = new Set([1, 2, 4, 6, 7])
// Step 0 is special: action is clicking a word card
const WORD_CARD_STEP = 0

function startServer(port = 8770) {
  const baseDir = __dirname
  const server = createServer((req, res) => {
    const url = decodeURIComponent(req.url === '/' ? `/${HTML_FILE}` : req.url)
    const filePath = join(baseDir, url)
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
  // Read timing
  const timing = JSON.parse(readFileSync(TIMING_PATH, 'utf8'))
  const totalDuration = timing.reduce((sum, t) => sum + t.duration, 0)
  const totalFrames = Math.ceil(totalDuration * FPS)
  console.log(`\nTiming: ${timing.length} segments, ${totalDuration.toFixed(1)}s total, ${totalFrames} frames @ ${FPS}fps\n`)

  // Calculate frame ranges for each segment
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
      actionTriggered: false,
      scrollStarted: false,
    })
    console.log(`  ${t.id}: step=${t.step}, ${t.duration}s, frames ${frameStart}-${frameStart + frameCount - 1} (${frameCount} frames)`)
    frameStart += frameCount
  }

  // Prepare directories
  if (existsSync(FRAMES_DIR)) rmSync(FRAMES_DIR, { recursive: true })
  mkdirSync(FRAMES_DIR, { recursive: true })
  mkdirSync(OUTPUT_DIR, { recursive: true })

  // Launch server and browser
  const server = await startServer()
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    locale: 'zh-CN',
    deviceScaleFactor: 2,
  })
  const page = await context.newPage()

  console.log('\nLoading page...')
  await page.goto('http://localhost:8770/')
  await page.waitForTimeout(3000) // Wait for fonts and initial render

  // Enter recording mode
  await page.evaluate(() => window.enterRecordingMode())
  console.log('Recording mode enabled.\n')

  // Track state
  let currentStep = -1
  const startTime = Date.now()

  for (let frame = 0; frame < totalFrames; frame++) {
    // Find which segment this frame belongs to
    const seg = segments.find(s => frame >= s.frameStart && frame < s.frameEnd)
    if (!seg) continue

    const frameInSeg = frame - seg.frameStart
    const segProgress = frameInSeg / seg.frameCount  // 0.0 to 1.0

    // --- Step transition: navigate to new step ---
    if (frame === seg.frameStart && seg.step >= 0 && seg.step !== currentStep) {
      currentStep = seg.step
      console.log(`  -> Step ${seg.step + 1}: ${seg.id}`)

      // Navigate to step
      await page.evaluate((step) => window.goStepSmooth(step), seg.step)
      await page.waitForTimeout(500)

      // Scroll to top for initial view
      await page.evaluate(() => window.scrollToY(0))
    }

    // --- Action trigger at ~30% of segment ---
    if (!seg.actionTriggered && seg.step >= 0 && segProgress >= 0.3) {
      seg.actionTriggered = true

      if (seg.step === WORD_CARD_STEP) {
        // Step 0: click each word card sequentially
        // Click all 4 word cards with delays to show all embeddings
        // We click the last one ("苹果") so it shows that embedding
        await page.evaluate(() => {
          const cards = document.querySelectorAll('.wcard')
          if (cards.length > 0) cards[cards.length - 1].click()
        })
        await page.waitForTimeout(ACTION_WAIT[seg.step])
      } else if (HAS_ACTION_BUTTON.has(seg.step)) {
        // Steps with explicit action buttons
        await page.evaluate(() => window.triggerAction())
        await page.waitForTimeout(ACTION_WAIT[seg.step])
      }
      // Steps 3, 5, 8, 9 auto-animate on render, no action needed
    }

    // --- Gradual scroll during the last 50% of segment ---
    if (seg.step >= 0 && seg.actionTriggered && segProgress >= 0.5) {
      const scrollProgress = (segProgress - 0.5) / 0.5  // 0.0 to 1.0
      const pageHeight = await page.evaluate(() => document.body.scrollHeight - window.innerHeight)
      const targetY = Math.min(scrollProgress * pageHeight, pageHeight)
      if (targetY > 0) {
        await page.evaluate((y) => window.scrollToY(y), targetY)
      }
    }

    // --- Intro/outro: stay at top or show final state ---
    if (seg.step === -1) {
      // For intro, stay on step 0 initial view; for outro, stay on last step
      if (seg.id === 'intro' && frame === seg.frameStart) {
        await page.evaluate(() => window.scrollToY(0))
      }
    }

    // Tick the render
    await page.evaluate(() => window.renderOneFrame())

    // Screenshot
    const frameName = `frame_${String(frame).padStart(6, '0')}.png`
    await page.screenshot({
      path: join(FRAMES_DIR, frameName),
      type: 'png',
    })

    // Progress reporting
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

  // ffmpeg assembly
  console.log('\nAssembling video with ffmpeg...')
  const audioPath = join(WORK_DIR, '59-full-narration.mp3')
  const outputPath = join(OUTPUT_DIR, '59-Transformer数学工坊.mp4')

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

  // Output info
  const dur = parseFloat(execSync(
    `ffprobe -v error -show_entries format=duration -of csv=p=0 "${outputPath}"`,
    { encoding: 'utf8' }
  ).trim())
  const sizeMB = (readFileSync(outputPath).length / 1024 / 1024).toFixed(1)

  console.log(`\nDone: ${outputPath}`)
  console.log(`  Duration: ${dur.toFixed(1)}s, Size: ${sizeMB}MB`)
  console.log(`  FPS: ${FPS}, Resolution: ${WIDTH * 2}x${HEIGHT * 2} (Retina)`)
}

main().catch(console.error)
