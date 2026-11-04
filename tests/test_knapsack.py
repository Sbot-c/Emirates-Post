"""0/1 knapsack DP, greedy, brute force, units and budget sweep."""
from itertools import combinations

from src import investment_core as ic
from src import routing_core as rc
from src.data_loader import eligible_routes


def baseline(ds, promise=20, hub="HUB", x=38):
    r = eligible_routes(ds.times, x)
    res = rc.dijkstra(ds.order, r, hub)
    pool = ic.build_pool(ds.upgrades, res["dist"], hub, promise)
    return res, pool


def test_baseline_450k(ds):
    res, pool = baseline(ds)
    assert [p["Code"] for p in pool["rows"]] == ["UMS", "JAF", "SHJ", "AJM"]
    s = ic.solve(pool["rows"], 450_000, "HUB", res["dist"], 20)
    n = s["names"]
    assert sorted(n[i] for i in s["dp"]["picks"]) == ["AJM", "JAF", "SHJ"]
    assert (s["dp"]["spent"], s["dp"]["benefit"], s["dp"]["left"]) == (411_960, 765_000, 38_040)
    assert sorted(n[i] for i in s["greedy"]["picks"]) == ["JAF", "SHJ", "UMS"]
    assert (s["greedy"]["spent"], s["greedy"]["benefit"]) == (344_340, 720_000)
    assert s["dp"]["benefit"] - s["greedy"]["benefit"] == 45_000
    assert s["brute_force"]["agrees"] and s["exact"] and s["unit"] == 20
    # v2.1: direct-transfer compliance stays 2/6; local fulfilment is a separate disposition (was wrongly "5 of 6")
    assert s["plan_before"]["direct"] == 2
    assert (s["dp"]["plan"]["direct"], s["dp"]["plan"]["local"], s["dp"]["plan"]["outside"]) == (2, 3, 1)
    assert s["dp"]["plan"]["with_disposition"] == 5


def test_trace_grid_matches_joan(ds):
    res, pool = baseline(ds)
    cost = [p["Cost_AED"] for p in pool["rows"]]
    ben = [p["Benefit_AED"] for p in pool["rows"]]
    hc, hb = ic.trace_units(cost, 450_000)
    assert hc == [7, 14, 13, 14] and hb == 45
    K, best, chosen, path = ic.knapsack(hc, ben, hb)
    assert best // 1000 == 765 and chosen == [1, 2, 3]
    assert [(i, w, t) for i, w, t in path] == [(4, 45, True), (3, 31, True), (2, 18, True), (1, 4, False)]


def test_budgets_never_overspend_and_match_brute_force(ds):
    res, pool = baseline(ds)
    for b in (0, 300_000, 450_000, 500_000, 600_000):
        s = ic.solve(pool["rows"], b, "HUB", res["dist"], 20)
        assert s["dp"]["spent"] <= b and s["greedy"]["spent"] <= b
        assert s["brute_force"]["agrees"]
    s = ic.solve(pool["rows"], 500_000, "HUB", res["dist"], 20)
    assert len(s["dp"]["picks"]) == 4 and s["dp"]["spent"] == 481_860 and s["dp"]["benefit"] == 900_000
    assert s["dp"]["left"] == 18_140
    p = s["dp"]["plan"]
    assert (p["direct"], p["alt_mode"], p["local"], p["outside"]) == (2, 1, 3, 0)
    assert ic.solve(pool["rows"], 0, "HUB", res["dist"], 20)["dp"]["picks"] == []


def test_dp_equals_exhaustive_at_every_slider_step(ds):
    res, pool = baseline(ds)
    cost = [p["Cost_AED"] for p in pool["rows"]]
    ben = [p["Benefit_AED"] for p in pool["rows"]]
    for b in range(0, 600_001, 10_000):
        best = max(sum(ben[i] for i in c) for r in range(5) for c in combinations(range(4), r)
                   if sum(cost[i] for i in c) <= b)
        assert ic.solve(pool["rows"], b, "HUB", res["dist"], 20)["dp"]["benefit"] == best, b


def test_gap_ranges(ds):
    res, pool = baseline(ds)
    cost = [p["Cost_AED"] for p in pool["rows"]]
    ben = [p["Benefit_AED"] for p in pool["rows"]]
    unit, exact = ic.choose_unit(cost)
    cu, _ = ic.to_units(cost, 0, unit, exact)
    ranges = ic.gap_ranges(ic.scan_budgets(cu, ben, unit))
    assert [(a, b) for a, b, _ in ranges] == [(130_920, 143_500), (274_440, 344_320), (411_960, 481_840)]


def test_fallback_unit_rounds_up_never_overspends():
    rows = [{"Code": "A", "Upgrade": "a", "Cost_AED": 69_901, "Benefit_AED": 100, "Minutes_after": 0.0, "Current_time": 30, "Fails": True},
            {"Code": "B", "Upgrade": "b", "Cost_AED": 30_099, "Benefit_AED": 90, "Minutes_after": 0.0, "Current_time": 30, "Fails": True}]
    s = ic.solve(rows, 100_000, "HUB", {"HUB": 0, "A": 30, "B": 30}, 20)
    assert not s["exact"] and s["unit"] == 1000
    assert s["units"] == [70, 31]                       # rounded UP
    assert s["dp"]["spent"] <= 100_000 and s["dp"]["picks"] == [0]   # 70+31 = 101 > 100 units: cannot take both
    assert s["brute_force"]["agrees"]


def test_edited_values_recalculate(ds):
    res, pool = baseline(ds)
    rows = [dict(r) for r in pool["rows"]]
    rows[0]["Benefit_AED"] = 400_000                    # make UMS hugely valuable
    s = ic.solve(rows, 450_000, "HUB", res["dist"], 20)
    assert 0 in s["dp"]["picks"] and s["brute_force"]["agrees"]


def test_greedy_tie_break_deterministic():
    total, picks, steps = ic.greedy([10, 10, 10], [20, 20, 20], 20)
    assert picks == [0, 1] and [i for i, _, _ in steps] == [0, 1, 2]


def test_non_hub_source_pool_and_unmodelled_motorbike(ds):
    res, pool = baseline(ds, hub="JAF")
    codes = [p["Code"] for p in pool["rows"]]
    assert "JAF" not in codes                            # the hub itself is never a destination
    assert set(pool["failing_no_option"]) <= {"HUB", "KAR", "QUS"}
    s = ic.solve(pool["rows"], 600_000, "JAF", res["dist"], 20, ds.order)
    if "UMS" in [s["names"][i] for i in s["dp"]["picks"]]:
        ums = {r["branch_code"]: r for r in s["dp"]["plan"]["rows"]}["UMS"]
        assert ums["alternative_mode_time_min"] is None              # motorbike time not modelled for a non-HUB source
        assert ums["modelled_service_disposition"] == ic.OUTSIDE


def test_no_failing_branch_means_empty_pool(ds):
    res, pool = baseline(ds, promise=60)
    assert pool["rows"] == []
