"""Evidence status logic. All files here are temporary test fixtures in pytest's tmp_path — nothing is written to
the project's evidence/ folders, and no handwriting is generated."""
import json

from PIL import Image

from src import evidence as ev

GOT = {"visit_order": ["HUB", "KAR", "QUS", "UMS", "JAF", "SHJ", "AJM"], "visited": 7, "connected": True}


def blank_png(path):
    Image.new("RGB", (8, 8), "white").save(path)       # plain fixture, not a trace


def tr(folder, **kw):
    d = {"produced_by": "Kushal", "confirmed_original_paper_trace": True, "visit_order": GOT["visit_order"],
         "visited": 7, "connected": True}
    d.update(kw)
    (folder / "transcription.json").write_text(json.dumps(d))


def test_missing_evidence_is_pending(tmp_path):
    (tmp_path / "transcription_TEMPLATE.json").write_text("{}")
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "PENDING"
    assert ev.state(tmp_path / "does_not_exist", "dfs", "Kushal", GOT)["state"] == "PENDING"


def test_unreadable_or_unsupported_file_needs_review(tmp_path):
    (tmp_path / "trace.jpg").write_bytes(b"this is not a jpeg")
    s = ev.state(tmp_path, "dfs", "Kushal", GOT)
    assert s["state"] == "NEEDS REVIEW" and "unreadable" in s["detail"]
    (tmp_path / "trace.jpg").unlink()
    (tmp_path / "trace.heic").write_bytes(b"x")
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "NEEDS REVIEW"


def test_readable_scan_alone_is_not_a_match(tmp_path):
    blank_png(tmp_path / "trace.png")
    s = ev.state(tmp_path, "dfs", "Kushal", GOT)
    assert s["state"] == "FILE PRESENT — REVIEW REQUIRED" and s["comparison"] == []


def test_incomplete_and_unconfirmed_transcriptions(tmp_path):
    blank_png(tmp_path / "trace.png")
    tr(tmp_path, visited=None)
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "INCOMPLETE"
    tr(tmp_path, confirmed_original_paper_trace=False)
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "INCOMPLETE"


def test_match_and_mismatch(tmp_path):
    blank_png(tmp_path / "trace.png")
    tr(tmp_path)
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "MATCHES TRANSCRIPTION"
    tr(tmp_path, visit_order=["HUB", "QUS", "KAR", "UMS", "JAF", "SHJ", "AJM"], mismatch_explanation="slip")
    s = ev.state(tmp_path, "dfs", "Kushal", GOT)
    assert s["state"] == "MISMATCH" and s["explanation"] == "slip"
    assert [r["Value"] for r in s["comparison"] if r["Match"] == "NO"] == ["visit_order"]


def test_wrong_member_or_bad_json_needs_review(tmp_path):
    blank_png(tmp_path / "trace.png")
    tr(tmp_path, produced_by="Someone else")
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "NEEDS REVIEW"
    (tmp_path / "transcription.json").write_text("{not json")
    assert ev.state(tmp_path, "dfs", "Kushal", GOT)["state"] == "NEEDS REVIEW"


def test_project_evidence_folders_are_pending_until_scans_are_added():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "evidence"
    for folder, key, member in [("dfs_kushal", "dfs", "Kushal"), ("kruskal_shashaank", "kruskal", "Shashaank"),
                                ("dijkstra_siddal", "dijkstra", "Siddal"), ("knapsack_joan", "knapsack", "Joan")]:
        assert ev.state(root / folder, key, member, {})["state"] == "PENDING"
