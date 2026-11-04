// Builds contribution_log_template.docx — one page, unsigned. Usage: node tools/make_contribution_log.js
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
        PageOrientation, AlignmentType, BorderStyle, VerticalAlign, LevelFormat } = require("docx");

const INK = "172B4D", MUTED = "52606D", TEAL = "138A83", BORDER = "C9D3DE";
const W = [2000, 1900, 7140, 2300, 1560];            // sums to 14900 DXA (A4 landscape, 0.65" margins)
const TOTAL = W.reduce((a, b) => a + b, 0);
const rows = [
  ["Kushal", "Data Lead", [
    "Chose Emirates Post and the seven branches; justified the Al Ramool hub",
    "Collected the 21 Google Maps pair-times (Thu 5 Nov 2026 07:00 departure, midpoint method)",
    "Chose threshold X = 38 (13 routes) and ran the DFS connectivity check; data file + data_check.py",
    "Paper hand-trace of the DFS connectivity check (scan to be added to Our working)"]],
  ["Shashaank", "Network Analyst", [
    "Built Tab 1 (Network): Kruskal's minimum network with the all-routes / minimum toggle",
    "Wrote Kruskal and Prim step by step with NetworkX cross-check (network_core.py, kruskal_check.py)",
    "Reported 124 vs 334 min (62.9%) and the seven rejected loop routes",
    "Paper hand-trace of the Kruskal table (scan to be added to Our working)"]],
  ["Siddal", "Routing Analyst", [
    "Built Tab 2 (Service coverage): Dijkstra from any hub with the transfer-target slider",
    "Showed fastest paths, pass/fail status and the JAF 47-min tie; NetworkX cross-check",
    "Identified the four failing branches (UMS, SHJ, JAF, AJM) that feed Tab 3",
    "Paper hand-trace of the Dijkstra table (scan to be added to Our working)"]],
  ["Joan", "Investment Analyst", [
    "Defined the four upgrade options with cost build-ups and benefit assumptions (upgrades.csv)",
    "Built Tab 3 (Investment): 0/1 knapsack DP, greedy comparison and brute-force check",
    "Found the AED 45,000/yr DP-vs-greedy gap at AED 450,000; knapsack notebook and grid",
    "Paper hand-trace of the knapsack grid (scan to be added to Our working)"]],
  ["Sparsh Saraya", "Integration & Business Lead", [
    "Wrote the business question; ratified the proposed 20-min internal transfer target and AED 450,000 budget",
    "Integrated the three tabs into one four-tab app with shared hub / target / budget / threshold state",
    "Built the Our working tab, assumption and source registers, tests and validation report",
    "Prepared the recommendation slide; deployment / submission"]],
];

const border = { style: BorderStyle.SINGLE, size: 4, color: BORDER };
const borders = { top: border, bottom: border, left: border, right: border };
const cell = (children, i, opts = {}) => new TableCell({
  width: { size: W[i], type: WidthType.DXA }, borders, verticalAlign: VerticalAlign.CENTER,
  margins: { top: 70, bottom: 70, left: 110, right: 110 },
  shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: "auto" } : undefined, children });
const p = (text, o = {}) => new Paragraph({ spacing: { after: o.after ?? 0 }, alignment: o.align,
  children: [new TextRun({ text, bold: o.bold, size: o.size ?? 19, color: o.color ?? INK, italics: o.italics })] });

const header = new TableRow({ tableHeader: true, children: ["Member", "Role", "What I actually did (3–4 lines — edit before signing)", "Signature", "Date"]
  .map((h, i) => cell([p(h, { bold: true, color: "FFFFFF", size: 19 })], i, { fill: INK })) });
const body = rows.map(([name, role, lines]) => new TableRow({ height: { value: 1250, rule: "atLeast" }, children: [
  cell([p(name, { bold: true, size: 21 })], 0),
  cell([p(role, { size: 19, color: MUTED })], 1),
  cell(lines.map((t) => new Paragraph({ numbering: { reference: "dots", level: 0 }, spacing: { after: 20 },
    children: [new TextRun({ text: t, size: 18, color: INK })] })), 2),
  cell([p("")], 3),
  cell([p("")], 4),
] }));

const doc = new Document({
  creator: "Integration & Business Lead",
  title: "Contribution log — The Network Audit",
  styles: { default: { document: { run: { font: "Calibri" } } } },
  numbering: { config: [{ reference: "dots", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 220, hanging: 180 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
                          margin: { top: 760, bottom: 640, left: 940, right: 940 } } },
    children: [
      new Paragraph({ spacing: { after: 40 }, children: [
        new TextRun({ text: "Contribution log", bold: true, size: 34, color: INK }),
        new TextRun({ text: "   The Network Audit · Emirates Post · DSA Final Project (MAIB)", size: 22, color: MUTED })] }),
      new Paragraph({ spacing: { after: 120 }, children: [
        new TextRun({ text: "TEMPLATE — COLLECT ALL FIVE SIGNATURES. ", bold: true, size: 19, color: "B37D00" }),
        new TextRun({ text: "Draft lines are summarised from each member's submitted files; every member edits their own row to say what they actually did, then signs and dates it. Group: ________________________   Submitted with the dashboard on: ____________", size: 18, color: MUTED })] }),
      new Table({ width: { size: TOTAL, type: WidthType.DXA }, columnWidths: W, rows: [header, ...body] }),
      new Paragraph({ spacing: { before: 140 }, children: [
        new TextRun({ text: "By signing, each member confirms their own row is accurate. If the group cannot agree on the log, record that in writing below instead of signing something untrue (brief, p. 10).", size: 17, italics: true, color: MUTED })] }),
      new Paragraph({ spacing: { before: 80 }, children: [new TextRun({ text: "Disagreement note (if any): ______________________________________________________________________________________________________________", size: 17, color: MUTED })] }),
    ],
  }],
});
Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "..", "contribution_log_template.docx");
  fs.writeFileSync(out, buf); console.log("wrote", out);
});
