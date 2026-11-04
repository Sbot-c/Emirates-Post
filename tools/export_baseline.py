"""Compute the baseline figures used on the recommendation slide (so the slide is generated, not typed)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import investment_core as ic, rationale as ra, routing_core as rc  # noqa: E402
from src.context import BASELINE, build  # noqa: E402
from src.data_loader import load_dataset  # noqa: E402

ds = load_dataset()
sc = build(ds, *BASELINE.values())
pool = ic.build_pool(ds.upgrades, sc.dijkstra["dist"], sc.hub, sc.promise)
a = ic.solve(pool["rows"], sc.budget, sc.hub, sc.dijkstra["dist"], sc.promise, ds.order)
b = ic.solve(pool["rows"], sc.budget + 50_000, sc.hub, sc.dijkstra["dist"], sc.promise, ds.order)


def _plan(p):
    """v2.1: replaces the v2 'coverage' count (which wrongly counted local fulfilment as within the target); v2.2 adds
    the selected-intervention counts."""
    return {"direct": p["direct"], "alt_mode": p["alt_mode"], "local": p["local"], "outside": p["outside"],
            "outside_codes": p["outside_codes"], "with_disposition": p["with_disposition"], "n_dest": p["n_dest"],
            "by_branch": {r["branch_code"]: r["modelled_service_disposition"] for r in p["rows"]},
            # v2.2: selected interventions, counted from the algorithm's picks (independent of primary disposition)
            "local_selected": p["local_selected"], "alt_selected": p["alt_selected"],
            "alt_qualifying_selected": p["alt_qualifying_selected"], "selected_on_direct": p["selected_on_direct"]}
tree = rc.tree_distances(ds.order, sc.kruskal["accepted"], sc.hub)
n = a["names"]
out = {
    "x": sc.x, "hub": sc.hub, "promise": sc.promise, "budget": sc.budget,
    "routes": len(sc.routes), "all_total": sc.summary["total_all"], "mst_total": sc.summary["total_min"],
    "mst_n": sc.summary["n_min"], "saving_pct": round(sc.summary["saving_pct"], 1),
    "pass_before": a["plan_before"]["direct"],
    "dp": {"picks": [n[i] for i in a["dp"]["picks"]], "spent": a["dp"]["spent"], "left": a["dp"]["left"],
           "benefit": a["dp"]["benefit"], "service_plan": _plan(a["dp"]["plan"])},
    "greedy": {"picks": [n[i] for i in a["greedy"]["picks"]], "benefit": a["greedy"]["benefit"], "spent": a["greedy"]["spent"],
               "service_plan": _plan(a["greedy"]["plan"])},
    "plus50": {"budget": sc.budget + 50_000, "picks": [n[i] for i in b["dp"]["picks"]], "spent": b["dp"]["spent"],
               "left": b["dp"]["left"], "benefit": b["dp"]["benefit"], "service_plan": _plan(b["dp"]["plan"]),
               "added": [b["names"][i] for i in b["dp"]["picks"] if i not in a["dp"]["picks"]],
               "added_cost": sum(b["cost"][i] for i in b["dp"]["picks"] if i not in a["dp"]["picks"])},
    "ums_now": int(sc.dijkstra["dist"]["UMS"]),
    "tree_vs_fast": {k: [int(tree[k][0]), int(sc.dijkstra["dist"][k])] for k in ("UMS", "JAF")},
}
_r = ra.promise_rationale(ds)
out["rationale"] = {"holds": _r["holds"], "pass_at_promise": _r["base"]["n_pass"],
                    "candidates_cost": _r["base"]["cost_total"], "next_promise": _r["alt"]["promise"],
                    "newly_passing": _r["newly_passing"], "next_candidates": _r["alt"]["candidates"],
                    "next_candidates_cost": _r["alt"]["cost_total"], "next_all_fit": _r["alt"]["all_fit"],
                    "next_dp": _r["alt"]["dp"], "next_greedy": _r["alt"]["greedy"], "next_gap": _r["alt"]["gap"],
                    "plateau": list(_r["plateau"]), "slide_note": ra.slide_note(_r)}
print(json.dumps(out, indent=1))
