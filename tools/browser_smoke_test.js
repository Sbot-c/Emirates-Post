// tools/browser_smoke_test.js — NEW in v2.2, extended in v2.3 and v2.3.1 (not the script used for the v2.1 run; that one is kept unchanged as
// tools/archive/v21.js). Browser smoke test of the running Streamlit app with Playwright + Chromium.
//
//   Setup (once):  npm install playwright@1.63.0 && npx playwright install chromium
//   Run:           streamlit run app.py            # in one terminal, from the project root
//                  node tools/browser_smoke_test.js [--url http://localhost:8501] [--screenshots screenshots/]
//   Or let it start/stop the app itself:
//                  node tools/browser_smoke_test.js --launch [--python .venv/bin/python]
//
// Checks: the three analytical tabs render with their headings and KPI labels; changing threshold, hub, internal
// transfer target and budget changes the displayed outputs (and the old baseline wording is gone); the offline
// coordinate map renders; the Project Team roster (5 names/roles in order); the 11 notebook baseline figures in Our
// working and their "fixed at baseline" note when the controls change; all four tab labels fully visible and clickable;
// zero requests leave localhost; no page-level horizontal overflow at 1440×900 and 820×1180. It does NOT test or assert anything about handwritten-evidence status
// or the contribution log. Exit code 0 = all checks passed.
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const APP_URL = opt("--url", "http://localhost:8501");
const SHOTS = opt("--screenshots", null);
const LAUNCH = args.includes("--launch");
const PY = opt("--python", process.platform === "win32" ? "python" : "python3");
const ROOT = path.resolve(__dirname, "..");
const PREFIX = "tested_build_v2_3_1_";

const results = [];
const check = (name, ok, detail = "") => { results.push({ name, ok: !!ok, detail }); console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`); };

async function waitHealthy(ms = 90000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    try { const r = await fetch(APP_URL + "/_stcore/health"); if (r.ok && (await r.text()).includes("ok")) return true; } catch (e) { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 1000));
  }
  return false;
}

(async () => {
  let server = null;
  if (LAUNCH) {
    const port = new URL(APP_URL).port || "8501";
    server = spawn(PY, ["-m", "streamlit", "run", "app.py", "--server.port", port, "--server.headless", "true",
                        "--browser.gatherUsageStats", "false"], { cwd: ROOT, stdio: "ignore" });
  }
  if (!(await waitHealthy())) { console.error(`App not reachable at ${APP_URL}`); if (server) server.kill(); process.exit(2); }
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const external = [];
  page.on("request", (r) => { const u = r.url(); if (!u.startsWith(APP_URL) && !u.startsWith("data:") && !u.startsWith("blob:")) external.push(u); });
  const main = () => page.locator('[data-testid="stMainBlockContainer"]');
  const mainText = async () => (await main().innerText()).replace(/\s+/g, " ");
  const tab = async (name) => { await page.getByRole("tab", { name, exact: true }).click(); await page.waitForTimeout(2500); };
  const slider = (label) => page.locator(`input[aria-label="${label}"]`);
  const nudge = async (label, key, n) => { const s = slider(label); await s.focus(); for (let i = 0; i < n; i++) { await page.keyboard.press(key); await page.waitForTimeout(250); } await page.waitForTimeout(3000); };
  const shot = async (file, full = false) => {
    if (!SHOTS) return;
    if (full) {
      const vp = page.viewportSize();
      const h = await page.evaluate(() => document.querySelector('[data-testid="stMainBlockContainer"]').scrollHeight + 120);
      await page.setViewportSize({ width: vp.width, height: Math.min(h, 16000) }); await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(SHOTS, PREFIX + file) });
      await page.setViewportSize(vp); await page.waitForTimeout(800);
    } else {
      await page.screenshot({ path: path.join(SHOTS, PREFIX + file) });
    }
  };
  const overflow = async () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  const navOk = async () => page.evaluate(() => {
    const cw = document.documentElement.clientWidth;
    const tabs = [...document.querySelectorAll('[data-testid="stTab"]')].map((e) => { const r = e.getBoundingClientRect(); return { t: e.innerText.trim(), l: r.left, r: r.right, w: r.width, sw: e.scrollWidth }; });
    return { ok: tabs.length === 4 && tabs.every((x) => x.l >= 0 && x.r <= cw + 0.5 && x.sw <= x.w + 1), tabs };
  });

  await page.goto(APP_URL, { waitUntil: "load" });
  await page.waitForSelector('[data-testid="stTab"]', { timeout: 60000 });
  await page.waitForTimeout(4000);

  // ---- 0. Project Team overview (header, before the tabs)
  const roster = await page.locator(".team .m").allInnerTexts();
  const want = ["Kushal Data Lead", "Shashaank Network Analyst", "Siddal Routing Analyst", "Joan Investment Analyst",
                "Sparsh Integration & Business Lead"];
  check("Project Team roster: 5 exact names and roles in order",
        JSON.stringify(roster.map((x) => x.replace(/^\d+\.\s*/, "").replace(/\s+/g, " ").trim())) === JSON.stringify(want), roster.join(" | "));
  await shot("team_overview_header_1440x900.png");

  // ---- 1. baseline: the three analytical tabs and key labels
  const tabs = await page.locator('[data-testid="stTab"]').allInnerTexts();
  check("exactly four tabs", JSON.stringify(tabs.map((t) => t.trim())) === JSON.stringify(["Network", "Service coverage", "Investment", "Our working"]), tabs.join(" | "));
  await tab("Network");
  let t = await mainText();
  check("Network heading + KPIs", t.includes("Which van routes should Emirates Post actually run?") && /ELIGIBLE LINKS 13/i.test(t) && t.includes("124 min"));
  await shot("tab1_network_schematic.png", true);
  await tab("Service coverage");
  t = await mainText();
  check("Service heading at 20 min", t.includes("proposed 20-minute internal transfer target") && /DIRECT HUB-TRANSFER BRANCHES WITHIN TARGET 2 \/ 6/i.test(t));
  await shot("tab2_service_20min.png", true);
  await tab("Investment");
  t = await mainText();
  check("Investment heading + separated KPIs", t.includes("Where should the first-year upgrade budget go?")
        && /SELECTED LOCAL-FULFILMENT UPGRADES 3 \/ 6/i.test(t) && /OUTSIDE SELECTED SERVICE PLAN 1 \/ 6/i.test(t)
        && t.includes("AED 765,000/yr") && t.includes("AED 411,960"));
  await shot("tab3_investment_dp_vs_greedy.png", true);

  // ---- 2. offline coordinate map
  await tab("Network");
  await page.getByText("Minimum network (Kruskal)", { exact: true }).click(); await page.waitForTimeout(1500);
  await page.getByText("Offline coordinate map", { exact: true }).click(); await page.waitForTimeout(3500);
  t = await mainText();
  check("coordinate map renders with km axes and caption", t.includes("Local coordinate projection for visualisation")
        && (await page.locator(".js-plotly-plot").count()) > 0 && (await page.getByText("East–west offset (km)").count()) > 0);
  await shot("tab1_offline_coordinate_map.png", true);

  // ---- 3. Our working: the 11 notebook baseline figures render (decoded, inside the panel width)
  await tab("Our working");
  await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(1000);
  t = await mainText();
  check("evidence status summary visible in the first viewport", await page.getByText("Our working — evidence status").first().evaluate((e) => e.getBoundingClientRect().top < window.innerHeight)
        && (t.match(/PENDING authentic handwritten scan/g) || []).length === 4);
  await shot("tab4_evidence_summary_top_1440x900.png");
  const imgs = await page.evaluate(() => [...document.querySelectorAll('[data-testid="stImage"] img')].map((i) => {
    const r = i.getBoundingClientRect(); const box = i.closest('[data-testid="stVerticalBlock"]').getBoundingClientRect();
    return { nw: i.naturalWidth, complete: i.complete, w: r.width, inside: r.right <= box.right + 1 }; }));
  const caps = (await page.locator('[data-testid="stImage"]').allInnerTexts()).join(" ");     // one caption per image
  check("Our working shows the 11 notebook figures + 4 Python-generated trace plots (decoded, within the panel)",
        imgs.length === 15 && imgs.every((i) => i.complete && i.nw > 0 && i.inside)
        && (t.match(/Python-generated · computer output, not handwriting/g) || []).length === 4
        && (caps.match(/Original notebook-generated figure/g) || []).length === 11
        && (caps.match(/Notebook baseline reference — X = 38, HUB, 20 min, AED 450,000/g) || []).length === 11,
        `${imgs.length} images; ${JSON.stringify(imgs.filter((i) => !(i.complete && i.nw > 0 && i.inside)))}; captions ${(caps.match(/Original notebook-generated figure/g) || []).length}`);
  check("notebook vs dashboard cross-check all agree", t.includes("12 of 12 agree"));
  for (const [label, file] of [["Data and threshold X", "tab4_notebook_data_threshold.png"], ["2 · Kruskal table", "tab4_notebook_kruskal_panel.png"],
                               ["3 · Dijkstra table", "tab4_notebook_dijkstra_panel.png"], ["4 · 0/1 knapsack grid", "tab4_notebook_knapsack_panel.png"]]) {
    const h = page.getByRole("heading", { name: label }).first();
    if (SHOTS && await h.count()) {
      await page.setViewportSize({ width: 1440, height: 2200 });
      await h.evaluate((e) => e.scrollIntoView({ block: "start" })); await page.waitForTimeout(2500);
      await shot(file);
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 });

  // ---- 4. controls change outputs (and the baseline wording is not left behind)
  await tab("Service coverage");
  await nudge("Proposed internal hub-to-branch transfer target (minutes)", "ArrowRight", 3);
  t = await mainText();
  check("target 20 → 23 updates Service tab", t.includes("proposed 23-minute internal transfer target") && /WITHIN TARGET 3 \/ 6/i.test(t)
        && t.includes("Current scenario result") && !t.includes("Which branches meet the proposed 20-minute internal transfer target?"));
  await shot("tab2_service_23min.png", true);
  await tab("Investment");
  t = await mainText();
  check("target 23 propagates to Investment", t.includes("23 min") && /DIRECT HUB-TRANSFER BRANCHES WITHIN TARGET 3 \/ 6/i.test(t));
  await nudge("First-year budget (AED)", "ArrowLeft", 15);
  t = await mainText();
  check("budget 450,000 → 300,000 updates KPIs and business reading", /CURRENT BUDGET AED 300,000/i.test(t)
        && !/CURRENT BUDGET AED 450,000/i.test(t) && t.includes("At AED 300,000:") && !t.includes("At AED 450,000:"));
  await tab("Service coverage");
  const hubBox = page.locator('[data-testid="stSelectbox"]').filter({ hasText: "Hub / source branch" });
  await hubBox.click(); await page.waitForTimeout(800);
  await page.getByRole("option", { name: /^JAF/ }).click(); await page.waitForTimeout(3500);
  t = await mainText();
  check("hub HUB → JAF updates Service tab", t.includes("from JAF") && /DIRECT HUB-TRANSFER BRANCHES WITHIN TARGET 0 \/ 6/i.test(t)
        && !/DIRECT HUB-TRANSFER BRANCHES WITHIN TARGET 3 \/ 6/i.test(t));
  await tab("Our working");
  t = await mainText();
  check("Our working notebook figures labelled fixed at baseline after controls change",
        (t.match(/stay fixed at the baseline/g) || []).length === 5 && t.includes("hub JAF, target 23 min"));
  await nudge("Threshold X (route exists if drive time < X min)", "ArrowLeft", 5);
  await tab("Network");
  t = await mainText();
  check("threshold 38 → 33 updates Network tab", /ELIGIBLE LINKS 11/i.test(t) && t.includes("X = 33"));
  await page.getByRole("button", { name: /Reset all to baseline/ }).click(); await page.waitForTimeout(4000);
  await tab("Network");
  t = await mainText();
  check("reset restores baseline", /ELIGIBLE LINKS 13/i.test(t));

  // ---- 5. responsive: no page-level horizontal overflow; v2.3.1 adds the Dijkstra panel layout at three widths
  const dijkstra = async () => page.locator(".st-key-ow_dijkstra_panel").evaluate((el) => {
    const pr = el.getBoundingClientRect();
    const cols = [...el.querySelectorAll('[data-testid="stColumn"]')].map((c) => ({ r: c.getBoundingClientRect(), t: c.innerText }));
    const tables = [...el.querySelectorAll("table.ht")].map((t) => ({ right: t.getBoundingClientRect().right, sw: t.scrollWidth, cw: t.parentElement.clientWidth }));
    return { panelW: Math.round(pr.width), n: cols.length,
             side: cols.length === 2 && Math.abs(cols[0].r.top - cols[1].r.top) < 2 && cols[0].r.right <= cols[1].r.left + 1,
             stacked: cols.length === 2 && cols[1].r.top >= cols[0].r.bottom - 1 && Math.abs(cols[0].r.left - cols[1].r.left) < 2,
             placeholderFirst: cols.length === 2 && cols[0].t.startsWith("Handwritten trace") && cols[0].t.includes("HANDWRITTEN TRACE REQUIRED")
                               && cols[1].t.startsWith("Dashboard — baseline evidence run"),
             tablesFit: tables.length === 2 && tables.every((x) => x.right <= pr.right + 1 && x.sw <= x.cw + 1),
             pending: el.innerText.includes("Upload the original paper photo/scan from Siddal") };
  });
  const dijkstraShot = async (file) => {
    if (!SHOTS) return;
    const vp = page.viewportSize();
    const box = await page.locator(".st-key-ow_dijkstra_panel").evaluate((el) => {
      const sec = el.closest('[data-testid="stVerticalBlock"]'); const h = [...sec.querySelectorAll("h4")].find((x) => x.innerText.startsWith("3 ·"));
      const top = (h || el).getBoundingClientRect().top + window.scrollY - 10; const r = el.getBoundingClientRect();
      return { top, height: r.bottom + window.scrollY - top + 12 };
    });
    await page.setViewportSize({ width: vp.width, height: Math.min(Math.ceil(box.height) + 70, 6000) }); await page.waitForTimeout(800);
    await page.getByRole("heading", { name: "3 · Dijkstra table" }).first().evaluate((e) => e.scrollIntoView({ block: "start" }));
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(SHOTS, PREFIX + file) });
    await page.setViewportSize(vp); await page.waitForTimeout(800);
  };
  for (const [w, h] of [[1440, 900], [820, 1180], [390, 844]]) {
    await page.setViewportSize({ width: w, height: h }); await page.waitForTimeout(1500);
    if (w < 640) {                                   // phones: Streamlit opens the sidebar as an overlay — close it
      const close = page.locator('[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarHeader"] button').first();
      if (await close.isVisible().catch(() => false)) { await close.click(); await page.waitForTimeout(1000); }
    }
    const nav = await navOk();
    check(`all four tab labels fully visible at ${w}×${h}`, nav.ok, nav.tabs.map((x) => `${x.t} ${Math.round(x.l)}–${Math.round(x.r)}`).join(", "));
    for (const name of ["Network", "Service coverage", "Investment", "Our working"]) {
      await tab(name); await page.evaluate(() => window.scrollTo(0, 0));
      const ov = await overflow();
      check(`no horizontal overflow ${w}×${h} · ${name}`, ov <= 1, `scrollWidth − clientWidth = ${ov}px`);
    }
    await tab("Our working");
    await page.locator(".st-key-ow_dijkstra_panel").scrollIntoViewIfNeeded(); await page.waitForTimeout(1200);
    const d = await dijkstra();
    const want = w >= 1200 ? d.side : d.stacked;
    check(`Dijkstra panel ${w >= 1200 ? "side by side" : "stacked (placeholder above result)"} at ${w}×${h}`,
          want && d.placeholderFirst && d.tablesFit && d.pending, JSON.stringify(d));
    await dijkstraShot(`dijkstra_panel_${w}x${h}.png`);
  }
  await page.setViewportSize({ width: 820, height: 1180 });
  await tab("Investment"); await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(1000);
  await shot("responsive_820px_investment_top.png");
  await tab("Our working");
  const fh = page.getByRole("heading", { name: "3 · Dijkstra table" }).first();
  if (await fh.count()) { await fh.evaluate((e) => e.scrollIntoView({ block: "start" })); await page.waitForTimeout(1500); await shot("responsive_820px_notebook_figures.png"); }

  check("no request left localhost (offline)", external.length === 0, external.slice(0, 3).join(", "));
  await browser.close();
  if (server) server.kill();
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(3); });
