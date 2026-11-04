"""v2.4: changing the hub dropdown moves the target slider to that hub's suggested value (whole-app AppTest)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
SUGGESTED = {"HUB": 20, "KAR": 20, "QUS": 25, "UMS": 25, "JAF": 35, "SHJ": 30, "AJM": 40}


def fresh():
    return AppTest.from_file(APP, default_timeout=120).run()


def ok(at):
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def text(at) -> str:
    return "\n".join(m.value for m in at.markdown) + "\n".join(c.value for c in at.caption)


@pytest.mark.parametrize("hub,target", sorted(SUGGESTED.items()))
def test_hub_change_sets_suggested_target(hub, target):
    at = fresh()
    at.selectbox(key="selected_hub").set_value(hub).run()
    ok(at)
    assert at.session_state["service_promise"] == target
    assert at.slider(key="service_promise").value == target
    assert f"Suggested target for hub {hub}: {target} min" in text(at)


def test_manual_target_survives_until_hub_changes_again():
    at = fresh()
    at.selectbox(key="selected_hub").set_value("SHJ").run()
    at.slider(key="service_promise").set_value(33).run()
    ok(at)
    assert at.session_state["service_promise"] == 33 and at.session_state["promise_auto"] is False
    assert "your own target" in text(at)
    at.slider(key="threshold_x").set_value(39).run()                 # X change must not overwrite a manual choice
    assert at.session_state["service_promise"] == 33
    at.selectbox(key="selected_hub").set_value("HUB").run()          # …but a new hub takes the suggestion again
    assert at.session_state["service_promise"] == 20 and at.session_state["promise_auto"] is True


def test_threshold_change_refreshes_an_automatic_target():
    at = fresh()
    at.selectbox(key="selected_hub").set_value("AJM").run()          # 40 at X = 38
    assert at.session_state["service_promise"] == 40
    at.slider(key="threshold_x").set_value(39).run()                 # AJM now reaches HUB in 38 → still 40, rule re-run
    ok(at)
    assert at.session_state["service_promise"] == 40


def test_reset_restores_baseline_and_auto_mode():
    at = fresh()
    at.selectbox(key="selected_hub").set_value("JAF").run()
    at.slider(key="service_promise").set_value(50).run()
    at.sidebar.button[0].click().run()
    ok(at)
    assert at.session_state["service_promise"] == 20 and at.session_state["promise_auto"] is True


def test_threshold_check_keeps_x38_and_hub_chip_is_shown():
    at = fresh()
    ok(at)
    t = text(at)
    assert "X = 38 stays selected" in t and "outside the brief’s 10–14 band" in t
    assert "Recommended hub: HUB" in t
