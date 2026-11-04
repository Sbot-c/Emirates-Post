"""v2.1 Part C/D/K: wording and claim hygiene, AED formatting, map proportionality, baseline fields, slide content."""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import ui_components as ui
from src.data_loader import eligible_routes

ROOT = Path(__file__).resolve().parent.parent
# Files scanned for stale claims (B3). Exclusions, by design: CHANGELOG.md and audit/validation_report.md (they quote
# the old wording when describing what was corrected), tests/ and tools/check_slide.py (pattern lists), the ORIGINAL
# typed notebook and member PDFs in evidence/ (kept unchanged as supplied; flagged in the app instead), data/upgrades.csv
# free-text (the Investment Analyst's verbatim wording, labelled in the app) and the Data Lead's workbook.
USER_FACING = [ROOT / "app.py", *sorted((ROOT / "src").glob("*.py")), ROOT / "README.md", ROOT / "tools" / "make_slide.js",
               ROOT / "tools" / "export_baseline.py", ROOT / "audit" / "assumption_register.md",
               ROOT / "audit" / "evidence_inventory.md", ROOT / "audit" / "source_register.csv",
               ROOT / "audit" / "source_workbook_errata.md", ROOT / "screenshots" / "README.md",
               ROOT / "tools" / "make_contribution_log.js"]
DERIVATIVE_NB = ROOT / "evidence" / "reference" / "Knapsack_Trace_Joan_v2_2_reference.ipynb"
STALE = [r"express[- ]service promise", r"express promise", r"20-minute express", r"\b5 of 6 (branches |offices )?(within|meet)",
         r"all five meet", r"five branches meet", r"within promise", r"branches within (the )?promise",
         r"local fulfil+ment (is|=|means) (a )?zero", r"zero[- ]minute (journey|travel|transfer)"]
# phrases allowed only when negated (e.g. "Not a zero-minute journey", "does not make ... zero minutes")
NEGATED_OK = re.compile(r"(not|never|no)\b[^.]{0,60}zero[- ]minute", re.IGNORECASE)


def _md_cells(nb_path):
    return "\n".join("".join(c["source"]) for c in json.loads(nb_path.read_text())["cells"] if c["cell_type"] == "markdown")


@pytest.fixture(scope="module")
def app_text():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    parts += [str(o) for s in at.selectbox for o in s.options] + [str(o) for s in at.select_slider for o in s.options]
    parts += [s.label for s in at.slider] + [s.label for s in at.select_slider]
    return "\n".join(parts)


def _stale_hits(txt):
    hits = []
    for pat in STALE:
        for m in re.finditer(pat, txt, re.IGNORECASE):
            window = txt[max(0, m.start() - 70):m.end()]
            if "zero" in pat and NEGATED_OK.search(window):
                continue
            hits.append(txt[max(0, m.start() - 40):m.end() + 20])
    return hits


@pytest.mark.parametrize("path", USER_FACING + [DERIVATIVE_NB], ids=lambda p: p.name)
def test_no_stale_claims_in_user_facing_files(path):
    txt = _md_cells(path) if path.suffix == ".ipynb" else path.read_text()
    if path == DERIVATIVE_NB:                      # the note cell quotes the corrected claim once, in quotation marks
        txt = txt.replace('"5 of 6 offices meet the 20-minute promise"', "")
    assert _stale_hits(txt) == [], path.name


def test_stale_claim_scanner_flags_known_bad_phrases():
    for bad in ["After funding, 5 of 6 offices meet the 20-minute promise.", "5 of 6 within target",
                "a 20-minute express-service promise", "Branches within promise: 5", "Local fulfilment = zero minutes"]:
        assert _stale_hits(bad), bad
    for good in ["Not a zero-minute journey and not direct-transfer compliant.",
                 "Five of six destinations have a modelled service disposition, but only two meet the direct-transfer target."]:
        assert not _stale_hits(good), good


def test_source_workbook_unchanged_and_errata_linked():
    import hashlib
    wb = ROOT / "data" / "source" / "EmiratesPost_Network_Data.xlsx"
    assert hashlib.sha256(wb.read_bytes()).hexdigest() == "ea35caa044273e1b3aca16604c26880f0acd6a0ba2b05655697f73c3d446f4b3"
    errata = (ROOT / "audit" / "source_workbook_errata.md").read_text()
    for s in ("7X HQ site", "not independently confirmed", "smallest", "largest", "X = 38"):
        assert s.lower() in errata.lower(), s
    assert "source_workbook_errata.md" in (ROOT / "README.md").read_text()
    assert "source_workbook_errata.md" in (ROOT / "audit" / "source_register.csv").read_text()


def test_data_inputs_unchanged_from_v21():
    """D4: route times, branches, upgrades and provenance are byte-identical to v2.1 (no input changed in v2.2)."""
    import hashlib
    expected = {"data/times.csv": "a3386053888d65795d1351b60711c55daa194d2f8d1a8095b51e71f8a15e3dbf",
                "data/branches.csv": "db94f2fb78addfed7f7df3bb900991f045de4d7edc7e5d86cf66e67e6b427e09",
                "data/upgrades.csv": "ac30d160cc8fa729a8e0cf2b443ee387483b70f8d75a6cd9ee46043d08a3b53d",
                "data/source/time_matrix_provenance.csv": "1f4df1015f2a870a6f5d7805cea5490078fedf066ca52200079466440f03a0b2"}
    for f, sha in expected.items():
        assert hashlib.sha256((ROOT / f).read_bytes()).hexdigest() == sha, f


def test_app_text_uses_internal_target_terminology(app_text):
    assert "proposed 20-minute internal hub-to-branch transfer target" in app_text
    assert "not an existing Emirates Post customer-facing service" in app_text
    assert _stale_hits(app_text) == []
    assert not re.search(r"loosest", app_text, re.IGNORECASE)


def test_no_unsupported_hq_claim_in_app(app_text):
    assert not re.search(r"7X HQ|HQ site", app_text)
    # HQ/headquarters may appear only as a dated, attributed report or inside an explicit non-claim / check label
    for m in re.finditer(r"headquarter|\bHQ\b", app_text, re.IGNORECASE):
        ctx = app_text[max(0, m.start() - 200):m.end() + 200]
        assert re.search(r"does not claim|no unsupported|reported .*no current official confirmation", ctx, re.S), ctx


def test_financial_terms_are_not_mislabelled(app_text):
    for m in re.finditer(r"profit|\bROI\b|cash saving", app_text):
        window = app_text[max(0, m.start() - 120):m.start()].lower()
        assert re.search(r"\bnot\b|\bno\b|are not established", window), app_text[max(0, m.start() - 120):m.end() + 20]
    assert "annual gross benefit proxy" in app_text


def test_aed_values_use_comma_separators(app_text):
    assert not re.findall(r"AED \d{4,}(?![\d,])", app_text)
    assert "AED 411,960" in app_text and "AED 481,860" in app_text


def test_map_projection_preserves_proportions(ds):
    pos, (lat0, lon0) = ui.project_km(ds.branches, ds.order)
    b = ds.branches.set_index("Code")

    def haversine(a, c):
        p1, p2 = math.radians(b.loc[a, "Latitude"]), math.radians(b.loc[c, "Latitude"])
        dl = math.radians(b.loc[c, "Longitude"] - b.loc[a, "Longitude"])
        h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * 6371.0 * math.asin(math.sqrt(h))
    for a, c in [("JAF", "AJM"), ("HUB", "KAR"), ("UMS", "SHJ"), ("HUB", "QUS")]:
        proj = math.dist(pos[a], pos[c])
        assert abs(proj - haversine(a, c)) / haversine(a, c) < 0.01, (a, c)   # within 1% over this extent


def test_route_tables_have_no_blank_or_duplicate_pairs(ds):
    for x in range(10, 67):
        r = eligible_routes(ds.times, x)
        assert not r[["From", "To", "Minutes"]].isna().any().any()
        keys = [frozenset((a, c)) for a, c in zip(r.From, r.To)]
        assert len(keys) == len(set(keys))


def test_baseline_json_regenerates_and_v2_fields_unchanged():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "export_baseline.py")], capture_output=True, text=True,
                         check=True).stdout
    new = json.loads(out)
    assert new == json.loads((ROOT / "tools" / "baseline.json").read_text())
    v2 = {"x": 38, "routes": 13, "all_total": 334, "mst_total": 124, "mst_n": 6, "saving_pct": 62.9, "pass_before": 2,
          "ums_now": 23, "tree_vs_fast": {"UMS": [33, 23], "JAF": [57, 47]}}
    for k, v in v2.items():
        assert new[k] == v, k
    assert (new["dp"]["spent"], new["dp"]["left"], new["dp"]["benefit"]) == (411_960, 38_040, 765_000)
    assert (new["greedy"]["spent"], new["greedy"]["benefit"]) == (344_340, 720_000)
    assert (new["plus50"]["spent"], new["plus50"]["left"], new["plus50"]["benefit"]) == (481_860, 18_140, 900_000)
    assert "coverage" not in new["dp"]                                     # documented v2.1 replacement
    assert new["dp"]["service_plan"]["direct"] == 2 and new["dp"]["service_plan"]["local"] == 3


def test_slide_content_check_passes():
    pytest.importorskip("pptx")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_slide.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
