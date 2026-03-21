/**
 * 59-Transformer数学工坊 截图
 *
 * 策略：只截视觉元素（条形图、角度图、饼图、计算过程、颜色混合）
 * 用 element.screenshot() 裁剪到具体元素，放大清晰
 * 文字说明在文章里写，不需要截进来
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

function startServer(port = 8771) {
  const server = createServer((req, res) => {
    const filePath = join(__dirname, decodeURIComponent(req.url === '/' ? '/59-Transformer数学工坊.html' : req.url))
    if (!existsSync(filePath)) { res.writeHead(404); res.end('Not Found'); return }
    res.writeHead(200, { 'Content-Type': MIME[extname(filePath)] || 'application/octet-stream' })
    res.end(readFileSync(filePath))
  })
  return new Promise(resolve => server.listen(port, () => resolve(server)))
}

async function shotEl(page, selector, name) {
  try {
    const el = page.locator(selector).first()
    await el.waitFor({ timeout: 3000 })
    await el.screenshot({ path: join(IMG_DIR, `${name}.png`), type: 'png' })
    console.log(`  OK ${name}.png`)
  } catch (e) {
    // 元素不存在时用全页截图兜底
    console.log(`  WARN ${name}: element "${selector}" not found, using full page`)
    await page.screenshot({ path: join(IMG_DIR, `${name}.png`), type: 'png' })
  }
}

async function shotPage(page, name) {
  await page.screenshot({ path: join(IMG_DIR, `${name}.png`), type: 'png' })
  console.log(`  OK ${name}.png`)
}

async function main() {
  const server = await startServer()
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1000, height: 900 },
    locale: 'zh-CN',
    deviceScaleFactor: 2,
  })
  const page = await context.newPage()
  await page.goto('http://localhost:8771/')
  await page.waitForTimeout(3000)

  // 隐藏导航，保留内容
  await page.evaluate(() => {
    document.querySelector('.nav-bar').style.display = 'none';
    document.querySelector('.progress-bar').style.display = 'none';
    document.getElementById('glossary-btn').style.display = 'none';
    document.querySelector('.main').style.paddingBottom = '40px';
  })

  // ====== Step 1: 词变数字 ======
  await page.evaluate(() => goTo(0))
  await page.waitForTimeout(500)
  // 点击"苹果"显示向量+条形图
  await page.evaluate(() => document.querySelectorAll('.wcard')[3].click())
  await page.waitForTimeout(1500)
  // 截向量+条形图区域
  await shotEl(page, '#vecArea', '59-step1-向量条形图')

  // ====== Step 2: 位置编码 ======
  await page.evaluate(() => { goTo(1); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(800)
  // 截 Canvas 波形图
  await shotEl(page, '#waveCanvas', '59-step2-波形动画')
  // 触发叠加
  await page.evaluate(() => animPos())
  await page.waitForTimeout(3000)
  // 截结果条形图
  await page.evaluate(() => window.scrollTo({top:400,behavior:'instant'}))
  await page.waitForTimeout(300)
  await shotEl(page, '#posArea', '59-step2-叠加结果')

  // ====== Step 3: 生成Q ======
  await page.evaluate(() => { goTo(2); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(500)
  await page.evaluate(() => animQ())
  await page.waitForTimeout(5000)
  // 截计算过程区域
  await shotEl(page, '#qArea', '59-step3-Q计算过程')

  // ====== Step 4: QKV ======
  await page.evaluate(() => { goTo(3); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(2000)
  // 截第一个词的QKV条形图对比
  await page.evaluate(() => window.scrollTo({top:0,behavior:'instant'}))
  await page.waitForTimeout(300)
  const calcSteps4 = page.locator('.calc-step')
  // 截"吃"的QKV（第3个calc-step）
  await shotEl(page, '.calc-step:nth-child(5)', '59-step4-吃的QKV')

  // ====== Step 5: 点积 ======
  await page.evaluate(() => { goTo(4); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(800)
  // 截角度图Canvas
  await shotEl(page, '#angleCanvas', '59-step5-角度图')
  // 触发计算
  await page.evaluate(() => animDot())
  await page.waitForTimeout(5000)
  // 截分数柱状图
  await page.evaluate(() => window.scrollTo({top: document.body.scrollHeight, behavior:'instant'}))
  await page.waitForTimeout(300)
  await shotEl(page, '.bar-group', '59-step5-分数柱状图')

  // ====== Step 6: 缩放 ======
  await page.evaluate(() => { goTo(5); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(2500)
  // 截整个对比区域（原始 vs 缩放后柱状图）
  await shotEl(page, '.card', '59-step6-缩放对比')

  // ====== Step 7: Softmax ======
  await page.evaluate(() => { goTo(6); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(500)
  await page.evaluate(() => animSM())
  await page.waitForTimeout(4000)
  // 截饼图
  await shotEl(page, '.pie-wrap', '59-step7-饼图')

  // ====== Step 8: 加权求和 ======
  await page.evaluate(() => { goTo(7); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(500)
  await page.evaluate(() => animMix())
  await page.waitForTimeout(3500)
  // 截颜色混合圆圈
  await shotEl(page, '#mixArea', '59-step8-颜色混合')
  // 截最终结果向量
  await page.evaluate(() => window.scrollTo({top: document.body.scrollHeight, behavior:'instant'}))
  await page.waitForTimeout(1500)
  await shotEl(page, '#wArea', '59-step8-结果向量')

  // ====== Step 9: 多头 ======
  await page.evaluate(() => { goTo(8); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(2000)
  // 截两个头的卡片
  await page.evaluate(() => window.scrollTo({top:100,behavior:'instant'}))
  await page.waitForTimeout(300)
  await shotEl(page, '.card', '59-step9-多头卡片')

  // ====== Step 10: FFN + 残差 ======
  await page.evaluate(() => { goTo(9); window.scrollTo({top:0,behavior:'instant'}) })
  await page.waitForTimeout(2500)
  // 截流水线
  await page.evaluate(() => window.scrollTo({top: document.body.scrollHeight, behavior:'instant'}))
  await page.waitForTimeout(300)
  await shotEl(page, '.pipeline', '59-step10-流水线')

  await context.close()
  await browser.close()
  server.close()
  console.log(`\nScreenshots saved to: ${IMG_DIR}`)
}

main().catch(console.error)
