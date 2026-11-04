"""Tab 3 — Investment. Owner: Joan (Investment Analyst). 0/1 knapsack (DP) vs greedy.
Inherits the hub and the proposed internal transfer target from the Service coverage tab (read-only here) and
owns the shared budget control. Service outcomes come from ONE classifier, investment_core.classify_branch:
direct hub transfer · alternative mode (assumption) · local fulfilment upgrade · outside selected service plan."""
from __future__ import annotations

from math import inf

import pandas as pd
import streamlit as st

from . import investment_core as ic
from . import rationale as ra
from . import ui_components as ui
from .context import BASELINE, Scenario

OWNER, ROLE = "Joan", "Investment Analyst"
BUDGET_OPTIONS = list(range(0, ic.BUDGET_MAX + 1, ic.BUDGET_STEP))     # same values/step as before; labels get commas
COST_COL, BEN_COL = "First-year cost (AED)", "Annual gross-benefit proxy (AED/year)"


def _plan(names, picks):
    return " + ".join(names[i] for i in picks) or "nothing"


def render(sc: Scenario):
    ds = sc.ds
    ui.owner_badge(OWNER, ROLE, "0/1 knapsack by dynamic programming · greedy benefit-per-AED comparison · brute-force check")
    st.markdown("### Where should the first-year upgrade budget go?")

    # ---- inherited context (read-only) + the budget control this tab owns
    st.markdown(
        f"<div class='card'><b>Inherited from Service coverage (read-only here):</b> hub "
        f"{ui.pill(sc.hub + ' · ' + ds.name(sc.hub), 'grey')} &nbsp; internal transfer target {ui.pill(str(sc.promise) + ' min', 'warn')} "
        f"&nbsp; threshold {ui.pill('X = ' + str(sc.x), 'grey')} — change them on the <i>Service coverage</i> tab "
        "(or the sidebar for X).</div>", unsafe_allow_html=True)
    st.select_slider("First-year budget (AED)", options=BUDGET_OPTIONS, key="budget_aed", format_func=ui.aed,
                     help="AED 0–600,000 in AED 10,000 steps. Baseline AED 450,000. Values are whole AED; only the "
                          "label is formatted.")
    budget = int(st.session_state["budget_aed"])
    c1, c2 = st.columns(2)
    show_all = c1.toggle("Scenario view: include priced options for branches that already pass", value=False,
                         key="t3_show_all", help="Off (default) = only branches that currently FAIL are eligible.")
    edit = c2.toggle("Scenario: edit cost / benefit assumptions", value=False, key="t3_edit",
                     help="Off (default) = the supplied upgrades.csv values. When on, every output below recalculates.")

    upgrades = ds.upgrades.copy()
    if edit:
        ui.callout("<b>Edited-assumption scenario.</b> Results below use your edits, not the supplied baseline. "
                   "Turn the toggle off to return to upgrades.csv.", "amber")
        edited = st.data_editor(upgrades[["Code", "Upgrade", "Cost_AED", "Benefit_AED"]], hide_index=True,
                                width="stretch", key="t3_editor", disabled=["Code", "Upgrade"],
                                column_config={"Cost_AED": st.column_config.NumberColumn(COST_COL, min_value=0, step=10),
                                               "Benefit_AED": st.column_config.NumberColumn(BEN_COL, min_value=0, step=1000)})
        bad = edited["Cost_AED"].isna() | (edited["Cost_AED"] <= 0) | edited["Benefit_AED"].isna() | (edited["Benefit_AED"] < 0)
        if bad.any():
            st.warning("Rows with a blank/zero cost or blank/negative benefit are excluded: "
                       + ", ".join(edited.loc[bad, "Code"]))
        edited = edited[~bad]
        upgrades = upgrades[upgrades["Code"].isin(edited["Code"])].copy()
        upgrades["Cost_AED"] = edited.set_index("Code").loc[upgrades["Code"], "Cost_AED"].round().astype(int).values
        upgrades["Benefit_AED"] = edited.set_index("Code").loc[upgrades["Code"], "Benefit_AED"].round().astype(int).values

    dist = sc.dijkstra["dist"]
    pool = ic.build_pool(upgrades, dist, sc.hub, sc.promise, show_all)
    rows = pool["rows"]

    # ---- upgrade options table: compact primary view + details expander (v2.2)
    table, details = [], []
    for r in ds.upgrades.itertuples(index=False):
        if r.Code == sc.hub:
            status = "Hub itself — not a destination"
        else:
            t = dist.get(r.Code, inf)
            status = ("Unreachable" if t == inf else "Outside target" if t > sc.promise else "Within target")
        u = upgrades[upgrades["Code"] == r.Code]
        cost = int(u["Cost_AED"].iloc[0]) if len(u) else None
        ben = int(u["Benefit_AED"].iloc[0]) if len(u) else None
        eligible = any(x["Code"] == r.Code for x in rows)
        elig_txt = ("eligible" if eligible and status != "Within target" else
                    "eligible (scenario view)" if eligible else "not eligible")
        table.append({"Branch": f"{r.Code} · {ds.name(r.Code)}", "Upgrade": r.Upgrade,
                      "Current hub-road time (min)": ui.minutes(dist.get(r.Code)) if r.Code != sc.hub else "—",
                      "Eligibility / status": f"{status} · {elig_txt}",
                      COST_COL: f"{cost:,}" if cost is not None else "—", BEN_COL: f"{ben:,}" if ben is not None else "—"})
        details.append({"Branch": r.Code, "Upgrade": r.Upgrade,
                        "Benefit per AED": f"{ben / cost:.2f}" if cost else "—",
                        "Service mechanism (assumption)": ic.mechanism_label(
                            {"Minutes_after": float(r.Minutes_after), "Upgrade": r.Upgrade}, sc.hub),
                        "Cost basis (first year)": r.Cost_basis, "Benefit assumption": r.Benefit_reason})
    st.markdown("#### Priced upgrade options")
    ui.html_table(pd.DataFrame(table), wrap=True)
    with st.expander("Upgrade details — service mechanism, first-year cost build-up and benefit assumptions"):
        ui.html_table(pd.DataFrame(details))
        st.markdown("<span class='note'>\"Benefit assumption\" and \"Cost basis\" are the Investment Analyst's wording "
                    "from <code>upgrades.csv</code>, shown verbatim; where it says \"promise\" it means the proposed "
                    "internal hub-to-branch transfer target, not a customer-facing service.</span>", unsafe_allow_html=True)
    st.markdown("<span class='note'>First-year upgrade cost = estimated set-up + 12 months' running, not lifetime cost. "
                "Annual gross benefit proxy = estimated annual gross fee/revenue opportunity (orders/day × fee × 300 days) — "
                "not net profit, cash flow or ROI; payback, NPV and ROI are not established (later-year operating costs, "
                "discount rate, taxes, timing and realised cash flows are not modelled). A <b>mini-hub is a local-fulfilment "
                "upgrade</b>: demand is served from stock held at the branch, the hub-to-branch travel time is unchanged and the "
                "branch is <b>not</b> counted as direct-transfer compliant. The UMS motorbike's 18 min is an assumed "
                "alternative-mode time (~20% faster than the 23-min van) defined from the Al Ramool hub. JAFZA's AED 150 "
                "'Premium B2B' rate is a fee proxy/assumption (no B2B tariff source). Sources: audit/source_register.csv."
                "</span>", unsafe_allow_html=True)
    if pool["failing_no_option"]:
        ui.callout("<b>No costed option supplied</b> for failing branch(es): "
                   + ", ".join(f"{n} ({ui.minutes(dist[n])})" for n in pool["failing_no_option"])
                   + ". The model does not invent a cost or benefit for them.", "coral")
    unreachable_funded = [r["Code"] for r in rows if r["Current_time"] == inf]
    if unreachable_funded:
        ui.callout("⚠️ " + ", ".join(unreachable_funded) + " is unreachable at this threshold. A local mini-hub still "
                   "needs a restocking route; treat its local-fulfilment assumption with caution.", "amber")

    if not rows:
        ui.callout(f"At a {sc.promise}-minute internal transfer target from {sc.hub}, no branch with a priced upgrade is "
                   "outside the target — nothing to fund. Lower the target on Service coverage, or switch on the scenario "
                   "view.", "teal")
        return

    res = ic.solve(rows, budget, sc.hub, dist, sc.promise, ds.order)
    names, cost, ben = res["names"], res["cost"], res["benefit"]
    dp, gr = res["dp"], res["greedy"]
    dplan, gplan = dp["plan"], gr["plan"]
    n_dest = dplan["n_dest"]

    st.markdown("#### DP portfolio — cost and modelled benefit")
    ui.kpi_row([
        ("Current budget", ui.aed(budget), "first-year limit", "amber"),
        ("DP first-year upgrade cost", ui.aed(dp["spent"]), _plan(names, dp["picks"]), "teal"),
        ("Annual gross benefit proxy", f"{ui.aed(dp['benefit'])}/yr", "modelled fee/revenue opportunity (DP)", "ok"),
        ("Unspent budget", ui.aed(dp["left"]), "budget − DP first-year cost", "blue"),
    ])
    st.markdown(f"#### DP portfolio — service disposition of the {n_dest} destination branches")
    alt_applicable = any(ic.upgrade_mechanism(r, sc.hub)["mechanism"] == "alternative_mode" for r in rows)
    cards = [("Direct hub-transfer branches within target", f"{dplan['direct']} / {n_dest}",
              f"primary disposition · road-network shortest time ≤ {sc.promise} min", "ok")]
    if alt_applicable:
        cards.append(("Alternative-mode branches within target (assumption)", f"{dplan['alt_qualifying_selected']} / {n_dest}",
                      "selected mode with assumed time ≤ target (upgrades.csv)"
                      + (f" · {dplan['alt_selected'] - dplan['alt_qualifying_selected']} selected, not qualifying"
                         if dplan["alt_selected"] > dplan["alt_qualifying_selected"] else ""), "blue"))
    on_direct = sum(1 for x in dplan["rows"] if x["local_fulfilment_selected"] and x["direct_transfer_pass"])
    cards += [("Selected local-fulfilment upgrades", f"{dplan['local_selected']} / {n_dest}",
               "selected interventions · travel time unchanged"
               + (f" · {on_direct} on branches already direct" if on_direct else ""), "teal"),
              ("Outside selected service plan", f"{dplan['outside']} / {n_dest}", ", ".join(dplan["outside_codes"]) or "none", "coral"),
              ("Modelled destinations with a service disposition", f"{dplan['with_disposition']} / {n_dest}",
               "primary: direct + alternative mode + local fulfilment", "amber")]
    ui.kpi_row(cards)
    st.markdown(f"<span class='note'><b>Definitions.</b> Denominator = the {n_dest} destination branches (the hub is not a "
                "destination). <i>Direct hub-transfer</i>, <i>outside selected service plan</i> and <i>modelled destinations "
                "with a service disposition</i> count each branch's single <b>primary</b> disposition (they always sum to "
                f"{n_dest}). <i>Selected local-fulfilment upgrades</i> and <i>alternative-mode branches</i> count the "
                "<b>selected interventions</b> from the DP portfolio — a branch that already meets the target directly can "
                "also carry a selected upgrade in the scenario view, and it is counted there too. Only direct hub-transfer is "
                f"travel-time compliance with the {sc.promise}-min target; local fulfilment changes the fulfilment model, not "
                "the journey time. Before any upgrade: "
                f"{res['plan_before']['direct']} / {n_dest} direct.</span>", unsafe_allow_html=True)
    st.write("")

    l, r = st.columns(2)
    for col, title, plan in [(l, "Dynamic programming optimum", dp), (r, "Greedy heuristic (best benefit per AED first)", gr)]:
        with col:
            pick_rows = [{"Upgrade": f"{names[i]} · {rows[i]['Upgrade']}", COST_COL: f"{cost[i]:,}",
                          BEN_COL: f"{ben[i]:,}"} for i in plan["picks"]] or \
                        [{"Upgrade": "nothing fits", COST_COL: "0", BEN_COL: "0"}]
            st.markdown(f"<div class='card'><h4>{title}</h4>First-year upgrade cost <b>{ui.aed(plan['spent'])}</b> · unused "
                        f"<b>{ui.aed(plan['left'])}</b> · annual gross benefit proxy <b>{ui.aed(plan['benefit'])}/yr</b><br>"
                        f"<span class='note'>{ic.plan_summary(plan['plan'])}</span></div>", unsafe_allow_html=True)
            ui.html_table(pd.DataFrame(pick_rows), wrap=True)

    # ---- branch-by-branch disposition, DP vs greedy (one classifier feeds both)
    st.markdown("#### Branch-by-branch service disposition — DP vs greedy")
    gmap = {x["branch_code"]: x for x in gplan["rows"]}
    disp = pd.DataFrame([{"Branch": f"{x['branch_code']} · {ds.name(x['branch_code'])}",
                          "Shortest hub-road time": ui.minutes(x["shortest_hub_time_min"]),
                          "Direct transfer (≤ target)": "yes" if x["direct_transfer_pass"] else "no",
                          "DP: selected upgrade": x["selected_intervention"],
                          "DP: primary disposition": x["modelled_service_disposition"],
                          "Greedy: selected upgrade": gmap[x["branch_code"]]["selected_intervention"],
                          "Greedy: primary disposition": gmap[x["branch_code"]]["modelled_service_disposition"]}
                         for x in dplan["rows"]])
    ui.html_table(disp, row_class=lambda r: "" if (r["DP: primary disposition"], r["DP: selected upgrade"]) ==
                  (r["Greedy: primary disposition"], r["Greedy: selected upgrade"]) else "bad", wrap=True)
    st.markdown("<span class='note'>Highlighted rows: the two portfolios treat the branch differently. \"Selected upgrade\" "
                "is the intervention chosen by each algorithm (\"—\" = none); it is shown even when the branch already meets "
                "the target directly. Alternative-mode times are upgrades.csv assumptions. The road-network time never "
                "changes with an upgrade.</span>", unsafe_allow_html=True)
    with st.expander("Why each branch has this disposition (DP and greedy)"):
        ui.html_table(pd.DataFrame([{"Branch": x["branch_code"], "DP": x["explanation"],
                                     "Greedy": gmap[x["branch_code"]]["explanation"]} for x in dplan["rows"]]))

    scan = ic.scan_budgets(res["units"], ben, res["unit"])
    ranges = ic.gap_ranges(scan)
    gap = dp["benefit"] - gr["benefit"]
    ui.callout(_dp_vs_greedy_text(names, cost, ben, dp, gr, ranges, budget, res["unit"]), "coral" if gap > 0 else "teal")

    # ---- does the current target force a choice? (live; uses edited assumptions when editing is on)
    lr = ra.promise_rationale(ds, upgrades=upgrades, x=sc.x, hub=sc.hub, promise=sc.promise, budget=budget)
    sens = []
    for label, b in [("Current target", lr["base"]), ("Next looser target", lr["alt"])]:
        if b is None:
            continue
        sens.append({"Scenario": label, "Target (min)": b["promise"],
                     "Direct-transfer branches": f"{b['n_pass']} of {b['n_dest']}",
                     "Failing priced candidates": ", ".join(b["candidates"]) or "none",
                     "Candidates' total first-year cost": ui.aed(b["cost_total"]),
                     "All fit the budget?": "yes" if b["all_fit"] else "no — choice forced",
                     "DP selection": ", ".join(b["dp"]) or "—", "Greedy selection": ", ".join(b["greedy"]) or "—",
                     "DP − greedy (AED/yr)": f"{b['gap']:,}"})
    st.markdown("#### Does the internal transfer target force a real investment choice?")
    st.dataframe(pd.DataFrame(sens), hide_index=True, width="stretch")
    st.markdown("<span class='note'>Computed live at the current hub, threshold, budget"
                + (" and <b>edited</b> cost/benefit values" if edit else "") + ". The next looser target is the time of the "
                "next-slowest branch outside the target (it passes because the rule is time ≤ target, inclusive). Baseline "
                "rationale: Service "
                "coverage tab and Our working → Assumptions.</span>", unsafe_allow_html=True)

    st.plotly_chart(ui.investment_chart(ic.compress_steps(scan), budget), width="stretch", config={"displayModeBar": False})
    if ranges:
        st.markdown("<span class='note'>Budgets where greedy earns less than the DP optimum: " + "; ".join(
            f"<b>{ui.aed(a)}–{ui.aed(b)}</b> (up to {ui.aed(g)}/yr)" for a, b, g in ranges) + "</span>", unsafe_allow_html=True)

    # ---- trace-scale grid and checks
    with st.expander("Knapsack DP grid and traceback (AED 10,000 trace scale) · cross-checks"):
        hc, hb = ic.trace_units(cost, budget)
        K, hbest, hchosen, hpath = ic.knapsack(hc, ben, hb)
        hspend = sum(cost[i] for i in hchosen)
        st.markdown(f"**Bottom-right K[{len(hc)}][{hb}] = {hbest // 1000:,} (AED '000)** → traceback takes "
                    f"**{_plan(names, hchosen)}**. Costs in AED 10,000 units, rounded to the nearest unit as on the hand-trace "
                    "sheet: " + ", ".join(f"{n} = {c}" for n, c in zip(names, hc)) + f"; budget = {hb} units.")
        same = sorted(hchosen) == sorted(dp["picks"])
        st.markdown(("✅ Same selection as the exact AED calculation." if same else
                     "⚠️ The trace-scale rounding changes the selection at this budget — the exact AED result above is authoritative.")
                    + (f" ⚠️ In exact AED that selection costs {ui.aed(hspend)}, over budget." if hspend > budget else ""))
        st.plotly_chart(ui.knapsack_heatmap(K, names, [r["Upgrade"] for r in rows], hc, hpath,
                                            title=f"DP grid at the current budget ({hb} units)"),
                        width="stretch", config={"displayModeBar": False})
        ui.html_table(pd.DataFrame(ic.traceback_rows(K, hpath, names, hc)), num_cols=("Step",))
        st.markdown(f"Exact calculation unit: **AED {res['unit']:,}** "
                    + ("(divides every cost and the AED 10,000 slider step — no rounding)" if res["exact"] else
                       "(no common divisor ≥ AED 10 — costs rounded UP, so the plan can never overspend)")
                    + f" → DP table of {len(cost) + 1} rows × {res['budget_units'] + 1:,} budget columns.")
        st.markdown(f"Brute force over all {2 ** len(cost)} combinations: best {ui.aed(res['brute_force']['benefit'])}/yr "
                    + ("✅ same as DP" if res["brute_force"]["agrees"] else "⚠️ different"))
        st.dataframe(pd.DataFrame([{"Greedy order": k + 1, "Upgrade": names[i], "Benefit per AED": round(ben[i] / cost[i], 3),
                                    "Cost (AED)": f"{cost[i]:,}", "Fits?": "yes" if fits else "no",
                                    "Left after (AED)": f"{left * res['unit']:,}" if res["exact"] else f"≈{left * res['unit']:,}"}
                                   for k, (i, fits, left) in enumerate(gr["steps"])]), hide_index=True, width="stretch")

    # ---- Integration & Business Lead reading of the live result
    plus = budget + 50_000
    res50 = ic.solve(rows, plus, sc.hub, dist, sc.promise, ds.order)
    added = [res50["names"][i] for i in res50["dp"]["picks"] if i not in dp["picks"]]
    dropped = [names[i] for i in dp["picks"] if i not in res50["dp"]["picks"]]
    st.markdown("#### Business reading of this result")
    ui.callout(
        f"<b>At {ui.aed(budget)}:</b> fund {_plan(names, dp['picks'])} — first-year upgrade cost {ui.aed(dp['spent'])}, "
        f"{ui.aed(dp['left'])} unspent, annual gross benefit proxy {ui.aed(dp['benefit'])}/yr. Service disposition: "
        f"{ic.plan_summary(dplan)}."
        f"<br><b>With AED 50,000 more ({ui.aed(plus)}):</b> "
        + (f"add {', '.join(added)}" + (f" (and drop {', '.join(dropped)})" if dropped else "")
           + f" → first-year cost {ui.aed(res50['dp']['spent'])}, {ui.aed(res50['dp']['left'])} unspent, "
           f"{ui.aed(res50['dp']['benefit'])}/yr; {ic.plan_summary(res50['dp']['plan'])}."
           if added or dropped else "the optimal plan does not change.")
        + "<br><span class='note'>Local fulfilment does not shorten the hub-to-branch journey; conditional on the "
          "order-volume, fee and local-fulfilment assumptions; benefits are gross estimates, not net profit.</span>", "teal")
    if (sc.hub, sc.promise) != (BASELINE["selected_hub"], BASELINE["service_promise"]):
        st.caption("Note: the four options were costed for the HUB / 20-minute baseline. Results for other hubs or targets "
                   "reuse those same supplied options only where the destination branch matches.")


def _dp_vs_greedy_text(names, cost, ben, dp, gr, ranges, budget, unit):
    """Branch-specific DP-vs-greedy explanation, computed from the two portfolios."""
    gap = dp["benefit"] - gr["benefit"]
    dsel, gsel = _plan(names, dp["picks"]), _plan(names, gr["picks"])
    obj = ("DP maximises the sum of the supplied annual gross benefit proxies within the budget (each upgrade 0 or 1 "
           "time; ratios are used only by greedy). It does not by itself optimise travel time, fairness, reliability, risk, "
           "net profit or geographic coverage.")
    if gap <= 0:
        hint = None
        for a, b, _ in ranges:
            v = -(-a // ic.BUDGET_STEP) * ic.BUDGET_STEP
            if v <= b and (hint is None or abs(v - budget) < abs(hint - budget)):
                hint = v
        return (f"At {ui.aed(budget)} greedy and DP agree ({dsel}, {ui.aed(dp['benefit'])}/yr)."
                + (f" Move the budget to <b>{ui.aed(hint)}</b> to see them differ." if hint is not None else
                   " With these options they never differ between AED 0 and 600,000.") + f"<br><span class='note'>{obj}</span>")
    order = [(i, fits, left) for i, fits, left in gr["steps"]]
    taken = [names[i] for i, fits, _ in order if fits]
    missed = [(names[i], cost[i], left) for i, fits, left in order if not fits]
    why = (f"Greedy takes the best benefit-per-AED ratios first ({', '.join(taken)})"
           + (f"; {missed[0][0]} (first-year cost {ui.aed(missed[0][1])}) then no longer fits the "
              f"{ui.aed(missed[0][2] * unit)} left" if missed else "") + ".")
    d_out, g_out = dp["plan"]["outside_codes"], gr["plan"]["outside_codes"]
    return (f"<b>DP beats greedy by {ui.aed(gap)}/yr</b> in modelled annual gross benefit at {ui.aed(budget)}. "
            f"DP funds <b>{dsel}</b> ({ui.aed(dp['spent'])}); greedy funds <b>{gsel}</b> ({ui.aed(gr['spent'])}). "
            f"Outside the selected plan: DP — {', '.join(d_out) or 'none'}; greedy — {', '.join(g_out) or 'none'}. {why} "
            f"DP compares whole combinations and finds a higher total within the same budget."
            f"<br><span class='note'>{obj}</span>")
