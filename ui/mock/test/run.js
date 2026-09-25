// Usage: node run.js <page> <scenario.js> [dark|light] [shot-prefix]
// Opens http://127.0.0.1:8765/<page> in headless Chrome, injects t.js, runs the scenario body (async, has T and wait), prints its return.
const { chromium } = require('playwright-core');
const fs = require('fs');
(async () => {
  const [page_, scen, scheme = 'light', shot] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 1000 }, colorScheme: scheme, reducedMotion: process.env.RM ? 'reduce' : 'no-preference', timezoneId: 'Australia/Brisbane' });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await ctx.grantPermissions(['clipboard-read','clipboard-write'], { origin: 'http://127.0.0.1:' + (process.env.PORT || '8766') }); await page.goto('http://127.0.0.1:' + (process.env.PORT || '8766') + '/' + page_);
  await page.waitForSelector('.te-root, h1, section', { timeout: 15000 }); await page.waitForTimeout(800);
  await page.evaluate(() => document.fonts.ready);
  await page.addScriptTag({ url: '/t.js?' + Date.now() });
  const body = fs.readFileSync(scen, 'utf8');
  let out;
  try { out = await page.evaluate(`(async () => { ${body} })()`); } catch (e) { out = 'SCENARIO ERROR: ' + e.message; }
  console.log(typeof out === 'string' ? out : JSON.stringify(out, null, 1));
  if (shot) {
    const root = await page.$('.te-root');
    const main = await page.$('.te-root main');
    if (main) {
      const h = await main.evaluate(m => m.scrollHeight);
      for (let y = 0, i = 0; y < h; y += 700, i++) { await main.evaluate((m, y) => { m.scrollTop = y; }, y); await page.waitForTimeout(150); await (root || page).screenshot({ path: `${shot}-${i}.png` }); }
    } else await page.screenshot({ path: `${shot}-0.png` });
  }
  if (errs.length) console.log('ERRORS:\n' + errs.join('\n'));
  await browser.close();
})();
