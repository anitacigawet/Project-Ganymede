import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';

const baseUrl = process.env.GANYMEDE_URL || 'http://127.0.0.1:4173';
await mkdir('docs/screenshots', { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1440, height: 1050 },
  deviceScaleFactor: 2,
});

await page.goto(baseUrl, { waitUntil: 'networkidle' });
await page.screenshot({ path: 'docs/screenshots/ganymede-overview.png', fullPage: false });

await page.locator('#run-button').click();
await page.locator('#phase-pill', { hasText: 'Complete' }).waitFor({ timeout: 15000 });
await page.locator('.workspace').screenshot({ path: 'docs/screenshots/reasoning-trail.png' });

await page.locator('[data-layer="uncertainty"]').click();
await page.locator('.map-panel').screenshot({ path: 'docs/screenshots/layer-inspection.png' });

await browser.close();

