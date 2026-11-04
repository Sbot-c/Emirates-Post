"""20- vs 23-minute rationale: computed from live state, never assumed."""
from src import rationale as ra


def test_baseline_20_minutes_from_live_state(ds):
    r = ra.promise_rationale(ds)
    b = r["base"]
    assert r["settings"] == {"x": 38, "hub": "HUB", "promise": 20, "budget": 450_000}
    assert b["n_pass"] == 2 and b["n_dest"] == 6 and sorted(b["passing"]) == ["KAR", "QUS"]
    assert b["candidates"] == ["UMS", "JAF", "SHJ", "AJM"]
    assert b["cost_total"] == 481_860 and not b["all_fit"] and b["choice_forced"]
    assert sorted(b["dp"]) == ["AJM", "JAF", "SHJ"] and sorted(b["greedy"]) == ["JAF", "SHJ", "UMS"]
    assert b["gap"] == 45_000


def test_23_minute_scenario_is_computed(ds):
    r = ra.promise_rationale(ds)
    a = r["alt"]
    assert a["promise"] == 23 and r["newly_passing"] == ["UMS"]       # UMS is exactly 23 and passes under <=
    assert a["candidates"] == ["JAF", "SHJ", "AJM"]
    assert a["cost_total"] == 143_520 + 130_920 + 137_520 == 411_960
    assert a["all_fit"]
    # compared, not assumed: both methods' selections are calculated
    assert sorted(a["dp"]) == sorted(a["greedy"]) == ["AJM", "JAF", "SHJ"] and a["gap"] == 0
    assert r["holds"]
    txt = ra.short_text(r)
    assert "AED 411,960" in txt and "UMS also passes" in txt and "the constrained choice disappears" in txt


def test_rationale_updates_when_costs_change(ds):
    up = ds.upgrades.copy()
    up.loc[up.Code == "AJM", "Cost_AED"] = 200_000            # three remaining options no longer fit at 23 min
    r = ra.promise_rationale(ds, upgrades=up)
    assert r["alt"]["cost_total"] == 143_520 + 130_920 + 200_000 and not r["alt"]["all_fit"]
    assert not r["holds"]
    assert "does not hold" in ra.short_text(r) and "the constrained choice disappears" not in ra.short_text(r)


def test_rationale_updates_when_benefits_change(ds):
    up = ds.upgrades.copy()
    up.loc[up.Code == "UMS", "Benefit_AED"] = 500_000          # greedy and DP now agree at 20 min
    r = ra.promise_rationale(ds, upgrades=up)
    assert r["base"]["gap"] == 0 and not r["holds"]
    assert "DP and greedy agree" in ra.short_text(r)


def test_rationale_follows_live_settings(ds):
    r = ra.promise_rationale(ds, promise=23)
    assert r["base"]["n_pass"] == 3 and r["alt"]["promise"] == 24
    r = ra.promise_rationale(ds, hub="JAF")
    assert r["base"]["n_pass"] == 0 and "JAF" not in r["base"]["candidates"]


def test_texts_are_labelled_as_internal_target(ds):
    r = ra.promise_rationale(ds)
    assert "proposed internal hub-to-branch transfer target" in ra.full_text(r)
    assert "not an existing Emirates Post customer-facing service" in ra.full_text(r)
    assert "not a proven optimum or a customer-facing service" in ra.slide_note(r)
