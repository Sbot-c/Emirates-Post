"""v2.4: Python-generated trace plots / tables for Our working are real PNGs drawn from the baseline run."""
import struct

import pytest

from src import context as cx
from src import investment_core as ic
from src import trace_visuals as tv


@pytest.fixture(scope="module")
def run(ds):
    B = cx.BASELINE
    sc = cx.build(ds, B["threshold_x"], B["selected_hub"], B["service_promise"], B["budget_aed"])
    pool = ic.build_pool(ds.upgrades, sc.dijkstra["dist"], sc.hub, sc.promise)
    inv = ic.solve(pool["rows"], sc.budget, sc.hub, sc.dijkstra["dist"], sc.promise)
    hc, hb = ic.trace_units(inv["cost"], sc.budget)
    K, hbest, hchosen, hpath = ic.knapsack(hc, inv["benefit"], hb)
    return sc, inv, (hc, hb, K, hbest, hchosen, hpath)


def _dims(png: bytes):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", png[16:24])


def test_all_four_figures_are_png_images(run):
    sc, inv, _ = run
    for png in (tv.dfs_figure(sc), tv.kruskal_figure(sc), tv.dijkstra_figure(sc), tv.knapsack_figure(inv, sc.budget)):
        w, h = _dims(png)
        assert w > 1200 and h > 500 and len(png) > 20_000


def test_summary_table_reports_the_baseline_results(run):
    sc, inv, trace = run
    t = tv.summary_table(sc, inv, trace)
    assert t["Algorithm"].tolist() == ["DFS (Kushal)", "Kruskal (Shashaank)", "Dijkstra (Siddal)", "0/1 knapsack (Joan)"]
    blob = " | ".join(t["Headline result"])
    for s in ("HUB → KAR → QUS → UMS → JAF → SHJ → AJM", "124 min vs 334 min", "2 of 6 within target", "JAF + SHJ + AJM",
              "765,000", "720,000"):
        assert s in blob, s
    assert "NO" not in " ".join(t["Check performed"])          # every integrity check passed


def test_answer_key_tables_match_the_panel_tables(run):
    sc, inv, trace = run
    tabs = tv.trace_tables(sc, inv, trace)
    assert len(tabs["dfs"]) == len(sc.dfs["steps"]) and len(tabs["kruskal"]) == 13
    assert len(tabs["dijkstra"]) == 7 and len(tabs["knapsack"]) == len(inv["names"])
    assert tabs["kruskal"]["Running total (min)"].iloc[-1] == sc.kruskal["total"] == 124


def test_layout_matches_the_dashboard_schematic(run):
    from src import ui_components as ui          # needs streamlit + plotly (installed in the real environment)
    assert tv.LAYOUT_PX == ui.LAYOUT_PX
