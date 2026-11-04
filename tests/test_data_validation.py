"""Data validation: the canonical files pass, malformed inputs are caught."""
import pandas as pd

from src.data_loader import eligible_routes, load_dataset, read_sources


def frames():
    return [f.copy() for f in read_sources()]


def failed(ds):
    return {c.name for c in ds.checks if c.status == "fail"}


def test_canonical_data_valid(ds):
    assert ds.status == "valid"
    assert ds.order == ["HUB", "KAR", "QUS", "UMS", "JAF", "SHJ", "AJM"]
    assert ds.hub == "HUB"
    assert len(ds.times) == 21


def test_baseline_routes(ds):
    r = eligible_routes(ds.times, 38)
    assert len(r) == 13 and r["Minutes"].sum() == 334
    # strict rule: the two 38-minute hub pairs are excluded
    pairs = {frozenset((a, b)) for a, b in zip(r.From, r.To)}
    assert frozenset(("HUB", "JAF")) not in pairs and frozenset(("HUB", "AJM")) not in pairs
    # the reference export equals the derived list
    ref = pd.read_csv("data/routes_X38_reference.csv")
    assert {frozenset((a, b)) for a, b in zip(ref.From, ref.To)} == pairs


def test_upgrade_cost_buildups_add_up(ds):
    # cost basis arithmetic from upgrades.csv
    expected = {"UMS": 9900 + 54000 + 6000, "JAF": 48000 + 9600 + 4800 + 15000 + 51120 + 15000,
                "SHJ": 48000 + 4800 + 15000 + 51120 + 12000, "AJM": 54000 + 5400 + 15000 + 51120 + 12000}
    got = dict(zip(ds.upgrades.Code, ds.upgrades.Cost_AED))
    assert got == expected
    assert sum(got.values()) == 481_860
    ben = dict(zip(ds.upgrades.Code, ds.upgrades.Benefit_AED))
    assert ben == {"UMS": 15 * 30 * 300, "JAF": 8 * 150 * 300, "SHJ": 25 * 30 * 300, "AJM": 20 * 30 * 300}


def test_missing_value_detected():
    b, t, u = frames()
    t["Minutes"] = t["Minutes"].astype(float)
    t.loc[3, "Minutes"] = None
    assert "pair-times are positive whole minutes" in failed(load_dataset(frames=(b, t, u)))


def test_fractional_and_zero_minutes_detected():
    b, t, u = frames()
    t["Minutes"] = t["Minutes"].astype(float)
    t.loc[0, "Minutes"] = 13.5
    assert "pair-times are positive whole minutes" in failed(load_dataset(frames=(b, t, u)))
    b, t, u = frames()
    t.loc[0, "Minutes"] = 0
    assert "pair-times are positive whole minutes" in failed(load_dataset(frames=(b, t, u)))


def test_unknown_branch_code_detected():
    b, t, u = frames()
    t.loc[0, "To"] = "XYZ"
    assert "every endpoint exists in branches.csv" in failed(load_dataset(frames=(b, t, u)))


def test_duplicate_pair_reversed_detected():
    b, t, u = frames()
    t.loc[1] = ["KAR", "HUB", 13]          # duplicates HUB-KAR in reverse, drops HUB-QUS
    f = failed(load_dataset(frames=(b, t, u)))
    assert "no duplicate pair in either direction" in f
    assert "exactly 21 unordered pairs, each present once" in f


def test_self_loop_detected():
    b, t, u = frames()
    t.loc[0, "To"] = "HUB"
    assert "no self-loops" in failed(load_dataset(frames=(b, t, u)))


def test_two_hubs_detected_and_bad_coordinates_warned():
    b, t, u = frames()
    b.loc[1, "Role"] = "Hub"
    assert "exactly one declared hub" in failed(load_dataset(frames=(b, t, u)))
    b, t, u = frames()
    b.loc[2, "Latitude"] = 40.0
    d = load_dataset(frames=(b, t, u))
    # coordinates are not used by any algorithm: a bad one is a WARNING (map falls back to the schematic)
    assert d.valid and d.status == "warning"
    assert {c.name for c in d.checks if c.status == "warn"} == {"coordinates numeric and inside UAE range"}


def test_malformed_route_record_raises():
    import pytest
    b, t, u = frames()
    t["Minutes"] = t["Minutes"].astype(float)
    t.loc[2, "Minutes"] = None
    with pytest.raises(ValueError):
        eligible_routes(t, 38)
    # a genuinely empty record is dropped, not turned into a blank row
    t2 = frames()[1]
    t2.loc[len(t2)] = [None, None, None]
    assert len(eligible_routes(t2, 38)) == 13


def test_provenance_midpoints_match_times(ds):
    c = {c.name: c for c in ds.checks}["drive times trace to recorded Google Maps ranges"]
    assert c.status == "pass"


def test_hub_name_has_no_unsupported_hq_claim(ds):
    import re
    names = ds.branches["Name on Google Maps"].astype(str).tolist() + [ds.name(c) for c in ds.order]
    assert not any(re.search(r"\bHQ\b|headquarter|7X HQ", n, re.IGNORECASE) for n in names)
    assert {c.name: c for c in ds.checks}["no unsupported headquarters claim in branch names"].status == "pass"
    assert ds.name("HUB") == "Al Ramool (model hub)"


def test_zero_cost_and_unknown_upgrade_detected():
    b, t, u = frames()
    u.loc[0, "Cost_AED"] = 0
    u.loc[1, "Code"] = "ZZZ"
    f = failed(load_dataset(frames=(b, t, u)))
    assert "upgrade costs are positive AED" in f
    assert "upgrade codes are known branches (one per branch)" in f


def test_missing_file_is_reported(tmp_path):
    d = load_dataset(data_dir=tmp_path)
    assert d.status == "invalid" and not d.valid
