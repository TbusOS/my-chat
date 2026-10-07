// 生成首页的分享图 docs/og.jpg(1200x630)和 iOS 主屏图标 docs/apple-touch-icon.png(180x180)
// 用法:node 19-ai-training-ppt/gen-og.mjs        首页首屏外观改了以后重跑一次
// 截完自动复制到 interactive/(见项目 CLAUDE.md 目录同步规则)
import { chromium } from 'playwright';
import { copyFileSync } from 'fs';
import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, resolve, join } from 'path';

const here = dirname(fileURLToPath(import.meta.url));
const docs = resolve(here, '..', 'docs');
const mirror = resolve(here, 'interactive');
const OG = { width: 1200, height: 630 };
const LAYOUT_WIDTH = 1400; // 按 1400 宽排版再缩到 1200,首屏的六层板子才能完整放进 630 高

// 和 index.html 顶栏 logo 同一张图:三层板子
const ICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="180" height="180">
  <rect width="32" height="32" fill="#060a14"/>
  <g stroke-width="1.6" stroke-linejoin="round" fill-opacity=".3" transform="translate(3.2 3.2) scale(.8)">
    <path d="M16 19 27 24 16 29 5 24Z" fill="#22d3ee" stroke="#22d3ee"/>
    <path d="M16 11 27 16 16 21 5 16Z" fill="#4a9eff" stroke="#4a9eff"/>
    <path d="M16 3 27 8 16 13 5 8Z" fill="#4ade80" stroke="#4ade80"/>
  </g>
</svg>`;

const browser = await chromium.launch();
try {
  const scale = OG.width / LAYOUT_WIDTH;
  const og = await browser.newContext({
    viewport: { width: LAYOUT_WIDTH, height: Math.round(OG.height / scale) },
    deviceScaleFactor: scale,
    reducedMotion: 'reduce', // 板子直接是拉开的静态图
  });
  const page = await og.newPage();
  await page.goto(pathToFileURL(join(docs, 'index.html')).href, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: '.td-caption, .help-btn, .stats { display: none !important; }' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(docs, 'og.jpg'), type: 'jpeg', quality: 88 });

  const icon = await browser.newContext({ viewport: { width: 180, height: 180 } });
  const ip = await icon.newPage();
  await ip.setContent(`<body style="margin:0">${ICON_SVG}</body>`);
  await ip.screenshot({ path: join(docs, 'apple-touch-icon.png') });
} finally {
  await browser.close();
}

for (const f of ['og.jpg', 'apple-touch-icon.png']) copyFileSync(join(docs, f), join(mirror, f));
console.log('已生成 og.jpg、apple-touch-icon.png,并复制到 interactive/');
