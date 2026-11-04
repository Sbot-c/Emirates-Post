"""v2.4: suggested target per hub, hub ranking and the X = 39 vs X = 38 decision (all computed, none typed in)."""
from math import inf

import pytest

from src import advisor as ad
from src import routing_core as rc
from src.data_loader import eligible_routes

EXPECTED_SUGGESTION_X38 = {"HUB": 20, "KAR": 20, "QUS": 25, "UMS": 25, "JAF": 35, "SHJ": 30, "AJM": 40}


def test_baseline_hub_reproduces_the_20_minute_target(ds):
    s = ad.suggest_promise(ds.order, eligible_routes(ds.times, 38), "HUB")
    assert s["target"] == 20 and s["passing"] == ["KAR", "QUS"] and s["plateau"] == (16, 22)


@pytest.mark.parametrize("hub,target", sorted(EXPECTED_SUGGESTION_X38.items()))
def test_suggestion_per_hub_x38(ds, hub, target):
    assert ad.suggest_promise(ds.order, eligible_routes(ds.times, 38), hub)["target"] == target


@pytest.mark.parametrize("x", range(31, 43))
def test_suggestion_rule_holds_for_every_hub_and_x(ds, x):
    r = eligible_routes(ds.times, x)
    for hub in ds.order:
        s = ad.suggest_promise(ds.order, r, hub)
        d = rc.dijkstra(ds.order, r, hub)["dist"]
        assert s["target"] % 5 == 0 and 10 <= s["target"] <= 90          # whole 5-minute step inside the slider range
        assert len(s["passing"]) >= s["k"]                               # at least a third of destinations pass
        assert s["passing"] == [n for n in ds.order if n != hub and d[n] <= s["target"]]
        smaller = s["target"] - 5                                        # …and it is the SMALLEST such step
        assert smaller < 10 or sum(1 for n in ds.order if n != hub and d[n] <= smaller) < s["k"]


def test_isolated_hub_falls_back_to_slider_floor(ds):
    r = eligible_routes(ds.times, 12)          # only HUB–KAR (13) is > 12, so no route survives at X = 12
    assert len(r) == 0
    s = ad.suggest_promise(ds.order, r, "HUB")
    assert s["target"] == 10 and s["passing"] == []


def test_hub_ranking_recommends_al_ramool(ds):
    for x in (38, 39):
        rank = ad.rank_hubs(ds.order, eligible_routes(ds.times, x))
        assert rank.iloc[0]["Hub"] == "HUB" and rank["Rank"].tolist() == list(range(1, 8))
        assert rank["_total"].is_monotonic_increasing
    r38 = ad.rank_hubs(ds.order, eligible_routes(ds.times, 38)).set_index("Hub")
    assert r38.loc["HUB", "Total travel (min)"] == 174 and r38.loc["HUB", "Slowest branch (min)"] == 51


def test_unreachable_branches_are_not_ignored_in_ranking(ds):
    rank = ad.rank_hubs(ds.order, eligible_routes(ds.times, 30)).set_index("Hub")   # X = 30: network still connected?
    for h, row in rank.iterrows():
        assert row["_reach"] <= 6
        if row["_reach"] < 6:
            assert row["_total"] == inf and rank.index.get_loc(h) >= (rank["_reach"] == 6).sum()


def test_x39_does_not_beat_x38(ds):
    d = ad.x_decision(ds.order, ds.times)
    assert d["switch"] is False and d["reach_gain"] == 0
    b, c = d["baseline_row"], d["candidate_row"]
    assert (b["Routes"], c["Routes"]) == (13, 15) and b["In 10–14 band"] and not c["In 10–14 band"]
    assert b["Branches reached"] == c["Branches reached"] == 6 and b["Connected"] and c["Connected"]
    assert d["new_links"] == ["HUB–JAF 38", "HUB–AJM 38"] and d["mst_same"]
    assert (d["time_gain_min"], d["slowest_gain_min"]) == (22, 13)
    assert "X = 38 stays selected" in ad.x_decision_text(d)


def test_x_decision_would_switch_if_candidate_reached_more(ds):
    """Rule check on data where the larger X is the only connected one: X = 31 (disconnected hub?) vs a bigger X."""
    aud = ad.threshold_audit(ds.order, ds.times, 10, 66).set_index("X (min)")
    lower = aud[aud["Branches reached"] < 6]
    assert len(lower) > 0                                  # small X genuinely cut branches off
    x_lo = int(lower.index.max())
    d = ad.x_decision(ds.order, ds.times, baseline=x_lo, candidate=x_lo + 1)
    assert d["reach_gain"] > 0 and d["switch"] == bool(d["candidate_row"]["In 10–14 band"])
