// 给首页每张卡片截一张缩略图:docs/thumbs/NN.webp
// 用法:node 19-ai-training-ppt/gen-thumbs.mjs [序号...]    不带参数 = 全部重截
// 新增动画后只截新的:node 19-ai-training-ppt/gen-thumbs.mjs 64
// 依赖:playwright、ffmpeg(给帧打分)、cwebp(压缩)
// 截完自动把 thumbs/ 复制到 interactive/(见项目 CLAUDE.md 目录同步规则)
//
// 怎么挑帧:一页截很多帧,留「边缘密度」最高的那帧。
//   边缘密度 = ffmpeg edgedetect 线稿的平均亮度。文字、图形产生边缘,平滑渐变不产生。
//   不用 PNG 文件大小:浅色页面里一个空的大渐变框压缩得很差,空舞台那帧反而最大
//   (15 号页实测:空框帧 126 KB,内容最满的一帧 90 KB)。
// 三类页面:
//   - 有「自动播放」按钮的叙事页:先点它再采样。这类页面暂停时,每一步里的小延时
//     要等人点「单步」才往下走,不点就一直停在空舞台。
//     按钮按文字「自动播放」认,不按 id 认:各页 id 不统一(btnAuto / btn-play / btnAutoPlay /
//     autoPlayBtn …),只认 btnAuto 时 01、02、07、11、12、32 都漏了。
//   - 有「下一步」但没有自动播放的页:先按时间采样,再翻 STEP_CLICKS 页,每页采一帧。
//     58 号页的第一个场景几乎是空的,翻到第 3 页才有内容。
//   - 其他页:按时间采样,覆盖入场动画。
//   - SETUP 表里的页面先切到指定状态再走上面的规则。只在自动规则挑不出有代表性的画面时才加。
// 另外,首页「最新」那几期(读 index.html 里的 NEW_IDS)再截一张 NN-clean.webp 给大卡片用:
//   只留 <canvas>,其余界面全部隐藏 —— 大卡片的标题叠在图上,图里再有面板文字就乱了。
//   做法是 `* { visibility: hidden } canvas { visibility: visible }`:visibility 会继承,
//   但子元素可以单独设回 visible,所以画布照常渲染,面板和文字消失。
import { chromium } from 'playwright';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { readdirSync, readFileSync, mkdirSync, rmSync, cpSync, writeFileSync, renameSync } from 'fs';
import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, resolve, join } from 'path';

const run = promisify(execFile);
const here = dirname(fileURLToPath(import.meta.url));
const docs = resolve(here, '..', 'docs');
const mirror = resolve(here, 'interactive');
const outDir = join(docs, 'thumbs');
const tmpDir = join(outDir, '.tmp');
const VIEWPORT = { width: 1024, height: 640 };
const SAMPLE_MS = 1500;
const STORY_MS = 24000;   // 叙事页采样时长:大约走完前 4~5 步
const DEFAULT_MS = 9000;  // 其他页:覆盖入场动画
const STEP_CLICKS = 3;
const STEP_WAIT_MS = 2500;
const NEXT_SELECTOR = '#btnNext, #nextBtn, #next-btn';
const WORKERS = 4;
// 个别页面先点一下再采样。why 写清楚为什么自动规则不够,别让这张表变成随手调图的地方
const SETUP = {
  '29': { click: '.tab[data-tab="heatmap"]',
          why: '热力图最能代表注意力;按边缘密度会挑文字多的「多头注意力」卡片页,默认 Tab 首屏只有四个词' },
};
const CLEAN_VIEWPORT = { width: 1280, height: 800 };
const CLEAN_SIZE = ['960', '600'];
const CLEAN_WAIT_MS = 4000;

const wanted = new Set(process.argv.slice(2).map((n) => n.padStart(2, '0')));
const files = readdirSync(docs)
  .filter((f) => /^\d{2}-.+\.html$/.test(f))
  .filter((f) => wanted.size === 0 || wanted.has(f.slice(0, 2)))
  .sort();

if (files.length === 0) {
  console.error('没有匹配的动画文件');
  process.exit(1);
}

// 首页「最新」几期的编号,和 index.html 保持同一个来源
function readNewIds() {
  const html = readFileSync(join(docs, 'index.html'), 'utf8');
  const m = html.match(/var NEW_IDS = \[([^\]]*)\]/);
  if (!m) throw new Error('index.html 里找不到 var NEW_IDS = [...]');
  return [...m[1].matchAll(/'(\d{2})'/g)].map((x) => x[1]);
}

async function edgeScore(png) {
  const { stderr } = await run('ffmpeg', ['-hide_banner', '-i', png, '-vf',
    'edgedetect=low=0.08:high=0.2,signalstats,metadata=print:key=lavfi.signalstats.YAVG', '-f', 'null', '-']);
  const m = stderr.match(/YAVG=([\d.]+)/);
  if (!m) throw new Error('ffmpeg 没有输出 YAVG,无法给帧打分');
  return Number(m[1]);
}

mkdirSync(tmpDir, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const failed = [];

async function shoot(f) {
  const num = f.slice(0, 2);
  // 每页一个独立 context,并行时互不当「后台标签页」
  const ctx = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  let best = null;
  let n = 0;
  async function sample(label) {
    await page.evaluate(() => window.scrollTo(0, 0));
    const png = join(tmpDir, `${num}-${n++}.png`);
    writeFileSync(png, await page.screenshot());
    const score = await edgeScore(png);
    if (!best || score > best.score) best = { png, score, label };
  }
  try {
    await page.goto(pathToFileURL(join(docs, f)).href, { waitUntil: 'load', timeout: 30000 });
    // 下面都用 JS 点,不让 Playwright 把按钮滚进视口
    if (SETUP[num]) {
      const hit = await page.evaluate((sel) => { const e = document.querySelector(sel); if (e) e.click(); return Boolean(e); }, SETUP[num].click);
      if (!hit) throw new Error(`SETUP 里的 ${SETUP[num].click} 在页面上找不到,页面改过了?`);
      await page.waitForTimeout(500);
    }
    const kind = await page.evaluate((sel) => {
      const auto = [...document.querySelectorAll('button')]
        .find((b) => b.textContent.includes('自动播放') && b.getClientRects().length > 0); // offsetParent 对 fixed 元素恒为 null,不能拿来判可见
      if (auto) { auto.click(); return 'story'; }
      return document.querySelector(sel) ? 'steps' : 'plain';
    }, NEXT_SELECTOR);
    const span = kind === 'story' ? STORY_MS : DEFAULT_MS;
    for (let t = SAMPLE_MS; t <= span; t += SAMPLE_MS) {
      await page.waitForTimeout(SAMPLE_MS);
      await sample(`${(t / 1000).toFixed(1)}s`);
    }
    if (kind === 'steps') {
      for (let k = 1; k <= STEP_CLICKS; k++) {
        await page.evaluate((sel) => { const b = document.querySelector(sel); if (b && !b.disabled) b.click(); }, NEXT_SELECTOR);
        await page.waitForTimeout(STEP_WAIT_MS);
        await sample(`下一步×${k}`);
      }
    }
    const webp = join(outDir, `${num}.webp`);
    await run('cwebp', ['-quiet', '-q', '72', '-resize', '640', '400', best.png, '-o', `${webp}.part`]);
    renameSync(`${webp}.part`, webp);
    console.log(`ok   ${num}  ${kind.padEnd(5)}  ${best.label.padEnd(8)} 边缘 ${best.score.toFixed(2)}  ${f}`);
  } catch (err) {
    failed.push(num);
    console.error(`FAIL ${num}  ${f}: ${err.message}`);
  } finally {
    await ctx.close();
  }
}

const queue = [...files];
await Promise.all(Array.from({ length: WORKERS }, async () => {
  while (queue.length) await shoot(queue.shift());
}));

async function shootClean(f) {
  const num = f.slice(0, 2);
  const ctx = await browser.newContext({ viewport: CLEAN_VIEWPORT, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  try {
    await page.goto(pathToFileURL(join(docs, f)).href, { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(CLEAN_WAIT_MS);
    const canvases = await page.locator('canvas').count();
    if (canvases === 0) throw new Error('页面里没有 <canvas>,截不了干净版');
    await page.addStyleTag({ content: '* { visibility: hidden !important; } canvas { visibility: visible !important; }' });
    await page.waitForTimeout(300);
    const png = join(tmpDir, `${num}-clean.png`);
    writeFileSync(png, await page.screenshot());
    const webp = join(outDir, `${num}-clean.webp`);
    await run('cwebp', ['-quiet', '-q', '78', '-resize', ...CLEAN_SIZE, png, '-o', `${webp}.part`]);
    renameSync(`${webp}.part`, webp);
    console.log(`ok   ${num}  clean  只留画布  ${f}`);
  } catch (err) {
    failed.push(`${num}-clean`);
    console.error(`FAIL ${num}-clean  ${f}: ${err.message}`);
  } finally {
    await ctx.close();
  }
}

const newIds = new Set(readNewIds());
for (const f of files.filter((x) => newIds.has(x.slice(0, 2)))) await shootClean(f);

await browser.close();
rmSync(tmpDir, { recursive: true, force: true });
cpSync(outDir, join(mirror, 'thumbs'), { recursive: true });
console.log(`\n${failed.length ? '有失败:' + failed.join(' ') : '全部成功'},已同步到 interactive/thumbs/`);
if (failed.length) process.exit(1);
