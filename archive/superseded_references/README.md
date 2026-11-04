# Superseded references — kept for provenance only

| File | Status | Use instead |
|---|---|---|
| `Knapsack_HandTrace_Sheet_Joan.pdf` | **Superseded in v2.3.1 — do not use as the current reference.** Kept byte-for-byte as supplied in the Investment Analyst's (Joan's) Tab 3 pack (SHA-256 `a8fa07fcc145b470f110308f26a5b1fb23b86723f3527433e7257f4ff23ca706`); moved here from `evidence/reference/`. | `evidence/reference/Knapsack_Comparison_Reference_v2_3_1.pdf` |

**Why it was superseded.** The sheet is a typed, computer-generated document (ReportLab) — not a handwritten trace, despite its file name. Its knapsack content (inputs, recurrence, 46-column grid, traceback, greedy comparison, AED 411,960 / AED 765,000 and AED 344,340 / AED 720,000) is correct, but page 3 has a row "Offices meeting the 20-min promise: 5 of 6" for both DP and greedy. That figure combines direct hub-transfer compliance (only KAR and QUS, 2 of 6) with local-fulfilment upgrades and, for greedy, the assumed UMS motorbike alternative mode.

**The corrected reference** (`tools/make_knapsack_reference_pdf.py`) is regenerated from the dashboard's v2.3 calculations, keeps the valid knapsack content, labels every page "Typed computational reference — not a handwritten trace", and replaces that row with a service-disposition table: DP — 2 direct, 0 alternative mode, 3 local fulfilment (JAF, SHJ, AJM), 1 outside (UMS); greedy — 2 direct, 1 alternative mode (UMS, assumed 18 min), 2 local fulfilment (JAF, SHJ), 1 outside (AJM); 5 of 6 destinations with a modelled service disposition in both, only 2 meeting the direct-transfer target.

`evidence/reference/reference_keys.json` still names this sheet as the source of the typed reference key; the key's values (grid bottom-right 765, JAF + SHJ + AJM, greedy JAF + UMS + SHJ) are unaffected by the correction. Joan's genuine handwritten knapsack trace is a separate requirement and is still pending.
