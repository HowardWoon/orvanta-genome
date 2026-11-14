# Final upgrade — reconnaissance and defect register (14 Nov 2026)

## 1. Architecture (unchanged, by decision)
Python 3.12 + DuckDB pipeline (`run_all.py`) → evidence JSON → PDFs (HTML → headless Edge), Streamlit lab, static web platform (vanilla ES modules, in-house SVG charts) on a protected Vercel preview. A framework migration would add risk five days before the deadline with no analytical gain (decision D-30).

## 2. Functionality at the start of this pass
49 web routes (2-minute guided tour + 48 pages in 10 groups); Forensic Replay; Rule Builder; Genealogy; Blueprint; Evidence Ledger (459 records); Scenario Studio with pin/compare/export; sensitivity analysis; responsive at 320–1920 px (833-render audit clean); 90 tests passing; dashboard 14 pages; deck 18 slides (the two anomaly slides had already been merged to respect one slide per feature group).

## 3. Findings (re-verified from `validation.json`)
| Finding | Value | All 5 splits |
|---|---|---|
| C2 exact | 9,999,998 / 10,000,000; 2 exceptions (both in P1 and half_1) — the only 2 payments touching an Eritrean bank | share_exact ≥ 0.9999996 everywhere |
| R1 law | q̂ = 0.3677 vs 1/e = 0.3679; Cohen's w ≤ 0.0013 | yes |
| R2 revised | cover-prone 61.4% vs other 6.7% out of sample; pooled 11.3%; V(type, K) < 0.001 | yes |
| Levels | 8 VALIDATED · 14 STRONGLY SUPPORTED · 9 SUPPORTED · 3 INCONCLUSIVE; 29 rejected hypotheses; H1–H38 | — |

## 4. Submission structure before → after
| Deliverable | Before | After |
|---|---|---|
| Dashboard PDF | 14 pages | **15 pages** — added page 15: generator blueprint by stage with confidence badges, deterministic vs stochastic, integrity, open questions, conclusion |
| Presentation PDF | 18 slides | **20 slides** — added "The challenge & the dataset" (introduction) and "Statistical robustness" (methodology); neither is a feature-group summary |
| Research report | per-rule markdown reports only | **`submission/ORVANTA_Comprehensive_Research_Report.{md,pdf}`** — 17 sections, all 34 rules with split metrics and evidence IDs, worked mathematics, H1–H38, verified references; generated from the registry |
| Consistency | tests on site data only | **`scripts/consistency_check.py`** + `tests/test_consistency.py` across validation, register, registry, ledger, replay, both PDFs, report and website data |

## 5. Defect register (this pass)
| ID | Sev | Defect | Fix |
|---|---|---|---|
| F1 | P0 | Exact-match shares within 0.001 of 1 were formatted with 4 significant digits, so C2's 0.9999998 displayed as **"1"** in the registry effect size, rule cards, the website and the report | `_num()` in `src/register.py`, `sig()` in `web/app/js/core.js`, `f()` in the report keep 7 decimals for such shares; checker asserts it |
| F2 | P1 | No standalone technical report that a reviewer could reproduce from | generated research report (MD + PDF) |
| F3 | P1 | Dashboard lacked a synthesis page (blueprint, open questions, conclusion) | page 15 |
| F4 | P1 | Deck opened methodology without stating the task and data; robustness argument spread across slides | two slides added (20 total) |
| F5 | P2 | No guidance on the most technical pages | "How to read this page" on 10 key pages (what, why, how to read, limits) |
| F6 | P2 | Report not downloadable from the site | Deliverables page links the report (PDF and Markdown) |
| F7 | P2 | Numbers duplicated by hand risked drift | consistency checker in the test suite and `run_all.py` |

## 6. Kept deliberately
Rule definitions and evidence counts (re-verified, unchanged); privacy-safe replay; protected deployment; existing pages (no feature added beyond the above).
