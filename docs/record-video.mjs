import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const htmlPath = resolve(__dirname, '05-Agent工作故事.html');
const outputDir = resolve(__dirname, '..', 'output');

async function record() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 800, height: 680 },
    recordVideo: {
      dir: outputDir,
      size: { width: 800, height: 680 },
    },
  });

  const page = await context.newPage();
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });

  // Wait for initial render
  await page.waitForTimeout(1500);

  // Click autoplay button
  await page.click('#btnAuto');

  // 6 steps x ~3.5s per step + animation time within steps + buffer
  // Each step has internal delays totaling ~2-4s, plus 3.5s interval
  // Total: ~6 * 5s = 30s + confetti celebration
  await page.waitForTimeout(32000);

  // Wait for celebration confetti to finish
  await page.waitForTimeout(3000);

  await page.close();
  await context.close();
  await browser.close();

  console.log(`Video saved to: ${outputDir}/`);
  console.log('Look for a .webm file in the output directory.');
}

record().catch(console.error);
