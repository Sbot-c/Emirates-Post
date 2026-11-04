"""v2.3: the team notebook's 11 original figures and its reference tables in `Our working` — extracted unchanged,
placed in the right section, labelled as static baseline references, offline, robust to missing/corrupt files and to
the working directory, without touching evidence status. Also: the v2.3 derivative notebook and Joan's v2.2 derivative."""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from src import notebook_diagrams as nd

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks" / "EmiratesPost_Graphs_and_Working.ipynb"
NB_SHA = "92cbc029236daf370aa872c76c336c02aa6f3078796a982bbb380924484c96de"        # as supplied by the user
NB23 = ROOT / "notebooks" / "EmiratesPost_Graphs_and_Working_v2_3_reference.ipynb"
JOAN = ROOT / "evidence" / "reference" / "Knapsack_Trace_Joan.ipynb"
JOAN_SHA = "486d6d7c8f9dfdf05962ed22fa3f8b6736af78a6754d74b0fd8f3262a1368e0e"
JOAN22 = ROOT / "evidence" / "reference" / "Knapsack_Trace_Joan_v2_2_reference.ipynb"

EXPECTED = {  # figure -> (cell, output, size, panel, file stem)
    "Figure 1.1": (4, 0, (757, 649), "data", "figure_1_1_drive_time_matrix"),
    "Figure 1.2": (5, 0, (979, 451), "data", "figure_1_2_threshold_connectivity_sensitivity"),
    "Figure 1.3": (6, 0, (1059, 694), "data", "figure_1_3_route_network_x38"),
    "Figure 2.1": (9, 0, (1089, 713), "dfs", "figure_2_1_dfs_traversal_tree"),
    "Figure 3.1": (12, 0, (1059, 694), "kruskal", "figure_3_1_kruskal_mst_vs_rejected"),
    "Figure 4.1": (16, 0, (1089, 713), "dijkstra", "figure_4_1_dijkstra_shortest_path_tree"),
    "Figure 4.2": (17, 0, (979, 429), "dijkstra", "figure_4_2_travel_time_vs_20min_target"),
    "Figure 4.4": (19, 0, (979, 429), "dijkstra", "figure_4_4_all_routes_vs_mst_shortest_paths"),
    "Figure 5.1a": (22, 0, (1529, 330), "knapsack", "figure_5_1a_knapsack_dp_grid_0_22"),
    "Figure 5.1b": (22, 1, (1529, 330), "knapsack", "figure_5_1b_knapsack_dp_grid_23_45"),
    "Figure 5.2": (24, 0, (1089, 462), "knapsack", "figure_5_2_dp_vs_greedy_budget_sweep"),
}


def _embedded(nb_path):
    """{(cell, output): sha256} for every embedded image (outputs and attachments)."""
    nb = json.loads(nb_path.read_text())
    out = {}
    for ci, c in enumerate(nb["cells"]):
        for name, att in (c.get("attachments") or {}).items():
            for m, d in att.items():
                if m.startswith("image/"):
                    out[(ci, f"attachment:{name}")] = hashlib.sha256(base64.b64decode(d)).hexdigest()
        for oi, o in enumerate(c.get("outputs") or []):
            for m, d in (o.get("data") or {}).items():
                if m.startswith("image/"):
                    out[(ci, oi)] = hashlib.sha256(base64.b64decode(d if isinstance(d, str) else "".join(d))).hexdigest()
    return out


def _images(at):
    out = []

    def walk(n):
        if getattr(n, "type", None) == "image":
            out.extend(i.caption for i in n.proto.imgs)
        ch = getattr(n, "children", None)
        if isinstance(ch, dict):
            for c in ch.values():
                walk(c)
    walk(at._tree)
    return out


# ---------------------------------------------------------------- source and extraction
def test_original_notebooks_unchanged():
    assert hashlib.sha256(NB.read_bytes()).hexdigest() == NB_SHA
    assert hashlib.sha256(JOAN.read_bytes()).hexdigest() == JOAN_SHA
    assert len(json.loads(NB.read_text())["cells"]) == 27


def test_all_11_figures_discovered_extracted_and_byte_identical():
    emb = _embedded(NB)
    assert len(emb) == 11 and not any(isinstance(k[1], str) for k in emb)      # 11 PNG outputs, no attachments
    m = nd.load_manifest()
    assert "error" not in m and len(m["figures"]) == 11
    figs = {f["figure_number"]: f for f in m["figures"]}
    assert set(figs) == set(EXPECTED)
    for name, (cell, out, size, panel, stem) in EXPECTED.items():
        f = figs[name]
        assert (f["source_cell_index"], f["output_index"], f["panel_key"]) == (cell, out, panel)
        assert f["descriptive_filename"] == f"assets/notebook_diagrams/{stem}.png"
        assert f["sha256"] == emb[(cell, out)]                                       # byte-verified vs the notebook
        ok, msg, p = nd.check_asset(f)
        assert ok, msg
        assert hashlib.sha256(p.read_bytes()).hexdigest() == emb[(cell, out)]
        with Image.open(p) as im:
            assert im.size == size == (f["width_px"], f["height_px"]) and im.format == "PNG"
        assert "not a handwritten paper trace" in f["classification"]


def test_extraction_is_idempotent_and_check_mode_passes():
    before = {p.name: p.read_bytes() for p in (ROOT / "assets" / "notebook_diagrams").iterdir()}
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "extract_notebook_figures.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "11 figures and 9 tables verified" in r.stdout, r.stdout + r.stderr
    after = {p.name: p.read_bytes() for p in (ROOT / "assets" / "notebook_diagrams").iterdir()}
    assert before == after and len([n for n in after if n.endswith(".png")]) == 11


def test_inventory_csv_columns_and_rows():
    import csv
    rows = list(csv.DictReader((ROOT / "audit" / "notebook_diagram_inventory.csv").open()))
    assert len(rows) == 11
    for col in ("diagram_id", "descriptive_filename", "original_notebook_filename", "source_cell_index", "output_index",
                "mime_type", "width_px", "height_px", "sha256", "algorithm_topic", "assigned_dashboard_panel",
                "classification", "extraction_status", "display_test_status"):
        assert col in rows[0], col
    assert {r["mime_type"] for r in rows} == {"image/png"}


def test_knapsack_grid_halves_cover_all_46_capacities():
    src = "".join(json.loads(NB.read_text())["cells"][22]["source"])
    halves = [tuple(map(int, t)) for t in re.findall(r"\((\d+), (\d+)\)", src.split("for lo, hi in")[1].split(":")[0])]
    assert halves == [(0, 23), (23, 46)]                                  # range(lo, hi): w = 0–22 and 23–45
    cols = [w for lo, hi in halves for w in range(lo, hi)]
    assert cols == list(range(46))
    m = {f["figure_number"]: f for f in nd.load_manifest()["figures"]}
    assert "0–22" in m["Figure 5.1a"]["algorithm_topic"] and "23–45" in m["Figure 5.1b"]["algorithm_topic"]


def test_reference_tables_extracted():
    m = nd.load_manifest()
    assert set(m["tables"]) == {"dfs_trace", "kruskal_decisions", "dijkstra_trace", "dijkstra_coverage",
                                "target_sensitivity_grid", "upgrade_options", "knapsack_traceback", "greedy_steps",
                                "notebook_vs_dashboard_summary"}
    k = nd.load_table("kruskal_decisions")
    assert len(k) == 13 and (k["Decision"] == "ACCEPT").sum() == 6 and (k["Decision"] == "REJECT").sum() == 7
    assert len(nd.load_table("dfs_trace")) >= 7 and len(nd.load_table("dijkstra_coverage")) == 6


def test_notebook_values_cross_check_against_dashboard(ds):
    from src.working_tab import baseline_run
    sc, pool, inv, trace = baseline_run(ds)
    nb = nd.notebook_summary()
    rows = nd.cross_check(list(nb), nb, nd.live_baseline_values(sc, inv, trace))
    assert len(rows) == 12 and all(r["Status"] == "AGREES" for r in rows), rows
    # the status is computed: a changed value is reported, never forced
    bad = nd.cross_check(["Kruskal total (min)"], {"Kruskal total (min)": "125"}, nd.live_baseline_values(sc, inv, trace))
    assert bad[0]["Status"] == "MISMATCH"
    # Kruskal accepted set in the notebook table == dashboard
    k = nd.load_table("kruskal_decisions")
    nb_acc = {frozenset(r.split("–")) for r in k.loc[k["Decision"] == "ACCEPT", "Route"]}
    assert nb_acc == {frozenset((a, b)) for a, b, _ in sc.kruskal["accepted"]}


def test_paths_resolve_independently_of_cwd(tmp_path):
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        m = nd.load_manifest()
        assert len(m["figures"]) == 11 and all(nd.check_asset(f)[0] for f in m["figures"])
        assert nd.load_table("greedy_steps") is not None
    finally:
        os.chdir(cwd)


def test_missing_or_corrupt_asset_is_reported_not_raised(tmp_path):
    f = dict(nd.load_manifest()["figures"][0])
    (tmp_path / "assets" / "notebook_diagrams").mkdir(parents=True)
    ok, msg, _ = nd.check_asset(f, root=tmp_path)
    assert not ok and "missing" in msg
    (tmp_path / f["descriptive_filename"]).write_bytes(b"")
    assert "empty" in nd.check_asset(f, root=tmp_path)[1]
    (tmp_path / f["descriptive_filename"]).write_bytes(b"not a png at all")
    assert not nd.check_asset(f, root=tmp_path)[0]
    assert "error" in nd.load_manifest(tmp_path / "nope.json")


# ---------------------------------------------------------------- derivative notebooks
def test_v23_derivative_preserves_figures_and_refreshes_comparison():
    o, d = json.loads(NB.read_text()), json.loads(NB23.read_text())
    assert list(_embedded(NB).values()) == list(_embedded(NB23).values())   # same 11 figures, byte-identical, same order
    md = "\n".join("".join(c["source"]) for c in d["cells"] if c["cell_type"] == "markdown")
    code = "\n".join("".join(c["source"]) for c in d["cells"] if c["cell_type"] == "code")
    assert "expected = {" not in code and "from the v2.1 build" not in md and "the dashboard (v2.1)" not in md
    assert "not handwritten traces" in md and "do not replace it" in md
    assert "Kushal (Data Lead)" in md and "Joan (Investment Analyst)" in md               # original roles retained
    for name in ("DIRECT HUB TRANSFER WITHIN TARGET", "ALTERNATIVE MODE WITHIN TARGET (ASSUMPTION)",
                 "LOCAL FULFILMENT UPGRADE", "OUTSIDE SELECTED SERVICE PLAN"):
        assert name in md
    sec6 = next(c for c in d["cells"] if c["cell_type"] == "code" and "live_baseline_values" in "".join(c["source"]))
    out = "".join("".join(x.get("text", "")) + "".join((x.get("data") or {}).get("text/plain", "")) for x in sec6["outputs"])
    assert "12 of 12 values match the v2.3 dashboard code" in out and "MISMATCH" not in out
    assert out.count("MATCH") >= 12
    # every original code cell other than section 6 is unchanged (source and outputs)
    oc = [c for i, c in enumerate(o["cells"]) if c["cell_type"] == "code" and i != 26]
    dc = [c for c in d["cells"] if c["cell_type"] == "code" and c.get("id") not in ("v23-disposition",)
          and "live_baseline_values" not in "".join(c["source"])]
    assert [json.dumps(c, sort_keys=True) for c in oc] == [json.dumps(c, sort_keys=True) for c in dc]


def test_joan_v22_derivative_still_valid():
    o, dv = json.loads(JOAN.read_text()), json.loads(JOAN22.read_text())
    assert list(_embedded(JOAN).values()) == list(_embedded(JOAN22).values())
    md = "\n".join("".join(c["source"]) for c in dv["cells"] if c["cell_type"] == "markdown")
    assert "After funding, 5 of 6 offices meet" not in md and "only two meet the direct-transfer target" in md


# ---------------------------------------------------------------- in the app
@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    return at


def test_app_shows_all_11_figures_in_the_right_sections(app):
    assert [t.label for t in app.tabs] == ["Network", "Service coverage", "Investment", "Our working"]
    caps = _images(app)
    nb_caps = [c for c in caps if "Original notebook-generated figure" in c]
    assert [c.split(" · ")[0] for c in nb_caps] == list(EXPECTED)                 # order = section order, no duplicates
    assert all("Notebook baseline reference — X = 38, HUB, 20 min, AED 450,000" in c for c in nb_caps)
    assert not any("handwritten" in c.lower() for c in nb_caps)
    md = [m.value for m in app.markdown]
    heads = {k: next(i for i, v in enumerate(md) if v.startswith(h)) for k, h in
             [("data", "---\n#### Data and threshold X"), ("dfs", "---\n#### 1 ·"), ("kruskal", "---\n#### 2 ·"),
              ("dijkstra", "---\n#### 3 ·"), ("knapsack", "---\n#### 4 ·"), ("overall", "---\n#### Notebook vs dashboard")]}
    tags = [i for i, v in enumerate(md) if "<span class='nbtag'>" in v]
    assert len(tags) == 5
    order = ["data", "dfs", "kruskal", "dijkstra", "knapsack", "overall"]
    for k, nxt, t in zip(order, order[1:], tags):                   # one notebook block inside each section
        assert heads[k] < t < heads[nxt]
    owners = "\n".join(md)
    for s in ("Data and threshold — Kushal — Data Lead", "DFS connectivity — Kushal — Data Lead",
              "Kruskal minimum network — Shashaank — Network Analyst", "Dijkstra service coverage — Siddal — Routing Analyst",
              "0/1 knapsack / investment — Joan — Investment Analyst"):
        assert s in owners, s
    assert "Overall integration and business recommendation — <b>Sparsh</b> · Integration & Business Lead" in owners
    assert "12 of 12 agree" in owners


def test_figures_do_not_change_evidence_status(app):
    t = "\n".join([m.value for m in app.markdown] + [c.value for c in app.caption])
    assert t.count("PENDING authentic handwritten scan") == 4
    assert "0 of 4 traces matched against a transcription" in t
    assert t.count("HANDWRITTEN TRACE REQUIRED") == 4


def test_baseline_label_and_note_when_live_controls_change():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not [i for i in at.info if "stay fixed at the baseline" in i.value]       # no note at baseline
    at.selectbox(key="selected_hub").set_value("JAF").run()          # v2.4: the target now follows the hub (JAF -> 35)
    at.slider(key="service_promise").set_value(23).run()             # a manual value is kept
    notes = [i.value for i in at.info if "stay fixed at the baseline" in i.value]
    assert len(notes) == 5 and all("hub JAF, target 23 min" in n for n in notes)
    assert all("Notebook baseline reference" in c for c in _images(at) if "notebook-generated" in c)


def test_app_with_missing_or_corrupt_figure_warns_instead_of_crashing(tmp_path):
    """Separate interpreter + project copy launched from another working directory, so the copy's own assets are used."""
    proj = tmp_path / "proj"
    shutil.copytree(ROOT, proj, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "screenshots"))
    (proj / "assets" / "notebook_diagrams" / "figure_3_1_kruskal_mst_vs_rejected.png").write_bytes(b"corrupt")
    (proj / "assets" / "notebook_diagrams" / "figure_5_2_dp_vs_greedy_budget_sweep.png").unlink()
    code = ("import json; from streamlit.testing.v1 import AppTest; "
            f"at = AppTest.from_file({str(proj / 'app.py')!r}, default_timeout=120).run(); "
            "print(json.dumps({'exc': [str(e.value) for e in at.exception], 'warn': [w.value for w in at.warning]}))")
    r = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=300)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["exc"] == []
    assert any("Figure 3.1" in w and "checksum" in w for w in out["warn"])
    assert any("Figure 5.2" in w and "missing" in w for w in out["warn"])
