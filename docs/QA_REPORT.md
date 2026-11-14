# QA report — 14 Nov 2026

> Superseded by `FINAL_RELEASE_QA.md (90 tests, 18 slides)`.

All results below were produced by commands actually run on this machine (Windows 11, Python 3.12, Microsoft Edge via Playwright 1.55). Log: `outputs/qa_run.log`.

## Automated suites — 81 / 81 passed (`python -m pytest -q tests`, 59 s)
| Suite | Tests | Covers | Result |
|---|---|---|---|
| test_rulelib.py | 16 | rule logic on hand-built cases (FX borders, gaps, pc, IBAN, 4×35, romance detector) | pass |
| test_outputs.py | 8 | cubes reconcile to 10,000,000; anomaly counts vs independent pandas profile; all validators pass; C2 exceptions ≤ 10 | pass |
| test_research.py | 5 | discovery coverage, registry completeness, atlas integrity, forensics, lineage contract | pass |
| test_submission.py | 1 | PDF limits: dashboard 14 pages (5–15), slides 19 (10–20) | pass |
| test_dashboard.py | 31 | Streamlit lab: every page renders, filters persist and act, reset, empty states | pass |
| test_web.py | 6 | site data: cube = 10M (counts and both histograms); registry = validation; BH per family; assets; no account IDs / IBAN-shaped strings; replay counts add up and are de-identified; C2 replay = validator's 2 exceptions; ledger covers every rule; genealogy only from logged hypotheses | pass |
| test_web_e2e.py | 14 | Playwright on Edge: all 48 routes render with no console errors, no NaN/undefined; 404; explorer counts = independent Python re-aggregation; URL state across reload/back/forward; empty state + reset; simulator calibration (Direct sim within 1 pt of observed) and scenario labels; atlas zoom/trace/focus; live rule search; X5 not significant after BH; JS ↔ Python rulelib parity; Forensic Replay (C2 shows exactly 2 contradicting rows; R6 none); Rule Builder supports D1 example, flags reversal, χ²/V for categorical targets; ledger/genealogy/blueprint; scenario pin/compare/export; sensitivity panels; 390 px phone layout without horizontal scroll on 10 pages, menu open/close | pass |

## Pipeline checks
| Check | Result |
|---|---|
| 34 validators × 5 splits | 34 / 34 PASS (`findings/validation_report.md`) |
| SQL vs Python cross-check (200k rows) | R6, R7, C2 100% agreement |
| Forensic Replay exact counts | R6 0 · R7 0 · R1 (Direct ⇔ pc=2) 0 · C2 2 · C3 126,857 · R5 972,971 replaced endpoints · P2 0 · X2 0 contradicting |
| Lineage schema contract | OK, 15 artefacts hashed |

## Manual / visual checks
- Screenshots at 1440×900 of overview, explorer, simulator, atlas, replay, builder, genealogy, blueprint reviewed; 390×844 of overview and explorer.
- Node syntax check of every ES module (caught one literal-newline defect, D-W28).

## Performance (local, measured during the e2e run)
- Every route reached its rendered state within the 30 s test timeout; the full 48-route sweep takes ≈ 20 s including page loads (≈ 0.4 s per route).
- Largest data file: `explorer.json` 1.7 MB (lazy, cached); whole site 9.5 MB.

## Deployment checks
- Logged-out requests to the preview (every path, including `/data/*.json`) → 302 to Vercel SSO.
- Production alias serves only the private placeholder.
- No `.env*` file in `web/dist`; `.vercelignore` excludes them.

## Not tested / open
- Signed-in click-through of the deployed preview (needs a team member's Vercel login).
- Tablet breakpoint is covered by CSS but not by an automated test.
- Public deployment: intentionally not made public before the deadline.
