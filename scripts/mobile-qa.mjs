import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errors = [];

page.on('console', (message) => {
  if (message.type() === 'error') errors.push(message.text());
});
page.on('pageerror', (error) => errors.push(error.message));

await page.goto(process.env.GANYMEDE_URL || 'http://127.0.0.1:4173', { waitUntil: 'networkidle' });
const before = await page.locator('body').evaluate((body) => ({
  scrollWidth: body.scrollWidth,
  clientWidth: body.clientWidth,
}));

await page.locator('[data-scenario="library"]').click();
await page.locator('#run-button').click();
await page.locator('#phase-pill', { hasText: 'Complete' }).waitFor({ timeout: 15000 });

const after = await page.locator('body').evaluate((body) => ({
  scrollWidth: body.scrollWidth,
  clientWidth: body.clientWidth,
}));
const confidence = await page.locator('#confidence-value').textContent();

if (before.scrollWidth !== before.clientWidth || after.scrollWidth !== after.clientWidth) {
  throw new Error(`Horizontal overflow detected: ${JSON.stringify({ before, after })}`);
}
if (confidence !== '82%') throw new Error(`Unexpected completed confidence: ${confidence}`);
if (errors.length > 0) throw new Error(`Browser errors: ${errors.join('\n')}`);

process.stdout.write(`${JSON.stringify({ before, after, confidence, errors })}\n`);
await browser.close();

