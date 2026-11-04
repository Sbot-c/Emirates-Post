# Change log

## v2.4 — hub-linked target, X check, Python trace plots, look (4 Nov 2026)

Applied to `DSA_FINAL_ZIP.zip` (v2.3.1). Algorithms, data, baseline numbers (`tools/baseline.json` identical), slide, evidence folders and status logic are unchanged.

| # | Change | Files |
|---|---|---|
| 1 | Hub dropdown moves the target slider to the hub's suggested value; manual override kept; suggestion banner, button, hub ranking | `src/advisor.py` (new), `src/promise_sync.py` (new), `src/tab_service.py`, `app.py`, `src/ui_components.py` |
| 2 | Python-generated plots, key-results table and CSV answer keys in all four hand-trace panels | `src/trace_visuals.py` (new), `src/working_tab.py` |
| 3 | X = 39 vs 38 computed check; X = 38 kept (no extra reach, 15 routes outside 10–14) | `src/advisor.py`, `src/tab_network.py`, `src/working_tab.py`, `src/ui_components.py` |
| 4 | Look-and-feel layer, recommended-hub chip | `src/ui_components.py`, `app.py` |
| 5 | Dependencies: matplotlib added | `requirements.txt`, `requirements-lock.txt`, `requirements-notebook.txt` |

Tests: new `tests/test_advisor.py`, `tests/test_trace_visuals.py`, `tests/test_hub_promise_sync.py`; `tests/test_integration.py::test_kpis_follow_hub_promise_and_budget_changes` updated (the target now follows the hub); `tools/browser_smoke_test.js` now expects 15 images (11 notebook + 4 Python-generated).

**Validation status (honest):** built in an environment without Streamlit/Plotly/pytest and without network. Executed: advisor and trace-visual tests via a small shim; a stub harness that ran all four tab `render()` functions for every hub, X = 39, 45 and 20; compile of every file; `baseline.json` diff. **Not executed:** the real app, the AppTest suite (old and new), the browser smoke test, visual QA of the CSS/Plotly charts. Run `pytest -q` and `node tools/browser_smoke_test.js --launch` before submission. `screenshots/` still shows v2.3.1 except `v2_4_python_trace_*.png`, which are direct renders of `trace_visuals.py`, not browser screenshots.

---
## v2.3.1 — patch: knapsack reference correction + responsive Dijkstra panel (3 Nov 2026)

Applied to `network-audit-v2_3.zip` (207 tests; a clean extracted copy was kept for comparison) per the *Final Two Refinements* prompt. Exactly two refinements; no other behaviour changed.

| # | Issue | Files changed | Implementation | Tests added |
|---|---|---|---|---|
| 1 | `evidence/reference/Knapsack_HandTrace_Sheet_Joan.pdf` (typed, ReportLab-generated, 3 pages) has a page-3 row "Offices meeting the 20-min promise: 5 of 6" for DP and greedy, mixing direct transfer with upgrades | `tools/make_knapsack_reference_pdf.py` (new), `evidence/reference/Knapsack_Comparison_Reference_v2_3_1.pdf` (new), `archive/superseded_references/Knapsack_HandTrace_Sheet_Joan.pdf` (moved, byte-identical) + `README.md`, `src/working_tab.py` (knapsack panel's typed reference → new PDF; note under the knapsack notebook block), `requirements-notebook.txt` (+ `reportlab==5.0.1`), README | The corrected reference is generated from the dashboard's v2.3 calculations (nothing typed by hand). It keeps the inputs, recurrence, full 46-column grid with traceback cells, traceback, greedy steps and result, and labels every page "Typed computational reference — not a handwritten trace". The old row is replaced by a service-disposition table: DP 2 direct (KAR, QUS) / 0 alternative mode / 3 local fulfilment (JAF, SHJ, AJM) / 1 outside (UMS); greedy 2 direct / 1 alternative mode (UMS, assumed 18 min) / 2 local (JAF, SHJ) / 1 outside (AJM); 5 of 6 with a modelled disposition in both. "Promise", "yearly benefit" and "Trace by" wording replaced by target / gross-benefit proxy / typed reference. Rendered (3 pages, no trailing page) and inspected | `tests/test_v231_patch.py`: archive SHA, not in the reference folder, complete PDF, label on every page, corrected wording and no stale phrase, numbers and the full grid match the v2.3 core, fresh regeneration gives identical text (needs reportlab), app download points to the new file |
| 2 | Our working → Dijkstra: placeholder and dashboard result stayed side by side at 820 px (panel ~488 px wide with the sidebar open) | `src/working_tab.py`, `src/ui_components.py` | The Dijkstra pair is wrapped in `st.container(key="ow_dijkstra_panel")` (stable `st-key-…` class). A CSS container query scoped to that class stacks the two columns when the panel is narrower than 760 px; the desktop layout (980 px panel at 1440×900) is unchanged. Its two tables use the existing wrapping table style. No other panel, content or calculation changed | `tests/test_v231_patch.py` (scoped CSS and container, Dijkstra content unchanged) + browser checks at 1440×900 (side by side), 820×1180 and 390×844 (stacked, placeholder first, tables inside the panel, no page overflow) |

**Validation (executed in this run — `audit/validation_report.md`):** 216 passed + 1 skipped (fresh extraction, lock environment, `-W error::FutureWarning`; the skip is the regeneration test, which needs reportlab), and all 10 patch tests passed in the notebook-tooling environment that has reportlab; compile OK; no warnings; browser smoke test 35/35 twice (other working directory; `--launch`); 0 external requests; slide check and external validator passed; `baseline.json` identical to v2.3.

**Intentionally unchanged:** algorithms, data, threshold, hub, target, costs, benefits, `tools/baseline.json`, the recommendation slide, the 11 notebook figures and their assets, the team roster, evidence folders and status logic (only the typed sheet moved to the archive; `evidence/reference/reference_keys.json` unchanged), `audit/evidence_inventory.md`, the contribution log, other `Our working` panels (DFS, Kruskal, Knapsack keep their side-by-side layout), colours, fonts and navigation.

**Still outstanding (user actions):** four genuine handwritten traces; contribution-log signatures and dates; deployment, live-link check and a second computer/network.

---

## v2.3 — final refinement (3 Nov 2026)

Applied to `network-audit-v2_2.zip` (197 tests; a clean extracted copy was kept for comparison) per the *v2.3 Final Refinement Master Prompt*, with the team notebook `EmiratesPost_Graphs_and_Working.ipynb` supplied by the user (the prompt calls it `…(1).ipynb`; the upload carried no "(1)" — same notebook: 27 cells, 11 PNG outputs). Same architecture, four tabs, data, algorithms, theme, baseline JSON and slide. Evidence folders, `src/evidence.py`, evidence cards and pending placeholders, `audit/evidence_inventory.md` and the contribution log are **unchanged**.

### Notebook inspection (Part A)

All 27 cells were read (Markdown, code, stream/HTML/plain outputs, MIME data, attachments, execution counts 1–20 in order). **Finding:** the 11 embedded images are PNG outputs of the notebook's Matplotlib code — original team-created, notebook-generated figures. None is a photograph or scan of pen-and-paper work, and there are no Markdown attachments. Cell, output index and pixel size of all 11 match the prompt's expected inventory exactly (Figures 1.1, 1.2, 1.3, 2.1, 3.1, 4.1, 4.2, 4.4, 5.1a, 5.1b, 5.2). The notebook's own section-6 summary agrees with the v2.3 dashboard on all 12 values; its fresh re-run reproduced every unchanged cell's text output.

### P0 — figures, team, derivative

| Issue | Files changed | Implementation | Tests |
|---|---|---|---|
| Integrate all notebook figures (Part B) | `notebooks/EmiratesPost_Graphs_and_Working.ipynb` (added, unchanged), `tools/extract_notebook_figures.py` (new; replaces `tools/extract_notebook_diagrams.py`), `assets/notebook_diagrams/` (11 PNG + `manifest.json`; the three v2.2 Joan-notebook PNGs removed), `assets/notebook_tables/` (9 CSV), `audit/notebook_diagram_inventory.csv`, `src/notebook_diagrams.py` (rewritten), `src/working_tab.py`, `src/ui_components.py` | Bytes written unchanged and SHA-checked; idempotent; `--check` mode; fails on missing/corrupt/resized images. Placement: Data and threshold X (new subsection, Kushal) — 1.1, 1.2, 1.3; DFS (Kushal) — 2.1; Kruskal (Shashaank) — 3.1; Dijkstra (Siddal) — 4.1, 4.2, 4.4; Knapsack (Joan) — 5.1a, 5.1b, 5.2. Each section: a box tagged "Notebook baseline reference — X = 38, HUB, 20 min, AED 450,000" after the dashboard's own result; natural-size images (never upscaled) shrunk to the panel width; captions with figure, notebook, cell, output; reading notes where the original image wording needs context (4.4 "cheapest", 5.2 "earns"); notebook tables in expanders; a computed cross-check (AGREES / MISMATCH). A note appears when the live controls differ from the baseline. New overall cross-check (12 of 12 agree) labelled *Overall integration — Sparsh*. Missing/corrupt file → warning for that figure only | `tests/test_notebook_diagrams.py` (15) |
| Duplicate knapsack visuals | — | The three v2.2 figures from Joan's notebook are no longer displayed (5.1a/5.1b/5.2 cover the same baseline content). Joan's notebook and its v2.2 derivative are unchanged | same |
| Project Team overview (Part C) | `app.py`, `src/ui_components.py` | Roster under the business question, before the tabs: Kushal — Data Lead; Shashaank — Network Analyst; Siddal — Routing Analyst; Joan — Investment Analyst; Sparsh — Integration & Business Lead. Two-column grid, one column below 760 px; neutral role pills | `tests/test_team_and_threshold.py` |
| Ownership labels | `src/working_tab.py`, `src/notebook_diagrams.py` | Our working: "Assembled and integrated by Sparsh · Integration & Business Lead" (was "Sparsh Saraya"); section owners per C3. Tab owners unchanged (Shashaank, Siddal, Joan) | same |
| Stale "dashboard (v2.1)" in the notebook (A4, G2) | `notebooks/EmiratesPost_Graphs_and_Working_v2_3_reference.ipynb` (new), `tools/make_notebook_v2_3_reference.py` (new), `requirements-notebook.txt` (new) | Derivative: note cell; cells 0/25 wording; section 6 recomputes the dashboard side from `../src` and computes MATCH/MISMATCH (12 of 12 MATCH); added service-disposition cell; only the changed cells were executed (nbclient); all 11 figures byte-identical | `test_v23_derivative_preserves_figures_and_refreshes_comparison` |

### P0/P1 — threshold, KPIs, navigation

| Issue | Files | Implementation |
|---|---|---|
| X = 38 rationale (E3) | `src/working_tab.py`, README, `audit/assumption_register.md` (A6), `audit/source_workbook_errata.md` (E2) | Exact criterion, computed from `times.csv`: QUS–AJM 37 min → X = 37 excludes it (12 routes; SHJ–AJM a bridge), X = 38 includes it (13 routes, connected, no bridge); the two 38-min HUB links stay out until X = 39 (15 routes). Text states other X (31–37) also qualify, so 38 is neither "the smallest valid X" nor merely "the largest". Replaces v2.2's "Largest X satisfying…" wording |
| D: KPI regression | — | Re-run: baseline DP 2 direct / 3 local / 1 outside; greedy UMS alternative mode (18 min, from upgrades.csv), JAF/SHJ local, AJM outside; JAF / 90 min / include-passing counts 2 selected local upgrades (1 primary LOCAL) — all from actual selections (existing v2.2 tests, executed) |
| F2: tab labels clipped at 820 px with the sidebar open | `src/ui_components.py` | Below 1,100 px the tab list wraps onto a second row (`[role="tablist"] { flex-wrap: wrap }`); measured: all four labels fully visible at 1440×900 and 820×1180 |
| Images wider than the panel at 820 px | `src/ui_components.py` | `stImageContainer`/`img` capped at 100% of the panel, height auto (found while testing: Streamlit's container kept the 1,529 px natural width) |
| H2: browser test | `tools/browser_smoke_test.js` | Extended: roster, 11 figures decoded and inside the panel, fixed-baseline note after control changes, 12/12 cross-check, evidence summary in first viewport, tab labels fully visible at both sizes; screenshots of the new sections |

### Tests and validation (executed in this v2.3 run — details in `audit/validation_report.md`)

207 passed, 0 failed, no warnings (fresh extraction, clean lock environment, `-W error::FutureWarning`); compile OK; `check_slide.py` and the external pptx validator passed; `baseline.json` regenerates identically and is identical to v2.2; `extract_notebook_figures.py --check` passed; browser smoke test 27/27 twice (app launched from another working directory; and `--launch` mode); 0 external requests; `requirements-notebook.txt` installs cleanly.

### Intentionally left unchanged

Data (`data/*.csv`, `data/source/*`), algorithms, `tools/baseline.json`, `recommendation_slide.pptx` (re-checked, still accurate), evidence folders and logic, evidence cards and placeholders, `audit/evidence_inventory.md`, the contribution log (it still reads "Sparsh Saraya"; not edited by instruction), the original team notebook, Joan's notebook and PDFs, colours and chart types; no fifth tab.

### Outstanding (not done in v2.3)

| Item | Status |
|---|---|
| Four genuine handwritten algorithm traces | **Pending — user action** (all panels PENDING; notebook figures do not satisfy this) |
| Contribution log wording, signatures, dates | **Pending — user action** |
| Deployment, live link, second computer/network test, backups | **Pending — user action** |

---

## v2.2 — consolidated refinement (3 Nov 2026)

Applied to `network-audit-v2_1.zip` (147 tests; a clean extracted copy was kept for comparison) per the *v2.2 Final Consolidated Refinement Prompt*. Targeted changes only: same architecture, four tabs, data, algorithms, theme and baseline figures. `data/*.csv`, `data/source/*` (incl. the Data Lead's workbook), the evidence folders, `src/evidence.py`, the evidence cards and pending placeholders, and the contribution log are **unchanged** (byte-identical where tested).

### P0 — correctness

| Issue identified | Files changed | Implementation | Tests added |
|---|---|---|---|
| A: the "local fulfilment upgrades selected" KPI counted the LOCAL primary disposition, so an optional mini-hub on a branch that already passes directly (scenario view, e.g. hub JAF / 90 min) was not counted (v2.1 showed 1 where 2 local upgrades were selected) | `src/investment_core.py`, `src/tab_investment.py`, `src/tab_service.py` (label) | `classify_branch` now records the selected intervention from the algorithm's picks (`upgrade_selected`, `selected_upgrade`, `selected_upgrade_type`, `selected_upgrade_cost_aed`, `local_fulfilment_selected`, `alternative_mode_upgrade_selected`, `selected_intervention`) separately from the primary disposition; `service_plan` adds `local_selected`, `alt_selected`, `alt_qualifying_selected`, `selected_on_direct`, `interventions`. KPI labels per Part F (E3) with a visible definition and denominator; the branch table now shows *selected upgrade* and *primary disposition* for DP and greedy; `plan_summary` notes optional upgrades on already-direct branches. A missing/negative/non-numeric `Minutes_after` is "mechanism not stated", never an alternative mode | `test_service_disposition.py` (+28 incl. parametrised hub × target × option sweep), `test_integration.py` (KPIs reconcile with the rendered table at baseline, after target/budget/hub/threshold changes, and in the JAF / 90 min / include-passing regression) |
| B1: typed notebook says "After funding, 5 of 6 offices meet the 20-minute promise" | `evidence/reference/Knapsack_Trace_Joan_v2_2_reference.ipynb` (new), `tools/make_joan_v2_2_reference.py` (new) | Corrected **derivative**; typed Markdown only; code, outputs and figures byte-identical (verified); original unchanged (SHA-256 test) | `test_notebook_diagrams.py` |
| B2: claim audit | `src/routing_core.py`, `src/tab_service.py` (comments), `src/working_tab.py` (assumption row; note flagging the outdated row in the unchanged typed PDF `Knapsack_HandTrace_Sheet_Joan.pdf`), README, registers | All `.py/.md/.csv/.js/.ipynb/.txt`, slide text and notes, and supporting PDFs were searched. Remaining hits are negations or quotes inside change records. The member PDF is not edited (typed member document) — flagged in the app instead | `test_claims.py`: scanner over the listed files + derivative notebook + rendered app text, with a self-test of the scanner (flags bad phrases, allows negated ones); exclusions documented in the test |
| D: slide coverage/finance wording | `tools/make_slide.js`, `recommendation_slide.pptx`, `tools/export_baseline.py`, `tools/baseline.json`, `tools/check_slide.py` | Title "Fund 3 local-fulfilment mini-hubs for AED 411,960 first-year cost"; AED 765,000/yr labelled "modelled annual gross-benefit proxy (not profit)"; "2 branches meet the 20-min target by direct transfer; Umm Suqeim outside plan"; "+AED 45,000/yr proxy vs greedy — not profit"; 62.9% = "summed edge-weight (proxy, not cash)". Notes add: internal planning target; assumption-based benefits; AED 45,000 is not incremental profit; DP not superior on fairness/resilience/service time/risk; not a capital-budgeting model. `baseline.json`: **additive only** (intervention counts); every v2.1 value identical | `check_slide.py` now requires 20 statements and forbids profit/ROI/payback/cash-saving phrasings; `test_claims.py` runs it |

### P1 — reproducibility and documentation

| Issue | Files | Implementation |
|---|---|---|
| C: notebook diagrams for *Our working* | `tools/extract_notebook_diagrams.py`, `assets/notebook_diagrams/` (3 PNG + `manifest.json`), `audit/notebook_diagram_inventory.csv`, `src/notebook_diagrams.py` (new), `src/working_tab.py` | Inventory of every embedded image in every supplied notebook. **Finding: only one notebook exists (`Knapsack_Trace_Joan.ipynb`) and its three images are matplotlib outputs of its own code (cells 20, 22, 24) — no hand-drawn diagram and no Markdown attachment exists in any supplied notebook.** All three are extracted unchanged (bytes, size, format) and shown in panel 4 with source cell/output captions, labelled as code-generated charts; DFS/Kruskal/Dijkstra panels state that no notebook diagram was found. Missing/corrupt files produce a warning. Evidence statuses unchanged |
| G1: `v21.js` cited but not bundled | `tools/archive/v21.js` (exact v2.1 script, unchanged), `tools/browser_smoke_test.js` (new v2.2 utility) | New smoke test: tabs, headings, KPI labels, threshold/hub/target/budget changes, stale-wording checks, offline map, notebook figures, zero external requests, overflow at 1440×900 and 820×1180; `--launch` mode starts/stops the app. A shadowed-`URL` bug in `--launch` mode was found while testing and fixed |
| E: source-workbook errata | `audit/source_workbook_errata.md` (new), `audit/source_register.csv` (F1, F2 notes), `audit/assumption_register.md` (A6, A15d), README | "7X HQ site" = not independently confirmed by the current source pack; Threshold-sheet "pick the smallest X" conflicts with the adopted X = 38. Workbook unchanged (SHA-256 test) |
| F4: pandas FutureWarning | — | Re-checked: none under pandas 3.1.0 with `-W error::FutureWarning` (fix and regression test from v2.1 retained) |
| F3: dependency lock | — | `requirements-lock.txt` retained: it matches the clean validation environment (re-created and re-verified for v2.2) |

### P2 — presentation

| Issue | Files | Implementation |
|---|---|---|
| Upgrade table too wide at 1440×900 (last column truncated) | `src/tab_investment.py`, `src/ui_components.py` | Default table = Branch · Upgrade · Current hub-road time (min) · Eligibility / status · First-year cost (AED) · Annual gross-benefit proxy (AED/year); mechanism, benefit/AED, cost build-up and benefit assumptions moved to an expander. Pick tables and the branch table use the wrapping HTML table (`html_table(..., wrap=True)`) |
| Docs | README (affected sections only), `screenshots/` (v2.1 images removed; 10 v2.2 images), `audit/validation_report.md` (fresh v2.2) | |

### Intentionally left unchanged

Evidence folders, `src/evidence.py`, evidence cards, pending placeholders, `audit/evidence_inventory.md`, the contribution log; the original typed notebook and member PDFs; `data/upgrades.csv` free text (shown verbatim with a note); the Data Lead's workbook; all algorithms and baseline figures; colours, typography, chart types; no fifth tab; no benefit-realisation sensitivity (see v2.1).

### Validation (executed in this v2.2 run — details in `audit/validation_report.md`)

197 passed, 0 failed, 0 warnings (fresh extraction, clean lock environment, `-W error::FutureWarning`); compile OK; `check_slide.py` passed (20 statements); external pptx validator passed; baseline regenerates identically; browser smoke test 21/21 (app launched from another working directory) and 21/21 again in `--launch` mode; 0 external requests.

### Outstanding (not done in v2.2)

| Item | Status |
|---|---|
| Four genuine handwritten traces | **Pending — user action** (out of scope by instruction; all panels PENDING) |
| Contribution log wording, signatures, dates | **Pending — user action** (not edited in v2.2) |
| Deployment, live-link check, second computer/network test, backups | **Pending — user action** |
| Hand-drawn notebook diagrams | **Not available** — the supplied notebook has none; another notebook would need to be supplied |

---

## v2.1 — final refinement (2 Nov 2026)

Applied to the v2 bundle (`network-audit-v2.zip`, 93 tests) per the *v2.1 Final Refinement Prompt*. Tab names, the four-tab structure (no fifth tab), shared-state architecture and every network/route/knapsack figure are unchanged; what changed is how service results are classified, worded and evidenced.

### P0 — service disposition (one classifier) and corrected meaning

| File | Change | Why |
|---|---|---|
| `src/investment_core.py` | New `classify_branch`, `service_plan`, `plan_summary`, `upgrade_mechanism`, `mechanism_label`; constants DIRECT / ALT_MODE / LOCAL / OUTSIDE. `solve()` now returns `plan` for DP and greedy and `plan_before`. Removed v2's `after_time` / `coverage`, which turned a mini-hub into "0 min" and counted it as within target | v2 reported "5 of 6 within target" at baseline although only KAR and QUS meet the 20-min target by road |
| `src/tab_investment.py` | KPI rows split into "cost and modelled benefit" and "service disposition" (direct n/6, alternative mode, local fulfilment, outside plan, with a disposition); DP/greedy cards show the disposition summary; new branch-by-branch DP-vs-greedy table + per-branch explanations; DP-vs-greedy text explains the branch-level reason and states what DP does not optimise; column "Direct transfer now"; note that `upgrades.csv` wording is shown verbatim | Separate service compliance from investment response |
| `src/tab_service.py` | KPIs are direct-transfer only; statement that upgrades never change travel times; rationale card retitled "Baseline target rationale" + "Current scenario result" | Same |
| `tools/export_baseline.py`, `tools/baseline.json` | Adds `service_plan` (DP, greedy, plus50) and `rationale.plateau`; **removes** `dp.coverage` / `plus50.coverage` (they encoded the v2 error). All other fields regenerated and compared: identical to v2 | Traceable change to the baseline file |

### P0 — 20-minute rationale and terminology

| File | Change | Why |
|---|---|---|
| `src/rationale.py` | Computes the plateau of targets giving the same direct-pass set (16–22 min at baseline). Text says 20 min is one planning value inside the plateau — no "loosest"/"unique" claim; 23-min scenario unchanged (UMS passes, AED 411,960 fits, DP = greedy); caveat: decision scenario, not a proven optimum, not a customer-facing service | v2 implied 20 min was a uniquely justified value |
| `app.py`, `src/*.py`, slide, contribution log, README, audit docs | "20-minute express-service promise" / "express promise" replaced by "proposed 20-minute internal hub-to-branch transfer target"; "within promise" → "within target"; HQ wording only as a dated, attributed report with an explicit non-claim | The project never had evidence of a customer-facing 20-min product |
| `tools/make_slide.js`, `recommendation_slide.pptx` | Decision question reworded; DP bullet "2 direct · 3 local fulfilment · UMS outside plan"; +50k bullet "2 direct · 1 alternative mode (assumed) · 3 local fulfilment"; footnote with 16–22 plateau and "Local fulfilment does not make the hub-to-branch journey zero minutes"; caveat that DP maximises the gross-benefit proxy, not service or risk objectives; notes state payback/NPV/ROI are not established | Slide must match the corrected model |

### P1 — map, pandas warning, reproducibility, checks

| File | Change | Why |
|---|---|---|
| `src/ui_components.py`, `src/tab_network.py` | Coordinate map now uses a local equirectangular km projection (centroid reference, 111.32 km/deg, cos-lat scaling) with equal axis scaling (`scaleanchor`), axes "East–west offset (km)" / "North–south offset (km)", hover keeps lat/lon, caption "Local coordinate projection for visualisation; straight lines represent modelled links, not road geometry."; labels no longer clipped | v2 stretched the axes, so on-screen distances were not proportional |
| `src/routing_core.py` | Coverage-table sort key built with `pd.to_numeric(...).astype("float64").fillna(inf)` instead of `fillna(10**9)` on an object column | Reproduced the v2 `FutureWarning: Downcasting object dtype arrays on .fillna` under pandas 2.2.3 at X = 10; v2.1 code gives no warning and the same order (X 38 / 27 / 10) |
| `requirements-lock.txt` (new), `requirements-dev.txt` (new) | Exact versions from a clean venv (`pip freeze`), Python 3.13.18; dev adds pytest 9.2.0 and python-pptx 1.0.2. `requirements.txt` keeps minimum ranges for deployment | Reproducible validation |
| `tools/check_slide.py` (new) | In-repo slide check (bounds, notes, required statements, forbidden phrases, AED comma format) | v2's report cited `validate.py`, which is not in the repository (it is the external pptx-skill validator) |
| `src/ui_components.py` | Owner chip wraps cleanly at narrow widths; shorter service-chart title | Responsive check at 820 px |

### P2 — tests, docs, screenshots

| File | Change |
|---|---|
| `tests/test_service_disposition.py` (new, 24 tests) | Direct set at 20; plateau 16–22 (parametrised); 15 and 23 change the set; no "loosest"/"unique"; 481,860 / 411,960; DP vs greedy at 23; DP 2/0/3/1 and greedy UMS alternative mode from data; `Minutes_after` 0 / 18 / 25 changes the disposition; local fulfilment never a zero-minute journey; counts reconcile; hub / target / budget / cost changes recalculate; pandas warning regression under `-W error::FutureWarning` |
| `tests/test_claims.py` (new, 27 tests) | No stale "express promise"/"within promise"/"5 of 6 within" wording in user-facing files; internal-target terminology in the rendered app; HQ only as attributed report/non-claim; profit/ROI only negated; AED comma format; projected distances within 1% of great-circle; no blank/duplicate route pairs X 10–66; baseline.json regenerates identically with v2 fields unchanged; slide check passes |
| `tests/test_integration.py` (+3), `test_knapsack.py`, `test_rationale.py`, `test_visuals.py` | KPIs reconcile with the rendered disposition table; KPIs follow hub/target/budget; equal-aspect map; updated expectations |
| `README.md`, `audit/assumption_register.md` (A15, A15b, A15c, A18b, A23, A24), `audit/source_register.csv` (F8), `audit/evidence_inventory.md`, `audit/validation_report.md` (new v2.1 report) | Terminology, disposition model, plateau, objective limits, projection, setup with lock files, outstanding actions |
| `screenshots/` | v2 images removed; nine v2.1 images of the tested build (see `screenshots/README.md`) |

Considered and **not** added: a benefit-realisation sensitivity (scaling all benefits by a common factor). Uniform scaling never changes the DP or greedy selection, so it would add a control without adding insight; payback/NPV remain explicitly "not established".

### Outstanding issues carried forward into v2.1

| Issue (from v2) | Status in v2.1 |
|---|---|
| Local fulfilment counted as "within target" (5 / 6) | **Corrected in v2.1** — 2 / 6 direct, 3 local fulfilment, 1 outside |
| "20-minute express-service promise" wording | **Corrected in v2.1** |
| "Loosest target" rationale | **Corrected in v2.1** — 16–22 plateau |
| Stretched coordinate-map axes | **Corrected in v2.1** — equal-scale km projection |
| pandas `fillna` FutureWarning | **Corrected in v2.1** — reproduced on pandas 2.2.3 and fixed; regression test |
| `validate.py` cited but not in repo | **Corrected in v2.1** — report states it is external; `tools/check_slide.py` added |
| No pinned versions | **Corrected in v2.1** — lock and dev files |
| Cost inputs partly unsourced; benefits are gross estimates | **Unchanged from v2** — labelled as estimates in the registers and app |
| Four genuine handwritten traces | **Still pending — user action** (all four panels PENDING) |
| Integration Lead display name | **Corrected in v2.1** — Sparsh Saraya (confirmed by the user) |
| Member names, contribution wording, signatures, dates | **Still pending — user action** |
| Deployment and live-link check; second computer/network test; backups | **Still pending — user action** |

---

## v2 refinement (2 Nov 2026)

Applied to the v1 bundle (`network-audit.zip`, 55 tests) per the *Master Refinement Prompt v2.0*. Business question, tab names, baseline figures and the shared-state architecture are unchanged. All v1 values in `tools/baseline.json` were regenerated and compared: identical; one field (`rationale`) was added.

### P0 — academic compliance, 20/23-minute rationale, data/business accuracy

| File | Change | Why |
|---|---|---|
| `src/network_core.py` | Rewritten on NetworkX: DFS via `nx.dfs_labeled_edges` (matrix-order `sort_neighbors`) with the paper-style stack trace rebuilt from its events; components / connectivity / articulation points / bridges via NetworkX (removal re-check kept); Kruskal via `nx.minimum_spanning_edges` with the teaching table replayed in NetworkX's edge order using `nx.utils.UnionFind` and verified identical (`networkx_verified`); Prim via NetworkX | Brief appendix p. 15: "Use the networkx library for the graph work"; prompt Part F |
| `src/routing_core.py` | Distances, all equal-time predecessors and the primary path from `nx.dijkstra_predecessor_and_distance` / `single_source_dijkstra_path`; Siddal's round-by-round table kept as a teaching trace checked against NetworkX (`trace_matches_networkx`) | Part F; no custom result is presented as NetworkX output |
| `tests/reference_algorithms.py` (new) | The original hand-written DFS / Kruskal / Dijkstra, used only by tests as an independent cross-check | Keep the educational code without it driving results |
| `src/rationale.py` (new) | Computes the 20- vs next-looser-target (23 min) rationale from live data: pass counts, candidates, total cost vs budget, DP and greedy selections and gap; text adapts or says the rationale no longer holds | Part A1–A3 (dynamic, not hard-coded) |
| `src/tab_service.py` | Concise rationale card (baseline) + separate "Current scenario" line when settings differ; slider/KPI relabelled "internal transfer target", boundary rule stated (time ≤ target); NetworkX wording | A1, A2, G1, D3 |
| `src/tab_investment.py` | "Does the service target force a real investment choice?" table (current vs next looser target, live, uses edited costs when editing is on); JAFZA AED 150 rate labelled a fee proxy | A2, A3, G3 |
| `src/working_tab.py` | Assumption row "20-minute internal target" uses the computed full text; model-hub wording; graph-library note; data-provenance expander | A2, G1–G3 |
| `app.py` | Header note: 20 min = proposed internal target, not a customer SLA; hub = selected model hub; chip "Internal service target" | G1, G2 |
| `data/branches.csv` | HUB name `Emirates Post - Al Ramool Post Office (central hub, 7X HQ site)` → `Emirates Post - Al Ramool Post Office` (only change; original kept in the source workbook) | E3 / G2 — unsupported HQ claim |
| `src/data_loader.py` | HUB short name "Al Ramool (model hub)"; HQ-claim check (warn); coordinate problems now a *warning* (map falls back) instead of stopping the app; provenance check (21/21 midpoints = times.csv); `eligible_routes` drops only fully empty records and raises on malformed ones | E2, E3, G3, D2 |
| `data/source/` (new) | Data Lead's workbook `EmiratesPost_Network_Data.xlsx`, `data_check.py` + output, and `time_matrix_provenance.csv` (LOW/HIGH, midpoint, road, collection date, departure setting, Google Maps link per pair) | G3 — provenance in the bundle |

### P1 — evidence status, heatmap, formatting, blank rows

| File | Change | Why |
|---|---|---|
| `src/evidence.py` (new) | File-driven states: PENDING / NEEDS REVIEW / FILE PRESENT — REVIEW REQUIRED / INCOMPLETE / MATCHES TRANSCRIPTION / MISMATCH; checks readability (Pillow verify / PDF header), type, transcription JSON, member name, confirmation flag | B2, B3, B4 |
| `src/working_tab.py` | Evidence status summary (4 cards) moved to the very top, then the fixed baseline-run card, then panels showing status, member/role, expected input, scan or placeholder, dashboard output, transcription comparison table, mismatch explanation, typed-reference check | B1–B3 |
| `src/ui_components.py` | `knapsack_heatmap()` — Plotly heatmap from the DP matrix (all 46 capacities, rows "0 — no upgrades" + items, AED '000 cells, colour bar, TAKE/SKIP outlines with legend, hover with stage/capacity/value/traceback/decision); evidence cards; `coordinate_map()`; removed the Google Fonts `@import` (no external request) | C1–C4, E1 |
| `src/investment_core.py` | `traceback_rows()` — step, stage, capacity, comparison, TAKE/SKIP, capacity left | C3 |
| `src/working_tab.py`, `src/tab_investment.py` | Wide 46-column dataframe replaced by the heatmap + traceback table + trace-vs-exact flag; compact table of key capacities for small screens | C1–C4 |
| `src/tab_investment.py` | Budget control → `st.select_slider` over the same 0–600,000 / 10,000 values with `AED 450,000`-style labels; AED table values comma-formatted strings; consistent "First-year cost (AED)" / "Annual gross benefit proxy (AED/yr)" labels | D1, D3 |
| `src/tab_network.py` | Blank route-table row fixed at the source: the table had a hard-coded pixel height larger than its rows; now `row_height=35` and `height = 35 × (rows + 1) + 3` (data had no empty rows — verified) | D2 |
| `evidence/*/transcription_TEMPLATE.json` | Added `mismatch_explanation` | B3 |

### P3 — offline coordinate map

`src/tab_network.py` + `src/ui_components.py`: "Diagram" toggle (Schematic / Offline coordinate map). Plotly scatter of branch latitude/longitude (no tiles, no geo layers), full width, link weights, MST accepted/rejected styling and hover, hub star, coordinates on hover; validates numeric / UAE-range / distinct coordinates and falls back to the schematic with a message. *(Superseded in v2.1 by the equal-scale km projection.)*

### P2 — tests, slide, documents

| File | Change |
|---|---|
| `tests/test_network.py`, `tests/test_dijkstra.py` | Updated for the NetworkX engine; cross-checks vs reference for every X 10–66 and source; DFS trace = Data Lead sheet; boundary X 38/39 and 27/28; X = 35 cut vertex; isolated nodes; exact 23-min boundary |
| `tests/test_rationale.py`, `tests/test_evidence.py`, `tests/test_visuals.py` (new) | Part I checks: 20/23 rationale, cost/benefit edits, evidence states, heatmap = DP matrix, traceback cells, visible capacities, offline map, fallback, no web font |
| `tests/test_integration.py`, `tests/test_data_validation.py` | Evidence summary before panels, comma budget labels (AED 0 / 30,000 / 450,000 / 600,000), no blank route rows (13 and 6), no HQ claim in app text, 23-min scenario in app, edit-mode rationale, map view; malformed route record, provenance, hub name |
| `tools/export_baseline.py`, `tools/baseline.json` | Adds the computed rationale block (v1 fields unchanged) |
| `tools/make_slide.js`, `recommendation_slide.pptx` | Comma AED figures (title, cards), "BASELINE SCENARIO" label, "annual gross benefit estimate", compact "Why 20 min?" footnote and fuller notes — all generated from `baseline.json` |
| `requirements.txt` | `networkx>=3.3` (needs `sort_neighbors`), `Pillow>=10.0` (now imported directly) |
| `README.md`, `audit/*.md`, `audit/source_register.csv` | Rationale, NetworkX interpretation, offline behaviour, evidence states, hub wording, provenance, fee-proxy labelling |
| `screenshots/` | Replaced with screenshots of the tested v2 build (+ slide render) |
