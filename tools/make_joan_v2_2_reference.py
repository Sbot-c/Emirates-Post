"""Create the v2.2 corrected DERIVATIVE of the typed reference notebook evidence/reference/Knapsack_Trace_Joan.ipynb.

The original notebook is never modified. Only typed Markdown narrative is corrected (the outdated "5 of 6 offices meet the
20-minute promise" claim and related wording); every code cell, every output and all three embedded figures are copied
unchanged, and the script verifies that byte-for-byte. A note cell is inserted at the top. The notebook is a typed,
computer-generated reference — it is not a handwritten trace.

Usage (from the project root):  python tools/make_joan_v2_2_reference.py
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "evidence" / "reference" / "Knapsack_Trace_Joan.ipynb"
DST = ROOT / "evidence" / "reference" / "Knapsack_Trace_Joan_v2_2_reference.ipynb"

# (original cell index, old text, new text) — exact substring replacements in Markdown cells only
EDITS = [
    (0, "which upgrades should Emirates Post fund so the offices that miss the 20-minute promise from the Al Ramool hub are "
        "fixed, and the yearly benefit is as large as possible?",
        "which upgrades should Emirates Post fund for the offices outside the proposed 20-minute internal hub-to-branch "
        "transfer target from the Al Ramool hub, so that the modelled annual gross-benefit proxy is as large as possible?"),
    (0, "| 0 | Dijkstra from the hub: which offices fail the 20-minute promise (same as Tab 2) |",
        "| 0 | Dijkstra from the hub: which offices are outside the 20-minute internal transfer target (same as Tab 2) |"),
    (2, "## Step 0: Which offices fail the promise? (Dijkstra, as in Tab 2)",
        "## Step 0: Which offices are outside the 20-minute internal transfer target? (Dijkstra, as in Tab 2)"),
    (4, "Four offices fail: **UMS (23), SHJ (24), JAF (47), AJM (51)**.",
        "Four offices are outside the target: **UMS (23), SHJ (24), JAF (47), AJM (51)**."),
    (5, "Benefits are AED recovered per year.",
        "Benefits are a modelled annual gross-benefit proxy (estimated gross fee/revenue opportunity per year) — not net "
        "profit, cash flow or ROI."),
    (25, "Spend **AED 411,960**, left **AED 38,040**, benefit **AED 765,000 a year**. After funding, 5 of 6 offices meet "
         "the 20-minute promise.",
         "First-year cost **AED 411,960**, left **AED 38,040**, modelled annual gross-benefit proxy **AED 765,000 a year**. "
         "Following the DP recommendation, two branches meet the proposed 20-minute target through direct hub transfer, "
         "three receive local-fulfilment upgrades, and Umm Suqeim remains outside the selected plan. Five of six "
         "destinations have a modelled service disposition, but only two meet the direct-transfer target."),
    (25, "- **Greedy:** UMS + JAF + SHJ, AED 720,000 a year. **Greedy loses AED 45,000 a year.**",
         "- **Greedy:** UMS + JAF + SHJ, first-year cost AED 344,340, AED 720,000 a year. **Greedy's gross-benefit proxy is "
         "AED 45,000 a year lower** under the supplied assumptions (not a profit figure)."),
    (25, "(budget AED 450,000, promise 20 min; expander \"Knapsack grid in AED 10,000 units\")",
         "(budget AED 450,000, target 20 min; expander \"Knapsack DP grid and traceback (AED 10,000 trace scale) · "
         "cross-checks\")"),
]

NOTE = ("> **v2.2 corrected derivative — typed reference, not a handwritten trace.** Copy of "
        "`Knapsack_Trace_Joan.ipynb` (kept unchanged alongside this file) with the typed Markdown narrative corrected in "
        "the Network Audit v2.2 refinement: the outdated claim that \"5 of 6 offices meet the 20-minute promise\" is "
        "replaced by the direct-transfer / local-fulfilment / outside-plan breakdown, and \"promise\" is worded as the "
        "proposed 20-minute internal hub-to-branch transfer target. All code cells, outputs and the three embedded "
        "figures are unchanged (verified byte-for-byte by `tools/make_joan_v2_2_reference.py`). The figures' own titles "
        "(e.g. \"yearly benefit\") are part of the original images and were not edited.")


def build() -> dict:
    orig = json.loads(SRC.read_text(encoding="utf-8"))
    nb = copy.deepcopy(orig)
    for idx, old, new in EDITS:
        cell = nb["cells"][idx]
        assert cell["cell_type"] == "markdown", (idx, cell["cell_type"])
        src = "".join(cell["source"])
        if old not in src:
            raise SystemExit(f"cell {idx}: expected text not found: {old[:60]!r}")
        src = src.replace(old, new)
        cell["source"] = src.splitlines(keepends=True)
    note = {"cell_type": "markdown", "metadata": {"id": "v2_2_derivative_note"}, "source": NOTE.splitlines(keepends=True)}
    nb["cells"].insert(0, note)
    # verification: every code cell (source + outputs) identical to the original, in the same order
    oc = [c for c in orig["cells"] if c["cell_type"] == "code"]
    nc = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(oc) == len(nc) and all(json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True) for a, b in zip(oc, nc))
    return nb


if __name__ == "__main__":
    nb = build()
    DST.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {DST.relative_to(ROOT)} — {len(nb['cells'])} cells; code cells/outputs identical to the original")
    sys.exit(0)
