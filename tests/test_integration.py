"""Whole-app tests with Streamlit's AppTest: shared state, unrehearsed inputs, no exceptions."""
import html
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def fresh():
    at = AppTest.from_file(APP, default_timeout=120)
    return at.run()


def text(at) -> str:
    return "\n".join(m.value for m in at.markdown) + "\n".join(c.value for c in at.caption)


def ok(at):
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def test_baseline_four_tabs_and_kpis():
    at = fresh()
    ok(at)
    assert [t.label for t in at.tabs] == ["Network", "Service coverage", "Investment", "Our working"]
    t = text(at)
    for s in ("334 min", "124 min", "62.9%", "2 / 6", "AED 411,960", "AED 765,000/yr", "AED 38,040",
              "DP beats greedy by AED 45,000/yr", "HANDWRITTEN TRACE REQUIRED", "Template — collect all five signatures"):
        assert s in t, s
    assert "Our working" in [t.label for t in at.tabs]


def test_shared_state_single_controls():
    at = fresh()
    # exactly one hub selector, one promise slider, one budget slider, one threshold slider
    assert len([s for s in at.selectbox if s.key == "selected_hub"]) == 1
    keys = [s.key for s in at.slider]  # at.slider already includes the sidebar
    assert keys.count("service_promise") == 1 and keys.count("threshold_x") == 1
    assert [s.key for s in at.select_slider].count("budget_aed") == 1


@pytest.mark.parametrize("x,expect", [(33, "11 routes"), (39, "outside the brief's 10–14 route rule"),
                                      (27, "Network NOT connected"), (10, "Network NOT connected")])
def test_thresholds(x, expect):
    at = fresh()
    at.slider(key="threshold_x").set_value(x).run()
    ok(at)
    t = text(at)
    assert expect in t or (x == 33 and "drive time < X = 33 min" in t)
    # baseline evidence run is unaffected by the live what-if
    assert "Visit order **HUB → KAR → QUS → UMS → JAF → SHJ → AJM**" in t
    if x == 27:
        assert "UNREACHABLE" in t or "unreachable" in t
        assert "minimum spanning forest" in t


@pytest.mark.parametrize("hub", ["JAF", "AJM", "KAR"])
def test_non_hub_sources_recalculate_everywhere(hub):
    at = fresh()
    at.selectbox(key="selected_hub").set_value(hub).run()
    ok(at)
    t = text(at)
    assert f"Fastest van paths from {hub}" not in t  # chart title is inside plotly, check other text instead
    assert f"Cheapest network ≠ fastest delivery (from {hub})" in t
    assert f"{hub} · " in t and "Inherited from Service coverage" in t
    assert "No costed option supplied" in t       # failing branches without a priced option are flagged


def test_promise_23_shared_with_investment():
    at = fresh()
    at.slider(key="service_promise").set_value(23).run()
    ok(at)
    t = text(at)
    assert "3 of 6" in t and "23 min" in t
    # UMS now passes, so its motorbike is not in the eligible pool
    assert "Express motorbike courier" not in [r for r in t.split("\n") if "DP spend" in r]


@pytest.mark.parametrize("budget", [0, 300_000, 450_000, 500_000, 600_000])
def test_budgets(budget):
    at = fresh()
    at.select_slider(key="budget_aed").set_value(budget).run()
    ok(at)
    t = text(at)
    assert f"Current budget" in t
    if budget == 500_000:
        assert "AED 481,860" in t and "AED 900,000/yr" in t and "AED 18,140" in t
    if budget == 0:
        assert "nothing fits" in t and "AED 0" in t


def test_edit_mode_and_scenario_view():
    at = fresh()
    at.toggle(key="t3_edit").set_value(True).run()
    ok(at)
    assert "Edited-assumption scenario" in text(at)
    at.toggle(key="t3_show_all").set_value(True).run()
    ok(at)


def test_reset_to_baseline():
    at = fresh()
    at.slider(key="threshold_x").set_value(30).run()
    at.selectbox(key="selected_hub").set_value("SHJ").run()
    at.sidebar.button[0].click().run()
    ok(at)
    assert at.session_state["threshold_x"] == 38 and at.session_state["selected_hub"] == "HUB"
    assert "Baseline scenario" in text(at)


# ---------------------------------------------------------------- refinement v2 checks
def all_text(at) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    parts += [str(o) for s in at.selectbox for o in s.options] + [str(o) for s in at.select_slider for o in s.options]
    return "\n".join(parts)


def test_evidence_summary_appears_before_panels():
    at = fresh()
    vals = [m.value for m in at.markdown]
    first_card = next(i for i, v in enumerate(vals) if "class='ev " in v)
    first_panel = next(i for i, v in enumerate(vals) if v.startswith("---\n#### 1 · DFS"))
    heading = next(i for i, v in enumerate(vals) if "Our working — evidence status" in v)
    assert heading < first_card < first_panel
    cards = [v for v in vals if "class='ev " in v]
    assert len(cards) == 4 and all("PENDING authentic handwritten scan" in c for c in cards)
    for name in ("Kushal", "Shashaank", "Siddal", "Joan"):
        assert any(name in c for c in cards)


def test_budget_display_uses_comma_grouping():
    at = fresh()
    ss = at.select_slider(key="budget_aed")
    opts = [str(o) for o in ss.options]
    for label in ("AED 0", "AED 30,000", "AED 450,000", "AED 600,000"):
        assert label in opts
    assert ss.value == 450_000                               # value stays a plain integer
    for v, label in [(0, "AED 0"), (30_000, "AED 30,000"), (600_000, "AED 600,000")]:
        ss.set_value(v).run()
        ok(at)
        assert label in text(at)


def test_route_tables_have_no_blank_rows():
    at = fresh()
    def route_tables():
        return [d.value for d in at.dataframe if "Route" in d.value.columns and "Minutes" in d.value.columns]
    t = route_tables()[0]
    assert len(t) == 13 and not t.isna().any().any()
    at.radio(key="t1_view").set_value("Minimum network (Kruskal)").run()
    t = route_tables()[0]
    assert len(t) == 6 and not t.isna().any().any()


def test_hub_label_has_no_unsupported_hq_claim_anywhere():
    at = fresh()
    txt = all_text(at)
    assert "7X HQ" not in txt and "HQ site" not in txt
    assert "Al Ramool (model hub)" in txt
    assert "not an existing Emirates Post customer-facing service" in txt
    assert "Selected model hub — Al Ramool / Umm Ramool" in txt


def test_23_minute_target_scenario_in_app():
    at = fresh()
    at.slider(key="service_promise").set_value(23).run()
    ok(at)
    t = text(at)
    assert "3 of 6" in t and "Current scenario" in t
    sens = [d.value for d in at.dataframe if "Scenario" in d.value.columns][0]
    cur = sens.iloc[0]
    assert cur["Target (min)"] == 23 and cur["Failing priced candidates"] == "JAF, SHJ, AJM"
    assert cur["Candidates' total first-year cost"] == "AED 411,960" and cur["All fit the budget?"] == "yes"
    assert cur["DP selection"] == cur["Greedy selection"] == "JAF, SHJ, AJM" and cur["DP − greedy (AED/yr)"] == "0"


def test_rationale_card_present_at_baseline():
    at = fresh()
    t = text(at)
    assert "Baseline target rationale" in t and "16–22 min" in t
    assert "cost AED 411,960, which fits the budget" in t and "DP beats greedy by AED 45,000/yr" in t
    assert "loosest" not in t


def test_edited_costs_change_the_investment_rationale():
    at = fresh()
    at.toggle(key="t3_edit").set_value(True).run()
    ok(at)
    assert "Cost/benefit edits are switched on" in text(at)
    sens = [d.value for d in at.dataframe if "Scenario" in d.value.columns][0]
    assert list(sens["Scenario"]) == ["Current target", "Next looser target"]


def test_offline_map_view_renders():
    at = fresh()
    at.radio(key="t1_diagram").set_value("Offline coordinate map").run()
    ok(at)
    assert "Local coordinate projection for visualisation" in text(at)
    assert "straight lines represent modelled links, not road geometry" in text(at)


# ---------------------------------------------------------------- v2.1 / v2.2 checks
def _kpis(at, label):
    """All KPI values with this exact label, in render order (Service coverage first, then Investment)."""
    out = []
    for m in at.markdown:
        out += re.findall(r"<div class='l'>" + re.escape(label) + r"</div><div class='v'>([^<]+)</div>", m.value)
    return out


def _kpi(at, label):
    v = _kpis(at, label)
    return v[0] if v else None


def _inv_kpi(at, label):
    """Investment-tab KPI (the last card with this label)."""
    v = _kpis(at, label)
    return v[-1] if v else None


def _disposition_table(at):
    for m in at.markdown:
        if "<th>DP: primary disposition</th>" in m.value:
            head = [html.unescape(h) for h in re.findall(r"<th>(.*?)</th>", m.value)]
            rows = re.findall(r"<tr class='[^']*'>(.*?)</tr>", m.value)
            return [dict(zip(head, [html.unescape(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r)])) for r in rows]
    return None


def _n(v):
    return int(v.split(" / ")[0])


def _reconcile(at):
    """Investment KPIs == counts derived from the rendered branch-level table (primary and intervention)."""
    rows = _disposition_table(at)
    n = len(rows)
    prim = [r["DP: primary disposition"] for r in rows]
    sel = [r["DP: selected upgrade"] for r in rows]
    assert _inv_kpi(at, "Direct hub-transfer branches within target") == f"{prim.count('DIRECT HUB TRANSFER WITHIN TARGET')} / {n}"
    assert _inv_kpi(at, "Outside selected service plan") == f"{prim.count('OUTSIDE SELECTED SERVICE PLAN')} / {n}"
    assert _inv_kpi(at, "Selected local-fulfilment upgrades") == f"{sum(x.endswith('— local fulfilment') for x in sel)} / {n}"
    assert _inv_kpi(at, "Modelled destinations with a service disposition") == \
        f"{n - prim.count('OUTSIDE SELECTED SERVICE PLAN')} / {n}"
    assert sum(prim.count(d) for d in set(prim)) == n                         # each destination counted exactly once
    return rows


def test_kpis_reconcile_with_disposition_table_at_baseline():
    at = fresh()
    rows = _reconcile(at)
    assert len(rows) == 6
    assert _inv_kpi(at, "Direct hub-transfer branches within target") == "2 / 6"
    assert _inv_kpi(at, "Selected local-fulfilment upgrades") == "3 / 6"
    assert _inv_kpi(at, "Outside selected service plan") == "1 / 6"
    assert _inv_kpi(at, "Alternative-mode branches within target (assumption)") == "0 / 6"
    assert _inv_kpi(at, "Modelled destinations with a service disposition") == "5 / 6"
    gr = {r["Branch"].split(" · ")[0]: r for r in rows}
    assert gr["UMS"]["Greedy: primary disposition"] == "ALTERNATIVE MODE WITHIN TARGET (ASSUMPTION)"
    assert gr["UMS"]["Greedy: selected upgrade"] == "Express motorbike courier — alternative mode, 18 min (assumption)"
    assert gr["AJM"]["Greedy: primary disposition"] == "OUTSIDE SELECTED SERVICE PLAN" and gr["AJM"]["Greedy: selected upgrade"] == "—"


def test_kpis_follow_hub_promise_and_budget_changes():
    at = fresh()
    at.slider(key="service_promise").set_value(23).run()
    ok(at)
    assert _inv_kpi(at, "Direct hub-transfer branches within target") == "3 / 6"
    _reconcile(at)
    at.select_slider(key="budget_aed").set_value(150_000).run()
    ok(at)
    _reconcile(at)
    assert _inv_kpi(at, "Selected local-fulfilment upgrades") == "1 / 6"
    at.selectbox(key="selected_hub").set_value("JAF").run()
    assert at.session_state["service_promise"] == 35        # v2.4: the target follows the hub (suggested value for JAF)
    at.slider(key="service_promise").set_value(23).run()    # back to the 23-min target this test was written for
    ok(at)
    assert _inv_kpi(at, "Direct hub-transfer branches within target") == "0 / 6"
    _reconcile(at)
    assert "Current scenario result" in text(at)


def test_threshold_change_recalculates_service_metrics():
    at = fresh()
    at.slider(key="threshold_x").set_value(27).run()                   # Ajman is cut off at X = 27
    ok(at)
    rows = _reconcile(at)
    ajm = [r for r in rows if r["Branch"].startswith("AJM")][0]
    assert ajm["Shortest hub-road time"] == "Unreachable" and ajm["Direct transfer (≤ target)"] == "no"


def test_jaf_hub_90_min_include_passing_counts_selected_interventions():
    """v2.2 regression: an already-passing branch can carry an optional local upgrade; the KPI counts the intervention."""
    at = fresh()
    at.selectbox(key="selected_hub").set_value("JAF").run()
    at.slider(key="service_promise").set_value(90).run()
    at.toggle(key="t3_show_all").set_value(True).run()
    ok(at)
    rows = _reconcile(at)
    by = {r["Branch"].split(" · ")[0]: r for r in rows}
    # both facts are displayed for SHJ: direct primary disposition AND a selected local-fulfilment upgrade
    assert by["SHJ"]["Direct transfer (≤ target)"] == "yes"
    assert by["SHJ"]["DP: primary disposition"] == "DIRECT HUB TRANSFER WITHIN TARGET"
    assert by["SHJ"]["DP: selected upgrade"] == "Sharjah mini-hub — local fulfilment"
    # the KPI is the selected-intervention count from the algorithm, not the LOCAL primary-disposition count
    n_local_sel = sum(r["DP: selected upgrade"].endswith("— local fulfilment") for r in rows)
    n_local_primary = sum(r["DP: primary disposition"] == "LOCAL FULFILMENT UPGRADE" for r in rows)
    assert _inv_kpi(at, "Selected local-fulfilment upgrades") == f"{n_local_sel} / 6"
    assert n_local_sel > n_local_primary
    # the UMS motorbike is selected but its time is not modelled from JAF -> not an alternative-mode pass
    assert "time not modelled" in by["UMS"]["DP: selected upgrade"]
    assert _inv_kpi(at, "Alternative-mode branches within target (assumption)").startswith("0 /")
    assert "on branches already direct" in text(at)


def test_service_tab_kpis_are_direct_transfer_only():
    at = fresh()
    assert _kpi(at, "Direct hub-transfer branches within target") == "2 / 6"     # Service coverage card (first match)
    t = text(at)
    assert "never change these travel times" in t
