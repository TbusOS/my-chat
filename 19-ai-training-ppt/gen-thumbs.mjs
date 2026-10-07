// 给首页每张卡片截一张缩略图:docs/thumbs/NN.webp
// 用法:node 19-ai-training-ppt/gen-thumbs.mjs [序号...]    不带参数 = 全部重截
// 新增动画后只截新的:node 19-ai-training-ppt/gen-thumbs.mjs 64
// 截完要把 thumbs/ 同步到 interactive/(见项目 CLAUDE.md 目录同步规则)
import { chromium } from 'playwright';
import { execFileSync } from 'child_process';
import { readdirSync, mkdirSync, rmSync, cpSync } from 'fs';
import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, resolve, join } from 'path';

const here = dirname(fileURLToPath(import.meta.url));
const docs = resolve(here, '..', 'docs');
const mirror = resolve(here, 'interactive');
const outDir = join(docs, 'thumbs');
const tmpDir = join(outDir, '.tmp');
const WAIT_MS = 3500; // 等入场动画放完再截

const wanted = new Set(process.argv.slice(2).map((n) => n.padStart(2, '0')));
const files = readdirSync(docs)
  .filter((f) => /^\d{2}-.+\.html$/.test(f))
  .filter((f) => wanted.size === 0 || wanted.has(f.slice(0, 2)))
  .sort();

if (files.length === 0) {
  console.error('没有匹配的动画文件');
  process.exit(1);
}

mkdirSync(tmpDir, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const ctx = await browser.newContext({ viewport: { width: 1024, height: 640 }, deviceScaleFactor: 1 });
const failed = [];

for (const f of files) {
  const num = f.slice(0, 2);
  const page = await ctx.newPage();
  try {
    await page.goto(pathToFileURL(join(docs, f)).href, { waitUntil: 'load', timeout: 30000 });
    await page.waitForTimeout(WAIT_MS);
    const png = join(tmpDir, `${num}.png`);
    await page.screenshot({ path: png });
    execFileSync('cwebp', ['-quiet', '-q', '72', '-resize', '640', '400', png, '-o', join(outDir, `${num}.webp`)]);
    console.log(`ok   ${num}  ${f}`);
  } catch (err) {
    failed.push(num);
    console.error(`FAIL ${num}  ${f}: ${err.message}`);
  } finally {
    await page.close();
  }
}

await browser.close();
rmSync(tmpDir, { recursive: true, force: true });
cpSync(outDir, join(mirror, 'thumbs'), { recursive: true });
console.log(`\n截了 ${files.length - failed.length}/${files.length} 张,已同步到 interactive/thumbs/`);
if (failed.length) process.exit(1);
