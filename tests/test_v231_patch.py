"""v2.3.1 patch: (1) corrected knapsack typed-reference PDF + archived original; (2) Dijkstra panel stacks when narrow.
Browser-level layout measurements (1440 / 820 / 390 px) are in tools/browser_smoke_test.js."""
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import investment_core as ic
from src import ui_components as ui
from src import working_tab as wt

ROOT = Path(__file__).resolve().parent.parent
NEW = ROOT / "evidence" / "reference" / "Knapsack_Comparison_Reference_v2_3_1.pdf"
OLD_NAME = "Knapsack_HandTrace_Sheet_Joan.pdf"
ARCHIVED = ROOT / "archive" / "superseded_references" / OLD_NAME
OLD_SHA = "a8fa07fcc145b470f110308f26a5b1fb23b86723f3527433e7257f4ff23ca706"
LABEL = "Typed computational reference — not a handwritten trace"


def _gen():
    spec = importlib.util.spec_from_file_location("mkpdf", ROOT / "tools" / "make_knapsack_reference_pdf.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _pages():
    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        pytest.skip("poppler-utils (pdftotext/pdfinfo) not installed")
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(NEW)], capture_output=True, text=True).stdout).group(1))
    return [" ".join(subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(NEW), "-"],
                                    capture_output=True, text=True, check=True).stdout.split()) for i in range(1, n + 1)]


# ---------------------------------------------------------------- refinement 1: the PDF
def test_original_archived_unchanged_and_not_in_reference_folder():
    assert hashlib.sha256(ARCHIVED.read_bytes()).hexdigest() == OLD_SHA
    assert not (ROOT / "evidence" / "reference" / OLD_NAME).exists()
    assert "Superseded in v2.3.1" in (ARCHIVED.parent / "README.md").read_text()


def test_corrected_pdf_exists_and_is_a_complete_pdf():
    raw = NEW.read_bytes()
    assert raw.startswith(b"%PDF-") and raw.rstrip().endswith(b"%%EOF") and len(raw) > 5_000


def test_every_page_labelled_typed_reference_and_wording_corrected():
    pages = _pages()
    assert len(pages) == 3                                   # no blank trailing page
    assert all(LABEL in p for p in pages)
    text = " ".join(pages)
    assert not re.search(r"5 of 6 offices|offices meeting the 20-min promise|five branches meet", text, re.IGNORECASE)
    assert "promise" not in text.lower()
    assert "Direct hub-transfer within target" in text and "2 of 6 — KAR, QUS 2 of 6 — KAR, QUS" in text
    assert "Local-fulfilment upgrade selected" in text and "3 of 6 — JAF, SHJ, AJM 2 of 6 — JAF, SHJ" in text
    assert "Outside selected service plan 1 of 6 — UMS 1 of 6 — AJM" in text
    assert "Alternative-mode service within target (assumption) 0 of 6 1 of 6 — UMS (motorbike, assumed 18 min" in text
    assert "Destinations with a modelled service disposition 5 of 6 5 of 6" in text
    assert "only two meet the direct-transfer target" in text
    assert "X = 38" in text and "HUB" in text and "AED 450,000" in text and "20 min" in text


def test_pdf_numbers_match_v23_core(ds):
    text = " ".join(_pages())
    c = _gen().content()
    # the content model is the dashboard's own calculation
    sc_routes = c["routes"]
    assert sc_routes == 13 and c["dist"] == {"KAR": 13, "QUS": 16, "UMS": 23, "JAF": 47, "SHJ": 24, "AJM": 51}
    assert c["dp"]["picks"] == ["JAF", "SHJ", "AJM"] and (c["dp"]["spent"], c["dp"]["left"], c["dp"]["benefit"]) == (411_960, 38_040, 765_000)
    assert c["greedy"]["picks"] == ["JAF", "UMS", "SHJ"] and (c["greedy"]["spent"], c["greedy"]["benefit"]) == (344_340, 720_000)
    assert c["gap"] == 45_000 and c["bottom_right"] == 765_000 and c["brute_agrees"] and c["trace_same_as_exact"]
    hc, hb = ic.trace_units([it["cost"] for it in c["items"]], 450_000)
    K, *_ = ic.knapsack(hc, [it["benefit"] for it in c["items"]], hb)
    assert c["K"] == K and hb == 45 and hc == [7, 14, 13, 14]
    assert {(i, w) for i, w in c["trace_cells"]} == {(4, 45), (3, 31), (2, 18), (1, 4)}
    # ... and the rendered PDF carries those numbers
    for s in ("411,960", "38,040", "765,000", "344,340", "105,660", "720,000", "AED 45,000/yr", "K[4][45] = 765 vs K[3][45] = 720",
              "TAKE AJM", "TAKE SHJ", "TAKE JAF", "SKIP UMS", "Units used: 41 of 45", "69,900", "143,520", "130,920", "137,520"):
        assert s in text, s
    # every grid row appears with its 46 values in two halves
    for i, row in enumerate(K):
        assert " ".join(str(v // 1000) for v in row[:23]) in text and " ".join(str(v // 1000) for v in row[23:]) in text


def test_committed_pdf_matches_a_fresh_regeneration(tmp_path):
    pytest.importorskip("reportlab")
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext not installed")
    m = _gen()
    out = m.render(m.content(), tmp_path / "regen.pdf")
    txt = lambda p: subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True).stdout  # noqa: E731
    assert txt(out) == txt(NEW)


def test_app_points_to_corrected_reference():
    assert wt.KNAPSACK_REFERENCE == NEW.name
    assert dict((p[0], p[5]) for p in wt.PANELS)["knapsack"] == NEW.name
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    labels = [b.label for b in at.get("download_button")]
    assert f"Typed reference (not handwritten): {NEW.name}" in labels
    assert not any(OLD_NAME in lbl for lbl in labels)
    caps = "\n".join(c.value for c in at.caption)
    assert "supersedes the earlier typed sheet" in caps and "archive/superseded_references/" in caps
    # evidence status unchanged
    t = "\n".join(m.value for m in at.markdown)
    assert t.count("HANDWRITTEN TRACE REQUIRED") == 4 and "0 of 4 traces matched" in t


# ---------------------------------------------------------------- refinement 2: Dijkstra layout
def test_dijkstra_panel_scoped_container_and_css():
    assert wt.DIJKSTRA_PANEL_KEY == "ow_dijkstra_panel"
    css = ui.CSS
    assert ".st-key-ow_dijkstra_panel {{ container-type: inline-size; }}".replace("{{", "{").replace("}}", "}") in css
    block = css[css.index("@container (max-width: 760px)"):]
    block = block[:block.index("}\n}") + 3]
    assert "flex-direction: column" in block and "width: 100% !important" in block
    # the rules are scoped to the Dijkstra panel only
    assert all(line.strip().startswith(".st-key-ow_dijkstra_panel") for line in block.splitlines()[1:-1] if line.strip())
    src = (ROOT / "src" / "working_tab.py").read_text()
    assert 'st.container(key=DIJKSTRA_PANEL_KEY) if key == "dijkstra" else nullcontext()' in src


def test_dijkstra_content_unchanged(ds):
    sc, pool, inv, trace = wt.baseline_run(ds)
    d = sc.dijkstra["dist"]
    assert [int(d[c]) for c in ("KAR", "QUS", "UMS", "SHJ", "JAF", "AJM")] == [13, 16, 23, 24, 47, 51]
    assert [s["Settle"] for s in sc.dijkstra["steps"]][:3] == ["HUB (0)", "KAR (13)", "QUS (16)"]
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    t = "\n".join(m.value for m in at.markdown)
    assert "HUB → UMS → JAF" in t                                       # JAF equal shortest path still shown
    assert "Upload the original paper photo/scan from <b>Siddal</b>" in t


PROTECTED = {   # SHA-256 in v2.3 — unchanged by the v2.3.1 patch
    "tools/baseline.json": "979cf3694f522f07e075cf87e8ff879888ae993c24a03af9049eee34920c4bc9",
    "recommendation_slide.pptx": "b78d37a47512804308ce0957f98508017ce50afcb1fd60627113263b4807131c",
    "contribution_log_template.docx": "3c01d6bf520313d228fbd44dc5c19efb25519103317cf9da23f9c41eda3cf4ea",
    "src/evidence.py": "9d35d30432ed0798ff511b7f13a640d39a14c7a697ed14e5385040e65c56eb4f",
    "evidence/reference/reference_keys.json": "02ffae3e85b035dc8a33e583d64bde79b994ff17530f1d1f8d67b67d16e54bbd",
}


def test_baseline_slide_log_and_evidence_logic_unchanged():
    for rel, sha in PROTECTED.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha, rel


def test_evidence_folders_unchanged_apart_from_the_two_reference_files():
    """Same `sha256sum`-style digest over every evidence file as v2.3, excluding only the moved sheet and the new PDF."""
    files = sorted(p for p in (ROOT / "evidence").rglob("*") if p.is_file() and p.name != NEW.name
                   and "__pycache__" not in p.parts)
    listing = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
    assert hashlib.sha256(listing.encode()).hexdigest() == "03cd2a46643e341c582ba25ecd8a894c3ad75f998afd780bf3b99d2a9ced774d"
