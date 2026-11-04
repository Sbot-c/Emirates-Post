"""
network_core.py — graph construction, DFS connectivity (Data Lead: Kushal) and the Kruskal / Prim
minimum network (Network Analyst: Shashaank). No Streamlit in here.

Academic compliance (brief, Technical appendix p. 15: "Use the networkx library for the graph work.
The one algorithm you should write yourself is the knapsack table"):
  * NetworkX is the AUTHORITATIVE engine for every graph result shown in the app — connectivity,
    connected components, the DFS visit order, the Kruskal minimum spanning tree/forest, the Prim
    cross-check, articulation points, bridges and connectivity numbers.
  * The step tables (DFS stack trace, Kruskal accept/reject table) are teaching views DERIVED FROM
    NetworkX's own outputs: the DFS trace from `nx.dfs_labeled_edges`, the Kruskal table by replaying
    NetworkX's edge order with NetworkX's `UnionFind`, and every replay is checked against
    `nx.minimum_spanning_edges(algorithm="kruskal")` (field `networkx_verified`).
  * The original hand-written versions are kept in tests/reference_algorithms.py as an independent
    pure-Python cross-check.

Graph construction: all seven vertices are added first (in matrix order HUB, KAR, QUS, UMS, JAF, SHJ,
AJM), so an isolated branch is never dropped; edges are then added in the eligible-route order.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd


# ---------------------------------------------------------------- graph
def nx_graph(order: list, routes: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    G.add_nodes_from(order)
    G.add_weighted_edges_from((a, b, int(m)) for a, b, m in routes[["From", "To", "Minutes"]].itertuples(index=False, name=None))
    return G


def adjacency(order: list, routes: pd.DataFrame) -> dict:
    """Neighbour lists in matrix order (display only — used for the paper-style neighbour checks)."""
    G = nx_graph(order, routes)
    return {n: [(v, G[n][v]["weight"]) for v in sorted(G[n], key=order.index)] for n in order}


def _matrix_sort(order):
    return lambda nbrs: sorted(nbrs, key=order.index)


# ---------------------------------------------------------------- DFS (Data Lead)
def dfs(order: list, routes: pd.DataFrame, start: str) -> dict:
    """DFS from `start` with NetworkX (`dfs_labeled_edges`, neighbours in matrix order).
    The paper-style stack trace is rebuilt from NetworkX's forward/reverse events."""
    G = nx_graph(order, routes)
    srt = _matrix_sort(order)
    visited, stack, steps, tree = set(), [], [], []

    def checks(u, target=None):
        notes = []
        for n in srt(G[u]):
            if n == target:
                notes.append(f"{n}: not visited → go")
                break
            notes.append(f"{n} ✗")
        return notes

    for u, v, kind in nx.dfs_labeled_edges(G, source=start, sort_neighbors=srt):
        if kind == "forward" and u == v:                       # the start vertex
            visited.add(u)
            stack.append(u)
            steps.append({"Step": 1, "At": "—", "Neighbour checks": "start", "Action": f"Visit {u}",
                          "Stack after": u, "Visited": 1})
        elif kind == "forward":                                # tree edge u → v
            visited.add(v)
            stack.append(v)
            tree.append((u, v))
            steps.append({"Step": len(steps) + 1, "At": u, "Neighbour checks": " · ".join(checks(u, v)),
                          "Action": f"Visit {v}", "Stack after": " > ".join(stack), "Visited": len(visited)})
        elif kind == "reverse":                                # finished v (u == v for the start)
            done = v
            notes = checks(done) or ["no routes"]
            if notes != ["no routes"]:
                notes.append("nothing new")
            stack.pop()
            steps.append({"Step": len(steps) + 1, "At": done, "Neighbour checks": " · ".join(notes),
                          "Action": f"Backtrack (pop {done})", "Stack after": " > ".join(stack) or "(empty)",
                          "Visited": len(visited)})
    visit_order = list(nx.dfs_preorder_nodes(G, source=start, sort_neighbors=srt))
    assert visit_order == [start] + [b for _, b in tree]          # trace is consistent with NetworkX
    comp = nx.node_connected_component(G, start)
    return {"visit_order": visit_order, "tree": tree, "steps": steps, "visited": len(comp),
            "total": len(order), "connected": nx.is_connected(G) if len(order) else False,
            "unreachable": [n for n in order if n not in comp], "engine": "networkx.dfs_labeled_edges"}


def components(order: list, routes: pd.DataFrame) -> list:
    """Connected components (NetworkX), each in matrix order; the hub's group first."""
    G = nx_graph(order, routes)
    comps = [sorted(c, key=order.index) for c in nx.connected_components(G)]
    return sorted(comps, key=lambda c: order.index(c[0]))


def robustness(order: list, routes: pd.DataFrame) -> dict:
    """Articulation points, bridges and connectivity from NetworkX; confirmed by removing each
    branch / route in turn and re-testing `nx.is_connected` (no inference from degree)."""
    G = nx_graph(order, routes)
    if not nx.is_connected(G):
        return {"applicable": False, "articulation_points": [], "bridges": [], "single_route_branches": []}
    cut_nodes = sorted(nx.articulation_points(G), key=order.index)
    bridges = [(a, b, G[a][b]["weight"]) for a, b in nx.bridges(G)]
    removal_nodes = [n for n in order if not nx.is_connected(G.subgraph([x for x in order if x != n]))]
    removal_edges = []
    for a, b in list(G.edges()):
        H = G.copy()
        H.remove_edge(a, b)
        if not nx.is_connected(H):
            removal_edges.append(frozenset((a, b)))
    return {"applicable": True, "articulation_points": cut_nodes, "bridges": bridges,
            "single_route_branches": [n for n in order if G.degree(n) == 1],
            "edge_connectivity": nx.edge_connectivity(G), "node_connectivity": nx.node_connectivity(G),
            "removal_check_agrees": (removal_nodes == cut_nodes and
                                     set(removal_edges) == {frozenset((a, b)) for a, b, _ in bridges})}


def threshold_table(order: list, times: pd.DataFrame, lo: int = 10, hi: int = 66) -> pd.DataFrame:
    """Routes and connectivity for every X (Data Lead's threshold sweep, recomputed with NetworkX)."""
    from .data_loader import eligible_routes
    rows = []
    for x in range(lo, hi + 1):
        r = eligible_routes(times, x)
        G = nx_graph(order, r)
        hub_group = nx.node_connected_component(G, order[0])
        rows.append({"X (min)": x, "Routes": len(r), "In 10–14 band": 10 <= len(r) <= 14,
                     "Connected": nx.is_connected(G),
                     "Cut off": ", ".join(n for n in order if n not in hub_group) or "—"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- Kruskal (Network Analyst)
def kruskal(order: list, routes: pd.DataFrame) -> dict:
    """Kruskal's minimum spanning tree (forest if disconnected) computed by NetworkX.

    Authoritative result: `nx.minimum_spanning_edges(G, algorithm="kruskal")`.
    Teaching table: the same edges in NetworkX's own order (stable sort by minutes over the graph's
    edge order, i.e. branch matrix order — at X = 38 the 24-minute tie HUB–SHJ comes before UMS–JAF),
    replayed with NetworkX's `UnionFind` to show ACCEPT / REJECT, running total and groups.
    A route is rejected only when both ends are already in the same group (it would close a loop)."""
    G = nx_graph(order, routes)
    nx_edges = [(u, v, d["weight"]) for u, v, d in nx.minimum_spanning_edges(G, algorithm="kruskal", data=True)]
    uf = nx.utils.UnionFind(order)
    forest = nx.Graph()
    forest.add_nodes_from(order)
    accepted, steps, running = [], [], 0
    for k, (a, b, d) in enumerate(sorted(G.edges(data=True), key=lambda e: e[2]["weight"]), 1):
        m = d["weight"]
        if uf[a] != uf[b]:
            uf.union(a, b)
            forest.add_edge(a, b)
            accepted.append((a, b, m))
            running += m
            decision, reason = "ACCEPT", f"joins two separate groups ({a} | {b})"
        else:
            decision = "REJECT"
            reason = f"loop — {a} and {b} already joined via {' – '.join(nx.shortest_path(forest, a, b))}"
        groups = sorted((sorted(g, key=order.index) for g in uf.to_sets()), key=lambda g: order.index(g[0]))
        steps.append({"Order": k, "Route": f"{a}–{b}", "Minutes": m, "Decision": decision,
                      "Running total (min)": running, "Groups after": len(groups),
                      "Component groups": " ".join("{" + ",".join(g) + "}" for g in groups), "Reason": reason})
    n_groups = nx.number_connected_components(G)
    return {"accepted": accepted, "steps": steps, "total": running, "groups": n_groups,
            "is_tree": n_groups == 1, "rejected": [s for s in steps if s["Decision"] == "REJECT"],
            "networkx_verified": accepted == nx_edges and running == sum(w for *_, w in nx_edges),
            "engine": "networkx.minimum_spanning_edges(algorithm='kruskal')"}


def prim(order: list, routes: pd.DataFrame) -> dict:
    """Prim's cross-check with NetworkX (starts from the first vertex, HUB; returns a forest if
    the network is disconnected)."""
    G = nx_graph(order, routes)
    edges = [(u, v, d["weight"]) for u, v, d in nx.minimum_spanning_edges(G, algorithm="prim", data=True)]
    return {"edges": edges, "total": sum(w for *_, w in edges), "spans_all": nx.is_connected(G)}


def networkx_mst_total(order: list, routes: pd.DataFrame) -> int:
    G = nx_graph(order, routes)
    return int(sum(d["weight"] for _, _, d in nx.minimum_spanning_tree(G, algorithm="kruskal").edges(data=True)))


def summarise(routes: pd.DataFrame, k: dict) -> dict:
    total_all = int(routes["Minutes"].sum()) if len(routes) else 0
    saving = total_all - k["total"]
    return {"n_all": len(routes), "n_min": len(k["accepted"]), "total_all": total_all, "total_min": k["total"],
            "saving_min": saving, "saving_pct": (saving / total_all * 100) if total_all else 0.0}
