"""
routing_core.py — Dijkstra service coverage (Routing Analyst: Siddal). No Streamlit in here.

Academic compliance: NetworkX is the AUTHORITATIVE engine for every distance and path shown —
`nx.dijkstra_predecessor_and_distance` (distances + all equal-time predecessors) and
`nx.single_source_dijkstra_path` (the primary path). Unreachable branches stay math.inf and are shown
as "Unreachable"; they are never cast to int or dropped.

The round-by-round step table ("settle / relax") is a TEACHING TRACE in Siddal's hand-trace format,
re-derived step by step and then checked against NetworkX (field `trace_matches_networkx`). It is not
the source of the displayed results.
"""
from __future__ import annotations

from math import inf

import networkx as nx
import pandas as pd

from .network_core import adjacency, nx_graph


def fmt(x) -> str:
    return "∞" if x == inf else str(int(x))


def _teaching_trace(order: list, routes: pd.DataFrame, source: str):
    """Siddal's array-scan Dijkstra, kept only to print the paper-style rounds."""
    adj = adjacency(order, routes)
    dist = {n: inf for n in order}
    dist[source] = 0
    settled, steps = [], []
    first = {}
    while len(settled) < len(order):
        cands = [n for n in order if n not in settled and dist[n] < inf]
        if not cands:
            break
        u = min(cands, key=lambda n: (dist[n], order.index(n)))
        settled.append(u)
        notes = []
        for v, w in adj[u]:
            if v in settled:
                continue
            new = dist[u] + w
            if new < dist[v]:
                notes.append(f"{v}: {fmt(dist[v])} → {new} via {u}")
                dist[v], first[v] = new, u
            elif new == dist[v]:
                notes.append(f"{v}: {new} via {u} = tie (keep via {first[v]}, record alternative)")
            else:
                notes.append(f"{v}: {new} via {u} ≥ {fmt(dist[v])}, no change")
        steps.append({"Round": len(settled), "Settle": f"{u} ({fmt(dist[u])})",
                      "Relaxations": "; ".join(notes) if notes else "no unsettled neighbours",
                      **{n: ("✔ " if n in settled else "") + fmt(dist[n]) for n in order}})
    return dist, steps


def dijkstra(order: list, routes: pd.DataFrame, source: str) -> dict:
    G = nx_graph(order, routes)
    pred, d = nx.dijkstra_predecessor_and_distance(G, source, weight="weight")
    paths = nx.single_source_dijkstra_path(G, source, weight="weight")
    dist = {n: d.get(n, inf) for n in order}
    preds = {}
    for n in order:
        p = list(pred.get(n, []))
        if n in paths and len(paths[n]) > 1:                 # NetworkX's chosen predecessor first
            main = paths[n][-2]
            p = [main] + [x for x in p if x != main]
        preds[n] = p
    trace_dist, steps = _teaching_trace(order, routes, source)
    return {"source": source, "dist": dist, "preds": preds, "paths": paths, "steps": steps,
            "unreachable": [n for n in order if dist[n] == inf],
            "trace_matches_networkx": all(trace_dist[n] == dist[n] for n in order),
            "engine": "networkx.dijkstra_predecessor_and_distance"}


def primary_path(preds: dict, source: str, node: str) -> list:
    path, n = [node], node
    while n != source:
        if not preds[n]:
            return []
        n = preds[n][0]
        path.append(n)
    return path[::-1]


def all_shortest_paths(preds: dict, source: str, node: str, limit: int = 6) -> list:
    """Every tied shortest path, enumerated from NetworkX's predecessor lists (equivalent to
    `nx.all_shortest_paths`, which is used in the tests as a cross-check). Primary path first."""
    if node == source:
        return [[source]]
    out = []
    for p in preds[node]:
        for head in all_shortest_paths(preds, source, p, limit):
            out.append(head + [node])
            if len(out) >= limit:
                return out
    return out


def coverage_table(order: list, routes: pd.DataFrame, times: pd.DataFrame, res: dict, promise: int,
                   names: dict, areas: dict) -> pd.DataFrame:
    """One row per destination. Service rule: PASS when shortest time <= promise (time exactly equal to
    the target passes). Unreachable is its own status and counts as failing."""
    src, dist, preds = res["source"], res["dist"], res["preds"]
    direct = {frozenset((a, b)): int(m) for a, b, m in times[["From", "To", "Minutes"]].itertuples(index=False, name=None)}
    rows = []
    for n in order:
        if n == src:
            continue
        t = dist[n]
        if t == inf:
            rows.append({"Code": n, "Branch": names.get(n, n), "Area": areas.get(n, ""), "Minutes": None,
                         "Shortest time": "Unreachable", "Path": "no route under X", "Tied paths": "",
                         "Legs": None, "Margin vs target (min)": None, "Status": "UNREACHABLE",
                         "Direct Google drive (min)": direct.get(frozenset((src, n)))})
            continue
        paths = all_shortest_paths(preds, src, n)
        rows.append({"Code": n, "Branch": names.get(n, n), "Area": areas.get(n, ""), "Minutes": int(t),
                     "Shortest time": f"{int(t)} min", "Path": " → ".join(paths[0]),
                     "Tied paths": " | ".join(" → ".join(p) for p in paths[1:]),
                     "Legs": len(paths[0]) - 1, "Margin vs target (min)": int(promise - t),
                     "Status": "PASS" if t <= promise else "FAIL",
                     "Direct Google drive (min)": direct.get(frozenset((src, n)))})
    df = pd.DataFrame(rows)
    # v2.1: type-safe sort key. Minutes is object dtype (ints + None for unreachable); calling fillna() on it
    # triggers pandas 2.2's "Downcasting object dtype arrays on .fillna" FutureWarning. Convert to float first.
    key = pd.to_numeric(df["Minutes"], errors="coerce").astype("float64").fillna(inf)
    order = sorted(range(len(df)), key=lambda i: (key.iloc[i], df["Code"].iloc[i]))
    return df.iloc[order].reset_index(drop=True)


def tree_distances(order: list, edges: list, source: str) -> dict:
    """Shortest times using only the given edge list (e.g. the Kruskal tree), via NetworkX."""
    r = pd.DataFrame(edges, columns=["From", "To", "Minutes"]) if edges else pd.DataFrame(columns=["From", "To", "Minutes"])
    res = dijkstra(order, r, source)
    return {n: (res["dist"][n], primary_path(res["preds"], source, n)) for n in order}
