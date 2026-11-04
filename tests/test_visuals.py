"""Knapsack heatmap and offline coordinate map: built from computed data, offline, with safe fallback."""
import plotly.graph_objects as go

from src import investment_core as ic
from src import ui_components as ui
from src.data_loader import load_dataset, read_sources
from src.working_tab import baseline_run


def test_heatmap_matrix_equals_dp_matrix(ds):
    sc, pool, inv, (hc, hb, K, hbest, hchosen, hpath) = baseline_run(ds)
    fig = ui.knapsack_heatmap(K, inv["names"], None, hc, hpath)
    hm = fig.data[0]
    assert isinstance(hm, go.Heatmap)
    assert [list(r) for r in hm.z] == [[v / 1000 for v in row] for row in K]       # AED '000, exact
    assert all(v % 1000 == 0 for row in K for v in row)                             # so the AED '000 label is exact
    assert len(hm.z) == 5 and len(hm.z[0]) == 46 and hb == 45
    assert hm.z[4][45] == 765


def test_traceback_cells_outlined_and_all_capacities_visible(ds):
    sc, pool, inv, (hc, hb, K, hbest, hchosen, hpath) = baseline_run(ds)
    fig = ui.knapsack_heatmap(K, inv["names"], None, hc, hpath)
    rects = {(round((s.x0 + s.x1) / 2), round((s.y0 + s.y1) / 2)) for s in fig.layout.shapes}
    assert rects == {(45, 4), (31, 3), (18, 2), (4, 1)}
    assert [(i, w, t) for i, w, t in hpath] == [(4, 45, True), (3, 31, True), (2, 18, True), (1, 4, False)]
    lo, hi = fig.layout.xaxis.range
    assert lo <= 0 and hi >= 45                      # capacities 0–45 (incl. 31–45) in the initial view, no scrolling


def test_traceback_summary_rows(ds):
    sc, pool, inv, (hc, hb, K, hbest, hchosen, hpath) = baseline_run(ds)
    rows = ic.traceback_rows(K, hpath, inv["names"], hc)
    assert [r["Decision"] for r in rows] == ["TAKE AJM", "TAKE SHJ", "TAKE JAF", "SKIP UMS"]
    assert [r["Capacity left (units)"] for r in rows] == [31, 18, 4, 4]


def test_coordinate_map_is_offline_scatter_only(ds):
    from src.context import build
    sc = build(ds, 38, "HUB", 20, 450_000)
    styles = {frozenset((a, b)): dict(colour="#000", width=2) for a, b in zip(sc.routes.From, sc.routes.To)}
    fig, note = ui.coordinate_map(ds, sc.routes, "t", styles, {}, [])
    assert note is None
    assert all(isinstance(t, go.Scatter) for t in fig.data)            # no Scattermapbox / Scattergeo / tiles
    js = fig.to_json()
    for token in ("mapbox", "scattergeo", "scattermap", "tile", "http://", "https://"):
        assert token not in js.lower()
    # node positions are the local km projection of the validated coordinates; hover keeps the original lat/lon
    hub = [t for t in fig.data if t.mode == "markers+text" and "HUB" in t.text[0]][0]
    pos, (lat0, lon0) = ui.project_km(ds.branches, ds.order)
    assert (hub.x[0], hub.y[0]) == pos["HUB"]
    assert "lat 25.23615, lon 55.35806" in hub.hovertemplate
    assert fig.layout.yaxis.scaleanchor == "x" and fig.layout.yaxis.scaleratio == 1


def test_coordinate_map_falls_back_on_invalid_coordinates():
    b, t, u = read_sources()
    b.loc[3, "Longitude"] = None
    ds_bad = load_dataset(frames=(b, t, u))
    assert ds_bad.valid                                                  # app keeps running
    fig, note = ui.coordinate_map(ds_bad, t.iloc[:0], "t", {}, {}, [])
    assert fig is None and "not drawn" in note
    b2 = read_sources()[0]
    b2.loc[1, ["Latitude", "Longitude"]] = b2.loc[0, ["Latitude", "Longitude"]].values
    ok, msg = ui.validate_coordinates(b2)
    assert not ok and "same coordinates" in msg


def test_no_web_font_or_external_url_in_css():
    assert "googleapis" not in ui.CSS and "@import" not in ui.CSS
