"""
promise_sync.py — keeps the internal transfer target in step with the selected hub (v2.4).

Changing the hub dropdown (Service coverage tab) now moves the target slider to that hub's suggested value
(src/advisor.py::suggest_promise). If the person then drags the slider themselves, their value is kept
(`promise_auto` = False) until they change the hub again, press "Use suggested target" or reset.
Changing the threshold X also refreshes the suggestion, but only while the target is still the automatic one.

Callbacks run before the script re-runs, so writing the slider's key here is allowed by Streamlit.
"""
from __future__ import annotations

import streamlit as st

from . import advisor as ad
from .data_loader import eligible_routes


def suggestion(ds, x: int, hub: str) -> dict:
    return ad.suggest_promise(ds.order, eligible_routes(ds.times, int(x)), hub)


def _apply(ds):
    sug = suggestion(ds, st.session_state["threshold_x"], st.session_state["selected_hub"])
    st.session_state["service_promise"] = int(sug["target"])
    st.session_state["promise_auto"] = True


def on_hub_change(ds):
    _apply(ds)


def on_x_change(ds):
    if st.session_state.get("promise_auto", True):
        _apply(ds)


def on_promise_manual():
    st.session_state["promise_auto"] = False


def use_suggested(ds):
    _apply(ds)
