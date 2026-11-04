> **v2.4 note:** the four `v2_4_python_trace_*.png` files are direct renders of `src/trace_visuals.py` (DFS, Kruskal, Dijkstra, knapsack), not browser screenshots. All other screenshots are from the v2.3.1 build and were not re-captured because the app could not be launched when v2.4 was assembled.

# Screenshots — tested build v2.3.1 (3 Nov 2026)

Captured by `tools/browser_smoke_test.js --screenshots` (Playwright 1.63.0, headless Chromium) against the app started
from a **fresh extraction of `network-audit-v2_3_1.zip`**, launched from a different working directory, in a clean
environment installed from `requirements-lock.txt` (Python 3.13.18, Streamlit 1.66.1). That run passed all 35 smoke
checks and recorded **zero requests leaving localhost**. PDF pages rendered with `pdftoppm` (110 dpi); slide via
LibreOffice → PDF → JPEG. The v2.3 screenshots were removed.

**New in v2.3.1 (the two refinements)**

| File | What it shows |
|---|---|
| `tested_build_v2_3_1_dijkstra_panel_1440x900.png` | Our working → Dijkstra at 1440×900: unchanged desktop layout (placeholder left, dashboard result right) |
| `tested_build_v2_3_1_dijkstra_panel_820x1180.png` | Same panel at 820×1180 (sidebar open): placeholder stacked above the dashboard result; tables fit the panel |
| `tested_build_v2_3_1_dijkstra_panel_390x844.png` | Same panel at 390×844 (phone, sidebar closed): single column, tables wrap inside the panel |
| `tested_build_v2_3_1_knapsack_reference_pdf_page-1.png` | Corrected typed reference, page 1: label, baseline inputs, item table, recurrence |
| `tested_build_v2_3_1_knapsack_reference_pdf_page-2.png` | Page 2: full 46-column DP grid (two halves) with the traceback cells highlighted |
| `tested_build_v2_3_1_knapsack_reference_pdf_page-3.png` | Page 3: traceback, greedy steps, result, and the service-disposition table that replaces the old five-of-six row |

**Regression screenshots of the same build (content unchanged from v2.3)**

`team_overview_header_1440x900`, `tab1_network_schematic`, `tab1_offline_coordinate_map`, `tab2_service_20min`,
`tab2_service_23min`, `tab3_investment_dp_vs_greedy`, `tab4_evidence_summary_top_1440x900`, `tab4_notebook_data_threshold`,
`tab4_notebook_kruskal_panel`, `tab4_notebook_dijkstra_panel`, `tab4_notebook_knapsack_panel`,
`responsive_820px_investment_top`, `responsive_820px_notebook_figures`, `recommendation_slide` (slide file unchanged).

The evidence state is shown as it is (all four hand-traces PENDING). Notebook figures and the corrected PDF are typed /
notebook-generated references, not handwritten traces. The app has not been deployed.
