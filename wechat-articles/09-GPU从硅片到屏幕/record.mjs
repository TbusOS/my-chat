/**
 * 逐帧录制 — 62 号「GPU 从硅片到屏幕」
 *
 * 原理:页面是累积渲染的,进一站先跑满采样把静态底图定住,
 *      之后每帧只重画数据流叠加层 + 合成,一帧几毫秒。
 *      帧数由 timing.json 的配音时长决定,音画天然同步。
 */
import { chromium } from '/Users/sky/linux-kernel/github/my-chat/node_modules/playwright/index.mjs'
import { readFileSync, existsSync, mkdirSync, rmSync, readdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { execSync } from 'child_process'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FPS = 30, W = 1280, H = 800, SPP = 72
const FRAMES = join(__dirname, 'frames')
const OUT = join(__dirname, 'output')
const HTML = join(__dirname, '62-GPU从硅片到屏幕.html')

const timing = JSON.parse(readFileSync(join(__dirname, 'timing.json'), 'utf8'))
const total = timing.reduce((s, t) => s + t.duration, 0)
const totalFrames = Math.ceil(total * FPS)
console.log(`配音 ${timing.length} 段 · ${total.toFixed(1)} 秒 · ${totalFrames} 帧 @${FPS}fps`)

if (existsSync(FRAMES)) rmSync(FRAMES, { recursive: true })
mkdirSync(FRAMES, { recursive: true }); mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch({
  args: ['--enable-gpu', '--use-angle=metal', '--ignore-gpu-blocklist', '--use-gl=angle'] })
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1.5 })
page.on('pageerror', e => console.log('[pageerror] ' + e.message))
await page.goto('file://' + HTML)
await page.waitForTimeout(4000)

const err = await page.evaluate(() => { const e = document.getElementById('err')
  return (e && e.style.display && e.style.display !== 'none') ? e.textContent : null })
if (err) { console.log('页面报错:\n' + err); await browser.close(); process.exit(1) }

// 录制态:隐藏渲染状态面板和操作提示,统计脚本也停掉
await page.addStyleTag({ content: `.hud,.tip,.gloss-btn,.gloss{display:none!important}
  #gc-views{display:none!important}` })
await page.evaluate(() => window.__rec.begin())

let frame = 0, lastStation = -1, t0 = 0
const t_start = Date.now()
for (const seg of timing) {
  if (seg.station !== lastStation) {
    const r = await page.evaluate(([i, n]) => window.__rec.enter(i, n), [seg.station, SPP])
    lastStation = seg.station
    console.log(`\n站 ${String(seg.station + 1).padStart(2, '0')} 底图已收敛 (${r.spp} 采样) · 段 ${seg.id} ${seg.duration.toFixed(1)}s`)
  }
  const n = Math.round(seg.duration * FPS)
  for (let k = 0; k < n; k++) {
    const t = t0 + k / FPS
    await page.evaluate(tt => window.__rec.frame(tt), t)
    await page.screenshot({ path: join(FRAMES, String(frame).padStart(6, '0') + '.jpg'),
      type: 'jpeg', quality: 92 })
    frame++
    if (frame % 300 === 0) {
      const el = (Date.now() - t_start) / 1000
      const eta = el / frame * (totalFrames - frame)
      process.stdout.write(`  ${frame}/${totalFrames}  已用 ${(el/60).toFixed(1)} 分 · 预计还要 ${(eta/60).toFixed(1)} 分\n`)
    }
  }
  t0 += seg.duration
}
await browser.close()
console.log(`\n共 ${frame} 帧,用时 ${((Date.now()-t_start)/60000).toFixed(1)} 分钟`)

// —— 合成:帧序列 + 配音 + 烧录中文字幕 ——
const voice = join(__dirname, 'work', 'voice.mp3')
const srt = join(__dirname, 'subtitles.srt')
const mp4 = join(OUT, 'GPU从硅片到屏幕.mp4')
const style = "FontName=PingFang SC,FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&HC0000000," +
              "BorderStyle=1,Outline=2,Shadow=0,MarginV=38,Alignment=2"
const sub = existsSync(srt) ? `,subtitles='${srt}':force_style='${style}'` : ''
console.log('\nffmpeg 合成中' + (sub ? '(带字幕)' : '(无字幕)') + '…')
execSync(`ffmpeg -v error -r ${FPS} -i "${join(FRAMES,'%06d.jpg')}" -i "${voice}" ` +
  `-vf "scale=1920:1200:flags=lanczos${sub}" ` +
  `-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest "${mp4}" -y`,
  { stdio: 'inherit' })
const size = execSync(`ls -lh "${mp4}" | awk '{print $5}'`).toString().trim()
console.log(`\n成品:${mp4}  (${size})`)
