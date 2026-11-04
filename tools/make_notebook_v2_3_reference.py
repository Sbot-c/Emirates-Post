"""Build notebooks/EmiratesPost_Graphs_and_Working_v2_3_reference.ipynb — the v2.3 DERIVATIVE of the team notebook.

The original notebooks/EmiratesPost_Graphs_and_Working.ipynb is never modified. The derivative:
  * inserts a note cell at the top (v2.3 derivative; computer-generated reference working that accompanies — does not
    replace — the members' separate handwritten traces; figures unchanged);
  * keeps every original cell, roles table, algorithm explanation, table and figure; only the stale "dashboard (v2.1)"
    wording in cells 0 and 25 is refreshed;
  * replaces section 6's static `expected` dictionary (typed v2.1 values with ✓ written by comparison against that typed
    copy) by code that recomputes the dashboard side from the project's own v2.3 code (../src) and computes MATCH /
    MISMATCH — nothing is typed by hand;
  * adds one Markdown + one code cell describing the four service-disposition categories, computed by the dashboard's
    classifier (dashboard-computed, labelled as such).

Only the changed/new code cells are executed (the whole derivative is run with nbclient in the notebooks/ folder so that
../data and ../src resolve, and only those cells' outputs are kept). Every other cell keeps its ORIGINAL outputs, so all
11 figures stay byte-identical to the original; the script verifies that and that the re-run produced the same text
outputs as the original for every unchanged cell.

Needs the optional notebook tooling (see requirements-notebook.txt):
    pip install -r requirements-notebook.txt
    python tools/make_notebook_v2_3_reference.py
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"
SRC = NB_DIR / "EmiratesPost_Graphs_and_Working.ipynb"
DST = NB_DIR / "EmiratesPost_Graphs_and_Working_v2_3_reference.ipynb"

NOTE = """> **v2.3 reference derivative — computer-generated working, not handwritten traces.**
> Copy of `EmiratesPost_Graphs_and_Working.ipynb` (kept unchanged beside this file). Changes in the Network Audit v2.3
> refinement: the stale "dashboard (v2.1)" wording is refreshed; section 6 now recomputes the dashboard side from the
> project's own v2.3 code and *computes* MATCH / MISMATCH instead of comparing with a typed copy; a short service-
> disposition cell is added. All other cells, tables and the 11 figures are the original outputs (figures byte-identical,
> verified by `tools/make_notebook_v2_3_reference.py`). These outputs accompany each member's separate handwritten trace;
> they do not replace it."""

CELL0_OLD = "computed from the same data as the dashboard (v2.1):"
CELL0_NEW = "computed from the same data as the dashboard (input data unchanged since v2.1; compared with the v2.3 build in section 6):"

CELL25 = """## 6 · Summary: notebook vs dashboard (baseline X 38, HUB, 20 min, AED 450,000)
Each *Notebook* value below is computed in this notebook. The *Dashboard v2.3* column is **recomputed at run time from the
project's own code** (`../src`: the same functions the Streamlit app calls for its fixed baseline evidence run), and the
*Status* column is calculated by comparing the two — `MATCH` or `MISMATCH`, never typed. (The original notebook compared
itself with a typed copy of the v2.1 dashboard values.)"""

CELL26 = '''# v2.3: the dashboard side is recomputed from the project's own code — nothing below is typed by hand
import sys
sys.path.insert(0, str(Path("..").resolve()))
from src.data_loader import load_dataset
from src.working_tab import baseline_run
from src.notebook_diagrams import live_baseline_values

_ds = load_dataset()
_sc, _pool, _inv, _trace = baseline_run(_ds)
dashboard = live_baseline_values(_sc, _inv, _trace)          # X 38 · HUB · 20 min · AED 450,000 (v2.3 code)

got = {"Routes under X = 38": len(ROUTES), "DFS visit order": " → ".join(dfs_order), "Connected": nx.is_connected(G),
       "Kruskal total (min)": mst_total, "All-routes total (min)": all_total, "Kruskal routes": len(accepted),
       "Dijkstra KAR/QUS/UMS/SHJ/JAF/AJM": "/".join(str(int(dist[c])) for c in ["KAR", "QUS", "UMS", "SHJ", "JAF", "AJM"]),
       "Within 20-min target": ", ".join(COV.loc[COV.Status == "WITHIN TARGET", "Code"]),
       "Knapsack K[4][45]": K[n][W], "DP choice": ", ".join(dp_picks), "Greedy choice": ", ".join(g_picks),
       "DP − greedy (AED/yr)": dp_b - ben_of(g_picks)}
status = {k: "MATCH" if str(got[k]) == str(dashboard.get(k)) else "MISMATCH" for k in got}
print(f"{sum(s == 'MATCH' for s in status.values())} of {len(status)} values match the v2.3 dashboard code")
pd.DataFrame({"Notebook": {k: str(v) for k, v in got.items()},
              "Dashboard v2.3 (computed now)": {k: dashboard.get(k, "—") for k in got}, "Status": status})'''

CELL_DISP_MD = """### Service disposition (dashboard v2.3 classifier, baseline DP and greedy portfolios)
The dashboard separates four service dispositions: **DIRECT HUB TRANSFER WITHIN TARGET** (road-network shortest time
≤ target), **ALTERNATIVE MODE WITHIN TARGET (ASSUMPTION)** (a selected option whose stated mode time is ≤ target, e.g.
the UMS motorbike at an assumed 18 min from HUB), **LOCAL FULFILMENT UPGRADE** (a selected mini-hub — the hub-to-branch
road time is unchanged; it is not a zero-minute journey and not direct-transfer compliance) and
**OUTSIDE SELECTED SERVICE PLAN**. The table below is computed by the dashboard's classifier (`src/investment_core.py`), not by this notebook."""

CELL_DISP = '''from src import investment_core as ic
_rows = []
for _label, _plan in [("DP", _inv["dp"]["plan"]), ("Greedy", _inv["greedy"]["plan"])]:
    for _r in _plan["rows"]:
        _rows.append({"Portfolio": _label, "Branch": _r["branch_code"], "Shortest hub time (min)": _r["shortest_hub_time_min"],
                      "Selected upgrade": _r["selected_intervention"], "Primary disposition": _r["modelled_service_disposition"]})
    print(f"{_label}: {ic.plan_summary(_plan)}")
pd.DataFrame(_rows)'''


def _png_hashes(nb: dict) -> list[str]:
    out = []
    for c in nb["cells"]:
        for o in c.get("outputs", []) or []:
            d = (o.get("data") or {}).get("image/png")
            if d:
                out.append(hashlib.sha256(base64.b64decode(d if isinstance(d, str) else "".join(d))).hexdigest())
    return out


def _text_outputs(cell: dict) -> list[str]:
    out = []
    for o in cell.get("outputs", []) or []:
        if o.get("text"):
            out.append("".join(o["text"]))
        tp = (o.get("data") or {}).get("text/plain")
        if tp and "image/png" not in o.get("data", {}):
            out.append("".join(tp))
    return out


def build() -> dict:
    orig = json.loads(SRC.read_text(encoding="utf-8"))
    nb = copy.deepcopy(orig)
    cells = nb["cells"]
    c0 = "".join(cells[0]["source"])
    assert CELL0_OLD in c0, "cell 0 text changed — update CELL0_OLD"
    cells[0]["source"] = c0.replace(CELL0_OLD, CELL0_NEW).splitlines(keepends=True)
    assert "v2.1" in "".join(cells[25]["source"]) and "expected = {" in "".join(cells[26]["source"])
    cells[25]["source"] = CELL25.splitlines(keepends=True)
    cells[26]["source"] = CELL26.splitlines(keepends=True)
    cells[26]["outputs"] = []
    cells.insert(27, {"cell_type": "markdown", "id": "v23-disposition-md", "metadata": {},
                      "source": CELL_DISP_MD.splitlines(keepends=True)})
    cells.insert(28, {"cell_type": "code", "id": "v23-disposition", "metadata": {}, "execution_count": None,
                      "outputs": [], "source": CELL_DISP.splitlines(keepends=True)})
    cells.insert(0, {"cell_type": "markdown", "id": "v23-derivative-note", "metadata": {},
                     "source": NOTE.splitlines(keepends=True)})
    # execute a copy in notebooks/ (so ../data and ../src resolve); keep outputs only for the changed/new code cells
    run = nbformat.reads(json.dumps(nb), as_version=4)
    NotebookClient(run, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(NB_DIR)}}).execute()
    ran = run.cells
    changed = {27, 29}                                       # new indices of section-6 code and the disposition cell
    for i in changed:
        cells[i]["outputs"] = [json.loads(json.dumps(o)) for o in ran[i]["outputs"]]
        cells[i]["execution_count"] = ran[i]["execution_count"]
    # checks: figures byte-identical; unchanged cells' text outputs reproduced by the fresh run
    assert _png_hashes(nb) == _png_hashes(orig), "derivative figures differ from the original"
    diffs = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and i not in changed
             and _text_outputs(c) != _text_outputs(ran[i])]
    match_line = "".join(ran[27]["outputs"][0].get("text", "")) if ran[27]["outputs"] else ""
    return {"nb": nb, "rerun_text_diffs": diffs, "summary": match_line.strip()}


if __name__ == "__main__":
    r = build()
    DST.write_text(json.dumps(r["nb"], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {DST.relative_to(ROOT)} ({len(r['nb']['cells'])} cells); 11 figures byte-identical to the original")
    print("section 6:", r["summary"])
    print("unchanged code cells whose fresh re-run text differs from the original output:", r["rerun_text_diffs"] or "none")
    sys.exit(0)
