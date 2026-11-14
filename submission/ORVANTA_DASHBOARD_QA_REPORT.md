# ORVANTA dashboard QA report (14 Nov 2026)

**Deliverable:** `ORVANTA_GENOME_FINAL_DASHBOARD.pdf`
- 15 pages, 16 × 9 in, rendered by headless Edge from `outputs/pdf_build/dashboard.html`.
- An identical copy is kept at `submission/dashboard.pdf`.

## Commands
```bash
python -m src.charts && python -m src.reporting      # 48 charts, dashboard + presentation PDFs
python scripts/dashboard_audit.py v2                  # per-page layout measurement (Playwright + Edge)
python scripts/dashboard_registers.py                 # rule crosswalk + claim register (fails on any gap)
python scripts/consistency_check.py                   # cross-deliverable agreement
python -m pytest -q                                   # full test suite
```

## Layout audit: before vs after
- **Blank share:** the share of the content area that is bare paper.
- **Largest gap:** the tallest fully empty horizontal band, in px at 1536 px width.
- **Clearance:** the space between the lowest content and the footer.
- **Zoom:** the smallest column scale the fit script applied.

| Page | Content | Blank before | Blank after | Largest gap before → after | Clearance after (px) | Zoom after | Overflow |
|---|---|---|---|---|---|---|---|
| 1 | Executive overview | 0.426 | 0.263 | 177 → 39 | 67 | 1.00 | 0 |
| 2 | Discovery & atlas | 0.242 | 0.156 | 25 → 17 | 22 | 0.79 (chart grid) | 0 |
| 3 | Time | 0.270 | 0.261 | 25 → 46 | 74 | 1.00 | 0 |
| 4 | Currency & FX | 0.246 | 0.175 | 17 → 19 | 9 | 0.85 | 0 |
| 5 | Routing | 0.161 | 0.193 | 16 → 17 | 31 | 0.86 | 0 |
| 6 | Institutions | 0.242 | 0.175 | 25 → 19 | 31 | 0.88 | 0 |
| 7 | Processing time | 0.267 | 0.216 | 17 → 19 | 46 | 1.00 | 0 |
| 8 | Network | 0.289 | 0.229 | 25 → 19 | 42 | 1.00 | 0 |
| 9 | Forensics | 0.255 | 0.172 | 25 → 19 | 25 | 1.00 | 0 |
| 10 | Robustness | 0.203 | 0.207 | 25 → 19 | 44 | 1.00 | 0 |
| 11 | Payment value | 0.281 | 0.227 | 17 → 19 | 41 | 1.00 | 0 |
| 12 | Parties & text | 0.233 | 0.211 | 17 → 30 | 60 | 0.96 | 0 |
| 13 | Fraud anomalies | 0.228 | 0.187 | 17 → 19 | 31 | 1.00 | 0 |
| 14 | Operational anomalies | 0.224 | 0.189 | 17 → 19 | 21 | 1.00 | 0 |
| 15 | Synthesis | 0.617 | 0.245 | 192 → 23 | 25 | 1.00 | 0 |

**Result:** no page overflows, and every page clears the footer (minimum 9 px). The two near-empty pages (1 and 15) are now as dense as the rest. Pages 3, 5 and 10 are slightly emptier than before, but their largest gap is still at most 46 px.

## Visual inspection
All 15 page renders (`ORVANTA_DASHBOARD_SOURCE/audit_after/page_NN.png`) were opened and checked by eye. Defects found and fixed in this pass:

| Defect | Pages | Fix |
|---|---|---|
| Chart titles clipped at the right edge | 7, 9, 13 | `charts.save()` now wraps every title to the figure width |
| Anomaly-profile chart showed label counts, but its caption described amounts and durations | 9, 13 | Chart rebuilt to show median amount and median duration per label against normal traffic. Page 9 now uses a new uniformity-fingerprint chart. |
| Page 9 headline wrapped onto two lines | 9 | Headline shortened |
| Page 12 overflowed the footer by 6 px at the zoom floor | 12 | Five tall charts widened to the grid aspect ratio |
| Page 2 had a 220 px empty band and a tiny heatmap beside an empty cell | 2 | Significance box moved left; added a table of the 9 strongest dependencies and what explains each |

The printed PDF was rasterised (pages 2 and 4) and matches the audited HTML. This confirms the fit script runs before Edge prints.

## Traceability
| Check | Result |
|---|---|
| Rules in an evidence table (`ORVANTA_RULE_CROSSWALK.csv`) | **34 / 34**, missing: none |
| Printed confidence level = `src/levels.py` | 34 / 34 agree (8 validated · 14 strongly supported · 9 supported · 3 inconclusive) |
| Validator status | 34 / 34 PASS on 5 splits |
| Claims traced (`ORVANTA_CLAIM_EVIDENCE_REGISTER.csv`) | 61: 15 headlines, 6 KPIs, 40 evidence-table rows, each mapped to its source JSON field, rule ID and evidence ID |
| Independent re-derivation | The Colab prototype `notebooks/ORVANTA_prototype_analysis.ipynb` recomputes 32 dashboard metrics on a 5% sample plus all labelled anomalies: **32 / 32 agree** within sampling tolerance (exact rules agree exactly) |
| Consistency checker | "all deliverables agree" (exit 0) |

## Integrity
- Inconclusive rules (T4, G1, X5) and negative results (fixed FX rate, CUSTOMER_RECALL) are shown with their status. None is rounded up.
- Every page footer states that the data is synthetic (n = 10,000,000). The scope box and the conclusion state that the rules are reconstructions, not recovered source code.
- Atlas edges are labelled as generation dependencies, not causal claims. The fraud page states that labels are not real-world prevalence.
- No account identifiers or names appear in the dashboard. The page 4 worked example shows synthetic BIC paths only.

## Automated tests
`python -m pytest -q`: **91 passed, 0 failed** (135 s). The suite covers the rule library, outputs, research report, submission page limits, the Streamlit AppTest, site contracts, Playwright end-to-end checks and cross-deliverable consistency.

## Not covered
- Printing on paper, and PDF viewers other than Edge and Chromium.
- Readability at the 0.79 chart-grid zoom on page 2 was checked on screen only.
