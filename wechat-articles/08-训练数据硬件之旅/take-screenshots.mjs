/**
 * 截图脚本 — 为公众号文章生成每个场景的配图
 * 放大到关键视觉元素，不截全屏
 */
import { chromium } from 'playwright'
import { createServer } from 'http'
import { readFileSync, existsSync, mkdirSync } from 'fs'
import { join, extname } from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const IMAGES_DIR = join(__dirname, 'images')
const HTML_FILE = '60-大模型训练数据硬件之旅.html'

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
}

// Per-scene screenshot config: zoom level and camera angle
const SCENE_CONFIGS = [
  { name: '01-训练系统全景',   zoom: 1.0, rotX: -0.3, rotY: 0.5 },
  { name: '02-NVMe内部',      zoom: 1.3, rotX: -0.25, rotY: 0.4 },
  { name: '03-CPU预处理',     zoom: 1.2, rotX: -0.35, rotY: 0.5 },
  { name: '04-PCIe通道',      zoom: 1.1, rotX: -0.2, rotY: 0.3 },
  { name: '05-GPU芯片鸟瞰',   zoom: 1.1, rotX: -0.4, rotY: 0.6 },
  { name: '06-HBM存储塔',     zoom: 1.4, rotX: -0.25, rotY: 0.5 },
  { name: '07-存储金字塔',     zoom: 1.1, rotX: -0.3, rotY: 0.5 },
  { name: '08-SM内部',        zoom: 1.3, rotX: -0.3, rotY: 0.5 },
  { name: '09-TensorCore',    zoom: 1.5, rotX: -0.2, rotY: 0.4 },
  { name: '10-Embedding',     zoom: 1.2, rotX: -0.3, rotY: 0.5 },
  { name: '11-自注意力',       zoom: 1.1, rotX: -0.3, rotY: 0.5 },
  { name: '12-FlashAttention', zoom: 1.0, rotX: -0.2, rotY: 0.3 },
  { name: '13-FFN层',         zoom: 1.2, rotX: -0.3, rotY: 0.5 },
  { name: '14-反向传播',       zoom: 1.1, rotX: -0.3, rotY: 0.5 },
  { name: '15-混合精度',       zoom: 1.2, rotX: -0.3, rotY: 0.5 },
  { name: '16-AllReduce',     zoom: 1.0, rotX: -0.35, rotY: 0.5 },
  { name: '17-优化器循环',     zoom: 1.1, rotX: -0.3, rotY: 0.5 },
]

function startServer(port = 8770) {
  const baseDir = __dirname
  const server = createServer((req, res) => {
    const filePath = join(baseDir, decodeURIComponent(req.url === '/' ? `/${HTML_FILE}` : req.url))
    if (!existsSync(filePath)) { res.writeHead(404); res.end('Not Found'); return }
    res.writeHead(200, { 'Content-Type': MIME[extname(filePath)] || 'application/octet-stream' })
    res.end(readFileSync(filePath))
  })
  return new Promise(resolve => server.listen(port, () => resolve(server)))
}

async function main() {
  mkdirSync(IMAGES_DIR, { recursive: true })

  const server = await startServer()
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 800, height: 600 },
    locale: 'zh-CN',
    deviceScaleFactor: 2,
  })
  const page = await context.newPage()

  await page.goto('http://localhost:8770/')
  await page.waitForTimeout(2000)

  // Enter recording mode to hide UI
  await page.evaluate(() => window.enterRecordingMode())

  for (let i = 0; i < SCENE_CONFIGS.length; i++) {
    const cfg = SCENE_CONFIGS[i]
    console.log(`  Capturing scene ${i}: ${cfg.name}...`)

    // Navigate to scene
    await page.evaluate((step) => window.goStepSmooth(step), i)

    // Set camera and zoom
    await page.evaluate(({ zoom, rotX, rotY }) => {
      camZoom = zoom
      camRotX = rotX
      camRotY = rotY
      autoRotate = false
    }, cfg)

    // Render some frames for animation to settle
    for (let f = 0; f < 60; f++) {
      await page.evaluate(() => window.renderOneFrame())
    }

    // Take screenshot
    await page.screenshot({
      path: join(IMAGES_DIR, `${cfg.name}.png`),
      type: 'png',
    })
  }

  console.log(`\nDone! ${SCENE_CONFIGS.length} screenshots saved to ${IMAGES_DIR}`)
  await context.close()
  await browser.close()
  server.close()
}

main().catch(console.error)
