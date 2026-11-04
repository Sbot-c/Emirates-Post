"""
trace_visuals.py — Python-generated plots and tables for the four hand-trace panels in *Our working* (v2.4).

Every figure is drawn LIVE with Matplotlib from the same fixed baseline run the panels use (X = 38, HUB, 20 min,
AED 450,000): nothing is a stored image and nothing is typed in. They are computer output, labelled as such in the
app, and never count as handwriting evidence. No Streamlit in here (PNG bytes are returned), so the module is
testable on its own.

    dfs_figure(sc)        network with DFS visit numbers + stack-depth / visited-count chart
    kruskal_figure(sc)    network with accepted / rejected routes + running-total step chart
    dijkstra_figure(sc)   shortest-path tree vs the target + round-by-round distance heat table
    knapsack_figure(inv)  cost vs benefit per option (+ benefit/cost ratio) and DP vs greedy budget sweep
    summary_table(...)    one-row-per-algorithm key-results table
"""
from __future__ import annotations

import io
import re
from math import inf

import matplotlib

matplotlib.use("Agg")                                   # headless: no display needed
from matplotlib import rcParams                          # noqa: E402
from matplotlib.figure import Figure                     # noqa: E402  (object API, no pyplot: thread-safe under Streamlit)
from matplotlib.lines import Line2D                      # noqa: E402
from matplotlib.patches import Patch, Rectangle          # noqa: E402
import pandas as pd                                      # noqa: E402

from . import investment_core as ic                      # noqa: E402
from . import routing_core as rc                         # noqa: E402

INK, TEAL, BLUE, OK, AMBER, CORAL = "#172B4D", "#138A83", "#3B82F6", "#16856B", "#E5A000", "#D95D55"
GREY, MUTED, BORDER = "#A7B1BE", "#52606D", "#E4EAF1"

# Same schematic layout as ui_components.LAYOUT_PX (kept in step by tests/test_trace_visuals.py); y is flipped for Matplotlib.
LAYOUT_PX = {"AJM": (695, 122), "SHJ": (585, 228), "QUS": (360, 243), "HUB": (448, 300),
             "UMS": (238, 387), "KAR": (375, 455), "JAF": (177, 561)}
POS = {c: (x / 100, -y / 100) for c, (x, y) in LAYOUT_PX.items()}

rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": BORDER, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.titleweight": "bold",
                     "axes.titlecolor": INK, "axes.titlesize": 11})


def _png(fig, dpi: int = 160) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    return buf.getvalue()


def _frame(ax):
    ax.set_aspect("equal")
    ax.axis("off")
    xs, ys = zip(*POS.values())
    ax.set_xlim(min(xs) - 0.7, max(xs) + 0.7)
    ax.set_ylim(min(ys) - 0.55, max(ys) + 0.55)


def _edge(ax, a, b, colour, lw, ls="-", z=1, alpha=1.0):
    (x1, y1), (x2, y2) = POS[a], POS[b]
    ax.plot([x1, x2], [y1, y2], color=colour, lw=lw, ls=ls, zorder=z, alpha=alpha, solid_capstyle="round")


LABEL_T = {frozenset(("HUB", "UMS")): 0.30, frozenset(("KAR", "QUS")): 0.30, frozenset(("QUS", "AJM")): 0.55,
           frozenset(("HUB", "SHJ")): 0.45, frozenset(("QUS", "SHJ")): 0.40, frozenset(("KAR", "SHJ")): 0.60,
           frozenset(("QUS", "UMS")): 0.45}          # nudges so crossing routes keep readable labels


def _edge_label(ax, a, b, text, colour=MUTED, t=None, bold=False, bg="white"):
    t = LABEL_T.get(frozenset((a, b)), 0.5) if t is None else t
    (x1, y1), (x2, y2) = POS[a], POS[b]
    ax.text(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, text, ha="center", va="center", fontsize=7.5,
            color=colour, fontweight="bold" if bold else "normal", zorder=4,
            bbox=dict(boxstyle="round,pad=0.15", fc=bg, ec="none", alpha=0.95))


def _node(ax, c, face, text="", edge=INK, ring=None, tcolour="white"):
    x, y = POS[c]
    if ring:
        ax.scatter([x], [y], s=1250, c=ring, zorder=5, edgecolors="none")
    ax.scatter([x], [y], s=860, c=face, zorder=6, edgecolors=edge, linewidths=1.4)
    ax.text(x, y, text or c, ha="center", va="center", fontsize=8.5, fontweight="bold", color=tcolour, zorder=7)


def _routes(sc):
    return [(a, b, int(m)) for a, b, m in sc.routes[["From", "To", "Minutes"]].itertuples(index=False, name=None)]


# ------------------------------------------------------------------------------------------------ DFS
def dfs_figure(sc) -> bytes:
    order, tree = sc.dfs["visit_order"], sc.dfs["tree"]
    tree_set = {frozenset(e) for e in tree}
    fig = Figure(figsize=(11.5, 4.6))
    ax, ax2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1.25, 1]})
    _frame(ax)
    for a, b, m in _routes(sc):
        if frozenset((a, b)) in tree_set:
            _edge(ax, a, b, TEAL, 3.6, z=2)
            _edge_label(ax, a, b, str(m), "#0B5E59", bold=True)
        else:
            _edge(ax, a, b, GREY, 1.3, ls=(0, (4, 3)), z=1, alpha=0.9)
            _edge_label(ax, a, b, str(m), MUTED)
    for n, c in enumerate(order, 1):
        _node(ax, c, BLUE if n == 1 else TEAL, f"{c}\n#{n}")
    ax.set_title(f"DFS from {order[0]}: visit order (#) and tree edges", loc="left")
    ax.legend(handles=[Line2D([0], [0], color=TEAL, lw=3.6, label="tree edge (first visit)"),
                       Line2D([0], [0], color=GREY, lw=1.3, ls=(0, (4, 3)), label="other route (already visited)")],
              loc="lower right", fontsize=8, frameon=False)

    steps = sc.dfs["steps"]
    depth = [len(str(s["Stack after"]).split(">")) if s["Stack after"] != "(empty)" else 0 for s in steps]
    xs = [s["Step"] for s in steps]
    ax2.step(xs, depth, where="post", color=BLUE, lw=2.4, label="stack depth")
    ax2.plot(xs, [s["Visited"] for s in steps], color=OK, lw=2.4, marker="o", ms=4, label="branches visited")
    for s, d in zip(steps, depth):
        if str(s["Action"]).startswith("Backtrack"):
            ax2.scatter([s["Step"]], [d], c=CORAL, s=34, zorder=5)
    ax2.set_xlabel("trace step")
    ax2.set_ylabel("count")
    ax2.set_ylim(-0.3, max(7, max(depth)) + 0.8)
    ax2.set_xticks(xs)
    ax2.grid(color="#EEF2F6")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.set_title("Stack depth and branches visited, step by step", loc="left")
    ax2.legend(handles=[Line2D([0], [0], color=BLUE, lw=2.4, label="stack depth"),
                        Line2D([0], [0], color=OK, lw=2.4, marker="o", ms=4, label="branches visited"),
                        Line2D([0], [0], marker="o", color="w", mfc=CORAL, ms=6, label="backtrack (pop)")],
               loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    return _png(fig)


# ------------------------------------------------------------------------------------------------ Kruskal
def kruskal_figure(sc) -> bytes:
    steps = sc.kruskal["steps"]
    acc = {s["Route"].replace("–", "-"): s["Order"] for s in steps if s["Decision"] == "ACCEPT"}
    fig = Figure(figsize=(11.5, 4.6))
    ax, ax2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1.25, 1]})
    _frame(ax)
    order_of = {s["Route"].replace("–", "-"): s["Order"] for s in steps}
    for a, b, m in _routes(sc):
        key = f"{a}-{b}"
        if key in acc:
            _edge(ax, a, b, TEAL, 4.2, z=2)
            _edge_label(ax, a, b, f"#{order_of[key]} · {m}", "#0B5E59", bold=True, bg="#DDF3EC")
        else:
            _edge(ax, a, b, CORAL, 1.5, ls=(0, (4, 3)), z=1, alpha=0.85)
            _edge_label(ax, a, b, f"#{order_of[key]} · {m} ✗", "#8E2B25", bg="#FBE3E1")
    for c in POS:
        _node(ax, c, "white", c, tcolour=INK, edge=BLUE if c == sc.hub else INK)
    ax.set_title(f"Kruskal: {len(acc)} routes kept = {sc.kruskal['total']} min "
                 f"(all {len(sc.routes)} routes = {sc.summary['total_all']} min)", loc="left")
    ax.legend(handles=[Line2D([0], [0], color=TEAL, lw=4.2, label="accepted (#order · minutes)"),
                       Line2D([0], [0], color=CORAL, lw=1.5, ls=(0, (4, 3)), label="rejected — would close a loop")],
              loc="lower right", fontsize=8, frameon=False)

    xs = [s["Order"] for s in steps]
    colours = [TEAL if s["Decision"] == "ACCEPT" else CORAL for s in steps]
    ax2.bar(xs, [s["Minutes"] for s in steps], color=colours, width=0.62, alpha=0.9)
    for s in steps:
        ax2.text(s["Order"], 0.8, s["Route"].replace("–", "-"), rotation=90, ha="center", va="bottom",
                 fontsize=7, color="white", fontweight="bold")
    ax3 = ax2.twinx()
    ax3.step(xs, [s["Running total (min)"] for s in steps], where="post", color=INK, lw=2.2)
    ax3.set_ylabel("running total of accepted minutes", color=INK)
    tot = sc.kruskal["total"]
    ax3.set_ylim(-tot * 0.5, tot * 1.2)                  # lifts the line clear of the route labels inside the bars
    ax3.set_yticks([v for v in range(0, int(tot * 1.2) + 1, 20)])
    ax2.set_ylim(0, max(s["Minutes"] for s in steps) * 1.45)
    ax2.set_xticks(xs)
    ax2.set_xlabel("routes tried in order (cheapest first)")
    ax2.set_ylabel("route minutes")
    ax2.set_title("Route minutes in the order tried; line = running total", loc="left")
    ax2.spines[["top"]].set_visible(False)
    ax3.spines[["top"]].set_visible(False)
    ax2.legend(handles=[Patch(color=TEAL, label="accept"), Patch(color=CORAL, label="reject (loop)"),
                        Line2D([0], [0], color=INK, lw=2.2, label="running total")], loc="upper left", fontsize=8,
               frameon=False)
    fig.tight_layout()
    return _png(fig)


# ------------------------------------------------------------------------------------------------ Dijkstra
def _parse_cell(v) -> tuple:
    """'✔ 13' -> (13, True); '∞' -> (inf, False)."""
    s = str(v)
    settled = s.startswith("✔")
    m = re.search(r"\d+", s)
    return (float(m.group()) if m else inf), settled


def dijkstra_figure(sc) -> bytes:
    res, order, hub, target = sc.dijkstra, sc.ds.order, sc.hub, sc.promise
    dist = res["dist"]
    fig = Figure(figsize=(11.5, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1])
    ax, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    _frame(ax)
    tree, tied = set(), set()
    for n in order:
        if n != hub and dist[n] < inf:
            for i, p in enumerate(rc.all_shortest_paths(res["preds"], hub, n)):
                (tree if i == 0 else tied).update(frozenset(e) for e in zip(p, p[1:]))
    tied -= tree
    for a, b, m in _routes(sc):
        key = frozenset((a, b))
        if key in tree:
            _edge(ax, a, b, INK, 3.4, z=2)
        elif key in tied:
            _edge(ax, a, b, AMBER, 2.8, ls=(0, (1, 2)), z=2)
        else:
            _edge(ax, a, b, GREY, 1.3, ls=(0, (4, 3)), z=1)
        _edge_label(ax, a, b, str(m), INK if key in tree else "#7A5600" if key in tied else MUTED, bold=key in tree or key in tied)
    for c in order:
        if c == hub:
            _node(ax, c, BLUE, f"{c}\nhub")
        elif dist[c] == inf:
            _node(ax, c, "#E9EDF2", f"{c}\n∞", tcolour=INK)
        else:
            ok = dist[c] <= target
            _node(ax, c, OK if ok else CORAL, f"{c}\n{int(dist[c])}", ring="#DDF3EC" if ok else "#FBE3E1")
    ax.set_title(f"Shortest-path tree from {hub} (node = minutes)", loc="left")
    ax.legend(handles=[Line2D([0], [0], marker="o", color="w", mfc=OK, ms=9, label=f"within {target} min"),
                       Line2D([0], [0], marker="o", color="w", mfc=CORAL, ms=9, label=f"outside {target} min"),
                       Line2D([0], [0], color=INK, lw=3.4, label="fastest-path edge"),
                       Line2D([0], [0], color=AMBER, lw=2.8, ls=(0, (1, 2)), label="equal-time alternative")],
              loc="lower right", fontsize=8, frameon=False)

    # round-by-round heat table (the same numbers as the hand-trace table)
    steps = res["steps"]
    cols = order
    grid = [[_parse_cell(s[c]) for c in cols] for s in steps]
    finite = [v for row in grid for v, _ in row if v < inf]
    vmax = max(finite) if finite else 1.0
    ax2.set_xlim(0, len(cols))
    ax2.set_ylim(len(steps), 0)
    cmap = matplotlib.colormaps["YlGnBu_r"]
    for r, row in enumerate(grid):
        for c, (v, settled) in enumerate(row):
            if v == inf:
                ax2.add_patch(Rectangle((c, r), 1, 1, fc="#F3F5F8", ec="white", hatch="///", lw=1.2))
                ax2.text(c + 0.5, r + 0.5, "∞", ha="center", va="center", color=MUTED, fontsize=10)
            else:
                ax2.add_patch(Rectangle((c, r), 1, 1, fc=cmap(0.15 + 0.7 * v / vmax), ec="white", lw=1.2))
                ax2.text(c + 0.5, r + 0.5, f"{int(v)}", ha="center", va="center", fontsize=10,
                         color="white" if v / vmax < 0.45 else INK, fontweight="bold" if settled else "normal")
            if settled:
                ax2.add_patch(Rectangle((c + 0.04, r + 0.04), 0.92, 0.92, fc="none", ec=INK, lw=1.6))
    ax2.set_xticks([i + 0.5 for i in range(len(cols))])
    ax2.set_xticklabels(cols, fontsize=9, fontweight="bold")
    ax2.xaxis.tick_top()
    ax2.set_yticks([i + 0.5 for i in range(len(steps))])
    ax2.set_yticklabels([f"{s['Round']}: settle {s['Settle'].split()[0]}" for s in steps], fontsize=8.5)
    ax2.tick_params(length=0)
    for sp in ax2.spines.values():
        sp.set_visible(False)
    ax2.set_title("Known shortest time after each round (boxed = settled)", loc="left", y=1.1)
    fig.tight_layout()
    return _png(fig)


# ------------------------------------------------------------------------------------------------ knapsack
def knapsack_figure(inv: dict, budget: int) -> bytes:
    names, cost, ben = inv["names"], inv["cost"], inv["benefit"]
    dp, gr = set(inv["dp"]["picks"]), set(inv["greedy"]["picks"])
    fig = Figure(figsize=(11.5, 4.5))
    ax, ax2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1, 1.1]})
    idx = sorted(range(len(names)), key=lambda i: -(ben[i] / cost[i]))      # greedy order: best ratio first
    xs = range(len(idx))
    w = 0.38
    ax.bar([x - w / 2 for x in xs], [cost[i] / 1000 for i in idx], w, color=BLUE, label="first-year cost")
    ax.bar([x + w / 2 for x in xs], [ben[i] / 1000 for i in idx], w, color=TEAL, label="annual benefit proxy")
    for x, i in zip(xs, idx):
        tag = ("DP ✔ " if i in dp else "") + ("greedy ✔" if i in gr else "")
        ax.text(x, max(cost[i], ben[i]) / 1000 + 12, f"ratio {ben[i] / cost[i]:.2f}\n{tag.strip() or 'not selected'}",
                ha="center", va="bottom", fontsize=7.6, color=INK)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([names[i] for i in idx], fontweight="bold")
    ax.set_ylabel("AED '000")
    ax.set_ylim(0, max(max(cost), max(ben)) / 1000 * 1.38)
    ax.grid(axis="y", color="#EEF2F6")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Options sorted by benefit ÷ cost (the greedy order)", loc="left")
    ax.legend(fontsize=8, frameon=False, loc="upper right")

    scan = ic.scan_budgets(inv["units"], ben, inv["unit"])
    b = [s[0] / 1000 for s in scan]
    ax2.step(b, [s[1] / 1000 for s in scan], where="post", color=TEAL, lw=2.8, label="DP optimum")
    ax2.step(b, [s[2] / 1000 for s in scan], where="post", color=BLUE, lw=2.0, ls="--", label="greedy")
    ax2.axvline(budget / 1000, color=AMBER, lw=2.2, ls=":")
    ax2.text(budget / 1000 - 6, 8, f"budget AED {budget:,}", rotation=90, ha="right", va="bottom", fontsize=8, color="#7A5600")
    ax2.set_xlabel("budget (AED '000)")
    ax2.set_ylabel("annual benefit proxy (AED '000/yr)")
    ax2.grid(color="#EEF2F6")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.set_title(f"DP vs greedy by budget (gap at AED {budget:,}: "
                  f"{(inv['dp']['benefit'] - inv['greedy']['benefit']) / 1000:,.0f}k/yr)", loc="left")
    ax2.legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout()
    return _png(fig)


# ------------------------------------------------------------------------------------------------ tables
def summary_table(sc, inv, trace) -> pd.DataFrame:
    """One row per algorithm: what was run, the headline result, and the integrity checks the code performed."""
    hc, hb, K, hbest, hchosen, _ = trace
    n = inv["names"]
    d = sc.dijkstra["dist"]
    fails = [c for c in sc.ds.order if c != sc.hub and d[c] > sc.promise]
    return pd.DataFrame([
        {"Algorithm": "DFS (Kushal)", "Input": f"X = {sc.x}, start {sc.hub}",
         "Headline result": f"visit order {' → '.join(sc.dfs['visit_order'])}; {sc.dfs['visited']}/{sc.dfs['total']} reached",
         "Check performed": "stack trace rebuilt from NetworkX dfs_labeled_edges; preorder equals tree edges"},
        {"Algorithm": "Kruskal (Shashaank)", "Input": f"{len(sc.routes)} routes under X = {sc.x}",
         "Headline result": f"{len(sc.kruskal['accepted'])} routes kept = {sc.kruskal['total']} min vs {sc.summary['total_all']} min "
                            f"for all ({sc.summary['saving_pct']:.1f}% less edge-time)",
         "Check performed": f"replay identical to NetworkX minimum_spanning_edges: {'yes' if sc.kruskal['networkx_verified'] else 'NO'}"},
        {"Algorithm": "Dijkstra (Siddal)", "Input": f"source {sc.hub}, target {sc.promise} min (≤ passes)",
         "Headline result": f"{len(sc.ds.order) - 1 - len(fails)} of {len(sc.ds.order) - 1} within target; outside: {', '.join(fails) or 'none'}",
         "Check performed": f"teaching trace equals NetworkX distances: {'yes' if sc.dijkstra['trace_matches_networkx'] else 'NO'}"},
        {"Algorithm": "0/1 knapsack (Joan)", "Input": f"{', '.join(n)}; budget AED {sc.budget:,} = {hb} units",
         "Headline result": f"DP picks {' + '.join(n[i] for i in inv['dp']['picks'])} (AED {inv['dp']['benefit']:,}/yr proxy); "
                            f"greedy AED {inv['greedy']['benefit']:,}/yr; K[{len(hc)}][{hb}] = {hbest // 1000}k",
         "Check performed": f"brute force over {2 ** len(n)} combinations agrees: {'yes' if inv['brute_force']['agrees'] else 'NO'}"},
    ])


def trace_tables(sc, inv, trace) -> dict:
    """CSV-ready answer-key tables (computer output) keyed by panel."""
    return {"dfs": pd.DataFrame(sc.dfs["steps"]),
            "kruskal": pd.DataFrame(sc.kruskal["steps"]),
            "dijkstra": pd.DataFrame(sc.dijkstra["steps"]),
            "knapsack": pd.DataFrame(ic.traceback_rows(trace[2], trace[5], inv["names"], trace[0]))}
