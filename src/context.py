"""
context.py — the single application-level scenario state shared by every tab.

    threshold_x     baseline 38   (Data Lead's threshold; edge rule Minutes < X)
    selected_hub    baseline HUB  (source for Dijkstra; Investment tab inherits it)
    service_promise baseline 20   (owned by the Service coverage tab; Investment tab reads it)
    budget_aed      baseline 450,000 (owned by the Investment tab)

Every tab receives the SAME derived edge list and the SAME Dijkstra result, so the tabs can never
be put into contradictory states. Calculations are recomputed on every run (nothing is cached
except reading the immutable CSV files).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import network_core as nc
from . import routing_core as rc
from .data_loader import Dataset, eligible_routes

BASELINE = {"threshold_x": 38, "selected_hub": "HUB", "service_promise": 20, "budget_aed": 450_000}
X_RANGE = (10, 66)            # 66 admits all 21 pairs (longest pair is 65 min)
PROMISE_RANGE = (10, 90)
ROUTE_BAND = (10, 14)         # brief: choose X so that 10–14 routes survive


@dataclass
class Scenario:
    ds: Dataset
    x: int
    hub: str
    promise: int
    budget: int
    routes: pd.DataFrame
    adj: dict
    dfs: dict
    comps: list
    kruskal: dict
    summary: dict
    dijkstra: dict

    @property
    def connected(self) -> bool:
        return len(self.comps) == 1

    @property
    def is_baseline(self) -> bool:
        return (self.x, self.hub, self.promise, self.budget) == tuple(BASELINE.values())

    @property
    def band_ok(self) -> bool:
        return ROUTE_BAND[0] <= len(self.routes) <= ROUTE_BAND[1]


def build(ds: Dataset, x: int, hub: str, promise: int, budget: int) -> Scenario:
    routes = eligible_routes(ds.times, x)
    adj = nc.adjacency(ds.order, routes)
    d = nc.dfs(ds.order, routes, ds.hub)         # connectivity is always checked from the declared hub
    comps = nc.components(ds.order, routes)
    k = nc.kruskal(ds.order, routes)
    return Scenario(ds, x, hub, promise, budget, routes, adj, d, comps, k, nc.summarise(routes, k),
                    rc.dijkstra(ds.order, routes, hub))
