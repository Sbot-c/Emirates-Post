// usage: node v21.js <outdir> — v2.1 tested-build screenshots + responsive checks + external-request log
const { chromium } = require('playwright');
(async () => {
  const out = process.argv[2];
  const P = 'tested_build_v2_1_';
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const requests = [];
  page.on('request', r => { const u = r.url(); if (!u.startsWith('http://localhost')) requests.push(u); });
  const log = [];
  const load = async () => {
    await page.goto('http://localhost:8501', { waitUntil: 'load' });
    await page.waitForSelector('[data-testid="stTab"]', { timeout: 60000 });
    await page.waitForTimeout(4000);
  };
  const tab = async (name) => { await page.getByRole('tab', { name, exact: true }).click(); await page.waitForTimeout(3000); };
  const full = async (file, w = 1600) => {
    const h = await page.evaluate(() => document.querySelector('[data-testid="stMainBlockContainer"]').scrollHeight + 120);
    await page.setViewportSize({ width: w, height: Math.min(h, 16000) });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${out}/${P}${file}.png` });
    await page.setViewportSize({ width: w, height: 1000 });
  };
  const overflow = async (label) => {
    const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    log.push(`${label}: scrollWidth ${r.sw} vs clientWidth ${r.cw} -> ${r.sw > r.cw + 1 ? 'HORIZONTAL OVERFLOW' : 'no page-level horizontal overflow'}`);
  };
  const sliderAt = async (value) => page.locator(`[role="slider"][aria-valuenow="${value}"]`);

  await load();
  // 1. Tab 1 schematic (all routes)
  await tab('Network'); await full('tab1_network_schematic');
  // 2. Tab 1 offline coordinate map (minimum network)
  await page.getByText('Minimum network (Kruskal)', { exact: true }).click(); await page.waitForTimeout(2000);
  await page.getByText('Offline coordinate map', { exact: true }).click(); await page.waitForTimeout(3500);
  await full('tab1_offline_coordinate_map');
  // 3. Tab 2 at 20 min
  await tab('Service coverage'); await full('tab2_service_20min');
  // 4. Tab 2 at 23 min (keyboard on the internal transfer target slider)
  const s = page.locator('input[aria-label="Proposed internal hub-to-branch transfer target (minutes)"]');
  await s.focus(); for (let i = 0; i < 3; i++) { await page.keyboard.press('ArrowRight'); await page.waitForTimeout(700); }
  await page.waitForTimeout(3500);
  log.push('target slider value now: ' + await s.inputValue());
  await full('tab2_service_23min');
  // back to baseline
  await page.getByRole('button', { name: /Reset all to baseline/ }).click(); await page.waitForTimeout(4000);
  // 5. Tab 3 DP vs greedy (full page)
  await tab('Investment'); await full('tab3_investment_dp_vs_greedy');
  // 6. Tab 4 evidence summary at the top, 1440x900, no scrolling
  await page.setViewportSize({ width: 1440, height: 900 });
  await tab('Our working'); await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}/${P}tab4_evidence_summary_top_1440x900.png` });
  await overflow('1440x900 Our working');
  // 7. Tab 4 knapsack heatmap
  const h4 = page.locator('h4', { hasText: /^4 ·/ }).first();
  await h4.scrollIntoViewIfNeeded(); await page.waitForTimeout(1500);
  await page.setViewportSize({ width: 1440, height: 1300 });
  await h4.evaluate(e => e.scrollIntoView({ block: 'start' })); await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}/${P}tab4_knapsack_heatmap.png` });
  // responsive checks
  for (const [w, h] of [[1440, 900], [820, 1180]]) {
    await page.setViewportSize({ width: w, height: h });
    for (const t of ['Network', 'Service coverage', 'Investment', 'Our working']) {
      await tab(t); await page.evaluate(() => window.scrollTo(0, 0)); await overflow(`${w}x${h} ${t}`);
    }
  }
  await page.setViewportSize({ width: 820, height: 1180 });
  await tab('Investment'); await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}/${P}responsive_820px_investment_top.png` });
  log.push('external requests: ' + JSON.stringify(requests));
  console.log(log.join('\n'));
  await browser.close();
})();
