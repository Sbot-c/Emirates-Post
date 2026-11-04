"""v2.3: Project Team overview, tab/panel ownership, and the X = 38 threshold criterion (QUS–AJM link)."""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import network_core as nc
from src import ui_components as ui
from src.data_loader import eligible_routes

ROOT = Path(__file__).resolve().parent.parent
TEAM = [("Kushal", "Data Lead"), ("Shashaank", "Network Analyst"), ("Siddal", "Routing Analyst"),
        ("Joan", "Investment Analyst"), ("Sparsh", "Integration & Business Lead")]


@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    return at


def test_team_roster_exact_names_roles_and_order(app):
    assert ui.TEAM == TEAM
    md = [m.value for m in app.markdown]
    roster = [v for v in md if "aria-label='Project Team'" in v]
    assert len(roster) == 1 and "Project Team" in roster[0]
    found = re.findall(r"<b>([^<]+)</b><span class='r'>([^<]+)</span>", roster[0])
    assert [(n, r.replace("&amp;", "&")) for n, r in found] == TEAM
    assert "Sparsh Saraya" not in roster[0]


def test_roster_sits_between_header_and_tabs(app):
    md = [m.value for m in app.markdown]
    i_hero = next(i for i, v in enumerate(md) if "<div class='hero'>" in v)
    i_team = next(i for i, v in enumerate(md) if "aria-label='Project Team'" in v)
    i_tab1 = next(i for i, v in enumerate(md) if "Tab owner: <b>Shashaank</b>" in v)
    assert i_hero < i_team < i_tab1


def test_tab_owners(app):
    t = "\n".join(m.value for m in app.markdown)
    assert "Tab owner: <b>Shashaank</b> · Network Analyst" in t
    assert "Tab owner: <b>Siddal</b> · Routing Analyst" in t
    assert "Tab owner: <b>Joan</b> · Investment Analyst" in t
    assert "Assembled and integrated by <b>Sparsh</b> · Integration & Business Lead" in t
    assert "Tab owner: <b>Kushal" not in t                       # Kushal owns data/DFS, not the Network tab


def test_responsive_roster_css():
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in ui.CSS
    assert re.search(r"@media \(max-width: 760px\) \{ \.team \.g \{ grid-template-columns: 1fr; \}", ui.CSS)
    assert 'flex-wrap: wrap' in ui.CSS and '[role="tablist"]' in ui.CSS            # tabs wrap instead of clipping


def test_qus_ajm_threshold_criterion(ds):
    t = {frozenset((a, b)): m for a, b, m in zip(ds.times.From, ds.times.To, ds.times.Minutes)}
    assert t[frozenset(("QUS", "AJM"))] == 37
    assert sorted(tuple(sorted(k)) for k, m in t.items() if m == 38) == [("AJM", "HUB"), ("HUB", "JAF")]
    keys = lambda x: {frozenset((a, b)) for a, b in zip(eligible_routes(ds.times, x).From, eligible_routes(ds.times, x).To)}
    r37, r38, r39 = keys(37), keys(38), keys(39)
    assert frozenset(("QUS", "AJM")) not in r37 and frozenset(("QUS", "AJM")) in r38
    assert len(r37) == 12 and len(r38) == 13 and len(r39) == 15
    assert r39 - r38 == {frozenset(("HUB", "JAF")), frozenset(("HUB", "AJM"))}
    tbl = nc.threshold_table(ds.order, ds.times, 26, 40)
    band = tbl[tbl["In 10–14 band"] & tbl["Connected"]]["X (min)"].tolist()
    assert 38 in band and len(band) > 1                     # other thresholds also qualify — 38 is chosen for QUS–AJM
    # the only X that admits the 37-min link AND excludes the 38-min links
    assert [x for x in range(10, 67) if frozenset(("QUS", "AJM")) in keys(x) and frozenset(("HUB", "JAF")) not in keys(x)] == [38]
    # at X = 37 Ajman hangs on Sharjah alone (bridge); at X = 38 it has a second route
    b37 = {frozenset(e[:2]) for e in nc.robustness(ds.order, eligible_routes(ds.times, 37))["bridges"]}
    assert frozenset(("SHJ", "AJM")) in b37
    assert nc.robustness(ds.order, eligible_routes(ds.times, 38))["bridges"] == []


def test_threshold_text_states_exact_criterion(app):
    t = "\n".join(m.value for m in app.markdown)
    assert "smallest whole-minute threshold that admits the 37-minute QUS–AJM link" in t
    assert "not on being the smallest or largest valid X" in t
    assert "Largest X satisfying" not in t
