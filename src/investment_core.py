"""
investment_core.py — 0/1 knapsack by dynamic programming, greedy comparison and brute-force
cross-check (Investment Analyst: Joan). No Streamlit in here.

Integrated from Joan's knapsack_core.py. The DP table is written out explicitly (no optimiser).
Integration changes: the failing-branch pool now comes from the shared Dijkstra result (live hub,
live threshold, shared promise); unreachable branches count as failing; branches with no priced
option are reported, never invented; a coarse unit never rounds a cost down.
"""
from __future__ import annotations

from functools import reduce
from itertools import combinations
from math import ceil, gcd, inf

BUDGET_STEP = 10_000
BUDGET_MAX = 600_000
FALLBACK_UNIT = 1_000
MOTORBIKE_REFERENCE_HUB = "HUB"   # UMS 18-min motorbike estimate is defined from the Al Ramool hub


# ---------------------------------------------------------------- the knapsack, written out
def knapsack(costs: list, benefits: list, budget: int):
    """K[i][w] = best benefit using only the first i options with budget w (grid units).
    Cell rule: K[i][w] = max(K[i-1][w]  (leave),  benefit_i + K[i-1][w - cost_i]  (take, if affordable)).
    Traceback: a cell that differs from the one above means option i was taken."""
    n = len(costs)
    K = [[0] * (budget + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        c, b = costs[i - 1], benefits[i - 1]
        for w in range(budget + 1):
            K[i][w] = K[i - 1][w]
            if c <= w and b + K[i - 1][w - c] > K[i][w]:
                K[i][w] = b + K[i - 1][w - c]
    chosen, w, path = [], budget, []
    for i in range(n, 0, -1):
        took = K[i][w] != K[i - 1][w]
        path.append((i, w, took))
        if took:
            chosen.append(i - 1)
            w -= costs[i - 1]
    chosen.reverse()
    return K, K[n][budget], chosen, path


def greedy(costs: list, benefits: list, budget: int):
    """Best benefit-per-cost first; ties broken by row (matrix) order. Takes each option that still fits."""
    order = sorted(range(len(costs)), key=lambda i: (-(benefits[i] / costs[i]), i))
    left, total, picks, steps = budget, 0, [], []
    for i in order:
        fits = costs[i] <= left
        if fits:
            left -= costs[i]
            total += benefits[i]
            picks.append(i)
        steps.append((i, fits, left))
    return total, sorted(picks), steps


def brute_force(costs: list, benefits: list, budget: int):
    best, best_set = 0, ()
    for r in range(len(costs) + 1):
        for combo in combinations(range(len(costs)), r):
            if sum(costs[i] for i in combo) <= budget:
                b = sum(benefits[i] for i in combo)
                if b > best:
                    best, best_set = b, combo
    return best, list(best_set)


# ---------------------------------------------------------------- money units
def choose_unit(costs_aed: list, step: int = BUDGET_STEP, minimum: int = 10):
    """Largest unit dividing every cost AND the budget step → exact DP. Otherwise AED 1,000 with costs
    rounded UP (the plan can then never overspend; it may be slightly conservative)."""
    u = reduce(gcd, [int(c) for c in costs_aed] + [int(step)])
    return (u, True) if u >= minimum else (FALLBACK_UNIT, False)


def to_units(costs_aed: list, budget_aed: int, unit: int, exact: bool):
    return [c // unit if exact else ceil(c / unit) for c in costs_aed], int(budget_aed // unit)


def trace_units(costs_aed: list, budget_aed: int, unit: int = 10_000):
    """The hand-trace convention on Joan's sheet: costs rounded to the NEAREST AED 10,000.
    Used only to reproduce the paper grid; the exact calculation is authoritative."""
    return [max(1, round(c / unit)) for c in costs_aed], int(budget_aed // unit)


# ---------------------------------------------------------------- budget sweep
def scan_budgets(costs_u: list, benefits: list, unit: int, max_aed: int = BUDGET_MAX):
    """DP optimum (last row of one DP table) and greedy total at every budget in grid units."""
    W = max_aed // unit
    K, _, _, _ = knapsack(costs_u, benefits, W)
    return [(w * unit, K[-1][w], greedy(costs_u, benefits, w)[0]) for w in range(W + 1)]


def compress_steps(scan: list) -> list:
    out, last = [], None
    for b, d, g in scan:
        if (d, g) != last:
            out.append((b, d, g))
            last = (d, g)
    out.append(scan[-1])
    return out


def gap_ranges(scan: list) -> list:
    out, start, worst, prev = [], None, 0, None
    for b, d, g in scan:
        if d > g:
            if start is None:
                start, worst = b, 0
            worst = max(worst, d - g)
        elif start is not None:
            out.append((start, prev, worst))
            start = None
        prev = b
    if start is not None:
        out.append((start, prev, worst))
    return out


# ---------------------------------------------------------------- the investment decision
def build_pool(upgrades, dist: dict, source: str, promise: int, show_all: bool = False) -> dict:
    """Which priced options are eligible under the live hub/promise.
    Eligible = destination branch currently FAILS (time > promise, or unreachable) and has a priced
    option. The hub's own row is never a destination. `show_all` is the labelled scenario view."""
    rows, failing_no_option = [], []
    priced = set(upgrades["Code"])
    for r in upgrades.itertuples(index=False):
        if r.Code == source:
            continue
        t = dist.get(r.Code, inf)
        fails = t > promise
        if fails or show_all:
            rows.append({"Code": r.Code, "Upgrade": r.Upgrade, "Cost_AED": int(r.Cost_AED),
                         "Benefit_AED": int(r.Benefit_AED), "Minutes_after": float(r.Minutes_after),
                         "Current_time": t, "Fails": fails})
    for n, t in dist.items():
        if n != source and t > promise and n not in priced:
            failing_no_option.append(n)
    return {"rows": rows, "failing_no_option": failing_no_option}


# ---------------------------------------------------------------- service disposition (v2.1)
DIRECT = "DIRECT HUB TRANSFER WITHIN TARGET"
ALT_MODE = "ALTERNATIVE MODE WITHIN TARGET (ASSUMPTION)"
LOCAL = "LOCAL FULFILMENT UPGRADE"
OUTSIDE = "OUTSIDE SELECTED SERVICE PLAN"
DISPOSITIONS = (DIRECT, ALT_MODE, LOCAL, OUTSIDE)
HAS_DISPOSITION = (DIRECT, ALT_MODE, LOCAL)        # "destinations with a modelled service disposition"


def upgrade_mechanism(row: dict, source: str) -> dict:
    """How an upgrade serves its branch, read from upgrades.csv `Minutes_after` (documented encoding):
      * Minutes_after == 0  -> LOCAL FULFILMENT: stock held at the branch (mini-hub). This is NOT a travel time;
        the hub-to-branch journey is unchanged.
      * Minutes_after  > 0  -> ALTERNATIVE MODE with that explicitly stated assumed time (the UMS motorbike, 18 min).
        The estimate is defined from the Al Ramool hub only; for any other hub the mode time is 'not modelled' (None).
      * missing / non-numeric / negative -> 'unspecified': no mechanism is assumed (never classified as a mode).
    """
    try:
        m = float(row.get("Minutes_after"))
    except (TypeError, ValueError):
        m = float("nan")
    if m != m or m < 0:                                     # NaN or negative: the data does not state a mechanism
        return {"mechanism": "unspecified", "mode_name": None, "mode_time": None}
    if m == 0:
        return {"mechanism": "local_fulfilment", "mode_name": None, "mode_time": None}
    return {"mechanism": "alternative_mode", "mode_name": str(row.get("Upgrade", "alternative mode")),
            "mode_time": m if source == MOTORBIKE_REFERENCE_HUB else None}


def mechanism_label(row: dict, source: str) -> str:
    mech = upgrade_mechanism(row, source)
    if mech["mechanism"] == "local_fulfilment":
        return "Local fulfilment (stock held at branch) — hub travel time unchanged"
    if mech["mechanism"] == "unspecified":
        return "Mechanism not stated in upgrades.csv — not modelled"
    if mech["mode_time"] is None:
        return "Alternative mode — time not modelled for this hub"
    return f"Alternative mode: {mech['mode_time']:.0f} min (assumption, from Al Ramool hub)"


def intervention_label(rec: dict) -> str:
    """Human-readable selected intervention for a classified branch ('—' when nothing is selected)."""
    if not rec["upgrade_selected"]:
        return "—"
    name = rec["selected_upgrade"]
    if rec["selected_upgrade_type"] == "local_fulfilment":
        return f"{name} — local fulfilment"
    if rec["selected_upgrade_type"] == "alternative_mode":
        t = rec["alternative_mode_time_min"]
        return f"{name} — alternative mode, " + (f"{t:.0f} min (assumption)" if t is not None else "time not modelled from this hub")
    return f"{name} — mechanism not stated"


def classify_branch(code: str, shortest: float, promise: int, selected_row: dict | None, source: str) -> dict:
    """THE single authoritative classification used by every card, table, chart and slide metric.

    Two separate concepts (v2.2):
      * PRIMARY service disposition — exactly one of DISPOSITIONS per destination. Direct transfer depends only on the
        road-network shortest time (time <= target, inclusive); a selected upgrade never changes that travel time.
      * SELECTED INTERVENTION flags — taken from the investment algorithm's selection (`selected_row`), never inferred
        from the primary disposition. A branch that already passes directly can still carry a selected upgrade
        (scenario view); its primary disposition stays DIRECT and the intervention is still reported and counted."""
    direct = shortest <= promise
    mech = upgrade_mechanism(selected_row, source) if selected_row else None
    rec = {"branch_code": code, "shortest_hub_time_min": None if shortest == inf else int(shortest),
           "direct_transfer_pass": direct,
           # ---- selected intervention (authoritative: from the portfolio's picks)
           "upgrade_selected": selected_row is not None,
           "selected_upgrade": selected_row["Upgrade"] if selected_row else None,
           "selected_upgrade_type": mech["mechanism"] if mech else None,
           "selected_upgrade_cost_aed": int(selected_row["Cost_AED"]) if selected_row else 0,
           "local_fulfilment_selected": bool(mech and mech["mechanism"] == "local_fulfilment"),
           "alternative_mode_upgrade_selected": bool(mech and mech["mechanism"] == "alternative_mode"),
           "alternative_mode_name": None, "alternative_mode_time_min": None, "alternative_mode_pass": False}
    if rec["alternative_mode_upgrade_selected"]:
        rec["alternative_mode_name"] = mech["mode_name"]
        rec["alternative_mode_time_min"] = mech["mode_time"]
        rec["alternative_mode_pass"] = mech["mode_time"] is not None and mech["mode_time"] <= promise
    rec["selected_intervention"] = intervention_label(rec)
    hub_txt = "unreachable on the van network" if shortest == inf else f"{int(shortest)} min by road network"
    if direct:
        rec["modelled_service_disposition"] = DIRECT
        rec["explanation"] = f"Shortest hub path {hub_txt} ≤ {promise}-min target." + (
            f" An optional upgrade is also selected (scenario view): {rec['selected_intervention']}; the primary "
            "disposition stays direct transfer and the intervention is counted separately." if selected_row else "")
    elif rec["alternative_mode_pass"]:
        rec["modelled_service_disposition"] = ALT_MODE
        rec["explanation"] = (f"Road network {hub_txt} > target; assumed {rec['alternative_mode_name'].lower()} at "
                              f"{rec['alternative_mode_time_min']:.0f} min ≤ {promise} min (upgrades.csv assumption).")
    elif rec["local_fulfilment_selected"]:
        rec["modelled_service_disposition"] = LOCAL
        rec["explanation"] = (f"Hub transfer still {hub_txt} (> target); demand assumed served from local stock at the "
                              "branch. Not a zero-minute journey and not direct-transfer compliant.")
    else:
        rec["modelled_service_disposition"] = OUTSIDE
        if selected_row is not None and rec["alternative_mode_upgrade_selected"]:
            why = ("its assumed time is not modelled from this hub" if rec["alternative_mode_time_min"] is None
                   else f"its assumed {rec['alternative_mode_time_min']:.0f} min exceeds the target")
            rec["explanation"] = f"Hub transfer {hub_txt} > target; selected alternative mode does not qualify — {why}."
        elif selected_row is not None:
            rec["explanation"] = (f"Hub transfer {hub_txt} > target; the selected upgrade's mechanism is not stated in "
                                  "upgrades.csv, so no service disposition is assumed.")
        else:
            rec["explanation"] = f"Hub transfer {hub_txt} > target and no qualifying upgrade in the selected portfolio."
    return rec


def service_plan(order: list, source: str, dist: dict, promise: int, pool_rows: list, picks: list) -> dict:
    """Per-branch primary dispositions and selected interventions for a portfolio (`picks` = indices into pool_rows).
    Primary-disposition counts always sum to the number of destinations; intervention counts are taken from the
    selected picks and are independent of the primary disposition."""
    chosen = {pool_rows[i]["Code"]: pool_rows[i] for i in picks}
    rows = [classify_branch(n, dist.get(n, inf), promise, chosen.get(n), source) for n in order if n != source]
    counts = {d: sum(r["modelled_service_disposition"] == d for r in rows) for d in DISPOSITIONS}
    sel = [r for r in rows if r["upgrade_selected"]]
    return {"rows": rows, "counts": counts, "n_dest": len(rows),
            "with_disposition": sum(counts[d] for d in HAS_DISPOSITION),
            "direct": counts[DIRECT], "alt_mode": counts[ALT_MODE], "local": counts[LOCAL], "outside": counts[OUTSIDE],
            "outside_codes": [r["branch_code"] for r in rows if r["modelled_service_disposition"] == OUTSIDE],
            # ---- selected interventions (branch count; the model allows at most one option per branch)
            "n_selected": len(sel),
            "local_selected": sum(r["local_fulfilment_selected"] for r in sel),
            "alt_selected": sum(r["alternative_mode_upgrade_selected"] for r in sel),
            "alt_qualifying_selected": sum(r["alternative_mode_pass"] for r in sel),
            "selected_on_direct": sum(r["direct_transfer_pass"] for r in sel),
            "local_selected_codes": [r["branch_code"] for r in sel if r["local_fulfilment_selected"]],
            "interventions": [{"branch_code": r["branch_code"], "upgrade": r["selected_upgrade"],
                               "type": r["selected_upgrade_type"], "cost_aed": r["selected_upgrade_cost_aed"],
                               "primary_disposition": r["modelled_service_disposition"]} for r in sel]}


def plan_summary(plan: dict) -> str:
    """Primary dispositions, plus any selected upgrades on branches that already meet the target directly."""
    parts = [f"{plan['direct']} direct hub transfer"]
    if plan["alt_mode"]:
        parts.append(f"{plan['alt_mode']} alternative mode (assumption)")
    parts.append(f"{plan['local']} local fulfilment")
    parts.append(f"{plan['outside']} outside plan" + (f" ({', '.join(plan['outside_codes'])})" if plan["outside_codes"] else ""))
    if plan.get("selected_on_direct"):
        parts.append(f"+{plan['selected_on_direct']} optional upgrade(s) on branches already direct")
    return " · ".join(parts)


def solve(pool_rows: list, budget_aed: int, source: str, dist: dict, promise: int, order: list | None = None) -> dict:
    """0/1 knapsack: each option taken 0 or 1 times, total first-year cost <= budget, maximise the sum of the supplied
    annual gross benefit proxies. Benefit/cost ratios are used only by the greedy comparator."""
    names = [r["Code"] for r in pool_rows]
    cost = [r["Cost_AED"] for r in pool_rows]
    ben = [r["Benefit_AED"] for r in pool_rows]
    order = order or [n for n in dist]
    unit, exact = choose_unit(cost) if cost else (BUDGET_STEP, True)
    cu, bu = to_units(cost, budget_aed, unit, exact)
    K, best, chosen, path = knapsack(cu, ben, bu)
    g_total, g_picks, g_steps = greedy(cu, ben, bu) if cost else (0, [], [])
    bf_best, bf_set = brute_force(cu, ben, bu)
    dp_spent = sum(cost[i] for i in chosen)
    g_spent = sum(cost[i] for i in g_picks)
    return {"names": names, "cost": cost, "benefit": ben, "unit": unit, "exact": exact,
            "dp": {"picks": chosen, "benefit": best, "spent": dp_spent, "left": budget_aed - dp_spent, "path": path,
                   "plan": service_plan(order, source, dist, promise, pool_rows, chosen)},
            "greedy": {"picks": g_picks, "benefit": g_total, "spent": g_spent, "left": budget_aed - g_spent,
                       "steps": g_steps, "plan": service_plan(order, source, dist, promise, pool_rows, g_picks)},
            "brute_force": {"benefit": bf_best, "picks": bf_set, "agrees": bf_best == best},
            "plan_before": service_plan(order, source, dist, promise, pool_rows, []),
            "units": cu, "budget_units": bu}


def traceback_rows(K, path, names, units, unit_label="units"):
    """Readable traceback: each stage's take/skip decision and the capacity left afterwards.
    K values are AED; shown in AED '000 when every value is a whole thousand."""
    k = (lambda v: f"{v // 1000:,}") if all(v % 1000 == 0 for row in K for v in row) else (lambda v: f"{v / 1000:,.1f}")
    rows = []
    for step, (i, w, took) in enumerate(path, 1):
        rows.append({"Step": step, "Item stage": f"{i} — {names[i - 1]}", f"Capacity w ({unit_label})": w,
                     "Compare (AED '000)": f"K[{i}][{w}] = {k(K[i][w])} vs K[{i - 1}][{w}] = {k(K[i - 1][w])}",
                     "Decision": f"TAKE {names[i - 1]}" if took else f"SKIP {names[i - 1]}",
                     f"Capacity left ({unit_label})": w - units[i - 1] if took else w})
    return rows
