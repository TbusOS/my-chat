/**
 * 58-Transformer原理3D直觉 截图
 *
 * 策略：只截3D画面，不要文字面板。用小视口+高zoom让粒子大而清晰。
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

function startServer(port = 8769) {
  const server = createServer((req, res) => {
    const filePath = join(__dirname, decodeURIComponent(req.url === '/' ? '/58-Transformer原理3D直觉.html' : req.url))
    if (!existsSync(filePath)) { res.writeHead(404); res.end('Not Found'); return }
    res.writeHead(200, { 'Content-Type': MIME[extname(filePath)] || 'application/octet-stream' })
    res.end(readFileSync(filePath))
  })
  return new Promise(resolve => server.listen(port, () => resolve(server)))
}

async function shot(page, name) {
  await page.screenshot({ path: join(IMG_DIR, `${name}.png`), type: 'png' })
  console.log(`  OK ${name}.png`)
}

async function main() {
  const server = await startServer()
  const browser = await chromium.launch({ headless: true })

  // 小视口 + 高 DPR = 粒子占画面比例大
  const context = await browser.newContext({
    viewport: { width: 800, height: 600 },
    locale: 'zh-CN',
    deviceScaleFactor: 2,
  })
  const page = await context.newPage()
  await page.goto('http://localhost:8769/')
  await page.waitForTimeout(3000)

  // 隐藏所有UI，只留3D画布
  await page.evaluate(() => {
    document.querySelector('.info-panel').style.display = 'none';
    document.querySelector('.nav-bar').style.display = 'none';
    document.querySelector('.progress').style.display = 'none';
    document.querySelector('.hint-bar').style.display = 'none';
    document.getElementById('glossary-btn').style.display = 'none';
    autoRotate = false;
  })

  const steps = [
    { step: 0, name: '58-step1-词的困境',     action: null,        zoom: 1.8, rotY: 0.5,  warmup: 80 },
    { step: 1, name: '58-step2-向量空间',     action: null,        zoom: 1.5, rotY: 0.6,  warmup: 80 },
    { step: 2, name: '58-step3-一词多义',     action: null,        zoom: 1.6, rotY: 0.4,  warmup: 80 },
    { step: 3, name: '58-step4-暴力平均',     action: null,        zoom: 1.5, rotY: 0.5,  warmup: 60 },
    { step: 4, name: '58-step5-注意力诞生',   action: 'attention', zoom: 1.5, rotY: 0.5,  warmup: 100 },
    { step: 5, name: '58-step6-QK分裂',       action: 'split',     zoom: 1.4, rotY: 0.6,  warmup: 120 },
    { step: 6, name: '58-step7-V登场',        action: 'flow',      zoom: 1.5, rotY: 0.5,  warmup: 120 },
    { step: 7, name: '58-step8-多头注意力',   action: 'heads',     zoom: 1.2, rotY: 0.4,  warmup: 100 },
    { step: 8, name: '58-step9-融合',         action: null,        zoom: 1.6, rotY: 0.55, warmup: 80 },
  ]

  for (const s of steps) {
    await page.evaluate(({step, zoom, rotY}) => {
      goToScene(step);
      camZoom = zoom;
      camRotY = rotY;
      camRotX = -0.3;
    }, { step: s.step, zoom: s.zoom, rotY: s.rotY })

    if (s.action) {
      await page.waitForTimeout(500)
      await page.evaluate((a) => sceneAction(a), s.action)
    }

    // 渲染足够帧让动画稳定
    for (let i = 0; i < s.warmup; i++) {
      await page.evaluate(() => {
        if (window.renderOneFrame) window.renderOneFrame()
        // 缓慢旋转找到好看的角度
        camRotY += 0.003;
      })
    }
    await page.waitForTimeout(300)

    await shot(page, s.name)
  }

  await context.close()
  await browser.close()
  server.close()
  console.log(`\nScreenshots saved to: ${IMG_DIR}`)
}

main().catch(console.error)
