// Builds recommendation_slide.pptx from tools/baseline.json (numbers computed by tools/export_baseline.py).
// Usage: node tools/make_slide.js
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaWarehouse, FaMotorcycle, FaProjectDiagram } = require("react-icons/fa");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const B = JSON.parse(fs.readFileSync(path.join(__dirname, "baseline.json"), "utf8"));
const aed = (x) => "AED " + x.toLocaleString("en-US");
const k = (x) => "AED " + Math.round(x / 1000).toLocaleString("en-US") + "k";
const NAME = { JAF: "JAFZA", SHJ: "Sharjah", AJM: "Ajman", UMS: "Umm Suqeim" };

const THEME = {
  name: "Network Audit",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "172B4D", lt1: "FFFFFF", dk2: "52606D", lt2: "F5F7FA",
    accent1: "138A83", accent2: "3B82F6", accent3: "E5A000", accent4: "D95D55", accent5: "16856B", accent6: "E4EAF1",
    hlink: "3B82F6", folHlink: "52606D",
  },
};

async function icon(Comp, hex) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
  pres.title = "Integration Lead recommendation";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "RECOMMENDATION",
    background: { color: C.background2 },
    objects: [
      { text: { text: "THE NETWORK AUDIT · EMIRATES POST | OPERATIONS MODEL · academic project, DSA Final Project (MAIB)",
                options: { x: 0.5, y: 7.05, w: 9.5, h: 0.3, fontSize: 10, color: C.text2, margin: 0 } } },
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.35, w: 12.3, h: 0.85,
                       fontSize: 30, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: 12.4, y: 7.05, w: 0.4, h: 0.3, fontSize: 10, color: C.text2 },
  });

  pres.addSection({ title: "Recommendation" });
  const s = pres.addSlide({ masterName: "RECOMMENDATION", sectionTitle: "Recommendation" });
  s.addText(`Fund ${B.dp.picks.length} local-fulfilment mini-hubs for ${aed(B.dp.spent)} first-year cost`,
            { placeholder: "title" });

  // business question strip
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 1.35, w: 12.3, h: 0.85, rectRadius: 0.08,
    fill: { color: C.background1 }, line: { color: "E4EAF1", width: 1 }, objectName: "question card" });
  s.addText([
    { text: "Decision question  ", options: { bold: true, color: C.accent1 } },
    { text: `Keep a connected, efficient van network, test a proposed ${B.promise}-minute internal hub-to-branch transfer target from the Al Ramool model hub, and place a first-year ${aed(B.budget)} upgrade budget where the modelled gross fee opportunity is strongest.`, options: { color: C.text1 } },
    { text: `\nBASELINE SCENARIO · X = ${B.x} min (${B.routes} routes) · model hub Al Ramool · ${B.promise}-min internal target (${B.pass_before} of 6 pass today) · budget ${aed(B.budget)}`, options: { color: C.text2, fontSize: 12 } },
  ], { x: 0.75, y: 1.4, w: 11.9, h: 0.75, fontSize: 14, valign: "middle", margin: 0, isTextBox: true, objectName: "question text" });

  const SP = B.dp.service_plan, P5 = B.plus50.service_plan, GP = B.greedy.service_plan;
  // three cards
  const cards = [
    { x: 0.5, w: 4.55, fill: "138A83", ink: "FFFFFF", sub: "DDF3EC", ic: FaWarehouse, icCol: "FFFFFF",
      head: `At ${aed(B.budget)} · dynamic programming`,
      big: `${aed(B.dp.benefit)}/yr`, bigLabel: "modelled annual gross-benefit proxy (not profit)",
      lines: [
        `${SP.local_selected} local-fulfilment upgrades: ${B.dp.picks.map((c) => NAME[c]).join(", ")}`,
        `First-year cost ${aed(B.dp.spent)} · ${aed(B.dp.left)} unspent`,
        `${SP.direct} branches meet the ${B.promise}-min target by direct transfer; ${SP.outside_codes.map((c) => NAME[c] || c).join(", ") || "none"} outside plan`,
        `+${aed(B.dp.benefit - B.greedy.benefit)}/yr proxy vs greedy (${B.greedy.picks.join(", ")}) — not profit`,
      ] },
    { x: 5.25, w: 3.75, fill: "FFFFFF", ink: "172B4D", sub: "52606D", ic: FaMotorcycle, icCol: "E5A000",
      head: `If AED 50,000 more (${aed(B.plus50.budget)})`,
      big: `${aed(B.plus50.benefit)}/yr`, bigLabel: `annual gross benefit proxy · all ${B.plus50.picks.length} upgrades · ${P5.outside} outside plan`,
      lines: [
        `Add ${B.plus50.added.map((c) => NAME[c]).join(", ")} motorbike (${aed(B.plus50.added_cost)}): assumed 18-min alternative mode`,
        `Total ${aed(B.plus50.spent)} · ${aed(B.plus50.left)} left`,
        `${P5.direct} direct · ${P5.alt_mode} alternative mode (assumed) · ${P5.local_selected} local fulfilment`,
      ] },
    { x: 9.2, w: 3.6, fill: "FFFFFF", ink: "172B4D", sub: "52606D", ic: FaProjectDiagram, icCol: "3B82F6",
      head: "Network: cheap backbone, keep backups",
      big: `${B.mst_total} vs ${B.all_total} min`, bigLabel: `${B.mst_n}-route Kruskal backbone · −${B.saving_pct}% summed edge-weight (proxy, not cash)`,
      lines: [
        "Tree has no spare route: every link is a single point of failure",
        `Deliver over all routes: the tree adds +${B.tree_vs_fast.UMS[0] - B.tree_vs_fast.UMS[1]}\u00A0min to Umm Suqeim and +${B.tree_vs_fast.JAF[0] - B.tree_vs_fast.JAF[1]}\u00A0min to JAFZA`,
      ] },
  ];
  for (const c of cards) {
    const y = 2.4, h = 3.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: c.x, y, w: c.w, h, rectRadius: 0.12,
      fill: { color: c.fill }, line: { color: c.fill === "FFFFFF" ? "E4EAF1" : c.fill, width: 1 },
      shadow: { type: "outer", color: "172B4D", opacity: 0.08, blur: 6, offset: 2, angle: 90 }, objectName: c.head });
    s.addImage({ data: await icon(c.ic, c.icCol), x: c.x + 0.3, y: y + 0.3, w: 0.42, h: 0.42, objectName: c.head + " icon" });
    s.addText(c.head, { x: c.x + 0.85, y: y + 0.25, w: c.w - 1.1, h: 0.55, fontSize: 15, bold: true, color: c.ink,
      valign: "middle", margin: 0, isTextBox: true });
    s.addText(c.big, { x: c.x + 0.3, y: y + 0.95, w: c.w - 0.6, h: 0.85, fontSize: c.w > 4 ? 34 : (c.icCol === "E5A000" ? 28 : 32), bold: true,
      color: c.fill === "FFFFFF" ? (c.icCol === "E5A000" ? "B37D00" : "172B4D") : "FFFFFF", margin: 0, isTextBox: true });
    s.addText(c.bigLabel, { x: c.x + 0.3, y: y + 1.78, w: c.w - 0.6, h: 0.45, fontSize: 12, color: c.sub, margin: 0,
      valign: "top", isTextBox: true });
    s.addText(c.lines.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < c.lines.length - 1 } })),
      { x: c.x + 0.3, y: y + 2.3, w: c.w - 0.55, h: h - 2.4, fontSize: c.lines.length > 3 ? 12 : 13, color: c.ink,
        valign: "top", paraSpaceAfter: c.lines.length > 3 ? 4 : 6, margin: 0, isTextBox: true });
  }

  // compact 20-vs-23 rationale (generated by src/rationale.py via export_baseline.py)
  const RT = B.rationale;
  s.addText([
    { text: `Why ${B.promise} min? `, options: { bold: true, color: C.accent1 } },
    { text: `A proposed internal transfer target: KAR and QUS pass directly for any target from ${RT.plateau[0]} to ${RT.plateau[1]} min; ` +
            `the 4 upgrades cost ${aed(RT.candidates_cost)} > ${aed(B.budget)}, so DP must choose. At ${RT.next_promise} min ` +
            `${RT.newly_passing.join(", ")} also passes and the other ${RT.next_candidates.length} cost ${aed(RT.next_candidates_cost)} — ` +
            (RT.next_all_fit ? "all fit, DP = greedy. " : "still over budget. ") +
            `Local fulfilment does not make the hub-to-branch journey zero minutes.`, options: { color: C.text1 } },
  ], { x: 0.5, y: 6.44, w: 12.3, h: 0.36, fontSize: 10.5, margin: 0, valign: "top", isTextBox: true, objectName: "promise rationale" });
  s.addText("Caveat: estimates only. Benefit = annual gross fee/revenue proxy, not net profit or ROI; DP maximises that proxy, not service or risk objectives. Edge-time is a cost proxy.",
    { x: 0.5, y: 6.83, w: 12.3, h: 0.2, fontSize: 10, italic: true, color: C.text2, margin: 0, isTextBox: true });

  const lst = (a) => a.map((c) => NAME[c] || c).join(", ");
  s.addNotes(
    `Integration & Business Lead, 9–11 min. BASELINE SCENARIO: X = ${B.x}, hub HUB (selected model hub, Al Ramool), proposed ${B.promise}-minute internal hub-to-branch transfer target, budget ${aed(B.budget)}; figures generated by tools/export_baseline.py from the dashboard's own functions. ` +
    `At ${aed(B.budget)} the knapsack DP funds the JAFZA, Sharjah and Ajman mini-hubs: first-year upgrade cost ${aed(B.dp.spent)}, ${aed(B.dp.left)} left, annual gross benefit proxy ${aed(B.dp.benefit)}. ` +
    `Why ${B.promise} minutes: it is a modelled internal planning target for hub-to-branch transfers, not an existing Emirates Post customer-facing service. ` +
    `Service disposition under DP: ${SP.direct} branches meet the ${B.promise}-minute target by direct hub transfer (KAR, QUS); ${SP.local_selected} selected local-fulfilment upgrades (JAFZA, Sharjah, Ajman) — their hub travel time is unchanged, so they are not counted as direct-transfer compliant; Umm Suqeim (${B.ums_now} min) remains outside the DP selected plan. Five of six have a modelled service disposition; only two meet the direct transfer target. ` +
    `Greedy funds ${lst(B.greedy.picks)} for ${aed(B.greedy.benefit)}: ${GP.direct} direct, ${GP.alt_mode} alternative mode (Umm Suqeim motorbike, assumed 18 min), ${GP.local} local fulfilment, ${lst(GP.outside_codes)} outside. DP is ${aed(B.dp.benefit - B.greedy.benefit)} a year higher in modelled gross benefit — a difference in the gross-benefit proxy, not incremental profit or cash flow. DP maximises the sum of the supplied gross-benefit proxies within budget; it is not superior on fairness, resilience, actual service time or risk, and it is not a complete capital-budgeting model. The gross-benefit estimates are assumption-based (orders per day × fee × 300 days). ` +
    `With AED 50,000 more we add the Umm Suqeim motorbike: ${aed(B.plus50.spent)} total, ${aed(B.plus50.left)} left, ${aed(B.plus50.benefit)} a year; ${P5.direct} direct, ${P5.alt_mode} alternative mode (assumed), ${P5.local} local fulfilment, ${P5.outside} outside. ` +
    `Network: the ${B.mst_n}-route Kruskal backbone is ${B.mst_total} minutes against ${B.all_total} for all ${B.routes} routes, a ${B.saving_pct}% reduction in the sum of eligible route-edge weights — a cost proxy, not cash savings or reduced daily driving cost. ` +
    `A tree has no redundancy and is slower for deliveries (Umm Suqeim ${B.tree_vs_fast.UMS[0]} vs ${B.tree_vs_fast.UMS[1]}, JAFZA ${B.tree_vs_fast.JAF[0]} vs ${B.tree_vs_fast.JAF[1]}), so service runs on all eligible routes and we keep selected backup corridors. ` +
    `${RT.slide_note} ` +
    `Payback, NPV and ROI are not established; all benefits are gross estimates.`);

  const out = path.join(__dirname, "..", "recommendation_slide.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
