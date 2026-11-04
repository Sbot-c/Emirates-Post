"""
ui_components.py — shared look-and-feel, charts and small widgets. Charts are Plotly, drawn
locally (no basemap tiles, no API keys), so the app works on classroom Wi-Fi.
"""
from __future__ import annotations

from math import inf

import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------- palette (master prompt §7.1)
BG, INK, TEAL, BLUE = "#F5F7FA", "#172B4D", "#138A83", "#3B82F6"
OK, AMBER, CORAL = "#16856B", "#E5A000", "#D95D55"
CARD, BORDER, MUTED, GREY = "#FFFFFF", "#E4EAF1", "#52606D", "#A7B1BE"

# Schematic layout from Shashaank's Kruskal_Network_X38.png (make_diagram.py): follows the real
# west–east / south–north order of the Google Maps pins, spread out so labels stay readable.
LAYOUT_PX = {"AJM": (695, 122), "SHJ": (585, 228), "QUS": (360, 243), "HUB": (448, 300),
             "UMS": (238, 387), "KAR": (375, 455), "JAF": (177, 561)}
POS = {c: (x / 100, -y / 100) for c, (x, y) in LAYOUT_PX.items()}
LABEL_SIDE = {"HUB": "middle right", "KAR": "bottom center", "QUS": "top left", "UMS": "middle left",
              "JAF": "bottom center", "SHJ": "middle right", "AJM": "top center"}

FONT = "Inter, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"   # system fonts only — no web-font request

CSS = f"""
<style>
html, body, [class*="css"], .stMarkdown, .stDataFrame {{ font-family: {FONT}; }}
.stApp {{ background: {BG}; }}
header[data-testid="stHeader"] {{ background: transparent; height: 2.6rem; }}
.block-container {{ padding-top: 3.4rem; padding-bottom: 3rem; max-width: 1440px; }}
h1, h2, h3, h4 {{ color: {INK}; letter-spacing: -0.01em; }}
.hero {{ background: linear-gradient(120deg, {INK} 0%, #1F3B63 60%, {TEAL} 140%); color: #fff;
        border-radius: 14px; padding: 18px 24px 16px; margin-bottom: 14px; }}
.hero .eyebrow {{ font-size: .72rem; letter-spacing: .16em; font-weight: 600; opacity: .85; }}
.hero .title {{ font-size: 1.75rem; font-weight: 700; margin: 2px 0 4px; }}
.hero .q {{ font-size: .98rem; opacity: .95; max-width: 1050px; line-height: 1.45; }}
.hero .meta {{ margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; }}
.chip {{ background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.25); border-radius: 999px;
        padding: 3px 11px; font-size: .80rem; white-space: nowrap; }}
.chip.alt {{ background: rgba(229,160,0,.25); border-color: rgba(229,160,0,.6); }}
.owner {{ display: inline-flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; background: {CARD}; border: 1px solid {BORDER};
         border-left: 5px solid {TEAL}; border-radius: 10px; padding: 7px 14px; font-size: .92rem;
         color: {INK}; margin: 2px 0 10px; }}
.owner b {{ color: {INK}; }}
.kpi {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 12px 14px 10px;
       height: 100%; }}
.kpi .l {{ font-size: .74rem; color: {MUTED}; text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }}
.kpi .v {{ font-size: 1.55rem; font-weight: 700; color: {INK}; line-height: 1.25; margin-top: 2px; }}
.kpi .s {{ font-size: .80rem; color: {MUTED}; margin-top: 2px; }}
.kpi.teal {{ border-top: 4px solid {TEAL}; }} .kpi.amber {{ border-top: 4px solid {AMBER}; }}
.kpi.coral {{ border-top: 4px solid {CORAL}; }} .kpi.blue {{ border-top: 4px solid {BLUE}; }}
.kpi.ok {{ border-top: 4px solid {OK}; }}
.card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 14px 18px; margin: 4px 0 12px; }}
.card h4 {{ margin: 0 0 6px; font-size: 1.02rem; }}
.note {{ font-size: .86rem; color: {MUTED}; }}
.pill {{ display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: .78rem; font-weight: 700;
        letter-spacing: .03em; }}
.pill.ok {{ background: #DDF3EC; color: #0E5E4B; }} .pill.bad {{ background: #FBE3E1; color: #8E2B25; }}
.pill.warn {{ background: #FDF0CF; color: #7A5600; }} .pill.grey {{ background: #E9EDF2; color: #3B4754; }}
.callout {{ border-radius: 10px; padding: 12px 16px; margin: 6px 0 12px; border: 1px solid {BORDER}; background: {CARD}; }}
.callout.amber {{ border-left: 5px solid {AMBER}; }} .callout.teal {{ border-left: 5px solid {TEAL}; }}
.callout.coral {{ border-left: 5px solid {CORAL}; }} .callout.blue {{ border-left: 5px solid {BLUE}; }}
.pending {{ border: 2px dashed {CORAL}; border-radius: 12px; background: repeating-linear-gradient(45deg,#FFF7F6,#FFF7F6 12px,#FFFFFF 12px,#FFFFFF 24px);
           padding: 28px 18px; text-align: center; color: #8E2B25; min-height: 220px; display: flex;
           flex-direction: column; justify-content: center; gap: 8px; }}
.pending .big {{ font-weight: 800; font-size: 1.05rem; letter-spacing: .02em; }}
.pending .small {{ font-size: .85rem; color: {MUTED}; }}
.ev {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 10px 14px; height: 100%; }}
.ev .t {{ font-weight: 700; color: {INK}; font-size: .95rem; }}
.ev .m {{ font-size: .82rem; color: {MUTED}; margin: 2px 0 6px; }}
.ev .d {{ font-size: .78rem; color: {MUTED}; margin-top: 6px; }}
.ev.pending-s {{ border-top: 4px solid {AMBER}; }} .ev.review-s {{ border-top: 4px solid {BLUE}; }}
.ev.bad-s {{ border-top: 4px solid {CORAL}; }} .ev.ok-s {{ border-top: 4px solid {OK}; }}
.stTabs [role="tablist"] {{ gap: 6px; background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
       padding: 5px; margin-bottom: 10px; }}
.stTabs [data-testid="stTab"] {{ border-radius: 9px !important; padding: 8px 22px !important; color: {MUTED}; }}
.stTabs [data-testid="stTab"] p {{ font-weight: 600; font-size: 1.0rem; }}
.stTabs [data-testid="stTab"][aria-selected="true"] {{ background: {INK} !important; }}
.stTabs [data-testid="stTab"][aria-selected="true"] p {{ color: #FFFFFF; }}
.stTabs .react-aria-SelectionIndicator {{ display: none; }}
div[data-testid="stExpander"] details {{ background: {CARD}; border-radius: 10px; border: 1px solid {BORDER}; }}
section[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {BORDER}; }}
.small-table td, .small-table th {{ padding: 4px 10px; font-size: .88rem; }}
table.ht {{ width: 100%; border-collapse: separate; border-spacing: 0; background: {CARD}; border: 1px solid {BORDER};
           border-radius: 10px; overflow: hidden; font-size: .86rem; margin: 4px 0 12px; }}
table.ht th {{ background: #EEF2F6; color: {INK}; text-align: left; padding: 7px 10px; font-weight: 600;
              border-bottom: 1px solid {BORDER}; white-space: nowrap; }}
table.ht td {{ padding: 6px 10px; border-bottom: 1px solid #F0F3F7; vertical-align: top; color: {INK}; }}
table.ht td.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
table.ht tr.ok td {{ background: #EAF6F3; }} table.ht tr.bad td {{ background: #FCEDEB; }}
table.ht tr:last-child td {{ border-bottom: none; }}
table.ht.wrap th, table.ht.wrap td {{ white-space: normal !important; }}
.scrollx {{ overflow-x: auto; }}
/* v2.3: project team roster (header, before the tabs) */
.team {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 8px 16px 8px; margin: 8px 0 4px; }}
.team .h {{ font-size: .74rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; color: {TEAL};
           margin-bottom: 2px; }}
.team .g {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 28px; }}
.team .m {{ display: flex; align-items: baseline; gap: 8px; padding: 3px 0; border-bottom: 1px dashed #EEF2F6;
           color: {INK}; font-size: .92rem; min-width: 0; }}
.team .m .i {{ color: {MUTED}; font-size: .8rem; width: 1.1rem; flex: none; }}
.team .m .r {{ background: #EEF2F6; color: {MUTED}; border-radius: 999px; padding: 1px 9px; font-size: .78rem;
              white-space: nowrap; }}
@media (max-width: 760px) {{ .team .g {{ grid-template-columns: 1fr; }} }}
/* v2.3.1: Our working → Dijkstra only — stack the hand-trace placeholder above the dashboard result when the panel
   itself is narrower than 760 px (e.g. an 820 px viewport with the sidebar open); desktop layout unchanged */
.st-key-ow_dijkstra_panel {{ container-type: inline-size; }}
@container (max-width: 760px) {{
  .st-key-ow_dijkstra_panel [data-testid="stHorizontalBlock"] {{ flex-direction: column; flex-wrap: nowrap; gap: .75rem; }}
  .st-key-ow_dijkstra_panel [data-testid="stColumn"] {{ width: 100% !important; flex: 1 1 auto !important; min-width: 0; }}
}}
/* v2.3: notebook baseline reference tag */
.nbtag {{ display: inline-block; background: #FFF6DD; color: #6B4E00; border: 1px solid {AMBER}; border-radius: 999px;
         padding: 2px 10px; font-size: .78rem; font-weight: 600; margin-right: 6px; }}
.nbref {{ margin-bottom: 6px; line-height: 1.7; }}
/* images: natural size, but never wider than their panel (aspect ratio kept) */
[data-testid="stImageContainer"] {{ max-width: 100%; }}
[data-testid="stImage"] img {{ max-width: 100% !important; height: auto !important; }}
/* v2.3: tab navigation never clips — labels wrap onto a second row instead of scrolling out of view */
@media (max-width: 1100px) {{
  .stTabs [role="tablist"] {{ flex-wrap: wrap; row-gap: 6px; overflow: visible !important; }}
  .stTabs [role="tablist"] [data-testid="stTab"] {{ flex: 0 0 auto; }}
}}
/* ------------------------------------------------------------------ v2.4 look-and-feel layer */
:root {{ --shadow-sm: 0 1px 2px rgba(23,43,77,.06), 0 4px 14px rgba(23,43,77,.06); --shadow-md: 0 2px 4px rgba(23,43,77,.08), 0 10px 28px rgba(23,43,77,.10); }}
.stApp {{ background: radial-gradient(1200px 500px at 85% -120px, #E6F3F2 0%, rgba(230,243,242,0) 70%), {BG}; }}
.hero {{ position: relative; overflow: hidden; box-shadow: var(--shadow-md); padding: 22px 28px 18px;
        background: radial-gradient(520px 260px at 92% -10%, rgba(19,138,131,.55) 0%, rgba(19,138,131,0) 70%),
                    radial-gradient(380px 200px at 6% 120%, rgba(59,130,246,.35) 0%, rgba(59,130,246,0) 70%),
                    linear-gradient(120deg, {INK} 0%, #1F3B63 62%, #14585C 130%); }}
.hero::after {{ content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .07;
               background-image: repeating-linear-gradient(135deg, #fff 0 1px, transparent 1px 14px); }}
.hero .title {{ font-size: 1.9rem; letter-spacing: -0.015em; }}
.chip {{ backdrop-filter: blur(2px); }}
.chip.rec {{ background: rgba(22,133,107,.35); border-color: rgba(120,230,200,.7); font-weight: 600; }}
.kpi, .card, .ev, .team, .callout {{ box-shadow: var(--shadow-sm); }}
.kpi {{ transition: transform .15s ease, box-shadow .15s ease; }}
.kpi:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
.kpi .v {{ font-variant-numeric: tabular-nums; letter-spacing: -0.015em; }}
.callout {{ border-radius: 12px; line-height: 1.5; }}
.callout.blue {{ background: linear-gradient(90deg, #F2F7FF 0%, {CARD} 60%); }}
.callout.teal {{ background: linear-gradient(90deg, #EFF9F8 0%, {CARD} 60%); }}
.callout.amber {{ background: linear-gradient(90deg, #FFF8E6 0%, {CARD} 60%); }}
.callout.coral {{ background: linear-gradient(90deg, #FFF1F0 0%, {CARD} 60%); }}
[data-testid="stPlotlyChart"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; padding: 6px 8px 2px;
                                box-shadow: var(--shadow-sm); overflow: hidden; }}
[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 10px; overflow: hidden; box-shadow: var(--shadow-sm); }}
div[data-testid="stMarkdownContainer"] h3 {{ font-weight: 750; margin-top: .6rem; }}
div[data-testid="stMarkdownContainer"] h4 {{ font-weight: 700; padding-left: 12px; border-left: 4px solid {TEAL};
                                            margin-top: 1.1rem; }}
.stButton > button, .stDownloadButton > button {{ border-radius: 10px; border: 1px solid {BORDER}; font-weight: 600;
        background: {CARD}; color: {INK}; box-shadow: var(--shadow-sm); transition: all .15s ease; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: {TEAL}; color: {TEAL}; transform: translateY(-1px);
        box-shadow: var(--shadow-md); }}
[data-testid="stWidgetLabel"] p {{ font-weight: 600; color: {INK}; }}
section[data-testid="stSidebar"] h3 {{ font-size: 1.05rem; letter-spacing: .02em; }}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{ background: linear-gradient(180deg, #FFFFFF 0%, #F7FAFB 100%); }}
.stTabs [data-testid="stTab"] {{ transition: background .15s ease, color .15s ease; }}
.stTabs [data-testid="stTab"]:hover {{ background: #EEF2F6; color: {INK}; }}
.stTabs [data-testid="stTab"][aria-selected="true"]:hover {{ background: {INK} !important; }}
[data-baseweb="tab-panel"] {{ animation: fadein .25s ease; }}
@keyframes fadein {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: none; }} }}
table.ht tbody tr:hover td {{ background: #F5F9FC; }} table.ht tr.ok:hover td {{ background: #DDF0EB; }} table.ht tr.bad:hover td {{ background: #F9DEDB; }}
table.ht {{ box-shadow: var(--shadow-sm); }}
.nbref {{ display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; }}
::-webkit-scrollbar {{ height: 9px; width: 9px; }} ::-webkit-scrollbar-thumb {{ background: #CBD5E0; border-radius: 6px; }}
/* v2.4.1 polish */
.kpi {{ border-top: 3px solid {TEAL}; }}
.stTabs [role="tablist"] {{ gap: 6px; border-bottom: 1px solid {BORDER}; padding-bottom: 6px; }}
.stTabs [data-testid="stTab"] {{ border-radius: 999px; padding: 6px 16px; font-weight: 600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}
div[data-baseweb="slider"] [role="slider"] {{ box-shadow: 0 0 0 4px rgba(19,138,131,.18); }}
div[data-baseweb="select"] > div {{ border-radius: 10px; }}
[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 12px; background: {CARD}; box-shadow: var(--shadow-sm); }}
.block-container {{ padding-top: 1.6rem; max-width: 1280px; }}
@media (prefers-reduced-motion: reduce) {{ .kpi, .stButton > button, [data-baseweb="tab-panel"] {{ transition: none; animation: none; }} }}
</style>
"""


TEAM = [("Kushal", "Data Lead"), ("Shashaank", "Network Analyst"), ("Siddal", "Routing Analyst"),
        ("Joan", "Investment Analyst"), ("Sparsh", "Integration & Business Lead")]


def team_roster_html() -> str:
    """Project Team overview: the five members and roles exactly as specified, in order."""
    import html as _h
    items = "".join(f"<div class='m'><span class='i'>{i}.</span><b>{_h.escape(n)}</b><span class='r'>{_h.escape(r)}</span></div>"
                    for i, (n, r) in enumerate(TEAM, 1))
    return f"<div class='team' role='region' aria-label='Project Team'><div class='h'>Project Team</div><div class='g'>{items}</div></div>"


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def aed(x) -> str:
    return f"AED {int(round(x)):,}"


def minutes(x) -> str:
    return "Unreachable" if x is None or x == inf else f"{int(x)} min"


def owner_badge(name: str, role: str, algo: str):
    st.markdown(f"<div class='owner'>👤 Tab owner: <b>{name}</b> · {role} · <span class='note'>{algo}</span></div>",
                unsafe_allow_html=True)


def kpi_row(items: list):
    """items = [(label, value, sub, accent)]"""
    cols = st.columns(len(items))
    for col, (label, value, sub, accent) in zip(cols, items):
        col.markdown(f"<div class='kpi {accent}'><div class='l'>{label}</div><div class='v'>{value}</div>"
                     f"<div class='s'>{sub}</div></div>", unsafe_allow_html=True)


def callout(html: str, tone: str = "teal"):
    st.markdown(f"<div class='callout {tone}'>{html}</div>", unsafe_allow_html=True)


def pill(text: str, tone: str) -> str:
    return f"<span class='pill {tone}'>{text}</span>"


def status_pill(status: str) -> str:
    return {"PASS": pill("✓ PASS", "ok"), "FAIL": pill("✗ FAIL", "bad"),
            "UNREACHABLE": pill("⊘ UNREACHABLE", "grey")}.get(status, pill(status, "grey"))


# ---------------------------------------------------------------- network diagram
def _label_xy(a, b, t=0.5):
    (x1, y1), (x2, y2) = POS[a], POS[b]
    return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t


# label positions nudged along a few edges whose midpoints collide on this layout
LABEL_T = {frozenset(("HUB", "UMS")): 0.30, frozenset(("KAR", "QUS")): 0.30, frozenset(("QUS", "AJM")): 0.55}


def network_figure(order, routes, title: str, edge_styles: dict, node_text: dict, node_colour: dict,
                   legend: list, height: int = 520):
    """edge_styles[frozenset((a,b))] = dict(colour, width, dash, label, opacity, group).
    legend = [(name, colour, dash, width)] — drawn as dummy traces so the legend is explicit."""
    fig = go.Figure()
    for (a, b, m) in routes[["From", "To", "Minutes"]].itertuples(index=False, name=None):
        s = edge_styles.get(frozenset((a, b)))
        if s is None:
            continue
        (x1, y1), (x2, y2) = POS[a], POS[b]
        fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode="lines", showlegend=False, hoverinfo="skip",
                                 opacity=s.get("opacity", 1.0),
                                 line=dict(color=s["colour"], width=s["width"], dash=s.get("dash", "solid"))))
        lx, ly = _label_xy(a, b, LABEL_T.get(frozenset((a, b)), 0.5))
        fig.add_annotation(x=lx, y=ly, text=s.get("label", f"{m}"), showarrow=False,
                           font=dict(size=12, color=s.get("label_colour", INK), family=FONT),
                           bgcolor="rgba(255,255,255,0.92)", borderpad=2)
        fig.add_trace(go.Scatter(x=[lx], y=[ly], mode="markers", marker=dict(size=14, opacity=0),
                                 showlegend=False, hovertemplate=s.get("hover", f"{a}–{b}: {m} min") + "<extra></extra>"))
    for name, colour, dash, width in legend:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name=name,
                                 line=dict(color=colour, dash=dash, width=width)))
    xs = [POS[c][0] for c in order]
    ys = [POS[c][1] for c in order]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text", showlegend=False,
        marker=dict(size=[40 if c == order[0] else 34 for c in order], color=[node_colour.get(c, "#FFFFFF") for c in order],
                    line=dict(color=INK, width=2.2)),
        text=[f"<b>{c}</b>" for c in order], textposition="middle center",
        textfont=dict(color=["#FFFFFF" if node_colour.get(c, "#FFFFFF") not in ("#FFFFFF",) else INK for c in order],
                      size=11, family=FONT),
        hovertext=[node_text.get(c, c) for c in order], hoverinfo="text"))
    for c in order:
        x, y = POS[c]
        dx, dy, xa = {"middle right": (0.32, 0, "left"), "middle left": (-0.32, 0, "right"),
                      "bottom center": (0, -0.42, "center"), "top center": (0, 0.40, "center"),
                      "top left": (-0.15, 0.40, "right")}[LABEL_SIDE[c]]
        fig.add_annotation(x=x + dx, y=y + dy, text=node_text.get(c, c), showarrow=False, xanchor=xa,
                           font=dict(size=12, color=INK, family=FONT), bgcolor="rgba(245,247,250,0.85)")
    fig.update_layout(
        title=dict(text=title, x=0.01, y=0.985, yanchor="top", font=dict(size=15, color=INK, family=FONT)),
        height=height, margin=dict(l=10, r=10, t=95, b=10), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(visible=False, range=[0.2, 8.4]), yaxis=dict(visible=False, range=[-6.4, -0.75]),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0.0, bgcolor="rgba(255,255,255,0.9)",
                    font=dict(size=12, family=FONT)),
        hoverlabel=dict(font=dict(family=FONT)))
    return fig


# ---------------------------------------------------------------- service bar chart
def service_bar_chart(df, promise: int, hub: str):
    """df: Code, Area, Minutes (None = unreachable), Status, Path."""
    reach = df[df["Status"] != "UNREACHABLE"]
    xmax = max([promise] + reach["Minutes"].tolist()) * 1.18 + 2 if len(reach) else promise * 1.5
    labels = [f"{c} · {a}" for c, a in zip(df["Code"], df["Area"])]
    order = labels[::-1]  # fastest at top
    fig = go.Figure()
    for status, name, colour in [("PASS", "Within transfer target", OK), ("FAIL", "Outside transfer target", CORAL)]:
        sub = df[df["Status"] == status]
        if len(sub):
            fig.add_trace(go.Bar(
                x=sub["Minutes"], y=[f"{c} · {a}" for c, a in zip(sub["Code"], sub["Area"])], orientation="h",
                name=name, marker_color=colour, text=[f"{int(m)} min" for m in sub["Minutes"]],
                textposition="outside", cliponaxis=False, customdata=sub["Path"],
                hovertemplate="%{y}<br>%{x} min<br>%{customdata}<extra>" + name + "</extra>"))
    un = df[df["Status"] == "UNREACHABLE"]
    if len(un):
        fig.add_trace(go.Bar(x=[xmax * 0.97] * len(un), y=[f"{c} · {a}" for c, a in zip(un["Code"], un["Area"])],
                             orientation="h", name="Unreachable (no route under X)", marker_color="#E9EDF2",
                             marker_pattern_shape="/", marker_line=dict(color=GREY, width=1),
                             text=["Unreachable"] * len(un), textposition="inside", insidetextanchor="middle",
                             hovertemplate="%{y}<br>Unreachable — no van route under X<extra></extra>"))
    fig.add_vline(x=promise, line_color=AMBER, line_width=3, line_dash="dash")
    fig.add_annotation(x=promise, y=1.0, yref="paper", yanchor="bottom", text=f"Target {promise} min (within if ≤)",
                       showarrow=False, font=dict(color="#7A5600", size=12, family=FONT), xanchor="center", bgcolor="#FDF0CF")
    fig.update_layout(
        title=dict(text=f"Shortest van time from {hub} vs the {promise}-min internal target", x=0.01,
                   font=dict(size=15, color=INK, family=FONT)),
        height=400, margin=dict(l=10, r=30, t=70, b=95), barmode="overlay", bargap=0.35,
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="Shortest travel time from selected hub (minutes)", range=[0, xmax], gridcolor="#EEF2F6",
                   ticksuffix=""),
        yaxis=dict(title="Branch", categoryorder="array", categoryarray=order),
        legend=dict(orientation="h", yanchor="top", y=-0.25, x=0),
        font=dict(family=FONT, color=INK))
    return fig


# ---------------------------------------------------------------- investment chart
def investment_chart(steps: list, budget: int):
    """steps = compressed [(budget_aed, dp_benefit, greedy_benefit)]."""
    xs = [s[0] for s in steps]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[s[1] for s in steps], mode="lines", line_shape="hv", name="Dynamic programming optimum",
                             line=dict(color=TEAL, width=3.2),
                             hovertemplate="Budget AED %{x:,.0f}<br>DP optimum AED %{y:,.0f}/yr<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[s[2] for s in steps], mode="lines", line_shape="hv", name="Greedy heuristic",
                             line=dict(color=BLUE, width=2.4, dash="dash"),
                             hovertemplate="Budget AED %{x:,.0f}<br>Greedy AED %{y:,.0f}/yr<extra></extra>"))
    fig.add_vline(x=budget, line_color=AMBER, line_width=3, line_dash="dot")
    fig.add_annotation(x=budget, y=1.0, yref="paper", text=f"Current budget {aed(budget)}", showarrow=False,
                       xanchor="right" if budget > 420_000 else "left", font=dict(color="#7A5600", size=12, family=FONT),
                       bgcolor="#FDF0CF")
    ymax = max([s[1] for s in steps] + [1]) * 1.15
    fig.update_layout(
        title=dict(text="Modelled annual benefit by budget — DP optimum vs greedy", x=0.01,
                   font=dict(size=15, color=INK, family=FONT)),
        height=400, margin=dict(l=20, r=20, t=55, b=40), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="Budget (AED)", tickformat=",.0f", range=[0, max(xs) if xs else 600_000], gridcolor="#EEF2F6"),
        yaxis=dict(title="Estimated annual gross fee/revenue<br>opportunity (AED/year)", tickformat=",.0f",
                   range=[0, ymax], gridcolor="#EEF2F6"),
        legend=dict(orientation="h", yanchor="top", y=-0.17, x=0), font=dict(family=FONT, color=INK),
        hovermode="x unified")
    return fig


def html_table(df, num_cols=(), row_class=None, max_height=None, wrap=False):
    """Readable wrapping table (Streamlit's grid truncates long text). row_class(row) -> 'ok' | 'bad' | ''."""
    import html as _h
    head = "".join(f"<th>{_h.escape(str(c))}</th>" for c in df.columns)
    body = []
    for _, r in df.iterrows():
        cls = row_class(r) if row_class else ""
        tds = "".join(f"<td class='{'num' if c in num_cols else ''}' style='{'' if len(str(v)) > 28 else 'white-space:nowrap'}'>{_h.escape('' if v is None or (isinstance(v, float) and v != v) else str(v))}</td>"
                      for c, v in r.items())
        body.append(f"<tr class='{cls}'>{tds}</tr>")
    style = f" style='max-height:{max_height}px;overflow-y:auto'" if max_height else ""
    st.markdown(f"<div class='scrollx'{style}><table class='ht{" wrap" if wrap else ""}'><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>",
                unsafe_allow_html=True)


# ---------------------------------------------------------------- v2.4: hub ranking + threshold check charts
def hub_rank_chart(rank, selected: str, recommended: str):
    """Average shortest travel time from each candidate hub (rank = advisor.rank_hubs() frame, best first)."""
    hubs = rank["Hub"].tolist()
    vals = [float(v) if v == v and v is not None else 0.0 for v in rank["Average (min)"]]
    colours = [TEAL if h == recommended else BLUE if h == selected else GREY for h in hubs]
    fig = go.Figure(go.Bar(x=hubs, y=vals, marker_color=colours, text=[f"{v:.1f}" for v in vals], textposition="outside",
                           cliponaxis=False, customdata=rank["Suggested target (min)"],
                           hovertemplate="%{x}<br>average %{y:.1f} min to the other six<br>suggested target %{customdata} min"
                                         "<extra></extra>"))
    fig.update_layout(
        title=dict(text="Average shortest van time to the other six offices, by hub (lower is better)", x=0.01,
                   font=dict(size=14, color=INK, family=FONT)),
        height=300, margin=dict(l=10, r=10, t=55, b=30), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="Candidate hub (teal = recommended, blue = selected)", categoryorder="array", categoryarray=hubs),
        yaxis=dict(title="minutes", gridcolor="#EEF2F6", range=[0, (max(vals) if vals else 1) * 1.2]),
        font=dict(family=FONT, color=INK), showlegend=False)
    return fig


def threshold_route_chart(audit, selected_x: int, candidate_x: int):
    """Routes surviving at each X, with the brief's 10–14 band shaded (audit = advisor.threshold_audit())."""
    xs = audit["X (min)"].tolist()
    colours = [OK if b else CORAL for b in audit["In 10–14 band"]]
    fig = go.Figure(go.Bar(x=xs, y=audit["Routes"], marker_color=colours, text=audit["Routes"], textposition="outside",
                           cliponaxis=False,
                           hovertemplate="X = %{x}<br>%{y} routes<extra></extra>"))
    fig.add_hrect(y0=9.5, y1=14.5, fillcolor=TEAL, opacity=0.10, line_width=0)
    fig.add_annotation(x=selected_x, y=1.0, yref="paper", yanchor="bottom", text=f"selected X = {selected_x}",
                       showarrow=False, bgcolor="#DDF3EC", font=dict(color="#0E5E4B", size=11, family=FONT))
    fig.update_layout(
        title=dict(text="Routes surviving at each X (shaded = the brief's 10–14 band)", x=0.01,
                   font=dict(size=14, color=INK, family=FONT)),
        height=300, margin=dict(l=10, r=10, t=60, b=30), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="Threshold X (min)", dtick=1), yaxis=dict(title="routes", gridcolor="#EEF2F6", range=[0, 20]),
        font=dict(family=FONT, color=INK), showlegend=False)
    return fig


def threshold_time_chart(audit, selected_x: int):
    """What the recommended hub gets at each X: total travel time and slowest branch."""
    xs = audit["X (min)"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=audit["Slowest branch (min)"], mode="lines+markers", name="Slowest branch (min)",
                             line=dict(color=CORAL, width=3), hovertemplate="X = %{x}<br>slowest %{y} min<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[v / 3 for v in audit["Total hub travel (min)"]], mode="lines+markers",
                             name="Total hub travel ÷ 3 (min)", line=dict(color=BLUE, width=3, dash="dot"),
                             customdata=audit["Total hub travel (min)"],
                             hovertemplate="X = %{x}<br>total hub travel %{customdata} min<extra></extra>"))
    fig.add_vline(x=selected_x, line_color=TEAL, line_width=2, line_dash="dash")
    fig.update_layout(
        title=dict(text="Travel time from the recommended hub — faster at 39, but reach is already 6 of 6", x=0.01,
                   font=dict(size=14, color=INK, family=FONT)),
        height=300, margin=dict(l=10, r=10, t=60, b=30), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="Threshold X (min)", dtick=1), yaxis=dict(title="minutes", gridcolor="#EEF2F6"),
        legend=dict(orientation="h", yanchor="top", y=-0.28, x=0), font=dict(family=FONT, color=INK))
    return fig


# ---------------------------------------------------------------- offline coordinate map
UAE_LAT, UAE_LON = (22.5, 26.5), (51.0, 56.5)
MAP_LABEL_POS = {"HUB": "bottom right", "KAR": "top left", "QUS": "middle right", "UMS": "middle left",
                 "JAF": "middle right", "SHJ": "middle left", "AJM": "middle right"}   # manual offsets around the HUB/KAR/QUS cluster


def validate_coordinates(branches) -> tuple[bool, str]:
    """Every branch needs a numeric latitude/longitude inside the UAE box, and no two branches may share
    a position. Returns (ok, message)."""
    import pandas as pd
    lat = pd.to_numeric(branches.get("Latitude"), errors="coerce")
    lon = pd.to_numeric(branches.get("Longitude"), errors="coerce")
    if lat is None or lon is None or lat.isna().any() or lon.isna().any():
        return False, "A branch latitude/longitude is missing or not numeric, so the coordinate map is not drawn."
    if not (lat.between(*UAE_LAT).all() and lon.between(*UAE_LON).all()):
        return False, "A branch coordinate falls outside the UAE, so the coordinate map is not drawn."
    if len({(round(a, 4), round(b, 4)) for a, b in zip(lat, lon)}) < len(lat):
        return False, "Two branches share the same coordinates, so the coordinate map cannot distinguish them."
    return True, ""


KM_PER_DEG = 111.32


def project_km(branches, order):
    """Local equirectangular projection for visualisation (not survey-grade):
        x_km = 111.32 · cos(lat_ref) · (lon − lon_ref),   y_km = 111.32 · (lat − lat_ref)
    with the reference at the centroid of the validated branch coordinates."""
    import math
    b = branches.set_index("Code")
    lat_ref = float(b.loc[order, "Latitude"].astype(float).mean())
    lon_ref = float(b.loc[order, "Longitude"].astype(float).mean())
    k = math.cos(math.radians(lat_ref))
    return {c: (KM_PER_DEG * k * (float(b.loc[c, "Longitude"]) - lon_ref), KM_PER_DEG * (float(b.loc[c, "Latitude"]) - lat_ref))
            for c in order}, (lat_ref, lon_ref)


def coordinate_map(ds, routes, title, edge_styles: dict, node_colour: dict, legend: list, kept=None, height=640):
    """Offline coordinate map on a local km projection with EQUAL aspect (1 km east = 1 km north on screen).
    Plotly Scatter traces only (no tiles, no geo layers, no network requests). Returns (figure, None) or
    (None, reason) when coordinates fail validation — the caller then falls back to the schematic."""
    ok, msg = validate_coordinates(ds.branches)
    if not ok:
        return None, msg
    b = ds.branches.set_index("Code")
    pos, _ref = project_km(ds.branches, ds.order)
    fig = go.Figure()
    for (a, c, m) in routes[["From", "To", "Minutes"]].itertuples(index=False, name=None):
        s = edge_styles.get(frozenset((a, c)))
        if s is None:
            continue
        (x1, y1), (x2, y2) = pos[a], pos[c]
        status = "" if kept is None else (" · Kruskal: ACCEPTED" if frozenset((a, c)) in kept else " · Kruskal: REJECTED (loop)")
        fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode="lines", showlegend=False, hoverinfo="skip",
                                 opacity=s.get("opacity", 1.0),
                                 line=dict(color=s["colour"], width=s["width"], dash=s.get("dash", "solid"))))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        fig.add_annotation(x=mx, y=my, text=s.get("label", str(m)), showarrow=False, bgcolor="rgba(255,255,255,0.9)",
                           font=dict(size=11, color=s.get("label_colour", INK), family=FONT), borderpad=1)
        fig.add_trace(go.Scatter(x=[mx], y=[my], mode="markers", marker=dict(size=14, opacity=0), showlegend=False,
                                 hovertemplate=f"{a}–{c}: {m} min{status}<extra></extra>"))
    for name, colour, dash, width in legend:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name=name, line=dict(color=colour, dash=dash, width=width)))
    disp = b["Name on Google Maps"].astype(str).to_dict()
    for c in ds.order:
        x, y = pos[c]
        lat, lon = float(b.loc[c, "Latitude"]), float(b.loc[c, "Longitude"])
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode="markers+text", showlegend=False, cliponaxis=False, text=[f"<b>{c}</b> · {ds.name(c)}"],
            textposition=MAP_LABEL_POS.get(c, "top center"), textfont=dict(size=12, color=INK, family=FONT),
            marker=dict(size=22 if c == ds.hub else 15, color=node_colour.get(c, "#FFFFFF"),
                        symbol="star" if c == ds.hub else "circle", line=dict(color=INK, width=2)),
            hovertemplate=(f"<b>{c}</b> — {disp.get(c, c)}<br>{b.loc[c, 'Area']}, {b.loc[c, 'Emirate']}<br>"
                           f"lat {lat:.5f}, lon {lon:.5f}<br>projected: {x:+.1f} km E, {y:+.1f} km N<extra></extra>")))
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    fig.update_layout(
        title=dict(text=title, x=0.01, y=0.985, yanchor="top", font=dict(size=15, color=INK, family=FONT)),
        height=height, margin=dict(l=60, r=20, t=95, b=50), plot_bgcolor="#FBFCFE", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="East–west offset (km)", range=[min(xs) - 12, max(xs) + 22], gridcolor="#EEF2F6",
                   zeroline=False, constrain="domain"),
        yaxis=dict(title="North–south offset (km)", range=[min(ys) - 4, max(ys) + 4], gridcolor="#EEF2F6",
                   zeroline=False, scaleanchor="x", scaleratio=1, constrain="domain"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.0, font=dict(size=12, family=FONT)),
        font=dict(family=FONT, color=INK))
    return fig, None


# ---------------------------------------------------------------- knapsack DP heatmap
def knapsack_heatmap(K, names, labels, units, path, title="0/1 knapsack DP grid", height=420):
    """Colour-graded DP grid built directly from the matrix K returned by investment_core.knapsack.
    Rows = stages (0 = no upgrades, then each option in order); columns = every capacity 0..W.
    Cell values are shown in AED '000 (K is in AED). Traceback cells are outlined and marked."""
    W = len(K[0]) - 1
    thousands = all(v % 1000 == 0 for row in K for v in row)
    z = [[v / 1000 for v in row] for row in K]
    ylab = ["0 — no upgrades"] + [f"{i} — {n} (cost {c})" for i, (n, c) in enumerate(zip(names, units), 1)]
    on_path = {(i, w): t for i, w, t in path}
    hover = []
    for i, row in enumerate(K):
        hrow = []
        for w, v in enumerate(row):
            if i == 0:
                dec = "— (no upgrades considered)"
            else:
                dec = (f"take {names[i - 1]}" if K[i][w] != K[i - 1][w] else f"skip {names[i - 1]}")
            tb = ("yes — " + ("TAKE" if on_path[(i, w)] else "SKIP")) if (i, w) in on_path else "no"
            hrow.append([ylab[i], w, f"{v / 1000:,.0f}" if thousands else f"{v / 1000:,.1f}", tb, dec])
        hover.append(hrow)
    fig = go.Figure(go.Heatmap(
        z=z, x=list(range(W + 1)), y=ylab, customdata=hover,
        colorscale=[[0, "#F5F7FA"], [0.35, "#CFEAE6"], [0.7, "#6FC1B8"], [1, TEAL]],
        texttemplate="%{z:.0f}" if thousands else "%{z:.1f}", textfont=dict(size=8.5, family=FONT),
        xgap=1, ygap=1, colorbar=dict(title=dict(text="Best annual gross benefit proxy (AED '000)", side="top"),
                                      orientation="h", thickness=10, len=0.45, x=1, xanchor="right", y=-0.42,
                                      yanchor="top", tickformat=",.0f"),
        hovertemplate=("Stage: %{customdata[0]}<br>Capacity w = %{customdata[1]} units<br>"
                       "DP value: AED %{customdata[2]}k<br>On traceback: %{customdata[3]}<br>"
                       "Cell decision: %{customdata[4]}<extra></extra>")))
    for (i, w), took in on_path.items():
        fig.add_shape(type="rect", x0=w - 0.5, x1=w + 0.5, y0=i - 0.5, y1=i + 0.5,
                      line=dict(color=AMBER if took else INK, width=3.5), fillcolor="rgba(0,0,0,0)")
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Traceback: TAKE (amber outline)",
                             marker=dict(symbol="square-open", size=13, color=AMBER, line=dict(width=3))))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Traceback: SKIP (navy outline)",
                             marker=dict(symbol="square-open", size=13, color=INK, line=dict(width=3))))
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(size=15, color=INK, family=FONT)),
        height=height, margin=dict(l=10, r=10, t=70, b=110), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        xaxis=dict(title="Budget capacity (AED 10,000 units)", tickmode="linear", tick0=0, dtick=5,
                   range=[-0.5, W + 0.5], showgrid=False, zeroline=False),
        yaxis=dict(title="Item stage", autorange="reversed", showgrid=False, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.45), font=dict(family=FONT, color=INK))
    return fig


def evidence_card(title, member, role, state, detail):
    tone = {"PENDING": ("pending-s", "warn"), "NEEDS REVIEW": ("bad-s", "bad"),
            "FILE PRESENT — REVIEW REQUIRED": ("review-s", "grey"), "INCOMPLETE": ("review-s", "warn"),
            "MISMATCH": ("bad-s", "bad"), "MATCHES TRANSCRIPTION": ("ok-s", "ok")}.get(state, ("review-s", "grey"))
    return (f"<div class='ev {tone[0]}'><div class='t'>{title}</div><div class='m'>{member} · {role}</div>"
            f"{pill(state, tone[1])}<div class='d'>{detail}</div></div>")
