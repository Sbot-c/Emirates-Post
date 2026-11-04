"""Notebook baseline references in `Our working` (v2.3).

Shows the 11 ORIGINAL figures and the reference tables from the team notebook
notebooks/EmiratesPost_Graphs_and_Working.ipynb, extracted unchanged at build time by tools/extract_notebook_figures.py
(assets/notebook_diagrams/*.png + manifest.json, assets/notebook_tables/*.csv). The app never parses the notebook.
Paths resolve from this module's location, so the app works from any working directory and fully offline.

Boundaries
  * The figures are original notebook-generated Matplotlib figures — not handwritten paper traces. They never change
    an evidence status; the pending hand-trace requirement in each panel stays exactly as it is.
  * They are STATIC baseline references (X = 38, HUB, 20 min, AED 450,000). They do not recalculate with the controls;
    when the live controls differ from the baseline, each block says so.
  * Cross-checks compare the notebook's recorded baseline values with this dashboard's fixed baseline run computed now;
    the status (AGREES / MISMATCH) is computed, never typed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from . import ui_components as ui

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "notebook_diagrams"
MANIFEST = ASSETS / "manifest.json"
NOTEBOOK_NAME = "EmiratesPost_Graphs_and_Working.ipynb"
BASELINE_LABEL = "Notebook baseline reference — X = 38, HUB, 20 min, AED 450,000"
OWNERS = {"data": "Data and threshold — Kushal — Data Lead", "dfs": "DFS connectivity — Kushal — Data Lead",
          "kruskal": "Kruskal minimum network — Shashaank — Network Analyst",
          "dijkstra": "Dijkstra service coverage — Siddal — Routing Analyst",
          "knapsack": "0/1 knapsack / investment — Joan — Investment Analyst"}
PANEL_TABLES = {"data": [], "dfs": [("dfs_trace", "DFS action / stack / visited trace")],
                "kruskal": [("kruskal_decisions", "Kruskal ACCEPT / REJECT decisions with reasons")],
                "dijkstra": [("dijkstra_trace", "Dijkstra settle / relaxation trace (long cells truncated in the "
                                                "notebook's own output)"),
                             ("dijkstra_coverage", "Shortest paths, distances and 20-min status"),
                             ("target_sensitivity_grid", "Within-target grid for targets 15–51 min")],
                "knapsack": [("upgrade_options", "Four priced upgrade options (AED 10,000 trace units)"),
                             ("knapsack_traceback", "DP traceback"), ("greedy_steps", "Greedy selection steps")]}
# reading notes for wording inside the original images (the images themselves are never edited)
FIGURE_NOTES = {
    "Figure 1.3": "The figure labels the hub by area (“Umm Ramool / Al Garhoud”); the app calls it the selected model hub — "
                  "Al Ramool / Umm Ramool. Layout is schematic, not to scale.",
    "Figure 4.2": "Pass/fail is also readable from the printed minutes against the dashed 20-min line (not colour alone); the "
                  "legend in the original image overlaps the AJM bar.",
    "Figure 4.4": "“Cheapest to run” in the title refers to the summed route-minutes (edge-time) proxy, not a cash cost.",
    "Figure 5.2": "“Earns” / “annual gross benefit” in the figure means the modelled annual gross-benefit proxy — not profit. "
                  "The notebook steps the budget in AED 10,000 increments, so its shaded gaps are coarser than the "
                  "dashboard's exact-AED ranges on the Investment tab.",
}
# notebook summary row -> panel whose cross-check shows it
SUMMARY_ROWS = {"data": ["Routes under X = 38", "All-routes total (min)"],
                "dfs": ["DFS visit order", "Connected"],
                "kruskal": ["Kruskal routes", "Kruskal total (min)", "All-routes total (min)"],
                "dijkstra": ["Dijkstra KAR/QUS/UMS/SHJ/JAF/AJM", "Within 20-min target"],
                "knapsack": ["Knapsack K[4][45]", "DP choice", "Greedy choice", "DP − greedy (AED/yr)"]}


# ---------------------------------------------------------------- data access (no Streamlit calls)
def load_manifest(path: Path = MANIFEST) -> dict:
    """Manifest dict, or {'error': ...} if it is missing or unreadable (the app keeps running)."""
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
        m.setdefault("figures", [])
        m.setdefault("tables", {})
        return m
    except FileNotFoundError:
        return {"error": f"manifest not found ({path.name})", "figures": [], "tables": {}}
    except (OSError, ValueError) as e:
        return {"error": f"manifest unreadable ({e})", "figures": [], "tables": {}}


def check_asset(fig: dict, root: Path = ROOT) -> tuple[bool, str, Path]:
    """(ok, message, path): exists, non-empty, matches the recorded SHA-256 and decodes as an image."""
    p = root / fig["descriptive_filename"]
    if not p.exists():
        return False, f"{fig['descriptive_filename']} is missing", p
    raw = p.read_bytes()
    if not raw:
        return False, f"{fig['descriptive_filename']} is empty", p
    if fig.get("sha256") and hashlib.sha256(raw).hexdigest() != fig["sha256"]:
        return False, f"{fig['descriptive_filename']} differs from the notebook original (checksum mismatch)", p
    try:
        with Image.open(p) as im:
            im.verify()
    except Exception as e:  # noqa: BLE001 — any decode failure becomes a warning, never a crash
        return False, f"{fig['descriptive_filename']} cannot be decoded ({type(e).__name__})", p
    return True, "ok", p


def for_panel(key: str, manifest: dict | None = None) -> list[dict]:
    m = manifest if manifest is not None else load_manifest()
    seen, out = set(), []
    for f in m.get("figures", []):
        if f.get("panel_key") == key and f["descriptive_filename"] not in seen:
            seen.add(f["descriptive_filename"])
            out.append(f)
    return out


def load_table(name: str, root: Path = ROOT) -> pd.DataFrame | None:
    p = root / "assets" / "notebook_tables" / f"{name}.csv"
    if not p.exists():
        return None
    with p.open(encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return pd.DataFrame(rows[1:], columns=rows[0]) if rows else None


def notebook_summary(root: Path = ROOT) -> dict:
    """The notebook's own computed baseline values (column 'Notebook' of its section-6 summary, cell 26)."""
    t = load_table("notebook_vs_dashboard_summary", root)
    return {} if t is None else dict(zip(t["Item"], t["Notebook"]))


def live_baseline_values(sc, inv, trace) -> dict:
    """The same quantities from THIS dashboard's fixed baseline run (computed now, v2.3 code), as display strings."""
    d = sc.dijkstra["dist"]
    hc, hb, K, hbest, hchosen, _ = trace
    n = inv["names"]
    taken = [n[i] for i, fits, _ in inv["greedy"]["steps"] if fits]          # greedy in selection order
    return {"Routes under X = 38": str(len(sc.routes)), "All-routes total (min)": str(sc.summary["total_all"]),
            "DFS visit order": " → ".join(sc.dfs["visit_order"]), "Connected": str(bool(sc.dfs["connected"])),
            "Kruskal routes": str(len(sc.kruskal["accepted"])), "Kruskal total (min)": str(sc.kruskal["total"]),
            "Dijkstra KAR/QUS/UMS/SHJ/JAF/AJM": "/".join(str(int(d[c])) for c in ["KAR", "QUS", "UMS", "SHJ", "JAF", "AJM"]),
            "Within 20-min target": ", ".join(c for c in sc.ds.order if c != sc.hub and d[c] <= sc.promise),
            "Knapsack K[4][45]": str(hbest // 1000), "DP choice": ", ".join(n[i] for i in inv["dp"]["picks"]),
            "Greedy choice": ", ".join(taken),
            "DP − greedy (AED/yr)": str(inv["dp"]["benefit"] - inv["greedy"]["benefit"])}


def cross_check(rows: list[str], notebook: dict, live: dict) -> list[dict]:
    out = []
    for r in rows:
        nbv, lv = notebook.get(r), live.get(r)
        status = "NOT IN NOTEBOOK" if nbv is None else ("AGREES" if str(nbv).strip() == str(lv).strip() else "MISMATCH")
        out.append({"Quantity": r, "Notebook (baseline, as recorded)": nbv if nbv is not None else "—",
                    "This dashboard — fixed baseline run, computed now": lv, "Status": status})
    return out


# ---------------------------------------------------------------- rendering
def _figure(fig: dict):
    ok, msg, p = check_asset(fig)
    src = f"{NOTEBOOK_NAME}, cell {fig['source_cell_index']}, output {fig['output_index']}"
    if not ok:
        st.warning(f"{fig['figure_number']} could not be shown: {msg}. Source: {src}. The rest of the panel is unaffected.")
        return
    # natural size, never upscaled; wider images shrink to the container with their aspect ratio preserved
    st.image(str(p), width=int(fig["width_px"]),
             caption=f"{fig['figure_number']} · Original notebook-generated figure · {src} · {BASELINE_LABEL}")
    extra = f" <i>Reading note:</i> {FIGURE_NOTES[fig['figure_number']]}" if fig["figure_number"] in FIGURE_NOTES else ""
    st.markdown(f"<div class='note'><b>Shows:</b> {fig['algorithm_topic']}. Original {fig['width_px']}×{fig['height_px']} px, "
                f"unchanged; use the image's expand icon to view full size.{extra}</div>", unsafe_allow_html=True)


def render_panel(key: str, manifest: dict, live_values: dict, live_scenario: str | None):
    """Notebook baseline block for one Our working section. `live_scenario` is None when the live controls are at the
    baseline; otherwise a short description of the live scenario shown on the analytical tabs."""
    figs = for_panel(key, manifest)
    with st.container(border=True):
        st.markdown(f"<div class='nbref'><span class='nbtag'>{BASELINE_LABEL}</span> "
                    f"<span class='note'>{OWNERS[key]} · original notebook-generated figures and typed computer "
                    "output from the team notebook — supplementary reference, not handwritten traces; they do not change "
                    "any evidence status.</span></div>", unsafe_allow_html=True)
        if live_scenario:
            st.info(f"The live controls are set to {live_scenario}. These notebook figures stay fixed at the baseline; the "
                    "live result for that scenario is on the Network, Service coverage and Investment tabs.", icon="📌")
        if manifest.get("error"):
            st.warning(f"Notebook figures unavailable — {manifest['error']}. The calculated results are unaffected.")
        elif not figs:
            st.markdown(f"<div class='note'>No figure for this section in {NOTEBOOK_NAME}.</div>", unsafe_allow_html=True)
        for f in figs:
            _figure(f)
        rows = cross_check(SUMMARY_ROWS[key], notebook_summary(), live_values)
        ui.html_table(pd.DataFrame(rows), row_class=lambda r: "ok" if r["Status"] == "AGREES" else "bad", wrap=True)
        st.markdown("<span class='note'>Status is computed by comparing the notebook's recorded baseline value with this "
                    "dashboard's fixed baseline run (same inputs) — a code-to-code check, not hand-trace evidence.</span>",
                    unsafe_allow_html=True)
        for name, title in PANEL_TABLES[key]:
            t = load_table(name)
            info = manifest.get("tables", {}).get(name, {})
            with st.expander(f"Notebook reference table — {title} (cell {info.get('cell', '?')}, typed computer output)"):
                if t is None:
                    st.warning(f"Reference table {name}.csv is missing.")
                else:
                    ui.html_table(t, wrap=True)


def render_overall(manifest: dict, live_values: dict):
    """Overall notebook-vs-dashboard cross-check (replaces the notebook's static 'Dashboard (v2.1)' column)."""
    nb = notebook_summary()
    rows = cross_check(list(nb.keys()) or [r for v in SUMMARY_ROWS.values() for r in v], nb, live_values)
    n_ok = sum(r["Status"] == "AGREES" for r in rows)
    st.markdown(f"<div class='owner'>🔗 Overall integration and business recommendation — <b>Sparsh</b> · Integration & "
                f"Business Lead</div>", unsafe_allow_html=True)
    st.markdown(f"**Notebook vs dashboard — all baseline values ({n_ok} of {len(rows)} agree).** The notebook's section 6 "
                "compared itself with a static copy of the v2.1 dashboard; here the dashboard side is recomputed by the "
                "current code on every run.")
    ui.html_table(pd.DataFrame(rows), row_class=lambda r: "ok" if r["Status"] == "AGREES" else "bad", wrap=True)
