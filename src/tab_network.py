"""Tab 1 — Network. Owner: Shashaank (Network Analyst). Kruskal's minimum network."""
from __future__ import annotations

from math import inf

import pandas as pd
import streamlit as st

from . import advisor as ad
from . import network_core as nc
from . import routing_core as rc
from . import ui_components as ui
from .context import BASELINE, Scenario

OWNER, ROLE = "Shashaank", "Network Analyst"
ROW_PX = 35   # fixed row height so the table height is exactly header + rows (no blank filler row)


def render(sc: Scenario):
    ds, s, k = sc.ds, sc.summary, sc.kruskal
    ui.owner_badge(OWNER, ROLE, "Kruskal's minimum spanning tree (NetworkX) · step table replayed with NetworkX UnionFind · Prim cross-check")
    st.markdown("### Which van routes should Emirates Post actually run?")
    st.markdown("<span class='note'>Running every eligible corridor costs the most edge-time; Kruskal's algorithm finds the "
                "smallest set of routes that still connects all seven offices.</span>", unsafe_allow_html=True)

    # ---- what-if / connectivity warnings (live)
    if sc.x != BASELINE["threshold_x"]:
        ui.callout(f"<b>What-if threshold X = {sc.x} min</b> (Data Lead baseline is {BASELINE['threshold_x']}). "
                   f"All tabs are using these {s['n_all']} routes. The hand-trace comparison on <i>Our working</i> stays "
                   "on the X = 38 baseline.", "amber")
    if not sc.band_ok:
        ui.callout(f"⚠️ {s['n_all']} routes survive at X = {sc.x}: outside the brief's 10–14 route rule.", "amber")
    if not sc.connected:
        cut = [c for c in ds.order if c not in sc.comps[0]] if ds.hub in sc.comps[0] else []
        ui.callout(f"<b>Network NOT connected at X = {sc.x}.</b> {len(sc.comps)} separate groups: "
                   + " · ".join("{" + ", ".join(g) + "}" for g in sc.comps)
                   + f". Cut off from the hub: <b>{', '.join(cut) or '—'}</b>. Kruskal's returns a <b>minimum spanning "
                   f"forest</b> ({len(k['accepted'])} routes = 7 branches − {k['groups']} groups), not a spanning tree.",
                   "coral")

    c1, c2, c3 = st.columns([3, 3, 2])
    view = c1.radio("Network view", ["All surviving routes", "Minimum network (Kruskal)"], horizontal=True,
                    key="t1_view", help="Toggle recomputes the totals below from the current route list.")
    diagram = c2.radio("Diagram", ["Schematic diagram", "Offline coordinate map"], horizontal=True, key="t1_diagram",
                       help="Coordinate map = branch latitude/longitude from branches.csv, drawn locally (no map tiles, "
                            "no internet). Straight lines are modelled links, not roads.")
    show_rej = c3.toggle("Show rejected loop edges", value=True, key="t1_rej", disabled=view.startswith("All"),
                         help="Minimum-network view only.")
    mst_view = view.startswith("Minimum")
    tree_word = "minimum spanning tree" if k["is_tree"] else "minimum spanning forest"

    ui.kpi_row([
        ("Branches", f"{len(ds.order)}", "post offices incl. hub", "blue"),
        ("Eligible links", f"{s['n_all']}", f"drive time < X = {sc.x} min", "teal"),
        ("All-link edge-time", f"{s['total_all']} min", f"sum of {s['n_all']} route minutes", "blue"),
        ("Minimum-network edge-time", f"{s['total_min']} min", f"{s['n_min']} routes · {tree_word}", "ok"),
        ("Edge-time reduction", f"{s['saving_pct']:.1f}%", f"{s['saving_min']} min less than all links", "amber"),
    ])
    st.write("")

    kept = {frozenset((a, b)) for a, b, _ in k["accepted"]}
    styles = {}
    for (a, b, m) in sc.routes[["From", "To", "Minutes"]].itertuples(index=False, name=None):
        key = frozenset((a, b))
        if not mst_view:
            styles[key] = dict(colour=ui.BLUE, width=3, label=f"{m}", hover=f"{a}–{b}: {m} min (eligible route)")
        elif key in kept:
            styles[key] = dict(colour=ui.TEAL, width=6, label=f"<b>{m}</b>", label_colour="#0B5E59",
                               hover=f"{a}–{b}: {m} min · ACCEPTED by Kruskal's")
        elif show_rej:
            styles[key] = dict(colour=ui.CORAL, width=2, dash="dash", opacity=0.8, label=f"{m} ✗",
                               label_colour="#8E2B25", hover=f"{a}–{b}: {m} min · REJECTED (would form a loop)")
    legend = ([("Eligible route (minutes on line)", ui.BLUE, "solid", 3)] if not mst_view else
              [("Kept by Kruskal's", ui.TEAL, "solid", 6)] + ([("Rejected — would form a loop", ui.CORAL, "dash", 2)]
                                                              if show_rej else []))
    node_colour = {c: ("#2563EB" if c == ds.hub else "#FFFFFF") for c in ds.order}
    node_text = {c: f"{c} · {ds.name(c)}" for c in ds.order}
    title = (f"All {s['n_all']} surviving routes · {s['total_all']} min total" if not mst_view else
             f"Kruskal {tree_word} · {s['n_min']} routes · {s['total_min']} min total")

    fig, note = None, None
    if diagram.startswith("Offline"):
        fig, note = ui.coordinate_map(ds, sc.routes, title, styles, node_colour, legend, kept if mst_view else None)
        if note:
            ui.callout(f"⚠️ {note} Showing the schematic diagram instead.", "amber")
    left, right = st.columns([3, 2])
    card_col = right
    with left:
        if fig is not None:
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.caption("Local coordinate projection for visualisation (equirectangular, centred on the branch centroid; equal "
                       "east–west and north–south scale); straight lines represent modelled links, not road geometry. "
                       "Hover a branch for its original latitude/longitude. No map tiles or internet connection are used.")
        else:
            st.plotly_chart(ui.network_figure(ds.order, sc.routes, title, styles, node_text, node_colour, legend),
                            width="stretch", config={"displayModeBar": False})
            st.caption("Schematic links, not road geometry: node placement follows the real west–east / south–north order "
                       "of the Google Maps pins, not to scale. Edge labels are Google Maps driving-time estimates in minutes.")
    with card_col:
        groups = k["groups"]
        st.markdown(
            f"<div class='card'><h4>Why exactly {s['n_min']} routes?</h4>"
            f"A network joining <b>{len(ds.order)}</b> branches into <b>{groups}</b> connected "
            f"group{'s' if groups > 1 else ''} needs exactly {len(ds.order)} − {groups} = <b>{s['n_min']}</b> routes. "
            "Each accepted route merges two groups; one fewer would leave a branch cut off, and one more would close a "
            "loop — paying for a corridor the backbone does not need.</div>", unsafe_allow_html=True)
    with right:
        if mst_view:
            tbl = pd.DataFrame([{"Route": f"{a}–{b}", "Minutes": m} for a, b, m in k["accepted"]])
            st.markdown("**Routes in the minimum network**")
        else:
            tbl = sc.routes.assign(Route=sc.routes["From"] + "–" + sc.routes["To"],
                                   Kruskal=["kept" if frozenset((a, b)) in kept else "rejected (loop)"
                                            for a, b in zip(sc.routes["From"], sc.routes["To"])])[["Route", "Minutes", "Kruskal"]]
            st.markdown("**All eligible routes**")
        st.dataframe(tbl, hide_index=True, width="stretch", row_height=ROW_PX, height=ROW_PX * (len(tbl) + 1) + 3,
                     column_config={"Minutes": st.column_config.NumberColumn("Minutes (min)", format="%d")})

    # ---- Kruskal decision table (required output — always visible)
    st.markdown("#### Kruskal's decisions, cheapest route first")
    st.markdown("<span class='note'>Computed with NetworkX (<code>minimum_spanning_edges</code>, algorithm = Kruskal). "
                "The table replays NetworkX's own edge order — sorted by minutes, ties in branch matrix order (at X = 38 the "
                "24-minute tie HUB–SHJ is tried before UMS–JAF; either order gives the same tree and total) — with "
                "NetworkX's <code>UnionFind</code>. A route is rejected only when both ends are already in the same group."
                "</span>", unsafe_allow_html=True)
    if k["steps"]:
        ui.html_table(pd.DataFrame(k["steps"]), num_cols=("Order", "Minutes", "Running total (min)", "Groups after"),
                      row_class=lambda r: "ok" if r["Decision"] == "ACCEPT" else "bad")
    else:
        st.info("No route is under this threshold, so there is nothing for Kruskal's to sort: seven isolated branches.")
    if k["rejected"]:
        st.markdown(f"**{len(k['rejected'])} routes rejected as loops**\n" +
                    "\n".join(f"- **{r['Route']}** ({r['Minutes']} min) — {r['Reason'].split('— ')[1]}" for r in k["rejected"]))

    # ---- cheapest network vs fastest delivery (shared hub)
    st.markdown(f"#### Cheapest network ≠ fastest delivery (from {sc.hub})")
    tree = rc.tree_distances(ds.order, k["accepted"], sc.hub)
    rows = []
    for n in ds.order:
        if n == sc.hub:
            continue
        t_all = sc.dijkstra["dist"][n]
        t_tree, p_tree = tree[n]
        extra = (t_tree - t_all) if (t_tree < inf and t_all < inf) else None
        rows.append({"Branch": n, "Over minimum network": ui.minutes(t_tree), "Path on minimum network": " → ".join(p_tree) or "—",
                     "Fastest over all eligible routes": ui.minutes(t_all),
                     "Fastest path": " → ".join(rc.primary_path(sc.dijkstra["preds"], sc.hub, n)) or "—",
                     "Extra minutes on minimum network": None if extra is None else int(extra)})
    cmp = pd.DataFrame(rows)
    st.dataframe(cmp, hide_index=True, width="stretch")
    worse = cmp[cmp["Extra minutes on minimum network"].fillna(0) > 0]
    if len(worse):
        ex = worse.iloc[0]
        ui.callout("Kruskal's minimises the <b>sum</b> of the selected edge-times, not each hub-to-branch journey. "
                   + ", ".join(f"<b>{b}</b> +{int(e)} min" for b, e in zip(worse["Branch"], worse["Extra minutes on minimum network"]))
                   + f" on the tree. Example: {ex['Branch']} takes {ex['Over minimum network']} via "
                   f"{ex['Path on minimum network']} but {ex['Fastest over all eligible routes']} via {ex['Fastest path']}. "
                   "That is why the Service coverage tab runs Dijkstra on <b>all</b> eligible routes.", "blue")
    else:
        ui.callout("From this hub the minimum network happens to give the fastest time to every reachable branch.", "blue")

    # ---- cost vs resilience trade-off
    rob = nc.robustness(ds.order, sc.routes)
    leaves = [n for n in ds.order if sum(n in (a, b) for a, b, _ in k["accepted"]) == 1]
    if rob["applicable"]:
        full_txt = ("no single branch closure and no single route closure disconnects the full network "
                    f"(edge connectivity {rob['edge_connectivity']}, node connectivity {rob['node_connectivity']})"
                    if not rob["articulation_points"] and not rob["bridges"] else
                    f"critical branches {rob['articulation_points'] or 'none'}, critical routes "
                    f"{[f'{a}–{b}' for a, b, _ in rob['bridges']] or 'none'}")
        ui.callout(f"<b>Cost vs resilience.</b> Full {s['n_all']}-route network: {full_txt}. "
                   f"The {s['n_min']}-route minimum network has no spare edge: every route is a single point of failure, and "
                   f"{', '.join(leaves)} hang on one route each. Edge-time is the project's proxy for operating cost — the "
                   f"{s['saving_pct']:.1f}% is a reduction in summed route minutes, not a measured AED or fleet-mileage saving. "
                   "A practical plan keeps the low-cost backbone and selects backup corridors by operational criticality.", "teal")
    # ---- v2.4: is X = 39 better than X = 38? (computed, with the recommended hub)
    st.markdown("#### Threshold check — is X = 39 a better choice than X = 38?")
    dec = ad.x_decision(ds.order, ds.times, BASELINE["threshold_x"], BASELINE["threshold_x"] + 1)
    ui.callout(ad.x_decision_text(dec), "teal" if not dec["switch"] else "amber")
    wide = ad.threshold_audit(ds.order, ds.times, 31, 42)
    g1, g2 = st.columns(2)
    g1.plotly_chart(ui.threshold_route_chart(wide, sc.x, BASELINE["threshold_x"] + 1), width="stretch",
                    config={"displayModeBar": False})
    g2.plotly_chart(ui.threshold_time_chart(wide, sc.x), width="stretch", config={"displayModeBar": False})
    show = wide[["X (min)", "Routes", "In 10–14 band", "Connected", "Bridges", "Edge connectivity", "Recommended hub",
                 "Branches reached", "Total hub travel (min)", "Slowest branch (min)", "Network edge-time (min)",
                 "Minimum network (min)"]].copy()
    show["In 10–14 band"] = show["In 10–14 band"].map({True: "yes", False: "NO"})
    show["Connected"] = show["Connected"].map({True: "yes", False: "NO"})
    show["Branches reached"] = show["Branches reached"].astype(str) + " / " + str(len(ds.order) - 1)
    ui.html_table(show, num_cols=("X (min)", "Routes", "Bridges", "Edge connectivity", "Total hub travel (min)",
                                  "Slowest branch (min)", "Network edge-time (min)", "Minimum network (min)"),
                  row_class=lambda r: "ok" if int(r["X (min)"]) == BASELINE["threshold_x"] else
                  "bad" if r["In 10–14 band"] == "NO" else "")
    st.caption("Decision rule: leave X = 38 only if the larger threshold lets the recommended hub reach branches that X = 38 "
               "cannot (and the route count stays in the brief's 10–14 band). Reach is measured from the best hub at each X "
               "(lowest total shortest travel time), recomputed with NetworkX. Green row = selected baseline; red rows "
               "are outside the route band. Bridges = routes whose loss disconnects the network.")

    with st.expander("Cross-checks: Prim's algorithm, step-table replay and robustness (all NetworkX)"):
        p = nc.prim(ds.order, sc.routes)
        nxt = nc.networkx_mst_total(ds.order, sc.routes)
        st.markdown(f"NetworkX Prim (from {ds.order[0]}): **{p['total']} min** over {len(p['edges'])} routes"
                    + ("" if sc.connected else " (a spanning forest — the network is disconnected)") + " "
                    + ("✅ same total as Kruskal's" if p["total"] == k["total"] else "⚠️ different — check data")
                    + " · Routes: " + (", ".join(f"{u}–{v} ({w})" for u, v, w in p["edges"]) or "none"))
        st.markdown(f"NetworkX `minimum_spanning_tree` total: **{nxt} min** "
                    + ("✅ agrees" if nxt == k["total"] else "⚠️ differs")
                    + " · Step-table replay identical to `minimum_spanning_edges`: "
                    + ("✅ yes" if k["networkx_verified"] else "⚠️ no"))
        if rob["applicable"]:
            st.markdown("Articulation points / bridges from `nx.articulation_points` / `nx.bridges`; re-checked by removing "
                        "each branch and each route and re-testing `nx.is_connected`: "
                        + ("✅ consistent" if rob["removal_check_agrees"] else "⚠️ inconsistent"))
    st.caption(f"Data: Google Maps driving estimates (Data Lead: Kushal), scheduled departure Thu 5 Nov 2026 07:00, midpoint "
               f"of typical range, one time per pair used in both directions. Edge rule: Minutes < X = {sc.x}.")
