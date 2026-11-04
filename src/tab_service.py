"""Tab 2 — Service coverage. Owner: Siddal (Routing Analyst). Dijkstra from the selected hub.
This tab OWNS the shared hub dropdown and the shared internal-transfer-target slider (session key service_promise)."""
from __future__ import annotations

from math import inf

import pandas as pd
import streamlit as st

from . import advisor as ad
from . import promise_sync as ps
from . import routing_core as rc
from . import rationale as ra
from . import ui_components as ui
from .context import BASELINE, PROMISE_RANGE, Scenario

OWNER, ROLE = "Siddal", "Routing Analyst"


def controls(ds):
    """Rendered inside the tab; values live in st.session_state and are shared with the other tabs.
    v2.4: choosing a hub moves the target slider to that hub's suggested value (promise_sync.on_hub_change);
    dragging the slider afterwards keeps the person's own value."""
    c1, c2 = st.columns([1, 2])
    c1.selectbox("Hub / source branch", ds.order, key="selected_hub", format_func=lambda c: f"{c} · {ds.name(c)}",
                 on_change=ps.on_hub_change, args=(ds,),
                 help="Any of the seven branches can be the source. Dijkstra, the pass/fail list and the Investment "
                      "tab's upgrade pool all recalculate from it, and the target slider jumps to the value suggested "
                      "for this hub.")
    c2.slider("Proposed internal hub-to-branch transfer target (minutes)", *PROMISE_RANGE, step=1,
              key="service_promise", on_change=ps.on_promise_manual,
              help="Shared with the Investment tab. A branch meets the target when its road-network shortest time from the "
                   "hub is ≤ target (inclusive: exactly equal passes). Follows the hub dropdown (suggested value) until "
                   "you drag it. Baseline 20 min from Al Ramool — the group's proposed internal planning target, not an "
                   "existing Emirates Post customer-facing service. (Routes themselves use the strict rule Minutes < X.)")


def suggestion_panel(sc: Scenario):
    """v2.4: what target does this hub suggest, and which hub would we recommend overall?"""
    ds = sc.ds
    sug = ad.suggest_promise(ds.order, sc.routes, sc.hub)
    rank = ad.rank_hubs(ds.order, sc.routes)
    best = str(rank.iloc[0]["Hub"])
    my_rank = int(rank.loc[rank["Hub"] == sc.hub, "Rank"].iloc[0])
    lo, hi = sug["plateau"]
    rng = f"{lo}–{hi} min" if hi is not None else f"{lo} min or more"
    on_sug = sc.promise == sug["target"]
    auto = st.session_state.get("promise_auto", True)
    state = (ui.pill("target = suggestion", "ok") if on_sug else
             ui.pill("your own target", "warn") if not auto else ui.pill("target out of step — press the button", "warn"))
    passing = ", ".join(sug["passing"]) or "none"
    ui.callout(
        f"<b>Suggested target for hub {sc.hub}: {sug['target']} min</b> &nbsp;{state}<br>"
        f"<span class='note'>Rule: the smallest whole 5-minute target at which at least a third of the destination branches "
        f"({sug['k']} of {sug['n_dest']}) meet it directly. For {sc.hub}: {sug['reason']}. At {sug['target']} min the direct "
        f"branches are <b>{passing}</b>; the same set passes for any target from {rng}, so the number is a communicable "
        f"planning value inside a plateau, not a unique optimum.</span><br>"
        f"<span class='note'>As a hub, {sc.hub} ranks <b>#{my_rank} of {len(ds.order)}</b> on total travel time to the other "
        f"offices; the recommended hub is <b>{best}</b>"
        + (" — the hub currently selected." if best == sc.hub else ".") + "</span>", "blue")
    if not on_sug:
        st.button(f"Use suggested target ({sug['target']} min)", on_click=ps.use_suggested, args=(ds,), key="use_suggested")
    with st.expander("Which hub should we recommend? All seven compared at the current X", expanded=False):
        show = rank[["Rank", "Hub", "Reaches", "Total travel (min)", "Average (min)", "Slowest branch (min)",
                     "Suggested target (min)", "Branches within suggestion"]]
        ui.html_table(show, num_cols=("Rank", "Total travel (min)", "Average (min)", "Slowest branch (min)",
                                      "Suggested target (min)"),
                      row_class=lambda r: "ok" if r["Hub"] == best else "")
        st.plotly_chart(ui.hub_rank_chart(rank, sc.hub, best), width="stretch", config={"displayModeBar": False})
        st.caption(f"Computed with NetworkX Dijkstra from every office on the same route list as the other tabs "
                   f"(X = {sc.x}). Total travel = sum of the shortest times to the other six; ties are broken by the "
                   "slowest branch. The upgrade costs and the 18-minute motorbike estimate in upgrades.csv are "
                   "defined from the Al Ramool hub, so Investment results for any other hub are what-if scenarios.")


def render(sc: Scenario):
    ds, res = sc.ds, sc.dijkstra
    ui.owner_badge(OWNER, ROLE, "Dijkstra's shortest paths computed with NetworkX · step-by-step teaching trace")
    st.markdown(f"### Which branches meet the proposed {sc.promise}-minute internal transfer target?")
    st.markdown("<span class='note'>This tab measures <b>direct hub-to-branch transfer time</b> only (road-network "
                "Dijkstra). Upgrades — local fulfilment or an alternative mode — are evaluated on the Investment tab and "
                "never change these travel times.</span>", unsafe_allow_html=True)
    controls(ds)
    suggestion_panel(sc)

    names = {c: ds.name(c) for c in ds.order}
    areas = ds.branches.set_index("Code")["Area"].to_dict()
    df = rc.coverage_table(ds.order, sc.routes, ds.times, res, sc.promise, names, areas)
    n_pass = int((df["Status"] == "PASS").sum())
    n_fail = int((df["Status"] == "FAIL").sum())
    n_un = int((df["Status"] == "UNREACHABLE").sum())
    reach = df[df["Status"] != "UNREACHABLE"]
    slow = reach.iloc[-1] if len(reach) else None

    # ---- why 20 minutes? baseline rationale (computed) + current scenario, kept separate
    base_r = ra.promise_rationale(ds)
    live = (sc.x, sc.hub, sc.promise, sc.budget) != tuple(BASELINE.values())
    live_txt = ""
    if live:
        lr = ra.promise_rationale(ds, x=sc.x, hub=sc.hub, promise=sc.promise, budget=sc.budget)
        b = lr["base"]
        live_txt = (f"<br><b>Current scenario result</b> (X = {sc.x}, hub {sc.hub}, target {sc.promise} min, budget "
                    f"{ui.aed(sc.budget)}): {b['n_pass']} of {b['n_dest']} meet the direct-transfer target; upgrade "
                    f"candidates {', '.join(b['candidates']) or 'none'}"
                    f" cost {ui.aed(b['cost_total'])} — "
                    + ("budget forces a choice" if b["choice_forced"] else "no budget-constrained choice")
                    + (f"; DP {'beats greedy by ' + ui.aed(b['gap']) + '/yr' if b['gap'] > 0 else 'and greedy agree'}"
                       if b["candidates"] else "") + ".")
    if st.session_state.get("t3_edit"):
        live_txt += ("<br><span class='note'>Cost/benefit edits are switched on in the Investment tab; this card uses the "
                     "supplied upgrades.csv values — the Investment tab shows the edited-scenario check.</span>")
    ui.callout(f"<b>Baseline target rationale — why a proposed 20-minute internal transfer target?</b> "
               f"<span class='note'>(fixed reference: X = 38, hub HUB, budget AED 450,000, supplied assumptions)</span><br>"
               f"{ra.short_text(base_r)}"
               f"<br><span class='note'>{ra.CAVEAT}</span>{live_txt}", "amber" if live else "teal")
    if n_un:
        ui.callout(f"<b>{n_un} branch{'es' if n_un > 1 else ''} unreachable</b> from {sc.hub} at X = {sc.x}: "
                   + ", ".join(df.loc[df['Status'] == 'UNREACHABLE', 'Code']) + ". They count as outside the target "
                   "and are shown explicitly below.", "coral")

    ui.kpi_row([
        ("Direct hub-transfer branches within target", f"{n_pass} / {len(df)}", f"shortest time ≤ {sc.promise} min", "ok"),
        ("Outside direct transfer target", f"{n_fail + n_un} / {len(df)}", f"{n_fail} slower · {n_un} unreachable", "coral"),
        ("Slowest reachable branch", f"{slow['Code']} · {int(slow['Minutes'])} min" if slow is not None else "—",
         (slow["Path"] if slow is not None else "no branch reachable"), "blue"),
        ("Internal transfer target", f"{sc.promise} min", f"from {sc.hub} · within if time ≤ target", "amber"),
    ])
    st.write("")

    # ---- map: shortest-path tree highlighted, other eligible edges subdued
    status = dict(zip(df["Code"], df["Status"]))
    tree, alt = set(), set()
    for n in ds.order:
        if n == sc.hub or res["dist"][n] == inf:
            continue
        for i, p in enumerate(rc.all_shortest_paths(res["preds"], sc.hub, n)):
            for a, b in zip(p, p[1:]):
                (tree if i == 0 else alt).add((frozenset((a, b)), n))
    mins = {frozenset((a, b)): int(m) for a, b, m in sc.routes[["From", "To", "Minutes"]].itertuples(index=False, name=None)}
    styles = {key: dict(colour=ui.GREY, width=1.6, opacity=0.6, label=f"{m}", label_colour=ui.MUTED,
                        hover=f"{'–'.join(sorted(key))}: {m} min (eligible, not on a fastest path)")
              for key, m in mins.items()}
    for key, dest in alt:
        styles[key] = dict(colour=ui.AMBER, width=3, dash="dot", label=f"{mins[key]}",
                           hover=f"equal-time alternative path to {dest}")
    # a fastest-path edge is green if it serves at least one branch within the target, coral otherwise
    for key in {k for k, _ in tree}:
        dests = sorted(d for k, d in tree if k == key)
        ok = any(status.get(d) == "PASS" for d in dests)
        styles[key] = dict(colour=ui.OK if ok else ui.CORAL, width=5.5, dash="solid" if ok else "dash", label=f"<b>{mins[key]}</b>",
                           hover=f"on the fastest path to {', '.join(dests)}")
    node_colour = {c: ("#2563EB" if c == sc.hub else ui.OK if status.get(c) == "PASS" else
                       ui.CORAL if status.get(c) == "FAIL" else "#FFFFFF") for c in ds.order}
    node_text = {c: (f"{c} · hub" if c == sc.hub else f"{c} · {rc.fmt(res['dist'][c])} min" if res['dist'][c] < inf
                     else f"{c} · unreachable") for c in ds.order}
    legend = [("Fastest path — branch within target", ui.OK, "solid", 5.5),
              ("Fastest path — branch outside target", ui.CORAL, "dash", 5.5),
              ("Equal-time alternative path", ui.AMBER, "dot", 3),
              ("Other eligible route", ui.GREY, "solid", 1.6)]
    left, right = st.columns([5, 4])
    with left:
        st.plotly_chart(ui.network_figure(ds.order, sc.routes, f"Fastest van paths from {sc.hub} (X = {sc.x})", styles,
                                          node_text, node_colour, legend, height=500),
                        width="stretch", config={"displayModeBar": False})
        st.caption("Schematic links, not road geometry. Minutes are Google Maps road-time estimates; a path is a "
                   "sequence of eligible van routes, not a straight-line drive.")
    with right:
        st.plotly_chart(ui.service_bar_chart(df, sc.promise, sc.hub), width="stretch", config={"displayModeBar": False})
        st.markdown(f"<span class='note'>Rule: PASS when shortest time ≤ {sc.promise} min. Unreachable branches have no "
                    "van route under X and are treated as failing.</span>", unsafe_allow_html=True)

    st.markdown("#### Branch by branch")
    show = df[["Code", "Branch", "Area", "Shortest time", "Path", "Tied paths", "Legs", "Margin vs target (min)",
               "Status", "Direct Google drive (min)"]].copy()
    show["Status"] = show["Status"].map({"PASS": "✓ WITHIN TARGET", "FAIL": "✗ OUTSIDE TARGET", "UNREACHABLE": "⊘ UNREACHABLE"})
    st.dataframe(show, hide_index=True, width="stretch",
                 column_config={"Margin vs target (min)": st.column_config.NumberColumn(format="%+d"),
                                "Legs": st.column_config.NumberColumn("Legs (routes)", format="%d"),
                                "Direct Google drive (min)": st.column_config.NumberColumn(
                                    help="The direct Google Maps time between the hub and this branch. It is only a van "
                                         "route if it is under X.", format="%d"),
                                "Path": st.column_config.TextColumn(width="medium"),
                                "Tied paths": st.column_config.TextColumn(width="medium", help="Other paths with exactly the same time.")})
    ties = df[df["Tied paths"] != ""]
    if len(ties):
        st.markdown("**Tied fastest paths shown, not hidden:** " + "; ".join(
            f"{r.Code} {r['Shortest time']}: {r.Path} = {r['Tied paths']}" for _, r in ties.iterrows())
            + ". The first path is NetworkX's returned path (a later equal-time path does not replace it); all are equally fast.")

    with st.expander("Dijkstra step by step (teaching trace, checked against NetworkX)"):
        st.markdown(f"Times and paths above come from NetworkX (`dijkstra_predecessor_and_distance`). This table re-derives "
                    f"the same result round by round in the hand-trace format: start at **{sc.hub}** = 0, every other branch "
                    "∞; each round settles the unsettled branch with the smallest known time (ties: matrix order HUB, KAR, "
                    "QUS, UMS, JAF, SHJ, AJM), then relaxes its routes. ✔ = settled. Minutes.")
        ui.html_table(pd.DataFrame(res["steps"]), num_cols=("Round",))
        st.markdown("Teaching trace vs NetworkX distances: "
                    + ("✅ identical for every branch" if res["trace_matches_networkx"] else "⚠️ differs — NetworkX result is used"))
    st.caption(f"Data: Google Maps driving estimates, scheduled departure Thu 5 Nov 2026 07:00 (midpoint of typical range), "
               f"one time per pair used both ways. Eligible routes: Minutes < X = {sc.x} — the same list as the Network tab.")
