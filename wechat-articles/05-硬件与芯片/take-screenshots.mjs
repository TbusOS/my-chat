/**
 * 给每个步骤截图，用于公众号文章配图
 */
import { chromium } from 'playwright'
import { createServer } from 'http'
import { readFileSync, existsSync, mkdirSync } from 'fs'
import { join, extname } from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const IMG_DIR = join(__dirname, 'images')
mkdirSync(IMG_DIR, { recursive: true })

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.png': 'image/png', '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2', '.woff': 'font/woff',
}

function startServer(port = 8767) {
  const server = createServer((req, res) => {
    const filePath = join(__dirname, decodeURIComponent(req.url === '/' ? '/56-LLM硬件推理全景.html' : req.url))
    if (!existsSync(filePath)) { res.writeHead(404); res.end('Not Found'); return }
    res.writeHead(200, { 'Content-Type': MIME[extname(filePath)] || 'application/octet-stream' })
    res.end(readFileSync(filePath))
  })
  return new Promise(resolve => server.listen(port, () => resolve(server)))
}

async function main() {
  const server = await startServer()
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    locale: 'zh-CN',
    deviceScaleFactor: 2,
  })
  const page = await context.newPage()
  await page.goto('http://localhost:8767/')
  await page.waitForTimeout(3000)

  // 让 3D 旋转到一个好看的角度后再截图
  const steps = [
    { step: 0, name: 'step1-模型加载', angle: 0.5, warmup: 60 },
    { step: 1, name: 'step2-Prefill预填充', angle: 0.6, warmup: 60 },
    { step: 2, name: 'step3-Decode生成', angle: 0.4, warmup: 60 },
    { step: 3, name: 'step4-KVCache增长', angle: 0.55, warmup: 80 },
    { step: 4, name: 'step5-带宽瓶颈', angle: 0.45, warmup: 40 },
    { step: 5, name: 'step6-多GPU并行', angle: 0.5, warmup: 60 },
  ]

  for (const s of steps) {
    // 切换步骤
    await page.evaluate((step) => {
      window.goStep(step)
    }, s.step)

    // 设置旋转角度
    await page.evaluate((angle) => {
      window.isoAngle = angle  // 不存在也没关系，不会报错
    }, s.angle)

    // 多渲染几帧让粒子系统启动 + 动画稳定
    for (let i = 0; i < s.warmup; i++) {
      await page.evaluate(() => {
        if (window.renderOneFrame) window.renderOneFrame()
      })
    }
    await page.waitForTimeout(500)

    // 截图
    const path = join(IMG_DIR, `${s.name}.png`)
    await page.screenshot({ path, type: 'png' })
    console.log(`  ✓ ${s.name}.png`)
  }

  await context.close()
  await browser.close()
  server.close()
  console.log(`\n截图保存在: ${IMG_DIR}`)
}

main().catch(console.error)
