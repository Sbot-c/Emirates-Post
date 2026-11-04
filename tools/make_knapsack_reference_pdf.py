"""Generate evidence/reference/Knapsack_Comparison_Reference_v2_3_1.pdf — the corrected typed computational reference
that supersedes Knapsack_HandTrace_Sheet_Joan.pdf (archived unchanged in archive/superseded_references/).

Every number is computed here from the dashboard's own v2.3 code (src.context.build, src.investment_core) at the fixed
baseline X = 38, hub HUB, proposed 20-minute internal transfer target, budget AED 450,000 — nothing is typed by hand.
The original sheet's knapsack content (inputs, recurrence, 46-column grid, traceback, greedy comparison, result) is kept;
its outdated row "Offices meeting the 20-min promise: 5 of 6" (for DP and greedy) is replaced by a service-disposition
table that separates direct hub transfer, alternative mode (assumption), local fulfilment, outside the selected plan and
destinations with a modelled disposition.

It is a TYPED computational reference, not a handwritten trace; every page says so.

Usage (project root):  python tools/make_knapsack_reference_pdf.py      (needs reportlab; tested with reportlab 5.0.1)
`content()` builds the data model without importing reportlab, so tests can check it in the app environment.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import investment_core as ic  # noqa: E402
from src.context import BASELINE, build  # noqa: E402
from src.data_loader import load_dataset  # noqa: E402

OUT = ROOT / "evidence" / "reference" / "Knapsack_Comparison_Reference_v2_3_1.pdf"
LABEL = "Typed computational reference — not a handwritten trace"
NAMES = {"UMS": "Umm Suqeim", "JAF": "JAFZA", "SHJ": "Sharjah", "AJM": "Ajman", "KAR": "Karama", "QUS": "Al Qusais"}


def aed(x) -> str:
    return f"AED {int(x):,}"


def content() -> dict:
    """All values for the document, computed from the v2.3 code at the fixed baseline."""
    ds = load_dataset()
    sc = build(ds, BASELINE["threshold_x"], BASELINE["selected_hub"], BASELINE["service_promise"], BASELINE["budget_aed"])
    pool = ic.build_pool(ds.upgrades, sc.dijkstra["dist"], sc.hub, sc.promise)["rows"]
    res = ic.solve(pool, sc.budget, sc.hub, sc.dijkstra["dist"], sc.promise, ds.order)
    names, cost, ben = res["names"], res["cost"], res["benefit"]
    hc, hb = ic.trace_units(cost, sc.budget)
    K, hbest, hchosen, hpath = ic.knapsack(hc, ben, hb)
    tb = ic.traceback_rows(K, hpath, names, hc)
    dp, gr = res["dp"], res["greedy"]
    g_steps = [{"name": names[i], "ratio": ben[i] / cost[i], "units": hc[i], "fits": fits,
                "left_units": round(sc.budget / 10_000) - sum(hc[j] for j, f, _ in gr["steps"][:k + 1] if f)}
               for k, (i, fits, _left) in enumerate(gr["steps"])]

    def disp(plan):
        rows = {r["branch_code"]: r for r in plan["rows"]}
        pick = lambda d: [c for c, r in rows.items() if r["modelled_service_disposition"] == d]   # noqa: E731
        alt = [c for c, r in rows.items() if r["alternative_mode_pass"]]
        return {"direct": pick(ic.DIRECT), "alt": alt, "alt_time": {c: rows[c]["alternative_mode_time_min"] for c in alt},
                "local": [c for c, r in rows.items() if r["local_fulfilment_selected"]], "outside": plan["outside_codes"],
                "with": plan["with_disposition"], "n": plan["n_dest"], "summary": ic.plan_summary(plan)}

    up = ds.upgrades.set_index("Code")
    return {
        "x": sc.x, "hub": sc.hub, "promise": sc.promise, "budget": sc.budget, "routes": len(sc.routes),
        "dist": {c: int(sc.dijkstra["dist"][c]) for c in ds.order if c != sc.hub},
        "items": [{"row": i + 1, "code": c, "upgrade": up.loc[c, "Upgrade"], "cost": cost[i], "units": hc[i],
                   "benefit": ben[i], "ben_k": ben[i] // 1000, "ratio": ben[i] / cost[i],
                   "mechanism": ic.mechanism_label({"Minutes_after": float(up.loc[c, "Minutes_after"]),
                                                    "Upgrade": up.loc[c, "Upgrade"]}, sc.hub)} for i, c in enumerate(names)],
        "budget_units": hb, "K": K, "bottom_right": hbest, "trace_cells": {(i, w) for i, w, _ in hpath},
        "traceback": tb, "trace_chosen": [names[i] for i in hchosen],
        "units_used": sum(hc[i] for i in hchosen),
        "dp": {"picks": [names[i] for i in dp["picks"]], "spent": dp["spent"], "left": dp["left"], "benefit": dp["benefit"],
               "disp": disp(dp["plan"])},
        "greedy": {"picks": [names[i] for i, f, _ in gr["steps"] if f], "spent": gr["spent"], "left": gr["left"],
                   "benefit": gr["benefit"], "steps": g_steps, "disp": disp(gr["plan"])},
        "gap": dp["benefit"] - gr["benefit"], "brute_agrees": res["brute_force"]["agrees"], "exact_unit": res["unit"],
        "trace_same_as_exact": sorted(hchosen) == sorted(dp["picks"]),
    }


def render(c: dict, out: Path = OUT) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)

    INK, TEAL, AMBER, CORAL, GRID, HEAD = (colors.HexColor(h) for h in
                                           ("#172B4D", "#138A83", "#E5A000", "#D95D55", "#C9D2DE", "#E8EEF5"))
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17, textColor=INK, spaceAfter=4)
    H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=INK, spaceBefore=6,
                        spaceAfter=3)
    P = ParagraphStyle("p", parent=ss["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=INK, alignment=TA_LEFT)
    SM = ParagraphStyle("sm", parent=P, fontSize=8, leading=10)
    CELL = ParagraphStyle("cell", parent=P, fontSize=8, leading=10)
    BANNER = ParagraphStyle("banner", parent=P, fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#6B4E00"),
                            backColor=colors.HexColor("#FFF6DD"), borderColor=AMBER, borderWidth=0.8, borderPadding=5,
                            spaceAfter=8)

    def tbl(data, widths, header_rows=1, extra=()):
        t = Table([[Paragraph(str(x), CELL) if isinstance(x, str) else x for x in row] for row in data], colWidths=widths,
                  repeatRows=header_rows)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, GRID), ("BACKGROUND", (0, 0), (-1, header_rows - 1), HEAD),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 3), *extra]))
        return t

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#52606D"))
        canvas.drawString(15 * mm, 9 * mm, f"{LABEL} · Emirates Post Network Audit · v2.3.1 · baseline X = {c['x']}, hub "
                                           f"{c['hub']}, {c['promise']}-min internal transfer target, {aed(c['budget'])}")
        canvas.drawRightString(landscape(A4)[0] - 15 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(out), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm, topMargin=13 * mm,
                            bottomMargin=16 * mm, title="Knapsack comparison reference (v2.3.1) — typed computational reference",
                            author="Emirates Post Network Audit — generated by tools/make_knapsack_reference_pdf.py",
                            subject=LABEL)
    W = landscape(A4)[0] - 30 * mm
    s = []
    # ---------------------------------------------------------------- page 1: inputs and method
    s += [Paragraph("Knapsack comparison reference — inputs and method", H1),
          Paragraph(f"{LABEL}. Regenerated in v2.3.1 from the dashboard's v2.3 calculations by "
                    "<font face='Courier'>tools/make_knapsack_reference_pdf.py</font>; it supersedes the typed sheet "
                    "Knapsack_HandTrace_Sheet_Joan.pdf from the Investment Analyst's (Joan's) Tab 3 pack, which is archived "
                    "unchanged in <font face='Courier'>archive/superseded_references/</font>. The member's genuine handwritten "
                    "knapsack trace is a separate requirement and is still pending.", BANNER),
          Paragraph("Baseline inputs", H2),
          tbl([["Threshold X", "Hub", "Proposed internal hub-to-branch transfer target", "First-year investment budget",
                "Eligible routes"],
               [f"{c['x']} min (route exists if Minutes < X)", f"{c['hub']} — selected model hub, Al Ramool / Umm Ramool",
                f"{c['promise']} min (direct transfer passes if shortest time ≤ target)", aed(c["budget"]),
                str(c["routes"])]], [W * 0.17, W * 0.24, W * 0.27, W * 0.17, W * 0.15]),
          Paragraph("Question", H2),
          Paragraph(f"At the {c['promise']}-minute target, Dijkstra from {c['hub']} gives "
                    + ", ".join(f"{k} {v}" for k, v in c["dist"].items())
                    + f" min: {', '.join(k for k, v in c['dist'].items() if v <= c['promise'])} meet it by direct hub transfer; "
                    f"the other four each have one priced upgrade. With a first-year budget of {aed(c['budget'])}, which "
                    "upgrades give the largest modelled annual gross-benefit proxy without exceeding the budget?", P),
          Paragraph("Inputs (rows in the group's matrix order)", H2)]
    rows = [["Row", "Office", "Upgrade", "First-year cost (AED)", "Cost (AED 10,000 units)", "Annual gross-benefit proxy (AED/yr)",
             "Benefit (AED '000)", "Benefit per AED", "Service mechanism (assumption)"]]
    for it in c["items"]:
        rows.append([str(it["row"]), it["code"], it["upgrade"], f"{it['cost']:,}", str(it["units"]), f"{it['benefit']:,}",
                     str(it["ben_k"]), f"{it['ratio']:.2f}", it["mechanism"]])
    rows.append(["", "Budget", "", f"{c['budget']:,}", str(c["budget_units"]), "", "", "", ""])
    s += [tbl(rows, [W * f for f in (0.04, 0.06, 0.15, 0.10, 0.09, 0.12, 0.08, 0.07, 0.29)]),
          Paragraph("Rule for every cell", H2),
          Paragraph("K[0][w] = 0 for every w. For row i and budget w: if cost<sub>i</sub> &gt; w then K[i][w] = K[i−1][w] "
                    "(cannot afford it); otherwise K[i][w] = max( K[i−1][w] (leave it), benefit<sub>i</sub> + "
                    "K[i−1][w − cost<sub>i</sub>] (take it) ). Each upgrade is taken 0 or 1 times.", P),
          Paragraph("Traceback and greedy comparison", H2),
          Paragraph(f"Start at K[4][{c['budget_units']}]. If a cell differs from the one directly above, that upgrade was "
                    "taken: move left by its cost; otherwise go up a row. Greedy sorts by benefit per AED (highest first) and "
                    "takes each upgrade that still fits.", P),
          Paragraph(f"Rounding note: costs are rounded to the nearest AED 10,000 only to keep the grid to "
                    f"{c['budget_units'] + 1} columns. The dashboard computes in exact AED (unit AED {c['exact_unit']}); "
                    + ("both give the same choice at this budget." if c["trace_same_as_exact"] else
                       "the exact-AED result differs and is authoritative."), SM),
          PageBreak()]
    # ---------------------------------------------------------------- page 2: completed grid
    s += [Paragraph("Completed knapsack grid", H1),
          Paragraph(f"Cells = best annual gross-benefit proxy in AED '000 using the first i upgrades with budget w (units of "
                    f"AED 10,000). Highlighted cells = traceback path. Bottom-right K[4][{c['budget_units']}] = "
                    f"<b>{c['bottom_right'] // 1000}</b>.", P), Spacer(1, 4)]
    labels = ["0 (none)"] + [f"{it['row']} {it['code']} (c={it['units']}, b={it['ben_k']})" for it in c["items"]]
    nb = c["budget_units"] + 1
    for lo, hi in ((0, nb // 2), (nb // 2, nb)):
        data = [["row / budget w"] + [str(w) for w in range(lo, hi)]]
        hl = []
        for i, lab in enumerate(labels):
            data.append([lab] + [str(c["K"][i][w] // 1000) for w in range(lo, hi)])
            for w in range(lo, hi):
                if (i, w) in c["trace_cells"]:
                    hl += [("BACKGROUND", (w - lo + 1, i + 1), (w - lo + 1, i + 1), colors.HexColor("#FFE29A")),
                           ("FONTNAME", (w - lo + 1, i + 1), (w - lo + 1, i + 1), "Helvetica-Bold")]
        cw = (W - 30 * mm) / (hi - lo)
        t = Table(data, colWidths=[30 * mm] + [cw] * (hi - lo))
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, GRID), ("BACKGROUND", (0, 0), (-1, 0), HEAD),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 6.6),
                               ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), *hl]))
        s += [t, Spacer(1, 8)]
    cmp_key = "Compare (AED '000)"
    s += [Paragraph("<b>Traceback:</b> " + " · ".join(f"{r[cmp_key]}: {r['Decision']}" for r in c["traceback"]), SM),
          Spacer(1, 3),
          Paragraph(f"<b>Chosen (trace scale):</b> {' + '.join(c['trace_chosen'])} &nbsp;&nbsp; <b>Best:</b> "
                    f"{c['bottom_right'] // 1000} (AED {c['bottom_right']:,}/yr gross-benefit proxy) &nbsp;&nbsp; "
                    f"<b>Units used:</b> {c['units_used']} of {c['budget_units']}", SM), Spacer(1, 3),
          Paragraph(f"<b>Greedy:</b> order {' &gt; '.join(g['name'] for g in c['greedy']['steps'])} picks "
                    f"{' + '.join(c['greedy']['picks'])} (AED {c['greedy']['benefit']:,}/yr) &nbsp;&nbsp; <b>Gap (DP − greedy):</b> "
                    f"AED {c['gap']:,}/yr in gross-benefit proxy", SM),
          PageBreak()]
    # ---------------------------------------------------------------- page 3: traceback, greedy, result, service
    tb_rows = [["Step", "Item stage", "Capacity w", "Compare (AED '000)", "Decision", "Capacity left"]]
    for r in c["traceback"]:
        tb_rows.append([str(r["Step"]), r["Item stage"], str(r["Capacity w (units)"]), r["Compare (AED '000)"], r["Decision"],
                        str(r["Capacity left (units)"])])
    g_rows = [["Greedy order", "Ratio", "Units", "Fits?", "Units left"]]
    for g in c["greedy"]["steps"]:
        g_rows.append([g["name"], f"{g['ratio']:.2f}", str(g["units"]), "yes" if g["fits"] else "no", str(g["left_units"])])
    side = Table([[tbl(tb_rows, [W * f for f in (0.04, 0.08, 0.07, 0.17, 0.08, 0.07)]),
                   tbl(g_rows, [W * f for f in (0.08, 0.05, 0.05, 0.04, 0.06)])]], colWidths=[W * 0.62, W * 0.38])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    d, g = c["dp"], c["greedy"]
    res_rows = [["", "Dynamic programming (optimal)", "Greedy (best benefit per AED first)"],
                ["Upgrades funded", " + ".join(f"{p} ({NAMES[p]})" for p in d["picks"]),
                 " + ".join(f"{p} ({NAMES[p]})" for p in g["picks"])],
                ["First-year upgrade cost (exact AED)", f"{d['spent']:,}", f"{g['spent']:,}"],
                ["Budget left (exact AED)", f"{d['left']:,}", f"{g['left']:,}"],
                ["Modelled annual gross-benefit proxy (AED/yr)", f"{d['benefit']:,}", f"{g['benefit']:,}"]]

    def lst(codes, extra=lambda c_: ""):
        return f"{len(codes)} of {d['disp']['n']}" + (f" — {', '.join(x + extra(x) for x in codes)}" if codes else "")

    alt_t = lambda dd: (lambda x: f" (motorbike, assumed {dd['alt_time'][x]:.0f} min from upgrades.csv)")  # noqa: E731
    disp_rows = [["Service disposition (baseline)", "Dynamic programming", "Greedy"],
                 ["Direct hub-transfer within target (road-network time ≤ 20 min)", lst(d["disp"]["direct"]), lst(g["disp"]["direct"])],
                 ["Alternative-mode service within target (assumption)", lst(d["disp"]["alt"], alt_t(d["disp"])),
                  lst(g["disp"]["alt"], alt_t(g["disp"]))],
                 ["Local-fulfilment upgrade selected (hub travel time unchanged)", lst(d["disp"]["local"]), lst(g["disp"]["local"])],
                 ["Outside selected service plan", lst(d["disp"]["outside"]), lst(g["disp"]["outside"])],
                 ["Destinations with a modelled service disposition", f"{d['disp']['with']} of {d['disp']['n']}",
                  f"{g['disp']['with']} of {g['disp']['n']}"]]
    s += [Paragraph("Traceback, greedy comparison, result and service disposition", H1),
          Paragraph("Start at the bottom-right cell; a cell that differs from the one above means that upgrade was taken.", P),
          Spacer(1, 3), side, Spacer(1, 6),
          KeepTogether([Paragraph("Result", H2), tbl(res_rows, [W * 0.34, W * 0.33, W * 0.33])]),
          KeepTogether([Paragraph("Service disposition — replaces the earlier sheet's single combined coverage row", H2),
                        tbl(disp_rows, [W * 0.34, W * 0.33, W * 0.33],
                            extra=[("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EAF6F3"))])]),
          Spacer(1, 4),
          Paragraph(f"<b>Reading.</b> Under DP, {lst(d['disp']['direct']).split(' — ')[0]} branches "
                    f"({', '.join(d['disp']['direct'])}) meet the proposed {c['promise']}-minute target by direct hub transfer; "
                    f"{', '.join(d['disp']['local'])} receive local-fulfilment upgrades and {', '.join(d['disp']['outside'])} "
                    f"remains outside the selected DP plan. Five of six destinations have a modelled service disposition, but "
                    f"only two meet the direct-transfer target. Under greedy, {', '.join(g['disp']['alt'])} is an assumed "
                    f"alternative-mode service (not direct transfer), {', '.join(g['disp']['local'])} are local fulfilment and "
                    f"{', '.join(g['disp']['outside'])} is outside the selected plan. A local-fulfilment mini-hub does not "
                    "make the hub-to-branch journey zero minutes.", P),
          Spacer(1, 3),
          Paragraph(f"<b>DP vs greedy.</b> Greedy takes {g['picks'][0]} first (best ratio) and then the cheap "
                    f"{g['picks'][1]} motorbike, leaving too little for a further mini-hub; DP skips it so two more mini-hubs "
                    f"fit. DP's gross-benefit proxy is AED {c['gap']:,}/yr higher — a difference between modelled gross-benefit "
                    "proxies, not profit; payback, NPV and ROI are not established.", P),
          Spacer(1, 3),
          Paragraph(f"<b>Agreement with the dashboard.</b> Same inputs as the dashboard's fixed baseline run: grid "
                    f"bottom-right K[4][{c['budget_units']}] = {c['bottom_right'] // 1000}; exact-AED DP "
                    f"{' + '.join(d['picks'])}; brute force over all 16 combinations "
                    + ("agrees" if c["brute_agrees"] else "DIFFERS") + ". Values computed at generation time from the v2.3 "
                    "code; nothing typed by hand.", SM)]
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    return out


if __name__ == "__main__":
    c = content()
    p = render(c)
    print(f"wrote {p.relative_to(ROOT)}: DP {' + '.join(c['dp']['picks'])} {aed(c['dp']['spent'])} / "
          f"{aed(c['dp']['benefit'])}/yr; greedy {' + '.join(c['greedy']['picks'])}; direct {c['dp']['disp']['direct']}")
