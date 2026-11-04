"""
evidence.py — status of each member's handwritten trace, driven by what is actually in evidence/<folder>/.

States (never hard-coded):
  PENDING                         no scan file in the folder
  NEEDS REVIEW                    a file is unreadable, of an unsupported type, or transcription.json is malformed /
                                  names a different member
  FILE PRESENT — REVIEW REQUIRED  readable scan(s) present but no transcription.json yet → no comparison is claimed
  INCOMPLETE                      transcription.json present but required values are blank, or the member has not
                                  confirmed it is the original paper trace
  MATCHES TRANSCRIPTION           every required transcribed value equals the dashboard's baseline evidence run
  MISMATCH                        at least one transcribed value differs (an explanation should be recorded)

A file existing is never treated as a verified match; the comparison is only against values transcribed
from the paper, and it is not an instructor-grade judgement of the handwriting itself.
"""
from __future__ import annotations

import json
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
SCAN_EXT = IMAGE_EXT | {".pdf"}
IGNORED = {"transcription.json", "transcription_template.json", "readme.md", ".gitkeep", ".ds_store"}

REQUIRED = {"dfs": ["visit_order", "visited", "connected"],
            "kruskal": ["accepted", "rejected", "total"],
            "dijkstra": ["times"],
            "knapsack": ["bottom_right_k", "chosen", "greedy"]}
META = {"_how_to_use", "produced_by", "confirmed_original_paper_trace", "mismatch_explanation", "source_file"}


def _readable(p: Path) -> tuple[bool, str]:
    ext = p.suffix.lower()
    if ext not in SCAN_EXT:
        return False, f"{p.name}: unsupported type ({ext or 'no extension'}) — use JPG/PNG/WEBP or PDF"
    try:
        if ext == ".pdf":
            with open(p, "rb") as fh:
                ok = fh.read(5) == b"%PDF-"
            return (ok, "" if ok else f"{p.name}: not a readable PDF")
        from PIL import Image
        with Image.open(p) as im:
            im.verify()
        return True, ""
    except Exception as e:  # corrupt / truncated / not really an image
        return False, f"{p.name}: unreadable image ({type(e).__name__})"


def _norm_edges(lst):
    return sorted("-".join(sorted(str(e).replace("–", "-").split("-"))) for e in (lst or []))


def compare(key: str, expected: dict, got: dict) -> list:
    """Row per material value present in `expected`: field, transcribed/reference, dashboard, match."""
    rows = []
    for f, v in expected.items():
        if f in META or f.startswith("_") or v is None:
            continue
        g = got.get(f)
        if f in ("accepted", "rejected", "tree_edges"):
            ok = _norm_edges(v) == _norm_edges(g)
        elif f in ("chosen", "greedy", "failing_at_20"):
            ok = sorted(v) == sorted(g or [])
        elif f in ("times", "trace_units"):
            ok = all(v.get(k) is None or (g.get(k) is not None and int(v[k]) == int(g[k])) for k in v)
        else:
            ok = v == g
        rows.append({"Value": f, "Transcribed": v, "Dashboard (baseline run)": g, "Match": "yes" if ok else "NO"})
    return rows


def state(folder: Path, key: str, member: str, got: dict) -> dict:
    """Evidence state for one panel. `got` = dashboard values from the baseline evidence run."""
    files = sorted(p for p in folder.glob("*") if p.is_file() and p.name.lower() not in IGNORED) if folder.exists() else []
    out = {"state": "PENDING", "detail": "No handwritten scan supplied yet.", "scans": [], "images": [], "pdfs": [],
           "problems": [], "transcription": None, "comparison": [], "explanation": ""}
    if not files:
        return out
    for p in files:
        ok, why = _readable(p)
        if ok:
            out["scans"].append(p)
            (out["pdfs"] if p.suffix.lower() == ".pdf" else out["images"]).append(p)
        else:
            out["problems"].append(why)
    if out["problems"]:
        out.update(state="NEEDS REVIEW", detail="; ".join(out["problems"]))
        return out
    tp = folder / "transcription.json"
    if not tp.exists():
        out.update(state="FILE PRESENT — REVIEW REQUIRED",
                   detail="Scan is readable. No comparison is claimed until transcription.json records the values "
                          "written on the paper.")
        return out
    try:
        tr = json.loads(tp.read_text())
        assert isinstance(tr, dict)
    except Exception:
        out.update(state="NEEDS REVIEW", detail="transcription.json is not valid JSON.")
        return out
    out["transcription"] = tr
    out["explanation"] = str(tr.get("mismatch_explanation") or "")
    if tr.get("produced_by") and str(tr["produced_by"]).strip().lower() != member.lower():
        out.update(state="NEEDS REVIEW", detail=f"transcription.json names '{tr['produced_by']}', not {member}.")
        return out
    missing = [f for f in REQUIRED[key] if tr.get(f) in (None, "", [])
               or (isinstance(tr.get(f), dict) and any(v is None for v in tr[f].values()))]
    if missing or not tr.get("confirmed_original_paper_trace"):
        why = (f"blank values: {', '.join(missing)}" if missing else "") + \
              ("; " if missing and not tr.get("confirmed_original_paper_trace") else "") + \
              ("member has not confirmed it is the original paper trace" if not tr.get("confirmed_original_paper_trace") else "")
        out.update(state="INCOMPLETE", detail=f"Transcription incomplete — {why}.")
        out["comparison"] = compare(key, {f: tr.get(f) for f in REQUIRED[key]}, got)
        return out
    rows = compare(key, {f: tr[f] for f in REQUIRED[key]}, got)
    out["comparison"] = rows
    bad = [r["Value"] for r in rows if r["Match"] != "yes"]
    if bad:
        out.update(state="MISMATCH", detail=f"Differs on: {', '.join(bad)}. "
                   + ("Explanation recorded." if out["explanation"] else "Record an explanation in transcription.json."))
    else:
        out.update(state="MATCHES TRANSCRIPTION",
                   detail="Every required transcribed value equals the baseline evidence run (not an instructor grading).")
    return out
