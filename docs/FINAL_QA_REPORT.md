# Final QA report (14 Nov 2026)

## Commands executed (log: `outputs/run_all_final.log`)
```bash
python run_all.py --skip-ingest      # validation → register → charts → PDFs → web data → replay → ledger → research report → site → pytest
python scripts/consistency_check.py
```

## Results
| Item | Result |
|---|---|
| Pipeline | exit 0 |
| Validators | 34 / 34 PASS on 5 partitions |
| Automated tests | **91 passed, 0 failed** (131 s): rulelib 16 · outputs 8 · research 5 · submission 1 · Streamlit AppTest 31 · site contracts 6 · Playwright e2e 23 · cross-deliverable consistency 1 |
| Consistency checker | all deliverables agree (ids, titles, levels, evidence coverage, C2/R1/R2 numbers in both PDFs and the report, replay = validator, page/slide limits, one summary slide per feature group, no stale 90.6%, no unverified reference, no "34 validated rules", C2 share not rounded to 1) |
| Dashboard PDF | 15 pages (5–15); every page rendered in Edge with zero overflow |
| Presentation PDF | 20 slides (10–20); zero overflow; feature-group slides unique |
| Research report | 41-page PDF + Markdown; all 34 rules; 17 sections |
| Website | 49 routes; responsive audit clean at 17 viewports (previous pass, 833 renders); the e2e suite re-checks every route at 320, 390, 844 (landscape), 768 and 1024 px in this run |
| Privacy / secrets | no account identifiers or IBAN-shaped strings in shipped JSON; no `.env*` in `web/dist` or the ZIP |

## Manual checks this pass
Dashboard page 15, slides 3, 15, 17, 18 rendered and inspected; research report markdown scanned for "None"/"nan" and C2 rounding.

## Not tested / team actions
- Signed-in click-through of the protected preview (needs a team member's Vercel login).
- Physical phones and non-Chromium browsers.
- Public deployment (intentionally not done before the deadline).
