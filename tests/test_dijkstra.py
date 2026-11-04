"""Dijkstra baselines, ties, unreachable handling and NetworkX agreement."""
from math import inf

import networkx as nx

import reference_algorithms as ref

from src import network_core as nc
from src import routing_core as rc
from src.data_loader import eligible_routes


def run(ds, x, src):
    r = eligible_routes(ds.times, x)
    return r, rc.dijkstra(ds.order, r, src)


def cov(ds, r, res, promise):
    return rc.coverage_table(ds.order, r, ds.times, res, promise, {c: c for c in ds.order},
                             ds.branches.set_index("Code")["Area"].to_dict())


def test_baseline_times_and_paths(ds):
    r, res = run(ds, 38, "HUB")
    assert {n: res["dist"][n] for n in ds.order if n != "HUB"} == {"KAR": 13, "QUS": 16, "UMS": 23, "SHJ": 24,
                                                                   "JAF": 47, "AJM": 51}
    p = rc.all_shortest_paths(res["preds"], "HUB", "JAF")
    assert p == [["HUB", "KAR", "JAF"], ["HUB", "UMS", "JAF"]]          # the tie is displayed
    assert rc.all_shortest_paths(res["preds"], "HUB", "AJM") == [["HUB", "SHJ", "AJM"]]
    assert res["trace_matches_networkx"] and res["engine"].startswith("networkx")
    G = nc.nx_graph(ds.order, r)
    assert sorted(map(tuple, nx.all_shortest_paths(G, "HUB", "JAF", weight="weight"))) == sorted(map(tuple, p))


def test_promise_20_two_pass_four_fail(ds):
    r, res = run(ds, 38, "HUB")
    t = cov(ds, r, res, 20)
    assert sorted(t[t.Status == "PASS"].Code) == ["KAR", "QUS"]
    assert sorted(t[t.Status == "FAIL"].Code) == ["AJM", "JAF", "SHJ", "UMS"]


def test_promise_23_scenario(ds):
    r, res = run(ds, 38, "HUB")
    t = cov(ds, r, res, 23)
    assert sorted(t[t.Status == "PASS"].Code) == ["KAR", "QUS", "UMS"]


def test_mst_vs_shortest(ds):
    r, res = run(ds, 38, "HUB")
    k = nc.kruskal(ds.order, r)
    tree = rc.tree_distances(ds.order, k["accepted"], "HUB")
    assert tree["UMS"][0] == 33 and tree["JAF"][0] == 57
    assert res["dist"]["UMS"] == 23 and res["dist"]["JAF"] == 47


def test_every_source_every_x_matches_networkx(ds):
    for x in (10, 20, 27, 28, 33, 38, 39, 50, 66):
        r = eligible_routes(ds.times, x)
        G = nc.nx_graph(ds.order, r)
        for s in ds.order:
            res = rc.dijkstra(ds.order, r, s)
            d = nx.single_source_dijkstra_path_length(G, s)
            assert all(res["dist"][n] == d.get(n, inf) for n in ds.order), (x, s)
            assert res["dist"] == ref.dijkstra(ds.order, r, s), (x, s)
            assert res["trace_matches_networkx"], (x, s)


def test_unreachable_is_explicit_x27(ds):
    r, res = run(ds, 27, "HUB")
    assert res["dist"]["AJM"] == inf and res["unreachable"] == ["AJM"]
    t = cov(ds, r, res, 20)
    row = t[t.Code == "AJM"].iloc[0]
    assert row.Status == "UNREACHABLE" and row["Shortest time"] == "Unreachable"
    assert len(t) == 6                                       # isolated node kept in the denominator


def test_empty_graph_all_unreachable(ds):
    r, res = run(ds, 10, "JAF")
    t = cov(ds, r, res, 20)
    assert (t.Status == "UNREACHABLE").all() and len(t) == 6


def test_jaf_as_source(ds):
    r, res = run(ds, 38, "JAF")
    assert res["dist"]["UMS"] == 24 and res["dist"]["KAR"] == 34 and res["dist"]["HUB"] == 47


def test_exact_boundary_passes_at_23(ds):
    """Service rule is time <= promise: UMS at exactly 23 min passes at 23, fails at 22."""
    r, res = run(ds, 38, "HUB")
    assert res["dist"]["UMS"] == 23
    t23, t22 = cov(ds, r, res, 23), cov(ds, r, res, 22)
    assert t23.set_index("Code").loc["UMS", "Status"] == "PASS"
    assert t22.set_index("Code").loc["UMS", "Status"] == "FAIL"
    assert (t23.Status == "PASS").sum() == 3
