# The Network Audit — Emirates Post (DSA Final Project, MAIB) — v2.4

A four-tab Streamlit dashboard that computes, live, three operating decisions for seven Emirates Post offices around the selected model hub at Al Ramool (Umm Ramool):

> We are advising Emirates Post on how to maintain a connected, efficient inter-branch van network, test a proposed 20-minute internal hub-to-branch transfer target from the Al Ramool hub, and allocate a first-year AED 450,000 upgrade budget to the branches with the strongest modelled annual fee opportunity.

The 20-minute figure is a **proposed internal hub-to-branch transfer target** used as a planning scenario in this model. It is not an existing Emirates Post customer-facing service, product or published service level. Academic model; not an Emirates Post / 7X product; no corporate logo is used.

| Tab | Owner | Engine | Controls |
|---|---|---|---|
| **Network** | Shashaank (Network Analyst) | Kruskal via NetworkX (step table replayed with NetworkX `UnionFind`), Prim cross-check | view (all routes / minimum network), diagram (schematic / offline coordinate map), rejected-edge toggle |
| **Service coverage** | Siddal (Routing Analyst) | Dijkstra via NetworkX + round-by-round teaching trace | hub dropdown (any of 7; **choosing a hub moves the target to that hub's suggested value**), internal transfer target 10–90 min, hub ranking |
| **Investment** | Joan (Investment Analyst) | 0/1 knapsack DP written by hand + traceback, greedy, brute force | budget AED 0–600,000 in AED 10,000 steps (comma-formatted), scenario toggles |
| **Our working** | assembled and integrated by Sparsh (Integration & Business Lead); sections by Kushal, Shashaank, Siddal, Joan | DFS via NetworkX (Kushal, Data Lead) + fixed baseline evidence run for all four traces | none — fixed baseline inputs |

Sidebar: threshold X (10–66, baseline 38; kept after the X = 39 check) and **Reset all to baseline**. There is no fifth tab.

## What's new in v2.4

1. **Target follows the hub.** `src/advisor.py::suggest_promise` proposes a target per hub: the smallest whole 5-minute target at which at least a third of the destinations (2 of 6) meet it directly. At X = 38: HUB 20, KAR 20, QUS 25, UMS 25, JAF 35, SHJ 30, AJM 40 (HUB reproduces the team's baseline 20). `src/promise_sync.py` applies it when the hub changes; a manual slider value is kept until the hub changes again, **Use suggested target** is pressed, or Reset. A threshold change refreshes only an automatic target. It is a transparent planning suggestion, not a proven optimum.
2. **Recommended hub** = lowest total shortest travel time to the other six (ties: slowest branch, then matrix order). Al Ramool (HUB) is ranked first at X = 38 and 39; shown in the header chip and in a Service coverage table/chart.
3. **X = 39 vs 38 (Network tab → Threshold check; also Our working → Assumptions).** Switch only if the larger X lets the recommended hub reach branches that X = 38 cannot, within the 10–14 route band. Result: both reach 6 of 6; X = 39 adds HUB–JAF 38 and HUB–AJM 38, giving 15 routes (outside the band), hub travel 174 → 152 min, slowest 51 → 38 min, minimum network unchanged at 124 min. **X = 38 stays selected.**
4. **Our working: Python-generated trace plots and answer-key tables** (`src/trace_visuals.py`, Matplotlib, drawn live from the fixed baseline run and cached by data content): DFS tree + stack depth, Kruskal accepted/rejected + running total, Dijkstra tree + round heat grid, knapsack cost/benefit + DP-vs-greedy sweep, a key-results table, and a CSV per panel. Computer output; never handwriting evidence; evidence statuses unchanged.
5. **Look and feel** (CSS layer in `ui_components.py`): card shadows, chart cards, header, buttons, tabs, hover states, reduced-motion support.

Matplotlib is now a runtime dependency. The only cached computations are file reading and the fixed-baseline trace PNGs (keyed by the data content).

## Project Team

Shown in the dashboard header (below the business question, before the tabs) in this order:

| # | Member | Role |
|---|---|---|
| 1 | Kushal | Data Lead |
| 2 | Shashaank | Network Analyst |
| 3 | Siddal | Routing Analyst |
| 4 | Joan | Investment Analyst |
| 5 | Sparsh | Integration & Business Lead |

Ownership in the app: Network — Shashaank; Service coverage — Siddal; Investment — Joan; Our working — assembled and integrated by Sparsh, with its sections labelled *Data, threshold and DFS — Kushal*, *Kruskal — Shashaank*, *Dijkstra — Siddal*, *Knapsack — Joan* and *Overall integration and business recommendation — Sparsh*. (The contribution log is unchanged by v2.3.)

## Threshold X = 38 — the exact criterion

Route rule: an edge exists only if `Minutes < X` (strict). QUS–AJM is 37 min, so X = 37 excludes it (12 routes) and X = 38 includes it (13 routes, connected, inside the brief's 10–14 band). The two 38-minute links (HUB–JAF, HUB–AJM) stay excluded at X = 38; at X = 39 they enter and the count rises to 15, outside the band. X = 38 is therefore the smallest whole-minute threshold that admits the 37-minute QUS–AJM link while keeping 10–14 routes and excluding the 38-minute links — and with it Ajman is no longer attached only through SHJ–AJM (at X = 37 that link is a bridge; at X = 38 there is no bridge). Other thresholds (31–37) are also connected and in the band, so X = 38 is *not* "the smallest X that is connected and in the band"; the choice rests on the QUS–AJM criterion (the notebook's section 1). The Data Lead's workbook uses "smallest" and "largest" labels for this choice — see [`audit/source_workbook_errata.md`](audit/source_workbook_errata.md).

## Service dispositions — direct transfer is not the same as an upgrade

Every destination branch is classified by one function (`src/investment_core.py::classify_branch`) into exactly one of:

| Disposition | Meaning |
|---|---|
| **DIRECT HUB TRANSFER WITHIN TARGET** | shortest road-network time from the hub (Dijkstra) ≤ target |
| **ALTERNATIVE MODE WITHIN TARGET (ASSUMPTION)** | the branch is outside the target by road; a selected priced option replaces the van leg with another mode whose assumed time (`Minutes_after` > 0 in `upgrades.csv`, e.g. UMS motorbike 18 min, valid only from HUB) is ≤ target |
| **LOCAL FULFILMENT UPGRADE** | the branch is outside the target by road; a selected priced option (`Minutes_after` = 0) serves the requirement locally (mini-hub). This does **not** make the hub-to-branch journey zero minutes — the road time is unchanged and still shown |
| **OUTSIDE SELECTED SERVICE PLAN** | outside the target by road and no selected option covers it |

The Dijkstra travel times are never altered by an upgrade. KPIs, cards, the branch-by-branch table, the slide and `tools/baseline.json` all read the same classification, so the counts always reconcile.

Baseline (X 38, HUB, 20 min, AED 450,000): only **KAR (13) and QUS (16)** meet the direct transfer target (2 / 6). The DP portfolio (JAF + SHJ + AJM) adds 3 local fulfilment upgrades; UMS remains outside the selected plan (5 / 6 with a modelled disposition, 1 outside). The greedy portfolio (UMS + JAF + SHJ) gives 2 direct · UMS alternative mode (assumption) · JAF, SHJ local fulfilment · AJM outside.

### Primary disposition vs selected intervention (v2.2)

The disposition above is each branch's single **primary** classification. Separately, `classify_branch` records the **selected intervention** taken from the investment algorithm's own picks (`upgrade_selected`, `selected_upgrade`, `selected_upgrade_type`, `selected_upgrade_cost_aed`, `local_fulfilment_selected`, `alternative_mode_upgrade_selected`) — never inferred from the primary disposition. The two can differ: with *Scenario view: include priced options for branches that already pass* switched on (e.g. hub JAF, 90-minute target), DP can select a mini-hub for a branch that already meets the target directly; its primary disposition stays DIRECT HUB TRANSFER, and the upgrade is still shown and counted.

| Investment KPI | Counts | Denominator |
|---|---|---|
| Direct hub-transfer branches within target | primary disposition = direct | destination branches (6) |
| Alternative-mode branches within target (assumption) | selected alternative-mode interventions whose stated mode time (`Minutes_after` > 0, defined from HUB) is ≤ target | 6 |
| Selected local-fulfilment upgrades | selected interventions with `Minutes_after` = 0 — **regardless of primary disposition** (branch count; at most one option per branch) | 6 |
| Outside selected service plan | primary disposition = outside | 6 |
| Modelled destinations with a service disposition | primary direct + alternative mode + local fulfilment | 6 |

Primary counts always sum to 6; intervention counts are reconciled with the branch-by-branch table (columns *DP: selected upgrade* / *DP: primary disposition* and the same for greedy). A missing, negative or non-numeric `Minutes_after` is treated as "mechanism not stated" and is never classified as an alternative mode.

## Why a proposed 20-minute internal transfer target?

Computed live by `src/rationale.py` and shown in Service coverage (concise card), Investment (sensitivity table at the current settings) and Our working → Assumptions (full text); also on the recommendation slide (footnote + notes).

- The same two branches (KAR, QUS) meet the direct target for **every whole-minute target from 16 to 22 min**. 20 minutes is one selected planning value inside that plateau — not a unique or "loosest" value.
- At 20 min the four priced candidates (UMS, JAF, SHJ, AJM) cost AED 481,860 — more than the AED 450,000 budget — so the knapsack must choose (DP beats greedy by AED 45,000/yr in annual gross benefit proxy).
- At 23 min, UMS (exactly 23 min) also meets the target because the service rule is inclusive (`time ≤ target`); the remaining JAF, SHJ and AJM cost 143,520 + 130,920 + 137,520 = AED 411,960, which all fit, and DP and greedy both select all three — the constrained choice disappears under the current assumptions.

This is a useful decision scenario under the supplied Google Maps estimates and cost/benefit assumptions — not a proven operational optimum and not an existing Emirates Post customer-facing service. If the data or assumptions change, the text changes (or says the rationale no longer holds).

## What the knapsack does — and does not — optimise

The DP maximises the **sum of the supplied annual gross-benefit proxies** (`Benefit_AED`) subject to first-year cost ≤ budget. It does not optimise travel time, fairness, reliability, risk, net profit or geographic coverage. Gross benefit is a modelled fee opportunity, not profit; payback, NPV and ROI are not established, and the knapsack is not a complete corporate capital-budgeting model. The AED 45,000/yr DP-vs-greedy difference is a difference in the gross-benefit proxy, not incremental profit or cash flow.

**Recommendation slide terminology (v2.2).** `recommendation_slide.pptx` (generated by `tools/make_slide.js` from `tools/baseline.json`) states: DP selects three local-fulfilment upgrades for AED 411,960 first-year cost; AED 765,000/yr is a *modelled annual gross-benefit proxy (not profit)*; 2 branches meet the 20-minute target by direct transfer and Umm Suqeim is outside the selected plan; the 62.9% figure is a summed edge-weight proxy, not cash. Speaker notes explain the internal-target status, direct vs local fulfilment, the assumption-based benefits and the DP objective; `tools/check_slide.py` checks that these statements survive in the saved file. The Investment tab explains branch by branch why DP and greedy differ (greedy takes UMS first on benefit/cost ratio, which leaves too little budget for AJM).

## Notebook baseline references in *Our working* (v2.3)

**Source:** `notebooks/EmiratesPost_Graphs_and_Working.ipynb` — the team's *graphs and working* notebook as supplied (27 cells; the upload prefix was dropped from the file name; SHA-256 `92cbc029…`, checked by a test). It is kept unchanged. It contains **11 embedded PNG figures**, all Matplotlib output of its own code — original team-created, notebook-generated figures, **not** photographs or scans of handwriting. No Markdown attachments exist.

`tools/extract_notebook_figures.py` (standard library + Pillow) checks the inventory (cell, output, MIME, size), writes the decoded PNG bytes **unchanged** to `assets/notebook_diagrams/`, extracts the notebook's reference tables to `assets/notebook_tables/*.csv`, and writes `manifest.json` plus the inventory [`audit/notebook_diagram_inventory.csv`](audit/notebook_diagram_inventory.csv). It is idempotent and fails clearly if an image is missing, corrupt or a different size; `--check` verifies the committed assets without writing. The app never parses the notebook at runtime.

| Figure | Cell | Our working section |
|---|---|---|
| 1.1 drive-time matrix · 1.2 threshold/connectivity sensitivity · 1.3 route network at X = 38 | 4, 5, 6 | Data and threshold X — Kushal |
| 2.1 DFS traversal tree | 9 | 1 · DFS — Kushal |
| 3.1 Kruskal MST vs rejected routes | 12 | 2 · Kruskal — Shashaank |
| 4.1 shortest-path tree · 4.2 travel time vs 20-min target · 4.4 all routes vs MST-only paths | 16, 17, 19 | 3 · Dijkstra — Siddal |
| 5.1a DP grid w = 0–22 · 5.1b DP grid w = 23–45 · 5.2 DP vs greedy budget sweep | 22 (×2), 24 | 4 · Knapsack — Joan |

Each section shows its figures (natural size, never upscaled, shrunk to the panel width with the aspect ratio kept; full-size view via the image's expand icon) inside a box tagged **"Notebook baseline reference — X = 38, HUB, 20 min, AED 450,000"**, with figure number, notebook file, cell and output in the caption, a short description, the relevant notebook reference tables (typed computer output) in expanders, and a **computed cross-check** of the notebook's recorded values against this dashboard's fixed baseline run (AGREES / MISMATCH; currently 12 of 12 agree). The figures are static: when the live controls differ from the baseline, each box says the figures stay fixed at the baseline and points to the live tabs. They sit after the dashboard's own calculation and never change an evidence status; the hand-trace placeholders are unchanged.

**v2.3 derivative notebook:** `notebooks/EmiratesPost_Graphs_and_Working_v2_3_reference.ipynb`, built by `tools/make_notebook_v2_3_reference.py` (needs `requirements-notebook.txt`). Section 6 no longer compares against a typed copy of the v2.1 dashboard: it recomputes the dashboard side from the project's own code and calculates MATCH / MISMATCH (12 of 12 MATCH); a cell describing the four service dispositions (computed by the dashboard classifier) is added; all other cells, tables and the 11 figures are the original outputs (figures byte-identical; a fresh re-run reproduced every unchanged cell's text output).

**Superseded:** the three figures shown in v2.2 from Joan's `Knapsack_Trace_Joan.ipynb` (knapsack grid, budget sweep, funded upgrades) are no longer displayed — Figures 5.1a/5.1b/5.2 cover the same baseline knapsack content and showing both would duplicate it. Joan's notebook and its v2.2 corrected derivative remain unchanged in `evidence/reference/`.

## Shared state — the tabs cannot contradict each other

One application-level state holds `threshold_x` (38), `selected_hub` (HUB), `service_promise` (20, the internal transfer target) and `budget_aed` (450,000). The route list is rebuilt from all 21 rows of `times.csv` with the single rule `Minutes < threshold_x` (**strict**: an edge equal to X is excluded); every tab receives the same graph and the same Dijkstra result. The service rule is separate and **inclusive**: direct transfer passes when `time ≤ target`. Hub and target are owned by *Service coverage*; *Investment* reads them and owns the budget. Only file reading is cached. *Our working* always uses the fixed baseline (X 38, HUB, 20 min, AED 450,000).

## Algorithms and the brief's NetworkX instruction

The brief's technical appendix (p. 15) says: "Use the networkx library for the graph work. The one algorithm you should write yourself is the knapsack table." Accordingly:

- **NetworkX is authoritative** for connectivity/components, DFS (`dfs_labeled_edges`, neighbours in matrix order), Kruskal (`minimum_spanning_edges`), Prim, Dijkstra (`dijkstra_predecessor_and_distance`, `single_source_dijkstra_path`), articulation points, bridges and connectivity numbers.
- The teaching tables are derived from NetworkX (DFS stack trace from its forward/reverse events; Kruskal table by replaying NetworkX's edge order with NetworkX's `UnionFind`, verified identical to `minimum_spanning_edges`) or checked against it (Dijkstra round-by-round trace).
- The **0/1 knapsack DP is written by hand** (`src/investment_core.py`), with brute force over all 16 combinations as a check.
- The original hand-written DFS/Kruskal/Dijkstra live in `tests/reference_algorithms.py` as an independent cross-check (identical results for every X from 10 to 66 and every source).

## Run it

Tested on **Python 3.13.18**. Exact versions used for the v2.1, v2.2 and v2.3 validation runs are pinned in `requirements-lock.txt` (Streamlit 1.66.1, pandas 3.1.0, NetworkX 3.7, Plotly 7.1.0, Pillow 13.0.0, NumPy 2.5.4 and their dependencies). `requirements.txt` keeps the minimum compatible ranges for Streamlit Community Cloud.

```bash
cd network-audit
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-lock.txt                   # reproducible; or: pip install -r requirements.txt
streamlit run app.py
```

Tests and slide check:

```bash
pip install -r requirements-dev.txt                    # lock file + pytest 9.2.0 + python-pptx 1.0.2
python -m pytest -q -W error::FutureWarning            # full suite (unit, cross-check, whole-app AppTest)
python tools/check_slide.py                            # content/bounds check of recommendation_slide.pptx
python tools/export_baseline.py > tools/baseline.json  # regenerate the baseline figures used by the slide
python tools/extract_notebook_figures.py               # re-extract the 11 notebook figures + tables (or --check)
python tools/make_joan_v2_2_reference.py               # rebuild Joan's corrected derivative notebook (v2.2)
pip install -r requirements-notebook.txt               # optional notebook tooling (nbclient, ipykernel, matplotlib)
python tools/make_notebook_v2_3_reference.py           # rebuild the v2.3 derivative of the team notebook
python tools/make_knapsack_reference_pdf.py            # regenerate the corrected knapsack typed reference (v2.3.1)
```

Browser smoke test (new in v2.2, extended in v2.3; Node 18+ and Playwright 1.63.0 — not part of the Python requirements; run from the project root):

```bash
npm install playwright@1.63.0 && npx playwright install chromium
node tools/browser_smoke_test.js --launch              # starts the app, runs the checks, stops it
node tools/browser_smoke_test.js --url http://localhost:8501 --screenshots screenshots/   # against a running app
```

It checks (v2.3.1) the Our working Dijkstra panel layout at 1440×900 (side by side), 820×1180 and 390×844 (placeholder stacked above the dashboard result, tables inside the panel), the Project Team roster, the four tabs, headings and KPI labels, that changing threshold / hub / target / budget changes the outputs (and the baseline wording disappears), the offline map, the 11 Our working notebook figures (decoded, inside the panel) and their fixed-baseline note after the controls change, all four tab labels fully visible, zero non-local requests, and no horizontal overflow at 1440×900 and 820×1180. It does not test evidence status or the contribution log. `tools/archive/v21.js` is the unchanged screenshot script actually used for the v2.1 run.

There is no `validate.py` in this repository. The slide was additionally checked during the build with the external pptx-skill validator and a LibreOffice render; those tools are not bundled — `tools/check_slide.py` is the in-repo check.

**Offline behaviour:** the app makes no external network requests (system fonts only; Plotly figures drawn locally; no map tiles, no API keys). The *Offline coordinate map* converts the latitude/longitude in `branches.csv` to a **local east–west / north–south kilometre projection** (equirectangular about the branch centroid, 111.32 km per degree, longitude scaled by cos(latitude)) drawn with **equal axis scaling**, so on-screen distances are proportional (within ~1% of great-circle distance at this extent). Axes: "East–west offset (km)" and "North–south offset (km)"; hover shows the original latitude/longitude. Caption: *Local coordinate projection for visualisation; straight lines represent modelled links, not road geometry.* If any coordinate is missing, out of the UAE box or duplicated, the app shows a warning and falls back to the schematic diagram.

**Source workbook errata:** the Data Lead's workbook is kept unchanged; its "7X HQ site" wording (not independently confirmed by the current source pack) and its Threshold-sheet "pick the smallest X" instruction (which conflicts with the adopted X = 38) are documented in [`audit/source_workbook_errata.md`](audit/source_workbook_errata.md).

## Deploy (Streamlit Community Cloud) — not yet performed

1. Push this folder to a GitHub repository (repo root = this folder, so `app.py` and `requirements.txt` sit at the top).
2. https://share.streamlit.io → **Create app** → repo, branch `main`, main file `app.py`; Advanced settings → Python 3.13.
3. Deploy; open the URL on a different machine and network; change the hub to JAF and the budget to e.g. AED 300,000.
4. Submit the URL (or the GitHub repo link).

## Files

```
app.py                         entry point; st.set_page_config once; four tabs
src/data_loader.py             validated loader; eligible_routes() = the shared strict edge rule; provenance check
src/context.py                 shared scenario state → one graph, one Dijkstra result
src/network_core.py            NetworkX: graph, DFS trace, components, robustness, Kruskal table, Prim
src/routing_core.py            NetworkX Dijkstra, tied paths, coverage table, teaching trace
src/investment_core.py         hand-written knapsack DP + traceback, greedy, brute force; service disposition classifier
src/rationale.py               computed 20- vs 23-minute rationale + 16–22 plateau (baseline and current scenario)
src/evidence.py                evidence states from the files in evidence/<member>/
src/notebook_diagrams.py       v2.3: notebook baseline figures, reference tables and computed cross-checks in Our working
src/tab_network.py | tab_service.py | tab_investment.py | working_tab.py    tab renderers
src/ui_components.py           theme, cards, schematic + local-km coordinate map, knapsack heatmap, charts
data/branches.csv              7 branches (Kushal); HUB name without the unsupported "7X HQ site" annotation
data/times.csv                 21 undirected pair-times, minutes (Kushal)
data/upgrades.csv              4 priced options (Joan)
data/routes_X38_reference.csv  Data Lead's X = 38 export — reference only, never read by the app
data/source/                   the Data Lead's workbook, data_check.py + output, time_matrix_provenance.csv
evidence/<member>/             drop the ORIGINAL paper-trace photo here + transcription.json
archive/superseded_references/ v2.3.1: superseded typed references kept unchanged for provenance (+ README)
evidence/reference/            typed / computer-generated reference documents (not handwriting), incl. the v2.3.1
                               corrected Knapsack_Comparison_Reference_v2_3_1.pdf and the v2.2
                               corrected derivative Knapsack_Trace_Joan_v2_2_reference.ipynb (original kept unchanged)
assets/notebook_diagrams/      v2.3: the 11 original notebook figures (unchanged bytes) + manifest.json
assets/notebook_tables/        v2.3: the notebook's reference tables as CSV
notebooks/                     the team notebook as supplied + its v2.3 reference derivative
tests/                         unit, cross-check, claim-hygiene and whole-app (AppTest) tests
audit/                         source_register.csv, assumption_register.md, evidence_inventory.md,
                               validation_report.md (v2.3.1), source_research_report.md, source_workbook_errata.md,
                               notebook_diagram_inventory.csv
tools/                         export_baseline.py (+ baseline.json), make_slide.js, make_contribution_log.js, check_slide.py,
                               extract_notebook_figures.py, make_notebook_v2_3_reference.py, make_joan_v2_2_reference.py,
                               make_knapsack_reference_pdf.py (v2.3.1),
                               browser_smoke_test.js,
                               archive/v21.js
requirements.txt               minimum ranges (deployment)
requirements-lock.txt          exact versions used for the v2.1–v2.3 validation (Python 3.13.18)
requirements-notebook.txt      optional: notebook tooling actually used to build the v2.3 derivative
requirements-dev.txt           lock file + pytest + python-pptx
recommendation_slide.pptx      Integration Lead's 9–11 min slide (baseline scenario, generated from the model)
contribution_log_template.docx one-page log — unsigned; collect all five signatures
screenshots/                   screenshots of the tested v2.3.1 build (see screenshots/README.md)
CHANGELOG.md                   every change in v2, v2.1, v2.2, v2.3 and v2.3.1 and why
```

## Baseline results (computed; asserted by tests, never typed into the UI)

- X = 38: 13 routes, 334 min, connected; DFS HUB → KAR → QUS → UMS → JAF → SHJ → AJM.
- Kruskal: 6 routes, 124 min, 210 min / 62.9% less summed edge-time (a cost proxy — not cash or delivery time); 7 loop rejections; Prim = NetworkX = 124.
- Dijkstra from HUB: KAR 13, QUS 16, UMS 23, SHJ 24, JAF 47 (two tied paths), AJM 51; at 20 min 2 meet the direct transfer target, 4 do not.
- Knapsack at AED 450,000: DP JAF + SHJ + AJM, AED 411,960, AED 38,040 unused, AED 765,000/yr annual gross benefit proxy → 2 direct · 3 local fulfilment · UMS outside plan. Greedy UMS + JAF + SHJ, AED 344,340, AED 720,000/yr → 2 direct · 1 alternative mode (assumption) · 2 local fulfilment · AJM outside. Gap AED 45,000/yr.
- At AED 500,000 all four fit (AED 481,860, AED 900,000/yr, AED 18,140 unused) → 2 direct · 1 alternative mode · 3 local fulfilment · 0 outside. Still only 2 branches meet the direct transfer target by road.

## Known limitations and outstanding user actions

- The four handwritten traces are **not yet supplied** — every *Our working* panel is PENDING (see `audit/evidence_inventory.md`). They must be genuine member-authored work; this build does not and will not generate them.
- Contribution log is an unsigned template; the other members' names, contribution wording, signatures and dates must be completed and confirmed by each member.
- Not deployed; not tested on a second computer/network. Keep a backup of the screenshots and the deployed app.
- Several cost inputs have no external source (`audit/source_register.csv`); benefits are gross fee estimates, not profit; payback, NPV and ROI are not established.
- The 20-minute target is a planning scenario under the supplied assumptions (see above).
- Non-evidence delivery tasks still outstanding: deploy to Streamlit Community Cloud and check the live link; test from a second computer and network; keep backups of the screenshots and the deployed app.
- The team notebook's 11 figures are notebook-generated Matplotlib figures, not handwritten traces; the paper-trace requirement is separate and still outstanding.
- v2.3.1: the typed sheet `Knapsack_HandTrace_Sheet_Joan.pdf` (outdated combined five-of-six coverage row) is superseded by `evidence/reference/Knapsack_Comparison_Reference_v2_3_1.pdf`, regenerated from the v2.3 calculations by `tools/make_knapsack_reference_pdf.py` (needs `reportlab`, pinned in `requirements-notebook.txt`); the original is kept unchanged in `archive/superseded_references/` with a README. Both are typed references, not handwritten traces.
- The project is not yet ready for final submission while the items above remain outstanding.
