"""
advisor.py — decision helpers added in v2.4 (Integration & Business Lead). No Streamlit in here.

Three computed answers, all from the shared data and NetworkX/Dijkstra (nothing is typed in):

1. suggest_promise()  — which internal transfer target to propose for a given hub.
   Rule (transparent, reproduces the team's baseline): the SMALLEST WHOLE 5-MINUTE target at which at least one
   third of the destination branches (2 of 6) meet the direct-transfer target (shortest road time <= target).
   From the Al Ramool hub the two nearest branches are KAR 13 and QUS 16 min, so the rule gives 20 min — the
   baseline. From another hub the same rule gives that hub's own number (e.g. Sharjah 30 min). It is a
   *suggestion*: the person can still move the slider.

2. rank_hubs()        — which of the seven offices is the best hub (lowest total shortest travel time to the other
   six; ties broken by the slowest branch, then matrix order).

3. threshold_audit() / x_decision() — whether a threshold other than the baseline (X = 39 vs 38) is worth switching
   to. Switch ONLY IF it lets the recommended hub reach branches that the baseline cannot (and keeps the brief's
   10-14 route band). Everything else (faster times, fewer hops) is reported but is not enough by itself.
"""
from __future__ import annotations

from math import ceil, inf

import networkx as nx
import pandas as pd

from . import network_core as nc
from . import routing_core as rc
from .data_loader import eligible_routes

STEP_MIN = 5                  # targets are communicated in whole 5-minute steps
SHARE = 1 / 3                 # at least one third of destinations should meet the target directly
PROMISE_RANGE = (10, 90)      # same bounds as the slider (context.PROMISE_RANGE)
ROUTE_BAND = (10, 14)         # brief: choose X so that 10–14 routes survive


def _dest_times(dist: dict, hub: str) -> list:
    return sorted(t for n, t in dist.items() if n != hub and t < inf)


def suggest_promise(order: list, routes: pd.DataFrame, hub: str) -> dict:
    """Suggested internal transfer target (minutes) for `hub` on the given route list."""
    dist = rc.dijkstra(order, routes, hub)["dist"]
    dests = [n for n in order if n != hub]
    times = _dest_times(dist, hub)
    k = max(1, ceil(len(dests) * SHARE))                  # 6 destinations -> 2
    if not times:                                          # hub isolated: nothing can pass, keep the slider's floor
        target, reason = PROMISE_RANGE[0], "no branch is reachable from this hub at the current X"
    else:
        kth = times[min(k, len(times)) - 1]
        target = int(ceil(kth / STEP_MIN) * STEP_MIN)
        reason = (f"the {k} nearest branches are reached in {', '.join(str(int(t)) for t in times[:k])} min, so the "
                  f"smallest whole {STEP_MIN}-minute target that admits {k} of {len(dests)} is {target} min")
    target = max(PROMISE_RANGE[0], min(PROMISE_RANGE[1], target))
    passing = [n for n in dests if dist[n] <= target]
    failing = [n for n in dests if dist[n] > target]
    lo = max((int(dist[n]) for n in passing), default=0)
    nxt = min((int(dist[n]) for n in failing if dist[n] < inf), default=None)
    return {"hub": hub, "target": target, "k": k, "n_dest": len(dests), "passing": passing, "failing": failing,
            "plateau": (lo, None if nxt is None else nxt - 1), "reason": reason, "dist": dist}


def rank_hubs(order: list, routes: pd.DataFrame) -> pd.DataFrame:
    """One row per candidate hub, best first. Unreachable branches are counted, never ignored."""
    rows = []
    for h in order:
        sug = suggest_promise(order, routes, h)
        dist = sug["dist"]
        t = [dist[n] for n in order if n != h]
        reach = [x for x in t if x < inf]
        rows.append({"Hub": h, "Reaches": f"{len(reach)}/{len(t)}", "_reach": len(reach),
                     "Total travel (min)": int(sum(reach)) if len(reach) == len(t) else None,
                     "Average (min)": round(sum(reach) / len(reach), 1) if reach else None,
                     "Slowest branch (min)": int(max(reach)) if reach else None,
                     "Suggested target (min)": sug["target"],
                     "Branches within suggestion": f"{len(sug['passing'])}/{len(t)}",
                     "_total": sum(reach) if len(reach) == len(t) else inf,
                     "_max": max(reach) if reach else inf, "_i": order.index(h)})
    df = pd.DataFrame(rows).sort_values(["_reach", "_total", "_max", "_i"], ascending=[False, True, True, True],
                                        kind="stable").reset_index(drop=True)
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df


def recommended_hub(order: list, routes: pd.DataFrame) -> str:
    return str(rank_hubs(order, routes).iloc[0]["Hub"])


def threshold_audit(order: list, times: pd.DataFrame, lo: int = 31, hi: int = 42) -> pd.DataFrame:
    """For every X: routes, band, connectivity, weakest points, and what the RECOMMENDED hub at that X can reach."""
    rows = []
    for x in range(lo, hi + 1):
        r = eligible_routes(times, x)
        G = nx.Graph()
        G.add_nodes_from(order)
        G.add_weighted_edges_from((a, b, int(m)) for a, b, m in r[["From", "To", "Minutes"]].itertuples(index=False, name=None))
        conn = nx.is_connected(G)
        rob = nc.robustness(order, r)
        hub = recommended_hub(order, r)
        dist = rc.dijkstra(order, r, hub)["dist"]
        t = [dist[n] for n in order if n != hub]
        reach = [v for v in t if v < inf]
        k = nc.kruskal(order, r)
        rows.append({"X (min)": x, "Routes": len(r), "In 10–14 band": ROUTE_BAND[0] <= len(r) <= ROUTE_BAND[1],
                     "Connected": conn,
                     "Bridges": len(rob["bridges"]) if rob["applicable"] else None,
                     "Edge connectivity": rob.get("edge_connectivity"),
                     "Recommended hub": hub, "Branches reached": len(reach), "Of": len(t),
                     "Total hub travel (min)": int(sum(reach)), "Slowest branch (min)": int(max(reach)) if reach else None,
                     "Network edge-time (min)": int(r["Minutes"].sum()), "Minimum network (min)": k["total"]})
    return pd.DataFrame(rows)


def x_decision(order: list, times: pd.DataFrame, baseline: int = 38, candidate: int = 39) -> dict:
    """Should `candidate` replace `baseline`? Yes only if it reaches MORE branches from the recommended hub
    (and stays in the route band). Faster times alone do not justify leaving the brief's route band."""
    aud = threshold_audit(order, times, min(baseline, candidate) - 1, max(baseline, candidate) + 1).set_index("X (min)")
    b, c = aud.loc[baseline], aud.loc[candidate]
    reach_gain = int(c["Branches reached"]) - int(b["Branches reached"])
    switch = reach_gain > 0 and bool(c["In 10–14 band"])
    rb, rc_ = eligible_routes(times, baseline), eligible_routes(times, candidate)
    new_links = [f"{a}–{b_} {int(m)}" for a, b_, m in rc_[["From", "To", "Minutes"]].itertuples(index=False, name=None)
                 if not ((rb["From"] == a) & (rb["To"] == b_)).any()]
    return {"baseline": baseline, "candidate": candidate, "switch": switch, "reach_gain": reach_gain,
            "baseline_row": b.to_dict(), "candidate_row": c.to_dict(), "new_links": new_links,
            "time_gain_min": int(b["Total hub travel (min)"]) - int(c["Total hub travel (min)"]),
            "slowest_gain_min": int(b["Slowest branch (min)"]) - int(c["Slowest branch (min)"]),
            "mst_same": int(b["Minimum network (min)"]) == int(c["Minimum network (min)"]),
            "audit": aud.reset_index()}


def x_decision_text(d: dict) -> str:
    """HTML sentence(s) for the Network tab / Our working — computed, so it changes if the data changes."""
    b, c = d["baseline_row"], d["candidate_row"]
    bx, cx = d["baseline"], d["candidate"]
    head = (f"<b>X = {cx} vs X = {bx}.</b> From the recommended hub ({b['Recommended hub']}) X = {bx} already reaches "
            f"{int(b['Branches reached'])} of {int(b['Of'])} branches over {int(b['Routes'])} routes "
            f"({'no single route is a bridge' if b['Bridges'] == 0 else str(b['Bridges']) + ' bridge route(s)'}). "
            f"X = {cx} reaches {int(c['Branches reached'])} of {int(c['Of'])}")
    if d["switch"]:
        return head + f" — {d['reach_gain']} more — and stays inside the 10–14 band, so the switch is justified."
    tail = (f", i.e. no additional branch. What it does change: {int(c['Routes'])} routes"
            f"{'' if c['In 10–14 band'] else ' (outside the brief’s 10–14 band)'}, new direct link"
            f"{'s' if len(d['new_links']) != 1 else ''} {', '.join(d['new_links']) or 'none'}, hub travel total "
            f"{int(b['Total hub travel (min)'])} → {int(c['Total hub travel (min)'])} min, slowest branch "
            f"{int(b['Slowest branch (min)'])} → {int(c['Slowest branch (min)'])} min, minimum network "
            f"{'unchanged at ' + str(int(c['Minimum network (min)'])) + ' min' if d['mst_same'] else 'changes'}. "
            f"Faster times are real but do not improve reach, and the extra links break the route-count rule, so "
            f"<b>X = {bx} stays selected</b>.")
    return head + tail
