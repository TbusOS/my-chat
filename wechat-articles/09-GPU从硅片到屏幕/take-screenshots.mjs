/**
 * 为公众号文章生成配图 — 逐站截图,隐藏界面外壳,裁到关键区域
 */
import { chromium } from '/Users/sky/linux-kernel/github/my-chat/node_modules/playwright/index.mjs'
import { mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
const __dirname = dirname(fileURLToPath(import.meta.url))
const IMG = join(__dirname, 'images'); mkdirSync(IMG, { recursive: true })
const HTML = join(__dirname, '62-GPU从硅片到屏幕.html')

// 站号(从 1 起) → 文件名 · 裁剪框(占画面比例) · 数据流走到第几拍
const SHOTS = [
  { st: 1,  name: '01-一块显卡',       crop: [0.16, 0.10, 0.84, 0.92] },
  { st: 2,  name: '02-拆开散热',       crop: [0.14, 0.08, 0.90, 0.86] },
  { st: 3,  name: '03-封装剖开',       crop: [0.20, 0.12, 0.92, 0.86] },
  { st: 4,  name: '04-硅片版图',       crop: [0.22, 0.08, 0.86, 0.92] },
  { st: 5,  name: '05-SM内部',         crop: [0.24, 0.14, 0.94, 0.82] },
  { st: 6,  name: '06-钻进硅片总线',   crop: [0.10, 0.08, 0.94, 0.92] },
  { st: 7,  name: '07-命令进门',       crop: [0.20, 0.10, 0.96, 0.90], tick: 5 },
  { st: 8,  name: '08-显存搬运',       crop: [0.18, 0.12, 0.92, 0.88], tick: 5 },
  { st: 9,  name: '09-图形流水线',     crop: [0.20, 0.10, 0.94, 0.90], tick: 4 },
  { st: 10, name: '10-SIMT分支',       crop: [0.22, 0.16, 0.90, 0.86], tick: 8 },
  { st: 11, name: '11-存储层级',       crop: [0.20, 0.12, 0.94, 0.88], tick: 9 },
  { st: 13, name: '12-帧缓冲扫出',     crop: [0.22, 0.10, 0.96, 0.90], tick: 2 },
  { st: 14, name: '13-DisplayPort',    crop: [0.02, 0.30, 0.86, 0.78], tick: 6 },
  { st: 15, name: '14-LCD像素',        crop: [0.14, 0.20, 0.94, 0.86], tick: 1 },
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
