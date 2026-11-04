"""v2.1 Part A/B: direct transfer vs alternative mode vs local fulfilment vs outside plan, the 16–22 plateau, and the
dynamic recalculation of every classification (Part K items 4–17, 10–12, 18)."""
import warnings
from math import inf

import pandas as pd
import pytest

from src import investment_core as ic
from src import rationale as ra
from src import routing_core as rc
from src.data_loader import eligible_routes

D, A, L, O = ic.DIRECT, ic.ALT_MODE, ic.LOCAL, ic.OUTSIDE


def setup(ds, hub="HUB", promise=20, x=38, upgrades=None):
    r = eligible_routes(ds.times, x)
    dist = rc.dijkstra(ds.order, r, hub)["dist"]
    pool = ic.build_pool(ds.upgrades if upgrades is None else upgrades, dist, hub, promise)["rows"]
    return dist, pool


def by_branch(plan):
    return {r["branch_code"]: r["modelled_service_disposition"] for r in plan["rows"]}


def test_direct_pass_set_at_20_is_kar_qus(ds):
    dist, _ = setup(ds)
    assert sorted(n for n in ds.order if n != "HUB" and dist[n] <= 20) == ["KAR", "QUS"]


@pytest.mark.parametrize("promise", range(16, 23))
def test_plateau_16_to_22_same_direct_set(ds, promise):
    dist, _ = setup(ds)
    assert sorted(n for n in ds.order if n != "HUB" and dist[n] <= promise) == ["KAR", "QUS"]
    assert ra.plateau(dist, "HUB", promise) == (16, 22)


def test_promise_15_and_23_change_the_set(ds):
    dist, _ = setup(ds)
    assert [n for n in ds.order if n != "HUB" and dist[n] <= 15] == ["KAR"]
    assert sorted(n for n in ds.order if n != "HUB" and dist[n] <= 23) == ["KAR", "QUS", "UMS"]


def test_rationale_does_not_claim_unique_loosest_target(ds):
    r = ra.promise_rationale(ds)
    assert r["plateau"] == (16, 22)
    for txt in (ra.short_text(r), ra.full_text(r), ra.slide_note(r)):
        assert "loosest" not in txt.lower() and "unique" not in txt.lower().replace("not a unique one", "")
        assert "16" in txt and "22" in txt


def test_candidate_totals_20_and_23(ds):
    _, pool20 = setup(ds, promise=20)
    _, pool23 = setup(ds, promise=23)
    assert sum(p["Cost_AED"] for p in pool20) == 481_860 > 450_000
    assert [p["Code"] for p in pool23] == ["JAF", "SHJ", "AJM"] and sum(p["Cost_AED"] for p in pool23) == 411_960 <= 450_000


def test_23_minute_dp_and_greedy_recalculated_and_compared(ds):
    dist, pool = setup(ds, promise=23)
    s = ic.solve(pool, 450_000, "HUB", dist, 23, ds.order)
    dp = sorted(s["names"][i] for i in s["dp"]["picks"])
    gr = sorted(s["names"][i] for i in s["greedy"]["picks"])
    assert dp == gr == ["AJM", "JAF", "SHJ"] and s["dp"]["benefit"] == s["greedy"]["benefit"]
    assert by_branch(s["dp"]["plan"])["UMS"] == D                     # inclusive boundary at exactly 23


def test_dp_baseline_dispositions(ds):
    dist, pool = setup(ds)
    s = ic.solve(pool, 450_000, "HUB", dist, 20, ds.order)
    p = s["dp"]["plan"]
    assert by_branch(p) == {"KAR": D, "QUS": D, "UMS": O, "JAF": L, "SHJ": L, "AJM": L}
    assert (p["direct"], p["alt_mode"], p["local"], p["outside"], p["with_disposition"]) == (2, 0, 3, 1, 5)
    assert p["outside_codes"] == ["UMS"]


def test_greedy_baseline_dispositions_use_data_alt_mode(ds):
    dist, pool = setup(ds)
    s = ic.solve(pool, 450_000, "HUB", dist, 20, ds.order)
    p = s["greedy"]["plan"]
    assert by_branch(p) == {"KAR": D, "QUS": D, "UMS": A, "JAF": L, "SHJ": L, "AJM": O}
    ums = {r["branch_code"]: r for r in p["rows"]}["UMS"]
    assert ums["shortest_hub_time_min"] == 23 and not ums["direct_transfer_pass"]      # road result preserved
    assert ums["alternative_mode_time_min"] == 18 and ums["alternative_mode_pass"]


@pytest.mark.parametrize("minutes_after,expected", [(0, L), (25, O), (18, A)])
def test_upgrade_type_from_data_changes_disposition(ds, minutes_after, expected):
    up = ds.upgrades.copy()
    up.loc[up.Code == "UMS", "Minutes_after"] = minutes_after
    dist, pool = setup(ds, upgrades=up)
    s = ic.solve(pool, 450_000, "HUB", dist, 20, ds.order)
    assert by_branch(s["greedy"]["plan"])["UMS"] == expected


def test_local_fulfilment_is_never_a_zero_minute_journey(ds):
    for budget in range(0, 600_001, 50_000):
        dist, pool = setup(ds)
        s = ic.solve(pool, budget, "HUB", dist, 20, ds.order)
        for plan in (s["dp"]["plan"], s["greedy"]["plan"]):
            for r in plan["rows"]:
                if r["modelled_service_disposition"] == L:
                    assert r["shortest_hub_time_min"] == dist[r["branch_code"]] > 20
                    assert not r["direct_transfer_pass"]
                    assert "zero-minute" in r["explanation"]                 # explanation states it is not zero


def test_counts_reconcile_with_rows(ds):
    dist, pool = setup(ds)
    for budget in (0, 300_000, 450_000, 600_000):
        s = ic.solve(pool, budget, "HUB", dist, 20, ds.order)
        for plan in (s["dp"]["plan"], s["greedy"]["plan"], s["plan_before"]):
            assert sum(plan["counts"].values()) == plan["n_dest"] == 6
            assert plan["with_disposition"] == plan["direct"] + plan["alt_mode"] + plan["local"]


def test_hub_change_recalculates_everything(ds):
    dist, pool = setup(ds, hub="JAF")
    assert dist["UMS"] == 24 and dist["HUB"] == 47
    s = ic.solve(pool, 450_000, "JAF", dist, 20, ds.order)
    assert "JAF" not in [r["branch_code"] for r in s["dp"]["plan"]["rows"]] and s["dp"]["plan"]["n_dest"] == 6
    assert s["plan_before"]["direct"] == 0
    rows = {r["branch_code"]: r for r in s["dp"]["plan"]["rows"]}
    assert rows["HUB"]["modelled_service_disposition"] == O                 # no priced option for HUB


def test_promise_change_recalculates(ds):
    dist, pool = setup(ds, promise=25)
    assert [p["Code"] for p in pool] == ["JAF", "AJM"]
    s = ic.solve(pool, 450_000, "HUB", dist, 25, ds.order)
    assert by_branch(s["dp"]["plan"]) == {"KAR": D, "QUS": D, "UMS": D, "JAF": L, "SHJ": D, "AJM": L}


def test_budget_change_recalculates(ds):
    dist, pool = setup(ds)
    small = ic.solve(pool, 150_000, "HUB", dist, 20, ds.order)
    assert [small["names"][i] for i in small["dp"]["picks"]] == ["JAF"]
    assert small["dp"]["plan"]["outside"] == 3


def test_cost_change_updates_disposition_and_rationale(ds):
    up = ds.upgrades.copy()
    up.loc[up.Code == "UMS", "Cost_AED"] = 10_000
    dist, pool = setup(ds, upgrades=up)
    s = ic.solve(pool, 450_000, "HUB", dist, 20, ds.order)
    assert by_branch(s["dp"]["plan"])["UMS"] == A                           # cheap motorbike now in the DP plan
    assert ra.promise_rationale(ds, upgrades=up)["base"]["cost_total"] == 481_860 - 69_900 + 10_000


def test_coverage_table_type_safe_and_unchanged():
    """F2: pandas 2.2 raised 'Downcasting object dtype arrays on .fillna' here; the v2.1 key is float-typed."""
    from src.data_loader import load_dataset
    ds = load_dataset()
    expected = {38: ["KAR", "QUS", "UMS", "SHJ", "JAF", "AJM"], 27: ["KAR", "QUS", "UMS", "SHJ", "JAF", "AJM"],
                10: ["AJM", "JAF", "KAR", "QUS", "SHJ", "UMS"]}
    for x, order in expected.items():
        r = eligible_routes(ds.times, x)
        res = rc.dijkstra(ds.order, r, "HUB")
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            df = rc.coverage_table(ds.order, r, ds.times, res, 20, {c: c for c in ds.order}, {c: "" for c in ds.order})
        assert list(df["Code"]) == order
        assert (df["Status"] == "UNREACHABLE").sum() == sum(res["dist"][n] == inf for n in ds.order if n != "HUB")
        assert df["Minutes"].isna().sum() == (df["Status"] == "UNREACHABLE").sum()


# ---------------------------------------------------------------- v2.2: primary disposition vs selected interventions
def setup_all(ds, hub, promise, show_all, x=38, upgrades=None):
    r = eligible_routes(ds.times, x)
    dist = rc.dijkstra(ds.order, r, hub)["dist"]
    pool = ic.build_pool(ds.upgrades if upgrades is None else upgrades, dist, hub, promise, show_all)["rows"]
    return dist, pool


def test_baseline_intervention_counts_equal_primary_counts(ds):
    dist, pool = setup(ds)
    p = ic.solve(pool, 450_000, "HUB", dist, 20, ds.order)["dp"]["plan"]
    assert (p["direct"], p["local"], p["outside"]) == (2, 3, 1)
    assert (p["n_selected"], p["local_selected"], p["alt_selected"], p["selected_on_direct"]) == (3, 3, 0, 0)
    assert p["local_selected_codes"] == ["JAF", "SHJ", "AJM"]


def test_jaf_90_include_passing_counts_interventions_not_primary(ds):
    dist, pool = setup_all(ds, "JAF", 90, True)
    s = ic.solve(pool, 450_000, "JAF", dist, 90, ds.order)
    picks = [s["names"][i] for i in s["dp"]["picks"]]
    p = s["dp"]["plan"]
    rows = {r["branch_code"]: r for r in p["rows"]}
    expected_local = [c for c in picks if float(ds.upgrades.set_index("Code").loc[c, "Minutes_after"]) == 0]
    assert p["local_selected"] == len(expected_local) == sum(r["local_fulfilment_selected"] for r in p["rows"])
    assert p["local_selected"] > p["local"]                       # an already-direct branch carries a local upgrade
    shj = rows["SHJ"]
    assert shj["direct_transfer_pass"] and shj["modelled_service_disposition"] == D and shj["local_fulfilment_selected"]
    assert "optional upgrade is also selected" in shj["explanation"]
    assert p["selected_on_direct"] >= 1
    assert f"+{p['selected_on_direct']} optional upgrade(s) on branches already direct" in ic.plan_summary(p)
    # UMS motorbike selected from JAF: mechanism is alternative mode but its time is not modelled -> never ALT_MODE
    assert rows["UMS"]["alternative_mode_upgrade_selected"] and not rows["UMS"]["alternative_mode_pass"]
    assert p["alt_qualifying_selected"] == 0


def test_option_toggle_recalculates(ds):
    dist, pool_off = setup_all(ds, "JAF", 90, False)
    _, pool_on = setup_all(ds, "JAF", 90, True)
    assert [r["Code"] for r in pool_off] == [r["Code"] for r in pool_on if r["Fails"]]
    assert len(pool_on) > len(pool_off)                           # already-passing options appear only in the scenario view
    off = ic.solve(pool_off, 450_000, "JAF", dist, 90, ds.order)["dp"]["plan"]
    on = ic.solve(pool_on, 450_000, "JAF", dist, 90, ds.order)["dp"]["plan"]
    assert off["selected_on_direct"] == 0 and on["selected_on_direct"] >= 1
    assert on["local_selected"] > off["local_selected"]
    assert on["direct"] == off["direct"]                            # primary direct set depends only on road times


@pytest.mark.parametrize("hub", ["HUB", "KAR", "QUS", "UMS", "JAF", "SHJ", "AJM"])
@pytest.mark.parametrize("promise,show_all", [(20, False), (45, True), (90, True)])
def test_every_destination_classified_once_and_counts_reconcile(ds, hub, promise, show_all):
    dist, pool = setup_all(ds, hub, promise, show_all)
    s = ic.solve(pool, 450_000, hub, dist, promise, ds.order)
    for plan, picks in ((s["dp"]["plan"], s["dp"]["picks"]), (s["greedy"]["plan"], s["greedy"]["picks"])):
        codes = [r["branch_code"] for r in plan["rows"]]
        assert sorted(codes) == sorted(n for n in ds.order if n != hub) and len(set(codes)) == len(codes)
        assert sum(plan["counts"].values()) == plan["n_dest"] == 6
        assert plan["n_selected"] == len(picks) == len(plan["interventions"])
        assert plan["local_selected"] + plan["alt_selected"] <= plan["n_selected"]
        assert sorted(i["branch_code"] for i in plan["interventions"]) == sorted(s["names"][i] for i in picks)
        assert sum(i["cost_aed"] for i in plan["interventions"]) == sum(s["cost"][i] for i in picks)


@pytest.mark.parametrize("value", [float("nan"), -5, "n/a"])
def test_alternative_mode_requires_explicit_qualifying_time(ds, value):
    row = {"Code": "UMS", "Upgrade": "Express motorbike courier", "Cost_AED": 69_900, "Minutes_after": value}
    assert ic.upgrade_mechanism(row, "HUB")["mechanism"] == "unspecified"
    rec = ic.classify_branch("UMS", 23, 20, row, "HUB")
    assert rec["modelled_service_disposition"] == O and not rec["alternative_mode_pass"]
    assert rec["upgrade_selected"] and not rec["local_fulfilment_selected"]


def test_alternative_mode_time_above_target_does_not_qualify(ds):
    row = {"Code": "UMS", "Upgrade": "Express motorbike courier", "Cost_AED": 69_900, "Minutes_after": 21}
    rec = ic.classify_branch("UMS", 23, 20, row, "HUB")
    assert rec["alternative_mode_upgrade_selected"] and not rec["alternative_mode_pass"]
    assert rec["modelled_service_disposition"] == O
    rec = ic.classify_branch("UMS", 23, 21, row, "HUB")              # inclusive at exactly the target
    assert rec["modelled_service_disposition"] == A
