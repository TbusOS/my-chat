/**
 * 为公众号文章生成配图 — 逐站截图,隐藏界面外壳,裁到关键区域
 */
import { chromium } from '/Users/sky/linux-kernel/github/my-chat/node_modules/playwright/index.mjs'
import { mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
const __dirname = dirname(fileURLToPath(import.meta.url))
const IMG = join(__dirname, 'images'); mkdirSync(IMG, { recursive: true })
const HTML = join(__dirname, '63-手机一帧画面怎么到你眼前.html')

// 站号(从 1 起) → 文件名 · 裁剪框(占画面比例) · 数据流走到第几拍
const SHOTS = [
  { st: 1,  name: '01-一部手机',     crop: [0.16, 0.08, 0.90, 0.94] },
  { st: 2,  name: '02-拆开三层',     crop: [0.14, 0.14, 0.94, 0.92] },
  { st: 3,  name: '03-SoC叠内存',    crop: [0.18, 0.14, 0.92, 0.88] },
  { st: 4,  name: '04-钻进SoC',      crop: [0.06, 0.08, 0.96, 0.92] },
  { st: 5,  name: '05-CPU派活',      crop: [0.14, 0.10, 0.94, 0.90], tick: 4 },
  { st: 6,  name: '06-GPU渲染',      crop: [0.16, 0.10, 0.96, 0.90], tick: 3 },
  { st: 7,  name: '07-DMA搬运',      crop: [0.14, 0.12, 0.94, 0.90], tick: 4 },
  { st: 8,  name: '08-DPU合成',      crop: [0.16, 0.10, 0.94, 0.90], tick: 4 },
  { st: 9,  name: '09-MIPI-DSI',     crop: [0.14, 0.14, 0.96, 0.86], tick: 5 },
  { st: 10, name: '10-驱动IC',       crop: [0.16, 0.08, 0.92, 0.94], tick: 8 },
  { st: 11, name: '11-OLED像素',     crop: [0.10, 0.16, 0.94, 0.90], tick: 1 },
  { st: 12, name: '12-LCD对比OLED',  crop: [0.12, 0.16, 0.94, 0.90], tick: 1 },
]

const browser = await chromium.launch({
  args: ['--enable-gpu','--use-angle=metal','--ignore-gpu-blocklist','--use-gl=angle'] })
const page = await browser.newPage({ viewport:{width:1280,height:800}, deviceScaleFactor:1.5 })
await page.goto('file://' + HTML)
await page.waitForTimeout(4000)
await page.addStyleTag({ content:
  `.hud,.tip,.gloss-btn,.gloss,.acts,.stations,.title,#gc-views{display:none!important}
   .caption{display:none!important}` })
await page.evaluate(() => window.__rec.begin())

for (const s of SHOTS) {
  await page.evaluate(([i,n]) => window.__rec.enter(i,n), [s.st-1, 56])
  await page.evaluate(t => window.__rec.frame(t), (s.tick ?? 0) / 1.4 + 0.35)
  // 上下文丢了就当场停,别默默出一堆黑图
  // 直接读画面中心像素:全黑说明这一站没画出来,当场停,别默默出一堆空图
  const probe = await page.evaluate(() => {
    const c = document.getElementById('gl'), g = c.getContext('webgl2')
    if (!g || g.isContextLost()) return null
    const a = new Uint8Array(4)
    g.readPixels(Math.floor(c.width*0.5), Math.floor(c.height*0.5), 1,1, g.RGBA, g.UNSIGNED_BYTE, a)
    return Array.from(a) })
  if (!probe) { console.log('!! WebGL 上下文丢失,停在 ' + s.name); break }
  if (probe[0]+probe[1]+probe[2] === 0) console.log('   (中心像素全黑,注意核对) ' + s.name)
  const [x0,y0,x1,y1] = s.crop
  await page.screenshot({ path: join(IMG, s.name + '.png'),
    clip: { x: 1280*x0, y: 800*y0, width: 1280*(x1-x0), height: 800*(y1-y0) } })
  console.log('  ' + s.name)
}
await browser.close()
console.log('\n配图生成完毕 → images/')
