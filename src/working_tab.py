"""Tab 4 — Our working. Owner: Integration & Business Lead.

Layout (top to bottom):
  1. Evidence status summary — four cards driven by evidence.py (visible without scrolling).
  2. The FIXED baseline evidence run inputs (X = 38, HUB, 20 min, AED 450,000), separate from the live controls.
  3. Four evidence panels (DFS, Kruskal, Dijkstra, knapsack): status, member, expected input, scan or placeholder,
     dashboard output from the same input, transcription comparison, typed-reference check.
     v2.2: original figures extracted unchanged from the supplied notebook are shown in the matching panel
     (src/notebook_diagrams.py) as supplementary visuals; they never change an evidence status.
  4. Assumptions and modelling choices (incl. the computed 20 vs 23-minute rationale), data provenance,
     contribution log.

Integrity: typed/computer-generated documents are never shown as handwriting; no trace is marked complete
without a genuine scan AND a transcription that matches.
"""
from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path

import pandas as pd
import streamlit as st

from . import advisor as ad
from . import evidence as ev
from . import investment_core as ic
from . import network_core as nc
from . import notebook_diagrams as nd
from . import rationale as ra
from . import routing_core as rc
from . import trace_visuals as tv
from . import ui_components as ui
from .context import BASELINE, build

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"
INTEGRATION_LEAD = "Sparsh (Integration & Business Lead)"
DIJKSTRA_PANEL_KEY = "ow_dijkstra_panel"
DERIVATIVE_NB = EVIDENCE / "reference" / "Knapsack_Trace_Joan_v2_2_reference.ipynb"
KNAPSACK_REFERENCE = "Knapsack_Comparison_Reference_v2_3_1.pdf"     # v2.3.1: corrected typed reference
REFERENCE_NOTES = {   # shown under the knapsack panel's notebook block
    KNAPSACK_REFERENCE: "Typed computational reference v2.3.1 (not a handwritten trace), regenerated from the dashboard's "
                        "v2.3 calculations by tools/make_knapsack_reference_pdf.py. It supersedes the earlier typed sheet "
                        "Knapsack_HandTrace_Sheet_Joan.pdf, whose combined five-of-six coverage row mixed direct transfer with "
                        "upgrades; that sheet is kept unchanged for provenance in archive/superseded_references/ and is not "
                        "the current reference."}

PANELS = [  # key, folder, title, member, role, typed reference, expected baseline input
    ("dfs", "dfs_kushal", "DFS connectivity check", "Kushal", "Data Lead", "DFS_Solution_EmiratesPost_X38.pdf",
     "X = 38 (Minutes < 38), start HUB, neighbours in matrix order HUB, KAR, QUS, UMS, JAF, SHJ, AJM"),
    ("kruskal", "kruskal_shashaank", "Kruskal table", "Shashaank", "Network Analyst",
     "Kruskal_Solution_EmiratesPost_X38.pdf", "X = 38: the 13 eligible routes sorted by minutes"),
    ("dijkstra", "dijkstra_siddal", "Dijkstra table", "Siddal", "Routing Analyst", None,
     "X = 38, source HUB, proposed internal transfer target 20 min (within if time ≤ 20)"),
    ("knapsack", "knapsack_joan", "0/1 knapsack grid", "Joan", "Investment Analyst",
     KNAPSACK_REFERENCE,
     "target 20 min from HUB (4 upgrade candidates outside the target), budget AED 450,000 = 45 units of AED 10,000"),
]


def _data_key(ds) -> str:
    """Content of the three canonical tables: the cache key for the fixed-baseline trace plots (v2.4)."""
    return ds.times.to_csv(index=False) + ds.upgrades.to_csv(index=False) + ds.branches.to_csv(index=False)


@st.cache_data(show_spinner=False)
def _trace_pngs(data_key: str, _sc, _inv, _trace) -> dict:
    """The four Python-generated trace figures (Matplotlib → PNG bytes). Only the fixed baseline run is plotted, so the
    result depends on nothing but the data (data_key); drawing is cached so interaction on other tabs stays quick."""
    return {"dfs": tv.dfs_figure(_sc), "kruskal": tv.kruskal_figure(_sc), "dijkstra": tv.dijkstra_figure(_sc),
            "knapsack": tv.knapsack_figure(_inv, _sc.budget)}


PY_CAPTION = {
    "dfs": "Left: tree edges (solid) and the routes DFS never needed to walk (dashed); the number in each node is its visit "
           "order. Right: the stack grows on every first visit and shrinks on every backtrack — the same rows as the step "
           "table above.",
    "kruskal": "Left: accepted routes (solid, with their order) and rejected loop routes (dashed ✗). Right: every route in the "
               "order Kruskal tries it; the line is the running total of accepted minutes and ends at the minimum-network "
               "total.",
    "dijkstra": "Left: fastest-path tree from the hub, nodes coloured against the target (dotted amber = an equal-time "
                "alternative path). Right: the known shortest time per branch after each round — boxed cells are settled; "
                "hatched cells are still ∞. This is the hand-trace grid, drawn by Python.",
    "knapsack": "Left: each option's cost and annual benefit proxy, in the order greedy considers them (benefit ÷ cost). "
                "Right: the best benefit reachable at every budget for DP and greedy — they differ exactly where greedy's "
                "first pick leaves too little budget for the better combination.",
}


def baseline_run(ds):
    sc = build(ds, BASELINE["threshold_x"], BASELINE["selected_hub"], BASELINE["service_promise"], BASELINE["budget_aed"])
    pool = ic.build_pool(ds.upgrades, sc.dijkstra["dist"], sc.hub, sc.promise)
    inv = ic.solve(pool["rows"], sc.budget, sc.hub, sc.dijkstra["dist"], sc.promise)
    hc, hb = ic.trace_units(inv["cost"], sc.budget)
    K, hbest, hchosen, hpath = ic.knapsack(hc, inv["benefit"], hb)
    return sc, pool, inv, (hc, hb, K, hbest, hchosen, hpath)


def dashboard_values(key, sc, inv, trace):
    """Values compared with a trace — every one computed now from the canonical data."""
    if key == "dfs":
        return {"visit_order": sc.dfs["visit_order"], "visited": sc.dfs["visited"], "connected": sc.dfs["connected"],
                "routes": len(sc.routes), "tree_edges": [f"{a}-{b}" for a, b in sc.dfs["tree"]]}
    if key == "kruskal":
        return {"accepted": [f"{a}-{b}" for a, b, _ in sc.kruskal["accepted"]],
                "rejected": [r["Route"].replace("–", "-") for r in sc.kruskal["rejected"]],
                "total": sc.kruskal["total"], "all_total": sc.summary["total_all"]}
    if key == "dijkstra":
        d = sc.dijkstra["dist"]
        return {"times": {n: (int(d[n]) if d[n] != float("inf") else None) for n in sc.ds.order if n != sc.hub},
                "failing_at_20": [n for n in sc.ds.order if n != sc.hub and d[n] > sc.promise]}
    hc, hb, K, hbest, hchosen, _ = trace
    n = inv["names"]
    return {"trace_units": dict(zip(n, hc)), "budget_units": hb, "bottom_right_k": hbest // 1000,
            "chosen": [n[i] for i in hchosen], "greedy": [n[i] for i in inv["greedy"]["picks"]],
            "dp_benefit_aed": inv["dp"]["benefit"], "greedy_benefit_aed": inv["greedy"]["benefit"]}


def compute_states(sc, inv, trace):
    out = {}
    for key, folder, *_rest in PANELS:
        member = _rest[1]
        out[key] = ev.state(EVIDENCE / folder, key, member, dashboard_values(key, sc, inv, trace))
    return out


def render(ds, live):
    sc, pool, inv, trace = baseline_run(ds)
    states = compute_states(sc, inv, trace)

    # ---- 1. evidence status summary (top of the tab)
    st.markdown("<div class='owner'>👤 Assembled and integrated by <b>Sparsh</b> · Integration & Business Lead · "
                "<span class='note'>each section below is labelled with its owner</span></div>", unsafe_allow_html=True)
    st.markdown("### Our working — evidence status")
    cols = st.columns(4)
    for col, (key, folder, title, member, role, _ref, _inp) in zip(cols, PANELS):
        s = states[key]
        label = "PENDING authentic handwritten scan" if s["state"] == "PENDING" else s["state"]
        col.markdown(ui.evidence_card(title, member, role, s["state"], label if s["state"] == "PENDING" else s["detail"]),
                     unsafe_allow_html=True)
    n_done = sum(states[k]["state"] == "MATCHES TRANSCRIPTION" for k in states)
    st.markdown(f"<span class='note'>{n_done} of 4 traces matched against a transcription. Status is read from "
                "<code>evidence/&lt;member&gt;/</code> on every run: a readable scan alone is not a match. "
                f"Tab owner: <b>{INTEGRATION_LEAD}</b>.</span>", unsafe_allow_html=True)

    # ---- 2. fixed baseline evidence run
    st.markdown(
        "<div class='card'><b>Fixed baseline evidence run</b> — every comparison below uses these inputs, independent of the "
        "live controls on the other tabs: "
        + " ".join(ui.pill(t, "grey") for t in ["X = 38 min (Minutes < 38)", "hub HUB · Al Ramool", "target 20 min",
                                                 "budget AED 450,000", f"{len(sc.routes)} eligible routes"])
        + (" &nbsp;" + ui.pill("live tabs are on a different scenario", "warn") if not live.is_baseline else "")
        + "</div>", unsafe_allow_html=True)
    pngs = _trace_pngs(_data_key(ds), sc, inv, trace)
    tables = tv.trace_tables(sc, inv, trace)
    st.markdown("---\n#### Key results at a glance — Python answer key for the four hand traces")
    st.markdown("<div class='note'>Computed now from the fixed baseline run, so a member can check each paper trace against one "
                "row. This is computer output — it is <b>not</b> handwriting evidence and never changes an evidence "
                "status.</div>", unsafe_allow_html=True)
    ui.html_table(tv.summary_table(sc, inv, trace), wrap=True)
    refs = json.loads((EVIDENCE / "reference" / "reference_keys.json").read_text())
    manifest = nd.load_manifest()
    live_values = nd.live_baseline_values(sc, inv, trace)
    live_scenario = None if live.is_baseline else (f"X = {live.x}, hub {live.hub}, target {live.promise} min, budget "
                                                   f"{ui.aed(live.budget)}")

    # ---- 2b. data and threshold (notebook baseline reference; no hand-trace panel of its own)
    st.markdown("---\n#### Data and threshold X")
    st.markdown(f"<div class='note'>{_threshold_sentence(sc)}</div>", unsafe_allow_html=True)
    nd.render_panel("data", manifest, live_values, live_scenario)

    # ---- 3. panels
    for n, (key, folder, title, member, role, ref_doc, expected) in enumerate(PANELS, 1):
        s = states[key]
        got = dashboard_values(key, sc, inv, trace)
        st.markdown(f"---\n#### {n} · {title}")
        st.markdown(f"<div class='owner'>✍️ Trace by <b>{member}</b> · {role} &nbsp; {ui.pill(s['state'], _tone(s['state']))}"
                    f"&nbsp; <span class='note'>folder <code>evidence/{folder}/</code></span></div>"
                    f"<div class='note'><b>Expected baseline input:</b> {expected}</div>", unsafe_allow_html=True)
        # v2.3.1: the Dijkstra pair sits in a keyed container (stable `st-key-…` class) so that a container query can
        # stack it when the panel is narrow (~820 px viewport with the sidebar open); other panels are untouched.
        with (st.container(key=DIJKSTRA_PANEL_KEY) if key == "dijkstra" else nullcontext()):
            left, right = st.columns([1, 1.25])
            with left:
                st.markdown("**Handwritten trace**")
                _evidence_column(s, folder, member, ref_doc)
            with right:
                st.markdown("**Dashboard — baseline evidence run (same input)**")
                _dashboard_panel(key, sc, inv, trace)
        if key == "knapsack":
            _knapsack_grid(inv, trace)
        _python_visuals(key, pngs, tables)                                  # v2.4: Python-generated plots + answer key
        nd.render_panel(key, manifest, live_values, live_scenario)   # v2.3: notebook baseline figures + cross-check
        if key == "knapsack":
            _knapsack_reference_notes()
        _comparison_block(key, s, got, refs[key])
    st.markdown("---\n#### Notebook vs dashboard — overall cross-check")
    nd.render_overall(manifest, live_values)

    _assumptions(ds, sc, inv)
    _provenance(ds)
    _contribution_log()


def _python_visuals(key, pngs, tables):
    """v2.4: Matplotlib plot + downloadable answer-key table for one panel (computer output, fixed baseline)."""
    st.markdown("<div class='nbref'><span class='nbtag' style='background:#E7F4F2;color:#0B5E59;border-color:#138A83'>"
                "Python-generated · computer output, not handwriting</span>"
                "<span class='note'>Fixed baseline run — X = 38, HUB, 20 min, AED 450,000</span></div>", unsafe_allow_html=True)
    st.image(pngs[key], caption=PY_CAPTION[key], width="stretch")
    st.download_button("Download this panel's answer-key table (CSV)", tables[key].to_csv(index=False).encode("utf-8"),
                       file_name=f"{key}_trace_answer_key_X38_HUB_20min.csv", mime="text/csv", key=f"csv_{key}")


def _tone(state):
    return {"PENDING": "warn", "NEEDS REVIEW": "bad", "MISMATCH": "bad", "MATCHES TRANSCRIPTION": "ok",
            "INCOMPLETE": "warn"}.get(state, "grey")


def _evidence_column(s, folder, member, ref_doc):
    if s["images"]:
        for p in s["images"]:
            st.image(str(p), caption=f"{p.name} — scan supplied for {member} (open full size via the ⤢ icon)", width="stretch")
    for p in s["pdfs"]:
        st.download_button(f"Open scan PDF: {p.name}", p.read_bytes(), file_name=p.name, key=f"dl_{folder}_{p.name}")
    if not s["scans"]:
        st.markdown(f"<div class='pending'><div class='big'>HANDWRITTEN TRACE REQUIRED</div>"
                    f"<div>Upload the original paper photo/scan from <b>{member}</b></div>"
                    f"<div class='small'>Place a JPG/PNG in <code>evidence/{folder}/</code>, then copy "
                    "<code>transcription_TEMPLATE.json</code> to <code>transcription.json</code> and enter the values "
                    "written on the paper. Typed or computer-generated sheets do not count.</div>"
                    + (f"<div class='small'><b>Problem:</b> {s['detail']}</div>" if s["state"] == "NEEDS REVIEW" else "")
                    + "</div>", unsafe_allow_html=True)
    if ref_doc:
        rp = EVIDENCE / "reference" / ref_doc
        if rp.exists():
            st.download_button(f"Typed reference (not handwritten): {ref_doc}", rp.read_bytes(), file_name=ref_doc,
                               key=f"ref_{folder}", help="Computational reference from the member's pack — useful for "
                                                         "checking, not evidence of handwriting.")
    else:
        st.caption("No typed reference document was supplied in this member's pack.")


def _knapsack_reference_notes():
    """v2.2: typed member documents are kept unchanged; outdated wording in them is flagged here, and the corrected
    derivative of the typed notebook is offered alongside (outside the evidence column and its status logic)."""
    for doc, note in REFERENCE_NOTES.items():
        if (EVIDENCE / "reference" / doc).exists():
            st.caption(note)
    if DERIVATIVE_NB.exists():
        st.download_button("Typed reference notebook — v2.2 corrected derivative (not handwritten)",
                           DERIVATIVE_NB.read_bytes(), file_name=DERIVATIVE_NB.name, key="ref_knapsack_nb_v22",
                           help="Knapsack_Trace_Joan.ipynb with its typed narrative corrected in v2.2; code, outputs and "
                                "figures unchanged. The original notebook is kept unchanged in evidence/reference/.")


def _comparison_block(key, s, got, ref):
    ref_rows = ev.compare(key, ref, got)
    ref_ok = all(r["Match"] == "yes" for r in ref_rows)
    body = f"<b>Hand-trace vs dashboard:</b> {ui.pill(s['state'], _tone(s['state']))} <span class='note'>{s['detail']}</span>"
    if s["explanation"]:
        body += f"<br><b>Mismatch explanation (member):</b> {s['explanation']}"
    body += (f"<br><b>Dashboard vs member's typed reference key:</b> "
             f"{ui.pill('AGREES', 'ok') if ref_ok else ui.pill('DOES NOT AGREE', 'bad')} "
             f"<span class='note'>({ref.get('source_file', '')}) — a code check, not hand-trace evidence.</span>")
    st.markdown(f"<div class='card'>{body}</div>", unsafe_allow_html=True)
    if s["comparison"]:
        ui.html_table(pd.DataFrame(s["comparison"]).astype(str),
                      row_class=lambda r: "ok" if r["Match"] == "yes" else "bad")


def _dashboard_panel(key, sc, inv, trace):
    ds = sc.ds
    if key == "dfs":
        st.markdown(f"Visit order **{' → '.join(sc.dfs['visit_order'])}** · reached **{sc.dfs['visited']}/{sc.dfs['total']}**"
                    f" → {'**CONNECTED**' if sc.dfs['connected'] else '**NOT CONNECTED**'} · {len(sc.routes)} routes. "
                    "Computed with NetworkX `dfs_labeled_edges`; the stack trace below is rebuilt from its events.")
        ui.html_table(pd.DataFrame(sc.dfs["steps"]), num_cols=("Step", "Visited"))
        st.caption("DFS tree edges: " + ", ".join(f"{a}–{b}" for a, b in sc.dfs["tree"]) + ". DFS proves reachability only; "
                   "it is not a delivery route.")
    elif key == "kruskal":
        acc = sc.kruskal["accepted"]
        st.markdown(f"**{len(acc)} accepted** = {' + '.join(f'{a}–{b} {m}' for a, b, m in acc)} = **{sc.kruskal['total']} min**; "
                    f"**{len(sc.kruskal['rejected'])} rejected** as loops. All {len(sc.routes)} routes = {sc.summary['total_all']} min. "
                    "Computed with NetworkX (Kruskal); table replayed with NetworkX UnionFind.")
        ui.html_table(pd.DataFrame(sc.kruskal["steps"])[["Order", "Route", "Minutes", "Decision", "Running total (min)", "Reason"]],
                      num_cols=("Order", "Minutes", "Running total (min)"),
                      row_class=lambda r: "ok" if r["Decision"] == "ACCEPT" else "bad")
    elif key == "dijkstra":
        df = rc.coverage_table(ds.order, sc.routes, ds.times, sc.dijkstra, sc.promise, {c: ds.name(c) for c in ds.order},
                               ds.branches.set_index("Code")["Area"].to_dict())
        ui.html_table(df[["Code", "Shortest time", "Path", "Tied paths", "Status"]],
                      row_class=lambda r: "ok" if r["Status"] == "PASS" else "bad", wrap=True)
        ui.html_table(pd.DataFrame(sc.dijkstra["steps"])[["Round", "Settle", "Relaxations"]], num_cols=("Round",), wrap=True)
        st.caption(f"Distances/paths from NetworkX; round-by-round teaching trace "
                   f"{'matches' if sc.dijkstra['trace_matches_networkx'] else 'DIFFERS FROM'} NetworkX. Target {sc.promise} min: "
                   f"{int((df.Status == 'PASS').sum())} within, {int((df.Status != 'PASS').sum())} outside (within if time ≤ target).")
    else:
        hc, hb, K, hbest, hchosen, hpath = trace
        n = inv["names"]
        dp, gr = inv["dp"], inv["greedy"]
        st.markdown(f"Trace scale (AED 10,000 units, costs rounded to nearest as on Joan's sheet): "
                    f"{', '.join(f'{a} {c}' for a, c in zip(n, hc))}; budget {hb}. **K[{len(hc)}][{hb}] = {hbest // 1000}** "
                    f"(AED '000).")
        st.markdown(f"**Exact AED (unit AED {inv['unit']}, authoritative):** DP {' + '.join(n[i] for i in dp['picks'])} — "
                    f"first-year cost {ui.aed(dp['spent'])}, unspent {ui.aed(dp['left'])}, annual gross benefit proxy "
                    f"{ui.aed(dp['benefit'])}/yr. Greedy {' + '.join(n[i] for i in gr['picks'])} — {ui.aed(gr['spent'])}, "
                    f"{ui.aed(gr['benefit'])}/yr. Gap **{ui.aed(dp['benefit'] - gr['benefit'])}/yr**. Brute force "
                    f"({2 ** len(n)} combinations) " + ("agrees." if inv["brute_force"]["agrees"] else "DIFFERS."))


def _knapsack_grid(inv, trace):
    hc, hb, K, hbest, hchosen, hpath = trace
    n = inv["names"]
    st.plotly_chart(ui.knapsack_heatmap(K, n, None, hc, hpath,
                                        title=f"Knapsack DP grid — baseline AED 450,000 = {hb} units · cells in AED '000"),
                    width="stretch", config={"displayModeBar": False})
    ui.html_table(pd.DataFrame(ic.traceback_rows(K, hpath, n, hc)), num_cols=("Step",))
    spend = sum(inv["cost"][i] for i in hchosen)
    same = sorted(hchosen) == sorted(inv["dp"]["picks"])
    flag = ("✅ The trace scale picks the same set as the exact-AED calculation"
            if same else "⚠️ Rounding to AED 10,000 changes the selection — the trace scale is a teaching approximation; "
                         "the exact-AED result is authoritative")
    flag += (f"; in exact AED that set costs {ui.aed(spend)} " + ("(within budget)." if spend <= BASELINE["budget_aed"]
                                                               else "— OVER BUDGET, so the exact-AED result governs."))
    st.markdown(f"<span class='note'>Selected set: <b>{' + '.join(n[i] for i in hchosen)}</b> · {flag} Unspent "
                f"{ui.aed(BASELINE['budget_aed'] - spend)}; annual gross benefit proxy {ui.aed(sum(inv['benefit'][i] for i in hchosen))}/yr."
                "</span>", unsafe_allow_html=True)
    with st.expander("Compact view for small screens — DP values at the key capacities"):
        keys = sorted({0, hb, *hc, *[w for _, w, _ in hpath]})
        rows = ["0 — no upgrades"] + [f"{i} — {x}" for i, x in enumerate(n, 1)]
        ui.html_table(pd.DataFrame([[f"{K[i][w] // 1000:,}" for w in keys] for i in range(len(K))],
                                   index=rows, columns=[f"w={w}" for w in keys]).reset_index(names="Stage (AED '000)"))


def _assumptions(ds, sc, inv):
    st.markdown("---\n#### Assumptions and modelling choices")
    tbl = nc.threshold_table(ds.order, ds.times, 26, 40)
    r39 = int(tbl.loc[tbl["X (min)"] == 39, "Routes"].iloc[0])
    r33 = int(tbl.loc[tbl["X (min)"] == 33, "Routes"].iloc[0])
    band = tbl[tbl["In 10–14 band"] & tbl["Connected"]]["X (min)"].tolist()
    total_cost = int(ds.upgrades["Cost_AED"].sum())
    rat = ra.promise_rationale(ds)
    items = [
        ("Threshold X = 38", _threshold_sentence(sc) + f" Valid connected 10–14 band: X = {band[0]}–{band[-1]}; X = 33 "
         f"is still connected with {r33} routes; X = 39 gives {r39}. Disclosure: the workbook's Threshold-sheet template "
         "says “pick the smallest X” and its Decision sheet calls 38 the largest X inside the rule — both labels are "
         "true of the band but neither is the criterion; see audit/source_workbook_errata.md. "
         + ad.x_decision_text(ad.x_decision(ds.order, ds.times))),
        ("Strict route rule Minutes < X", "HUB–JAF and HUB–AJM are exactly 38 min and are therefore excluded at X = 38. "
         "(The service rule is separate: a branch passes when time ≤ target.)"),
        ("Drive-time data", "Google Maps driving estimates for a scheduled departure of Thu 5 Nov 2026 07:00 (the morning "
         "van run), midpoint of Google's typical LOW–HIGH range rounded half-up, recorded 30 Oct 2026 — estimates for a "
         "scheduled departure, not observed journeys. Ranges, road and links: data/source/time_matrix_provenance.csv."),
        ("Two-way routes", "One time per pair, used in both directions (brief FAQ). Not a directed or time-dependent model."),
        ("Model hub", "Selected model hub — Al Ramool / Umm Ramool. Rationale (partly sourced, dated): Gulf News (2018) "
         "reported Emirates Post's HQ and central sorting moving there from Karama; no current official confirmation, so "
         "the app does not claim it is the corporate headquarters."),
        ("Proposed 20-minute internal hub-to-branch transfer target", ra.full_text(rat)),
        ("Two different boundary rules", "Route exists only if Minutes < X (strict — an edge exactly equal to X is excluded). "
         "A branch meets the transfer target if its shortest time ≤ target (inclusive — exactly equal passes, e.g. UMS at "
         "23 min with a 23-minute target)."),
        ("Primary disposition vs selected intervention (v2.2)", "Each destination has exactly one primary disposition "
         "(below). Separately, the investment algorithm's selected upgrades are recorded as interventions "
         "(local_fulfilment_selected / alternative_mode_upgrade_selected, with upgrade name and first-year cost). The "
         "'Selected local-fulfilment upgrades' KPI counts those selected interventions — so a branch that already meets "
         "the target directly but receives an optional upgrade in the scenario view is still counted, while its primary "
         "disposition stays direct transfer."),
        ("Service disposition (v2.1)", "One classifier (investment_core.classify_branch) labels every destination: DIRECT "
         "HUB TRANSFER WITHIN TARGET (road-network time ≤ target) · ALTERNATIVE MODE WITHIN TARGET (ASSUMPTION) (a selected "
         "upgrade whose assumed mode time, from upgrades.csv, is ≤ target) · LOCAL FULFILMENT UPGRADE (stock at the branch; "
         "travel time unchanged; not direct-transfer compliant) · OUTSIDE SELECTED SERVICE PLAN. Baseline DP: 2 direct, "
         "3 local fulfilment, 1 outside (UMS) — five of six have a modelled service disposition, but only two meet the "
         "20-minute direct transfer target."),
        ("AED 450,000 first-year budget", f"All four options cost {ui.aed(total_cost)}, so the budget cannot fund all of them "
         "at the 20-minute target and the knapsack has a real choice. DP maximises the sum of supplied annual gross benefit "
         "proxies; it does not optimise travel time, fairness, reliability, risk or net profit."),
        ("Upgrade costs and benefits", "The only invented numbers permitted by the brief. Costs are first-year build-ups; "
         "benefits are orders/day × fee × 300 days — an annual gross benefit proxy (modelled fee/revenue opportunity), not "
         "net profit, cash flow, ROI or verified revenue; payback, NPV and ROI are not established. The JAFZA AED 150 'Premium B2B' rate is a fee proxy/assumption (no B2B tariff "
         "source). Status of each input: audit/source_register.csv."),
        ("MST as an edge-time proxy", f"{sc.summary['saving_pct']:.1f}% is a reduction in summed route minutes (13 links → "
         "6-edge tree), a proxy for network operating cost — not a cash saving or a delivery-time reduction."),
        ("Local fulfilment", "In upgrades.csv, Minutes_after = 0 encodes a mini-hub: stock held and fulfilled locally at "
         "that branch. It is not a travel time — the hub-to-branch journey is unchanged. UMS 18 min is an assumed "
         "alternative-mode (motorbike) time, ~20% faster than the 23-min van, defined from the Al Ramool hub."),
        ("Graph library", "NetworkX computes connectivity, DFS, Kruskal, Prim and Dijkstra (brief appendix); the 0/1 knapsack "
         "DP is written by hand, with brute force as a check."),
    ]
    st.markdown("<div class='card'><table class='small-table'>" + "".join(
        f"<tr><td style='vertical-align:top;white-space:nowrap'><b>{a}</b></td><td>{b}</td></tr>" for a, b in items)
        + "</table></div>", unsafe_allow_html=True)
    with st.expander("Data Lead threshold sweep (recomputed with NetworkX from times.csv)"):
        st.dataframe(nc.threshold_table(ds.order, ds.times), hide_index=True, width="stretch")


def _provenance(ds):
    p = ROOT / "data" / "source" / "time_matrix_provenance.csv"
    with st.expander("Data provenance — recorded Google Maps ranges for all 21 pairs"):
        if p.exists():
            prov = pd.read_csv(p)
            st.dataframe(prov, hide_index=True, width="stretch",
                         column_config={"Google_Maps_directions_link": st.column_config.LinkColumn("Google Maps link",
                                                                                                   display_text="open")})
            st.caption("Extracted from the Data Lead's workbook (data/source/EmiratesPost_Network_Data.xlsx). Minutes = "
                       "midpoint of LOW and HIGH rounded half-up; the loader checks all 21 against times.csv.")
        else:
            st.warning("Provenance file not in this bundle.")


def _contribution_log():
    st.markdown("---\n#### Contribution log")
    p = ROOT / "contribution_log_template.docx"
    st.markdown(f"<div class='card'>{ui.pill('Template — collect all five signatures', 'warn')} &nbsp;One page, five "
                "members: name, role, 3–4 lines of actual work, signature, date. Not signed; not stated as agreed."
                "</div>", unsafe_allow_html=True)
    if p.exists():
        st.download_button("Download contribution_log_template.docx", p.read_bytes(), file_name=p.name, key="dl_log")


def _threshold_sentence(sc) -> str:
    """X = 38 rationale, computed from times.csv (strict rule Minutes < X)."""
    t = {frozenset((a, b)): int(m) for a, b, m in zip(sc.ds.times.From, sc.ds.times.To, sc.ds.times.Minutes)}
    qa = t[frozenset(("QUS", "AJM"))]
    eq38 = sorted("–".join(sorted(k, key=sc.ds.order.index)) for k, m in t.items() if m == sc.x)
    n = {x: sum(m < x for m in t.values()) for x in (sc.x - 1, sc.x, sc.x + 1)}
    tbl = nc.threshold_table(sc.ds.order, sc.ds.times, 26, 40)
    band = tbl[tbl["In 10–14 band"] & tbl["Connected"]]["X (min)"].tolist()
    others = [b for b in band if b != sc.x]
    return (f"<b>Threshold X = {sc.x}</b> (route exists only if Minutes &lt; X): QUS–AJM is {qa} min, so X = {sc.x - 1} "
            f"excludes it ({n[sc.x - 1]} routes) and X = {sc.x} includes it ({n[sc.x]} routes, connected, inside the brief's "
            f"10–14 band). The {sc.x}-minute links ({', '.join(eq38)}) stay excluded; at X = {sc.x + 1} they enter and the "
            f"count rises to {n[sc.x + 1]}, outside the band. X = {sc.x} is the smallest whole-minute threshold that admits "
            f"the {qa}-minute QUS–AJM link while keeping 10–14 routes and excluding the {sc.x}-minute links — giving Ajman a "
            "second route instead of depending on Sharjah alone. Other thresholds "
            f"({others[0]}–{others[-1]}) are also connected and in the band; the choice rests on this criterion, not on being "
            "the smallest or largest valid X.")
