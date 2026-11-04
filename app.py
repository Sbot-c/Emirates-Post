"""
THE NETWORK AUDIT — Emirates Post | Operations model (academic project)
DSA Final Project · Design and Analysis of Algorithms · MAIB

Single entry point:   streamlit run app.py

Exactly four tabs: Network · Service coverage · Investment · Our working.
One shared scenario state (threshold_x, selected_hub, service_promise, budget_aed) feeds every tab.
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="The Network Audit · Emirates Post", page_icon="📮", layout="wide",
                   initial_sidebar_state="expanded")

from src import promise_sync, tab_investment, tab_network, tab_service, working_tab  # noqa: E402
from src import ui_components as ui  # noqa: E402
from src.context import BASELINE, X_RANGE, build  # noqa: E402
from src.data_loader import DATA_DIR, load_dataset, read_sources  # noqa: E402


@st.cache_data(show_spinner=False)
def _read(data_dir: str, stamp: tuple):
    """Only immutable source-file reading is cached; the key includes file modification times."""
    return read_sources(data_dir)


def _stamp(d: Path) -> tuple:
    return tuple((p.name, p.stat().st_mtime_ns) for p in sorted(d.glob("*.csv")))


def _reset():
    for k, v in BASELINE.items():
        st.session_state[k] = v
    st.session_state["promise_auto"] = True      # v2.4: target follows the hub again


ui.inject_css()

# ---------------------------------------------------------------- data + validation
try:
    frames = _read(str(DATA_DIR), _stamp(DATA_DIR))
    ds = load_dataset(frames=frames)
except Exception as e:  # missing / unreadable file
    st.error(f"Data could not be read: {e}")
    st.stop()

# ---------------------------------------------------------------- shared state (initialise once)
for k, v in BASELINE.items():
    st.session_state.setdefault(k, v)
st.session_state.setdefault("promise_auto", True)   # v2.4: target follows the hub until the person overrides it
if ds.valid and st.session_state["selected_hub"] not in ds.order:
    st.session_state["selected_hub"] = ds.hub

# ---------------------------------------------------------------- sidebar: shared scenario controls
with st.sidebar:
    st.markdown("### Scenario controls")
    st.slider("Threshold X (route exists if drive time < X min)", *X_RANGE, step=1, key="threshold_x",
              help="Data Lead's baseline X = 38 (kept: X = 39 reaches no extra branch and breaks the 10–14 route rule — "
                   "see the threshold check on the Network tab). Shared by all tabs: one derived route list.",
              on_change=promise_sync.on_x_change, args=(ds,))
    st.markdown(
        "<div class='note'>Hub and internal transfer target are set on <b>Service coverage</b> (picking a hub suggests its "
        "target); budget on <b>Investment</b>. All tabs read the same values.</div>", unsafe_allow_html=True)
    st.button("↺ Reset all to baseline", on_click=_reset, width="stretch")
    st.markdown("---")
    tone = {"valid": "ok", "warning": "warn", "invalid": "bad"}[ds.status]
    st.markdown(f"**Data status** {ui.pill(ds.status.upper(), tone)}", unsafe_allow_html=True)
    with st.expander("Validation checks", expanded=ds.status != "valid"):
        for c in ds.checks:
            icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[c.status]
            st.markdown(f"{icon} {c.name} — <span class='note'>{c.detail}</span>", unsafe_allow_html=True)
    st.caption("Academic model built for the DSA Final Project (MAIB). Not an Emirates Post / 7X product; no corporate "
               "logo used.")

x = int(st.session_state["threshold_x"])
hub = st.session_state["selected_hub"]
promise = int(st.session_state["service_promise"])
budget = int(st.session_state["budget_aed"])

# ---------------------------------------------------------------- hero header
chips = [f"Threshold X = {x} min", f"Hub {hub} · {ds.name(hub)}", f"Internal transfer target {promise} min", f"Budget {ui.aed(budget)}",
         "Google Maps estimates · scheduled departure Thu 5 Nov 2026 07:00"]
if ds.valid:                      # v2.4: the hub we would recommend on the current route list (lowest total travel time)
    from src import advisor as _ad  # noqa: E402
    from src.data_loader import eligible_routes as _er  # noqa: E402
    _best = _ad.recommended_hub(ds.order, _er(ds.times, x))
    chips.append(f"Recommended hub: {_best} · {ds.name(_best)}")
base = (x, hub, promise, budget) == tuple(BASELINE.values())
st.markdown(
    "<div class='hero'><div class='eyebrow'>THE NETWORK AUDIT &nbsp;·&nbsp; EMIRATES POST | OPERATIONS MODEL</div>"
    "<div class='title'>Al Ramool hub · seven post offices · three decisions</div>"
    "<div class='q'>We are advising Emirates Post on how to maintain a connected, efficient inter-branch van network, "
    "test a proposed 20-minute internal hub-to-branch transfer target from the Al Ramool model hub, and allocate a "
    "first-year AED 450,000 upgrade budget to the branches with the strongest modelled annual gross fee opportunity.</div>"
    "<div class='q' style='font-size:.82rem;opacity:.8;margin-top:4px'>The 20-minute target is the group's planning "
    "assumption for this model — not an existing Emirates Post customer-facing service. Selected model hub — Al Ramool / "
    "Umm Ramool.</div><div class='meta'>"
    + "".join(f"<span class='chip{' rec' if c.startswith('Recommended hub') else '' if base else ' alt'}'>{c}</span>" for c in chips)
    + f"<span class='chip'>{'Baseline scenario' if base else 'What-if scenario (live)'}</span>"
    "</div></div>", unsafe_allow_html=True)
st.markdown(ui.team_roster_html(), unsafe_allow_html=True)

if not ds.valid:
    st.error("Input data failed validation — calculations are stopped so no plausible-looking but wrong numbers are shown. "
             "Open 'Validation checks' in the sidebar for the failed check.")
    st.stop()

sc = build(ds, x, hub, promise, budget)

t1, t2, t3, t4 = st.tabs(["Network", "Service coverage", "Investment", "Our working"])
with t1:
    tab_network.render(sc)
with t2:
    tab_service.render(sc)
with t3:
    tab_investment.render(sc)
with t4:
    working_tab.render(ds, sc)
