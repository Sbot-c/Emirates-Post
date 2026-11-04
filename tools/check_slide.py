"""
tools/check_slide.py — reproducible content checks for recommendation_slide.pptx (needs python-pptx; see
requirements-dev.txt). Run from the project root:   python tools/check_slide.py

Checks: one slide; every shape inside the slide bounds; speaker notes present; required v2.2 statements present;
forbidden phrases absent; AED values use comma separators. (Visual overflow inside a text box is checked by
rendering the slide — see audit/validation_report.md — which needs LibreOffice and is not part of this script.)
"""
import re
import sys
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["proposed 20-minute internal hub-to-branch transfer target", "16 to 22 min", "local-fulfilment upgrades",
            "2 branches meet the 20-min target by direct transfer", "Umm Suqeim outside plan",
            "not make the hub-to-branch journey zero minutes", "first-year cost", "AED 411,960",
            "AED 765,000/yr", "modelled annual gross-benefit proxy (not profit)", "not profit", "proxy, not cash"]
REQUIRED_NOTES = ["modelled internal planning target", "only two meet the direct transfer target",
                  "remains outside the DP selected plan", "DP maximises the sum of the supplied gross-benefit proxies",
                  "not incremental profit", "assumption-based", "not cash savings",
                  "Payback, NPV and ROI are not established"]
FORBIDDEN = [r"express promise", r"express-service promise", r"\b5 of 6 (branches |offices )?(within|meet)",
             r"all five meet", r"five branches meet", r"loosest", r"\bnet profit of\b", r"profit saved",
             r"cash saving(s)? of", r"\bROI of\b", r"payback (period )?of"]


def main(path=ROOT / "recommendation_slide.pptx") -> int:
    prs = Presentation(str(path))
    problems = []
    if len(prs.slides) != 1:
        problems.append(f"expected 1 slide, found {len(prs.slides)}")
    W, H = prs.slide_width, prs.slide_height
    slide = prs.slides[0]
    text = []
    for sh in slide.shapes:
        if sh.left < 0 or sh.top < 0 or sh.left + sh.width > W or sh.top + sh.height > H:
            problems.append(f"shape '{sh.name}' extends outside the slide")
        if sh.has_text_frame:
            text.append(sh.text_frame.text)
    body = " ".join(text)
    notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
    if not notes.strip():
        problems.append("speaker notes missing")
    for r in REQUIRED:
        if r.lower() not in body.lower():
            problems.append(f"slide text missing: {r!r}")
    for r in REQUIRED_NOTES:
        if r.lower() not in notes.lower():
            problems.append(f"notes missing: {r!r}")
    for pat in FORBIDDEN:
        if re.search(pat, body + " " + notes, re.IGNORECASE):
            problems.append(f"forbidden phrase present: {pat!r}")
    bad_aed = re.findall(r"AED \d{4,}(?![\d,])", body + " " + notes)
    if bad_aed:
        problems.append(f"AED values without comma separators: {bad_aed}")
    if problems:
        print("SLIDE CHECK FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"SLIDE CHECK PASSED: 1 slide, {len(slide.shapes)} shapes within bounds, notes {len(notes)} chars, "
          f"{len(REQUIRED) + len(REQUIRED_NOTES)} required statements present, no forbidden phrases, AED comma format OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
