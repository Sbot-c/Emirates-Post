"""DFS connectivity and Kruskal / Prim baselines and edge cases (NetworkX engine, cross-checked)."""
import networkx as nx
import pytest

import reference_algorithms as ref
from src import network_core as nc
from src.data_loader import eligible_routes


def routes(ds, x):
    return eligible_routes(ds.times, x)


def test_dfs_baseline(ds):
    r = routes(ds, 38)
    d = nc.dfs(ds.order, r, "HUB")
    assert d["engine"] == "networkx.dfs_labeled_edges"
    assert d["visit_order"] == ["HUB", "KAR", "QUS", "UMS", "JAF", "SHJ", "AJM"]
    assert d["tree"] == [("HUB", "KAR"), ("KAR", "QUS"), ("QUS", "UMS"), ("UMS", "JAF"), ("QUS", "SHJ"), ("SHJ", "AJM")]
    assert d["visited"] == 7 and d["connected"]
    assert len(d["steps"]) == 14
    assert [n for n, _ in nc.adjacency(ds.order, r)["HUB"]] == ["KAR", "QUS", "UMS", "SHJ"]


def test_dfs_trace_matches_data_lead_sheet(ds):
    """The rebuilt stack trace equals the Data Lead's DFS solution sheet, row by row."""
    steps = nc.dfs(ds.order, routes(ds, 38), "HUB")["steps"]
    assert [s["Action"] for s in steps] == [
        "Visit HUB", "Visit KAR", "Visit QUS", "Visit UMS", "Visit JAF", "Backtrack (pop JAF)", "Backtrack (pop UMS)",
        "Visit SHJ", "Visit AJM", "Backtrack (pop AJM)", "Backtrack (pop SHJ)", "Backtrack (pop QUS)",
        "Backtrack (pop KAR)", "Backtrack (pop HUB)"]
    assert [s["Visited"] for s in steps] == [1, 2, 3, 4, 5, 5, 5, 6, 7, 7, 7, 7, 7, 7]


def test_threshold_band(ds):
    t = nc.threshold_table(ds.order, ds.times)
    band = t[t["In 10–14 band"] & t["Connected"]]["X (min)"].tolist()
    assert band == list(range(31, 39))
    assert max(band) == 38                            # largest valid X (not the smallest)
    assert int(t.loc[t["X (min)"] == 39, "Routes"].iloc[0]) == 15


def test_x33_and_x35(ds):
    assert len(routes(ds, 33)) == 11 and nc.dfs(ds.order, routes(ds, 33), "HUB")["connected"]
    r = routes(ds, 35)
    assert len(r) == 12 and [n for n, _ in nc.adjacency(ds.order, r)["AJM"]] == ["SHJ"]


def test_x27_disconnects_ajman_x28_reconnects(ds):
    r = routes(ds, 27)
    d = nc.dfs(ds.order, r, "HUB")
    assert not d["connected"] and d["unreachable"] == ["AJM"]
    k = nc.kruskal(ds.order, r)
    assert not k["is_tree"] and k["groups"] == 2 and len(k["accepted"]) == 5 and k["networkx_verified"]
    assert nc.dfs(ds.order, routes(ds, 28), "HUB")["connected"]


def test_empty_graph_x10(ds):
    r = routes(ds, 10)
    assert len(r) == 0
    d = nc.dfs(ds.order, r, "HUB")
    assert d["visited"] == 1 and len(d["unreachable"]) == 6
    k = nc.kruskal(ds.order, r)
    assert k["accepted"] == [] and k["groups"] == 7 and k["total"] == 0
    assert nc.summarise(r, k)["saving_pct"] == 0.0    # no division by zero
    assert len(nc.components(ds.order, r)) == 7
    assert nc.prim(ds.order, r)["total"] == 0


def test_graph_keeps_isolated_nodes(ds):
    G = nc.nx_graph(ds.order, routes(ds, 10))
    assert G.number_of_nodes() == 7 and G.number_of_edges() == 0 and not nx.is_connected(G)


def test_robustness_baseline(ds):
    rob = nc.robustness(ds.order, routes(ds, 38))
    assert rob["articulation_points"] == [] and rob["bridges"] == []
    assert rob["edge_connectivity"] == 2 and rob["node_connectivity"] == 2
    assert rob["removal_check_agrees"]


def test_robustness_detects_cut_vertex_at_x35(ds):
    rob = nc.robustness(ds.order, routes(ds, 35))       # AJM hangs on SHJ only
    assert "SHJ" in rob["articulation_points"] and rob["single_route_branches"] == ["AJM"]
    assert rob["removal_check_agrees"]


def test_kruskal_baseline(ds):
    r = routes(ds, 38)
    k = nc.kruskal(ds.order, r)
    assert k["accepted"] == [("HUB", "KAR", 13), ("HUB", "QUS", 16), ("KAR", "UMS", 20), ("HUB", "SHJ", 24),
                             ("UMS", "JAF", 24), ("SHJ", "AJM", 27)]
    assert k["total"] == 124 and k["is_tree"] and len(k["accepted"]) == len(ds.order) - 1
    assert [s["Route"] for s in k["rejected"]] == ["HUB–UMS", "KAR–QUS", "QUS–SHJ", "KAR–SHJ", "QUS–UMS", "KAR–JAF", "QUS–AJM"]
    s = nc.summarise(r, k)
    assert (s["total_all"], s["total_min"], s["saving_min"]) == (334, 124, 210)
    assert round(s["saving_pct"], 1) == 62.9
    assert nc.prim(ds.order, r)["total"] == 124 == nc.networkx_mst_total(ds.order, r)
    assert k["networkx_verified"]


def test_kruskal_tie_order_irrelevant(ds):
    """24-minute tie (HUB-SHJ / UMS-JAF): reversing the edge insertion order gives the same tree and total."""
    r = routes(ds, 38)
    a = nc.kruskal(ds.order, r)
    b = nc.kruskal(ds.order, r.iloc[::-1].reset_index(drop=True))
    assert {frozenset(e[:2]) for e in a["accepted"]} == {frozenset(e[:2]) for e in b["accepted"]}
    assert a["total"] == b["total"] == 124
    order = [s["Route"] for s in a["steps"]]
    assert order.index("HUB–SHJ") < order.index("UMS–JAF")        # documented display order


def test_kruskal_matches_networkx_and_reference_every_x(ds):
    for x in range(10, 67):
        r = routes(ds, x)
        k = nc.kruskal(ds.order, r)
        assert k["networkx_verified"], x
        assert k["total"] == nc.networkx_mst_total(ds.order, r) == ref.kruskal(ds.order, r)[1], x


def test_networkx_dfs_equals_independent_reference_every_x_and_source(ds):
    for x in range(10, 67):
        r = routes(ds, x)
        for s in ds.order:
            a, b = nc.dfs(ds.order, r, s), ref.dfs(ds.order, r, s)
            assert a["visit_order"] == b["visit_order"] and a["tree"] == b["tree"], (x, s)
            assert len(a["steps"]) == b["steps"] and a["unreachable"] == b["unreachable"], (x, s)


@pytest.mark.parametrize("x,n,has", [(38, 13, False), (39, 15, True)])
def test_strict_threshold_boundary(ds, x, n, has):
    r = routes(ds, x)
    pairs = {frozenset((a, b)) for a, b in zip(r.From, r.To)}
    assert len(r) == n
    assert (frozenset(("HUB", "JAF")) in pairs) is has and (frozenset(("HUB", "AJM")) in pairs) is has
    assert (r["Minutes"] < x).all()


def test_threshold_boundary_27_28_for_ajman(ds):
    assert "AJM" in nc.dfs(ds.order, routes(ds, 27), "HUB")["unreachable"]
    assert nc.dfs(ds.order, routes(ds, 28), "HUB")["connected"]
