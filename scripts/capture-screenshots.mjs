import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';

const baseUrl = process.env.GANYMEDE_URL || 'http://127.0.0.1:4173';
await mkdir('docs/screenshots', { recursive: true });

const browser = await chromium.launch({ headless: true });
const desktop = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});

await desktop.goto(baseUrl, { waitUntil: 'networkidle' });
await desktop.screenshot({
  path: 'docs/screenshots/ganymede-workspace.png',
  fullPage: false,
});

await desktop.getByRole('button', { name: 'Classify intent' }).click();
await desktop.getByRole('button', { name: 'Run with this' }).waitFor();
await desktop.screenshot({
  path: 'docs/screenshots/ganymede-route-review.png',
  fullPage: false,
});

await desktop.getByRole('button', { name: 'Run with this' }).click();
await desktop.getByText('Resolution ready').waitFor({ timeout: 15_000 });
await desktop.screenshot({
  path: 'docs/screenshots/ganymede-optics-resolution.png',
  fullPage: false,
});

const mobile = await browser.newPage({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
});
await mobile.goto(baseUrl, { waitUntil: 'networkidle' });
await mobile.screenshot({
  path: 'docs/screenshots/ganymede-mobile.png',
  fullPage: false,
});

await browser.close();
