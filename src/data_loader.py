"""
data_loader.py — one validated loader for the canonical data/ directory.

Owner of the data: Kushal (Data Lead). Owner of upgrades.csv: Joan (Investment Analyst).
Integration: the Integration & Business Lead.

Nothing in here computes a dashboard answer. It reads the three source files, checks them,
and builds the eligible-route list from the full 21-pair time table with the single shared
rule  Minutes < threshold_x.  routes_X38_reference.csv is kept only as an export/reference
of the Data Lead's X = 38 list and is never read by the app.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

BRANCH_COLS = ["Code", "Name on Google Maps", "Area", "Emirate", "Role", "Latitude", "Longitude",
               "Google place ID"]
TIME_COLS = ["From", "To", "Minutes"]
UPGRADE_COLS = ["Code", "Upgrade", "Cost_AED", "Benefit_AED", "Minutes_after", "Benefit_reason",
                "Cost_basis"]

# plausible UAE bounding box for the coordinate check
UAE_LAT, UAE_LON = (22.5, 26.5), (51.0, 56.5)

SHORT_NAME = {"HUB": "Al Ramool (model hub)", "KAR": "Karama", "QUS": "Al Qusais", "UMS": "Umm Suqeim",
              "JAF": "Jebel Ali (JAFZA)", "SHJ": "Sharjah Central", "AJM": "Ajman Central"}


@dataclass
class Check:
    name: str
    status: str          # "pass" | "warn" | "fail"
    detail: str


@dataclass
class Dataset:
    branches: pd.DataFrame
    times: pd.DataFrame
    upgrades: pd.DataFrame
    order: list            # branch codes in matrix order (file order) — the documented neighbour order
    hub: str               # the declared hub (Role == Hub)
    checks: list = field(default_factory=list)

    @property
    def status(self) -> str:
        s = {c.status for c in self.checks}
        return "invalid" if "fail" in s else ("warning" if "warn" in s else "valid")

    @property
    def valid(self) -> bool:
        return self.status != "invalid"

    def name(self, code: str) -> str:
        return SHORT_NAME.get(code, code)


def read_sources(data_dir: Path | str = DATA_DIR):
    d = Path(data_dir)
    return (pd.read_csv(d / "branches.csv"), pd.read_csv(d / "times.csv"),
            pd.read_csv(d / "upgrades.csv"))


def eligible_routes(times: pd.DataFrame, threshold_x: int) -> pd.DataFrame:
    """THE single shared edge rule used by every tab: a van route exists only if Minutes < X.
    Stable sort by minutes keeps the file order for ties (documented tie rule)."""
    rec = times[TIME_COLS].dropna(how="all")                      # genuinely empty records only
    if rec.isna().any().any():
        raise ValueError("malformed route record (missing From/To/Minutes) in times.csv")
    r = rec[rec["Minutes"] < threshold_x].copy()
    r["FileOrder"] = r.index
    return r.sort_values(["Minutes", "FileOrder"], kind="stable").reset_index(drop=True)


def validate(branches: pd.DataFrame, times: pd.DataFrame, upgrades: pd.DataFrame) -> list:
    out: list[Check] = []

    def add(name, ok, detail, level="fail"):
        out.append(Check(name, "pass" if ok else level, detail))

    # ---- branches
    missing = [c for c in BRANCH_COLS if c not in branches.columns]
    add("branches.csv columns", not missing, "all present" if not missing else f"missing {missing}")
    if missing:
        return out
    codes = branches["Code"].astype(str).tolist()
    add("7 unique branch codes", len(codes) == 7 and len(set(codes)) == 7, f"{len(set(codes))} unique of {len(codes)}")
    hubs = branches.loc[branches["Role"].astype(str).str.lower() == "hub", "Code"].tolist()
    add("exactly one declared hub", len(hubs) == 1, f"hub = {hubs}")
    lat = pd.to_numeric(branches["Latitude"], errors="coerce")
    lon = pd.to_numeric(branches["Longitude"], errors="coerce")
    ok_coord = lat.notna().all() and lon.notna().all() and lat.between(*UAE_LAT).all() and lon.between(*UAE_LON).all()
    add("coordinates numeric and inside UAE range", bool(ok_coord),
        f"lat {lat.min():.3f}–{lat.max():.3f}, lon {lon.min():.3f}–{lon.max():.3f}" if ok_coord
        else "bad or missing coordinate — the coordinate map falls back to the schematic", level="warn")
    hq = [c for c, n in zip(codes, branches["Name on Google Maps"].astype(str))
          if re.search(r"\bHQ\b|headquarter", n, re.IGNORECASE)]
    add("no unsupported headquarters claim in branch names", not hq, "ok" if not hq else f"check names of {hq}",
        level="warn")

    # ---- times
    missing = [c for c in TIME_COLS if c not in times.columns]
    add("times.csv columns", not missing, "From, To, Minutes" if not missing else f"missing {missing}")
    if missing:
        return out
    mins = pd.to_numeric(times["Minutes"], errors="coerce")
    whole = mins.notna().all() and (mins > 0).all() and (mins == mins.round()).all()
    add("pair-times are positive whole minutes", bool(whole),
        f"{mins.min():.0f}–{mins.max():.0f} min" if whole else "missing, non-numeric, zero/negative or fractional value")
    unknown = sorted((set(times["From"]) | set(times["To"])) - set(codes))
    add("every endpoint exists in branches.csv", not unknown, "ok" if not unknown else f"unknown codes {unknown}")
    selfloops = int((times["From"] == times["To"]).sum())
    add("no self-loops", selfloops == 0, f"{selfloops} self-loop rows")
    keys = [frozenset((a, b)) for a, b in zip(times["From"], times["To"])]
    dupes = len(keys) - len(set(keys))
    add("no duplicate pair in either direction", dupes == 0, f"{dupes} duplicate pair rows")
    expected = {frozenset(p) for p in combinations(codes, 2)}
    add("exactly 21 unordered pairs, each present once", len(times) == 21 and set(keys) == expected,
        f"{len(set(keys) & expected)} of 21 expected pairs, {len(times)} rows")

    # ---- Data Lead's documented baseline (X = 38) — guards against silent data drift
    if whole and not unknown and dupes == 0:
        t = times.assign(Minutes=mins.astype(int))
        r = eligible_routes(t, 38)
        add("baseline X = 38: 13 routes, 334 min (Data Lead decision sheet)",
            len(r) == 13 and int(r["Minutes"].sum()) == 334,
            f"{len(r)} routes, {int(r['Minutes'].sum())} min", level="warn")

    # ---- upgrades
    missing = [c for c in UPGRADE_COLS if c not in upgrades.columns]
    add("upgrades.csv columns", not missing, "all present" if not missing else f"missing {missing}")
    if missing:
        return out
    ucodes = upgrades["Code"].astype(str).tolist()
    add("upgrade codes are known branches (one per branch)",
        set(ucodes) <= set(codes) and len(ucodes) == len(set(ucodes)), f"{ucodes}")
    cost = pd.to_numeric(upgrades["Cost_AED"], errors="coerce")
    ben = pd.to_numeric(upgrades["Benefit_AED"], errors="coerce")
    after = pd.to_numeric(upgrades["Minutes_after"], errors="coerce")
    add("upgrade costs are positive AED", bool(cost.notna().all() and (cost > 0).all()), f"{cost.tolist()}")
    add("upgrade benefits are non-negative AED", bool(ben.notna().all() and (ben >= 0).all()), f"{ben.tolist()}")
    add("Minutes_after is a non-negative number", bool(after.notna().all() and (after >= 0).all()), f"{after.tolist()}")
    return out


def _provenance_check(d: Path, times: pd.DataFrame) -> Check:
    """times.csv must equal the rounded midpoint of the recorded Google Maps LOW/HIGH range
    (data/source/time_matrix_provenance.csv, extracted from the Data Lead's workbook)."""
    p = d / "source" / "time_matrix_provenance.csv"
    if not p.exists():
        return Check("drive times trace to recorded Google Maps ranges", "warn", "provenance file not in bundle")
    prov = pd.read_csv(p)
    m = times.merge(prov, on=["From", "To"], how="left")
    ok = len(m) == 21 and m["Midpoint_rounded_min"].notna().all() and (m["Minutes"] == m["Midpoint_rounded_min"]).all()
    return Check("drive times trace to recorded Google Maps ranges", "pass" if ok else "warn",
                 "21/21 midpoints of LOW/HIGH match times.csv" if ok else "a pair differs from its recorded midpoint")


def load_dataset(data_dir: Path | str = DATA_DIR, frames=None) -> Dataset:
    """Read (or accept already-read) frames, validate, and return a Dataset.
    `frames` lets tests inject malformed data without touching disk."""
    try:
        branches, times, upgrades = frames if frames is not None else read_sources(data_dir)
    except Exception as e:  # unreadable / missing file
        empty = pd.DataFrame()
        return Dataset(empty, empty, empty, [], "", [Check("read source files", "fail", str(e))])
    branches, times, upgrades = branches.copy(), times.copy(), upgrades.copy()
    checks = validate(branches, times, upgrades)
    ok = all(c.status != "fail" for c in checks)
    if ok:
        times["Minutes"] = pd.to_numeric(times["Minutes"]).astype(int)
        for c in ("Cost_AED", "Benefit_AED"):
            upgrades[c] = pd.to_numeric(upgrades[c]).round().astype(int)
        upgrades["Minutes_after"] = pd.to_numeric(upgrades["Minutes_after"])
    if ok and frames is None:
        checks.append(_provenance_check(Path(data_dir), times))
    order = branches["Code"].astype(str).tolist() if "Code" in branches else []
    hubs = (branches.loc[branches["Role"].astype(str).str.lower() == "hub", "Code"].tolist()
            if "Role" in branches else [])
    return Dataset(branches, times, upgrades, order, hubs[0] if hubs else (order[0] if order else ""), checks)
