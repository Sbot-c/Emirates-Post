"""
rationale.py — why the model uses a 20-minute internal transfer target (Integration & Business Lead).

Everything here is computed from the current data and assumptions, never typed in:
  * at the chosen promise: how many branches pass, which priced options are candidates, what they cost
    in total, and whether the budget forces a choice (DP vs greedy compared, not assumed);
  * at the NEXT promise at which one more branch passes (23 min on the supplied data — UMS is exactly
    23 min and passes under `time <= promise`): the same figures.
If the data or the cost/benefit assumptions change, the sentences change with them; if the baseline
claim stops being true, the text says so instead of repeating it.

The 20-minute figure is the group's PROPOSED INTERNAL HUB-TO-BRANCH TRANSFER TARGET for this planning model. It is
not presented as an existing Emirates Post customer-facing service, and the rationale is a model-design /
sensitivity finding, not proof that 20 minutes is operationally optimal.

v2.1 correction: 20 minutes is NOT "the loosest whole-minute target" — with HUB times 13, 16, 23, 24, 47, 51 the same
two branches (KAR, QUS) pass for every whole-minute target from 16 to 22 (the "plateau", derived below by
`plateau()`); 20 is one selected planning target inside that range.
"""
from __future__ import annotations

from math import inf

from . import investment_core as ic
from . import routing_core as rc
from .context import BASELINE
from .data_loader import eligible_routes

TARGET_NAME = "proposed internal hub-to-branch transfer target"
CAVEAT = ("The 20-minute target is a useful decision scenario for this planning model — not a proven operational optimum "
          "and not an existing Emirates Post customer-facing service. It depends on the Google Maps estimates and the "
          "upgrade cost/benefit assumptions.")


def _scenario(order, upgrades, dist, hub, promise, budget):
    dests = [n for n in order if n != hub]
    passing = [n for n in dests if dist[n] <= promise]
    pool = ic.build_pool(upgrades, dist, hub, promise)
    rows = pool["rows"]
    out = {"promise": promise, "passing": passing, "n_pass": len(passing), "n_dest": len(dests),
           "candidates": [r["Code"] for r in rows], "no_option": pool["failing_no_option"],
           "cost_total": sum(r["Cost_AED"] for r in rows), "budget": budget}
    out["all_fit"] = out["cost_total"] <= budget
    if rows:
        s = ic.solve(rows, budget, hub, dist, promise, order)
        n = s["names"]
        out.update(dp=[n[i] for i in s["dp"]["picks"]], greedy=[n[i] for i in s["greedy"]["picks"]],
                   dp_benefit=s["dp"]["benefit"], greedy_benefit=s["greedy"]["benefit"],
                   dp_spent=s["dp"]["spent"], greedy_spent=s["greedy"]["spent"],
                   dp_plan=s["dp"]["plan"], greedy_plan=s["greedy"]["plan"])
    else:
        empty = ic.service_plan(order, hub, dist, promise, [], [])
        out.update(dp=[], greedy=[], dp_benefit=0, greedy_benefit=0, dp_spent=0, greedy_spent=0,
                   dp_plan=empty, greedy_plan=empty)
    out["gap"] = out["dp_benefit"] - out["greedy_benefit"]
    out["same_selection"] = sorted(out["dp"]) == sorted(out["greedy"])
    out["choice_forced"] = bool(rows) and not out["all_fit"]
    return out


def promise_rationale(ds, upgrades=None, x=None, hub=None, promise=None, budget=None) -> dict:
    """Rationale at the given settings (defaults = the baseline X 38 / HUB / 20 min / AED 450,000)."""
    upgrades = ds.upgrades if upgrades is None else upgrades
    x = BASELINE["threshold_x"] if x is None else x
    hub = BASELINE["selected_hub"] if hub is None else hub
    promise = BASELINE["service_promise"] if promise is None else promise
    budget = BASELINE["budget_aed"] if budget is None else budget
    routes = eligible_routes(ds.times, x)
    dist = rc.dijkstra(ds.order, routes, hub)["dist"]
    base = _scenario(ds.order, upgrades, dist, hub, promise, budget)
    failing_times = sorted(t for n, t in dist.items() if n != hub and promise < t < inf)
    nxt = int(failing_times[0]) if failing_times else None
    alt = _scenario(ds.order, upgrades, dist, hub, nxt, budget) if nxt is not None else None
    newly = [n for n in (alt["passing"] if alt else []) if n not in base["passing"]]
    holds = bool(alt) and base["choice_forced"] and base["gap"] > 0 and alt["all_fit"] and alt["same_selection"] \
        and alt["gap"] == 0
    return {"settings": {"x": x, "hub": hub, "promise": promise, "budget": budget}, "base": base, "alt": alt,
            "newly_passing": newly, "holds": holds, "dist": dist, "plateau": plateau(dist, hub, promise)}


def plateau(dist: dict, hub: str, promise: int):
    """Whole-minute targets that give exactly the same direct-transfer pass set as `promise` (inclusive rule):
    from the slowest passing time (or 0) up to one minute below the fastest failing reachable time."""
    times = [t for n, t in dist.items() if n != hub and t < inf]
    passing = [t for t in times if t <= promise]
    failing = [t for t in times if t > promise]
    lo = int(max(passing)) if passing else 0
    hi = int(min(failing)) - 1 if failing else None
    return lo, hi


def _aed(v):
    return f"AED {int(v):,}"


def _list(codes):
    return ", ".join(codes) if codes else "none"


def short_text(r: dict) -> str:
    """Compact rationale (HTML) — Service coverage card and the core of the longer texts."""
    b, a = r["base"], r["alt"]
    p = r["settings"]["promise"]
    lo, hi = r["plateau"]
    passing = _list(b["passing"])
    rng = (f"{lo}–{hi} min" if hi is not None else f"{lo} min or more")
    head = (f"At <b>{p} min</b> ({TARGET_NAME}), {b['n_pass']} of {b['n_dest']} branches meet the direct-transfer target "
            f"({passing}); the same {b['n_pass']} pass for every whole-minute target from <b>{rng}</b>, so {p} min is one "
            f"selected planning value in that range, not a unique one. {len(b['candidates'])} upgrade candidates "
            f"({_list(b['candidates'])}) cost {_aed(b['cost_total'])} against an {_aed(b['budget'])} budget")
    if b["choice_forced"]:
        head += (", so the budget forces a constrained choice (DP "
                 + (f"beats greedy by {_aed(b['gap'])}/yr in modelled gross benefit)." if b["gap"] > 0 else "and greedy agree)."))
    elif b["candidates"]:
        head += " — all fit, so the budget does not force a choice at this target."
    else:
        head += " — nothing to fund."
    if a is None:
        return head + " No slower reachable branch exists, so there is no looser target to compare."
    tail = (f" At <b>{a['promise']} min</b>, {_list(r['newly_passing'])} also passes (time ≤ target, inclusive); the "
            f"remaining {len(a['candidates'])} candidates ({_list(a['candidates'])}) cost {_aed(a['cost_total'])}")
    if a["all_fit"] and a["same_selection"] and a["gap"] == 0:
        tail += (f", which fits the budget — recalculated DP and greedy both select {_list(a['dp'])}, so the constrained "
                 "choice disappears under the current assumptions.")
    elif a["all_fit"]:
        tail += f", which fits the budget, but DP ({_list(a['dp'])}) and greedy ({_list(a['greedy'])}) still differ."
    else:
        tail += (f", which still exceeds the budget (DP {_list(a['dp'])} vs greedy {_list(a['greedy'])}, gap "
                 f"{_aed(a['gap'])}/yr) — on these assumptions the 20-vs-23 contrast described for the baseline does not hold.")
    return head + tail


def full_text(r: dict) -> str:
    """Our working assumptions register — fuller explanation."""
    verdict = ("The 20-minute target is therefore a useful decision scenario: it keeps a genuine budget-constrained choice "
               "that a 23-minute target removes." if r["holds"] else
               "On the current data/assumptions the baseline 20-vs-23 contrast no longer holds as stated — see the figures above.")
    return short_text(r) + " " + verdict + " " + CAVEAT


def slide_note(r: dict) -> str:
    b, a = r["base"], r["alt"]
    lo, hi = r["plateau"]
    s = (f"Why {r['settings']['promise']} min? A proposed internal transfer target: {b['n_pass']} of {b['n_dest']} branches "
         f"pass directly (the same for any target from {lo} to {hi} min); the {len(b['candidates'])} upgrade candidates "
         f"cost {_aed(b['cost_total'])} > {_aed(b['budget'])}, so the budget forces a choice.")
    if a:
        s += (f" At {a['promise']} min {_list(r['newly_passing'])} also passes and the other {len(a['candidates'])} cost "
              f"{_aed(a['cost_total'])}" + (" — all fit, DP = greedy, no constrained choice." if a["all_fit"] and a["gap"] == 0
                                            else " — the choice remains."))
    return s + " A decision scenario, not a proven optimum or a customer-facing service."
