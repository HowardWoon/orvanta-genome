# Project status: task tracker · testing register · submission checklist

## Task tracker
| Task | Priority | Owner | Status | Evidence of completion |
|---|---|---|---|---|
| Requirements traceability & document conflicts | P0 | Tech | Done | docs/competition_requirements.md |
| L1 ingestion with reconciliation | P0 | Tech | Done | src/ingestion.py; row asserts |
| L3 discovery: distributions, graph, stats | P0 | Tech | Done | outputs/evidence/{evidence,graph,stats}.json |
| L4/L5: 34 validators × 5 splits, cross-check | P0 | Tech | Done | findings/validation_report.md (34/34 PASS) |
| Web research platform (39 routes, explorer, simulator, playground, atlas) | P0 | Tech | Done | web/app, src/webdata.py, docs/defect_register.md |
| Team-only Vercel preview of the platform | P0 | Tech | Done | web/DEPLOY.md |
| Register with confidence classes | P0 | Tech | Done | findings/rule_evidence_register.md, register.json |
| Discovery engine, forensics, atlas, lineage | P0 | Tech | Done | outputs/evidence/{discovery,forensics,atlas,lineage}.json |
| L6 workbench (Synthetic Rule Intelligence Lab) | P0 | Tech | Done | dashboard/app.py; AppTest suite |
| Dashboard PDF (15 pp), slide PDF (20 pp) & research report | P0 | Tech → Pitch team | Draft complete | submission/*.pdf |
| Verify external references (APA, URLs) | P0 | Pitch team | **Open** | docs/source_register.md |
| Slide visual polish & rehearsal | P1 | Pitch team | **Open** | presentation.pdf is content-complete |
| Ask mentor: CUSTOMER_RECALL, start time | P2 | Team | Optional | docs/competition_requirements.md |
| Submit both PDFs before 19 Nov 12:00 | P0 | Team | **Open** | — |

## Testing register
| Suite | Tests | What it proves | Last result |
|---|---|---|---|
| tests/test_rulelib.py | 16 | rule logic (FX borders, gaps, pc, lattice, IBAN, 4×35, romance detector) on hand-built cases | pass |
| tests/test_outputs.py | 8 | cubes reconcile to 10,000,000; anomaly counts match the independent pandas profile; all validators pass; C2 exceptions ≤ 10 | pass |
| tests/test_web.py | 4 | static site: cube reconciles to 10M (counts and both histograms), registry = validation, BH per family, assets present, no account IDs or IBAN-shaped strings, noindex/.vercelignore | pass |
| tests/test_web_e2e.py | 10 | Playwright on Edge: all 39 routes render without errors, 404, explorer counts = Python re-aggregation, URL state across reload/back/forward, empty state + reset, simulator calibration and scenario labels, atlas trace/focus/zoom, live rule search, X5 not significant after BH, JS ↔ Python rulelib parity, 390 px layout | pass |
| tests/test_submission.py | 1 | PDF page limits (dashboard 5–15, slides 10–20) | pass |
| tests/test_dashboard.py | 31 | 8 pages render; filters survive page navigation (regression); filters appear only where they act; filters change KPIs; reset restores; empty states; Rule Lab selection and empty state; route explorer; anomaly selector | pass |
| src/validation.py | 34 rules × 5 splits + 3 cross-checks | rule acceptance on independent subsets | 34/34 PASS |
| tests/test_research.py | 5 | discovery coverage, registry completeness, atlas integrity, forensics, lineage contract | pass |
| Live browser check | manual | light theme, Rule Lab, no server errors | done |

Run everything with `python -m pytest -q tests` (91 tests, about 2.5 min; the browser tests need `pip install playwright` and Microsoft Edge, and skip otherwise).

## Submission checklist
- [x] Dashboard PDF in landscape, 12 pages, one feature group per page, a rule and a chart on every page
- [x] Slides PDF, 18 pages: intro, 3 methodology slides, at most 1 slide per feature group, economic reading per rule, limits, references
- [x] Every number generated from outputs/evidence (no hand-typed statistics in charts or KPIs)
- [x] No raw data in the ZIP; dataset filename asserted absent
- [x] Tools and AI use disclosed
- [ ] References verified by the team (APA 7 with URLs)
- [ ] Team walkthrough of docs/judge_qa.md
- [ ] Final file names as required by the submission link, then submit
